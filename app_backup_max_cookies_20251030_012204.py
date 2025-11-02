import sqlite3
import json
import os
import random
import google.generativeai as genai
from flask import Flask, render_template, jsonify, request, session
from dotenv import load_dotenv

# --- Configuração Inicial ---
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)


# =============================================================================
# 🍪 CONFIGURAÇÕES MÁXIMAS DE COOKIE (SUPORTE 500+ QUESTÕES)
# =============================================================================
app.config.update(
    # 🚀 LIMITES MÁXIMOS DE COOKIE
    SESSION_COOKIE_MAX_SIZE=65536,      # 64KB (MÁXIMO RECOMENDADO)
    MAX_COOKIE_SIZE=65536,              # 64KB
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE='Lax',
    
    # ⚡ OTIMIZAÇÕES DE PERFORMANCE
    PERMANENT_SESSION_LIFETIME=3600,    # 1 hora
    SESSION_REFRESH_EACH_REQUEST=True,
    
    # 📊 LIMITES GERAIS AUMENTADOS
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB para uploads
    JSON_AS_ASCII=False,
    
    # 🔧 CONFIGURAÇÕES AVANÇADAS
    EXPLAIN_TEMPLATE_LOADING=False,
    TEMPLATES_AUTO_RELOAD=True
)

# 🎯 ESTRATÉGIA DE SESSÃO OTIMIZADA PARA MUITAS QUESTÕES
def setup_optimized_session():
    \"\"\"Configura sessão otimizada para grandes volumes de dados\"\"\"
    pass
app.secret_key = os.getenv("FLASK_SECRET_KEY", "uma-chave-secreta-muito-forte")
DATABASE = 'database.db'

# ===================================================================
# 💡 MAPA DAS GRANDES ÁREAS (Seu agrupamento) 💡
# ===================================================================
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
# ===================================================================

# --- Funções de Banco de Dados ---
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row 
    return conn

