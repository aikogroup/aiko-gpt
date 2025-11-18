"""
Agent de filtrage sémantique utilisant GPT-5-nano
"""
import logging
from typing import List, Dict, Any
from openai import OpenAI
import os
from dotenv import load_dotenv
from .interesting_parts_agent import InterestingPartsAgent
from prompts.transcript_agent_prompts import (
    SEMANTIC_ANALYSIS_PROMPT_V2,
    SEMANTIC_ANALYSIS_SYSTEM_PROMPT_V2
)
from models.transcript_models import SemanticAnalysisResponse

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

class SemanticFilterAgent:
    """Agent de filtrage sémantique avec GPT-5-nano"""
    
    def __init__(self, api_key: str = None):
        self.interesting_parts_agent = InterestingPartsAgent()
        
        # Configuration OpenAI
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("Clé API OpenAI non configurée")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
    
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
        """Prépare le texte pour l'analyse sémantique avec métadonnées"""
        text_parts = []
        
        for intervention in interventions:
            speaker = intervention["speaker"]
            timestamp = intervention.get("timestamp", "")
            text = intervention["text"]
            speaker_type = intervention.get("speaker_type", "inconnu")
            speaker_level = intervention.get("speaker_level")
            
            # Formater l'intervention avec métadonnées
            metadata_parts = []
            if speaker_type:
                metadata_parts.append(f"type={speaker_type}")
            if speaker_level:
                metadata_parts.append(f"niveau={speaker_level}")
            
            metadata_str = f"[{'|'.join(metadata_parts)}]" if metadata_parts else ""
            
            if timestamp:
                text_parts.append(f"{metadata_str} [{timestamp}] {speaker}: {text}")
            else:
                text_parts.append(f"{metadata_str} {speaker}: {text}")
        
        return "\n".join(text_parts)
    
    def _perform_semantic_analysis(self, text: str) -> Dict[str, Any]:
        """Effectue l'analyse sémantique avec GPT-5-nano"""
        prompt = SEMANTIC_ANALYSIS_PROMPT_V2.format(transcript_text=text)
        
        try:
            # Appel à l'API OpenAI Responses avec structured output
            # Utilisation du paramètre 'instructions' pour le system prompt
            response = self.client.responses.parse(
                model=self.model,
                instructions=SEMANTIC_ANALYSIS_SYSTEM_PROMPT_V2,
                input=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                text_format=SemanticAnalysisResponse
            )
            
            # Extraction de la réponse structurée
            parsed_response = response.output_parsed
            
            # Conversion en dictionnaire pour compatibilité avec le reste du code
            analysis = parsed_response.model_dump()
            
            logger.info("Analyse sémantique réussie avec structured output")
            logger.info(f"Besoins: {len(analysis.get('besoins_exprimes', []))}, "
                       f"Frustrations: {len(analysis.get('frustrations_blocages', []))}, "
                       f"Opportunités: {len(analysis.get('opportunites_automatisation', []))}")
            
            # Log détaillé de la structure SemanticAnalysisResponse
            logger.info("=" * 80)
            logger.info("📊 STRUCTURE COMPLÈTE DE SemanticAnalysisResponse")
            logger.info("=" * 80)
            
            import json
            for key in ['besoins_exprimes', 'frustrations_blocages', 'attentes_implicites', 
                       'opportunites_amelioration', 'opportunites_automatisation', 'citations_cles']:
                items = analysis.get(key, [])
                logger.info(f"\n🔹 {key.upper()}: {len(items)} éléments")
                
                if items:
                    # Afficher le premier élément comme échantillon
                    sample = items[0]
                    logger.info(f"   Échantillon (premier élément):")
                    logger.info(f"   {json.dumps(sample, ensure_ascii=False, indent=6)}")
                    
                    # Vérifier la structure
                    if isinstance(sample, dict):
                        logger.info(f"   ✓ Structure: dict avec clés: {list(sample.keys())}")
                        if 'speaker_level' in sample:
                            logger.info(f"   ✓ speaker_level présent: {sample.get('speaker_level')}")
                        if 'speaker' in sample:
                            logger.info(f"   ✓ speaker présent: {sample.get('speaker')}")
                        if 'text' in sample:
                            text_preview = sample.get('text', '')[:100]
                            logger.info(f"   ✓ text présent (preview): {text_preview}...")
                    else:
                        logger.info(f"   ⚠ Structure: {type(sample).__name__} (attendu: dict)")
                else:
                    logger.info(f"   (liste vide)")
            
            logger.info("=" * 80)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse sémantique: {e}", exc_info=True)
            # Retourner une structure par défaut en cas d'erreur (format compatible avec CitationWithMetadata)
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
        
        # Fonction helper pour extraire le texte d'un élément (string ou dict)
        def get_text(item):
            if isinstance(item, dict):
                return item.get("text", str(item))
            return str(item)
        
        if analysis.get("besoins_exprimes"):
            summary_parts.append(f"Besoins exprimés ({len(analysis['besoins_exprimes'])}):")
            for besoin in analysis["besoins_exprimes"]:
                summary_parts.append(f"  - {get_text(besoin)}")
        
        if analysis.get("frustrations_blocages"):
            summary_parts.append(f"Frustrations/Blocages ({len(analysis['frustrations_blocages'])}):")
            for frustration in analysis["frustrations_blocages"]:
                summary_parts.append(f"  - {get_text(frustration)}")
        
        if analysis.get("opportunites_automatisation"):
            summary_parts.append(f"Opportunités d'automatisation ({len(analysis['opportunites_automatisation'])}):")
            for opportunite in analysis["opportunites_automatisation"]:
                summary_parts.append(f"  - {get_text(opportunite)}")
        
        return "\n".join(summary_parts)
