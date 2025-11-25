#!/bin/bash
# Script para iniciar o Treinamento IdentyFire

echo ""
echo "========================================"
echo "   IDENTYFIRE - TREINAMENTO"
echo "========================================"
echo ""

cd "$(dirname "$0")/.."

# Ativar ambiente virtual
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
else
    echo "AVISO: Ambiente virtual não encontrado!"
    echo "Execute scripts/install.sh primeiro."
    echo ""
    read -p "Pressione Enter para sair..."
    exit 1
fi

echo "Iniciando interface de treinamento..."
echo ""

python src/training_gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERRO: Não foi possível iniciar o treinamento!"
    echo ""
    read -p "Pressione Enter para sair..."
fi
