"""
Application principale - Serveur FastAPI avec routes custom

FR: Ce fichier définit l'application FastAPI qui sera utilisée par LangGraph Server
     pour ajouter des routes personnalisées (upload, etc.)
"""

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.upload_routes import router as upload_router

logger = logging.getLogger(__name__)

# FR: Créer l'application FastAPI
app = FastAPI(
    title="aikoGPT API",
    description="API pour l'analyse de besoins et génération de cas d'usage IA",
    version="1.0.0",
)

# FR: Configurer CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # FR: En production, restreindre aux domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FR: Inclure les routes d'upload
app.include_router(upload_router)

# FR: Route de santé custom
@app.get("/health")
async def health_check():
    """FR: Endpoint de santé pour vérifier que le serveur fonctionne"""
    return {"status": "healthy", "service": "aikoGPT"}


logger.info("✅ Application FastAPI initialisée avec routes custom")

