import sqlite3
import pandas as pd
import json
import os

DB_NAME = 'database.db'
CSV_NAME = 'questoes.csv'

def criar_tabelas(conn):
    cursor = conn.cursor()
    # Tabela de Questões
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disciplina TEXT NOT NULL,
        materia TEXT NOT NULL,
        dificuldade TEXT,
        enunciado TEXT NOT NULL,
        alternativas TEXT NOT NULL, -- Armazenado como JSON
        resposta_correta TEXT NOT NULL,
        justificativa TEXT,
        dica TEXT,
        formula TEXT
    );
    """)
    
    # Tabela de Resultados (para o Dashboard)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resultados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_questoes INTEGER NOT NULL,
        total_acertos INTEGER NOT NULL,
        percentual REAL NOT NULL
    );
    """)
    
    # Tabela de Desempenho por Matéria (para o Dashboard)
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
    print("Tabelas 'questoes', 'resultados' e 'desempenho_materia' verificadas/criadas.")

def importar_dados():
    if not os.path.exists(CSV_NAME):
        print(f"Erro: Arquivo '{CSV_NAME}' não encontrado no diretório.")
        print("Por favor, crie o arquivo e adicione os dados antes de executar este script.")
        return

    conn = sqlite3.connect(DB_NAME)
    criar_tabelas(conn)
    cursor = conn.cursor()

    # Limpa dados antigos para evitar duplicatas na re-importação
    cursor.execute("DELETE FROM questoes")
    conn.commit()
    print("Tabela 'questoes' limpa (dados antigos removidos).")

    try:
        # Usando pandas para facilitar a leitura do CSV
        df = pd.read_csv(CSV_NAME, encoding='utf-8', sep=';')
        
        # Renomeia colunas se necessário (ajuste conforme seu CSV)
        # Ex: df = df.rename(columns={'Enunciado da Questão': 'enunciado'})

        # Verifica colunas essenciais
        colunas_essenciais = ['disciplina', 'materia', 'enunciado', 'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'resposta_correta']
        for col in colunas_essenciais:
            if col not in df.columns:
                print(f"Erro: Coluna essencial '{col}' não encontrada no CSV.")
                return

        total_importadas = 0
        for _, row in df.iterrows():
            alternativas = {
                'a': row['alternativa_a'],
                'b': row['alternativa_b'],
                'c': row['alternativa_c'],
                'd': row['alternativa_d'],
            }
            # Adiciona alternativa 'e' se ela existir no CSV
            if 'alternativa_e' in df.columns and pd.notna(row['alternativa_e']):
                alternativas['e'] = row['alternativa_e']
            
            alternativas_json = json.dumps(alternativas)

            cursor.execute("""
            INSERT INTO questoes (disciplina, materia, dificuldade, enunciado, alternativas, resposta_correta, justificativa, dica, formula)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get('disciplina'),
                row.get('materia'),
                row.get('dificuldade', 'Média'), # Valor padrão
                row.get('enunciado'),
                alternativas_json,
                str(row.get('resposta_correta')).lower(), # Garante minúscula
                row.get('justificativa'),
                row.get('dica'),
                row.get('formula')
            ))
            total_importadas += 1

        conn.commit()
        print(f"Sucesso! {total_importadas} questões importadas do '{CSV_NAME}' para '{DB_NAME}'.")

    except Exception as e:
        print(f"Ocorreu um erro durante a importação: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    importar_dados()




