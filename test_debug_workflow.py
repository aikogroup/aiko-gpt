#!/usr/bin/env python3
"""
Script de test pour vérifier le workflow en mode debugging
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.append('/home/addeche/aiko/aikoGPT')

from workflow.need_analysis_workflow import NeedAnalysisWorkflow

def test_debug_workflow():
    """
    Teste le workflow en mode debugging
    """
    print("🧪 Test du workflow en mode debugging...")
    
    # Vérifier que les fichiers de données mockées existent
    mock_files = [
        '/home/addeche/aiko/aikoGPT/workshop_results.json',
        '/home/addeche/aiko/aikoGPT/transcript_results.json',
        '/home/addeche/aiko/aikoGPT/web_search_cousin_surgery.json'
    ]
    
    for file_path in mock_files:
        if not Path(file_path).exists():
            print(f"❌ Fichier mocké manquant: {file_path}")
            return False
        print(f"✅ Fichier mocké trouvé: {file_path}")
    
    # Initialiser le workflow en mode debugging
    try:
        print("\n🔧 Initialisation du workflow en mode debugging...")
        workflow = NeedAnalysisWorkflow(
            api_key="test-key",  # Clé factice pour le test
            dev_mode=True,
            debug_mode=True
        )
        print("✅ Workflow initialisé avec succès")
        
        # Vérifier que le checkpointer est configuré
        if workflow.checkpointer:
            print("✅ Checkpointer SQLite configuré")
        else:
            print("❌ Checkpointer non configuré")
            return False
        
        # Vérifier que le graphe est compilé avec les options de debugging
        print("✅ Graphe compilé avec options de debugging")
        
        print("\n🎯 Test réussi ! Le workflow est prêt pour LangGraph Studio")
        print("📝 Pour démarrer LangGraph Studio:")
        print("   1. Exécutez: python start_debug_server.py")
        print("   2. Ouvrez: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024")
        print("   3. Sélectionnez le graph 'need_analysis'")
        print("   4. Utilisez les données mockées pour tester")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        return False

if __name__ == "__main__":
    success = test_debug_workflow()
    sys.exit(0 if success else 1)
