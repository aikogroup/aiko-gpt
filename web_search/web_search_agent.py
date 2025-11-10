"""
Web Search Agent - Collecte d'informations sur les entreprises via Perplexity Sonar
"""

import os
import sys
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from perplexity import Perplexity
from openai import OpenAI

# Ajouter le répertoire parent au PYTHONPATH pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.web_search_models import CompanyInfo
from prompts.web_search_agent_prompts import (
    WEB_SEARCH_SYSTEM_PROMPT,
    WEB_SEARCH_USER_PROMPT_TEMPLATE
)

# Charger les variables d'environnement
load_dotenv()


class WebSearchAgent:
    """
    Agent de recherche web pour collecter des informations sur les entreprises
    """
    
    def __init__(self):
        """Initialise l'agent avec les clés API Perplexity et OpenAI"""
        self.perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.perplexity_api_key:
            raise ValueError("PERPLEXITY_API_KEY non trouvée dans les variables d'environnement")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY non trouvée dans les variables d'environnement")
        
        # Initialiser le client Perplexity
        self.perplexity_client = Perplexity(api_key=self.perplexity_api_key)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
    
    def search_company_info(
        self, 
        company_name: str,
        company_url: Optional[str] = None,
        company_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recherche des informations sur une entreprise
        
        Args:
            company_name (str): Nom de l'entreprise à rechercher
            company_url (str, optional): URL du site web de l'entreprise
            company_description (str, optional): Description courte de l'activité de l'entreprise
            
        Returns:
            Dict[str, Any]: Informations structurées sur l'entreprise
        """
        try:
            # Construction de la requête avec contexte supplémentaire si fourni
            context_parts = []
            
            if company_url:
                context_parts.append(f"Site web de l'entreprise: {company_url}")
            
            if company_description:
                context_parts.append(f"Description de l'activité: {company_description}")
            
            context_section = ""
            if context_parts:
                context_section = "\n\nCONTEXTE SUPPLÉMENTAIRE:\n" + "\n".join(context_parts) + "\n"
            
            # Recherche avec Perplexity Sonar - une seule requête complète
            search_query = f"""Recherche des informations détaillées sur l'entreprise {company_name}:
- Nom complet officiel de l'entreprise
- Secteur d'activité principal
- Nombre d'employés (approximatif)
- Chiffre d'affaires (le plus récent disponible)
- Description de l'activité de l'entreprise

{context_section}Fournis des informations précises et vérifiables. Utilise le contexte supplémentaire fourni pour affiner ta recherche et donner des informations plus pertinentes."""
            
            print(f"🔍 Recherche pour: {company_name}")
            
            perplexity_response = self.perplexity_client.chat.completions.create(
                model="sonar",
                messages=[
                    {"role": "system", "content": "Tu es un assistant de recherche spécialisé dans l'analyse d'entreprises. Tu fournis des informations précises, factuelles et vérifiables."},
                    {"role": "user", "content": search_query}
                ]
            )
            
            search_results = perplexity_response.choices[0].message.content
            
            print(f"📊 Résultats Perplexity:\n{search_results}")
            
            # Traitement et structuration des résultats avec LLM
            company_info = self._process_search_results(
                company_name, 
                search_results
            )
            
            return company_info
            
        except Exception as e:
            print(f"Erreur lors de la recherche pour {company_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._get_default_info(company_name)
    
    def _process_search_results(
        self, 
        company_name: str, 
        search_results: str
    ) -> Dict[str, Any]:
        """
        Traite et structure les résultats de recherche avec LLM structured output
        
        Args:
            company_name (str): Nom de l'entreprise
            search_results (str): Résultats de recherche de Perplexity Sonar
            
        Returns:
            Dict[str, Any]: Informations structurées
        """
        try:
            # Utilisation des prompts depuis le fichier web_search_agent_prompts.py
            user_prompt = f"""Analyse les résultats de recherche suivants pour l'entreprise "{company_name}" et extrait les informations structurées.

RÉSULTATS DE RECHERCHE PERPLEXITY:
{search_results}

{WEB_SEARCH_USER_PROMPT_TEMPLATE.format(company_name=company_name)}"""

            # Appel à l'API OpenAI avec structured output
            # Utilisation du paramètre 'instructions' pour le system prompt
            response = self.openai_client.responses.parse(
                model=self.model,
                instructions=WEB_SEARCH_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": user_prompt
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
        company_name = "aiko"
        
        # Exemple avec contexte supplémentaire
        company_url = "https://www.aikogroup.ai/"
        company_description = "aiko fournit aux entreprises les méthodes, les architectures et les outils pour intégrer les performances de l'IA au sein de leurs processus"
        
        print(f"Recherche d'informations pour : {company_name}")
        print("-" * 50)
        
        # Appel avec contexte supplémentaire
        results = agent.search_company_info(
            company_name,
            company_url=company_url,
            company_description=company_description
        )
        
        print("Résultats :")
        print(json.dumps(results, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"Erreur : {str(e)}")


if __name__ == "__main__":
    main()
