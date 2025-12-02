"""
Agent pour extraire les atouts de l'entreprise pour l'intégration de l'IA
"""
import logging
from typing import List, Dict, Any
import openai
import os
from dotenv import load_dotenv

from models.atouts_models import CitationsAtoutsResponse, AtoutsResponse
from prompts.atouts_agent_prompts import (
    ATOUTS_CITATIONS_SYSTEM_PROMPT,
    ATOUTS_CITATIONS_PROMPT,
    ATOUTS_SYNTHESIS_SYSTEM_PROMPT,
    ATOUTS_SYNTHESIS_PROMPT,
    ATOUTS_REGENERATION_PROMPT
)

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)


class AtoutsAgent:
    """Agent pour extraire les atouts de l'entreprise depuis les transcriptions et web search"""
    
    def __init__(self, api_key: str = None):
        """Initialise l'agent avec la clé API OpenAI"""
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
    
    def extract_citations_from_transcript(self, interesting_interventions: List[Dict[str, Any]]) -> CitationsAtoutsResponse:
        """
        Extrait les citations révélant les atouts depuis les interventions intéressantes
        
        Args:
            interesting_interventions: Liste des interventions filtrées par interesting_parts_agent
            
        Returns:
            CitationsAtoutsResponse avec les citations d'atouts identifiées
        """
        if not interesting_interventions:
            logger.warning("Aucune intervention intéressante fournie")
            return CitationsAtoutsResponse(citations=[])
        
        # Préparer le texte pour l'analyse
        transcript_text = self._format_interventions(interesting_interventions)
        
        # Appeler le LLM pour extraire les citations
        prompt = ATOUTS_CITATIONS_PROMPT.format(transcript_text=transcript_text)
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=ATOUTS_CITATIONS_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                text_format=CitationsAtoutsResponse
            )
            
            citations_response = response.output_parsed
            logger.info(f"Extrait {len(citations_response.citations)} citations d'atouts")
            return citations_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des citations d'atouts: {e}")
            return CitationsAtoutsResponse(citations=[])
    
    def synthesize_atouts(
        self,
        citations: CitationsAtoutsResponse,
        company_info: Dict[str, Any],
        additional_context: str = ""
    ) -> AtoutsResponse:
        """
        Synthétise les atouts de l'entreprise à partir des citations et des infos web
        
        Args:
            citations: Citations extraites des transcriptions
            company_info: Informations sur l'entreprise depuis web search
            additional_context: Contexte additionnel fourni par l'utilisateur
            
        Returns:
            AtoutsResponse avec les atouts synthétisés
        """
        # Formater les citations
        citations_text = self._format_citations(citations)
        
        # Formater les informations de l'entreprise
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM pour synthétiser
        prompt = ATOUTS_SYNTHESIS_PROMPT.format(
            citations=citations_text,
            company_info=company_info_text
        )
        
        # Ajouter le contexte additionnel si fourni
        if additional_context:
            prompt += f"\n\nContexte additionnel fourni par l'utilisateur :\n{additional_context}"
        
        print(prompt)
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=ATOUTS_SYNTHESIS_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                text_format=AtoutsResponse
            )
            
            atouts_response = response.output_parsed
            logger.info(f"Synthétisé {len(atouts_response.atouts)} atouts")
            return atouts_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse des atouts: {e}")
            return AtoutsResponse(atouts=[])
    
    def regenerate_atouts(
        self,
        citations: CitationsAtoutsResponse,
        company_info: Dict[str, Any],
        validated_atouts: List[Dict[str, Any]],
        rejected_atouts: List[Dict[str, Any]],
        user_feedback: str,
        additional_context: str = ""
    ) -> AtoutsResponse:
        """
        Régénère de nouveaux atouts en évitant les doublons avec ceux déjà validés/rejetés
        
        Args:
            citations: Citations extraites des transcriptions
            company_info: Informations sur l'entreprise
            validated_atouts: Atouts déjà validés par l'utilisateur
            rejected_atouts: Atouts déjà rejetés par l'utilisateur
            user_feedback: Feedback de l'utilisateur
            additional_context: Contexte additionnel
            
        Returns:
            AtoutsResponse avec de nouveaux atouts différents
        """
        # Formater les citations
        citations_text = self._format_citations(citations)
        
        # Formater les informations de l'entreprise
        company_info_text = self._format_company_info(company_info)
        
        # Formater les atouts validés
        validated_text = self._format_atouts_list(validated_atouts) if validated_atouts else "Aucun"
        
        # Formater les atouts rejetés
        rejected_text = self._format_atouts_list(rejected_atouts) if rejected_atouts else "Aucun"
        
        # Appeler le LLM avec le prompt de régénération
        prompt = ATOUTS_REGENERATION_PROMPT.format(
            validated_atouts=validated_text,
            rejected_atouts=rejected_text,
            user_feedback=user_feedback if user_feedback else "Aucun feedback spécifique",
            citations=citations_text,
            company_info=company_info_text
        )
        
        # Ajouter le contexte additionnel si fourni
        if additional_context:
            prompt += f"\n\nContexte additionnel :\n{additional_context}"
        
        print(prompt)
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=ATOUTS_SYNTHESIS_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                text_format=AtoutsResponse
            )
            
            atouts_response = response.output_parsed
            logger.info(f"Régénéré {len(atouts_response.atouts)} nouveaux atouts")
            return atouts_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la régénération des atouts: {e}")
            return AtoutsResponse(atouts=[])
    
    def _format_interventions(self, interventions: List[Dict[str, Any]]) -> str:
        """Formate les interventions pour l'analyse LLM avec métadonnées enrichies (role et level)"""
        formatted = []
        
        for intervention in interventions:
            text = intervention.get("text", "")
            speaker_level = intervention.get("speaker_level", "")
            speaker_role = intervention.get("speaker_role", "")
            
            # Construire un préfixe informatif avec role et level (sans timestamp ni nom)
            metadata_parts = []
            if speaker_level:
                metadata_parts.append(f"niveau={speaker_level}")
            if speaker_role:
                metadata_parts.append(f"rôle={speaker_role}")
            
            if metadata_parts:
                prefix = "[" + "|".join(metadata_parts) + "]"
                formatted.append(f"{prefix} {text}")
            else:
                formatted.append(text)
        
        return "\n\n".join(formatted)
    
    def _format_citations(self, citations: CitationsAtoutsResponse) -> str:
        """Formate les citations pour la synthèse"""
        if not citations.citations:
            return "Aucune citation disponible."
        
        formatted = []
        for i, citation in enumerate(citations.citations, 1):
            formatted.append(
                f"{i}. [{citation.type_atout}]\n"
                f"   Citation: \"{citation.citation}\"\n"
                f"   Contexte: {citation.contexte}"
            )
        
        return "\n\n".join(formatted)
    
    def _format_company_info(self, company_info: Dict[str, Any]) -> str:
        """Formate les informations de l'entreprise"""
        if not company_info:
            return "Aucune information disponible."
        
        formatted = []
        
        # Nom de l'entreprise
        if "nom" in company_info:
            formatted.append(f"**Nom**: {company_info['nom']}")
        
        # Description
        if "description" in company_info:
            formatted.append(f"**Description**: {company_info['description']}")
        
        # Secteur
        if "secteur" in company_info:
            formatted.append(f"**Secteur**: {company_info['secteur']}")
        
        # Taille
        if "taille" in company_info:
            formatted.append(f"**Taille**: {company_info['taille']}")
        
        # Localisation
        if "localisation" in company_info:
            formatted.append(f"**Localisation**: {company_info['localisation']}")
        
        # Site web
        if "site_web" in company_info:
            formatted.append(f"**Site web**: {company_info['site_web']}")
        
        # Informations supplémentaires
        if "informations_supplementaires" in company_info:
            formatted.append(f"**Informations supplémentaires**: {company_info['informations_supplementaires']}")
        
        return "\n".join(formatted)
    
    def _format_atouts_list(self, atouts: List[Dict[str, Any]]) -> str:
        """Formate une liste d'atouts pour affichage"""
        if not atouts:
            return "Aucun"
        
        formatted = []
        for atout in atouts:
            titre = atout.get('titre', 'Titre non défini')
            description = atout.get('description', 'Description non définie')
            formatted.append(f"- **{titre}**: {description}")
        
        return "\n".join(formatted)

