@echo off
REM Script para instalar dependencias do IdentyFire
echo.
echo ========================================
echo   IDENTYFIRE - INSTALACAO
echo ========================================
echo.

cd /d "%~dp0.."

REM Verificar se venv existe, se nao, criar
if not exist ".venv" (
    echo Criando ambiente virtual...
    python -m venv .venv
    echo.
)

echo Ativando ambiente virtual...
call .venv\Scripts\activate.bat
echo.

echo Instalando dependencias Python...
echo.

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

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

python tests\test_setup.py

echo.
echo Pressione qualquer tecla para sair...
pause > nul
