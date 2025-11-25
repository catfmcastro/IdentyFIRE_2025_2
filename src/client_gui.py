"""
IdentyFire Client - Cliente de Detecção com Seleção de Modelos
Responsabilidades:
- Conectar ao servidor
- Selecionar modelo a ser usado no servidor
- Enviar imagens para análise
- Exibir resultados
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import requests
import os
import threading


class FireDetectionClient:
    """Cliente de detecção de incêndios"""
    
    def __init__(self, server_url="http://127.0.0.1:5000"):
        self.server_url = server_url.rstrip('/')
        self.is_connected = False
        self.current_model = None
        self.available_models = []
        
    def check_health(self):
        """Verifica saúde do servidor"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                return True, response.json()
            return False, None
        except requests.exceptions.RequestException as e:
            return False, str(e)
    
    def get_current_model(self):
        """Obtém informações do modelo atual"""
        try:
            response = requests.get(f"{self.server_url}/current_model", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    return True, data['model']
                return False, None
            return False, None
        except requests.exceptions.RequestException as e:
            return False, str(e)
    
    def predict_image(self, image_path):
        """Envia imagem para predição"""
        try:
            with open(image_path, 'rb') as f:
                files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
                response = requests.post(
                    f"{self.server_url}/predict",
                    files=files,
                    timeout=30
                )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                return False, error_data.get('error', 'Unknown error')
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"
    
    def predict_batch(self, image_paths):
        """Envia múltiplas imagens para predição em lote (otimizado para GPU)"""
        try:
            files = []
            for image_path in image_paths:
                f = open(image_path, 'rb')
                files.append(('images', (os.path.basename(image_path), f, 'image/jpeg')))
            
            try:
                response = requests.post(
                    f"{self.server_url}/predict_batch",
                    files=files,
                    timeout=120  # Timeout maior para batch
                )
                
                if response.status_code == 200:
                    return True, response.json()
                else:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                    return False, error_data.get('error', 'Unknown error')
            finally:
                # Fechar todos os arquivos
                for _, file_tuple in files:
                    file_tuple[1].close()
                
        except requests.exceptions.RequestException as e:
            return False, f"Connection error: {str(e)}"


class ClientGUI:
    """Interface gráfica do cliente"""
    
    def __init__(self, master):
        self.master = master
        self.client = FireDetectionClient()
        
        # Tentar carregar URL salva
        self.load_saved_config()
        
        # Configuração da janela
        self.master.title("IdentyFire - Cliente de Detecção")
        self.master.geometry("950x900")
        self.master.configure(bg="#f0f0f0")
        
        self.setup_ui()
        
        # Verificar conexão automaticamente
        self.master.after(500, self.connect_to_server)
    
    def load_saved_config(self):
        """Carrega configuração salva"""
        try:
            if os.path.exists('.client_config.json'):
                import json
                with open('.client_config.json', 'r') as f:
                    config = json.load(f)
                    self.client.server_url = config.get('server_url', self.client.server_url)
        except:
            pass
    
    def save_config(self):
        """Salva configuração"""
        try:
            import json
            config = {'server_url': self.client.server_url}
            with open('.client_config.json', 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def setup_ui(self):
        """Configura interface do usuário"""
        
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
        
        # URL do servidor
        tk.Label(
            config_frame,
            text="URL do Servidor:",
            bg="#e3f2fd",
            font=("Helvetica", 10)
        ).grid(row=0, column=0, sticky="w", pady=5, padx=5)
        
        self.server_entry = tk.Entry(config_frame, width=40, font=("Helvetica", 10))
        self.server_entry.insert(0, self.client.server_url)
        self.server_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Botão conectar
        self.btn_connect = tk.Button(
            config_frame,
            text="🔌 Conectar",
            command=self.connect_to_server,
            font=("Helvetica", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            cursor="hand2",
            width=15
        )
        self.btn_connect.grid(row=0, column=2, padx=5, pady=5)
        
        # Status da conexão
        self.label_connection = tk.Label(
            config_frame,
            text="⚪ Desconectado",
            font=("Helvetica", 11, "bold"),
            bg="#e3f2fd",
            fg="#666"
        )
        self.label_connection.grid(row=1, column=0, columnspan=3, pady=5)
        
        # ==================== STATUS DO MODELO ====================
        model_frame = tk.LabelFrame(
            self.master,
            text="🤖 Modelo do Servidor",
            font=("Helvetica", 12, "bold"),
            bg="#fff3e0",
            padx=15,
            pady=15
        )
        model_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Modelo atual no servidor
        tk.Label(
            model_frame,
            text="Modelo Ativo:",
            bg="#fff3e0",
            font=("Helvetica", 10, "bold")
        ).pack(pady=5)
        
        self.label_current_model = tk.Label(
            model_frame,
            text="⚠️ Verificando...",
            font=("Helvetica", 11),
            bg="#fff3e0",
            fg="#ff6f00"
        )
        self.label_current_model.pack(pady=5)
        
        # Botão atualizar status do modelo
        self.btn_refresh_model_status = tk.Button(
            model_frame,
            text="🔄 Atualizar Status",
            command=self.refresh_model_status,
            font=("Helvetica", 9),
            bg="#2196F3",
            fg="white",
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_refresh_model_status.pack(pady=5)
        
        # ==================== TESTE DE IMAGEM ====================
        test_frame = tk.LabelFrame(
            self.master,
            text="🔥 Detecção de Incêndios",
            font=("Helvetica", 12, "bold"),
            bg="#e8f5e9",
            padx=15,
            pady=15
        )
        test_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aviso de pré-requisito
        self.label_warning = tk.Label(
            test_frame,
            text="💡 Use a GUI de Treinamento para carregar modelos no servidor",
            font=("Helvetica", 10, "italic"),
            bg="#e8f5e9",
            fg="#555"
        )
        self.label_warning.pack(pady=5)
        
        # Botão de seleção
        self.btn_select_image = tk.Button(
            test_frame,
            text="🖼️ Selecionar e Analisar Imagem",
            command=self.select_and_analyze,
            font=("Helvetica", 12, "bold"),
            bg="#2196F3",
            fg="white",
            height=2,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_select_image.pack(pady=10)
        
        # Frame para imagem
        image_container = tk.Frame(test_frame, bg="#ffffff", relief=tk.RIDGE, borderwidth=2)
        image_container.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.image_label = tk.Label(
            image_container,
            text="Nenhuma imagem selecionada\n\nConecte-se ao servidor e selecione um modelo",
            font=("Helvetica", 11),
            bg="#ffffff",
            fg="#666",
            justify=tk.CENTER
        )
        self.image_label.pack(padx=10, pady=10, expand=True)
        
        # Resultado
        result_frame = tk.Frame(test_frame, bg="#e8f5e9")
        result_frame.pack(pady=10)
        
        self.label_result = tk.Label(
            result_frame,
            text="Aguardando análise...",
            font=("Helvetica", 14, "bold"),
            bg="#e8f5e9",
            fg="#666"
        )
        self.label_result.pack()
        
        self.label_details = tk.Label(
            result_frame,
            text="",
            font=("Helvetica", 10),
            bg="#e8f5e9",
            fg="#555",
            justify=tk.CENTER
        )
        self.label_details.pack(pady=5)
        
        # Barra de progresso
        self.progress = ttk.Progressbar(
            test_frame,
            mode='indeterminate',
            length=300
        )
        
        # ==================== BATCH PROCESSING ====================
        batch_frame = tk.Frame(test_frame, bg="#e8f5e9")
        batch_frame.pack(pady=5)
        
        self.btn_batch = tk.Button(
            batch_frame,
            text="📁 Processar Pasta",
            command=self.process_folder,
            font=("Helvetica", 10),
            bg="#FF9800",
            fg="white",
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_batch.pack(side=tk.LEFT, padx=5)
        
        self.label_batch_status = tk.Label(
            batch_frame,
            text="",
            font=("Helvetica", 9),
            bg="#e8f5e9",
            fg="#555"
        )
        self.label_batch_status.pack(side=tk.LEFT, padx=5)
    
    def connect_to_server(self):
        """Conecta ao servidor"""
        self.client.server_url = self.server_entry.get().rstrip('/')
        self.save_config()
        
        self.btn_connect.config(state=tk.DISABLED, text="Verificando...")
        self.label_connection.config(text="⏳ Verificando conexão...", fg="#FF9800")
        
        # Executar em thread
        thread = threading.Thread(target=self._connect_thread, daemon=True)
        thread.start()
    
    def _connect_thread(self):
        """Thread de conexão"""
        success, data = self.client.check_health()
        
        if success:
            self.client.is_connected = True
            self.master.after(0, self._on_connected, data)
        else:
            self.client.is_connected = False
            self.master.after(0, self._on_connection_failed, data)
    
    def _on_connected(self, data):
        """Callback quando conectado"""
        self.label_connection.config(text="🟢 Conectado", fg="green")
        self.btn_connect.config(state=tk.NORMAL, text="🔌 Reconectar")
        
        # Habilitar controles
        self.btn_refresh_model_status.config(state=tk.NORMAL)
        
        # Verificar modelo atual
        if data.get('model_loaded'):
            model_name = data.get('model_name', 'Unknown')
            self.label_current_model.config(
                text=f"✅ {model_name}",
                fg="green"
            )
            self.label_warning.config(
                text="✅ Servidor online e modelo carregado - pronto para análise!",
                fg="green"
            )
            self.btn_select_image.config(state=tk.NORMAL)
            self.btn_batch.config(state=tk.NORMAL)
        else:
            self.label_current_model.config(
                text="⚠️ Nenhum modelo carregado no servidor",
                fg="#ff6f00"
            )
            self.label_warning.config(
                text="⚠️ Use a GUI de Treinamento para carregar um modelo",
                fg="#ff6f00"
            )
    
    def _on_connection_failed(self, error):
        """Callback quando falha conexão"""
        self.label_connection.config(text="🔴 Desconectado", fg="red")
        self.btn_connect.config(state=tk.NORMAL, text="🔌 Tentar Novamente")
        
        self.label_current_model.config(
            text="⚠️ Sem conexão com servidor",
            fg="red"
        )
        self.label_warning.config(
            text="⚠️ Não foi possível conectar - verifique se o servidor está rodando",
            fg="red"
        )
        
        # Desabilitar controles
        self.btn_refresh_model_status.config(state=tk.DISABLED)
        self.btn_select_image.config(state=tk.DISABLED)
        self.btn_batch.config(state=tk.DISABLED)
        
        messagebox.showerror(
            "Erro de Conexão",
            f"Não foi possível conectar ao servidor:\n\n{error}\n\n"
            "Verifique se o servidor está rodando."
        )
    
    def refresh_model_status(self):
        """Atualiza status do modelo no servidor"""
        if not self.client.is_connected:
            messagebox.showwarning("Aviso", "Conecte-se ao servidor primeiro!")
            return
        
        self.btn_refresh_model_status.config(state=tk.DISABLED, text="Verificando...")
        
        thread = threading.Thread(target=self._refresh_model_status_thread, daemon=True)
        thread.start()
    
    def _refresh_model_status_thread(self):
        """Thread para verificar status do modelo"""
        success, model_info = self.client.get_current_model()
        self.master.after(0, self._on_model_status_updated, success, model_info)
    
    def _on_model_status_updated(self, success, model_info):
        """Callback quando status do modelo é atualizado"""
        self.btn_refresh_model_status.config(state=tk.NORMAL, text="🔄 Atualizar Status")
        
        if success and model_info:
            model_name = model_info.get('name', 'Unknown')
            self.label_current_model.config(
                text=f"✅ {model_name}",
                fg="green"
            )
            self.label_warning.config(
                text="✅ Modelo carregado - pronto para análise!",
                fg="green"
            )
            self.btn_select_image.config(state=tk.NORMAL)
            self.btn_batch.config(state=tk.NORMAL)
        else:
            self.label_current_model.config(
                text="⚠️ Nenhum modelo carregado",
                fg="#ff6f00"
            )
            self.label_warning.config(
                text="⚠️ Use a GUI de Treinamento para carregar um modelo",
                fg="#ff6f00"
            )
            self.btn_select_image.config(state=tk.DISABLED)
            self.btn_batch.config(state=tk.DISABLED)
    
    def select_and_analyze(self):
        """Seleciona e analisa imagem"""
        if not self.client.is_connected:
            messagebox.showwarning("Aviso", "Conecte-se ao servidor primeiro!")
            return
        
        image_path = filedialog.askopenfilename(
            title="Escolha uma imagem para análise",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        
        if not image_path:
            return
        
        # Exibir imagem
        self._display_image(image_path)
        
        # Analisar
        self._analyze_image(image_path)
    
    def _display_image(self, image_path):
        """Exibe imagem selecionada"""
        try:
            img = Image.open(image_path)
            img.thumbnail((550, 550))
            img_tk = ImageTk.PhotoImage(img)
            
            self.image_label.config(image=img_tk, text="")
            self.image_label.image = img_tk
            
            self.label_result.config(text="Analisando...", fg="#FF9800")
            self.label_details.config(text="")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível exibir a imagem:\n{str(e)}")
    
    def _analyze_image(self, image_path):
        """Analisa imagem"""
        # Mostrar progresso
        self.progress.pack(pady=10)
        self.progress.start(10)
        
        # Desabilitar botões
        self.btn_select_image.config(state=tk.DISABLED)
        self.btn_batch.config(state=tk.DISABLED)
        
        thread = threading.Thread(
            target=self._analyze_image_thread,
            args=(image_path,),
            daemon=True
        )
        thread.start()
    
    def _analyze_image_thread(self, image_path):
        """Thread de análise"""
        success, data = self.client.predict_image(image_path)
        self.master.after(0, self._on_analysis_complete, success, data, image_path)
    
    def _on_analysis_complete(self, success, data, image_path):
        """Callback de análise completa"""
        # Parar progresso
        self.progress.stop()
        self.progress.pack_forget()
        
        # Habilitar botões
        self.btn_select_image.config(state=tk.NORMAL)
        self.btn_batch.config(state=tk.NORMAL)
        
        if success:
            if data['fire_detected']:
                self.label_result.config(text="🔥 INCÊNDIO DETECTADO!", fg="#d32f2f")
                details = (
                    f"Confiança: {data['confidence']:.2f}%\n"
                    f"⚠️ ALERTA: Fogo detectado na imagem!\n"
                    f"📁 {os.path.basename(image_path)}"
                )
                self.label_details.config(text=details, fg="#d32f2f")
            else:
                self.label_result.config(text="✅ NENHUM INCÊNDIO", fg="#2e7d32")
                details = (
                    f"Confiança: {data['confidence']:.2f}%\n"
                    f"✓ Imagem segura - Sem fogo detectado\n"
                    f"📁 {os.path.basename(image_path)}"
                )
                self.label_details.config(text=details, fg="#2e7d32")
        else:
            error_msg = data if isinstance(data, str) else data.get('error', 'Unknown error')
            self.label_result.config(text="❌ ERRO NA ANÁLISE", fg="#FF5722")
            self.label_details.config(text=f"Erro: {error_msg}", fg="#FF5722")
            messagebox.showerror("Erro", f"Erro ao analisar imagem:\n{error_msg}")
    
    def process_folder(self):
        """Processa pasta de imagens"""
        if not self.client.is_connected:
            messagebox.showwarning("Aviso", "Conecte-se ao servidor primeiro!")
            return
        
        folder = filedialog.askdirectory(title="Selecione a pasta com imagens")
        
        if not folder:
            return
        
        # Obter imagens
        extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
        images = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if f.lower().endswith(extensions)
        ]
        
        if not images:
            messagebox.showinfo("Aviso", "Nenhuma imagem encontrada na pasta.")
            return
        
        resposta = messagebox.askyesno(
            "Processar Pasta",
            f"Encontradas {len(images)} imagens.\n\nDeseja processar todas?"
        )
        
        if not resposta:
            return
        
        # Desabilitar botões
        self.btn_select_image.config(state=tk.DISABLED)
        self.btn_batch.config(state=tk.DISABLED)
        
        thread = threading.Thread(
            target=self._process_folder_thread,
            args=(images,),
            daemon=True
        )
        thread.start()
    
    def _process_folder_thread(self, images):
        """Thread para processar pasta de imagens usando batch otimizado"""
        self.master.after(0, self.label_batch_status.config, {'text': f"Processando {len(images)} imagens em batch..."})
        
        # Usar endpoint de batch para processar todas de uma vez (otimizado para GPU)
        success, data = self.client.predict_batch(images)
        
        if success:
            results = []
            for result in data.get('results', []):
                results.append((result['filename'], True, result))
            
            # Adicionar erros se houver
            for error in data.get('errors', []):
                results.append((error['filename'], False, {'error': error['error']}))
            
            self.master.after(0, self._on_batch_complete, results)
        else:
            # Fallback: processar uma por uma se batch falhar
            self.master.after(0, self.label_batch_status.config, {'text': 'Batch falhou, processando individualmente...'})
            self._process_folder_individual(images)
    
    def _process_folder_individual(self, images):
        """Fallback: processa imagens individualmente"""
        results = []
        total = len(images)
        
        for i, image_path in enumerate(images, 1):
            self.master.after(
                0,
                self.label_batch_status.config,
                {'text': f"Processando {i}/{total}..."}
            )
            
            success, data = self.client.predict_image(image_path)
            results.append((os.path.basename(image_path), success, data))
        
        self.master.after(0, self._on_batch_complete, results)
    
    def _on_batch_complete(self, results):
        """Callback de processamento em lote completo"""
        # Habilitar botões
        self.btn_select_image.config(state=tk.NORMAL)
        self.btn_batch.config(state=tk.NORMAL)
        self.label_batch_status.config(text="")
        
        # Calcular estatísticas
        total = len(results)
        success_count = sum(1 for _, s, _ in results if s)
        fire_count = sum(1 for _, s, d in results if s and d.get('fire_detected'))
        safe_count = success_count - fire_count
        error_count = total - success_count
        
        # Criar janela de resultado
        self._show_batch_results(results, total, success_count, fire_count, safe_count, error_count)
    
    def _show_batch_results(self, results, total, success, fires, safe, errors):
        """Mostra resultados do processamento em lote"""
        window = tk.Toplevel(self.master)
        window.title("Resultado do Processamento em Lote")
        window.geometry("750x550")
        window.configure(bg="#f0f0f0")
        
        # Título
        tk.Label(
            window,
            text="📊 Resumo do Processamento",
            font=("Helvetica", 14, "bold"),
            bg="#f0f0f0"
        ).pack(pady=10)
        
        # Estatísticas
        stats_frame = tk.Frame(window, bg="#e8f5e9", relief=tk.RIDGE, borderwidth=2)
        stats_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(stats_frame, text=f"Total de imagens: {total}", bg="#e8f5e9", font=("Helvetica", 11)).pack(pady=5)
        tk.Label(stats_frame, text=f"✓ Processadas: {success}", bg="#e8f5e9", font=("Helvetica", 11), fg="green").pack(pady=5)
        tk.Label(stats_frame, text=f"🔥 Fogo detectado: {fires}", bg="#e8f5e9", font=("Helvetica", 11, "bold"), fg="red").pack(pady=5)
        tk.Label(stats_frame, text=f"✅ Sem fogo: {safe}", bg="#e8f5e9", font=("Helvetica", 11), fg="green").pack(pady=5)
        tk.Label(stats_frame, text=f"❌ Erros: {errors}", bg="#e8f5e9", font=("Helvetica", 11), fg="orange").pack(pady=5)
        
        # Lista de resultados
        tk.Label(window, text="Detalhes:", font=("Helvetica", 11, "bold"), bg="#f0f0f0").pack(pady=5)
        
        list_frame = tk.Frame(window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Courier", 9))
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        
        # Adicionar resultados
        for filename, success, data in results:
            if success:
                if data.get('fire_detected'):
                    status = f"🔥 FOGO ({data['confidence']:.1f}%)"
                else:
                    status = f"✅ SEGURO ({data['confidence']:.1f}%)"
            else:
                status = "❌ ERRO"
            
            listbox.insert(tk.END, f"{filename:45s} {status}")
        
        # Botão fechar
        tk.Button(
            window,
            text="Fechar",
            command=window.destroy,
            font=("Helvetica", 10),
            bg="#2196F3",
            fg="white",
            cursor="hand2"
        ).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = ClientGUI(root)
    root.mainloop()
