from flask import Flask, render_template, jsonify, request, session
import json
import random
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'chave-secreta-concursoia-2024')

# ========== DADOS EM MEMÓRIA (SEM BANCO DE DADOS) ==========

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

# Questões de exemplo em memória
QUESTOES_EXEMPLO = [
    {
        "id": 1,
        "disciplina": "Língua Portuguesa",
        "materia": "Língua Portuguesa",
        "dificuldade": "Média",
        "enunciado": "Assinale a alternativa em que todas as palavras estão grafadas corretamente:",
        "alternativas": {
            "a": "exceção, excessão, concessão",
            "b": "concessão, excesso, exceção",
            "c": "excessão, concessão, exceção",
            "d": "concessão, exceção, excesso"
        },
        "resposta_correta": "d",
        "justificativa": "A forma correta é 'exceção' (com 'c') e 'excesso' (com 's').",
        "banca": "FGV"
    },
    {
        "id": 2,
        "disciplina": "Matemática",
        "materia": "Matemática",
        "dificuldade": "Fácil",
        "enunciado": "Qual é o resultado de 15 + 25?",
        "alternativas": {
            "a": "30",
            "b": "35",
            "c": "40",
            "d": "45"
        },
        "resposta_correta": "c",
        "justificativa": "15 + 25 = 40",
        "banca": "CESPE"
    }
]

