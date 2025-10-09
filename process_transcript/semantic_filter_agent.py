"""
Agent de filtrage sémantique utilisant GPT-5-nano
"""
import logging
from typing import List, Dict, Any
import openai
import os
from dotenv import load_dotenv
from .interesting_parts_agent import InterestingPartsAgent
from prompts.transcript_agent_prompts import (
    SEMANTIC_ANALYSIS_PROMPT_V2,
    SEMANTIC_ANALYSIS_SYSTEM_PROMPT_V2
)

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

class SemanticFilterAgent:
    """Agent de filtrage sémantique avec GPT-5-nano"""
    
    def __init__(self, api_key: str = None):
        self.interesting_parts_agent = InterestingPartsAgent()
        
        # Configuration OpenAI
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        
        if not openai.api_key:
            logger.warning("Clé API OpenAI non configurée")
    
    def analyze_transcript(self, pdf_path: str) -> Dict[str, Any]:
        """
        Analyse une transcription avec filtrage sémantique
        """
        logger.info(f"Analyse sémantique du PDF: {pdf_path}")
        
        # D'abord, récupérer les parties intéressantes
        interesting_data = self.interesting_parts_agent.process_pdf(pdf_path)
        logger.info(f"Parties intéressantes identifiées: {interesting_data['interesting_interventions']}")
        
        # Préparer le texte pour l'analyse sémantique
        text_for_analysis = self._prepare_text_for_analysis(interesting_data["interventions"])
        
        # Analyse sémantique avec GPT-5-nano
        semantic_analysis = self._perform_semantic_analysis(text_for_analysis)
        
        # Structurer le résultat
        result = {
            "pdf_path": pdf_path,
            "total_interventions": interesting_data["total_interventions"],
            "interesting_interventions": interesting_data["interesting_interventions"],
            "semantic_analysis": semantic_analysis,
            "raw_interventions": interesting_data["interventions"]
        }
        
        logger.info("Analyse sémantique terminée")
        return result
    
    def _prepare_text_for_analysis(self, interventions: List[Dict[str, Any]]) -> str:
        """Prépare le texte pour l'analyse sémantique"""
        text_parts = []
        
        for intervention in interventions:
            speaker = intervention["speaker"]
            timestamp = intervention.get("timestamp", "")
            text = intervention["text"]
            
            # Formater l'intervention
            if timestamp:
                text_parts.append(f"[{timestamp}] {speaker}: {text}")
            else:
                text_parts.append(f"{speaker}: {text}")
        
        return "\n".join(text_parts)
    
    def _perform_semantic_analysis(self, text: str) -> Dict[str, Any]:
        """Effectue l'analyse sémantique avec GPT-5-nano"""
        prompt = SEMANTIC_ANALYSIS_PROMPT_V2.format(transcript_text=text)
        
        try:
            response = openai.responses.create(
                model="gpt-5-nano",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": f"{SEMANTIC_ANALYSIS_SYSTEM_PROMPT_V2}\n\n{prompt}"
                            }
                        ]
                    }
                ]
            )
            
            # Parser la réponse JSON
            import json
            response_text = response.output_text.strip()
            logger.info(f"Réponse LLM: {response_text[:200]}...")
            
            try:
                # Nettoyer la réponse si elle contient du markdown
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json", "").replace("```", "").strip()
                elif response_text.startswith("```"):
                    response_text = response_text.replace("```", "").strip()
                
                analysis = json.loads(response_text)
                logger.info("Analyse sémantique réussie")
                return analysis
            except json.JSONDecodeError as e:
                logger.error(f"Erreur de parsing JSON: {e}")
                logger.error(f"Réponse reçue: {response_text[:500]}...")
                # Retourner une structure par défaut
                return {
                    "besoins_exprimes": [],
                    "frustrations_blocages": [],
                    "attentes_implicites": [],
                    "opportunites_amelioration": [],
                    "opportunites_automatisation": [],
                    "citations_cles": [],
                    "erreur_parsing": str(e)
                }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse sémantique: {e}")
            return {
                "besoins_exprimes": [],
                "frustrations_blocages": [],
                "attentes_implicites": [],
                "opportunites_amelioration": [],
                "opportunites_automatisation": [],
                "citations_cles": [],
                "erreur": str(e)
            }
    
    def get_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Génère un résumé de l'analyse"""
        analysis = analysis_result.get("semantic_analysis", {})
        
        summary_parts = []
        
        if analysis.get("besoins_exprimes"):
            summary_parts.append(f"Besoins exprimés ({len(analysis['besoins_exprimes'])}):")
            for besoin in analysis["besoins_exprimes"]:
                summary_parts.append(f"  - {besoin}")
        
        if analysis.get("frustrations_blocages"):
            summary_parts.append(f"Frustrations/Blocages ({len(analysis['frustrations_blocages'])}):")
            for frustration in analysis["frustrations_blocages"]:
                summary_parts.append(f"  - {frustration}")
        
        if analysis.get("opportunites_automatisation"):
            summary_parts.append(f"Opportunités d'automatisation ({len(analysis['opportunites_automatisation'])}):")
            for opportunite in analysis["opportunites_automatisation"]:
                summary_parts.append(f"  - {opportunite}")
        
        return "\n".join(summary_parts)
