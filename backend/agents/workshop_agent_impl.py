"""
WorkshopAgent Implementation - Parsing Excel et analyse LLM

FR: Implémentation complète du WorkshopAgent avec parsing Excel et appel OpenAI
"""

import logging
import json
from typing import Dict, Any, List
from pathlib import Path
import openpyxl
from openai import OpenAI
from langchain_core.runnables import RunnableConfig

from models.graph_state import NeedAnalysisState
from prompts.workshop_agent_prompts import (
    WORKSHOP_ANALYSIS_SYSTEM_PROMPT,
    WORKSHOP_ANALYSIS_USER_PROMPT
)

logger = logging.getLogger(__name__)


def parse_excel_file(file_path: str) -> List[Dict[str, str]]:
    """
    FR: Parse un fichier Excel et extrait les données des 3 colonnes
    
    Args:
        file_path: Chemin vers le fichier Excel
        
    Returns:
        List[Dict]: Liste de dictionnaires avec colonne_a, colonne_b, colonne_c
        
    Raises:
        FileNotFoundError: Si le fichier n'existe pas
        Exception: Si erreur de parsing
    """
    logger.info(f"📄 Parsing fichier Excel: {file_path}")
    
    if not Path(file_path).exists():
        logger.error(f"❌ Fichier introuvable: {file_path}")
        raise FileNotFoundError(f"Fichier Excel introuvable: {file_path}")
    
    try:
        # FR: Charger le fichier Excel
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active  # FR: Prendre la première feuille
        
        # FR: Extraire les données (en ignorant la ligne d'en-tête si présente)
        raw_data = []
        for row_idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
            if not row or not any(row):  # FR: Ignorer les lignes vides
                continue
                
            col_a = str(row[0]) if row[0] is not None else ""
            col_b = str(row[1]) if len(row) > 1 and row[1] is not None else ""
            col_c = str(row[2]) if len(row) > 2 and row[2] is not None else ""
            
            # FR: Ne garder que les lignes avec au moins un contenu
            if col_a or col_b or col_c:
                raw_data.append({
                    "row_number": row_idx,
                    "nom_atelier": col_a,
                    "cas_usage": col_b,
                    "objectif_gain": col_c
                })
        
        logger.info(f"✅ {len(raw_data)} lignes extraites du fichier Excel")
        return raw_data
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du parsing Excel: {e}")
        raise


def analyze_with_openai(raw_data: List[Dict[str, str]], config: RunnableConfig) -> Dict[str, Any]:
    """
    FR: Analyse les données brutes avec OpenAI pour structurer les informations
    
    Args:
        raw_data: Données brutes extraites du fichier Excel
        config: Configuration LangGraph (contient les settings OpenAI)
        
    Returns:
        Dict: Données structurées (workshop_name, use_cases, objectives, gains, themes, summary)
    """
    logger.info("🤖 Analyse des données avec OpenAI...")
    
    try:
        # FR: Préparer les données brutes pour le prompt
        raw_data_str = json.dumps(raw_data, indent=2, ensure_ascii=False)
        
        # FR: Créer le client OpenAI
        client = OpenAI()  # FR: Utilise OPENAI_API_KEY depuis .env
        
        # FR: Appeler OpenAI avec les prompts
        response = client.chat.completions.create(
            model=config.get("configurable", {}).get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": WORKSHOP_ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": WORKSHOP_ANALYSIS_USER_PROMPT.format(
                    raw_data=raw_data_str
                )}
            ],
            temperature=0.3,  # FR: Basse température pour plus de précision
            response_format={"type": "json_object"}  # FR: Forcer réponse JSON
        )
        
        # FR: Parser la réponse JSON
        result = json.loads(response.choices[0].message.content)
        
        logger.info(f"✅ Analyse terminée - {len(result.get('use_cases', []))} cas d'usage identifiés")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse OpenAI: {e}")
        # FR: En cas d'erreur, retourner une structure minimale
        return {
            "workshop_name": "Atelier (analyse échouée)",
            "use_cases": [],
            "objectives": [],
            "gains": [],
            "main_themes": [],
            "summary": f"Erreur lors de l'analyse: {str(e)}"
        }


def workshop_agent(state: NeedAnalysisState, config: RunnableConfig) -> Dict[str, Any]:
    """
    FR: Agent LangGraph pour analyser le fichier Excel (ateliers)
    
    Args:
        state: État actuel du workflow LangGraph
        config: Configuration LangGraph
        
    Returns:
        Dict: Mise à jour de l'état avec workshop_data
    """
    logger.info("🏭 WorkshopAgent - Début analyse fichier Excel")
    
    excel_file_path = state.get("excel_file_path")
    
    if not excel_file_path:
        logger.warning("⚠️ Aucun fichier Excel fourni, skip")
        return {
            "workshop_data": None,
            "current_step": "workshop_skipped",
            "errors": ["Aucun fichier Excel fourni"]
        }
    
    try:
        # FR: Étape 1 - Parser le fichier Excel
        raw_data = parse_excel_file(excel_file_path)
        
        if not raw_data:
            logger.warning("⚠️ Aucune donnée extraite du fichier Excel")
            return {
                "workshop_data": {
                    "raw_data": [],
                    "use_cases": [],
                    "objectives": [],
                    "parsed": True,
                    "warning": "Fichier Excel vide"
                },
                "current_step": "workshop_empty",
                "errors": ["Fichier Excel vide ou mal formaté"]
            }
        
        # FR: Étape 2 - Analyser avec OpenAI
        analyzed_data = analyze_with_openai(raw_data, config)
        
        # FR: Combiner données brutes + analyse
        workshop_data = {
            **analyzed_data,
            "raw_data": raw_data,
            "parsed": True
        }
        
        logger.info("✅ WorkshopAgent - Analyse terminée")
        logger.info(f"📊 Résumé: {len(raw_data)} lignes, {len(analyzed_data.get('use_cases', []))} cas d'usage")
        
        return {
            "workshop_data": workshop_data,
            "current_step": "workshop_completed"
        }
        
    except FileNotFoundError as e:
        logger.error(f"❌ Fichier introuvable: {e}")
        return {
            "workshop_data": None,
            "current_step": "workshop_error",
            "errors": [f"Fichier Excel introuvable: {excel_file_path}"]
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur inattendue dans WorkshopAgent: {e}")
        import traceback
        traceback.print_exc()
        return {
            "workshop_data": None,
            "current_step": "workshop_error",
            "errors": [f"Erreur WorkshopAgent: {str(e)}"]
        }

