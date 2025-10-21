"""
Agents Nodes - Fonctions nodes pour le workflow LangGraph

FR: Chaque fonction représente un agent (node) dans le workflow
FR: Ces fonctions wrappent les implémentations réelles des agents
"""

import logging
from typing import Dict, Any, Optional

# FR: Import optionnel de RunnableConfig (si langchain_core installé)
try:
    from langchain_core.runnables import RunnableConfig
except ImportError:
    RunnableConfig = Dict[str, Any]  # FR: Fallback pour tests sans dépendances

from models.graph_state import NeedAnalysisState

logger = logging.getLogger(__name__)


def workshop_agent(state: NeedAnalysisState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    FR: Agent pour analyser le fichier Excel (ateliers)
    
    Args:
        state: État actuel du workflow
        config: Configuration LangGraph (optionnel)
        
    Returns:
        Dict: Mise à jour de l'état avec workshop_data
    """
    # FR: Import dynamique de l'implémentation
    try:
        from agents.workshop_agent_impl import workshop_agent as workshop_agent_impl
        return workshop_agent_impl(state, config or {})
    except ImportError as e:
        logger.warning(f"⚠️ workshop_agent_impl non disponible: {e}")
        # FR: Version de test/fallback
        return {
            "workshop_data": {"test": True, "parsed": False},
            "current_step": "workshop_test_mode",
            "errors": ["workshop_agent_impl non disponible"]
        }


def transcript_agent(state: NeedAnalysisState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    FR: Agent pour analyser les fichiers PDF/JSON (transcriptions)
    
    Args:
        state: État actuel du workflow
        config: Configuration LangGraph (optionnel)
        
    Returns:
        Dict: Mise à jour de l'état avec transcript_data
    """
    # FR: Import dynamique de l'implémentation
    try:
        from agents.transcript_agent_impl import transcript_agent as transcript_agent_impl
        return transcript_agent_impl(state, config or {})
    except ImportError as e:
        logger.warning(f"⚠️ transcript_agent_impl non disponible: {e}")
        # FR: Version de test/fallback
        return {
            "transcript_data": [{"test": True, "parsed": False}],
            "current_step": "transcript_test_mode",
            "errors": ["transcript_agent_impl non disponible"]
        }


def web_search_agent(state: NeedAnalysisState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    FR: Agent pour rechercher le contexte entreprise (Perplexity)
    
    Args:
        state: État actuel du workflow
        config: Configuration LangGraph (optionnel)
        
    Returns:
        Dict: Mise à jour de l'état avec web_search_data
    """
    # FR: Import dynamique de l'implémentation
    try:
        from agents.web_search_agent_impl import web_search_agent as web_search_agent_impl
        return web_search_agent_impl(state, config or {})
    except ImportError as e:
        logger.warning(f"⚠️ web_search_agent_impl non disponible: {e}")
        # FR: Version de test/fallback
        return {
            "web_search_data": {
                "company_name": state.get("company_name", ""),
                "context_summary": "Mode test - recherche non disponible",
                "fetched": False
            },
            "current_step": "web_search_test_mode",
            "errors": ["web_search_agent_impl non disponible"]
        }


def need_analysis_agent(state: NeedAnalysisState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    FR: Agent pour générer les 10 besoins
    
    Args:
        state: État actuel du workflow
        config: Configuration LangGraph (optionnel)
        
    Returns:
        Dict: Mise à jour de l'état avec needs
    """
    # FR: Import dynamique de l'implémentation
    try:
        from agents.need_analysis_agent_impl import need_analysis_agent as need_analysis_agent_impl
        return need_analysis_agent_impl(state, config or {})
    except ImportError as e:
        logger.warning(f"⚠️ need_analysis_agent_impl non disponible: {e}")
        # FR: Version de test/fallback
        return {
            "needs": [
                {
                    "id": f"test_need_{i+1:03d}",
                    "title": f"Besoin test {i+1}",
                    "citations": [f"Citation test {j+1}" for j in range(5)],
                    "selected": False,
                    "edited": False
                }
                for i in range(10)
            ],
            "current_step": "needs_test_mode",
            "errors": ["need_analysis_agent_impl non disponible"]
        }


def use_case_analysis_agent(state: NeedAnalysisState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    FR: Agent pour générer les cas d'usage (Quick Wins + Structuration IA)
    
    Args:
        state: État actuel du workflow
        config: Configuration LangGraph (optionnel)
        
    Returns:
        Dict: Mise à jour de l'état avec quick_wins et structuration_ia
    """
    # FR: Import dynamique de l'implémentation
    try:
        from agents.use_case_analysis_agent_impl import use_case_analysis_agent as use_case_analysis_agent_impl
        return use_case_analysis_agent_impl(state, config or {})
    except ImportError as e:
        logger.warning(f"⚠️ use_case_analysis_agent_impl non disponible: {e}")
        # FR: Version de test/fallback
        return {
            "quick_wins": [
                {
                    "id": f"test_qw_{i+1:03d}",
                    "category": "quick_win",
                    "title": f"Test Quick Win {i+1}",
                    "description": "Description test",
                    "ai_technologies": ["LLM", "RAG"],
                    "selected": False
                }
                for i in range(8)
            ],
            "structuration_ia": [
                {
                    "id": f"test_sia_{i+1:03d}",
                    "category": "structuration_ia",
                    "title": f"Test Structuration IA {i+1}",
                    "description": "Description test",
                    "ai_technologies": ["ML", "NLP"],
                    "selected": False
                }
                for i in range(10)
            ],
            "current_step": "use_cases_test_mode",
            "errors": ["use_case_analysis_agent_impl non disponible"]
        }


def report_agent(state: NeedAnalysisState, config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
    """
    FR: Agent pour générer le rapport Word final
    
    Args:
        state: État actuel du workflow
        config: Configuration LangGraph (optionnel)
        
    Returns:
        Dict: Mise à jour de l'état avec report_path
    """
    # FR: Import dynamique de l'implémentation
    try:
        from agents.report_agent_impl import report_agent as report_agent_impl
        return report_agent_impl(state, config or {})
    except ImportError as e:
        logger.warning(f"⚠️ report_agent_impl non disponible: {e}")
        # FR: Version de test/fallback
        return {
            "report_path": "./outputs/rapport_test_fallback.docx",
            "current_step": "report_test_mode",
            "errors": ["report_agent_impl non disponible"]
        }

