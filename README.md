# IdentyFIRE — Arquitetura Distribuída com gRPC (Local)

Migração de uma aplicação monolítica para uma arquitetura local distribuída usando **gRPC**, sem Docker. O sistema consiste em três processos Python independentes que se comunicam via gRPC.

## 📋 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  GUI (Cliente gRPC)           (localhost:50051)    │
│  - Seleciona imagens                               │
│  - Envia bytes para inference_server                │
│  - Exibe resultado (label, confiança)              │
│                                                     │
└────────────────────┬────────────────────────────────┘
                     │ gRPC PredictImage
                     ▼
┌─────────────────────────────────────────────────────┐
│                                                     │
│  Inference Server (localhost:50051)                 │
│  - Carrega modelo ./models/latest.h5               │
│  - Processa imagem (resize, normalização)           │
│  - Retorna label + confidence                       │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                                                     │
│  Training Service (localhost:50052)                 │
│  - SubmitTrainingJob: lança main.py via subprocess │
│  - GetJobStatus: retorna status do processo         │
│  - Salva modelos/plots em ./models/<job_id>/       │
│                                                     │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                                                     │
│  Training Script (main.py)                          │
│  - Recebe args: --dataset, --epochs, --output-dir  │
│  - Treina modelo CNN                               │
│  - Salva modelo + gráficos em --output-dir         │
│  - Sem plt.show() (apenas plt.savefig)            │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## 🚀 Instalação e Configuração

### Opção Rápida (Recomendado) — Windows

**Execute o arquivo `start_all.bat`:**

```bash
Double-click em: start_all.bat
```

Este arquivo automaticamente:
1. ✅ Cria ambiente virtual (se não existir)
2. ✅ Verifica e instala todas as dependências
3. ✅ Gera stubs gRPC (se necessário)
4. ✅ Copia modelo pré-treinado
5. ✅ Inicia os 3 servidores em janelas separadas
6. ✅ Abre a GUI

Pronto! Você pode começar a usar a aplicação.

---

### Opção Manual — Todos os Sistemas

#### 1. Clonar Repositório

```bash
git clone https://github.com/catfmcastro/IdentyFIRE_2025_2.git
cd IdentyFIRE_2025_2
git checkout distribuida
```

#### 2. Criar Ambiente Virtual

```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate

# macOS / Linux
source .venv/bin/activate
```

#### 3. Instalar Dependências

```bash
pip install --upgrade pip
pip install grpcio grpcio-tools tensorflow pillow numpy matplotlib scikit-learn pytest
```

#### 4. Gerar Stubs gRPC (se ainda não existirem)

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/identyfire.proto
```

Isso criará:
- `identyfire_pb2.py` — definições de mensagens
- `identyfire_pb2_grpc.py` — stubs e servicers

#### 5. Preparar Estrutura de Diretórios

```bash
mkdir -p models
mkdir -p proto

# Copiar modelo pré-treinado (se disponível)
# Windows (PowerShell)
Copy-Item .\IdentyFIRE1.h5 .\models\latest.h5

