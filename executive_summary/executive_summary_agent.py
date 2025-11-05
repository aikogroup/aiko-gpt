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
    RecommendationsResponse
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
        rejected_challenges: Optional[List[Dict[str, Any]]] = None,
        validated_challenges: Optional[List[Dict[str, Any]]] = None,
        challenges_feedback: str = ""
    ) -> Dict[str, Any]:
        """
        Identifie 5 enjeux stratégiques de l'IA.
        
        Args:
            transcript_content: Contenu des transcripts formaté
            workshop_content: Contenu des ateliers formaté
            final_needs: Liste des besoins identifiés
            rejected_challenges: Enjeux précédemment rejetés (pour régénération)
            validated_challenges: Enjeux validés à conserver (pour régénération)
            challenges_feedback: Feedback utilisateur (pour régénération)
            
        Returns:
            Dict avec 'challenges' (liste de 5 enjeux)
        """
        print(f"final_needs dans identify_challenges : {final_needs}")
        try:
            # Formater les besoins pour le prompt
            needs_str = self._format_needs(final_needs)
            
            # Choisir le prompt selon le contexte (régénération ou première génération)
            if rejected_challenges and challenges_feedback:
                # Mode régénération
                rejected_str = self._format_challenges(rejected_challenges)
                validated_str = self._format_challenges(validated_challenges) if validated_challenges else "Aucun"
                
                prompt = REGENERATE_CHALLENGES_PROMPT.format(
                    rejected_challenges=rejected_str,
                    challenges_feedback=challenges_feedback,
                    validated_challenges=validated_str,
                    transcript_content=transcript_content,
                    workshop_content=workshop_content,
                    final_needs=needs_str
                )
            else:
                # Mode première génération
                prompt = IDENTIFY_CHALLENGES_PROMPT.format(
                    transcript_content=transcript_content,
                    workshop_content=workshop_content,
                    final_needs=needs_str
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
                text_format=ChallengesResponse
            )
            
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
            
            logger.info(f"✅ {len(challenges_dict)} enjeux identifiés")
            return {"challenges": challenges_dict}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'identification des enjeux: {e}", exc_info=True)
            return {"challenges": []}
    
    def evaluate_maturity(
        self,
        transcript_content: str,
        workshop_content: str,
        final_needs: List[Dict[str, Any]],
        final_quick_wins: List[Dict[str, Any]],
        final_structuration_ia: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Évalue la maturité IA de l'entreprise (1-5).
        
        Args:
            transcript_content: Contenu des transcripts formaté
            workshop_content: Contenu des ateliers formaté
            final_needs: Besoins identifiés
            final_quick_wins: Quick Wins proposés
            final_structuration_ia: Structuration IA proposée
            
        Returns:
            Dict avec 'echelle' (int 1-5) et 'phrase_resumant' (str)
        """
        try:
            # Formater les données pour le prompt
            needs_str = self._format_needs(final_needs)
            quick_wins_str = self._format_use_cases(final_quick_wins)
            structuration_str = self._format_use_cases(final_structuration_ia)
            
            prompt = EVALUATE_MATURITY_PROMPT.format(
                transcript_content=transcript_content,
                workshop_content=workshop_content,
                final_needs=needs_str,
                final_quick_wins=quick_wins_str,
                final_structuration_ia=structuration_str
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
        final_quick_wins: List[Dict[str, Any]],
        final_structuration_ia: List[Dict[str, Any]],
        rejected_recommendations: Optional[List[str]] = None,
        validated_recommendations: Optional[List[str]] = None,
        recommendations_feedback: str = ""
    ) -> Dict[str, Any]:
        """
        Génère 4 recommandations personnalisées.
        
        Args:
            maturite_ia: Dict avec 'echelle' et 'phrase_resumant'
            final_needs: Besoins identifiés
            final_quick_wins: Quick Wins proposés
            final_structuration_ia: Structuration IA proposée
            rejected_recommendations: Recommandations précédemment rejetées (pour régénération)
            validated_recommendations: Recommandations validées à conserver (pour régénération)
            recommendations_feedback: Feedback utilisateur (pour régénération)
            
        Returns:
            Dict avec 'recommendations' (liste de 4 recommandations)
        """
        try:
            # Formater les données pour le prompt
            maturite_str = f"Échelle: {maturite_ia.get('echelle', 3)}/5\n{maturite_ia.get('phrase_resumant', '')}"
            needs_str = self._format_needs(final_needs)
            quick_wins_str = self._format_use_cases(final_quick_wins)
            structuration_str = self._format_use_cases(final_structuration_ia)
            
            # Choisir le prompt selon le contexte (régénération ou première génération)
            if rejected_recommendations and recommendations_feedback:
                # Mode régénération
                rejected_str = "\n".join([f"- {r}" for r in rejected_recommendations])
                validated_str = "\n".join([f"- {r}" for r in validated_recommendations]) if validated_recommendations else "Aucune"
                
                prompt = REGENERATE_RECOMMENDATIONS_PROMPT.format(
                    rejected_recommendations=rejected_str,
                    recommendations_feedback=recommendations_feedback,
                    validated_recommendations=validated_str,
                    maturite_ia=maturite_str,
                    final_needs=needs_str,
                    final_quick_wins=quick_wins_str,
                    final_structuration_ia=structuration_str
                )
            else:
                # Mode première génération
                prompt = GENERATE_RECOMMENDATIONS_PROMPT.format(
                    maturite_ia=maturite_str,
                    final_needs=needs_str,
                    final_quick_wins=quick_wins_str,
                    final_structuration_ia=structuration_str
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
            recommendations = parsed_response.get("recommendations", [])
            
            logger.info(f"✅ {len(recommendations)} recommandations générées")
            return {"recommendations": recommendations}
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des recommandations: {e}", exc_info=True)
            return {"recommendations": []}
    
    def _format_needs(self, needs: List[Dict[str, Any]]) -> str:
        """Formate les besoins pour le prompt"""
        if not needs:
            return "Aucun besoin identifié"
        
        formatted = []
        for i, need in enumerate(needs, 1):
            theme = need.get("titre", f"Besoins {i}")
            quotes = need.get("quotes", [])
            quotes_str = "\n  - ".join(quotes) if quotes else "Aucune citation"
            formatted.append(f"{i}. {theme}:\n  - {quotes_str}")
        
        return "\n\n".join(formatted)
    
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

