Write-Host "🔄 SINCRONIZANDO TUDO COM GITHUB..." -ForegroundColor Cyan

# 1. Verificar status
Write-Host "
1. VERIFICANDO STATUS..." -ForegroundColor Green
git status

# 2. Adicionar TODOS os arquivos
Write-Host "
2. ADICIONANDO ARQUIVOS..." -ForegroundColor Green
git add .

# 3. Fazer commit
Write-Host "
3. FAZENDO COMMIT..." -ForegroundColor Green
git commit -m "Deploy: Sincronização completa - app, templates, static, dados"

# 4. Fazer push
Write-Host "
4. ENVIANDO PARA GITHUB..." -ForegroundColor Green
git push origin main

Write-Host "
✅ SINCRONIZAÇÃO COMPLETA!" -ForegroundColor Green
Write-Host "⏳ Aguarde 2-3 minutos para o Railway fazer deploy..." -ForegroundColor Yellow
Write-Host "🌐 Teste: https://concursoia.up.railway.app" -ForegroundColor White
