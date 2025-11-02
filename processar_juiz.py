import csv
import re
import os

INPUT_FILE = 'JUIZ.CSV'
OUTPUT_FILE = 'questoes_processadas.csv' # Nome do novo arquivo de saída

# O cabeçalho de 13 colunas que nosso projeto espera
HEADERS = [
    'disciplina', 'materia', 'dificuldade', 'enunciado',
    'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_e',
    'resposta_correta', 'justificativa', 'dica', 'formula'
]

questoes = []
current_question = {}
capturing_alternativas = False
current_field = None # Para lidar com enunciados ou justificativas de múltiplas linhas

# Regex para capturar alternativas (ex: "(A) Texto...")
alt_regex = re.compile(r'\(([A-E])\)\s*(.*)')

print(f"Iniciando processamento do arquivo '{INPUT_FILE}'...")

try:
    if not os.path.exists(INPUT_FILE):
        print(f"Erro: Arquivo '{INPUT_FILE}' não encontrado no diretório atual.")
        print("Por favor, verifique se o nome do arquivo está correto.")
        exit()

    with open(INPUT_FILE, mode='r', encoding='utf-8') as f_in:
        # Lê o arquivo inteiro para facilitar o processamento multi-linha
        lines = f_in.readlines()

    # Itera pelas linhas, pulando o cabeçalho original
    for line in lines[1:]: 
        line = line.strip()
        
        if not line: # Ignora linhas em branco
            continue

        if line.startswith('Questão '):
            # Se uma nova questão começa, salva a anterior (se existir e não estiver vazia)
            if current_question:
                questoes.append(current_question)
            current_question = {}
            capturing_alternativas = False
            current_field = None
            continue
        
        # Identifica os rótulos
        if line.startswith('Disciplina:'):
            current_question['disciplina'] = line.replace('Disciplina:', '').strip()
            current_field = 'disciplina'
        elif line.startswith('Matéria:'):
            current_question['materia'] = line.replace('Matéria:', '').strip()
            current_field = 'materia'
        elif line.startswith('Dificuldade:'):
            current_question['dificuldade'] = line.replace('Dificuldade:', '').strip()
            current_field = 'dificuldade'
        elif line.startswith('Enunciado:'):
            current_question['enunciado'] = line.replace('Enunciado:', '').strip()
            current_field = 'enunciado'
        elif line.startswith('Alternativas:'):
            capturing_alternativas = True
            current_field = None
        elif line.startswith('Resposta Correta:'):
            current_question['resposta_correta'] = line.replace('Resposta Correta:', '').strip().lower()
            capturing_alternativas = False
            current_field = 'resposta_correta'
        elif line.startswith('Justificativa:'):
            current_question['justificativa'] = line.replace('Justificativa:', '').strip()
            capturing_alternativas = False
            current_field = 'justificativa'
        elif line.startswith('Dica:'):
            current_question['dica'] = line.replace('Dica:', '').strip()
            capturing_alternativas = False
            current_field = 'dica'
        elif line.startswith('Fórmula:'):
            current_question['formula'] = line.replace('Fórmula:', '').strip()
            capturing_alternativas = False
            current_field = 'formula'
        
        # Lógica de captura
        elif capturing_alternativas:
            match = alt_regex.match(line)
            if match:
                letra = match.group(1).lower()
                texto = match.group(2).strip()
                current_question[f'alternativa_{letra}'] = texto
            else:
                # Se não for uma alternativa, pode ser a continuação de uma alternativa anterior
                # (Lógica simplificada: assume que alternativas são uma linha só)
                pass 
        
        elif current_field and current_field in ['enunciado', 'justificativa', 'dica']:
            # Se não for um novo rótulo, é continuação do campo anterior (multi-linha)
            current_question[current_field] += " " + line


    # Adiciona a última questão processada
    if current_question:
        questoes.append(current_question)

    # Agora, escreve o arquivo CSV de saída
    with open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as f_out:
        writer = csv.writer(f_out, delimiter=';')
        writer.writerow(HEADERS)
        
        linhas_escritas = 0
        for q in questoes:
            # Garante que a questão tenha pelo menos um enunciado antes de salvar
            if q.get('enunciado'):
                writer.writerow([
                    q.get('disciplina', ''),
                    q.get('materia', ''),
                    q.get('dificuldade', ''),
                    q.get('enunciado', ''),
                    q.get('alternativa_a', ''),
                    q.get('alternativa_b', ''),
                    q.get('alternativa_c', ''),
                    q.get('alternativa_d', ''),
                    q.get('alternativa_e', ''),
                    q.get('resposta_correta', ''),
                    q.get('justificativa', ''),
                    q.get('dica', ''),
                    q.get('formula', '')
                ])
                linhas_escritas += 1
    
    print(f"\n--- Processamento Concluído ---")
    print(f"Sucesso! {linhas_escritas} questões foram processadas do '{INPUT_FILE}'.")
    print(f"O novo arquivo foi salvo como: '{OUTPUT_FILE}'.")
    print("\nPróximo passo: Junte este novo arquivo ao seu 'questoes.csv' principal e depois rode 'importar_questoes.py'.")

except FileNotFoundError:
    print(f"Erro: O arquivo '{INPUT_FILE}' não foi encontrado.")
except Exception as e:
    print(f"Ocorreu um erro inesperado: {e}")
