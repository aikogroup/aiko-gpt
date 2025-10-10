#!/usr/bin/env python3
"""
Script de test final pour LangGraph Studio
"""

import requests
import time
import subprocess
import sys
from pathlib import Path

def test_langgraph_studio():
    """
    Teste que LangGraph Studio fonctionne correctement
    """
    print("🧪 Test final de LangGraph Studio...")
    
    # Vérifier que les fichiers nécessaires existent
    required_files = [
        "langgraph.json",
        "graph_factory.py",
        "workflow/need_analysis_workflow.py"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Fichier manquant: {file_path}")
            return False
        print(f"✅ Fichier trouvé: {file_path}")
    
    # Démarrer le serveur en arrière-plan
    print("\n🚀 Démarrage du serveur LangGraph...")
    try:
        process = subprocess.Popen(
            ["uv", "run", "langgraph", "dev", "--port", "2024", "--host", "127.0.0.1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Attendre que le serveur démarre
        print("⏳ Attente du démarrage du serveur...")
        time.sleep(5)
        
        # Tester l'API
        print("🔍 Test de l'API...")
        try:
            response = requests.get("http://127.0.0.1:2024/docs", timeout=5)
            if response.status_code == 200:
                print("✅ API accessible")
            else:
                print(f"❌ API non accessible: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur API: {e}")
            return False
        
        # Tester l'endpoint des graphs
        print("🔍 Test des graphs...")
        try:
            response = requests.get("http://127.0.0.1:2024/assistants/search", timeout=5)
            if response.status_code == 200:
                print("✅ Graphs accessibles")
            else:
                print(f"❌ Graphs non accessibles: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur graphs: {e}")
            return False
        
        # Arrêter le serveur
        print("🛑 Arrêt du serveur...")
        process.terminate()
        process.wait(timeout=5)
        
        print("\n🎉 Test réussi ! LangGraph Studio est prêt à utiliser")
        print("📝 Pour démarrer:")
        print("   1. python start_debug_server.py")
        print("   2. Ouvrir: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
        print("   3. Sélectionner le graph 'need_analysis'")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    success = test_langgraph_studio()
    sys.exit(0 if success else 1)
