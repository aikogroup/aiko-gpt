"""
UseCaseAnalysisAgent Implementation - Génération des cas d'usage IA

FR: Implémentation complète du UseCaseAnalysisAgent avec génération Quick Wins et Structuration IA
"""

import logging
import json
from typing import Dict, Any, List
from openai import OpenAI

from models.graph_state import NeedAnalysisState
from prompts.use_case_analysis_prompts import (
    USE_CASE_ANALYSIS_SYSTEM_PROMPT,
    USE_CASE_ANALYSIS_INITIAL_USER_PROMPT,
    USE_CASE_ANALYSIS_REGENERATION_USER_PROMPT
)

logger = logging.getLogger(__name__)


def format_validated_needs_for_prompt(validated_needs: List[Dict[str, Any]]) -> str:
    """
    FR: Formate les besoins validés pour le prompt LLM
    
    Args:
        validated_needs: Liste des besoins validés par l'utilisateur
        
    Returns:
        str: Besoins formatés en texte lisible
    """
    if not validated_needs:
        return "Aucun besoin validé"
    
    parts = []
    for idx, need in enumerate(validated_needs, 1):
        parts.append(f"\n**Besoin {idx} :** {need.get('title', 'N/A')}")
        if need.get('citations'):
            parts.append("  **Citations associées :**")
            for citation in need['citations'][:3]:
                parts.append(f"    - \"{citation}\"")
    
    return "\n".join(parts)


