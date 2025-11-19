"""
Modèles Pydantic pour l'agent d'extraction de la chaîne de valeur
"""

from pydantic import BaseModel, Field
from typing import List


class Team(BaseModel):
    """Modèle pour une équipe (métier ou support)"""
    id: str = Field(description="ID unique de l'équipe (ex: E1, E2, ...)")
    nom: str = Field(description="Nom de l'équipe (ex: R&D, Infra&IT, Marketing&Communication)")
    type: str = Field(description="Type d'équipe: 'equipe_metier' ou 'equipe_support'")
    description: str = Field(description="Description de l'équipe et de son rôle dans l'entreprise")


class Activity(BaseModel):
    """Modèle pour une activité d'une équipe"""
    id: str = Field(description="ID unique de l'activité (ex: A1, A2, ...)")
    team_nom: str = Field(description="Nom de l'équipe à laquelle appartient cette activité (ex: 'Production', 'R&D')")
    resume: str = Field(description="Une phrase résumé des activités principales de l'équipe")


class FrictionPoint(BaseModel):
    """Modèle pour un point de friction lié à la gestion des données"""
    id: str = Field(description="ID unique du point de friction (ex: F1, F2, ...)")
    team_nom: str = Field(description="Nom de l'équipe concernée par ce point de friction (ex: 'Production', 'R&D')")
    citation: str = Field(description="Citation textuelle extraite des transcripts révélant le point de friction")
    description: str = Field(description="Explication du point de friction lié à la gestion des données")


class TeamsResponse(BaseModel):
    """Modèle pour la réponse d'extraction des équipes"""
    teams: List[Team] = Field(description="Liste des équipes identifiées (métier et support)")


class ActivitiesResponse(BaseModel):
    """Modèle pour la réponse d'extraction des activités"""
    activities: List[Activity] = Field(description="Liste des activités par équipe (une phrase résumé par équipe)")


class FrictionPointsResponse(BaseModel):
    """Modèle pour la réponse d'extraction des points de friction"""
    friction_points: List[FrictionPoint] = Field(description="Liste des points de friction liés à la gestion des données, groupés par équipe")


class ValueChainResponse(BaseModel):
    """Modèle complet pour la chaîne de valeur"""
    teams: List[Team] = Field(description="Liste des équipes (métier et support)")
    activities: List[Activity] = Field(description="Liste des activités (une phrase résumé par équipe)")
    friction_points: List[FrictionPoint] = Field(description="Liste des points de friction liés à la gestion des données")

