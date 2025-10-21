"""
Modèles Pydantic pour l'agent de recherche web
"""

from pydantic import BaseModel, Field


class CompanyInfo(BaseModel):
    """Modèle pour les informations structurées d'une entreprise"""
    nom: str = Field(description="Nom de l'entreprise")
    secteur: str = Field(
        description="Secteur d'activité de l'entreprise",
        default="Non identifié"
    )
    chiffre_affaires: str = Field(
        description="Chiffre d'affaires de l'entreprise",
        default="Non disponible"
    )
    nombre_employes: str = Field(
        description="Nombre d'employés de l'entreprise",
        default="Non disponible"
    )
    description: str = Field(
        description="Description concise de l'entreprise et de ses activités",
        default="Description non disponible"
    )

