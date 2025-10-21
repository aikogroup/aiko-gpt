from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import uuid
import os
from typing import List, Dict, Any

try:
    # SDK pour interagir avec le serveur LangGraph en processus (ASGI) ou via URL
    from langgraph_sdk import get_sync_client
except Exception:  # pragma: no cover
    get_sync_client = None  # type: ignore

from utils.report_generator import ReportGenerator


# Dossier partagé via volume Docker (nommé "uploads")
UPLOAD_DIR = Path("/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


app = FastAPI(title="aiko - HTTP App (uploads & report)")


@app.post("/files/upload")
async def upload_files(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    try:
        saved_paths: List[str] = []
        workshop_files: List[str] = []
        transcript_files: List[str] = []

        for f in files:
            file_id = str(uuid.uuid4())
            ext = Path(f.filename).suffix or ""
            out_path = UPLOAD_DIR / f"{file_id}_{f.filename}"
            content = await f.read()
            with open(out_path, "wb") as w:
                w.write(content)

            saved_paths.append(str(out_path))
            if ext.lower() == ".xlsx":
                workshop_files.append(str(out_path))
            elif ext.lower() == ".pdf":
                transcript_files.append(str(out_path))

        return {
            "file_paths": saved_paths,
            "file_types": {
                "workshop": workshop_files,
                "transcript": transcript_files,
            },
            "count": len(saved_paths),
        }
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Erreur upload: {e}")


@app.get("/report")
def generate_report(thread_id: str) -> FileResponse:
    if get_sync_client is None:
        raise HTTPException(status_code=500, detail="SDK LangGraph indisponible")

    try:
        client = get_sync_client()  # Détection auto (ASGI / HTTP)
        state = client.threads.get_state(thread_id)

        values = state.get("values") or {}
        company_name = ((values.get("company_info") or {}).get("company_name")) or "Entreprise"
        final_needs = (
            values.get("validated_needs")
            or values.get("final_needs")
            or []
        )
        final_qw = (
            values.get("validated_quick_wins")
            or values.get("final_quick_wins")
            or []
        )
        final_sia = (
            values.get("validated_structuration_ia")
            or values.get("final_structuration_ia")
            or []
        )

        generator = ReportGenerator()
        output_path = generator.generate_report(
            company_name=company_name,
            final_needs=final_needs,
            final_quick_wins=final_qw,
            final_structuration_ia=final_sia,
            output_dir=str(UPLOAD_DIR),
        )

        filename = os.path.basename(output_path)
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Erreur génération rapport: {e}")


