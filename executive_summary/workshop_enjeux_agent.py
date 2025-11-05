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
from prompts.executive_summary_prompts import EXTRACT_WORKSHOP_ENJEUX_PROMPT

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
    
    def extract_informations(self, workshop_files: List[str]) -> List[Dict[str, Any]]:
        """
        Extrait les informations liées aux enjeux stratégiques depuis plusieurs fichiers d'ateliers.
        
        Args:
            workshop_files: Liste des chemins vers les fichiers Excel d'ateliers
            
        Returns:
            Liste des informations extraites avec métadonnées
        """
        all_informations = []
        
        for file_path in workshop_files:
            try:
                logger.info(f"Traitement atelier pour enjeux: {file_path}")
                
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
        
        logger.info(f"✅ {len(all_informations)} informations d'enjeux extraites au total")
        return all_informations
    
    def _extract_informations_with_llm(self, workshop_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait les informations avec LLM"""
        try:
            # Extraire les informations pertinentes directement par filtrage
            # (pas besoin d'appel LLM coûteux si on fait juste un filtrage par mots-clés)
            informations = []
            
            # Retourner les use cases qui révèlent des enjeux stratégiques
            use_cases = workshop_data.get("use_cases", [])
            for uc in use_cases:
                # Si le titre ou l'objectif contient des mots-clés stratégiques
                title = uc.get("title", "").lower()
                objective = uc.get("objective", "").lower()
                
                strategic_keywords = ["stratégie", "transformation", "enjeu", "défi", "vision", "avenir", "compétitivité"]
                
                if any(keyword in title or keyword in objective for keyword in strategic_keywords):
                    informations.append({
                        "atelier": workshop_data.get("theme", ""),
                        "use_case": uc.get("title", ""),
                        "objectif": uc.get("objective", ""),
                        "type": "enjeu_strategique"
                    })
            
            return informations
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction LLM: {e}", exc_info=True)
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

