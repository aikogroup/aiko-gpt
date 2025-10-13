"""
Modèles Pydantic pour l'agent de recherche web
"""

from pydantic import BaseModel, Field
from typing import List


class CompanyInfo(BaseModel):
    """Modèle pour les informations structurées d'une entreprise"""
    company_name: str = Field(description="Nom de l'entreprise")
    sector: str = Field(
        description="Secteur d'activité de l'entreprise",
        default="Non identifié"
    )
    size: str = Field(
        description="Taille de l'entreprise (nombre d'employés)",
        default="Non disponible"
    )
    revenue: str = Field(
        description="Chiffre d'affaires de l'entreprise",
        default="Non disponible"
    )
    description: str = Field(
        description="Description concise de l'entreprise et de ses activités",
        default="Description non disponible"
    )
    recent_news: List[str] = Field(
        description="Liste des actualités récentes de l'entreprise",
        default_factory=lambda: ["Aucune actualité récente trouvée"]
    )

