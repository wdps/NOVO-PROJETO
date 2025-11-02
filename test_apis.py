import requests
import json

BASE_URL = "http://localhost:5000"
apis = ["/api/areas", "/api/bancas", "/api/redacao/temas", "/api/dashboard/estatisticas-areas"]

print("🔍 TESTANDO APIs...")
for api in apis:
    try:
        response = requests.get(f"{BASE_URL}{api}", timeout=5)
        if response.status_code == 200:
            print(f"✅ {api} - OK ({len(response.json())} itens)")
        else:
            print(f"❌ {api} - ERRO {response.status_code}")
    except Exception as e:
        print(f"❌ {api} - FALHA: {e}")

# Testar simulado
try:
    response = requests.post(f"{BASE_URL}/api/simulado", 
                           json={"areas": ["Conhecimentos Jurídicos"], "quantidade": 5},
                           timeout=5)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ /api/simulado - OK ({data['total']} questões)")
    else:
        print(f"❌ /api/simulado - ERRO {response.status_code}")
except Exception as e:
    print(f"❌ /api/simulado - FALHA: {e}")
