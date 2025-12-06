"""
IdentyFire Server - Servidor RPC com Painel de Monitoramento
Responsabilidades:
- Servir API RPC (TCP Sockets) para predições
- Auto-descoberta e gerenciamento de modelos
- Monitoramento em tempo real
- Estatísticas de uso
- Controle de Concorrência Distribuída (Mutex Centralizado)
"""

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import os
import time
from datetime import datetime

# Importar protocolo RPC
from rpc_protocol import RPCServerBase, base64_to_image

# Importar utilitários e MutexManager
from utils import (
    load_config, scan_models, load_model, 
    process_image_from_bytes, make_prediction,
    get_model_info, format_timestamp, 
    validate_image_file, bytes_to_mb,
    MutexManager
)

class IdentyFireRPCServer(RPCServerBase):
    """Servidor de detecção de incêndios usando RPC Manual"""
    
    def __init__(self, host="0.0.0.0", port=5000):
        # Inicializa a base do servidor socket
        super().__init__(host, port)
        
        self.config = load_config()
        self.modelo = None
        self.modelo_path = None
        self.modelo_info = {}
        self.available_models = []
        
        # Inicializa o gerenciador de Exclusão Mútua
        self.mutex = MutexManager(timeout_seconds=30)
        
        # Estatísticas
        self.stats = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'fires_detected': 0,
            'no_fire': 0,
            'server_start_time': None
        }
        
        self.log_callback = None
        
        # ====================================================================
        # REGISTRO DE MÉTODOS RPC (Substitui Rotas Flask)
        # ====================================================================
        self.register_method("health_check", self.rpc_health_check)
        self.register_method("get_models", self.rpc_list_models)
        self.register_method("get_current_model", self.rpc_current_model)
        self.register_method("load_model", self.rpc_load_model)
        self.register_method("mutex_acquire", self.rpc_mutex_acquire)
        self.register_method("mutex_release", self.rpc_mutex_release)
        self.register_method("predict_image", self.rpc_predict_image)
        self.register_method("predict_batch", self.rpc_predict_batch)

    def set_log_callback(self, callback):
        """Define callback para logging na GUI"""
        self.log_callback = callback
        
    def log(self, message):
        """Envia mensagem para log"""
        timestamp = format_timestamp()
        log_message = f"[{timestamp}] {message}"
        if self.log_callback:
            self.log_callback(log_message)
        print(log_message)
    
    # ====================================================================
    # LÓGICA DE GERENCIAMENTO DE MODELOS
    # ====================================================================

    def scan_available_models(self):
        models_dir = self.config['server']['models_directory']
        self.available_models = scan_models(models_dir)
        self.log(f"✓ Encontrados {len(self.available_models)} modelo(s) disponível(is)")
        return self.available_models
    
    def load_default_model(self):
        if not self.config['server'].get('auto_load_default', False):
            return False
        
        default_model = self.config['server'].get('default_model')
        if not default_model:
            return False
        
        models_dir = self.config['server']['models_directory']
        
        model_path = os.path.join(models_dir, default_model)
        return self.load_model_by_path(model_path)
    
    def load_model_by_path(self, model_path):
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
    
    def get_current_model_info_dict(self):
        if not self.modelo:
            return None
        return {
            'name': os.path.basename(self.modelo_path) if self.modelo_path else 'Unknown',
            'info': self.modelo_info,
            'loaded': True
        }

    # ====================================================================
    # MÉTODOS RPC (IMPLEMENTAÇÃO)
    # ====================================================================

    def rpc_health_check(self, params):
        uptime = None
        if self.stats['server_start_time']:
            uptime_seconds = (datetime.now() - self.stats['server_start_time']).total_seconds()
            uptime = f"{int(uptime_seconds // 3600)}h {int((uptime_seconds % 3600) // 60)}m"
        
        return {
            'status': 'online',
            'model_loaded': self.modelo is not None,
            'model_name': os.path.basename(self.modelo_path) if self.modelo_path else None,
            'uptime': uptime,
            'mutex_locked': self.mutex.locked,
            'mutex_owner': self.mutex.owner_id,
            'stats': {
                'total_requests': self.stats['requests_total'],
                'fires_detected': self.stats['fires_detected']
            }
        }

    def rpc_list_models(self, params):
        self.log("📋 RPC: Listar modelos")
        models = self.scan_available_models()
        return {'success': True, 'models': models, 'total': len(models)}

    def rpc_current_model(self, params):
        info = self.get_current_model_info_dict()
        if info:
            return {'success': True, 'model': info}
        return {'success': False, 'message': 'Nenhum modelo carregado'}

    def rpc_load_model(self, params):
        model_path = params.get('model_path')
        if not model_path:
            return {'success': False, 'error': 'No model path provided'}
        
        self.log(f"🔄 RPC: Carregar modelo '{model_path}'")
        
        # Resolução de caminho
        if not os.path.isabs(model_path):
            models_dir = self.config['server']['models_directory']
            if not os.path.isabs(models_dir):
                script_dir = os.path.dirname(os.path.abspath(__file__))
                models_dir = os.path.join(script_dir, models_dir)
            model_path = os.path.join(models_dir, model_path)
            
        if not os.path.exists(model_path):
            return {'success': False, 'error': 'File not found'}
            
        if self.load_model_by_path(model_path):
            return {'success': True, 'model': self.get_current_model_info_dict()}
        return {'success': False, 'error': 'Failed to load model'}

    def rpc_mutex_acquire(self, params):
        client_id = params.get('client_id')
        if not client_id:
            return {'success': False, 'error': 'Missing client_id'}
            
        granted, status, position = self.mutex.request_access(client_id)
        
        if status == "GRANTED":
            self.log(f"🔒 Mutex CONCEDIDO para: {client_id}")
            
        return {'success': True, 'status': status, 'queue_position': position}

    def rpc_mutex_release(self, params):
        client_id = params.get('client_id')
        success = self.mutex.release(client_id)
        if success:
            self.log(f"🔓 Mutex LIBERADO por: {client_id}")
        return {'success': success}

    def rpc_predict_image(self, params):
        """Predição de uma única imagem (Base64)"""
        self.stats['requests_total'] += 1
        
        # 1. Verificar Mutex
        client_id = params.get('client_id')
        if not client_id or not self.mutex.check_permission(client_id):
            self.log(f"🚫 Acesso negado (Mutex) ao cliente {client_id}")
            self.stats['requests_error'] += 1
            return {'success': False, 'error': 'Mutex Violation - Acquire lock first'}

        # 2. Verificar Modelo
        if self.modelo is None:
            self.stats['requests_error'] += 1
            return {'success': False, 'error': 'Model not loaded'}

        # 3. Processar Imagem
        try:
            image_b64 = params.get('image_b64')
            filename = params.get('filename', 'unknown.jpg')
            
            if not image_b64:
                return {'success': False, 'error': 'No image data'}

            image_bytes = base64_to_image(image_b64)
            
            # Validação de tamanho
            max_size_mb = self.config['server'].get('max_image_size_mb', 10)
            if bytes_to_mb(len(image_bytes)) > max_size_mb:
                return {'success': False, 'error': 'File too large'}

            # Pre-processamento
            img_config = self.config['model']
            processed_image, error = process_image_from_bytes(
                image_bytes,
                img_config['img_width'],
                img_config['img_height']
            )
            
            if error:
                self.stats['requests_error'] += 1
                return {'success': False, 'error': f'Processing failed: {error}'}

            # Predição
            threshold = img_config.get('prediction_threshold', 0.5)
            result = make_prediction(self.modelo, processed_image, threshold)
            
            if result['success']:
                self.stats['requests_success'] += 1
                if result['fire_detected']:
                    self.stats['fires_detected'] += 1
                    status = "🔥 FIRE"
                else:
                    self.stats['no_fire'] += 1
                    status = "✅ SAFE"
                
                self.log(f"{status} - {filename} ({result['confidence']:.1f}%)")
            else:
                self.stats['requests_error'] += 1

            return result

        except Exception as e:
            self.stats['requests_error'] += 1
            return {'success': False, 'error': str(e)}

    def rpc_predict_batch(self, params):
        """Predição em lote otimizada"""
        if self.modelo is None:
            return {'success': False, 'error': 'Model not loaded'}

        # 1. Verificar Mutex
        client_id = params.get('client_id')
        if not client_id or not self.mutex.check_permission(client_id):
            return {'success': False, 'error': 'Mutex Violation'}

        images_list = params.get('images', []) # Lista de dicts {filename, image_b64}
        if not images_list:
            return {'success': False, 'error': 'No images provided'}

        try:
            import numpy as np
            
            self.log(f"📦 Batch RPC: {len(images_list)} imagens")
            
            img_config = self.config['model']
            threshold = img_config.get('prediction_threshold', 0.5)
            
            processed_images = []
            filenames = []
            errors = []
            
            # Processamento
            for item in images_list:
                fname = item.get('filename', 'unknown')
                b64 = item.get('image_b64')
                
                try:
                    img_bytes = base64_to_image(b64)
                    proc_img, err = process_image_from_bytes(
                        img_bytes, img_config['img_width'], img_config['img_height']
                    )
                    
                    if err:
                        errors.append({'filename': fname, 'error': err})
                    else:
                        processed_images.append(proc_img[0]) # Remove dimensão extra (1, W, H, C)
                        filenames.append(fname)
                except Exception as e:
                    errors.append({'filename': fname, 'error': str(e)})

            if not processed_images:
                return {'success': False, 'error': 'No valid images in batch', 'errors': errors}

            # Predição na GPU (Batch único)
            batch_array = np.array(processed_images)
            self.log(f"🚀 Enviando tensor {batch_array.shape} para GPU...")
            predictions = self.modelo.predict(batch_array, verbose=0)
            
            results = []
            fire_count = 0
            
            for i, pred in enumerate(predictions):
                score = float(pred[0])
                is_fire = score > threshold
                conf = score if is_fire else 1 - score
                
                if is_fire: fire_count += 1
                
                results.append({
                    'filename': filenames[i],
                    'fire_detected': is_fire,
                    'confidence': round(conf * 100, 2),
                    'raw_prediction': score
                })

            # Atualizar stats globais
            self.stats['requests_total'] += len(results)
            self.stats['requests_success'] += len(results)
            self.stats['fires_detected'] += fire_count
            self.stats['no_fire'] += (len(results) - fire_count)

            self.log(f"✅ Batch Finalizado. Fogos: {fire_count}/{len(results)}")
            
            return {
                'success': True,
                'results': results,
                'errors': errors,
                'fires_detected': fire_count
            }

        except Exception as e:
            self.log(f"✗ Erro Fatal no Batch: {e}")
            return {'success': False, 'error': str(e)}

    # ====================================================================
    # CONTROLE DE SERVIDOR
    # ====================================================================

    def start_server_wrapper(self, host, port):
        """Wrapper para iniciar o servidor com parâmetros da GUI"""
        self.host = host
        self.port = port
        self.stats['server_start_time'] = datetime.now()
        
        self.log("=" * 60)
        self.log("SERVIDOR IDENTYFIRE RPC (TCP SOCKETS) INICIADO")
        self.log("=" * 60)
        self.log(f"🌐 Escutando em: {host}:{port}")
        self.log(f"📁 Diretório de modelos: {self.config['server']['models_directory']}")
        
        # Carregamento inicial
        self.scan_available_models()
        if self.load_default_model():
            self.log(f"✓ Modelo padrão carregado")
        else:
            self.log("⚠ Nenhum modelo carregado - aguardando cliente")
            
        # Inicia loop principal do socket (herdado de RPCServerBase)
        self.start() 

