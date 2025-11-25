#!/bin/bash
# Script para instalar dependências do IdentyFire

echo ""
echo "========================================"
echo "   IDENTYFIRE - INSTALAÇÃO"
echo "========================================"
echo ""

cd "$(dirname "$0")/.."

# Verificar se venv existe, se não, criar
if [ ! -d ".venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv .venv
    echo ""
fi

echo "Ativando ambiente virtual..."
source .venv/bin/activate
echo ""

echo "Instalando dependências Python..."
echo ""

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "   INSTALAÇÃO CONCLUÍDA!"
    echo "========================================"
    echo ""
    echo "Executando teste de instalação..."
    echo ""
    
    python tests/test_setup.py
    
    echo ""
    echo "Pressione Enter para sair..."
    read
else
    echo ""
    echo "ERRO: Falha na instalação!"
    echo ""
    read -p "Pressione Enter para sair..."
    exit 1
fi
