@echo off
REM IdentyFIRE Network Setup - Batch Wrapper
REM Facilita a configuração de rede para Windows

echo.
echo ============================================
echo   IdentyFIRE - Configuracao de Rede
echo ============================================
echo.
echo Escolha uma opcao:
echo.
echo [1] Configurar SERVIDOR (aceitar conexoes remotas)
echo [2] Testar conexao do CLIENTE ao servidor
echo [3] Ajuda / Instrucoes
echo [0] Sair
echo.

set /p choice="Digite sua escolha (0-3): "

if "%choice%"=="1" goto servidor
if "%choice%"=="2" goto cliente
if "%choice%"=="3" goto ajuda
if "%choice%"=="0" goto fim
goto inicio

:servidor
echo.
echo ============================================
echo Configurando SERVIDOR...
echo ============================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0setup_network.ps1" -Server
goto fim

:cliente
echo.
set /p serverip="Digite o IP do servidor (ex: 192.168.1.100): "
echo.
echo ============================================
echo Testando conexao com %serverip%...
echo ============================================
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0setup_network.ps1" -Client -ServerIP %serverip%
goto fim

:ajuda
echo.
echo ============================================
echo GUIA RAPIDO - CONFIGURACAO MULTI-MAQUINA
echo ============================================
echo.
echo SERVIDOR (Maquina A):
echo   1. Execute esta opcao [1] neste menu
echo   2. Anote o IP mostrado (ex: 192.168.1.100)
echo   3. Inicie o servidor: python src/server_gui.py
echo.
echo CLIENTE (Maquina B):
echo   1. Execute a opcao [2] neste menu
echo   2. Digite o IP do servidor
echo   3. Se tudo OK, inicie: python src/client_gui.py
echo   4. Na GUI, use: http://IP_SERVIDOR:5000
echo.
echo ============================================
echo.
pause
goto inicio

:fim
echo.
pause
