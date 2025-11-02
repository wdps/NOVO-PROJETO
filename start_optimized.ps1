#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Inicializador otimizado do ConcursoIA
#>

Write-Host "🚀 INICIANDO CONCURSOIA COM CONFIGURAÇÃO OTIMIZADA" -ForegroundColor Cyan

# Configura variáveis de ambiente
$env:FLASK_ENV = "development"
$env:FLASK_DEBUG = "1"
$env:PYTHONUNBUFFERED = "1"

# Configurações específicas para cookies grandes
$env:FLASK_SESSION_COOKIE_MAX_SIZE = "16384"
$env:FLASK_MAX_COOKIE_SIZE = "16384"

Write-Host "📋 Variáveis de ambiente configuradas" -ForegroundColor Green

# Verifica se o app.py existe
if (-not (Test-Path "app.py")) {
    Write-Host "❌ ERRO: app.py não encontrado!" -ForegroundColor Red
    exit 1
}

Write-Host "🎯 Iniciando servidor Flask..." -ForegroundColor Yellow

# Inicia o Flask com configurações otimizadas
try {
    flask run --host=0.0.0.0 --port=5000 --debug --extra-files "*.py;*.html;*.js;*.css"
    Write-Host "✅ Servidor iniciado com sucesso!" -ForegroundColor Green
}
catch {
    Write-Host "❌ Erro ao iniciar servidor: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Tentando método alternativo..." -ForegroundColor Yellow
    python app.py
}
