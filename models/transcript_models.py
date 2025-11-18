"""
Modèles Pydantic pour les agents de traitement des transcriptions
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class CitationWithMetadata(BaseModel):
    """Citation avec métadonnées sur le speaker"""
    text: str = Field(
        description="Le texte de la citation, besoin, frustration ou opportunité"
    )
    speaker: Optional[str] = Field(
        default=None,
        description="Nom du speaker qui a exprimé cette citation"
    )
    speaker_level: Optional[str] = Field(
        default=None,
        description="Niveau hiérarchique du speaker: 'direction', 'métier', ou 'inconnu'"
    )
    speaker_type: Optional[str] = Field(
        default=None,
        description="Type de speaker: 'interviewé' ou 'interviewer'"
    )


class SemanticAnalysisResponse(BaseModel):
    """Modèle pour la réponse de l'analyse sémantique des transcriptions"""
    besoins_exprimes: List[CitationWithMetadata] = Field(
        description="Liste des besoins exprimés par les participants avec métadonnées",
        default_factory=list
    )
    frustrations_blocages: List[CitationWithMetadata] = Field(
        description="Liste des frustrations et blocages identifiés avec métadonnées",
        default_factory=list
    )
    attentes_implicites: List[CitationWithMetadata] = Field(
        description="Liste des attentes implicites détectées avec métadonnées",
        default_factory=list
    )
    opportunites_amelioration: List[CitationWithMetadata] = Field(
        description="Liste des opportunités d'amélioration identifiées avec métadonnées",
        default_factory=list
    )
    opportunites_automatisation: List[CitationWithMetadata] = Field(
        description="Liste des opportunités d'automatisation identifiées avec métadonnées",
        default_factory=list
    )
    citations_cles: List[CitationWithMetadata] = Field(
        description="Liste des citations clés extraites des transcriptions avec métadonnées",
        default_factory=list
    )