# macOS / Linux
cp ./IdentyFIRE1.h5 ./models/latest.h5
```

## 📁 Estrutura do Projeto

```
IdentyFIRE_2025_2/
├── README.md                      # Este arquivo
├── proto/
│   └── identyfire.proto           # Definições gRPC (mensagens e serviços)
├── models/
│   ├── latest.h5                  # Modelo padrão para inferência
│   ├── <job_id_1>/
│   │   ├── IdentyFIRE.h5          # Modelo treinado
│   │   ├── accuracy_plot.png      # Gráfico de acurácia
│   │   ├── confusion_matrix.png   # Matriz de confusão
│   │   ├── predictions_sample.png # Amostras de predições
│   │   ├── train.log              # Logs de stdout
│   │   └── train.log.err          # Logs de stderr
│   └── <job_id_2>/
│       └── ...
├── inference_server.py            # Servidor de inferência gRPC (porta 50051)
├── training_service.py            # Servidor de treinamento gRPC (porta 50052)
├── gui.py                         # Cliente gRPC com interface Tkinter
├── main.py                        # Script de treinamento com argparse
├── test_inference.py              # Testes do servidor de inferência
├── test_inference_e2e.py          # Testes end-to-end de inferência
├── test_training.py               # Testes do servidor de treinamento
├── identyfire_pb2.py              # [Gerado] Stubs de mensagens
└── identyfire_pb2_grpc.py         # [Gerado] Stubs de serviços
```

## 🎯 Como Executar

### ⚡ Forma Rápida (Windows)

Double-click nos arquivos `.bat`:

| Arquivo | Função |
|---------|--------|
| `start_all.bat` | Inicia tudo: verifica dependências, ambiente, stubs, servidores e GUI |
| `start_training.bat` | Dispara um novo job de treinamento (interativo) |
| `menu.bat` | Menu de gerenciamento com múltiplas opções |

**Recomendação:** Use `start_all.bat` na primeira vez. Depois, use `menu.bat` para gerenciar.

---

### Opção 1: Execução Manual (3 Terminais)

#### Terminal 1: Servidor de Inferência

```bash
python inference_server.py
```

Saída esperada:
```
INFO:root:Carregando modelo de inferência: ./models/latest.h5
INFO:root:Modelo carregado com sucesso.
INFO:root:Servidor de inferência gRPC rodando em localhost:50051
```

#### Terminal 2: Servidor de Treinamento

```bash
python training_service.py
```

Saída esperada:
```
INFO:root:TrainingServicer initialized
INFO:root:Training service gRPC rodando em localhost:50052
```

#### Terminal 3: GUI Cliente

```bash
python gui.py
```

Uma janela Tkinter se abrirá. Você poderá:
1. Clicar em "Selecionar Imagem de Satélite"
2. Escolher uma imagem (PNG, JPG, JPEG, BMP)
3. Ver o resultado: "INCÊNDIO DETECTADO" ou "Nenhum incêndio detectado"

### Opção 2: Disparar um Job de Treinamento

#### Opção A: Via Script Interativo (Recomendado)

```bash
start_training.bat
```

O script irá:
1. Solicitar o caminho do dataset
2. Solicitar o número de épocas
3. Submeter o job via gRPC
4. Monitorar o status em tempo real

#### Opção B: Via Script Python Customizado

Crie um arquivo `trigger_training_custom.py`:

```python
import grpc
import identyfire_pb2
import identyfire_pb2_grpc
import time

def submit_training_job():
    channel = grpc.insecure_channel('localhost:50052')
    stub = identyfire_pb2_grpc.TrainingServiceStub(channel)

    # Ajuste o caminho para o seu dataset
    dataset_path = "/caminho/para/dataset/com/train_valid_test"
    
    req = identyfire_pb2.TrainRequest(dataset_uri=dataset_path, epochs=10)
    resp = stub.SubmitTrainingJob(req)
    
    print(f"Job submetido: {resp.job_id}")
    
    # Polling do status
    job_id = resp.job_id
    while True:
        status_req = identyfire_pb2.JobStatusRequest(job_id=job_id)
        status_resp = stub.GetJobStatus(status_req)
        
        state_name = identyfire_pb2.JobStatusResponse.State.Name(status_resp.state)
        print(f"Status: {state_name} | Logs: {status_resp.logs_path}")
        
        if status_resp.state in [
            identyfire_pb2.JobStatusResponse.State.COMPLETED,
            identyfire_pb2.JobStatusResponse.State.FAILED
        ]:
            break
        
        time.sleep(5)

if __name__ == "__main__":
    submit_training_job()
```

Execute:

```bash
python trigger_training_custom.py
```

## 🧪 Testes Automatizados

Todos os testes usam `pytest`. Certifique-se de que os servidores **não** estão rodando (as fixtures os iniciam automaticamente).

### Rodar Todos os Testes

```bash
pytest -v
```

### Rodar Testes Específicos

```bash
# Testes de Inferência
pytest test_inference.py test_inference_e2e.py -v

