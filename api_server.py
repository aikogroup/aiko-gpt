"""
Serveur API FastAPI pour câbler le frontend avec client.py
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import os
from typing import List, Dict, Any, Optional
import uuid
from langgraph_sdk import get_client
from langgraph_cli.exec import Runner

# Import des fonctions de client.py
from client import (
    get_langgraph_client,
    create_thread_and_dispatch,
    human_validation,
    use_case_validation
)

app = FastAPI(title="aikoGPT API", version="1.0.0")

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Stockage temporaire des threads (en production, utiliser une base de données)
active_threads: Dict[str, Dict[str, Any]] = {}

@app.get("/")
async def root():
    return {"message": "aikoGPT API Server", "status": "running"}

@app.post("/threads")
async def create_thread(request: Dict[str, Any]):
    """
    Crée un nouveau thread et démarre le workflow
    """
    try:
        client = get_langgraph_client()
        
        # Extraire les données de la requête
        input_data = request.get("input", {})
        company_name = input_data.get("company_info", {}).get("company_name", "")
        workshop_files = input_data.get("workshop_files", [])
        transcript_files = input_data.get("transcript_files", [])
        
        # Démarrer le workflow avec les fonctions de client.py
        with Runner() as runner:
            thread_id, state = await runner.run(
                create_thread_and_dispatch(
                    client,
                    company_name,
                    workshop_files,
                    transcript_files
                )
            )
        
        # Stocker les informations du thread
        active_threads[thread_id] = {
            "thread_id": thread_id,
            "state": state,
            "status": "running"
        }
        
        return {
            "thread_id": thread_id,
            "status": "created",
            "state": state
        }
        
    except Exception as e:
        print(f"Error in create_thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str):
    """
    Récupère l'état actuel d'un thread
    """
    try:
        if thread_id not in active_threads:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        thread_info = active_threads[thread_id]
        return {
            "thread_id": thread_id,
            "state": thread_info["state"],
            "status": thread_info["status"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/threads/{thread_id}/state")
async def update_thread_state(
    thread_id: str,
    values: Dict[str, Any]
):
    """
    Met à jour l'état d'un thread (pour la validation)
    """
    try:
        if thread_id not in active_threads:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Mettre à jour l'état local
        active_threads[thread_id]["state"].update(values)
        
        # Utiliser le client LangGraph pour mettre à jour l'état distant
        client = get_langgraph_client()
        
        # Simuler la mise à jour de l'état via l'API LangGraph
        # (Dans un vrai setup, on utiliserait l'API LangGraph)
        
        return {
            "thread_id": thread_id,
            "status": "updated",
            "values": values
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/threads/{thread_id}/validate-needs")
async def validate_needs(
    thread_id: str,
    validated_needs: List[Dict[str, Any]],
    rejected_needs: List[Dict[str, Any]],
    user_feedback: str
):
    """
    Valide les besoins identifiés
    """
    try:
        if thread_id not in active_threads:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        client = get_langgraph_client()
        
        # Utiliser la fonction de validation du client.py
        with Runner() as runner:
            result = await runner.run(
                human_validation(
                    client,
                    thread_id,
                    validated_needs,
                    rejected_needs,
                    [user_feedback]
                )
            )
        
        # Mettre à jour l'état local
        active_threads[thread_id]["state"] = result
        
        return {
            "thread_id": thread_id,
            "status": "validated",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/threads/{thread_id}/validate-use-cases")
async def validate_use_cases(
    thread_id: str,
    validated_quick_wins: List[Dict[str, Any]],
    validated_structuration_ia: List[Dict[str, Any]],
    rejected_quick_wins: List[Dict[str, Any]],
    rejected_structuration_ia: List[Dict[str, Any]],
    user_feedback: str
):
    """
    Valide les cas d'usage
    """
    try:
        if thread_id not in active_threads:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        client = get_langgraph_client()
        
        # Utiliser la fonction de validation des use cases du client.py
        with Runner() as runner:
            result = await runner.run(
                use_case_validation(
                    client,
                    thread_id,
                    validated_quick_wins,
                    validated_structuration_ia,
                    rejected_quick_wins,
                    rejected_structuration_ia,
                    user_feedback
                )
            )
        
        # Mettre à jour l'état local
        active_threads[thread_id]["state"] = result
        
        return {
            "thread_id": thread_id,
            "status": "validated",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/threads/{thread_id}/download")
async def download_report(thread_id: str):
    """
    Télécharge le rapport final
    """
    try:
        if thread_id not in active_threads:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Pour l'instant, retourner un message
        # Dans un vrai setup, on générerait le rapport
        return {
            "message": "Rapport en cours de génération",
            "thread_id": thread_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Vérification de l'état du serveur
    """
    return {"status": "healthy", "active_threads": len(active_threads)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=2024)
