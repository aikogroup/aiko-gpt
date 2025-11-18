"""
Endpoints API pour la gestion de la base de données
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.db import get_db
from database import schemas
from database.repository import (
    ProjectRepository,
    DocumentRepository,
    TranscriptRepository,
    WorkflowStateRepository,
    AgentResultRepository,
)

router = APIRouter(prefix="/db", tags=["database"])


# ============================================================================
# Endpoints pour Project
# ============================================================================

@router.post("/projects", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """Crée un nouveau projet"""
    # Vérifier si le projet existe déjà
    existing = ProjectRepository.get_by_company_name(db, project.company_name)
    if existing:
        raise HTTPException(status_code=400, detail="Un projet avec ce nom d'entreprise existe déjà")
    
    return ProjectRepository.create(db, project)


@router.get("/projects", response_model=List[schemas.Project])
def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Récupère tous les projets avec pagination"""
    return ProjectRepository.get_all(db, skip=skip, limit=limit)


@router.get("/projects/{project_id}", response_model=schemas.Project)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Récupère un projet par son ID"""
    project = ProjectRepository.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.get("/projects/by-name/{company_name}", response_model=schemas.Project)
def get_project_by_name(company_name: str, db: Session = Depends(get_db)):
    """Récupère un projet par le nom de l'entreprise"""
    project = ProjectRepository.get_by_company_name(db, company_name)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.put("/projects/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    project_update: schemas.ProjectUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un projet"""
    project = ProjectRepository.update(db, project_id, project_update)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return project


@router.delete("/projects/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """Supprime un projet (cascade sur les relations)"""
    success = ProjectRepository.delete(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return {"message": "Projet supprimé avec succès"}


# ============================================================================
# Endpoints pour Document
# ============================================================================

@router.post("/documents", response_model=schemas.Document)
def create_document(document: schemas.DocumentCreate, db: Session = Depends(get_db)):
    """Crée un nouveau document"""
    # Vérifier que le projet existe
    project = ProjectRepository.get_by_id(db, document.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return DocumentRepository.create(db, document)


@router.get("/documents/{document_id}", response_model=schemas.Document)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Récupère un document par son ID"""
    document = DocumentRepository.get_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return document


@router.get("/projects/{project_id}/documents", response_model=List[schemas.Document])
def get_project_documents(
    project_id: int,
    file_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Récupère tous les documents d'un projet, optionnellement filtrés par type"""
    # Vérifier que le projet existe
    project = ProjectRepository.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return DocumentRepository.get_by_project(db, project_id, file_type)


@router.put("/documents/{document_id}", response_model=schemas.Document)
def update_document(
    document_id: int,
    document_update: schemas.DocumentUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un document"""
    document = DocumentRepository.update(db, document_id, document_update)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    return document


# ============================================================================
# Endpoints pour Transcript
# ============================================================================

@router.post("/transcripts", response_model=schemas.Transcript)
def create_transcript(transcript: schemas.TranscriptCreate, db: Session = Depends(get_db)):
    """Crée un nouveau transcript"""
    # Vérifier que le document existe
    document = DocumentRepository.get_by_id(db, transcript.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    return TranscriptRepository.create(db, transcript)


@router.post("/transcripts/batch", response_model=List[schemas.Transcript])
def create_transcripts_batch(batch: schemas.TranscriptBatchCreate, db: Session = Depends(get_db)):
    """Crée plusieurs transcripts en batch"""
    # Vérifier que le document existe
    document = DocumentRepository.get_by_id(db, batch.document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    return TranscriptRepository.create_batch(db, batch)


@router.get("/transcripts/search", response_model=List[schemas.TranscriptSearchResult])
def search_transcripts(
    search_query: str = Query(..., description="Requête de recherche"),
    project_id: Optional[int] = Query(None, description="Filtrer par projet"),
    speaker: Optional[str] = Query(None, description="Filtrer par speaker"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Recherche full-text dans les transcripts"""
    results = TranscriptRepository.search_fulltext(
        db, search_query, project_id, speaker, limit
    )
    return results


@router.get("/documents/{document_id}/transcripts", response_model=List[schemas.Transcript])
def get_document_transcripts(document_id: int, db: Session = Depends(get_db)):
    """Récupère tous les transcripts d'un document"""
    # Vérifier que le document existe
    document = DocumentRepository.get_by_id(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    
    return TranscriptRepository.get_by_document(db, document_id)


# ============================================================================
# Endpoints pour WorkflowState
# ============================================================================

@router.post("/workflow-states", response_model=schemas.WorkflowState)
def create_or_update_workflow_state(
    workflow_state: schemas.WorkflowStateCreate,
    db: Session = Depends(get_db)
):
    """Crée ou met à jour un workflow state (upsert)"""
    # Vérifier que le projet existe
    project = ProjectRepository.get_by_id(db, workflow_state.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return WorkflowStateRepository.create_or_update(db, workflow_state)


@router.get("/workflow-states/{state_id}", response_model=schemas.WorkflowState)
def get_workflow_state(state_id: int, db: Session = Depends(get_db)):
    """Récupère un workflow state par son ID"""
    state = WorkflowStateRepository.get_by_id(db, state_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow state non trouvé")
    return state


@router.get("/projects/{project_id}/workflow-states", response_model=List[schemas.WorkflowState])
def get_project_workflow_states(
    project_id: int,
    workflow_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Récupère tous les workflow states d'un projet"""
    # Vérifier que le projet existe
    project = ProjectRepository.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return WorkflowStateRepository.get_by_project(db, project_id, workflow_type)


@router.get("/workflow-states/by-thread", response_model=schemas.WorkflowState)
def get_workflow_state_by_thread(
    project_id: int = Query(...),
    workflow_type: str = Query(...),
    thread_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """Récupère un workflow state par thread"""
    state = WorkflowStateRepository.get_by_thread(db, project_id, workflow_type, thread_id)
    if not state:
        raise HTTPException(status_code=404, detail="Workflow state non trouvé")
    return state


# ============================================================================
# Endpoints pour AgentResult
# ============================================================================

@router.post("/agent-results", response_model=schemas.AgentResult)
def create_agent_result(
    agent_result: schemas.AgentResultCreate,
    db: Session = Depends(get_db)
):
    """Crée un nouveau résultat d'agent"""
    # Vérifier que le projet existe
    project = ProjectRepository.get_by_id(db, agent_result.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return AgentResultRepository.create(db, agent_result)


@router.get("/agent-results/{result_id}", response_model=schemas.AgentResult)
def get_agent_result(result_id: int, db: Session = Depends(get_db)):
    """Récupère un résultat d'agent par son ID"""
    result = AgentResultRepository.get_by_id(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Résultat d'agent non trouvé")
    return result


@router.get("/projects/{project_id}/agent-results", response_model=List[schemas.AgentResult])
def get_project_agent_results(
    project_id: int,
    workflow_type: Optional[str] = Query(None),
    result_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Récupère les résultats d'agents d'un projet avec filtres optionnels"""
    # Vérifier que le projet existe
    project = ProjectRepository.get_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    
    return AgentResultRepository.get_by_project(
        db, project_id, workflow_type, result_type, status
    )


@router.get("/agent-results/latest", response_model=schemas.AgentResult)
def get_latest_agent_result(
    project_id: int = Query(...),
    workflow_type: str = Query(...),
    result_type: str = Query(...),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Récupère le dernier résultat d'agent pour un projet/workflow/type"""
    result = AgentResultRepository.get_latest(
        db, project_id, workflow_type, result_type, status
    )
    if not result:
        raise HTTPException(status_code=404, detail="Résultat d'agent non trouvé")
    return result


@router.put("/agent-results/{result_id}", response_model=schemas.AgentResult)
def update_agent_result(
    result_id: int,
    result_update: schemas.AgentResultUpdate,
    db: Session = Depends(get_db)
):
    """Met à jour un résultat d'agent"""
    result = AgentResultRepository.update(db, result_id, result_update)
    if not result:
        raise HTTPException(status_code=404, detail="Résultat d'agent non trouvé")
    return result