# Testes de Treinamento
pytest test_training.py -v
```

### Cobertura de Testes (opcional)

```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
```

Isso gera um relatório em `htmlcov/index.html`.

## 🖱️ Scripts de Automação (.bat)

Para usuários Windows, você tem 4 scripts `.bat` que facilitam o uso da aplicação:

### 0. `setup_once.bat` — Configuração Inicial (Execute PRIMEIRO!)

**O que faz:**
- ✅ Cria ambiente virtual
- ✅ Instala dependências para **inferência** (rápido ~2 min)
- ✅ Opcionalmente instala dependências para **treinamento** (lento ~10 min)
- ✅ Gera stubs gRPC
- ✅ Copia modelo pré-treinado

**Como usar:**
```bash
Double-click em: setup_once.bat
```

**Quando usar:** **PRIMEIRA VEZ** antes de usar qualquer outro script. Depois não precisa mais!

---

### 1. `start_all.bat` — Iniciar Tudo (Use SEMPRE)

**O que faz:**
- ✅ Verifica arquivos necessários
- ✅ Copia modelo pré-treinado
- ✅ Gera stubs gRPC (se necessário)
- ✅ Inicia Inference Server (porta 50051)
- ✅ Inicia Training Service (porta 50052)
- ✅ Abre a GUI

**Como usar:**
```bash
Double-click em: start_all.bat
```

**Quando usar:** Toda vez que quer usar a aplicação (após `setup_once.bat` ser executado uma vez).

---

### 2. `start_training.bat` — Disparar Job de Treinamento

**O que faz:**
- ✅ Interface interativa para submeter jobs
- ✅ Solicita dataset path
- ✅ Solicita número de épocas
- ✅ Monitora status em tempo real
- ✅ Mostra localização dos artefatos

**Como usar:**
```bash
Double-click em: start_training.bat
```

**Pré-requisito:** `training_service.py` deve estar rodando (execute `start_all.bat` primeiro).

**Exemplo de interação:**
```
[REQUERIDO] Caminho para o dataset:
Digite o caminho: C:\Users\seu_usuario\datasets\fire_dataset

[OPCIONAL] Numero de epocas para treinamento (padrao: 25)
Digite o numero (ou pressione Enter para usar padrao): 50

[INFO] Job submetido com sucesso!
[INFO] Job ID: a1b2c3d4
[INFO] Monitorando status do treinamento...

[14:23:15] Status: RUNNING       | Logs: ./models/a1b2c3d4
[14:23:20] Status: RUNNING       | Logs: ./models/a1b2c3d4
[14:23:50] Status: COMPLETED     | Logs: ./models/a1b2c3d4
```

---

### 3. `menu.bat` — Menu de Gerenciamento

**O que oferece:**
```
1. Iniciar todos os servicos (GUI + Servers)
2. Iniciar apenas o Inference Server (porta 50051)
3. Iniciar apenas o Training Service (porta 50052)
4. Disparar novo job de treinamento
5. Abrir GUI (conecta aos servidores existentes)
6. Verificar dependencias
7. Regenerar stubs gRPC
8. Configurar ambiente inicial
0. Sair
```

**Como usar:**
```bash
Double-click em: menu.bat
```

**Exemplos de uso:**
- Opção **1**: Iniciar tudo (equivalente a `start_all.bat`)
- Opção **2**: Iniciar apenas inference server (útil para testes específicos)
- Opção **6**: Verificar quais pacotes estão instalados
- Opção **7**: Regenerar stubs após modificar `proto/identyfire.proto`
- Opção **8**: Configuração inicial completa

---

### Comparação dos Scripts

| Situação | Recomendado |
|----------|------------|
| Primeira vez usando | `start_all.bat` |
| Usar aplicação normalmente | `start_all.bat` |
| Treinar novo modelo | `start_training.bat` |
| Controle granular de serviços | `menu.bat` |
| Verificar instalação | `menu.bat` → Opção 6 |
| Modificou proto/ | `menu.bat` → Opção 7 |

## 📝 Refatorações Principais

### 1. **gui.py** — De Monolítico para Cliente gRPC

**Antes:**
```python
import tensorflow as tf
import numpy as np

# Carrega modelo localmente
modelo = tf.keras.models.load_model("IdentyFIRE1.h5")

# Processa imagem localmente
img_array = tf.keras.preprocessing.image.img_to_array(...)
predicao = modelo.predict(img_array)[0][0]
```

**Depois:**
```python
import grpc
import identyfire_pb2
import identyfire_pb2_grpc

channel = grpc.insecure_channel('localhost:50051')
stub = identyfire_pb2_grpc.ModelServiceStub(channel)

# Envia bytes para o servidor
req = identyfire_pb2.PredictRequest(model_id="latest", image_bytes=img_bytes)
response = stub.PredictImage(req)
print(f"Label: {response.label}, Confiança: {response.confidence}")
```

**Benefícios:**
- GUI sem dependências de TensorFlow/NumPy (mais leve)
- Separação de responsabilidades

### 2. **main.py** — De Hardcoded para Argumentos

**Antes:**
```python
dataset_dir = "/mnt/h/Arquivos/Documents/code/2025_2/TI_VI/IdentyFIRE_2025_2/images"
epochs = 25
model.save("IdentyFIRE1.h5")
plt.show()
```

**Depois:**
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--dataset", required=True)
parser.add_argument("--epochs", type=int, default=25)
parser.add_argument("--output-dir", required=True)
args = parser.parse_args()

dataset_dir = args.dataset
epochs = args.epochs
output_dir = args.output_dir

model_path = os.path.join(output_dir, "IdentyFIRE.h5")
model.save(model_path)
plt.savefig(os.path.join(output_dir, "accuracy_plot.png"))
```

**Uso:**
```bash
python main.py --dataset ./images --epochs 50 --output-dir ./models/job_123
```

### 3. **inference_server.py** — Novo Servidor de Inferência

- Carrega `./models/latest.h5` uma única vez
- Expõe RPC `PredictImage(model_id, image_bytes) → (label, confidence)`
- Trata erros com gRPC codes apropriados

### 4. **training_service.py** — Novo Servidor de Treinamento

- Expõe RPC `SubmitTrainingJob(dataset_uri, epochs) → job_id`
- Expõe RPC `GetJobStatus(job_id) → (state, logs_path)`
- Lança `main.py` com argumentos corretos
- Rastreia processos e retorna RUNNING/COMPLETED/FAILED

## ⚙️ Requisitos de Sistema

- **Python:** 3.8+
- **RAM:** 4 GB mínimo (8+ GB recomendado para treinamento)
- **GPU:** Opcional (CUDA 11.x + cuDNN recomendado para treinamento rápido)

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'identyfire_pb2'"

**Solução:** Execute o comando de geração de stubs:
```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/identyfire.proto
```

### Erro: "Connection refused" ao conectar na GUI

**Solução:** Certifique-se de que `inference_server.py` está rodando:
```bash
python inference_server.py
```

### Erro: "Modelo não encontrado" no `inference_server.py`

**Solução:** Copie o modelo para `./models/latest.h5`:
```bash
Copy-Item .\IdentyFIRE1.h5 .\models\latest.h5
```

### Testes falhando com "Address already in use"

**Solução:** Mate processos antigos de servidores:
```bash
# Windows (PowerShell)
Get-Process python | Stop-Process -Force

# macOS / Linux
killall python
```

## 📚 Referências

- [gRPC Python](https://grpc.io/docs/languages/python/)
- [Protocol Buffers](https://developers.google.com/protocol-buffers)
- [TensorFlow Keras](https://tensorflow.org/guide/keras)
- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)

## 📄 Licença

Este projeto está sob a licença [MIT](LICENSE).

## 👥 Contribuidores

- **Desenvolvedor:** IdentyFIRE Team (2025.2)

---

**Última atualização:** 10 de novembro de 2025
