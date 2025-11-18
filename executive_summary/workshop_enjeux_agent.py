"""
Agent spécialisé pour extraire les informations liées aux enjeux stratégiques depuis les ateliers
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv
from process_atelier.workshop_agent import WorkshopAgent
from prompts.executive_summary_prompts import EXTRACT_WORKSHOP_ENJEUX_PROMPT, EXECUTIVE_SUMMARY_SYSTEM_PROMPT
from models.executive_summary_models import WorkshopEnjeuxResponse

load_dotenv()

logger = logging.getLogger(__name__)


class WorkshopEnjeuxAgent:
    """Agent spécialisé pour extraire informations liées aux enjeux stratégiques depuis ateliers"""
    
    def __init__(self, api_key: str = None):
        """
        Initialise l'agent.
        
        Args:
            api_key: Clé API OpenAI
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY doit être définie")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
        
        # Réutiliser WorkshopAgent pour le parsing de base
        self.workshop_agent = WorkshopAgent(openai_api_key=api_key)
    
    def extract_informations(self, document_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Extrait les informations liées aux enjeux stratégiques depuis plusieurs documents workshop dans la BDD.
        
        Args:
            document_ids: Liste des IDs de documents workshop dans la base de données
            
        Returns:
            Liste des informations extraites avec métadonnées
        """
        all_informations = []
        
        for document_id in document_ids:
            try:
                logger.info(f"Traitement atelier pour enjeux: document_id={document_id}")
                
                # Utiliser WorkshopAgent pour charger depuis la BDD
                workshops_data = self.workshop_agent.process_workshop_from_db(document_id)
                
                if not workshops_data:
                    logger.warning(f"Aucune donnée d'atelier trouvée pour document_id={document_id}")
                    continue
                
                # Convertir les WorkshopData en dict si nécessaire
                workshops_dict = []
                for wd in workshops_data:
                    if hasattr(wd, 'model_dump'):
                        workshops_dict.append(wd.model_dump())
                    else:
                        workshops_dict.append(wd)
                
                # Traiter chaque atelier
                for workshop_data in workshops_dict:
                    informations = self._extract_informations_with_llm(workshop_data)
                    all_informations.extend(informations)
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement du document_id {document_id}: {e}", exc_info=True)
                continue
        
        logger.info(f"✅ {len(all_informations)} informations d'enjeux extraites au total")
        return all_informations
    
    def _extract_informations_with_llm(self, workshop_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait les informations pertinentes pour les enjeux stratégiques avec LLM"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Préparer le texte de l'atelier pour l'analyse
                workshop_text = self._prepare_workshop_text(workshop_data)
                
                # Formater le prompt
                prompt = EXTRACT_WORKSHOP_ENJEUX_PROMPT.format(workshop_data=workshop_text)
                
                # Appel LLM avec structured output
                response = self.client.responses.parse(
                    model=self.model,
                    instructions=EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
                    input=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    text_format=WorkshopEnjeuxResponse
                )
                
                # Extraire les informations structurées
                parsed_response = response.output_parsed.model_dump()
                informations_list = parsed_response.get("informations", [])
                
                # Convertir en format dict pour compatibilité
                informations = []
                for info in informations_list:
                    informations.append({
                        "atelier": info.get("atelier", ""),
                        "use_case": info.get("use_case", ""),
                        "objectif": info.get("objectif", ""),
                        "type": info.get("type", "enjeu_strategique")
                    })
                
                logger.info(f"✅ {len(informations)} informations d'enjeux extraites pour l'atelier '{workshop_data.get('theme', 'N/A')}'")
                return informations
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Erreur lors de l'extraction LLM (tentative {attempt + 1}/{max_retries}): {error_msg}")
                
                # Si c'est une erreur de parsing JSON, essayer de récupérer la réponse brute
                if "json_invalid" in error_msg or "EOF while parsing" in error_msg:
                    logger.warning("Erreur de parsing JSON détectée - le modèle a peut-être retourné un JSON invalide")
                    if attempt < max_retries - 1:
                        logger.info("Nouvelle tentative avec un prompt plus strict...")
                        continue
                
                # Si c'est la dernière tentative, logger l'erreur complète et retourner vide
                if attempt == max_retries - 1:
                    logger.error(f"Erreur lors de l'extraction LLM après {max_retries} tentatives: {e}", exc_info=True)
                    return []
        
        return []
    
    def _prepare_workshop_text(self, workshop_data: Dict[str, Any]) -> str:
        """Prépare le texte de l'atelier pour l'analyse"""
        theme = workshop_data.get("theme", "")
        use_cases = workshop_data.get("use_cases", [])
        
        text_parts = [f"Atelier: {theme}"]
        
        for uc in use_cases:
            title = uc.get("title", "")
            objective = uc.get("objective", "")
            text_parts.append(f"- {title}: {objective}")
        
        return "\n".join(text_parts)

