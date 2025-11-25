@echo off
REM Script para ativar o ambiente virtual
cd /d "%~dp0.."

if exist ".venv\Scripts\activate.bat" (
    echo.
    echo ========================================
    echo   ATIVANDO AMBIENTE VIRTUAL
    echo ========================================
    echo.
    call .venv\Scripts\activate.bat
    echo.
    echo Ambiente virtual ativado!
    echo Para desativar, digite: deactivate
    echo.
) else (
    echo.
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute scripts\install.bat primeiro para criar o venv.
    echo.
    pause
)
