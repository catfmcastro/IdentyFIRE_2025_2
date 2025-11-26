"""
IdentyFire Utils - Funções auxiliares para processamento de imagens e gerenciamento de modelos
"""

import os
import io
import json
from PIL import Image
import numpy as np
import tensorflow as tf
from datetime import datetime


def load_config(config_path="config.json"):
    """Carrega arquivo de configuração"""
    try:
        # Se o caminho não for absoluto, buscar no diretório raiz do projeto
        if not os.path.isabs(config_path):
            # Obter diretório onde utils.py está (src/)
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Subir um nível para obter o diretório raiz do projeto
            project_root = os.path.dirname(script_dir)
            config_path = os.path.join(project_root, config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠ Arquivo de configuração não encontrado: {config_path}")
        return get_default_config()
    except json.JSONDecodeError as e:
        print(f"⚠ Erro ao ler configuração: {e}")
        return get_default_config()


def get_default_config():
    """Retorna configuração padrão"""
    return {
        "server": {
            "host": "127.0.0.1",
            "port": 5000,
            "models_directory": "./models",
            "default_model": "best_model.h5",
            "auto_load_default": True,
            "max_image_size_mb": 10
        },
        "model": {
            "img_height": 150,
            "img_width": 150,
            "prediction_threshold": 0.5
        }
    }


def scan_models(models_dir="./models"):
    """
    Escaneia diretório de modelos e retorna lista de arquivos .h5
    
    Returns:
        list: Lista de dicionários com informações dos modelos
    """
    models = []
    
    # Se o caminho não for absoluto, torná-lo relativo ao diretório raiz do projeto
    if not os.path.isabs(models_dir):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        models_dir = os.path.join(project_root, models_dir)
    
    if not os.path.exists(models_dir):
        print(f"⚠ Diretório de modelos não encontrado: {models_dir}")
        os.makedirs(models_dir, exist_ok=True)
        return models
    
    try:
        for filename in os.listdir(models_dir):
            if filename.lower().endswith('.h5'):
                full_path = os.path.abspath(os.path.join(models_dir, filename))
                file_size = os.path.getsize(full_path)
                modified_time = os.path.getmtime(full_path)
                
                models.append({
                    'name': filename,
                    'path': full_path,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Ordenar por data de modificação (mais recente primeiro)
        models.sort(key=lambda x: x['modified'], reverse=True)
        
    except Exception as e:
        print(f"⚠ Erro ao escanear modelos: {e}")
    
    return models


def load_model(model_path):
    """
    Carrega um modelo TensorFlow/Keras
    
    Args:
        model_path (str): Caminho para o arquivo .h5
        
    Returns:
        tuple: (modelo, erro) - modelo carregado ou None, mensagem de erro ou None
    """
    try:
        if not os.path.exists(model_path):
            return None, f"Arquivo não encontrado: {model_path}"
        
        # Tentar carregar normalmente primeiro
        try:
            model = tf.keras.models.load_model(model_path)
            return model, None
        except (TypeError, ValueError) as e:
            # Se falhar com erro de 'batch_shape', tentar com compile=False
            if 'batch_shape' in str(e) or 'Unrecognized keyword' in str(e):
                print(f"⚠ Modelo legado detectado, tentando carregar com compile=False...")
                model = tf.keras.models.load_model(model_path, compile=False)
                
                # Recompilar o modelo com configuração padrão
                model.compile(
                    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                    loss='binary_crossentropy',
                    metrics=['accuracy']
                )
                print(f"✓ Modelo legado carregado e recompilado com sucesso")
                return model, None
            else:
                raise
        
    except Exception as e:
        return None, f"Erro ao carregar modelo: {str(e)}"


def process_image_from_bytes(image_bytes, img_width=150, img_height=150):
    """
    Processa imagem a partir de bytes para predição
    
    Args:
        image_bytes (bytes): Bytes da imagem
        img_width (int): Largura desejada
        img_height (int): Altura desejada
        
    Returns:
        tuple: (array_processado, erro) - array numpy ou None, erro ou None
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = img.resize((img_width, img_height))
        img_array = tf.keras.utils.img_to_array(img)
        img_array /= 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array, None
        
    except Exception as e:
        return None, f"Erro ao processar imagem: {str(e)}"


def process_image_from_path(image_path, img_width=150, img_height=150):
    """
    Processa imagem a partir de caminho de arquivo
    
    Args:
        image_path (str): Caminho para a imagem
        img_width (int): Largura desejada
        img_height (int): Altura desejada
        
    Returns:
        tuple: (array_processado, erro) - array numpy ou None, erro ou None
    """
    try:
        img = Image.open(image_path)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = img.resize((img_width, img_height))
        img_array = tf.keras.utils.img_to_array(img)
        img_array /= 255.0
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array, None
        
    except Exception as e:
        return None, f"Erro ao processar imagem: {str(e)}"


def make_prediction(model, processed_image, threshold=0.5):
    """
    Faz predição usando o modelo
    
    Args:
        model: Modelo TensorFlow/Keras
        processed_image: Array numpy da imagem processada
        threshold (float): Limiar de decisão (0.5 por padrão)
        
    Returns:
        dict: Resultado da predição
    """
    try:
        prediction = model.predict(processed_image, verbose=0)[0][0]
        
        is_fire = bool(prediction > threshold)
        confidence = float(prediction if is_fire else 1 - prediction)
        
        return {
            'success': True,
            'fire_detected': is_fire,
            'confidence': round(confidence * 100, 2),
            'raw_prediction': float(prediction),
            'threshold': threshold
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Erro na predição: {str(e)}"
        }


def get_model_info(model):
    """
    Obtém informações sobre o modelo
    
    Args:
        model: Modelo TensorFlow/Keras
        
    Returns:
        dict: Informações do modelo
    """
    try:
        return {
            'input_shape': str(model.input_shape),
            'output_shape': str(model.output_shape),
            'total_params': model.count_params(),
            'layers': len(model.layers)
        }
    except Exception as e:
        return {'error': str(e)}


def format_timestamp():
    """Retorna timestamp formatado para logs"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def validate_image_file(filename):
    """
    Valida se o arquivo é uma imagem suportada
    
    Args:
        filename (str): Nome do arquivo
        
    Returns:
        bool: True se válido
    """
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    _, ext = os.path.splitext(filename.lower())
    return ext in allowed_extensions


def bytes_to_mb(bytes_size):
    """Converte bytes para MB"""
    return round(bytes_size / (1024 * 1024), 2)
