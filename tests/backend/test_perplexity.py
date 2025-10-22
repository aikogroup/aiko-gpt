"""
Script de test pour l'API Perplexity

FR: Test isolé de l'API Perplexity avec httpx
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import httpx

# FR: Charger les variables d'environnement
load_dotenv()

# FR: Vérifier la clé API
api_key = os.getenv("PERPLEXITY_API_KEY")

if not api_key:
    print("❌ PERPLEXITY_API_KEY non trouvée dans .env")
    print("💡 Ajoutez: PERPLEXITY_API_KEY=pplx-xxxxxxxxx")
    exit(1)

print(f"✅ Clé API trouvée: {api_key[:10]}...{api_key[-4:]}")

# FR: Test 1 - Requête minimale
print("\n" + "="*60)
print("🧪 Test 1 : Requête minimale avec modèle 'sonar'")
print("="*60)

try:
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is the capital of France?"}
        ]
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    start_time = time.time()
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
    
    end_time = time.time()
    result = response.json()
    
    print(f"✅ Succès! (Temps: {end_time - start_time:.2f}s)")
    print(f"📝 Réponse: {result['choices'][0]['message']['content']}\n")
    
except httpx.HTTPStatusError as e:
    print(f"❌ Erreur HTTP: {e.response.status_code}")
    print(f"   Détails: {e.response.text}")
    exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    exit(1)

# FR: Test 2 - Recherche entreprise
print("\n" + "="*60)
print("🧪 Test 2 : Recherche entreprise 'Cousin Biotech'")
print("="*60)

company_name = "Cousin Biotech"
search_query = f"Recherche des informations factuelles sur l'entreprise '{company_name}': secteur d'activité, taille (nombre d'employés), localisation principale, et actualités récentes."

try:
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "Tu es un assistant de recherche web. Fournis des informations factuelles et récentes."
            },
            {
                "role": "user",
                "content": search_query
            }
        ]
    }
    
    start_time = time.time()
    
    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            "https://api.perplexity.ai/chat/completions",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
    
    end_time = time.time()
    result = response.json()
    content = result['choices'][0]['message']['content']
    
    print(f"✅ Succès! (Temps: {end_time - start_time:.2f}s)")
    print(f"📝 Contenu ({len(content)} caractères):\n{content}\n")
    
except httpx.HTTPStatusError as e:
    print(f"❌ Erreur HTTP: {e.response.status_code}")
    print(f"   Détails: {e.response.text}")
    exit(1)
except Exception as e:
    print(f"❌ Erreur: {e}")
    exit(1)

print("\n" + "="*60)
print("📋 Résumé")
print("="*60)
print("✅ Les deux tests ont réussi → Perplexity est correctement configuré")
print("\nDocumentation: https://docs.perplexity.ai/")
