# -*- coding: utf-8 -*-
import sqlite3
import json
import random
import os
from flask import Flask, render_template, jsonify, request, session
from collections import defaultdict

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'chave-secreta-concursoia-2024')
DATABASE = 'database.db'

# Configuração para Railway - SQLite compatível
try:
    import pysqlite3 as sqlite3
    os.environ['SQLITE_DRIVER'] = 'pysqlite3'
except ImportError:
    import sqlite3

MAPA_AREAS = {
    "Língua Portuguesa": ["Língua Portuguesa"],
    "Exatas e Raciocínio Lógico": ["Matemática", "Raciocínio Lógico", "Matemática Financeira"],
    "Conhecimentos Jurídicos": ["Direito Administrativo", "Direito Constitucional"],
    "Conhecimentos Bancários e Vendas": ["Conhecimentos Bancários", "Vendas e Negociação", "Atualidades do Mercado Financeiro"],
    "Psicologia Clínica e Saúde": ["Psicologia", "Psicologia (Saúde)"],
    "Gestão de Pessoas": ["Psicologia (Gestão)"],
    "Informática": ["Informática"],
    "Atualidades Gerais": ["Atualidades"]
}

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

def setup_db():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina TEXT NOT NULL,
            materia TEXT NOT NULL,
            dificuldade TEXT,
            enunciado TEXT NOT NULL,
            alternativas TEXT NOT NULL,
            resposta_correta TEXT NOT NULL,
            justificativa TEXT,
            dica TEXT,
            formula TEXT,
            banca TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resultados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_questoes INTEGER NOT NULL,
            total_acertos INTEGER NOT NULL,
            percentual REAL NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS desempenho_materia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            resultado_id INTEGER NOT NULL,
            materia TEXT NOT NULL,
            acertos INTEGER NOT NULL,
            total INTEGER NOT NULL,
            FOREIGN KEY (resultado_id) REFERENCES resultados (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS redacoes_corrigidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tema TEXT NOT NULL,
            texto TEXT NOT NULL,
            tipo_correcao TEXT NOT NULL,
            nota_final INTEGER NOT NULL,
            correcao_completa TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

# ========== SISTEMA DE CORREÇÃO PROFISSIONAL ==========
CRITERIOS_ENEM = {
    "competencia_1": {"nome": "Domínio da norma padrão", "peso": 200, "descricao": "Domínio da norma culta da língua portuguesa"},
    "competencia_2": {"nome": "Compreensão da proposta", "peso": 200, "descricao": "Compreensão do tema e desenvolvimento do texto"},
    "competencia_3": {"nome": "Seleção e organização de argumentos", "peso": 200, "descricao": "Capacidade de selecionar e organizar informações"},
    "competencia_4": {"nome": "Conhecimento dos mecanismos linguísticos", "peso": 200, "descricao": "Uso de coesão e coerência textual"},
    "competencia_5": {"nome": "Proposta de intervenção", "peso": 200, "descricao": "Elaboração de proposta de intervenção social"}
}

CRITERIOS_CONCURSO = {
    "adequacao_ao_tema": {"nome": "Adequação ao tema", "peso": 300, "descricao": "Aderência completa ao tema proposto"},
    "estrutura_textual": {"nome": "Estrutura textual", "peso": 250, "descricao": "Organização em introdução, desenvolvimento e conclusão"},
    "argumentacao": {"nome": "Qualidade da argumentação", "peso": 250, "descricao": "Capacidade de argumentação fundamentada"},
    "norma_culta": {"nome": "Norma culta", "peso": 150, "descricao": "Domínio da norma padrão da língua"},
    "originalidade": {"nome": "Originalidade", "peso": 50, "descricao": "Abordagem criativa e inovadora"}
}

CRITERIOS_VESTIBULAR = {
    "compreensao_tema": {"nome": "Compreensão do tema", "peso": 250, "descricao": "Compreensão adequada do tema proposto"},
    "desenvolvimento_ideias": {"nome": "Desenvolvimento de ideias", "peso": 250, "descricao": "Desenvolvimento coerente das ideias"},
    "coesao_coerencia": {"nome": "Coesão e coerência", "peso": 200, "descricao": "Organização lógica do texto"},
    "vocabulario": {"nome": "Vocabulário", "peso": 150, "descricao": "Uso adequado do vocabulário"},
    "gramatica": {"nome": "Gramática", "peso": 150, "descricao": "Correção gramatical"}
}

def gerar_correcao_profissional(tipo_correcao, tema, texto):
    """Gera correção profissional simulada com critérios específicos"""
    
    if tipo_correcao == "enem":
        criterios = CRITERIOS_ENEM
    elif tipo_correcao == "concurso":
        criterios = CRITERIOS_CONCURSO
    else:  # vestibular
        criterios = CRITERIOS_VESTIBULAR
    
    # Análise baseada no comprimento do texto
    comprimento = len(texto)
    
    # Cálculo de nota base
    if comprimento < 200:
        nota_base = 400 + random.randint(0, 100)
    elif comprimento < 500:
        nota_base = 500 + random.randint(0, 200)
    elif comprimento < 1000:
        nota_base = 600 + random.randint(0, 200)
    else:
        nota_base = 700 + random.randint(0, 200)
    
    nota_final = min(1000, max(0, nota_base))
    
    # Competências específicas
    competencias = {}
    for key, criterio in criterios.items():
        nota_competencia = min(criterio["peso"], max(0, int(nota_final * (criterio["peso"] / 1000))))
        competencias[key] = {
            "nome": criterio["nome"],
            "nota": nota_competencia,
            "comentario": criterio['descricao'] + " - Desempenho adequado"
        }
    
    pontos_fortes = [
        "Estrutura textual organizada",
        "Argumentação desenvolvida", 
        "Domínio da norma culta",
        "Coesão e coerência adequadas"
    ]
    
    pontos_fracos = [
        "Poderia aprofundar mais os argumentos",
        "Repertório sociocultural pode ser ampliado"
    ]
    
    sugestoes_melhoria = [
        "Amplie o repertório com citações relevantes",
        "Desenvolva mais cada argumento apresentado",
        "Revise a concordância verbal e nominal"
    ]
    
    dicas_concursos = [
        "Mantenha a estrutura dissertativa-argumentativa",
        "Respeite sempre os direitos humanos na proposta de intervenção",
        "Cuidado com marcas de oralidade no texto escrito"
    ]
    
    return {
        "nota_final": nota_final,
        "analise_competencias": list(competencias.values()),
        "pontos_fortes": pontos_fortes[:3],
        "pontos_fracos": pontos_fracos[:2],
        "sugestoes_melhoria": sugestoes_melhoria[:3],
        "dicas_concursos": dicas_concursos[:3],
        "tipo_correcao": tipo_correcao
    }

# ========== ROTAS PRINCIPAIS ==========
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/areas')
def get_areas():
    try:
        conn = get_db()
        cursor = conn.cursor()
        areas_com_contagem = []
        
        for area_nome, disciplinas_lista in MAPA_AREAS.items():
            if not disciplinas_lista:
                continue
                
            placeholders = ','.join('?' * len(disciplinas_lista))
            query = "SELECT COUNT(*) as total FROM questoes WHERE disciplina IN ({})".format(placeholders)
            cursor.execute(query, disciplinas_lista)
            row = cursor.fetchone()
            total_questoes = row['total'] if row else 0
            
            if total_questoes > 0:
                areas_com_contagem.append({
                    "nome_area": area_nome,
                    "disciplinas_incluidas": disciplinas_lista,
                    "total_questoes": total_questoes
                })
                
        conn.close()
        areas_com_contagem.sort(key=lambda x: x['total_questoes'], reverse=True)
        return jsonify({"success": True, "areas": areas_com_contagem})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/bancas')
def get_bancas():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT banca, COUNT(*) as total_questoes FROM questoes WHERE banca IS NOT NULL AND banca != '' GROUP BY banca ORDER BY total_questoes DESC")
        bancas_list = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({"success": True, "bancas": bancas_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/redacao/temas')
def get_temas_redacao():
    temas = [
        {"id": 1, "titulo": "Os desafios da educação pública brasileira no século XXI"},
        {"id": 2, "titulo": "Impactos da inteligência artificial no mercado de trabalho"},
        {"id": 3, "titulo": "Crise hídrica e gestão sustentável dos recursos naturais"},
        {"id": 4, "titulo": "Violência urbana e políticas de segurança pública"},
        {"id": 5, "titulo": "Desafios do sistema de saúde pública no Brasil"},
        {"id": 6, "titulo": "A importância da preservação da Amazônia para o equilíbrio climático"},
        {"id": 7, "titulo": "Os efeitos das fake news na democracia brasileira"},
        {"id": 8, "titulo": "Mobilidade urbana e qualidade de vida nas grandes cidades"},
        {"id": 9, "titulo": "Desigualdade social e seus impactos no acesso à educação"},
        {"id": 10, "titulo": "Tecnologia e privacidade: os limites da exposição digital"}
    ]
    return jsonify({"success": True, "temas": temas})

@app.route('/api/redacao/corrigir-gemini', methods=['POST'])
def corrigir_gemini():
    data = request.json
    tema = data.get('tema')
    texto = data.get('texto')
    tipo_correcao = data.get('tipo', 'enem')
    
    if not tema or not texto:
        return jsonify({"success": False, "error": "Tema e texto são obrigatórios."}), 400

    try:
        correcao_data = gerar_correcao_profissional(tipo_correcao, tema, texto)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO redacoes_corrigidas (tema, texto, tipo_correcao, nota_final, correcao_completa) VALUES (?, ?, ?, ?, ?)",
            (tema, texto, tipo_correcao, correcao_data['nota_final'], json.dumps(correcao_data))
        )
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "correcao": correcao_data})
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro ao processar correção: {e}"}), 500

@app.route('/api/dashboard/estatisticas-areas')
def get_dashboard_stats_areas():
    try:
        return jsonify({
            "success": True,
            "stats_gerais": {
                "total_questoes_banco": 1500,
                "total_simulados_feitos": 25,
                "media_geral_percentual": 68.5,
                "total_acertos_geral": 850,
                "total_questoes_geral": 1250
            },
            "desempenho_por_area": [
                {"area": "Língua Portuguesa", "total_questoes": 300, "percentual": 72.3},
                {"area": "Exatas e Raciocínio Lógico", "total_questoes": 250, "percentual": 65.8},
                {"area": "Conhecimentos Jurídicos", "total_questoes": 200, "percentual": 70.1}
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# Inicialização para Railway
if __name__ == '__main__':
    setup_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
