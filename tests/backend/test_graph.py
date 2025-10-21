"""
Script de test du graphe LangGraph

FR: Test rapide du workflow d'analyse de besoins
"""

import os
import sys
import logging
from pathlib import Path

# FR: Ajouter le backend au path Python
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from dotenv import load_dotenv

# FR: Charger les variables d'environnement
load_dotenv()

# FR: Activer le checkpointer pour les tests directs
os.environ["USE_CHECKPOINTER"] = "true"

# FR: Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_graph_creation():
    """FR: Test de création du graphe"""
    logger.info("=" * 60)
    logger.info("🧪 Test 1 : Création du graphe LangGraph")
    logger.info("=" * 60)
    
    try:
        from graph_factory import need_analysis
        
        logger.info("✅ Graphe créé avec succès")
        logger.info(f"📊 Type: {type(need_analysis)}")
        
        # FR: Afficher les nodes du graphe
        if hasattr(need_analysis, 'get_graph'):
            graph_def = need_analysis.get_graph()
            logger.info(f"📍 Nodes: {list(graph_def.nodes.keys())}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du graphe: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_execution():
    """FR: Test d'exécution du graphe avec des données de test"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Test 2 : Exécution du graphe avec données de test")
    logger.info("=" * 60)
    
    try:
        from graph_factory import need_analysis
        
        # FR: État initial de test
        root_path = Path(__file__).parent.parent.parent
        initial_state = {
            "excel_file_path": str(root_path / "documents/atelier_exemple.xlsx"),
            "pdf_json_file_paths": [
                str(root_path / "documents/040425-Cousin-Biotech-x-aiko-Echange-IA-Booster-RH-DAF-4e7c7d16-b8f6.pdf")
            ],
            "company_name": "Cousin Biotech",
            "action": "generate_needs"
        }
        
        logger.info("🚀 Lancement du workflow...")
        logger.info(f"📄 Excel: {initial_state['excel_file_path']}")
        logger.info(f"📚 PDF/JSON: {len(initial_state['pdf_json_file_paths'])} fichiers")
        logger.info(f"🏢 Entreprise: {initial_state['company_name']}")
        
        # FR: Configuration avec thread_id (requis par le checkpointer)
        config = {"configurable": {"thread_id": "test-run-001"}}
        
        # FR: Exécuter le graphe
        result = need_analysis.invoke(initial_state, config)
        
        logger.info("\n✅ Workflow terminé avec succès !")
        logger.info(f"📊 Étape finale: {result.get('current_step', 'N/A')}")
        logger.info(f"💡 Besoins générés: {len(result.get('needs', []))}")
        logger.info(f"🎯 Quick Wins: {len(result.get('quick_wins', []))}")
        logger.info(f"🏗️ Structuration IA: {len(result.get('structuration_ia', []))}")
        
        # FR: Afficher le premier besoin généré
        if result.get('needs'):
            logger.info("\n📝 Premier besoin généré:")
            first_need = result['needs'][0]
            logger.info(f"   Titre: {first_need.get('title', 'N/A')}")
            logger.info(f"   Citations: {len(first_need.get('citations', []))}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution du graphe: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """FR: Fonction principale de test"""
    logger.info("🚀 Début des tests du graphe LangGraph")
    logger.info(f"🔑 OpenAI Model: {os.getenv('OPENAI_MODEL', 'Non configuré')}")
    
    # FR: Test 1 - Création
    success_creation = test_graph_creation()
    
    if not success_creation:
        logger.error("❌ Échec du test de création, arrêt des tests")
        return False
    
    # FR: Test 2 - Exécution
    success_execution = test_graph_execution()
    
    # FR: Résumé
    logger.info("\n" + "=" * 60)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("=" * 60)
    logger.info(f"✅ Création du graphe: {'OK' if success_creation else 'ÉCHEC'}")
    logger.info(f"✅ Exécution du graphe: {'OK' if success_execution else 'ÉCHEC'}")
    
    if success_creation and success_execution:
        logger.info("\n🎉 Tous les tests sont passés !")
        return True
    else:
        logger.error("\n❌ Certains tests ont échoué")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

