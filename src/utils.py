import os
import json
import time
import io
import numpy as np
from datetime import datetime
from collections import deque
from PIL import Image

# Tenta importar TensorFlow (necessário apenas no servidor)
try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("Aviso: TensorFlow não encontrado. As funções de ML não funcionarão neste ambiente.")

# ============================================================================
# CLASSE DE EXCLUSÃO MÚTUA (REQ. SISTEMAS DISTRIBUÍDOS)
# ============================================================================

class MutexManager:
    """
    Gerenciador de Exclusão Mútua Centralizada.
    Garante que apenas um cliente utilize a GPU (Seção Crítica) por vez.
    """
    def __init__(self, timeout_seconds=30):
        self.locked = False
        self.owner_id = None
        self.queue = deque()  # Fila FIFO para garantir justiça (fairness)
        self.last_activity = 0
        self.TIMEOUT_SECONDS = timeout_seconds

    def request_access(self, client_id):
        """
        Tenta adquirir o lock.
        Retorna: (bool_granted, status_string, queue_position)
        """
        current_time = time.time()

        # 1. Segurança: Se o dono atual sumiu (crashou), libera o lock
        if self.locked and (current_time - self.last_activity > self.TIMEOUT_SECONDS):
            print(f"[MUTEX] Timeout detectado para {self.owner_id}. Liberando forçadamente.")
            self.force_release()

        # 2. Se ninguém está usando, concede acesso
        if not self.locked:
            # Mas só concede se a fila estiver vazia ou se ele for o primeiro da fila
            if not self.queue or self.queue[0] == client_id:
                if self.queue and self.queue[0] == client_id:
                    self.queue.popleft() # Remove da fila se estava lá
                
                self._grant_lock(client_id, current_time)
                return True, "GRANTED", 0
            
            # Se está livre mas tem gente na fila e não é ele, entra na fila
            if client_id not in self.queue:
                self.queue.append(client_id)
            return False, "QUEUED", list(self.queue).index(client_id)

        # 3. Se já é o dono (Reentrância / Renovação de lease)
        if self.owner_id == client_id:
            self.last_activity = current_time
            return True, "GRANTED", 0

        # 4. Se está ocupado por outro, coloca na fila
        if client_id not in self.queue:
            self.queue.append(client_id)
        
        return False, "QUEUED", list(self.queue).index(client_id)

    def release(self, client_id):
        """Libera o recurso se o solicitante for o dono"""
        if self.owner_id == client_id:
            print(f"[MUTEX] Lock liberado por {client_id}")
            self.locked = False
            self.owner_id = None
            return True
        return False

    def check_permission(self, client_id):
        """Verifica se o cliente tem permissão para operar agora"""
        if self.locked and self.owner_id == client_id:
            self.last_activity = time.time() # Renova atividade
            return True
        return False

    def force_release(self):
        """Liberação forçada (uso interno ou admin)"""
        self.locked = False
        self.owner_id = None

    def _grant_lock(self, client_id, timestamp):
        self.locked = True
        self.owner_id = client_id
        self.last_activity = timestamp
        print(f"[MUTEX] Lock CONCEDIDO para {client_id}")


# ============================================================================
# FUNÇÕES UTILITÁRIAS GERAIS E DE ML
# ============================================================================

def load_config(config_path='config.json'):
    """Carrega configuração ou cria padrão se não existir"""
    default_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 5000,
            "models_directory": "models",
            "max_image_size_mb": 10,
            "auto_load_default": False,
            "default_model": ""
        },
        "model": {
            "img_height": 150,
            "img_width": 150,
            "prediction_threshold": 0.5
        }
    }

    if not os.path.exists(config_path):
        try:
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
        except:
            pass
        return default_config
    
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except:
        return default_config

def format_timestamp():
    """Retorna timestamp formatado para logs"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def bytes_to_mb(size_in_bytes):
    """Converte bytes para megabytes"""
    return size_in_bytes / (1024 * 1024)

def validate_image_file(filename):
    """Verifica extensão do arquivo"""
    valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    return os.path.splitext(filename.lower())[1] in valid_extensions

def scan_models(models_dir):
    """Escaneia diretório por arquivos .h5"""
    if not os.path.exists(models_dir):
        os.makedirs(models_dir, exist_ok=True)
        return []
    
    models = []
    for f in os.listdir(models_dir):
        if f.endswith('.h5'):
            full_path = os.path.join(models_dir, f)
            size_mb = bytes_to_mb(os.path.getsize(full_path))
            models.append({
                'name': f,
                'path': full_path,
                'size': f"{size_mb:.2f} MB"
            })
    return models

def load_model(model_path):
    """Carrega modelo Keras do disco"""
    if not TF_AVAILABLE:
        return None, "TensorFlow not installed on server"
        
    try:
        # Configuração para evitar erros de GPU/DirectML se necessário
        # os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 
        model = tf.keras.models.load_model(model_path)
        return model, None
    except Exception as e:
        return None, str(e)

def get_model_info(model):
    """Extrai metadados básicos do modelo carregado"""
    try:
        input_shape = model.input_shape
        return {
            'input_shape': str(input_shape),
            'layers': len(model.layers),
            'output_shape': str(model.output_shape)
        }
    except:
        return {'info': 'Unavailable'}

def process_image_from_bytes(image_bytes, target_width=150, target_height=150):
    """
    Converte bytes brutos da imagem para formato numpy array pronto para o modelo.
    Retorna: (image_array, error_message)
    """
    if not TF_AVAILABLE:
        return None, "TensorFlow not installed"

    try:
        # Abrir imagem da memória
        img = Image.open(io.BytesIO(image_bytes))
        
        # Converter para RGB (caso seja PNG com transparência ou Grayscale)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionar
        img = img.resize((target_width, target_height))
        
        # Converter para array
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        
        # Normalizar (1./255) - IMPORTANTE: Deve bater com o ImageDataGenerator do treino
        img_array = img_array / 255.0
        
        # Adicionar dimensão do batch (1, 150, 150, 3)
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array, None
        
    except Exception as e:
        return None, str(e)

def make_prediction(model, processed_image, threshold=0.5):
    """Realiza a predição usando o modelo"""
    try:
        # Predição
        prediction = model.predict(processed_image, verbose=0)
        score = float(prediction[0][0])
        
        # Lógica binária
        is_fire = score > threshold
        
        # Confiança
        confidence = score if is_fire else 1 - score
        
        return {
            'success': True,
            'fire_detected': is_fire,
            'confidence': confidence * 100,
            'raw_score': score
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }