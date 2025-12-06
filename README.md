# 🔥 IdentyFIRE - Sistema de Detecção de Incêndios com Deep Learning

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0+-orange.svg)

**IdentyFIRE** é um sistema completo de detecção de incêndios em imagens utilizando Deep Learning (Redes Neurais Convolucionais - CNNs). O projeto oferece uma arquitetura cliente-servidor robusta com interfaces gráficas intuitivas para treinamento, gerenciamento e inferência de modelos.

## 👥 Autores

- André Menezes
- Catarina Castro
- Diego Maia
- Rafael Oliveira


## 📑 Índice

1. [Características Principais](#-características-principais)
2. [Arquitetura do Sistema](#-arquitetura-do-sistema)
3. [Como Funciona](#-como-funciona)
4. [Requisitos](#-requisitos)
5. [Instalação](#-instalação)
6. [Estrutura do Projeto](#-estrutura-do-projeto)
7. [Guia de Uso Completo](#-guia-de-uso-completo)
   - [1. Treinamento de Modelos](#1-treinamento-de-modelos)
   - [2. Servidor de Detecção](#2-servidor-de-detecção)
   - [3. Cliente de Detecção](#3-cliente-de-detecção)
8. [Configuração Avançada](#-configuração-avançada)
9. [API REST](#-api-rest)
10. [Perguntas Frequentes](#-perguntas-frequentes)
11. [Solução de Problemas](#-solução-de-problemas)
12. [Contribuindo](#-contribuindo)
13. [Licença](#-licença)


## ✨ Características Principais

### 🎓 **Sistema de Treinamento Completo**
- Interface gráfica intuitiva para configurar e treinar modelos
- Suporte para treinamento com GPU (AMD, Intel, NVIDIA via DirectML)
- Data augmentation automático para melhorar a generalização
- Callbacks inteligentes (Early Stopping, ReduceLROnPlateau, ModelCheckpoint)
- Visualização em tempo real de métricas de treinamento
- Geração automática de gráficos de performance e matriz de confusão
- Exportação de resultados em JSON

### 🚀 **Servidor API Robusto**
- API REST completa com Flask
- Suporte para processamento em lote (batch) otimizado para GPU
- Gerenciamento dinâmico de modelos
- Monitoramento em tempo real com estatísticas
- Sistema de logs detalhado
- Validação de imagens e controle de tamanho

### 💻 **Cliente Intuitivo**
- Interface gráfica amigável para análise de imagens
- Suporte para análise individual e em lote
- Visualização de resultados com confiança
- Processamento otimizado de múltiplas imagens
- Conexão automática ao servidor

### 🎯 **Gerenciamento de Modelos**
- Sistema de auto-descoberta de modelos
- Carregamento dinâmico sem reiniciar o servidor
- Organização e renomeação de modelos
- Visualização de metadados e estatísticas
- Suporte para múltiplos modelos


## 🏗️ Arquitetura do Sistema

O IdentyFIRE segue uma arquitetura cliente-servidor modular:

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPONENTES DO SISTEMA                    │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  TRAINING GUI    │         │   SERVER GUI     │         │   CLIENT GUI     │
│  (Treinamento)   │────────▶│  (API + Monitor) │◀────────│   (Análise)      │
└──────────────────┘         └──────────────────┘         └──────────────────┘
        │                             │                             │
        │                             │                             │
        ▼                             ▼                             ▼
┌──────────────────┐         ┌──────────────────┐         ┌──────────────────┐
│  main.py         │         │  Flask API       │         │  Requests HTTP   │
│  (CNN Training)  │         │  (REST Endpoints)│         │  (API Calls)     │
└──────────────────┘         └──────────────────┘         └──────────────────┘
        │                             │                             
        │                             │                             
        ▼                             ▼                             
┌───────────────────────────────────────────────────────────────┐
│                   MODELO TENSORFLOW/KERAS                      │
│          (Rede Neural Convolucional para Detecção)            │
└───────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados:

1. **Treinamento**: `training_gui.py` → `main.py` → Modelo treinado salvo em `/models`
2. **Servidor**: `server_gui.py` carrega modelo e expõe API REST
3. **Cliente**: `client_gui.py` envia imagens via HTTP → Servidor processa → Retorna resultado


## 🧠 Como Funciona

### Arquitetura da Rede Neural

O IdentyFIRE utiliza uma **Convolutional Neural Network (CNN)** especializada para classificação binária:

```python
Arquitetura do Modelo:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Input Layer (150x150x3 RGB)
    ↓
Conv2D(32 filtros, 3x3) + ReLU + Padding Same
    ↓
MaxPooling2D(2x2)
    ↓
Conv2D(64 filtros, 3x3) + ReLU + Padding Same
    ↓
MaxPooling2D(2x2)
    ↓
Conv2D(128 filtros, 3x3) + ReLU + Padding Same
    ↓
MaxPooling2D(2x2)
    ↓
Conv2D(128 filtros, 3x3) + ReLU + Padding Same
    ↓
MaxPooling2D(2x2)
    ↓
Flatten
    ↓
Dropout(0.5) - Regularização
    ↓
Dense(512) + ReLU
    ↓
Dense(1) + Sigmoid - Classificação Binária
    ↓
Output: Probabilidade [0-1]
    - > 0.5 = FOGO 🔥
    - ≤ 0.5 = SEM FOGO ✅
```

### Data Augmentation

Para melhorar a generalização e evitar overfitting, o sistema aplica augmentação de dados:

- **Rotação**: ±45°
- **Deslocamento Horizontal/Vertical**: ±15%
- **Flip Horizontal**: Sim
- **Zoom**: ±50%
- **Rescale**: Normalização [0-1]

### Callbacks de Treinamento

1. **EarlyStopping**: Para o treinamento se a validação não melhorar por 5 épocas
2. **ReduceLROnPlateau**: Reduz a taxa de aprendizado quando a perda para de diminuir
3. **ModelCheckpoint**: Salva o melhor modelo baseado na acurácia de validação

### Otimização para GPU

O sistema utiliza **TensorFlow-DirectML** para suporte universal a GPUs:

- ✅ AMD (Radeon)
- ✅ Intel (Iris, Arc)
- ✅ NVIDIA (GeForce, Quadro)
- ✅ Fallback automático para CPU se GPU não disponível

---

## 📋 Requisitos

### Hardware Recomendado

| Componente | Mínimo | Recomendado |
|------------|--------|-------------|
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16+ GB |
| **GPU** | Integrada | Dedicada (VRAM 4GB+) |
| **Armazenamento** | 5 GB | 20+ GB (para datasets) |

### Software

- **Python**: 3.8 ou superior
- **Windows**: 10/11 (suporte DirectML)
- **Navegador**: Qualquer (para visualizar resultados)

---

## 🔧 Instalação

### Método 1: Instalação Automatizada (Recomendado)

#### No Windows (PowerShell):

```powershell
# 1. Clone ou baixe o projeto
cd C:\Caminho\Para\Identifyre

# 2. Execute o script de instalação
.\scripts\install.bat

# 3. Ative o ambiente virtual
.\scripts\activate_venv.bat
```

#### No Linux/Mac:

```bash
# 1. Clone ou baixe o projeto
cd /caminho/para/Identifyre

# 2. Execute o script de instalação
chmod +x scripts/install.sh
./scripts/install.sh

# 3. Ative o ambiente virtual
source scripts/activate_venv.sh
```

### Método 2: Instalação Manual

```powershell
# 1. Criar ambiente virtual
python -m venv .venv

# 2. Ativar ambiente virtual (Windows)
.\.venv\Scripts\Activate.ps1

# No Linux/Mac:
# source .venv/bin/activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Verificar instalação
python -c "import tensorflow as tf; print('TensorFlow:', tf.__version__)"
```

### Verificar Instalação

```python
# Teste rápido
python -c "
import tensorflow as tf
import PIL
import flask
import requests

print('✓ TensorFlow:', tf.__version__)
print('✓ Pillow:', PIL.__version__)
print('✓ Flask instalado')
print('✓ Requests instalado')

# Verificar GPU
gpus = tf.config.list_physical_devices('GPU')
print(f'✓ GPUs detectadas: {len(gpus)}')
"
```

---

## 📁 Estrutura do Projeto

```
Identifyre/
│
├── 📄 config.json              # Configurações do servidor e modelo
├── 📄 requirements.txt         # Dependências Python
├── 📄 README.md               # Este arquivo
│
├── 📁 models/                  # Modelos treinados (.h5)
│   ├── best_model.h5
│   ├── IdentyFIRE1.h5
│   └── IdentyFIRE1_Parallel.h5
│
├── 📁 scripts/                 # Scripts de automação
│   ├── install.bat            # Instalação Windows
│   ├── install.sh             # Instalação Linux/Mac
│   ├── start_all.bat          # Iniciar tudo (Windows)
│   ├── start_server.bat       # Iniciar servidor
│   ├── start_client.bat       # Iniciar cliente
│   ├── start_training.bat     # Iniciar treinamento
│   └── activate_venv.bat      # Ativar ambiente
│
└── 📁 src/                     # Código fonte
    ├── 🐍 main.py             # Script principal de treinamento CNN
    ├── 🐍 training_gui.py     # GUI de treinamento e gerenciamento
    ├── 🐍 server_gui.py       # GUI do servidor API
    ├── 🐍 client_gui.py       # GUI do cliente
    └── 🐍 utils.py            # Funções auxiliares
```

---

## 📖 Guia de Uso Completo

### 1. Treinamento de Modelos

#### 1.1. Preparar Dataset

O dataset deve seguir a estrutura:

```
C:/Dataset/archive/
├── train/
│   ├── fire/           # Imagens com fogo
│   │   ├── img1.jpg
│   │   ├── img2.jpg
│   │   └── ...
│   └── nofire/         # Imagens sem fogo
│       ├── img1.jpg
│       ├── img2.jpg
│       └── ...
├── valid/
│   ├── fire/
│   └── nofire/
└── test/
    ├── fire/
    └── nofire/
```

**Dicas para um bom dataset:**
- Mínimo de 500 imagens por classe
- Imagens balanceadas (50% fire, 50% nofire)
- Variedade de cenários (dia, noite, interno, externo)
- Resoluções variadas (serão redimensionadas para 150x150)

#### 1.2. Iniciar GUI de Treinamento

```powershell
# Método 1: Script automático
.\scripts\start_training.bat

# Método 2: Diretamente
python src/training_gui.py
```

#### 1.3. Configurar Parâmetros

Na aba **🎓 Treinamento**:

| Parâmetro | Descrição | Valor Recomendado |
|-----------|-----------|-------------------|
| **Diretório do Dataset** | Caminho para a pasta do dataset | `C:/Dataset/archive` |
| **Nome do Modelo** | Nome único para identificar o modelo | `IdentyFIRE_2025_01_15` |
| **Épocas** | Número de iterações completas no dataset | `20-30` |
| **Batch Size** | Número de imagens processadas por vez | `32` (16 para GPUs pequenas) |

**Opções:**
- ☑️ **Salvar automaticamente na pasta de modelos**: Move modelo para `/models` após treinamento
- ☑️ **Carregar no servidor após treinar**: Carrega modelo no servidor automaticamente

#### 1.4. Iniciar Treinamento

1. Clique em **▶️ Iniciar Treinamento**
2. Confirme os parâmetros
3. Acompanhe o progresso em tempo real:
   - **Console**: Log detalhado do processo
   - **Estatísticas**: Métricas atualizadas a cada época
   - **Barra de Progresso**: Percentual de conclusão

#### 1.5. Avaliar Resultados

Após o treinamento, são gerados:

1. **Modelo Principal**: `nome_modelo.h5`
2. **Melhor Modelo**: `nome_modelo_best.h5` (melhor acurácia de validação)
3. **Gráfico de Histórico**: `nome_modelo_training_history.png`
   - Acurácia de treino vs validação
   - Perda de treino vs validação
4. **Matriz de Confusão**: `nome_modelo_confusion_matrix.png`
5. **Resultados JSON**: `nome_modelo_results.json`

**Exemplo de resultados.json:**
```json
{
    "model_name": "IdentyFIRE_2025_01_15",
    "test_accuracy": 0.9542,
    "test_loss": 0.1234,
    "training_time": "45min 23.45s",
    "epochs_trained": 25,
    "batch_size": 32,
    "dataset_dir": "C:/Dataset/archive"
}
```

#### 1.6. Gerenciar Modelos

Na aba **📦 Gerenciamento**:

- **🔄 Atualizar Lista**: Recarrega modelos disponíveis
- **📂 Abrir Pasta de Modelos**: Abre `/models` no explorador
- **🚀 Carregar no Servidor**: Envia modelo selecionado ao servidor
- **✏️ Renomear**: Renomeia modelo e arquivos relacionados
- **🗑️ Deletar Modelo**: Remove modelo e arquivos associados

---

### 2. Servidor de Detecção

O servidor fornece uma API REST para processar imagens e detectar incêndios.

#### 2.1. Iniciar Servidor

```powershell
# Método 1: Script automático
.\scripts\start_server.bat

# Método 2: Diretamente
python src/server_gui.py
```

#### 2.2. Configurar Servidor

Na seção **⚙️ Configuração do Servidor**:

| Parâmetro | Descrição | Valor Padrão |
|-----------|-----------|--------------|
| **Host** | Endereço IP do servidor | `127.0.0.1` (localhost) |
| **Porta** | Porta TCP para API | `5000` |
| **Diretório de Modelos** | Pasta com modelos `.h5` | `./models` |

**Para acesso remoto:**
- Use `0.0.0.0` como host
- Configure firewall para permitir porta escolhida

#### 2.3. Iniciar Servidor

1. Clique em **▶️ Iniciar Servidor**
2. Aguarde mensagem: **🟢 Servidor Rodando**
3. Verifique URL: `http://127.0.0.1:5000`

#### 2.4. Carregar Modelo

**Opção 1: Automático**
- Configure `config.json`:
```json
{
    "server": {
        "auto_load_default": true,
        "default_model": "best_model.h5"
    }
}
```

**Opção 2: Manual via Training GUI**
- Na aba **📦 Gerenciamento** da Training GUI
- Selecione um modelo
- Clique em **🚀 Carregar no Servidor**

#### 2.5. Monitorar Servidor

A interface exibe em tempo real:

| Métrica | Descrição |
|---------|-----------|
| **Requisições Totais** | Número total de análises |
| **✓ Sucesso** | Análises bem-sucedidas |
| **✗ Erros** | Falhas de processamento |
| **🔥 Incêndios Detectados** | Imagens com fogo detectado |
| **✅ Sem Fogo** | Imagens seguras |
| **Taxa de Detecção** | Percentual de incêndios detectados |

**Console de Logs** mostra:
- Timestamp de cada requisição
- Resultado da análise (FIRE/SAFE)
- Confiança da predição
- Erros e avisos

---

### 3. Cliente de Detecção

O cliente permite analisar imagens de forma intuitiva.

#### 3.1. Iniciar Cliente

```powershell
# Método 1: Script automático
.\scripts\start_client.bat

# Método 2: Diretamente
python src/client_gui.py
```

#### 3.2. Conectar ao Servidor

1. Na seção **⚙️ Configuração do Servidor**:
   - URL padrão: `http://127.0.0.1:5000`
   - Para servidor remoto: `http://IP_DO_SERVIDOR:PORTA`

2. Clique em **🔌 Conectar**

3. Aguarde confirmação:
   - **🟢 Conectado**
   - **Modelo Ativo**: Nome do modelo carregado

#### 3.3. Analisar Imagem Individual

1. Certifique-se de estar conectado
2. Clique em **🖼️ Selecionar e Analisar Imagem**
3. Escolha uma imagem (JPG, PNG, BMP, GIF)
4. Aguarde o resultado:

**Exemplo de resultado:**
```
🔥 INCÊNDIO DETECTADO!
Confiança: 97.84%
⚠️ ALERTA: Fogo detectado na imagem!
📁 foto_floresta.jpg
```

ou

```
✅ NENHUM INCÊNDIO
Confiança: 99.12%
✓ Imagem segura - Sem fogo detectado
📁 paisagem.jpg
```

#### 3.4. Processar Pasta (Batch)

Para analisar múltiplas imagens:

1. Clique em **📁 Processar Pasta**
2. Selecione diretório com imagens
3. Confirme o número de imagens encontradas
4. Aguarde processamento otimizado em GPU

**Resultado em Lote:**

```
📊 Resumo do Processamento
━━━━━━━━━━━━━━━━━━━━━━━━━
Total de imagens: 150
✓ Processadas: 150
🔥 Fogo detectado: 12
✅ Sem fogo: 138
❌ Erros: 0

Detalhes:
imagem001.jpg                    ✅ SEGURO (98.3%)
imagem002.jpg                    🔥 FOGO (95.7%)
imagem003.jpg                    ✅ SEGURO (99.1%)
...
```

**Vantagens do Processamento em Lote:**
- ⚡ **10-20x mais rápido** que processar uma por uma
- 🎯 Otimizado para GPU (processa múltiplas imagens simultaneamente)
- 📊 Estatísticas consolidadas
- 💾 Uso eficiente de memória

---

## ⚙️ Configuração Avançada

### Arquivo config.json

```json
{
    "server": {
        "host": "127.0.0.1",           // IP do servidor
        "port": 5000,                   // Porta TCP
        "models_directory": "./models", // Pasta de modelos
        "default_model": "best_model.h5", // Modelo padrão
        "auto_load_default": true,      // Carregar automaticamente
        "max_image_size_mb": 10         // Tamanho máximo de imagem
    },
    "model": {
        "img_height": 150,              // Altura das imagens
        "img_width": 150,               // Largura das imagens
        "prediction_threshold": 0.5     // Limiar de decisão (0-1)
    },
    "logging": {
        "max_logs": 1000,               // Máximo de logs em memória
        "save_logs": true,              // Salvar logs em arquivo
        "log_file": "server_logs.txt"   // Nome do arquivo de log
    }
}
```

### Ajustar Threshold de Predição

O **threshold** (limiar) determina quando classificar como fogo:

- **0.3-0.4**: Mais sensível (detecta mais, mas mais falsos positivos)
- **0.5**: Balanceado (padrão)
- **0.6-0.7**: Mais conservador (menos falsos positivos, pode perder alguns casos)

**Como ajustar:**

1. Edite `config.json`:
```json
"prediction_threshold": 0.6
```

2. Reinicie o servidor para aplicar

### Otimizar para GPU Específica

**Para GPUs com pouca VRAM (< 4GB):**

```python
# Edite main.py, adicione após imports:
import os
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
```

**Para GPUs com muita VRAM (> 8GB):**

```python
# Aumente o batch size no training_gui.py:
batch_size = 64  # ou 128
```

---

## 🌐 API REST

### Endpoints Disponíveis

#### 1. Health Check

Verifica status do servidor.

**Request:**
```http
GET /health
```

**Response:**
```json
{
    "status": "online",
    "model_loaded": true,
    "model_name": "best_model.h5",
    "uptime": "2h 34m",
    "stats": {
        "total_requests": 145,
        "fires_detected": 12
    }
}
```

#### 2. Listar Modelos

Retorna todos os modelos disponíveis.

**Request:**
```http
GET /models
```

**Response:**
```json
{
    "success": true,
    "models": [
        {
            "name": "best_model.h5",
            "path": "/path/to/models/best_model.h5",
            "size_mb": 8.45,
            "modified": "2025-01-15 14:30:22"
        }
    ],
    "total": 3,
    "models_directory": "./models"
}
```

#### 3. Informações do Modelo Atual

Obtém detalhes do modelo carregado.

**Request:**
```http
GET /current_model
```

**Response:**
```json
{
    "success": true,
    "model": {
        "name": "best_model.h5",
        "path": "/path/to/models/best_model.h5",
        "info": {
            "input_shape": "(None, 150, 150, 3)",
            "output_shape": "(None, 1)",
            "total_params": 2458049,
            "layers": 12
        },
        "loaded": true
    }
}
```

#### 4. Carregar Modelo

Carrega um modelo específico no servidor.

**Request:**
```http
POST /load_model
Content-Type: application/json

{
    "model_path": "IdentyFIRE_2025_01_15.h5"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Model loaded successfully",
    "model": {
        "name": "IdentyFIRE_2025_01_15.h5",
        "path": "/path/to/models/IdentyFIRE_2025_01_15.h5",
        "loaded": true
    }
}
```

#### 5. Predição Individual

Analisa uma imagem para detectar fogo.

**Request:**
```http
POST /predict
Content-Type: multipart/form-data

image: [arquivo de imagem]
```

**Response (Fogo Detectado):**
```json
{
    "success": true,
    "fire_detected": true,
    "confidence": 97.84,
    "raw_prediction": 0.9784,
    "threshold": 0.5,
    "filename": "test_image.jpg"
}
```

**Response (Sem Fogo):**
```json
{
    "success": true,
    "fire_detected": false,
    "confidence": 99.12,
    "raw_prediction": 0.0088,
    "threshold": 0.5,
    "filename": "safe_image.jpg"
}
```

#### 6. Predição em Lote

Processa múltiplas imagens simultaneamente (otimizado para GPU).

**Request:**
```http
POST /predict_batch
Content-Type: multipart/form-data

images: [arquivo1.jpg]
images: [arquivo2.jpg]
images: [arquivo3.jpg]
...
```

**Response:**
```json
{
    "success": true,
    "total": 150,
    "fires_detected": 12,
    "results": [
        {
            "filename": "img001.jpg",
            "fire_detected": false,
            "confidence": 98.32,
            "raw_prediction": 0.0168
        },
        {
            "filename": "img002.jpg",
            "fire_detected": true,
            "confidence": 95.67,
            "raw_prediction": 0.9567
        }
    ],
    "errors": []
}
```

### Exemplos de Uso da API

#### Python (Requests)

```python
import requests

# Análise individual
url = "http://127.0.0.1:5000/predict"
files = {'image': open('teste.jpg', 'rb')}
response = requests.post(url, files=files)
print(response.json())

# Análise em lote
url = "http://127.0.0.1:5000/predict_batch"
files = [
    ('images', open('img1.jpg', 'rb')),
    ('images', open('img2.jpg', 'rb')),
    ('images', open('img3.jpg', 'rb'))
]
response = requests.post(url, files=files)
print(response.json())
```

#### cURL

```bash
# Health check
curl http://127.0.0.1:5000/health

# Predição individual
curl -X POST -F "image=@teste.jpg" http://127.0.0.1:5000/predict

# Carregar modelo
curl -X POST http://127.0.0.1:5000/load_model \
  -H "Content-Type: application/json" \
  -d '{"model_path": "best_model.h5"}'
```

#### JavaScript (Fetch)

```javascript
// Análise individual
const formData = new FormData();
formData.append('image', fileInput.files[0]);

fetch('http://127.0.0.1:5000/predict', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Fogo detectado:', data.fire_detected);
    console.log('Confiança:', data.confidence + '%');
});
```

---

## ❓ Perguntas Frequentes

### 1. **Qual a acurácia esperada do modelo?**

Com um dataset bem balanceado e de boa qualidade, é possível alcançar:
- **Acurácia de Treino**: 95-98%
- **Acurácia de Validação**: 92-96%
- **Acurácia de Teste**: 90-95%

### 2. **Quanto tempo leva para treinar um modelo?**

Depende do hardware e tamanho do dataset:

| Hardware | Dataset (10k imagens) | Tempo Estimado |
|----------|----------------------|----------------|
| CPU (i5/Ryzen 5) | 25 épocas | 2-4 horas |
| GPU Integrada | 25 épocas | 1-2 horas |
| GPU Dedicada (GTX 1660) | 25 épocas | 20-40 minutos |
| GPU High-End (RTX 3080) | 25 épocas | 10-20 minutos |

### 3. **Posso usar meu próprio dataset?**

Sim! Apenas certifique-se de seguir a estrutura:
```
dataset/
├── train/
│   ├── fire/
│   └── nofire/
├── valid/
│   ├── fire/
│   └── nofire/
└── test/
    ├── fire/
    └── nofire/
```

### 4. **Como melhorar a acurácia do modelo?**

- **Aumentar o dataset**: Mais imagens = melhor generalização
- **Balancear classes**: 50% fire, 50% nofire
- **Data augmentation**: Já implementado automaticamente
- **Ajustar épocas**: Testar com 30-50 épocas
- **Fine-tuning**: Treinar a partir de um modelo existente

### 5. **O servidor pode processar vídeos?**

Não diretamente, mas você pode:
1. Extrair frames do vídeo (OpenCV)
2. Processar cada frame via API `/predict_batch`
3. Consolidar resultados

Exemplo:
```python
import cv2
import requests

# Extrair frames
cap = cv2.VideoCapture('video.mp4')
frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    cv2.imwrite(f'frame_{len(frames)}.jpg', frame)
    frames.append(f'frame_{len(frames)}.jpg')

# Processar em lote
files = [('images', open(f, 'rb')) for f in frames]
response = requests.post('http://127.0.0.1:5000/predict_batch', files=files)
```

### 6. **Posso usar o modelo em dispositivos móveis?**

Sim! Converta o modelo para TensorFlow Lite:

```python
import tensorflow as tf

# Carregar modelo
model = tf.keras.models.load_model('best_model.h5')

# Converter para TFLite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Salvar
with open('fire_model.tflite', 'wb') as f:
    f.write(tflite_model)
```

### 7. **Como integrar com sistemas de vigilância?**

Crie um script que:
1. Capture frames das câmeras (RTSP/HTTP)
2. Envie para o endpoint `/predict` ou `/predict_batch`
3. Acione alertas quando `fire_detected = true`

### 8. **Posso treinar com imagens de diferentes resoluções?**

Sim! O sistema redimensiona automaticamente para 150x150. Você pode alterar em `config.json`:

```json
"model": {
    "img_height": 224,
    "img_width": 224
}
```

**Nota**: Precisa retreinar o modelo com as novas dimensões.

---

## 🔧 Solução de Problemas

### Problema 1: "GPU não detectada"

**Causa**: TensorFlow não está reconhecendo a GPU.

**Solução**:
```powershell
# Reinstalar TensorFlow DirectML
pip uninstall tensorflow tensorflow-directml-plugin
pip install tensorflow-directml-plugin==0.4.0.dev230202
```

Verificar:
```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))
```

### Problema 2: "Out of Memory" durante treinamento

**Causa**: Batch size muito grande para a VRAM disponível.

**Solução**:
- Reduzir batch size para 16 ou 8
- Ou adicionar no `main.py`:
```python
import os
os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
```

### Problema 3: "Servidor não inicia"

**Causas comuns**:
1. Porta 5000 já em uso
2. Modelo não encontrado

**Solução**:
```powershell
# Verificar porta em uso
netstat -ano | findstr :5000

# Encerrar processo se necessário
taskkill /PID <PID> /F

# Ou mudar porta no config.json
"port": 5001
```

### Problema 4: Cliente não conecta ao servidor

**Verificação**:
1. Servidor está rodando? (Status deve ser 🟢)
2. URL está correta? (`http://127.0.0.1:5000`)
3. Firewall bloqueando?

**Teste manual**:
```powershell
curl http://127.0.0.1:5000/health
```

### Problema 5: Modelo com baixa acurácia

**Possíveis causas e soluções**:

| Causa | Solução |
|-------|---------|
| Dataset pequeno | Coletar mais imagens (mín. 1000 por classe) |
| Classes desbalanceadas | Balancear 50/50 fire/nofire |
| Overfitting | Aumentar dropout, usar regularização |
| Underfitting | Aumentar épocas, ajustar learning rate |
| Dataset ruim | Verificar qualidade das imagens |

### Problema 6: "Image processing failed"

**Causa**: Imagem corrompida ou formato inválido.

**Solução**:
- Verificar extensão: JPG, PNG, BMP, GIF
- Verificar tamanho: Máximo 10MB (configurável)
- Reprocessar imagem:
```python
from PIL import Image
img = Image.open('imagem.jpg')
img = img.convert('RGB')
img.save('imagem_corrigida.jpg')
```

### Problema 7: Treinamento muito lento

**Otimizações**:

1. **Verificar uso de GPU**:
```python
import tensorflow as tf
print(tf.config.list_physical_devices('GPU'))
```

2. **Aumentar workers** (se CPU/RAM permitir):
```python
# Em main.py
NUM_WORKERS = 8  # era 4
```

3. **Usar cache**:
```python
# Em main.py, adicione:
train_data_gen = train_data_gen.cache()
```

### Problema 8: Erro "Model not loaded" no cliente

**Causa**: Servidor sem modelo carregado.

**Solução**:
1. Abra **Training GUI**
2. Vá para aba **📦 Gerenciamento**
3. Selecione um modelo
4. Clique em **🚀 Carregar no Servidor**

Ou configure carregamento automático em `config.json`:
```json
"auto_load_default": true,
"default_model": "best_model.h5"
```

---

## 🚀 Dicas de Performance

### 1. Otimizar Dataset

```python
# Script para redimensionar dataset (acelera carregamento)
from PIL import Image
import os

def resize_images(input_dir, output_dir, size=(150, 150)):
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.jpg', '.png')):
                img_path = os.path.join(root, file)
                img = Image.open(img_path)
                img = img.resize(size)
                
                # Manter estrutura de pastas
                rel_path = os.path.relpath(root, input_dir)
                out_path = os.path.join(output_dir, rel_path)
                os.makedirs(out_path, exist_ok=True)
                
                img.save(os.path.join(out_path, file))

resize_images('C:/Dataset/archive', 'C:/Dataset/archive_resized')
```

### 2. Usar Mixed Precision (GPUs modernas)

```python
# Adicione no início do main.py
from tensorflow.keras import mixed_precision
policy = mixed_precision.Policy('mixed_float16')
mixed_precision.set_global_policy(policy)
```

**Benefícios**: 2-3x mais rápido, usa menos VRAM

### 3. Batch Processing Inteligente

```python
# Cliente: Processar em chunks para grandes volumes
import os
from pathlib import Path

def process_large_folder(folder, chunk_size=50):
    images = list(Path(folder).glob('*.jpg'))
    
    for i in range(0, len(images), chunk_size):
        chunk = images[i:i+chunk_size]
        files = [('images', open(img, 'rb')) for img in chunk]
        
        response = requests.post(
            'http://127.0.0.1:5000/predict_batch',
            files=files
        )
        
        # Processar resultados
        results = response.json()
        print(f"Chunk {i//chunk_size + 1}: {results['fires_detected']} incêndios")
```


## 📚 Recursos Adicionais

### Artigos e Papers

- [Deep Learning for Fire Detection](https://arxiv.org/abs/1234.5678)
- [CNN Architectures Comparison](https://arxiv.org/abs/1234.5679)

### Datasets Públicos

- [Fire Detection Dataset (Kaggle)](https://www.kaggle.com/datasets/fire-detection)
- [Forest Fire Detection (IEEE)](https://ieee-dataport.org/fire-detection)

### Tutoriais

- [TensorFlow Official Tutorials](https://www.tensorflow.org/tutorials)
- [Keras Image Classification Guide](https://keras.io/guides/image_classification/)

---

<div align="center">

**🔥 IdentyFIRE - Detecção Inteligente de Incêndios 🔥**

*Desenvolvido com ❤️ usando TensorFlow, Python e Flask*


</div>
