"""
Modèles Pydantic pour Web Search

FR: Définit la structure des données de recherche entreprise
"""

from pydantic import BaseModel
from typing import Optional, List

# Références code existant :
# - OLD/models/web_search_models.py


# TODO (FR): Modèle pour les données de recherche
class WebSearchData(BaseModel):
    """
    FR: Modèle pour les données de recherche entreprise
    
    Attributes:
        company_name : Nom de l'entreprise recherchée
        sector : Secteur d'activité
        size : Taille de l'entreprise (nb employés, CA)
        location : Localisation (pays, ville)
        recent_news : Actualités récentes
        context : Contexte additionnel enrichi
    """
    company_name: str
    sector: Optional[str] = None
    size: Optional[str] = None
    location: Optional[str] = None
    recent_news: Optional[List[str]] = None
    context: Optional[str] = None


# TODO (FR): Modèle pour l'input de WebSearchAgent
class WebSearchInput(BaseModel):
    """
    FR: Input pour WebSearchAgent
    
    Attributes:
        company_name : Nom de l'entreprise à rechercher
    """
    company_name: str


# TODO (FR): Modèle pour l'output de WebSearchAgent
class WebSearchOutput(BaseModel):
    """
    FR: Output de WebSearchAgent
    
    Attributes:
        data : Données de recherche structurées
    """
    data: WebSearchData

