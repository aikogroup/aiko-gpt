"""
Modèles Pydantic pour les agents Executive Summary
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Challenge(BaseModel):
    """Modèle pour un enjeu stratégique"""
    id: str = Field(description="ID unique de l'enjeu (E1, E2, E3, E4, E5)")
    titre: str = Field(description="Titre court et percutant (max 10 mots)")
    description: str = Field(description="Description détaillée en 3-5 lignes expliquant l'enjeu, son impact et sa valeur stratégique")
    besoins_lies: List[str] = Field(description="IDs ou titres des besoins qui se rattachent à cet enjeu", default_factory=list)


class ChallengesResponse(BaseModel):
    """Modèle pour la réponse d'identification des enjeux"""
    challenges: List[Challenge] = Field(description="Liste des 5 enjeux stratégiques identifiés")


class MaturityResponse(BaseModel):
    """Modèle pour l'évaluation de maturité IA"""
    echelle: int = Field(description="Échelle de 1 à 5 (1 = Débutant, 2 = Émergent, 3 = Intermédiaire, 4 = Avancé, 5 = Expert)", ge=1, le=5)
    phrase_resumant: str = Field(description="Phrase résumant la situation avec les données, les outils numériques")


class RecommendationsResponse(BaseModel):
    """Modèle pour les recommandations"""
    recommendations: List[str] = Field(description="Liste des 4 recommandations personnalisées", min_length=4, max_length=4)


class NeedItem(BaseModel):
    """Modèle pour un besoin dans le rapport Word"""
    id: Optional[str] = Field(description="ID du besoin", default=None)
    titre: Optional[str] = Field(description="Titre du besoin", default="")
    description: Optional[str] = Field(description="Description du besoin", default="")
    priority: Optional[str] = Field(description="Priorité du besoin", default=None)
    domain: Optional[str] = Field(description="Domaine du besoin", default=None)


class QuickWinItem(BaseModel):
    """Modèle pour un cas d'usage Quick Win dans le rapport Word"""
    id: Optional[str] = Field(description="ID du cas d'usage", default=None)
    titre: Optional[str] = Field(description="Titre du cas d'usage", default="")
    description: Optional[str] = Field(description="Description du cas d'usage", default="")
    impact: Optional[str] = Field(description="Impact attendu", default=None)
    effort: Optional[str] = Field(description="Effort estimé", default=None)


class StructurationIAItem(BaseModel):
    """Modèle pour un cas d'usage Structuration IA dans le rapport Word"""
    id: Optional[str] = Field(description="ID du cas d'usage", default=None)
    titre: Optional[str] = Field(description="Titre du cas d'usage", default="")
    description: Optional[str] = Field(description="Description du cas d'usage", default="")
    impact: Optional[str] = Field(description="Impact attendu", default=None)
    effort: Optional[str] = Field(description="Effort estimé", default=None)


class WordReportExtraction(BaseModel):
    """Modèle pour l'extraction du rapport Word"""
    final_needs: List[NeedItem] = Field(description="Liste des besoins identifiés", default_factory=list)
    final_quick_wins: List[QuickWinItem] = Field(description="Liste des cas d'usage Quick Wins", default_factory=list)
    final_structuration_ia: List[StructurationIAItem] = Field(description="Liste des cas d'usage Structuration IA", default_factory=list)


class CitationEnjeux(BaseModel):
    """Modèle pour une citation liée aux enjeux stratégiques"""
    citation: str = Field(description="Citation textuelle")
    speaker: str = Field(description="Auteur de la citation")
    timestamp: Optional[str] = Field(description="Horodatage si disponible", default=None)
    contexte: str = Field(description="Contexte de la citation", default="")


class CitationsEnjeuxResponse(BaseModel):
    """Modèle pour les citations d'enjeux extraites"""
    citations: List[CitationEnjeux] = Field(description="Liste des citations liées aux enjeux stratégiques", default_factory=list)


class CitationMaturite(BaseModel):
    """Modèle pour une citation liée à la maturité IA"""
    citation: str = Field(description="Citation textuelle")
    speaker: str = Field(description="Auteur de la citation")
    timestamp: Optional[str] = Field(description="Horodatage si disponible", default=None)
    type_info: str = Field(description="Type d'information: 'outils_digitaux', 'processus_automatises', 'gestion_donnees', 'culture_numérique'")
    contexte: str = Field(description="Contexte de la citation", default="")


class CitationsMaturiteResponse(BaseModel):
    """Modèle pour les citations de maturité extraites"""
    citations: List[CitationMaturite] = Field(description="Liste des citations liées à la maturité IA", default_factory=list)


class WorkshopMaturiteInfo(BaseModel):
    """Modèle pour une information de maturité extraite depuis un atelier"""
    atelier: str = Field(description="Thème de l'atelier")
    use_case: str = Field(description="Titre du cas d'usage")
    objectif: str = Field(description="Objectif du cas d'usage")
    type_info: str = Field(description="Type d'information: 'outils_digitaux', 'processus_automatises', 'gestion_donnees', 'culture_numérique'")


class WorkshopMaturiteResponse(BaseModel):
    """Modèle pour les informations de maturité extraites depuis les ateliers"""
    informations: List[WorkshopMaturiteInfo] = Field(description="Liste des informations pertinentes pour évaluer la maturité IA", default_factory=list)

