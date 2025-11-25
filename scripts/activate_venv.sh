#!/bin/bash
# Script para ativar o ambiente virtual

cd "$(dirname "$0")/.."

if [ -f ".venv/bin/activate" ]; then
    echo ""
    echo "========================================"
    echo "   ATIVANDO AMBIENTE VIRTUAL"
    echo "========================================"
    echo ""
    source .venv/bin/activate
    echo ""
    echo "Ambiente virtual ativado!"
    echo "Para desativar, digite: deactivate"
    echo ""
    # Manter shell aberto
    exec $SHELL
else
    echo ""
    echo "ERRO: Ambiente virtual não encontrado!"
    echo "Execute scripts/install.sh primeiro para criar o venv."
    echo ""
    read -p "Pressione Enter para sair..."
fi
