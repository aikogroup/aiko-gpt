"""
Modèles Pydantic pour Need Analysis

FR: Définit la structure des besoins et données associées
"""

from pydantic import BaseModel, Field
from typing import List, Optional

# Références code existant :
# - OLD/models/need_analysis_models.py


# TODO (FR): Modèle pour un Besoin
class Need(BaseModel):
    """
    FR: Modèle pour un besoin généré
    
    Attributes:
        id : Identifiant unique
        title : Titre clair résumant l'apport
        citations : Liste de 5 citations (sources : Excel + PDF/JSON)
        selected : Indique si l'utilisateur a sélectionné ce besoin
        edited : Indique si le besoin a été édité
    """
    id: str
    title: str
    citations: List[str] = Field(..., min_items=5, max_items=5)
    selected: bool = False
    edited: bool = False


# TODO (FR): Modèle pour l'input de NeedAnalysisAgent
class NeedAnalysisInput(BaseModel):
    """
    FR: Input pour NeedAnalysisAgent
    
    Attributes:
        workshop_data : Données du fichier Excel
        transcript_data : Données des PDF/JSON
        web_search_data : Contexte entreprise (⚠️ CONTEXTE uniquement)
        excluded_needs : Besoins à ne pas régénérer (optionnel)
        user_comment : Commentaire/consignes utilisateur (optionnel)
    """
    workshop_data: dict
    transcript_data: List[dict]
    web_search_data: dict
    excluded_needs: Optional[List[str]] = None
    user_comment: Optional[str] = None


# TODO (FR): Modèle pour l'output de NeedAnalysisAgent
class NeedAnalysisOutput(BaseModel):
    """
    FR: Output de NeedAnalysisAgent
    
    Attributes:
        needs : Liste de 10 besoins générés
    """
    needs: List[Need] = Field(..., min_items=10, max_items=10)

