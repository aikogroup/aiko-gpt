"""
Parser PDF pour extraire le contenu des transcriptions
"""
import pdfplumber
import re
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class PDFParser:
    """Parser pour extraire le contenu des PDF de transcriptions"""
    
    def __init__(self):
        # Patterns améliorés pour détecter les vrais speakers
        self.speaker_patterns = [
            # Format "Nom - HH:MM" (format principal observé) - pattern permissif
            r'^([A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ\-\']+)*)\s*-\s*\d{1,2}:\d{2}$',
            # Format "Nom: texte" - nom en début de ligne suivi de :
            r'^([A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ\-\']+)*)\s*:\s*(.*)',
            # Format "Nom - texte" - nom suivi de tiret
            r'^([A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ\-\']+)*)\s*-\s*(.*)',
            # Format avec timestamp: "Nom (HH:MM): texte"
            r'^([A-Za-zÀ-ÿ\-\']+(?:\s+[A-Za-zÀ-ÿ\-\']+)*)\s*\(\d{1,2}:\d{2}\)\s*:\s*(.*)',
        ]
        
        # Pas de patterns d'exclusion - trop contextuels
        
        self.timestamp_patterns = [
            r'(\d{1,2}:\d{2}(?::\d{2})?)',  # Format HH:MM ou HH:MM:SS
            r'(\d{1,2}h\d{2})',  # Format HHhMM
        ]
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrait tout le texte d'un PDF"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction du PDF {pdf_path}: {e}")
            raise
    
    def parse_transcript(self, pdf_path: str) -> List[Dict[str, Any]]:
        """
        Parse un PDF de transcription et retourne une liste de dicts
        avec speaker, timestamp et text
        """
        logger.info(f"Début du parsing du PDF: {pdf_path}")
        
        # Extraire le texte brut
        raw_text = self.extract_text_from_pdf(pdf_path)
        logger.info(f"Texte extrait: {len(raw_text)} caractères")
        
        # Diviser en lignes et nettoyer
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        logger.info(f"Nombre de lignes: {len(lines)}")
        
        # Parser les interventions
        interventions = []
        current_speaker = None
        current_text = ""
        current_timestamp = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Pas de vérification de faux speaker - trop contextuel
            
            # Chercher un pattern speaker
            speaker_match = None
            matched_pattern_index = -1
            for j, pattern in enumerate(self.speaker_patterns):
                match = re.match(pattern, line)
                if match:
                    speaker_match = match
                    matched_pattern_index = j
                    break
            
            if speaker_match:
                # Valider le speaker extrait
                speaker = speaker_match.group(1).strip()
                if self._is_valid_speaker(speaker):
                    # Sauvegarder l'intervention précédente si elle existe
                    if current_speaker and current_text.strip():
                        interventions.append({
                            "speaker": current_speaker,
                            "timestamp": current_timestamp,
                            "text": current_text.strip()
                        })
                    
                    # Nouvelle intervention
                    current_speaker = speaker
                    current_timestamp = self._extract_timestamp_from_line(line)
                    
                    # Si c'est le pattern "Nom - HH:MM" (index 0), le texte est sur la ligne suivante
                    if matched_pattern_index == 0:
                        # Format "Nom - HH:MM", texte sur la ligne suivante
                        current_text = ""
                        if i + 1 < len(lines):
                            current_text = lines[i + 1].strip()
                            i += 2  # Passer la ligne du speaker et la ligne du texte
                        else:
                            i += 1
                    else:
                        # Format "Nom: texte" ou "Nom - texte", tout sur la même ligne
                        current_text = speaker_match.group(2).strip() if len(speaker_match.groups()) > 1 else ""
                        i += 1
                else:
                    # Continuer le texte si le speaker n'est pas valide
                    if current_speaker:
                        current_text += " " + line
                    i += 1
            else:
                # Continuer le texte de l'intervention actuelle
                if current_speaker:
                    current_text += " " + line
                i += 1
        
        # Ajouter la dernière intervention
        if current_speaker and current_text.strip():
            interventions.append({
                "speaker": current_speaker,
                "timestamp": current_timestamp,
                "text": current_text.strip()
            })
        
        logger.info(f"Nombre d'interventions extraites: {len(interventions)}")
        return interventions
    
    def _extract_timestamp_from_line(self, line: str) -> str:
        """Extrait un timestamp d'une ligne"""
        for pattern in self.timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None
    
    def get_speakers(self, interventions: List[Dict[str, Any]]) -> List[str]:
        """Retourne la liste des speakers uniques"""
        speakers = set()
        for intervention in interventions:
            speakers.add(intervention["speaker"])
        return list(speakers)
    
    def filter_by_speakers(self, interventions: List[Dict[str, Any]], 
                          target_speakers: List[str]) -> List[Dict[str, Any]]:
        """Filtre les interventions par speakers"""
        return [intervention for intervention in interventions 
                if intervention["speaker"] in target_speakers]
    
    def _is_valid_speaker(self, speaker: str) -> bool:
        """Valide si un speaker extrait est valide - règles de base seulement"""
        # Règles minimales pour éviter les faux positifs évidents
        if not speaker or len(speaker) < 2:
            return False
        
        # Max 4 mots pour éviter les phrases complètes
        words = speaker.split()
        if len(words) > 4:
            return False
        
        # Doit contenir au moins une lettre
        if not any(c.isalpha() for c in speaker):
            return False
        
        return True
