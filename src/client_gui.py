"""
IdentyFire Client - Cliente de Detecção com Testes de Mutex Integrados
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk, scrolledtext
from PIL import Image, ImageTk
import os
import threading
import uuid
import time
import socket
import json
import subprocess
import sys

sys.setrecursionlimit(5000)  # Default = 1000

# Importação do protocolo RPC manual
from rpc_protocol import send_rpc_message, receive_rpc_message, image_to_base64

class FireDetectionClient:
    """Cliente de detecção de incêndios via RPC Manual"""
    
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.is_connected = False
        self.client_id = str(uuid.uuid4())
        
    def _send_request(self, method, params=None):
        if params is None:
            params = {}
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        
        try:
            sock.connect((self.host, self.port))
            
            message = {
                "method": method,
                "params": params
            }
            
            send_rpc_message(sock, message)
            response = receive_rpc_message(sock)
            
            return True, response
        except ConnectionRefusedError:
            return False, "Conexão recusada. O servidor está rodando?"
        except socket.timeout:
            return False, "Timeout de conexão."
        except Exception as e:
            return False, f"Erro RPC: {str(e)}"
        finally:
            try:
                sock.close()
            except:
                pass

    def check_health(self):
        success, response = self._send_request("health_check")
        if success and response:
            return True, response
        return False, response if response else "Sem resposta"
    
    def get_current_model(self):
        success, response = self._send_request("get_current_model")
        if success and response:
            if response.get('success'):
                return True, response.get('model')
            return False, None
        return False, response
    
    def acquire_lock(self, status_callback=None):
        while True:
            success, response = self._send_request("mutex_acquire", {"client_id": self.client_id})
            
            if success and response:
                if response.get('success') and response.get('status') == 'GRANTED':
                    return True
                
                pos = response.get('queue_position', 1)
                wait_time = 1.0 + (pos * 0.5)
                
                msg = f"⏳ Aguardando vez na fila (Posição: {pos})..."
                if status_callback:
                    status_callback(msg)
                print(msg)
                
                time.sleep(wait_time)
            else:
                if status_callback:
                    status_callback("⚠️ Falha de rede... tentando reconectar.")
                time.sleep(2)

    def release_lock(self):
        self._send_request("mutex_release", {"client_id": self.client_id})

    def predict_image(self, image_path):
        try:
            with open(image_path, 'rb') as f:
                img_bytes = f.read()
                
            b64_string = image_to_base64(img_bytes)
            
            params = {
                'client_id': self.client_id,
                'image_b64': b64_string,
                'filename': os.path.basename(image_path)
            }
            
            success, response = self._send_request("predict_image", params)
            
            if success and response:
                if response.get('success'):
                    return True, response
                else:
                    return False, response.get('error', 'Unknown error from server')
            else:
                return False, response

        except Exception as e:
            return False, f"Client Error: {str(e)}"
    
    def predict_batch(self, image_paths):
        try:
            images_payload = []
            
            for path in image_paths:
                with open(path, 'rb') as f:
                    b_content = f.read()
                    images_payload.append({
                        'filename': os.path.basename(path),
                        'image_b64': image_to_base64(b_content)
                    })
            
            params = {
                'client_id': self.client_id,
                'images': images_payload
            }

            success, response = self._send_request("predict_batch", params)
            
            if success and response:
                return True, response
            return False, response
                
        except Exception as e:
            return False, f"Batch Error: {str(e)}"


class ClientGUI:
    """Interface gráfica do cliente com testes integrados"""
    
    def __init__(self, master):
        self.master = master
        self.client = FireDetectionClient()
        
        self.load_saved_config()
        
        # Configuração da janela
        self.master.title(f"IdentyFire (RPC) - Cliente [{self.client.client_id[:8]}]")
        self.master.geometry("1200x900")
        self.master.configure(bg="#f0f0f0")
        
        # Notebook para abas
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 1: Detecção
        self.tab_detection = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab_detection, text="🔥 Detecção")
        
        # Aba 2: Testes de Mutex
        self.tab_tests = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab_tests, text="🧪 Testes de Mutex")
        
        # Aba 3: Visualizações
        self.tab_viz = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab_viz, text="📊 Visualizações")
        
        self.setup_detection_tab()
        self.setup_tests_tab()
        self.setup_viz_tab()
        
        # Verificar conexão automaticamente
        self.master.after(500, self.connect_to_server)
    
    def load_saved_config(self):
        try:
            if os.path.exists('.client_config.json'):
                with open('.client_config.json', 'r') as f:
                    config = json.load(f)
                    self.client.host = config.get('host', '127.0.0.1')
                    self.client.port = config.get('port', 5000)
        except:
            pass
    
    def save_config(self):
        try:
            config = {'host': self.client.host, 'port': self.client.port}
            with open('.client_config.json', 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def setup_detection_tab(self):
        """Configura aba de detecção (original)"""
        # ==================== CONFIGURAÇÃO DO SERVIDOR ====================
        config_frame = tk.LabelFrame(
            self.tab_detection, text="⚙️ Configuração RPC", font=("Helvetica", 12, "bold"),
            bg="#e3f2fd", padx=15, pady=15
        )
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(config_frame, text="Host:", bg="#e3f2fd").grid(row=0, column=0, sticky="w")
        self.entry_host = tk.Entry(config_frame, width=20)
        self.entry_host.insert(0, self.client.host)
        self.entry_host.grid(row=0, column=1, padx=5)

        tk.Label(config_frame, text="Porta:", bg="#e3f2fd").grid(row=0, column=2, sticky="w")
        self.entry_port = tk.Entry(config_frame, width=10)
        self.entry_port.insert(0, str(self.client.port))
        self.entry_port.grid(row=0, column=3, padx=5)
        
        self.btn_connect = tk.Button(
            config_frame, text="🔌 Conectar", command=self.connect_to_server,
            bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold")
        )
        self.btn_connect.grid(row=0, column=4, padx=10)
        
        self.label_connection = tk.Label(
            config_frame, text="⚪ Desconectado", font=("Helvetica", 11, "bold"),
            bg="#e3f2fd", fg="#666"
        )
        self.label_connection.grid(row=1, column=0, columnspan=5, pady=5)
        
        # ==================== STATUS DO MODELO ====================
        model_frame = tk.LabelFrame(
            self.tab_detection, text="🤖 Modelo do Servidor", font=("Helvetica", 12, "bold"),
            bg="#fff3e0", padx=15, pady=15
        )
        model_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.label_current_model = tk.Label(
            model_frame, text="⚠️ Verificando...", font=("Helvetica", 11),
            bg="#fff3e0", fg="#ff6f00"
        )
        self.label_current_model.pack(pady=5)
        
        self.btn_refresh_model_status = tk.Button(
            model_frame, text="🔄 Atualizar Status", command=self.refresh_model_status,
            bg="#2196F3", fg="white", state=tk.DISABLED
        )
        self.btn_refresh_model_status.pack(pady=5)
        
        # ==================== TESTE DE IMAGEM ====================
        test_frame = tk.LabelFrame(
            self.tab_detection, text="🔥 Detecção de Incêndios (RPC + Mutex)",
            font=("Helvetica", 12, "bold"), bg="#e8f5e9", padx=15, pady=15
        )
        test_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.label_warning = tk.Label(
            test_frame, text="💡 Conecte ao servidor RPC",
            font=("Helvetica", 10, "italic"), bg="#e8f5e9", fg="#555"
        )
        self.label_warning.pack(pady=5)
        
        self.btn_select_image = tk.Button(
            test_frame, text="🖼️ Selecionar e Analisar", command=self.select_and_analyze,
            font=("Helvetica", 12, "bold"), bg="#2196F3", fg="white", state=tk.DISABLED
        )
        self.btn_select_image.pack(pady=10)
        
        # Frame imagem
        image_container = tk.Frame(test_frame, bg="#ffffff", relief=tk.RIDGE, borderwidth=2)
        image_container.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(
            image_container, text="Sem imagem", bg="#ffffff", fg="#666"
        )
        self.image_label.pack(padx=10, pady=10, expand=True)
        
        # Resultados
        result_frame = tk.Frame(test_frame, bg="#e8f5e9")
        result_frame.pack(pady=10)
        
        self.label_result = tk.Label(
            result_frame, text="Aguardando...", font=("Helvetica", 14, "bold"),
            bg="#e8f5e9", fg="#666"
        )
        self.label_result.pack()
        
        self.label_details = tk.Label(
            result_frame, text="", bg="#e8f5e9", fg="#555"
        )
        self.label_details.pack(pady=5)
        
        self.progress = ttk.Progressbar(test_frame, mode='indeterminate', length=300)
        
        # Batch
        batch_frame = tk.Frame(test_frame, bg="#e8f5e9")
        batch_frame.pack(pady=5)
        
        self.btn_batch = tk.Button(
            batch_frame, text="📁 Processar Pasta", command=self.process_folder,
            bg="#FF9800", fg="white", state=tk.DISABLED
        )
        self.btn_batch.pack(side=tk.LEFT, padx=5)
        
        self.label_batch_status = tk.Label(batch_frame, text="", bg="#e8f5e9")
        self.label_batch_status.pack(side=tk.LEFT, padx=5)
    
    def setup_tests_tab(self):
        """Configura aba de testes de mutex"""
        # Frame de configuração
        config_frame = tk.LabelFrame(
            self.tab_tests, text="⚙️ Configuração dos Testes",
            font=("Helvetica", 12, "bold"), bg="#e3f2fd", padx=15, pady=15
        )
        config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Tipo de teste
        tk.Label(config_frame, text="Tipo de Teste:", bg="#e3f2fd").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.test_type_var = tk.StringVar(value="single")
        test_types = [
            ("Cliente Único", "single"),
            ("Múltiplos Clientes", "concurrent"),
            ("Teste de Stress", "stress"),
            ("Suite Completa", "all")
        ]
        for i, (label, value) in enumerate(test_types):
            tk.Radiobutton(
                config_frame, text=label, variable=self.test_type_var,
                value=value, bg="#e3f2fd"
            ).grid(row=0, column=i+1, padx=5)
        
        # Parâmetros
        tk.Label(config_frame, text="Nº Clientes:", bg="#e3f2fd").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.test_clients_var = tk.Spinbox(config_frame, from_=1, to=10, width=10)
        self.test_clients_var.delete(0, tk.END)
        self.test_clients_var.insert(0, "3")
        self.test_clients_var.grid(row=1, column=1, padx=5)
        
        tk.Label(config_frame, text="Nº Acessos:", bg="#e3f2fd").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        self.test_accesses_var = tk.Spinbox(config_frame, from_=1, to=20, width=10)
        self.test_accesses_var.delete(0, tk.END)
        self.test_accesses_var.insert(0, "3")
        self.test_accesses_var.grid(row=1, column=3, padx=5)
        
        # Botões de ação
        btn_frame = tk.Frame(self.tab_tests, bg="#f0f0f0")
        btn_frame.pack(pady=10)
        
        self.btn_run_test = tk.Button(
            btn_frame, text="▶️ Executar Teste", command=self.run_mutex_test,
            bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"), width=20
        )
        self.btn_run_test.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop_test = tk.Button(
            btn_frame, text="⏹️ Parar Teste", command=self.stop_mutex_test,
            bg="#f44336", fg="white", font=("Helvetica", 12, "bold"), width=20, state=tk.DISABLED
        )
        self.btn_stop_test.pack(side=tk.LEFT, padx=5)
        
        # Console de output
        console_frame = tk.LabelFrame(
            self.tab_tests, text="📋 Console de Testes",
            font=("Helvetica", 12, "bold"), bg="#f0f0f0", padx=10, pady=10
        )
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.test_console = scrolledtext.ScrolledText(
            console_frame, height=20, bg="#1e1e1e", fg="#00ff00",
            font=("Courier", 9), wrap=tk.WORD
        )
        self.test_console.pack(fill=tk.BOTH, expand=True)
        
        tk.Button(
            console_frame, text="🗑️ Limpar Console",
            command=lambda: self.test_console.delete(1.0, tk.END)
        ).pack(pady=5)
        
        # Processo de teste
        self.test_process = None
    
    def setup_viz_tab(self):
        """Configura aba de visualizações"""
        # Frame de controles
        control_frame = tk.Frame(self.tab_viz, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            control_frame, text="🔄 Atualizar Lista",
            command=self.refresh_visualizations,
            bg="#2196F3", fg="white", font=("Helvetica", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            control_frame, text="📊 Gerar Visualizações",
            command=self.generate_visualizations,
            bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        # Lista de arquivos
        files_frame = tk.LabelFrame(
            self.tab_viz, text="📁 Arquivos Gerados",
            font=("Helvetica", 11, "bold"), bg="#f0f0f0", padx=10, pady=10
        )
        files_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.files_listbox = tk.Listbox(files_frame, height=6, font=("Courier", 9))
        self.files_listbox.pack(fill=tk.X, pady=5)
        self.files_listbox.bind('<Double-Button-1>', self.open_selected_file)
        
        tk.Label(
            files_frame, text="💡 Clique duas vezes para abrir arquivo",
            bg="#f0f0f0", font=("Helvetica", 9, "italic")
        ).pack()
        
        # Visualizador de imagens
        image_frame = tk.LabelFrame(
            self.tab_viz, text="🖼️ Visualizador",
            font=("Helvetica", 11, "bold"), bg="#ffffff", padx=10, pady=10
        )
        image_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.viz_image_label = tk.Label(
            image_frame, text="Selecione uma imagem PNG da lista acima",
            bg="#ffffff", fg="#666"
        )
        self.viz_image_label.pack(expand=True)
        
        self.refresh_visualizations()
    
    # ==================== MÉTODOS DE DETECÇÃO (ORIGINAL) ====================
    
    def connect_to_server(self):
        if hasattr(self, '_connecting') and self._connecting:
            return
        
        try:
            self.client.host = self.entry_host.get()
            self.client.port = int(self.entry_port.get())
            self.save_config()
            
            self._connecting = True  # Set flag
            self.btn_connect.config(state=tk.DISABLED, text="Verificando...")
            self.label_connection.config(text="⏳ Conectando...", fg="#FF9800")
            
            threading.Thread(target=self._connect_thread, daemon=True).start()
        except ValueError:
            self._connecting = False
            messagebox.showerror("Erro", "Porta deve ser um número inteiro.")
    
    def _connect_thread(self):
        success, data = self.client.check_health()
        
        if success:
            self.client.is_connected = True
            self.master.after(0, self._on_connected, data)
        else:
            self.client.is_connected = False
            self.master.after(0, self._on_connection_failed, data)
    
    def _on_connected(self, data):
        self._connecting = False  # Clear flag
        self.label_connection.config(text=f"🟢 Conectado a {self.client.host}:{self.client.port}", fg="green")
        self.btn_connect.config(state=tk.NORMAL, text="🔌 Reconectar")
        self.btn_refresh_model_status.config(state=tk.NORMAL)
        
        model_name = data.get('model_name', 'Unknown') if isinstance(data, dict) else 'Unknown'
        is_loaded = data.get('model_loaded', False) if isinstance(data, dict) else False
        
        if is_loaded:
            self.label_current_model.config(text=f"✅ {model_name}", fg="green")
            self.label_warning.config(text="✅ Servidor online e modelo carregado", fg="green")
            self.btn_select_image.config(state=tk.NORMAL)
            self.btn_batch.config(state=tk.NORMAL)
        else:
            self.label_current_model.config(text="⚠️ Nenhum modelo carregado", fg="#ff6f00")
            self.label_warning.config(text="⚠️ Carregue um modelo no servidor", fg="#ff6f00")

    def _on_connection_failed(self, error):
        self._connecting = False  # Clear flag
        self.label_connection.config(text="🔴 Falha na conexão", fg="red")
        self.btn_connect.config(state=tk.NORMAL, text="🔌 Tentar Novamente")
        self.label_warning.config(text=f"Erro: {error}", fg="red")
        self.btn_select_image.config(state=tk.DISABLED)
        self.btn_batch.config(state=tk.DISABLED)
    
    def refresh_model_status(self):
        threading.Thread(target=self._refresh_model_thread, daemon=True).start()
        
    def _refresh_model_thread(self):
        success, info = self.client.get_current_model()
        self.master.after(0, self._on_model_status, success, info)
        
    def _on_model_status(self, success, info):
        if success and info:
            self.label_current_model.config(text=f"✅ {info.get('name')}", fg="green")
            self.btn_select_image.config(state=tk.NORMAL)
            self.btn_batch.config(state=tk.NORMAL)
        else:
            self.label_current_model.config(text="⚠️ Erro ao obter status", fg="red")

    def select_and_analyze(self):
        path = filedialog.askopenfilename(filetypes=[("Imagens", "*.jpg *.png *.jpeg")])
        if not path: return
        
        img = Image.open(path)
        img.thumbnail((400, 400))
        tk_img = ImageTk.PhotoImage(img)
        self.image_label.config(image=tk_img, text="")
        self.image_label.image = tk_img
        
        self.progress.pack(pady=10)
        self.progress.start(10)
        self.btn_select_image.config(state=tk.DISABLED)
        
        threading.Thread(target=self._analyze_thread, args=(path,), daemon=True).start()
        
    def _analyze_thread(self, path):
        def update(msg):
            self.master.after(0, lambda: self.label_details.config(text=msg))
            
        success = False
        data = None
        
        try:
            update("Solicitando Mutex...")
            if self.client.acquire_lock(status_callback=update):
                update("Processando RPC...")
                success, data = self.client.predict_image(path)
            else:
                data = "Falha no Lock"
        finally:
            self.client.release_lock()
            
        self.master.after(0, self._analyze_done, success, data)

    def _analyze_done(self, success, data):
        self.progress.stop()
        self.progress.pack_forget()
        self.btn_select_image.config(state=tk.NORMAL)
        
        if success:
            if data.get('fire_detected'):
                self.label_result.config(text="🔥 FOGO DETECTADO", fg="red")
            else:
                self.label_result.config(text="✅ SEGURO", fg="green")
            self.label_details.config(text=f"Confiança: {data.get('confidence', 0):.2f}%")
        else:
            self.label_result.config(text="❌ ERRO", fg="red")
            self.label_details.config(text=str(data))

    def process_folder(self):
        folder = filedialog.askdirectory()
        if not folder: return
        
        images = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))]
        if not images: return
        
        self.btn_batch.config(state=tk.DISABLED)
        threading.Thread(target=self._batch_thread, args=(images,), daemon=True).start()
        
    def _batch_thread(self, images):
        def update(txt):
            self.master.after(0, lambda: self.label_batch_status.config(text=txt))
            
        results = []
        try:
            update("Aguardando GPU (Lock)...")
            if self.client.acquire_lock(status_callback=update):
                update(f"Enviando {len(images)} imagens...")
                success, data = self.client.predict_batch(images)
                
                if success:
                    for res in data.get('results', []):
                        results.append((res['filename'], True, res))
                    for err in data.get('errors', []):
                        results.append((err['filename'], False, err))
                else:
                    results = [("Batch Failed", False, str(data))]
            else:
                results = [("Lock Failed", False, "Timeout")]
        finally:
            self.client.release_lock()
            
        self.master.after(0, lambda: self._show_batch_results(results))
        self.master.after(0, lambda: self.btn_batch.config(state=tk.NORMAL))
        self.master.after(0, lambda: self.label_batch_status.config(text=""))

    def _show_batch_results(self, results):
        win = tk.Toplevel(self.master)
        win.title("Resultados Batch")
        win.geometry("600x400")
        
        lb = tk.Listbox(win, font=("Courier", 10))
        lb.pack(fill=tk.BOTH, expand=True)
        
        for name, success, data in results:
            if success:
                status = "🔥 FOGO" if data.get('fire_detected') else "✅ OK"
                conf = f"{data.get('confidence',0):.1f}%"
                lb.insert(tk.END, f"{name[:30]:<30} | {status} | {conf}")
            else:
                lb.insert(tk.END, f"{name[:30]:<30} | ❌ ERRO: {data}")
    
    # ==================== MÉTODOS DE TESTES ====================
    
    def log_test(self, message):
        """Adiciona mensagem ao console de testes"""
        self.test_console.insert(tk.END, message + "\n")
        self.test_console.see(tk.END)
        self.test_console.update()
    
    def run_mutex_test(self):
        """Executa teste de mutex"""
        test_type = self.test_type_var.get()

        try:
            clients = str(int(self.test_clients_var.get()))
            accesses = str(int(self.test_accesses_var.get()))
        except (ValueError, tk.TclError):
            messagebox.showerror("Erro", "Valores inválidos para número de clientes ou acessos!")
            return
        
        self.test_console.delete(1.0, tk.END)
        self.log_test("="*60)
        self.log_test(f"INICIANDO TESTE: {test_type}")
        self.log_test(f"Clientes solicitados: {clients} | Acessos: {accesses}")
        self.log_test("="*60)
        
        self.btn_run_test.config(state=tk.DISABLED)
        self.btn_stop_test.config(state=tk.NORMAL)
        
        # Executa mutex_tester.py em subprocess
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mutex_tester_path = os.path.join(script_dir, "mutex_tester.py")
        
        cmd = [
            sys.executable, mutex_tester_path,
            "--host", self.client.host,
            "--port", str(self.client.port),
            "--test", test_type,
            "--clients", clients,
            "--accesses", accesses
        ]
        
        self.log_test(f"\nComando executado:")
        self.log_test(f"  {' '.join(cmd)}\n")
        
        threading.Thread(
            target=self._run_test_process,
            args=(cmd,),
            daemon=True
        ).start()
    
    def _run_test_process(self, cmd):
        """Executa processo de teste e captura output"""
        try:
            self.test_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1
            )
            
            for line in self.test_process.stdout:
                if line.strip():
                    self.master.after(0, self.log_test, line.strip())
            
            self.test_process.wait()
            
            if self.test_process.returncode == 0:
                self.master.after(0, self.log_test, "\n✅ TESTE CONCLUÍDO COM SUCESSO")
            else:
                self.master.after(0, self.log_test, f"\n⚠️ Teste finalizado com código: {self.test_process.returncode}")
            
            self.master.after(0, self._test_finished)
            self.master.after(100, self.refresh_visualizations)
            
        except Exception as e:
            self.master.after(0, self.log_test, f"\n✗ ERRO: {e}")
            import traceback
            self.master.after(0, self.log_test, traceback.format_exc())
            self.master.after(0, self._test_finished)
    
    def stop_mutex_test(self):
        """Para teste em execução"""
        if self.test_process:
            self.log_test("\n⏹️ Parando teste...")
            self.test_process.terminate()
            self._test_finished()
    
    def _test_finished(self):
        """Callback quando teste termina"""
        self.btn_run_test.config(state=tk.NORMAL)
        self.btn_stop_test.config(state=tk.DISABLED)
    
    # ==================== MÉTODOS DE VISUALIZAÇÃO ====================
    
    def refresh_visualizations(self):
        """Atualiza lista de arquivos gerados (apenas imagens)"""
        self.files_listbox.delete(0, tk.END)
        
        # Procura apenas arquivos PNG na pasta tests
        import glob
        
        if not os.path.exists('tests'):
            self.files_listbox.insert(tk.END, "Pasta 'tests' não encontrada. Execute um teste primeiro.")
            return
        
        files = glob.glob("tests/*.png")
        files.sort(key=os.path.getmtime, reverse=True)
        
        for f in files:
            size = os.path.getsize(f) / 1024
            filename = os.path.basename(f)
            self.files_listbox.insert(tk.END, f"{filename} ({size:.1f} KB)")
        
        if not files:
            self.files_listbox.insert(tk.END, "Nenhuma visualização encontrada. Execute testes e gere visualizações.")
    
    def open_selected_file(self, event):
        """Abre arquivo selecionado"""
        selection = self.files_listbox.curselection()
        if not selection:
            return
        
        filename = self.files_listbox.get(selection[0]).split()[0]
        filepath = os.path.join('tests', filename)
        
        if not os.path.exists(filepath):
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{filepath}")
            return
        
        self.show_image_in_viz(filepath)
    
    def show_image_in_viz(self, filename):
        """Mostra imagem PNG no visualizador"""
        try:
            img = Image.open(filename)
            
            # Redimensiona mantendo proporção
            max_size = (900, 500)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            tk_img = ImageTk.PhotoImage(img)
            self.viz_image_label.config(image=tk_img, text="")
            self.viz_image_label.image = tk_img
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir a imagem:\n{e}")
    
    def show_json_in_viewer(self, filename):
        """Mostra JSON em janela popup"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            win = tk.Toplevel(self.master)
            win.title(f"Visualizador JSON - {filename}")
            win.geometry("800x600")
            
            text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Courier", 9))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text.insert(1.0, json.dumps(data, indent=2))
            text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o JSON:\n{e}")
    
    def show_text_in_viewer(self, filename):
        """Mostra arquivo de texto em janela popup"""
        try:
            with open(filename, 'r') as f:
                content = f.read()
            
            win = tk.Toplevel(self.master)
            win.title(f"Visualizador - {filename}")
            win.geometry("800x600")
            
            text = scrolledtext.ScrolledText(win, wrap=tk.WORD, font=("Courier", 9))
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            text.insert(1.0, content)
            text.config(state=tk.DISABLED)
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível abrir o arquivo:\n{e}")
    
    def generate_visualizations(self):
        """Gera visualizações dos logs existentes"""
        import glob
        
        # Procura arquivos JSON na pasta tests
        if not os.path.exists('tests'):
            messagebox.showwarning(
                "Aviso",
                "Pasta 'tests' não encontrada.\n\n"
                "Execute um teste primeiro."
            )
            return
        
        json_files = glob.glob("tests/test_concurrent_client_*.json")
        
        if not json_files:
            messagebox.showwarning(
                "Aviso",
                "Nenhum arquivo de log encontrado em ./tests\n\n"
                "Execute um teste de múltiplos clientes primeiro."
            )
            return
        
        self.log_test("\n" + "="*60)
        self.log_test("GERANDO VISUALIZAÇÕES")
        self.log_test(f"Arquivos encontrados: {len(json_files)}")
        self.log_test("="*60)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_visualizer_path = os.path.join(script_dir, "log_visualizer.py")
        
        if not os.path.exists(log_visualizer_path):
            self.log_test(f"\n✗ Erro: log_visualizer.py não encontrado")
            messagebox.showerror("Erro", f"Arquivo não encontrado:\n{log_visualizer_path}")
            return
        
        cmd = [sys.executable, log_visualizer_path] + json_files
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=30
            )
            
            self.log_test(result.stdout)
            
            if result.returncode == 0:
                self.log_test("\n✓ Visualizações geradas com sucesso em ./tests/")
                messagebox.showinfo(
                    "Sucesso",
                    "Visualizações geradas em ./tests/\n\n"
                    "Verifique a aba 'Visualizações' para ver os gráficos."
                )
                self.refresh_visualizations()
            else:
                self.log_test(f"\n✗ Código de retorno: {result.returncode}")
                self.log_test(f"Stderr: {result.stderr}")
                messagebox.showerror("Erro", f"Falha ao gerar visualizações:\n{result.stderr}")
        
        except subprocess.TimeoutExpired:
            self.log_test("\n✗ Timeout ao gerar visualizações")
            messagebox.showerror("Erro", "Timeout ao gerar visualizações")
        except Exception as e:
            self.log_test(f"\n✗ Erro: {e}")
            import traceback
            self.log_test(traceback.format_exc())
            messagebox.showerror("Erro", f"Erro ao gerar visualizações:\n{e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()