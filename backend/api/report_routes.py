"""
Report Routes - Téléchargement du rapport généré

FR: Routes HTTP pour exposer les rapports Word produits via LangGraph.
"""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["report"])

OUTPUT_DIR = Path("/app/outputs").resolve()


@router.get("/report", response_class=FileResponse)
async def download_report(path: str = Query(..., description="Chemin absolu du rapport généré par LangGraph")):
    """
    FR: Permet de télécharger un rapport Word généré par le workflow.
    """
    requested_path = Path(path).resolve()

    if not requested_path.is_file():
        logger.error("❌ Rapport introuvable: %s", requested_path)
        raise HTTPException(status_code=404, detail="Rapport introuvable")

    try:
        requested_path.relative_to(OUTPUT_DIR)
    except ValueError:
        logger.error("❌ Accès refusé à %s (hors dossier outputs)", requested_path)
        raise HTTPException(status_code=403, detail="Accès non autorisé")

    logger.info("📥 Téléchargement du rapport: %s", requested_path)
    return FileResponse(
        requested_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=requested_path.name,
    )
