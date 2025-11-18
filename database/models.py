"""
Modèles SQLAlchemy ORM pour la base de données PostgreSQL
"""

from sqlalchemy import (
    Column, BigInteger, String, Text, Integer, DateTime, 
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List

Base = declarative_base()


class User(Base):
    """Modèle pour les utilisateurs (préparé pour migration future)"""
    __tablename__ = "users"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=True)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations (désactivées pour l'instant - créera une FK vers users.id plus tard)
    # projects = relationship("Project", back_populates="creator", foreign_keys="Project.created_by")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class Project(Base):
    """Modèle pour les projets (1 projet = 1 entreprise)"""
    __tablename__ = "projects"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    company_name = Column(String(255), nullable=False, unique=True)
    company_info = Column(JSONB, nullable=True)  # secteur, CA, employés, description
    created_by = Column(String(100), nullable=True)  # String simple pour l'instant, FK vers users.id plus tard
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    workflow_states = relationship("WorkflowState", back_populates="project", cascade="all, delete-orphan")
    agent_results = relationship("AgentResult", back_populates="project", cascade="all, delete-orphan")
    speakers = relationship("Speaker", back_populates="project", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Project(id={self.id}, company_name={self.company_name})>"


class Document(Base):
    """Modèle pour les documents (métadonnées uniquement)"""
    __tablename__ = "documents"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # workshop, transcript, word_report
    file_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    project = relationship("Project", back_populates="documents")
    transcripts = relationship("Transcript", back_populates="document", cascade="all, delete-orphan")
    workshops = relationship("Workshop", back_populates="document", cascade="all, delete-orphan")
    word_extractions = relationship("WordExtraction", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, file_name={self.file_name}, file_type={self.file_type})>"


class Speaker(Base):
    """Modèle pour les speakers (interviewers et interviewés)"""
    __tablename__ = "speakers"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)  # Rôle exact (ex: "Directeur Général")
    level = Column(String(50), nullable=True)  # 'direction', 'métier', 'inconnu'
    speaker_type = Column(String(50), nullable=False)  # 'interviewer' ou 'interviewé'
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)  # NULL pour interviewers globaux
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Contrainte unique : un speaker unique par projet (NULL = global)
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_speakers_project_name"),
    )
    
    # Relations
    project = relationship("Project", back_populates="speakers")
    transcripts = relationship("Transcript", back_populates="speaker_obj")
    
    def __repr__(self):
        return f"<Speaker(id={self.id}, name={self.name}, type={self.speaker_type}, project_id={self.project_id})>"


class Transcript(Base):
    """Modèle pour les interventions extraites avec recherche full-text"""
    __tablename__ = "transcripts"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    speaker = Column(String(255), nullable=True)  # Gardé pour compatibilité (nom parsé original)
    speaker_id = Column(BigInteger, ForeignKey("speakers.id", ondelete="SET NULL"), nullable=True)  # Lien vers speaker validé
    timestamp = Column(String(50), nullable=True)
    text = Column(Text, nullable=False)
    speaker_type = Column(String(50), nullable=True)  # interviewer, interviewé, etc.
    search_vector = Column(TSVECTOR, nullable=True)  # Mis à jour automatiquement par trigger
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    document = relationship("Document", back_populates="transcripts")
    speaker_obj = relationship("Speaker", back_populates="transcripts")
    
    # Index pour recherche full-text (défini dans schema.sql)
    
    def __repr__(self):
        return f"<Transcript(id={self.id}, speaker={self.speaker}, speaker_id={self.speaker_id}, text_length={len(self.text) if self.text else 0})>"


class WorkflowState(Base):
    """Modèle pour les checkpoints LangGraph"""
    __tablename__ = "workflow_states"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    workflow_type = Column(String(50), nullable=False)  # need_analysis, atouts, executive_summary, rappel_mission
    thread_id = Column(String(255), nullable=False)
    state_data = Column(JSONB, nullable=False)  # Checkpoint complet LangGraph
    status = Column(String(50), default="running", nullable=False)  # running, paused, completed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Contrainte unique
    __table_args__ = (
        UniqueConstraint("project_id", "workflow_type", "thread_id", name="uq_workflow_states_project_workflow_thread"),
    )
    
    # Relations
    project = relationship("Project", back_populates="workflow_states")
    
    def __repr__(self):
        return f"<WorkflowState(id={self.id}, workflow_type={self.workflow_type}, thread_id={self.thread_id}, status={self.status})>"


class Workshop(Base):
    """Modèle pour les données extraites des fichiers Excel d'ateliers"""
    __tablename__ = "workshops"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    atelier_name = Column(String(255), nullable=False)
    raw_extract = Column(JSONB, nullable=False)  # {use_case1: {text: "...", objective: "..."}, ...}
    aggregate = Column(JSONB, nullable=True)  # Résultat WorkshopData après LLM
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    document = relationship("Document", back_populates="workshops")
    
    def __repr__(self):
        return f"<Workshop(id={self.id}, atelier_name={self.atelier_name}, document_id={self.document_id})>"


class WordExtraction(Base):
    """Modèle pour les données extraites des rapports Word"""
    __tablename__ = "word_extractions"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    document_id = Column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    extraction_type = Column(String(50), nullable=False)  # 'needs' ou 'use_cases'
    data = Column(JSONB, nullable=False)  # Données structurées extraites
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relations
    document = relationship("Document", back_populates="word_extractions")
    
    def __repr__(self):
        return f"<WordExtraction(id={self.id}, extraction_type={self.extraction_type}, document_id={self.document_id})>"


class AgentResult(Base):
    """Modèle pour les résultats structurés des agents"""
    __tablename__ = "agent_results"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    project_id = Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    workflow_type = Column(String(50), nullable=False)
    result_type = Column(String(50), nullable=False)  # needs, use_cases, atouts, challenges, recommendations, maturity, etc.
    data = Column(JSONB, nullable=False)  # Résultats structurés
    status = Column(String(50), default="proposed", nullable=False)  # proposed, validated, rejected, final
    iteration_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relations
    project = relationship("Project", back_populates="agent_results")
    
    def __repr__(self):
        return f"<AgentResult(id={self.id}, workflow_type={self.workflow_type}, result_type={self.result_type}, status={self.status})>"

