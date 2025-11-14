"""
Agent spécialisé pour extraire les citations liées aux enjeux stratégiques depuis les transcripts
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv
from process_transcript.transcript_agent import TranscriptAgent
from models.executive_summary_models import CitationsEnjeuxResponse
from prompts.executive_summary_prompts import EXTRACT_ENJEUX_CITATIONS_PROMPT

load_dotenv()

logger = logging.getLogger(__name__)


class TranscriptEnjeuxAgent:
    """Agent spécialisé pour extraire citations liées aux enjeux stratégiques"""
    
    def __init__(self, api_key: str = None, interviewer_names: List[str] = None):
        """
        Initialise l'agent.
        
        Args:
            api_key: Clé API OpenAI
            interviewer_names: Liste des noms d'intervieweurs (optionnel)
        """
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY doit être définie")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
        
        # Réutiliser TranscriptAgent pour le parsing de base
        self.transcript_agent = TranscriptAgent(openai_api_key=api_key, interviewer_names=interviewer_names)
    
    def extract_citations(self, transcript_files: List[str], validated_speakers: Optional[List[Dict[str, str]]] = None) -> List[Dict[str, Any]]:
        """
        Extrait les citations liées aux enjeux stratégiques depuis plusieurs fichiers de transcript.
        
        Args:
            transcript_files: Liste des chemins vers les fichiers de transcript (PDF ou JSON)
            validated_speakers: Liste optionnelle des speakers validés par l'utilisateur (NOUVEAU)
            
        Returns:
            Liste des citations extraites avec métadonnées
        """
        all_citations = []
        
        for file_path in transcript_files:
            try:
                logger.info(f"Traitement transcript pour enjeux: {file_path}")
                
                # Utiliser TranscriptAgent pour parser et filtrer (SANS analyse sémantique)
                result = self.transcript_agent.get_interesting_parts_only(file_path, validated_speakers=validated_speakers)
                
                # Extraire les interventions intéressantes
                interesting_parts = result.get("interesting_parts", {})
                interesting_interventions = interesting_parts.get("interventions", [])
                
                if not interesting_interventions:
                    logger.warning(f"Aucune intervention intéressante trouvée dans {file_path}")
                    continue
                
                # Préparer le texte pour l'extraction
                transcript_text = self._prepare_transcript_text(interesting_interventions)
                
                # Extraire les citations avec LLM
                citations = self._extract_citations_with_llm(transcript_text, interesting_interventions)
                
                all_citations.extend(citations)
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement de {file_path}: {e}", exc_info=True)
                continue
        
        logger.info(f"✅ {len(all_citations)} citations d'enjeux extraites au total")
        return all_citations
    
    def _prepare_transcript_text(self, interventions: List[Dict[str, Any]]) -> str:
        """Prépare le texte du transcript pour l'analyse"""
        text_parts = []
        
        for i, intervention in enumerate(interventions):
            speaker = intervention.get("speaker", "Unknown")
            timestamp = intervention.get("timestamp", "")
            text = intervention.get("text", "")
            speaker_type = intervention.get("speaker_type", "")
            
            metadata = f"[{i}]"
            if speaker_type:
                metadata += f" type={speaker_type}"
            if timestamp:
                metadata += f" {timestamp}"
            
            text_parts.append(f"{metadata} {speaker}: {text}")
        
        return "\n".join(text_parts)
    
    def _extract_citations_with_llm(self, transcript_text: str, interventions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrait les citations avec LLM"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                prompt = EXTRACT_ENJEUX_CITATIONS_PROMPT.format(transcript_text=transcript_text)
                
                response = self.client.responses.parse(
                    model=self.model,
                    instructions="Tu es un expert en analyse stratégique. Extrait uniquement les citations pertinentes pour les enjeux stratégiques. IMPORTANT: Assure-toi que toutes les citations sont correctement échappées dans le JSON (guillemets, apostrophes, retours à la ligne).",
                    input=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    text_format=CitationsEnjeuxResponse
                )
                
                parsed_response = response.output_parsed.model_dump()
                citations = parsed_response.get("citations", [])
                
                # Enrichir avec les métadonnées des interventions
                enriched_citations = []
                for citation_data in citations:
                    citation_text = citation_data.get("citation", "")
                    
                    # Trouver l'intervention correspondante
                    matching_intervention = None
                    for intervention in interventions:
                        if citation_text in intervention.get("text", ""):
                            matching_intervention = intervention
                            break
                    
                    enriched_citation = {
                        "citation": citation_data.get("citation", ""),
                        "speaker": citation_data.get("speaker", matching_intervention.get("speaker", "") if matching_intervention else ""),
                        "timestamp": citation_data.get("timestamp", matching_intervention.get("timestamp", "") if matching_intervention else ""),
                        "contexte": citation_data.get("contexte", ""),
                        "speaker_type": matching_intervention.get("speaker_type", "") if matching_intervention else "",
                        "speaker_level": matching_intervention.get("speaker_level", "") if matching_intervention else ""
                    }
                    enriched_citations.append(enriched_citation)
                
                return enriched_citations
                
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"Erreur lors de l'extraction LLM (tentative {attempt + 1}/{max_retries}): {error_msg}")
                
                # Si c'est une erreur de parsing JSON, essayer de récupérer la réponse brute
                if "json_invalid" in error_msg or "EOF while parsing" in error_msg:
                    logger.warning("Erreur de parsing JSON détectée - le modèle a peut-être retourné un JSON invalide")
                    if attempt < max_retries - 1:
                        logger.info("Nouvelle tentative avec un prompt plus strict...")
                        continue
                
                # Si c'est la dernière tentative, logger l'erreur complète et retourner vide
                if attempt == max_retries - 1:
                    logger.error(f"Erreur lors de l'extraction LLM après {max_retries} tentatives: {e}", exc_info=True)
                    return []
        
        return []

