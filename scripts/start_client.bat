@echo off
REM Script para iniciar o Cliente IdentyFire
echo.
echo ========================================
echo   IDENTYFIRE - CLIENTE
echo ========================================
echo.

cd /d "%~dp0.."

REM Verificar se venv existe
if exist ".venv\Scripts\python.exe" (
    set PYTHON_VENV=%CD%\.venv\Scripts\python.exe
) else (
    echo AVISO: Ambiente virtual nao encontrado!
    echo Execute scripts\install.bat primeiro.
    echo.
    pause
    exit /b 1
)

echo Iniciando cliente...
echo.

"%PYTHON_VENV%" src\client_gui.py

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel iniciar o cliente!
    echo.
    pause
)
