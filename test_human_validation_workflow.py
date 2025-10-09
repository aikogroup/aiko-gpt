"""
Test du workflow avec validation humaine
"""

import os
import sys
from dotenv import load_dotenv

# Ajout du chemin du projet
sys.path.append('/home/addeche/aiko/aikoGPT')

# Chargement des variables d'environnement
load_dotenv()

from workflow.need_analysis_workflow import NeedAnalysisWorkflow


def test_human_validation_workflow():
    """
    Test du workflow avec validation humaine
    """
    print("🚀 Test du Workflow avec Validation Humaine")
    print("=" * 60)
    
    # Vérification de la clé API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Clé API OpenAI non trouvée. Vérifiez votre fichier .env")
        return False
    
    try:
        # Initialisation du workflow
        print("🔧 Initialisation du workflow...")
        workflow = NeedAnalysisWorkflow(api_key)
        
        # Fichiers d'exemple
        workshop_files = ["/home/addeche/aiko/aikoGPT/inputs/atelier_exemple.xlsx"]
        transcript_files = [
            "/home/addeche/aiko/aikoGPT/inputs/-Cousin-Biotech-x-aiko-Echange-Production-b04e9caa-d79c.pdf"
        ]
        company_info = {
            "company_name": "Cousin Biotech",
            "sector": "Médical",
            "description": "Entreprise spécialisée dans les dispositifs médicaux"
        }
        
        print("📁 Fichiers d'entrée:")
        print(f"   📊 Workshop: {len(workshop_files)} fichier(s)")
        print(f"   📄 Transcript: {len(transcript_files)} fichier(s)")
        print(f"   🏢 Entreprise: {company_info['company_name']}")
        
        print("\n🔄 Exécution du workflow...")
        print("   ├── Start Agents (traitement des fichiers)")
        print("   ├── Collect Data (agrégation)")
        print("   ├── Analyze Needs (identification besoins)")
        print("   ├── Human Validation (validation humaine)")
        print("   ├── Check Success (vérification)")
        print("   └── Finalize Results (sauvegarde + graph)")
        
        # Exécution du workflow
        results = workflow.run(
            workshop_files=workshop_files,
            transcript_files=transcript_files,
            company_info=company_info
        )
        
        # Affichage des résultats
        print("\n📋 Résultats du workflow:")
        print(f"   ✅ Succès: {results.get('success', False)}")
        print(f"   🔄 Itérations: {results.get('iteration_count', 0)}")
        print(f"   📝 Besoins finaux: {len(results.get('final_needs', []))}")
        
        if results.get('final_needs'):
            print("\n🎯 Besoins validés:")
            for i, need in enumerate(results['final_needs'], 1):
                print(f"   {i}. {need.get('title', 'N/A')} - {need.get('theme', 'N/A')}")
        
        # Vérification des fichiers générés
        print("\n📁 Fichiers générés:")
        
        graph_path = "/home/addeche/aiko/aikoGPT/outputs/workflow_graph.png"
        if os.path.exists(graph_path):
            print(f"   📊 Graph: {graph_path}")
        else:
            print("   ⚠️ Graph non généré")
        
        results_path = "/home/addeche/aiko/aikoGPT/outputs/need_analysis_results.json"
        if os.path.exists(results_path):
            print(f"   💾 Résultats: {results_path}")
        else:
            print("   ⚠️ Résultats non sauvegardés")
        
        state_path = "/home/addeche/aiko/aikoGPT/outputs/workflow_state.json"
        if os.path.exists(state_path):
            print(f"   🔄 État: {state_path}")
        else:
            print("   ⚠️ État non sauvegardé")
        
        # Messages du workflow
        if results.get('messages'):
            print("\n💬 Messages du workflow:")
            for msg in results['messages']:
                print(f"   - {msg}")
        
        print("\n✅ Test terminé!")
        return results.get('success', False)
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_human_validation_workflow()
    
    if success:
        print("\n🎉 Workflow avec validation humaine fonctionnel!")
    else:
        print("\n💥 Workflow en erreur!")
