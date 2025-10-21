"""
Graph Factory - Création du workflow LangGraph

FR: Ce fichier définit le graphe d'exécution des agents
"""

import logging
import os
from models.graph_state import NeedAnalysisState

# FR: Import optionnel de LangGraph (si installé)
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("⚠️ LangGraph non installé - mode fallback")
    StateGraph = None
    END = "END"

from agents.nodes import (
    workshop_agent,
    transcript_agent,
    web_search_agent,
    need_analysis_agent,
    use_case_analysis_agent,
    report_agent
)

logger = logging.getLogger(__name__)


def create_need_analysis_graph():
    """
    FR: Crée le graphe d'analyse de besoins
    
    Workflow:
    1. WorkshopAgent → Parse Excel
    2. TranscriptAgent → Parse PDF/JSON
    3. WebSearchAgent → Recherche contexte entreprise
    4. NeedAnalysisAgent → Génère 10 besoins
    5. UseCaseAnalysisAgent → Génère Quick Wins + Structuration IA
    6. ReportAgent → Génère rapport Word
    
    Returns:
        CompiledGraph: Le graphe LangGraph compilé et prêt à exécuter
    """
    if not LANGGRAPH_AVAILABLE:
        logger.error("❌ LangGraph n'est pas installé - impossible de créer le graphe")
        logger.info("💡 Installez les dépendances: cd backend && uv pip install -e .")
        return None
    
    logger.info("🔨 Création du graphe d'analyse de besoins...")
    
    # FR: Créer le StateGraph avec notre état personnalisé
    workflow = StateGraph(NeedAnalysisState)
    
    # FR: Ajouter les agents comme nodes
    workflow.add_node("workshop", workshop_agent)
    workflow.add_node("transcript", transcript_agent)
    workflow.add_node("web_search", web_search_agent)
    workflow.add_node("need_analysis", need_analysis_agent)
    workflow.add_node("use_case_analysis", use_case_analysis_agent)
    workflow.add_node("report", report_agent)
    
    # FR: Définir le flux d'exécution (edges)
    # START → workshop → transcript → web_search → need_analysis
    workflow.set_entry_point("workshop")
    workflow.add_edge("workshop", "transcript")
    workflow.add_edge("transcript", "web_search")
    workflow.add_edge("web_search", "need_analysis")
    
    # FR: Après need_analysis, on peut :
    # - Aller vers use_case_analysis (si besoins validés)
    # - Ou terminer (si régénération demandée)
    # Pour l'instant, on va directement à use_case_analysis
    workflow.add_edge("need_analysis", "use_case_analysis")
    
    # FR: use_case_analysis → report → END
    workflow.add_edge("use_case_analysis", "report")
    workflow.add_edge("report", END)
    
    # FR: Checkpointer uniquement pour tests directs (pas pour langgraph dev)
    # LangGraph Server gère automatiquement la persistence
    use_checkpointer = os.getenv("USE_CHECKPOINTER", "false").lower() == "true"
    
    if use_checkpointer:
        # FR: Mode test direct - ajouter un checkpointer
        try:
            from langgraph.checkpoint.memory import InMemorySaver
            checkpointer = InMemorySaver()
            graph = workflow.compile(checkpointer=checkpointer)
            logger.info("🗄️ Graphe compilé avec InMemorySaver (mode test)")
        except ImportError:
            logger.warning("⚠️ InMemorySaver non disponible - compilation sans checkpointer")
            graph = workflow.compile()
        except Exception as e:
            logger.warning(f"⚠️ Erreur checkpointer: {e} - compilation sans checkpointer")
            graph = workflow.compile()
    else:
        # FR: Mode normal - pas de checkpointer (géré par LangGraph Server)
        graph = workflow.compile()
        logger.info("📊 Graphe compilé sans checkpointer (persistence gérée par LangGraph Server)")
    
    logger.info("✅ Graphe d'analyse de besoins créé avec succès")
    logger.info("📊 Nodes: workshop, transcript, web_search, need_analysis, use_case_analysis, report")
    
    return graph


# FR: Créer l'instance du graphe (pour langgraph.json)
need_analysis = create_need_analysis_graph()

if need_analysis:
    logger.info("🚀 Graph factory initialisé avec succès")
else:
    logger.warning("⚠️ Graph factory initialisé en mode fallback (LangGraph non disponible)")

