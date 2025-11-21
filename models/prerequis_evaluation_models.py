"""
Modèles Pydantic pour l'évaluation des 5 prérequis de transformation IA
"""

from pydantic import BaseModel, Field
from typing import List


class PrerequisEvaluation(BaseModel):
    """Modèle pour une évaluation individuelle d'un prérequis"""
    prerequis_id: int = Field(description="ID du prérequis (1 à 5)")
    titre: str = Field(description="Titre du prérequis")
    evaluation_text: str = Field(description="Texte d'évaluation détaillé expliquant la note attribuée")
    note: float = Field(description="Note sur 5 (peut avoir une décimale, ex: 2.3, 4.1)", ge=0.0, le=5.0)


class PrerequisEvaluationResponse(BaseModel):
    """Modèle pour la réponse d'un agent d'évaluation (une évaluation)"""
    evaluation: PrerequisEvaluation = Field(description="Évaluation du prérequis")


class PrerequisDocumentEvaluation(BaseModel):
    """Modèle pour une évaluation par document (prerequis 4 et 5)"""
    prerequis_id: int = Field(description="ID du prérequis (4 ou 5)")
    document_id: int = Field(description="ID du document transcript analysé")
    evaluation_text: str = Field(description="Texte d'évaluation pour ce document")
    note: float = Field(description="Note sur 5 pour ce document (peut avoir une décimale)", ge=0.0, le=5.0)


class PrerequisDocumentEvaluationResponse(BaseModel):
    """Modèle pour la réponse d'évaluation par document"""
    evaluation: PrerequisDocumentEvaluation = Field(description="Évaluation du prérequis pour ce document")


class PrerequisGlobalSynthesis(BaseModel):
    """Modèle pour la synthèse globale (prerequis 4, 5, ou finale)"""
    synthese_text: str = Field(description="Texte de synthèse globale")


class PrerequisFinalResponse(BaseModel):
    """Modèle pour la réponse finale avec les 5 évaluations validées"""
    evaluations: List[PrerequisEvaluation] = Field(description="Liste des 5 évaluations validées", min_length=5, max_length=5)
    synthese_globale: str = Field(description="Synthèse globale des 5 évaluations")

