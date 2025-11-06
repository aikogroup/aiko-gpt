"""
Modèles Pydantic pour l'analyse des atouts de l'entreprise.
"""

from typing import List

from pydantic import BaseModel, Field


class Strength(BaseModel):
    """Représente un atout majeur de l'entreprise."""

    title: str = Field(description="Titre synthétique de l'atout")
    description: str = Field(description="Description concise de l'atout (1 à 2 phrases)")
    evidence: List[str] = Field(
        default_factory=list,
        description="Preuves ou citations issues des ateliers, transcripts ou web"
    )
    ai_opportunities: List[str] = Field(
        default_factory=list,
        description="Opportunités IA concrètes pour exploiter cet atout"
    )


class AtoutsResponse(BaseModel):
    """Sortie structurée de l'agent Atouts."""

    company_name: str = Field(description="Nom de l'entreprise analysée")
    strengths: List[Strength] = Field(
        description="Liste des atouts identifiés (3 à 5 éléments)",
        min_length=3,
        max_length=5
    )
    summary: str = Field(description="Conclusion synthétique mettant en perspective l'IA")


