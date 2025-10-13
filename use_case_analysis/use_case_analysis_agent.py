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

# Configuration du logger
logger = logging.getLogger(__name__)


class UseCaseAnalysisAgent:
    """
    Agent responsable de l'identification des cas d'usage IA à partir des besoins validés.
    Propose 2 familles de cas d'usage :
    - Quick Wins (8) : automatisation rapide, ROI immédiat
    - Structuration IA (10) : solutions avancées, ROI moyen/long terme
    """
    
    def __init__(self, api_key: str):
        """
        Initialise l'agent avec la clé API OpenAI.
        
        Args:
            api_key: Clé API OpenAI
        """
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-5-nano"
        logger.info(f"UseCaseAnalysisAgent initialisé avec le modèle {self.model}")
        
    def analyze_use_cases(
        self, 
        validated_needs: List[Dict],
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
            
            # Conversion sécurisée des données pour la sérialisation JSON
            validated_needs_safe = self._safe_serialize(validated_needs)
            validated_needs_str = json.dumps(validated_needs_safe, ensure_ascii=False, indent=2)
            
            # Choix du prompt selon l'itération
            if iteration == 1:
                logger.info("Première itération - Génération initiale des cas d'usage")
                user_prompt = USE_CASE_ANALYSIS_USER_PROMPT.format(
                    validated_needs=validated_needs_str
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
                    current_iteration=iteration,
                    max_iterations=3
                )
            
            logger.info("Appel à l'API OpenAI Response...")
            
            # Appel à l'API OpenAI Responses
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"{USE_CASE_ANALYSIS_SYSTEM_PROMPT}\n\n{user_prompt}"
                            }
                        ]
                    }
                ]
            )
            
            # Extraction et parsing de la réponse
            content = response.output_text
            logger.info("Réponse reçue de l'API")
            
            # Nettoyer les caractères de contrôle invalides et trailing commas
            import re
            content_cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
            # Supprimer les virgules avant les accolades/crochets fermants (trailing commas)
            content_cleaned = re.sub(r',\s*([}\]])', r'\1', content_cleaned)
            
            # Tentative de parsing JSON
            try:
                result = json.loads(content_cleaned)
                logger.info("Parsing JSON réussi")
            except json.JSONDecodeError as e:
                logger.warning(f"Erreur de parsing JSON initial : {e}")
                # Si le JSON n'est pas valide, on essaie d'extraire le JSON du contenu
                json_match = re.search(r'\{.*\}', content_cleaned, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group())
                        logger.info("Extraction JSON alternative réussie")
                    except json.JSONDecodeError as e2:
                        logger.error(f"Erreur de parsing JSON alternative : {e2}")
                        logger.error(f"Contenu reçu (premiers 500 caractères) : {content_cleaned[:500]}")
                        raise ValueError(f"Impossible de parser la réponse JSON: {e2}")
                else:
                    logger.error(f"Contenu reçu (premiers 500 caractères) : {content_cleaned[:500]}")
                    raise ValueError("Impossible de parser la réponse JSON")
            
            # Validation de la structure
            if "quick_wins" not in result or "structuration_ia" not in result:
                logger.error("Structure JSON invalide - clés manquantes")
                raise ValueError("Structure JSON invalide : quick_wins ou structuration_ia manquant")
            
            logger.info(f"Cas d'usage générés : {len(result.get('quick_wins', []))} Quick Wins, "
                       f"{len(result.get('structuration_ia', []))} Structuration IA")
            
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

