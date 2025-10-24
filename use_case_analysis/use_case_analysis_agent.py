"""
Agent d'analyse et identification des cas d'usage IA
"""

import json
import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
from prompts.use_case_analysis_prompts import (
    USE_CASE_ANALYSIS_SYSTEM_PROMPT,
    USE_CASE_ANALYSIS_USER_PROMPT,
    USE_CASE_REGENERATION_PROMPT
)
from models.use_case_analysis_models import UseCaseAnalysisResponse

# Import du tracker
import sys
sys.path.append('/home/addeche/aiko/aikoGPT')
from utils.token_tracker import TokenTracker

# Configuration du logger
logger = logging.getLogger(__name__)


class UseCaseAnalysisAgent:
    """
    Agent responsable de l'identification des cas d'usage IA à partir des besoins validés.
    Propose 2 familles de cas d'usage :
    - Quick Wins (8) : automatisation rapide, ROI immédiat
    - Structuration IA (10) : solutions avancées, ROI moyen/long terme
    """
    
    def __init__(self, api_key: str, tracker: Optional[TokenTracker] = None):
        """
        Initialise l'agent avec la clé API OpenAI.
        
        Args:
            api_key: Clé API OpenAI
            tracker: TokenTracker optionnel pour le suivi des tokens et coûts
        """
        import os
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.tracker = tracker  # Tracker pour le suivi des tokens
        logger.info(f"UseCaseAnalysisAgent initialisé avec le modèle {self.model}")
        
    def analyze_use_cases(
        self, 
        validated_needs: List[Dict],
        workshop_data: Dict = None,
        transcript_data: List[Dict] = None,
        web_search_data: Dict = None,
        iteration: int = 1,
        previous_use_cases: Optional[Dict] = None,
        rejected_quick_wins: Optional[List[Dict]] = None,
        rejected_structuration_ia: Optional[List[Dict]] = None,
        user_feedback: str = "",
        validated_quick_wins_count: int = 0,
        validated_structuration_ia_count: int = 0
    ) -> Dict[str, Any]:
        """
        Analyse les besoins validés et identifie les cas d'usage IA pertinents.
        
        Args:
            validated_needs: Liste des besoins validés
            workshop_data: Données des workshops (contexte entreprise)
            transcript_data: Données des transcripts (contexte métier)
            web_search_data: Données web search (contexte marché)
            iteration: Numéro de l'itération actuelle
            previous_use_cases: Cas d'usage proposés lors de l'itération précédente
            rejected_quick_wins: Quick Wins rejetés par l'utilisateur
            rejected_structuration_ia: Structuration IA rejetés par l'utilisateur
            user_feedback: Commentaires de l'utilisateur
            validated_quick_wins_count: Nombre de Quick Wins validés
            validated_structuration_ia_count: Nombre de Structuration IA validés
            
        Returns:
            Dict contenant les cas d'usage identifiés (quick_wins et structuration_ia)
        """
        try:
            logger.info(f"Début de l'analyse des cas d'usage - Itération {iteration}")
            logger.info(f"Nombre de besoins validés en entrée : {len(validated_needs)}")
            
            # LOG DÉTAILLÉ : Afficher les besoins reçus
            print(f"\n🔍 [DEBUG USE CASE] Besoins validés reçus par l'agent:")
            print(f"  📊 Nombre total: {len(validated_needs)}")
            print(f"  📝 Type de données: {type(validated_needs)}")
            for i, need in enumerate(validated_needs, 1):
                if isinstance(need, dict):
                    theme = need.get('theme', 'N/A')
                    quotes_count = len(need.get('quotes', []))
                    print(f"  {i}. Theme: {theme} (Citations: {quotes_count})")
                else:
                    # Objet Pydantic
                    theme = getattr(need, 'theme', 'N/A')
                    quotes_count = len(getattr(need, 'quotes', []))
                    print(f"  {i}. Theme: {theme} (Citations: {quotes_count})")
            
            # Conversion sécurisée des données pour la sérialisation JSON
            validated_needs_safe = self._safe_serialize(validated_needs)
            validated_needs_str = json.dumps(validated_needs_safe, ensure_ascii=False, indent=2)
            
            # Sérialiser les données de contexte (workshop, transcript, web_search)
            workshop_data_safe = self._safe_serialize(workshop_data or {})
            transcript_data_safe = self._safe_serialize(transcript_data or [])
            web_search_data_safe = self._safe_serialize(web_search_data or {})
            
            workshop_str = json.dumps(workshop_data_safe, ensure_ascii=False, indent=2)
            transcript_str = json.dumps(transcript_data_safe, ensure_ascii=False, indent=2)
            web_search_str = json.dumps(web_search_data_safe, ensure_ascii=False, indent=2)
            
            # LOG DÉTAILLÉ : Afficher le JSON envoyé au LLM (premiers 1000 caractères)
            print(f"\n📤 [DEBUG USE CASE] Données envoyées au LLM:")
            print(f"  📊 Validated needs: {len(validated_needs_str)} caractères")
            print(f"  🏭 Workshop data: {len(workshop_str)} caractères")
            print(f"  🎤 Transcript data: {len(transcript_str)} caractères")
            print(f"  🌐 Web search data: {len(web_search_str)} caractères")
            print(f"  📈 Total: {len(validated_needs_str) + len(workshop_str) + len(transcript_str) + len(web_search_str)} caractères")
            print()
            
            # Choix du prompt selon l'itération
            if iteration == 1:
                logger.info("Première itération - Génération initiale des cas d'usage")
                user_prompt = USE_CASE_ANALYSIS_USER_PROMPT.format(
                    validated_needs=validated_needs_str,
                    workshop_data=workshop_str,
                    transcript_data=transcript_str,
                    web_search_data=web_search_str
                )
            else:
                logger.info(f"Itération {iteration} - Régénération avec feedback")
                logger.info(f"Quick Wins validés : {validated_quick_wins_count} / 5")
                logger.info(f"Structuration IA validés : {validated_structuration_ia_count} / 5")
                
                if user_feedback:
                    logger.info(f"Commentaires utilisateur : {user_feedback[:100]}...")
                
                rejected_qw_count = len(rejected_quick_wins or [])
                rejected_sia_count = len(rejected_structuration_ia or [])
                
                logger.info(f"Quick Wins rejetés : {rejected_qw_count}")
                logger.info(f"Structuration IA rejetés : {rejected_sia_count}")
                
                previous_use_cases_str = json.dumps(
                    self._safe_serialize(previous_use_cases), 
                    ensure_ascii=False, 
                    indent=2
                )
                
                rejected_use_cases = {
                    "rejected_quick_wins": rejected_quick_wins or [],
                    "rejected_structuration_ia": rejected_structuration_ia or []
                }
                rejected_use_cases_str = json.dumps(
                    self._safe_serialize(rejected_use_cases),
                    ensure_ascii=False,
                    indent=2
                )
                
                user_prompt = USE_CASE_REGENERATION_PROMPT.format(
                    previous_use_cases=previous_use_cases_str,
                    rejected_use_cases=rejected_use_cases_str,
                    user_feedback=user_feedback if user_feedback else "Aucun commentaire spécifique",
                    validated_quick_wins_count=validated_quick_wins_count,
                    validated_structuration_ia_count=validated_structuration_ia_count,
                    rejected_quick_wins_count=rejected_qw_count,
                    rejected_structuration_ia_count=rejected_sia_count,
                    validated_needs=validated_needs_str,
                    workshop_data=workshop_str,
                    transcript_data=transcript_str,
                    web_search_data=web_search_str,
                    current_iteration=iteration,
                    max_iterations=3
                )
            
            logger.info("Appel à l'API OpenAI Response avec structured output...")
            
            # Appel à l'API OpenAI Responses avec structured output
            # Utilisation du paramètre 'instructions' pour le system prompt
            response = self.client.responses.parse(
                model=self.model,
                instructions=USE_CASE_ANALYSIS_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                text_format=UseCaseAnalysisResponse
            )
            
            logger.info("Réponse structurée reçue de l'API")
            
            # Tracking des tokens et coûts
            if self.tracker:
                operation = f"analyze_use_cases_iteration_{iteration}"
                self.tracker.track_response(
                    response,
                    agent_name="use_case_analysis",
                    operation=operation,
                    model=self.model
                )
            
            # Extraction de la réponse structurée
            parsed_response = response.output_parsed
            
            # Conversion en dictionnaire pour compatibilité avec le reste du code
            result = {
                "quick_wins": [qw.model_dump() for qw in parsed_response.quick_wins],
                "structuration_ia": [sia.model_dump() for sia in parsed_response.structuration_ia],
                "summary": parsed_response.summary.model_dump()
            }
            
            logger.info(f"Cas d'usage générés : {len(result['quick_wins'])} Quick Wins, "
                       f"{len(result['structuration_ia'])} Structuration IA")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des cas d'usage : {str(e)}", exc_info=True)
            return {
                "error": f"Erreur lors de l'analyse des cas d'usage: {str(e)}",
                "quick_wins": [],
                "structuration_ia": [],
                "summary": {
                    "total_quick_wins": 0,
                    "total_structuration_ia": 0,
                    "total_use_cases": 0,
                    "main_themes": []
                }
            }
    
    def _safe_serialize(self, obj):
        """
        Convertit les objets Pydantic en dictionnaires pour la sérialisation JSON.
        
        Args:
            obj: Objet à sérialiser
            
        Returns:
            Objet sérialisable
        """
        if hasattr(obj, 'model_dump'):
            return obj.model_dump()
        elif hasattr(obj, 'dict'):
            return obj.dict()
        elif isinstance(obj, dict):
            return {k: self._safe_serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._safe_serialize(item) for item in obj]
        else:
            return obj
    
    def check_validation_success(
        self, 
        validated_quick_wins_count: int, 
        validated_structuration_ia_count: int
    ) -> bool:
        """
        Vérifie si la validation est un succès.
        Succès = au moins 5 Quick Wins validés ET au moins 5 Structuration IA validés.
        
        Args:
            validated_quick_wins_count: Nombre de Quick Wins validés
            validated_structuration_ia_count: Nombre de Structuration IA validés
            
        Returns:
            True si succès, False sinon
        """
        success = (
            validated_quick_wins_count >= 5 and 
            validated_structuration_ia_count >= 5
        )
        
        logger.info(f"Vérification du succès de validation : "
                   f"Quick Wins={validated_quick_wins_count}/5, "
                   f"Structuration IA={validated_structuration_ia_count}/5, "
                   f"Succès={success}")
        
        return success