# --- [MODIFICADO] Adiciona Banca à Tabela Questões (se necessário) ---
def setup_db():
    conn = get_db()
    cursor = conn.cursor()
    # Cria a tabela questoes com a coluna banca
    cursor.execute("""
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
    );
    """)
    # Verifica/Cria a coluna 'banca' se ela não existir
    try:
        cursor.execute("SELECT banca FROM questoes LIMIT 1")
    except sqlite3.OperationalError:
        try:
             cursor.execute("ALTER TABLE questoes ADD COLUMN banca TEXT DEFAULT ''")
        except Exception as e:
            pass # Ignora se a tabela não existe
    
    # Verifica/Cria outras tabelas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_questoes INTEGER NOT NULL,
        total_acertos INTEGER NOT NULL,
        percentual REAL NOT NULL
    );
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS desempenho_materia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        resultado_id INTEGER NOT NULL,
        materia TEXT NOT NULL,
        acertos INTEGER NOT NULL,
        total INTEGER NOT NULL,
        FOREIGN KEY (resultado_id) REFERENCES resultados (id)
    );
    """)
    conn.commit()
    conn.close()

# --- Rota Principal (Frontend) ---
@app.route('/')
def index():
    return render_template('index.html')

# --- API: Carregar ÁREAS ---
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
            query = f"""
            SELECT COUNT(*) as total
            FROM questoes
            WHERE disciplina IN ({placeholders});
            """
            
            cursor.execute(query, disciplinas_lista)
            row = cursor.fetchone()
            total_questoes = row['total'] if row else 0
            
            if total_questoes > 0:
                areas_com_contagem.append({
                    "nome_area": area_nome,
                    "disciplinas_incluidas": disciplinas_lista, # Corrigido: não é 'disciplines_lista'
                    "total_questoes": total_questoes
                })
                
        conn.close()
        
        areas_com_contagem.sort(key=lambda x: x['total_questoes'], reverse=True)
        
        return jsonify({"success": True, "areas": areas_com_contagem})
        
    except Exception as e:
        print(f"Erro em /api/areas: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- [NOVO] API: Carregar Bancas (Para o Filtro) ---
@app.route('/api/bancas')
def get_bancas():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Seleciona todas as bancas únicas que não são vazias e conta quantas questões cada uma tem
        cursor.execute("""
            SELECT banca, COUNT(*) as total_questoes
            FROM questoes
            WHERE banca IS NOT NULL AND banca != ''
            GROUP BY banca
            ORDER BY total_questoes DESC;
        """)
        bancas_list = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({"success": True, "bancas": bancas_list})
        
    except Exception as e:
        print(f"Erro em /api/bancas: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- [MODIFICADO] API: Iniciar Simulado (Filtra por Área E Banca) ---
@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    try:
        data = request.json
        areas_selecionadas = data.get('areas', [])
        banca_selecionada = data.get('banca', '')
        quantidade_str = data.get('quantidade', '10')

        if not areas_selecionadas:
            return jsonify({"success": False, "error": "Nenhuma área selecionada."}), 400

        disciplinas_para_buscar = []
        for area_nome in areas_selecionadas:
            if area_nome in MAPA_AREAS:
                disciplinas_para_buscar.extend(MAPA_AREAS[area_nome])
        
        disciplinas_unicas = list(set(disciplinas_para_buscar))
        
        if not disciplinas_unicas:
            return jsonify({"success": False, "error": "Nenhuma disciplina correspondente às áreas selecionadas."}), 400

        conn = get_db()
        cursor = conn.cursor()
        
        placeholders = ','.join('?' * len(disciplinas_unicas))
        
        # Constrói a query base
        query_parts = [f"SELECT * FROM questoes WHERE disciplina IN ({placeholders})"]
        query_params = disciplinas_unicas
        
        # Adiciona o filtro de BANCA se ele existir
        if banca_selecionada and banca_selecionada != 'todas':
            query_parts.append("AND banca = ?")
            query_params.append(banca_selecionada)
        
        # Aplica a lógica de limite/randomização
        if quantidade_str == "295": # Flag para "Todas as Questões"
            query = " ".join(query_parts)
            cursor.execute(query, query_params)
            questoes_raw = cursor.fetchall()
            random.shuffle(questões_raw)
        else:
            limite = int(quantidade_str)
            query = " ".join(query_parts) + " ORDER BY RANDOM() LIMIT ?"
            query_params.append(limite)
            cursor.execute(query, query_params)
            questões_raw = cursor.fetchall()
        
        conn.close()
        
        if not questões_raw:
             return jsonify({"success": False, "error": "Nenhuma questão encontrada para os filtros selecionados (Área e/ou Banca)."}), 404

        questoes = []
        for q in questões_raw:
            questao_dict = dict(q)
            questao_dict['alternativas'] = json.loads(q['alternativas'])
            questoes.append(questao_dict)

        
        # 🚀 ESTRATÉGIA DE ARMAZENAMENTO OTIMIZADO
        # Armazena apenas IDs na sessão para economizar espaço
        questao_ids = [q['id'] for q in questoes_raw]
        session['simulado_questoes_ids'] = questao_ids
        session['simulado_respostas'] = {}
        session['indice_atual'] = 0
        
        # Limpeza de dados desnecessários da sessão
        session.modified = True
        session['simulado_respostas'] = {} 
        session['indice_atual'] = 0
        
        primeira_questao = questoes[0]
        
        return jsonify({
            "success": True,
            "simulado_id": "simulado_sessao",
            "total_questoes": len(questoes),
            "indice_atual": 0,
            "questao": primeira_questao,
            "resposta_anterior": None
        })

    except Exception as e:
        print(f"Erro em /api/simulado/iniciar: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- API: Mudar de Questão (Próxima/Anterior) ---
@app.route('/api/simulado/questao/<int:indice>')
def get_questao(indice):
    questoes = session.get('simulado_questoes')
    if not questoes:
        return jsonify({"success": False, "error": "Simulado não encontrado na sessão."}), 404
        
    total_questoes = len(questoes)
    
    if 0 <= indice < total_questoes:
        session['indice_atual'] = indice
        questao_atual = questoes[indice]
        resposta_anterior = session.get('simulado_respostas', {}).get(str(questao_atual['id']))
        
        return jsonify({
            "success": True,
            "total_questoes": total_questoes,
            "indice_atual": indice,
            "questao": questao_atual,
            "resposta_anterior": resposta_anterior
        })
    else:
        return jsonify({"success": False, "error": "Índice da questão fora dos limites."}), 404

# --- API: Responder Questão ---
@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    data = request.json
    questao_id = str(data.get('questao_id')) 
    alternativa_escolhida = data.get('alternativa', '').lower()
    
    questoes = session.get('simulado_questoes')
    respostas = session.get('simulado_respostas', {})

    if not questoes:
        return jsonify({"success": False, "error": "Simulado não encontrado."}), 404
        
    if questao_id in respostas:
        return jsonify({"success": False, "error": "Esta questão já foi respondida."}), 400

    questao_correta = None
    for q in questoes:
        if str(q['id']) == questao_id:
            questao_correta = q
            break
            
    if not questao_correta:
         return jsonify({"success": False, "error": "ID da questão não encontrado no simulado atual."}), 404

    resposta_certa = questao_correta['resposta_correta'].lower()
    acertou = (alternativa_escolhida == resposta_certa)

    respostas[questao_id] = {
        "alternativa_escolhida": alternativa_escolhida,
        "acertou": acertou
    }
    session['simulado_respostas'] = respostas
    
    return jsonify({
        "success": True,
        "acertou": acertou,
        "resposta_correta": resposta_certa.upper(),
        "justificativa": questao_correta.get('justificativa', 'Sem justificativa detalhada.')
    })

# --- API: Finalizar Simulado ---
@app.route('/api/simulado/finalizar', methods=['POST'])
def finalizar_simulado():
    questoes = session.get('simulado_questoes')
    respostas = session.get('simulado_respostas', {})
    
    if not questoes:
        return jsonify({"success": False, "error": "Nenhum simulado ativo para finalizar."}), 404

    total_questoes = len(questoes)
    total_acertos = 0
    desempenho_materia = {} 

    for q in questoes:
        materia = q['materia'] 
        if materia not in desempenho_materia:
            desempenho_materia[materia] = {'acertos': 0, 'total': 0}
            
        desempenho_materia[materia]['total'] += 1
        
        resposta = respostas.get(str(q['id']))
        if resposta and resposta['acertou']:
            total_acertos += 1
            desempenho_materia[materia]['acertos'] += 1

    percentual_acerto = round((total_acertos / total_questoes) * 100, 2) if total_questoes > 0 else 0
    nota_final = percentual_acerto 

    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO resultados (total_questoes, total_acertos, percentual) VALUES (?, ?, ?)",
            (total_questoes, total_acertos, percentual_acerto)
        )
        resultado_id = cursor.lastrowid
        
        for materia, dados in desempenho_materia.items():
            cursor.execute(
                "INSERT INTO desempenho_materia (resultado_id, materia, acertos, total) VALUES (?, ?, ?, ?)",
                (resultado_id, materia, dados['acertos'], dados['total'])
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro ao salvar resultado no DB: {e}")

    session.pop('simulado_questões', None)
    session.pop('simulado_respostas', None)
    session.pop('indice_atual', None)

    return jsonify({
        "success": True,
        "relatorio": {
            "total_questoes": total_questoes,
            "total_acertos": total_acertos,
            "percentual_acerto": percentual_acerto,
            "nota_final": nota_final
        }
    })

# --- API: Redação (Temas) ---
@app.route('/api/redacao/temas')
def get_temas_redacao():
    temas = [
        {"id": 1, "titulo": "A crise hídrica e os desafios da gestão de recursos naturais no século XXI"},
        {"id": 2, "titulo": "Os impactos da Inteligência Artificial no mercado de trabalho brasileiro"},
        {"id": 3, "titulo": "Desafios da segurança pública nas grandes metrópoles"},
        {"id": 4, "titulo": "A persistência do analfabetismo funcional como entrave ao desenvolvimento social"}
    ]
    return jsonify({"success": True, "temas": temas})

# --- API: Redação (Correção Gemini) ---
@app.route('/api/redacao/corrigir-gemini', methods=['POST'])
def corrigir_gemini():
    data = request.json
    tema = data.get('tema')
    texto = data.get('texto')
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return jsonify({"success": False, "error": "Chave da API Gemini não configurada no servidor."}), 500
        
    if not tema or not texto:
        return jsonify({"success": False, "error": "Tema e texto são obrigatórios."}), 400

    try:
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""
        Você é um corretor de redações de concursos públicos, focado no modelo ENEM/VUNESP.
        Analise a redação a seguir sobre o tema: "{tema}".
        
        Texto da redação:
        ---
        {texto}
        ---
        
        Sua resposta DEVE ser um objeto JSON válido, sem nenhum texto antes ou depois (sem markdown '```json').
        O JSON deve seguir EXATAMENTE esta estrutura:
        
        {{
            "nota_final": <um número de 0 a 100>,
            "analise_competencias": [
                {{"competencia": "Competência 1: Domínio da norma culta", "nota": <número 0-20>, "comentario": "<comentário detalhado sobre gramática, ortografia, etc>"}},
                {{"competencia": "Competência 2: Compreensão do tema e estrutura", "nota": <número 0-20>, "comentario": "<comentário sobre a abordagem do tema e a estrutura dissertativa>"}},
                {{"competencia": "Competência 3: Argumentação e repertório", "nota": <número 0-20>, "comentario": "<comentário sobre a seleção e uso de argumentos e repertório sociocultural>"}},
                {{"competencia": "Competência 4: Coesão e coerência", "nota": <número 0-20>, "comentario": "<comentário sobre o uso de conectivos e a fluidez do texto>"}},
                {{"competencia": "Competência 5: Proposta de intervenção", "nota": <número 0-20>, "comentario": "<comentário sobre a proposta de intervenção (agente, ação, meio, efeito, detalhamento)>"}}
            ],
            "pontos_fortes": ["<ponto forte 1>", "<ponto forte 2>", "..."],
            "pontos_fracos": ["<ponto fraco 1>", "<ponto fraco 2>", "..."],
            "sugestoes_melhoria": ["<sugestão 1>", "<sugestão 2>", "..."],
            "dicas_concursos": ["<dica específica 1>", "<dica específica 2>", "..."]
        }}
        """
        
        response = model.generate_content(prompt)
        
        json_response = response.text.strip().replace("```json", "").replace("```", "")
        
        correcao_data = json.loads(json_response)
        
        return jsonify({"success": True, "correcao": correcao_data})
        
    except Exception as e:
        print(f"Erro na API Gemini: {e}")
        return jsonify({"success": False, "error": f"Erro ao processar correção com IA: {e}"}), 500

