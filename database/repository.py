"""
Repository pattern pour les opérations CRUD sur la base de données
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict, Any
from database.models import (
    Project,
    Document,
    Transcript,
    Workshop,
    WordExtraction,
    WorkflowState,
    AgentResult,
    Speaker,
)
from database.schemas import (
    ProjectCreate,
    ProjectUpdate,
    DocumentCreate,
    DocumentUpdate,
    TranscriptCreate,
    TranscriptBatchCreate,
    WorkshopCreate,
    WorkshopUpdate,
    WordExtractionCreate,
    WorkflowStateCreate,
    WorkflowStateUpdate,
    AgentResultCreate,
    AgentResultUpdate,
    SpeakerCreate,
    SpeakerUpdate,
)


# ============================================================================
# Repository pour Project
# ============================================================================

class ProjectRepository:
    """Repository pour les opérations sur les projets"""
    
    @staticmethod
    def get_by_id(db: Session, project_id: int) -> Optional[Project]:
        """Récupère un projet par son ID"""
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def get_by_company_name(db: Session, company_name: str) -> Optional[Project]:
        """Récupère un projet par le nom de l'entreprise"""
        return db.query(Project).filter(Project.company_name == company_name).first()
    
    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """Récupère tous les projets avec pagination"""
        return db.query(Project).offset(skip).limit(limit).all()
    
    @staticmethod
    def create(db: Session, project: ProjectCreate) -> Project:
        """Crée un nouveau projet"""
        db_project = Project(**project.model_dump())
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project
    
    @staticmethod
    def update(db: Session, project_id: int, project_update: ProjectUpdate) -> Optional[Project]:
        """Met à jour un projet"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return None
        
        update_data = project_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)
        
        db.commit()
        db.refresh(db_project)
        return db_project
    
    @staticmethod
    def delete(db: Session, project_id: int) -> bool:
        """Supprime un projet (cascade sur les relations)"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if not db_project:
            return False
        
        db.delete(db_project)
        db.commit()
        return True


# ============================================================================
# Repository pour Document
# ============================================================================

class DocumentRepository:
    """Repository pour les opérations sur les documents"""
    
    @staticmethod
    def get_by_id(db: Session, document_id: int) -> Optional[Document]:
        """Récupère un document par son ID"""
        return db.query(Document).filter(Document.id == document_id).first()
    
    @staticmethod
    def get_by_project(db: Session, project_id: int, file_type: Optional[str] = None) -> List[Document]:
        """Récupère tous les documents d'un projet, optionnellement filtrés par type"""
        query = db.query(Document).filter(Document.project_id == project_id)
        if file_type:
            query = query.filter(Document.file_type == file_type)
        return query.all()
    
    @staticmethod
    def create(db: Session, document: DocumentCreate) -> Document:
        """Crée un nouveau document"""
        db_document = Document(**document.model_dump())
        db.add(db_document)
        db.commit()
        db.refresh(db_document)
        return db_document
    
    @staticmethod
    def update(db: Session, document_id: int, document_update: DocumentUpdate) -> Optional[Document]:
        """Met à jour un document"""
        db_document = db.query(Document).filter(Document.id == document_id).first()
        if not db_document:
            return None
        
        update_data = document_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_document, key, value)
        
        db.commit()
        db.refresh(db_document)
        return db_document
    
    @staticmethod
    def delete(db: Session, document_id: int) -> bool:
        """Supprime un document"""
        db_document = db.query(Document).filter(Document.id == document_id).first()
        if not db_document:
            return False
        
        db.delete(db_document)
        db.commit()
        return True


# ============================================================================
# Repository pour Transcript
# ============================================================================

