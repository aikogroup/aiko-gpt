"""
NeedAnalysisAgent Implementation - Génération des besoins métier

FR: Implémentation complète du NeedAnalysisAgent avec génération et régénération
FR: ⚠️ AGENT CRITIQUE - Contient toute la logique métier de génération de besoins
"""

import logging
import json
from typing import Dict, Any, List
from openai import OpenAI

from models.graph_state import NeedAnalysisState
from prompts.need_analysis_agent_prompts import (
    NEED_ANALYSIS_SYSTEM_PROMPT,
    NEED_ANALYSIS_INITIAL_USER_PROMPT,
    NEED_ANALYSIS_REGENERATION_USER_PROMPT
)

logger = logging.getLogger(__name__)


def format_workshop_data_for_prompt(workshop_data: Dict[str, Any]) -> str:
    """
    FR: Formate les données workshop pour le prompt LLM
    
    Args:
        workshop_data: Données structurées du WorkshopAgent
        
    Returns:
        str: Données formatées en texte lisible
    """
    if not workshop_data:
        return "Aucune donnée workshop disponible"
    
    parts = []
    parts.append(f"**Atelier :** {workshop_data.get('workshop_name', 'N/A')}")
    
    if workshop_data.get('use_cases'):
        parts.append("\n**Cas d'usage identifiés :**")
        for uc in workshop_data['use_cases']:
            parts.append(f"  - {uc}")
    
    if workshop_data.get('objectives'):
        parts.append("\n**Objectifs :**")
        for obj in workshop_data['objectives']:
            parts.append(f"  - {obj}")
    
    if workshop_data.get('gains'):
        parts.append("\n**Gains attendus :**")
        for gain in workshop_data['gains']:
            parts.append(f"  - {gain}")
    
    if workshop_data.get('summary'):
        parts.append(f"\n**Résumé :** {workshop_data['summary']}")
    
    return "\n".join(parts)


def format_transcript_data_for_prompt(transcript_data: List[Dict[str, Any]]) -> str:
    """
    FR: Formate les données transcript pour le prompt LLM
    
    Args:
        transcript_data: Liste des données structurées du TranscriptAgent
        
    Returns:
        str: Données formatées en texte lisible
    """
    if not transcript_data:
        return "Aucune donnée transcript disponible"
    
    parts = []
    
    for idx, trans in enumerate(transcript_data, 1):
        parts.append(f"\n**Source {idx} :** {trans.get('source', 'N/A')}")
        
        if trans.get('citations'):
            parts.append("  **Citations :**")
            for citation in trans['citations'][:10]:  # Max 10 citations par source
                text = citation.get('text', citation) if isinstance(citation, dict) else citation
                parts.append(f"    - \"{text}\"")
        
        if trans.get('frustrations'):
            parts.append("  **Frustrations :**")
            for frust in trans['frustrations'][:5]:
                desc = frust.get('description', frust) if isinstance(frust, dict) else frust
                parts.append(f"    - {desc}")
        
        if trans.get('expressed_needs'):
            parts.append("  **Besoins exprimés :**")
            for need in trans['expressed_needs'][:5]:
                need_text = need.get('need', need) if isinstance(need, dict) else need
                parts.append(f"    - {need_text}")
    
    return "\n".join(parts)


def format_web_search_data_for_prompt(web_search_data: Dict[str, Any]) -> str:
    """
    FR: Formate les données web search pour le prompt LLM
    
    Args:
        web_search_data: Données structurées du WebSearchAgent
        
    Returns:
        str: Données formatées en texte lisible
    """
    if not web_search_data or not web_search_data.get('fetched'):
        return "Aucune donnée contexte disponible"
    
    parts = []
    parts.append(f"**Entreprise :** {web_search_data.get('company_name', 'N/A')}")
    parts.append(f"**Secteur :** {web_search_data.get('sector', 'N/A')}")
    parts.append(f"**Taille :** {web_search_data.get('size', 'N/A')}")
    
    if web_search_data.get('location'):
        parts.append(f"**Localisation :** {web_search_data['location']}")
    
    if web_search_data.get('recent_news'):
        parts.append("\n**Actualités récentes :**")
        for news in web_search_data['recent_news'][:3]:
            if isinstance(news, dict):
                parts.append(f"  - {news.get('title', news.get('summary', 'N/A'))}")
            else:
                parts.append(f"  - {news}")
    
    if web_search_data.get('sector_challenges'):
        parts.append("\n**Défis du secteur :**")
        for challenge in web_search_data['sector_challenges'][:3]:
            parts.append(f"  - {challenge}")
    
    if web_search_data.get('context_summary'):
        parts.append(f"\n**Contexte :** {web_search_data['context_summary']}")
    
    return "\n".join(parts)


