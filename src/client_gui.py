"""
IdentyFire Client - Cliente de Detecção com Seleção de Modelos (Versão RPC)
Responsabilidades:
- Conectar ao servidor via Sockets TCP/RPC
- Selecionar modelo a ser usado no servidor
- Enviar imagens para análise (Serializadas em Base64)
- Exibir resultados
- Implementar Algoritmo de Exclusão Mútua (Cliente)
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import threading
import uuid
import time
import socket

# Importação do protocolo RPC manual
from rpc_protocol import send_rpc_message, receive_rpc_message, image_to_base64

class FireDetectionClient:
    """Cliente de detecção de incêndios via RPC Manual"""
    
    def __init__(self, host="127.0.0.1", port=5000):
        self.host = host
        self.port = port
        self.is_connected = False
        self.client_id = str(uuid.uuid4()) # ID Único para o mecanismo de Exclusão Mútua
        
    def _send_request(self, method, params=None):
        """
        Função auxiliar para abrir socket, enviar RPC e receber resposta.
        RPC Simples: Abre conexão -> Envia -> Recebe -> Fecha.
        """
        if params is None:
            params = {}
            
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10) # Timeout de conexão
        
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
        """Verifica saúde do servidor"""
        # Mapeia para um método 'health_check' no servidor
        success, response = self._send_request("health_check")
        if success and response:
            return True, response
        return False, response if response else "Sem resposta"
    
    def get_current_model(self):
        """Obtém informações do modelo atual"""
        success, response = self._send_request("get_current_model")
        if success and response:
            if response.get('success'):
                return True, response.get('model')
            return False, None
        return False, response
    
    # ====================================================================
    # MÉTODOS DE EXCLUSÃO MÚTUA
    # ====================================================================

    def acquire_lock(self, status_callback=None):
        """
        Tenta adquirir acesso exclusivo à GPU (Polling via RPC).
        Bloqueia a execução até conseguir a vez (GRANTED).
        """
        while True:
            success, response = self._send_request("mutex_acquire", {"client_id": self.client_id})
            
            if success and response:
                if response.get('success') and response.get('status') == 'GRANTED':
                    return True
                
                # Se estiver na fila
                pos = response.get('queue_position', 1)
                wait_time = 1.0 + (pos * 0.5)
                
                msg = f"⏳ Aguardando vez na fila (Posição: {pos})..."
                if status_callback:
                    status_callback(msg)
                print(msg)
                
                time.sleep(wait_time)
            else:
                # Falha de rede
                if status_callback:
                    status_callback("⚠️ Falha de rede... tentando reconectar.")
                time.sleep(2)

    def release_lock(self):
        """Libera a GPU"""
        self._send_request("mutex_release", {"client_id": self.client_id})

    # ====================================================================
    # MÉTODOS DE PREDIÇÃO
    # ====================================================================

    def predict_image(self, image_path):
        """Envia imagem para predição via RPC (Base64)"""
        try:
            with open(image_path, 'rb') as f:
                img_bytes = f.read()
                
            # Converter bytes para string Base64 para envio via JSON
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
        """Envia múltiplas imagens em lote"""
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

            # Aumentar timeout implícito no socket se necessário para batches grandes
            success, response = self._send_request("predict_batch", params)
            
            if success and response:
                return True, response
            return False, response
                
        except Exception as e:
            return False, f"Batch Error: {str(e)}"


class ClientGUI:
    """Interface gráfica do cliente"""
    
    def __init__(self, master):
        self.master = master
        self.client = FireDetectionClient()
        
        self.load_saved_config()
        
        # Configuração da janela
        self.master.title(f"IdentyFire (RPC) - Cliente [{self.client.client_id[:8]}]")
        self.master.geometry("950x900")
        self.master.configure(bg="#f0f0f0")
        
        self.setup_ui()
        
        # Verificar conexão automaticamente
        self.master.after(500, self.connect_to_server)
    
    def load_saved_config(self):
        try:
            if os.path.exists('.client_config.json'):
                import json
                with open('.client_config.json', 'r') as f:
                    config = json.load(f)
                    self.client.host = config.get('host', '127.0.0.1')
                    self.client.port = config.get('port', 5000)
        except:
            pass
    
    def save_config(self):
        try:
            import json
            config = {'host': self.client.host, 'port': self.client.port}
            with open('.client_config.json', 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def setup_ui(self):
        # ==================== CONFIGURAÇÃO DO SERVIDOR ====================
        config_frame = tk.LabelFrame(
            self.master, text="⚙️ Configuração RPC", font=("Helvetica", 12, "bold"),
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
            self.master, text="🤖 Modelo do Servidor", font=("Helvetica", 12, "bold"),
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
            self.master, text="🔥 Detecção de Incêndios (RPC + Mutex)",
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
    
    def connect_to_server(self):
        try:
            self.client.host = self.entry_host.get()
            self.client.port = int(self.entry_port.get())
            self.save_config()
            
            self.btn_connect.config(state=tk.DISABLED, text="Verificando...")
            self.label_connection.config(text="⏳ Conectando...", fg="#FF9800")
            
            threading.Thread(target=self._connect_thread, daemon=True).start()
        except ValueError:
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
        self.label_connection.config(text=f"🟢 Conectado a {self.client.host}:{self.client.port}", fg="green")
        self.btn_connect.config(state=tk.NORMAL, text="🔌 Reconectar")
        self.btn_refresh_model_status.config(state=tk.NORMAL)
        
        # Info do modelo vinda do health check ou chamada separada
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
        
        # Display
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

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()