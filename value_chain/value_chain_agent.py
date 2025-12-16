"""
Agent pour extraire la chaîne de valeur de l'entreprise
"""
import logging
from typing import List, Dict, Any
import openai
import os
from dotenv import load_dotenv

from models.value_chain_models import (
    FunctionsResponse,
    MissionsResponse,
    FrictionPointsResponse,
    Function,
    Mission,
    FrictionPoint
)
from prompts.value_chain_prompts import (
    VALUE_CHAIN_TEAMS_SYSTEM_PROMPT,
    VALUE_CHAIN_TEAMS_PROMPT,
    VALUE_CHAIN_MISSIONS_SYSTEM_PROMPT,
    VALUE_CHAIN_MISSIONS_PROMPT,
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
        
        self.model = 'gpt-4.1-nano-2025-04-14'
    
    def extract_functions(
        self,
        interventions: List[Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> FunctionsResponse:
        """
        Extrait les fonctions (métier et support) depuis les interventions
        
        Args:
            interventions: Liste des interventions enrichies depuis la DB
            company_info: Informations sur l'entreprise depuis web search (pour contexte uniquement)
            
        Returns:
            FunctionsResponse avec les fonctions identifiées
        """
        if not interventions:
            logger.warning("Aucune intervention fournie")
            return FunctionsResponse(functions=[])
        
        # Préparer le texte pour l'analyse
        transcript_text = self._format_interventions(interventions)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM pour extraire les fonctions
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
                text_format=FunctionsResponse
            )
            
            functions_response = response.output_parsed
            logger.info(f"Extrait {len(functions_response.functions)} fonctions")
            return functions_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des fonctions: {e}")
            return FunctionsResponse(functions=[])
    
    def extract_missions(
        self,
        interventions: List[Dict[str, Any]],
        functions: List[Function]
    ) -> MissionsResponse:
        """
        Extrait les missions pour chaque fonction validée
        
        Args:
            interventions: Liste des interventions enrichies depuis la DB
            functions: Liste des fonctions validées
            
        Returns:
            MissionsResponse avec une phrase résumé par fonction
        """
        if not interventions or not functions:
            logger.warning("Aucune intervention ou fonction fournie")
            return MissionsResponse(missions=[])
        
        # Préparer le texte pour l'analyse
        transcript_text = self._format_interventions(interventions)
        functions_text = self._format_functions(functions)
        
        # Appeler le LLM pour extraire les missions
        prompt = VALUE_CHAIN_MISSIONS_PROMPT.format(
            transcript_text=transcript_text,
            functions=functions_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=VALUE_CHAIN_MISSIONS_SYSTEM_PROMPT,
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
                text_format=MissionsResponse
            )
            
            missions_response = response.output_parsed
            logger.info(f"Extrait {len(missions_response.missions)} missions")
            return missions_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des missions: {e}")
            return MissionsResponse(missions=[])
    
    def extract_friction_points(
        self,
        interventions: List[Dict[str, Any]],
        functions: List[Function]
    ) -> FrictionPointsResponse:
        """
        Extrait les points de friction liés à la gestion des données pour chaque fonction
        
        Args:
            interventions: Liste des interventions enrichies depuis la DB
            functions: Liste des fonctions validées
            
        Returns:
            FrictionPointsResponse avec les points de friction identifiés
        """
        if not interventions or not functions:
            logger.warning("Aucune intervention ou fonction fournie")
            return FrictionPointsResponse(friction_points=[])
        
        # LOGS DÉTAILLÉS - Début
        logger.info(f"🔍 [FRICTION] Début extraction points de friction")
        logger.info(f"🔍 [FRICTION] Nombre d'interventions: {len(interventions)}")
        logger.info(f"🔍 [FRICTION] Nombre de fonctions validées: {len(functions)}")
        
        # Afficher les noms des fonctions
        function_names = [function.nom for function in functions]
        logger.info(f"🔍 [FRICTION] Noms des fonctions validées: {function_names}")
        
        # Statistiques sur les interventions
        if interventions:
            interventions_with_role = sum(1 for i in interventions if i.get("speaker_role"))
            interventions_with_level = sum(1 for i in interventions if i.get("speaker_level"))
            logger.info(f"🔍 [FRICTION] Interventions avec rôle: {interventions_with_role}/{len(interventions)}")
            logger.info(f"🔍 [FRICTION] Interventions avec niveau: {interventions_with_level}/{len(interventions)}")
            
            # Aperçu des premières interventions
            logger.info(f"🔍 [FRICTION] Aperçu des 3 premières interventions:")
            for i, interv in enumerate(interventions[:3], 1):
                text_preview = interv.get("text", "")[:100] + "..." if len(interv.get("text", "")) > 100 else interv.get("text", "")
                role = interv.get("speaker_role", "N/A")
                level = interv.get("speaker_level", "N/A")
                logger.info(f"   {i}. [niveau={level}|rôle={role}] {text_preview}")
        
        # Préparer le texte pour l'analyse
        transcript_text = self._format_interventions(interventions)
        functions_text = self._format_functions(functions)
        
        # Logs sur les données formatées
        logger.info(f"🔍 [FRICTION] Longueur transcript_text formaté: {len(transcript_text)} caractères")
        logger.info(f"🔍 [FRICTION] Aperçu transcript_text (premiers 500 caractères): {transcript_text[:500]}...")
        logger.info(f"🔍 [FRICTION] Functions_text formaté:\n{functions_text}")
        
        # Appeler le LLM pour extraire les points de friction
        prompt = VALUE_CHAIN_FRICTION_POINTS_PROMPT.format(
            transcript_text=transcript_text,
            functions=functions_text
        )
        
        logger.info(f"🔍 [FRICTION] Longueur prompt final: {len(prompt)} caractères")
        logger.info(f"🔍 [FRICTION] Modèle utilisé: {self.model}")
        # LOGS DÉTAILLÉS - Fin
        
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
            
            # Log détaillé des points de friction extraits
            if friction_points_response.friction_points:
                logger.info(f"🔍 [FRICTION] Détail des points de friction extraits:")
                for fp in friction_points_response.friction_points:
                    logger.info(f"   - ID: {fp.id}, Function: {fp.function_nom}, Citation: {fp.citation[:100]}...")
            else:
                logger.warning(f"🔍 [FRICTION] ⚠️ Aucun point de friction extrait par le LLM")
            
            return friction_points_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des points de friction: {e}")
            logger.error(f"🔍 [FRICTION] ❌ Exception détaillée: {type(e).__name__}: {str(e)}")
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
    
    def _format_functions(self, functions: List[Function]) -> str:
        """Formate les fonctions pour l'analyse"""
        if not functions:
            return "Aucune fonction disponible."
        
        formatted = []
        for function in functions:
            formatted.append(
                f"- **ID: {function.id}** - **{function.nom}** ({function.type}): {function.description}"
            )
        
        return "\n".join(formatted)