# --- API: Dashboard (Estatísticas) ---
@app.route('/api/dashboard/estatisticas')
def get_dashboard_stats():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM questoes")
        total_questoes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT materia) FROM questoes")
        total_materias = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM resultados")
        total_simulados_feitos = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(percentual) FROM resultados")
        media_geral_percentual = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(total_acertos) FROM resultados")
        total_acertos_geral = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(total_questoes) FROM resultados")
        total_questoes_geral = cursor.fetchone()[0] or 0
        
        cursor.execute("""
        SELECT materia, SUM(acertos) as total_acertos, SUM(total) as total_questoes
        FROM desempenho_materia
        GROUP BY materia
        ORDER BY (SUM(acertos) * 1.0 / SUM(total)) DESC;
        """)
        desempenho_materias = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
        SELECT id, data, total_questoes, total_acertos, percentual
        FROM resultados
        ORDER BY data DESC
        LIMIT 5;
        """)
        historico_recente = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        return jsonify({
            "success": True,
            "stats_gerais": {
                "total_questoes_banco": total_questoes,
                "total_materias_banco": total_materias,
                "total_simulados_feitos": total_simulados_feitos,
                "media_geral_percentual": round(media_geral_percentual, 2),
                "total_acertos_geral": total_acertos_geral,
                "total_questoes_geral": total_questoes_geral
            },
            "desempenho_por_materia": desempenho_materias,
            "historico_recente": historico_recente
        })

    except Exception as e:
        print(f"Erro em /api/dashboard/estatisticas: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- Execução ---
if __name__ == '__main__':
    setup_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
