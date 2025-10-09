"""
Agent pour identifier les parties intéressantes des transcriptions
"""
import logging
from typing import List, Dict, Any
import openai
import os
from dotenv import load_dotenv
from .pdf_parser import PDFParser
from prompts.transcript_agent_prompts import (
    INTERESTING_PARTS_FILTER_PROMPT,
    INTERESTING_PARTS_SYSTEM_PROMPT
)

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

class InterestingPartsAgent:
    """Agent pour filtrer les parties intéressantes des transcriptions avec LLM"""
    
    def __init__(self, api_key: str = None):
        self.pdf_parser = PDFParser()
        
        # Configuration OpenAI
        if api_key:
            openai.api_key = api_key
        else:
            openai.api_key = os.getenv("OPENAI_API_KEY")
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Traite un PDF et retourne les parties intéressantes
        """
        logger.info(f"Traitement du PDF: {pdf_path}")
        
        # Parser le PDF
        interventions = self.pdf_parser.parse_transcript(pdf_path)
        logger.info(f"Nombre d'interventions totales: {len(interventions)}")
        
        # Identifier les parties intéressantes
        interesting_interventions = self._filter_interesting_parts(interventions)
        logger.info(f"Nombre d'interventions intéressantes: {len(interesting_interventions)}")
        
        # Structurer le résultat
        result = {
            "pdf_path": pdf_path,
            "total_interventions": len(interventions),
            "interesting_interventions": len(interesting_interventions),
            "interventions": interesting_interventions,
            "speakers": self.pdf_parser.get_speakers(interventions),
            "interesting_speakers": self.pdf_parser.get_speakers(interesting_interventions)
        }
        
        logger.info(f"Résultat: {result['interesting_interventions']}/{result['total_interventions']} interventions intéressantes")
        return result
    
    def _filter_interesting_parts(self, interventions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtre les interventions avec un LLM pour identifier les parties intéressantes"""
        if not interventions:
            return []
        
        # Préparer le texte pour l'analyse LLM
        text_for_analysis = self._prepare_text_for_llm_analysis(interventions)
        
        # Utiliser le LLM pour identifier les parties intéressantes
        interesting_indices = self._llm_filter_interventions(text_for_analysis, len(interventions))
        
        # Retourner les interventions sélectionnées
        interesting = [interventions[i] for i in interesting_indices if i < len(interventions)]
        
        logger.info(f"LLM a sélectionné {len(interesting)} interventions intéressantes sur {len(interventions)}")
        return interesting
    
    def _prepare_text_for_llm_analysis(self, interventions: List[Dict[str, Any]]) -> str:
        """Prépare le texte pour l'analyse LLM"""
        text_parts = []
        
        for i, intervention in enumerate(interventions):
            speaker = intervention["speaker"]
            timestamp = intervention.get("timestamp", "")
            text = intervention["text"]
            
            # Formater l'intervention avec un index
            if timestamp:
                text_parts.append(f"[{i}] [{timestamp}] {speaker}: {text}")
            else:
                text_parts.append(f"[{i}] {speaker}: {text}")
        
        return "\n".join(text_parts)
    
    def _llm_filter_interventions(self, text: str, total_interventions: int) -> List[int]:
        """Utilise un LLM pour identifier les interventions intéressantes"""
        prompt = INTERESTING_PARTS_FILTER_PROMPT.format(transcript_text=text)
        
        try:
            response = openai.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": INTERESTING_PARTS_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Faible température pour plus de cohérence
                max_completion_tokens=500
            )
            
            # Parser la réponse pour extraire les indices
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Réponse LLM: {response_text}")
            
            # Extraire les numéros entre crochets
            import re
            matches = re.findall(r'\[(\d+)\]', response_text)
            indices = [int(match) for match in matches if int(match) < total_interventions]
            
            logger.info(f"Indices sélectionnés par LLM: {indices}")
            return indices
            
        except Exception as e:
            logger.error(f"Erreur lors du filtrage LLM: {e}")
            # Fallback: retourner toutes les interventions si erreur
            return list(range(total_interventions))
    
    def get_consultant_interventions(self, interventions: List[Dict[str, Any]], 
                                   consultant_names: List[str] = None) -> List[Dict[str, Any]]:
        """Filtre les interventions des consultants (Christella, Adrien)"""
        if consultant_names is None:
            consultant_names = ["christella", "adrien", "aiko"]
        
        consultant_interventions = []
        for intervention in interventions:
            speaker_lower = intervention["speaker"].lower()
            if any(name.lower() in speaker_lower for name in consultant_names):
                consultant_interventions.append(intervention)
        
        return consultant_interventions
    
    def get_client_interventions(self, interventions: List[Dict[str, Any]], 
                               consultant_names: List[str] = None) -> List[Dict[str, Any]]:
        """Filtre les interventions du client (tous sauf les consultants)"""
        if consultant_names is None:
            consultant_names = ["christella", "adrien", "aiko"]
        
        client_interventions = []
        for intervention in interventions:
            speaker_lower = intervention["speaker"].lower()
            if not any(name.lower() in speaker_lower for name in consultant_names):
                client_interventions.append(intervention)
        
        return client_interventions
