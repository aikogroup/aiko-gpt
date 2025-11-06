"""
Factory function pour LangGraph CLI

IMPORTANT: Pour développer avec LangGraph Studio, lancez avec:
    uv run langgraph dev --allow-blocking

Les opérations bloquantes (mkdir, file I/O) sont nécessaires pour
l'initialisation mais non-critiques en production.
"""

import os
from langchain_core.runnables import RunnableConfig
from workflow.need_analysis_workflow import NeedAnalysisWorkflow
from executive_summary.executive_summary_workflow import ExecutiveSummaryWorkflow 

def need_analysis(config: RunnableConfig):
    """
    Factory function pour créer le workflow d'analyse des besoins.
    
    Args:
        config: Configuration LangGraph
        
    Returns:
        Workflow configuré
    """
    # Récupérer la clé API depuis la configuration ou l'environnement
    api_key = os.getenv("OPENAI_API_KEY", "test-key")
    
    # Créer le workflow en mode debugging
    workflow = NeedAnalysisWorkflow(
        api_key=api_key,
        dev_mode=False,  # Mode production : vraies recherches
        debug_mode=True  # Debug activé pour LangGraph Studio
    )
    
    return workflow.graph


def executive_summary(config: RunnableConfig):
    """
    Factory function pour créer le workflow d'Executive Summary.
    
    Args:
        config: Configuration LangGraph
        
    Returns:
        Workflow configuré
    """
    # Récupérer la clé API depuis la configuration ou l'environnement
    api_key = os.getenv("OPENAI_API_KEY", "test-key")

        # Créer le workflow en mode debugging
    workflow = ExecutiveSummaryWorkflow(
        api_key=api_key,
        dev_mode=False,  # Mode production : vraies recherches
        debug_mode=True  # Debug activé pour LangGraph Studio
    )
    
    return workflow.graph