import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def test_gemini_connection():
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == 'sua_chave_gemini_aqui_cole_sua_chave_real':
        print("❌ CHAVE NÃO CONFIGURADA")
        print("Edite o arquivo .env com sua chave real da API Gemini")
        return False
    
    try:
        print("🔗 Conectando com Google Gemini API...")
        genai.configure(api_key=api_key)
        
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Escreva 'Conexão bem-sucedida' em português.")
        
        print("✅ CONEXÃO BEM-SUCEDIDA!")
        print(f"Resposta: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ ERRO NA CONEXÃO: {e}")
        return False

if __name__ == '__main__':
    test_gemini_connection()