class TranscriptRepository:
    """Repository pour les opérations sur les transcripts"""
    
    @staticmethod
    def get_by_id(db: Session, transcript_id: int) -> Optional[Transcript]:
        """Récupère un transcript par son ID"""
        return db.query(Transcript).filter(Transcript.id == transcript_id).first()
    
    @staticmethod
    def get_by_document(db: Session, document_id: int) -> List[Transcript]:
        """Récupère tous les transcripts d'un document"""
        return db.query(Transcript).filter(Transcript.document_id == document_id).all()
    
    @staticmethod
    def get_enriched_by_document(
        db: Session,
        document_id: int,
        filter_interviewers: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Récupère tous les transcripts d'un document avec les infos speakers enrichies.
        
        Args:
            db: Session de base de données
            document_id: ID du document
            filter_interviewers: Si True, exclut les interventions des interviewers
        
        Returns:
            Liste de dicts avec toutes les infos enrichies :
            - speaker: Nom parsé original
            - speaker_id: ID du speaker validé
            - speaker_type: Type (interviewer/interviewé) depuis speakers ou transcripts
            - speaker_role: Rôle exact du speaker (depuis speakers)
            - speaker_level: Niveau hiérarchique (direction/métier/inconnu) depuis speakers
            - speaker_name: Nom validé du speaker (depuis speakers)
            - timestamp: Timestamp de l'intervention
            - text: Texte de l'intervention
        """
        from database.models import Speaker
        
        # Jointure LEFT JOIN entre Transcript et Speaker
        query = db.query(
            Transcript,
            Speaker
        ).outerjoin(
            Speaker, Transcript.speaker_id == Speaker.id
        ).filter(
            Transcript.document_id == document_id
        )
        
        # Filtrer les interviewers si demandé
        if filter_interviewers:
            query = query.filter(
                or_(
                    Speaker.speaker_type != 'interviewer',
                    Speaker.speaker_type.is_(None),
                    # Si pas de speaker_id, utiliser speaker_type depuis transcripts
                    and_(
                        Transcript.speaker_id.is_(None),
                        or_(
                            Transcript.speaker_type != 'interviewer',
                            Transcript.speaker_type.is_(None)
                        )
                    )
                )
            )
        
        results = query.all()
        
        enriched = []
        for transcript, speaker in results:
            # Utiliser les infos depuis speakers si disponible, sinon depuis transcripts
            enriched.append({
                "speaker": transcript.speaker,  # Nom parsé original
                "speaker_id": transcript.speaker_id,
                "timestamp": transcript.timestamp,
                "text": transcript.text,
                # Infos depuis speakers (si speaker_id existe)
                "speaker_type": speaker.speaker_type if speaker else transcript.speaker_type,
                "speaker_role": speaker.role if speaker else None,
                "speaker_level": speaker.level if speaker else None,
                "speaker_name": speaker.name if speaker else transcript.speaker,  # Nom validé
            })
        
        return enriched
    
    @staticmethod
    def search_fulltext(
        db: Session,
        search_query: str,
        project_id: Optional[int] = None,
        speaker: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Recherche full-text dans les transcripts.
        Utilise la fonction PostgreSQL search_transcripts.
        """
        from sqlalchemy import text
        
        # Construire la requête SQL
        query = text("""
            SELECT * FROM search_transcripts(
                :search_query,
                :project_id,
                :speaker
            )
            LIMIT :limit
        """)
        
        result = db.execute(
            query,
            {
                "search_query": search_query,
                "project_id": project_id,
                "speaker": speaker,
                "limit": limit
            }
        )
        
        # Convertir les résultats en dictionnaires
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result]
    
    @staticmethod
    def create(db: Session, transcript: TranscriptCreate) -> Transcript:
        """Crée un nouveau transcript"""
        db_transcript = Transcript(**transcript.model_dump())
        db.add(db_transcript)
        db.commit()
        db.refresh(db_transcript)
        return db_transcript
    
    @staticmethod
    def create_batch(db: Session, batch: TranscriptBatchCreate) -> List[Transcript]:
        """Crée plusieurs transcripts en batch"""
        db_transcripts = [
            Transcript(document_id=batch.document_id, **t.model_dump())
            for t in batch.transcripts
        ]
        db.add_all(db_transcripts)
        db.commit()
        for t in db_transcripts:
            db.refresh(t)
        return db_transcripts
    
    @staticmethod
    def delete_by_document(db: Session, document_id: int) -> int:
        """Supprime tous les transcripts d'un document"""
        count = db.query(Transcript).filter(Transcript.document_id == document_id).delete()
        db.commit()
        return count


# ============================================================================
# Repository pour Speaker
# ============================================================================

