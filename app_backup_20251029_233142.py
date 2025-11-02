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
# 🍪 CONFIGURAÇÕES OTIMIZADAS DE COOKIE (Adicionadas pelo script)
# =============================================================================
app.config.update(
    SESSION_COOKIE_MAX_SIZE=16384,  # 16KB
    MAX_COOKIE_SIZE=16384,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=1800,
    SESSION_REFRESH_EACH_REQUEST=True
)
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
                    "disciplinas_incluidas": disciplinas_lista,
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

# --- [CORREÇÃO COMPLETA] API: Iniciar Simulado (OTIMIZADO) ---
@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    try:
        data = request.json
        areas_selecionadas = data.get('areas', [])
        banca_selecionada = data.get('banca', '')
        quantidade_str = data.get('quantidade', '10')

        if not areas_selecionadas:
            return jsonify({"success": False, "error": "Nenhuma área selecionada."}), 400

        # Limpa sessão anterior para evitar cookie grande
        session.clear()

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
        
        # [CORREÇÃO] Limita automaticamente para evitar cookie grande
        limite_maximo = 30  # Máximo de questões por sessão para evitar cookie grande
        
        if quantidade_str == "295": 
            # Para "Todas as Questões", usa limite máximo
            query = " ".join(query_parts) + " ORDER BY RANDOM() LIMIT ?"
            query_params.append(limite_maximo)
            cursor.execute(query, query_params)
            questoes_raw = cursor.fetchall()
            random.shuffle(questoes_raw)
        else:
            limite = min(int(quantidade_str), limite_maximo)  # Não passa do máximo
            query = " ".join(query_parts) + " ORDER BY RANDOM() LIMIT ?"
            query_params.append(limite)
            cursor.execute(query, query_params)
            questoes_raw = cursor.fetchall()
        
        conn.close()
        
        if not questoes_raw:
             return jsonify({"success": False, "error": "Nenhuma questão encontrada para os filtros selecionados (Área e/ou Banca)."}), 404

        # [CORREÇÃO] Armazena apenas IDs na sessão, não questões completas
        questoes_ids = [q['id'] for q in questoes_raw]
        session['simulado_questoes_ids'] = questoes_ids
        session['simulado_respostas'] = {} 
        session['indice_atual'] = 0
        
        # Busca a primeira questão completa
        primeira_questao = get_questao_completa(questoes_ids[0])
        
        return jsonify({
            "success": True,
            "simulado_id": "simulado_sessao",
            "total_questoes": len(questoes_ids),
            "indice_atual": 0,
            "questao": primeira_questao,
            "resposta_anterior": None
        })

    except Exception as e:
        print(f"Erro em /api/simulado/iniciar: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- [NOVA FUNÇÃO] Busca questão completa do banco ---
def get_questao_completa(questao_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questoes WHERE id = ?", (questao_id,))
        questao = cursor.fetchone()
        conn.close()
        
        if questao:
            questao_dict = dict(questao)
            questao_dict['alternativas'] = json.loads(questao['alternativas'])
            return questao_dict
        return None
    except Exception as e:
        print(f"Erro ao buscar questão {questao_id}: {e}")
        return None

# --- [CORREÇÃO] API: Mudar de Questão ---
@app.route('/api/simulado/questao/<int:indice>')
def get_questao(indice):
    # [CORREÇÃO] Busca IDs da sessão
    questoes_ids = session.get('simulado_questoes_ids', [])
    if not questoes_ids:
        return jsonify({"success": False, "error": "Simulado não encontrado na sessão."}), 404
        
    total_questoes = len(questoes_ids)
    
    if 0 <= indice < total_questoes:
        session['indice_atual'] = indice
        # [CORREÇÃO] Busca questão completa do banco
        questao_atual = get_questao_completa(questoes_ids[indice])
        if not questao_atual:
            return jsonify({"success": False, "error": "Questão não encontrada no banco."}), 404
            
        resposta_anterior = session.get('simulado_respostas', {}).get(str(questoes_ids[indice]))
        
        return jsonify({
            "success": True,
            "total_questoes": total_questoes,
            "indice_atual": indice,
            "questao": questao_atual,
            "resposta_anterior": resposta_anterior
        })
    else:
        return jsonify({"success": False, "error": "Índice da questão fora dos limites."}), 404

# --- [CORREÇÃO COMPLETA] API: Responder Questão ---
@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    try:
        data = request.json
        questao_id = str(data.get('questao_id')) 
        alternativa_escolhida = data.get('alternativa', '').lower()
        
        # [CORREÇÃO] Busca IDs da sessão
        questoes_ids = session.get('simulado_questoes_ids', [])
        respostas = session.get('simulado_respostas', {})

        if not questoes_ids:
            return jsonify({"success": False, "error": "Simulado não encontrado."}), 404
            
        if questao_id in respostas:
            return jsonify({"success": False, "error": "Esta questão já foi respondida."}), 400

        # [CORREÇÃO] Busca questão do banco
        questao_correta = get_questao_completa(int(questao_id))
        if not questao_correta:
            return jsonify({"success": False, "error": "ID da questão não encontrado no banco."}), 404

        resposta_certa = questao_correta.get('resposta_correta', '').lower()
        acertou = (alternativa_escolhida == resposta_certa)

        # [CORREÇÃO] Armazena apenas dados essenciais
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
        
    except Exception as e:
        print(f"Erro em /api/simulado/responder: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# --- [CORREÇÃO] API: Finalizar Simulado ---
@app.route('/api/simulado/finalizar', methods=['POST'])
def finalizar_simulado():
    try:
        # [CORREÇÃO] Busca IDs da sessão
        questoes_ids = session.get('simulado_questoes_ids', [])
        respostas = session.get('simulado_respostas', {})
        
        if not questoes_ids:
            return jsonify({"success": False, "error": "Nenhum simulado ativo para finalizar."}), 404

        total_questoes = len(questoes_ids)
        total_acertos = 0
        desempenho_materia = {} 

        for questao_id in questoes_ids:
            # [CORREÇÃO] Busca questão do banco
            questao = get_questao_completa(questao_id)
            if not questao:
                continue
                
            materia = questao['materia'] 
            if materia not in desempenho_materia:
                desempenho_materia[materia] = {'acertos': 0, 'total': 0}
                
            desempenho_materia[materia]['total'] += 1
            
            resposta = respostas.get(str(questao_id))
            if resposta and resposta['acertou']:
                total_acertos += 1
                desempenho_materia[materia]['acertos'] += 1

        percentual_acerto = round((total_acertos / total_questoes) * 100, 2) if total_questoes > 0 else 0
        nota_final = percentual_acerto 

        # Salva no banco
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

        # Limpa sessão
        session.pop('simulado_questoes_ids', None)
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
        
    except Exception as e:
        print(f"Erro em /api/simulado/finalizar: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

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
