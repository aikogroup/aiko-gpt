"""
Parser JSON pour extraire le contenu des transcriptions
"""
import json
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class JSONParser:
    """Parser pour extraire le contenu des fichiers JSON de transcriptions"""
    
    def __init__(self):
        pass
    
    def parse_transcript(self, json_path: str) -> List[Dict[str, Any]]:
        """
        Parse un fichier JSON de transcription et retourne une liste de dicts
        avec speaker, timestamp et text.
        
        Fusionne les interventions consécutives du même speaker.
        
        Args:
            json_path: Chemin vers le fichier JSON
            
        Returns:
            Liste de dictionnaires avec les clés:
            - speaker: nom du speaker (ou "Speaker {id}" si speaker_name absent)
            - timestamp: timestamp de début de l'intervention
            - text: texte de l'intervention (fusion des phrases consécutives)
        """
        logger.info(f"Début du parsing du JSON: {json_path}")
        
        # Charger le fichier JSON
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du fichier JSON {json_path}: {e}")
            raise
        
        logger.info(f"Nombre d'entrées dans le JSON: {len(raw_data)}")
        
        # Fusionner les interventions consécutives du même speaker
        interventions = self._merge_consecutive_interventions(raw_data)
        
        logger.info(f"Nombre d'interventions après fusion: {len(interventions)}")
        return interventions
    
    def _merge_consecutive_interventions(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fusionne les interventions consécutives du même speaker
        
        Args:
            raw_data: Liste des entrées brutes du JSON
            
        Returns:
            Liste d'interventions fusionnées
        """
        if not raw_data:
            return []
        
        interventions = []
        current_speaker_name = None
        current_speaker_id = None
        current_text = ""
        current_timestamp = None
        
        for entry in raw_data:
            # Extraire les informations de l'entrée
            speaker_name = entry.get("speaker_name")
            speaker_id = entry.get("speaker_id")
            sentence = entry.get("sentence", "").strip()
            start_time = entry.get("startTime")
            
            # Déterminer l'identifiant du speaker (priorité au speaker_name, sinon speaker_id)
            speaker_identifier = speaker_name if speaker_name else f"Speaker {speaker_id}"
            
            # Si c'est le même speaker, fusionner
            if (speaker_name == current_speaker_name and 
                speaker_id == current_speaker_id):
                # Ajouter la phrase au texte courant
                if sentence:
                    current_text += " " + sentence
            else:
                # Sauvegarder l'intervention précédente si elle existe
                if current_text.strip():
                    interventions.append({
                        "speaker": current_speaker_name if current_speaker_name else f"Speaker {current_speaker_id}",
                        "speaker_name": current_speaker_name,
                        "speaker_id": current_speaker_id,
                        "timestamp": current_timestamp,
                        "text": current_text.strip()
                    })
                
                # Commencer une nouvelle intervention
                current_speaker_name = speaker_name
                current_speaker_id = speaker_id
                current_text = sentence
                current_timestamp = start_time
        
        # Ajouter la dernière intervention
        if current_text.strip():
            interventions.append({
                "speaker": current_speaker_name if current_speaker_name else f"Speaker {current_speaker_id}",
                "speaker_name": current_speaker_name,
                "speaker_id": current_speaker_id,
                "timestamp": current_timestamp,
                "text": current_text.strip()
            })
        
        return interventions
    
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

