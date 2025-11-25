"""
IdentyFire Server - Servidor API com Painel de Monitoramento
Responsabilidades:
- Servir API REST para predições
- Auto-descoberta e gerenciamento de modelos
- Monitoramento em tempo real
- Estatísticas de uso
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.serving import make_server
import tensorflow as tf

# Importar utilitários
from utils import (
    load_config, scan_models, load_model, 
    process_image_from_bytes, make_prediction,
    get_model_info, format_timestamp, 
    validate_image_file, bytes_to_mb
)


class IdentyFireServer:
    """Servidor API de detecção de incêndios"""
    
    def __init__(self):
        self.config = load_config()
        self.modelo = None
        self.modelo_path = None
        self.modelo_info = {}
        self.available_models = []
        
        # Estatísticas
        self.stats = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'fires_detected': 0,
            'no_fire': 0,
            'server_start_time': None
        }
        
        self.server = None
        self.flask_app = None
        self.log_callback = None
        
    def set_log_callback(self, callback):
        """Define callback para logging"""
        self.log_callback = callback
        
    def log(self, message):
        """Envia mensagem para log"""
        timestamp = format_timestamp()
        log_message = f"[{timestamp}] {message}"
        if self.log_callback:
            self.log_callback(log_message)
        print(log_message)
    
    def scan_available_models(self):
        """Escaneia e atualiza lista de modelos disponíveis"""
        models_dir = self.config['server']['models_directory']
        self.available_models = scan_models(models_dir)
        self.log(f"✓ Encontrados {len(self.available_models)} modelo(s) disponível(is)")
        return self.available_models
    
    def load_default_model(self):
        """Carrega modelo padrão se configurado"""
        if not self.config['server'].get('auto_load_default', False):
            return False
        
        default_model = self.config['server'].get('default_model')
        if not default_model:
            return False
        
        models_dir = self.config['server']['models_directory']
        
        # Se models_dir for relativo, torná-lo absoluto
        if not os.path.isabs(models_dir):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            models_dir = os.path.join(project_root, models_dir)
        
        model_path = os.path.join(models_dir, default_model)
        
        return self.load_model_by_path(model_path)
    
    def load_model_by_path(self, model_path):
        """Carrega modelo por caminho"""
        self.log(f"Carregando modelo: {model_path}")
        
        model, error = load_model(model_path)
        
        if error:
            self.log(f"✗ Erro: {error}")
            return False
        
        self.modelo = model
        self.modelo_path = model_path
        self.modelo_info = get_model_info(model)
        
        self.log(f"✓ Modelo carregado: {os.path.basename(model_path)}")
        return True
    
    def get_current_model_info(self):
        """Retorna informações do modelo atual"""
        if not self.modelo:
            return None
        
        return {
            'name': os.path.basename(self.modelo_path) if self.modelo_path else 'Unknown',
            'path': self.modelo_path,
            'info': self.modelo_info,
            'loaded': True
        }
    
    def create_flask_app(self):
        """Cria aplicação Flask com endpoints"""
        app = Flask(__name__)
        CORS(app)
        
        @app.route('/health', methods=['GET'])
        def health_check():
            """Endpoint de verificação de saúde"""
            uptime = None
            if self.stats['server_start_time']:
                uptime_seconds = (datetime.now() - self.stats['server_start_time']).total_seconds()
                uptime = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
            
            return jsonify({
                'status': 'online',
                'model_loaded': self.modelo is not None,
                'model_name': os.path.basename(self.modelo_path) if self.modelo_path else None,
                'uptime': uptime,
                'stats': {
                    'total_requests': self.stats['requests_total'],
                    'fires_detected': self.stats['fires_detected']
                }
            })
        
        @app.route('/models', methods=['GET'])
        def list_models():
            """Lista todos os modelos disponíveis"""
            self.log("📋 Requisição: Listar modelos")
            models = self.scan_available_models()
            
            return jsonify({
                'success': True,
                'models': models,
                'total': len(models),
                'models_directory': self.config['server']['models_directory']
            })
        
        @app.route('/current_model', methods=['GET'])
        def current_model():
            """Retorna informações do modelo atual"""
            self.log("📋 Requisição: Informações do modelo atual")
            
            model_info = self.get_current_model_info()
            
            if not model_info:
                return jsonify({
                    'success': False,
                    'message': 'Nenhum modelo carregado',
                    'loaded': False
                }), 200
            
            return jsonify({
                'success': True,
                'model': model_info
            })
        
        @app.route('/load_model', methods=['POST'])
        def load_model_endpoint():
            """Carrega um modelo específico"""
            data = request.get_json()
            
            if not data or 'model_path' not in data:
                return jsonify({
                    'success': False,
                    'error': 'No model path provided',
                    'message': 'Send JSON with "model_path" key'
                }), 400
            
            model_path = data['model_path']
            self.log(f"🔄 Requisição: Carregar modelo '{model_path}'")
            
            # Se for apenas o nome do arquivo, adicionar diretório
            if not os.path.isabs(model_path):
                models_dir = self.config['server']['models_directory']
                
                # Se models_dir for relativo, torná-lo absoluto
                if not os.path.isabs(models_dir):
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    project_root = os.path.dirname(script_dir)
                    models_dir = os.path.join(project_root, models_dir)
                
                model_path = os.path.join(models_dir, model_path)
            
            if not os.path.exists(model_path):
                self.log(f"✗ Modelo não encontrado: {model_path}")
                return jsonify({
                    'success': False,
                    'error': 'Model file not found',
                    'message': f'File does not exist: {model_path}'
                }), 404
            
            success = self.load_model_by_path(model_path)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': f'Model loaded successfully',
                    'model': self.get_current_model_info()
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to load model',
                    'message': 'Could not load the specified model'
                }), 500
        
        @app.route('/predict', methods=['POST'])
        def predict():
            """Endpoint de predição"""
            self.stats['requests_total'] += 1
            
            # Verificar se modelo está carregado
            if self.modelo is None:
                self.log("⚠ Requisição recebida mas modelo não carregado")
                self.stats['requests_error'] += 1
                return jsonify({
                    'success': False,
                    'error': 'Model not loaded',
                    'message': 'Server needs to load a model first'
                }), 503
            
            # Verificar se imagem foi enviada
            if 'image' not in request.files:
                self.stats['requests_error'] += 1
                return jsonify({
                    'success': False,
                    'error': 'No image provided',
                    'message': 'Please send an image file with key "image"'
                }), 400
            
            file = request.files['image']
            
            if file.filename == '':
                self.stats['requests_error'] += 1
                return jsonify({
                    'success': False,
                    'error': 'Empty filename',
                    'message': 'No file selected'
                }), 400
            
            # Validar extensão
            if not validate_image_file(file.filename):
                self.stats['requests_error'] += 1
                return jsonify({
                    'success': False,
                    'error': 'Invalid file type',
                    'message': 'Only image files are allowed (jpg, png, bmp, gif)'
                }), 400
            
            try:
                # Ler bytes da imagem
                image_bytes = file.read()
                
                # Verificar tamanho
                max_size_mb = self.config['server'].get('max_image_size_mb', 10)
                if bytes_to_mb(len(image_bytes)) > max_size_mb:
                    self.stats['requests_error'] += 1
                    return jsonify({
                        'success': False,
                        'error': 'File too large',
                        'message': f'Maximum file size is {max_size_mb}MB'
                    }), 413
                
                # Processar imagem
                img_config = self.config['model']
                processed_image, error = process_image_from_bytes(
                    image_bytes,
                    img_config['img_width'],
                    img_config['img_height']
                )
                
                if error:
                    self.log(f"✗ Erro ao processar: {error}")
                    self.stats['requests_error'] += 1
                    return jsonify({
                        'success': False,
                        'error': 'Image processing failed',
                        'message': error
                    }), 400
                
                # Fazer predição
                threshold = img_config.get('prediction_threshold', 0.5)
                result = make_prediction(self.modelo, processed_image, threshold)
                
                if not result['success']:
                    self.log(f"✗ Erro na predição: {result.get('error')}")
                    self.stats['requests_error'] += 1
                    return jsonify(result), 500
                
                # Atualizar estatísticas
                self.stats['requests_success'] += 1
                if result['fire_detected']:
                    self.stats['fires_detected'] += 1
                else:
                    self.stats['no_fire'] += 1
                
                # Log
                status = "🔥 FIRE" if result['fire_detected'] else "✅ SAFE"
                self.log(f"{status} - {file.filename} (confidence: {result['confidence']:.1f}%)")
                
                result['filename'] = file.filename
                return jsonify(result), 200
                
            except Exception as e:
                self.log(f"✗ Erro inesperado: {str(e)}")
                self.stats['requests_error'] += 1
                return jsonify({
                    'success': False,
                    'error': 'Prediction failed',
                    'message': str(e)
                }), 500
        
        @app.route('/predict_batch', methods=['POST'])
        def predict_batch():
            """Endpoint de predição em lote otimizado para GPU"""
            if self.modelo is None:
                return jsonify({
                    'success': False,
                    'error': 'Model not loaded',
                    'message': 'Server needs to load a model first'
                }), 503
            
            # Verificar se múltiplas imagens foram enviadas
            if 'images' not in request.files:
                return jsonify({
                    'success': False,
                    'error': 'No images provided',
                    'message': 'Please send image files with key "images"'
                }), 400
            
            files = request.files.getlist('images')
            
            if not files or len(files) == 0:
                return jsonify({
                    'success': False,
                    'error': 'No images provided',
                    'message': 'Please send at least one image'
                }), 400
            
            try:
                import numpy as np
                
                self.log(f"📦 Processamento em lote: {len(files)} imagens")
                
                img_config = self.config['model']
                threshold = img_config.get('prediction_threshold', 0.5)
                max_size_mb = self.config['server'].get('max_image_size_mb', 10)
                
                # Processar todas as imagens em batch
                processed_images = []
                filenames = []
                errors = []
                
                for file in files:
                    if file.filename == '':
                        continue
                    
                    if not validate_image_file(file.filename):
                        errors.append({'filename': file.filename, 'error': 'Invalid file type'})
                        continue
                    
                    image_bytes = file.read()
                    
                    if bytes_to_mb(len(image_bytes)) > max_size_mb:
                        errors.append({'filename': file.filename, 'error': 'File too large'})
                        continue
                    
                    processed_image, error = process_image_from_bytes(
                        image_bytes,
                        img_config['img_width'],
                        img_config['img_height']
                    )
                    
                    if error:
                        errors.append({'filename': file.filename, 'error': error})
                        continue
                    
                    processed_images.append(processed_image[0])  # Remove batch dimension
                    filenames.append(file.filename)
                
                if not processed_images:
                    return jsonify({
                        'success': False,
                        'error': 'No valid images',
                        'message': 'All images failed processing',
                        'errors': errors
                    }), 400
                
                # Converter para batch numpy array
                batch_images = np.array(processed_images)
                
                # Fazer predições em batch (otimizado para GPU)
                self.log(f"🚀 Processando {len(batch_images)} imagens em batch na GPU...")
                predictions = self.modelo.predict(batch_images, verbose=0)
                
                # Processar resultados
                results = []
                for i, (pred, filename) in enumerate(zip(predictions, filenames)):
                    pred_value = float(pred[0])
                    is_fire = bool(pred_value > threshold)
                    confidence = float(pred_value if is_fire else 1 - pred_value)
                    
                    result = {
                        'filename': filename,
                        'fire_detected': is_fire,
                        'confidence': round(confidence * 100, 2),
                        'raw_prediction': pred_value
                    }
                    results.append(result)
                    
                    # Atualizar estatísticas
                    self.stats['requests_total'] += 1
                    self.stats['requests_success'] += 1
                    if is_fire:
                        self.stats['fires_detected'] += 1
                    else:
                        self.stats['no_fire'] += 1
                
                # Log resumo
                fire_count = sum(1 for r in results if r['fire_detected'])
                self.log(f"✅ Batch completo: {len(results)} imagens | 🔥 {fire_count} incêndios detectados")
                
                return jsonify({
                    'success': True,
                    'total': len(results),
                    'fires_detected': fire_count,
                    'results': results,
                    'errors': errors
                }), 200
                
            except Exception as e:
                self.log(f"✗ Erro no batch: {str(e)}")
                return jsonify({
                    'success': False,
                    'error': 'Batch prediction failed',
                    'message': str(e)
                }), 500
        
        return app
    
    def start_server(self, host, port):
        """Inicia o servidor Flask"""
        try:
            self.stats['server_start_time'] = datetime.now()
            self.flask_app = self.create_flask_app()
            self.server = make_server(host, port, self.flask_app, threaded=True)
            
            self.log("=" * 60)
            self.log("SERVIDOR IDENTYFIRE INICIADO")
            self.log("=" * 60)
            self.log(f"🌐 URL: http://{host}:{port}")
            self.log(f"📁 Diretório de modelos: {self.config['server']['models_directory']}")
            
            # Escanear modelos disponíveis
            self.scan_available_models()
            
            # Tentar carregar modelo padrão
            if self.load_default_model():
                self.log(f"✓ Modelo padrão carregado automaticamente")
            else:
                self.log("⚠ Nenhum modelo carregado - aguardando requisição do cliente")
            
            self.log("\n🔄 Aguardando requisições...")
            self.server.serve_forever()
            
        except Exception as e:
            self.log(f"✗ Erro ao iniciar servidor: {str(e)}")
            raise
    
    def stop_server(self):
        """Para o servidor"""
        if self.server:
            self.log("⏹ Parando servidor...")
            self.server.shutdown()
            self.log("✓ Servidor parado")


class ServerGUI:
    """Interface gráfica do servidor (Painel de Monitoramento)"""
    
    def __init__(self, master):
        self.master = master
        self.server = IdentyFireServer()
        self.server.set_log_callback(self.log_to_console)
        
        self.server_thread = None
        self.server_running = False
        
        # Configuração da janela
        self.master.title("IdentyFire - Servidor de Monitoramento")
        self.master.geometry("1000x800")
        self.master.configure(bg="#f0f0f0")
        
        self.setup_ui()
        
        # Atualizar estatísticas periodicamente
        self.update_stats_loop()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        
        # ==================== CONFIGURAÇÃO DO SERVIDOR ====================
        config_frame = tk.LabelFrame(
            self.master,
            text="⚙️ Configuração do Servidor",
            font=("Helvetica", 12, "bold"),
            bg="#e3f2fd",
            padx=15,
            pady=15
        )
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Host
        tk.Label(config_frame, text="Host:", bg="#e3f2fd", font=("Helvetica", 10)).grid(
            row=0, column=0, sticky="w", pady=5, padx=5
        )
        self.host_entry = tk.Entry(config_frame, width=20, font=("Helvetica", 10))
        self.host_entry.insert(0, self.server.config['server']['host'])
        self.host_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Porta
        tk.Label(config_frame, text="Porta:", bg="#e3f2fd", font=("Helvetica", 10)).grid(
            row=0, column=2, sticky="w", pady=5, padx=5
        )
        self.port_entry = tk.Entry(config_frame, width=10, font=("Helvetica", 10))
        self.port_entry.insert(0, str(self.server.config['server']['port']))
        self.port_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        # Diretório de modelos
        tk.Label(config_frame, text="Diretório de Modelos:", bg="#e3f2fd", font=("Helvetica", 10)).grid(
            row=1, column=0, sticky="w", pady=5, padx=5
        )
        self.models_dir_label = tk.Label(
            config_frame,
            text=self.server.config['server']['models_directory'],
            font=("Helvetica", 10),
            bg="#e3f2fd",
            fg="#555"
        )
        self.models_dir_label.grid(row=1, column=1, columnspan=3, sticky="w", pady=5, padx=5)
        
        # ==================== CONTROLE DO SERVIDOR ====================
        control_frame = tk.LabelFrame(
            self.master,
            text="🚀 Controle do Servidor",
            font=("Helvetica", 12, "bold"),
            bg="#e8f5e9",
            padx=15,
            pady=15
        )
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Status
        self.label_status = tk.Label(
            control_frame,
            text="⚪ Servidor Parado",
            font=("Helvetica", 14, "bold"),
            bg="#e8f5e9",
            fg="#666"
        )
        self.label_status.pack(pady=5)
        
        # URL
        self.label_url = tk.Label(
            control_frame,
            text="",
            font=("Helvetica", 10),
            bg="#e8f5e9",
            fg="#555"
        )
        self.label_url.pack(pady=5)
        
        # Modelo atual
        self.label_modelo_atual = tk.Label(
            control_frame,
            text="Modelo: Nenhum carregado",
            font=("Helvetica", 11),
            bg="#e8f5e9",
            fg="#666"
        )
        self.label_modelo_atual.pack(pady=5)
        
        # Botões
        btn_frame = tk.Frame(control_frame, bg="#e8f5e9")
        btn_frame.pack(pady=10)
        
        self.btn_start = tk.Button(
            btn_frame,
            text="▶️ Iniciar Servidor",
            command=self.start_server,
            font=("Helvetica", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2,
            width=20,
            cursor="hand2"
        )
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(
            btn_frame,
            text="⏹️ Parar Servidor",
            command=self.stop_server,
            font=("Helvetica", 11, "bold"),
            bg="#f44336",
            fg="white",
            height=2,
            width=20,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        # ==================== ESTATÍSTICAS ====================
        stats_frame = tk.LabelFrame(
            self.master,
            text="📊 Estatísticas em Tempo Real",
            font=("Helvetica", 12, "bold"),
            bg="#fff3e0",
            padx=15,
            pady=15
        )
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Grid de estatísticas
        stats_grid = tk.Frame(stats_frame, bg="#fff3e0")
        stats_grid.pack(fill=tk.X)
        
        # Requisições totais
        self.label_requests = tk.Label(
            stats_grid,
            text="Requisições Totais: 0",
            font=("Helvetica", 10),
            bg="#fff3e0"
        )
        self.label_requests.grid(row=0, column=0, sticky="w", padx=10, pady=3)
        
        # Sucesso
        self.label_success = tk.Label(
            stats_grid,
            text="✓ Sucesso: 0",
            font=("Helvetica", 10),
            bg="#fff3e0",
            fg="#2e7d32"
        )
        self.label_success.grid(row=0, column=1, sticky="w", padx=10, pady=3)
        
        # Erros
        self.label_errors = tk.Label(
            stats_grid,
            text="✗ Erros: 0",
            font=("Helvetica", 10),
            bg="#fff3e0",
            fg="#d32f2f"
        )
        self.label_errors.grid(row=0, column=2, sticky="w", padx=10, pady=3)
        
        # Incêndios detectados
        self.label_fires = tk.Label(
            stats_grid,
            text="🔥 Incêndios Detectados: 0",
            font=("Helvetica", 11, "bold"),
            bg="#fff3e0",
            fg="#d32f2f"
        )
        self.label_fires.grid(row=1, column=0, sticky="w", padx=10, pady=3)
        
        # Sem fogo
        self.label_safe = tk.Label(
            stats_grid,
            text="✅ Sem Fogo: 0",
            font=("Helvetica", 10),
            bg="#fff3e0",
            fg="#2e7d32"
        )
        self.label_safe.grid(row=1, column=1, sticky="w", padx=10, pady=3)
        
        # Taxa de detecção
        self.label_detection_rate = tk.Label(
            stats_grid,
            text="Taxa de Detecção: 0%",
            font=("Helvetica", 10),
            bg="#fff3e0"
        )
        self.label_detection_rate.grid(row=1, column=2, sticky="w", padx=10, pady=3)
        
        # ==================== CONSOLE DE LOGS ====================
        log_frame = tk.LabelFrame(
            self.master,
            text="📋 Console de Logs",
            font=("Helvetica", 12, "bold"),
            bg="#f0f0f0",
            padx=10,
            pady=10
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.console = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            width=120,
            font=("Courier", 9),
            bg="#1e1e1e",
            fg="#00ff00",
            wrap=tk.WORD
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Botão limpar console
        tk.Button(
            log_frame,
            text="🗑️ Limpar Console",
            command=self.clear_console,
            font=("Helvetica", 9),
            bg="#757575",
            fg="white",
            cursor="hand2"
        ).pack(pady=5)
    
    def log_to_console(self, message):
        """Adiciona mensagem ao console"""
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.update()
    
    def clear_console(self):
        """Limpa o console"""
        self.console.delete(1.0, tk.END)
    
    def start_server(self):
        """Inicia o servidor"""
        host = self.host_entry.get()
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Erro", "Porta deve ser um número!")
            return
        
        # Atualizar config
        self.server.config['server']['host'] = host
        self.server.config['server']['port'] = port
        
        # Atualizar UI
        self.server_running = True
        self.label_status.config(text="🟢 Servidor Rodando", fg="green")
        self.label_url.config(text=f"http://{host}:{port}")
        
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.host_entry.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.DISABLED)
        
        self.clear_console()
        
        # Iniciar servidor em thread separada
        self.server_thread = threading.Thread(
            target=self.server.start_server,
            args=(host, port),
            daemon=True
        )
        self.server_thread.start()
    
    def stop_server(self):
        """Para o servidor"""
        if self.server_running:
            self.server.stop_server()
            self.server_running = False
            
            self.label_status.config(text="⚪ Servidor Parado", fg="#666")
            self.label_url.config(text="")
            
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.host_entry.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.NORMAL)
    
    def update_stats_loop(self):
        """Atualiza estatísticas periodicamente"""
        if self.server_running:
            stats = self.server.stats
            
            self.label_requests.config(text=f"Requisições Totais: {stats['requests_total']}")
            self.label_success.config(text=f"✓ Sucesso: {stats['requests_success']}")
            self.label_errors.config(text=f"✗ Erros: {stats['requests_error']}")
            self.label_fires.config(text=f"🔥 Incêndios Detectados: {stats['fires_detected']}")
            self.label_safe.config(text=f"✅ Sem Fogo: {stats['no_fire']}")
            
            # Taxa de detecção
            if stats['requests_success'] > 0:
                rate = (stats['fires_detected'] / stats['requests_success']) * 100
                self.label_detection_rate.config(text=f"Taxa de Detecção: {rate:.1f}%")
            
            # Atualizar modelo atual
            model_info = self.server.get_current_model_info()
            if model_info:
                self.label_modelo_atual.config(
                    text=f"Modelo: {model_info['name']} ✓",
                    fg="green"
                )
            else:
                self.label_modelo_atual.config(
                    text="Modelo: Nenhum carregado",
                    fg="#666"
                )
        
        # Reagendar
        self.master.after(1000, self.update_stats_loop)
    
    def on_closing(self):
        """Handler para fechar janela"""
        if self.server_running:
            resposta = messagebox.askyesno(
                "Confirmar",
                "O servidor está rodando. Deseja parar e sair?"
            )
            if resposta:
                self.stop_server()
                self.master.destroy()
        else:
            self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
