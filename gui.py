import tkinter as tk
from tkinter import filedialog, Label, Button, Frame
from PIL import Image, ImageTk
import numpy as np
import tensorflow as tf

def carregar_modelo(caminho_modelo):
    print(f"Carregando modelo {caminho_modelo}...")
    try:
        modelo = tf.keras.models.load_model(caminho_modelo)
        print("Modelo carregado com sucesso.")
        return modelo
    except Exception as e:
        print(
            f"ERRO: Não foi possível carregar o modelo. Verifique o caminho. Erro: {e}"
        )
        return None

class IdentyFireGUI:
    def __init__(self, master, modelo):
        self.master = master
        self.modelo = modelo

        # título e tamanho da janela
        self.master.title("Detector de Incêndios em Imagens de Satélite")
        self.master.geometry("600x700")

        # tamanho da imagem esperada
        self.tamanho_imagem_modelo = (150, 150)

        # frame principal
        main_frame = Frame(self.master, padx=10, pady=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # btn para selecioanr imagem
        self.btn_selecionar = Button(
            main_frame,
            text="Selecionar Imagem de Satélite",
            command=self.selecionar_e_prever,
            font=("Helvetica", 12),
            bg="#2E8B57",  # Verde mar
            fg="white",
            relief=tk.RAISED,
            borderwidth=2,
        )
        self.btn_selecionar.pack(pady=10)

        # painel que exibe a imagem selecionada
        self.painel_imagem = Label(
            main_frame, text="Nenhuma imagem selecionada", font=("Helvetica", 10)
        )
        self.painel_imagem.pack(pady=10)

        # LABEL DO RESULTADO
        self.label_resultado = Label(
            main_frame,
            text="Resultado: Aguardando imagem...",
            font=("Helvetica", 14, "bold"),
        )
        self.label_resultado.pack(pady=20)

    def processar_imagem(self, caminho_imagem):

        try:
            # abre imagem, redimensiona e converte para array
            img = Image.open(caminho_imagem).resize(self.tamanho_imagem_modelo)
            img_array = tf.keras.preprocessing.image.img_to_array(img)

            # normaliza os pixels
            img_array /= 255.0

            # dimensão extra para representar o batch da imagem
            img_array = np.expand_dims(img_array, axis=0)

            return img_array
        except Exception as e:
            print(f"ERRO ao processar a imagem: {e}")
            return None

    def previsao(self):

        # abre explorador de arquivos
        caminho_arquivo = filedialog.askopenfilename(
            title="Escolha uma imagem",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp")],
        )

        if not caminho_arquivo:
            return

        # exibir a imagem na GUI
        img_visualizacao = Image.open(caminho_arquivo)
        img_visualizacao.thumbnail((500, 500))
        img_tk = ImageTk.PhotoImage(img_visualizacao)

        self.painel_imagem.config(image=img_tk)
        self.painel_imagem.image = img_tk  # guarda uma referência para a imagem

        # processar imagem
        imagem_processada = self.processar_imagem(caminho_arquivo)

        if imagem_processada is None or self.modelo is None:
            self.label_resultado.config(
                text="Erro ao processar ou carregar modelo.", fg="orange"
            )
            return

        # predição propriamente dita
        try:
            predicao = self.modelo.predict(imagem_processada)[0][
                0
            ]

            #interpretar e mostrar o resultado
            # threshold 0.5
            # se saída > 0.5, entende-se classe positiva (incêndio)
            if predicao > 0.5:
                resultado_texto = f"INCÊNDIO DETECTADO (Confiança: {predicao:.2%})"
                cor_texto = "red"
            else:
                resultado_texto = (
                    f"Nenhum incêndio detectado (Confiança: {1-predicao:.2%})"
                )
                cor_texto = "green"

            self.label_resultado.config(text=resultado_texto, fg=cor_texto)

        except Exception as e:
            self.label_resultado.config(text=f"Erro na predição: {e}", fg="orange")


if __name__ == "__main__":

    # alterar com base no modelo
    CAMINHO_DO_MODELO = "IdentyFIRE1_Parallel.h5"

    # carrega modelo
    modelo_carregado = carregar_modelo(CAMINHO_DO_MODELO)

    # inicia GUI
    root = tk.Tk()
    app = IdentyFireGUI(root, modelo_carregado)
    root.mainloop()
