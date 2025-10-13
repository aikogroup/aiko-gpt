"""
Modèles Pydantic pour l'agent d'analyse des cas d'usage IA
"""

from pydantic import BaseModel, Field
from typing import List


class QuickWin(BaseModel):
    """Modèle pour un cas d'usage Quick Win"""
    id: str = Field(description="Identifiant unique du Quick Win (ex: qw_1)")
    titre: str = Field(description="Titre du cas d'usage")
    ia_utilisee: str = Field(description="Technologies IA utilisées (ex: LLM + RAG, OCR + NLP)")
    description: str = Field(description="Description détaillée et actionnable du cas d'usage")


class StructurationIA(BaseModel):
    """Modèle pour un cas d'usage Structuration IA"""
    id: str = Field(description="Identifiant unique de la Structuration IA (ex: sia_1)")
    titre: str = Field(description="Titre du cas d'usage")
    ia_utilisee: str = Field(description="Technologies IA utilisées (ex: XGBoost + NLP, Séries temporelles)")
    description: str = Field(description="Description détaillée et actionnable du cas d'usage")


class UseCaseSummary(BaseModel):
    """Modèle pour le résumé de l'analyse des cas d'usage"""
    total_quick_wins: int = Field(description="Nombre total de Quick Wins proposés")
    total_structuration_ia: int = Field(description="Nombre total de Structuration IA proposés")
    total_use_cases: int = Field(description="Nombre total de cas d'usage proposés")
    main_themes: List[str] = Field(description="Liste des thèmes principaux couverts")


class UseCaseAnalysisResponse(BaseModel):
    """Modèle pour la réponse complète de l'analyse des cas d'usage"""
    quick_wins: List[QuickWin] = Field(
        description="Liste des cas d'usage Quick Wins",
        min_length=6,
        max_length=10
    )
    structuration_ia: List[StructurationIA] = Field(
        description="Liste des cas d'usage Structuration IA",
        min_length=8,
        max_length=12
    )
    summary: UseCaseSummary = Field(description="Résumé de l'analyse")

