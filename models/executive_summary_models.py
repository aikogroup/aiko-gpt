"""
Modèles Pydantic pour les agents Executive Summary
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class Challenge(BaseModel):
    """Modèle pour un enjeu stratégique"""
    id: str = Field(description="ID unique de l'enjeu (E1, E2, E3, ...)")
    titre: str = Field(description="Titre court et percutant (max 10 mots)")
    description: str = Field(description="Description détaillée en 3-5 lignes expliquant l'enjeu, son impact et sa valeur stratégique")
    besoins_lies: List[str] = Field(description="Titres EXACTS des besoins de la liste fournie qui se rattachent à cet enjeu", default_factory=list)


class ChallengesResponse(BaseModel):
    """Modèle pour la réponse d'identification des enjeux"""
    challenges: List[Challenge] = Field(description="Liste des enjeux stratégiques identifiés (nombre défini par l'utilisateur, généralement entre 6 et 8)")


class MaturityResponse(BaseModel):
    """Modèle pour l'évaluation de maturité IA"""
    echelle: int = Field(description="Échelle de 1 à 5 (1 = Débutant, 2 = Émergent, 3 = Intermédiaire, 4 = Avancé, 5 = Expert)", ge=1, le=5)
    phrase_resumant: str = Field(description="Phrase résumant la situation avec les données, les outils numériques")


class Recommendation(BaseModel):
    """Modèle pour une recommandation stratégique (macro)"""
    id: str = Field(description="ID unique de la recommandation (R1, R2, R3, ...)")
    titre: str = Field(
        description=(
            "Orientation stratégique IA de haut niveau "
            "(max 10 mots, formulation non opérationnelle, vision / principe / axe structurant)"
        )
    )
    description: str = Field(
        description=(
            "Description stratégique expliquant l'intention, "
            "l'impact structurant et l'horizon temporel (12–36 mois). "
            "Aucune action opérationnelle ou outil spécifique."
        )
    )



class RecommendationsResponse(BaseModel):
    """Modèle pour les recommandations"""
    recommendations: List[Recommendation] = Field(description="Liste des recommandations personnalisées (nombre défini par l'utilisateur, généralement entre 6 et 8)")


class NeedItem(BaseModel):
    """Modèle pour un besoin dans le rapport Word"""
    id: Optional[str] = Field(description="ID du besoin", default=None)
    titre: Optional[str] = Field(description="Titre du besoin", default="")
    description: Optional[str] = Field(description="Description du besoin", default="")
    priority: Optional[str] = Field(description="Priorité du besoin", default=None)
    domain: Optional[str] = Field(description="Domaine du besoin", default=None)


class UseCaseItem(BaseModel):
    """Modèle pour un cas d'usage IA dans le rapport Word"""
    id: Optional[str] = Field(description="ID du cas d'usage", default=None)
    titre: Optional[str] = Field(description="Titre du cas d'usage", default="")
    description: Optional[str] = Field(description="Description du cas d'usage", default="")
    famille: Optional[str] = Field(description="Famille optionnelle du cas d'usage", default=None)
    impact: Optional[str] = Field(description="Impact attendu", default=None)
    effort: Optional[str] = Field(description="Effort estimé", default=None)


class WordReportExtraction(BaseModel):
    """Modèle pour l'extraction du rapport Word"""
    final_needs: List[NeedItem] = Field(description="Liste des besoins identifiés", default_factory=list)
    final_use_cases: List[UseCaseItem] = Field(description="Liste des cas d'usage IA", default_factory=list)


class CitationEnjeux(BaseModel):
    """Modèle pour une citation liée aux enjeux stratégiques"""
    citation: str = Field(description="Citation textuelle")
    speaker: str = Field(description="Auteur de la citation")


class CitationsEnjeuxResponse(BaseModel):
    """Modèle pour les citations d'enjeux extraites"""
    citations: List[CitationEnjeux] = Field(description="Liste des citations liées aux enjeux stratégiques", default_factory=list)


class CitationMaturite(BaseModel):
    """Modèle pour une citation liée à la maturité IA"""
    citation: str = Field(description="Citation textuelle")
    speaker: str = Field(description="Auteur de la citation")
    type_info: str = Field(description="Type d'information: 'outils_digitaux', 'processus_automatises', 'gestion_donnees', 'culture_numérique'")


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


class WorkshopEnjeuxInfo(BaseModel):
    """Modèle pour une information d'enjeu stratégique extraite depuis un atelier"""
    atelier: str = Field(description="Thème de l'atelier")
    use_case: str = Field(description="Titre du cas d'usage")
    objectif: str = Field(description="Objectif du cas d'usage")
    type: str = Field(description="Type d'information, toujours 'enjeu_strategique'", default="enjeu_strategique")


class WorkshopEnjeuxResponse(BaseModel):
    """Modèle pour les informations d'enjeux stratégiques extraites depuis les ateliers"""
    informations: List[WorkshopEnjeuxInfo] = Field(description="Liste des cas d'usage qui révèlent des enjeux stratégiques de l'IA", default_factory=list)