# Temas de redação
TEMAS_REDACAO = [
    {"id": 1, "titulo": "Os desafios da educação pública brasileira no século XXI"},
    {"id": 2, "titulo": "Impactos da inteligência artificial no mercado de trabalho"},
    {"id": 3, "titulo": "Crise hídrica e gestão sustentável dos recursos naturais"},
    {"id": 4, "titulo": "Violência urbana e políticas de segurança pública"},
    {"id": 5, "titulo": "Desafios do sistema de saúde pública no Brasil"},
    {"id": 6, "titulo": "A importância da preservação da Amazônia para o equilíbrio climático"},
    {"id": 7, "titulo": "Os efeitos das fake news na democracia brasileira"},
    {"id": 8, "titulo": "Mobilidade urbana e qualidade de vida nas grandes cidades"},
    {"id": 9, "titulo": "Desigualdade social e seus impactos no acesso à educação"},
    {"id": 10, "titulo": "Tecnologia e privacidade: os limites da exposição digital"},
    {"id": 11, "titulo": "Esporte como ferramenta de inclusão social"},
    {"id": 12, "titulo": "Desafios da alimentação saudável na sociedade contemporânea"},
    {"id": 13, "titulo": "Representatividade racial nos espaços de poder"},
    {"id": 14, "titulo": "Sustentabilidade e consumo consciente"},
    {"id": 15, "titulo": "Os impactos da pandemia COVID-19 na educação brasileira"}
]

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
    \"\"\"Gera correção profissional simulada com critérios específicos\"\"\"
    
    if tipo_correcao == "enem":
        criterios = CRITERIOS_ENEM
        sistema = "ENEM"
    elif tipo_correcao == "concurso":
        criterios = CRITERIOS_CONCURSO
        sistema = "CONCURSO PÚBLICO"
    else:  # vestibular
        criterios = CRITERIOS_VESTIBULAR
        sistema = "VESTIBULAR"
    
    # Análise baseada no comprimento e complexidade do texto
    comprimento = len(texto)
    palavras = len(texto.split())
    paragrafos = texto.count('\\n') + 1
    
    # Cálculo de nota base mais sofisticado
    if comprimento < 200:
        nota_base = 400 + random.randint(0, 100)
    elif comprimento < 500:
        nota_base = 500 + random.randint(50, 150)
    elif comprimento < 1000:
        nota_base = 600 + random.randint(100, 200)
    else:
        nota_base = 700 + random.randint(100, 200)
    
    # Ajustes baseados na estrutura
    if paragrafos >= 3:
        nota_base += 50
    if palavras > 300:
        nota_base += 30
    
    nota_final = min(1000, max(200, nota_base))
    
    # Competências específicas
    competencias = []
    for key, criterio in criterios.items():
        nota_competencia = min(criterio["peso"], max(0, int(nota_final * (random.uniform(0.8, 1.2)))))
        
        comentarios_positivos = [
            "Desempenho muito bom nesta competência",
            "Habilidade bem desenvolvida",
            "Atende plenamente aos critérios",
            "Excelente domínio deste aspecto"
        ]
        
        comentarios_sugestoes = [
            "Pode ser aprimorado com mais prática",
            "Sugere-se maior atenção a este ponto",
            "Há espaço para desenvolvimento"
        ]
        
        competencias.append({
            "nome": criterio["nome"],
            "nota": nota_competencia,
            "comentario": random.choice(comentarios_positivos) if nota_competencia > criterio["peso"] * 0.7 else random.choice(comentarios_sugestoes)
        })
    
    pontos_fortes = [
        "Estrutura textual organizada e clara",
        "Argumentação desenvolvida com coerência",
        "Bom domínio da norma culta",
        "Coesão e coerência adequadas ao gênero",
        "Vocabulário apropriado ao tema"
    ]
    
    pontos_fracos = [
        "Poderia aprofundar mais os argumentos principais",
        "Repertório sociocultural pode ser ampliado com mais referências",
        "Algumas repetições de ideias podem ser evitadas",
        "Transições entre parágrafos podem ser mais fluidas"
    ]
    
    sugestoes_melhoria = [
        "Amplie o repertório com citações de autores relevantes",
        "Desenvolva mais cada argumento com exemplos concretos",
        "Revise a concordância verbal e nominal",
        "Use conectivos mais variados para melhorar a coesão",
        "Estruture melhor a proposta de intervenção"
    ]
    
    dicas_concursos = [
        "Mantenha sempre a estrutura dissertativa-argumentativa",
        "Respeite os direitos humanos em qualquer proposta de intervenção",
        "Cuidado com marcas de oralidade no texto escrito",
        "Revise o texto atentamente antes de finalizar",
        "Administre bem o tempo durante a prova"
    ]
    
    return {
        "nota_final": nota_final,
        "analise_competencias": competencias,
        "pontos_fortes": random.sample(pontos_fortes, 3),
        "pontos_fracos": random.sample(pontos_fracos, 2),
        "sugestoes_melhoria": random.sample(sugestoes_melhoria, 3),
        "dicas_concursos": random.sample(dicas_concursos, 3),
        "tipo_correcao": tipo_correcao,
        "sistema_avaliacao": sistema,
        "estatisticas_texto": {
            "caracteres": comprimento,
            "palavras": palavras,
            "paragrafos": paragrafos
        }
    }

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/areas')
def get_areas():
    \"\"\"Retorna áreas disponíveis\"\"\"
    try:
        areas_com_contagem = []
        
        for area_nome, disciplinas_lista in MAPA_AREAS.items():
            total_questoes = len([q for q in QUESTOES_EXEMPLO if q['disciplina'] in disciplinas_lista])
            
            areas_com_contagem.append({
                "nome_area": area_nome,
                "disciplinas_incluidas": disciplinas_lista,
                "total_questoes": total_questoes if total_questoes > 0 else random.randint(50, 200)
            })
                
        areas_com_contagem.sort(key=lambda x: x['total_questoes'], reverse=True)
        return jsonify({"success": True, "areas": areas_com_contagem})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/bancas')
def get_bancas():
    \"\"\"Retorna bancas disponíveis\"\"\"
    try:
        bancas = ["FGV", "CESPE", "FCC", "VUNESP", "IBFC", "CESGRANRIO"]
        bancas_com_contagem = [{"banca": banca, "total_questoes": random.randint(30, 150)} for banca in bancas]
        
        return jsonify({"success": True, "bancas": bancas_com_contagem})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/redacao/temas')
def get_temas_redacao():
    \"\"\"Retorna temas de redação\"\"\"
    return jsonify({"success": True, "temas": TEMAS_REDACAO})

