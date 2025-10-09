"""
Test du Web Search Agent avec Tavily
"""

import json
from web_search.web_search_agent import WebSearchAgent


def test_web_search_agent():
    """Test de l'agent de recherche web"""
    try:
        print("🔍 Test du Web Search Agent")
        print("=" * 50)
        
        # Initialisation de l'agent
        agent = WebSearchAgent()
        print("✅ Agent initialisé avec succès")
        
        # Test avec "cousin surgery"
        company_name = "cousin surgery"
        print(f"\n🔎 Recherche d'informations pour : {company_name}")
        print("-" * 30)
        
        # Recherche des informations
        results = agent.search_company_info(company_name)
        
        # Affichage des résultats
        print("\n📊 Résultats de la recherche :")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
        # Vérification de la structure
        required_fields = ["company_name", "sector", "size", "revenue", "description", "recent_news"]
        missing_fields = [field for field in required_fields if field not in results]
        
        if missing_fields:
            print(f"\n⚠️  Champs manquants : {missing_fields}")
        else:
            print("\n✅ Tous les champs requis sont présents")
        
        # Sauvegarde des résultats
        output_file = "outputs/web_search_test_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvegardés dans : {output_file}")
        
        return results
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {str(e)}")
        return None


if __name__ == "__main__":
    test_web_search_agent()
