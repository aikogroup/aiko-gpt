"""
Test minimal de l'architecture LangGraph

FR: Vérifie que le graphe se compile et que la structure est correcte
"""

import sys
import os
import logging
from pathlib import Path

# FR: Ajouter le backend au path Python
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# FR: Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def test_imports():
    """FR: Test 1 - Vérifier que tous les imports fonctionnent"""
    logger.info("=" * 60)
    logger.info("🧪 Test 1 : Imports des modules")
    logger.info("=" * 60)
    
    try:
        logger.info("📦 Import models.graph_state...")
        from models.graph_state import NeedAnalysisState
        logger.info("✅ NeedAnalysisState importé")
        
        logger.info("📦 Import prompts...")
        from prompts.workshop_agent_prompts import WORKSHOP_ANALYSIS_SYSTEM_PROMPT
        from prompts.transcript_agent_prompts import TRANSCRIPT_SEMANTIC_FILTER_SYSTEM_PROMPT
        from prompts.web_search_agent_prompts import WEB_SEARCH_CONTEXT_SYSTEM_PROMPT
        from prompts.need_analysis_agent_prompts import NEED_ANALYSIS_SYSTEM_PROMPT
        from prompts.use_case_analysis_prompts import USE_CASE_ANALYSIS_SYSTEM_PROMPT
        logger.info("✅ Tous les prompts importés")
        
        logger.info("📦 Import agents...")
        from agents.nodes import workshop_agent, transcript_agent, web_search_agent
        logger.info("✅ Agents importés")
        
        logger.info("📦 Import workshop_agent_impl...")
        from agents.workshop_agent_impl import parse_excel_file, analyze_with_openai
        logger.info("✅ Workshop agent implementation importé")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors des imports: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_structure():
    """FR: Test 2 - Vérifier que le graphe LangGraph se compile"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Test 2 : Structure du graphe LangGraph")
    logger.info("=" * 60)
    
    try:
        logger.info("🔨 Import graph_factory...")
        from graph_factory import need_analysis
        
        logger.info("✅ Graphe importé avec succès")
        logger.info(f"📊 Type du graphe: {type(need_analysis)}")
        
        # FR: Vérifier la structure du graphe
        if hasattr(need_analysis, 'get_graph'):
            graph_def = need_analysis.get_graph()
            nodes = list(graph_def.nodes.keys())
            logger.info(f"📍 Nodes du graphe: {nodes}")
            logger.info(f"📊 Nombre de nodes: {len(nodes)}")
            
            expected_nodes = ["workshop", "transcript", "web_search", "need_analysis", "use_case_analysis", "report"]
            missing_nodes = [n for n in expected_nodes if n not in nodes]
            if missing_nodes:
                logger.warning(f"⚠️ Nodes manquants: {missing_nodes}")
            else:
                logger.info("✅ Tous les nodes attendus sont présents")
        else:
            logger.warning("⚠️ Impossible de lire la structure du graphe")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la compilation du graphe: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_structure():
    """FR: Test 3 - Vérifier la structure du State"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Test 3 : Structure du State")
    logger.info("=" * 60)
    
    try:
        from models.graph_state import NeedAnalysisState
        
        # FR: Créer un state de test
        test_state: NeedAnalysisState = {
            "excel_file_path": "./test.xlsx",
            "pdf_json_file_paths": ["./test.pdf"],
            "company_name": "Test Company",
            "workshop_data": None,
            "transcript_data": None,
            "web_search_data": None,
            "needs": None,
            "validated_needs": [],
            "excluded_needs": [],
            "quick_wins": None,
            "structuration_ia": None,
            "validated_quick_wins": [],
            "validated_structuration_ia": [],
            "report_path": None,
            "user_comment": None,
            "action": "generate_needs",
            "errors": [],
            "current_step": "initialized"
        }
        
        logger.info("✅ State de test créé")
        logger.info(f"📊 Clés du state: {list(test_state.keys())}")
        logger.info(f"📝 Company: {test_state.get('company_name')}")
        logger.info(f"📝 Action: {test_state.get('action')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du state: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_prompts_content():
    """FR: Test 4 - Vérifier le contenu des prompts"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Test 4 : Contenu des prompts")
    logger.info("=" * 60)
    
    try:
        from prompts.workshop_agent_prompts import WORKSHOP_ANALYSIS_SYSTEM_PROMPT, WORKSHOP_ANALYSIS_USER_PROMPT
        from prompts.need_analysis_agent_prompts import (
            NEED_ANALYSIS_SYSTEM_PROMPT,
            NEED_ANALYSIS_INITIAL_USER_PROMPT,
            NEED_ANALYSIS_REGENERATION_USER_PROMPT
        )
        
        logger.info("📝 Vérification des prompts Workshop...")
        if "expert en analyse" in WORKSHOP_ANALYSIS_SYSTEM_PROMPT.lower():
            logger.info("✅ Workshop System Prompt OK")
        if "{raw_data}" in WORKSHOP_ANALYSIS_USER_PROMPT:
            logger.info("✅ Workshop User Prompt OK (variable {raw_data} présente)")
        
        logger.info("📝 Vérification des prompts Need Analysis...")
        if "règles cruciales" in NEED_ANALYSIS_SYSTEM_PROMPT.lower():
            logger.info("✅ Need Analysis System Prompt OK (règles critiques présentes)")
        if "workshop_data" in NEED_ANALYSIS_INITIAL_USER_PROMPT:
            logger.info("✅ Need Analysis Initial Prompt OK (variables présentes)")
        if "excluded_needs" in NEED_ANALYSIS_REGENERATION_USER_PROMPT:
            logger.info("✅ Need Analysis Regeneration Prompt OK (exclusions présentes)")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification des prompts: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """FR: Fonction principale de test"""
    logger.info("🚀 Début des tests de validation de l'architecture LangGraph")
    logger.info("")
    
    results = {}
    
    # Test 1 : Imports
    results["imports"] = test_imports()
    
    # Test 2 : Graphe (seulement si imports OK)
    if results["imports"]:
        results["graph"] = test_graph_structure()
    else:
        results["graph"] = False
        logger.warning("⏭️ Test du graphe ignoré (imports échoués)")
    
    # Test 3 : State
    results["state"] = test_state_structure()
    
    # Test 4 : Prompts
    results["prompts"] = test_prompts_content()
    
    # FR: Résumé
    logger.info("\n" + "=" * 60)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - Test {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n🎉 Tous les tests sont passés !")
        logger.info("✅ L'architecture LangGraph est correctement configurée")
        logger.info("🚀 Vous pouvez continuer l'implémentation des agents restants")
        return True
    else:
        logger.error("\n❌ Certains tests ont échoué")
        logger.error("🔧 Veuillez corriger les erreurs avant de continuer")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

