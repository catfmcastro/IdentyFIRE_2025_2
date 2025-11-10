@echo off
REM ============================================================================
REM IdentyFIRE - Script para Disparar Job de Treinamento
REM ============================================================================
REM Este script permite submeter um novo job de treinamento via gRPC
REM Certifique-se de que training_service.py esta rodando antes de usar este script
REM ============================================================================

setlocal enabledelayedexpansion

REM Diretórios
set "VENV_DIR=.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
REM Caminho default para o dataset (pode ser relativo)
set "DEFAULT_DATASET=dataset"

cls
echo.
echo ============================================================================
echo   IdentyFIRE - Disparador de Job de Treinamento
echo ============================================================================
echo.

REM Verificar se o ambiente virtual existe
if not exist "%VENV_DIR%" (
    echo [ERRO] Ambiente virtual nao encontrado.
    echo [ACAO] Execute start_all.bat primeiro para configurar o ambiente.
    pause
    exit /b 1
)

echo [INFO] Ativando ambiente virtual...
call "%VENV_DIR%\Scripts\activate.bat"

REM Verificar se training_service esta rodando
echo [INFO] Verificando se Training Service esta rodando (porta 50052)...
%VENV_PYTHON% -c "import socket; s = socket.socket(); s.connect(('localhost', 50052)); s.close()" >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Training Service nao esta respondendo em localhost:50052
    echo [DICA] Inicie todos os servicos com start_all.bat primeiro
    pause
    exit /b 1
)
echo [OK] Training Service esta rodando.

echo.
echo ============================================================================
echo   Configuracao do Job de Treinamento
echo ============================================================================
echo.

REM Detectar automaticamente o dataset (não solicitar input do usuário)
set "DATASET_PATH="

echo [INFO] Tentando detectar dataset automaticamente...

REM 1) Verifica pasta padrão
if exist "%DEFAULT_DATASET%\train" (
    for %%I in ("%DEFAULT_DATASET%") do set "DATASET_PATH=%%~fI"
    goto :found_dataset
)

REM 2) Procurar qualquer pasta no diretório atual que contenha train/ valid/ test
for /d %%D in (*) do (
    if exist "%%D\train" if exist "%%D\valid" if exist "%%D\test" (
        set "DATASET_PATH=%%~fD"
        goto :found_dataset
    )
)

echo [ERRO] Nenhum dataset com estrutura esperada (train/ valid/ test) foi encontrado no diretório do projeto.
echo [ACAO] Coloque a pasta do dataset na raiz do projeto com a estrutura: dataset\train, dataset\valid, dataset\test
pause
exit /b 1

:found_dataset
echo [OK] Dataset detectado automaticamente em: "%DATASET_PATH%"

echo.

REM Solicitar número de épocas
set "EPOCHS=25"
echo [OPCIONAL] Numero de epocas para treinamento (padrao: 25)
set /p EPOCHS="Digite o numero (ou pressione Enter para usar padrao): "

if "!EPOCHS!"=="" (
    set "EPOCHS=25"
)

REM Validar que é um número
for /f %%A in ('powershell -command "[int]::TryParse('!EPOCHS!', [ref]$null) -and !EPOCHS! -gt 0"') do (
    if not "%%A"=="True" (
        echo [ERRO] Numero de epocas invalido
        set "EPOCHS=25"
    )
)

echo [OK] Epocas definidas para: !EPOCHS!

echo.
echo ============================================================================
echo   Criando arquivo temporario de cliente...
echo ============================================================================
echo.

REM Criar arquivo Python temporário para disparar o job
set "TEMP_SCRIPT=%temp%\trigger_training_temp.py"

(
    echo import grpc
    echo import identyfire_pb2
    echo import identyfire_pb2_grpc
    echo import time
    echo import sys
    echo import os
    echo.
    echo def submit_training_job(dataset_path, epochs):
    echo     try:
    echo         channel = grpc.insecure_channel('localhost:50052')
    echo         stub = identyfire_pb2_grpc.TrainingServiceStub(channel)
    echo.
    echo         print("[INFO] Submetendo job de treinamento...")
    echo         req = identyfire_pb2.TrainRequest(dataset_uri=dataset_path, epochs=epochs)
    echo         resp = stub.SubmitTrainingJob(req)
    echo.
    echo         job_id = resp.job_id
    echo         print(f"[OK] Job submetido com sucesso!")
    echo         print(f"[INFO] Job ID: {job_id}")
    echo         print()
    echo.
    echo         # Polling do status
    echo         print("[INFO] Monitorando status do treinamento...")
    echo         print("[DICA] Pode fechar esta janela a qualquer momento.")
    echo         print()
    echo.
    echo         max_attempts = 999  # Very high limit
    echo         attempt = 0
    echo.
    echo         while attempt ^< max_attempts:
    echo             try:
    echo                 status_req = identyfire_pb2.JobStatusRequest(job_id=job_id)
    echo                 status_resp = stub.GetJobStatus(status_req)
    echo.
    echo                 state_name = identyfire_pb2.JobStatusResponse.State.Name(status_resp.state)
    echo                 logs_path = status_resp.logs_path
    echo.
    echo                 print(f"[{time.strftime('%%H:%%M:%%S')}] Status: {state_name:12} | Logs: {logs_path}")
    echo.
    echo                 if state_name in ["COMPLETED", "FAILED"]:
    echo                     print()
    echo                     print("[RESULTADO]")
    echo                     print(f"  Estado final: {state_name}")
    echo                     print(f"  Artefatos salvos em: {logs_path}")
    echo                     if state_name == "COMPLETED":
    echo                         model_path = os.path.join(os.path.dirname(logs_path), "IdentyFIRE.h5")
    echo                         print(f"  Modelo: {model_path}")
    echo                     break
    echo.
    echo                 time.sleep(5)
    echo                 attempt += 1
    echo.
    echo             except grpc.RpcError as e:
    echo                 print(f"[ERRO] Falha ao consultar status: {e.details()}")
    echo                 time.sleep(5)
    echo                 attempt += 1
    echo.
    echo     except grpc.RpcError as e:
    echo         print(f"[ERRO] Falha ao submeter job: {e.details()}")
    echo         return False
    echo     except Exception as e:
    echo         print(f"[ERRO] Erro inesperado: {str(e)}")
    echo         return False
    echo.
    echo     return True
    echo.
    echo if __name__ == "__main__":
    echo     dataset = sys.argv[1] if len(sys.argv^) ^> 1 else ""
    echo     epochs = int(sys.argv[2]) if len(sys.argv^) ^> 2 else 25
    echo     success = submit_training_job(dataset, epochs)
    echo     sys.exit(0 if success else 1)
) > "%TEMP_SCRIPT%"

echo [INFO] Executando cliente de treinamento...
echo.

%VENV_PYTHON% "%TEMP_SCRIPT%" "!DATASET_PATH!" !EPOCHS!

set "EXIT_CODE=!ERRORLEVEL!"

echo.
echo ============================================================================
echo   Operacao concluida
echo ============================================================================
echo.

if !EXIT_CODE! equ 0 (
    echo [OK] Job processado com sucesso.
) else (
    echo [ERRO] Falha ao processar job.
)

REM Limpar arquivo temporário
if exist "%TEMP_SCRIPT%" (
    del "%TEMP_SCRIPT%"
)

echo.
pause
endlocal
exit /b !EXIT_CODE!
