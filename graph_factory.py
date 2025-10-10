"""
Factory function pour LangGraph CLI
"""

from langchain_core.runnables import RunnableConfig
from workflow.need_analysis_workflow import NeedAnalysisWorkflow

def need_analysis(config: RunnableConfig):
    """
    Factory function pour créer le workflow d'analyse des besoins.
    
    Args:
        config: Configuration LangGraph
        
    Returns:
        Workflow configuré
    """
    # Récupérer la clé API depuis la configuration ou l'environnement
    import os
    api_key = os.getenv("OPENAI_API_KEY", "test-key")
    
    # Créer le workflow en mode debugging
    workflow = NeedAnalysisWorkflow(
        api_key=api_key,
        dev_mode=True,
        debug_mode=True
    )
    
    return workflow.graph
