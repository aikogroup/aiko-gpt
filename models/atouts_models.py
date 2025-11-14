"""
Modèles Pydantic pour l'agent d'extraction des atouts de l'entreprise
"""

from pydantic import BaseModel, Field
from typing import List


class Atout(BaseModel):
    """Modèle pour un atout de l'entreprise"""
    id: int = Field(description="ID unique de l'atout (1, 2, 3, ...)")
    titre: str = Field(description="Titre court et percutant de l'atout (max 15 mots)")
    description: str = Field(description="Description détaillée de l'atout en 3-5 lignes expliquant comment cet atout facilite l'intégration de l'IA dans l'entreprise")


class AtoutsResponse(BaseModel):
    """Modèle pour la réponse d'extraction des atouts"""
    atouts: List[Atout] = Field(description="Liste des atouts identifiés pour l'intégration de l'IA (généralement entre 3 et 6 atouts)")


class CitationAtout(BaseModel):
    """Modèle pour une citation liée aux atouts"""
    citation: str = Field(description="Citation textuelle extraite de l'intervention")
    type_atout: str = Field(description="Type d'atout: 'expertise_metier', 'infrastructure_technique', 'capital_humain', 'culture_innovation', 'agilite_organisation'")
    contexte: str = Field(description="Explication de pourquoi cette citation révèle un atout pour l'intégration de l'IA")


class CitationsAtoutsResponse(BaseModel):
    """Modèle pour les citations d'atouts extraites"""
    citations: List[CitationAtout] = Field(description="Liste des citations révélant les atouts de l'entreprise", default_factory=list)

