import io
import logging
from concurrent import futures

import grpc
from PIL import Image
import numpy as np
import tensorflow as tf

import identyfire_pb2
import identyfire_pb2_grpc


class ModelServicer(identyfire_pb2_grpc.ModelServiceServicer):
    def __init__(self, model_path="./models/latest.h5", target_size=(150, 150)):
        self.model_path = model_path
        self.target_size = target_size
        self.model = None

        logging.info(f"Carregando modelo de inferência: {self.model_path}")
        try:
            self.model = tf.keras.models.load_model(self.model_path)
            logging.info("Modelo carregado com sucesso.")
        except Exception as e:
            logging.exception(f"Falha ao carregar o modelo: {e}")
            self.model = None

    def PredictImage(self, request, context):
        if self.model is None:
            context.set_code(grpc.StatusCode.FAILED_PRECONDITION)
            context.set_details("Modelo não carregado no servidor")
            return identyfire_pb2.PredictResponse()

        try:
            # Ler bytes da imagem
            img_bytes = request.image_bytes
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            img = img.resize(self.target_size)

            # Converter para array e normalizar
            img_array = np.array(img).astype("float32") / 255.0
            img_array = np.expand_dims(img_array, axis=0)  # batch dim

            # Predição
            preds = self.model.predict(img_array)
            # tentar obter um escalar de confiança
            try:
                confidence_raw = float(preds[0][0])
            except Exception:
                # fallback: tentar extrair primeira saída
                confidence_raw = float(np.ravel(preds)[0])

            # Classificação com threshold 0.5
            if confidence_raw > 0.5:
                label = "INCÊNDIO"
                # Confiança calibrada: quanto maior a saída, maior a confiança (0.5-1.0)
                confidence = confidence_raw
            else:
                label = "Nenhum incêndio"
                # Confiança calibrada: quanto menor a saída, maior a confiança (0.5-1.0)
                confidence = 1.0 - confidence_raw

            return identyfire_pb2.PredictResponse(label=label, confidence=confidence)

        except Exception as e:
            logging.exception(f"Erro ao processar a requisição de predição: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Erro interno no servidor: {e}")
            return identyfire_pb2.PredictResponse()


def serve(host="localhost", port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    identyfire_pb2_grpc.add_ModelServiceServicer_to_server(ModelServicer(), server)
    bind_addr = f"{host}:{port}"
    server.add_insecure_port(bind_addr)
    server.start()
    logging.info(f"Servidor de inferência gRPC rodando em {bind_addr}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logging.info("Shutdown solicitado por teclado. Parando o servidor...")
        server.stop(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    serve()
