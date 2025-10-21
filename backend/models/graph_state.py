"""
Graph State - État partagé du workflow LangGraph

FR: Définit la structure de données partagée entre tous les agents
"""

from typing import List, Dict, Optional, TypedDict, Annotated
from operator import add


# FR: État partagé pour le workflow d'analyse de besoins
class NeedAnalysisState(TypedDict):
    """
    FR: État partagé pour le workflow d'analyse de besoins
    
    Cet état est passé entre tous les agents du workflow.
    Chaque agent peut lire et mettre à jour cet état.
    """
    
    # FR: Inputs initiaux
    excel_file_path: Optional[str]  # Chemin vers le fichier Excel uploadé
    pdf_json_file_paths: Annotated[List[str], add]  # Chemins vers les PDF/JSON
    company_name: Optional[str]  # Nom de l'entreprise
    
    # FR: Données parsées par les agents
    workshop_data: Optional[Dict]  # Données du WorkshopAgent (Excel)
    transcript_data: Optional[List[Dict]]  # Données du TranscriptAgent (PDF/JSON)
    web_search_data: Optional[Dict]  # Données du WebSearchAgent (Perplexity)
    
    # FR: Besoins générés
    needs: Optional[List[Dict]]  # Liste des 10 besoins générés
    validated_needs: Annotated[List[Dict], add]  # Besoins validés par l'utilisateur
    excluded_needs: Annotated[List[str], add]  # IDs des besoins exclus (pour régénération)
    
    # FR: Cas d'usage générés
    quick_wins: Optional[List[Dict]]  # Liste des Quick Wins (8)
    structuration_ia: Optional[List[Dict]]  # Liste Structuration IA (10)
    validated_quick_wins: Annotated[List[Dict], add]  # Quick Wins validés
    validated_structuration_ia: Annotated[List[Dict], add]  # Structuration IA validés
    
    # FR: Rapport final
    report_path: Optional[str]  # Chemin vers le rapport Word généré
    
    # FR: Métadonnées et contrôle
    user_comment: Optional[str]  # Commentaire utilisateur pour régénération
    action: Optional[str]  # Action demandée (generate_needs, regenerate_needs, etc.)
    errors: Annotated[List[str], add]  # Liste des erreurs rencontrées
    current_step: Optional[str]  # Étape actuelle du workflow

