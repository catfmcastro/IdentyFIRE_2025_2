@echo off
REM ============================================================================
REM IdentyFIRE - Menu de Gerenciamento
REM ============================================================================
REM Menu interativo para iniciar/parar servicos ou executar outras acoes
REM ============================================================================

setlocal enabledelayedexpansion

:menu
cls
echo.
echo ============================================================================
echo   IdentyFIRE - Menu de Gerenciamento
echo ============================================================================
echo.
echo 1. Iniciar todos os servicos (GUI + Servers)
echo 2. Iniciar apenas o Inference Server (porta 50051)
echo 3. Iniciar apenas o Training Service (porta 50052)
echo 4. Disparar novo job de treinamento
echo 5. Abrir GUI (conecta aos servidores existentes)
echo 6. Verificar dependencias
echo 7. Regenerar stubs gRPC
echo 8. Configurar ambiente inicial
echo 0. Sair
echo.
set /p choice="Escolha uma opcao (0-8): "

if "!choice!"=="1" goto start_all
if "!choice!"=="2" goto start_inference
if "!choice!"=="3" goto start_training
if "!choice!"=="4" goto trigger_training
if "!choice!"=="5" goto start_gui
if "!choice!"=="6" goto check_deps
if "!choice!"=="7" goto regen_proto
if "!choice!"=="8" goto setup
if "!choice!"=="0" goto end

echo [ERRO] Opcao invalida
pause
goto menu

:start_all
echo.
echo [INFO] Iniciando todos os servicos...
call start_all.bat
goto menu

:start_inference
echo.
echo [INFO] Iniciando Inference Server...
set VENV_DIR=.venv
if not exist "%VENV_DIR%" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute opcao 8 primeiro.
    pause
    goto menu
)
call "%VENV_DIR%\Scripts\activate.bat"
start "IdentyFIRE - Inference Server" cmd /k "cd /d "%cd%" && python inference_server.py"
echo [OK] Inference Server iniciado em nova janela
pause
goto menu

:start_training
echo.
echo [INFO] Iniciando Training Service...
set VENV_DIR=.venv
if not exist "%VENV_DIR%" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute opcao 8 primeiro.
    pause
    goto menu
)
call "%VENV_DIR%\Scripts\activate.bat"
start "IdentyFIRE - Training Service" cmd /k "cd /d "%cd%" && python training_service.py"
echo [OK] Training Service iniciado em nova janela
pause
goto menu

:trigger_training
echo.
call start_training.bat
goto menu

:start_gui
echo.
echo [INFO] Iniciando GUI...
set VENV_DIR=.venv
if not exist "%VENV_DIR%" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute opcao 8 primeiro.
    pause
    goto menu
)
call "%VENV_DIR%\Scripts\activate.bat"
python gui.py
goto menu

:check_deps
echo.
echo [INFO] Verificando dependencias...
set VENV_DIR=.venv
if not exist "%VENV_DIR%" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute opcao 8 primeiro.
    pause
    goto menu
)
call "%VENV_DIR%\Scripts\activate.bat"

set "DEPENDENCIES=grpcio grpcio-tools tensorflow pillow numpy matplotlib scikit-learn"
echo.
echo Pacotes necessarios:
echo.

set "MISSING="
for %%P in (%DEPENDENCIES%) do (
    "%VENV_DIR%\Scripts\python.exe" -c "import %%P" >nul 2>&1
    if errorlevel 1 (
        echo [X] %%P (faltando)
        set "MISSING=1"
    ) else (
        echo [OK] %%P
    )
)

if "!MISSING!"=="1" (
    echo.
    echo [AVISO] Alguns pacotes estao faltando.
    echo [INFO] Instalando...
    "%VENV_DIR%\Scripts\pip.exe" install %DEPENDENCIES%
) else (
    echo.
    echo [OK] Todas as dependencias estao instaladas!
)

pause
goto menu

:regen_proto
echo.
echo [INFO] Regenerando stubs gRPC...
set VENV_DIR=.venv
if not exist "%VENV_DIR%" (
    echo [ERRO] Ambiente virtual nao encontrado. Execute opcao 8 primeiro.
    pause
    goto menu
)
call "%VENV_DIR%\Scripts\activate.bat"

if not exist "proto\identyfire.proto" (
    echo [ERRO] Arquivo proto/identyfire.proto nao encontrado.
    pause
    goto menu
)

echo [INFO] Executando: python -m grpc_tools.protoc...
python -m grpc_tools.protoc -I.\proto --python_out=. --grpc_python_out=. .\proto\identyfire.proto

if errorlevel 1 (
    echo [ERRO] Falha ao regenerar stubs gRPC.
) else (
    echo [OK] Stubs gRPC regenerados com sucesso!
    echo   - identyfire_pb2.py
    echo   - identyfire_pb2_grpc.py
)

pause
goto menu

:setup
echo.
echo ============================================================================
echo   Configuracao Inicial do Ambiente
echo ============================================================================
echo.
echo [INFO] Criando ambiente virtual...

if exist ".venv" (
    echo [AVISO] Ambiente virtual ja existe. Pulando criacao.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual.
        echo [DICA] Certifique-se de que Python 3.8+ esta instalado e disponivel no PATH.
        pause
        goto menu
    )
    echo [OK] Ambiente virtual criado.
)

echo.
echo [INFO] Ativando ambiente virtual...
call ".venv\Scripts\activate.bat"

echo.
echo [INFO] Atualizando pip...
".venv\Scripts\pip.exe" install --upgrade pip >nul

echo.
echo [INFO] Instalando dependencias...
set "DEPENDENCIES=grpcio grpcio-tools tensorflow pillow numpy matplotlib scikit-learn pytest"
".venv\Scripts\pip.exe" install %DEPENDENCIES%

if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    goto menu
)

echo.
echo [INFO] Gerando stubs gRPC...
if not exist "proto\identyfire.proto" (
    echo [ERRO] Arquivo proto/identyfire.proto nao encontrado.
    pause
    goto menu
)

python -m grpc_tools.protoc -I.\proto --python_out=. --grpc_python_out=. .\proto\identyfire.proto

if errorlevel 1 (
    echo [ERRO] Falha ao gerar stubs gRPC.
    pause
    goto menu
)

echo.
echo [INFO] Criando diretorio models...
if not exist "models" (
    mkdir models
)

echo.
echo [INFO] Procurando modelo pre-treinado...
if exist "IdentyFIRE1.h5" (
    echo [OK] Copiando IdentyFIRE1.h5 para models\latest.h5
    copy "IdentyFIRE1.h5" "models\latest.h5" >nul
) else if exist "IdentyFIRE1_Parallel.h5" (
    echo [OK] Copiando IdentyFIRE1_Parallel.h5 para models\latest.h5
    copy "IdentyFIRE1_Parallel.h5" "models\latest.h5" >nul
) else (
    echo [AVISO] Nenhum modelo pre-treinado encontrado.
    echo [DICA] Coloque IdentyFIRE1.h5 ou IdentyFIRE1_Parallel.h5 neste diretorio.
)

echo.
echo ============================================================================
echo   Configuracao concluida com sucesso!
echo ============================================================================
echo.
echo [PROXIMOS PASSOS]
echo   1. Volte ao menu (opcao 1)
echo   2. Escolha "Iniciar todos os servicos"
echo.

pause
goto menu

:end
echo.
echo [INFO] Encerrando menu de gerenciamento.
echo.
endlocal
exit /b 0
