@echo off
REM Script para iniciar o Servidor IdentyFire
echo.
echo ========================================
echo   IDENTYFIRE - SERVIDOR
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

echo Iniciando servidor...
echo.

python src\server_gui.py

if errorlevel 1 (
    echo.
    echo ERRO: Nao foi possivel iniciar o servidor!
    echo.
    pause
)