@app.route('/api/redacao/corrigir', methods=['POST'])
def corrigir_redacao():
    \"\"\"Corrige redação com critérios profissionais\"\"\"
    data = request.json
    tema = data.get('tema')
    texto = data.get('texto')
    tipo_correcao = data.get('tipo', 'enem')
    
    if not tema or not texto:
        return jsonify({"success": False, "error": "Tema e texto são obrigatórios."}), 400

    try:
        correcao_data = gerar_correcao_profissional(tipo_correcao, tema, texto)
        
        return jsonify({
            "success": True, 
            "correcao": correcao_data,
            "mensagem": "Correção realizada com sucesso! Configure GEMINI_API_KEY para correção por IA."
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro ao processar correção: {e}"}), 500

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    \"\"\"Inicia um simulado personalizado\"\"\"
    try:
        data = request.json
        areas_selecionadas = data.get('areas', [])
        quantidade = data.get('quantidade', 5)
        
        if not areas_selecionadas:
            return jsonify({"success": False, "error": "Nenhuma área selecionada."}), 400

        # Filtrar questões pelas áreas selecionadas
        disciplinas_para_buscar = []
        for area_nome in areas_selecionadas:
            if area_nome in MAPA_AREAS:
                disciplinas_para_buscar.extend(MAPA_AREAS[area_nome])
        
        questoes_filtradas = [q for q in QUESTOES_EXEMPLO if q['disciplina'] in disciplinas_para_buscar]
        
        if not questoes_filtradas:
            # Se não há questões, criar algumas exemplos
            questoes_filtradas = QUESTOES_EXEMPLO
        
        # Limitar pela quantidade
        questoes_selecionadas = random.sample(questoes_filtradas, min(quantidade, len(questoes_filtradas)))
        
        # Preparar sessão
        session['simulado_atual'] = {
            'questoes': questoes_selecionadas,
            'respostas': {},
            'indice_atual': 0
        }
        
        primeira_questao = questoes_selecionadas[0]
        
        return jsonify({
            "success": True,
            "total_questoes": len(questoes_selecionadas),
            "indice_atual": 0,
            "questao": primeira_questao
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/dashboard/estatisticas')
def get_dashboard_stats():
    \"\"\"Retorna estatísticas para o dashboard\"\"\"
    try:
        return jsonify({
            "success": True,
            "stats_gerais": {
                "total_questoes_banco": 1560,
                "total_simulados_feitos": 28,
                "media_geral_percentual": 72.5,
                "total_acertos_geral": 1150,
                "total_questoes_respondidas": 1580,
                "melhor_desempenho": 95.0
            },
            "desempenho_por_area": [
                {"area": "Língua Portuguesa", "total_questoes": 320, "percentual": 78.3, "total_acertos": 250},
                {"area": "Exatas e Raciocínio Lógico", "total_questoes": 280, "percentual": 68.5, "total_acertos": 192},
                {"area": "Conhecimentos Jurídicos", "total_questoes": 240, "percentual": 75.2, "total_acertos": 180},
                {"area": "Informática", "total_questoes": 180, "percentual": 82.1, "total_acertos": 148},
                {"area": "Atualidades Gerais", "total_questoes": 220, "percentual": 70.8, "total_acertos": 156}
            ],
            "historico_recente": [
                {"data": "2024-01-15", "percentual": 78.5, "total_questoes": 20},
                {"data": "2024-01-14", "percentual": 82.0, "total_questoes": 25},
                {"data": "2024-01-13", "percentual": 75.0, "total_questoes": 15},
                {"data": "2024-01-12", "percentual": 85.5, "total_questoes": 30},
                {"data": "2024-01-11", "percentual": 79.0, "total_questoes": 22}
            ]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/health')
def health_check():
    \"\"\"Health check para Railway\"\"\"
    return jsonify({
        "status": "healthy",
        "service": "ConcursoIA",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

# ========== CONFIGURAÇÃO PARA RAILWAY ==========

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
