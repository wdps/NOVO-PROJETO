import csv
import os

ARQUIVO_ANTIGO = 'questoes_antigas.csv' # O arquivo com 16 colunas
ARQUIVO_NOVO = 'questoes.csv'           # O arquivo correto de 13 colunas

# O cabeçalho correto que o 'importar_questoes.py' espera
CABECALHO_CORRETO = [
    'disciplina', 'materia', 'dificuldade', 'enunciado',
    'alternativa_a', 'alternativa_b', 'alternativa_c', 'alternativa_d', 'alternativa_e',
    'resposta_correta', 'justificativa', 'dica', 'formula'
]

# Mapeia a letra da resposta (row[8]) para o índice da sua justificativa (row[9] a row[12])
# ATENÇÃO: Isso assume que suas questões têm 4 alternativas (A, B, C, D)
MAPA_JUSTIFICATIVA = {
    'A': 9,  # 'A' (letra) -> índice 9 (justificativa_a)
    'B': 10, # 'B' (letra) -> índice 10 (justificativa_b)
    'C': 11, # 'C' (letra) -> índice 11 (justificativa_c)
    'D': 12  # 'D' (letra) -> índice 12 (justificativa_d)
}

def corrigir_csv():
    # Verifica se o arquivo antigo existe
    if not os.path.exists(ARQUIVO_ANTIGO):
        print(f"Erro: Arquivo '{ARQUIVO_ANTIGO}' não encontrado.")
        print(f"Por favor, renomeie seu arquivo CSV de 295 questões para '{ARQUIVO_ANTIGO}' e tente novamente.")
        return

    total_linhas = 0
    linhas_corrigidas = 0
    linhas_com_erro = 0

    try:
        with open(ARQUIVO_ANTIGO, mode='r', encoding='utf-8', newline='') as f_antigo, \
             open(ARQUIVO_NOVO, mode='w', encoding='utf-8', newline='') as f_novo:
            
            # Leitor para o arquivo antigo (com 16 colunas, separado por ;)
            leitor = csv.reader(f_antigo, delimiter=';')
            
            # Escritor para o novo arquivo (correto, separado por ;)
            escritor = csv.writer(f_novo, delimiter=';')
            
            # 1. Escreve o cabeçalho correto no novo arquivo
            escritor.writerow(CABECALHO_CORRETO)
            
            # 2. Pula o cabeçalho do arquivo antigo (que está errado)
            try:
                next(leitor)
                total_linhas += 1
            except StopIteration:
                print("Erro: Arquivo antigo está vazio.")
                return

            # 3. Processa cada linha de dados
            for row in leitor:
                total_linhas += 1
                try:
                    # Verifica se a linha tem o número esperado de colunas
                    if len(row) < 16:
                        print(f"Erro na linha {total_linhas}: Formato inesperado (menos de 16 colunas). Pulando linha.")
                        linhas_com_erro += 1
                        continue
                        
                    # Pega a letra da resposta correta
                    letra_correta = row[8].strip().upper()
                    
                    # Encontra o índice da justificativa correta
                    indice_justificativa = MAPA_JUSTIFICATIVA.get(letra_correta)
                    
                    if indice_justificativa is None:
                        # Se a letra não for A, B, C, ou D, marca como erro
                        print(f"Erro na linha {total_linhas}: Resposta correta '{letra_correta}' não é A, B, C ou D. Pulando linha.")
                        linhas_com_erro += 1
                        continue

                    # ---- MONTA A NOVA LINHA (13 COLUNAS) ----
                    nova_linha = [
                        row[1].strip(),          # 1. disciplina
                        row[2].strip(),          # 2. materia
                        row[15].strip(),         # 3. dificuldade (do final da linha)
                        row[3].strip(),          # 4. enunciado
                        row[4].strip(),          # 5. alternativa_a
                        row[5].strip(),          # 6. alternativa_b
                        row[6].strip(),          # 7. alternativa_c
                        row[7].strip(),          # 8. alternativa_d
                        "",                      # 9. alternativa_e (vazia)
                        letra_correta.lower(),   # 10. resposta_correta (em minúsculo)
                        row[indice_justificativa].strip(),# 11. justificativa (apenas a correta)
                        row[13].strip(),         # 12. dica
                        row[14].strip()          # 13. formula
                    ]
                    
                    escritor.writerow(nova_linha)
                    linhas_corrigidas += 1
                    
                except IndexError:
                    print(f"Erro na linha {total_linhas}: Formato inesperado. Pulando linha.")
                    linhas_com_erro += 1
                except Exception as e:
                    print(f"Erro inesperado na linha {total_linhas}: {e}. Pulando linha.")
                    linhas_com_erro += 1

    except Exception as e:
        print(f"Erro fatal ao ler/escrever arquivos: {e}")
        return

    print("\n--- Correção Concluída ---")
    print(f"Novo arquivo '{ARQUIVO_NOVO}' foi criado.")
    print(f"Linhas processadas (do arquivo antigo): {total_linhas - 1}") # -1 pelo cabeçalho
    print(f"Linhas corrigidas com sucesso: {linhas_corrigidas}")
    print(f"Linhas puladas por erro: {linhas_com_erro}")
    if linhas_com_erro > 0:
        print("AVISO: Algumas linhas continham erros e não foram migradas. Verifique o log acima.")
    else:
        print("✅ Sucesso total! Todos os dados foram migrados.")

if __name__ == "__main__":
    corrigir_csv()