def generate_use_cases_with_openai(
    validated_needs: List[Dict[str, Any]],
    workshop_data: Dict[str, Any],
    transcript_data: List[Dict[str, Any]],
    web_search_data: Dict[str, Any],
    validated_quick_wins_count: int,
    validated_structuration_ia_count: int,
    excluded_use_cases: List[str],
    user_comment: str,
    is_regeneration: bool,
    config: Dict[str, Any]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    FR: Génère les cas d'usage avec OpenAI
    
    Args:
        validated_needs: Besoins validés
        workshop_data: Données workshop (contexte)
        transcript_data: Données transcripts (contexte)
        web_search_data: Données contexte
        validated_quick_wins_count: Nombre de QW déjà validés
        validated_structuration_ia_count: Nombre de SIA déjà validées
        excluded_use_cases: Titres de cas d'usage à exclure
        user_comment: Commentaire utilisateur
        is_regeneration: True si régénération
        config: Configuration (model, etc.)
        
    Returns:
        Dict: {"quick_wins": [...], "structuration_ia": [...]}
    """
    logger.info(f"🤖 Génération de cas d'usage avec OpenAI (régénération: {is_regeneration})...")
    
    try:
        # FR: Appliquer la règle intelligente de régénération
        # Si >= 5 validés dans une catégorie, ne rien régénérer pour cette catégorie
        should_generate_qw = (validated_quick_wins_count < 5) if is_regeneration else True
        should_generate_sia = (validated_structuration_ia_count < 5) if is_regeneration else True
        
        if is_regeneration and not should_generate_qw and not should_generate_sia:
            logger.info("✅ Assez de cas d'usage validés dans les 2 catégories (>= 5 chacune), pas de régénération nécessaire")
            return {"quick_wins": [], "structuration_ia": []}
        
        # FR: Formater les données pour le prompt
        from agents.need_analysis_agent_impl import (
            format_workshop_data_for_prompt,
            format_transcript_data_for_prompt,
            format_web_search_data_for_prompt
        )
        
        validated_needs_formatted = format_validated_needs_for_prompt(validated_needs)
        workshop_formatted = format_workshop_data_for_prompt(workshop_data)
        transcript_formatted = format_transcript_data_for_prompt(transcript_data)
        web_search_formatted = format_web_search_data_for_prompt(web_search_data)
        
        # FR: Créer le client OpenAI
        client = OpenAI()
        
        # FR: Choisir le prompt approprié
        if is_regeneration and excluded_use_cases:
            remaining_qw = 8 - validated_quick_wins_count if should_generate_qw else 0
            remaining_sia = 10 - validated_structuration_ia_count if should_generate_sia else 0
            
            user_prompt = USE_CASE_ANALYSIS_REGENERATION_USER_PROMPT.format(
                excluded_use_cases="\n".join(f"- {uc}" for uc in excluded_use_cases),
                user_comment=user_comment or "Aucun commentaire",
                validated_quick_wins_count=validated_quick_wins_count,
                validated_structuration_ia_count=validated_structuration_ia_count,
                remaining_quick_wins_count=remaining_qw,
                remaining_structuration_ia_count=remaining_sia,
                validated_needs=validated_needs_formatted,
                workshop_data=workshop_formatted,
                transcript_data=transcript_formatted,
                web_search_data=web_search_formatted
            )
        else:
            user_prompt = USE_CASE_ANALYSIS_INITIAL_USER_PROMPT.format(
                validated_needs=validated_needs_formatted,
                workshop_data=workshop_formatted,
                transcript_data=transcript_formatted,
                web_search_data=web_search_formatted
            )
        
        # FR: Appeler OpenAI
        response = client.chat.completions.create(
            model=config.get("configurable", {}).get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": USE_CASE_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        # FR: Parser la réponse JSON
        result = json.loads(response.choices[0].message.content)
        
        # FR: Extraire et valider les cas d'usage
        quick_wins = []
        if should_generate_qw:
            for idx, uc in enumerate(result.get("quick_wins", [])[:8], 1):
                quick_wins.append({
                    "id": uc.get("id", f"qw_{idx:03d}"),
                    "category": "quick_win",
                    "title": uc.get("title", f"Quick Win {idx}"),
                    "description": uc.get("description", "Description non disponible"),
                    "ai_technologies": uc.get("ai_technologies", []),
                    "selected": False
                })
        
        structuration_ia = []
        if should_generate_sia:
            for idx, uc in enumerate(result.get("structuration_ia", [])[:10], 1):
                structuration_ia.append({
                    "id": uc.get("id", f"sia_{idx:03d}"),
                    "category": "structuration_ia",
                    "title": uc.get("title", f"Structuration IA {idx}"),
                    "description": uc.get("description", "Description non disponible"),
                    "ai_technologies": uc.get("ai_technologies", []),
                    "selected": False
                })
        
        logger.info(f"✅ {len(quick_wins)} Quick Wins et {len(structuration_ia)} Structuration IA générés")
        
        return {
            "quick_wins": quick_wins,
            "structuration_ia": structuration_ia
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération OpenAI: {e}")
        import traceback
        traceback.print_exc()
        
        # FR: Retourner cas d'usage de fallback
        return {
            "quick_wins": [
                {
                    "id": f"error_qw_{i+1:03d}",
                    "category": "quick_win",
                    "title": f"Erreur Quick Win {i+1}",
                    "description": f"Erreur lors de la génération: {str(e)}",
                    "ai_technologies": ["Erreur"],
                    "selected": False
                }
                for i in range(8)
            ],
            "structuration_ia": [
                {
                    "id": f"error_sia_{i+1:03d}",
                    "category": "structuration_ia",
                    "title": f"Erreur Structuration IA {i+1}",
                    "description": f"Erreur lors de la génération: {str(e)}",
                    "ai_technologies": ["Erreur"],
                    "selected": False
                }
                for i in range(10)
            ]
        }


def use_case_analysis_agent(state: NeedAnalysisState, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    FR: Agent LangGraph pour générer les cas d'usage IA (Quick Wins + Structuration IA)
    
    Args:
        state: État actuel du workflow LangGraph
        config: Configuration LangGraph
        
    Returns:
        Dict: Mise à jour de l'état avec quick_wins et structuration_ia
    """
    logger.info("🎯 UseCaseAnalysisAgent - Début génération cas d'usage")
    
    # FR: Récupérer les données d'entrée
    validated_needs = state.get("validated_needs", [])
    workshop_data = state.get("workshop_data")
    transcript_data = state.get("transcript_data", [])
    web_search_data = state.get("web_search_data")
    action = state.get("action", "generate_use_cases")
    user_comment = state.get("user_comment", "")
    
    # FR: Compter les validés (pour règle intelligente)
    validated_quick_wins_count = len(state.get("validated_quick_wins", []))
    validated_structuration_ia_count = len(state.get("validated_structuration_ia", []))
    
    # FR: Récupérer les exclusions (pour régénération)
    excluded_use_cases = []
    if action == "regenerate_use_cases":
        # FR: Extraire les titres des cas d'usage non validés
        all_qw = state.get("quick_wins", [])
        all_sia = state.get("structuration_ia", [])
        validated_qw_ids = [uc.get("id") for uc in state.get("validated_quick_wins", [])]
        validated_sia_ids = [uc.get("id") for uc in state.get("validated_structuration_ia", [])]
        
        for uc in all_qw:
            if uc.get("id") not in validated_qw_ids:
                excluded_use_cases.append(uc.get("title", ""))
        for uc in all_sia:
            if uc.get("id") not in validated_sia_ids:
                excluded_use_cases.append(uc.get("title", ""))
    
    # FR: Vérifier minimum 5 besoins validés
    if len(validated_needs) < 5:
        logger.warning(f"⚠️ Seulement {len(validated_needs)} besoins validés (minimum 5 requis)")
        return {
            "quick_wins": [],
            "structuration_ia": [],
            "current_step": "use_cases_insufficient_needs",
            "errors": [f"Minimum 5 besoins validés requis (actuellement: {len(validated_needs)})"]
        }
    
    # FR: Déterminer si c'est une régénération
    is_regeneration = (action == "regenerate_use_cases" and len(excluded_use_cases) > 0)
    
    try:
        # FR: Générer les cas d'usage avec OpenAI
        use_cases = generate_use_cases_with_openai(
            validated_needs,
            workshop_data,
            transcript_data,
            web_search_data,
            validated_quick_wins_count,
            validated_structuration_ia_count,
            excluded_use_cases,
            user_comment,
            is_regeneration,
            config
        )
        
        logger.info("✅ UseCaseAnalysisAgent - Génération terminée")
        logger.info(f"📊 {len(use_cases['quick_wins'])} QW + {len(use_cases['structuration_ia'])} SIA générés")
        
        return {
            "quick_wins": use_cases["quick_wins"],
            "structuration_ia": use_cases["structuration_ia"],
            "current_step": "use_cases_generated"
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur inattendue dans UseCaseAnalysisAgent: {e}")
        import traceback
        traceback.print_exc()
        return {
            "quick_wins": [],
            "structuration_ia": [],
            "current_step": "use_cases_error",
            "errors": [f"Erreur UseCaseAnalysisAgent: {str(e)}"]
        }

