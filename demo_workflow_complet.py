"""
Démonstration complète du workflow d'analyse des besoins
"""

import os
import sys
from dotenv import load_dotenv

# Ajout du chemin du projet
sys.path.append('/home/addeche/aiko/aikoGPT')

# Chargement des variables d'environnement
load_dotenv()

from workflow.need_analysis_workflow import NeedAnalysisWorkflow


def demo_workflow_complet():
    """
    Démonstration complète du workflow avec les 3 agents intégrés
    """
    print("🚀 Démonstration du Workflow d'Analyse des Besoins")
    print("=" * 60)
    
    # Vérification de la clé API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Clé API OpenAI non trouvée.")
        print("💡 Créez un fichier .env avec OPENAI_API_KEY=votre_cle")
        return False
    
    try:
        # Initialisation du workflow
        print("🔧 Initialisation du workflow...")
        workflow = NeedAnalysisWorkflow(api_key)
        
        # Préparation des fichiers d'entrée
        print("\n📁 Préparation des fichiers d'entrée...")
        
        # Fichiers workshop (Excel)
        workshop_files = [
            "/home/addeche/aiko/aikoGPT/inputs/atelier_exemple.xlsx"
        ]
        print(f"   📊 Fichiers workshop: {len(workshop_files)} fichier(s)")
        
        # Fichiers transcript (PDF)
        transcript_files = [
            "/home/addeche/aiko/aikoGPT/inputs/-Cousin-Biotech-x-aiko-Echange-Production-b04e9caa-d79c.pdf",
            "/home/addeche/aiko/aikoGPT/inputs/-Cousin-x-aiko-Echange-Equipe-Technique-64264037-0daa.pdf"
        ]
        print(f"   📄 Fichiers transcript: {len(transcript_files)} fichier(s)")
        
        # Informations entreprise
        company_info = {
            "company_name": "Cousin Biotech",
            "sector": "Médical",
            "size": "50-100 employés",
            "description": "Entreprise spécialisée dans les dispositifs médicaux"
        }
        print(f"   🏢 Entreprise: {company_info['company_name']}")
        
        # Exécution du workflow
        print("\n🔄 Exécution du workflow...")
        print("   ├── Workshop Agent (traitement Excel)")
        print("   ├── Transcript Agent (traitement PDF)")
        print("   ├── Web Search Agent (recherche entreprise)")
        print("   ├── Collect Data (agrégation)")
        print("   ├── Analyze Needs (identification besoins)")
        print("   ├── Human Validation (validation simulée)")
        print("   ├── Check Success (vérification)")
        print("   └── Finalize Results (sauvegarde + graph)")
        
        results = workflow.run(
            workshop_files=workshop_files,
            transcript_files=transcript_files,
            company_info=company_info
        )
        
        # Affichage des résultats détaillés
        print("\n📋 Résultats détaillés:")
        print(f"   ✅ Succès: {results.get('success', False)}")
        print(f"   🔄 Itérations: {results.get('iteration_count', 0)}")
        print(f"   📝 Besoins finaux: {len(results.get('final_needs', []))}")
        
        # Résultats des agents
        print("\n🤖 Résultats des agents:")
        workshop_results = results.get('workshop_results', {})
        print(f"   📊 Workshop: {len(workshop_results.get('use_cases', []))} cas d'usage")
        
        transcript_results = results.get('transcript_results', [])
        print(f"   📄 Transcript: {len(transcript_results)} interventions")
        
        web_search_results = results.get('web_search_results', {})
        print(f"   🌐 Web Search: {web_search_results.get('company_name', 'N/A')}")
        
        # Besoins identifiés
        if results.get('final_needs'):
            print("\n🎯 Besoins métier identifiés:")
            for i, need in enumerate(results['final_needs'], 1):
                print(f"   {i}. {need.get('title', 'N/A')}")
                print(f"      Thème: {need.get('theme', 'N/A')}")
                print(f"      Priorité: {need.get('priority', 'N/A')}")
                if need.get('quotes'):
                    print(f"      Citations: {len(need['quotes'])}")
                print()
        
        # Vérification des fichiers générés
        print("📁 Fichiers générés:")
        
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
        
        # Messages du workflow
        if results.get('messages'):
            print("\n💬 Messages du workflow:")
            for msg in results['messages']:
                print(f"   - {msg}")
        
        print("\n✅ Démonstration terminée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la démonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = demo_workflow_complet()
    
    if success:
        print("\n🎉 Workflow fonctionnel!")
    else:
        print("\n💥 Workflow en erreur!")