class ServerGUI:
    """Interface gráfica do servidor (Painel de Monitoramento)"""
    
    def __init__(self, master):
        self.master = master
        # Instancia o servidor RPC mas não inicia ainda
        self.server = IdentyFireRPCServer() 
        self.server.set_log_callback(self.log_to_console)
        
        self.server_thread = None
        self.server_running = False
        
        # Configuração da janela
        self.master.title("IdentyFire - Servidor RPC")
        self.master.geometry("1000x800")
        self.master.configure(bg="#f0f0f0")
        
        self.setup_ui()
        self.update_stats_loop()
    
    def setup_ui(self):
        # ==================== CONFIGURAÇÃO ====================
        config_frame = tk.LabelFrame(self.master, text="⚙️ Configuração RPC", 
                                   font=("Helvetica", 12, "bold"), bg="#e3f2fd", padx=15, pady=15)
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(config_frame, text="Host:", bg="#e3f2fd").grid(row=0, column=0, sticky="w")
        self.host_entry = tk.Entry(config_frame, width=20)
        self.host_entry.insert(0, self.server.config['server']['host'])
        self.host_entry.grid(row=0, column=1, padx=5)
        
        tk.Label(config_frame, text="Porta (TCP):", bg="#e3f2fd").grid(row=0, column=2, sticky="w")
        self.port_entry = tk.Entry(config_frame, width=10)
        self.port_entry.insert(0, str(self.server.config['server']['port']))
        self.port_entry.grid(row=0, column=3, padx=5)
        
        # ==================== CONTROLE ====================
        control_frame = tk.LabelFrame(self.master, text="🚀 Controle", 
                                    font=("Helvetica", 12, "bold"), bg="#e8f5e9", padx=15, pady=15)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.label_status = tk.Label(control_frame, text="⚪ Parado", font=("Helvetica", 14, "bold"), bg="#e8f5e9", fg="#666")
        self.label_status.pack(pady=5)
        
        self.label_modelo_atual = tk.Label(control_frame, text="Modelo: Nenhum", bg="#e8f5e9")
        self.label_modelo_atual.pack(pady=5)
        
        btn_frame = tk.Frame(control_frame, bg="#e8f5e9")
        btn_frame.pack(pady=10)
        
        self.btn_start = tk.Button(btn_frame, text="▶️ Iniciar RPC", command=self.start_server,
                                 bg="#4CAF50", fg="white", font=("bold"), width=15)
        self.btn_start.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(btn_frame, text="⏹️ Parar", command=self.stop_server,
                                bg="#f44336", fg="white", font=("bold"), width=15, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        # ==================== ESTATÍSTICAS ====================
        stats_frame = tk.LabelFrame(self.master, text="📊 Estatísticas", bg="#fff3e0", padx=15, pady=15)
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.label_requests = tk.Label(stats_frame, text="Requisições: 0", bg="#fff3e0")
        self.label_requests.grid(row=0, column=0, padx=10)
        self.label_fires = tk.Label(stats_frame, text="🔥 Fogo: 0", bg="#fff3e0", fg="red", font=("bold"))
        self.label_fires.grid(row=0, column=1, padx=10)
        self.label_safe = tk.Label(stats_frame, text="✅ Seguro: 0", bg="#fff3e0", fg="green")
        self.label_safe.grid(row=0, column=2, padx=10)
        
        # ==================== LOGS ====================
        log_frame = tk.LabelFrame(self.master, text="📋 Console", bg="#f0f0f0")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.console = scrolledtext.ScrolledText(log_frame, height=15, bg="#1e1e1e", fg="#00ff00", font=("Courier", 9))
        self.console.pack(fill=tk.BOTH, expand=True)
        tk.Button(log_frame, text="Limpar", command=lambda: self.console.delete(1.0, tk.END)).pack()

    def log_to_console(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
    
    def start_server(self):
        host = self.host_entry.get()
        try:
            port = int(self.port_entry.get())
        except ValueError:
            messagebox.showerror("Erro", "Porta inválida")
            return
            
        self.server_running = True
        self.label_status.config(text="🟢 Rodando", fg="green")
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.host_entry.config(state=tk.DISABLED)
        self.port_entry.config(state=tk.DISABLED)
        
        self.server_thread = threading.Thread(
            target=self.server.start_server_wrapper,
            args=(host, port),
            daemon=True
        )
        self.server_thread.start()
        
    def stop_server(self):
        if self.server_running:
            self.server.stop()
            self.server_running = False
            self.label_status.config(text="⚪ Parado", fg="#666")
            self.btn_start.config(state=tk.NORMAL)
            self.btn_stop.config(state=tk.DISABLED)
            self.host_entry.config(state=tk.NORMAL)
            self.port_entry.config(state=tk.NORMAL)
            
    def update_stats_loop(self):
        if self.server_running:
            stats = self.server.stats
            self.label_requests.config(text=f"Requisições: {stats['requests_total']}")
            self.label_fires.config(text=f"🔥 Fogo: {stats['fires_detected']}")
            self.label_safe.config(text=f"✅ Seguro: {stats['no_fire']}")
            
            info = self.server.get_current_model_info_dict()
            if info:
                self.label_modelo_atual.config(text=f"Modelo: {info['name']}", fg="green")
            else:
                self.label_modelo_atual.config(text="Modelo: Nenhum", fg="red")
                
        self.master.after(1000, self.update_stats_loop)
        
    def on_closing(self):
        if self.server_running:
            if messagebox.askyesno("Sair", "Parar servidor e sair?"):
                self.stop_server()
                self.master.destroy()
        else:
            self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ServerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()