class SpeakerRepository:
    """Repository pour les opérations sur les speakers"""
    
    @staticmethod
    def get_by_id(db: Session, speaker_id: int) -> Optional[Speaker]:
        """Récupère un speaker par son ID"""
        return db.query(Speaker).filter(Speaker.id == speaker_id).first()
    
    @staticmethod
    def get_by_name_and_project(db: Session, name: str, project_id: Optional[int] = None) -> Optional[Speaker]:
        """Récupère un speaker par son nom et project_id"""
        return db.query(Speaker).filter(
            Speaker.name == name,
            Speaker.project_id == project_id
        ).first()
    
    @staticmethod
    def get_or_create_speaker(
        db: Session,
        name: str,
        role: Optional[str],
        level: Optional[str],
        speaker_type: str,
        project_id: Optional[int] = None
    ) -> Speaker:
        """
        Récupère un speaker existant ou en crée un nouveau.
        
        Args:
            db: Session de base de données
            name: Nom du speaker
            role: Rôle du speaker (ex: "Directeur Général")
            level: Niveau hiérarchique ('direction', 'métier', 'inconnu')
            speaker_type: Type de speaker ('interviewer' ou 'interviewé')
            project_id: ID du projet (NULL pour interviewers globaux)
        
        Returns:
            Speaker existant ou nouvellement créé
        """
        # Chercher un speaker existant
        speaker = SpeakerRepository.get_by_name_and_project(db, name, project_id)
        
        if speaker:
            # Mettre à jour les infos si elles ont changé
            if role is not None and speaker.role != role:
                speaker.role = role
            if level is not None and speaker.level != level:
                speaker.level = level
            if speaker.speaker_type != speaker_type:
                speaker.speaker_type = speaker_type
            db.commit()
            db.refresh(speaker)
            return speaker
        
        # Créer un nouveau speaker
        speaker_data = SpeakerCreate(
            name=name,
            role=role,
            level=level,
            speaker_type=speaker_type,
            project_id=project_id
        )
        db_speaker = Speaker(**speaker_data.model_dump())
        db.add(db_speaker)
        db.commit()
        db.refresh(db_speaker)
        return db_speaker
    
    @staticmethod
    def get_by_project(db: Session, project_id: int) -> List[Speaker]:
        """Récupère tous les speakers d'un projet"""
        return db.query(Speaker).filter(Speaker.project_id == project_id).all()
    
    @staticmethod
    def get_interviewers(db: Session) -> List[Speaker]:
        """Récupère tous les interviewers globaux (project_id = NULL)"""
        return db.query(Speaker).filter(
            Speaker.project_id.is_(None),
            Speaker.speaker_type == 'interviewer'
        ).all()
    
    @staticmethod
    def get_by_document(db: Session, document_id: int) -> List[Speaker]:
        """Récupère tous les speakers associés à un document via ses transcripts"""
        from database.models import Document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            return []
        
        # Récupérer les speaker_ids uniques depuis les transcripts du document
        speaker_ids = db.query(Transcript.speaker_id).filter(
            Transcript.document_id == document_id,
            Transcript.speaker_id.isnot(None)
        ).distinct().all()
        
        if not speaker_ids:
            return []
        
        # Récupérer les speakers
        ids = [sid[0] for sid in speaker_ids]
        return db.query(Speaker).filter(Speaker.id.in_(ids)).all()
    
    @staticmethod
    def update(db: Session, speaker_id: int, speaker_update: SpeakerUpdate) -> Optional[Speaker]:
        """Met à jour un speaker"""
        db_speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
        if not db_speaker:
            return None
        
        update_data = speaker_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_speaker, field, value)
        
        db.commit()
        db.refresh(db_speaker)
        return db_speaker
    
    @staticmethod
    def delete(db: Session, speaker_id: int) -> bool:
        """Supprime un speaker"""
        db_speaker = db.query(Speaker).filter(Speaker.id == speaker_id).first()
        if not db_speaker:
            return False
        
        db.delete(db_speaker)
        db.commit()
        return True


# ============================================================================
# Repository pour WorkflowState
# ============================================================================

