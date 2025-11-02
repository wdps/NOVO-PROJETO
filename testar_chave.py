import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def testar_chave():
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ Chave não encontrada")
        return False
    
    try:
        print("🔗 Conectando com Gemini...")
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content("Diga 'OK' se estiver funcionando")
        
        print("✅ CHAVE VÁLIDA! Conexão bem-sucedida.")
        print(f"🤖 Resposta: {response.text}")
        return True
        
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

testar_chave()
