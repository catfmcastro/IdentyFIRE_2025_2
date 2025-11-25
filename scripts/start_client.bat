@echo off
REM Script para iniciar o Cliente IdentyFire
echo.
echo ========================================
echo   IDENTYFIRE - CLIENTE
echo ========================================
echo.

cd /d "%~dp0.."

REM Ativar ambiente virtual
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo AVISO: Ambiente virtual nao encontrado!
    echo Execute scripts\install.bat primeiro.
    echo.
    pause
    exit /b 1
)

echo Iniciando cliente...
echo.

python src\client_gui.py

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel iniciar o cliente!
    echo.
    pause
)