class WorkflowStateRepository:
    """Repository pour les opérations sur les workflow states"""
    
    @staticmethod
    def get_by_id(db: Session, state_id: int) -> Optional[WorkflowState]:
        """Récupère un workflow state par son ID"""
        return db.query(WorkflowState).filter(WorkflowState.id == state_id).first()
    
    @staticmethod
    def get_by_thread(
        db: Session,
        project_id: int,
        workflow_type: str,
        thread_id: str
    ) -> Optional[WorkflowState]:
        """Récupère un workflow state par thread"""
        return db.query(WorkflowState).filter(
            and_(
                WorkflowState.project_id == project_id,
                WorkflowState.workflow_type == workflow_type,
                WorkflowState.thread_id == thread_id
            )
        ).first()
    
    @staticmethod
    def get_by_project(
        db: Session,
        project_id: int,
        workflow_type: Optional[str] = None
    ) -> List[WorkflowState]:
        """Récupère tous les workflow states d'un projet"""
        query = db.query(WorkflowState).filter(WorkflowState.project_id == project_id)
        if workflow_type:
            query = query.filter(WorkflowState.workflow_type == workflow_type)
        return query.order_by(WorkflowState.created_at.desc()).all()
    
    @staticmethod
    def create_or_update(
        db: Session,
        workflow_state: WorkflowStateCreate
    ) -> WorkflowState:
        """Crée ou met à jour un workflow state (upsert)"""
        existing = db.query(WorkflowState).filter(
            and_(
                WorkflowState.project_id == workflow_state.project_id,
                WorkflowState.workflow_type == workflow_state.workflow_type,
                WorkflowState.thread_id == workflow_state.thread_id
            )
        ).first()
        
        if existing:
            # Mise à jour
            for key, value in workflow_state.model_dump(exclude={"project_id", "workflow_type", "thread_id"}).items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Création
            db_state = WorkflowState(**workflow_state.model_dump())
            db.add(db_state)
            db.commit()
            db.refresh(db_state)
            return db_state
    
    @staticmethod
    def update(
        db: Session,
        state_id: int,
        state_update: WorkflowStateUpdate
    ) -> Optional[WorkflowState]:
        """Met à jour un workflow state"""
        db_state = db.query(WorkflowState).filter(WorkflowState.id == state_id).first()
        if not db_state:
            return None
        
        update_data = state_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_state, key, value)
        
        db.commit()
        db.refresh(db_state)
        return db_state
    
    @staticmethod
    def delete(db: Session, state_id: int) -> bool:
        """Supprime un workflow state"""
        db_state = db.query(WorkflowState).filter(WorkflowState.id == state_id).first()
        if not db_state:
            return False
        
        db.delete(db_state)
        db.commit()
        return True


# ============================================================================
# Repository pour AgentResult
# ============================================================================

class AgentResultRepository:
    """Repository pour les opérations sur les résultats d'agents"""
    
    @staticmethod
    def get_by_id(db: Session, result_id: int) -> Optional[AgentResult]:
        """Récupère un résultat d'agent par son ID"""
        return db.query(AgentResult).filter(AgentResult.id == result_id).first()
    
    @staticmethod
    def get_by_project(
        db: Session,
        project_id: int,
        workflow_type: Optional[str] = None,
        result_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[AgentResult]:
        """Récupère les résultats d'agents d'un projet avec filtres optionnels"""
        query = db.query(AgentResult).filter(AgentResult.project_id == project_id)
        
        if workflow_type:
            query = query.filter(AgentResult.workflow_type == workflow_type)
        if result_type:
            query = query.filter(AgentResult.result_type == result_type)
        if status:
            query = query.filter(AgentResult.status == status)
        
        return query.order_by(AgentResult.created_at.desc()).all()
    
    @staticmethod
    def get_latest(
        db: Session,
        project_id: int,
        workflow_type: str,
        result_type: str,
        status: Optional[str] = None
    ) -> Optional[AgentResult]:
        """Récupère le dernier résultat d'agent pour un projet/workflow/type"""
        query = db.query(AgentResult).filter(
            and_(
                AgentResult.project_id == project_id,
                AgentResult.workflow_type == workflow_type,
                AgentResult.result_type == result_type
            )
        )
        
        if status:
            query = query.filter(AgentResult.status == status)
        
        return query.order_by(AgentResult.created_at.desc()).first()
    
    @staticmethod
    def create(db: Session, agent_result: AgentResultCreate) -> AgentResult:
        """Crée un nouveau résultat d'agent"""
        db_result = AgentResult(**agent_result.model_dump())
        db.add(db_result)
        db.commit()
        db.refresh(db_result)
        return db_result
    
    @staticmethod
    def update(
        db: Session,
        result_id: int,
        result_update: AgentResultUpdate
    ) -> Optional[AgentResult]:
        """Met à jour un résultat d'agent"""
        db_result = db.query(AgentResult).filter(AgentResult.id == result_id).first()
        if not db_result:
            return None
        
        update_data = result_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_result, key, value)
        
        db.commit()
        db.refresh(db_result)
        return db_result
    
    @staticmethod
    def delete(db: Session, result_id: int) -> bool:
        """Supprime un résultat d'agent"""
        db_result = db.query(AgentResult).filter(AgentResult.id == result_id).first()
        if not db_result:
            return False
        
        db.delete(db_result)
        db.commit()
        return True


