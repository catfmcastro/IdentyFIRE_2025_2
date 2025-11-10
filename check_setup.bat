@echo off
REM ============================================================================
REM IdentyFIRE - Arquivo de Verificação Rápida
REM ============================================================================
REM Este arquivo verifica tudo está configurado e pronto para uso
REM ============================================================================

cls
echo.
echo ============================================================================
echo   IdentyFIRE - Verificacao de Configuracao
echo ============================================================================
echo.

REM Verificar arquivos críticos
echo [VERIFICACAO] Arquivos Principais
echo.

if exist "start_all.bat" (
    echo [OK] start_all.bat encontrado
) else (
    echo [ERRO] start_all.bat NAO encontrado
)

if exist "start_training.bat" (
    echo [OK] start_training.bat encontrado
) else (
    echo [ERRO] start_training.bat NAO encontrado
)

if exist "menu.bat" (
    echo [OK] menu.bat encontrado
) else (
    echo [ERRO] menu.bat NAO encontrado
)

if exist "README.md" (
    echo [OK] README.md encontrado
) else (
    echo [ERRO] README.md NAO encontrado
)

if exist "QUICKSTART.txt" (
    echo [OK] QUICKSTART.txt encontrado
) else (
    echo [ERRO] QUICKSTART.txt NAO encontrado
)

if exist "SUMMARY.md" (
    echo [OK] SUMMARY.md encontrado
) else (
    echo [ERRO] SUMMARY.md NAO encontrado
)

echo.
echo [VERIFICACAO] Servidores
echo.

if exist "inference_server.py" (
    echo [OK] inference_server.py encontrado
) else (
    echo [ERRO] inference_server.py NAO encontrado
)

if exist "training_service.py" (
    echo [OK] training_service.py encontrado
) else (
    echo [ERRO] training_service.py NAO encontrado
)

if exist "gui.py" (
    echo [OK] gui.py encontrado
) else (
    echo [ERRO] gui.py NAO encontrado
)

if exist "main.py" (
    echo [OK] main.py encontrado
) else (
    echo [ERRO] main.py NAO encontrado
)

echo.
echo [VERIFICACAO] Testes
echo.

if exist "test_inference.py" (
    echo [OK] test_inference.py encontrado
) else (
    echo [ERRO] test_inference.py NAO encontrado
)

if exist "test_training.py" (
    echo [OK] test_training.py encontrado
) else (
    echo [ERRO] test_training.py NAO encontrado
)

echo.
echo [VERIFICACAO] Configuracao gRPC
echo.

if exist "proto\identyfire.proto" (
    echo [OK] proto\identyfire.proto encontrado
) else (
    echo [ERRO] proto\identyfire.proto NAO encontrado
)

if exist "identyfire_pb2.py" (
    echo [OK] identyfire_pb2.py (stubs) encontrado
) else (
    echo [ERRO] identyfire_pb2.py NAO encontrado
)

if exist "identyfire_pb2_grpc.py" (
    echo [OK] identyfire_pb2_grpc.py (stubs) encontrado
) else (
    echo [ERRO] identyfire_pb2_grpc.py NAO encontrado
)

echo.
echo [VERIFICACAO] Modelos
echo.

if exist "models" (
    echo [OK] Diretorio models encontrado
) else (
    echo [ERRO] Diretorio models NAO encontrado
)

if exist "models\latest.h5" (
    echo [OK] models\latest.h5 encontrado
) else (
    echo [AVISO] models\latest.h5 NAO encontrado
    echo [DICA] Execute start_all.bat para configurar
)

echo.
echo ============================================================================
echo   RECOMENDACOES DE PROXIMO PASSO
echo ============================================================================
echo.
echo Para comecal a usar IdentyFIRE, escolha uma das opcoes:
echo.
echo 1. FORMA MAIS RAPIDA (Recomendado):
echo    Double-click em: start_all.bat
echo.
echo 2. MENU DE CONTROLE:
echo    Double-click em: menu.bat
echo.
echo 3. MAIS INFORMACOES:
echo    Abra com editor de texto: QUICKSTART.txt
echo    Abra com navegador: README.md
echo.
echo ============================================================================
echo.
pause
