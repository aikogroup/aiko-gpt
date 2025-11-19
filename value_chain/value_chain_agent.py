"""
Agent pour extraire la chaîne de valeur de l'entreprise
"""
import logging
from typing import List, Dict, Any
import openai
import os
from dotenv import load_dotenv

from models.value_chain_models import (
    TeamsResponse,
    ActivitiesResponse,
    FrictionPointsResponse,
    Team,
    Activity,
    FrictionPoint
)
from prompts.value_chain_prompts import (
    VALUE_CHAIN_TEAMS_SYSTEM_PROMPT,
    VALUE_CHAIN_TEAMS_PROMPT,
    VALUE_CHAIN_ACTIVITIES_SYSTEM_PROMPT,
    VALUE_CHAIN_ACTIVITIES_PROMPT,
    VALUE_CHAIN_FRICTION_POINTS_SYSTEM_PROMPT,
    VALUE_CHAIN_FRICTION_POINTS_PROMPT
)

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)


class ValueChainAgent:
    """Agent pour extraire la chaîne de valeur depuis les transcriptions et web search"""
    
    def __init__(self, api_key: str = None):
        """Initialise l'agent avec la clé API OpenAI"""
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
    
    def extract_teams(
        self,
        interventions: List[Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> TeamsResponse:
        """
        Extrait les équipes (métier et support) depuis les interventions
        
        Args:
            interventions: Liste des interventions enrichies depuis la DB
            company_info: Informations sur l'entreprise depuis web search (pour contexte uniquement)
            
        Returns:
            TeamsResponse avec les équipes identifiées
        """
        if not interventions:
            logger.warning("Aucune intervention fournie")
            return TeamsResponse(teams=[])
        
        # Préparer le texte pour l'analyse
        transcript_text = self._format_interventions(interventions)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM pour extraire les équipes
        prompt = VALUE_CHAIN_TEAMS_PROMPT.format(
            transcript_text=transcript_text,
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=VALUE_CHAIN_TEAMS_SYSTEM_PROMPT,
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
                text_format=TeamsResponse
            )
            
            teams_response = response.output_parsed
            logger.info(f"Extrait {len(teams_response.teams)} équipes")
            return teams_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des équipes: {e}")
            return TeamsResponse(teams=[])
    
    def extract_activities(
        self,
        interventions: List[Dict[str, Any]],
        teams: List[Team]
    ) -> ActivitiesResponse:
        """
        Extrait les activités pour chaque équipe validée
        
        Args:
            interventions: Liste des interventions enrichies depuis la DB
            teams: Liste des équipes validées
            
        Returns:
            ActivitiesResponse avec une phrase résumé par équipe
        """
        if not interventions or not teams:
            logger.warning("Aucune intervention ou équipe fournie")
            return ActivitiesResponse(activities=[])
        
        # Préparer le texte pour l'analyse
        transcript_text = self._format_interventions(interventions)
        teams_text = self._format_teams(teams)
        
        # Appeler le LLM pour extraire les activités
        prompt = VALUE_CHAIN_ACTIVITIES_PROMPT.format(
            transcript_text=transcript_text,
            teams=teams_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=VALUE_CHAIN_ACTIVITIES_SYSTEM_PROMPT,
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
                text_format=ActivitiesResponse
            )
            
            activities_response = response.output_parsed
            logger.info(f"Extrait {len(activities_response.activities)} activités")
            return activities_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des activités: {e}")
            return ActivitiesResponse(activities=[])
    
    def extract_friction_points(
        self,
        interventions: List[Dict[str, Any]],
        teams: List[Team]
    ) -> FrictionPointsResponse:
        """
        Extrait les points de friction liés à la gestion des données pour chaque équipe
        
        Args:
            interventions: Liste des interventions enrichies depuis la DB
            teams: Liste des équipes validées
            
        Returns:
            FrictionPointsResponse avec les points de friction identifiés
        """
        if not interventions or not teams:
            logger.warning("Aucune intervention ou équipe fournie")
            return FrictionPointsResponse(friction_points=[])
        
        # Préparer le texte pour l'analyse
        transcript_text = self._format_interventions(interventions)
        teams_text = self._format_teams(teams)
        
        # Appeler le LLM pour extraire les points de friction
        prompt = VALUE_CHAIN_FRICTION_POINTS_PROMPT.format(
            transcript_text=transcript_text,
            teams=teams_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=VALUE_CHAIN_FRICTION_POINTS_SYSTEM_PROMPT,
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
                text_format=FrictionPointsResponse
            )
            
            friction_points_response = response.output_parsed
            logger.info(f"Extrait {len(friction_points_response.friction_points)} points de friction")
            return friction_points_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des points de friction: {e}")
            return FrictionPointsResponse(friction_points=[])
    
    def _format_interventions(self, interventions: List[Dict[str, Any]]) -> str:
        """Formate les interventions pour l'analyse LLM avec métadonnées enrichies"""
        formatted = []
        
        for intervention in interventions:
            text = intervention.get("text", "")
            speaker_level = intervention.get("speaker_level", "")
            speaker_role = intervention.get("speaker_role", "")
            
            # Construire un préfixe informatif avec role et level
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
        
        # Chiffre d'affaires
        if "chiffre_affaires" in company_info:
            formatted.append(f"**Chiffre d'affaires**: {company_info['chiffre_affaires']}")
        
        # Nombre d'employés
        if "nombre_employes" in company_info:
            formatted.append(f"**Nombre d'employés**: {company_info['nombre_employes']}")
        
        return "\n".join(formatted) if formatted else "Aucune information disponible."
    
    def _format_teams(self, teams: List[Team]) -> str:
        """Formate les équipes pour l'analyse"""
        if not teams:
            return "Aucune équipe disponible."
        
        formatted = []
        for team in teams:
            formatted.append(
                f"- **ID: {team.id}** - **{team.nom}** ({team.type}): {team.description}"
            )
        
        return "\n".join(formatted)

