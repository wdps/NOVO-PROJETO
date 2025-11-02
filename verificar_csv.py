import csv
import os

INPUT_FILE = 'questoes.csv'
EXPECTED_COLUMNS = 13
DELIMITER = ';'

def verificar_csv():
    print(f"--- Iniciando Verificação de '{INPUT_FILE}' ---")
    
    if not os.path.exists(INPUT_FILE):
        print(f"❌ ERRO: Arquivo '{INPUT_FILE}' não encontrado.")
        return

    try:
        with open(INPUT_FILE, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=DELIMITER)
            
            # 1. Verifica o cabeçalho (Linha 1)
            try:
                header = next(reader)
                if len(header) != EXPECTED_COLUMNS:
                    print(f"❌ ERRO no Cabeçalho: Esperava {EXPECTED_COLUMNS} colunas, mas encontrou {len(header)}.")
                    print(f"   Cabeçalho Lido: {header}")
                    print(f"--- Verificação Falhou ---")
                    return
                print(f"✅ Cabeçalho (Linha 1) está correto ({EXPECTED_COLUMNS} colunas).")
            except StopIteration:
                print("❌ ERRO: Arquivo vazio ou corrompido.")
                return

            # 2. Verifica as linhas de dados
            linha_numero = 1
            erros = 0
            for row in reader:
                linha_numero += 1
                
                # Ignora linhas que parecem estar vazias
                if not any(row):
                     continue

                if len(row) != EXPECTED_COLUMNS:
                    print(f"❌ ERRO na Linha {linha_numero}: Esperava {EXPECTED_COLUMNS} colunas, mas encontrou {len(row)}.")
                    print(f"   Conteúdo: {row[:5]}...") # Mostra o início do conteúdo para contexto
                    erros += 1

            if erros == 0:
                print(f"✅ SUCESSO! Todas as {linha_numero - 1} linhas de dados estão corretas.")
                print(f"--- Verificação Concluída ---")
            else:
                print(f"\n--- Verificação Falhou ---")
                print(f"Foram encontrados {erros} erros. Corrija-os no '{INPUT_FILE}'.")
                
    except Exception as e:
        print(f"❌ ERRO CRÍTICO ao ler o arquivo: {e}")
        print(f"Verifique a codificação (deve ser UTF-8) e o delimitador (deve ser '{DELIMITER}').")

if __name__ == "__main__":
    verificar_csv()
