import requests
import sys

def testar_apis():
    base_url = "https://concursoia.up.railway.app"
    apis = [
        "/api/areas",
        "/api/bancas", 
        "/api/redacao/temas",
        "/api/dashboard/estatisticas-areas",
        "/health"
    ]
    
    print("🔍 TESTANDO APIs DO CONCURSOIA...")
    for api in apis:
        try:
            response = requests.get(f"{base_url}{api}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    print(f"✅ {api} - OK ({len(data)} itens)")
                else:
                    print(f"✅ {api} - OK")
            else:
                print(f"❌ {api} - ERRO {response.status_code}")
        except Exception as e:
            print(f"❌ {api} - FALHA: {e}")

if __name__ == "__main__":
    testar_apis()
