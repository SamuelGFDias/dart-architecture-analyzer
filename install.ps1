# Script de instalação global do Dart Architecture Analyzer
# Uso: .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host "📊 Instalando Dart Architecture Analyzer..." -ForegroundColor Cyan
Write-Host ""

# Verifica se Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python encontrado: $pythonVersion" -ForegroundColor Green
}
catch {
    Write-Host "✗ Python não encontrado. Instale Python 3.7+ primeiro." -ForegroundColor Red
    Write-Host "   Download: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Verifica versão do Python (precisa ser 3.7+)
$pythonVersionNumber = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ([version]$pythonVersionNumber -lt [version]"3.7") {
    Write-Host "✗ Python 3.7+ é necessário. Versão atual: $pythonVersionNumber" -ForegroundColor Red
    exit 1
}

# Obtém o diretório do script
$scriptDir = $PSScriptRoot
$analyseScript = Join-Path $scriptDir "analyse.py"

if (-not (Test-Path $analyseScript)) {
    Write-Host "✗ arquivo analyse.py não encontrado em $scriptDir" -ForegroundColor Red
    exit 1
}

# Diretório de instalação (Scripts do Python)
$pythonScriptsDir = python -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))"

if (-not (Test-Path $pythonScriptsDir)) {
    Write-Host "✗ Diretório Scripts do Python não encontrado: $pythonScriptsDir" -ForegroundColor Red
    exit 1
}

Write-Host "📁 Instalando em: $pythonScriptsDir" -ForegroundColor Yellow
Write-Host ""

# Copia analyse.py
$destScript = Join-Path $pythonScriptsDir "dart-analyse.py"
Copy-Item $analyseScript $destScript -Force
Write-Host "✓ dart-analyse.py copiado" -ForegroundColor Green

# Cria wrapper batch para Windows
$batchContent = @"
@echo off
python "%~dp0dart-analyse.py" %*
"@

$destBatch = Join-Path $pythonScriptsDir "dart-analyse.bat"
Set-Content -Path $destBatch -Value $batchContent -Encoding ASCII
Write-Host "✓ dart-analyse.bat criado" -ForegroundColor Green

# Cria wrapper PowerShell
$ps1Content = @"
#!/usr/bin/env pwsh
python "$pythonScriptsDir\dart-analyse.py" @args
"@

$destPs1 = Join-Path $pythonScriptsDir "dart-analyse.ps1"
Set-Content -Path $destPs1 -Value $ps1Content -Encoding UTF8
Write-Host "✓ dart-analyse.ps1 criado" -ForegroundColor Green

# Verifica se Scripts está no PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathNeedsUpdate = $currentPath -notlike "*$pythonScriptsDir*"

if ($pathNeedsUpdate) {
    Write-Host "" 
    Write-Host "⚠️  O diretório Python Scripts não está no PATH!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Para usar 'dart-analyse' globalmente, adicione ao PATH:" -ForegroundColor Yellow
    Write-Host "   $pythonScriptsDir" -ForegroundColor Cyan
    Write-Host ""
    
    $addToPath = Read-Host "   Adicionar ao PATH automaticamente? (S/N)"
    if ($addToPath -eq "S" -or $addToPath -eq "s" -or $addToPath -eq "Y" -or $addToPath -eq "y") {
        try {
            $newPath = "$currentPath;$pythonScriptsDir"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
            Write-Host ""
            Write-Host "✓ Adicionado ao PATH do usuário" -ForegroundColor Green
            Write-Host "  ⚠️  Reinicie o terminal para aplicar as mudanças" -ForegroundColor Yellow
        }
        catch {
            Write-Host ""
            Write-Host "✗ Erro ao adicionar ao PATH. Adicione manualmente." -ForegroundColor Red
        }
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host "✅ Instalação concluída!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""

# Testa se jq está instalado
$jqInstalled = Get-Command jq -ErrorAction SilentlyContinue
if ($jqInstalled) {
    Write-Host "✓ jq detectado - filtros coloridos habilitados" -ForegroundColor Green
}
else {
    Write-Host "ℹ️  jq não encontrado - instale para habilitar colorização:" -ForegroundColor Yellow
    Write-Host "   choco install jq" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "📖 Uso:" -ForegroundColor Cyan
Write-Host "  dart-analyse --help" -ForegroundColor White
Write-Host "  dart-analyse --output stdout | jq '.summary_kpis'" -ForegroundColor White
Write-Host "  dart-analyse --files lib/main.dart --output stdout" -ForegroundColor White
Write-Host ""

if ($pathNeedsUpdate -and -not ($addToPath -eq "S" -or $addToPath -eq "s")) {
    Write-Host "⚠️  Lembre-se de adicionar ao PATH para usar 'dart-analyse' globalmente" -ForegroundColor Yellow
    Write-Host "   $pythonScriptsDir" -ForegroundColor Cyan
    Write-Host ""
}
