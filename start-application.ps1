Write-Host "🚀 CONCURSOIA - INICIANDO APLICAÇÃO" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Yellow

# Verificar arquivos necessários
$requiredFiles = @("app.py", "templates/index.html", "static/css/style.css", "static/js/script.js", ".env")
$missingFiles = @()

foreach ($file in $requiredFiles) {
    if (-not (Test-Path $file)) {
        $missingFiles += $file
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host "❌ Arquivos faltantes:" -ForegroundColor Red
    $missingFiles | ForEach-Object { Write-Host "   - $_" -ForegroundColor Red }
    exit 1
}

# Verificar chave API Gemini
$envContent = Get-Content ".env" -Raw
if ($envContent -notmatch "GEMINI_API_KEY=.+") {
    Write-Host "❌ Chave da API Gemini não configurada!" -ForegroundColor Red
    Write-Host "Edite o arquivo .env e adicione sua chave" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n🌐 Iniciando servidor Flask..." -ForegroundColor Cyan
Write-Host "📧 Acesse: http://localhost:5000" -ForegroundColor White
Write-Host "⏹️  Para parar: Ctrl+C" -ForegroundColor Yellow

try {
    python app.py
} catch {
    Write-Host "❌ Erro: $_" -ForegroundColor Red
}
