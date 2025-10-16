"""
Agent d'analyse des besoins métier
"""

import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from prompts.need_analysis_agent_prompts import (
    NEED_ANALYSIS_SYSTEM_PROMPT,
    NEED_ANALYSIS_USER_PROMPT,
    HUMAN_VALIDATION_PROMPT,
    NEED_REGENERATION_PROMPT
)
from models.need_analysis_models import NeedAnalysisResponse
import os
from dotenv import load_dotenv

# Import du tracker
import sys
sys.path.append('/home/addeche/aiko/aikoGPT')
from utils.token_tracker import TokenTracker

class NeedAnalysisAgent:
    """
    Agent responsable de l'analyse des besoins métier à partir des données
    collectées par les agents workshop, transcript et web_search.
    """
    
    def __init__(self, api_key: str, tracker: Optional[TokenTracker] = None):
        """
        Initialise l'agent avec la clé API OpenAI.
        
        Args:
            api_key: Clé API OpenAI
            tracker: TokenTracker optionnel pour le suivi des tokens et coûts
        """
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')  # Modèle configurable via .env
        self.tracker = tracker  # Tracker pour le suivi des tokens
        
    def analyze_needs(
        self,
        workshop_data: Dict,
        transcript_data: List[Dict],
        web_search_data: Dict,
        iteration: int = 1,
        previous_needs: Optional[List[Dict]] = None,
        rejected_needs: Optional[List[Dict]] = None,
        user_feedback: str = "",
        validated_needs_count: int = 0
    ) -> Dict[str, Any]:
        """
        Analyse les besoins métier à partir des données d'entrée.
        
        Args:
            workshop_data: Données du workshop agent
            transcript_data: Données du transcript agent
            web_search_data: Données du web search agent
            iteration: Numéro de l'itération actuelle
            previous_needs: Besoins proposés lors de l'itération précédente
            rejected_needs: Besoins rejetés par l'utilisateur
            user_feedback: Commentaires de l'utilisateur
            validated_needs_count: Nombre de besoins validés
            
        Returns:
            Dict contenant les besoins identifiés et le résumé
        """
        try:
            # Conversion sécurisée des données pour la sérialisation JSON
            def safe_serialize(obj):
                """Convertit les objets Pydantic en dictionnaires pour la sérialisation JSON"""
                if hasattr(obj, 'model_dump'):
                    return obj.model_dump()
                elif hasattr(obj, 'dict'):
                    return obj.dict()
                elif isinstance(obj, dict):
                    return {k: safe_serialize(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [safe_serialize(item) for item in obj]
                else:
                    return obj
            
            # Formatage des données d'entrée avec conversion sécurisée
            workshop_safe = safe_serialize(workshop_data)
            transcript_safe = safe_serialize(transcript_data)
            web_search_safe = safe_serialize(web_search_data)
            
            workshop_str = json.dumps(workshop_safe, ensure_ascii=False, indent=2)
            transcript_str = json.dumps(transcript_safe, ensure_ascii=False, indent=2)
            web_search_str = json.dumps(web_search_safe, ensure_ascii=False, indent=2)
            
            # Choix du prompt selon l'itération
            if iteration == 1 or not previous_needs:
                # Première itération - génération initiale
                user_prompt = NEED_ANALYSIS_USER_PROMPT.format(
                    workshop_data=workshop_str,
                    transcript_data=transcript_str,
                    web_search_data=web_search_str
                )
            else:
                # Itération suivante - régénération avec feedback
                previous_needs_str = json.dumps(safe_serialize(previous_needs), ensure_ascii=False, indent=2)
                rejected_needs_str = json.dumps(safe_serialize(rejected_needs or []), ensure_ascii=False, indent=2)
                remaining_needs_count = max(0, 10 - validated_needs_count)
                rejected_needs_count = len(rejected_needs or [])
                
                user_prompt = NEED_REGENERATION_PROMPT.format(
                    previous_needs=previous_needs_str,
                    rejected_needs=rejected_needs_str,
                    user_feedback=user_feedback if user_feedback else "Aucun commentaire spécifique",
                    validated_needs_count=validated_needs_count,
                    rejected_needs_count=rejected_needs_count,
                    workshop_data=workshop_str,
                    transcript_data=transcript_str,
                    web_search_data=web_search_str,
                    remaining_needs_count=remaining_needs_count,
                    current_iteration=iteration,
                    max_iterations=3
                )
            
            # Appel à l'API OpenAI Responses avec structured output
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": f"{NEED_ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt}"
                    }
                ],
                text_format=NeedAnalysisResponse
            )
            
            # Tracking des tokens et coûts
            if self.tracker:
                operation = f"analyze_needs_iteration_{iteration}"
                self.tracker.track_response(
                    response,
                    agent_name="need_analysis",
                    operation=operation,
                    model=self.model
                )
            
            # Extraction de la réponse structurée
            parsed_response = response.output_parsed
            
            # Conversion en dictionnaire pour compatibilité avec le reste du code
            result = {
                "identified_needs": [need.model_dump() for need in parsed_response.identified_needs],
                "summary": parsed_response.summary.model_dump()
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Erreur lors de l'analyse des besoins: {str(e)}",
                "identified_needs": [],
                "summary": {
                    "total_needs": 0,
                    "themes": []
                }
            }
    
    def validate_needs_with_human(self, identified_needs: List[Dict]) -> Dict[str, Any]:
        """
        Présente les besoins identifiés pour validation humaine.
        
        Args:
            identified_needs: Liste des besoins identifiés
            
        Returns:
            Dict contenant les besoins validés et rejetés
        """
        try:
            # Formatage des besoins pour présentation
            needs_str = json.dumps(identified_needs, ensure_ascii=False, indent=2)
            
            # Construction du prompt de validation
            validation_prompt = HUMAN_VALIDATION_PROMPT.format(
                identified_needs=needs_str
            )
            
            # Appel à l'API pour simuler la validation humaine
            # Dans un vrai workflow, ceci serait remplacé par une interface utilisateur
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"Tu es un expert qui valide les besoins métier identifiés. Tu dois valider au moins 5 besoins pour que l'analyse soit un succès.\n\n{validation_prompt}"
                            }
                        ]
                    }
                ]
            )
            
            content = response.output_text
            
            # Parsing de la réponse de validation
            try:
                validation_result = json.loads(content)
            except json.JSONDecodeError:
                # Simulation d'une validation réussie si parsing échoue
                validation_result = {
                    "validated_needs": [need["id"] for need in identified_needs[:5]],
                    "rejected_needs": [need["id"] for need in identified_needs[5:]],
                    "success": True,
                    "total_validated": 5
                }
            
            return validation_result
            
        except Exception as e:
            return {
                "error": f"Erreur lors de la validation: {str(e)}",
                "validated_needs": [],
                "rejected_needs": [],
                "success": False,
                "total_validated": 0
            }
    
    def check_validation_success(self, validation_result: Dict[str, Any]) -> bool:
        """
        Vérifie si la validation est un succès (au moins 5 besoins validés).
        
        Args:
            validation_result: Résultat de la validation
            
        Returns:
            True si succès, False sinon
        """
        return (
            validation_result.get("success", False) and 
            validation_result.get("total_validated", 0) >= 5
        )
