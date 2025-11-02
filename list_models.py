import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    
    print("🔍 MODELOS DISPONÍVEIS:")
    for model in genai.list_models():
        print(f"📦 {model.name}")
        if 'generateContent' in model.supported_generation_methods:
            print("   ✅ Suporta generateContent")
else:
    print("❌ Chave da API não encontrada")
