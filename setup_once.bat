@echo off
REM ============================================================================
REM IdentyFIRE - Configuração Inicial (Execute APENAS uma vez!)
REM ============================================================================
REM Este script instala TODAS as dependências necessárias
REM Execute este ANTES de usar start_all.bat
REM ============================================================================

setlocal enabledelayedexpansion

set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_PIP=%VENV_DIR%\Scripts\pip.exe"

cls
echo.
echo ============================================================================
echo   IdentyFIRE - Configuracao Inicial (Execute UMA VEZ)
echo ============================================================================
echo.

REM Criar ambiente virtual
if not exist "%VENV_DIR%" (
    echo [INFO] Criando ambiente virtual...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado.
) else (
    echo [OK] Ambiente virtual ja existe.
)

echo.
echo [INFO] Ativando ambiente virtual...
call "%VENV_DIR%\Scripts\activate.bat"

echo.
echo [INFO] Atualizando pip...
%VENV_PIP% install --upgrade pip

echo.
echo [INFO] Instalando dependencias para INFERENCIA (rapido)...
echo   - grpcio
echo   - grpcio-tools
echo   - pillow
echo   - numpy
echo   - matplotlib
%VENV_PIP% install grpcio grpcio-tools pillow numpy matplotlib
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias basicas.
    pause
    exit /b 1
)
echo [OK] Dependencias basicas instaladas!

echo.
echo [OPCAO] Deseja instalar dependencias para TREINAMENTO?
echo   (TensorFlow, scikit-learn, pytest - ~1GB, pode levar alguns minutos)
echo.
set /p TRAIN_DEPS="Digite 'sim' para instalar treinamento, ou Enter para pular: "

if /i "!TRAIN_DEPS!"=="sim" (
    echo.
    echo [INFO] Instalando dependencias para TREINAMENTO...
    echo   - tensorflow
    echo   - scikit-learn
    echo   - pytest
    %VENV_PIP% install tensorflow scikit-learn pytest pytest-cov
    if errorlevel 1 (
        echo [AVISO] Falha ao instalar algumas dependencias de treinamento.
        echo [INFO] Prosseguindo mesmo assim...
    ) else (
        echo [OK] Dependencias de treinamento instaladas!
    )
) else (
    echo [INFO] Pulando dependencias de treinamento.
)

echo.
echo [INFO] Gerando stubs gRPC...
if exist "proto\identyfire.proto" (
    python -m grpc_tools.protoc -I.\proto --python_out=. --grpc_python_out=. .\proto\identyfire.proto
    if errorlevel 1 (
        echo [ERRO] Falha ao gerar stubs gRPC.
        pause
        exit /b 1
    )
    echo [OK] Stubs gRPC gerados!
) else (
    echo [ERRO] proto\identyfire.proto nao encontrado.
    pause
    exit /b 1
)

echo.
echo [INFO] Criando estrutura de diretorios...
if not exist "models" mkdir models
echo [OK] Diretorio models criado/verificado.

echo.
echo [INFO] Verificando modelo pre-treinado...
if exist "models\latest.h5" (
    echo [OK] models\latest.h5 ja existe.
) else if exist "IdentyFIRE1.h5" (
    echo [INFO] Copiando IdentyFIRE1.h5...
    copy "IdentyFIRE1.h5" "models\latest.h5" >nul
    echo [OK] Modelo copiado.
) else if exist "IdentyFIRE1_Parallel.h5" (
    echo [INFO] Copiando IdentyFIRE1_Parallel.h5...
    copy "IdentyFIRE1_Parallel.h5" "models\latest.h5" >nul
    echo [OK] Modelo copiado.
) else (
    echo [AVISO] Nenhum modelo pre-treinado encontrado.
    echo [DICA] Coloque IdentyFIRE1.h5 ou IdentyFIRE1_Parallel.h5 nesta pasta depois.
)

echo.
echo ============================================================================
echo   Configuracao concluida com sucesso!
echo ============================================================================
echo.
echo [PROXIMOS PASSOS]
echo   1. Execute: start_all.bat
echo   2. Aguarde as 3 janelas abrirem
echo   3. Use a GUI para selecionar imagens
echo.

endlocal
pause
