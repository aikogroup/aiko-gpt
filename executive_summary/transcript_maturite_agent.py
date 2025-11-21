"""
Agent spécialisé pour extraire les citations liées à la maturité IA depuis les transcripts
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import os
from dotenv import load_dotenv
from process_transcript.transcript_agent import TranscriptAgent
from models.executive_summary_models import CitationsMaturiteResponse
from prompts.executive_summary_prompts import EXTRACT_MATURITE_CITATIONS_PROMPT

load_dotenv()

logger = logging.getLogger(__name__)


class TranscriptMaturiteAgent:
    """Agent spécialisé pour extraire citations liées à la maturité IA"""
    
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
    
    def extract_citations(self, document_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Extrait les citations liées à la maturité IA depuis plusieurs documents transcript dans la BDD.
        PARALLÉLISÉ : Traite tous les documents en même temps pour gagner du temps.
        
        Args:
            document_ids: Liste des IDs de documents transcript dans la base de données
            
        Returns:
            Liste des citations extraites avec métadonnées
        """
        if not document_ids:
            return []
        
        all_citations = []
        
        # 🚀 PARALLÉLISATION : Traiter tous les documents en même temps
        max_workers = min(len(document_ids), 10)  # Maximum 10 threads en parallèle
        logger.info(f"🚀 Parallélisation avec {max_workers} workers pour {len(document_ids)} transcripts (maturité)")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre tous les documents pour traitement parallèle
            future_to_doc = {
                executor.submit(self._process_single_document, document_id): document_id
                for document_id in document_ids
            }
            
            # Récupérer les résultats au fur et à mesure
            for future in as_completed(future_to_doc):
                document_id = future_to_doc[future]
                try:
                    citations = future.result()
                    if citations:
                        all_citations.extend(citations)
                        logger.info(f"✅ Transcript document_id={document_id} terminé: {len(citations)} citations")
                except Exception as e:
                    logger.error(f"❌ Erreur lors du traitement du transcript document_id={document_id}: {e}", exc_info=True)
        
        logger.info(f"✅ {len(all_citations)} citations de maturité extraites au total")
        return all_citations
    
    def _process_single_document(self, document_id: int) -> List[Dict[str, Any]]:
        """
        Traite un seul document transcript pour extraire les citations de maturité.
        
        Args:
            document_id: ID du document transcript dans la base de données
            
        Returns:
            Liste des citations extraites pour ce document
        """
        try:
            logger.info(f"Traitement transcript pour maturité: document_id={document_id}")
            
            # Utiliser TranscriptAgent pour charger depuis la BDD et filtrer (SANS analyse sémantique)
            result = self.transcript_agent.process_from_db(
                document_id=document_id,
                filter_interviewers=True
            )
            
            # Extraire les interventions depuis le résultat
            if result.get("status") == "error":
                logger.warning(f"Erreur lors du traitement du document {document_id}: {result.get('error')}")
                return []
            
            # Utiliser TOUTES les interventions depuis parsing.interventions
            # Le LLM filtrera ensuite pour extraire uniquement les citations pertinentes
            # Important pour la maturité : certaines mentions factuelles d'outils peuvent être exclues par interesting_parts
            interventions = result.get("parsing", {}).get("interventions", [])
            
            if not interventions:
                logger.warning(f"Aucune intervention trouvée pour document_id={document_id}")
                return []
            
            # Préparer le texte pour l'extraction
            transcript_text = self._prepare_transcript_text(interventions)
            
            # Extraire les citations avec LLM
            citations = self._extract_citations_with_llm(transcript_text, interventions)
            
            return citations
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du document_id {document_id}: {e}", exc_info=True)
            return []
    
    def _prepare_transcript_text(self, interventions: List[Dict[str, Any]]) -> str:
        """Prépare le texte du transcript pour l'analyse"""
        text_parts = []
        
        for i, intervention in enumerate(interventions):
            speaker = intervention.get("speaker", "Unknown")
            text = intervention.get("text", "")
            speaker_type = intervention.get("speaker_type", "")
            
            metadata = f"[{i}]"
            if speaker_type:
                metadata += f" type={speaker_type}"
            
            text_parts.append(f"{metadata} {speaker}: {text}")
        
        return "\n".join(text_parts)
    
    def _extract_citations_with_llm(self, transcript_text: str, interventions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrait les citations avec LLM"""
        max_retries = 2
        for attempt in range(max_retries):
            try:
                prompt = EXTRACT_MATURITE_CITATIONS_PROMPT.format(transcript_text=transcript_text)
                
                response = self.client.responses.parse(
                    model=self.model,
                    instructions="Tu es un expert en évaluation de maturité IA. Extrait uniquement les citations pertinentes pour évaluer la maturité IA. IMPORTANT: Assure-toi que toutes les citations sont correctement échappées dans le JSON (guillemets, apostrophes, retours à la ligne).",
                    input=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    text_format=CitationsMaturiteResponse
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
                        "type_info": citation_data.get("type_info", ""),
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

