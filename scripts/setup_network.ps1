# IdentyFIRE Network Setup Script
# Configura o servidor para aceitar conexões de rede

param(
    [switch]$Server,
    [switch]$Client,
    [string]$ServerIP
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "   IdentyFIRE - Configuração de Rede" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ==================== MODO SERVIDOR ====================
if ($Server) {
    Write-Host "[SERVIDOR] Configurando para aceitar conexões remotas...`n" -ForegroundColor Yellow
    
    # 1. Mostrar IP atual
    Write-Host "1. Descobrindo endereço IP da rede..." -ForegroundColor White
    $ip = Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*" -or $_.IPAddress -like "10.*"} | Select-Object -First 1
    
    if ($ip) {
        Write-Host "   ✓ IP encontrado: " -NoNewline -ForegroundColor Green
        Write-Host $ip.IPAddress -ForegroundColor Cyan
        Write-Host "   Interface: $($ip.InterfaceAlias)`n" -ForegroundColor Gray
    } else {
        Write-Host "   ⚠ Não foi possível detectar IP de rede local" -ForegroundColor Red
        Write-Host "   Verifique sua conexão WiFi/Ethernet`n" -ForegroundColor Yellow
        exit
    }
    
    # 2. Verificar config.json
    Write-Host "2. Verificando config.json..." -ForegroundColor White
    $configPath = "..\config.json"
    
    if (Test-Path $configPath) {
        $config = Get-Content $configPath | ConvertFrom-Json
        $currentHost = $config.server.host
        
        Write-Host "   Host atual: $currentHost" -ForegroundColor Gray
        
        if ($currentHost -eq "0.0.0.0") {
            Write-Host "   ✓ Já configurado para aceitar conexões remotas`n" -ForegroundColor Green
        } else {
            Write-Host "   ⚠ Necessário alterar host para 0.0.0.0" -ForegroundColor Yellow
            
            $confirm = Read-Host "   Deseja atualizar automaticamente? (S/N)"
            if ($confirm -eq "S" -or $confirm -eq "s") {
                $config.server.host = "0.0.0.0"
                $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
                Write-Host "   ✓ config.json atualizado!`n" -ForegroundColor Green
            } else {
                Write-Host "   → Edite manualmente: `"host`": `"0.0.0.0`"`n" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "   ⚠ config.json não encontrado em $configPath`n" -ForegroundColor Red
    }
    
    # 3. Verificar Firewall
    Write-Host "3. Verificando regra de firewall..." -ForegroundColor White
    $firewallRule = Get-NetFirewallRule -DisplayName "IdentyFIRE Server" -ErrorAction SilentlyContinue
    
    if ($firewallRule) {
        Write-Host "   ✓ Regra de firewall já existe`n" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ Regra de firewall não encontrada" -ForegroundColor Yellow
        Write-Host "   É necessário executar como Administrador`n" -ForegroundColor Yellow
        
        # Verificar se é admin
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        
        if ($isAdmin) {
            $confirm = Read-Host "   Deseja criar regra de firewall agora? (S/N)"
            if ($confirm -eq "S" -or $confirm -eq "s") {
                try {
                    New-NetFirewallRule -DisplayName "IdentyFIRE Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow | Out-Null
                    Write-Host "   ✓ Regra de firewall criada com sucesso!`n" -ForegroundColor Green
                } catch {
                    Write-Host "   ✗ Erro ao criar regra: $_`n" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "   → Execute este script como Administrador para configurar firewall" -ForegroundColor Yellow
            Write-Host "   Ou execute manualmente:" -ForegroundColor Yellow
            Write-Host "   New-NetFirewallRule -DisplayName 'IdentyFIRE Server' -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow`n" -ForegroundColor Gray
        }
    }
    
    # 4. Testar porta
    Write-Host "4. Verificando se porta 5000 está em uso..." -ForegroundColor White
    $portInUse = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue
    
    if ($portInUse) {
        Write-Host "   ⚠ Porta 5000 já está em uso" -ForegroundColor Yellow
        Write-Host "   Processo: $(Get-Process -Id $portInUse.OwningProcess -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)`n" -ForegroundColor Gray
    } else {
        Write-Host "   ✓ Porta 5000 disponível`n" -ForegroundColor Green
    }
    
    # Resumo
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "RESUMO - Configure o cliente com:" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "URL do Servidor: " -NoNewline -ForegroundColor White
    Write-Host "http://$($ip.IPAddress):5000" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "Pronto para iniciar o servidor!" -ForegroundColor Green
    Write-Host "Execute: " -NoNewline -ForegroundColor White
    Write-Host "python src/server_gui.py`n" -ForegroundColor Cyan
}

# ==================== MODO CLIENTE ====================
elseif ($Client) {
    Write-Host "[CLIENTE] Testando conexão com servidor...`n" -ForegroundColor Yellow
    
    if (-not $ServerIP) {
        $ServerIP = Read-Host "Digite o IP do servidor (ex: 192.168.1.100)"
    }
    
    Write-Host "1. Testando ping..." -ForegroundColor White
    $ping = Test-Connection -ComputerName $ServerIP -Count 2 -Quiet
    
    if ($ping) {
        Write-Host "   ✓ Servidor alcançável via ping`n" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Servidor não responde ao ping" -ForegroundColor Red
        Write-Host "   Verifique se ambos estão na mesma rede`n" -ForegroundColor Yellow
        exit
    }
    
    Write-Host "2. Testando porta 5000..." -ForegroundColor White
    $port = Test-NetConnection -ComputerName $ServerIP -Port 5000 -WarningAction SilentlyContinue
    
    if ($port.TcpTestSucceeded) {
        Write-Host "   ✓ Porta 5000 acessível`n" -ForegroundColor Green
    } else {
        Write-Host "   ✗ Porta 5000 não está acessível" -ForegroundColor Red
        Write-Host "   Possíveis causas:" -ForegroundColor Yellow
        Write-Host "   - Servidor não está rodando" -ForegroundColor Gray
        Write-Host "   - Firewall bloqueando" -ForegroundColor Gray
        Write-Host "   - config.json não tem host: 0.0.0.0`n" -ForegroundColor Gray
        exit
    }
    
    Write-Host "3. Testando endpoint /health..." -ForegroundColor White
    try {
        $response = Invoke-RestMethod -Uri "http://${ServerIP}:5000/health" -Method Get -TimeoutSec 5
        Write-Host "   ✓ Servidor respondendo!" -ForegroundColor Green
        Write-Host "   Status: $($response.status)" -ForegroundColor Gray
        Write-Host "   Modelo carregado: $($response.model_loaded)" -ForegroundColor Gray
        if ($response.model_name) {
            Write-Host "   Modelo: $($response.model_name)`n" -ForegroundColor Gray
        }
    } catch {
        Write-Host "   ✗ Servidor não responde ao endpoint /health" -ForegroundColor Red
        Write-Host "   Erro: $_`n" -ForegroundColor Gray
        exit
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "CONEXÃO OK - Use no cliente:" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "URL: " -NoNewline -ForegroundColor White
    Write-Host "http://${ServerIP}:5000" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "Pronto para usar o cliente!" -ForegroundColor Green
    Write-Host "Execute: " -NoNewline -ForegroundColor White
    Write-Host "python src/client_gui.py`n" -ForegroundColor Cyan
}

# ==================== AJUDA ====================
else {
    Write-Host "Uso:`n" -ForegroundColor White
    Write-Host "  Configurar SERVIDOR:" -ForegroundColor Yellow
    Write-Host "    .\setup_network.ps1 -Server`n" -ForegroundColor Cyan
    
    Write-Host "  Testar conexão no CLIENTE:" -ForegroundColor Yellow
    Write-Host "    .\setup_network.ps1 -Client -ServerIP 192.168.1.100`n" -ForegroundColor Cyan
    
    Write-Host "Exemplos:`n" -ForegroundColor White
    Write-Host "  # No computador do servidor" -ForegroundColor Gray
    Write-Host "  .\setup_network.ps1 -Server`n" -ForegroundColor Cyan
    
    Write-Host "  # No computador do cliente" -ForegroundColor Gray
    Write-Host "  .\setup_network.ps1 -Client -ServerIP 192.168.1.100`n" -ForegroundColor Cyan
}