def generate_needs_with_openai(
    workshop_data: Dict[str, Any],
    transcript_data: List[Dict[str, Any]],
    web_search_data: Dict[str, Any],
    excluded_needs: List[str],
    user_comment: str,
    is_regeneration: bool,
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    FR: Génère les 10 besoins avec OpenAI
    
    Args:
        workshop_data: Données workshop
        transcript_data: Données transcripts
        web_search_data: Données contexte
        excluded_needs: Titres de besoins à exclure (régénération)
        user_comment: Commentaire utilisateur
        is_regeneration: True si régénération
        config: Configuration (model, etc.)
        
    Returns:
        List[Dict]: Liste de 10 besoins
    """
    logger.info(f"🤖 Génération de besoins avec OpenAI (régénération: {is_regeneration})...")
    
    try:
        # FR: Formater les données pour le prompt
        workshop_formatted = format_workshop_data_for_prompt(workshop_data)
        transcript_formatted = format_transcript_data_for_prompt(transcript_data)
        web_search_formatted = format_web_search_data_for_prompt(web_search_data)
        
        # FR: Créer le client OpenAI
        client = OpenAI()
        
        # FR: Choisir le prompt approprié
        if is_regeneration and excluded_needs:
            user_prompt = NEED_ANALYSIS_REGENERATION_USER_PROMPT.format(
                excluded_needs="\n".join(f"- {need}" for need in excluded_needs),
                user_comment=user_comment or "Aucun commentaire",
                workshop_data=workshop_formatted,
                transcript_data=transcript_formatted,
                web_search_data=web_search_formatted
            )
        else:
            user_prompt = NEED_ANALYSIS_INITIAL_USER_PROMPT.format(
                workshop_data=workshop_formatted,
                transcript_data=transcript_formatted,
                web_search_data=web_search_formatted
            )
        
        # FR: Appeler OpenAI
        response = client.chat.completions.create(
            model=config.get("configurable", {}).get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": NEED_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,  # FR: Température plus élevée pour créativité
            response_format={"type": "json_object"}
        )
        
        # FR: Parser la réponse JSON
        result = json.loads(response.choices[0].message.content)
        
        # FR: Extraire les besoins
        needs = result.get("needs", [])
        
        # FR: Valider et normaliser
        validated_needs = []
        for idx, need in enumerate(needs[:10]):  # FR: Max 10
            validated_needs.append({
                "id": need.get("id", f"need_{idx+1:03d}"),
                "title": need.get("title", f"Besoin {idx+1}"),
                "citations": need.get("citations", [])[:5],  # FR: Max 5 citations
                "selected": False,
                "edited": False
            })
        
        logger.info(f"✅ {len(validated_needs)} besoins générés avec succès")
        
        return validated_needs
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération OpenAI: {e}")
        import traceback
        traceback.print_exc()
        
        # FR: Retourner besoins de fallback en cas d'erreur
        return [
            {
                "id": f"error_need_{i+1:03d}",
                "title": f"Erreur génération besoin {i+1}",
                "citations": [
                    f"Erreur lors de la génération: {str(e)}"
                ],
                "selected": False,
                "edited": False
            }
            for i in range(10)
        ]


def need_analysis_agent(state: NeedAnalysisState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    FR: Agent LangGraph pour générer les besoins métier
    
    ⚠️ AGENT CRITIQUE - Logique métier complexe
    
    Args:
        state: État actuel du workflow LangGraph
        config: Configuration LangGraph
        
    Returns:
        Dict: Mise à jour de l'état avec needs
    """
    logger.info("💡 NeedAnalysisAgent - Début génération besoins")
    
    # FR: Récupérer les données d'entrée
    workshop_data = state.get("workshop_data")
    transcript_data = state.get("transcript_data", [])
    web_search_data = state.get("web_search_data")
    action = state.get("action", "generate_needs")
    excluded_needs = state.get("excluded_needs", [])
    user_comment = state.get("user_comment", "")
    
    # FR: Vérifier les données minimales
    if not workshop_data and not transcript_data:
        logger.error("❌ Aucune donnée workshop ou transcript disponible")
        return {
            "needs": [],
            "current_step": "needs_error",
            "errors": ["Données insuffisantes pour générer des besoins"]
        }
    
    # FR: Déterminer si c'est une régénération
    is_regeneration = (action == "regenerate_needs" and len(excluded_needs) > 0)
    
    try:
        # FR: Générer les besoins avec OpenAI
        needs = generate_needs_with_openai(
            workshop_data,
            transcript_data,
            web_search_data,
            excluded_needs,
            user_comment,
            is_regeneration,
            config
        )
        
        logger.info("✅ NeedAnalysisAgent - Génération terminée")
        logger.info(f"📊 {len(needs)} besoins générés")
        
        return {
            "needs": needs,
            "current_step": "needs_generated"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur inattendue dans NeedAnalysisAgent: {e}")
        import traceback
        traceback.print_exc()
        return {
            "needs": [],
            "current_step": "needs_error",
            "errors": [f"Erreur NeedAnalysisAgent: {str(e)}"]
        }

