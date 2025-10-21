"""
Script de test pour l'API Perplexity

FR: Test isolé de l'API Perplexity avec le client officiel
"""

import os
import sys
from pathlib import Path

# FR: Ajouter le backend au path Python
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv

# FR: Charger les variables d'environnement
load_dotenv()

try:
    from perplexity import Perplexity
    print("✅ Client Perplexity installé")
except ImportError:
    print("❌ Client Perplexity non installé")
    print("💡 Installation: uv pip install perplexity-python")
    exit(1)

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
    # FR: Initialiser le client
    client = Perplexity(api_key=api_key)
    
    # FR: Requête simple
    response = client.chat.completions.create(
        model="sonar",
        messages=[
            {
                "role": "system",
                "content": "Tu es un assistant de recherche web."
            },
            {
                "role": "user",
                "content": "What is the capital of France?"
            }
        ]
    )
    
    # FR: Afficher la réponse
    content = response.choices[0].message.content
    print(f"✅ Succès!")
    print(f"📝 Réponse: {content}")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

# FR: Test 2 - Recherche entreprise (comme dans le code)
print("\n" + "="*60)
print("🧪 Test 2 : Recherche entreprise 'Cousin Biotech'")
print("="*60)

try:
    client = Perplexity(api_key=api_key)
    
    response = client.chat.completions.create(
        model="sonar",
        messages=[
            {
                "role": "system",
                "content": "Tu es un assistant de recherche web. Fournis des informations factuelles et récentes."
            },
            {
                "role": "user",
                "content": "Recherche des informations factuelles sur l'entreprise 'Cousin Biotech': secteur d'activité, taille (nombre d'employés), localisation principale, et actualités récentes."
            }
        ]
    )
    
    content = response.choices[0].message.content
    print(f"✅ Succès!")
    print(f"📝 Contenu ({len(content)} caractères):")
    print(content)
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("📋 Résumé")
print("="*60)
print("✅ Si les deux tests ont réussi → Perplexity est correctement configuré")
print("❌ Si les tests échouent → Vérifiez:")
print("   1. La clé API est valide")
print("   2. La facturation est configurée")
print("   3. Le client perplexity-python est installé")
print("\nDocumentation: https://docs.perplexity.ai/")
