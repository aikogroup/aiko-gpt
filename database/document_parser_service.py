"""
Service centralisé pour parser et sauvegarder les documents dans la base de données
"""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd

from database.db import get_db_context
from database.repository import (
    DocumentRepository,
    TranscriptRepository,
    WorkshopRepository,
    WordExtractionRepository,
    SpeakerRepository,
)
from database.schemas import (
    DocumentCreate,
    TranscriptBatchCreate,
    TranscriptBase,
    WorkshopCreate,
    WordExtractionCreate,
)
from process_transcript.pdf_parser import PDFParser
from process_transcript.json_parser import JSONParser
from process_atelier.workshop_agent import WorkshopAgent
from executive_summary.word_report_extractor import WordReportExtractor

logger = logging.getLogger(__name__)


class DocumentParserService:
    """Service centralisé pour parser et sauvegarder les documents"""
    
    def __init__(self):
        self.pdf_parser = PDFParser()
        self.json_parser = JSONParser()
        self.workshop_agent = WorkshopAgent()
        self.word_extractor = WordReportExtractor()
    
    def parse_and_save_transcript(
        self,
        file_path: str,
        project_id: int,
        file_name: str,
        validated_speakers: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Parse un fichier transcript (PDF ou JSON) et sauvegarde dans la BDD.
        
        Args:
            file_path: Chemin vers le fichier
            project_id: ID du projet
            file_name: Nom du fichier
            validated_speakers: Liste des speakers validés par l'utilisateur
                              Format: [{"name": str, "role": str, "level": str, "is_interviewer": bool}, ...]
            metadata: Métadonnées supplémentaires (optionnel, pour compatibilité)
        
        Returns:
            ID du document créé
        
        Raises:
            ValueError: Si aucun speaker validé n'est fourni (sauf interviewers)
        """
        logger.info(f"Parsing et sauvegarde du transcript: {file_path}")
        
        # Vérifier qu'au moins un speaker non-interviewer est validé
        if not validated_speakers:
            raise ValueError("Aucun speaker validé fourni. Vous devez valider au moins un speaker avant de sauvegarder.")
        
        non_interviewer_speakers = [s for s in validated_speakers if not s.get("is_interviewer", False)]
        if not non_interviewer_speakers:
            raise ValueError("Aucun speaker interviewé validé. Vous devez valider au moins un speaker interviewé avant de sauvegarder.")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Le fichier n'existe pas: {file_path}")
        
        file_extension = path.suffix.lower()
        interventions = []
        
        # Parser selon le type de fichier
        if file_extension == ".pdf":
            logger.info("Parsing PDF")
            interventions = self.pdf_parser.parse_transcript(file_path)
        elif file_extension == ".json":
            logger.info("Parsing JSON")
            interventions = self.json_parser.parse_transcript(file_path)
        else:
            raise ValueError(f"Format de fichier non supporté pour transcript: {file_extension}")
        
        if not interventions:
            raise ValueError(f"Aucune intervention trouvée dans le fichier: {file_path}")
        
        # Créer un mapping nom validé -> speaker validé
        validated_speakers_map = {s["name"]: s for s in validated_speakers}
        validated_names = set(validated_speakers_map.keys())
        
        # Créer un mapping nom original -> nom validé pour gérer les renommages
        original_to_validated_map = {}
        for speaker_data in validated_speakers:
            validated_name = speaker_data["name"]
            original_name = speaker_data.get("original_name")
            if original_name and original_name != validated_name:
                original_to_validated_map[original_name] = validated_name
        
        # Sauvegarder dans la BDD
        with get_db_context() as db:
            # Créer l'entrée document (sans file_metadata pour les speakers)
            document_data = DocumentCreate(
                project_id=project_id,
                file_name=file_name,
                file_type="transcript",
                file_metadata=metadata or {},  # Garder pour autres métadonnées si nécessaire
            )
            document = DocumentRepository.create(db, document_data)
            
            # Créer ou récupérer les speakers dans la table speakers
            speaker_id_map = {}  # Mapping nom -> speaker_id
            speaker_type_map = {}  # Mapping nom -> speaker_type
            
            for speaker_data in validated_speakers:
                name = speaker_data["name"]
                role = speaker_data.get("role", "")
                level = speaker_data.get("level", "inconnu")
                is_interviewer = speaker_data.get("is_interviewer", False)
                
                # Déterminer project_id : NULL pour interviewers globaux, project_id pour interviewés
                speaker_project_id = None if is_interviewer else project_id
                speaker_type = "interviewer" if is_interviewer else "interviewé"
                
                # Normaliser level pour interviewers
                if is_interviewer:
                    level = None
                else:
                    # Pour les interviewés, normaliser "inconnu" en None seulement si vraiment vide
                    # Sinon garder "inconnu" comme valeur valide
                    if not level or level == "":
                        level = None
                    elif level not in ["direction", "métier", "inconnu"]:
                        # Si level invalide, mettre "inconnu" par défaut
                        level = "inconnu"
                
                # Créer ou récupérer le speaker
                speaker = SpeakerRepository.get_or_create_speaker(
                    db=db,
                    name=name,
                    role=role if role else None,
                    level=level,  # Peut être "direction", "métier", "inconnu" ou None (pour interviewers)
                    speaker_type=speaker_type,
                    project_id=speaker_project_id
                )
                speaker_id_map[name] = speaker.id
                speaker_type_map[name] = speaker.speaker_type
            
            # Filtrer les interventions : ne garder que celles avec un speaker validé
            # ET créer les transcripts avec speaker_id
            transcript_bases = []
            for intervention in interventions:
                speaker_name = intervention.get("speaker")  # Nom original du JSON/PDF
                
                # Déterminer le nom validé à utiliser pour le matching
                validated_name_to_use = None
                
                # 1. D'abord essayer de matcher par nom exact (nom validé)
                if speaker_name in validated_names:
                    validated_name_to_use = speaker_name
                # 2. Sinon utiliser le mapping original_name -> validated_name si le speaker a été renommé
                elif speaker_name in original_to_validated_map:
                    validated_name_to_use = original_to_validated_map[speaker_name]
                
                # Si le speaker est validé (directement ou via mapping), associer speaker_id
                if validated_name_to_use and validated_name_to_use in validated_names:
                    speaker_id = speaker_id_map.get(validated_name_to_use)
                    speaker_type = speaker_type_map.get(validated_name_to_use)
                    transcript_bases.append(
                        TranscriptBase(
                            speaker=speaker_name,  # Garder le nom original du JSON/PDF pour traçabilité
                            speaker_id=speaker_id,
                            timestamp=intervention.get("timestamp"),
                            text=intervention.get("text", ""),
                            speaker_type=speaker_type,  # Rempli depuis speakers
                        )
                    )
                # Sinon, on ne l'insère pas (selon les spécifications)
            
            if not transcript_bases:
                raise ValueError("Aucune intervention avec speaker validé trouvée dans le fichier")
            
            batch = TranscriptBatchCreate(
                document_id=document.id,
                transcripts=transcript_bases,
            )
            
            TranscriptRepository.create_batch(db, batch)
            
            logger.info(f"✅ {len(transcript_bases)} interventions sauvegardées (sur {len(interventions)} parsées) pour le document {document.id}")
            logger.info(f"✅ {len(speaker_id_map)} speakers créés/récupérés dans la table speakers")
            return document.id
    
    def parse_and_save_workshop(
        self,
        file_path: str,
        project_id: int,
        file_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Parse un fichier Excel d'atelier et sauvegarde dans la BDD.
        
        Args:
            file_path: Chemin vers le fichier Excel
            project_id: ID du projet
            file_name: Nom du fichier
            metadata: Métadonnées supplémentaires
        
        Returns:
            ID du document créé
        """
        logger.info(f"Parsing et sauvegarde du workshop: {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Le fichier n'existe pas: {file_path}")
        
        # Parser le fichier Excel
        df = self.workshop_agent.parse_excel(file_path)
        
        # Grouper par atelier
        workshops_dict = self.workshop_agent.group_by_workshop(df)
        
        if not workshops_dict:
            raise ValueError(f"Aucun atelier trouvé dans le fichier: {file_path}")
        
        # Sauvegarder dans la BDD
        with get_db_context() as db:
            # Créer l'entrée document
            document_data = DocumentCreate(
                project_id=project_id,
                file_name=file_name,
                file_type="workshop",
                file_metadata=metadata or {},
            )
            document = DocumentRepository.create(db, document_data)
            
            # Créer les entrées workshops
            workshop_creates = []
            for atelier_name, workshop_df in workshops_dict.items():
                # Construire le raw_extract JSON
                raw_extract = {}
                for idx, (_, row) in enumerate(workshop_df.iterrows(), start=1):
                    use_case = row.get('Use_Case', '').strip()
                    objective = row.get('Objective', '').strip()
                    if use_case:
                        raw_extract[f"use_case{idx}"] = {
                            "text": use_case,
                            "objective": objective,
                        }
                
                workshop_create = WorkshopCreate(
                    document_id=document.id,
                    atelier_name=atelier_name,
                    raw_extract=raw_extract,
                    aggregate=None,  # Sera rempli plus tard par WorkshopAgent
                )
                workshop_creates.append(workshop_create)
            
            WorkshopRepository.create_batch(db, workshop_creates)
            
            logger.info(f"✅ {len(workshop_creates)} ateliers sauvegardés pour le document {document.id}")
            return document.id
    
    def parse_and_save_word_report(
        self,
        file_path: str,
        project_id: int,
        file_name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Parse un fichier Word report et sauvegarde dans la BDD.
        
        Args:
            file_path: Chemin vers le fichier Word
            project_id: ID du projet
            file_name: Nom du fichier
            metadata: Métadonnées supplémentaires
        
        Returns:
            ID du document créé
        """
        logger.info(f"Parsing et sauvegarde du word report: {file_path}")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Le fichier n'existe pas: {file_path}")
        
        # Extraire les données depuis le Word
        extracted = self.word_extractor.extract_from_word(file_path)
        
        needs = extracted.get("final_needs", [])
        use_cases = extracted.get("final_use_cases", [])
        
        if not needs and not use_cases:
            raise ValueError(f"Aucune donnée extraite du fichier Word: {file_path}")
        
        # Sauvegarder dans la BDD
        with get_db_context() as db:
            # Créer l'entrée document
            document_data = DocumentCreate(
                project_id=project_id,
                file_name=file_name,
                file_type="word_report",
                file_metadata=metadata or {},
            )
            document = DocumentRepository.create(db, document_data)
            
            # Créer les entrées word_extractions
            extractions = []
            
            if needs:
                extraction_needs = WordExtractionCreate(
                    document_id=document.id,
                    extraction_type="needs",
                    data={"needs": needs},
                )
                extractions.append(extraction_needs)
            
            if use_cases:
                extraction_use_cases = WordExtractionCreate(
                    document_id=document.id,
                    extraction_type="use_cases",
                    data={"use_cases": use_cases},
                )
                extractions.append(extraction_use_cases)
            
            if extractions:
                WordExtractionRepository.create_batch(db, extractions)
            
            logger.info(f"✅ {len(extractions)} extractions sauvegardées pour le document {document.id}")
            return document.id

