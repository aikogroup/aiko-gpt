"""
Modèles Pydantic pour l'agent d'analyse des besoins
"""

from pydantic import BaseModel, Field
from typing import List


class Need(BaseModel):
    """Modèle pour un besoin métier identifié"""
    id: str = Field(description="Identifiant unique du besoin (ex: need_1)")
    theme: str = Field(description="Thème du besoin (ex: Automatisation & efficacité opérationnelle)")
    quotes: List[str] = Field(
        description="Liste de citations exactes provenant des workshops ou transcripts (minimum 1, maximum 10)",
        min_length=1,
        max_length=10
    )


class NeedSummary(BaseModel):
    """Modèle pour le résumé de l'analyse des besoins"""
    total_needs: int = Field(description="Nombre total de besoins identifiés")
    themes: List[str] = Field(description="Liste des thèmes identifiés")


class NeedAnalysisResponse(BaseModel):
    """Modèle pour la réponse complète de l'analyse des besoins"""
    identified_needs: List[Need] = Field(
        description="Liste des besoins métier identifiés"
    )
    summary: NeedSummary = Field(description="Résumé de l'analyse")

