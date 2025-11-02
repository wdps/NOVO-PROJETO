# CONFIGURAÇÃO FLASK OTIMIZADA PARA COOKIES GRANDES
import os

class Config:
    # 🍪 CONFIGURAÇÕES DE SESSÃO OTIMIZADAS
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'chave-super-secreta-aqui')
    
    # Aumenta drasticamente o limite de cookies
    SESSION_COOKIE_MAX_SIZE = 16384  # 16KB (padrão: 4093)
    MAX_COOKIE_SIZE = 16384
    
    # Otimizações de performance
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # True em produção com HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Tempo de vida da sessão
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutos
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Configurações do servidor
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB para uploads
    
    # Otimizações gerais
    JSONIFY_PRETTYPRINT_REGULAR = False
    EXPLAIN_TEMPLATE_LOADING = False

# Configuração para desenvolvimento
class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

# Configuração para produção  
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
