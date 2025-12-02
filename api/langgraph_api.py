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
from workflow.atouts_workflow import AtoutsWorkflow
from workflow.value_chain_workflow import ValueChainWorkflow
from executive_summary.executive_summary_workflow import ExecutiveSummaryWorkflow
from prerequis_evaluation.prerequis_evaluation_workflow import PrerequisEvaluationWorkflow
from langgraph.checkpoint.memory import MemorySaver
from process_transcript.pdf_parser import PDFParser
from process_transcript.json_parser import JSONParser
from process_transcript.speaker_classifier import SpeakerClassifier

# Importer les endpoints de base de données
from api.db_endpoints import router as db_router

# Initialisation de l'API
app = FastAPI(
    title="aiko - LangGraph API",
    description="API pour le workflow d'analyse des besoins IA",
    version="1.0.0"
)

# Middleware de logging pour toutes les requêtes
import logging
from fastapi import Request
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware pour logger toutes les requêtes"""
    start_time = time.time()
    
    # Logger la requête entrante
    logger.info(f"📥 {request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Logger la réponse
        logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.3f}s")
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"❌ {request.method} {request.url.path} - Error: {str(e)} - Time: {process_time:.3f}s")
        raise

# Inclure les endpoints de base de données
app.include_router(db_router)

# Logger tous les endpoints au démarrage
@app.on_event("startup")
async def startup_event():
    """Log tous les endpoints disponibles au démarrage"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append(f"{', '.join(route.methods)} {route.path}")
    
    logger.info("=" * 80)
    logger.info("🚀 API aiko démarrée - Endpoints disponibles:")
    for route in sorted(routes):
        logger.info(f"   {route}")
    logger.info("=" * 80)

# Stockage en mémoire des workflows (en production, utiliser Redis ou DB)
workflows: Dict[str, Any] = {}
executive_workflows: Dict[str, Any] = {}  # Workflows Executive Summary
rappel_workflows: Dict[str, Any] = {}  # Workflows Rappel de la mission
atouts_workflows: Dict[str, Any] = {}  # Workflows Atouts de l'entreprise
value_chain_workflows: Dict[str, Any] = {}  # Workflows Chaîne de valeur
prerequis_evaluation_workflows: Dict[str, Any] = {}  # Workflows Évaluation des prérequis
checkpointer = MemorySaver()

# Dossier temporaire pour les fichiers uploadés
UPLOAD_DIR = Path("/tmp/aiko_uploads")
# Créer le dossier avec les bonnes permissions
UPLOAD_DIR.mkdir(exist_ok=True, mode=0o755)
# Vérifier que le dossier existe et est accessible en écriture
if not UPLOAD_DIR.exists():
    raise RuntimeError(f"Impossible de créer le dossier d'upload: {UPLOAD_DIR}")
if not os.access(UPLOAD_DIR, os.W_OK):
    raise RuntimeError(f"Le dossier d'upload n'est pas accessible en écriture: {UPLOAD_DIR}")
print(f"✅ Dossier d'upload initialisé: {UPLOAD_DIR} (existe: {UPLOAD_DIR.exists()}, accessible: {os.access(UPLOAD_DIR, os.W_OK)})")


# ==================== MODÈLES PYDANTIC ====================

class WorkflowInput(BaseModel):
    """Input pour démarrer un workflow"""
    workshop_document_ids: List[int] = []
    transcript_document_ids: List[int] = []
    company_name: Optional[str] = None
    company_url: Optional[str] = None
    company_description: Optional[str] = None
    validated_company_info: Optional[Dict[str, Any]] = None
    interviewer_names: Optional[List[str]] = None
    additional_context: Optional[str] = ""

class ValidationFeedback(BaseModel):
    """Feedback de validation utilisateur"""
    validated_needs: List[Dict[str, Any]]
    rejected_needs: List[Dict[str, Any]]
    user_feedback: str = ""
    user_action: str = "continue_needs"  # "continue_needs" ou "continue_to_use_cases"

class PreUseCaseContextInput(BaseModel):
    """Input pour le contexte additionnel avant génération des use cases"""
    use_case_additional_context: str = ""

class UseCaseValidationFeedback(BaseModel):
    """Feedback de validation des use cases"""
    validated_use_cases: List[Dict[str, Any]]
    rejected_use_cases: List[Dict[str, Any]]
    user_feedback: str = ""
    use_case_user_action: str = "finalize_use_cases"  # "continue_use_cases" ou "finalize_use_cases"

class ExecutiveSummaryInput(BaseModel):
    """Input pour démarrer un workflow Executive Summary"""
    transcript_document_ids: List[int] = []
    workshop_document_ids: List[int] = []
    company_name: str
    interviewer_note: str = ""
    validated_needs: Optional[List[Dict[str, Any]]] = None
    validated_use_cases: Optional[List[Dict[str, Any]]] = None


class RappelMissionInput(BaseModel):
    """Input pour démarrer un workflow de rappel de mission"""

    company_name: str
    validated_company_info: Optional[Dict[str, Any]] = None


class AtoutsEntrepriseInput(BaseModel):
    """Input pour démarrer un workflow d'extraction des atouts"""
    transcript_document_ids: List[int]  # IDs des documents transcripts dans la DB
    company_info: Dict[str, Any]
    interviewer_names: Optional[List[str]] = None
    atouts_additional_context: Optional[str] = ""
    validated_speakers: Optional[List[Dict[str, str]]] = None


class PreAtoutContextInput(BaseModel):
    """Input pour le contexte additionnel avant génération des atouts"""
    atouts_additional_context: str = ""


class AtoutsValidationFeedback(BaseModel):
    """Feedback de validation des atouts"""
    validated_atouts: List[Dict[str, Any]]
    rejected_atouts: List[Dict[str, Any]]
    user_feedback: str = ""
    atouts_user_action: str = "finalize_atouts"  # "continue_atouts" ou "finalize_atouts"


class ValueChainInput(BaseModel):
    """Input pour démarrer un workflow d'extraction de la chaîne de valeur"""
    transcript_document_ids: List[int]  # IDs des documents transcripts dans la DB
    company_info: Dict[str, Any]


class ValueChainValidationFeedback(BaseModel):
    """Feedback de validation de la chaîne de valeur"""
    validation_type: str  # "teams", "activities", "friction_points"
    validated_items: List[Dict[str, Any]]
    rejected_items: List[Dict[str, Any]]
    user_action: str  # "continue_teams", "continue_to_activities", "continue_activities", "continue_to_friction", "continue_friction", "finalize"


