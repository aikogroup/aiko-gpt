"""
Modèles Pydantic pour l'agent d'analyse des cas d'usage IA
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class UseCase(BaseModel):
    """Modèle unifié pour un cas d'usage IA"""
    id: str = Field(description="Identifiant unique du cas d'usage (ex: uc_1)")
    titre: str = Field(description="Titre du cas d'usage")
    # ia_utilisee: str = Field(description="Technologies IA utilisées (ex: LLM + RAG, OCR + NLP, XGBoost + NLP)")
    description: str = Field(description="Description détaillée et actionnable du cas d'usage")
    famille: Optional[str] = Field(
        default=None,
        description="Famille ou catégorie optionnelle du cas d'usage (pour classification manuelle)"
    )


class UseCaseSummary(BaseModel):
    """Modèle pour le résumé de l'analyse des cas d'usage"""
    total_use_cases: int = Field(description="Nombre total de cas d'usage proposés")
    main_themes: List[str] = Field(description="Liste des thèmes principaux couverts")


class UseCaseAnalysisResponse(BaseModel):
    """Modèle pour la réponse complète de l'analyse des cas d'usage"""
    use_cases: List[UseCase] = Field(
        description="Liste des cas d'usage identifiés"
    )
    summary: UseCaseSummary = Field(description="Résumé de l'analyse")

