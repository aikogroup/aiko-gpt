"""
API LangGraph pour le workflow d'analyse des besoins.
Architecture propre : Streamlit = UI, API = Logique métier.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
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

# Importer le workflow
import sys
sys.path.append(str(Path(__file__).parent.parent))
from workflow.need_analysis_workflow import NeedAnalysisWorkflow
from langgraph.checkpoint.memory import MemorySaver
from utils.report_generator import ReportGenerator

# Initialisation de l'API
app = FastAPI(
    title="AIKO - LangGraph API",
    description="API pour le workflow d'analyse des besoins IA",
    version="1.0.0"
)

# CORS pour Next.js (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage en mémoire des workflows (en production, utiliser Redis ou DB)
workflows: Dict[str, Any] = {}
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


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "AIKO LangGraph API",
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
            elif file_extension == ".pdf":
                transcript_files.append(str(file_path))
        
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
        
        # Exécuter le workflow (mode asynchrone géré par LangGraph)
        result = workflow.run(
            workshop_files=workflow_input.workshop_files,
            transcript_files=workflow_input.transcript_files,
            company_info={"company_name": workflow_input.company_name} if workflow_input.company_name else {},
            thread_id=thread_id
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
    Récupère l'état actuel du workflow depuis le checkpointer (état à jour).
    
    Returns:
        {
            "thread_id": "uuid",
            "status": "running" | "paused" | "completed",
            "values": {...},  # État complet depuis checkpointer
            "next": ["node_name"] | []  # Prochain nœud ou vide si terminé
        }
    """
    if thread_id not in workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    try:
        workflow_data = workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        # Lire l'état à jour depuis le checkpointer
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = workflow.graph.get_state(config)
        state = snapshot.values
        next_nodes = list(snapshot.next) if snapshot.next else []
        
        # Mettre à jour le cache local avec l'état à jour
        workflow_data["state"] = state
        
        # Déterminer le statut en fonction de l'état
        status = workflow_data["status"]
        if state.get("use_case_workflow_paused"):
            status = "paused"
        elif state.get("workflow_paused"):
            status = "paused"
        elif state.get("success"):
            status = "completed"
        elif next_nodes:
            status = "paused"
        
        workflow_data["status"] = status
        
        return {
            "thread_id": thread_id,
            "status": status,
            "values": state,
            "next": next_nodes,
            # Exposer aussi au niveau racine pour compatibilité frontend
            "validated_needs": state.get("validated_needs", []),
            "validated_quick_wins": state.get("validated_quick_wins", []),
            "validated_structuration_ia": state.get("validated_structuration_ia", [])
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur get_state: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération état: {str(e)}")


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
        
        # Lire l'état à jour depuis le checkpointer après reprise
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = workflow.graph.get_state(config)
        state = snapshot.values
        next_nodes = list(snapshot.next) if snapshot.next else []
        
        # Mettre à jour le cache local avec l'état à jour
        workflow_data["state"] = state
        
        # Déterminer le statut en fonction de l'état
        if state.get("use_case_workflow_paused"):
            workflow_data["status"] = "paused"
        elif state.get("workflow_paused"):
            workflow_data["status"] = "paused"
        elif state.get("success"):
            workflow_data["status"] = "completed"
        elif next_nodes:
            workflow_data["status"] = "paused"
        else:
            workflow_data["status"] = "completed"
        
        print(f"🔄 [API] État après validation: {workflow_data['status']}")
        print(f"📊 [API] validated_needs count: {len(state.get('validated_needs', []))}")
        
        return {
            "status": "resumed",
            "thread_id": thread_id,
            "workflow_status": workflow_data["status"],
            "validated_needs_count": len(state.get("validated_needs", []))
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
        
        # Lire l'état à jour depuis le checkpointer après reprise
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = workflow.graph.get_state(config)
        state = snapshot.values
        next_nodes = list(snapshot.next) if snapshot.next else []
        
        # Mettre à jour le cache local avec l'état à jour
        workflow_data["state"] = state
        
        # Déterminer le statut en fonction de l'état
        if state.get("success"):
            workflow_data["status"] = "completed"
        elif state.get("use_case_workflow_paused"):
            workflow_data["status"] = "paused"
        elif next_nodes:
            workflow_data["status"] = "paused"
        else:
            workflow_data["status"] = "completed"
        
        print(f"🔄 [API] État après validation use cases: {workflow_data['status']}")
        print(f"📊 [API] validated_quick_wins count: {len(state.get('validated_quick_wins', []))}")
        print(f"📊 [API] validated_structuration_ia count: {len(state.get('validated_structuration_ia', []))}")
        
        return {
            "status": workflow_data["status"],
            "thread_id": thread_id,
            "final_results": result,
            "success": result.get("success", False),
            "validated_quick_wins_count": len(state.get("validated_quick_wins", [])),
            "validated_structuration_ia_count": len(state.get("validated_structuration_ia", []))
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur reprise workflow: {str(e)}")


@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """
    Supprime un thread et nettoie les ressources.
    
    Returns:
        {"status": "deleted"}
    """
    if thread_id in workflows:
        del workflows[thread_id]
        return {"status": "deleted", "thread_id": thread_id}
    else:
        raise HTTPException(status_code=404, detail="Thread non trouvé")


@app.get("/threads/{thread_id}/report")
async def generate_report(thread_id: str):
    """
    Génère et renvoie un rapport Word basé sur l'état courant du workflow.
    Utilise prioritairement validated_* puis fallback sur final_*.
    """
    if thread_id not in workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    try:
        workflow = workflows[thread_id]["workflow"]
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = workflow.graph.get_state(config)
        state = snapshot.values

        company_name = (state.get("company_info", {}) or {}).get("company_name", "Entreprise")
        final_needs = state.get("validated_needs") or state.get("final_needs") or []
        final_qw = state.get("validated_quick_wins") or state.get("final_quick_wins") or []
        final_sia = state.get("validated_structuration_ia") or state.get("final_structuration_ia") or []

        generator = ReportGenerator()
        # Écrire dans /tmp pour portabilité
        output_path = generator.generate_report(
            company_name=company_name,
            final_needs=final_needs,
            final_quick_wins=final_qw,
            final_structuration_ia=final_sia,
            output_dir=str(UPLOAD_DIR)
        )
        filename = os.path.basename(output_path)
        return FileResponse(output_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération rapport: {str(e)}")


# ==================== DÉMARRAGE ====================

if __name__ == "__main__":
    print("🚀 Démarrage de l'API LangGraph AIKO...")
    print("📍 URL: http://localhost:2025")
    print("📖 Documentation: http://localhost:2025/docs")
    print("ℹ️  LangGraph Studio utilise le port 2024")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=2025,
        log_level="info"
    )

