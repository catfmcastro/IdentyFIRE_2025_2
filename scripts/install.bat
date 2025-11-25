@echo off
REM Script para instalar dependencias do IdentyFire
echo.
echo ========================================
echo   IDENTYFIRE - INSTALACAO
echo ========================================
echo.

cd /d "%~dp0.."

REM Verificar se venv existe, se nao, criar
if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo.
        echo ERRO: Nao foi possivel criar o ambiente virtual!
        echo Verifique se o Python esta instalado corretamente.
        pause
        exit /b 1
    )
    echo.
)

set PYTHON_VENV=%CD%\.venv\Scripts\python.exe
set PIP_VENV=%CD%\.venv\Scripts\pip.exe

echo Usando Python do venv: %PYTHON_VENV%
echo.

echo Instalando dependencias Python...
echo.

"%PIP_VENV%" install --upgrade pip
"%PIP_VENV%" install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERRO: Falha na instalacao!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   INSTALACAO CONCLUIDA!
echo ========================================
echo.
echo Executando teste de instalacao...
echo.

if exist "tests\test_setup.py" (
    "%PYTHON_VENV%" tests\test_setup.py
) else (
    echo.
    echo Testando importacoes...
    "%PYTHON_VENV%" -c "import tensorflow as tf; import PIL; import flask; import requests; print('Instalacao OK!')"
)

echo.
echo Pressione qualquer tecla para sair...
pause > nul
