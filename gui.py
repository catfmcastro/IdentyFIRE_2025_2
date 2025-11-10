import tkinter as tk
from tkinter import filedialog, Label, Button, Frame
from PIL import Image, ImageTk
import grpc
import identyfire_pb2
import identyfire_pb2_grpc


class IdentyFireGUI:
    def __init__(self, master):
        self.master = master

        # título e tamanho da janela
        self.master.title("Detector de Incêndios em Imagens de Satélite")
        self.master.geometry("600x700")

        # tamanho da imagem esperada (server fará o redimensionamento quando necessário)
        self.tamanho_imagem_modelo = (150, 150)

        # configurar canal e stub gRPC
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = identyfire_pb2_grpc.ModelServiceStub(channel)

        # frame principal
        main_frame = Frame(self.master, padx=10, pady=10)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # btn para selecionar imagem
        self.btn_selecionar = Button(
            main_frame,
            text="Selecionar Imagem de Satélite",
            command=self.previsao,
            font=("Helvetica", 12),
            bg="#2E8B57",
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

    # note: image processing is done on the server; GUI sends raw bytes
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

        # Ler bytes da imagem e enviar para o servidor de inferência via gRPC
        try:
            with open(caminho_arquivo, 'rb') as f:
                img_bytes = f.read()

            grpc_request = identyfire_pb2.PredictRequest(model_id="latest", image_bytes=img_bytes)
            response = self.stub.PredictImage(grpc_request)

            # Exibir resultado com base na resposta do servidor
            try:
                conf = float(response.confidence)
            except Exception:
                conf = 0.0

            label = response.label or "Desconhecido"
            if label.upper().startswith("INCÊNDIO") or label.upper().startswith("INCENDIO") or label == "INCÊNDIO":
                cor_texto = "red"
            else:
                cor_texto = "green"

            resultado_texto = f"{label} (Confiança: {conf:.2%})"
            self.label_resultado.config(text=resultado_texto, fg=cor_texto)

        except grpc.RpcError as e:
            self.label_resultado.config(text=f"Erro RPC: {e.code()} - {e.details()}", fg="orange")
        except Exception as e:
            self.label_resultado.config(text=f"Erro ao enviar imagem: {e}", fg="orange")


if __name__ == "__main__":
    root = tk.Tk()
    app = IdentyFireGUI(root)
    root.mainloop()
