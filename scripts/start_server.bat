@echo off
REM Script para iniciar o Servidor IdentyFire
echo.
echo ========================================
echo   IDENTYFIRE - SERVIDOR
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

echo Iniciando servidor...
echo.

"%PYTHON_VENV%" src\server_gui.py

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel iniciar o servidor!
    echo.
    pause
)
