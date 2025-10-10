#!/usr/bin/env python3
"""
Script de démarrage pour LangGraph Studio en mode debugging
"""

import os
import sys
import subprocess
from pathlib import Path

def start_langgraph_studio():
    """
    Démarre le serveur LangGraph Studio pour le debugging
    """
    print("🚀 Démarrage de LangGraph Studio en mode debugging...")
    print("📍 Répertoire de travail:", os.getcwd())
    
    # Vérifier que nous sommes dans le bon répertoire
    if not Path("langgraph.json").exists():
        print("❌ Erreur: langgraph.json non trouvé dans le répertoire courant")
        print("💡 Assurez-vous d'être dans le répertoire racine du projet")
        return False
    
    # Vérifier que langgraph-cli est installé
    try:
        result = subprocess.run(["langgraph", "--version"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Erreur: langgraph-cli non installé ou non accessible")
            print("💡 Installez avec: uv add 'langgraph-cli[inmem]'")
            return False
        print(f"✅ LangGraph CLI version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Erreur: langgraph-cli non trouvé")
        print("💡 Installez avec: uv add 'langgraph-cli[inmem]'")
        return False
    
    # Démarrer le serveur de développement
    print("\n🔧 Démarrage du serveur LangGraph...")
    print("🌐 LangGraph Studio sera accessible à: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
    print("🛑 Appuyez sur Ctrl+C pour arrêter le serveur")
    print("\n" + "="*60)
    
    try:
        # Démarrer langgraph dev avec les options de debugging
        cmd = [
            "langgraph", "dev",
            "--port", "2024",
            "--host", "127.0.0.1"
        ]
        
        print(f"📝 Commande exécutée: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Serveur arrêté par l'utilisateur")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du démarrage du serveur: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    success = start_langgraph_studio()
    sys.exit(0 if success else 1)