class PrerequisEvaluationInput(BaseModel):
    """Input pour démarrer un workflow d'évaluation des prérequis"""
    transcript_document_ids: List[int]  # IDs des documents transcripts dans la DB
    company_info: Dict[str, Any]
    validated_use_cases: List[Dict[str, Any]]  # Cas d'usage validés (obligatoire)
    comments: Optional[Dict[str, str]] = None  # Commentaires (comment_general, comment_1 à comment_5)


class PrerequisValidationFeedback(BaseModel):
    """Feedback de validation des prérequis"""
    validated_prerequis: List[int]  # Liste des IDs des prérequis validés (1 à 5)
    regeneration_comment: str = ""  # Commentaire pour la régénération des prérequis non validés
    comments: Optional[Dict[str, str]] = None  # Commentaires (comment_general, comment_1 à comment_5)
    modified_evaluations: Optional[Dict[int, Dict[str, Any]]] = None  # Modifications des prérequis validés (prerequis_id -> {note, evaluation_text})


class ExecutiveValidationFeedback(BaseModel):
    """Feedback de validation Executive Summary"""
    validation_type: str  # "challenges" ou "recommendations"
    validation_result: Dict[str, Any]

class ClassifySpeakersInput(BaseModel):
    """Input pour classifier les speakers d'un transcript"""
    file_path: str
    interviewer_names: Optional[List[str]] = None
    known_speakers: Optional[Dict[str, str]] = None  # speaker_name -> role pour réutilisation


class WordExtractInput(BaseModel):
    """Input pour extraire les données d'un fichier Word"""
    word_path: str
    force_llm: bool = False  # Si True, force l'extraction via LLM


class ParseTranscriptInput(BaseModel):
    """Input pour parser et sauvegarder un transcript"""
    file_path: str
    project_id: int
    file_name: str
    validated_speakers: List[Dict[str, Any]]  # Liste des speakers validés
    metadata: Optional[Dict[str, Any]] = None


class ParseWorkshopInput(BaseModel):
    """Input pour parser et sauvegarder un workshop"""
    file_path: str
    project_id: int
    file_name: str
    metadata: Optional[Dict[str, Any]] = None


class ParseWordReportInput(BaseModel):
    """Input pour parser et sauvegarder un word report"""
    file_path: str
    project_id: int
    file_name: str
    metadata: Optional[Dict[str, Any]] = None


# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "aiko LangGraph API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check détaillé avec liste des endpoints disponibles"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods)
            })
    
    # Vérifier spécifiquement si l'endpoint classify-speakers existe
    classify_endpoint_exists = any(
        route.get("path") == "/transcripts/classify-speakers" 
        and "POST" in route.get("methods", [])
        for route in routes
    )
    
    return {
        "status": "healthy",
        "endpoints": routes,
        "classify_speakers_endpoint_exists": classify_endpoint_exists,
        "upload_dir": str(UPLOAD_DIR),
        "upload_dir_exists": UPLOAD_DIR.exists(),
        "upload_dir_writable": os.access(UPLOAD_DIR, os.W_OK) if UPLOAD_DIR.exists() else False
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
        # Vérifier que le dossier d'upload existe et est accessible
        if not UPLOAD_DIR.exists():
            UPLOAD_DIR.mkdir(exist_ok=True, mode=0o755)
            print(f"⚠️ Dossier d'upload recréé: {UPLOAD_DIR}")
        
        if not os.access(UPLOAD_DIR, os.W_OK):
            raise HTTPException(
                status_code=500, 
                detail=f"Le dossier d'upload n'est pas accessible en écriture: {UPLOAD_DIR}"
            )
        
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
            content_size = len(content)
            
            # Écrire le fichier
            with open(file_path, "wb") as f:
                f.write(content)
            
            # Vérifier que le fichier a bien été écrit
            if not file_path.exists():
                raise HTTPException(
                    status_code=500,
                    detail=f"Le fichier n'a pas pu être sauvegardé: {file_path}"
                )
            
            # Vérifier la taille du fichier écrit
            written_size = file_path.stat().st_size
            if written_size != content_size:
                raise HTTPException(
                    status_code=500,
                    detail=f"Taille du fichier incorrecte: attendu {content_size} octets, obtenu {written_size} octets"
                )
            
            print(f"✅ Fichier sauvegardé: {file_path} ({written_size} octets)")
            
            file_paths.append(str(file_path))
            
            # Classifier par type
            if file_extension == ".xlsx":
                workshop_files.append(str(file_path))
            elif file_extension in [".pdf", ".json"]:
                transcript_files.append(str(file_path))
            elif file_extension == ".docx":
                # Fichier Word pour Executive Summary
                workshop_files.append(str(file_path))  # Pour l'instant, on le met dans workshop_files
        
        print(f"✅ {len(file_paths)} fichier(s) uploadé(s) avec succès dans {UPLOAD_DIR}")
        
        return {
            "file_paths": file_paths,
            "file_types": {
                "workshop": workshop_files,
                "transcript": transcript_files
            },
            "count": len(file_paths)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erreur lors de l'upload: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur upload: {str(e)}")


@app.post("/transcripts/classify-speakers")
async def classify_speakers(input_data: ClassifySpeakersInput):
    """
    Classe les speakers d'un transcript et extrait leurs rôles
    
    Args:
        input_data: Contient file_path, interviewer_names (optionnel), et known_speakers (optionnel)
    
    Returns:
        {
            "speakers": [
                {"name": "...", "role": "...", "level": "direction"|"métier"|"inconnu"|None, "is_interviewer": bool},
                ...
            ]
        }
    """
    logger.info(f"🔍 [classify-speakers] Début de la classification - file_path: {input_data.file_path}")
    try:
        file_path = input_data.file_path
        
        # DEBUG: Vérifier si le chemin contient aiko_uploads_local au lieu de aiko_uploads
        if "aiko_uploads_local" in file_path:
            logger.warning(f"⚠️ [classify-speakers] Chemin contient 'aiko_uploads_local', correction automatique")
            file_path = file_path.replace("/tmp/aiko_uploads_local", "/tmp/aiko_uploads")
            logger.info(f"🔧 [classify-speakers] Chemin corrigé: {file_path}")
        
        # Vérifier que le fichier existe
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            logger.error(f"❌ [classify-speakers] Fichier non trouvé: {file_path}")
            # Essayer de trouver le fichier dans aiko_uploads si on cherchait dans aiko_uploads_local
            if "aiko_uploads_local" in str(input_data.file_path):
                alternative_path = str(input_data.file_path).replace("/tmp/aiko_uploads_local", "/tmp/aiko_uploads")
                logger.info(f"🔍 [classify-speakers] Tentative avec chemin alternatif: {alternative_path}")
                if Path(alternative_path).exists():
                    file_path = alternative_path
                    file_path_obj = Path(file_path)
                    logger.info(f"✅ [classify-speakers] Fichier trouvé avec chemin alternatif")
                else:
                    raise HTTPException(status_code=404, detail=f"Fichier non trouvé: {file_path}")
            else:
                raise HTTPException(status_code=404, detail=f"Fichier non trouvé: {file_path}")
        logger.info(f"✅ [classify-speakers] Fichier trouvé: {file_path} ({file_path_obj.stat().st_size} octets)")
        
        # Initialiser les parsers et le classificateur
        pdf_parser = PDFParser()
        json_parser = JSONParser()
        
        interviewer_names = input_data.interviewer_names or ["Christella Umuhoza", "Adrien Fabry"]
        speaker_classifier = SpeakerClassifier(
            api_key=os.getenv("OPENAI_API_KEY"),
            interviewer_names=interviewer_names
        )
        
        # Parser le transcript selon son type
        file_extension = Path(file_path).suffix.lower()
        if file_extension == '.json':
            interventions = json_parser.parse_transcript(file_path)
        elif file_extension == '.pdf':
            interventions = pdf_parser.parse_transcript(file_path)
        else:
            raise HTTPException(status_code=400, detail=f"Format de fichier non supporté: {file_extension}")
        
        if not interventions:
            return {"speakers": []}
        
        # Identifier les interviewers (par matching de noms)
        interviewer_names_set = speaker_classifier._identify_interviewers(interventions)
        
        # Construire le dictionnaire de rôles connus
        known_roles = input_data.known_speakers or {}
        
        # Pour JSON : extraire directement les speaker_name uniques et utiliser extract_roles_for_json_speakers
        # Pour PDF : utiliser identify_and_extract_speakers_with_roles (identification + extraction rôles)
        if file_extension == '.json':
            # Extraire directement les speaker_name uniques du JSON
            json_speakers = list(set(
                interv.get("speaker", "") 
                for interv in interventions 
                if interv.get("speaker")
            ))
            
            logger.info(f"🔍 [classify-speakers] Extraction rôles pour {len(json_speakers)} speakers JSON")
            
            # Utiliser la nouvelle fonction qui n'identifie pas les speakers (déjà fait par le JSON)
            speakers_list = speaker_classifier.extract_roles_for_json_speakers(
                json_speakers=json_speakers,
                interventions=interventions,
                interviewer_names_set=interviewer_names_set,
                known_roles=known_roles
            )
        else:
            # Pour PDF : extraire TOUS les speakers uniques et identifier les vrais speakers
            all_speakers = list(set(
                interv.get("speaker", "") 
                for interv in interventions 
                if interv.get("speaker")
            ))
            
            logger.info(f"🔍 [classify-speakers] Classification de {len(all_speakers)} speakers uniques (PDF)")
            
            # Utiliser la fonction qui identifie ET extrait les rôles
            speakers_list = speaker_classifier.identify_and_extract_speakers_with_roles(
                all_speakers=all_speakers,
                interventions=interventions,
                interviewer_names_set=interviewer_names_set,
                known_roles=known_roles
            )
        
        logger.info(f"✅ [classify-speakers] Classification terminée - {len(speakers_list)} speakers identifiés")
        return {"speakers": speakers_list}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [classify-speakers] Erreur lors de la classification: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur classification: {str(e)}")


@app.post("/word/extract")
async def extract_word_data(input_data: WordExtractInput):
    """
    Extrait les besoins et cas d'usage depuis un fichier Word.
    
    Args:
        input_data: Contient word_path (chemin vers le fichier .docx) et force_llm (optionnel)
    
    Returns:
        {
            "final_needs": [
                {"titre": "...", "description": "..."},
                ...
            ],
            "final_use_cases": [
                {"titre": "...", "description": "...", "famille": "..."},
                ...
            ],
            "extraction_method": "structured" | "llm_fallback" | "llm_forced"
        }
    """
    try:
        word_path = input_data.word_path
        force_llm = input_data.force_llm
        
        # Vérifier que le fichier existe
        if not Path(word_path).exists():
            raise HTTPException(status_code=404, detail=f"Fichier non trouvé: {word_path}")
        
        # Importer et utiliser WordReportExtractor
        from executive_summary.word_report_extractor import WordReportExtractor
        
        extractor = WordReportExtractor()
        extracted_data = extractor.extract_from_word(word_path, force_llm=force_llm)
        
        return extracted_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [word/extract] Erreur lors de l'extraction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur extraction: {str(e)}")


@app.post("/documents/parse-transcript")
async def parse_and_save_transcript(input_data: ParseTranscriptInput):
    """
    Parse et sauvegarde un transcript dans la base de données.
    
    Args:
        input_data: Contient file_path, project_id, file_name, validated_speakers, metadata
    
    Returns:
        {"document_id": int}
    """
    try:
        logger.info(f"🔍 [parse-transcript] Début du parsing - file_path: {input_data.file_path}")
        
        # Importer DocumentParserService
        from database.document_parser_service import DocumentParserService
        
        parser_service = DocumentParserService()
        document_id = parser_service.parse_and_save_transcript(
            file_path=input_data.file_path,
            project_id=input_data.project_id,
            file_name=input_data.file_name,
            validated_speakers=input_data.validated_speakers,
            metadata=input_data.metadata
        )
        
        logger.info(f"✅ [parse-transcript] Document sauvegardé avec ID: {document_id}")
        return {"document_id": document_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [parse-transcript] Erreur lors du parsing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur parsing: {str(e)}")


@app.post("/documents/parse-workshop")
async def parse_and_save_workshop(input_data: ParseWorkshopInput):
    """
    Parse et sauvegarde un workshop dans la base de données.
    
    Args:
        input_data: Contient file_path, project_id, file_name, metadata
    
    Returns:
        {"document_id": int}
    """
    try:
        logger.info(f"🔍 [parse-workshop] Début du parsing - file_path: {input_data.file_path}")
        
        # Importer DocumentParserService
        from database.document_parser_service import DocumentParserService
        
        parser_service = DocumentParserService()
        document_id = parser_service.parse_and_save_workshop(
            file_path=input_data.file_path,
            project_id=input_data.project_id,
            file_name=input_data.file_name,
            metadata=input_data.metadata
        )
        
        logger.info(f"✅ [parse-workshop] Document sauvegardé avec ID: {document_id}")
        return {"document_id": document_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [parse-workshop] Erreur lors du parsing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur parsing: {str(e)}")


@app.post("/documents/parse-word-report")
async def parse_and_save_word_report(input_data: ParseWordReportInput):
    """
    Parse et sauvegarde un word report dans la base de données.
    
    Args:
        input_data: Contient file_path, project_id, file_name, metadata
    
    Returns:
        {"document_id": int}
    """
    try:
        logger.info(f"🔍 [parse-word-report] Début du parsing - file_path: {input_data.file_path}")
        
        # Importer DocumentParserService
        from database.document_parser_service import DocumentParserService
        
        parser_service = DocumentParserService()
        document_id = parser_service.parse_and_save_word_report(
            file_path=input_data.file_path,
            project_id=input_data.project_id,
            file_name=input_data.file_name,
            metadata=input_data.metadata
        )
        
        logger.info(f"✅ [parse-word-report] Document sauvegardé avec ID: {document_id}")
        return {"document_id": document_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [parse-word-report] Erreur lors du parsing: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Erreur parsing: {str(e)}")


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
            # Vérifier si DEV_MODE est activé
            dev_mode = os.getenv("DEV_MODE", "0") == "1"
            workflow = NeedAnalysisWorkflow(
                api_key=api_key,
                dev_mode=dev_mode  # Activer dev_mode si DEV_MODE=1
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
        print(f"📁 Workshop document IDs: {workflow_input.workshop_document_ids}")
        print(f"📁 Transcript document IDs: {workflow_input.transcript_document_ids}")
        print(f"🏢 Company: {workflow_input.company_name}")
        if workflow_input.company_url:
            print(f"🌐 Company URL: {workflow_input.company_url}")
        if workflow_input.company_description:
            print(f"📄 Company Description: {workflow_input.company_description}")
        print(f"👥 Interviewers: {workflow_input.interviewer_names}")
        print(f"📝 Additional context: {len(workflow_input.additional_context or '')} caractères")
        
        # Construire company_info avec tous les champs disponibles
        # Si validated_company_info est fourni, l'utiliser directement
        if workflow_input.validated_company_info:
            company_info = workflow_input.validated_company_info
        else:
            # Sinon, construire à partir des champs individuels (rétrocompatibilité)
            company_info = {}
            if workflow_input.company_name:
                company_info["company_name"] = workflow_input.company_name
            if workflow_input.company_url:
                company_info["company_url"] = workflow_input.company_url
            if workflow_input.company_description:
                company_info["company_description"] = workflow_input.company_description
        
        # Exécuter le workflow (mode asynchrone géré par LangGraph)
        result = workflow.run(
            workshop_document_ids=workflow_input.workshop_document_ids,
            transcript_document_ids=workflow_input.transcript_document_ids,
            company_info=company_info,
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
    Utilise le snapshot LangGraph pour déterminer le vrai prochain nœud.
    
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
    workflow = workflow_data["workflow"]
    
    # Récupérer l'état actuel depuis le checkpointer LangGraph
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = workflow.graph.get_state(config)
    
    if snapshot and snapshot.values:
        state = snapshot.values
        workflow_data["state"] = state
        
        # Déterminer le prochain nœud depuis le snapshot LangGraph
        next_nodes = []
        if snapshot.next:
            if isinstance(snapshot.next, (list, tuple)):
                next_nodes = list(snapshot.next)
            else:
                next_nodes = [snapshot.next]
        
        # Mettre à jour le statut en fonction du prochain nœud
        if "human_validation" in next_nodes:
            workflow_data["status"] = "paused"
        elif "pre_use_case_interrupt" in next_nodes:
            workflow_data["status"] = "paused"
        elif "validate_use_cases" in next_nodes:
            workflow_data["status"] = "paused"
        elif len(next_nodes) == 0:
            workflow_data["status"] = "completed"
        else:
            workflow_data["status"] = "running"
        
        return {
            "thread_id": thread_id,
            "status": workflow_data["status"],
            "values": state,
            "next": tuple(next_nodes) if next_nodes else []
        }
    else:
        # Fallback si pas de snapshot
        state = workflow_data.get("state", {})
        return {
            "thread_id": thread_id,
            "status": workflow_data.get("status", "paused"),
            "values": state,
            "next": []
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
        print(f"🎯 Action utilisateur: {feedback.user_action}")
        
        # Reprendre le workflow avec le feedback
        result = workflow.resume_workflow_with_feedback(
            validated_needs=feedback.validated_needs,
            rejected_needs=feedback.rejected_needs,
            user_feedback=feedback.user_feedback,
            user_action=feedback.user_action,
            thread_id=thread_id
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        
        # Récupérer le snapshot LangGraph pour déterminer le vrai statut
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = workflow.graph.get_state(config)
        
        if snapshot and snapshot.next:
            next_nodes = list(snapshot.next) if isinstance(snapshot.next, (list, tuple)) else [snapshot.next]
            
            # Mettre à jour le statut en fonction du prochain nœud réel
            if "pre_use_case_interrupt" in next_nodes:
                workflow_data["status"] = "paused"  # Va s'arrêter à pre_use_case_interrupt
            elif "human_validation" in next_nodes:
                workflow_data["status"] = "paused"  # Va s'arrêter à human_validation
            elif len(next_nodes) == 0:
                workflow_data["status"] = "completed"
            else:
                workflow_data["status"] = "running"
        else:
            # Fallback : déterminer le statut selon l'action utilisateur
            if feedback.user_action == "continue_to_use_cases":
                workflow_data["status"] = "paused"  # Va s'arrêter à pre_use_case_interrupt
            else:
                workflow_data["status"] = "paused"  # Va continuer avec analyze_needs
        
        return {
            "status": "resumed",
            "thread_id": thread_id,
            "workflow_status": workflow_data["status"]
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur reprise workflow: {str(e)}")


@app.post("/threads/{thread_id}/pre-use-case-context")
async def send_pre_use_case_context(thread_id: str, context_input: PreUseCaseContextInput):
    """
    Envoie le contexte additionnel avant la génération des use cases et reprend le workflow.
    
    Args:
        thread_id: ID du thread
        context_input: Contexte additionnel
    
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
        
        print(f"\n📝 [API] Réception du contexte additionnel pour thread {thread_id}")
        print(f"💡 Contexte: {len(context_input.use_case_additional_context)} caractères")
        
        # Reprendre le workflow avec le contexte
        result = workflow.resume_pre_use_case_interrupt_with_context(
            use_case_additional_context=context_input.use_case_additional_context,
            thread_id=thread_id
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        workflow_data["status"] = "running"  # Le workflow va générer les use cases
        
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
        print(f"✅ Cas d'usage validés: {len(feedback.validated_use_cases)}")
        print(f"🎯 Action: {feedback.use_case_user_action}")
        
        # Reprendre le workflow avec le feedback
        result = workflow.resume_use_case_workflow_with_feedback(
            validated_use_cases=feedback.validated_use_cases,
            rejected_use_cases=feedback.rejected_use_cases,
            user_feedback=feedback.user_feedback,
            use_case_user_action=feedback.use_case_user_action,
            thread_id=thread_id
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        
        # Déterminer le statut selon l'action utilisateur
        if feedback.use_case_user_action == "finalize_use_cases":
            workflow_data["status"] = "completed"
        else:
            workflow_data["status"] = "paused"  # Va continuer avec analyze_use_cases
        
        return {
            "status": workflow_data["status"],
            "thread_id": thread_id,
            "final_results": result,
            "success": result.get("success", False),
            "workflow_status": workflow_data["status"]
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

        result = workflow.run(
            company_name=mission_input.company_name,
            validated_company_info=mission_input.validated_company_info,
            thread_id=thread_id
        )

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


@app.post("/atouts-entreprise/threads/{thread_id}/runs")
async def create_atouts_run(thread_id: str, atouts_input: AtoutsEntrepriseInput):
    """Démarre un workflow d'extraction des atouts de l'entreprise"""
    try:
        if thread_id not in atouts_workflows:
            workflow = AtoutsWorkflow(
                interviewer_names=atouts_input.interviewer_names,
                checkpointer=checkpointer
            )
            atouts_workflows[thread_id] = {
                "workflow": workflow,
                "state": None,
                "status": "created"
            }
        
        workflow_data = atouts_workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n🚀 [API] Démarrage workflow Atouts pour thread {thread_id}")
        print(f"📁 Documents: {len(atouts_input.transcript_document_ids)}")
        print(f"🏢 Entreprise: {atouts_input.company_info.get('nom', 'N/A')}")
        print(f"📝 Contexte additionnel: {len(atouts_input.atouts_additional_context)} caractères")
        
        # Exécuter le workflow avec le contexte additionnel
        result = workflow.run(
            transcript_document_ids=atouts_input.transcript_document_ids,
            company_info=atouts_input.company_info,
            thread_id=thread_id,
            atouts_additional_context=atouts_input.atouts_additional_context,
            validated_speakers=atouts_input.validated_speakers
        )
        
        workflow_data["state"] = result
        workflow_data["status"] = "paused" if result.get("atouts_workflow_paused") else ("completed" if result.get("success") else "error")
        
        return {
            "thread_id": thread_id,
            "status": workflow_data["status"],
            "result": result
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur Atouts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur workflow atouts: {str(e)}")


@app.get("/atouts-entreprise/threads/{thread_id}/state")
async def get_atouts_state(thread_id: str):
    """
    Récupère l'état actuel du workflow Atouts.
    Utilise le snapshot LangGraph pour déterminer le vrai prochain nœud.
    """
    if thread_id not in atouts_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    workflow_data = atouts_workflows[thread_id]
    workflow = workflow_data["workflow"]
    
    # Récupérer l'état actuel depuis le checkpointer LangGraph
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = workflow.graph.get_state(config)
    
    if snapshot and snapshot.values:
        state = snapshot.values
        workflow_data["state"] = state
        
        # Déterminer le prochain nœud depuis le snapshot LangGraph
        next_nodes = []
        if snapshot.next:
            if isinstance(snapshot.next, (list, tuple)):
                next_nodes = list(snapshot.next)
            else:
                next_nodes = [snapshot.next]
        
        # Mettre à jour le statut en fonction du prochain nœud
        if "pre_atout_interrupt" in next_nodes:
            workflow_data["status"] = "paused"
        elif "validate_atouts" in next_nodes:
            workflow_data["status"] = "paused"
        elif len(next_nodes) == 0:
            workflow_data["status"] = "completed"
        else:
            workflow_data["status"] = "running"
        
        return {
            "thread_id": thread_id,
            "status": workflow_data["status"],
            "values": state,
            "next": tuple(next_nodes) if next_nodes else []
        }
    else:
        # Fallback si pas de snapshot
        state = workflow_data.get("state", {})
        return {
            "thread_id": thread_id,
            "status": workflow_data.get("status", "paused"),
            "values": state,
            "next": []
        }


@app.post("/atouts-entreprise/threads/{thread_id}/validate")
async def send_atouts_validation(thread_id: str, feedback: AtoutsValidationFeedback):
    """
    Envoie le feedback de validation des atouts et reprend le workflow.
    """
    if thread_id not in atouts_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    try:
        workflow_data = atouts_workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n📝 [API] Réception du feedback de validation atouts pour thread {thread_id}")
        print(f"✅ Validés: {len(feedback.validated_atouts)}")
        print(f"❌ Rejetés: {len(feedback.rejected_atouts)}")
        print(f"🎯 Action utilisateur: {feedback.atouts_user_action}")
        
        # Reprendre le workflow avec le feedback
        result = workflow.resume_workflow_with_validation(
            validated_atouts=feedback.validated_atouts,
            rejected_atouts=feedback.rejected_atouts,
            user_feedback=feedback.user_feedback,
            atouts_user_action=feedback.atouts_user_action,
            thread_id=thread_id
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        
        # Récupérer le snapshot LangGraph pour déterminer le vrai statut
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = workflow.graph.get_state(config)
        
        if snapshot and snapshot.next:
            next_nodes = list(snapshot.next) if isinstance(snapshot.next, (list, tuple)) else [snapshot.next]
            
            if "validate_atouts" in next_nodes:
                workflow_data["status"] = "paused"
            elif len(next_nodes) == 0:
                workflow_data["status"] = "completed"
            else:
                workflow_data["status"] = "running"
        else:
            if result.get("success"):
                workflow_data["status"] = "completed"
            else:
                workflow_data["status"] = "paused"
        
        return {
            "status": "resumed",
            "thread_id": thread_id,
            "workflow_status": workflow_data["status"]
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur reprise workflow: {str(e)}")


# ==================== ENDPOINTS CHAÎNE DE VALEUR ====================

@app.post("/value-chain/threads/{thread_id}/runs")
async def create_value_chain_run(thread_id: str, value_chain_input: ValueChainInput):
    """Démarre un workflow d'extraction de la chaîne de valeur"""
    try:
        if thread_id not in value_chain_workflows:
            workflow = ValueChainWorkflow(checkpointer=checkpointer)
            value_chain_workflows[thread_id] = {
                "workflow": workflow,
                "state": None,
                "status": "created"
            }
        
        workflow_data = value_chain_workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n🚀 [API] Démarrage workflow Chaîne de valeur pour thread {thread_id}")
        print(f"📁 Documents: {len(value_chain_input.transcript_document_ids)}")
        print(f"🏢 Entreprise: {value_chain_input.company_info.get('nom', 'N/A')}")
        
        # Exécuter le workflow
        result = workflow.run(
            transcript_document_ids=value_chain_input.transcript_document_ids,
            company_info=value_chain_input.company_info,
            thread_id=thread_id
        )
        
        workflow_data["state"] = result
        workflow_data["status"] = "paused" if result.get("workflow_paused") else ("completed" if result.get("success") else "error")
        
        return {
            "thread_id": thread_id,
            "status": workflow_data["status"],
            "result": result
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur Chaîne de valeur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur workflow chaîne de valeur: {str(e)}")


@app.get("/value-chain/threads/{thread_id}/state")
async def get_value_chain_state(thread_id: str):
    """
    Récupère l'état actuel du workflow Chaîne de valeur.
    Utilise le snapshot LangGraph pour déterminer le vrai prochain nœud.
    """
    # Si le thread n'existe pas encore dans le dictionnaire, vérifier s'il existe dans le checkpointer
    if thread_id not in value_chain_workflows:
        # Vérifier si le thread existe dans le checkpointer LangGraph
        try:
            # Créer un workflow temporaire pour vérifier
            temp_workflow = ValueChainWorkflow(checkpointer=checkpointer)
            config = {"configurable": {"thread_id": thread_id}}
            snapshot = temp_workflow.graph.get_state(config)
            
            if snapshot and snapshot.values:
                # Le thread existe dans le checkpointer, initialiser le workflow
                workflow = ValueChainWorkflow(checkpointer=checkpointer)
                value_chain_workflows[thread_id] = {
                    "workflow": workflow,
                    "state": snapshot.values,
                    "status": "paused" if snapshot.next else "completed"
                }
            else:
                # Le thread n'existe nulle part
                raise HTTPException(status_code=404, detail="Thread non trouvé")
        except HTTPException:
            raise
        except Exception as e:
            # Si erreur lors de la vérification, retourner 404
            raise HTTPException(status_code=404, detail=f"Thread non trouvé: {str(e)}")
    
    workflow_data = value_chain_workflows[thread_id]
    workflow = workflow_data["workflow"]
    
    # Récupérer l'état actuel depuis le checkpointer LangGraph
    config = {"configurable": {"thread_id": thread_id}}
    snapshot = workflow.graph.get_state(config)
    
    if snapshot and snapshot.values:
        state = snapshot.values
        workflow_data["state"] = state
        
        # Déterminer le prochain nœud depuis le snapshot LangGraph
        next_nodes = []
        if snapshot.next:
            if isinstance(snapshot.next, (list, tuple)):
                next_nodes = list(snapshot.next)
            else:
                next_nodes = [snapshot.next]
        
        # Mettre à jour le statut en fonction du prochain nœud
        if any(node in next_nodes for node in ["validate_teams", "validate_activities", "validate_friction_points"]):
            workflow_data["status"] = "paused"
        elif len(next_nodes) == 0:
            workflow_data["status"] = "completed"
        else:
            workflow_data["status"] = "running"
        
        return {
            "thread_id": thread_id,
            "status": workflow_data["status"],
            "values": state,
            "next": tuple(next_nodes) if next_nodes else []
        }
    else:
        # Fallback si pas de snapshot
        state = workflow_data.get("state", {})
        return {
            "thread_id": thread_id,
            "status": workflow_data.get("status", "paused"),
            "values": state,
            "next": []
        }


@app.post("/value-chain/threads/{thread_id}/validate")
async def send_value_chain_validation(thread_id: str, feedback: ValueChainValidationFeedback):
    """
    Envoie le feedback de validation de la chaîne de valeur et reprend le workflow.
    """
    if thread_id not in value_chain_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    try:
        workflow_data = value_chain_workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n📝 [API] Réception du feedback de validation chaîne de valeur pour thread {thread_id}")
        print(f"📋 Type de validation: {feedback.validation_type}")
        print(f"✅ Validés: {len(feedback.validated_items)}")
        print(f"❌ Rejetés: {len(feedback.rejected_items)}")
        print(f"🎯 Action utilisateur: {feedback.user_action}")
        
        # Reprendre le workflow avec le feedback
        result = workflow.resume_workflow_with_validation(
            validation_type=feedback.validation_type,
            validated_items=feedback.validated_items,
            rejected_items=feedback.rejected_items,
            user_action=feedback.user_action,
            thread_id=thread_id
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        
        # Récupérer le snapshot LangGraph pour déterminer le vrai statut
        config = {"configurable": {"thread_id": thread_id}}
        snapshot = workflow.graph.get_state(config)
        
        if snapshot and snapshot.next:
            next_nodes = list(snapshot.next) if isinstance(snapshot.next, (list, tuple)) else [snapshot.next]
            
            if any(node in next_nodes for node in ["validate_teams", "validate_activities", "validate_friction_points"]):
                workflow_data["status"] = "paused"
            elif len(next_nodes) == 0:
                workflow_data["status"] = "completed"
            else:
                workflow_data["status"] = "running"
        else:
            if result.get("success"):
                workflow_data["status"] = "completed"
            else:
                workflow_data["status"] = "paused"
        
        return {
            "status": "resumed",
            "thread_id": thread_id,
            "workflow_status": workflow_data["status"],
            "result": result
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

    if thread_id in atouts_workflows:
        del atouts_workflows[thread_id]
        deleted = True

    if thread_id in value_chain_workflows:
        del value_chain_workflows[thread_id]
        deleted = True

    if thread_id in prerequis_evaluation_workflows:
        del prerequis_evaluation_workflows[thread_id]
        deleted = True

    if deleted:
        return {"status": "deleted", "thread_id": thread_id}

    raise HTTPException(status_code=404, detail="Thread non trouvé")


# ==================== ENDPOINTS ÉVALUATION PRÉREQUIS ====================

@app.post("/prerequis-evaluation/threads/{thread_id}/runs")
async def create_prerequis_evaluation_run(thread_id: str, prerequis_input: PrerequisEvaluationInput):
    """Démarre un workflow d'évaluation des prérequis"""
    try:
        if thread_id not in prerequis_evaluation_workflows:
            workflow = PrerequisEvaluationWorkflow(checkpointer=checkpointer)
            prerequis_evaluation_workflows[thread_id] = {
                "workflow": workflow,
                "state": None,
                "status": "created"
            }
        
        workflow_data = prerequis_evaluation_workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n🚀 [API] Démarrage workflow Évaluation prérequis pour thread {thread_id}")
        print(f"📁 Documents: {len(prerequis_input.transcript_document_ids)}")
        print(f"🏢 Entreprise: {prerequis_input.company_info.get('nom', 'N/A')}")
        print(f"📋 Cas d'usage validés: {len(prerequis_input.validated_use_cases)}")
        
        # Exécuter le workflow
        result = workflow.run(
            transcript_document_ids=prerequis_input.transcript_document_ids,
            company_info=prerequis_input.company_info,
            validated_use_cases=prerequis_input.validated_use_cases,
            thread_id=thread_id,
            comments=prerequis_input.comments
        )
        
        workflow_data["state"] = result
        
        # Vérifier si on est en attente de validation
        if result.get("validation_pending", False):
            workflow_data["status"] = "validation_pending"
        else:
            workflow_data["status"] = "completed" if result.get("success") else "error"
        
        return {
            "thread_id": thread_id,
            "status": workflow_data["status"],
            "result": result,
            "validation_pending": result.get("validation_pending", False)
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur Évaluation prérequis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur workflow évaluation prérequis: {str(e)}")


@app.get("/prerequis-evaluation/threads/{thread_id}/state")
async def get_prerequis_evaluation_state(thread_id: str):
    """
    Récupère l'état actuel du workflow d'évaluation des prérequis
    
    Args:
        thread_id: ID du thread
        
    Returns:
        État du workflow
    """
    if thread_id not in prerequis_evaluation_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    workflow_data = prerequis_evaluation_workflows[thread_id]
    
    return {
        "thread_id": thread_id,
        "status": workflow_data["status"],
        "state": workflow_data["state"],
        "result": workflow_data["state"],  # Alias pour compatibilité avec Streamlit
        "validation_pending": workflow_data["state"].get("validation_pending", False) if workflow_data["state"] else False
    }


@app.post("/prerequis-evaluation/threads/{thread_id}/validate")
async def send_prerequis_validation(thread_id: str, feedback: PrerequisValidationFeedback):
    """
    Envoie le feedback de validation des prérequis et reprend le workflow.
    
    Args:
        thread_id: ID du thread
        feedback: Feedback utilisateur avec les prérequis validés et le commentaire de régénération
    
    Returns:
        {
            "status": "resumed",
            "thread_id": "uuid",
            "result": {...}
        }
    """
    if thread_id not in prerequis_evaluation_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    try:
        workflow_data = prerequis_evaluation_workflows[thread_id]
        workflow = workflow_data["workflow"]
        
        print(f"\n📝 [API] Réception du feedback de validation pour thread {thread_id}")
        print(f"✅ Validés: {feedback.validated_prerequis}")
        print(f"💬 Commentaire régénération: {feedback.regeneration_comment[:50]}..." if feedback.regeneration_comment else "💬 Pas de commentaire")
        
        # Reprendre le workflow avec le feedback
        result = workflow.resume_workflow_with_validation(
            validated_prerequis=feedback.validated_prerequis,
            regeneration_comment=feedback.regeneration_comment,
            thread_id=thread_id,
            modified_evaluations=feedback.modified_evaluations
        )
        
        # Mettre à jour l'état
        workflow_data["state"] = result
        
        # Vérifier si on est encore en attente de validation (nouvelle boucle)
        if result.get("validation_pending", False):
            workflow_data["status"] = "validation_pending"
        else:
            workflow_data["status"] = "completed" if result.get("success") else "error"
        
        return {
            "thread_id": thread_id,
            "status": workflow_data["status"],
            "result": result,
            "validation_pending": result.get("validation_pending", False)
        }
    
    except Exception as e:
        print(f"❌ [API] Erreur validation prérequis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur validation prérequis: {str(e)}")


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
                dev_mode=False
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
            transcript_document_ids=workflow_input.transcript_document_ids,
            workshop_document_ids=workflow_input.workshop_document_ids,
            company_name=workflow_input.company_name,
            interviewer_note=workflow_input.interviewer_note,
            thread_id=thread_id,
            validated_needs=workflow_input.validated_needs,
            validated_use_cases=workflow_input.validated_use_cases
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
        else:
            # Par défaut, le workflow est en cours d'exécution
            # (le statut sera mis à jour par get_executive_status en fonction de snapshot.next)
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
        
        # PRIORITÉ 1: Si pas de nœuds suivants, le workflow est terminé
        if not next_nodes or len(next_nodes) == 0:
            workflow_data["status"] = "completed"
            state["workflow_paused"] = False
            state["validation_type"] = ""
            workflow.graph.update_state(config, state)
            workflow_data["state"] = state
        # PRIORITÉ 2: Si le prochain nœud est une validation ou un interrupt, mettre à jour les flags
        elif "human_validation_enjeux" in next_nodes:
            state["workflow_paused"] = True
            state["validation_type"] = "challenges"
            workflow.graph.update_state(config, state)
            workflow_data["state"] = state
            workflow_data["status"] = "waiting_validation_challenges"
        elif "pre_recommendations_interrupt" in next_nodes:
            state["workflow_paused"] = True
            state["validation_type"] = "pre_recommendations"
            workflow.graph.update_state(config, state)
            workflow_data["state"] = state
            workflow_data["status"] = "waiting_pre_recommendations_context"
        elif "human_validation_recommendations" in next_nodes:
            state["workflow_paused"] = True
            state["validation_type"] = "recommendations"
            workflow.graph.update_state(config, state)
            workflow_data["state"] = state
            workflow_data["status"] = "waiting_validation_recommendations"
        # PRIORITÉ 3: Il y a des nœuds suivants, le workflow est en cours
        else:
            workflow_data["status"] = "running"
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


@app.post("/executive-summary/threads/{thread_id}/continue")
async def continue_executive(thread_id: str, context_data: dict):
    """Continue le workflow après l'interrupt pre_recommendations"""
    import time
    api_start_time = time.time()
    print(f"⏱️ [TIMING] continue_executive - DÉBUT ({time.strftime('%H:%M:%S.%f', time.localtime(api_start_time))[:-3]})")
    
    if thread_id not in executive_workflows:
        raise HTTPException(status_code=404, detail="Thread non trouvé")
    
    try:
        workflow_data = executive_workflows[thread_id]
        workflow = workflow_data["workflow"]
        config = {"configurable": {"thread_id": thread_id}}
        
        # Récupérer le feedback depuis le body de la requête
        recommendations_feedback = context_data.get("recommendations_feedback", "")
        
        print(f"📝 [API] Feedback reçu: {recommendations_feedback[:100]}...")
        
        # Mettre à jour l'état avec le feedback
        get_state_start = time.time()
        snapshot = workflow.graph.get_state(config)
        get_state_duration = time.time() - get_state_start
        print(f"⏱️ [TIMING] get_state: {get_state_duration:.3f}s")
        
        if snapshot and snapshot.values:
            state = snapshot.values
            # Accumuler le feedback (ne pas écraser si déjà présent)
            existing_feedback = state.get("recommendations_feedback", "")
            if recommendations_feedback:
                if existing_feedback:
                    state["recommendations_feedback"] = f"{existing_feedback}\n\n{recommendations_feedback}"
                else:
                    state["recommendations_feedback"] = recommendations_feedback
            state["workflow_paused"] = False
            state["validation_type"] = ""
            
            update_state_start = time.time()
            workflow.graph.update_state(config, state)
            update_state_duration = time.time() - update_state_start
            print(f"⏱️ [TIMING] update_state: {update_state_duration:.3f}s")
        
        # Reprendre le workflow
        stream_start = time.time()
        final_state = None
        for chunk in workflow.graph.stream(None, config):
            print(f"📊 [EXECUTIVE] Chunk reçu après continue: {list(chunk.keys())}")
            for node_name, node_state in chunk.items():
                print(f"  • Nœud '{node_name}' exécuté")
                final_state = node_state
        
        stream_duration = time.time() - stream_start
        print(f"⏱️ [TIMING] workflow.graph.stream: {stream_duration:.3f}s")
        
        # Récupérer l'état final
        get_state_after_start = time.time()
        snapshot = workflow.graph.get_state(config)
        get_state_after_duration = time.time() - get_state_after_start
        print(f"⏱️ [TIMING] get_state (après stream): {get_state_after_duration:.3f}s")
        
        if snapshot and snapshot.values:
            state = snapshot.values
            workflow_data["state"] = state
            
            # Vérifier si on est à un interrupt
            is_at_interrupt = False
            if snapshot.next:
                next_nodes = list(snapshot.next) if hasattr(snapshot.next, '__iter__') else [snapshot.next]
                if "human_validation_recommendations" in next_nodes:
                    is_at_interrupt = True
                    state["workflow_paused"] = True
                    state["validation_type"] = "recommendations"
                    workflow.graph.update_state(config, state)
                    print(f"🛑 [API] Workflow arrêté à l'interrupt: {next_nodes}")
            
            # Mettre à jour le statut
            if state.get("workflow_paused") or is_at_interrupt:
                validation_type = state.get("validation_type", "")
                if validation_type == "recommendations":
                    workflow_data["status"] = "waiting_validation_recommendations"
                else:
                    workflow_data["status"] = "paused"
            elif not snapshot.next:
                workflow_data["status"] = "completed"
            else:
                workflow_data["status"] = "running"
        elif final_state:
            workflow_data["state"] = final_state
            workflow_data["status"] = "running"
        
        total_duration = time.time() - api_start_time
        print(f"⏱️ [TIMING] continue_executive (total): {total_duration:.3f}s")
        
        return {
            "status": "success",
            "workflow_status": workflow_data["status"],
            "message": "Workflow repris avec succès"
        }
        
    except Exception as e:
        print(f"❌ [API] Erreur lors de la reprise: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur lors de la reprise: {str(e)}")

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
            if "human_validation_enjeux" in next_nodes or "pre_recommendations_interrupt" in next_nodes or "human_validation_recommendations" in next_nodes:
                is_at_interrupt = True
                state["workflow_paused"] = True
                if "human_validation_enjeux" in next_nodes:
                    state["validation_type"] = "challenges"
                elif "pre_recommendations_interrupt" in next_nodes:
                    state["validation_type"] = "pre_recommendations"
                elif "human_validation_recommendations" in next_nodes:
                    state["validation_type"] = "recommendations"
                # Mettre à jour l'état dans le checkpointer
                workflow.graph.update_state(config, state)
                print(f"🛑 [API] Workflow arrêté à l'interrupt: {next_nodes}")
        
        # Mettre à jour le statut
        # PRIORITÉ 1: Si pas de nœuds suivants (snapshot.next est vide), le workflow est terminé
        if not snapshot.next or (hasattr(snapshot.next, '__len__') and len(snapshot.next) == 0):
            workflow_data["status"] = "completed"
            state["workflow_paused"] = False
            state["validation_type"] = ""
            workflow.graph.update_state(config, state)
        # PRIORITÉ 2: Vérifier si on est à l'interrupt ou en pause
        elif state.get("workflow_paused") or is_at_interrupt:
            validation_type = state.get("validation_type", "")
            if validation_type == "challenges":
                workflow_data["status"] = "waiting_validation_challenges"
            elif validation_type == "recommendations":
                workflow_data["status"] = "waiting_validation_recommendations"
            else:
                workflow_data["status"] = "paused"
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

