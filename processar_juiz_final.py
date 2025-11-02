import csv
import json
import os
import sqlite3

INPUT_FILE = 'JUIZ.CSV'
DB_NAME = 'database.db'

# Cabeçalhos do seu JUIZ.CSV (13 colunas)
INPUT_HEADERS = [
    'disciplina', 'materia', 'dificuldade', 'enunciado',
    'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_e',
    'resposta_correta', 'justificativa', 'dica', 'formula'
]

# Nova lista de questões para a importação final
questoes_para_db = []
erros = 0

try:
    # 1. Abre a Conexão com o DB e garante que a tabela questões exista
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
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

    # 2. Lê o arquivo JUIZ.CSV para extrair e formatar
    with open(INPUT_FILE, mode='r', encoding='utf-8') as f:
        # Pula a linha do cabeçalho original e usa os nomes corretos para o DictReader
        next(f)
        reader = csv.DictReader(f, fieldnames=INPUT_HEADERS, delimiter=';')
        
        for i, row in enumerate(reader):
            # Ignora linhas vazias ou incompletas
            if not row.get('enunciado') or not row.get('disciplina'):
                erros += 1
                continue

            try:
                # 3. Formata alternativas para JSON (como o app.py espera)
                alternativas = {
                    'a': row.get('alternativa_a', ''),
                    'b': row.get('alternativa_b', ''),
                    'c': row.get('alternativa_c', ''),
                    'd': row.get('alternativa_d', ''),
                    'e': row.get('alternativa_e', ''),
                }

                # 4. Adiciona a Banca e formata para o DB
                questoes_para_db.append({
                    'disciplina': row['disciplina'].strip(),
                    'materia': row['materia'].strip(),
                    'dificuldade': row.get('dificuldade', 'Média').strip(),
                    'enunciado': row['enunciado'].strip(),
                    'alternativas': json.dumps(alternativas),
                    'resposta_correta': row['resposta_correta'].strip().lower(),
                    'justificativa': row.get('justificativa', '').strip(),
                    'dica': row.get('dica', '').strip(),
                    'formula': row.get('formula', '').strip(),
                    'banca': 'FGV - JUIZ DO TRABALHO' # BANCA PADRÃO INSERIDA
                })
            except Exception as e:
                print(f"Erro ao processar a questão {i+1} do JUIZ.CSV: {e}")
                erros += 1

    # 5. Remove todas as questões antigas (Para evitar duplicatas)
    cursor.execute("DELETE FROM questoes WHERE banca = ?", ('FGV - JUIZ DO TRABALHO',))
    conn.commit()

    # 6. Insere as novas questões
    sql_insert = """
    INSERT INTO questoes (disciplina, materia, dificuldade, enunciado, alternativas, 
                          resposta_correta, justificativa, dica, formula, banca)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for q in questoes_para_db:
        cursor.execute(sql_insert, (
            q['disciplina'], q['materia'], q['dificuldade'], q['enunciado'], q['alternativas'],
            q['resposta_correta'], q['justificativa'], q['dica'], q['formula'], q['banca']
        ))

    conn.commit()
    conn.close()

    print(f"\n--- ATUALIZAÇÃO COMPLETA ---")
    print(f"✅ SUCESSO! {len(questoes_para_db)} questões de Juiz (FGV) importadas.")
    print(f"Total de questões no DB: {len(questoes_para_db)}")

except Exception as e:
    print(f"\n❌ ERRO FATAL NA IMPORTAÇÃO: {e}")

