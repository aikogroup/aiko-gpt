"""
Agent spécialisé pour extraire les informations liées à la maturité IA depuis les ateliers
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv
from process_atelier.workshop_agent import WorkshopAgent
from prompts.executive_summary_prompts import EXTRACT_WORKSHOP_MATURITE_PROMPT, EXECUTIVE_SUMMARY_SYSTEM_PROMPT
from models.executive_summary_models import WorkshopMaturiteResponse

load_dotenv()

logger = logging.getLogger(__name__)


class WorkshopMaturiteAgent:
    """Agent spécialisé pour extraire informations liées à la maturité IA depuis ateliers"""
    
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
    
    def extract_informations(self, workshop_files: List[str]) -> List[Dict[str, Any]]:
        """
        Extrait les informations liées à la maturité IA depuis plusieurs fichiers d'ateliers.
        
        Args:
            workshop_files: Liste des chemins vers les fichiers Excel d'ateliers
            
        Returns:
            Liste des informations extraites avec métadonnées
        """
        all_informations = []
        
        for file_path in workshop_files:
            try:
                logger.info(f"Traitement atelier pour maturité: {file_path}")
                
                # Utiliser WorkshopAgent pour parser (process_workshop_file attend un fichier, pas une liste)
                workshops_data = self.workshop_agent.process_workshop_file(file_path)
                
                if not workshops_data:
                    logger.warning(f"Aucune donnée d'atelier trouvée dans {file_path}")
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
                logger.error(f"Erreur lors du traitement de {file_path}: {e}", exc_info=True)
                continue
        
        logger.info(f"✅ {len(all_informations)} informations de maturité extraites au total")
        return all_informations
    
    def _extract_informations_with_llm(self, workshop_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait les informations pertinentes pour la maturité IA avec LLM"""
        try:
            # Préparer le texte de l'atelier pour l'analyse
            workshop_text = self._prepare_workshop_text(workshop_data)
            
            # Formater le prompt
            prompt = EXTRACT_WORKSHOP_MATURITE_PROMPT.format(workshop_data=workshop_text)
            
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
                text_format=WorkshopMaturiteResponse
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
                    "type_info": info.get("type_info", "culture_numérique")
                })
            
            logger.info(f"✅ {len(informations)} informations de maturité extraites pour l'atelier '{workshop_data.get('theme', 'N/A')}'")
            return informations
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction LLM: {e}", exc_info=True)
            # Fallback : retourner une liste vide plutôt que de tout retourner
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

