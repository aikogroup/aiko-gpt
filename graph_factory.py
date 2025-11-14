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
from workflow.rappel_mission_workflow import RappelMissionWorkflow
from workflow.atouts_workflow import AtoutsWorkflow 

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
        dev_mode=False  # Mode production : vraies recherches
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
        dev_mode=False  # Mode production : vraies recherches
    )
    
    return workflow.graph


def rappel_mission(config: RunnableConfig):
    """
    Factory function pour créer le workflow de rappel de la mission.
    
    Args:
        config: Configuration LangGraph
        
    Returns:
        Workflow configuré
    """
    workflow = RappelMissionWorkflow()
    return workflow.graph


def atouts_entreprise(config: RunnableConfig):
    """
    Factory function pour créer le workflow d'extraction des atouts de l'entreprise.
    
    Args:
        config: Configuration LangGraph
        
    Returns:
        Workflow configuré
    """
    workflow = AtoutsWorkflow()
    return workflow.graph