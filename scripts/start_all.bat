@echo off
REM Script para executar todos os componentes do IdentyFire
echo.
echo ========================================
echo   IDENTYFIRE - INICIAR TUDO
echo ========================================
echo.

cd /d "%~dp0.."

REM Verificar se venv existe
if not exist ".venv\Scripts\python.exe" (
    echo ERRO: Ambiente virtual nao encontrado!
    echo Execute scripts\install.bat primeiro.
    echo.
    pause
    exit /b 1
)

set PYTHON_VENV=%CD%\.venv\Scripts\python.exe

echo Iniciando Servidor em nova janela...
start "IdentyFire - Servidor" cmd /k "cd /d %CD% && "%PYTHON_VENV%" src\server_gui.py"

timeout /t 3 /nobreak > nul

echo Iniciando Cliente em nova janela...
start "IdentyFire - Cliente" cmd /k "cd /d %CD% && "%PYTHON_VENV%" src\client_gui.py"

timeout /t 2 /nobreak > nul

echo Iniciando Treinamento em nova janela...
start "IdentyFire - Treinamento" cmd /k "cd /d %CD% && "%PYTHON_VENV%" src\training_gui.py"

echo.
echo ========================================
echo   TODOS OS COMPONENTES INICIADOS!
echo ========================================
echo.
echo Feche esta janela quando terminar.
echo.
pause
