"""
Script de test pour le workflow d'analyse des besoins
"""

import os
import sys
from dotenv import load_dotenv

# Ajout du chemin du projet
sys.path.append('/home/addeche/aiko/aikoGPT')

# Chargement des variables d'environnement
load_dotenv()

from workflow.need_analysis_workflow import NeedAnalysisWorkflow


def test_workflow():
    """
    Test du workflow d'analyse des besoins
    """
    try:
        # Vérification de la clé API
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ Clé API OpenAI non trouvée. Vérifiez votre fichier .env")
            return False
        
        print("🚀 Démarrage du test du workflow d'analyse des besoins...")
        
        # Initialisation du workflow
        workflow = NeedAnalysisWorkflow(api_key)
        
        # Exécution du workflow avec des fichiers d'exemple
        print("📊 Exécution du workflow...")
        
        # Fichiers d'exemple (à remplacer par de vrais fichiers)
        workshop_files = ["/home/addeche/aiko/aikoGPT/inputs/atelier_exemple.xlsx"]
        transcript_files = ["/home/addeche/aiko/aikoGPT/inputs/-Cousin-Biotech-x-aiko-Echange-Production-b04e9caa-d79c.pdf"]
        company_info = {
            "company_name": "Cousin Biotech",
            "sector": "Médical",
            "description": "Entreprise spécialisée dans les dispositifs médicaux"
        }
        
        results = workflow.run(
            workshop_files=workshop_files,
            transcript_files=transcript_files,
            company_info=company_info
        )
        
        # Affichage des résultats
        print("\n📋 Résultats du workflow:")
        print(f"✅ Succès: {results.get('success', False)}")
        print(f"🔄 Nombre d'itérations: {results.get('iteration_count', 0)}")
        print(f"📝 Nombre de besoins finaux: {len(results.get('final_needs', []))}")
        
        if results.get('messages'):
            print("\n💬 Messages du workflow:")
            for msg in results['messages']:
                print(f"  - {msg}")
        
        if results.get('final_needs'):
            print("\n🎯 Besoins identifiés:")
            for i, need in enumerate(results['final_needs'], 1):
                print(f"  {i}. {need.get('title', 'N/A')} - {need.get('theme', 'N/A')}")
        
        # Vérification de la génération du graph
        graph_path = "/home/addeche/aiko/aikoGPT/outputs/workflow_graph.png"
        if os.path.exists(graph_path):
            print(f"\n📊 Graph généré: {graph_path}")
        else:
            print("\n⚠️ Graph non généré")
        
        # Vérification de la sauvegarde des résultats
        results_path = "/home/addeche/aiko/aikoGPT/outputs/need_analysis_results.json"
        if os.path.exists(results_path):
            print(f"💾 Résultats sauvegardés: {results_path}")
        else:
            print("⚠️ Résultats non sauvegardés")
        
        return results.get('success', False)
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        return False


if __name__ == "__main__":
    print("🧪 Test du Workflow d'Analyse des Besoins")
    print("=" * 50)
    
    success = test_workflow()
    
    if success:
        print("\n✅ Test réussi!")
    else:
        print("\n❌ Test échoué!")
