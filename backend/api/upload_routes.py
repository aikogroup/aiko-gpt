"""
Upload Routes - Endpoints pour l'upload de fichiers

FR: Routes HTTP pour gérer l'upload des fichiers Excel et PDF/JSON
"""

import asyncio
import logging
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import aiofiles

logger = logging.getLogger(__name__)

# FR: Créer le routeur
router = APIRouter(prefix="/api", tags=["upload"])

# FR: Dossier de destination pour les fichiers uploadés
UPLOAD_DIR = Path("/app/temp/uploads")


class UploadResponse(BaseModel):
    """FR: Réponse de l'endpoint d'upload"""
    excel_file_path: str
    pdf_json_file_paths: List[str]
    company_name: str
    thread_id: str


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    excel: UploadFile = File(..., description="Fichier Excel des ateliers"),
    company_name: str = Form(..., description="Nom de l'entreprise"),
    pdf_json_0: UploadFile = File(None),
    pdf_json_1: UploadFile = File(None),
    pdf_json_2: UploadFile = File(None),
    pdf_json_3: UploadFile = File(None),
    pdf_json_4: UploadFile = File(None),
):
    """
    FR: Upload les fichiers et retourne leurs chemins

    Args:
        excel: Fichier Excel (.xlsx)
        company_name: Nom de l'entreprise
        pdf_json_X: Fichiers PDF ou JSON (max 5)

    Returns:
        UploadResponse: Chemins des fichiers sauvegardés
    """
    logger.info(f"📤 Upload de fichiers pour l'entreprise: {company_name}")

    try:
        # FR: Générer un ID de thread unique
        import time
        thread_id = f"thread-{int(time.time())}"
        thread_upload_dir = UPLOAD_DIR / thread_id
        
        # FR: Créer le dossier de manière asynchrone
        await asyncio.to_thread(thread_upload_dir.mkdir, parents=True, exist_ok=True)

        # FR: Sauvegarder le fichier Excel de manière asynchrone
        excel_path = thread_upload_dir / excel.filename
        content = await excel.read()
        async with aiofiles.open(excel_path, "wb") as f:
            await f.write(content)
        logger.info(f"✅ Excel sauvegardé: {excel_path}")

        # FR: Sauvegarder les fichiers PDF/JSON de manière asynchrone
        pdf_json_files = [pdf_json_0, pdf_json_1, pdf_json_2, pdf_json_3, pdf_json_4]
        pdf_json_paths = []

        for pdf_json in pdf_json_files:
            if pdf_json and pdf_json.filename:
                file_path = thread_upload_dir / pdf_json.filename
                content = await pdf_json.read()
                async with aiofiles.open(file_path, "wb") as f:
                    await f.write(content)
                pdf_json_paths.append(str(file_path))
                logger.info(f"✅ Fichier sauvegardé: {file_path}")

        if not pdf_json_paths:
            raise HTTPException(
                status_code=400,
                detail="Au moins un fichier PDF ou JSON est requis"
            )

        logger.info(f"✅ Upload terminé: {len(pdf_json_paths)} fichiers PDF/JSON")

        return UploadResponse(
            excel_file_path=str(excel_path),
            pdf_json_file_paths=pdf_json_paths,
            company_name=company_name,
            thread_id=thread_id,
        )

    except Exception as e:
        logger.error(f"❌ Erreur lors de l'upload: {e}")
        raise HTTPException(status_code=500, detail=str(e))

