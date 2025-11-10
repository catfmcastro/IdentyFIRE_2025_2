@echo off
REM ============================================================================
REM IdentyFIRE - Script de Inicialização de Todos os Serviços (Versão Leve)
REM ============================================================================
REM Este script:
REM   1. Verifica se o ambiente virtual existe
REM   2. Ativa o ambiente virtual
REM   3. Inicia APENAS os servidores gRPC (inferência + treinamento)
REM   4. Inicia a aplicação GUI
REM ============================================================================
REM NOTA: Este script usa APENAS latest.h5, sem treinar novos modelos
REM ============================================================================

setlocal enabledelayedexpansion

REM Diretórios
set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

cls
echo.
echo ============================================================================
echo   IdentyFIRE - Inicializacao Rapida (Usando latest.h5)
echo ============================================================================
echo.

REM Verificar se o ambiente virtual existe
echo [INFO] Verificando ambiente virtual...
if not exist "%VENV_DIR%" (
    echo [ERRO] Ambiente virtual nao encontrado em %VENV_DIR%
    echo.
    echo [ACAO] Criando ambiente virtual...
    python -m venv %VENV_DIR%
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual.
        echo [DICA] Certifique-se de que Python 3.8+ esta instalado.
        pause
        exit /b 1
    )
    echo [OK] Ambiente virtual criado.
) else (
    echo [OK] Ambiente virtual encontrado.
)

echo.
echo [INFO] Ativando ambiente virtual...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERRO] Falha ao ativar ambiente virtual.
    pause
    exit /b 1
)
echo [OK] Ambiente virtual ativado.

REM Verificar se os arquivos necessários existem
echo.
echo [INFO] Verificando arquivos necessarios...

if not exist "proto\identyfire.proto" (
    echo [ERRO] proto\identyfire.proto nao encontrado.
    pause
    exit /b 1
)
echo [OK] proto\identyfire.proto encontrado.

if not exist "identyfire_pb2.py" (
    echo [AVISO] Stubs gRPC nao encontrados. Gerando...
    python -m grpc_tools.protoc -I.\proto --python_out=. --grpc_python_out=. .\proto\identyfire.proto
    if errorlevel 1 (
        echo [ERRO] Falha ao gerar stubs gRPC.
        pause
        exit /b 1
    )
    echo [OK] Stubs gRPC gerados.
) else (
    echo [OK] Stubs gRPC encontrados.
)

if not exist "inference_server.py" (
    echo [ERRO] inference_server.py nao encontrado.
    pause
    exit /b 1
)
echo [OK] inference_server.py encontrado.

if not exist "training_service.py" (
    echo [ERRO] training_service.py nao encontrado.
    pause
    exit /b 1
)
echo [OK] training_service.py encontrado.

if not exist "gui.py" (
    echo [ERRO] gui.py nao encontrado.
    pause
    exit /b 1
)
echo [OK] gui.py encontrado.

REM Verificar se o diretório models existe
if not exist "models" (
    echo [INFO] Criando diretorio models...
    mkdir models
)

REM Verificar modelo latest.h5
if not exist "models\latest.h5" (
    echo [AVISO] models\latest.h5 nao encontrado.
    if exist "IdentyFIRE1.h5" (
        echo [INFO] Copiando IdentyFIRE1.h5 para models\latest.h5...
        copy "IdentyFIRE1.h5" "models\latest.h5" >nul
        echo [OK] Modelo copiado.
    ) else if exist "IdentyFIRE1_Parallel.h5" (
        echo [INFO] Copiando IdentyFIRE1_Parallel.h5 para models\latest.h5...
        copy "IdentyFIRE1_Parallel.h5" "models\latest.h5" >nul
        echo [OK] Modelo copiado.
    ) else (
        echo [ERRO] Modelo pre-treinado nao encontrado.
        echo [DICA] Coloque IdentyFIRE1.h5 ou IdentyFIRE1_Parallel.h5 nesta pasta.
        pause
        exit /b 1
    )
) else (
    echo [OK] models\latest.h5 encontrado.
)

echo.
echo ============================================================================
echo   Pre-requisitos verificados com sucesso!
echo ============================================================================
echo.
echo [INFO] Inicializando servidores...
echo.
echo Este script abrira 3 janelas de terminal:
echo   1. Inference Server (porta 50051) - Processamento de imagens
echo   2. Training Service (porta 50052)  - Gerenciamento de treinamento
echo   3. GUI (cliente)                   - Interface grafica
echo.
echo [DICA] Feche a janela do comando (ou pressione Ctrl+C) para parar tudo.
echo.
pause

REM Iniciar os servidores em janelas separadas
echo [INFO] Iniciando Inference Server em nova janela...
start "IdentyFIRE - Inference Server" cmd /k "cd /d "%cd%" && call %VENV_DIR%\Scripts\activate.bat && python inference_server.py"

REM Aguardar um pouco para o servidor de inferência inicializar
timeout /t 3 /nobreak

echo [INFO] Iniciando Training Service em nova janela...
start "IdentyFIRE - Training Service" cmd /k "cd /d "%cd%" && call %VENV_DIR%\Scripts\activate.bat && python training_service.py"

REM Aguardar um pouco para o servidor de treinamento inicializar
timeout /t 2 /nobreak

echo [INFO] Iniciando GUI em nova janela...
start "IdentyFIRE - GUI" cmd /k "cd /d "%cd%" && call %VENV_DIR%\Scripts\activate.bat && python gui.py"

echo.
echo [OK] Todos os servicos foram iniciados!
echo.
echo [PROXIMOS PASSOS]
echo   1. A interface grafica (GUI) deve abrir em breve
echo   2. Use a GUI para selecionar imagens e fazer predicoes
echo.
echo [INFORMACOES]
echo   - Inference Server: localhost:50051
echo   - Training Service: localhost:50052
echo   - Janelas abertas:
echo     * IdentyFIRE - Inference Server (nao feche!)
echo     * IdentyFIRE - Training Service  (nao feche!)
echo     * IdentyFIRE - GUI              (interface principal)
echo.

endlocal
pause