# ============================================================================
# Repository pour Workshop
# ============================================================================

class WorkshopRepository:
    """Repository pour les opérations sur les workshops"""
    
    @staticmethod
    def get_by_id(db: Session, workshop_id: int) -> Optional[Workshop]:
        """Récupère un workshop par son ID"""
        return db.query(Workshop).filter(Workshop.id == workshop_id).first()
    
    @staticmethod
    def get_by_document(db: Session, document_id: int) -> List[Workshop]:
        """Récupère tous les workshops d'un document"""
        return db.query(Workshop).filter(Workshop.document_id == document_id).all()
    
    @staticmethod
    def get_by_document_and_atelier(
        db: Session,
        document_id: int,
        atelier_name: str
    ) -> Optional[Workshop]:
        """Récupère un workshop par document et nom d'atelier"""
        return db.query(Workshop).filter(
            and_(
                Workshop.document_id == document_id,
                Workshop.atelier_name == atelier_name
            )
        ).first()
    
    @staticmethod
    def create(db: Session, workshop: WorkshopCreate) -> Workshop:
        """Crée un nouveau workshop"""
        db_workshop = Workshop(**workshop.model_dump())
        db.add(db_workshop)
        db.commit()
        db.refresh(db_workshop)
        return db_workshop
    
    @staticmethod
    def create_batch(db: Session, workshops: List[WorkshopCreate]) -> List[Workshop]:
        """Crée plusieurs workshops en batch"""
        db_workshops = [Workshop(**w.model_dump()) for w in workshops]
        db.add_all(db_workshops)
        db.commit()
        for w in db_workshops:
            db.refresh(w)
        return db_workshops
    
    @staticmethod
    def update_aggregate(
        db: Session,
        workshop_id: int,
        aggregate_data: Dict[str, Any]
    ) -> Optional[Workshop]:
        """Met à jour l'agrégat d'un workshop"""
        db_workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
        if not db_workshop:
            return None
        
        db_workshop.aggregate = aggregate_data
        db.commit()
        db.refresh(db_workshop)
        return db_workshop
    
    @staticmethod
    def delete(db: Session, workshop_id: int) -> bool:
        """Supprime un workshop"""
        db_workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
        if not db_workshop:
            return False
        
        db.delete(db_workshop)
        db.commit()
        return True


# ============================================================================
# Repository pour WordExtraction
# ============================================================================

class WordExtractionRepository:
    """Repository pour les opérations sur les word extractions"""
    
    @staticmethod
    def get_by_id(db: Session, extraction_id: int) -> Optional[WordExtraction]:
        """Récupère une extraction par son ID"""
        return db.query(WordExtraction).filter(WordExtraction.id == extraction_id).first()
    
    @staticmethod
    def get_by_document(
        db: Session,
        document_id: int,
        extraction_type: Optional[str] = None
    ) -> List[WordExtraction]:
        """Récupère toutes les extractions d'un document, optionnellement filtrées par type"""
        query = db.query(WordExtraction).filter(WordExtraction.document_id == document_id)
        if extraction_type:
            query = query.filter(WordExtraction.extraction_type == extraction_type)
        return query.all()
    
    @staticmethod
    def create(db: Session, extraction: WordExtractionCreate) -> WordExtraction:
        """Crée une nouvelle extraction"""
        db_extraction = WordExtraction(**extraction.model_dump())
        db.add(db_extraction)
        db.commit()
        db.refresh(db_extraction)
        return db_extraction
    
    @staticmethod
    def create_batch(
        db: Session,
        extractions: List[WordExtractionCreate]
    ) -> List[WordExtraction]:
        """Crée plusieurs extractions en batch"""
        db_extractions = [WordExtraction(**e.model_dump()) for e in extractions]
        db.add_all(db_extractions)
        db.commit()
        for e in db_extractions:
            db.refresh(e)
        return db_extractions
    
    @staticmethod
    def delete(db: Session, extraction_id: int) -> bool:
        """Supprime une extraction"""
        db_extraction = db.query(WordExtraction).filter(WordExtraction.id == extraction_id).first()
        if not db_extraction:
            return False
        
        db.delete(db_extraction)
        db.commit()
        return True

