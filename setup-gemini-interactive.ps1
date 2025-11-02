Write-Host "🔑 CONCURSOIA - CONFIGURADOR DA API GEMINI" -ForegroundColor Magenta
Write-Host "===========================================" -ForegroundColor Yellow

Write-Host "`n🎯 CONFIGURAÇÃO DA API GOOGLE GEMINI" -ForegroundColor Cyan
Write-Host "1. Acesse: https://aistudio.google.com/app/apikey" -ForegroundColor White
Write-Host "2. Crie uma chave e cole abaixo:" -ForegroundColor White

$userApiKey = Read-Host "`nDigite sua API Key do Gemini"

if ($userApiKey) {
    $envContent = @"
FLASK_SECRET_KEY=concursoia_super_secret_key_2024
GEMINI_API_KEY=$userApiKey
DATABASE_URL=sqlite:///database.db
DEBUG=True
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8 -Force
    Write-Host "`n✅ CHAVE SALVA COM SUCESSO!" -ForegroundColor Green
    
    # Testar a chave
    Write-Host "`n🧪 TESTANDO CONEXÃO..." -ForegroundColor Yellow
    python test_gemini.py
} else {
    Write-Host "`n❌ Nenhuma chave fornecida." -ForegroundColor Red
}

Write-Host "`n🎯 PRÓXIMOS PASSOS: .\start-application.ps1" -ForegroundColor Cyan
