"""
Modèles Pydantic pour Use Case Analysis

FR: Définit la structure des cas d'usage (Quick Wins et Structuration IA)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# Références code existant :
# - OLD/models/use_case_analysis_models.py


# TODO (FR): Enum pour les catégories de cas d'usage
class UseCaseCategory(str, Enum):
    """FR: Catégories de cas d'usage"""
    QUICK_WIN = "quick_win"
    STRUCTURATION_IA = "structuration_ia"


# TODO (FR): Modèle pour un Cas d'Usage
class UseCase(BaseModel):
    """
    FR: Modèle pour un cas d'usage
    
    Attributes:
        id : Identifiant unique
        category : Catégorie (Quick Win ou Structuration IA)
        title : Titre clair et concis
        description : Description du projet
        ai_technologies : Technologies IA utilisées (LLM, RAG, OCR, ML, etc.)
        selected : Indique si l'utilisateur a sélectionné ce cas d'usage
    """
    id: str
    category: UseCaseCategory
    title: str
    description: str
    ai_technologies: List[str]
    selected: bool = False


# TODO (FR): Modèle pour l'input de UseCaseAnalysisAgent
class UseCaseAnalysisInput(BaseModel):
    """
    FR: Input pour UseCaseAnalysisAgent
    
    Attributes:
        validated_needs : Besoins validés à la page 2 (minimum 5)
        workshop_data : Contexte
        transcript_data : Contexte
        web_search_data : Contexte
        validated_quick_wins : QW déjà validés (pour régénération)
        validated_structuration_ia : SIA déjà validés (pour régénération)
        user_comment : Commentaire/consignes utilisateur (optionnel)
    """
    validated_needs: List[dict] = Field(..., min_items=5)
    workshop_data: dict
    transcript_data: List[dict]
    web_search_data: dict
    validated_quick_wins: Optional[List[str]] = None
    validated_structuration_ia: Optional[List[str]] = None
    user_comment: Optional[str] = None


# TODO (FR): Modèle pour l'output de UseCaseAnalysisAgent
class UseCaseAnalysisOutput(BaseModel):
    """
    FR: Output de UseCaseAnalysisAgent
    
    Attributes:
        quick_wins : Liste de 8 Quick Wins
        structuration_ia : Liste de 10 Structuration IA
    """
    quick_wins: List[UseCase] = Field(..., min_items=0, max_items=8)
    structuration_ia: List[UseCase] = Field(..., min_items=0, max_items=10)

