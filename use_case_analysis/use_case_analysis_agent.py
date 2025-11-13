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
    Génère une liste unifiée de cas d'usage sans distinction de catégorie.
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
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
        self.tracker = tracker  # Tracker pour le suivi des tokens
        logger.info(f"UseCaseAnalysisAgent initialisé avec le modèle {self.model}")
        
    def analyze_use_cases(
        self, 
        validated_needs: List[Dict],
        workshop_data: Dict = None,
        transcript_data: List[Dict] = None,
        web_search_data: Dict = None,
        previous_use_cases: Optional[List[Dict]] = None,
        rejected_use_cases: Optional[List[Dict]] = None,
        user_feedback: str = "",
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """
        Analyse les besoins validés et identifie les cas d'usage IA pertinents.
        
        Args:
            validated_needs: Liste des besoins validés
            workshop_data: Données des workshops (contexte entreprise)
            transcript_data: Données des transcripts (contexte métier)
            web_search_data: Données web search (contexte marché)
            previous_use_cases: Cas d'usage proposés lors de l'itération précédente
            rejected_use_cases: Cas d'usage rejetés par l'utilisateur
            user_feedback: Commentaires de l'utilisateur
            additional_context: Contexte additionnel fourni par l'utilisateur pour guider la génération
            
        Returns:
            Dict contenant les cas d'usage identifiés (use_cases)
        """
        try:
            logger.info(f"Début de l'analyse des cas d'usage")
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
            
            # Choix du prompt selon qu'il y a des cas d'usage précédents
            if previous_use_cases is None or len(previous_use_cases) == 0:
                logger.info("Génération initiale des cas d'usage")
                user_prompt = USE_CASE_ANALYSIS_USER_PROMPT.format(
                    validated_needs=validated_needs_str,
                    workshop_data=workshop_str,
                    transcript_data=transcript_str,
                    web_search_data=web_search_str,
                    additional_context=additional_context if additional_context else "Aucune information supplémentaire fournie."
                )
            else:
                logger.info(f"Régénération avec feedback")
                
                if user_feedback:
                    logger.info(f"Commentaires utilisateur : {user_feedback[:100]}...")
                
                rejected_count = len(rejected_use_cases or [])
                logger.info(f"Cas d'usage rejetés : {rejected_count}")
                
                previous_use_cases_str = json.dumps(
                    self._safe_serialize(previous_use_cases), 
                    ensure_ascii=False, 
                    indent=2
                )
                
                rejected_use_cases_str = json.dumps(
                    self._safe_serialize(rejected_use_cases or []),
                    ensure_ascii=False,
                    indent=2
                )
                
                user_prompt = USE_CASE_REGENERATION_PROMPT.format(
                    previous_use_cases=previous_use_cases_str,
                    rejected_use_cases=rejected_use_cases_str,
                    user_feedback=user_feedback if user_feedback else "Aucun commentaire spécifique",
                    validated_needs=validated_needs_str,
                    workshop_data=workshop_str,
                    transcript_data=transcript_str,
                    web_search_data=web_search_str,
                    additional_context=additional_context if additional_context else "Aucune information supplémentaire fournie."
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
                operation = "analyze_use_cases"
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
                "use_cases": [uc.model_dump() for uc in parsed_response.use_cases],
                "summary": parsed_response.summary.model_dump()
            }
            
            logger.info(f"Cas d'usage générés : {len(result['use_cases'])} cas d'usage")
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des cas d'usage : {str(e)}", exc_info=True)
            return {
                "error": f"Erreur lors de l'analyse des cas d'usage: {str(e)}",
                "use_cases": [],
                "summary": {
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
    

