# Script de desinstalação do Dart Architecture Analyzer
# Uso: .\uninstall.ps1

$ErrorActionPreference = "Stop"

Write-Host "🗑️  Desinstalando Dart Architecture Analyzer..." -ForegroundColor Cyan
Write-Host ""

try {
    $pythonScriptsDir = python -c "import sys; import os; print(os.path.join(sys.prefix, 'Scripts'))"
} catch {
    Write-Host "✗ Python não encontrado" -ForegroundColor Red
    exit 1
}

$files = @(
    "analyse.py",
    "analyse.bat",
    "analyse.ps1"
)

$removed = 0
foreach ($file in $files) {
    $path = Join-Path $pythonScriptsDir $file
    if (Test-Path $path) {
        try {
            Remove-Item $path -Force
            Write-Host "✓ Removido: $file" -ForegroundColor Green
            $removed++
        } catch {
            Write-Host "✗ Erro ao remover: $file" -ForegroundColor Red
        }
    }
}

Write-Host ""

if ($removed -eq 0) {
    Write-Host "ℹ️  Nenhum arquivo encontrado para remover" -ForegroundColor Yellow
} else {
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "✅ Desinstalação concluída! ($removed arquivo(s) removido(s))" -ForegroundColor Green
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
}

Write-Host ""
