"""
Agent principal pour l'Executive Summary : identification des enjeux, évaluation de maturité, recommandations
"""

import logging
from typing import Dict, List, Any, Optional
from openai import OpenAI
import os
from dotenv import load_dotenv
from models.executive_summary_models import (
    ChallengesResponse,
    MaturityResponse,
    RecommendationsResponse,
    Recommendation
)
from prompts.executive_summary_prompts import (
    EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
    IDENTIFY_CHALLENGES_PROMPT,
    REGENERATE_CHALLENGES_PROMPT,
    EVALUATE_MATURITY_PROMPT,
    GENERATE_RECOMMENDATIONS_PROMPT,
    REGENERATE_RECOMMENDATIONS_PROMPT
)

load_dotenv()

logger = logging.getLogger(__name__)


class ExecutiveSummaryAgent:
    """Agent principal pour l'Executive Summary"""
    
    def __init__(self, api_key: str = None):
        """
        Initialise l'agent.
        
        Args:
            api_key: Clé API OpenAI (optionnel)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY doit être définie")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
    
    def identify_challenges(
        self,
        transcript_content: str,
        workshop_content: str,
        final_needs: List[Dict[str, Any]],
        interviewer_note: str = "",
        rejected_challenges: Optional[List[Dict[str, Any]]] = None,
        validated_challenges: Optional[List[Dict[str, Any]]] = None,
        challenges_feedback: str = ""
    ) -> Dict[str, Any]:
        """
        Identifie des enjeux stratégiques de l'IA.
        
        Args:
            transcript_content: Contenu des transcripts formaté
            workshop_content: Contenu des ateliers formaté
            final_needs: Liste des besoins identifiés
            interviewer_note: Note de l'interviewer avec contexte et insights
            rejected_challenges: Enjeux précédemment rejetés (pour régénération)
            validated_challenges: Enjeux validés à conserver (pour régénération)
            challenges_feedback: Feedback utilisateur (pour régénération)
            
        Returns:
            Dict avec 'challenges' (liste d'enjeux)
        """
        import time
        api_start_time = time.time()
        print(f"final_needs dans identify_challenges : {final_needs}")
        try:
            # Formater les besoins pour le prompt
            format_start = time.time()
            needs_str = self._format_needs(final_needs)
            format_end = time.time()
            
            # Choisir le prompt selon le contexte (régénération ou première génération)
            # Si on a des enjeux validés ou rejetés, c'est une régénération
            prompt_start = time.time()
            if validated_challenges or rejected_challenges:
                # Mode régénération - passer TOUS les enjeux précédents
                all_previous = []
                if validated_challenges:
                    all_previous.extend(validated_challenges)
                if rejected_challenges:
                    all_previous.extend(rejected_challenges)
                
                previous_str = self._format_challenges(all_previous) if all_previous else "Aucun"
                rejected_str = self._format_challenges(rejected_challenges) if rejected_challenges else "Aucun"
                validated_str = self._format_challenges(validated_challenges) if validated_challenges else "Aucun"
                
                # Calculer les valeurs pour le prompt
                validated_count = len(validated_challenges) if validated_challenges else 0
                rejected_count = len(rejected_challenges) if rejected_challenges else 0
                
                prompt = REGENERATE_CHALLENGES_PROMPT.format(
                    previous_challenges=previous_str,
                    rejected_challenges=rejected_str,
                    challenges_feedback=challenges_feedback or "Aucun commentaire",
                    validated_challenges=validated_str,
                    validated_count=validated_count,
                    rejected_count=rejected_count,
                    interviewer_note=interviewer_note or "Aucune note de l'interviewer",
                    transcript_content=transcript_content,
                    workshop_content=workshop_content,
                    final_needs=needs_str
                )
            else:
                # Mode première génération
                prompt = IDENTIFY_CHALLENGES_PROMPT.format(
                    interviewer_note=interviewer_note or "Aucune note de l'interviewer",
                    transcript_content=transcript_content,
                    workshop_content=workshop_content,
                    final_needs=needs_str
                )
            
            prompt_end = time.time()
            format_duration = format_end - format_start
            prompt_duration = prompt_end - prompt_start
            print(f"⏱️ [TIMING] Formatage besoins: {format_duration:.3f}s")
            print(f"⏱️ [TIMING] Construction prompt: {prompt_duration:.3f}s")
            
            # Appel à l'API avec structured output
            api_call_start = time.time()
            
            response = self.client.responses.parse(
                model=self.model,
                instructions=EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                text_format=ChallengesResponse
            )
            
            api_call_end = time.time()
            api_duration = api_call_end - api_call_start
            print(f"⏱️ [TIMING] Appel API OpenAI: {api_duration:.3f}s")
            
            parsed_response = response.output_parsed.model_dump()
            challenges = parsed_response.get("challenges", [])
            
            # Convertir en format dict
            challenges_dict = []
            for challenge in challenges:
                challenges_dict.append({
                    "id": challenge.get("id", ""),
                    "titre": challenge.get("titre", ""),
                    "description": challenge.get("description", ""),
                    "besoins_lies": challenge.get("besoins_lies", [])
                })
            
            total_duration = time.time() - api_start_time
            logger.info(f"✅ {len(challenges_dict)} enjeux identifiés")
            print(f"⏱️ [TIMING] identify_challenges (total): {total_duration:.3f}s")
            return {"challenges": challenges_dict}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'identification des enjeux: {e}", exc_info=True)
            return {"challenges": []}
    
    def evaluate_maturity(
        self,
        transcript_content: str,
        workshop_content: str,
        final_needs: List[Dict[str, Any]],
        final_use_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Évalue la maturité IA de l'entreprise (1-5).
        
        Args:
            transcript_content: Contenu des transcripts formaté
            workshop_content: Contenu des ateliers formaté
            final_needs: Besoins identifiés
            final_use_cases: Cas d'usage proposés
            
        Returns:
            Dict avec 'echelle' (int 1-5) et 'phrase_resumant' (str)
        """
        try:
            # Formater les données pour le prompt
            needs_str = self._format_needs(final_needs)
            use_cases_str = self._format_use_cases(final_use_cases)
            
            prompt = EVALUATE_MATURITY_PROMPT.format(
                transcript_content=transcript_content,
                workshop_content=workshop_content,
                final_needs=needs_str,
                final_use_cases=use_cases_str
            )
            
            # Appel à l'API avec structured output
            response = self.client.responses.parse(
                model=self.model,
                instructions=EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                text_format=MaturityResponse
            )
            
            parsed_response = response.output_parsed.model_dump()
            
            result = {
                "echelle": parsed_response.get("echelle", 3),
                "phrase_resumant": parsed_response.get("phrase_resumant", "")
            }
            
            logger.info(f"✅ Maturité IA évaluée: {result['echelle']}/5")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de maturité: {e}", exc_info=True)
            return {
                "echelle": 3,
                "phrase_resumant": "Évaluation de maturité non disponible"
            }
    
    def generate_recommendations(
        self,
        maturite_ia: Dict[str, Any],
        final_needs: List[Dict[str, Any]],
        final_use_cases: List[Dict[str, Any]],
        rejected_recommendations: Optional[List[str]] = None,
        validated_recommendations: Optional[List[str]] = None,
        recommendations_feedback: str = ""
    ) -> Dict[str, Any]:
        """
        Génère des recommandations personnalisées.
        
        Args:
            maturite_ia: Dict avec 'echelle' et 'phrase_resumant'
            final_needs: Besoins identifiés
            final_use_cases: Cas d'usage proposés
            rejected_recommendations: Recommandations précédemment rejetées (pour régénération)
            validated_recommendations: Recommandations validées à conserver (pour régénération)
            recommendations_feedback: Feedback utilisateur (pour première génération et régénération)
            
        Returns:
            Dict avec 'recommendations' (liste de recommandations)
        """
        try:
            # Formater les données pour le prompt
            maturite_str = f"Échelle: {maturite_ia.get('echelle', 3)}/5\n{maturite_ia.get('phrase_resumant', '')}"
            needs_str = self._format_needs(final_needs)
            use_cases_str = self._format_use_cases(final_use_cases)
            
            # Choisir le prompt selon le contexte (régénération ou première génération)
            # Si on a des recommandations validées ou rejetées, c'est une régénération
            if validated_recommendations or rejected_recommendations:
                # Mode régénération - passer TOUTES les recommandations précédentes
                all_previous = []
                if validated_recommendations:
                    all_previous.extend(validated_recommendations)
                if rejected_recommendations:
                    all_previous.extend(rejected_recommendations)
                
                previous_str = "\n".join([f"- {r}" for r in all_previous]) if all_previous else "Aucune"
                rejected_str = "\n".join([f"- {r}" for r in rejected_recommendations]) if rejected_recommendations else "Aucune"
                validated_str = "\n".join([f"- {r}" for r in validated_recommendations]) if validated_recommendations else "Aucune"
                
                # Calculer les valeurs pour le prompt
                validated_count = len(validated_recommendations) if validated_recommendations else 0
                rejected_count = len(rejected_recommendations) if rejected_recommendations else 0
                
                prompt = REGENERATE_RECOMMENDATIONS_PROMPT.format(
                    previous_recommendations=previous_str,
                    rejected_recommendations=rejected_str,
                    recommendations_feedback=recommendations_feedback or "Aucun commentaire",
                    validated_recommendations=validated_str,
                    validated_count=validated_count,
                    rejected_count=rejected_count,
                    maturite_ia=maturite_str,
                    final_needs=needs_str,
                    final_use_cases=use_cases_str
                )
            else:
                # Mode première génération
                # Utiliser recommendations_feedback si disponible, sinon message par défaut
                feedback_str = recommendations_feedback.strip() if recommendations_feedback else "Aucun commentaire spécifique. Génère des recommandations adaptées à la maturité IA et aux besoins identifiés."
                
                prompt = GENERATE_RECOMMENDATIONS_PROMPT.format(
                    maturite_ia=maturite_str,
                    final_needs=needs_str,
                    final_use_cases=use_cases_str,
                    recommendations_feedback=feedback_str
                )
            
            # Appel à l'API avec structured output
            response = self.client.responses.parse(
                model=self.model,
                instructions=EXECUTIVE_SUMMARY_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                text_format=RecommendationsResponse
            )
            
            parsed_response = response.output_parsed.model_dump()
            recommendations_objects = parsed_response.get("recommendations", [])
            
            # Convertir les objets Recommendation en liste de strings (extraire le text)
            recommendations = []
            for rec_obj in recommendations_objects:
                if isinstance(rec_obj, dict):
                    text = rec_obj.get("text", "").strip()
                else:
                    # Si c'est déjà un objet Recommendation
                    text = rec_obj.text.strip() if hasattr(rec_obj, 'text') else str(rec_obj).strip()
                
                if text:
                    recommendations.append(text)
            
            logger.info(f"✅ {len(recommendations)} recommandations générées")
            return {"recommendations": recommendations}
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des recommandations: {e}", exc_info=True)
            return {"recommendations": []}
    
    def _format_needs(self, needs: List[Dict[str, Any]]) -> str:
        """Formate les besoins pour le prompt - ne passe que les titres"""
        if not needs:
            return "Aucun besoin identifié"
        
        formatted = []
        for i, need in enumerate(needs, 1):
            # Utiliser "titre" ou "theme" selon la structure du besoin
            titre = need.get("titre") or need.get("theme", f"Besoins {i}")
            formatted.append(f"{i}. {titre}")
        
        return "\n".join(formatted)
    
    def _format_use_cases(self, use_cases: List[Dict[str, Any]]) -> str:
        """Formate les cas d'usage pour le prompt"""
        if not use_cases:
            return "Aucun cas d'usage identifié"
        
        formatted = []
        for i, uc in enumerate(use_cases, 1):
            titre = uc.get("titre", f"Cas d'usage {i}")
            description = uc.get("description", "")
            formatted.append(f"{i}. {titre}:\n   {description}")
        
        return "\n\n".join(formatted)
    
    def _format_challenges(self, challenges: List[Dict[str, Any]]) -> str:
        """Formate les enjeux pour le prompt"""
        if not challenges:
            return "Aucun enjeu"
        
        formatted = []
        for challenge in challenges:
            id_challenge = challenge.get("id", "")
            titre = challenge.get("titre", "")
            description = challenge.get("description", "")
            formatted.append(f"- {id_challenge}: {titre}\n  {description}")
        
        return "\n".join(formatted)

