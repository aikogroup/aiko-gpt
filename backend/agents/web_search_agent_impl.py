"""
WebSearchAgent Implementation - Recherche contextuelle entreprise

FR: Implémentation complète du WebSearchAgent avec Perplexity et OpenAI
"""

import logging
import json
import os
from typing import Dict, Any, List
from openai import OpenAI

# FR: Import optionnel du client Perplexity
try:
    from perplexity import Perplexity
    PERPLEXITY_AVAILABLE = True
except ImportError:
    PERPLEXITY_AVAILABLE = False
    Perplexity = None

from models.graph_state import NeedAnalysisState
from prompts.web_search_agent_prompts import (
    WEB_SEARCH_CONTEXT_SYSTEM_PROMPT,
    WEB_SEARCH_STRUCTURING_USER_PROMPT
)

logger = logging.getLogger(__name__)


def search_with_perplexity(company_name: str) -> List[str]:
    """
    FR: Effectue une recherche avec l'API Perplexity
    
    Args:
        company_name: Nom de l'entreprise à rechercher
        
    Returns:
        List[str]: Résultats de la recherche
    """
    logger.info(f"🔍 Recherche Perplexity pour: {company_name}")
    
    if not PERPLEXITY_AVAILABLE:
        logger.warning("⚠️ Client Perplexity non installé")
        return ["Client Perplexity non installé - contexte limité"]
    
    perplexity_api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not perplexity_api_key:
        logger.warning("⚠️ PERPLEXITY_API_KEY non configurée")
        return ["Perplexity API key manquante - contexte limité"]
    
    try:
        # FR: Initialiser le client Perplexity
        perplexity_client = Perplexity(api_key=perplexity_api_key)
        
        # FR: Requête de recherche
        search_query = f"Recherche des informations factuelles sur l'entreprise '{company_name}': secteur d'activité, taille (nombre d'employés), localisation principale, et actualités récentes."
        
        # FR: Appel à l'API Perplexity avec le modèle "sonar"
        # Doc: https://docs.perplexity.ai/
        perplexity_response = perplexity_client.chat.completions.create(
            model="sonar",  # FR: Modèle Perplexity avec recherche web
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant de recherche web. Fournis des informations factuelles et récentes."
                },
                {
                    "role": "user",
                    "content": search_query
                }
            ]
        )
        
        # FR: Extraire le contenu de la réponse
        content = perplexity_response.choices[0].message.content
        
        if not content:
            logger.warning("⚠️ Réponse Perplexity vide")
            return ["Aucun résultat Perplexity"]
        
        logger.info(f"✅ Recherche Perplexity terminée - {len(content)} caractères")
        
        return [content]  # FR: Contenu de la recherche
        
    except Exception as e:
        logger.error(f"❌ Erreur Perplexity: {e}")
        return [f"Erreur lors de la recherche: {str(e)}"]


def structure_with_openai(company_name: str, perplexity_results: List[str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    FR: Structure les résultats de recherche avec OpenAI
    
    Args:
        company_name: Nom de l'entreprise
        perplexity_results: Résultats bruts de Perplexity
        config: Configuration (contient model, etc.)
        
    Returns:
        Dict: Données structurées (sector, size, news, challenges, summary)
    """
    logger.info(f"🤖 Structuration des résultats avec OpenAI pour {company_name}...")
    
    try:
        # FR: Combiner les résultats Perplexity
        perplexity_text = "\n\n".join(perplexity_results)
        
        # FR: Créer le client OpenAI
        client = OpenAI()
        
        # FR: Appeler OpenAI avec les prompts
        response = client.chat.completions.create(
            model=config.get("configurable", {}).get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": WEB_SEARCH_CONTEXT_SYSTEM_PROMPT},
                {"role": "user", "content": WEB_SEARCH_STRUCTURING_USER_PROMPT.format(
                    company_name=company_name,
                    perplexity_results=perplexity_text
                )}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        
        # FR: Parser la réponse JSON
        result = json.loads(response.choices[0].message.content)
        
        logger.info(f"✅ Structuration terminée - Secteur: {result.get('sector', 'N/A')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la structuration OpenAI: {e}")
        # FR: Retourner structure minimale en cas d'erreur
        return {
            "company_name": company_name,
            "sector": "Non disponible",
            "industry": "Non disponible",
            "size": "Non disponible",
            "employee_count": "Non disponible",
            "location": "Non disponible",
            "recent_news": [],
            "sector_challenges": [],
            "context_summary": f"Contexte limité pour {company_name} (erreur lors de la recherche)"
        }


def web_search_agent(state: NeedAnalysisState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    FR: Agent LangGraph pour rechercher le contexte entreprise
    
    ⚠️ RÈGLE CRITIQUE : Fournit uniquement du CONTEXTE, ne génère JAMAIS de besoins
    
    Args:
        state: État actuel du workflow LangGraph
        config: Configuration LangGraph
        
    Returns:
        Dict: Mise à jour de l'état avec web_search_data
    """
    logger.info("🔍 WebSearchAgent - Début recherche contexte entreprise")
    
    company_name = state.get("company_name")
    
    if not company_name:
        logger.warning("⚠️ Aucun nom d'entreprise fourni, skip")
        return {
            "web_search_data": {
                "company_name": None,
                "context_summary": "Aucune recherche effectuée (nom d'entreprise manquant)",
                "fetched": False
            },
            "current_step": "web_search_skipped",
            "errors": ["Aucun nom d'entreprise fourni"]
        }
    
    try:
        # FR: Étape 1 - Recherche avec Perplexity
        perplexity_results = search_with_perplexity(company_name)
        
        # FR: Étape 2 - Structuration avec OpenAI
        web_search_data = structure_with_openai(company_name, perplexity_results, config)
        
        # FR: Ajouter métadonnées
        web_search_data["fetched"] = True
        web_search_data["raw_results"] = perplexity_results
        
        logger.info("✅ WebSearchAgent - Recherche terminée")
        logger.info(f"📊 Secteur: {web_search_data.get('sector', 'N/A')}, Taille: {web_search_data.get('size', 'N/A')}")
        
        return {
            "web_search_data": web_search_data,
            "current_step": "web_search_completed"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur inattendue dans WebSearchAgent: {e}")
        import traceback
        traceback.print_exc()
        return {
            "web_search_data": {
                "company_name": company_name,
                "context_summary": f"Erreur lors de la recherche pour {company_name}",
                "fetched": False,
                "error": str(e)
            },
            "current_step": "web_search_error",
            "errors": [f"Erreur WebSearchAgent: {str(e)}"]
        }

