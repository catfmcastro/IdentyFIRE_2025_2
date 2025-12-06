@echo off
REM Script para iniciar o Treinamento IdentyFire
echo.
echo ========================================
echo   IDENTYFIRE - TREINAMENTO
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

echo Iniciando interface de treinamento...
echo.

"%PYTHON_VENV%" src\training_gui.py

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel iniciar o treinamento!
    echo.
    pause
)
