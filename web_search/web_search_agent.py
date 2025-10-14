"""
Web Search Agent - Collecte d'informations sur les entreprises via Tavily
"""

import os
import json
from typing import Dict, Any, List
from dotenv import load_dotenv
from tavily import TavilyClient
from openai import OpenAI
from prompts.web_search_agent_prompts import WEB_SEARCH_SYSTEM_PROMPT, WEB_SEARCH_USER_PROMPT_TEMPLATE
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
            # Recherche web avec Tavily
            search_results = self.tavily_client.search(
                query=f"{company_name} entreprise société informations",
                search_depth="advanced",
                max_results=5
            )
            
            # Recherche d'informations financières
            financial_results = self.tavily_client.search(
                query=f"{company_name} chiffre d'affaires, nombre d'employés, taille de l'entreprise",
                search_depth="advanced", 
                max_results=3
            )
            
            # Recherche d'actualités
            news_results = self.tavily_client.search(
                query=f"{company_name} actualités OR \"communiqué de presse\" OR \"annonce récente\" OR partenariat OR lancement 2025",
                search_depth="advanced",
                max_results=8
            )

            print(search_results)
            print(financial_results)
            print(news_results)
            # Traitement et structuration des résultats
            company_info = self._process_search_results(
                company_name, 
                search_results, 
                financial_results, 
                news_results
            )
            
            return company_info
            
        except Exception as e:
            print(f"Erreur lors de la recherche pour {company_name}: {str(e)}")
            return self._get_default_info(company_name)
    
    def _process_search_results(
        self, 
        company_name: str, 
        general_results: Dict, 
        financial_results: Dict, 
        news_results: Dict
    ) -> Dict[str, Any]:
        """
        Traite et structure les résultats de recherche avec LLM structured output
        
        Args:
            company_name (str): Nom de l'entreprise
            general_results (Dict): Résultats de recherche générale
            financial_results (Dict): Résultats de recherche financière
            news_results (Dict): Résultats de recherche d'actualités
            
        Returns:
            Dict[str, Any]: Informations structurées
        """
        try:
            # Préparation des données pour le LLM
            search_data = {
                "company_name": company_name,
                "general_results": general_results.get("results", []),
                "financial_results": financial_results.get("results", []),
                "news_results": news_results.get("results", [])
            }
            
            # Formatage des résultats en texte pour le prompt
            general_content = "\n".join([
                f"- {r.get('title', '')}: {r.get('content', '')[:500]}"
                for r in search_data["general_results"][:3]
            ])
            
            financial_content = "\n".join([
                f"- {r.get('title', '')}: {r.get('content', '')[:300]}"
                for r in search_data["financial_results"][:2]
            ])
            
            news_content = "\n".join([
                f"- {r.get('title', r.get('content', ''))[:200]}"
                for r in search_data["news_results"][:5]
            ])
            
            prompt = f"""Analyse les résultats de recherche suivants pour l'entreprise "{company_name}" et extrait les informations structurées.

INFORMATIONS GÉNÉRALES:
{general_content}

INFORMATIONS FINANCIÈRES:
{financial_content}

ACTUALITÉS RÉCENTES:
{news_content}

Extrait et structure les informations suivantes:
- Secteur d'activité de l'entreprise
- Taille de l'entreprise (nombre d'employés)
- Chiffre d'affaires
- Description concise de l'entreprise (2-3 phrases)
- Liste des actualités récentes les plus pertinentes (jusqu'à 5)

Si une information n'est pas disponible, utilise des valeurs par défaut appropriées."""

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
            # Fallback sur les méthodes manuelles
            return self._fallback_extraction(
                company_name, 
                general_results, 
                financial_results, 
                news_results
            )
    
    def _fallback_extraction(
        self,
        company_name: str,
        general_results: Dict,
        financial_results: Dict,
        news_results: Dict
    ) -> Dict[str, Any]:
        """Méthode fallback en cas d'échec du structured output"""
        description = self._extract_description(general_results)
        sector = self._extract_sector(general_results)
        size = self._extract_company_size(financial_results)
        revenue = self._extract_revenue(financial_results)
        recent_news = self._extract_news(news_results)
        
        return {
            "company_name": company_name,
            "sector": sector,
            "size": size,
            "revenue": revenue,
            "description": description,
            "recent_news": recent_news
        }
    
    def _extract_description(self, results: Dict) -> str:
        """Extrait la description de l'entreprise"""
        if "results" in results and results["results"]:
            # Prendre le premier résultat qui contient une description
            for result in results["results"]:
                print("result dans extract_description")
                print(result)
                if "content" in result:
                    content = result["content"]
                    # Si le contenu dépasse 500 caractères, le résumer avec LLM
                    if len(content) > 500:
                        print("content dans extract_description")
                        print(content)
                        return self._summarize_with_llm(content, "description")
                    else:
                        return content
        return "Description non disponible"
    
    def _extract_sector(self, results: Dict) -> str:
        """Extrait le secteur d'activité"""
        if "results" in results and results["results"]:
            for result in results["results"]:
                if "content" in result:
                    content = result["content"].lower()
                    # Recherche de mots-clés de secteurs
                    sectors = [
                        "technologie", "tech", "informatique", "software",
                        "santé", "médical", "medical", "healthcare",
                        "finance", "banque", "assurance",
                        "industrie", "manufacturing", "production",
                        "conseil", "consulting", "services",
                        "retail", "commerce", "distribution",
                        "automobile", "automotive",
                        "énergie", "energy", "pétrole", "oil",
                        "télécommunications", "telecom"
                    ]
                    
                    for sector in sectors:
                        if sector in content:
                            return sector.title()
        return "Secteur non identifié"
    
    def _extract_company_size(self, results: Dict) -> str:
        """Extrait la taille de l'entreprise"""
        if "results" in results and results["results"]:
            for result in results["results"]:
                if "content" in result:
                    content = result["content"]
                    # Recherche de patterns de taille
                    import re
                    patterns = [
                        r"(\d+)\s*employés?",
                        r"(\d+)\s*personnes?",
                        r"(\d+)\s*salariés?",
                        r"équipe\s*de\s*(\d+)",
                        r"(\d+)\s*personnel"
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            size = int(match.group(1))
                            if size < 10:
                                return "1-10 employés"
                            elif size < 50:
                                return "10-50 employés"
                            elif size < 200:
                                return "50-200 employés"
                            elif size < 1000:
                                return "200-1000 employés"
                            else:
                                return "1000+ employés"
        return "Taille non disponible"
    
    def _extract_revenue(self, results: Dict) -> str:
        """Extrait le chiffre d'affaires"""
        if "results" in results and results["results"]:
            for result in results["results"]:
                if "content" in result:
                    content = result["content"]
                    import re
                    # Recherche de patterns de chiffre d'affaires
                    patterns = [
                        r"chiffre\s*d'affaires\s*[:\s]*([0-9,.\s]+)\s*(€|EUR|euros?|millions?|M)",
                        r"revenue\s*[:\s]*([0-9,.\s]+)\s*(€|EUR|euros?|millions?|M)",
                        r"CA\s*[:\s]*([0-9,.\s]+)\s*(€|EUR|euros?|millions?|M)"
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, content, re.IGNORECASE)
                        if match:
                            amount = match.group(1).strip()
                            unit = match.group(2).upper()
                            return f"{amount} {unit}"
        return "Chiffre d'affaires non disponible"
    
    def _extract_news(self, results: Dict) -> List[str]:
        """Extrait les actualités récentes"""
        news = []
        if "results" in results and results["results"]:
            for result in results["results"]: 
                if "title" in result:
                    title = result["title"]
                    # Si le titre dépasse 500 caractères, le résumer
                    if len(title) > 500:
                        news.append(self._summarize_with_llm(title, "news"))
                    else:
                        news.append(title)
                elif "content" in result:
                    content = result["content"]
                    # Si le contenu dépasse 500 caractères, le résumer
                    if len(content) > 500:
                        news.append(self._summarize_with_llm(content, "news"))
                    else:
                        news.append(content)
        return news if news else ["Aucune actualité récente trouvée"]
    
    def _summarize_with_llm(self, content: str, content_type: str) -> str:
        """
        Résume le contenu avec GPT-4o-mini si il dépasse 500 caractères
        
        Args:
            content (str): Contenu à résumer
            content_type (str): Type de contenu ("description" ou "news")
            
        Returns:
            str: Contenu résumé ou original
        """
        try:
            if content_type == "description":
                print(f"Description: {content}")
                prompt = f"""Résume cette description d'entreprise en 2-3 phrases concises, en gardant les informations clés sur l'activité, le secteur et les caractéristiques principales :

{content}"""
            else:  # news
                prompt = f"""Résume cette actualité en 1-2 phrases, en gardant les informations essentielles et le contexte :

{content}"""
            
            response = self.openai_client.responses.create(
                model=self.model,
                input=[
                    {"role": "developer", "content": "Tu es un assistant spécialisé dans le résumé de contenu. Tu dois fournir des résumés concis et informatifs."},
                    {"role": "user", "content": prompt}
                ],
                max_output_tokens=500
            )
            
            summary = response.output_text
            return summary if summary else content[:500] + "..."
            
        except Exception as e:
            print(f"Erreur lors du résumé LLM: {str(e)}")
            # Fallback: tronquer à 500 caractères
            return content[:500] + "..."
    
    def _get_default_info(self, company_name: str) -> Dict[str, Any]:
        """Retourne des informations par défaut en cas d'erreur"""
        return {
            "company_name": company_name,
            "sector": "Non identifié",
            "size": "Non disponible",
            "revenue": "Non disponible",
            "description": f"Informations sur {company_name} non disponibles",
            "recent_news": ["Aucune actualité trouvée"]
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
