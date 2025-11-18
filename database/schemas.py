"""
Modèles Pydantic pour validation API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


# ============================================================================
# Schemas de base
# ============================================================================

class UserBase(BaseModel):
    """Schéma de base pour User"""
    username: Optional[str] = Field(None, max_length=100)
    email: Optional[str] = Field(None, max_length=255)


class UserCreate(UserBase):
    """Schéma pour créer un User"""
    pass


class User(UserBase):
    """Schéma pour retourner un User"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour Project
# ============================================================================

class ProjectBase(BaseModel):
    """Schéma de base pour Project"""
    company_name: str = Field(..., max_length=255)
    company_info: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = Field(None, max_length=100)


class ProjectCreate(ProjectBase):
    """Schéma pour créer un Project"""
    pass


class ProjectUpdate(BaseModel):
    """Schéma pour mettre à jour un Project"""
    company_name: Optional[str] = Field(None, max_length=255)
    company_info: Optional[Dict[str, Any]] = None


class Project(ProjectBase):
    """Schéma pour retourner un Project"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour Document
# ============================================================================

class DocumentBase(BaseModel):
    """Schéma de base pour Document"""
    file_name: str = Field(..., max_length=255)
    file_type: str = Field(..., max_length=50)  # workshop, transcript, word_report
    file_metadata: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    """Schéma pour créer un Document"""
    project_id: int


class DocumentUpdate(BaseModel):
    """Schéma pour mettre à jour un Document"""
    file_name: Optional[str] = Field(None, max_length=255)
    file_metadata: Optional[Dict[str, Any]] = None


class Document(DocumentBase):
    """Schéma pour retourner un Document"""
    id: int
    project_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour Speaker
# ============================================================================

class SpeakerBase(BaseModel):
    """Schéma de base pour Speaker"""
    name: str = Field(..., max_length=255)
    role: Optional[str] = Field(None, max_length=255)
    level: Optional[str] = Field(None, max_length=50)  # 'direction', 'métier', 'inconnu'
    speaker_type: str = Field(..., max_length=50)  # 'interviewer' ou 'interviewé'


class SpeakerCreate(SpeakerBase):
    """Schéma pour créer un Speaker"""
    project_id: Optional[int] = None  # NULL pour interviewers globaux


class SpeakerUpdate(BaseModel):
    """Schéma pour mettre à jour un Speaker"""
    role: Optional[str] = Field(None, max_length=255)
    level: Optional[str] = Field(None, max_length=50)
    speaker_type: Optional[str] = Field(None, max_length=50)


class Speaker(SpeakerBase):
    """Schéma pour retourner un Speaker"""
    id: int
    project_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour Transcript
# ============================================================================

class TranscriptBase(BaseModel):
    """Schéma de base pour Transcript"""
    speaker: Optional[str] = Field(None, max_length=255)  # Nom parsé original (pour compatibilité)
    speaker_id: Optional[int] = None  # Lien vers speaker validé
    timestamp: Optional[str] = Field(None, max_length=50)
    text: str
    speaker_type: Optional[str] = Field(None, max_length=50)


class TranscriptCreate(TranscriptBase):
    """Schéma pour créer un Transcript"""
    document_id: int


class TranscriptBatchCreate(BaseModel):
    """Schéma pour créer plusieurs Transcripts en batch"""
    document_id: int
    transcripts: List[TranscriptBase]


class Transcript(TranscriptBase):
    """Schéma pour retourner un Transcript"""
    id: int
    document_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour WorkflowState
# ============================================================================

class WorkflowStateBase(BaseModel):
    """Schéma de base pour WorkflowState"""
    workflow_type: str = Field(..., max_length=50)
    thread_id: str = Field(..., max_length=255)
    state_data: Dict[str, Any]
    status: str = Field(default="running", max_length=50)


class WorkflowStateCreate(WorkflowStateBase):
    """Schéma pour créer un WorkflowState"""
    project_id: int


class WorkflowStateUpdate(BaseModel):
    """Schéma pour mettre à jour un WorkflowState"""
    state_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=50)


class WorkflowState(WorkflowStateBase):
    """Schéma pour retourner un WorkflowState"""
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour AgentResult
# ============================================================================

class AgentResultBase(BaseModel):
    """Schéma de base pour AgentResult"""
    workflow_type: str = Field(..., max_length=50)
    result_type: str = Field(..., max_length=50)
    data: Dict[str, Any]
    status: str = Field(default="proposed", max_length=50)
    iteration_count: int = Field(default=0)


class AgentResultCreate(AgentResultBase):
    """Schéma pour créer un AgentResult"""
    project_id: int


class AgentResultUpdate(BaseModel):
    """Schéma pour mettre à jour un AgentResult"""
    data: Optional[Dict[str, Any]] = None
    status: Optional[str] = Field(None, max_length=50)
    iteration_count: Optional[int] = None


class AgentResult(AgentResultBase):
    """Schéma pour retourner un AgentResult"""
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour requêtes de recherche
# ============================================================================

class TranscriptSearchQuery(BaseModel):
    """Schéma pour recherche full-text dans transcripts"""
    search_query: str = Field(..., description="Requête de recherche")
    project_id: Optional[int] = Field(None, description="Filtrer par projet")
    speaker: Optional[str] = Field(None, description="Filtrer par speaker")
    limit: int = Field(default=100, ge=1, le=1000)


class TranscriptSearchResult(BaseModel):
    """Schéma pour résultat de recherche full-text"""
    id: int
    document_id: int
    speaker: Optional[str]
    timestamp: Optional[str]
    text: str
    speaker_type: Optional[str]
    rank: float
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour Workshop
# ============================================================================

class WorkshopBase(BaseModel):
    """Schéma de base pour Workshop"""
    atelier_name: str = Field(..., max_length=255)
    raw_extract: Dict[str, Any]  # {use_case1: {text: "...", objective: "..."}, ...}
    aggregate: Optional[Dict[str, Any]] = None  # Résultat WorkshopData après LLM


class WorkshopCreate(WorkshopBase):
    """Schéma pour créer un Workshop"""
    document_id: int


class WorkshopUpdate(BaseModel):
    """Schéma pour mettre à jour un Workshop"""
    aggregate: Optional[Dict[str, Any]] = None


class Workshop(WorkshopBase):
    """Schéma pour retourner un Workshop"""
    id: int
    document_id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Schemas pour WordExtraction
# ============================================================================

class WordExtractionBase(BaseModel):
    """Schéma de base pour WordExtraction"""
    extraction_type: str = Field(..., max_length=50)  # 'needs' ou 'use_cases'
    data: Dict[str, Any]  # Données structurées extraites


class WordExtractionCreate(WordExtractionBase):
    """Schéma pour créer un WordExtraction"""
    document_id: int


class WordExtraction(WordExtractionBase):
    """Schéma pour retourner un WordExtraction"""
    id: int
    document_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

