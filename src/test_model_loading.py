"""
Script de teste para diagnosticar problema de carregamento de modelo
"""
import requests
import json
import os

# Configuração
SERVER_URL = "http://127.0.0.1:5000"
MODEL_NAME = "IdentyFIRE_2064_best.h5"

print("=" * 60)
print("TESTE DE CARREGAMENTO DE MODELO")
print("=" * 60)

# 1. Verificar se servidor está online
print("\n1. Verificando servidor...")
try:
    response = requests.get(f"{SERVER_URL}/health", timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Servidor online")
        print(f"  Status: {data.get('status')}")
        print(f"  Modelo carregado: {data.get('model_loaded')}")
        print(f"  Modelo atual: {data.get('model_name', 'Nenhum')}")
    else:
        print(f"✗ Servidor retornou status {response.status_code}")
        exit(1)
except Exception as e:
    print(f"✗ Não foi possível conectar ao servidor: {e}")
    print("  Certifique-se de que server_gui.py está rodando!")
    exit(1)

# 2. Verificar modelos disponíveis
print("\n2. Listando modelos disponíveis...")
try:
    response = requests.get(f"{SERVER_URL}/models", timeout=5)
    if response.status_code == 200:
        data = response.json()
        models = data.get('models', [])
        print(f"✓ {len(models)} modelo(s) encontrado(s):")
        for model in models:
            print(f"  - {model['name']} ({model['size_mb']} MB)")
    else:
        print(f"✗ Erro ao listar modelos: {response.status_code}")
except Exception as e:
    print(f"✗ Erro: {e}")

# 3. Verificar se modelo de teste existe
print(f"\n3. Verificando modelo '{MODEL_NAME}'...")
with open('config.json') as f:
    config = json.load(f)

models_dir = config['server']['models_directory']
if not os.path.isabs(models_dir):
    models_dir = os.path.join(os.getcwd(), models_dir)

model_path = os.path.join(models_dir, MODEL_NAME)
if os.path.exists(model_path):
    print(f"✓ Modelo existe: {model_path}")
else:
    print(f"✗ Modelo não encontrado: {model_path}")
    print(f"  Usando primeiro modelo disponível...")
    try:
        response = requests.get(f"{SERVER_URL}/models", timeout=5)
        data = response.json()
        if data['models']:
            MODEL_NAME = data['models'][0]['name']
            print(f"  Modelo selecionado: {MODEL_NAME}")
        else:
            print("  Nenhum modelo disponível!")
            exit(1)
    except:
        exit(1)

# 4. Tentar carregar modelo
print(f"\n4. Carregando modelo '{MODEL_NAME}'...")
try:
    payload = {'model_path': MODEL_NAME}
    print(f"  Payload: {json.dumps(payload)}")
    print(f"  URL: {SERVER_URL}/load_model")
    
    response = requests.post(
        f"{SERVER_URL}/load_model",
        json=payload,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    print(f"  Status code: {response.status_code}")
    print(f"  Content-Type: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Modelo carregado com sucesso!")
        print(f"  Resposta: {json.dumps(data, indent=2)}")
    elif response.status_code == 404:
        data = response.json()
        print(f"✗ Modelo não encontrado no servidor")
        print(f"  Erro: {data.get('message')}")
        print(f"  Path esperado: {data.get('message')}")
    else:
        try:
            data = response.json()
            print(f"✗ Erro ao carregar modelo")
            print(f"  Erro: {data.get('error')}")
            print(f"  Mensagem: {data.get('message')}")
        except:
            print(f"✗ Erro ao carregar modelo (não-JSON)")
            print(f"  Response: {response.text[:500]}")
            
except Exception as e:
    print(f"✗ Exceção ao carregar modelo: {e}")
    import traceback
    traceback.print_exc()

# 5. Verificar modelo atual após carregamento
print("\n5. Verificando modelo atual...")
try:
    response = requests.get(f"{SERVER_URL}/current_model", timeout=5)
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            model_info = data.get('model', {})
            print(f"✓ Modelo ativo: {model_info.get('name')}")
            print(f"  Path: {model_info.get('path')}")
            print(f"  Loaded: {model_info.get('loaded')}")
        else:
            print(f"✗ Nenhum modelo carregado")
    else:
        print(f"✗ Erro ao verificar modelo atual: {response.status_code}")
except Exception as e:
    print(f"✗ Erro: {e}")

print("\n" + "=" * 60)
print("TESTE CONCLUÍDO")
print("=" * 60)
