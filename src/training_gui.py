"""
IdentyFire Training GUI - Interface para treinamento de modelos
Responsabilidades:
- Treinar novos modelos
- Visualizar estatísticas de treinamento
- Carregar modelos automaticamente no servidor
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

from utils import load_config


class TrainingGUI:
    """Interface gráfica para treinamento de modelos"""
    
    def __init__(self, master):
        self.master = master
        self.config = load_config()
        self.training_process = None
        self.is_training = False
        
        # Construir URL do servidor - usar 127.0.0.1 se host for 0.0.0.0
        host = self.config['server']['host']
        if host == '0.0.0.0':
            host = '127.0.0.1'
        self.server_url = f"http://{host}:{self.config['server']['port']}"
        
        # Configuração da janela
        self.master.title("IdentyFire - Treinamento de Modelos")
        self.master.geometry("1200x850")
        self.master.configure(bg="#f0f0f0")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura a interface do usuário"""
        
        # Criar frame principal para treinamento (sem notebook)
        self.tab_training = tk.Frame(self.master, bg="#f0f0f0")
        self.tab_training.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.setup_training_tab()
    
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
            
            # Obter diretório raiz do projeto (pai de src/)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            main_py_path = os.path.join(script_dir, "main.py")
            
            if 'PYTHONPATH' not in env:
                env['PYTHONPATH'] = project_root
            env['TF_DIRECTML_PATH'] = ''
            
            cmd = [sys.executable, main_py_path, dataset_dir, model_name, str(epochs), str(batch_size)]
            
            self.log_training(f"Comando: {' '.join(cmd)}\n")
            self.log_training(f"Diretório de trabalho: {project_root}\n")
            
            start_time = datetime.now()
            
            self.training_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env,
                cwd=project_root
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
            # Obter diretório raiz do projeto
            script_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(script_dir)
            
            models_dir = self.config['server']['models_directory']
            
            # Se models_dir for relativo, torná-lo absoluto em relação ao project_root
            if not os.path.isabs(models_dir):
                models_dir = os.path.join(project_root, models_dir)
            
            os.makedirs(models_dir, exist_ok=True)
            
            source_files = [
                f"{model_name}.h5",
                f"{model_name}_best.h5",
                f"{model_name}_results.json",
                f"{model_name}_training_history.png",
                f"{model_name}_confusion_matrix.png"
            ]
            
            for filename in source_files:
                # Os arquivos são gerados no diretório raiz do projeto
                source_path = os.path.join(project_root, filename)
                if os.path.exists(source_path):
                    dest = os.path.join(models_dir, filename)
                    shutil.move(source_path, dest)
                    self.log_training(f"✓ Movido: {filename} -> {models_dir}")
        except Exception as e:
            self.log_training(f"⚠ Erro ao mover arquivos: {e}")
    
    def auto_load_model_to_server(self, model_name):
        """Carrega modelo automaticamente no servidor após treinamento"""
        try:
            model_file = f"{model_name}.h5"
            self.log_training(f"Tentando carregar modelo no servidor: {model_file}")
            self.log_training(f"URL do servidor: {self.server_url}/load_model")
            
            response = requests.post(
                f"{self.server_url}/load_model",
                json={'model_path': model_file},
                timeout=10
            )
            
            self.log_training(f"Status da resposta: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log_training(f"✓ Modelo carregado no servidor automaticamente")
                self.log_training(f"Resposta: {data}")
            else:
                try:
                    data = response.json()
                    self.log_training(f"⚠ Erro ao carregar no servidor: {data.get('message', 'Unknown')}")
                    self.log_training(f"Detalhes: {data}")
                except:
                    self.log_training(f"⚠ Erro ao carregar no servidor (status {response.status_code})")
                    self.log_training(f"Resposta: {response.text}")
        except requests.exceptions.RequestException as e:
            self.log_training(f"⚠ Erro de conexão com servidor: {str(e)}")
        except Exception as e:
            self.log_training(f"⚠ Erro inesperado ao carregar modelo: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = TrainingGUI(root)
    root.mainloop()
