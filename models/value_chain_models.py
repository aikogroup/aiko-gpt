"""
Modèles Pydantic pour l'agent d'extraction de la chaîne de valeur
"""

from pydantic import BaseModel, Field
from typing import List


class Function(BaseModel):
    """Modèle pour une fonction (métier ou support)"""
    id: str = Field(description="ID unique de la fonction (ex: F1, F2, ...)")
    nom: str = Field(description="Nom de la fonction (ex: R&D, Infra&IT, Marketing&Communication)")
    type: str = Field(description="Type de fonction: 'fonction_metier' ou 'fonction_support'")
    description: str = Field(description="Description de la fonction et de son rôle dans l'entreprise")


class Mission(BaseModel):
    """Modèle pour une mission d'une fonction"""
    id: str = Field(description="ID unique de la mission (ex: M1, M2, ...)")
    function_nom: str = Field(description="Nom de la fonction à laquelle appartient cette mission (ex: 'Production', 'R&D')")
    resume: str = Field(description="Une phrase résumé de la mission principale de la fonction")


class FrictionPoint(BaseModel):
    """Modèle pour un point de friction lié à la gestion des données"""
    id: str = Field(description="ID unique du point de friction (ex: F1, F2, ...)")
    function_nom: str = Field(description="Nom de la fonction concernée par ce point de friction (ex: 'Production', 'R&D')")
    citation: str = Field(description="Citation textuelle extraite des transcripts révélant le point de friction")
    description: str = Field(description="Explication du point de friction lié à la gestion des données")


class FunctionsResponse(BaseModel):
    """Modèle pour la réponse d'extraction des fonctions"""
    functions: List[Function] = Field(description="Liste des fonctions identifiées (métier et support)")


class MissionsResponse(BaseModel):
    """Modèle pour la réponse d'extraction des missions"""
    missions: List[Mission] = Field(description="Liste des missions par fonction (une phrase résumé par fonction)")


class FrictionPointsResponse(BaseModel):
    """Modèle pour la réponse d'extraction des points de friction"""
    friction_points: List[FrictionPoint] = Field(description="Liste des points de friction liés à la gestion des données, groupés par fonction")


class ValueChainResponse(BaseModel):
    """Modèle complet pour la chaîne de valeur"""
    functions: List[Function] = Field(description="Liste des fonctions (métier et support)")
    missions: List[Mission] = Field(description="Liste des missions (une phrase résumé par fonction)")
    friction_points: List[FrictionPoint] = Field(description="Liste des points de friction liés à la gestion des données")

