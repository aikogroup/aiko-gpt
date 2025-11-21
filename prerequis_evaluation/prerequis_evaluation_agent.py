"""
Agent pour évaluer les 5 prérequis de transformation IA réussie
"""
import logging
from typing import List, Dict, Any
import openai
import os
from dotenv import load_dotenv

from models.prerequis_evaluation_models import (
    PrerequisEvaluation,
    PrerequisEvaluationResponse,
    PrerequisDocumentEvaluation,
    PrerequisDocumentEvaluationResponse,
    PrerequisGlobalSynthesis
)
from prompts.prerequis_evaluation_prompts import (
    PREREQUIS_EVALUATION_SYSTEM_PROMPT,
    PREREQUIS_1_PROMPT,
    PREREQUIS_2_PROMPT,
    PREREQUIS_3_PROMPT,
    PREREQUIS_4_PROMPT,
    PREREQUIS_5_PROMPT,
    PREREQUIS_SYNTHESIS_SYSTEM_PROMPT,
    PREREQUIS_4_SYNTHESIS_PROMPT,
    PREREQUIS_5_SYNTHESIS_PROMPT,
    PREREQUIS_GLOBAL_SYNTHESIS_PROMPT
)

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)


class PrerequisEvaluationAgent:
    """Agent pour évaluer les 5 prérequis de transformation IA"""
    
    def __init__(self, api_key: str = None):
        """Initialise l'agent avec la clé API OpenAI"""
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
    
    def evaluate_prerequis_1(
        self,
        interventions: List[Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> PrerequisEvaluationResponse:
        """
        Évalue le prérequis 1 : Vision claire des leaders
        
        Args:
            interventions: Interventions des dirigeants (speaker_level="direction")
            company_info: Informations sur l'entreprise
            
        Returns:
            PrerequisEvaluationResponse avec l'évaluation
        """
        if not interventions:
            logger.warning("Aucune intervention de direction fournie")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=1,
                    titre="Vision claire des leaders : Pourquoi l'IA ?",
                    evaluation_text="Aucune intervention de direction disponible pour évaluer ce prérequis.",
                    note=0.0
                )
            )
        
        # Formater les interventions
        interventions_text = self._format_interventions(interventions)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM
        prompt = PREREQUIS_1_PROMPT.format(
            interventions=interventions_text,
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=PREREQUIS_EVALUATION_SYSTEM_PROMPT,
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
                text_format=PrerequisEvaluationResponse
            )
            
            evaluation_response = response.output_parsed
            # S'assurer que l'ID est correct
            evaluation_response.evaluation.prerequis_id = 1
            evaluation_response.evaluation.titre = "Vision claire des leaders : Pourquoi l'IA ?"
            
            logger.info(f"Évaluation prérequis 1 terminée : note {evaluation_response.evaluation.note}/5")
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 1: {e}")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=1,
                    titre="Vision claire des leaders : Pourquoi l'IA ?",
                    evaluation_text=f"Erreur lors de l'évaluation : {str(e)}",
                    note=0.0
                )
            )
    
    def evaluate_prerequis_2(
        self,
        interventions: List[Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> PrerequisEvaluationResponse:
        """
        Évalue le prérequis 2 : Équipe projet complète
        
        Args:
            interventions: Interventions des équipes métier (speaker_level="métier")
            company_info: Informations sur l'entreprise
            
        Returns:
            PrerequisEvaluationResponse avec l'évaluation
        """
        if not interventions:
            logger.warning("Aucune intervention métier fournie")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=2,
                    titre="Équipe projet complète, compétente et qui décide",
                    evaluation_text="Aucune intervention métier disponible pour évaluer ce prérequis.",
                    note=0.0
                )
            )
        
        # Formater les interventions
        interventions_text = self._format_interventions(interventions)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM
        prompt = PREREQUIS_2_PROMPT.format(
            interventions=interventions_text,
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=PREREQUIS_EVALUATION_SYSTEM_PROMPT,
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
                text_format=PrerequisEvaluationResponse
            )
            
            evaluation_response = response.output_parsed
            # S'assurer que l'ID est correct
            evaluation_response.evaluation.prerequis_id = 2
            evaluation_response.evaluation.titre = "Équipe projet complète, compétente et qui décide"
            
            logger.info(f"Évaluation prérequis 2 terminée : note {evaluation_response.evaluation.note}/5")
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 2: {e}")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=2,
                    titre="Équipe projet complète, compétente et qui décide",
                    evaluation_text=f"Erreur lors de l'évaluation : {str(e)}",
                    note=0.0
                )
            )
    
    def evaluate_prerequis_3(
        self,
        validated_use_cases: List[Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> PrerequisEvaluationResponse:
        """
        Évalue le prérequis 3 : Cas d'usage important
        
        Args:
            validated_use_cases: Liste des cas d'usage validés
            company_info: Informations sur l'entreprise
            
        Returns:
            PrerequisEvaluationResponse avec l'évaluation
        """
        if not validated_use_cases:
            logger.warning("Aucun cas d'usage validé fourni")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=3,
                    titre="Cas d'usage important pour le business",
                    evaluation_text="Aucun cas d'usage validé disponible pour évaluer ce prérequis.",
                    note=0.0
                )
            )
        
        # Formater les cas d'usage
        use_cases_text = self._format_use_cases(validated_use_cases)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM
        prompt = PREREQUIS_3_PROMPT.format(
            validated_use_cases=use_cases_text,
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=PREREQUIS_EVALUATION_SYSTEM_PROMPT,
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
                text_format=PrerequisEvaluationResponse
            )
            
            evaluation_response = response.output_parsed
            # S'assurer que l'ID est correct
            evaluation_response.evaluation.prerequis_id = 3
            evaluation_response.evaluation.titre = "Cas d'usage important pour le business"
            
            logger.info(f"Évaluation prérequis 3 terminée : note {evaluation_response.evaluation.note}/5")
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 3: {e}")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=3,
                    titre="Cas d'usage important pour le business",
                    evaluation_text=f"Erreur lors de l'évaluation : {str(e)}",
                    note=0.0
                )
            )
    
    def evaluate_prerequis_4_document(
        self,
        document_id: int,
        interventions: List[Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> PrerequisDocumentEvaluationResponse:
        """
        Évalue le prérequis 4 pour un document : Données présentes
        
        Args:
            document_id: ID du document
            interventions: Interventions du document
            company_info: Informations sur l'entreprise
            
        Returns:
            PrerequisDocumentEvaluationResponse avec l'évaluation
        """
        if not interventions:
            logger.warning(f"Aucune intervention pour le document {document_id}")
            return PrerequisDocumentEvaluationResponse(
                evaluation=PrerequisDocumentEvaluation(
                    prerequis_id=4,
                    document_id=document_id,
                    evaluation_text="Aucune intervention disponible pour ce document.",
                    note=0.0
                )
            )
        
        # Formater les interventions
        interventions_text = self._format_interventions(interventions)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM
        prompt = PREREQUIS_4_PROMPT.format(
            document_id=document_id,
            interventions=interventions_text,
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=PREREQUIS_EVALUATION_SYSTEM_PROMPT,
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
                text_format=PrerequisDocumentEvaluationResponse
            )
            
            evaluation_response = response.output_parsed
            # S'assurer que les IDs sont corrects
            evaluation_response.evaluation.prerequis_id = 4
            evaluation_response.evaluation.document_id = document_id
            
            logger.info(f"Évaluation prérequis 4 document {document_id} terminée : note {evaluation_response.evaluation.note}/5")
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 4 pour document {document_id}: {e}")
            return PrerequisDocumentEvaluationResponse(
                evaluation=PrerequisDocumentEvaluation(
                    prerequis_id=4,
                    document_id=document_id,
                    evaluation_text=f"Erreur lors de l'évaluation : {str(e)}",
                    note=0.0
                )
            )
    
    def synthesize_prerequis_4(
        self,
        evaluations_by_document: List[PrerequisDocumentEvaluation],
        company_info: Dict[str, Any]
    ) -> PrerequisEvaluationResponse:
        """
        Synthétise les évaluations du prérequis 4 par document
        
        Args:
            evaluations_by_document: Liste des évaluations par document
            company_info: Informations sur l'entreprise
            
        Returns:
            PrerequisEvaluationResponse avec la synthèse globale
        """
        if not evaluations_by_document:
            logger.warning("Aucune évaluation par document pour le prérequis 4")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=4,
                    titre="Données présentes et faciles d'accès",
                    evaluation_text="Aucune évaluation disponible pour synthétiser.",
                    note=0.0
                )
            )
        
        # Formater les évaluations par document
        evaluations_text = self._format_document_evaluations(evaluations_by_document)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM
        prompt = PREREQUIS_4_SYNTHESIS_PROMPT.format(
            evaluations_by_document=evaluations_text,
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=PREREQUIS_SYNTHESIS_SYSTEM_PROMPT,
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
                text_format=PrerequisEvaluationResponse
            )
            
            evaluation_response = response.output_parsed
            # S'assurer que l'ID est correct
            evaluation_response.evaluation.prerequis_id = 4
            evaluation_response.evaluation.titre = "Données présentes et faciles d'accès"
            
            logger.info(f"Synthèse prérequis 4 terminée : note {evaluation_response.evaluation.note}/5")
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse du prérequis 4: {e}")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=4,
                    titre="Données présentes et faciles d'accès",
                    evaluation_text=f"Erreur lors de la synthèse : {str(e)}",
                    note=0.0
                )
            )
    
    def evaluate_prerequis_5_document(
        self,
        document_id: int,
        interventions: List[Dict[str, Any]],
        company_info: Dict[str, Any]
    ) -> PrerequisDocumentEvaluationResponse:
        """
        Évalue le prérequis 5 pour un document : Entreprise en mouvement
        
        Args:
            document_id: ID du document
            interventions: Interventions du document
            company_info: Informations sur l'entreprise
            
        Returns:
            PrerequisDocumentEvaluationResponse avec l'évaluation
        """
        if not interventions:
            logger.warning(f"Aucune intervention pour le document {document_id}")
            return PrerequisDocumentEvaluationResponse(
                evaluation=PrerequisDocumentEvaluation(
                    prerequis_id=5,
                    document_id=document_id,
                    evaluation_text="Aucune intervention disponible pour ce document.",
                    note=0.0
                )
            )
        
        # Formater les interventions
        interventions_text = self._format_interventions(interventions)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM
        prompt = PREREQUIS_5_PROMPT.format(
            document_id=document_id,
            interventions=interventions_text,
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=PREREQUIS_EVALUATION_SYSTEM_PROMPT,
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
                text_format=PrerequisDocumentEvaluationResponse
            )
            
            evaluation_response = response.output_parsed
            # S'assurer que les IDs sont corrects
            evaluation_response.evaluation.prerequis_id = 5
            evaluation_response.evaluation.document_id = document_id
            
            logger.info(f"Évaluation prérequis 5 document {document_id} terminée : note {evaluation_response.evaluation.note}/5")
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 5 pour document {document_id}: {e}")
            return PrerequisDocumentEvaluationResponse(
                evaluation=PrerequisDocumentEvaluation(
                    prerequis_id=5,
                    document_id=document_id,
                    evaluation_text=f"Erreur lors de l'évaluation : {str(e)}",
                    note=0.0
                )
            )
    
    def synthesize_prerequis_5(
        self,
        evaluations_by_document: List[PrerequisDocumentEvaluation],
        company_info: Dict[str, Any]
    ) -> PrerequisEvaluationResponse:
        """
        Synthétise les évaluations du prérequis 5 par document
        
        Args:
            evaluations_by_document: Liste des évaluations par document
            company_info: Informations sur l'entreprise
            
        Returns:
            PrerequisEvaluationResponse avec la synthèse globale
        """
        if not evaluations_by_document:
            logger.warning("Aucune évaluation par document pour le prérequis 5")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=5,
                    titre="Entreprise en mouvement (digitalisation…)",
                    evaluation_text="Aucune évaluation disponible pour synthétiser.",
                    note=0.0
                )
            )
        
        # Formater les évaluations par document
        evaluations_text = self._format_document_evaluations(evaluations_by_document)
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM
        prompt = PREREQUIS_5_SYNTHESIS_PROMPT.format(
            evaluations_by_document=evaluations_text,
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=PREREQUIS_SYNTHESIS_SYSTEM_PROMPT,
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
                text_format=PrerequisEvaluationResponse
            )
            
            evaluation_response = response.output_parsed
            # S'assurer que l'ID est correct
            evaluation_response.evaluation.prerequis_id = 5
            evaluation_response.evaluation.titre = "Entreprise en mouvement (digitalisation…)"
            
            logger.info(f"Synthèse prérequis 5 terminée : note {evaluation_response.evaluation.note}/5")
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse du prérequis 5: {e}")
            return PrerequisEvaluationResponse(
                evaluation=PrerequisEvaluation(
                    prerequis_id=5,
                    titre="Entreprise en mouvement (digitalisation…)",
                    evaluation_text=f"Erreur lors de la synthèse : {str(e)}",
                    note=0.0
                )
            )
    
    def synthesize_global_evaluation(
        self,
        evaluations: List[PrerequisEvaluation],
        company_info: Dict[str, Any]
    ) -> PrerequisGlobalSynthesis:
        """
        Synthétise globalement les 5 évaluations
        
        Args:
            evaluations: Liste des 5 évaluations validées
            company_info: Informations sur l'entreprise
            
        Returns:
            PrerequisGlobalSynthesis avec la synthèse globale
        """
        if len(evaluations) != 5:
            logger.warning(f"Nombre d'évaluations incorrect : {len(evaluations)} au lieu de 5")
        
        # Trier les évaluations par prerequis_id pour garantir l'ordre
        sorted_evaluations = sorted(evaluations, key=lambda e: e.prerequis_id)
        
        # Formater les évaluations
        company_info_text = self._format_company_info(company_info)
        
        # Appeler le LLM
        prompt = PREREQUIS_GLOBAL_SYNTHESIS_PROMPT.format(
            evaluation_1=sorted_evaluations[0].evaluation_text if len(sorted_evaluations) > 0 else "N/A",
            evaluation_2=sorted_evaluations[1].evaluation_text if len(sorted_evaluations) > 1 else "N/A",
            evaluation_3=sorted_evaluations[2].evaluation_text if len(sorted_evaluations) > 2 else "N/A",
            evaluation_4=sorted_evaluations[3].evaluation_text if len(sorted_evaluations) > 3 else "N/A",
            evaluation_5=sorted_evaluations[4].evaluation_text if len(sorted_evaluations) > 4 else "N/A",
            company_info=company_info_text
        )
        
        try:
            response = openai.responses.parse(
                model=self.model,
                instructions=PREREQUIS_SYNTHESIS_SYSTEM_PROMPT,
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
                text_format=PrerequisGlobalSynthesis
            )
            
            synthesis_response = response.output_parsed
            logger.info("Synthèse globale terminée")
            return synthesis_response
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse globale: {e}")
            return PrerequisGlobalSynthesis(
                synthese_text=f"Erreur lors de la synthèse globale : {str(e)}"
            )
    
    def _format_interventions(self, interventions: List[Dict[str, Any]]) -> str:
        """Formate les interventions pour l'analyse LLM"""
        formatted = []
        
        for intervention in interventions:
            text = intervention.get("text", "")
            speaker_level = intervention.get("speaker_level", "")
            speaker_role = intervention.get("speaker_role", "")
            
            # Construire un préfixe informatif
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
        elif "company_name" in company_info:
            formatted.append(f"**Nom**: {company_info['company_name']}")
        
        # Description
        if "description" in company_info:
            formatted.append(f"**Description**: {company_info['description']}")
        elif "company_description" in company_info:
            formatted.append(f"**Description**: {company_info['company_description']}")
        
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
        elif "company_url" in company_info:
            formatted.append(f"**Site web**: {company_info['company_url']}")
        
        # Informations supplémentaires
        if "informations_supplementaires" in company_info:
            formatted.append(f"**Informations supplémentaires**: {company_info['informations_supplementaires']}")
        
        return "\n".join(formatted) if formatted else "Aucune information disponible."
    
    def _format_use_cases(self, use_cases: List[Dict[str, Any]]) -> str:
        """Formate les cas d'usage validés"""
        if not use_cases:
            return "Aucun cas d'usage disponible."
        
        formatted = []
        for i, uc in enumerate(use_cases, 1):
            titre = uc.get("titre", "Titre non défini")
            description = uc.get("description", "")
            famille = uc.get("famille", "")
            
            uc_text = f"{i}. **{titre}**"
            if famille:
                uc_text += f" (Famille: {famille})"
            if description:
                uc_text += f"\n   {description}"
            
            formatted.append(uc_text)
        
        return "\n\n".join(formatted)
    
    def _format_document_evaluations(self, evaluations: List[PrerequisDocumentEvaluation]) -> str:
        """Formate les évaluations par document"""
        if not evaluations:
            return "Aucune évaluation disponible."
        
        formatted = []
        for eval_doc in evaluations:
            formatted.append(
                f"**Document {eval_doc.document_id}** :\n"
                f"Note: {eval_doc.note}/5\n"
                f"Évaluation: {eval_doc.evaluation_text}"
            )
        
        return "\n\n".join(formatted)
    
    def _format_evaluations(self, evaluations: List[PrerequisEvaluation]) -> str:
        """Formate les évaluations finales"""
        if not evaluations:
            return "Aucune évaluation disponible."
        
        formatted = []
        for eval_item in evaluations:
            formatted.append(
                f"**{eval_item.prerequis_id}. {eval_item.titre}** :\n"
                f"Note: {eval_item.note}/5\n"
                f"Évaluation: {eval_item.evaluation_text}"
            )
        
        return "\n\n".join(formatted)

