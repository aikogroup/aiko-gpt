"""
Exemple d'utilisation du workflow d'analyse des besoins
"""

import os
import sys
from dotenv import load_dotenv

# Ajout du chemin du projet
sys.path.append('/home/addeche/aiko/aikoGPT')

# Chargement des variables d'environnement
load_dotenv()

from workflow.need_analysis_workflow import NeedAnalysisWorkflow


def main():
    """
    Exemple d'utilisation du workflow d'analyse des besoins
    """
    print("🔍 Exemple d'utilisation du Workflow d'Analyse des Besoins")
    print("=" * 60)
    
    # Vérification de la clé API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Clé API OpenAI non trouvée.")
        print("💡 Créez un fichier .env avec OPENAI_API_KEY=votre_cle")
        return
    
    try:
        # Initialisation du workflow
        print("🚀 Initialisation du workflow...")
        workflow = NeedAnalysisWorkflow(api_key)
        
        # Exécution du workflow
        print("📊 Exécution du workflow d'analyse des besoins...")
        print("   - Collecte des données (workshop, transcript, web_search)")
        print("   - Analyse des besoins métier")
        print("   - Validation humaine (simulée)")
        print("   - Génération du graph PNG")
        print("   - Sauvegarde des résultats")
        
        # Fichiers d'exemple
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
        print("\n📋 Résultats:")
        print(f"   ✅ Succès: {results.get('success', False)}")
        print(f"   🔄 Itérations: {results.get('iteration_count', 0)}")
        print(f"   📝 Besoins identifiés: {len(results.get('final_needs', []))}")
        
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
        
        print("\n✅ Workflow terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        print("💡 Vérifiez que tous les modules sont correctement installés")


if __name__ == "__main__":
    main()
