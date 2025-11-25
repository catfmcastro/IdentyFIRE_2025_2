"""
IdentyFire Training GUI - Interface para treinamento e gerenciamento de modelos
Responsabilidades:
- Treinar novos modelos
- Gerenciar modelos existentes
- Carregar modelos no servidor
- Visualizar estatísticas de treinamento
- Editar parâmetros de treinamento
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import sys
import json
import threading
import subprocess
import requests
from datetime import datetime
import shutil

from utils import load_config, scan_models


class TrainingGUI:
    """Interface gráfica para treinamento e gerenciamento de modelos"""
    
    def __init__(self, master):
        self.master = master
        self.config = load_config()
        self.training_process = None
        self.is_training = False
        self.server_url = f"http://{self.config['server']['host']}:{self.config['server']['port']}"
        
        # Configuração da janela
        self.master.title("IdentyFire - Treinamento e Gerenciamento de Modelos")
        self.master.geometry("1200x900")
        self.master.configure(bg="#f0f0f0")
        
        self.setup_ui()
        self.refresh_models_list()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        
        # Criar notebook (abas)
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # ==================== ABA 1: TREINAMENTO ====================
        self.tab_training = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab_training, text="🎓 Treinamento")
        
        self.setup_training_tab()
        
        # ==================== ABA 2: GERENCIAMENTO ====================
        self.tab_management = tk.Frame(self.notebook, bg="#f0f0f0")
        self.notebook.add(self.tab_management, text="📦 Gerenciamento")
        
        self.setup_management_tab()
    
    def setup_training_tab(self):
        """Configura aba de treinamento"""
        
        # ==================== PARÂMETROS DE TREINAMENTO ====================
        params_frame = tk.LabelFrame(
            self.tab_training,
            text="⚙️ Parâmetros de Treinamento",
            font=("Helvetica", 12, "bold"),
            bg="#e3f2fd",
            padx=15,
            pady=15
        )
        params_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Grid de parâmetros
        row = 0
        
        # Dataset
        tk.Label(params_frame, text="Diretório do Dataset:", bg="#e3f2fd", font=("Helvetica", 10)).grid(
            row=row, column=0, sticky="w", pady=5, padx=5
        )
        self.dataset_entry = tk.Entry(params_frame, width=50, font=("Helvetica", 10))
        self.dataset_entry.insert(0, "C:/Dataset/archive")
        self.dataset_entry.grid(row=row, column=1, padx=5, pady=5)
        tk.Button(
            params_frame,
            text="📁 Procurar",
            command=self.browse_dataset,
            bg="#4CAF50",
            fg="white",
            cursor="hand2"
        ).grid(row=row, column=2, padx=5)
        row += 1
        
        # Nome do modelo
        tk.Label(params_frame, text="Nome do Modelo:", bg="#e3f2fd", font=("Helvetica", 10)).grid(
            row=row, column=0, sticky="w", pady=5, padx=5
        )
        self.model_name_entry = tk.Entry(params_frame, width=50, font=("Helvetica", 10))
        self.model_name_entry.insert(0, f"IdentyFIRE_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        self.model_name_entry.grid(row=row, column=1, padx=5, pady=5)
        row += 1
        
        # Épocas
        tk.Label(params_frame, text="Épocas:", bg="#e3f2fd", font=("Helvetica", 10)).grid(
            row=row, column=0, sticky="w", pady=5, padx=5
        )
        self.epochs_entry = tk.Entry(params_frame, width=20, font=("Helvetica", 10))
        self.epochs_entry.insert(0, "25")
        self.epochs_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        tk.Label(params_frame, text="Recomendado: 20-30", bg="#e3f2fd", font=("Helvetica", 9, "italic"), fg="#666").grid(
            row=row, column=2, sticky="w", padx=5
        )
        row += 1
        
        # Batch Size
        tk.Label(params_frame, text="Batch Size:", bg="#e3f2fd", font=("Helvetica", 10)).grid(
            row=row, column=0, sticky="w", pady=5, padx=5
        )
        self.batch_size_entry = tk.Entry(params_frame, width=20, font=("Helvetica", 10))
        self.batch_size_entry.insert(0, "32")
        self.batch_size_entry.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        tk.Label(params_frame, text="Recomendado: 16, 32 ou 64", bg="#e3f2fd", font=("Helvetica", 9, "italic"), fg="#666").grid(
            row=row, column=2, sticky="w", padx=5
        )
        row += 1
        
        # Opções
        options_frame = tk.Frame(params_frame, bg="#e3f2fd")
        options_frame.grid(row=row, column=0, columnspan=3, sticky="w", pady=10)
        
        self.auto_save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Salvar automaticamente na pasta de modelos",
            variable=self.auto_save_var,
            bg="#e3f2fd",
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        self.auto_load_server_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            options_frame,
            text="Carregar no servidor após treinar",
            variable=self.auto_load_server_var,
            bg="#e3f2fd",
            font=("Helvetica", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # ==================== CONTROLE DE TREINAMENTO ====================
        control_frame = tk.LabelFrame(
            self.tab_training,
            text="🚀 Controle",
            font=("Helvetica", 12, "bold"),
            bg="#e8f5e9",
            padx=15,
            pady=15
        )
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Botões
        btn_frame = tk.Frame(control_frame, bg="#e8f5e9")
        btn_frame.pack(pady=10)
        
        self.btn_start_training = tk.Button(
            btn_frame,
            text="▶️ Iniciar Treinamento",
            command=self.start_training,
            font=("Helvetica", 11, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2,
            width=20,
            cursor="hand2"
        )
        self.btn_start_training.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop_training = tk.Button(
            btn_frame,
            text="⏹️ Parar Treinamento",
            command=self.stop_training,
            font=("Helvetica", 11, "bold"),
            bg="#f44336",
            fg="white",
            height=2,
            width=20,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_stop_training.pack(side=tk.LEFT, padx=5)
        
        # Status
        self.label_training_status = tk.Label(
            control_frame,
            text="⚪ Aguardando",
            font=("Helvetica", 12, "bold"),
            bg="#e8f5e9",
            fg="#666"
        )
        self.label_training_status.pack(pady=5)
        
        # ==================== ESTATÍSTICAS ====================
        stats_frame = tk.LabelFrame(
            self.tab_training,
            text="📊 Estatísticas em Tempo Real",
            font=("Helvetica", 12, "bold"),
            bg="#fff3e0",
            padx=15,
            pady=15
        )
        stats_frame.pack(fill=tk.X, padx=10, pady=10)
        
        stats_grid = tk.Frame(stats_frame, bg="#fff3e0")
        stats_grid.pack(fill=tk.X)
        
        self.label_current_epoch = tk.Label(
            stats_grid,
            text="Época: -/-",
            font=("Helvetica", 10),
            bg="#fff3e0"
        )
        self.label_current_epoch.grid(row=0, column=0, sticky="w", padx=10, pady=3)
        
        self.label_train_acc = tk.Label(
            stats_grid,
            text="Acurácia Treino: -",
            font=("Helvetica", 10),
            bg="#fff3e0"
        )
        self.label_train_acc.grid(row=0, column=1, sticky="w", padx=10, pady=3)
        
        self.label_val_acc = tk.Label(
            stats_grid,
            text="Acurácia Validação: -",
            font=("Helvetica", 10),
            bg="#fff3e0"
        )
        self.label_val_acc.grid(row=0, column=2, sticky="w", padx=10, pady=3)
        
        self.label_train_loss = tk.Label(
            stats_grid,
            text="Loss Treino: -",
            font=("Helvetica", 10),
            bg="#fff3e0"
        )
        self.label_train_loss.grid(row=1, column=0, sticky="w", padx=10, pady=3)
        
        self.label_val_loss = tk.Label(
            stats_grid,
            text="Loss Validação: -",
            font=("Helvetica", 10),
            bg="#fff3e0"
        )
        self.label_val_loss.grid(row=1, column=1, sticky="w", padx=10, pady=3)
        
        self.label_elapsed_time = tk.Label(
            stats_grid,
            text="Tempo Decorrido: 0s",
            font=("Helvetica", 10),
            bg="#fff3e0"
        )
        self.label_elapsed_time.grid(row=1, column=2, sticky="w", padx=10, pady=3)
        
        # Barra de progresso
        self.progress_training = ttk.Progressbar(
            stats_frame,
            mode='determinate',
            length=800
        )
        self.progress_training.pack(pady=10, fill=tk.X)
        
        # ==================== CONSOLE ====================
        console_frame = tk.LabelFrame(
            self.tab_training,
            text="📋 Console de Treinamento",
            font=("Helvetica", 12, "bold"),
            bg="#f0f0f0",
            padx=10,
            pady=10
        )
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.console_training = scrolledtext.ScrolledText(
            console_frame,
            height=15,
            width=140,
            font=("Courier", 9),
            bg="#1e1e1e",
            fg="#00ff00",
            wrap=tk.WORD
        )
        self.console_training.pack(fill=tk.BOTH, expand=True)
        
        tk.Button(
            console_frame,
            text="🗑️ Limpar Console",
            command=lambda: self.console_training.delete(1.0, tk.END),
            font=("Helvetica", 9),
            bg="#757575",
            fg="white",
            cursor="hand2"
        ).pack(pady=5)
    
    def setup_management_tab(self):
        """Configura aba de gerenciamento"""
        
        # ==================== LISTA DE MODELOS ====================
        list_frame = tk.LabelFrame(
            self.tab_management,
            text="📦 Modelos Disponíveis",
            font=("Helvetica", 12, "bold"),
            bg="#e3f2fd",
            padx=15,
            pady=15
        )
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Botões de ação
        btn_frame = tk.Frame(list_frame, bg="#e3f2fd")
        btn_frame.pack(fill=tk.X, pady=5)
        
        tk.Button(
            btn_frame,
            text="🔄 Atualizar Lista",
            command=self.refresh_models_list,
            font=("Helvetica", 10),
            bg="#2196F3",
            fg="white",
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="📂 Abrir Pasta de Modelos",
            command=self.open_models_folder,
            font=("Helvetica", 10),
            bg="#4CAF50",
            fg="white",
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # Tabela de modelos
        table_frame = tk.Frame(list_frame, bg="#e3f2fd")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Scrollbars
        scrollbar_y = tk.Scrollbar(table_frame)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        scrollbar_x = tk.Scrollbar(table_frame, orient=tk.HORIZONTAL)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview
        self.models_tree = ttk.Treeview(
            table_frame,
            columns=('name', 'size', 'modified', 'status'),
            show='headings',
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        
        self.models_tree.heading('name', text='Nome do Modelo')
        self.models_tree.heading('size', text='Tamanho')
        self.models_tree.heading('modified', text='Modificado')
        self.models_tree.heading('status', text='Status')
        
        self.models_tree.column('name', width=300)
        self.models_tree.column('size', width=100)
        self.models_tree.column('modified', width=150)
        self.models_tree.column('status', width=150)
        
        self.models_tree.pack(fill=tk.BOTH, expand=True)
        
        scrollbar_y.config(command=self.models_tree.yview)
        scrollbar_x.config(command=self.models_tree.xview)
        
        # ==================== AÇÕES DO MODELO ====================
        actions_frame = tk.LabelFrame(
            self.tab_management,
            text="🔧 Ações",
            font=("Helvetica", 12, "bold"),
            bg="#e8f5e9",
            padx=15,
            pady=15
        )
        actions_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Informações do modelo selecionado
        self.label_selected_model = tk.Label(
            actions_frame,
            text="Nenhum modelo selecionado",
            font=("Helvetica", 10, "italic"),
            bg="#e8f5e9",
            fg="#666"
        )
        self.label_selected_model.pack(pady=5)
        
        # Botões de ação
        actions_btn_frame = tk.Frame(actions_frame, bg="#e8f5e9")
        actions_btn_frame.pack(pady=10)
        
        self.btn_load_to_server = tk.Button(
            actions_btn_frame,
            text="🚀 Carregar no Servidor",
            command=self.load_model_to_server,
            font=("Helvetica", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            height=2,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_load_to_server.pack(side=tk.LEFT, padx=5)
        
        self.btn_delete_model = tk.Button(
            actions_btn_frame,
            text="🗑️ Deletar Modelo",
            command=self.delete_model,
            font=("Helvetica", 10),
            bg="#f44336",
            fg="white",
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_delete_model.pack(side=tk.LEFT, padx=5)
        
        self.btn_rename_model = tk.Button(
            actions_btn_frame,
            text="✏️ Renomear",
            command=self.rename_model,
            font=("Helvetica", 10),
            bg="#FF9800",
            fg="white",
            cursor="hand2",
            state=tk.DISABLED
        )
        self.btn_rename_model.pack(side=tk.LEFT, padx=5)
        
        # Status do servidor
        server_frame = tk.LabelFrame(
            actions_frame,
            text="🌐 Servidor",
            bg="#e8f5e9",
            font=("Helvetica", 10, "bold")
        )
        server_frame.pack(fill=tk.X, pady=10)
        
        self.label_server_status = tk.Label(
            server_frame,
            text="Status: Verificando...",
            font=("Helvetica", 10),
            bg="#e8f5e9"
        )
        self.label_server_status.pack(pady=5)
        
        tk.Button(
            server_frame,
            text="🔄 Verificar Servidor",
            command=self.check_server_status,
            font=("Helvetica", 9),
            bg="#2196F3",
            fg="white",
            cursor="hand2"
        ).pack(pady=5)
        
        # Bind de seleção
        self.models_tree.bind('<<TreeviewSelect>>', self.on_model_select)
        
        # Verificar servidor automaticamente
        self.check_server_status()
    
    # ==================== MÉTODOS DE TREINAMENTO ====================
    
    def browse_dataset(self):
        """Abre diálogo para selecionar dataset"""
        folder = filedialog.askdirectory(title="Selecione o diretório do dataset")
        if folder:
            self.dataset_entry.delete(0, tk.END)
            self.dataset_entry.insert(0, folder)
    
    def log_training(self, message):
        """Adiciona mensagem ao console de treinamento"""
        self.console_training.insert(tk.END, message + "\n")
        self.console_training.see(tk.END)
        self.console_training.update()
        
        # Parsear estatísticas se possível
        self.parse_training_stats(message)
    
    def parse_training_stats(self, message):
        """Parseia estatísticas da mensagem de treinamento"""
        try:
            # Parsear época
            if "Epoch " in message and "/" in message:
                parts = message.split("Epoch ")[1].split("/")
                if len(parts) >= 2:
                    current = parts[0].strip()
                    total = parts[1].split()[0].strip()
                    self.label_current_epoch.config(text=f"Época: {current}/{total}")
                    
                    # Atualizar barra de progresso
                    try:
                        progress = (int(current) / int(total)) * 100
                        self.progress_training['value'] = progress
                    except:
                        pass
            
            # Parsear acurácia e loss
            if "accuracy:" in message.lower():
                parts = message.split("-")
                for part in parts:
                    part = part.strip()
                    if "accuracy:" in part.lower():
                        acc = part.split(":")[1].strip().split()[0]
                        self.label_train_acc.config(text=f"Acurácia Treino: {acc}")
                    elif "loss:" in part.lower():
                        loss = part.split(":")[1].strip().split()[0]
                        self.label_train_loss.config(text=f"Loss Treino: {loss}")
                    elif "val_accuracy:" in part.lower():
                        val_acc = part.split(":")[1].strip().split()[0]
                        self.label_val_acc.config(text=f"Acurácia Validação: {val_acc}")
                    elif "val_loss:" in part.lower():
                        val_loss = part.split(":")[1].strip().split()[0]
                        self.label_val_loss.config(text=f"Loss Validação: {val_loss}")
        except:
            pass
    
    def start_training(self):
        """Inicia o treinamento"""
        dataset_dir = self.dataset_entry.get()
        model_name = self.model_name_entry.get()
        
        try:
            epochs = int(self.epochs_entry.get())
            batch_size = int(self.batch_size_entry.get())
        except ValueError:
            messagebox.showerror("Erro", "Épocas e Batch Size devem ser números inteiros!")
            return
        
        if not os.path.exists(dataset_dir):
            messagebox.showerror("Erro", f"Diretório não encontrado: {dataset_dir}")
            return
        
        if not model_name:
            messagebox.showerror("Erro", "Por favor, forneça um nome para o modelo!")
            return
        
        # Confirmar
        resposta = messagebox.askyesno(
            "Confirmar Treinamento",
            f"Iniciar treinamento com os seguintes parâmetros?\n\n"
            f"Dataset: {dataset_dir}\n"
            f"Modelo: {model_name}\n"
            f"Épocas: {epochs}\n"
            f"Batch Size: {batch_size}"
        )
        
        if not resposta:
            return
        
        self.is_training = True
        self.console_training.delete(1.0, tk.END)
        self.label_training_status.config(text="🟢 Treinando...", fg="green")
        self.btn_start_training.config(state=tk.DISABLED)
        self.btn_stop_training.config(state=tk.NORMAL)
        self.progress_training['value'] = 0
        
        # Resetar labels
        self.label_current_epoch.config(text="Época: -/-")
        self.label_train_acc.config(text="Acurácia Treino: -")
        self.label_val_acc.config(text="Acurácia Validação: -")
        self.label_train_loss.config(text="Loss Treino: -")
        self.label_val_loss.config(text="Loss Validação: -")
        
        # Iniciar thread de treinamento
        thread = threading.Thread(
            target=self.run_training_process,
            args=(dataset_dir, model_name, epochs, batch_size),
            daemon=True
        )
        thread.start()
    
    def run_training_process(self, dataset_dir, model_name, epochs, batch_size):
        """Executa o processo de treinamento"""
        try:
            self.log_training("=" * 80)
            self.log_training("INICIANDO TREINAMENTO")
            self.log_training("=" * 80)
            
            env = os.environ.copy()
            if 'PYTHONPATH' not in env:
                env['PYTHONPATH'] = os.getcwd()
            env['TF_DIRECTML_PATH'] = ''
            
            cmd = [sys.executable, "main.py", dataset_dir, model_name, str(epochs), str(batch_size)]
            
            self.log_training(f"Comando: {' '.join(cmd)}\n")
            
            start_time = datetime.now()
            
            self.training_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                cwd=os.getcwd()
            )
            
            # Ler saída em tempo real
            for line in self.training_process.stdout:
                if not self.is_training:
                    break
                self.master.after(0, self.log_training, line.strip())
                
                # Atualizar tempo decorrido
                elapsed = (datetime.now() - start_time).total_seconds()
                minutes = int(elapsed // 60)
                seconds = int(elapsed % 60)
                self.master.after(0, self.label_elapsed_time.config, {'text': f"Tempo: {minutes}m {seconds}s"})
            
            self.training_process.wait()
            
            if self.training_process.returncode == 0 and self.is_training:
                self.master.after(0, self.on_training_complete, model_name)
            elif not self.is_training:
                self.master.after(0, self.on_training_stopped)
            else:
                self.master.after(0, self.on_training_error)
                
        except Exception as e:
            self.master.after(0, self.log_training, f"\n✗ ERRO: {str(e)}")
            self.master.after(0, self.on_training_error)
    
    def stop_training(self):
        """Para o treinamento"""
        if self.training_process:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Tem certeza que deseja parar o treinamento?\n\nO progresso será perdido."
            )
            
            if resposta:
                self.is_training = False
                self.training_process.terminate()
                self.log_training("\n⏹️ TREINAMENTO INTERROMPIDO PELO USUÁRIO")
    
    def on_training_complete(self, model_name):
        """Callback quando treinamento completa"""
        self.log_training("\n✅ TREINAMENTO CONCLUÍDO COM SUCESSO!")
        self.label_training_status.config(text="✅ Concluído", fg="green")
        self.btn_start_training.config(state=tk.NORMAL)
        self.btn_stop_training.config(state=tk.DISABLED)
        self.progress_training['value'] = 100
        
        # Mover modelo para pasta de modelos se opção marcada
        if self.auto_save_var.get():
            self.move_model_to_folder(model_name)
        
        # Carregar no servidor se opção marcada
        if self.auto_load_server_var.get():
            self.auto_load_model_to_server(model_name)
        
        self.refresh_models_list()
        messagebox.showinfo("Sucesso", f"Modelo '{model_name}.h5' treinado com sucesso!")
    
    def on_training_stopped(self):
        """Callback quando treinamento é parado"""
        self.label_training_status.config(text="⚪ Parado", fg="#666")
        self.btn_start_training.config(state=tk.NORMAL)
        self.btn_stop_training.config(state=tk.DISABLED)
    
    def on_training_error(self):
        """Callback quando há erro no treinamento"""
        self.log_training("\n❌ ERRO NO TREINAMENTO")
        self.label_training_status.config(text="❌ Erro", fg="red")
        self.btn_start_training.config(state=tk.NORMAL)
        self.btn_stop_training.config(state=tk.DISABLED)
        self.is_training = False
        messagebox.showerror("Erro", "Ocorreu um erro durante o treinamento. Verifique o console.")
    
    def move_model_to_folder(self, model_name):
        """Move modelo treinado para pasta de modelos"""
        try:
            models_dir = self.config['server']['models_directory']
            os.makedirs(models_dir, exist_ok=True)
            
            source_files = [
                f"{model_name}.h5",
                f"{model_name}_best.h5",
                f"{model_name}_results.json",
                f"{model_name}_training_history.png",
                f"{model_name}_confusion_matrix.png"
            ]
            
            for filename in source_files:
                if os.path.exists(filename):
                    dest = os.path.join(models_dir, filename)
                    shutil.move(filename, dest)
                    self.log_training(f"✓ Movido: {filename} -> {models_dir}")
        except Exception as e:
            self.log_training(f"⚠ Erro ao mover arquivos: {e}")
    
    def auto_load_model_to_server(self, model_name):
        """Carrega modelo automaticamente no servidor após treinamento"""
        try:
            model_file = f"{model_name}.h5"
            response = requests.post(
                f"{self.server_url}/load_model",
                json={'model_path': model_file},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_training(f"✓ Modelo carregado no servidor automaticamente")
            else:
                self.log_training(f"⚠ Não foi possível carregar no servidor automaticamente")
        except:
            self.log_training(f"⚠ Servidor não disponível para carregamento automático")
    
    # ==================== MÉTODOS DE GERENCIAMENTO ====================
    
    def refresh_models_list(self):
        """Atualiza lista de modelos"""
        models_dir = self.config['server']['models_directory']
        models = scan_models(models_dir)
        
        # Limpar tabela
        for item in self.models_tree.get_children():
            self.models_tree.delete(item)
        
        # Adicionar modelos
        for model in models:
            status = "Disponível"
            self.models_tree.insert(
                '',
                tk.END,
                values=(
                    model['name'],
                    f"{model['size_mb']} MB",
                    model['modified'],
                    status
                )
            )
    
    def on_model_select(self, event):
        """Callback quando modelo é selecionado"""
        selection = self.models_tree.selection()
        if selection:
            item = self.models_tree.item(selection[0])
            model_name = item['values'][0]
            
            self.label_selected_model.config(
                text=f"Selecionado: {model_name}",
                fg="green"
            )
            
            self.btn_load_to_server.config(state=tk.NORMAL)
            self.btn_delete_model.config(state=tk.NORMAL)
            self.btn_rename_model.config(state=tk.NORMAL)
        else:
            self.label_selected_model.config(
                text="Nenhum modelo selecionado",
                fg="#666"
            )
            
            self.btn_load_to_server.config(state=tk.DISABLED)
            self.btn_delete_model.config(state=tk.DISABLED)
            self.btn_rename_model.config(state=tk.DISABLED)
    
    def load_model_to_server(self):
        """Carrega modelo selecionado no servidor"""
        selection = self.models_tree.selection()
        if not selection:
            return
        
        item = self.models_tree.item(selection[0])
        model_name = item['values'][0]
        
        resposta = messagebox.askyesno(
            "Confirmar",
            f"Carregar o modelo '{model_name}' no servidor?"
        )
        
        if not resposta:
            return
        
        try:
            response = requests.post(
                f"{self.server_url}/load_model",
                json={'model_path': model_name},
                timeout=10
            )
            
            if response.status_code == 200:
                messagebox.showinfo("Sucesso", f"Modelo '{model_name}' carregado no servidor!")
                self.check_server_status()
            else:
                data = response.json()
                messagebox.showerror("Erro", f"Não foi possível carregar o modelo:\n{data.get('message', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro de Conexão", f"Não foi possível conectar ao servidor:\n{str(e)}")
    
    def delete_model(self):
        """Deleta modelo selecionado"""
        selection = self.models_tree.selection()
        if not selection:
            return
        
        item = self.models_tree.item(selection[0])
        model_name = item['values'][0]
        
        resposta = messagebox.askyesno(
            "Confirmar Exclusão",
            f"Tem certeza que deseja deletar o modelo '{model_name}'?\n\nEsta ação não pode ser desfeita!"
        )
        
        if not resposta:
            return
        
        try:
            models_dir = self.config['server']['models_directory']
            model_path = os.path.join(models_dir, model_name)
            
            if os.path.exists(model_path):
                os.remove(model_path)
                
                # Remover arquivos relacionados
                base_name = model_name.replace('.h5', '')
                related_files = [
                    f"{base_name}_results.json",
                    f"{base_name}_training_history.png",
                    f"{base_name}_confusion_matrix.png"
                ]
                
                for related_file in related_files:
                    related_path = os.path.join(models_dir, related_file)
                    if os.path.exists(related_path):
                        os.remove(related_path)
                
                messagebox.showinfo("Sucesso", f"Modelo '{model_name}' deletado!")
                self.refresh_models_list()
            else:
                messagebox.showerror("Erro", f"Arquivo não encontrado: {model_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível deletar o modelo:\n{str(e)}")
    
    def rename_model(self):
        """Renomeia modelo selecionado"""
        selection = self.models_tree.selection()
        if not selection:
            return
        
        item = self.models_tree.item(selection[0])
        old_name = item['values'][0]
        
        # Diálogo para novo nome
        dialog = tk.Toplevel(self.master)
        dialog.title("Renomear Modelo")
        dialog.geometry("400x150")
        dialog.configure(bg="#f0f0f0")
        
        tk.Label(dialog, text="Novo nome:", bg="#f0f0f0", font=("Helvetica", 10)).pack(pady=10)
        
        new_name_entry = tk.Entry(dialog, width=40, font=("Helvetica", 10))
        new_name_entry.insert(0, old_name.replace('.h5', ''))
        new_name_entry.pack(pady=5)
        
        def do_rename():
            new_name = new_name_entry.get().strip()
            if not new_name:
                messagebox.showwarning("Aviso", "Nome não pode ser vazio!")
                return
            
            if not new_name.endswith('.h5'):
                new_name += '.h5'
            
            if new_name == old_name:
                dialog.destroy()
                return
            
            try:
                models_dir = self.config['server']['models_directory']
                old_path = os.path.join(models_dir, old_name)
                new_path = os.path.join(models_dir, new_name)
                
                if os.path.exists(new_path):
                    messagebox.showerror("Erro", f"Já existe um modelo com o nome '{new_name}'!")
                    return
                
                os.rename(old_path, new_path)
                
                # Renomear arquivos relacionados
                old_base = old_name.replace('.h5', '')
                new_base = new_name.replace('.h5', '')
                
                related_files = [
                    ('_results.json', '_results.json'),
                    ('_training_history.png', '_training_history.png'),
                    ('_confusion_matrix.png', '_confusion_matrix.png')
                ]
                
                for old_suffix, new_suffix in related_files:
                    old_related = os.path.join(models_dir, f"{old_base}{old_suffix}")
                    new_related = os.path.join(models_dir, f"{new_base}{new_suffix}")
                    if os.path.exists(old_related):
                        os.rename(old_related, new_related)
                
                messagebox.showinfo("Sucesso", f"Modelo renomeado para '{new_name}'!")
                dialog.destroy()
                self.refresh_models_list()
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível renomear:\n{str(e)}")
        
        tk.Button(
            dialog,
            text="✅ Renomear",
            command=do_rename,
            font=("Helvetica", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            cursor="hand2"
        ).pack(pady=10)
    
    def open_models_folder(self):
        """Abre pasta de modelos no explorador"""
        models_dir = self.config['server']['models_directory']
        if os.path.exists(models_dir):
            os.startfile(models_dir)
        else:
            messagebox.showerror("Erro", f"Pasta não encontrada: {models_dir}")
    
    def check_server_status(self):
        """Verifica status do servidor"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=3)
            if response.status_code == 200:
                data = response.json()
                model_name = data.get('model_name', 'Nenhum')
                self.label_server_status.config(
                    text=f"Status: 🟢 Online | Modelo: {model_name}",
                    fg="green"
                )
            else:
                self.label_server_status.config(
                    text="Status: 🔴 Erro no servidor",
                    fg="red"
                )
        except:
            self.label_server_status.config(
                text="Status: 🔴 Offline",
                fg="red"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = TrainingGUI(root)
    root.mainloop()
