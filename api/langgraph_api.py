"""
API LangGraph pour le workflow d'analyse des besoins.
Architecture propre : Streamlit = UI, API = Logique métier.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uvicorn
import uuid
import os
from pathlib import Path
import tempfile
from pydantic import BaseModel
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Importer les workflows
import sys
sys.path.append(str(Path(__file__).parent.parent))
from workflow.need_analysis_workflow import NeedAnalysisWorkflow
from workflow.rappel_mission_workflow import RappelMissionWorkflow
from executive_summary.executive_summary_workflow import ExecutiveSummaryWorkflow
from langgraph.checkpoint.memory import MemorySaver

# Initialisation de l'API
app = FastAPI(
    title="aiko - LangGraph API",
    description="API pour le workflow d'analyse des besoins IA",
    version="1.0.0"
)

# Stockage en mémoire des workflows (en production, utiliser Redis ou DB)
workflows: Dict[str, Any] = {}
executive_workflows: Dict[str, Any] = {}  # Workflows Executive Summary
rappel_workflows: Dict[str, Any] = {}  # Workflows Rappel de la mission
checkpointer = MemorySaver()

# Dossier temporaire pour les fichiers uploadés
UPLOAD_DIR = Path("/tmp/aiko_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ==================== MODÈLES PYDANTIC ====================

class WorkflowInput(BaseModel):
    """Input pour démarrer un workflow"""
    workshop_files: List[str] = []
    transcript_files: List[str] = []
    company_name: Optional[str] = None
    interviewer_names: Optional[List[str]] = None
    additional_context: Optional[str] = ""

class ValidationFeedback(BaseModel):
    """Feedback de validation utilisateur"""
    validated_needs: List[Dict[str, Any]]
    rejected_needs: List[Dict[str, Any]]
    user_feedback: str = ""

class UseCaseValidationFeedback(BaseModel):
    """Feedback de validation des use cases"""
    validated_quick_wins: List[Dict[str, Any]]
    validated_structuration_ia: List[Dict[str, Any]]
    rejected_quick_wins: List[Dict[str, Any]]
    rejected_structuration_ia: List[Dict[str, Any]]
    user_feedback: str = ""

class ExecutiveSummaryInput(BaseModel):
    """Input pour démarrer un workflow Executive Summary"""
    word_report_path: str
    transcript_files: List[str] = []
    workshop_files: List[str] = []
    company_name: str
    interviewer_note: str = ""


class RappelMissionInput(BaseModel):
    """Input pour démarrer un workflow de rappel de mission"""

    company_name: str

class ExecutiveValidationFeedback(BaseModel):
    """Feedback de validation Executive Summary"""
    validation_type: str  # "challenges" ou "recommendations"
    validation_result: Dict[str, Any]


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "aiko LangGraph API",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/files/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload des fichiers et retourne les chemins locaux.
    
    Returns:
        {
            "file_paths": ["/tmp/aiko_uploads/uuid_filename.xlsx", ...],
            "file_types": {"workshop": [...], "transcript": [...]}
        }
    """
    try:
        file_paths = []
        workshop_files = []
        transcript_files = []
        
        for file in files:
            # Générer un nom unique
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            file_path = UPLOAD_DIR / f"{file_id}_{file.filename}"
            
            # Sauvegarder le fichier
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            file_paths.append(str(file_path))
            
            # Classifier par type
            if file_extension == ".xlsx":
                workshop_files.append(str(file_path))
            elif file_extension in [".pdf", ".json"]:
                transcript_files.append(str(file_path))
            elif file_extension == ".docx":
                # Fichier Word pour Executive Summary
                workshop_files.append(str(file_path))  # Pour l'instant, on le met dans workshop_files
        
        return {
            "file_paths": file_paths,
            "file_types": {
                "workshop": workshop_files,
                "transcript": transcript_files
            },
            "count": len(file_paths)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")


@app.post("/threads/{thread_id}/runs")
async def create_run(thread_id: str, workflow_input: WorkflowInput):
    """
    Démarre ou reprend un workflow.
    
    Args:
        thread_id: ID du thread (UUID)
        workflow_input: Fichiers et paramètres du workflow
    
    Returns:
        {
            "run_id": "uuid",
            "thread_id": "uuid",
            "status": "running"
        }
    """
    try:
        # Créer ou récupérer le workflow
        if thread_id not in workflows:
            # Nouveau workflow
            api_key = os.getenv("OPENAI_API_KEY")
            workflow = NeedAnalysisWorkflow(
                api_key=api_key,
                dev_mode=False,
                debug_mode=False  # Mode production
            )
            workflows[thread_id] = {
                "workflow": workflow,
                "state": None,
                "status": "created"
            }
        
        workflow_data = workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        # Lancer le workflow
        print(f"\n🚀 [API] Démarrage du workflow pour thread {thread_id}")
        print(f"📁 Workshop files: {workflow_input.workshop_files}")
        print(f"📁 Transcript files: {workflow_input.transcript_files}")
        print(f"🏢 Company: {workflow_input.company_name}")
        print(f"👥 Interviewers: {workflow_input.interviewer_names}")
        print(f"📝 Additional context: {len(workflow_input.additional_context or '')} caractères")
        
        # Exécuter le workflow (mode asynchrone géré par LangGraph)
        result = workflow.run(
            workshop_files=workflow_input.workshop_files,
            transcript_files=workflow_input.transcript_files,
            company_info={"company_name": workflow_input.company_name} if workflow_input.company_name else {},
            interviewer_names=workflow_input.interviewer_names,
            thread_id=thread_id,
            additional_context=workflow_input.additional_context or ""
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        workflow_data["status"] = "completed" if result.get("success") else "paused"
        
        run_id = str(uuid.uuid4())
        
        return {
            "run_id": run_id,
            "thread_id": thread_id,
            "status": workflow_data["status"]
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur workflow: {str(e)}")


@app.get("/threads/{thread_id}/state")
async def get_state(thread_id: str):
    """
    Récupère l'état actuel du workflow.
    
    Returns:
        {
            "thread_id": "uuid",
            "status": "running" | "paused" | "completed",
            "values": {...},  # État complet
            "next": ["node_name"] | []  # Prochain nœud ou vide si terminé
        }
    """
    if thread_id not in workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    workflow_data = workflows[thread_id]
    state = workflow_data.get("state", {})
    
    # Déterminer le prochain nœud en fonction de l'état
    next_node = []
    if workflow_data["status"] == "paused":
        # Vérifier où le workflow est en pause
        if state.get("use_case_workflow_paused"):
            # Priorité à use_case car c'est la phase 2
            next_node = ("validate_use_cases",)  # Tuple pour être cohérent avec LangGraph
        elif state.get("workflow_paused"):
            next_node = ("human_validation",)
        elif state.get("identified_needs"):
            # Si on a des besoins identifiés mais pas encore de flag workflow_paused
            next_node = ("human_validation",)
        elif state.get("proposed_quick_wins") or state.get("proposed_structuration_ia"):
            # Si on a des use cases proposés
            next_node = ("validate_use_cases",)
    
    return {
        "thread_id": thread_id,
        "status": workflow_data["status"],
        "values": state,
        "next": next_node
    }


@app.post("/threads/{thread_id}/validation")
async def send_validation(thread_id: str, feedback: ValidationFeedback):
    """
    Envoie le feedback de validation des besoins et reprend le workflow.
    
    Args:
        thread_id: ID du thread
        feedback: Feedback utilisateur
    
    Returns:
        {
            "status": "resumed",
            "thread_id": "uuid"
        }
    """
    if thread_id not in workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    try:
        workflow_data = workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n📝 [API] Réception du feedback de validation pour thread {thread_id}")
        print(f"✅ Validés: {len(feedback.validated_needs)}")
        print(f"❌ Rejetés: {len(feedback.rejected_needs)}")
        
        # Reprendre le workflow avec le feedback
        result = workflow.resume_workflow_with_feedback(
            validated_needs=feedback.validated_needs,
            rejected_needs=feedback.rejected_needs,
            user_feedback=feedback.user_feedback,
            thread_id=thread_id
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        workflow_data["status"] = "completed" if result.get("success") else "paused"
        
        return {
            "status": "resumed",
            "thread_id": thread_id,
            "workflow_status": workflow_data["status"]
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur reprise workflow: {str(e)}")


@app.post("/threads/{thread_id}/use-case-validation")
async def send_use_case_validation(thread_id: str, feedback: UseCaseValidationFeedback):
    """
    Envoie le feedback de validation des use cases et reprend le workflow.
    
    Args:
        thread_id: ID du thread
        feedback: Feedback utilisateur
    
    Returns:
        {
            "status": "completed",
            "thread_id": "uuid"
        }
    """
    if thread_id not in workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    try:
        workflow_data = workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n📝 [API] Réception du feedback use cases pour thread {thread_id}")
        print(f"✅ Quick Wins validés: {len(feedback.validated_quick_wins)}")
        print(f"✅ Structuration IA validés: {len(feedback.validated_structuration_ia)}")
        
        # Reprendre le workflow avec le feedback
        result = workflow.resume_use_case_workflow_with_feedback(
            validated_quick_wins=feedback.validated_quick_wins,
            validated_structuration_ia=feedback.validated_structuration_ia,
            rejected_quick_wins=feedback.rejected_quick_wins,
            rejected_structuration_ia=feedback.rejected_structuration_ia,
            user_feedback=feedback.user_feedback,
            thread_id=thread_id
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        # Mettre à jour le statut en fonction du résultat
        if result.get("success"):
            workflow_data["status"] = "completed"
        elif result.get("use_case_workflow_paused"):
            workflow_data["status"] = "paused"
        else:
            workflow_data["status"] = "error"
        
        return {
            "status": workflow_data["status"],
            "thread_id": thread_id,
            "final_results": result,
            "success": result.get("success", False)
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur reprise workflow: {str(e)}")


@app.post("/rappel-mission/threads/{thread_id}/runs")
async def create_rappel_mission_run(thread_id: str, mission_input: RappelMissionInput):
    """Démarre un workflow dédié au rappel de la mission."""

    try:
        if thread_id not in rappel_workflows:
            workflow = RappelMissionWorkflow()
            rappel_workflows[thread_id] = {
                "workflow": workflow,
                "state": None,
                "status": "created",
            }

        workflow_data = rappel_workflows[thread_id]
        workflow = workflow_data["workflow"]

        result = workflow.run(company_name=mission_input.company_name, thread_id=thread_id)

        workflow_data["state"] = result
        workflow_data["status"] = "completed" if result.get("success") else "error"

        return {
            "thread_id": thread_id,
            "status": workflow_data["status"],
            "result": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur rappel mission: {str(e)}")


@app.get("/rappel-mission/threads/{thread_id}/state")
async def get_rappel_mission_state(thread_id: str):
    """Récupère l'état courant du workflow rappel de mission."""

    if thread_id not in rappel_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")

    return {
        "thread_id": thread_id,
        "status": rappel_workflows[thread_id]["status"],
        "state": rappel_workflows[thread_id]["state"],
    }


@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """
    Supprime un thread et nettoie les ressources.
    
    Returns:
        {"status": "deleted"}
    """
    deleted = False

    if thread_id in workflows:
        del workflows[thread_id]
        deleted = True

    if thread_id in executive_workflows:
        del executive_workflows[thread_id]
        deleted = True

    if thread_id in rappel_workflows:
        del rappel_workflows[thread_id]
        deleted = True

    if deleted:
        return {"status": "deleted", "thread_id": thread_id}

    raise HTTPException(status_code=404, detail="Thread non trouvé")


# ==================== DÉMARRAGE ====================

if __name__ == "__main__":
    print("🚀 Démarrage de l'API LangGraph aiko...")
    print("📍 URL: http://localhost:2025")
    print("📖 Documentation: http://localhost:2025/docs")
    print("ℹ️  LangGraph Studio utilise le port 2024")
    
# ==================== ENDPOINTS EXECUTIVE SUMMARY ====================

@app.post("/executive-summary/threads/{thread_id}/runs")
async def create_executive_run(thread_id: str, workflow_input: ExecutiveSummaryInput):
    """Démarre un workflow Executive Summary"""
    try:
        # Créer ou récupérer le workflow
        if thread_id not in executive_workflows:
            api_key = os.getenv("OPENAI_API_KEY")
            workflow = ExecutiveSummaryWorkflow(
                api_key=api_key,
                dev_mode=False,
                debug_mode=False
            )
            executive_workflows[thread_id] = {
                "workflow": workflow,
                "state": None,
                "status": "created"
            }
        
        workflow_data = executive_workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n🚀 [API] Démarrage workflow Executive Summary pour thread {thread_id}")
        
        # Exécuter le workflow
        result = workflow.run(
            word_report_path=workflow_input.word_report_path,
            transcript_files=workflow_input.transcript_files,
            workshop_files=workflow_input.workshop_files,
            company_name=workflow_input.company_name,
            interviewer_note=workflow_input.interviewer_note,
            thread_id=thread_id
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        
        # Déterminer le statut
        if result.get("workflow_paused"):
            validation_type = result.get("validation_type", "")
            if validation_type == "challenges":
                workflow_data["status"] = "waiting_validation_challenges"
            elif validation_type == "recommendations":
                workflow_data["status"] = "waiting_validation_recommendations"
            else:
                workflow_data["status"] = "paused"
        elif result.get("challenges_success") and result.get("recommendations_success"):
            workflow_data["status"] = "completed"
        else:
            workflow_data["status"] = "running"
        
        return {
            "run_id": str(uuid.uuid4()),
            "thread_id": thread_id,
            "status": workflow_data["status"]
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur Executive Summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur workflow: {str(e)}")


@app.get("/executive-summary/threads/{thread_id}/status")
async def get_executive_status(thread_id: str):
    """Récupère le statut du workflow Executive Summary"""
    if thread_id not in executive_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    workflow_data = executive_workflows[thread_id]
    workflow = workflow_data["workflow"]
    
    # Récupérer l'état actuel depuis le checkpointer
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = workflow.graph.get_state(config)
    
    if snapshot and snapshot.values:
        state = snapshot.values
        
        # Vérifier si on est à un interrupt en regardant snapshot.next
        next_nodes = []
        if snapshot.next:
            if isinstance(snapshot.next, (list, tuple)):
                next_nodes = list(snapshot.next)
            else:
                next_nodes = [snapshot.next]
        
        # Si le prochain nœud est une validation, mettre à jour les flags
        if "human_validation_enjeux" in next_nodes:
            state["workflow_paused"] = True
            state["validation_type"] = "challenges"
            workflow.graph.update_state(config, state)
            workflow_data["state"] = state
            workflow_data["status"] = "waiting_validation_challenges"
        elif "human_validation_recommendations" in next_nodes:
            state["workflow_paused"] = True
            state["validation_type"] = "recommendations"
            workflow.graph.update_state(config, state)
            workflow_data["state"] = state
            workflow_data["status"] = "waiting_validation_recommendations"
        # Sinon, déterminer le statut en fonction de l'état actuel
        elif state.get("workflow_paused"):
            validation_type = state.get("validation_type", "")
            if validation_type == "challenges":
                workflow_data["status"] = "waiting_validation_challenges"
            elif validation_type == "recommendations":
                workflow_data["status"] = "waiting_validation_recommendations"
            else:
                workflow_data["status"] = "paused"
        elif state.get("challenges_success") and state.get("recommendations_success"):
            workflow_data["status"] = "completed"
            # S'assurer que l'état est bien stocké dans workflow_data
            workflow_data["state"] = state
        elif next_nodes:
            # Il y a des nœuds suivants, le workflow est en cours
            workflow_data["status"] = "running"
        else:
            # Pas de nœuds suivants et pas de pause, donc terminé
            workflow_data["status"] = "completed"
            # S'assurer que l'état est bien stocké dans workflow_data
            workflow_data["state"] = state
    
    return {"status": workflow_data["status"]}


@app.get("/executive-summary/threads/{thread_id}/state")
async def get_executive_state(thread_id: str):
    """Récupère l'état du workflow Executive Summary"""
    if thread_id not in executive_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    workflow_data = executive_workflows[thread_id]
    workflow = workflow_data["workflow"]
    
    # Récupérer l'état actuel depuis le checkpointer
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = workflow.graph.get_state(config)
    
    # Prioriser l'état du checkpointer, mais utiliser aussi l'état stocké dans workflow_data
    state_from_checkpointer = None
    if snapshot and snapshot.values:
        state_from_checkpointer = snapshot.values
    
    state_from_storage = workflow_data.get("state", {})
    
    # Fusionner les deux états (priorité au checkpointer, mais compléter avec storage)
    if state_from_checkpointer:
        state = state_from_checkpointer.copy()
        # Compléter avec les données de storage si manquantes dans checkpointer
        for key in ["validated_challenges", "validated_recommendations", "maturity_score", "maturity_summary"]:
            if not state.get(key) and state_from_storage.get(key):
                state[key] = state_from_storage[key]
    else:
        state = state_from_storage
    
    # Debug: afficher ce qui est retourné
    print(f"📊 [API] État retourné pour thread {thread_id}:")
    print(f"   - validated_challenges: {len(state.get('validated_challenges', []))}")
    print(f"   - validated_recommendations: {len(state.get('validated_recommendations', []))}")
    
    # Convertir en format JSON-serializable
    return {
        "identified_challenges": state.get("identified_challenges", []),
        "validated_challenges": state.get("validated_challenges", []),
        "extracted_needs": state.get("extracted_needs", []),
        "challenges_iteration_count": state.get("challenges_iteration_count", 0),
        "maturity_score": state.get("maturity_score", 3),
        "maturity_summary": state.get("maturity_summary", ""),
        "recommendations": state.get("recommendations", []),
        "validated_recommendations": state.get("validated_recommendations", []),
        "workflow_paused": state.get("workflow_paused", False),
        "validation_type": state.get("validation_type", "")
    }


@app.post("/executive-summary/threads/{thread_id}/validate")
async def validate_executive(thread_id: str, feedback: ExecutiveValidationFeedback):
    """Valide les enjeux ou recommandations"""
    if thread_id not in executive_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    workflow_data = executive_workflows[thread_id]
    workflow = workflow_data["workflow"]
    
    # Injecter le feedback dans l'état
    import time
    api_start_time = time.time()
    print(f"⏱️ [TIMING] validate_executive - DÉBUT ({time.strftime('%H:%M:%S.%f', time.localtime(api_start_time))[:-3]})")
    
    config = {"configurable": {"thread_id": thread_id}}
    get_state_start = time.time()
    current_state = workflow.graph.get_state(config)
    get_state_duration = time.time() - get_state_start
    print(f"⏱️ [TIMING] get_state: {get_state_duration:.3f}s")
    
    # Mettre à jour avec le feedback
    update_start = time.time()
    updated_state = current_state.values.copy()
    updated_state["validation_result"] = feedback.validation_result
    updated_state["validation_type"] = feedback.validation_type
    
    # Reprendre le workflow
    workflow.graph.update_state(config, updated_state)
    update_duration = time.time() - update_start
    print(f"⏱️ [TIMING] update_state: {update_duration:.3f}s")
    
    # Continuer l'exécution jusqu'au prochain interrupt
    stream_start = time.time()
    final_state = None
    for chunk in workflow.graph.stream(None, config):
        print(f"📊 [EXECUTIVE] Chunk reçu après validation: {list(chunk.keys())}")
        for node_name, node_state in chunk.items():
            print(f"  • Nœud '{node_name}' exécuté")
            final_state = node_state
    
    stream_duration = time.time() - stream_start
    print(f"⏱️ [TIMING] workflow.graph.stream: {stream_duration:.3f}s")
    
    # Récupérer l'état complet depuis le checkpointer après l'exécution
    # IMPORTANT : Le workflow s'arrête à human_validation_enjeux grâce à interrupt_before
    get_state_after_start = time.time()
    snapshot = workflow.graph.get_state(config)
    get_state_after_duration = time.time() - get_state_after_start
    print(f"⏱️ [TIMING] get_state (après stream): {get_state_after_duration:.3f}s")
    
    if snapshot and snapshot.values:
        state = snapshot.values
        workflow_data["state"] = state
        
        # Vérifier si on est à un interrupt (workflow_paused ou next contient human_validation)
        is_at_interrupt = False
        if snapshot.next:
            next_nodes = list(snapshot.next) if hasattr(snapshot.next, '__iter__') else [snapshot.next]
            if "human_validation_enjeux" in next_nodes or "human_validation_recommendations" in next_nodes:
                is_at_interrupt = True
                state["workflow_paused"] = True
                if "human_validation_enjeux" in next_nodes:
                    state["validation_type"] = "challenges"
                elif "human_validation_recommendations" in next_nodes:
                    state["validation_type"] = "recommendations"
                # Mettre à jour l'état dans le checkpointer
                workflow.graph.update_state(config, state)
                print(f"🛑 [API] Workflow arrêté à l'interrupt: {next_nodes}")
        
        # Mettre à jour le statut
        if state.get("workflow_paused") or is_at_interrupt:
            validation_type = state.get("validation_type", "")
            if validation_type == "challenges":
                workflow_data["status"] = "waiting_validation_challenges"
            elif validation_type == "recommendations":
                workflow_data["status"] = "waiting_validation_recommendations"
            else:
                workflow_data["status"] = "paused"
        elif state.get("challenges_success") and state.get("recommendations_success"):
            workflow_data["status"] = "completed"
        else:
            workflow_data["status"] = "running"
    elif final_state:
        workflow_data["state"] = final_state
        workflow_data["status"] = "running"
    
    total_duration = time.time() - api_start_time
    print(f"⏱️ [TIMING] validate_executive (total): {total_duration:.3f}s")
    
    return {"status": "success", "workflow_status": workflow_data["status"]}


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=2025,
        log_level="info"
    )

