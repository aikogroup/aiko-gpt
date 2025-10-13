"""
Modèles Pydantic pour les agents de traitement des transcriptions
"""

from pydantic import BaseModel, Field
from typing import List


class SemanticAnalysisResponse(BaseModel):
    """Modèle pour la réponse de l'analyse sémantique des transcriptions"""
    besoins_exprimes: List[str] = Field(
        description="Liste des besoins exprimés par les participants",
        default_factory=list
    )
    frustrations_blocages: List[str] = Field(
        description="Liste des frustrations et blocages identifiés",
        default_factory=list
    )
    attentes_implicites: List[str] = Field(
        description="Liste des attentes implicites détectées",
        default_factory=list
    )
    opportunites_amelioration: List[str] = Field(
        description="Liste des opportunités d'amélioration identifiées",
        default_factory=list
    )
    opportunites_automatisation: List[str] = Field(
        description="Liste des opportunités d'automatisation identifiées",
        default_factory=list
    )
    citations_cles: List[str] = Field(
        description="Liste des citations clés extraites des transcriptions",
        default_factory=list
    )

