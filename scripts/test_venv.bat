@echo off
REM Script para testar o ambiente virtual
echo.
echo ========================================
echo   TESTE DO AMBIENTE VIRTUAL
echo ========================================
echo.

cd /d "%~dp0.."

echo Verificando estrutura do venv...
echo.

if exist ".venv" (
    echo [OK] Pasta .venv existe
) else (
    echo [ERRO] Pasta .venv NAO encontrada!
    goto :error
)

if exist ".venv\Scripts\python.exe" (
    echo [OK] python.exe encontrado
) else (
    echo [ERRO] python.exe NAO encontrado!
    goto :error
)

if exist ".venv\Scripts\pip.exe" (
    echo [OK] pip.exe encontrado
) else (
    echo [AVISO] pip.exe NAO encontrado (pode ser normal)
)

echo.
echo Testando Python do venv...
echo.

set PYTHON_VENV=%CD%\.venv\Scripts\python.exe

echo Caminho: %PYTHON_VENV%
echo.

"%PYTHON_VENV%" --version
if errorlevel 1 (
    echo [ERRO] Nao foi possivel executar o Python!
    goto :error
)

echo.
echo Testando importacoes...
echo.

"%PYTHON_VENV%" -c "import sys; print('Python:', sys.version)"
echo.

"%PYTHON_VENV%" -c "import tensorflow as tf; print('[OK] TensorFlow:', tf.__version__)"
if errorlevel 1 (
    echo [ERRO] TensorFlow nao encontrado!
    goto :error
)

"%PYTHON_VENV%" -c "import PIL; print('[OK] Pillow:', PIL.__version__)"
if errorlevel 1 (
    echo [ERRO] Pillow nao encontrado!
    goto :error
)

"%PYTHON_VENV%" -c "import flask; print('[OK] Flask importado')"
if errorlevel 1 (
    echo [ERRO] Flask nao encontrado!
    goto :error
)

"%PYTHON_VENV%" -c "import requests; print('[OK] Requests importado')"
if errorlevel 1 (
    echo [ERRO] Requests nao encontrado!
    goto :error
)

echo.
echo Verificando GPU...
echo.
"%PYTHON_VENV%" -c "import tensorflow as tf; gpus = tf.config.list_physical_devices('GPU'); print('[INFO] GPUs detectadas:', len(gpus))"

echo.
echo ========================================
echo   TODOS OS TESTES PASSARAM!
echo ========================================
echo.
echo O ambiente virtual esta configurado corretamente.
echo Voce pode usar os scripts em scripts\
echo.
goto :end

:error
echo.
echo ========================================
echo   TESTES FALHARAM!
echo ========================================
echo.
echo Execute: scripts\install.bat
echo.

:end
pause
