"""
Web Search Agent - Collecte d'informations sur les entreprises via Tavily
"""

import os
import json
from typing import Dict, Any
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI
from models.web_search_models import CompanyInfo

# Charger les variables d'environnement
load_dotenv()


class WebSearchAgent:
    """
    Agent de recherche web pour collecter des informations sur les entreprises
    """
    
    def __init__(self):
        """Initialise l'agent avec les clés API Tavily et OpenAI"""
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY non trouvée dans les variables d'environnement")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY non trouvée dans les variables d'environnement")
        
        self.tavily_client = TavilyClient(api_key=self.tavily_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
    
    def search_company_info(self, company_name: str) -> Dict[str, Any]:
        """
        Recherche des informations sur une entreprise
        
        Args:
            company_name (str): Nom de l'entreprise à rechercher
            
        Returns:
            Dict[str, Any]: Informations structurées sur l'entreprise
        """
        try:
            # Recherche générale
            general_query = f"Informations sur l'entreprise {company_name}"
            general_results = self.tavily_client.search(
                query=general_query,
                search_depth="advanced",
                max_results=5
            )
            
            # Recherche spécifique
            search_query = f"Informations sur l'entreprise {company_name} : secteur, chiffre d'affaires, nombre d'employés"
            specific_results = self.tavily_client.search(
                query=search_query,
                search_depth="advanced", 
                max_results=5
            )

            print(f"Résultats recherche générale: {general_results}")
            print(f"Résultats recherche spécifique: {specific_results}")
            
            # Traitement et structuration des résultats avec LLM
            company_info = self._process_search_results(
                company_name, 
                general_results, 
                specific_results
            )
            
            return company_info
            
        except Exception as e:
            print(f"Erreur lors de la recherche pour {company_name}: {str(e)}")
            return self._get_default_info(company_name)
    
    def _process_search_results(
        self, 
        company_name: str, 
        general_results: Dict, 
        specific_results: Dict
    ) -> Dict[str, Any]:
        """
        Traite et structure les résultats de recherche avec LLM structured output
        
        Args:
            company_name (str): Nom de l'entreprise
            general_results (Dict): Résultats de recherche générale
            specific_results (Dict): Résultats de recherche spécifique (secteur, CA, employés)
            
        Returns:
            Dict[str, Any]: Informations structurées
        """
        try:
            # Formatage des résultats en texte pour le prompt
            general_content = "\n".join([
                f"- {r.get('title', '')}: {r.get('content', '')}"
                for r in general_results.get("results", [])
            ])
            
            specific_content = "\n".join([
                f"- {r.get('title', '')}: {r.get('content', '')}"
                for r in specific_results.get("results", [])
            ])
            
            prompt = f"""Analyse les résultats de recherche suivants pour l'entreprise "{company_name}" et extrait les informations structurées.

INFORMATIONS GÉNÉRALES:
{general_content}

INFORMATIONS SPÉCIFIQUES (SECTEUR, CHIFFRE D'AFFAIRES, EMPLOYÉS):
{specific_content}

Extrait et structure les informations suivantes:
- Nom complet de l'entreprise
- Secteur d'activité de l'entreprise
- Nombre d'employés
- Chiffre d'affaires
- Description concise de l'entreprise (2-3 phrases)

Si une information n'est pas disponible dans les résultats, indique "Non disponible"."""

            # Appel à l'API OpenAI avec structured output
            response = self.openai_client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": f"Tu es un expert en analyse d'informations d'entreprises. Extrait et structure les informations de manière concise et précise.\n\n{prompt}"
                    }
                ],
                text_format=CompanyInfo
            )
            
            # Extraction de la réponse structurée
            parsed_response = response.output_parsed
            company_info = parsed_response.model_dump()
            
            print(f"✓ Informations structurées extraites pour {company_name}")
            
            return company_info
            
        except Exception as e:
            print(f"Erreur lors du traitement LLM: {str(e)}")
            return self._get_default_info(company_name)
    
    def _get_default_info(self, company_name: str) -> Dict[str, Any]:
        """Retourne des informations par défaut en cas d'erreur"""
        return {
            "nom": company_name,
            "secteur": "Non identifié",
            "nombre_employes": "Non disponible",
            "chiffre_affaires": "Non disponible",
            "description": f"Informations sur {company_name} non disponibles"
        }


def main():
    """Fonction de test pour l'agent"""
    try:
        agent = WebSearchAgent()
        company_name = "cousin surgery"
        
        print(f"Recherche d'informations pour : {company_name}")
        print("-" * 50)
        
        results = agent.search_company_info(company_name)
        
        print("Résultats :")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Erreur : {str(e)}")


if __name__ == "__main__":
    main()
