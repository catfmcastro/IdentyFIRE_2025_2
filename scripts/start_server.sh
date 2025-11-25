#!/bin/bash
# Script para iniciar o Servidor IdentyFire

echo ""
echo "========================================"
echo "   IDENTYFIRE - SERVIDOR"
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

echo "Iniciando servidor..."
echo ""

python src/server_gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERRO: Não foi possível iniciar o servidor!"
    echo ""
    read -p "Pressione Enter para sair..."
fi
