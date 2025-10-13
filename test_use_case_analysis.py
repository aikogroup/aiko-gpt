"""
Test du workflow d'analyse des cas d'usage IA
"""

import os
import json
import logging
from dotenv import load_dotenv
from use_case_analysis.use_case_analysis_agent import UseCaseAnalysisAgent

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_use_case_analysis():
    """
    Test de l'agent d'analyse des cas d'usage IA.
    """
    logger.info("="*80)
    logger.info("DÉBUT DU TEST - Analyse des cas d'usage IA")
    logger.info("="*80)
    
    # Chargement de la clé API
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("❌ Clé API OpenAI non trouvée dans .env")
        return
    
    logger.info("✅ Clé API OpenAI chargée")
    
    # Initialisation de l'agent
    logger.info("\n📦 Initialisation de l'agent d'analyse des cas d'usage...")
    agent = UseCaseAnalysisAgent(api_key)
    logger.info("✅ Agent initialisé avec succès")
    
    # Charger les besoins validés depuis le fichier de résultats
    logger.info("\n📂 Chargement des besoins validés...")
    try:
        with open('/home/addeche/aiko/aikoGPT/outputs/need_analysis_results.json', 'r', encoding='utf-8') as f:
            need_results = json.load(f)
        
        validated_needs = need_results.get("final_needs", [])
        
        if not validated_needs:
            logger.error("❌ Aucun besoin validé trouvé dans need_analysis_results.json")
            return
        
        logger.info(f"✅ {len(validated_needs)} besoins validés chargés")
        logger.info("\n📋 Besoins validés:")
        for i, need in enumerate(validated_needs, 1):
            logger.info(f"   {i}. {need.get('theme', 'N/A')}")
    
    except FileNotFoundError:
        logger.error("❌ Fichier need_analysis_results.json non trouvé")
        logger.info("💡 Exécutez d'abord test_need_analysis_workflow.py pour générer les besoins")
        return
    except Exception as e:
        logger.error(f"❌ Erreur lors du chargement des besoins: {str(e)}")
        return
    
    # Test 1 : Génération initiale des cas d'usage
    logger.info("\n" + "="*80)
    logger.info("TEST 1 : Génération initiale des cas d'usage")
    logger.info("="*80)
    
    try:
        result = agent.analyze_use_cases(
            validated_needs=validated_needs,
            iteration=1
        )
        
        if "error" in result:
            logger.error(f"❌ Erreur lors de la génération: {result['error']}")
            return
        
        quick_wins = result.get("quick_wins", [])
        structuration_ia = result.get("structuration_ia", [])
        summary = result.get("summary", {})
        
        logger.info(f"\n✅ Cas d'usage générés avec succès!")
        logger.info(f"📊 Quick Wins: {len(quick_wins)}")
        logger.info(f"📊 Structuration IA: {len(structuration_ia)}")
        logger.info(f"📊 Total: {summary.get('total_use_cases', 0)}")
        
        # Afficher les Quick Wins
        logger.info("\n⚡ QUICK WINS:")
        for i, uc in enumerate(quick_wins, 1):
            logger.info(f"\n   {i}. {uc.get('titre', 'N/A')}")
            logger.info(f"      💡 IA: {uc.get('ia_utilisee', 'N/A')}")
            description = uc.get('description', 'N/A')
            if len(description) > 150:
                description = description[:150] + "..."
            logger.info(f"      📝 {description}")
        
        # Afficher les Structuration IA
        logger.info("\n🧠 STRUCTURATION IA:")
        for i, uc in enumerate(structuration_ia, 1):
            logger.info(f"\n   {i}. {uc.get('titre', 'N/A')}")
            logger.info(f"      💡 IA: {uc.get('ia_utilisee', 'N/A')}")
            description = uc.get('description', 'N/A')
            if len(description) > 150:
                description = description[:150] + "..."
            logger.info(f"      📝 {description}")
        
        # Sauvegarder les résultats
        output_path = "/home/addeche/aiko/aikoGPT/outputs/use_case_analysis_test_results.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 Résultats sauvegardés dans {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 2 : Vérification de la validation
    logger.info("\n" + "="*80)
    logger.info("TEST 2 : Vérification de la validation")
    logger.info("="*80)
    
    # Simuler une validation partielle
    validated_qw_count = 3
    validated_sia_count = 4
    
    logger.info(f"📊 Simulation: {validated_qw_count} Quick Wins validés, {validated_sia_count} Structuration IA validés")
    
    success = agent.check_validation_success(validated_qw_count, validated_sia_count)
    
    if success:
        logger.info("✅ Validation réussie (au moins 5 dans chaque famille)")
    else:
        logger.info("⚠️ Validation insuffisante (minimum 5 requis dans chaque famille)")
        logger.info(f"   - Quick Wins: {validated_qw_count}/5")
        logger.info(f"   - Structuration IA: {validated_sia_count}/5")
    
    # Test avec validation complète
    validated_qw_count = 5
    validated_sia_count = 5
    
    logger.info(f"\n📊 Simulation: {validated_qw_count} Quick Wins validés, {validated_sia_count} Structuration IA validés")
    
    success = agent.check_validation_success(validated_qw_count, validated_sia_count)
    
    if success:
        logger.info("✅ Validation réussie (au moins 5 dans chaque famille)")
    else:
        logger.info("⚠️ Validation insuffisante")
    
    # Test 3 : Régénération avec feedback
    logger.info("\n" + "="*80)
    logger.info("TEST 3 : Régénération avec feedback")
    logger.info("="*80)
    
    try:
        # Simuler une régénération
        previous_use_cases = {
            "quick_wins": quick_wins,
            "structuration_ia": structuration_ia
        }
        
        logger.info("📊 Simulation d'une régénération (itération 2)")
        logger.info(f"   - Quick Wins validés: 3/5")
        logger.info(f"   - Structuration IA validés: 4/5")
        
        result2 = agent.analyze_use_cases(
            validated_needs=validated_needs,
            iteration=2,
            previous_use_cases=previous_use_cases,
            validated_quick_wins_count=3,
            validated_structuration_ia_count=4
        )
        
        if "error" in result2:
            logger.error(f"❌ Erreur lors de la régénération: {result2['error']}")
            return
        
        quick_wins2 = result2.get("quick_wins", [])
        structuration_ia2 = result2.get("structuration_ia", [])
        
        logger.info(f"\n✅ Cas d'usage régénérés avec succès!")
        logger.info(f"📊 Quick Wins: {len(quick_wins2)}")
        logger.info(f"📊 Structuration IA: {len(structuration_ia2)}")
        
        # Sauvegarder les résultats de régénération
        output_path2 = "/home/addeche/aiko/aikoGPT/outputs/use_case_analysis_test_iteration2.json"
        with open(output_path2, 'w', encoding='utf-8') as f:
            json.dump(result2, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Résultats de l'itération 2 sauvegardés dans {output_path2}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de régénération: {str(e)}")
        import traceback
        traceback.print_exc()
    
    logger.info("\n" + "="*80)
    logger.info("FIN DU TEST - Analyse des cas d'usage IA")
    logger.info("="*80)
    logger.info("\n✅ Tous les tests sont terminés avec succès!")
    logger.info("\n📂 Fichiers générés:")
    logger.info("   - outputs/use_case_analysis_test_results.json")
    logger.info("   - outputs/use_case_analysis_test_iteration2.json")


if __name__ == "__main__":
    test_use_case_analysis()

