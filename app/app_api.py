"""
Application Streamlit PURE INTERFACE - communique avec l'API LangGraph
Architecture propre : Streamlit = UI, API LangGraph = Logique métier
"""

from datetime import date
import streamlit as st
import requests
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import queue
import os
import sys

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

# Charger les variables d'environnement depuis un fichier .env
try:
    from dotenv import load_dotenv
    # Chercher le fichier .env dans plusieurs emplacements possibles
    project_root = Path(__file__).parent.parent
    env_files = [
        project_root / "deploy" / ".env",  # Dans deploy/ (priorité pour compatibilité avec script de déploiement)
        project_root / ".env",  # À la racine du projet
        Path(__file__).parent / ".env",  # Dans app/
    ]
    env_loaded = False
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=False)  # override=False pour ne pas écraser les variables déjà définies
            env_loaded = True
            # Optionnel : afficher un message de debug (uniquement en dev)
            if os.getenv("DEV_MODE") == "1":
                print(f"✅ Fichier .env chargé depuis: {env_file}")
            break
    if not env_loaded and os.getenv("DEV_MODE") == "1":
        print("⚠️ Aucun fichier .env trouvé")
except ImportError:
    # python-dotenv n'est pas installé, continuer sans
    if os.getenv("DEV_MODE") == "1":
        print("⚠️ python-dotenv n'est pas installé, les fichiers .env ne seront pas chargés")
except Exception as e:
    if os.getenv("DEV_MODE") == "1":
        print(f"⚠️ Erreur lors du chargement du .env: {e}")

from utils.report_generator import ReportGenerator
from human_in_the_loop.streamlit_validation_interface import StreamlitValidationInterface
from use_case_analysis.streamlit_use_case_validation import StreamlitUseCaseValidation
from web_search.web_search_agent import WebSearchAgent
from executive_summary.streamlit_validation_executive import StreamlitExecutiveValidation
from database.streamlit_db import (
    load_project_list,
    create_new_project,
    load_project_data,
    delete_document_by_id,
    save_agent_result,
    has_validated_results,
    load_agent_results,
    reject_agent_results,
)
from database.document_parser_service import DocumentParserService

# Configuration de l'API
# Utiliser la variable d'environnement API_URL si disponible, sinon utiliser localhost pour le développement
API_URL = os.getenv("API_URL", "http://localhost:2025")

# Initialisation des interfaces de validation
validation_interface = StreamlitValidationInterface()
use_case_validation = StreamlitUseCaseValidation()

# Initialisation du service de parsing
document_parser_service = DocumentParserService()

# Configuration de la page
st.set_page_config(
    page_title="aiko - Analyse des Besoins IA",
    page_icon="🤖",
    layout="wide"
)

# Interviewers par défaut (utilisés si la BDD est vide)
DEFAULT_INTERVIEWERS = ["Christella Umuhoza", "Adrien Fabry"]

# ==================== AUTHENTIFICATION ====================

def is_dev_mode() -> bool:
    """Vérifie si le mode DEV est activé"""
    return os.getenv("DEV_MODE", "0") == "1"

def get_auth_username() -> str:
    """Récupère le nom d'utilisateur depuis les variables d'environnement"""
    return os.getenv("AUTH_USERNAME", "").strip()

def get_auth_password() -> str:
    """Récupère le mot de passe depuis les variables d'environnement"""
    return os.getenv("AUTH_PASSWORD", "").strip()

def is_auth_enabled() -> bool:
    """Vérifie si l'authentification est activée (variables configurées)"""
    username = get_auth_username()
    password = get_auth_password()
    return bool(username and password)

def check_authentication() -> bool:
    """
    Vérifie si l'utilisateur est authentifié.
    
    Returns:
        True si l'utilisateur est authentifié, False sinon
    """
    # En mode DEV, auto-login (bypasser l'authentification et marquer comme authentifié)
    if is_dev_mode():
        st.session_state.authenticated = True
        return True
    
    # Si l'authentification n'est pas configurée, autoriser l'accès
    if not is_auth_enabled():
        return True
    
    # Vérifier si l'utilisateur est authentifié dans la session
    return st.session_state.get("authenticated", False)

def verify_credentials(username: str, password: str) -> bool:
    """
    Vérifie les identifiants de l'utilisateur.
    
    Args:
        username: Nom d'utilisateur
        password: Mot de passe
    
    Returns:
        True si les identifiants sont corrects, False sinon
    """
    # Si l'authentification n'est pas configurée, autoriser l'accès
    if not is_auth_enabled():
        return True
    
    auth_username = get_auth_username()
    auth_password = get_auth_password()
    return username.strip() == auth_username and password == auth_password

def display_login_page():
    """Affiche la page de connexion"""
    # Centrer le contenu
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Logo si disponible
        import config
        logo_path = config.get_white_logo_path()
        if logo_path.exists():
            st.image(str(logo_path), width=300)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("# 🔐 Connexion")
        st.markdown("---")
        
        # Formulaire de connexion
        with st.form("login_form"):
            username = st.text_input("👤 Nom d'utilisateur", placeholder="Entrez votre nom d'utilisateur")
            password = st.text_input("🔒 Mot de passe", type="password", placeholder="Entrez votre mot de passe")
            
            submitted = st.form_submit_button("🚀 Se connecter", type="primary", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("❌ Veuillez remplir tous les champs")
                elif verify_credentials(username, password):
                    st.session_state.authenticated = True
                    st.success("✅ Connexion réussie !")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")
        
        # Avertissement si l'authentification n'est pas configurée
        if not is_auth_enabled():
            st.warning("⚠️ L'authentification n'est pas configurée. Configurez AUTH_USERNAME et AUTH_PASSWORD pour activer la protection.")
            
            # Debug : afficher les valeurs pour diagnostiquer
            if os.getenv("DEV_MODE") == "1":
                st.write("🔍 Debug:")
                st.write(f"- AUTH_USERNAME (from env): `{get_auth_username()}`")
                st.write(f"- AUTH_PASSWORD (from env): `{'*' * len(get_auth_password()) if get_auth_password() else '(vide)'}`")
                st.write(f"- is_auth_enabled(): `{is_auth_enabled()}`")

def load_interviewers() -> List[str]:
    """
    Charge la liste des intervieweurs depuis la base de données.
    
    Returns:
        Liste des noms d'intervieweurs
    """
    try:
        from database.repository import SpeakerRepository
        from database.db import get_db_context
        
        with get_db_context() as db:
            # Récupérer tous les interviewers globaux (project_id = NULL)
            global_interviewers = SpeakerRepository.get_interviewers(db)
            
            if global_interviewers:
                # Retourner les noms des interviewers depuis la BDD
                return [speaker.name for speaker in global_interviewers]
            else:
                # Si aucun interviewer en BDD, créer les interviewers par défaut
                default_interviewers = []
                for name in DEFAULT_INTERVIEWERS:
                    SpeakerRepository.get_or_create_speaker(
                        db=db,
                        name=name,
                        role=None,
                        level=None,
                        speaker_type="interviewer",
                        project_id=None  # NULL pour interviewers globaux
                    )
                    default_interviewers.append(name)
                return default_interviewers
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des intervieweurs : {str(e)}")
        return DEFAULT_INTERVIEWERS

def save_interviewers(interviewers: List[str]) -> bool:
    """
    Sauvegarde la liste des intervieweurs dans la base de données.
    
    Args:
        interviewers: Liste des noms d'intervieweurs à sauvegarder
    
    Returns:
        True si la sauvegarde a réussi, False sinon
    """
    try:
        from database.repository import SpeakerRepository
        from database.db import get_db_context
        from database.models import Transcript
        
        with get_db_context() as db:
            # Normaliser les noms (strip)
            interviewers_normalized = [name.strip() for name in interviewers if name.strip()]
            
            # Récupérer les interviewers existants
            existing_interviewers = SpeakerRepository.get_interviewers(db)
            existing_names = {speaker.name for speaker in existing_interviewers}
            
            # Créer ou mettre à jour les interviewers de la liste
            for name in interviewers_normalized:
                SpeakerRepository.get_or_create_speaker(
                    db=db,
                    name=name,
                    role=None,
                    level=None,
                    speaker_type="interviewer",
                    project_id=None  # NULL pour interviewers globaux
                )
            
            # Supprimer les interviewers qui ne sont plus dans la liste
            # (mais seulement s'ils n'ont pas de transcripts associés)
            for speaker in existing_interviewers:
                if speaker.name not in interviewers_normalized:
                    # Vérifier si le speaker a des transcripts associés
                    transcript_count = db.query(Transcript).filter(
                        Transcript.speaker_id == speaker.id
                    ).count()
                    
                    if transcript_count == 0:
                        # Pas de transcripts, on peut le supprimer
                        db.delete(speaker)
                    # Sinon, on le garde (il a des transcripts historiques)
            
            db.commit()
            return True
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde des intervieweurs : {str(e)}")
        return False

def init_debug_data():
    """Initialise les données simulées en mode DEV"""
    if not is_dev_mode():
        return
    
    # Marquer que le DEBUG a été initialisé
    if 'debug_data_initialized' not in st.session_state:
        st.session_state.debug_data_initialized = False
    
    # Ne pas réinitialiser si déjà fait
    if st.session_state.debug_data_initialized:
        return
    
    # Simuler des transcripts uploadés (utiliser des fichiers réels du dossier inputs/)
    inputs_dir = Path(__file__).parent.parent / "inputs"
    if inputs_dir.exists():
        # Chercher des fichiers PDF dans inputs/
        pdf_files = list(inputs_dir.glob("*.pdf"))
        if pdf_files:
            # Prendre les 2 premiers PDF
            for pdf_file in pdf_files[:2]:
                transcript_data = {
                    "file_path": str(pdf_file.absolute()),
                    "speakers": [
                        {"name": "Jean Dupont", "role": "Directeur Commercial"},
                        {"name": "Marie Martin", "role": "Responsable R&D"}
                    ]
                }
                st.session_state.uploaded_transcripts.append(transcript_data)
        
        # Chercher des fichiers Excel dans inputs/
        excel_files = list(inputs_dir.glob("*.xlsx"))
        if excel_files:
            # Prendre le premier Excel
            for excel_file in excel_files[:1]:
                st.session_state.uploaded_workshops.append(str(excel_file.absolute()))
    
    # Simuler la validation des informations de l'entreprise
    st.session_state.validated_company_info = {
        "nom": "Entreprise Test DEBUG",
        "url": "https://example.com",
        "description": "Entreprise simulée pour les tests en mode DEBUG"
    }
    st.session_state.company_name = "Entreprise Test DEBUG"
    st.session_state.company_url = "https://example.com"
    st.session_state.company_description = "Entreprise simulée pour les tests en mode DEBUG"
    
    # Simuler les résultats de web search pour éviter l'appel API
    st.session_state.web_search_results = {
        "company_name": "Entreprise Test DEBUG",
        "company_url": "https://example.com",
        "company_description": "Entreprise simulée pour les tests en mode DEBUG",
        "summary": "Données simulées en mode DEBUG - pas d'appel API réel"
    }
    
    # Marquer comme initialisé
    st.session_state.debug_data_initialized = True

def init_session_state():
    """Initialise l'état de session"""
    # Authentification
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = None
    if 'workflow_status' not in st.session_state:
        st.session_state.workflow_status = None
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Accueil"
    # Gestion de projet (base de données)
    if 'current_project_id' not in st.session_state:
        st.session_state.current_project_id = None
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'project_loaded' not in st.session_state:
        st.session_state.project_loaded = False
    # Uploads persistants (session)
    if 'uploaded_transcripts' not in st.session_state:
        st.session_state.uploaded_transcripts = []
    if 'uploaded_workshops' not in st.session_state:
        st.session_state.uploaded_workshops = []
    if 'company_name' not in st.session_state:
        st.session_state.company_name = ""
    if 'company_url' not in st.session_state:
        st.session_state.company_url = ""
    if 'company_description' not in st.session_state:
        st.session_state.company_description = ""
    # Executive Summary workflow
    if 'executive_thread_id' not in st.session_state:
        st.session_state.executive_thread_id = None
    if 'executive_workflow_status' not in st.session_state:
        st.session_state.executive_workflow_status = None
    if 'executive_workflow_state' not in st.session_state:
        st.session_state.executive_workflow_state = {}
    if 'executive_final_results' not in st.session_state:
        st.session_state.executive_final_results = None
    if 'executive_final_results_cached' not in st.session_state:
        st.session_state.executive_final_results_cached = False
    if 'rappel_mission' not in st.session_state:
        st.session_state.rappel_mission = ""
    if 'rappel_mission_company' not in st.session_state:
        st.session_state.rappel_mission_company = ""
    if 'validated_company_info' not in st.session_state:
        st.session_state.validated_company_info = None
    if 'web_search_results' not in st.session_state:
        st.session_state.web_search_results = None
    if 'trigger_web_search' not in st.session_state:
        st.session_state.trigger_web_search = False
    if 'web_search_agent' not in st.session_state:
        try:
            st.session_state.web_search_agent = WebSearchAgent()
        except Exception as e:
            st.session_state.web_search_agent = None
            if os.getenv("DEV_MODE") == "1":
                print(f"⚠️ Erreur lors de l'initialisation de WebSearchAgent: {e}")
    if 'web_search_counter' not in st.session_state:
        st.session_state.web_search_counter = 0
    
    # Initialiser les données DEBUG si le mode est activé
    init_debug_data()
    
    # Value Chain workflow
    if 'value_chain_thread_id' not in st.session_state:
        st.session_state.value_chain_thread_id = None
    if 'value_chain_workflow_status' not in st.session_state:
        st.session_state.value_chain_workflow_status = None
    if 'value_chain_workflow_state' not in st.session_state:
        st.session_state.value_chain_workflow_state = {}
    if 'value_chain_workflow_completed' not in st.session_state:
        st.session_state.value_chain_workflow_completed = False
    if 'value_chain_data' not in st.session_state:
        st.session_state.value_chain_data = {}
    if 'value_chain_markdown' not in st.session_state:
        st.session_state.value_chain_markdown = ""
    if 'value_chain_json' not in st.session_state:
        st.session_state.value_chain_json = ""

def get_transcript_file_paths(transcripts: List[Any]) -> List[str]:
    """
    Extrait les file_paths depuis la liste de transcripts (nouvelle structure)
    
    Args:
        transcripts: Liste de dictionnaires avec structure {file_path, speakers}
                     ou liste de strings (ancienne structure)
        
    Returns:
        Liste des file_paths
    """
    if not transcripts:
        return []
    
    # Si c'est déjà une liste de strings (ancienne structure), retourner tel quel
    if transcripts and isinstance(transcripts[0], str):
        return transcripts
    
    # Sinon, extraire les file_paths depuis la nouvelle structure
    return [t.get("file_path", "") for t in transcripts if isinstance(t, dict) and t.get("file_path")]

def upload_files_to_api(files: List[Any]) -> Dict[str, Any]:
    """
    Upload les fichiers vers l'API.
    
    Returns:
        {"workshop": [paths], "transcript": [paths], "file_paths": [paths]}
    """
    try:
        files_data = []
        # Stocker les fichiers en mémoire pour pouvoir les copier localement si nécessaire
        files_content = {}
        for uploaded_file in files:
            file_content = uploaded_file.getvalue()
            files_content[uploaded_file.name] = file_content
            files_data.append(
                ("files", (uploaded_file.name, file_content, uploaded_file.type))
            )
        
        response = requests.post(
            f"{API_URL}/files/upload",
            files=files_data
        )
        response.raise_for_status()
        
        result = response.json()
        api_paths = {
            "workshop": result.get("file_types", {}).get("workshop", []),
            "transcript": result.get("file_types", {}).get("transcript", []),
            "file_paths": result.get("file_paths", [])
        }
        
        # Vérifier que les fichiers existent bien dans /tmp/aiko_uploads/ de l'API
        # Si ce n'est pas le cas (API et Streamlit sur des machines/conteneurs différents),
        # copier les fichiers localement
        local_upload_dir = Path("/tmp/aiko_uploads_local")
        local_upload_dir.mkdir(exist_ok=True)
        
        local_paths = {
            "workshop": [],
            "transcript": [],
            "file_paths": []
        }
        
        # Créer une liste des fichiers uploadés avec leur index pour le mapping
        uploaded_files_list = list(files_content.items())
        
        # Fonction helper pour vérifier et copier si nécessaire
        def ensure_file_accessible(api_path: str, file_type: str = None) -> str:
            """Vérifie que le fichier existe, sinon le copie localement"""
            api_path_obj = Path(api_path)
            
            # Vérifier si le fichier existe sur le chemin de l'API
            if api_path_obj.exists():
                # Le fichier existe dans /tmp/aiko_uploads/ de l'API, l'utiliser
                return api_path
            else:
                # Le fichier n'existe pas, le copier localement comme fallback
                file_name = api_path_obj.name
                matching_file = None
                
                # Chercher le fichier correspondant dans les fichiers uploadés
                for orig_name, content in files_content.items():
                    # Le nom de l'API contient l'UUID suivi du nom original
                    if orig_name in file_name or file_name.endswith(orig_name):
                        matching_file = (orig_name, content)
                        break
                
                if matching_file:
                    orig_name, content = matching_file
                    # Créer un chemin local unique
                    local_file_id = str(uuid.uuid4())
                    local_path = local_upload_dir / f"{local_file_id}_{orig_name}"
                    # Copier le fichier localement
                    with open(local_path, "wb") as f:
                        f.write(content)
                    print(f"⚠️ Fichier copié localement (API non accessible): {local_path}")
                    return str(local_path)
                else:
                    # Si on ne trouve pas, retourner le chemin de l'API quand même
                    print(f"⚠️ Fichier non trouvé, utilisation du chemin API: {api_path}")
                    return api_path
        
        # Pour chaque type de fichier, vérifier l'accessibilité
        for file_type in ["workshop", "transcript"]:
            for api_path in api_paths[file_type]:
                local_paths[file_type].append(ensure_file_accessible(api_path, file_type))
        
        # Faire de même pour file_paths
        for api_path in api_paths["file_paths"]:
            local_paths["file_paths"].append(ensure_file_accessible(api_path))
        
        return local_paths
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'upload: {str(e)}")
        return {"workshop": [], "transcript": [], "file_paths": []}

def start_workflow_api_call(workshop_data: List[Any], transcript_data: List[Any], company_name: str, company_url: str, company_description: str, validated_company_info: Optional[Dict[str, Any]], interviewer_names: List[str], additional_context: str, result_queue: queue.Queue):
    """
    Fait l'appel API dans un thread séparé.
    Extrait les document_ids depuis workshop_data et transcript_data et les passe à l'API.
    Met le résultat dans la queue : (success: bool, thread_id: str, error_msg: str)
    """
    try:
        # Générer un thread_id
        thread_id = str(uuid.uuid4())
        
        # Extraire les document_ids depuis workshop_data
        workshop_document_ids = []
        if workshop_data:
            for workshop in workshop_data:
                if isinstance(workshop, dict):
                    document_id = workshop.get("document_id")
                    if document_id is not None:
                        workshop_document_ids.append(document_id)
                # Si c'est un string (ancienne structure), on ne peut pas récupérer le document_id
                # Dans ce cas, on laisse vide et le workflow devra gérer différemment
        
        # Extraire les document_ids depuis transcript_data
        transcript_document_ids = []
        if transcript_data:
            for transcript in transcript_data:
                if isinstance(transcript, dict):
                    document_id = transcript.get("document_id")
                    if document_id is not None:
                        transcript_document_ids.append(document_id)
                # Si c'est un string (ancienne structure), on ne peut pas récupérer le document_id
        
        # Vérifier qu'on a au moins un document_id
        if not workshop_document_ids and not transcript_document_ids:
            error_msg = "Aucun document_id trouvé. Veuillez d'abord uploader et sauvegarder les documents dans la base de données."
            result_queue.put((False, None, None, error_msg))
            return
        
        # Lancer le workflow avec les document_ids
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/runs",
            json={
                "workshop_document_ids": workshop_document_ids,
                "transcript_document_ids": transcript_document_ids,
                "company_name": company_name if company_name else None,
                "company_url": company_url if company_url else None,
                "company_description": company_description if company_description else None,
                "validated_company_info": validated_company_info,
                "interviewer_names": interviewer_names,
                "additional_context": additional_context if additional_context else ""
            },
            timeout=900  # 5 minutes pour le traitement initial
        )
        response.raise_for_status()
        
        result = response.json()
        result_queue.put((True, thread_id, result["status"], None))
    
    except Exception as e:
        result_queue.put((False, None, None, str(e)))

def display_rotating_messages(company_name: str = None):
    """
    Affiche des messages rotatifs pour indiquer la progression.
    
    Returns:
        Liste des messages à afficher en rotation
    """
    company_display = company_name if company_name else "l'entreprise"
    
    messages = [
        f"📝 Traitement des ateliers en cours...",
        f"📄 Etude des transcripts...",
        f"🌐 Recherche web sur {company_display}...",
        f"🤖 Interprétation des données par l'IA...",
        f"🔍 Identification des besoins métier...",
        f"⚙️ Analyse en cours..."
    ]
    
    return messages

def poll_workflow_status():
    """
    Poll le statut du workflow.
    
    Returns:
        "running", "waiting_validation", "waiting_use_case_validation", "completed", "error"
    """
    if not st.session_state.thread_id:
        return "no_thread"
    
    try:
        response = requests.get(
            f"{API_URL}/threads/{st.session_state.thread_id}/state",
            timeout=60  # 60 secondes pour récupérer l'état
        )
        response.raise_for_status()
        
        state = response.json()
        st.session_state.workflow_state = state["values"]
        
        # Déterminer le statut
        # Note: state["next"] peut être une liste, un tuple ou vide
        next_nodes = list(state["next"]) if state["next"] else []
        
        # Debug: afficher les next_nodes détectés
        print(f"🔍 [DEBUG] poll_workflow_status - next_nodes: {next_nodes}")
        
        if "human_validation" in next_nodes:
            return "waiting_validation"
        elif "pre_use_case_interrupt" in next_nodes:
            return "waiting_pre_use_case_context"
        elif "validate_use_cases" in next_nodes:
            return "waiting_use_case_validation"
        elif len(next_nodes) == 0:
            return "completed"
        else:
            return "running"
    
    except Exception as e:
        st.error(f"❌ Erreur lors du polling: {str(e)}")
        return "error"

def poll_executive_workflow_status():
    """
    Poll le statut du workflow Executive Summary.
    
    Returns:
        "running", "waiting_validation_challenges", "waiting_validation_recommendations", "completed", "error"
    """
    if not st.session_state.get("executive_thread_id"):
        return "no_thread"
    
    try:
        thread_id = st.session_state.executive_thread_id
        
        # Récupérer le statut
        status_response = requests.get(
            f"{API_URL}/executive-summary/threads/{thread_id}/status",
            timeout=60
        )
        status_response.raise_for_status()
        status_data = status_response.json()
        status = status_data.get("status", "unknown")
        
        # Récupérer l'état complet
        state_response = requests.get(
            f"{API_URL}/executive-summary/threads/{thread_id}/state",
            timeout=60
        )
        state_response.raise_for_status()
        state_data = state_response.json()
        
        # Mettre à jour session_state avec l'état complet
        st.session_state.executive_workflow_state = {
            "identified_challenges": state_data.get("identified_challenges", []),
            "validated_challenges": state_data.get("validated_challenges", []),
            "rejected_challenges": [],
            "extracted_needs": state_data.get("extracted_needs", []),
            "maturity_score": state_data.get("maturity_score", 3),
            "maturity_summary": state_data.get("maturity_summary", ""),
            "recommendations": state_data.get("recommendations", []),
            "validated_recommendations": state_data.get("validated_recommendations", []),
            "challenges_iteration_count": state_data.get("challenges_iteration_count", 0),
            "workflow_paused": state_data.get("workflow_paused", False),
            "validation_type": state_data.get("validation_type", "")
        }
        
        # Mettre à jour le statut dans session_state pour éviter de poller inutilement
        st.session_state.executive_workflow_status = status
        
        return status
    
    except Exception as e:
        st.error(f"❌ Erreur lors du polling executive: {str(e)}")
        return "error"

def send_validation_feedback_api_call(validated_needs: List[Dict], rejected_needs: List[Dict], 
                                      user_feedback: str, user_action: str, thread_id: str, result_queue: queue.Queue):
    """
    Envoie le feedback de validation à l'API dans un thread séparé.
    """
    try:
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/validation",
            json={
                "validated_needs": validated_needs,
                "rejected_needs": rejected_needs,
                "user_feedback": user_feedback,
                "user_action": user_action
            },
            timeout=600  # 10 minutes pour la validation et la reprise du workflow
        )
        response.raise_for_status()
        result_queue.put((True, None))
    
    except Exception as e:
        result_queue.put((False, str(e)))

def send_pre_use_case_context_api_call(additional_context: str, thread_id: str, result_queue: queue.Queue):
    """
    Envoie le contexte additionnel pour la génération des use cases à l'API dans un thread séparé.
    """
    try:
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/pre-use-case-context",
            json={
                "use_case_additional_context": additional_context
            },
            timeout=600
        )
        response.raise_for_status()
        result_queue.put((True, None))
    
    except Exception as e:
        result_queue.put((False, str(e)))

def send_use_case_validation_feedback_api_call(validated_use_cases: List[Dict],
                                                rejected_use_cases: List[Dict], 
                                                user_feedback: str, 
                                                use_case_user_action: str,
                                                thread_id: str, result_queue: queue.Queue):
    """
    Envoie le feedback de validation des use cases à l'API dans un thread séparé.
    Retourne la réponse complète avec les final_results.
    """
    try:
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/use-case-validation",
            json={
                "validated_use_cases": validated_use_cases,
                "rejected_use_cases": rejected_use_cases,
                "user_feedback": user_feedback,
                "use_case_user_action": use_case_user_action
            },
            timeout=600  # 10 minutes pour la validation finale
        )
        response.raise_for_status()
        response_data = response.json()
        result_queue.put((True, response_data))
    
    except Exception as e:
        result_queue.put((False, str(e)))

# ==================== INTERFACE STREAMLIT ====================

def display_home_page():
    """Affiche la page d'accueil avec le logo et le message de bienvenue"""
    # Afficher le mode DEV en haut si activé
    if is_dev_mode():
        st.warning("🔧 **MODE DEV ACTIVÉ** - Connexion automatique et upload de documents simulé")
    
    # Charger le logo depuis config.py (détection automatique)
    import config
    logo_path = config.get_white_logo_path()
    
    # Centrer le contenu
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Afficher le logo si disponible
        if logo_path.exists():
            st.image(str(logo_path), width="stretch")
        else:
            st.warning("⚠️ Logo non trouvé à l'emplacement attendu")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("# Bienvenue sur aikoGPT")
        st.markdown("---")
        st.markdown("""
        **aikoGPT** est une plateforme d'analyse des besoins IA qui vous permet de :
        
        - 📊 Analyser les besoins métier à partir d'ateliers et de transcriptions
        - 🤖 Générer des recommandations personnalisées
        - 📝 Créer des rapports structurés
        """)
        
        # Vérifier le statut de l'API
        try:
            response = requests.get(f"{API_URL}/", timeout=5)
            if response.status_code == 200:
                st.success("✅ API connectée")
            else:
                st.warning("⚠️ L'API n'est pas accessible")
        except Exception:
            st.warning("⚠️ L'API n'est pas accessible. Assurez-vous que l'API est lancée avec : `uv run python api/start_api.py`")

def display_interviewers_config_page():
    """Affiche l'interface complète de configuration des intervieweurs dans la page principale"""
    st.header("👥 Configuration des Intervieweurs")
    
    # Charger les intervieweurs depuis le fichier JSON
    interviewers = load_interviewers()
    
    st.info("💡 Les intervieweurs configurés seront utilisés pour identifier les speakers dans les transcriptions.")
    
    # Afficher la liste actuelle avec possibilité de suppression
    if interviewers:
        st.markdown("**Interviewers configurés :**")
        for idx, interviewer in enumerate(interviewers):
            col_display, col_delete = st.columns([3, 1])
            with col_display:
                st.text(f"• {interviewer}")
            with col_delete:
                if st.button("🗑️", key=f"delete_{idx}"):
                    interviewers.remove(interviewer)
                    if save_interviewers(interviewers):
                        st.success(f"✅ {interviewer} retiré")
                        st.rerun()
    else:
        st.warning("⚠️ Aucun interviewer configuré")
    
    st.markdown("---")
    
    # Interface pour ajouter un nouvel interviewer
    st.subheader("➕ Ajouter un interviewer")
    new_interviewer = st.text_input(
        "Nom de l'interviewer",
        placeholder="Ex: Jean Dupont",
        key="new_interviewer"
    )
    
    if st.button("➕ Ajouter", key="add_btn"):
        if new_interviewer and new_interviewer.strip():
            if new_interviewer.strip() not in interviewers:
                interviewers.append(new_interviewer.strip())
                if save_interviewers(interviewers):
                    st.success(f"✅ {new_interviewer.strip()} ajouté")
                    st.rerun()
            else:
                st.warning("⚠️ Ce nom est déjà dans la liste")
        else:
            st.warning("⚠️ Veuillez saisir un nom")

def display_work_in_progress():
    """Affiche un message WORK IN PROGRESS pour la section de génération des recommandations"""
    st.header("Génération des Enjeux et Recommandations")
    
    # Message WORK IN PROGRESS bien visible
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 50px; background-color: #ffeb3b; border-radius: 10px; margin: 20px 0;">
        <h1 style="color: #d32f2f; font-size: 72px; font-weight: bold; margin: 20px 0;">⚠️</h1>
        <h1 style="color: #d32f2f; font-size: 48px; font-weight: bold; margin: 20px 0;">WORK IN PROGRESS</h1>
        <p style="color: #424242; font-size: 24px; margin: 20px 0;">Cette fonctionnalité est en cours de développement</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")

# ==================== GESTION DE PROJET (BASE DE DONNÉES) ====================

def load_project_data_to_session(project_id: int):
    """
    Charge les données d'un projet dans st.session_state.
    
    Args:
        project_id: ID du projet
    """
    try:
        data = load_project_data(project_id)
        if not data:
            st.warning(f"⚠️ Aucune donnée trouvée pour le projet {project_id}")
            return
        
        project = data.get("project", {})
        documents = data.get("documents", [])
        transcripts_data = data.get("transcripts", {})  # NOUVEAU: Charger les transcripts depuis la DB
        workshops_data = data.get("workshops", {})  # NOUVEAU: Charger les workshops depuis la DB
        word_extractions_data = data.get("word_extractions", {})  # NOUVEAU: Charger les word_extractions
        agent_results = data.get("agent_results", {})
        
        # Charger les informations du projet
        st.session_state.current_project = project
        st.session_state.company_name = project.get("company_name", "")
        company_info = project.get("company_info", {})
        # Toujours mettre à jour validated_company_info, même si c'est un dict vide
        st.session_state.validated_company_info = company_info
        
        # Charger les transcripts depuis la base de données
        # Les transcripts sont déjà chargés avec leurs speakers dans transcripts_data
        st.session_state.uploaded_transcripts = []
        for document_id, transcript_info in transcripts_data.items():
            transcript_entry = {
                "document_id": transcript_info.get("document_id"),
                "file_name": transcript_info.get("file_name", ""),
                "speakers": transcript_info.get("speakers", []),
            }
            st.session_state.uploaded_transcripts.append(transcript_entry)
        
        # Charger les workshops depuis la base de données
        # Les workshops sont déjà chargés dans workshops_data
        # Regrouper par document (un fichier peut contenir plusieurs ateliers)
        st.session_state.uploaded_workshops = []
        for document_id, workshops_list in workshops_data.items():
            # Trouver le document correspondant pour récupérer file_name
            document = next((d for d in documents if d.get("id") == document_id), None)
            if document:
                # Créer une seule entrée par document avec la liste des ateliers
                workshop_entry = {
                    "document_id": document_id,
                    "file_name": document.get("file_name", ""),
                    "ateliers": [w.get("atelier_name", "") for w in workshops_list],  # Liste des noms d'ateliers
                }
                st.session_state.uploaded_workshops.append(workshop_entry)
        
        # Charger le word_report si disponible
        word_reports = [d for d in documents if d.get("file_type") == "word_report"]
        if word_reports:
            word_report = word_reports[0]  # Prendre le premier
            st.session_state.word_path = None  # Plus besoin du chemin, tout est en DB
            # Les word_extractions sont dans word_extractions_data si nécessaire
        
        # Charger les résultats validés
        # Besoins et use cases
        needs_result = agent_results.get("word_validation_needs") or agent_results.get("need_analysis_needs")
        if needs_result:
            st.session_state.validated_needs = needs_result.get("data", {}).get("needs", [])
        
        use_cases_result = agent_results.get("word_validation_use_cases") or agent_results.get("need_analysis_use_cases")
        if use_cases_result:
            st.session_state.validated_use_cases = use_cases_result.get("data", {}).get("use_cases", [])
        
        # Enjeux et recommandations
        challenges_result = agent_results.get("executive_summary_challenges")
        if challenges_result:
            st.session_state.validated_challenges = challenges_result.get("data", {}).get("challenges", [])
        
        recommendations_result = agent_results.get("executive_summary_recommendations")
        if recommendations_result:
            st.session_state.validated_recommendations = recommendations_result.get("data", {}).get("recommendations", [])
        
        maturity_result = agent_results.get("executive_summary_maturity")
        if maturity_result:
            st.session_state.validated_maturity = maturity_result.get("data", {}).get("maturity", {})
        
        # Atouts
        atouts_result = agent_results.get("atouts_atouts")
        if atouts_result:
            st.session_state.validated_atouts = atouts_result.get("data", {}).get("atouts", [])
        
        # Rappel de mission
        rappel_result = agent_results.get("rappel_mission_rappel_mission")
        if rappel_result:
            st.session_state.rappel_mission = rappel_result.get("data", {}).get("rappel_mission", "")
        
        # Web search results
        web_search_result = agent_results.get("rappel_mission_web_search_results") or agent_results.get("atouts_web_search_results")
        if web_search_result:
            st.session_state.web_search_results = web_search_result.get("data", {}).get("results", [])
        
        st.session_state.project_loaded = True
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données du projet: {str(e)}")
        st.session_state.project_loaded = False


def display_project_selection():
    """
    Affiche l'interface de sélection/création de projet (obligatoire).
    Retourne True si un projet est sélectionné, False sinon.
    """
    st.title("📁 Sélection de projet")
    st.info("💡 Vous devez sélectionner un projet existant ou en créer un nouveau pour continuer.")
    
    # Charger la liste des projets
    projects = load_project_list()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if projects:
            project_options = ["-- Sélectionner un projet --"] + [
                f"{p['company_name']} (ID: {p['id']})" for p in projects
            ]
            selected = st.selectbox(
                "Projets existants",
                project_options,
                key="project_selectbox"
            )
            
            if selected and selected != "-- Sélectionner un projet --":
                # Extraire l'ID du projet
                project_id = int(selected.split("ID: ")[1].split(")")[0])
                st.session_state.current_project_id = project_id
                load_project_data_to_session(project_id)
                st.success(f"✅ Projet sélectionné: {projects[project_id - 1]['company_name']}")
                st.rerun()
        else:
            st.info("ℹ️ Aucun projet existant. Créez-en un nouveau ci-dessous.")
    
    with col2:
        st.markdown("### ➕ Nouveau projet")
        with st.form("new_project_form"):
            new_company_name = st.text_input("Nom de l'entreprise", key="new_company_name")
            submit = st.form_submit_button("Créer", use_container_width=True)
            
            if submit:
                if new_company_name.strip():
                    project_id = create_new_project(new_company_name.strip())
                    if project_id:
                        st.session_state.current_project_id = project_id
                        load_project_data_to_session(project_id)
                        st.success(f"✅ Projet créé: {new_company_name}")
                        st.rerun()
                    else:
                        st.error("❌ Erreur lors de la création du projet")
                else:
                    st.warning("⚠️ Veuillez saisir un nom d'entreprise")
    
    return st.session_state.current_project_id is not None


def display_project_selector_in_sidebar():
    """
    Affiche le sélecteur de projet dans la sidebar.
    Retourne True si un projet est sélectionné, False sinon.
    """
    st.markdown("### 📁 Projet")
    
    # Charger la liste des projets
    projects = load_project_list()
    
    # Options pour le selectbox
    if projects:
        project_options = ["-- Sélectionner --"] + [
            f"{p['company_name']}" for p in projects
        ]
        
        # Trouver l'index du projet actuel
        current_index = 0
        if st.session_state.current_project_id:
            for i, p in enumerate(projects):
                if p['id'] == st.session_state.current_project_id:
                    current_index = i + 1
                    break
        
        selected = st.selectbox(
            "Projet",
            project_options,
            index=current_index,
            key="sidebar_project_select",
            label_visibility="collapsed"
        )
        
        # Si un projet est sélectionné
        if selected and selected != "-- Sélectionner --":
            # Trouver l'ID du projet sélectionné
            for p in projects:
                if p['company_name'] == selected:
                    if st.session_state.current_project_id != p['id']:
                        st.session_state.current_project_id = p['id']
                        load_project_data_to_session(p['id'])
                        st.rerun()
                    break
        
        # Afficher le nom de l'entreprise si un projet est sélectionné
        if st.session_state.current_project_id:
            project_name = next(
                (p['company_name'] for p in projects if p['id'] == st.session_state.current_project_id),
                None
            )
            if project_name:
                st.caption(f"🏢 {project_name}")
    else:
        st.info("ℹ️ Aucun projet")
    
    # Bouton pour créer un nouveau projet
    if st.button("➕ Nouveau projet", use_container_width=True, key="sidebar_new_project"):
        st.session_state.show_new_project_modal = True
    
    # Modal pour créer un nouveau projet
    if st.session_state.get("show_new_project_modal", False):
        with st.container():
            st.markdown("### ➕ Créer un nouveau projet")
            new_company_name = st.text_input("Nom de l'entreprise", key="modal_new_company_name")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Créer", use_container_width=True, key="modal_create"):
                    if new_company_name.strip():
                        project_id = create_new_project(new_company_name.strip())
                        if project_id:
                            st.session_state.current_project_id = project_id
                            st.session_state.show_new_project_modal = False
                            load_project_data_to_session(project_id)
                            st.success(f"✅ Projet créé: {new_company_name}")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de la création du projet")
                    else:
                        st.warning("⚠️ Veuillez saisir un nom d'entreprise")
            with col2:
                if st.button("Annuler", use_container_width=True, key="modal_cancel"):
                    st.session_state.show_new_project_modal = False
                    st.rerun()
    
    return st.session_state.current_project_id is not None

def main():
    init_session_state()
    
    # Debug : afficher si l'authentification est activée (uniquement en développement)
    if os.getenv("DEV_MODE") == "1":
        auth_enabled = is_auth_enabled()
        auth_user = get_auth_username()
        st.sidebar.write(f"🔐 Auth enabled: {auth_enabled}")
        if auth_enabled:
            st.sidebar.write(f"👤 User: {auth_user}")
    
    # Vérifier l'authentification avant d'afficher le contenu
    if not check_authentication():
        display_login_page()
        return
    
    # Sidebar avec navigation
    with st.sidebar:
        st.title("🤖 aikoGPT")
        st.markdown("---")
        
        # Sélection de projet (obligatoire)
        project_selected = display_project_selector_in_sidebar()
        
        # Si aucun projet n'est sélectionné, afficher l'écran de sélection
        if not project_selected:
            st.markdown("---")
            st.warning("⚠️ Veuillez sélectionner ou créer un projet pour continuer")
            st.stop()
        
        st.markdown("---")
        
        # Initialiser la page si nécessaire
        if 'current_page' not in st.session_state:
            st.session_state.current_page = "Accueil"
        
        # Radio button Accueil en haut
        page_accueil = st.radio(
            "Navigation",
            ["Accueil"],
            index=0 if st.session_state.current_page == "Accueil" else None,
            key="nav_accueil"
        )
        
        # Section Documents et configuration
        st.markdown("**Documents et configuration**")
        page_docs = st.radio(
            "Navigation Documents et configuration",
            ["Upload de documents", "Contexte de l'entreprise", "Configuration des Intervieweurs"],
            index=0 if st.session_state.current_page == "Upload de documents" else (1 if st.session_state.current_page == "Contexte de l'entreprise" else (2 if st.session_state.current_page == "Configuration des Intervieweurs" else None)),
            key="nav_docs",
            label_visibility="collapsed"
        )
        
        # Section Rapport initial
        st.markdown("**Génération des Use Cases**")
        page_rapport = st.radio(
            "Navigation Génération des Use Cases",
            ["Générer les Use Cases"],
            index=0 if st.session_state.current_page == "Générer les Use Cases" else None,
            key="nav_rapport",
            label_visibility="collapsed"
        )
        
        # NOUVELLE SECTION : Validation des besoins et use cases
        st.markdown("**Validation des besoins et use cases**")
        page_word_validation = st.radio(
            "Navigation Validation des besoins et use cases",
            ["Validation des besoins et use cases"],
            index=0 if st.session_state.current_page == "Validation des besoins et use cases" else None,
            key="nav_word_validation",
            label_visibility="collapsed"
        )
        
        # Section Diag - Synthèse de mission
        st.markdown("**Génération du rapport**")
        page_diag = st.radio(
            "Navigation Génération du rapport",
            ["Génération des Enjeux et Recommandations", "Rappel de la mission", "Atouts de l'entreprise", "Chaîne de valeur", "Prérequis IA"],
            index=0 if st.session_state.current_page == "Génération des Enjeux et Recommandations" else (1 if st.session_state.current_page == "Rappel de la mission" else (2 if st.session_state.current_page == "Atouts de l'entreprise" else (3 if st.session_state.current_page == "Chaîne de valeur" else (4 if st.session_state.current_page == "Prérequis IA" else None)))),
            key="nav_diag",
            label_visibility="collapsed"
        )
        
        # Déterminer quelle page est sélectionnée
        # On vérifie chaque groupe et on met à jour si une sélection différente de la page actuelle est faite
        page = st.session_state.current_page
        page_changed = False
        
        if page_accueil == "Accueil" and st.session_state.current_page != "Accueil":
            page = "Accueil"
            st.session_state.current_page = "Accueil"
            page_changed = True
        elif page_docs and st.session_state.current_page != page_docs:
            page = page_docs
            st.session_state.current_page = page_docs
            page_changed = True
        elif page_rapport and st.session_state.current_page != page_rapport:
            page = page_rapport
            st.session_state.current_page = page_rapport
            page_changed = True
        elif page_word_validation and st.session_state.current_page != page_word_validation:
            page = page_word_validation
            st.session_state.current_page = page_word_validation
            page_changed = True
        elif page_diag and st.session_state.current_page != page_diag:
            page = page_diag
            st.session_state.current_page = page_diag
            page_changed = True
        
        # Si la page a changé, forcer un rerun pour mettre à jour immédiatement
        if page_changed:
            st.rerun()
        
        st.markdown("---")
        
        # Affichages de statut
        # Statut des transcripts
        transcript_count = len(st.session_state.get("uploaded_transcripts", []))
        if transcript_count == 0:
            st.warning("⚠️ Pas de transcript uploadé")
        else:
            st.success(f"✅ {transcript_count} transcript{'s' if transcript_count > 1 else ''} uploadé{'s' if transcript_count > 1 else ''}")
        
        # Statut des workshops
        workshop_count = len(st.session_state.get("uploaded_workshops", []))
        if workshop_count == 0:
            st.warning("⚠️ Pas de fichier Workshop uploadé")
        else:
            st.success(f"✅ {workshop_count} fichier{'s' if workshop_count > 1 else ''} workshop uploadé{'s' if workshop_count > 1 else ''}")
        
        # Statut des informations de l'entreprise
        validated_company_info = st.session_state.get("validated_company_info")
        if validated_company_info:
            company_name = validated_company_info.get("nom", "")
            if company_name:
                st.success(f"✅ Contexte d'entreprise validé : {company_name}")
            else:
                st.success("✅ Contexte d'entreprise validé")
        else:
            st.warning("⚠️ Aucune info d'entreprise")
        
        st.markdown("------")
        
        # Bouton de suppression de projet (si un projet est sélectionné)
        if st.session_state.current_project_id:
            projects = load_project_list()
            current_project = next(
                (p for p in projects if p['id'] == st.session_state.current_project_id),
                None
            )
            
            if current_project:
                project_name = current_project['company_name']
                
                # Gérer l'état de confirmation
                if 'confirm_delete_project' not in st.session_state:
                    st.session_state.confirm_delete_project = False
                
                if not st.session_state.confirm_delete_project:
                    # Premier clic : afficher le bouton de suppression
                    if st.button("🗑️ Supprimer les données du projet", use_container_width=True, key="delete_project_button"):
                        st.session_state.confirm_delete_project = True
                        st.rerun()
                else:
                    # Mode confirmation
                    st.warning(f"⚠️ Vous allez supprimer le projet '{project_name}' et toutes ses données")
                    st.warning("⚠️ Cette action est irréversible !")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Confirmer", key="confirm_delete_yes", use_container_width=True, type="primary"):
                            try:
                                from database.repository import ProjectRepository
                                from database.db import get_db_context
                                
                                project_id = st.session_state.current_project_id
                                
                                with get_db_context() as db:
                                    success = ProjectRepository.delete(db, project_id)
                                    
                                    if success:
                                        # Réinitialiser TOUTES les variables de session liées au projet
                                        st.session_state.current_project_id = None
                                        st.session_state.current_project = None
                                        st.session_state.project_loaded = False
                                        
                                        # Réinitialiser les uploads
                                        if 'uploaded_transcripts' in st.session_state:
                                            st.session_state.uploaded_transcripts = []
                                        if 'uploaded_workshops' in st.session_state:
                                            st.session_state.uploaded_workshops = []
                                        
                                        # Réinitialiser les informations de l'entreprise
                                        if 'validated_company_info' in st.session_state:
                                            st.session_state.validated_company_info = None
                                        if 'company_name' in st.session_state:
                                            st.session_state.company_name = ""
                                        if 'company_url' in st.session_state:
                                            st.session_state.company_url = ""
                                        if 'company_description' in st.session_state:
                                            st.session_state.company_description = ""
                                        
                                        # Réinitialiser les workflows
                                        if 'thread_id' in st.session_state:
                                            st.session_state.thread_id = None
                                        if 'workflow_status' in st.session_state:
                                            st.session_state.workflow_status = None
                                        if 'workflow_state' in st.session_state:
                                            st.session_state.workflow_state = {}
                                        
                                        # Réinitialiser les workflows Executive Summary
                                        if 'executive_thread_id' in st.session_state:
                                            st.session_state.executive_thread_id = None
                                        if 'executive_workflow_status' in st.session_state:
                                            st.session_state.executive_workflow_status = None
                                        if 'executive_workflow_state' in st.session_state:
                                            st.session_state.executive_workflow_state = {}
                                        if 'executive_final_results' in st.session_state:
                                            st.session_state.executive_final_results = None
                                        if 'executive_final_results_cached' in st.session_state:
                                            st.session_state.executive_final_results_cached = False
                                        
                                        # Réinitialiser les workflows Value Chain
                                        if 'value_chain_thread_id' in st.session_state:
                                            st.session_state.value_chain_thread_id = None
                                        if 'value_chain_workflow_status' in st.session_state:
                                            st.session_state.value_chain_workflow_status = None
                                        if 'value_chain_workflow_state' in st.session_state:
                                            st.session_state.value_chain_workflow_state = {}
                                        
                                        # Réinitialiser les workflows Atouts
                                        if 'atouts_thread_id' in st.session_state:
                                            st.session_state.atouts_thread_id = None
                                        if 'atouts_workflow_status' in st.session_state:
                                            st.session_state.atouts_workflow_status = None
                                        if 'atouts_workflow_state' in st.session_state:
                                            st.session_state.atouts_workflow_state = {}
                                        
                                        # Réinitialiser les résultats de recherche web
                                        if 'web_search_results' in st.session_state:
                                            st.session_state.web_search_results = None
                                        if 'trigger_web_search' in st.session_state:
                                            st.session_state.trigger_web_search = False
                                        
                                        # Réinitialiser les données validées
                                        if 'validated_needs' in st.session_state:
                                            st.session_state.validated_needs = []
                                        if 'validated_use_cases' in st.session_state:
                                            st.session_state.validated_use_cases = []
                                        if 'validated_challenges' in st.session_state:
                                            st.session_state.validated_challenges = []
                                        if 'validated_recommendations' in st.session_state:
                                            st.session_state.validated_recommendations = []
                                        
                                        # Retourner à la page d'accueil
                                        st.session_state.current_page = "Accueil"
                                        
                                        st.session_state.confirm_delete_project = False
                                        st.success(f"✅ Projet '{project_name}' supprimé avec succès")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("❌ Erreur lors de la suppression du projet")
                                        st.session_state.confirm_delete_project = False
                            except Exception as e:
                                st.error(f"❌ Erreur lors de la suppression: {str(e)}")
                                st.session_state.confirm_delete_project = False
                    with col2:
                        if st.button("❌ Annuler", key="cancel_delete_project", use_container_width=True):
                            st.session_state.confirm_delete_project = False
                            st.rerun()
        
        # Bouton de déconnexion
        if st.button("🚪 Se déconnecter", use_container_width=True, key="logout_button"):
            # Réinitialiser toutes les variables de session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
    # Afficher le contenu selon la page sélectionnée
    if page == "Accueil":
        display_home_page()
    elif page == "Upload de documents":
        display_upload_documents_section()
    elif page == "Contexte de l'entreprise":
        display_company_context_section()
    elif page == "Configuration des Intervieweurs":
        display_interviewers_config_page()
    elif page == "Générer les Use Cases":
        display_diagnostic_section()
    elif page == "Validation des besoins et use cases":
        display_word_validation_section()
    elif page == "Génération des Enjeux et Recommandations":
        display_recommendations_section()
        # display_work_in_progress()
    elif page == "challenges_validation":
        # Page dédiée pour la validation des enjeux
        display_challenges_validation_page()
    elif page == "Rappel de la mission":
        display_rappel_mission()
    elif page == "Atouts de l'entreprise":
        display_atouts_entreprise()
    elif page == "Chaîne de valeur":
        display_value_chain_page()
    elif page == "Prérequis IA":
        display_prerequis_evaluation_page()

def display_diagnostic_section():
    """Affiche la section de génération du diagnostic (utilise fichiers depuis session_state)"""
    st.header("🔍 Générer les Use Cases")
    
    # Vérifier d'abord si workflow_state contient des résultats finaux (workflow en cours terminé)
    workflow_state = st.session_state.get("workflow_state", {})
    final_needs = workflow_state.get("final_needs", [])
    final_use_cases = workflow_state.get("final_use_cases", [])
    
    # Variables pour suivre si les résultats viennent de la BDD
    results_from_db = False
    
    # Si pas de résultats dans workflow_state, vérifier dans la BDD
    if not final_needs and not final_use_cases and st.session_state.current_project_id:
        has_needs = has_validated_results(
            st.session_state.current_project_id,
            "need_analysis",
            "needs"
        )
        has_use_cases = has_validated_results(
            st.session_state.current_project_id,
            "need_analysis",
            "use_cases"
        )
        
        if has_needs or has_use_cases:
            results_from_db = True
            # Charger les résultats validés depuis la BDD
            validated_needs = load_agent_results(
                st.session_state.current_project_id,
                "need_analysis",
                "needs",
                "validated"
            )
            validated_use_cases = load_agent_results(
                st.session_state.current_project_id,
                "need_analysis",
                "use_cases",
                "validated"
            )
            
            if validated_needs:
                final_needs = validated_needs.get("needs", [])
            if validated_use_cases:
                final_use_cases = validated_use_cases.get("use_cases", [])
    
    # Vérifier le statut du workflow avant d'afficher les résultats finaux
    # Ne pas afficher les résultats si le workflow est en cours ou en attente de contexte
    workflow_status = None
    if st.session_state.get("thread_id"):
        try:
            workflow_status = poll_workflow_status()
        except Exception as e:
            print(f"⚠️ [DEBUG] Erreur lors de la vérification du statut: {e}")
            workflow_status = None
    
    # Afficher les résultats finaux uniquement si le workflow est terminé
    # ou si les résultats proviennent de la BDD (workflow précédent terminé)
    should_display_final_results = False
    if workflow_status == "completed":
        should_display_final_results = True
    elif workflow_status is None and (final_needs or final_use_cases):
        # Si pas de thread_id actif mais résultats présents, c'est probablement un workflow terminé précédemment
        # Vérifier si les résultats viennent de la BDD
        if results_from_db:
            should_display_final_results = True
    
    # Ne pas afficher les résultats si le workflow est en attente de contexte ou validation
    if workflow_status in ["waiting_pre_use_case_context", "waiting_use_case_validation", "waiting_validation"]:
        should_display_final_results = False
    
    # Afficher les résultats si disponibles et workflow terminé
    if should_display_final_results and (final_needs or final_use_cases):
        # Afficher directement les résultats finaux
        st.success("✅ **Workflow terminé - Résultats disponibles**")
        st.markdown("---")
        
        if final_needs:
            st.subheader(f"📋 Besoins identifiés ({len(final_needs)})")
            with st.expander("Voir les besoins", expanded=True):
                for i, need in enumerate(final_needs, 1):
                    st.markdown(f"### {i}. {need.get('theme', 'N/A')}")
                    quotes = need.get('quotes', [])
                    if quotes:
                        st.markdown("**Citations clés :**")
                        for quote in quotes:
                            st.markdown(f"• {quote}")
                    st.markdown("---")
        
        if final_use_cases:
            st.subheader(f"💼 Use Cases générés ({len(final_use_cases)})")
            with st.expander("Voir les use cases", expanded=True):
                for i, uc in enumerate(final_use_cases, 1):
                    st.markdown(f"### {i}. {uc.get('titre', 'N/A')}")
                    st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                    famille = uc.get('famille', '')
                    if famille:
                        st.markdown(f"**Famille :** {famille}")
                    st.markdown("---")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✏️ Modifier", use_container_width=True):
                # Rejeter les résultats pour permettre la modification
                if st.session_state.current_project_id:
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "need_analysis",
                        "needs"
                    )
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "need_analysis",
                        "use_cases"
                    )
                # Réinitialiser le workflow
                st.session_state.thread_id = None
                st.session_state.workflow_status = None
                if 'workflow_state' in st.session_state:
                    st.session_state.workflow_state = {}
                st.rerun()
        with col2:
            if st.button("🔄 Régénérer", use_container_width=True):
                # Rejeter les résultats existants
                if st.session_state.current_project_id:
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "need_analysis",
                        "needs"
                    )
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "need_analysis",
                        "use_cases"
                    )
                # Réinitialiser le workflow
                st.session_state.thread_id = None
                st.session_state.workflow_status = None
                if 'workflow_state' in st.session_state:
                    st.session_state.workflow_state = {}
                st.rerun()
        
        # Boutons de téléchargement (JSON et Word)
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            # Bouton de téléchargement JSON
            results_json = {
                "final_needs": final_needs,
                "final_use_cases": final_use_cases
            }
            st.download_button(
                label="📥 Télécharger les résultats (JSON)",
                data=json.dumps(results_json, indent=2, ensure_ascii=False),
                file_name="aiko_results.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Bouton de génération de rapport Word
            if st.button("📄 Générer le rapport Word", type="primary", use_container_width=True):
                # Préparer les données au format attendu par generate_word_report
                if 'workflow_state' not in st.session_state:
                    st.session_state.workflow_state = {}
                st.session_state.workflow_state['final_needs'] = final_needs
                st.session_state.workflow_state['final_use_cases'] = final_use_cases
                
                generate_word_report()
        
        return
    
    # Si le workflow est en cours, afficher la progression
    if st.session_state.thread_id and st.session_state.workflow_status is not None:
        display_workflow_progress()
        return
    
    st.info("💡 Cette section génère l'analyse des besoins et des cas d'usage. Les fichiers sont chargés depuis la section 'Upload de documents'.")
    
    # En mode DEV, skip la vérification des fichiers uploadés
    if not is_dev_mode():
        # Vérifier que les fichiers sont uploadés
        if not st.session_state.uploaded_transcripts and not st.session_state.uploaded_workshops:
            st.warning("⚠️ Veuillez d'abord uploader des fichiers dans la section 'Upload de documents'.")
            return
    
    # Vérifier le nom d'entreprise (depuis company_name ou validated_company_info)
    company_name = st.session_state.get("company_name") or (
        st.session_state.get("validated_company_info", {}).get("nom", "")
    )
    # En mode DEV, utiliser un nom par défaut si pas de nom d'entreprise
    if not company_name:
        if is_dev_mode():
            company_name = "Entreprise Test"
            st.session_state.company_name = company_name
        else:
            st.warning("⚠️ Veuillez d'abord saisir et valider le nom de l'entreprise dans la section 'Contexte de l'entreprise'.")
            return
    
    # Synchroniser company_name si nécessaire
    if not st.session_state.company_name and company_name:
        st.session_state.company_name = company_name
    
    st.metric("Entreprise", company_name)
    
    # Zone : Informations supplémentaires
    st.subheader("Informations Supplémentaires")
    st.info("💡 Vous pouvez ajouter ici des informations complémentaires qui ne sont pas présentes dans les transcriptions ou les ateliers.")
    additional_context = st.text_area(
        "Informations supplémentaires",
        placeholder="Ex: L'entreprise souhaite prioriser les solutions IA pour la R&D. Il y a également un projet de fusion prévu pour 2025 qui impacte la stratégie.",
        height=150,
        key="additional_context_input",
        label_visibility="hidden"
    )
    
    # Bouton de démarrage
    st.markdown("---")
    
    if st.session_state.uploaded_transcripts or st.session_state.uploaded_workshops:
        if st.button("🚀 Démarrer l'Analyse des Besoins", type="primary", width="stretch"):
            # Utiliser les fichiers depuis session_state
            # Étape 1 : Démarrage du workflow avec messages rotatifs
            messages = display_rotating_messages(st.session_state.company_name)
            status_placeholder = st.empty()
            
            # Créer une queue pour récupérer le résultat
            result_queue = queue.Queue()
            
            # Récupérer les interviewer_names depuis le fichier JSON
            interviewer_names = load_interviewers()
            
            # Lancer l'appel API dans un thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                # Passer directement les données complètes (avec document_ids)
                future = executor.submit(
                    start_workflow_api_call,
                    st.session_state.uploaded_workshops,
                    st.session_state.uploaded_transcripts,
                    st.session_state.company_name,
                    st.session_state.get("company_url", ""),
                    st.session_state.get("company_description", ""),
                    st.session_state.get("validated_company_info"),
                    interviewer_names,
                    additional_context or "",
                    result_queue
                )
                
                # Afficher des messages rotatifs pendant que l'API traite
                message_index = 0
                while not future.done():
                    status_placeholder.info(f"🔄 {messages[message_index % len(messages)]}")
                    time.sleep(3)  # Changer de message toutes les 3 secondes
                    message_index += 1
                
                # Récupérer le résultat
                try:
                    success, thread_id, status, error_msg = result_queue.get(timeout=1)
                    
                    if success:
                        st.session_state.thread_id = thread_id
                        st.session_state.workflow_status = status
                        # Sauvegarder le nom de l'entreprise dans session_state pour récupération ultérieure
                        if st.session_state.company_name and st.session_state.company_name.strip():
                            st.session_state.company_name_input = st.session_state.company_name.strip()
                            print(f"💾 [APP] Nom d'entreprise sauvegardé dans session_state: {st.session_state.company_name.strip()}")
                        
                        # En mode DEV, pré-remplir les besoins identifiés pour gagner du temps
                        if is_dev_mode():
                            debug_needs = [
                                {
                                    "theme": "Automatisation des processus administratifs",
                                    "quotes": [
                                        "Nous passons trop de temps sur les tâches administratives répétitives",
                                        "L'automatisation nous ferait gagner beaucoup de temps"
                                    ]
                                },
                                {
                                    "theme": "Optimisation de la performance commerciale",
                                    "quotes": [
                                        "Nous avons besoin de mieux suivre nos performances commerciales",
                                        "Un dashboard en temps réel serait très utile"
                                    ]
                                },
                                {
                                    "theme": "Gestion proactive des stocks",
                                    "quotes": [
                                        "Nous avons souvent des ruptures de stock",
                                        "Une meilleure prévision nous aiderait"
                                    ]
                                },
                                {
                                    "theme": "Formation et gestion des talents",
                                    "quotes": [
                                        "La formation de nos équipes est un enjeu majeur",
                                        "Nous avons besoin d'un système de suivi des compétences"
                                    ]
                                },
                                {
                                    "theme": "Amélioration de la qualité et conformité",
                                    "quotes": [
                                        "La conformité réglementaire est complexe",
                                        "Nous devons améliorer notre traçabilité"
                                    ]
                                },
                                {
                                    "theme": "Analyse prédictive des ventes",
                                    "quotes": [
                                        "Nous aimerions mieux prévoir nos ventes",
                                        "L'IA pourrait nous aider à anticiper les tendances"
                                    ]
                                },
                                {
                                    "theme": "Optimisation de la chaîne logistique",
                                    "quotes": [
                                        "Notre chaîne logistique peut être optimisée",
                                        "Nous cherchons à réduire les délais de livraison"
                                    ]
                                },
                                {
                                    "theme": "Amélioration de l'expérience client",
                                    "quotes": [
                                        "L'expérience client est notre priorité",
                                        "Nous voulons mieux comprendre nos clients"
                                    ]
                                },
                                {
                                    "theme": "Gestion intelligente des données",
                                    "quotes": [
                                        "Nous avons beaucoup de données mais ne savons pas les exploiter",
                                        "Un système de BI serait très utile"
                                    ]
                                },
                                {
                                    "theme": "Automatisation des réponses aux appels entrants",
                                    "quotes": [
                                        "Nous recevons beaucoup d'appels répétitifs",
                                        "Un chatbot pourrait nous aider"
                                    ]
                                }
                            ]
                            
                            # Initialiser workflow_state avec les besoins pré-remplis
                            if "workflow_state" not in st.session_state:
                                st.session_state.workflow_state = {}
                            
                            st.session_state.workflow_state["identified_needs"] = debug_needs
                            print(f"🔧 [DEBUG] {len(debug_needs)} besoins pré-remplis en mode DEBUG")
                        
                        status_placeholder.success(f"✅ Workflow démarré ! Thread ID: {thread_id[:8]}...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        status_placeholder.error(f"❌ Erreur lors du démarrage: {error_msg}")
                
                except queue.Empty:
                    status_placeholder.error("❌ Timeout lors de la récupération du résultat")
    else:
        st.info("👆 Veuillez uploader au moins un fichier pour démarrer")

def display_workflow_progress():
    """Affiche la progression du workflow et gère les validations"""
    
    st.markdown("---")
    st.header("🔄 Progression du Workflow")
    
    # Poll le statut
    status = poll_workflow_status()
    
    # Debug: afficher le statut détecté
    print(f"🔍 [DEBUG] display_workflow_progress - Statut détecté: {status}")
    
    if status == "running":
        st.info("⚙️ Le workflow est en cours d'exécution...")
        st.markdown("#### Étapes en cours :")
        st.markdown("""
        - 📝 Traitement des ateliers
        - 📄 Traitement des transcriptions
        - 🌐 Recherche web
        - 🔍 Analyse des besoins
        """)
        
        # Auto-refresh toutes les 3 secondes
        time.sleep(3)
        st.rerun()
    
    elif status == "waiting_validation":
        # Vérifier si identified_needs est vide (workflow peut être passé à l'étape suivante)
        identified_needs = st.session_state.workflow_state.get("identified_needs", [])
        if not identified_needs:
            # Si identified_needs est vide, le workflow a probablement passé à l'étape suivante
            # Faire plusieurs tentatives pour vérifier le statut (le checkpointer peut prendre du temps)
            print(f"🔍 [DEBUG] display_workflow_progress - identified_needs vide, re-vérification du statut")
            max_retries = 3
            for attempt in range(max_retries):
                time.sleep(1)
                status = poll_workflow_status()
                print(f"🔍 [DEBUG] display_workflow_progress - Tentative {attempt + 1}/{max_retries} - Statut: {status}")
                # Si le statut a changé, faire un rerun pour afficher la bonne interface
                if status != "waiting_validation":
                    print(f"✅ [DEBUG] display_workflow_progress - Statut changé vers: {status}")
                    st.rerun()
                    return
            # Si après toutes les tentatives, le statut est toujours waiting_validation mais identified_needs est vide,
            # c'est probablement une erreur - afficher un message d'info
            print(f"⚠️ [DEBUG] display_workflow_progress - Statut toujours waiting_validation après {max_retries} tentatives")
        
        st.warning("⏸️ **Validation requise !**")
        display_needs_validation_interface(status)
        # Pas de rerun automatique ici, l'utilisateur doit valider
        # Le rerun sera déclenché par display_needs_validation_interface() après la validation
    
    elif status == "waiting_pre_use_case_context":
        st.info("💡 **Préparation de la génération des cas d'usage**")
        display_pre_use_case_interrupt_interface()
        # Pas de rerun automatique ici, l'utilisateur doit fournir le contexte
    
    elif status == "waiting_use_case_validation":
        st.warning("⏸️ **Validation des cas d'usage requise !**")
        display_use_cases_validation_interface()
        # Pas de rerun automatique ici, l'utilisateur doit valider
    
    elif status == "completed":
        st.success("✅ **Workflow terminé avec succès !**")
        # Les résultats seront affichés par display_diagnostic_section() qui est appelée automatiquement
    
    elif status == "error":
        st.error("❌ Une erreur s'est produite")
    
    elif status == "no_thread":
        # Thread ID perdu, revenir à l'interface initiale
        st.session_state.thread_id = None
        st.session_state.workflow_status = None
        st.rerun()
    
    else:
        st.warning(f"⚠️ Statut inconnu: {status}")
        # Auto-refresh pour détecter les changements de statut
        time.sleep(3)
        st.rerun()

def display_needs_validation_interface(current_status: str = None):
    """
    Affiche l'interface de validation des besoins.
    Utilise StreamlitValidationInterface et envoie le résultat à l'API.
    
    Args:
        current_status: Le statut actuel du workflow (optionnel, sera vérifié si non fourni)
    """
    
    # Vérifier le statut actuel si non fourni
    if current_status is None:
        current_status = poll_workflow_status()
    
    # Debug: afficher le statut
    print(f"🔍 [DEBUG] display_needs_validation_interface - Statut: {current_status}")
    
    # Si le workflow n'est plus en attente de validation, ne pas afficher l'interface
    # Laisser display_workflow_progress() gérer l'affichage de l'étape suivante
    if current_status != "waiting_validation":
        print(f"🔍 [DEBUG] display_needs_validation_interface - Retour silencieux, statut={current_status}")
        return
    
    st.markdown("### Validation des Besoins Identifiés")
    
    identified_needs = st.session_state.workflow_state.get("identified_needs", [])
    validated_count = len(st.session_state.workflow_state.get("validated_needs", []))
    iteration_count = st.session_state.workflow_state.get("iteration_count", 0)
    
    # Si identified_needs est vide, ne pas afficher l'interface de validation
    # Cela peut arriver si tous les besoins ont été validés/rejetés et que le workflow est passé à l'étape suivante
    if not identified_needs:
        # Si identified_needs est vide ET que le statut n'est pas waiting_validation,
        # c'est que le workflow est passé à l'étape suivante
        # Ne pas afficher de message, juste retourner silencieusement
        # display_workflow_progress() gérera l'affichage de l'étape suivante
        print(f"🔍 [DEBUG] display_needs_validation_interface - identified_needs vide, statut={current_status}")
        return
    
    st.markdown("---")
    
    # ✅ UTILISER LA CLASSE pour afficher l'interface de validation
    # La classe retourne le résultat si l'utilisateur clique sur un bouton
    result = validation_interface.display_needs_for_validation(
        identified_needs=identified_needs,
        validated_count=validated_count,
        key_suffix=f"needs_{iteration_count}"  # Utiliser iteration_count pour réinitialiser les checkboxes
    )
    
    # Si un résultat est retourné, envoyer à l'API avec messages rotatifs
    if result is not None:
        user_action = result.get("user_action", "continue_needs")
        
        # Envoyer à l'API avec messages rotatifs
        validation_messages = [
            "📤 Envoi de votre validation...",
            "🤖 Analyse vos retours...",
            "⚙️ Traitement en cours..."
        ]
        
        status_placeholder = st.empty()
        result_queue = queue.Queue()
        
        # Lancer l'appel API dans un thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                send_validation_feedback_api_call,
                result['validated_needs'],
                result['rejected_needs'],
                result['user_feedback'],
                user_action,
                st.session_state.thread_id,
                result_queue
            )
            
            # Afficher des messages rotatifs pendant le traitement
            message_index = 0
            while not future.done():
                status_placeholder.info(f"🔄 {validation_messages[message_index % len(validation_messages)]}")
                time.sleep(2)  # Changer de message toutes les 2 secondes
                message_index += 1
            
            # Récupérer le résultat
            try:
                success, error_msg = result_queue.get(timeout=1)
                
                if success:
                    status_placeholder.success("✅ Validation envoyée ! Le workflow reprend...")
                    
                    # Gestion différente selon l'action de l'utilisateur
                    if user_action == "continue_to_use_cases":
                        # Pour "passer aux use cases", attendre plus longtemps car le workflow doit passer à pre_use_case_interrupt
                        # Le checkpointer peut prendre du temps à sauvegarder l'état
                        max_retries = 5
                        retry_delay = 1.5
                        new_status = None
                        
                        for attempt in range(max_retries):
                            time.sleep(retry_delay)
                            try:
                                new_status = poll_workflow_status()
                                print(f"🔍 [DEBUG] Tentative {attempt + 1}/{max_retries} - Statut: {new_status}")
                                
                                if new_status == "waiting_pre_use_case_context":
                                    print(f"✅ [DEBUG] Statut correct détecté après {attempt + 1} tentatives")
                                    time.sleep(0.5)
                                    st.rerun()
                                    return
                            except Exception as e:
                                print(f"⚠️ [DEBUG] Erreur lors du polling (tentative {attempt + 1}): {e}")
                        
                        # Si après toutes les tentatives, le statut n'est toujours pas bon, faire un rerun quand même
                        # display_workflow_progress() gérera l'affichage avec la vérification supplémentaire
                        print(f"⚠️ [DEBUG] Statut final après {max_retries} tentatives: {new_status}")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        # Pour "continue_needs", logique normale
                        time.sleep(2)
                        try:
                            new_status = poll_workflow_status()
                            time.sleep(0.5)
                            st.rerun()
                        except Exception as e:
                            print(f"⚠️ [DEBUG] Erreur lors du polling après validation: {e}")
                            time.sleep(1.5)
                            st.rerun()
                else:
                    status_placeholder.error(f"❌ Erreur : {error_msg}")
            
            except queue.Empty:
                status_placeholder.error("❌ Timeout lors de la validation")

def display_pre_use_case_interrupt_interface():
    """
    Affiche l'interface avant la génération des use cases.
    Affiche les besoins validés avec leurs citations et un champ pour le contexte additionnel.
    """

    poll_workflow_status()
    
    st.markdown("### 📋 Besoins Validés - Préparation de la Génération des Cas d'Usage")
    
    # Afficher les besoins validés avec leurs citations
    final_needs = st.session_state.workflow_state.get("final_needs", [])
    
    if not final_needs:
        # Essayer aussi validated_needs si final_needs est vide
        final_needs = st.session_state.workflow_state.get("validated_needs", [])
    
    if final_needs:
        st.success(f"✅ **{len(final_needs)} besoin(s) validé(s)**")
        st.markdown("---")
        
        # Afficher les besoins avec leurs citations - 2 par ligne
        for i in range(0, len(final_needs), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Premier besoin de la ligne
            with col1:
                need = final_needs[i]
                theme = need.get('theme', 'Thème non défini')
                quotes = need.get('quotes', [])
                
                st.markdown(f"**{i+1}. {theme}**")
                
                # Afficher les citations si disponibles
                if quotes:
                    st.markdown("*Citations:*")
                    for quote in quotes:
                        st.text(f"• {quote}")
                else:
                    st.info("Aucune citation disponible")
            
            # Deuxième besoin de la ligne (si existant)
            if i + 1 < len(final_needs):
                with col2:
                    need = final_needs[i + 1]
                    theme = need.get('theme', 'Thème non défini')
                    quotes = need.get('quotes', [])
                    
                    st.markdown(f"**{i+2}. {theme}**")
                    
                    # Afficher les citations si disponibles
                    if quotes:
                        st.markdown("*Citations:*")
                        for quote in quotes:
                            st.text(f"• {quote}")
                    else:
                        st.info("Aucune citation disponible")
            
            # Ligne de séparation fine entre les besoins
            st.markdown("---")
    else:
        st.warning("⚠️ Aucun besoin validé trouvé")
        st.markdown("---")
    
    # Champ pour le contexte additionnel
    st.markdown("#### Instructions pour la Génération des Cas d'Usage")
    st.markdown("Ajoutez des commentaires ou instructions pour guider la génération des cas d'usage :")
    
    additional_context = st.text_area(
        "Commentaires et instructions (optionnel) :",
        placeholder="Ex: Génère 15 cas d'usage en priorisant l'automatisation des processus métier. Classifie par famille : automatisation, prédiction, optimisation...",
        height=150,
        key="use_case_additional_context_input",
        label_visibility="hidden"
    )
    
    st.markdown("---")
    
    # Bouton pour continuer
    if st.button("✅ Générer les Cas d'Usage", type="primary", use_container_width=True):
        # Envoyer le contexte additionnel à l'API
        status_placeholder = st.empty()
        result_queue = queue.Queue()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                send_pre_use_case_context_api_call,
                additional_context,
                st.session_state.thread_id,
                result_queue
            )
            
            status_placeholder.info("🔄 Envoi du contexte...")
            
            try:
                success, error_msg = result_queue.get(timeout=180)  # 3 minutes pour permettre la génération des cas d'usage
                
                if success:
                    status_placeholder.success("✅ Contexte envoyé ! Génération des cas d'usage en cours...")
                    time.sleep(1)
                    st.rerun()
                else:
                    status_placeholder.error(f"❌ Erreur : {error_msg}")
            
            except queue.Empty:
                status_placeholder.error("❌ Timeout lors de l'envoi")

def display_use_cases_validation_interface():
    """
    Affiche l'interface de validation des use cases.
    Utilise StreamlitUseCaseValidation et envoie le résultat à l'API.
    """
    
    st.markdown("### Validation des Cas d'Usage")
    
    proposed_use_cases = st.session_state.workflow_state.get("proposed_use_cases", [])
    validated_count = len(st.session_state.workflow_state.get("validated_use_cases", []))
    use_case_iteration_count = st.session_state.workflow_state.get("use_case_iteration_count", 0)
    
    st.markdown("---")
    
    # ✅ UTILISER LA CLASSE pour afficher l'interface de validation
    # La classe retourne le résultat si l'utilisateur clique sur "Valider"
    result = use_case_validation.display_use_cases_for_validation(
        use_cases=proposed_use_cases,
        validated_count=validated_count,
        key_suffix=f"use_cases_{use_case_iteration_count}"  # Utiliser use_case_iteration_count pour réinitialiser les checkboxes
    )
    
    # Si un résultat est retourné, envoyer à l'API avec messages rotatifs
    if result is not None:
        # Envoyer à l'API avec messages rotatifs
        validation_messages = [
            "📤 Envoi de votre validation finale...",
            "🤖 L'IA finalise l'analyse...",
            "📊 Génération du rapport final...",
            "⚙️ Derniers ajustements..."
        ]
        
        status_placeholder = st.empty()
        result_queue = queue.Queue()
        
        # Lancer l'appel API dans un thread
        use_case_user_action = result.get("use_case_user_action", "finalize_use_cases")
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                send_use_case_validation_feedback_api_call,
                result['validated_use_cases'],
                result['rejected_use_cases'],
                result['user_feedback'],
                use_case_user_action,
                st.session_state.thread_id,
                result_queue
            )
            
            # Afficher des messages rotatifs pendant le traitement
            message_index = 0
            while not future.done():
                status_placeholder.info(f"🔄 {validation_messages[message_index % len(validation_messages)]}")
                time.sleep(2)  # Changer de message toutes les 2 secondes
                message_index += 1
            
            # Récupérer le résultat
            try:
                result_data = result_queue.get(timeout=1)
                
                # Gérer les deux formats possibles : (success, data) ou (success, error_msg)
                if isinstance(result_data, tuple) and len(result_data) == 2:
                    success, data = result_data
                    if success:
                        # data contient maintenant la réponse complète de l'API
                        if isinstance(data, dict):
                            # Mettre à jour workflow_state avec les final_results de l'API
                            final_results = data.get("final_results", {})
                            if final_results:
                                # Mettre à jour workflow_state avec les résultats finaux
                                if "final_needs" in final_results:
                                    st.session_state.workflow_state["final_needs"] = final_results.get("final_needs", [])
                                if "final_use_cases" in final_results:
                                    st.session_state.workflow_state["final_use_cases"] = final_results.get("final_use_cases", [])
                                
                                # Mettre à jour aussi les autres champs si présents
                                for key in ["workshop_results", "transcript_results", "summary"]:
                                    if key in final_results:
                                        st.session_state.workflow_state[key] = final_results[key]
                            
                            # Déterminer le message selon l'action
                            if use_case_user_action == "finalize_use_cases":
                                st.session_state.workflow_status = "completed"
                                
                                # Sauvegarder les résultats finaux dans la base de données
                                if st.session_state.current_project_id:
                                    try:
                                        # Utiliser les données de final_results si disponibles, sinon workflow_state
                                        final_needs = final_results.get("final_needs") if final_results else st.session_state.workflow_state.get("final_needs", [])
                                        if final_needs:
                                            save_agent_result(
                                                project_id=st.session_state.current_project_id,
                                                workflow_type="need_analysis",
                                                result_type="needs",
                                                data={"needs": final_needs},
                                                status="validated"
                                            )
                                        
                                        # Utiliser les données de final_results si disponibles, sinon workflow_state
                                        final_use_cases = final_results.get("final_use_cases") if final_results else st.session_state.workflow_state.get("final_use_cases", [])
                                        if final_use_cases:
                                            save_agent_result(
                                                project_id=st.session_state.current_project_id,
                                                workflow_type="need_analysis",
                                                result_type="use_cases",
                                                data={"use_cases": final_use_cases},
                                                status="validated"
                                            )
                                    except Exception as e:
                                        st.warning(f"⚠️ Erreur lors de la sauvegarde en base de données: {str(e)}")
                                
                                status_placeholder.success("✅ Validation envoyée ! Le workflow est terminé !")
                            else:
                                status_placeholder.success("✅ Validation envoyée ! Régénération des use cases en cours...")
                        else:
                            # Format ancien (True, None) - pas de données à mettre à jour
                            if use_case_user_action == "finalize_use_cases":
                                st.session_state.workflow_status = "completed"
                                status_placeholder.success("✅ Validation envoyée ! Le workflow est terminé !")
                            else:
                                status_placeholder.success("✅ Validation envoyée ! Régénération des use cases en cours...")
                        
                        # Forcer une mise à jour de l'état depuis le checkpointer
                        # pour s'assurer que tous les champs sont à jour
                        try:
                            poll_workflow_status()
                        except Exception as e:
                            print(f"⚠️ Erreur lors du polling après validation: {str(e)}")
                        
                        time.sleep(1)
                        st.rerun()
                    else:
                        # data contient le message d'erreur
                        error_msg = data if isinstance(data, str) else "Erreur inconnue"
                        status_placeholder.error(f"❌ Erreur : {error_msg}")
                else:
                    # Format inattendu
                    status_placeholder.error(f"❌ Format de réponse inattendu")
            
            except queue.Empty:
                status_placeholder.error("❌ Timeout lors de la validation")

def generate_word_report():
    """
    Génère un rapport Word à partir des résultats d'analyse.
    """
    with st.spinner("📝 Génération du rapport Word en cours..."):
        try:
            # Récupérer le nom de l'entreprise depuis workflow_state
            company_name = "Entreprise"  # Valeur par défaut
            
            workflow_state = st.session_state.workflow_state
            
            # Essayer plusieurs sources dans l'ordre de priorité
            # 1. D'abord vérifier company_info directement (source principale du workflow)
            if workflow_state.get('company_info'):
                company_info = workflow_state['company_info']
                potential_name = company_info.get('company_name', '')
                if potential_name and potential_name.strip():
                    company_name = potential_name.strip()
                    print(f"🏢 [REPORT] Nom d'entreprise trouvé dans workflow_state.company_info: {company_name}")
            
            # 2. Ensuite vérifier web_search_results (peut contenir le nom enrichi)
            if (company_name == "Entreprise" and workflow_state.get('web_search_results')):
                web_search = workflow_state['web_search_results']
                potential_name = web_search.get('company_name', '')
                if potential_name and potential_name.strip():
                    company_name = potential_name.strip()
                    print(f"🏢 [REPORT] Nom d'entreprise trouvé dans workflow_state.web_search_results: {company_name}")
            
            # 3. Vérifier aussi dans session_state si le nom a été saisi directement (fallback)
            if company_name == "Entreprise":
                potential_name = st.session_state.get('company_name_input', '')
                if potential_name and potential_name.strip():
                    company_name = potential_name.strip()
                    print(f"🏢 [REPORT] Nom d'entreprise trouvé dans session_state.company_name_input: {company_name}")
            
            # Formater le nom de l'entreprise (première lettre en majuscule pour chaque mot)
            if company_name and company_name != "Entreprise":
                company_name = company_name.title()
                print(f"✨ [REPORT] Nom formaté: {company_name}")
            
            print(f"🏢 [REPORT] Nom final de l'entreprise: {company_name}")
            
            # Récupérer les données depuis workflow_state
            final_needs = workflow_state.get('final_needs', [])
            final_use_cases = workflow_state.get('final_use_cases', [])
            
            # Vérifier qu'on a au moins des données à exporter
            if not final_needs and not final_use_cases:
                st.warning("⚠️ Aucune donnée à exporter. Veuillez d'abord valider des besoins et des cas d'usage.")
                return
            
            # Initialiser le générateur de rapport
            report_generator = ReportGenerator()
            
            # Générer le rapport
            output_path = report_generator.generate_report(
                company_name=company_name,
                final_needs=final_needs,
                final_use_cases=final_use_cases
            )
            
            st.success(f"✅ Rapport généré avec succès !")
            st.info(f"📁 Fichier sauvegardé : `{output_path}`")
            
            # Sauvegarder dans session_state
            st.session_state.word_path = output_path
            
            # Sauvegarder dans la base de données si un projet est sélectionné
            if st.session_state.current_project_id:
                try:
                    # Parser et sauvegarder directement avec DocumentParserService
                    file_name = os.path.basename(output_path)
                    document_parser_service.parse_and_save_word_report(
                        file_path=output_path,
                        project_id=st.session_state.current_project_id,
                        file_name=file_name,
                        metadata={}
                    )
                except Exception as e:
                    st.warning(f"⚠️ Erreur lors de la sauvegarde en base de données: {str(e)}")
            
            # Proposer le téléchargement du fichier
            with open(output_path, 'rb') as f:
                st.download_button(
                    label="📥 Télécharger le rapport Word",
                    data=f,
                    file_name=os.path.basename(output_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    width="stretch"
                )
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du rapport : {str(e)}")
            st.exception(e)

def display_upload_documents_section():
    """Section pour uploader et gérer les documents de manière persistante (session)"""
    st.header("Upload de Documents")
    st.info("💡 Uploadez vos fichiers ici. Ils seront conservés pendant toute la session et réutilisables dans les workflows.")
    
    # Initialiser le tracking des fichiers déjà uploadés
    if 'uploaded_file_names' not in st.session_state:
        st.session_state.uploaded_file_names = set()
    
    # Initialiser l'état pour le formulaire de transcript
    if 'current_transcript_file_path' not in st.session_state:
        st.session_state.current_transcript_file_path = None
    if 'current_transcript_speakers' not in st.session_state:
        st.session_state.current_transcript_speakers = []
    if 'transcript_classification_in_progress' not in st.session_state:
        st.session_state.transcript_classification_in_progress = False
    
    # Upload Transcripts - un par un
    st.subheader("Transcriptions (PDF ou JSON)")
    
    # Si on a un transcript en cours de traitement, afficher le formulaire
    if st.session_state.current_transcript_file_path and st.session_state.current_transcript_speakers:
        st.markdown("---")
        st.markdown("### Configuration du transcript")
        
        # Afficher le nom du fichier
        filename = os.path.basename(st.session_state.current_transcript_file_path)
        st.caption(f"Fichier: {filename}")
        
        # Formulaire pour les speakers
        st.markdown("**Intervenants :**")
        st.caption("💡 Vous pouvez supprimer les speakers qui ne sont pas des participants directs (ex: personnes citées)")
        
        # Ajouter un identifiant unique à chaque speaker s'il n'existe pas déjà
        if 'current_transcript_speakers' in st.session_state:
            for speaker in st.session_state.current_transcript_speakers:
                if 'unique_id' not in speaker:
                    speaker['unique_id'] = str(uuid.uuid4())
        
        # Gérer la suppression de speakers par identifiant unique
        if 'delete_speaker_id' in st.session_state:
            speaker_id_to_delete = st.session_state.delete_speaker_id
            st.session_state.current_transcript_speakers = [
                s for s in st.session_state.current_transcript_speakers 
                if s.get('unique_id') != speaker_id_to_delete
            ]
            del st.session_state.delete_speaker_id
            st.rerun()
        
        updated_speakers = []
        
        for idx, speaker in enumerate(st.session_state.current_transcript_speakers):
            # S'assurer que chaque speaker a un identifiant unique
            if 'unique_id' not in speaker:
                speaker['unique_id'] = str(uuid.uuid4())
            
            speaker_unique_id = speaker.get('unique_id')
            is_interviewer = speaker.get("is_interviewer", False)
            
            # Colonnes : Nom, Rôle, Level (si interviewé), Type, Supprimer
            if is_interviewer:
                col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
            else:
                col1, col2, col3, col4, col5 = st.columns([2.5, 2.5, 2, 1, 1])
            
            with col1:
                speaker_name = st.text_input(
                    "Nom",
                    value=speaker.get("name", ""),
                    key=f"speaker_name_{speaker_unique_id}"
                )
            with col2:
                speaker_role = st.text_input(
                    "Rôle",
                    value=speaker.get("role", ""),
                    key=f"speaker_role_{speaker_unique_id}"
                )
            
            # Afficher le level seulement pour les interviewés
            if not is_interviewer:
                with col3:
                    current_level = speaker.get("level", "inconnu")
                    # Si level est None, None ou vide, afficher "inconnu" comme valeur par défaut
                    if not current_level or current_level == "None" or current_level == "":
                        current_level = "inconnu"
                    
                    # Options pour la liste déroulante
                    level_options = ["direction", "métier", "inconnu"]
                    # Index par défaut
                    default_index = level_options.index(current_level) if current_level in level_options else 2
                    
                    selected_level = st.selectbox(
                        "Niveau",
                        options=level_options,
                        index=default_index,
                        key=f"speaker_level_{speaker_unique_id}",
                        help="Sélectionnez le niveau hiérarchique du speaker"
                    )
            
            with col4:
                if is_interviewer:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("Interviewer")
                else:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("Participant")
            
            if not is_interviewer:
                with col5:
                    # Bouton supprimer (sauf pour les interviewers)
                    if st.button("🗑️", key=f"delete_speaker_{speaker_unique_id}", help="Supprimer ce speaker"):
                        st.session_state.delete_speaker_id = speaker_unique_id
                        st.rerun()
            
            # Construire le dictionnaire du speaker
            speaker_dict = {
                "name": speaker_name,
                "role": speaker_role,
                "is_interviewer": is_interviewer,
                "unique_id": speaker_unique_id
            }
            
            # Ajouter le level seulement pour les interviewés
            if not is_interviewer:
                speaker_dict["level"] = selected_level
            else:
                speaker_dict["level"] = None  # Interviewers n'ont pas de level
            
            updated_speakers.append(speaker_dict)
        
        st.session_state.current_transcript_speakers = updated_speakers
        
        # Bouton pour ajouter un nouveau speaker
        st.markdown("---")
        with st.expander("➕ Ajouter un speaker manuellement"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_speaker_name = st.text_input(
                    "Nom du nouveau speaker",
                    key="new_speaker_name_input",
                    placeholder="Ex: Jean Dupont"
                )
            with col2:
                new_speaker_role = st.text_input(
                    "Rôle du nouveau speaker",
                    key="new_speaker_role_input",
                    placeholder="Ex: Directeur Commercial"
                )
            with col3:
                new_speaker_level = st.selectbox(
                    "Niveau",
                    options=["direction", "métier", "inconnu"],
                    index=2,  # "inconnu" par défaut
                    key="new_speaker_level_input",
                    help="Sélectionnez le niveau hiérarchique du speaker"
                )
            
            if st.button("➕ Ajouter ce speaker", key="add_new_speaker_btn"):
                if new_speaker_name and new_speaker_name.strip():
                    new_speaker = {
                        "name": new_speaker_name.strip(),
                        "role": new_speaker_role.strip() if new_speaker_role else "",
                        "level": new_speaker_level,  # Level sélectionné par l'utilisateur
                        "is_interviewer": False,
                        "unique_id": str(uuid.uuid4())
                    }
                    st.session_state.current_transcript_speakers.append(new_speaker)
                    st.rerun()
                else:
                    st.warning("⚠️ Veuillez saisir au moins un nom")
        
        # Boutons de validation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Valider", type="primary", key="validate_transcript"):
                # Vérifier qu'au moins un speaker non-interviewer est validé
                non_interviewer_speakers = [s for s in updated_speakers if not s.get("is_interviewer", False)]
                if not non_interviewer_speakers:
                    st.error("❌ Vous devez valider au moins un speaker interviewé avant de sauvegarder.")
                    st.stop()
                
                # Préparer les speakers avec level (sélectionné par l'utilisateur ou depuis l'API)
                validated_speakers_list = []
                for speaker in updated_speakers:
                    # Pour les interviewers, level est None
                    # Pour les interviewés, level est sélectionné via la liste déroulante
                    level = speaker.get("level")
                    if not level and not speaker.get("is_interviewer", False):
                        # Si pas de level et que ce n'est pas un interviewer, mettre "inconnu" par défaut
                        level = "inconnu"
                    
                    speaker_dict = {
                        "name": speaker["name"],
                        "role": speaker.get("role", ""),
                        "level": level,
                        "is_interviewer": speaker.get("is_interviewer", False)
                    }
                    validated_speakers_list.append(speaker_dict)
                
                # Sauvegarder dans la base de données si un projet est sélectionné
                document_id = None
                file_name = None
                if st.session_state.current_project_id:
                    # Vérifier que le fichier existe avant de le parser
                    from pathlib import Path
                    file_path_obj = Path(st.session_state.current_transcript_file_path)
                    if not file_path_obj.exists():
                        st.error(f"❌ Le fichier n'existe pas : {st.session_state.current_transcript_file_path}")
                        st.error(f"   Vérifiez que le fichier a bien été uploadé et que le chemin est correct.")
                        st.stop()
                    
                    try:
                        # Parser et sauvegarder directement avec DocumentParserService
                        file_name = os.path.basename(st.session_state.current_transcript_file_path)
                        document_id = document_parser_service.parse_and_save_transcript(
                            file_path=st.session_state.current_transcript_file_path,
                            project_id=st.session_state.current_project_id,
                            file_name=file_name,
                            validated_speakers=validated_speakers_list  # Passer les speakers validés avec level
                        )
                    except ValueError as e:
                        st.error(f"❌ {str(e)}")
                        st.stop()
                    except FileNotFoundError as e:
                        st.error(f"❌ {str(e)}")
                        st.error(f"   Le fichier a peut-être été supprimé ou n'est pas accessible.")
                        st.stop()
                    except Exception as e:
                        st.error(f"❌ Erreur lors de la sauvegarde en base de données: {str(e)}")
                        import traceback
                        st.error(f"**Détails de l'erreur :**")
                        st.code(traceback.format_exc())
                        st.stop()
                else:
                    st.error("❌ Veuillez d'abord sélectionner un projet avant de valider le transcript.")
                    st.stop()
                
                # Vérifier que document_id a bien été créé
                if document_id is None:
                    st.error("❌ Erreur : Le document n'a pas pu être sauvegardé. Veuillez réessayer.")
                    st.stop()
                
                # Sauvegarder le transcript dans la liste (pour compatibilité avec workflows)
                transcript_data = {
                    "file_path": st.session_state.current_transcript_file_path,
                    "file_name": file_name,  # NOUVEAU: Sauvegarder le nom du fichier
                    "document_id": document_id,  # NOUVEAU: Stocker document_id
                    "speakers": [
                        {"name": s["name"], "role": s["role"]}
                        for s in updated_speakers
                        if not s.get("is_interviewer", False)  # Exclure les interviewers
                    ]
                }
                
                # Ajouter à la liste des transcripts
                if 'uploaded_transcripts' not in st.session_state:
                    st.session_state.uploaded_transcripts = []
                st.session_state.uploaded_transcripts.append(transcript_data)
                
                # Réinitialiser l'état pour permettre un nouvel upload
                st.session_state.current_transcript_file_path = None
                st.session_state.current_transcript_speakers = []
                st.session_state.transcript_classification_in_progress = False
                
                st.success("✅ Transcript sauvegardé avec succès !")
                st.rerun()
        
        with col2:
            if st.button("❌ Annuler", key="cancel_transcript"):
                # Réinitialiser l'état
                st.session_state.current_transcript_file_path = None
                st.session_state.current_transcript_speakers = []
                st.session_state.transcript_classification_in_progress = False
                st.rerun()
        
        st.markdown("---")
    
    # Upload d'un nouveau transcript (seulement si aucun en cours)
    if not st.session_state.current_transcript_file_path:
        uploaded_transcript = st.file_uploader(
            "Uploadez un transcript (PDF ou JSON)",
            type=["pdf", "json"],
            accept_multiple_files=False,
            key="upload_transcript_single"
        )
        
        if uploaded_transcript:
            if st.button("🔍 Classifier les speakers", type="primary", key="classify_speakers"):
                # Upload le fichier
                with st.spinner("Upload du fichier..."):
                    try:
                        transcript_paths = upload_files_to_api([uploaded_transcript])
                        new_paths = transcript_paths.get("transcript", [])
                        
                        if not new_paths:
                            st.error("❌ Erreur lors de l'upload du fichier")
                        else:
                            file_path = new_paths[0]
                            
                            # Construire le dictionnaire des rôles connus depuis les transcripts précédents
                            known_speakers = {}
                            if 'uploaded_transcripts' in st.session_state:
                                for transcript in st.session_state.uploaded_transcripts:
                                    for speaker in transcript.get("speakers", []):
                                        speaker_name = speaker.get("name", "")
                                        speaker_role = speaker.get("role", "")
                                        if speaker_name and speaker_role:
                                            known_speakers[speaker_name] = speaker_role
                            
                            # Appeler l'API pour classifier les speakers
                            st.session_state.transcript_classification_in_progress = True
                            with st.spinner("🔍 Classification des speakers en cours..."):
                                try:
                                    response = requests.post(
                                        f"{API_URL}/transcripts/classify-speakers",
                                        json={
                                            "file_path": file_path,
                                            "interviewer_names": None,  # Utiliser les valeurs par défaut
                                            "known_speakers": known_speakers
                                        }
                                    )
                                    response.raise_for_status()
                                    result = response.json()
                                    
                                    # Sauvegarder les données dans session_state
                                    st.session_state.current_transcript_file_path = file_path
                                    st.session_state.current_transcript_speakers = result.get("speakers", [])
                                    st.session_state.transcript_classification_in_progress = False
                                    
                                    st.success("✅ Classification terminée !")
                                    st.rerun()
                                    
                                except requests.exceptions.RequestException as e:
                                    st.error(f"❌ Erreur lors de la classification: {str(e)}")
                                    st.session_state.transcript_classification_in_progress = False
                                    
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'upload: {str(e)}")
                        st.session_state.transcript_classification_in_progress = False
    
    # Afficher les transcripts déjà uploadés et validés
    if st.session_state.get("uploaded_transcripts"):
        st.markdown("---")
        st.markdown("**Transcripts sauvegardés :**")
        for idx, transcript in enumerate(st.session_state.uploaded_transcripts):
            # Utiliser document_id si disponible, sinon file_name
            document_id = transcript.get("document_id")
            file_name = transcript.get("file_name", "")
            
            # Si pas de file_name, utiliser document_id comme identifiant
            if not file_name and document_id:
                file_name = f"Transcript (ID: {document_id})"
            elif not file_name:
                file_name = "Transcript (nom inconnu)"
            
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**{file_name}**")
                speakers = transcript.get("speakers", [])
                if speakers:
                    speakers_text = " | ".join([
                        f"{s.get('name', '')} ({s.get('role', 'N/A')})"
                        for s in speakers
                        if not s.get("is_interviewer", False)  # Exclure les interviewers
                    ])
                    if speakers_text:
                        st.caption(f"Intervenants: {speakers_text}")
            with col2:
                if st.button("🗑️", key=f"delete_transcript_{idx}", help="Supprimer"):
                    # Supprimer de la base de données si un projet est sélectionné
                    if st.session_state.current_project_id and document_id:
                        try:
                            from database.repository import DocumentRepository
                            from database.db import get_db_context
                            with get_db_context() as db:
                                DocumentRepository.delete(db, document_id)
                        except Exception as e:
                            st.warning(f"⚠️ Erreur lors de la suppression: {str(e)}")
                    # Supprimer de la session state
                    st.session_state.uploaded_transcripts.pop(idx)
                    st.rerun()
    
    st.markdown("---")
    
    # Upload Workshops
    st.subheader("Ateliers (Fichiers Excel)")
    uploaded_workshops = st.file_uploader(
        "Uploadez vos fichiers d'ateliers",
        type=["xlsx"],
        accept_multiple_files=True,
        key="upload_workshops_persistent"
    )
    
    if uploaded_workshops:
        # Filtrer uniquement les nouveaux fichiers (ceux qui n'ont pas encore été uploadés)
        new_workshops = [
            f for f in uploaded_workshops 
            if f.name not in st.session_state.uploaded_file_names
        ]
        
        if new_workshops:
            # Sauvegarder dans session_state
            workshop_paths = upload_files_to_api(new_workshops)
            new_paths = workshop_paths.get("workshop", [])
            
            # Convertir les nouveaux chemins en dictionnaires pour cohérence
            new_workshop_dicts = [
                {
                    "file_path": path,
                    "extracted_text": "",
                    "file_name": os.path.basename(path),
                }
                for path in new_paths
            ]
            
            # Sauvegarder dans la base de données si un projet est sélectionné
            if not st.session_state.current_project_id:
                st.error("❌ Veuillez d'abord sélectionner un projet avant d'uploader les workshops.")
                st.stop()
            
            try:
                from database.repository import WorkshopRepository
                from database.db import get_db_context
                
                for i, file_path in enumerate(new_paths):
                    # Vérifier que le fichier existe avant de le parser
                    from pathlib import Path
                    file_path_obj = Path(file_path)
                    if not file_path_obj.exists():
                        st.error(f"❌ Le fichier n'existe pas : {file_path}")
                        st.error(f"   Vérifiez que le fichier a bien été uploadé et que le chemin est correct.")
                        continue
                    
                    # Parser et sauvegarder directement avec DocumentParserService
                    file_name = os.path.basename(file_path)
                    try:
                        document_id = document_parser_service.parse_and_save_workshop(
                            file_path=file_path,
                            project_id=st.session_state.current_project_id,
                            file_name=file_name,
                            metadata={}
                        )
                    except FileNotFoundError as e:
                        st.error(f"❌ {str(e)}")
                        st.error(f"   Le fichier a peut-être été supprimé ou n'est pas accessible.")
                        continue
                    except Exception as e:
                        st.error(f"❌ Erreur lors du parsing du fichier {file_name}: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
                        continue
                    
                    # Vérifier que document_id a bien été créé
                    if document_id is None:
                        st.error(f"❌ Erreur : Le document {file_name} n'a pas pu être sauvegardé.")
                        continue
                    
                    # Charger les ateliers depuis la base de données pour ce document
                    with get_db_context() as db:
                        workshops = WorkshopRepository.get_by_document(db, document_id)
                        ateliers = [w.atelier_name for w in workshops]
                    
                    # Mettre à jour le workshop_dict avec document_id et ateliers
                    # IMPORTANT: Conserver file_name, ne pas le supprimer
                    if i < len(new_workshop_dicts):
                        new_workshop_dicts[i]["document_id"] = document_id
                        new_workshop_dicts[i]["ateliers"] = ateliers
                        # S'assurer que file_name est bien présent
                        if "file_name" not in new_workshop_dicts[i]:
                            new_workshop_dicts[i]["file_name"] = file_name
                        # Supprimer file_path et extracted_text qui ne sont plus nécessaires
                        new_workshop_dicts[i].pop("file_path", None)
                        new_workshop_dicts[i].pop("extracted_text", None)
            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde en base de données: {str(e)}")
                import traceback
                st.error(f"**Détails de l'erreur :**")
                st.code(traceback.format_exc())
                st.stop()
            
            # Filtrer les workshops qui n'ont pas de document_id (échec de sauvegarde)
            new_workshop_dicts = [w for w in new_workshop_dicts if w.get("document_id") is not None]
            
            if not new_workshop_dicts:
                st.error("❌ Aucun workshop n'a pu être sauvegardé. Veuillez vérifier les erreurs ci-dessus.")
                st.stop()
            
            # Ajouter les nouveaux workshops aux workshops existants (après avoir récupéré les document_id)
            existing_workshops = st.session_state.get("uploaded_workshops", [])
            st.session_state.uploaded_workshops = existing_workshops + new_workshop_dicts
            
            # Marquer les fichiers comme uploadés
            for f in new_workshops:
                st.session_state.uploaded_file_names.add(f.name)
            
            st.success(f"✅ {len(new_workshop_dicts)} nouveau(x) fichier(s) d'atelier sauvegardé(s)")
            # Forcer la mise à jour de la sidebar
            st.rerun()
    
    # Afficher les workshops déjà uploadés
    if st.session_state.uploaded_workshops:
        st.markdown("**Fichiers d'ateliers sauvegardés :**")
        for idx, workshop in enumerate(st.session_state.uploaded_workshops):
            # Gérer les deux formats : dict ou string (pour compatibilité)
            document_id = None
            file_name = ""
            ateliers = []
            
            if isinstance(workshop, dict):
                document_id = workshop.get("document_id")
                file_name = workshop.get("file_name", "")
                ateliers = workshop.get("ateliers", [])  # Liste des ateliers
                # Format ancien avec atelier_name (un seul atelier)
                if not ateliers:
                    atelier_name = workshop.get("atelier_name", "")
                    if atelier_name:
                        ateliers = [atelier_name]
                # Format ancien avec file_path
                if not file_name:
                    file_path = workshop.get("file_path", "")
                    file_name = os.path.basename(file_path) if file_path else "Unknown"
            else:
                # Format ancien (string) - pas de document_id disponible
                file_path = workshop
                file_name = os.path.basename(file_path)
            
            # Construire le nom d'affichage
            if not file_name:
                file_name = f"Workshop (ID: {document_id})" if document_id else "Workshop (nom inconnu)"
            
            col1, col2 = st.columns([4, 1])
            with col1:
                # Afficher le nom du fichier
                st.text(f"• {file_name}")
                # Afficher les ateliers en dessous si disponibles
                if ateliers:
                    for atelier in ateliers:
                        st.caption(f"  └─ {atelier}")
            with col2:
                # Utiliser document_id + index comme clé unique pour le bouton (éviter les doublons)
                button_key = f"delete_workshop_{document_id}_{idx}" if document_id else f"delete_workshop_{idx}"
                if st.button("🗑️", key=button_key, help="Supprimer"):
                    # Supprimer de la base de données si un projet est sélectionné
                    if st.session_state.current_project_id and document_id:
                        try:
                            from database.repository import DocumentRepository
                            from database.db import get_db_context
                            with get_db_context() as db:
                                DocumentRepository.delete(db, document_id)
                        except Exception as e:
                            st.warning(f"⚠️ Erreur lors de la suppression: {str(e)}")
                    # Supprimer de la session state
                    st.session_state.uploaded_workshops.pop(idx)
                    # Retirer aussi le nom du fichier du tracking si on peut le retrouver
                    if file_name:
                        # Chercher le nom original dans uploaded_file_names
                        for name in list(st.session_state.uploaded_file_names):
                            if file_name.endswith(name) or name in file_name:
                                st.session_state.uploaded_file_names.discard(name)
                                break
                    st.rerun()

def display_company_context_section():
    """Section pour configurer le contexte de l'entreprise avec recherche web"""
    st.header("Contexte de l'entreprise")
    st.info("💡 Configurez les informations sur l'entreprise et lancez une recherche web pour obtenir des informations détaillées.")
    
    # En mode DEV, auto-valider les informations de l'entreprise si pas déjà fait
    if is_dev_mode() and not st.session_state.get("validated_company_info"):
        st.session_state.validated_company_info = {
            "nom": "Entreprise Test",
            "secteur": "Technologie",
            "chiffre_affaires": "",
            "nombre_employes": "",
            "description": "Entreprise simulée pour les tests en mode DEV"
        }
        if not st.session_state.get("company_name"):
            st.session_state.company_name = "Entreprise Test"
        st.success("✅ Mode DEV : Informations de l'entreprise auto-validées")
    
    # Initialiser les variables pour suivre les changements
    if 'company_context_name' not in st.session_state:
        st.session_state.company_context_name = ""
    if 'company_context_url' not in st.session_state:
        st.session_state.company_context_url = ""
    if 'company_context_description' not in st.session_state:
        st.session_state.company_context_description = ""
    if 'previous_company_context_name' not in st.session_state:
        st.session_state.previous_company_context_name = ""
    if 'web_search_counter' not in st.session_state:
        st.session_state.web_search_counter = 0
    
    # Champs de saisie
    col1, col2 = st.columns(2)
    with col1:
        company_context_name = st.text_input(
            "Nom de l'entreprise *",
            value=st.session_state.company_context_name,
            placeholder="Ex: aiko",
            key="company_context_name_input"
        )
    with col2:
        company_context_url = st.text_input(
            "URL du site (optionnel)",
            value=st.session_state.company_context_url,
            placeholder="Ex: https://www.example.com",
            key="company_context_url_input"
        )
    
    company_context_description = st.text_area(
        "Description de l'entreprise (optionnel)",
        value=st.session_state.company_context_description,
        placeholder="Ex: Fabricant de dispositifs médicaux spécialisé dans...",
        height=100,
        key="company_context_description_input"
    )
    
    # Normaliser les valeurs
    normalized_name = company_context_name.strip() if company_context_name else ""
    normalized_url = company_context_url.strip() if company_context_url else ""
    normalized_description = company_context_description.strip() if company_context_description else ""
    
    # Vérifier si le nom a changé (réinitialiser les résultats validés)
    name_changed = normalized_name != st.session_state.previous_company_context_name
    if name_changed and normalized_name:
        # Réinitialiser les résultats validés si le nom change
        st.session_state.validated_company_info = None
        st.session_state.previous_company_context_name = normalized_name
    
    # Mettre à jour le session_state
    st.session_state.company_context_name = normalized_name
    st.session_state.company_context_url = normalized_url
    st.session_state.company_context_description = normalized_description
    
    # Exécuter la recherche si déclenchée (avant d'afficher le bouton pour éviter les problèmes de rerun)
    if st.session_state.get("trigger_web_search", False) and normalized_name:
        st.session_state.trigger_web_search = False  # Réinitialiser le flag
        if st.session_state.web_search_agent is None:
            st.error("❌ WebSearchAgent n'est pas initialisé. Vérifiez les variables d'environnement.")
        else:
            with st.spinner("🔍 Recherche d'informations sur l'entreprise..."):
                try:
                    search_results = st.session_state.web_search_agent.search_company_info(
                        normalized_name,
                        company_url=normalized_url if normalized_url else None,
                        company_description=normalized_description if normalized_description else None
                    )
                    st.session_state.web_search_results = search_results
                    st.success("✅ Recherche terminée !")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erreur lors de la recherche: {str(e)}")
                    st.session_state.web_search_results = None
    
    # Bouton pour lancer la recherche web
    col1, col2 = st.columns([1, 4])
    with col1:
        search_button = st.button("🔍 Lancer la recherche web", type="primary", disabled=not normalized_name)
    
    # Afficher les résultats de recherche ou les données validées
    if search_button and normalized_name:
        # Réinitialiser les données validées pour afficher les nouveaux résultats de recherche
        st.session_state.validated_company_info = None
        # Incrémenter le compteur pour forcer la mise à jour des clés du formulaire
        st.session_state.web_search_counter += 1
        st.session_state.trigger_web_search = True
        st.rerun()
    
    # Afficher le formulaire éditable avec les résultats
    if st.session_state.get("web_search_results") or st.session_state.get("validated_company_info"):
        st.markdown("---")
        st.subheader("Informations de l'entreprise")
        
        # Utiliser les résultats validés s'ils existent, sinon les résultats de recherche
        # Les résultats validés ont la priorité, mais si une nouvelle recherche a été effectuée,
        # validated_company_info a été réinitialisé, donc on affichera les nouveaux résultats
        data_to_display = st.session_state.get("validated_company_info") or st.session_state.get("web_search_results", {})
        
        if data_to_display:
            # Créer un formulaire avec des champs texte pour chaque clé
            # Utiliser le compteur de recherche dans les clés pour forcer la mise à jour
            form_key_suffix = st.session_state.get("web_search_counter", 0)
            with st.form(f"company_info_form_{form_key_suffix}", clear_on_submit=False):
                st.markdown("**Modifiez les valeurs ci-dessous si nécessaire :**")
                
                # Champs modifiables pour chaque clé de CompanyInfo
                # Utiliser le compteur dans les clés pour forcer la mise à jour
                edited_nom = st.text_input(
                    "Nom de l'entreprise",
                    value=data_to_display.get("nom", ""),
                    key=f"edit_nom_{form_key_suffix}"
                )
                
                edited_secteur = st.text_input(
                    "Secteur d'activité",
                    value=data_to_display.get("secteur", ""),
                    key=f"edit_secteur_{form_key_suffix}"
                )
                
                edited_chiffre_affaires = st.text_input(
                    "Chiffre d'affaires",
                    value=data_to_display.get("chiffre_affaires", ""),
                    key=f"edit_chiffre_affaires_{form_key_suffix}"
                )
                
                edited_nombre_employes = st.text_input(
                    "Nombre d'employés",
                    value=data_to_display.get("nombre_employes", ""),
                    key=f"edit_nombre_employes_{form_key_suffix}"
                )
                
                edited_description = st.text_area(
                    "Description",
                    value=data_to_display.get("description", ""),
                    height=150,
                    key=f"edit_description_{form_key_suffix}"
                )
                
                # Bouton de validation
                col1, col2 = st.columns([1, 4])
                with col1:
                    validate_button = st.form_submit_button("✅ Valider", type="primary")
                
                if validate_button:
                    # Créer le dictionnaire validé
                    validated_data = {
                        "nom": edited_nom.strip() if edited_nom else "",
                        "secteur": edited_secteur.strip() if edited_secteur else "",
                        "chiffre_affaires": edited_chiffre_affaires.strip() if edited_chiffre_affaires else "",
                        "nombre_employes": edited_nombre_employes.strip() if edited_nombre_employes else "",
                        "description": edited_description.strip() if edited_description else ""
                    }
                    
                    # Sauvegarder dans session_state
                    st.session_state.validated_company_info = validated_data
                    # Synchroniser le nom d'entreprise pour la section "Générer les Use Cases"
                    if validated_data.get("nom"):
                        st.session_state.company_name = validated_data["nom"]
                    
                    # Sauvegarder dans la base de données si un projet est sélectionné
                    if st.session_state.current_project_id:
                        try:
                            from database.db import get_db_context
                            from database.repository import ProjectRepository
                            from database.schemas import ProjectUpdate
                            
                            with get_db_context() as db:
                                project_update = ProjectUpdate(company_info=validated_data)
                                updated_project = ProjectRepository.update(
                                    db, 
                                    st.session_state.current_project_id, 
                                    project_update
                                )
                                if updated_project:
                                    st.info("💾 Informations sauvegardées dans la base de données")
                        except Exception as e:
                            st.warning(f"⚠️ Erreur lors de la sauvegarde en base de données: {str(e)}")
                    
                    st.success("✅ Informations validées et sauvegardées !")
                    st.rerun()
    
    # Afficher un message si aucune recherche n'a été effectuée
    if not st.session_state.get("web_search_results") and not st.session_state.get("validated_company_info"):
        if normalized_name:
            st.info("💡 Cliquez sur 'Lancer la recherche web' pour obtenir des informations sur l'entreprise.")
        else:
            st.warning("⚠️ Veuillez saisir au moins le nom de l'entreprise pour lancer une recherche.")
    
    # Afficher le statut de validation si des informations sont validées
    if st.session_state.get("validated_company_info"):
        st.markdown("---")
        st.success("✅ Informations de l'entreprise validées et prêtes à être utilisées dans les workflows.")

def display_recommendations_section():
    """Section pour générer l'Executive Summary (enjeux et recommandations)"""
    st.header("Génération des Enjeux et Recommandations")
    st.info("💡 Cette section génère un Executive Summary avec les enjeux stratégiques, l'évaluation de maturité IA et les recommandations.")
    
    # Vérifier si des résultats validés existent déjà
    if st.session_state.current_project_id:
        has_challenges = has_validated_results(
            st.session_state.current_project_id,
            "executive_summary",
            "challenges"
        )
        has_recommendations = has_validated_results(
            st.session_state.current_project_id,
            "executive_summary",
            "recommendations"
        )
        has_maturity = has_validated_results(
            st.session_state.current_project_id,
            "executive_summary",
            "maturity"
        )
        
        if has_challenges or has_recommendations or has_maturity:
            # Afficher directement les résultats finaux
            st.success("✅ **Workflow terminé - Résultats disponibles**")
            st.markdown("---")
            
            # Charger les résultats validés
            validated_challenges = load_agent_results(
                st.session_state.current_project_id,
                "executive_summary",
                "challenges",
                "validated"
            )
            validated_recommendations = load_agent_results(
                st.session_state.current_project_id,
                "executive_summary",
                "recommendations",
                "validated"
            )
            validated_maturity = load_agent_results(
                st.session_state.current_project_id,
                "executive_summary",
                "maturity",
                "validated"
            )
            
            # Afficher les résultats (similaire à display_executive_final_summary)
            if validated_challenges:
                challenges_list = validated_challenges.get("challenges", [])
                st.subheader(f"Enjeux ({len(challenges_list)})")
                for i, challenge in enumerate(challenges_list, 1):
                    if isinstance(challenge, dict):
                        st.markdown(f"**{i}. {challenge.get('titre', 'N/A')}**")
                    else:
                        st.markdown(f"**{i}. {str(challenge)}**")
            
            if validated_recommendations:
                recommendations_list = validated_recommendations.get("recommendations", [])
                st.subheader(f"Recommandations ({len(recommendations_list)})")
                for i, rec in enumerate(recommendations_list, 1):
                    if isinstance(rec, dict):
                        st.markdown(f"**{i}. {rec.get('titre', 'N/A')}**")
                    else:
                        st.markdown(f"**{i}. {str(rec)}**")
            
            if validated_maturity:
                maturity_score = validated_maturity.get("maturity_score")
                maturity_summary = validated_maturity.get("maturity_summary", "")
                if maturity_score is not None:
                    st.subheader("Maturité IA")
                    st.metric("Score", maturity_score)
                    if maturity_summary:
                        st.markdown(maturity_summary)
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Modifier", use_container_width=True):
                    # Rejeter les résultats pour permettre la modification
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "executive_summary",
                        "challenges"
                    )
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "executive_summary",
                        "recommendations"
                    )
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "executive_summary",
                        "maturity"
                    )
                    # Réinitialiser le workflow
                    st.session_state.executive_thread_id = None
                    st.session_state.executive_workflow_status = None
                    st.rerun()
            with col2:
                if st.button("🔄 Régénérer", use_container_width=True):
                    # Rejeter les résultats existants
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "executive_summary",
                        "challenges"
                    )
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "executive_summary",
                        "recommendations"
                    )
                    reject_agent_results(
                        st.session_state.current_project_id,
                        "executive_summary",
                        "maturity"
                    )
                    # Réinitialiser le workflow
                    st.session_state.executive_thread_id = None
                    st.session_state.executive_workflow_status = None
                    st.rerun()
            
            return
    
    # Si le workflow est en cours, afficher la progression
    if st.session_state.get("executive_thread_id") and st.session_state.get("executive_workflow_status") is not None:
        display_executive_workflow_progress()
        return
    
    # Vérifier si des besoins/use cases validés existent dans "Validation des besoins et use cases"
    has_word_validation_needs = False
    has_word_validation_use_cases = False
    
    if st.session_state.current_project_id:
        has_word_validation_needs = has_validated_results(
            st.session_state.current_project_id,
            "word_validation",
            "needs"
        )
        has_word_validation_use_cases = has_validated_results(
            st.session_state.current_project_id,
            "word_validation",
            "use_cases"
        )
        
        if not (has_word_validation_needs or has_word_validation_use_cases):
            st.warning("⚠️ Veuillez d'abord valider les besoins et use cases dans la section 'Validation des besoins et use cases'")
            return
    
    # Vérifier que les fichiers sont uploadés
    if not st.session_state.uploaded_transcripts and not st.session_state.uploaded_workshops:
        st.warning("⚠️ Veuillez d'abord uploader des fichiers dans la section 'Upload de documents'.")
        return
    
    if not st.session_state.company_name:
        st.warning("⚠️ Veuillez d'abord saisir le nom de l'entreprise dans la section 'Upload de documents'.")
        return
    
    # Charger les besoins et use cases validés depuis la base de données
    validated_needs = []
    validated_use_cases = []
    
    if st.session_state.current_project_id and has_word_validation_needs:
        needs_data = load_agent_results(
            st.session_state.current_project_id,
            "word_validation",
            "needs",
            "validated"
        )
        if needs_data:
            validated_needs = needs_data.get("needs", [])
    
    if has_word_validation_use_cases:
        use_cases_data = load_agent_results(
            st.session_state.current_project_id,
            "word_validation",
            "use_cases",
            "validated"
        )
        if use_cases_data:
            validated_use_cases = use_cases_data.get("use_cases", [])
    
    # Afficher un résumé des données chargées
    st.success("✅ Besoins et use cases validés chargés depuis 'Validation des besoins et use cases'")
    st.markdown("---")
    
    if validated_needs:
        st.info(f"📋 {len(validated_needs)} besoins validés")
    if validated_use_cases:
        st.info(f"💼 {len(validated_use_cases)} use cases validés")
    
    st.markdown("---")
    
    # Note de l'intervieweur
    st.subheader("📝 Note de l'Intervieweur")
    interviewer_note = st.text_area(
        "Note ou commentaire supplémentaire de l'intervieweur",
        placeholder="Ex: Les entretiens se sont bien déroulés, l'entreprise est ouverte à l'IA...",
        height=100,
        key="interviewer_note"
    )
    

    # Bouton de démarrage
    st.markdown("---")
    if st.button("🚀 Démarrer la Génération Executive Summary", type="primary", use_container_width=True):
        # Vérifier que les données validées sont présentes
        if not validated_needs and not validated_use_cases:
            st.error("❌ Erreur : Aucune donnée validée trouvée. Veuillez d'abord valider les besoins et use cases dans 'Validation des besoins et use cases'.")
            return
        
        # Extraire les document_ids depuis uploaded_transcripts et uploaded_workshops
        transcript_document_ids = []
        for transcript in st.session_state.get("uploaded_transcripts", []):
            if isinstance(transcript, dict) and "document_id" in transcript:
                doc_id = transcript.get("document_id")
                if doc_id is not None:
                    transcript_document_ids.append(doc_id)
        
        workshop_document_ids = []
        for workshop in st.session_state.get("uploaded_workshops", []):
            if isinstance(workshop, dict) and "document_id" in workshop:
                doc_id = workshop.get("document_id")
                if doc_id is not None:
                    workshop_document_ids.append(doc_id)
        
        if not transcript_document_ids and not workshop_document_ids:
            st.error("❌ Erreur : Aucun document trouvé. Veuillez d'abord uploader et sauvegarder les transcripts et workshops dans la base de données.")
            return
        
        # Démarrer le workflow Executive Summary
        with st.spinner("🚀 Démarrage du workflow Executive Summary..."):
            try:
                # Créer un thread_id unique
                thread_id = str(uuid.uuid4())
                st.session_state.executive_thread_id = thread_id
                
                # Appel API pour démarrer le workflow avec les données validées
                response = requests.post(
                    f"{API_URL}/executive-summary/threads/{thread_id}/runs",
                    json={
                        "transcript_document_ids": transcript_document_ids,
                        "workshop_document_ids": workshop_document_ids,
                        "company_name": st.session_state.company_name,
                        "interviewer_note": interviewer_note or "",
                        "validated_needs": validated_needs,
                        "validated_use_cases": validated_use_cases
                    }
                )
                
                if response.status_code == 200:
                    st.success("✅ Workflow démarré avec succès !")
                    st.session_state.executive_workflow_status = "running"
                    st.rerun()
                else:
                    st.error(f"❌ Erreur: {response.text}")
                    
            except Exception as e:
                st.error(f"❌ Erreur lors du démarrage: {str(e)}")
    
def display_executive_workflow_progress():
    """Affiche la progression du workflow Executive Summary et gère les validations"""
    
    st.markdown("---")
    st.header("🔄 Progression du Workflow Executive Summary")
    
    # Si le workflow est déjà terminé dans session_state, afficher la page de résultats finale
    if st.session_state.get("executive_workflow_status") == "completed":
        display_executive_final_summary()
        return
    
    # Poll le statut
    status = poll_executive_workflow_status()
    
    if status == "running":
        st.info("⚙️ Le workflow est en cours d'exécution...")
        st.markdown("#### Étapes en cours :")
        st.markdown("""
        - 📝 Extraction des données du rapport Word
        - 📄 Analyse des transcriptions et ateliers
        - 🎯 Identification des enjeux stratégiques
        - 📊 Évaluation de la maturité IA
        - 💡 Génération des recommandations
        """)
        
        # Auto-refresh toutes les 3 secondes
        time.sleep(3)
        st.rerun()
    
    elif status == "waiting_validation_challenges":
        st.warning("⏸️ **Validation des enjeux requise !**")
        display_challenges_validation_interface()
        # Pas de rerun automatique ici, l'utilisateur doit valider
    
    elif status == "waiting_pre_recommendations_context":
        st.info("💡 **Préparation de la génération des recommandations**")
        display_pre_recommendations_interrupt_interface()
        # Pas de rerun automatique ici, l'utilisateur doit fournir le contexte
    
    elif status == "waiting_validation_recommendations":
        st.warning("⏸️ **Validation des recommandations requise !**")
        display_recommendations_validation_interface()
        # Pas de rerun automatique ici, l'utilisateur doit valider
    
    elif status == "completed":
        # Récupérer l'état final UNE SEULE FOIS et le stocker
        if not st.session_state.get("executive_final_results_cached"):
            thread_id = st.session_state.get("executive_thread_id")
            if thread_id:
                try:
                    state_response = requests.get(
                        f"{API_URL}/executive-summary/threads/{thread_id}/state",
                        timeout=60
                    )
                    state_response.raise_for_status()
                    state_data = state_response.json()
                    
                    # Stocker les résultats finaux dans session_state
                    st.session_state.executive_final_results = {
                        "validated_challenges": state_data.get("validated_challenges", []),
                        "validated_recommendations": state_data.get("validated_recommendations", []),
                        "maturity_score": state_data.get("maturity_score", 3),
                        "maturity_summary": state_data.get("maturity_summary", "")
                    }
                    st.session_state.executive_final_results_cached = True
                except Exception as e:
                    st.error(f"❌ Erreur lors de la récupération des résultats: {str(e)}")
        
        # Mettre à jour le statut pour ne plus poller
        st.session_state.executive_workflow_status = "completed"
        
        # Sauvegarder les résultats finaux dans la base de données
        if st.session_state.current_project_id and st.session_state.get("executive_final_results"):
            try:
                final_results = st.session_state.executive_final_results
                
                # Sauvegarder les enjeux
                validated_challenges = final_results.get("validated_challenges", [])
                if validated_challenges:
                    save_agent_result(
                        project_id=st.session_state.current_project_id,
                        workflow_type="executive_summary",
                        result_type="challenges",
                        data={"challenges": validated_challenges},
                        status="validated"
                    )
                
                # Sauvegarder les recommandations
                validated_recommendations = final_results.get("validated_recommendations", [])
                if validated_recommendations:
                    save_agent_result(
                        project_id=st.session_state.current_project_id,
                        workflow_type="executive_summary",
                        result_type="recommendations",
                        data={"recommendations": validated_recommendations},
                        status="validated"
                    )
                
                # Sauvegarder la maturité
                maturity_score = final_results.get("maturity_score")
                maturity_summary = final_results.get("maturity_summary", "")
                if maturity_score is not None:
                    save_agent_result(
                        project_id=st.session_state.current_project_id,
                        workflow_type="executive_summary",
                        result_type="maturity",
                        data={
                            "maturity_score": maturity_score,
                            "maturity_summary": maturity_summary
                        },
                        status="validated"
                    )
            except Exception as e:
                st.warning(f"⚠️ Erreur lors de la sauvegarde en base de données: {str(e)}")
        
        st.rerun()
    
    elif status == "error":
        st.error("❌ Une erreur s'est produite")
    
    elif status == "no_thread":
        # Thread ID perdu, revenir à l'interface initiale
        st.session_state.executive_thread_id = None
        st.session_state.executive_workflow_status = None
        st.rerun()
    
    else:
        st.warning(f"⚠️ Statut inconnu: {status}")
        # Auto-refresh pour détecter les changements de statut
        time.sleep(3)
        st.rerun()

def display_executive_final_summary():
    """
    Affiche une page simple avec les résultats finaux de l'Executive Summary.
    N'effectue AUCUN appel API - utilise uniquement les données en cache.
    """
    st.success("✅ **Workflow terminé avec succès !**")
    st.markdown("---")
    
    # Titre principal
    st.title("Résumé Executive Summary")
    st.markdown("")
    
    # Récupérer les résultats depuis session_state (déjà chargés)
    final_results = st.session_state.get("executive_final_results", {})
    
    if not final_results:
        st.warning("⚠️ Aucun résultat disponible")
        return
    
    validated_challenges = final_results.get("validated_challenges", [])
    validated_recommendations = final_results.get("validated_recommendations", [])
    
    # Section Enjeux - Titres uniquement
    st.header("Enjeux")
    if validated_challenges:
        for i, challenge in enumerate(validated_challenges, 1):
            # Gérer le cas où challenge est une chaîne JSON
            if isinstance(challenge, str):
                try:
                    challenge = json.loads(challenge)
                except (json.JSONDecodeError, TypeError):
                    st.markdown(f"**{i}. {challenge}**")
                    continue
            
            # Vérifier que challenge est un dict
            if isinstance(challenge, dict):
                titre = challenge.get("titre", f"Enjeu {i}")
                st.markdown(f"**{i}. {titre}**")
            else:
                st.markdown(f"**{i}. {str(challenge)}**")
        st.markdown("")
    else:
        st.info("Aucun enjeu validé")
    
    st.markdown("---")
    
    # Section Recommandations - Titres uniquement
    st.header("Recommandations")
    if validated_recommendations:
        # Normaliser les IDs des recommandations pour éviter les doublons
        normalized_recommendations = []
        used_ids = set()
        
        for rec in validated_recommendations:
            # Gérer le cas où rec est une chaîne JSON
            if isinstance(rec, str):
                try:
                    rec = json.loads(rec)
                except (json.JSONDecodeError, TypeError):
                    # Si ce n'est pas du JSON, traiter comme une chaîne simple
                    normalized_recommendations.append({
                        "id": f"R{len(normalized_recommendations) + 1}",
                        "titre": rec,
                        "description": ""
                    })
                    continue
            
            # Vérifier que rec est un dict
            if isinstance(rec, dict):
                rec_id = rec.get("id", "")
                rec_titre = rec.get("titre", "")
                
                # Si l'ID est déjà utilisé ou vide, générer un nouvel ID unique
                if rec_id in used_ids or not rec_id:
                    counter = len(normalized_recommendations) + 1
                    rec_id = f"R{counter}"
                    while rec_id in used_ids:
                        counter += 1
                        rec_id = f"R{counter}"
                
                used_ids.add(rec_id)
                
                # Extraire le titre (ou utiliser la chaîne complète si pas de titre)
                if rec_titre:
                    normalized_recommendations.append({
                        "id": rec_id,
                        "titre": rec_titre,
                        "description": rec.get("description", "")
                    })
                else:
                    # Ancien format string - utiliser la valeur complète comme titre
                    normalized_recommendations.append({
                        "id": rec_id,
                        "titre": str(rec),
                        "description": ""
                    })
            else:
                # Format inconnu - traiter comme string
                normalized_recommendations.append({
                    "id": f"R{len(normalized_recommendations) + 1}",
                    "titre": str(rec),
                    "description": ""
                })
        
        # Afficher uniquement les titres
        for i, rec in enumerate(normalized_recommendations, 1):
            titre = rec.get("titre", f"Recommandation {i}")
            st.markdown(f"**{i}. {titre}**")
        st.markdown("")
    else:
        st.info("Aucune recommandation validée")
    
    st.markdown("---")
    
    # Section Enjeux de l'IA pour {company_name} - Titres + Descriptions
    company_name = st.session_state.get("company_name", "l'entreprise")
    st.markdown(f"## Enjeux de l'IA pour {company_name}")
    st.markdown("")
    
    if validated_challenges:
        for i, challenge in enumerate(validated_challenges, 1):
            # Gérer le cas où challenge est une chaîne JSON
            if isinstance(challenge, str):
                try:
                    challenge = json.loads(challenge)
                except (json.JSONDecodeError, TypeError):
                    st.markdown(f"**{i}. {challenge}**")
                    if i < len(validated_challenges):
                        st.markdown("")
                    continue
            
            # Vérifier que challenge est un dict
            if isinstance(challenge, dict):
                challenge_titre = challenge.get("titre", f"Enjeu {i}")
                challenge_desc = challenge.get("description", "")
                
                if challenge_titre:
                    st.markdown(f"**{challenge_titre}**")
                else:
                    st.markdown(f"**Enjeu {i}**")
                
                if challenge_desc:
                    st.markdown(challenge_desc)
            else:
                st.markdown(f"**{i}. {str(challenge)}**")
            
            if i < len(validated_challenges):
                st.markdown("")
    else:
        st.warning("⚠️ Aucun enjeu validé")
    
    st.markdown("---")
    
    # Boutons d'action
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Recommencer un nouveau workflow", type="secondary", use_container_width=True):
            # Réinitialiser le workflow
            st.session_state.executive_thread_id = None
            st.session_state.executive_workflow_status = None
            st.session_state.executive_final_results = None
            st.session_state.executive_final_results_cached = False
            st.rerun()
    
    with col2:
        # Préparer les données pour le téléchargement
        results_json = {
            "validated_challenges": validated_challenges,
            "validated_recommendations": validated_recommendations,
            "generated_at": str(date.today())
        }
        st.download_button(
            label="📥 Télécharger les résultats (JSON)",
            data=json.dumps(results_json, indent=2, ensure_ascii=False),
            file_name=f"executive_summary_{date.today()}.json",
            mime="application/json",
            type="primary",
            use_container_width=True
        )

def display_word_validation_section():
    """
    Section : Validation des besoins et use cases
    Charge d'abord les besoins et use cases de la base de données (workflow_type="need_analysis")
    Permet de modifier/supprimer/ajouter, ou d'uploader un Word Report pour remplacer.
    """
    st.header("✅ Validation des besoins et use cases")
    
    if not st.session_state.current_project_id:
        st.warning("⚠️ Veuillez d'abord sélectionner ou créer un projet.")
        return
    
    # Initialiser les états de session si nécessaire
    if "word_validation_editing_needs" not in st.session_state:
        st.session_state.word_validation_editing_needs = None
    if "word_validation_editing_use_cases" not in st.session_state:
        st.session_state.word_validation_editing_use_cases = None
    if "word_validation_show_upload" not in st.session_state:
        st.session_state.word_validation_show_upload = False
    if "word_validation_edit_mode" not in st.session_state:
        st.session_state.word_validation_edit_mode = False
    
    # Charger les données depuis la base de données (workflow_type="need_analysis")
    has_needs = has_validated_results(
        st.session_state.current_project_id,
        "need_analysis",
        "needs"
    )
    has_use_cases = has_validated_results(
        st.session_state.current_project_id,
        "need_analysis",
        "use_cases"
    )
    
    # Charger les données
    validated_needs_data = None
    validated_use_cases_data = None
    needs_list = []
    use_cases_list = []
    
    if has_needs:
        validated_needs_data = load_agent_results(
            st.session_state.current_project_id,
            "need_analysis",
            "needs",
            "validated"
        )
        if validated_needs_data:
            needs_list = validated_needs_data.get("needs", [])
    
    if has_use_cases:
        validated_use_cases_data = load_agent_results(
            st.session_state.current_project_id,
            "need_analysis",
            "use_cases",
            "validated"
        )
        if validated_use_cases_data:
            use_cases_list = validated_use_cases_data.get("use_cases", [])
    
    # Si on est en mode upload Word, afficher l'interface d'upload
    if st.session_state.word_validation_show_upload:
        st.info("💡 Mode : Upload d'un nouveau document Word. Les données extraites remplaceront les données existantes.")
        
        # Bouton pour revenir au mode édition
        if st.button("← Retour au mode édition", type="secondary"):
            st.session_state.word_validation_show_upload = False
            st.session_state.word_validation_path = None
            st.session_state.word_validation_extracted = False
            st.session_state.word_validation_data = None
            st.rerun()
        
        # Upload du Word Report
        st.subheader("📄 Rapport Word")
        word_file = st.file_uploader(
            "Uploadez le rapport Word (.docx)",
            type=["docx"],
            key="word_validation_upload"
        )
        
        # Si un fichier est uploadé, l'uploader vers l'API
        if word_file:
            if st.button("📤 Uploader et extraire", type="primary"):
                with st.spinner("Upload du fichier..."):
                    try:
                        # Upload vers l'API
                        word_paths = upload_files_to_api([word_file])
                        all_paths = word_paths.get("file_paths", [])
                        
                        if all_paths:
                            word_path = all_paths[0]
                            st.session_state.word_validation_path = word_path
                            
                            # Sauvegarder le document dans la base de données
                            try:
                                file_name = os.path.basename(word_path)
                                document_parser_service.parse_and_save_word_report(
                                    file_path=word_path,
                                    project_id=st.session_state.current_project_id,
                                    file_name=file_name,
                                    metadata={}
                                )
                            except Exception as e:
                                st.warning(f"⚠️ Erreur lors de la sauvegarde du document: {str(e)}")
                            
                            st.success("✅ Fichier uploadé avec succès !")
                            st.rerun()
                        else:
                            st.error("❌ Erreur lors de l'upload du fichier")
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
        
        # Extraction des données
        word_path = st.session_state.get("word_validation_path")
        
        if word_path and not st.session_state.get("word_validation_extracted"):
            st.subheader("🔍 Extraction")
            
            # Option pour forcer l'extraction LLM
            force_llm = st.checkbox("🤖 Forcer l'extraction via LLM", value=False, key="word_validation_force_llm")
            
            if st.button("🔍 Extraire les besoins et use cases", type="primary"):
                with st.spinner("Extraction des données du rapport Word..."):
                    try:
                        # Appeler l'API pour extraire les données
                        response = requests.post(
                            f"{API_URL}/word/extract",
                            json={
                                "word_path": word_path,
                                "force_llm": force_llm
                            },
                            timeout=300
                        )
                        response.raise_for_status()
                        extracted_data = response.json()
                        st.session_state.word_validation_extracted = True
                        st.session_state.word_validation_data = extracted_data
                        
                        extraction_method = extracted_data.get("extraction_method", "unknown")
                        if extraction_method == "structured":
                            st.success("✅ Extraction réussie via parsing structuré")
                        elif extraction_method == "llm_fallback":
                            st.info("ℹ️ Extraction réussie via LLM (fallback automatique)")
                        elif extraction_method == "llm_forced":
                            st.info("🤖 Extraction réussie via LLM (forcé)")
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur lors de l'extraction: {str(e)}")
        
        # Validation/Modification après extraction
        if st.session_state.get("word_validation_data"):
            st.subheader("✏️ Validation/Modification")
            st.warning("⚠️ Les données extraites remplaceront les données existantes dans la base de données.")
            
            extracted_data = st.session_state.word_validation_data
            final_needs = extracted_data.get("final_needs", [])
            final_use_cases = extracted_data.get("final_use_cases", [])
            
            # Interface de validation pour les besoins
            if final_needs:
                st.markdown("#### 📋 Besoins identifiés")
                needs_result = validation_interface.display_needs_for_validation(
                    identified_needs=final_needs,
                    validated_count=0,
                    key_suffix="word_validation_needs"
                )
                
                if needs_result:
                    validated_needs = needs_result.get("validated_needs", [])
                    
                    # Sauvegarder dans la base de données (workflow_type="need_analysis" + copie avec "word_validation")
                    if st.session_state.current_project_id and validated_needs:
                        try:
                            # Sauvegarder avec need_analysis (pour que "Générer les Use Cases" continue de fonctionner)
                            save_agent_result(
                                project_id=st.session_state.current_project_id,
                                workflow_type="need_analysis",
                                result_type="needs",
                                data={"needs": validated_needs},
                                status="validated"
                            )
                            # Créer une copie avec word_validation (pour que "Génération des enjeux" puisse vérifier)
                            save_agent_result(
                                project_id=st.session_state.current_project_id,
                                workflow_type="word_validation",
                                result_type="needs",
                                data={"needs": validated_needs},
                                status="validated"
                            )
                            st.success("✅ Besoins validés et sauvegardés !")
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")
            
            # Interface de validation pour les use cases
            if final_use_cases:
                st.markdown("#### 💼 Use Cases identifiés")
                use_cases_result = use_case_validation.display_use_cases_for_validation(
                    use_cases=final_use_cases,
                    validated_count=0,
                    key_suffix="word_validation_use_cases"
                )
                
                if use_cases_result:
                    validated_use_cases = use_cases_result.get("validated_use_cases", [])
                    
                    # Sauvegarder dans la base de données (workflow_type="need_analysis" + copie avec "word_validation")
                    if st.session_state.current_project_id and validated_use_cases:
                        try:
                            # Sauvegarder avec need_analysis (pour que "Générer les Use Cases" continue de fonctionner)
                            save_agent_result(
                                project_id=st.session_state.current_project_id,
                                workflow_type="need_analysis",
                                result_type="use_cases",
                                data={"use_cases": validated_use_cases},
                                status="validated"
                            )
                            # Créer une copie avec word_validation (pour que "Génération des enjeux" puisse vérifier)
                            save_agent_result(
                                project_id=st.session_state.current_project_id,
                                workflow_type="word_validation",
                                result_type="use_cases",
                                data={"use_cases": validated_use_cases},
                                status="validated"
                            )
                            st.success("✅ Use cases validés et sauvegardés !")
                            
                            # Réinitialiser l'état
                            st.session_state.word_validation_extracted = False
                            st.session_state.word_validation_data = None
                            st.session_state.word_validation_path = None
                            st.session_state.word_validation_show_upload = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur lors de la sauvegarde: {str(e)}")
        
        return
    
    # Mode édition : Afficher les données existantes avec interface d'édition
    if has_needs or has_use_cases:
        st.info("💡 Modifiez, supprimez ou ajoutez des besoins et use cases. Vous pouvez également uploader un nouveau document Word pour remplacer toutes les données.")
    else:
        st.info("💡 Aucune donnée trouvée. Uploadez un document Word pour extraire les besoins et use cases, ou ajoutez-les manuellement.")
    
    # Bouton pour basculer vers le mode upload
    if st.button("📄 Uploader un nouveau document Word", type="secondary"):
        st.session_state.word_validation_show_upload = True
        st.rerun()
    
    st.markdown("---")
    
    # Initialiser les listes d'édition si nécessaire
    if st.session_state.word_validation_editing_needs is None:
        st.session_state.word_validation_editing_needs = needs_list.copy() if needs_list else []
    if st.session_state.word_validation_editing_use_cases is None:
        st.session_state.word_validation_editing_use_cases = use_cases_list.copy() if use_cases_list else []
    
    # Interface d'édition des besoins
    st.subheader("📋 Besoins")
    
    editing_needs = st.session_state.word_validation_editing_needs
    
    # Afficher chaque besoin avec possibilité de modification/suppression
    for i, need in enumerate(editing_needs):
        with st.expander(f"**{i+1}. {need.get('theme', 'N/A')}**", expanded=False):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Formulaire d'édition
                with st.form(key=f"edit_need_{i}"):
                    theme = st.text_input("Thème", value=need.get('theme', ''), key=f"need_theme_{i}")
                    quotes = st.text_area(
                        "Citations (une par ligne)",
                        value='\n'.join(need.get('quotes', [])),
                        height=100,
                        key=f"need_quotes_{i}"
                    )
                    
                    col_save, col_delete = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                            # Mettre à jour le besoin
                            editing_needs[i] = {
                                'id': need.get('id', i+1),
                                'theme': theme,
                                'quotes': [q.strip() for q in quotes.split('\n') if q.strip()]
                            }
                            st.session_state.word_validation_editing_needs = editing_needs
                            st.success("✅ Besoin modifié")
                            st.rerun()
                    
                    with col_delete:
                        if st.form_submit_button("🗑️ Supprimer", use_container_width=True):
                            # Supprimer le besoin
                            editing_needs.pop(i)
                            st.session_state.word_validation_editing_needs = editing_needs
                            st.success("✅ Besoin supprimé")
                            st.rerun()
    
    # Formulaire pour ajouter un nouveau besoin
    with st.expander("➕ Ajouter un nouveau besoin", expanded=False):
        with st.form(key="add_need"):
            new_theme = st.text_input("Thème", key="new_need_theme")
            new_quotes = st.text_area(
                "Citations (une par ligne)",
                height=100,
                key="new_need_quotes"
            )
            
            if st.form_submit_button("➕ Ajouter", use_container_width=True):
                if new_theme.strip():
                    new_need = {
                        'id': len(editing_needs) + 1,
                        'theme': new_theme.strip(),
                        'quotes': [q.strip() for q in new_quotes.split('\n') if q.strip()]
                    }
                    editing_needs.append(new_need)
                    st.session_state.word_validation_editing_needs = editing_needs
                    st.success("✅ Besoin ajouté")
                    st.rerun()
                else:
                    st.warning("⚠️ Veuillez saisir un thème")
    
    st.markdown("---")
    
    # Interface d'édition des use cases
    st.subheader("💼 Use Cases")
    
    editing_use_cases = st.session_state.word_validation_editing_use_cases
    
    # Afficher chaque use case avec possibilité de modification/suppression
    for i, uc in enumerate(editing_use_cases):
        with st.expander(f"**{i+1}. {uc.get('titre', 'N/A')}**", expanded=False):
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Formulaire d'édition
                with st.form(key=f"edit_use_case_{i}"):
                    titre = st.text_input("Titre", value=uc.get('titre', ''), key=f"uc_titre_{i}")
                    description = st.text_area(
                        "Description",
                        value=uc.get('description', ''),
                        height=150,
                        key=f"uc_description_{i}"
                    )
                    famille = st.text_input("Famille (optionnel)", value=uc.get('famille', ''), key=f"uc_famille_{i}")
                    ia_utilisee = st.text_input("IA utilisée (optionnel)", value=uc.get('ia_utilisee', ''), key=f"uc_ia_{i}")
                    
                    col_save, col_delete = st.columns(2)
                    with col_save:
                        if st.form_submit_button("💾 Enregistrer", use_container_width=True):
                            # Mettre à jour le use case
                            editing_use_cases[i] = {
                                'id': uc.get('id', i+1),
                                'titre': titre,
                                'description': description,
                                'famille': famille if famille.strip() else None,
                                'ia_utilisee': ia_utilisee if ia_utilisee.strip() else None
                            }
                            st.session_state.word_validation_editing_use_cases = editing_use_cases
                            st.success("✅ Use case modifié")
                            st.rerun()
                    
                    with col_delete:
                        if st.form_submit_button("🗑️ Supprimer", use_container_width=True):
                            # Supprimer le use case
                            editing_use_cases.pop(i)
                            st.session_state.word_validation_editing_use_cases = editing_use_cases
                            st.success("✅ Use case supprimé")
                            st.rerun()
    
    # Formulaire pour ajouter un nouveau use case
    with st.expander("➕ Ajouter un nouveau use case", expanded=False):
        with st.form(key="add_use_case"):
            new_titre = st.text_input("Titre", key="new_uc_titre")
            new_description = st.text_area(
                "Description",
                height=150,
                key="new_uc_description"
            )
            new_famille = st.text_input("Famille (optionnel)", key="new_uc_famille")
            new_ia_utilisee = st.text_input("IA utilisée (optionnel)", key="new_uc_ia")
            
            if st.form_submit_button("➕ Ajouter", use_container_width=True):
                if new_titre.strip():
                    new_uc = {
                        'id': len(editing_use_cases) + 1,
                        'titre': new_titre.strip(),
                        'description': new_description.strip(),
                        'famille': new_famille.strip() if new_famille.strip() else None,
                        'ia_utilisee': new_ia_utilisee.strip() if new_ia_utilisee.strip() else None
                    }
                    editing_use_cases.append(new_uc)
                    st.session_state.word_validation_editing_use_cases = editing_use_cases
                    st.success("✅ Use case ajouté")
                    st.rerun()
                else:
                    st.warning("⚠️ Veuillez saisir un titre")
    
    st.markdown("---")
    
    # Bouton pour sauvegarder toutes les modifications
    if st.button("✅ Sauvegarder toutes les modifications", type="primary", use_container_width=True):
        # Sauvegarder les besoins
        if editing_needs:
            try:
                # Sauvegarder avec need_analysis (pour que "Générer les Use Cases" continue de fonctionner)
                save_agent_result(
                    project_id=st.session_state.current_project_id,
                    workflow_type="need_analysis",
                    result_type="needs",
                    data={"needs": editing_needs},
                    status="validated"
                )
                # Créer une copie avec word_validation (pour que "Génération des enjeux" puisse vérifier)
                save_agent_result(
                    project_id=st.session_state.current_project_id,
                    workflow_type="word_validation",
                    result_type="needs",
                    data={"needs": editing_needs},
                    status="validated"
                )
                st.success("✅ Besoins sauvegardés !")
            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde des besoins: {str(e)}")
        elif has_needs:
            # Si on avait des besoins mais qu'on les a tous supprimés, rejeter les anciens
            reject_agent_results(
                st.session_state.current_project_id,
                "need_analysis",
                "needs"
            )
            # Rejeter aussi les entrées word_validation
            reject_agent_results(
                st.session_state.current_project_id,
                "word_validation",
                "needs"
            )
        
        # Sauvegarder les use cases
        if editing_use_cases:
            try:
                # Sauvegarder avec need_analysis (pour que "Générer les Use Cases" continue de fonctionner)
                save_agent_result(
                    project_id=st.session_state.current_project_id,
                    workflow_type="need_analysis",
                    result_type="use_cases",
                    data={"use_cases": editing_use_cases},
                    status="validated"
                )
                # Créer une copie avec word_validation (pour que "Génération des enjeux" puisse vérifier)
                save_agent_result(
                    project_id=st.session_state.current_project_id,
                    workflow_type="word_validation",
                    result_type="use_cases",
                    data={"use_cases": editing_use_cases},
                    status="validated"
                )
                st.success("✅ Use cases sauvegardés !")
            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde des use cases: {str(e)}")
        elif has_use_cases:
            # Si on avait des use cases mais qu'on les a tous supprimés, rejeter les anciens
            reject_agent_results(
                st.session_state.current_project_id,
                "need_analysis",
                "use_cases"
            )
            # Rejeter aussi les entrées word_validation
            reject_agent_results(
                st.session_state.current_project_id,
                "word_validation",
                "use_cases"
            )
        
        # Réinitialiser les états d'édition
        st.session_state.word_validation_editing_needs = None
        st.session_state.word_validation_editing_use_cases = None
        st.rerun()

def display_challenges_validation_interface():
    """
    Affiche l'interface de validation des enjeux.
    Utilise StreamlitExecutiveValidation et envoie le résultat à l'API.
    """
    import importlib
    from executive_summary import streamlit_validation_executive
    # Forcer le rechargement du module pour éviter les problèmes de cache
    importlib.reload(streamlit_validation_executive)
    from executive_summary.streamlit_validation_executive import StreamlitExecutiveValidation
    
    st.markdown("### Validation des Enjeux Stratégiques")
    
    validation_interface = StreamlitExecutiveValidation()
    
    # Récupérer les données depuis session_state (pas d'appel API direct)
    workflow_state = st.session_state.executive_workflow_state
    identified_challenges = workflow_state.get("identified_challenges", [])
    validated_challenges = workflow_state.get("validated_challenges", [])
    
    # Créer un compteur d'itération pour réinitialiser les checkboxes
    if "challenges_iteration_count" not in st.session_state:
        st.session_state.challenges_iteration_count = 0
    
    st.markdown("---")
    
    # Utiliser la classe pour afficher l'interface de validation
    result = validation_interface.display_challenges_for_validation(
        identified_challenges=identified_challenges,
        validated_challenges=validated_challenges,
        key_suffix=f"challenges_{st.session_state.challenges_iteration_count}"
    )
    
    # Si un résultat est retourné, envoyer à l'API avec messages rotatifs
    if result is not None:
        thread_id = st.session_state.get("executive_thread_id")
        if not thread_id:
            st.error("❌ Aucun thread ID disponible")
            return
        
        # Envoyer à l'API avec messages rotatifs
        validation_messages = [
            "📤 Envoi de votre validation...",
            "🤖 Analyse vos retours...",
            "⚙️ Traitement en cours..."
        ]
        
        status_placeholder = st.empty()
        result_queue = queue.Queue()
        
        # Lancer l'appel API dans un thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                send_executive_validation_api_call,
                thread_id,
                "challenges",
                result,
                result_queue
            )
            
            # Afficher des messages rotatifs pendant le traitement
            message_index = 0
            while not future.done():
                status_placeholder.info(f"🔄 {validation_messages[message_index % len(validation_messages)]}")
                time.sleep(2)  # Changer de message toutes les 2 secondes
                message_index += 1
            
            # Récupérer le résultat
            try:
                success, error_msg = result_queue.get(timeout=1)
                
                if success:
                    status_placeholder.success("✅ Validation envoyée ! Le workflow reprend...")
                    st.session_state.executive_workflow_status = "running"
                    # Incrémenter le compteur pour réinitialiser les checkboxes à la prochaine itération
                    st.session_state.challenges_iteration_count += 1
                    time.sleep(1)
                    st.rerun()
                else:
                    status_placeholder.error(f"❌ Erreur : {error_msg}")
            
            except queue.Empty:
                status_placeholder.error("❌ Timeout lors de la validation")

def display_pre_recommendations_interrupt_interface():
    """
    Affiche l'interface avant la génération des recommandations.
    Affiche les enjeux validés et un champ pour le contexte additionnel.
    """
    st.markdown("### 📋 Enjeux Validés - Préparation de la Génération des Recommandations")
    
    # Afficher les enjeux validés
    validated_challenges = st.session_state.executive_workflow_state.get("validated_challenges", [])
    
    if validated_challenges:
        st.success(f"✅ **{len(validated_challenges)} enjeu(x) validé(s)**")
        st.markdown("---")
        
        # Afficher les enjeux - 2 par ligne
        for i in range(0, len(validated_challenges), 2):
            col1, col2 = st.columns(2, gap="large")
            
            with col1:
                challenge = validated_challenges[i]
                st.markdown(f"**{challenge.get('titre', 'Enjeu')}**")
                st.text(challenge.get('description', ''))
                
                # Afficher les besoins liés
                besoins_lies = challenge.get('besoins_lies', [])
                if besoins_lies:
                    st.caption(f"**Besoins liés:** {', '.join(besoins_lies)}")
            
            # Deuxième enjeu de la ligne (si existant)
            if i + 1 < len(validated_challenges):
                with col2:
                    challenge = validated_challenges[i + 1]
                    st.markdown(f"**{challenge.get('titre', 'Enjeu')}**")
                    st.text(challenge.get('description', ''))
                    
                    # Afficher les besoins liés
                    besoins_lies = challenge.get('besoins_lies', [])
                    if besoins_lies:
                        st.caption(f"**Besoins liés:** {', '.join(besoins_lies)}")
            
            st.markdown("---")
    else:
        st.warning("Aucun enjeu validé")
    
    st.markdown("### 💬 Instructions pour la Génération des Recommandations")
    st.markdown("Ajoutez des commentaires ou instructions pour guider la génération des recommandations :")
    
    additional_context = st.text_area(
        "Commentaires et instructions (optionnel) :",
        placeholder="Ex: Focalise-toi sur les recommandations quick-win, priorise la formation des équipes, etc.",
        height=150,
        key="recommendations_additional_context_input"
    )
    
    st.markdown("---")
    
    # Bouton pour continuer
    if st.button("✅ Générer les Recommandations", type="primary", use_container_width=True):
        # Envoyer le contexte additionnel à l'API
        status_placeholder = st.empty()
        result_queue = queue.Queue()
        
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                send_pre_recommendations_context_api_call,
                additional_context,
                st.session_state.executive_thread_id,
                result_queue
            )
            
            status_placeholder.info("🔄 Envoi du contexte...")
            
            try:
                success, error_msg = result_queue.get(timeout=180)  # 3 minutes
                
                if success:
                    status_placeholder.success("✅ Contexte envoyé ! Génération des recommandations en cours...")
                    time.sleep(1)
                    st.rerun()
                else:
                    status_placeholder.error(f"❌ Erreur : {error_msg}")
            
            except queue.Empty:
                status_placeholder.error("❌ Timeout lors de l'envoi")

def send_pre_recommendations_context_api_call(additional_context: str, thread_id: str, result_queue: queue.Queue):
    """Envoie le feedback pour les recommandations dans un thread séparé"""
    try:
        response = requests.post(
            f"{API_URL}/executive-summary/threads/{thread_id}/continue",
            json={
                "recommendations_feedback": additional_context or ""
            },
            timeout=600  # 10 minutes
        )
        response.raise_for_status()
        result_queue.put((True, None))
    except Exception as e:
        result_queue.put((False, str(e)))

def display_recommendations_validation_interface():
    """Affiche l'interface de validation des recommandations"""
    from executive_summary.streamlit_validation_executive import StreamlitExecutiveValidation
    
    validation_interface = StreamlitExecutiveValidation()
    
    # Récupérer les données depuis session_state (pas d'appel API direct)
    workflow_state = st.session_state.executive_workflow_state
    recommendations = workflow_state.get("recommendations", [])
    validated_recommendations = workflow_state.get("validated_recommendations", [])
    
    # Créer un compteur d'itération pour réinitialiser les checkboxes
    if "recommendations_iteration_count" not in st.session_state:
        st.session_state.recommendations_iteration_count = 0
    
    result = validation_interface.display_recommendations_for_validation(
        recommendations=recommendations,
        validated_recommendations=validated_recommendations,
        key_suffix=f"recommendations_{st.session_state.recommendations_iteration_count}"
    )
    
    # Si un résultat est retourné, envoyer à l'API avec messages rotatifs
    if result is not None:
        thread_id = st.session_state.get("executive_thread_id")
        if not thread_id:
            st.error("❌ Aucun thread ID disponible")
            return
        
        # Messages de validation
        validation_messages = [
            "📤 Envoi de votre validation...",
            "🤖 L'IA analyse vos retours...",
            "⚙️ Traitement en cours..."
        ]
        
        status_placeholder = st.empty()
        result_queue = queue.Queue()
        
        # Lancer l'appel API dans un thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                send_executive_validation_api_call,
                thread_id,
                "recommendations",
                result,
                result_queue
            )
            
            # Afficher des messages rotatifs pendant le traitement
            message_index = 0
            while not future.done():
                status_placeholder.info(f"🔄 {validation_messages[message_index % len(validation_messages)]}")
                time.sleep(2)  # Changer de message toutes les 2 secondes
                message_index += 1
            
            # Récupérer le résultat
            try:
                success, error_msg = result_queue.get(timeout=1)
                
                if success:
                    status_placeholder.success("✅ Validation envoyée ! Le workflow reprend...")
                    st.session_state.executive_workflow_status = "running"
                    # Incrémenter le compteur pour réinitialiser les checkboxes à la prochaine itération
                    st.session_state.recommendations_iteration_count += 1
                    time.sleep(1)
                    st.rerun()
                else:
                    status_placeholder.error(f"❌ Erreur : {error_msg}")
            
            except queue.Empty:
                status_placeholder.error("❌ Timeout lors de la validation")

def send_executive_validation_api_call(thread_id: str, validation_type: str, validation_result: Dict[str, Any], result_queue: queue.Queue):
    """
    Envoie le résultat de validation à l'API dans un thread séparé.
    
    Args:
        thread_id: ID du thread
        validation_type: Type de validation ("challenges" ou "recommendations")
        validation_result: Résultat de la validation
        result_queue: Queue pour retourner le résultat (success: bool, error_msg: str)
    """
    try:
        response = requests.post(
            f"{API_URL}/executive-summary/threads/{thread_id}/validate",
            json={
                "validation_type": validation_type,
                "validation_result": validation_result
            },
            timeout=600  # 10 minutes pour la validation et la reprise du workflow
        )
        response.raise_for_status()
        result = response.json()
        # Mettre à jour le statut du workflow
        workflow_status = result.get("workflow_status", "running")
        st.session_state.executive_workflow_status = workflow_status
        result_queue.put((True, None))
    except Exception as e:
        result_queue.put((False, str(e)))

def send_executive_validation(thread_id: str, validation_type: str, validation_result: Dict[str, Any]):
    """Envoie le résultat de validation à l'API (ancienne version, conservée pour compatibilité)"""
    try:
        response = requests.post(
            f"{API_URL}/executive-summary/threads/{thread_id}/validate",
            json={
                "validation_type": validation_type,
                "validation_result": validation_result
            }
        )
        
        if response.status_code == 200:
            st.success("✅ Validation envoyée avec succès !")
            st.session_state.executive_workflow_status = "running"
            time.sleep(2)
            st.rerun()
        else:
            st.error(f"❌ Erreur: {response.text}")
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")


def display_rappel_mission():
    """Affiche le rappel de la mission"""
    st.header("Rappel de la mission")
    
    # Vérifier si validated_company_info existe
    validated_company_info = st.session_state.get("validated_company_info")
    
    if not validated_company_info:
        st.warning("⚠️ Veuillez d'abord valider les informations de l'entreprise dans la section 'Upload de documents' > 'Contexte de l'entreprise'.")
        return
    
    # Afficher le nom de l'entreprise validée
    company_name = validated_company_info.get("nom", "")
    if company_name:
        st.info(f"🏢 Entreprise : {company_name}")
    
    if st.button("📥 Générer le rappel de la mission", type="primary"):
        thread_id = str(uuid.uuid4())
        try:
            with st.spinner("Génération du rappel de la mission..."):
                # Envoyer validated_company_info au lieu de company_name
                response = requests.post(
                    f"{API_URL}/rappel-mission/threads/{thread_id}/runs",
                    json={
                        "company_name": company_name,  # Pour compatibilité
                        "validated_company_info": validated_company_info
                    },
                    timeout=120
                )
                response.raise_for_status()
                data = response.json()
                result = data.get("result", {})
                mission_markdown = result.get("mission_markdown", "")

            if mission_markdown:
                st.session_state.rappel_mission = mission_markdown
                st.session_state.rappel_mission_company = company_name
                
                # Sauvegarder dans la base de données
                if st.session_state.current_project_id:
                    try:
                        save_agent_result(
                            project_id=st.session_state.current_project_id,
                            workflow_type="rappel_mission",
                            result_type="rappel_mission",
                            data={"rappel_mission": mission_markdown},
                            status="validated"
                        )
                    except Exception as e:
                        st.warning(f"⚠️ Erreur lors de la sauvegarde en base de données: {str(e)}")
                
                st.success("Rappel de la mission mis à jour.")
                st.rerun()
            else:
                error_message = result.get("error") or "Aucun contenu retourné par le workflow."
                st.error(f"Impossible de générer le rappel : {error_message}")
        except Exception as e:  # pragma: no cover - feedback utilisateur
            st.error(f"Erreur lors de la génération du rappel : {str(e)}")

    mission_content = st.session_state.get("rappel_mission", "")

    if mission_content:
        st.markdown(mission_content)
        st.markdown("Elle a fait appel à aiko au travers du dispositif \"IA Booster\" de BPI France pour :​\
                \n- faire le point sur les opportunités qui se présentent  pour son business model​\
                \n- évaluer sa propre capacité à appréhender cette technologie​\
                \n- définir, évaluer et prioriser les possibles cas d'usage​")
        st.markdown("Nous allons démarré la mission en " + date.today().strftime("%B %Y"))
    else:
        st.info("💡 Cliquez sur 'Générer le rappel de la mission' pour afficher les informations de l'entreprise.")


def poll_atouts_workflow_status():
    """
    Poll le statut du workflow atouts.
    
    Returns:
        "running", "waiting_atouts_validation", "completed", "error"
    """
    if not st.session_state.get("atouts_thread_id"):
        return "no_thread"
    
    try:
        response = requests.get(
            f"{API_URL}/atouts-entreprise/threads/{st.session_state.atouts_thread_id}/state",
            timeout=60
        )
        response.raise_for_status()
        
        state = response.json()
        st.session_state.atouts_workflow_state = state["values"]
        
        # Déterminer le statut
        next_nodes = list(state["next"]) if state["next"] else []
        
        print(f"🔍 [DEBUG] poll_atouts_workflow_status - next_nodes: {next_nodes}")
        
        if "validate_atouts" in next_nodes:
            return "waiting_atouts_validation"
        elif len(next_nodes) == 0:
            return "completed"
        else:
            return "running"
    
    except Exception as e:
        st.error(f"❌ Erreur lors du polling: {str(e)}")
        return "error"


def send_atouts_validation_api_call(thread_id: str, validation_result: Dict[str, Any], result_queue: queue.Queue):
    """
    Envoie le résultat de validation à l'API dans un thread séparé.
    """
    try:
        response = requests.post(
            f"{API_URL}/atouts-entreprise/threads/{thread_id}/validate",
            json=validation_result,
            timeout=600
        )
        response.raise_for_status()
        result = response.json()
        workflow_status = result.get("workflow_status", "running")
        st.session_state.atouts_workflow_status = workflow_status
        result_queue.put((True, None))
    except Exception as e:
        result_queue.put((False, str(e)))


def display_atouts_validation_interface():
    """Affiche l'interface de validation des atouts"""
    from human_in_the_loop.streamlit_atouts_validation import StreamlitAtoutsValidation
    
    workflow_state = st.session_state.get("atouts_workflow_state", {})
    proposed_atouts = workflow_state.get("proposed_atouts", [])
    validated_count = len(workflow_state.get("validated_atouts", []))
    iteration_count = workflow_state.get("iteration_count", 0)
    
    if not proposed_atouts:
        st.warning("⚠️ Aucun atout proposé. Veuillez relancer le workflow.")
        return
    
    # Utiliser l'interface de validation
    validation_interface = StreamlitAtoutsValidation()
    
    # Afficher l'interface avec le key_suffix basé sur iteration_count
    validation_result = validation_interface.display_atouts_for_validation(
        proposed_atouts=proposed_atouts,
        validated_count=validated_count,
        key_suffix=str(iteration_count)
    )
    
    # Si l'utilisateur a validé
    if validation_result:
        print(f"📝 [DEBUG] Validation result reçu: {validation_result.keys()}")
        
        # Préparer les données pour l'API
        api_payload = {
            "validated_atouts": validation_result["validated_atouts"],
            "rejected_atouts": validation_result["rejected_atouts"],
            "user_feedback": validation_result["user_feedback"],
            "atouts_user_action": validation_result["atouts_user_action"]
        }
        
        # Créer une queue pour la communication entre threads
        result_queue = queue.Queue()
        
        # Lancer l'appel API dans un thread séparé
        api_thread = threading.Thread(
            target=send_atouts_validation_api_call,
            args=(st.session_state.atouts_thread_id, api_payload, result_queue)
        )
        api_thread.start()
        
        # Afficher un spinner pendant l'appel API
        status_placeholder = st.empty()
        
        messages = [
            "⚙️ Envoi de la validation...",
            "🔄 Traitement en cours...",
            "✨ Génération en cours..." if validation_result["atouts_user_action"] == "continue_atouts" else "✅ Finalisation..."
        ]
        
        message_index = 0
        while api_thread.is_alive():
            status_placeholder.info(messages[message_index % len(messages)])
            time.sleep(2)
            message_index += 1
        
        # Récupérer le résultat
        try:
            success, error_msg = result_queue.get(timeout=1)
            
            if success:
                status_placeholder.success("✅ Validation envoyée ! Le workflow reprend...")
                
                # Attendre un peu pour que le workflow se mette à jour
                time.sleep(2)
                st.rerun()
            else:
                status_placeholder.error(f"❌ Erreur: {error_msg}")
        
        except queue.Empty:
            status_placeholder.error("❌ Timeout lors de la validation")


def display_atouts_workflow_progress():
    """Affiche la progression du workflow Atouts et gère les validations"""
    
    st.markdown("---")
    st.header("🔄 Progression du Workflow Atouts")
    
    # Si le workflow est déjà terminé dans session_state, afficher les résultats
    if st.session_state.get("atouts_workflow_completed"):
        display_atouts_final_results()
        return
    
    # Poll le statut
    status = poll_atouts_workflow_status()
    
    if status == "running":
        st.info("⚙️ Le workflow est en cours d'exécution...")
        st.markdown("#### Étapes en cours :")
        st.markdown("""
        - 📝 Extraction des parties intéressantes
        - 📄 Extraction des citations d'atouts
        - ✨ Génération des atouts
        """)
        
        # Auto-refresh toutes les 3 secondes
        time.sleep(3)
        st.rerun()
    
    elif status == "waiting_atouts_validation":
        st.warning("⏸️ **Validation des atouts requise !**")
        display_atouts_validation_interface()
    
    elif status == "completed":
        # Récupérer l'état final
        workflow_state = st.session_state.get("atouts_workflow_state", {})
        final_atouts = workflow_state.get("final_atouts", [])
        atouts_markdown = workflow_state.get("atouts_markdown", "")
        
        if final_atouts:
            st.session_state.atouts_data = {"atouts": final_atouts}
            st.session_state.atouts_markdown = atouts_markdown
            st.session_state.atouts_workflow_completed = True
            
            # Sauvegarder dans la base de données
            if st.session_state.current_project_id:
                try:
                    # Sauvegarder les atouts validés
                    save_agent_result(
                        project_id=st.session_state.current_project_id,
                        workflow_type="atouts",
                        result_type="atouts",
                        data={"atouts": final_atouts},
                        status="validated"
                    )
                except Exception as e:
                    st.warning(f"⚠️ Erreur lors de la sauvegarde en base de données: {str(e)}")
            
            st.success("✅ Workflow terminé avec succès !")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("⚠️ Workflow terminé mais aucun atout validé.")
    
    elif status == "error":
        st.error("❌ Une erreur s'est produite dans le workflow.")
    
    elif status == "no_thread":
        st.info("💡 Cliquez sur 'Lancer l'analyse des atouts' pour démarrer.")


def display_atouts_final_results():
    """Affiche les résultats finaux des atouts"""
    atouts_markdown = st.session_state.get("atouts_markdown", "")
    atouts_data = st.session_state.get("atouts_data", {})
    validated_company_info = st.session_state.get("validated_company_info", {})
    company_name = validated_company_info.get("nom", "l'entreprise")
    
    if atouts_markdown:
        st.markdown("---")
        st.markdown(atouts_markdown)
        
        # Bouton de téléchargement
        if atouts_data:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Télécharger en JSON
                atouts_json = json.dumps(atouts_data, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📥 Télécharger (JSON)",
                    data=atouts_json,
                    file_name=f"atouts_{company_name.replace(' ', '_')}_{date.today().strftime('%Y%m%d')}.json",
                    mime="application/json"
                )
            
            with col2:
                # Télécharger en Markdown
                st.download_button(
                    label="📥 Télécharger (Markdown)",
                    data=atouts_markdown,
                    file_name=f"atouts_{company_name.replace(' ', '_')}_{date.today().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
            
            with col3:
                # Bouton pour recommencer
                if st.button("🔄 Nouvelle analyse", type="secondary"):
                    # Nettoyer les états
                    st.session_state.atouts_workflow_completed = False
                    st.session_state.atouts_thread_id = None
                    st.session_state.atouts_workflow_state = {}
                    st.session_state.atouts_markdown = ""
                    st.session_state.atouts_data = {}
                    st.rerun()


def display_atouts_entreprise():
    """Affiche la page d'extraction des atouts de l'entreprise avec HITL"""
    st.header("Atouts de l'entreprise")
    
    # Vérifier si des résultats validés existent déjà
    if st.session_state.current_project_id:
        has_atouts = has_validated_results(
            st.session_state.current_project_id,
            "atouts",
            "atouts"
        )
        
        if has_atouts:
            # Afficher directement les atouts
            atouts_data = load_agent_results(
                st.session_state.current_project_id,
                "atouts",
                "atouts",
                "validated"
            )
            
            if atouts_data:
                atouts_list = atouts_data.get("atouts", [])
                st.success(f"✅ **Atouts identifiés ({len(atouts_list)})**")
                st.markdown("---")
                
                # Afficher les atouts
                for i, atout in enumerate(atouts_list, 1):
                    if isinstance(atout, dict):
                        st.markdown(f"**{i}. {atout.get('titre', 'N/A')}**")
                        description = atout.get('description', '')
                        if description:
                            st.markdown(description)
                    else:
                        st.markdown(f"**{i}. {str(atout)}**")
                    st.markdown("---")
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Modifier", use_container_width=True):
                        reject_agent_results(
                            st.session_state.current_project_id,
                            "atouts",
                            "atouts"
                        )
                        st.session_state.atouts_workflow_completed = False
                        st.session_state.atouts_thread_id = None
                        st.rerun()
                with col2:
                    if st.button("🔄 Régénérer", use_container_width=True):
                        reject_agent_results(
                            st.session_state.current_project_id,
                            "atouts",
                            "atouts"
                        )
                        st.session_state.atouts_workflow_completed = False
                        st.session_state.atouts_thread_id = None
                        st.rerun()
                
                return
    
    # Si un workflow est en cours, afficher la progression
    if st.session_state.get("atouts_thread_id"):
        display_atouts_workflow_progress()
        return
    
    # Afficher les résultats finaux s'ils existent
    if st.session_state.get("atouts_workflow_completed"):
        display_atouts_final_results()
        return
    
    # Afficher le texte d'introduction uniquement si aucun workflow n'est en cours
    st.markdown("""
    Cette section identifie les **atouts** de l'entreprise qui facilitent l'intégration de l'intelligence artificielle.
    
    L'analyse se base sur :
    - Les transcriptions des entretiens
    - Les informations de l'entreprise validées
    
    **Nouveau** : Vous pourrez valider et modifier les atouts proposés avant finalisation.
    """)
    
    # Vérifier les prérequis
    validated_company_info = st.session_state.get("validated_company_info")
    uploaded_transcripts = st.session_state.get("uploaded_transcripts", [])
    
    if not validated_company_info:
        st.warning("⚠️ Veuillez d'abord valider les informations de l'entreprise dans 'Contexte de l'entreprise'.")
        return
    
    if not uploaded_transcripts:
        st.warning("⚠️ Veuillez d'abord uploader des transcriptions dans 'Upload de documents'.")
        return
    
    # Afficher le nom de l'entreprise
    company_name = validated_company_info.get("nom", "")
    if company_name:
        st.info(f"🏢 Entreprise : {company_name}")
    
    # Afficher le nombre de transcriptions
    st.info(f"📄 {len(uploaded_transcripts)} transcription(s) disponible(s)")
    
    # Sinon, afficher le formulaire de démarrage avec contexte additionnel
    st.markdown("---")
    st.markdown("### Contexte additionnel (optionnel)")
    st.markdown("Ajoutez des informations pour guider la génération des atouts :")
    
    additional_context = st.text_area(
        "Contexte",
        placeholder="Ex: Mettre l'accent sur les aspects techniques, la culture d'innovation est importante, etc.",
        height=150,
        key="atouts_initial_context_input"
    )
    
    if st.button("Lancer l'analyse des atouts", type="primary"):
        thread_id = str(uuid.uuid4())
        st.session_state.atouts_thread_id = thread_id
        st.session_state.atouts_workflow_completed = False
        
        try:
            with st.spinner("Démarrage du workflow... Extraction et analyse en cours..."):
                # Récupérer les document_ids depuis uploaded_transcripts
                # S'assurer qu'ils sont des entiers
                transcript_document_ids = []
                for t in uploaded_transcripts:
                    doc_id = t.get("document_id")
                    if doc_id is not None:
                        # Convertir en int si c'est une string ou un autre type
                        try:
                            transcript_document_ids.append(int(doc_id))
                        except (ValueError, TypeError):
                            st.error(f"❌ Document ID invalide: {doc_id}")
                            return
                
                if not transcript_document_ids:
                    st.error("❌ Aucun document transcript trouvé dans la base de données. Veuillez d'abord uploader et valider les transcripts.")
                    return
                
                # Récupérer les noms des interviewers
                interviewer_names = load_interviewers()
                if interviewer_names is None:
                    interviewer_names = []
                
                # Préparer les speakers validés depuis uploaded_transcripts
                validated_speakers = []
                for transcript in uploaded_transcripts:
                    speakers = transcript.get("speakers", [])
                    if speakers:
                        # S'assurer que chaque speaker est un dict avec des strings
                        for speaker in speakers:
                            if isinstance(speaker, dict):
                                validated_speakers.append({
                                    "name": str(speaker.get("name", "")),
                                    "role": str(speaker.get("role", ""))
                                })
                
                # S'assurer que additional_context est une string et non None
                if additional_context is None:
                    additional_context = ""
                else:
                    additional_context = str(additional_context)
                
                # S'assurer que validated_company_info est un dictionnaire
                if not isinstance(validated_company_info, dict):
                    st.error("❌ Les informations de l'entreprise ne sont pas valides. Veuillez les valider à nouveau dans 'Contexte de l'entreprise'.")
                    return
                
                # Appeler l'API pour démarrer le workflow avec le contexte
                response = requests.post(
                    f"{API_URL}/atouts-entreprise/threads/{thread_id}/runs",
                    json={
                        "transcript_document_ids": transcript_document_ids,
                        "company_info": validated_company_info,
                        "interviewer_names": interviewer_names if interviewer_names else None,
                        "atouts_additional_context": additional_context,
                        "validated_speakers": validated_speakers if validated_speakers else None
                    },
                    timeout=600
                )
                response.raise_for_status()
                
                st.success("✅ Workflow démarré ! Analyse en cours...")
                time.sleep(1)
                st.rerun()
                    
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 422:
                # Erreur de validation - afficher les détails
                try:
                    error_details = e.response.json()
                    detail_msg = error_details.get("detail", "Erreur de validation")
                    if isinstance(detail_msg, list):
                        # Format FastAPI pour les erreurs de validation
                        errors = "\n".join([f"- {err.get('loc', [])}: {err.get('msg', '')}" for err in detail_msg])
                        st.error(f"❌ Erreur de validation des données :\n{errors}")
                    else:
                        st.error(f"❌ Erreur de validation : {detail_msg}")
                except:
                    st.error(f"❌ Erreur 422 : Les données envoyées ne sont pas valides. Détails : {str(e)}")
            else:
                st.error(f"❌ Erreur HTTP {e.response.status_code} : {str(e)}")
            st.session_state.atouts_thread_id = None
        except requests.exceptions.Timeout:
            st.error("❌ La requête a expiré. Le traitement prend trop de temps. Veuillez réessayer.")
            st.session_state.atouts_thread_id = None
        except Exception as e:
            st.error(f"❌ Erreur lors du démarrage du workflow : {str(e)}")
            st.session_state.atouts_thread_id = None


# ==================== FONCTIONS CHAÎNE DE VALEUR ====================

def poll_value_chain_workflow_status():
    """
    Poll le statut du workflow chaîne de valeur.
    
    Returns:
        "running", "waiting_validation", "completed", "error"
    """
    if not st.session_state.get("value_chain_thread_id"):
        return "no_thread"
    
    try:
        response = requests.get(
            f"{API_URL}/value-chain/threads/{st.session_state.value_chain_thread_id}/state",
            timeout=60
        )
        response.raise_for_status()
        
        state = response.json()
        workflow_state = state["values"]
        
        # Déterminer le statut
        next_nodes = list(state["next"]) if state["next"] else []
        
        print(f"🔍 [DEBUG] poll_value_chain_workflow_status - next_nodes: {next_nodes}")
        
        # Déterminer le validation_type depuis les next_nodes si nécessaire
        if any(node in next_nodes for node in ["validate_teams", "validate_activities", "validate_friction_points"]):
            # Extraire le validation_type depuis les next_nodes
            if "validate_teams" in next_nodes:
                workflow_state["validation_type"] = "teams"
            elif "validate_activities" in next_nodes:
                workflow_state["validation_type"] = "activities"
            elif "validate_friction_points" in next_nodes:
                workflow_state["validation_type"] = "friction_points"
        
        st.session_state.value_chain_workflow_state = workflow_state
        
        if any(node in next_nodes for node in ["validate_teams", "validate_activities", "validate_friction_points"]):
            return "waiting_validation"
        elif len(next_nodes) == 0:
            return "completed"
        else:
            return "running"
    
    except Exception as e:
        st.error(f"❌ Erreur lors du polling: {str(e)}")
        return "error"


def send_value_chain_validation_api_call(thread_id: str, validation_result: Dict[str, Any], result_queue: queue.Queue):
    """
    Envoie le résultat de validation à l'API dans un thread séparé.
    """
    try:
        response = requests.post(
            f"{API_URL}/value-chain/threads/{thread_id}/validate",
            json=validation_result,
            timeout=600
        )
        response.raise_for_status()
        result = response.json()
        workflow_status = result.get("workflow_status", "running")
        st.session_state.value_chain_workflow_status = workflow_status
        result_queue.put((True, None))
    except Exception as e:
        result_queue.put((False, str(e)))


def _on_checkbox_change():
    """Callback pour les changements de checkbox - force un rerun"""
    pass


def display_value_chain_validation_interface():
    """Affiche l'interface de validation de la chaîne de valeur"""
    workflow_state = st.session_state.get("value_chain_workflow_state", {})
    validation_type = workflow_state.get("validation_type", "")
    
    if validation_type == "teams":
        proposed_items = workflow_state.get("proposed_teams", [])
        validated_items = workflow_state.get("validated_teams", [])
        item_type = "équipe"
        item_type_plural = "équipes"
    elif validation_type == "activities":
        proposed_items = workflow_state.get("proposed_activities", [])
        validated_items = workflow_state.get("validated_activities", [])
        item_type = "activité"
        item_type_plural = "activités"
    elif validation_type == "friction_points":
        proposed_items = workflow_state.get("proposed_friction_points", [])
        validated_items = workflow_state.get("validated_friction_points", [])
        item_type = "point de friction"
        item_type_plural = "points de friction"
    else:
        st.warning("⚠️ Type de validation inconnu.")
        return
    
    if not proposed_items:
        st.warning(f"⚠️ Aucune {item_type} proposée. Veuillez relancer le workflow.")
        return
    
    # Utiliser un suffixe basé sur la longueur des items proposés
    key_suffix = str(len(proposed_items))
    
    st.markdown(f"### Validation des {item_type_plural.capitalize()}")
    st.info(f"📊 {len(validated_items)} {item_type_plural} déjà validées")
    st.markdown("---")
    
    # Interface de validation selon le type
    if validation_type == "teams":
        # Séparer les équipes métier et support
        teams_metier = [item for item in proposed_items if item.get('type') == 'equipe_metier']
        teams_support = [item for item in proposed_items if item.get('type') == 'equipe_support']
        
        # Afficher d'abord les équipes métier, puis les équipes support (2 par ligne)
        all_teams_ordered = teams_metier + teams_support
        
        # Afficher les équipes avec champs éditables (2 par ligne)
        for i in range(0, len(all_teams_ordered), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Première équipe de la ligne
            with col1:
                team = all_teams_ordered[i]
                original_nom = team.get('nom', '')
                original_description = team.get('description', '')
                original_type = team.get('type', 'equipe_metier')
                
                # Clés pour les widgets
                nom_key = f"team_nom_{i}_{key_suffix}"
                desc_key = f"team_description_{i}_{key_suffix}"
                type_key = f"team_type_{i}_{key_suffix}"
                
                # Champs éditables - Streamlit gère la valeur via key=
                modified_nom = st.text_input(
                    "**Nom**",
                    value=original_nom,
                    key=nom_key,
                    label_visibility="visible"
                )
                
                modified_type = st.selectbox(
                    "**Type**",
                    options=["equipe_metier", "equipe_support"],
                    index=0 if original_type == "equipe_metier" else 1,
                    format_func=lambda x: "Equipe métier" if x == "equipe_metier" else "Equipe support",
                    key=type_key
                )
                
                modified_description = st.text_input(
                    "**Description**",
                    value=original_description,
                    key=desc_key,
                    label_visibility="visible"
                )
                
                # Checkbox pour valider
                checkbox_key = f"validate_team_{i+1}_{key_suffix}"
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = False
                is_selected = st.checkbox(f"Valider cette équipe", key=checkbox_key, on_change=_on_checkbox_change)
            
            # Deuxième équipe de la ligne (si existante)
            if i + 1 < len(all_teams_ordered):
                with col2:
                    team = all_teams_ordered[i + 1]
                    original_nom = team.get('nom', '')
                    original_description = team.get('description', '')
                    original_type = team.get('type', 'equipe_metier')
                    
                    # Clés pour les widgets
                    nom_key = f"team_nom_{i+1}_{key_suffix}"
                    desc_key = f"team_description_{i+1}_{key_suffix}"
                    type_key = f"team_type_{i+1}_{key_suffix}"
                    
                    # Champs éditables - Streamlit gère la valeur via key=
                    modified_nom = st.text_input(
                        "**Nom**",
                        value=original_nom,
                        key=nom_key,
                        label_visibility="visible"
                    )
                    
                    modified_type = st.selectbox(
                        "**Type**",
                        options=["equipe_metier", "equipe_support"],
                        index=0 if original_type == "equipe_metier" else 1,
                        format_func=lambda x: "Equipe métier" if x == "equipe_metier" else "Equipe support",
                        key=type_key
                    )
                    
                    modified_description = st.text_input(
                        "**Description**",
                        value=original_description,
                        key=desc_key,
                        label_visibility="visible"
                    )
                    
                    # Checkbox pour valider
                    checkbox_key = f"validate_team_{i+2}_{key_suffix}"
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = False
                    is_selected = st.checkbox(f"Valider cette équipe", key=checkbox_key, on_change=_on_checkbox_change)
            
            # Ligne de séparation
            st.markdown("---")
        
        # Calculer le nombre d'équipes sélectionnées
        selected_count = 0
        for i in range(1, len(all_teams_ordered) + 1):
            checkbox_key = f"validate_team_{i}_{key_suffix}"
            if st.session_state.get(checkbox_key, False):
                selected_count += 1
        
        if selected_count > 0:
            st.info(f"{selected_count} équipe(s) sélectionnée(s)")
    
    elif validation_type == "activities":
        # Afficher les activités avec champs éditables (2 par ligne)
        validated_teams = workflow_state.get("validated_teams", [])
        # Utiliser directement les noms d'équipes au lieu de team_id
        team_names = [t.get("nom") for t in validated_teams if t.get("nom")]
        
        for i in range(0, len(proposed_items), 2):
            col1, col2 = st.columns(2, gap="large")
            
            # Première activité de la ligne
            with col1:
                activity = proposed_items[i]
                original_resume = activity.get('resume', '')
                original_team_nom = activity.get('team_nom', '')
                
                # Clés pour les widgets
                resume_key = f"activity_resume_{i}_{key_suffix}"
                team_key = f"activity_team_{i}_{key_suffix}"
                
                # Initialiser team_key si nécessaire pour le selectbox
                if team_key not in st.session_state:
                    # Utiliser le nom directement
                    st.session_state[team_key] = original_team_nom if original_team_nom in team_names else (team_names[0] if team_names else '')
                
                # Champs éditables
                modified_resume = st.text_input(
                    "**Résumé**",
                    value=original_resume,
                    key=resume_key,
                    label_visibility="visible"
                )
                
                if team_names:
                    # Utiliser directement les noms d'équipes
                    current_index = team_names.index(st.session_state[team_key]) if st.session_state[team_key] in team_names else 0
                    modified_team_nom = st.selectbox(
                        "**Équipe**",
                        options=team_names,
                        index=current_index,
                        key=team_key
                    )
                else:
                    st.info("Aucune équipe validée")
                
                # Checkbox pour valider
                checkbox_key = f"validate_activity_{i+1}_{key_suffix}"
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = False
                is_selected = st.checkbox(f"Valider cette activité", key=checkbox_key, on_change=_on_checkbox_change)
            
            # Deuxième activité de la ligne (si existante)
            if i + 1 < len(proposed_items):
                with col2:
                    activity = proposed_items[i + 1]
                    original_resume = activity.get('resume', '')
                    original_team_nom = activity.get('team_nom', '')
                    
                    # Clés pour les widgets
                    resume_key = f"activity_resume_{i+1}_{key_suffix}"
                    team_key = f"activity_team_{i+1}_{key_suffix}"
                    
                    # Initialiser team_key si nécessaire
                    if team_key not in st.session_state:
                        st.session_state[team_key] = original_team_nom if original_team_nom in team_names else (team_names[0] if team_names else '')
                    
                    # Champs éditables
                    modified_resume = st.text_input(
                        "**Résumé**",
                        value=original_resume,
                        key=resume_key,
                        label_visibility="visible"
                    )
                    
                    if team_names:
                        current_index = team_names.index(st.session_state[team_key]) if st.session_state[team_key] in team_names else 0
                        modified_team_nom = st.selectbox(
                            "**Équipe**",
                            options=team_names,
                            index=current_index,
                            key=team_key
                        )
                    else:
                        st.info("Aucune équipe validée")
                    
                    # Checkbox pour valider
                    checkbox_key = f"validate_activity_{i+2}_{key_suffix}"
                    if checkbox_key not in st.session_state:
                        st.session_state[checkbox_key] = False
                    is_selected = st.checkbox(f"Valider cette activité", key=checkbox_key, on_change=_on_checkbox_change)
            
            # Ligne de séparation
            st.markdown("---")
        
        # Calculer le nombre d'activités sélectionnées
        selected_count = 0
        for i in range(1, len(proposed_items) + 1):
            checkbox_key = f"validate_activity_{i}_{key_suffix}"
            if st.session_state.get(checkbox_key, False):
                selected_count += 1
        
        if selected_count > 0:
            st.info(f"{selected_count} activité(s) sélectionnée(s)")
    
    elif validation_type == "friction_points":
        # Regrouper les points de friction par équipe
        validated_teams = workflow_state.get("validated_teams", [])
        if not validated_teams:
            st.info("💡 Validez d'abord des équipes pour voir les points de friction.")
            return
        
        # Fonction de normalisation pour le matching (enlève espaces autour de &, normalise espaces)
        def normalize_for_matching(name: str) -> str:
            """Normalise un nom pour le matching uniquement (sans modifier la valeur originale)"""
            if not name:
                return ""
            # Enlever espaces autour de &
            normalized = name.replace(" & ", "&").replace(" &", "&").replace("& ", "&")
            # Normaliser espaces multiples
            normalized = " ".join(normalized.split())
            return normalized.strip().lower()
        
        # Créer un mapping team_nom -> liste des noms d'équipes pour les listes déroulantes
        team_names = [t.get('nom', '') for t in validated_teams]
        team_names = [n for n in team_names if n]  # Filtrer les noms vides
        
        # Grouper les points de friction par team_nom normalisé
        friction_by_team = {}
        for friction in proposed_items:
            team_nom = friction.get('team_nom', '')
            # Normaliser pour le matching
            normalized_team_nom = normalize_for_matching(team_nom)
            
            # Trouver l'équipe validée correspondante par nom normalisé
            matching_team_nom = None
            for validated_team in validated_teams:
                if normalize_for_matching(validated_team.get('nom', '')) == normalized_team_nom:
                    matching_team_nom = validated_team.get('nom', '')
                    break
            
            # Utiliser le nom exact de l'équipe validée pour le groupement
            key_team_nom = matching_team_nom if matching_team_nom else team_nom
            if key_team_nom not in friction_by_team:
                friction_by_team[key_team_nom] = []
            friction_by_team[key_team_nom].append(friction)
        
        # Séparer les équipes métier et support
        teams_metier = [t for t in validated_teams if t.get('type') == 'equipe_metier']
        teams_support = [t for t in validated_teams if t.get('type') == 'equipe_support']
        
        # Afficher d'abord les équipes métier, puis les équipes support
        all_teams_ordered = teams_metier + teams_support
        
        selected_count = 0
        friction_index = 0  # Index global pour les checkboxes
        
        # Équipes métier
        if teams_metier:
            st.markdown("## Équipes métier")
            for team in teams_metier:
                team_nom = team.get('nom', 'N/A')
                team_frictions = friction_by_team.get(team_nom, [])
                
                if team_frictions:
                    st.markdown(f"### {team_nom}")
                    
                    # Afficher les citations côte à côte (2 colonnes)
                    num_frictions = len(team_frictions)
                    cols_per_row = 2
                    
                    for row_start in range(0, num_frictions, cols_per_row):
                        cols = st.columns(cols_per_row)
                        
                        for col_idx, col in enumerate(cols):
                            friction_idx = row_start + col_idx
                            if friction_idx < num_frictions:
                                friction = team_frictions[friction_idx]
                                friction_index += 1
                                original_citation = friction.get('citation', '')
                                original_description = friction.get('description', '')
                                original_team_nom = friction.get('team_nom', '')
                                
                                with col:
                                    # Container pour chaque citation
                                    with st.container():
                                        # Citation
                                        st.markdown("**Citation :**")
                                        st.markdown(f"*\"{original_citation}\"*")
                                        
                                        # Description à la ligne
                                        st.markdown("**Description :**")
                                        st.markdown(f"{original_description}")
                                        
                                        # Liste déroulante pour modifier l'équipe
                                        team_select_key = f"friction_team_{friction_index}_{key_suffix}"
                                        
                                        # Trouver l'index de l'équipe actuelle
                                        current_index = 0
                                        if original_team_nom in team_names:
                                            current_index = team_names.index(original_team_nom)
                                        
                                        # Ne pas définir st.session_state avant le selectbox
                                        # Le selectbox gère sa propre valeur via l'index
                                        selected_team_nom = st.selectbox(
                                            "**Équipe**",
                                            options=team_names,
                                            index=current_index,
                                            key=team_select_key
                                        )
                                        
                                        # Checkbox pour valider
                                        checkbox_key = f"validate_friction_{friction_index}_{key_suffix}"
                                        if checkbox_key not in st.session_state:
                                            st.session_state[checkbox_key] = False
                                        
                                        # Stocker l'index du friction dans le proposed_items pour la soumission
                                        friction['_friction_index'] = friction_index
                                        
                                        is_selected = st.checkbox(
                                            "✅ Valider ce point de friction",
                                            key=checkbox_key,
                                            on_change=_on_checkbox_change
                                        )
                                        
                                        if is_selected:
                                            selected_count += 1
                                        
                                        st.markdown("---")
                    
                    st.markdown("---")
        
        # Équipes support
        if teams_support:
            st.markdown("## Équipes support")
            for team in teams_support:
                team_nom = team.get('nom', 'N/A')
                team_frictions = friction_by_team.get(team_nom, [])
                
                if team_frictions:
                    st.markdown(f"### {team_nom}")
                    
                    # Afficher les citations côte à côte (2 colonnes)
                    num_frictions = len(team_frictions)
                    cols_per_row = 2
                    
                    for row_start in range(0, num_frictions, cols_per_row):
                        cols = st.columns(cols_per_row)
                        
                        for col_idx, col in enumerate(cols):
                            friction_idx = row_start + col_idx
                            if friction_idx < num_frictions:
                                friction = team_frictions[friction_idx]
                                friction_index += 1
                                original_citation = friction.get('citation', '')
                                original_description = friction.get('description', '')
                                original_team_nom = friction.get('team_nom', '')
                                
                                with col:
                                    # Container pour chaque citation
                                    with st.container():
                                        # Citation
                                        st.markdown("**Citation :**")
                                        st.markdown(f"*\"{original_citation}\"*")
                                        
                                        # Description à la ligne
                                        st.markdown("**Description :**")
                                        st.markdown(f"{original_description}")
                                        
                                        # Liste déroulante pour modifier l'équipe
                                        team_select_key = f"friction_team_{friction_index}_{key_suffix}"
                                        
                                        # Trouver l'index de l'équipe actuelle
                                        current_index = 0
                                        if original_team_nom in team_names:
                                            current_index = team_names.index(original_team_nom)
                                        
                                        # Ne pas définir st.session_state avant le selectbox
                                        # Le selectbox gère sa propre valeur via l'index
                                        selected_team_nom = st.selectbox(
                                            "**Équipe**",
                                            options=team_names,
                                            index=current_index,
                                            key=team_select_key
                                        )
                                        
                                        # Checkbox pour valider
                                        checkbox_key = f"validate_friction_{friction_index}_{key_suffix}"
                                        if checkbox_key not in st.session_state:
                                            st.session_state[checkbox_key] = False
                                        
                                        # Stocker l'index du friction dans le proposed_items pour la soumission
                                        friction['_friction_index'] = friction_index
                                        
                                        is_selected = st.checkbox(
                                            "✅ Valider ce point de friction",
                                            key=checkbox_key,
                                            on_change=_on_checkbox_change
                                        )
                                        
                                        if is_selected:
                                            selected_count += 1
                                        
                                        st.markdown("---")
                    
                    st.markdown("---")
        
        if selected_count > 0:
            st.info(f"{selected_count} point(s) de friction sélectionné(s)")
    
    # Section pour ajouter manuellement
    st.markdown("---")
    st.markdown(f"### Ajouter une {item_type} manuellement")
    
    if validation_type == "teams":
        with st.form(f"add_team_form"):
            new_team_nom = st.text_input("Nom de l'équipe")
            new_team_type = st.selectbox(
                "Type",
                options=["equipe_metier", "equipe_support"],
                format_func=lambda x: "Equipe métier" if x == "equipe_metier" else "Equipe support"
            )
            new_team_description = st.text_area("Description")
            if st.form_submit_button("Ajouter"):
                if new_team_nom:
                    import uuid
                    new_team = {
                        "id": f"E{len(validated_items) + len(proposed_items) + 1}",
                        "nom": new_team_nom,
                        "type": new_team_type,
                        "description": new_team_description
                    }
                    # Stocker dans session_state pour récupération lors de la soumission
                    manual_items_key = f"manual_{validation_type}_{key_suffix}"
                    if manual_items_key not in st.session_state:
                        st.session_state[manual_items_key] = []
                    st.session_state[manual_items_key].append(new_team)
                    st.success(f"✅ {item_type.capitalize()} ajoutée !")
                    st.rerun()
    elif validation_type == "activities":
        # Récupérer les équipes validées pour le selectbox
        validated_teams = workflow_state.get("validated_teams", [])
        if validated_teams:
            with st.form(f"add_activity_form"):
                # Utiliser directement les noms d'équipes
                team_names = [t.get("nom", "") for t in validated_teams if t.get("nom")]
                selected_team_nom = st.selectbox("Équipe", options=team_names)
                new_activity_resume = st.text_area("Résumé des activités")
                if st.form_submit_button("Ajouter"):
                    if new_activity_resume:
                        import uuid
                        new_activity = {
                            "id": f"A{len(validated_items) + len(proposed_items) + 1}",
                            "team_nom": selected_team_nom,
                            "resume": new_activity_resume
                        }
                        # Stocker dans session_state pour récupération lors de la soumission
                        manual_items_key = f"manual_{validation_type}_{key_suffix}"
                        if manual_items_key not in st.session_state:
                            st.session_state[manual_items_key] = []
                        st.session_state[manual_items_key].append(new_activity)
                        st.success(f"✅ {item_type.capitalize()} ajoutée !")
                        st.rerun()
        else:
            st.info("💡 Validez d'abord des équipes pour pouvoir ajouter des activités.")
    elif validation_type == "friction_points":
        validated_teams = workflow_state.get("validated_teams", [])
        if validated_teams:
            with st.form(f"add_friction_form"):
                team_names = [t.get("nom", "") for t in validated_teams if t.get("nom")]
                selected_team_nom = st.selectbox("Équipe", options=team_names)
                new_friction_citation = st.text_area("Citation")
                new_friction_description = st.text_area("Description")
                if st.form_submit_button("Ajouter"):
                    if new_friction_citation and new_friction_description:
                        import uuid
                        new_friction = {
                            "id": f"F{len(validated_items) + len(proposed_items) + 1}",
                            "team_nom": selected_team_nom,
                            "citation": new_friction_citation,
                            "description": new_friction_description
                        }
                        # Stocker dans session_state pour récupération lors de la soumission
                        manual_items_key = f"manual_{validation_type}_{key_suffix}"
                        if manual_items_key not in st.session_state:
                            st.session_state[manual_items_key] = []
                        st.session_state[manual_items_key].append(new_friction)
                        st.success(f"✅ {item_type.capitalize()} ajouté !")
                        st.rerun()
        else:
            st.info("💡 Validez d'abord des équipes pour pouvoir ajouter des points de friction.")
    
    # Boutons d'action
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if validation_type == "teams":
            continue_action = "continue_to_activities"
            continue_label = "Continuer vers les activités"
        elif validation_type == "activities":
            continue_action = "continue_to_friction"
            continue_label = "Continuer vers les points de friction"
        else:
            continue_action = "finalize"
            continue_label = "Finaliser"
        
        if st.button(continue_label, type="primary", use_container_width=True):
            # Construire les items validés depuis les checkboxes et les valeurs modifiées
            validated = []
            rejected = []
            
            if validation_type == "teams":
                # Séparer les équipes métier et support
                teams_metier = [item for item in proposed_items if item.get('type') == 'equipe_metier']
                teams_support = [item for item in proposed_items if item.get('type') == 'equipe_support']
                all_teams_ordered = teams_metier + teams_support
                
                # Lire les valeurs modifiées depuis session_state
                for i in range(len(all_teams_ordered)):
                    checkbox_key = f"validate_team_{i+1}_{key_suffix}"
                    if st.session_state.get(checkbox_key, False):
                        # Récupérer les valeurs modifiées
                        nom_key = f"team_nom_{i}_{key_suffix}"
                        desc_key = f"team_description_{i}_{key_suffix}"
                        type_key = f"team_type_{i}_{key_suffix}"
                        
                        validated_team = {
                            **all_teams_ordered[i],  # Conserver les autres champs (id, etc.)
                            "nom": st.session_state.get(nom_key, all_teams_ordered[i].get('nom', '')),
                            "description": st.session_state.get(desc_key, all_teams_ordered[i].get('description', '')),
                            "type": st.session_state.get(type_key, all_teams_ordered[i].get('type', 'equipe_metier'))
                        }
                        validated.append(validated_team)
            
            elif validation_type == "activities":
                # Lire les valeurs modifiées depuis session_state
                for i in range(len(proposed_items)):
                    checkbox_key = f"validate_activity_{i+1}_{key_suffix}"
                    if st.session_state.get(checkbox_key, False):
                        # Récupérer les valeurs modifiées
                        resume_key = f"activity_resume_{i}_{key_suffix}"
                        team_key = f"activity_team_{i}_{key_suffix}"
                        
                        # Récupérer directement le team_nom sélectionné
                        selected_team_nom = st.session_state.get(team_key, proposed_items[i].get('team_nom', ''))
                        
                        validated_activity = {
                            **proposed_items[i],  # Conserver les autres champs (id, etc.)
                            "resume": st.session_state.get(resume_key, proposed_items[i].get('resume', '')),
                            "team_nom": selected_team_nom  # Utiliser directement team_nom
                        }
                        validated.append(validated_activity)
            
            elif validation_type == "friction_points":
                # Lire les valeurs depuis les checkboxes (utiliser _friction_index stocké)
                for friction in proposed_items:
                    friction_index = friction.get('_friction_index', 0)
                    if friction_index > 0:
                        checkbox_key = f"validate_friction_{friction_index}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            # Récupérer l'équipe modifiée si elle a été changée
                            team_select_key = f"friction_team_{friction_index}_{key_suffix}"
                            modified_team_nom = st.session_state.get(team_select_key, friction.get('team_nom', ''))
                            
                            # Ajouter le friction avec l'équipe modifiée
                            validated_friction = {
                                **friction,
                                "team_nom": modified_team_nom  # Utiliser l'équipe modifiée
                            }
                            # Retirer le champ temporaire
                            validated_friction.pop('_friction_index', None)
                            validated.append(validated_friction)
            
            # Ajouter les items ajoutés manuellement
            manual_items_key = f"manual_{validation_type}_{key_suffix}"
            if manual_items_key in st.session_state:
                validated.extend(st.session_state[manual_items_key])
            
            if validated or rejected:
                # Préparer les données pour l'API
                api_payload = {
                    "validation_type": validation_type,
                    "validated_items": validated,
                    "rejected_items": rejected,
                    "user_action": continue_action
                }
                
                # Créer une queue pour la communication entre threads
                result_queue = queue.Queue()
                
                # Lancer l'appel API dans un thread séparé
                api_thread = threading.Thread(
                    target=send_value_chain_validation_api_call,
                    args=(st.session_state.value_chain_thread_id, api_payload, result_queue)
                )
                api_thread.start()
                
                # Afficher un spinner pendant l'appel API
                status_placeholder = st.empty()
                messages = [
                    "⚙️ Envoi de la validation...",
                    "🔄 Traitement en cours...",
                    "✨ Génération en cours..." if continue_action != "finalize" else "✅ Finalisation..."
                ]
                
                message_index = 0
                while api_thread.is_alive():
                    status_placeholder.info(messages[message_index % len(messages)])
                    time.sleep(2)
                    message_index += 1
                
                # Récupérer le résultat
                try:
                    success, error_msg = result_queue.get(timeout=1)
                    
                    if success:
                        status_placeholder.success("✅ Validation envoyée ! Le workflow reprend...")
                        time.sleep(2)
                        st.rerun()
                    else:
                        status_placeholder.error(f"❌ Erreur: {error_msg}")
                
                except queue.Empty:
                    status_placeholder.error("❌ Timeout lors de la validation")
            else:
                st.warning("⚠️ Veuillez valider ou rejeter au moins une item, ou ajouter une item manuellement.")
    
    with col2:
        if validation_type != "friction_points":
            if validation_type == "teams":
                regenerate_action = "continue_teams"
            else:
                regenerate_action = "continue_activities"
            
            if st.button("🔄 Régénérer", use_container_width=True):
                # Construire les items validés depuis les checkboxes et les valeurs modifiées
                validated = []
                rejected = []
                
                if validation_type == "teams":
                    # Séparer les équipes métier et support
                    teams_metier = [item for item in proposed_items if item.get('type') == 'equipe_metier']
                    teams_support = [item for item in proposed_items if item.get('type') == 'equipe_support']
                    all_teams_ordered = teams_metier + teams_support
                    
                    # Lire les valeurs modifiées depuis session_state
                    for i in range(len(all_teams_ordered)):
                        checkbox_key = f"validate_team_{i+1}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            # Récupérer les valeurs modifiées
                            nom_key = f"team_nom_{i}_{key_suffix}"
                            desc_key = f"team_description_{i}_{key_suffix}"
                            type_key = f"team_type_{i}_{key_suffix}"
                            
                            validated_team = {
                                **all_teams_ordered[i],  # Conserver les autres champs (id, etc.)
                                "nom": st.session_state.get(nom_key, all_teams_ordered[i].get('nom', '')),
                                "description": st.session_state.get(desc_key, all_teams_ordered[i].get('description', '')),
                                "type": st.session_state.get(type_key, all_teams_ordered[i].get('type', 'equipe_metier'))
                            }
                            validated.append(validated_team)
                
                elif validation_type == "activities":
                    # Lire les valeurs modifiées depuis session_state
                    for i in range(len(proposed_items)):
                        checkbox_key = f"validate_activity_{i+1}_{key_suffix}"
                        if st.session_state.get(checkbox_key, False):
                            # Récupérer les valeurs modifiées
                            resume_key = f"activity_resume_{i}_{key_suffix}"
                            team_key = f"activity_team_{i}_{key_suffix}"
                            
                            # Récupérer directement le team_nom sélectionné
                            selected_team_nom = st.session_state.get(team_key, proposed_items[i].get('team_nom', ''))
                            
                            validated_activity = {
                                **proposed_items[i],  # Conserver les autres champs (id, etc.)
                                "resume": st.session_state.get(resume_key, proposed_items[i].get('resume', '')),
                                "team_nom": selected_team_nom  # Utiliser directement team_nom
                            }
                            validated.append(validated_activity)
                
                # Ajouter les items ajoutés manuellement
                manual_items_key = f"manual_{validation_type}_{key_suffix}"
                if manual_items_key in st.session_state:
                    validated.extend(st.session_state[manual_items_key])
                
                if validated or rejected:
                    api_payload = {
                        "validation_type": validation_type,
                        "validated_items": validated,
                        "rejected_items": rejected,
                        "user_action": regenerate_action
                    }
                    
                    result_queue = queue.Queue()
                    api_thread = threading.Thread(
                        target=send_value_chain_validation_api_call,
                        args=(st.session_state.value_chain_thread_id, api_payload, result_queue)
                    )
                    api_thread.start()
                    
                    status_placeholder = st.empty()
                    message_index = 0
                    while api_thread.is_alive():
                        status_placeholder.info(["⚙️ Envoi...", "🔄 Régénération..."][message_index % 2])
                        time.sleep(2)
                        message_index += 1
                    
                    try:
                        success, error_msg = result_queue.get(timeout=1)
                        if success:
                            status_placeholder.success("✅ Régénération lancée !")
                            time.sleep(2)
                            st.rerun()
                        else:
                            status_placeholder.error(f"❌ Erreur: {error_msg}")
                    except queue.Empty:
                        status_placeholder.error("❌ Timeout")


def display_value_chain_workflow_progress():
    """Affiche la progression du workflow Chaîne de valeur et gère les validations"""
    
    st.markdown("---")
    st.header("🔄 Progression du Workflow Chaîne de valeur")
    
    # Si le workflow est déjà terminé dans session_state, afficher les résultats
    if st.session_state.get("value_chain_workflow_completed"):
        display_value_chain_final_results()
        return
    
    # Poll le statut
    status = poll_value_chain_workflow_status()
    
    if status == "running":
        st.info("⚙️ Le workflow est en cours d'exécution...")
        st.markdown("#### Étapes en cours :")
        st.markdown("""
        - 📝 Chargement des interventions
        - 👥 Extraction des équipes
        - 📋 Extraction des activités
        - ⚠️ Extraction des points de friction
        """)
        
        # Auto-refresh toutes les 3 secondes
        time.sleep(3)
        st.rerun()
    
    elif status == "waiting_validation":
        workflow_state = st.session_state.get("value_chain_workflow_state", {})
        validation_type = workflow_state.get("validation_type", "")
        
        if validation_type == "teams":
            st.warning("⏸️ **Validation des équipes requise !**")
        elif validation_type == "activities":
            st.warning("⏸️ **Validation des activités requise !**")
        elif validation_type == "friction_points":
            st.warning("⏸️ **Validation des points de friction requise !**")
        
        display_value_chain_validation_interface()
    
    elif status == "completed":
        # Récupérer l'état final
        workflow_state = st.session_state.get("value_chain_workflow_state", {})
        final_value_chain = workflow_state.get("final_value_chain", {})
        value_chain_markdown = workflow_state.get("value_chain_markdown", "")
        value_chain_json = workflow_state.get("value_chain_json", "")
        
        if final_value_chain:
            st.session_state.value_chain_data = final_value_chain
            st.session_state.value_chain_markdown = value_chain_markdown
            st.session_state.value_chain_json = value_chain_json
            st.session_state.value_chain_workflow_completed = True
            
            # Sauvegarder dans la base de données
            if st.session_state.current_project_id:
                try:
                    save_agent_result(
                        project_id=st.session_state.current_project_id,
                        workflow_type="value_chain",
                        result_type="value_chain",
                        data=final_value_chain,
                        status="validated"
                    )
                except Exception as e:
                    st.warning(f"⚠️ Erreur lors de la sauvegarde en base de données: {str(e)}")
            
            st.success("✅ Workflow terminé avec succès !")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("⚠️ Workflow terminé mais aucune donnée validée.")
    
    elif status == "error":
        st.error("❌ Une erreur s'est produite dans le workflow.")
    
    elif status == "no_thread":
        st.info("💡 Cliquez sur 'Lancer l'extraction de la chaîne de valeur' pour démarrer.")


def display_value_chain_final_results():
    """Affiche les résultats finaux de la chaîne de valeur"""
    value_chain_markdown = st.session_state.get("value_chain_markdown", "")
    value_chain_data = st.session_state.get("value_chain_data", {})
    value_chain_json = st.session_state.get("value_chain_json", "")
    validated_company_info = st.session_state.get("validated_company_info", {})
    company_name = validated_company_info.get("nom", "l'entreprise")
    
    if value_chain_markdown:
        st.markdown("---")
        st.markdown(value_chain_markdown)
        
        # Boutons de téléchargement
        if value_chain_data:
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Télécharger en JSON
                if value_chain_json:
                    st.download_button(
                        label="📥 Télécharger (JSON)",
                        data=value_chain_json,
                        file_name=f"chaine_valeur_{company_name.replace(' ', '_')}_{date.today().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
            
            with col2:
                # Télécharger en Markdown
                st.download_button(
                    label="📥 Télécharger (Markdown)",
                    data=value_chain_markdown,
                    file_name=f"chaine_valeur_{company_name.replace(' ', '_')}_{date.today().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
            
            with col3:
                # Bouton pour recommencer
                if st.button("🔄 Nouvelle analyse", type="secondary"):
                    # Nettoyer les états
                    st.session_state.value_chain_workflow_completed = False
                    st.session_state.value_chain_thread_id = None
                    st.session_state.value_chain_workflow_state = {}
                    st.session_state.value_chain_markdown = ""
                    st.session_state.value_chain_data = {}
                    st.rerun()


def display_value_chain_page():
    """Affiche la page d'extraction de la chaîne de valeur"""
    st.header("Chaîne de valeur")
    
    # Vérifier si des résultats validés existent déjà
    if st.session_state.current_project_id:
        has_value_chain = has_validated_results(
            st.session_state.current_project_id,
            "value_chain",
            "value_chain"
        )
        
        if has_value_chain:
            # Afficher directement les résultats
            value_chain_data = load_agent_results(
                st.session_state.current_project_id,
                "value_chain",
                "value_chain",
                "validated"
            )
            
            if value_chain_data:
                st.success(f"✅ **Chaîne de valeur identifiée**")
                st.markdown("---")
                
                # Afficher le markdown si disponible
                if "value_chain_markdown" in value_chain_data:
                    st.markdown(value_chain_data["value_chain_markdown"])
                else:
                    # Afficher les données structurées
                    teams = value_chain_data.get("teams", [])
                    activities = value_chain_data.get("activities", [])
                    friction_points = value_chain_data.get("friction_points", [])
                    
                    if teams:
                        # Séparer les équipes métier et support
                        teams_metier = [t for t in teams if t.get('type') == 'equipe_metier']
                        teams_support = [t for t in teams if t.get('type') == 'equipe_support']
                        
                        # Grouper les friction_points par team_nom
                        friction_by_team = {}
                        for fp in friction_points:
                            team_nom = fp.get('team_nom', '')
                            if team_nom not in friction_by_team:
                                friction_by_team[team_nom] = []
                            friction_by_team[team_nom].append(fp)
                        
                        # Afficher les équipes métier
                        if teams_metier:
                            st.markdown("## Équipes métier")
                            for team in teams_metier:
                                team_nom = team.get('nom', 'N/A')
                                team_name = team.get('nom', 'N/A')
                                team_type = team.get('type', 'equipe_metier')
                                team_desc = team.get('description', '')
                                
                                st.markdown(f"### {team_name}")
                                st.markdown(f"*Equipe Métier*")
                                st.markdown(team_desc)
                                
                                # Afficher les citations associées
                                team_frictions = friction_by_team.get(team_nom, [])
                                if team_frictions:
                                    st.markdown("**Citations** :")
                                    for fp in team_frictions:
                                        citation = fp.get('citation', '')
                                        description = fp.get('description', '')
                                        st.markdown(f"- *\"{citation}\"* - {description}")
                                
                                st.markdown("---")
                        
                        # Afficher les équipes support
                        if teams_support:
                            st.markdown("## Équipes support")
                            for team in teams_support:
                                team_nom = team.get('nom', 'N/A')
                                team_name = team.get('nom', 'N/A')
                                team_type = team.get('type', 'equipe_support')
                                team_desc = team.get('description', '')
                                
                                st.markdown(f"### {team_name}")
                                st.markdown(f"*Equipe Support*")
                                st.markdown(team_desc)
                                
                                # Afficher les citations associées
                                team_frictions = friction_by_team.get(team_nom, [])
                                if team_frictions:
                                    st.markdown("**Citations** :")
                                    for fp in team_frictions:
                                        citation = fp.get('citation', '')
                                        description = fp.get('description', '')
                                        st.markdown(f"- *\"{citation}\"* - {description}")
                                
                                st.markdown("---")
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✏️ Modifier", use_container_width=True):
                        reject_agent_results(
                            st.session_state.current_project_id,
                            "value_chain",
                            "value_chain"
                        )
                        st.session_state.value_chain_workflow_completed = False
                        st.session_state.value_chain_thread_id = None
                        st.rerun()
                with col2:
                    if st.button("📥 Télécharger", use_container_width=True):
                        st.info("Utilisez les boutons de téléchargement ci-dessus")
                
                return
    
    # Vérifier si un workflow est en cours
    if st.session_state.get("value_chain_thread_id"):
        # Un workflow est en cours, afficher la progression
        display_value_chain_workflow_progress()
        return
    
    # Afficher le formulaire de démarrage
    st.info("💡 Cette fonctionnalité extrait la chaîne de valeur de l'entreprise à partir des transcripts de réunions.")
    
    # Extraire les transcript_document_ids depuis uploaded_transcripts (chargés depuis la DB)
    uploaded_transcripts = st.session_state.get("uploaded_transcripts", [])
    transcript_document_ids = []
    for t in uploaded_transcripts:
        doc_id = t.get("document_id")
        if doc_id is not None:
            try:
                transcript_document_ids.append(int(doc_id))
            except (ValueError, TypeError):
                st.error(f"❌ Document ID invalide: {doc_id}")
                return
    
    # Sélection des documents
    if not transcript_document_ids:
        st.warning("⚠️ Veuillez d'abord uploader des documents transcripts.")
        return
    validated_company_info = st.session_state.get("validated_company_info", {})
    
    if not validated_company_info:
        st.warning("⚠️ Veuillez d'abord configurer le contexte de l'entreprise.")
        return
    
    # Afficher les informations
    st.markdown("### Paramètres")
    st.write(f"📁 **Documents transcripts**: {len(transcript_document_ids)}")
    st.write(f"🏢 **Entreprise**: {validated_company_info.get('nom', 'N/A')}")
    
    # Bouton pour lancer le workflow
    if st.button("🚀 Lancer l'extraction de la chaîne de valeur", type="primary"):
        # Générer un thread_id
        import uuid
        thread_id = str(uuid.uuid4())
        st.session_state.value_chain_thread_id = thread_id
        
        try:
            # Appel API pour démarrer le workflow
            response = requests.post(
                f"{API_URL}/value-chain/threads/{thread_id}/runs",
                json={
                    "transcript_document_ids": transcript_document_ids,
                    "company_info": validated_company_info
                },
                timeout=120
            )
            response.raise_for_status()
            
            st.success("✅ Workflow lancé !")
            st.rerun()
        
        except Exception as e:
            st.error(f"❌ Erreur lors du démarrage du workflow : {str(e)}")
            st.session_state.value_chain_thread_id = None
    
    # Afficher la progression si un workflow est en cours
    if st.session_state.get("value_chain_thread_id"):
        display_value_chain_workflow_progress()


def display_prerequis_evaluation_page():
    """Affiche la page d'évaluation des prérequis IA"""
    st.header("📊 Évaluation des Prérequis IA")
    
    st.markdown("""
    Cette section évalue les **5 prérequis de transformation IA** de l'entreprise
    """)
    
    # Vérifier les prérequis
    validated_company_info = st.session_state.get("validated_company_info")
    uploaded_transcripts = st.session_state.get("uploaded_transcripts", [])
    
    # Vérifier les cas d'usage validés
    validated_use_cases = st.session_state.get("validated_use_cases", [])
    
    if not validated_company_info:
        st.warning("⚠️ Veuillez d'abord valider les informations de l'entreprise dans 'Contexte de l'entreprise'.")
        return
    
    if not uploaded_transcripts:
        st.warning("⚠️ Veuillez d'abord uploader des transcriptions dans 'Upload de documents'.")
        return
    
    if not validated_use_cases:
        st.warning("⚠️ Veuillez d'abord valider les cas d'usage dans 'Validation des besoins et use cases'.")
        return
    
    # Afficher les informations
    company_name = validated_company_info.get("nom", "")
    if company_name:
        st.info(f"🏢 Entreprise : {company_name}")
    
    st.info(f"📄 {len(uploaded_transcripts)} transcription(s) disponible(s)")
    st.info(f"✅ {len(validated_use_cases)} cas d'usage validé(s)")
    
    # Si un workflow est en cours, afficher la progression
    if st.session_state.get("prerequis_thread_id"):
        display_prerequis_workflow_progress()
        return
    
    # Afficher les résultats finaux s'ils existent
    if st.session_state.get("prerequis_workflow_completed"):
        display_prerequis_final_results()
        return
    
    st.markdown("---")
    
    # Section des commentaires
    st.subheader("💬 Commentaires pour l'évaluation")
    st.markdown("Vous pouvez ajouter des commentaires qui seront intégrés dans les prompts d'évaluation.")
    
    # Initialiser les commentaires dans session_state s'ils n'existent pas
    if "prerequis_comment_general" not in st.session_state:
        st.session_state.prerequis_comment_general = ""
    if "prerequis_comment_1" not in st.session_state:
        st.session_state.prerequis_comment_1 = ""
    if "prerequis_comment_2" not in st.session_state:
        st.session_state.prerequis_comment_2 = ""
    if "prerequis_comment_3" not in st.session_state:
        st.session_state.prerequis_comment_3 = ""
    if "prerequis_comment_4" not in st.session_state:
        st.session_state.prerequis_comment_4 = ""
    if "prerequis_comment_5" not in st.session_state:
        st.session_state.prerequis_comment_5 = ""
    
    # Commentaire général
    st.text_area(
        "Commentaire général (appliqué à tous les prérequis)",
        value=st.session_state.prerequis_comment_general,
        key="prerequis_comment_general",
        height=100,
        help="Ce commentaire sera ajouté à tous les prompts d'évaluation comme contexte global."
    )
    
    # Commentaires spécifiques
    st.markdown("#### Commentaires spécifiques par prérequis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_area(
            "1. Vision claire des leaders",
            value=st.session_state.prerequis_comment_1,
            key="prerequis_comment_1",
            height=80,
            help="Commentaire spécifique pour le prérequis 1"
        )
        
        st.text_area(
            "2. Équipe projet complète",
            value=st.session_state.prerequis_comment_2,
            key="prerequis_comment_2",
            height=80,
            help="Commentaire spécifique pour le prérequis 2"
        )
        
        st.text_area(
            "3. Cas d'usage important",
            value=st.session_state.prerequis_comment_3,
            key="prerequis_comment_3",
            height=80,
            help="Commentaire spécifique pour le prérequis 3"
        )
    
    with col2:
        st.text_area(
            "4. Données présentes",
            value=st.session_state.prerequis_comment_4,
            key="prerequis_comment_4",
            height=80,
            help="Commentaire spécifique pour le prérequis 4"
        )
        
        st.text_area(
            "5. Entreprise en mouvement",
            value=st.session_state.prerequis_comment_5,
            key="prerequis_comment_5",
            height=80,
            help="Commentaire spécifique pour le prérequis 5"
        )
    
    st.markdown("---")
    
    # Bouton pour lancer le workflow
    if st.button("🚀 Lancer l'évaluation des prérequis IA", type="primary"):
        thread_id = str(uuid.uuid4())
        st.session_state.prerequis_thread_id = thread_id
        st.session_state.prerequis_workflow_completed = False
        
        try:
            with st.spinner("Démarrage du workflow d'évaluation des prérequis..."):
                # Récupérer les document_ids depuis uploaded_transcripts
                transcript_document_ids = []
                for t in uploaded_transcripts:
                    doc_id = t.get("document_id")
                    if doc_id is not None:
                        try:
                            transcript_document_ids.append(int(doc_id))
                        except (ValueError, TypeError):
                            st.error(f"❌ Document ID invalide: {doc_id}")
                            return
                
                if not transcript_document_ids:
                    st.error("❌ Aucun document transcript trouvé.")
                    return
                
                # Récupérer les commentaires
                comments = {
                    "comment_general": st.session_state.prerequis_comment_general,
                    "comment_1": st.session_state.prerequis_comment_1,
                    "comment_2": st.session_state.prerequis_comment_2,
                    "comment_3": st.session_state.prerequis_comment_3,
                    "comment_4": st.session_state.prerequis_comment_4,
                    "comment_5": st.session_state.prerequis_comment_5
                }
                
                # Appel API pour démarrer le workflow
                response = requests.post(
                    f"{API_URL}/prerequis-evaluation/threads/{thread_id}/runs",
                    json={
                        "transcript_document_ids": transcript_document_ids,
                        "company_info": validated_company_info,
                        "validated_use_cases": validated_use_cases,
                        "comments": comments
                    },
                    timeout=600
                )
                response.raise_for_status()
                
                st.success("✅ Workflow lancé !")
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Erreur lors du démarrage du workflow : {str(e)}")
            st.session_state.prerequis_thread_id = None


def poll_prerequis_workflow_status():
    """Poll le statut du workflow d'évaluation des prérequis"""
    thread_id = st.session_state.get("prerequis_thread_id")
    if not thread_id:
        return None
    
    try:
        response = requests.get(
            f"{API_URL}/prerequis-evaluation/threads/{thread_id}/state",
            timeout=10
        )
        response.raise_for_status()
        state = response.json()
        return state.get("status", "unknown")
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération du statut : {str(e)}")
        return None


def display_prerequis_workflow_progress():
    """Affiche la progression du workflow d'évaluation des prérequis"""
    st.markdown("---")
    st.header("🔄 Progression du Workflow d'Évaluation des Prérequis")
    
    # Si le workflow est déjà terminé dans session_state, afficher les résultats
    if st.session_state.get("prerequis_workflow_completed"):
        display_prerequis_final_results()
        return
    
    # Poll le statut
    status = poll_prerequis_workflow_status()
    
    # Vérifier si on est en attente de validation
    thread_id = st.session_state.get("prerequis_thread_id")
    if thread_id:
        try:
            response = requests.get(
                f"{API_URL}/prerequis-evaluation/threads/{thread_id}/state",
                timeout=10
            )
            response.raise_for_status()
            state_data = response.json()
            validation_pending = state_data.get("validation_pending", False)
            
            if validation_pending:
                # Afficher l'interface de validation (elle gère elle-même le rafraîchissement)
                display_prerequis_validation_interface()
                return
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération de l'état : {str(e)}")
    
    if status == "running":
        st.info("⚙️ Le workflow est en cours d'exécution...")
        st.markdown("#### Étapes en cours :")
        st.markdown("""
        - 📝 Chargement des interventions
        - 📊 Évaluation du prérequis 1 (Vision claire des leaders)
        - 👥 Évaluation du prérequis 2 (Équipe projet complète)
        - 🎯 Évaluation du prérequis 3 (Cas d'usage important)
        - 💾 Évaluation du prérequis 4 (Données présentes)
        - 🚀 Évaluation du prérequis 5 (Entreprise en mouvement)
        - 📋 Synthèse globale
        """)
        
        # Auto-refresh toutes les 3 secondes
        time.sleep(3)
        st.rerun()
    
    elif status == "completed":
        # Récupérer l'état final UNE SEULE FOIS
        thread_id = st.session_state.get("prerequis_thread_id")
        try:
            response = requests.get(
                f"{API_URL}/prerequis-evaluation/threads/{thread_id}/state",
                timeout=10
            )
            response.raise_for_status()
            state = response.json()
            
            # Extraire les résultats depuis le state
            result = state.get("result", {})
            if result:
                # Le résultat contient directement les données
                st.session_state.prerequis_workflow_state = {
                    "final_evaluations": result.get("final_evaluations", []),
                    "synthese_globale": result.get("synthese_globale", ""),
                    "prerequis_markdown": result.get("prerequis_markdown", "")
                }
            else:
                # Fallback : utiliser values si disponible
                values = state.get("values", {})
                st.session_state.prerequis_workflow_state = {
                    "final_evaluations": values.get("final_evaluations", []),
                    "synthese_globale": values.get("synthese_globale", ""),
                    "prerequis_markdown": values.get("prerequis_markdown", "")
                }
            
            st.session_state.prerequis_workflow_completed = True
            st.rerun()
        except Exception as e:
            st.error(f"❌ Erreur lors de la récupération des résultats : {str(e)}")
    
    elif status == "error":
        st.error("❌ Une erreur s'est produite lors de l'exécution du workflow.")
        st.session_state.prerequis_thread_id = None


def display_prerequis_validation_interface():
    """Affiche l'interface de validation des prérequis avec checkboxes"""
    thread_id = st.session_state.get("prerequis_thread_id")
    if not thread_id:
        st.error("❌ Thread ID manquant")
        return
    
    st.header("✅ Validation des Prérequis")
    st.markdown("Cochez les prérequis que vous validez. Les prérequis non validés seront régénérés avec votre commentaire.")
    st.markdown("---")
    
    # Récupérer les évaluations depuis l'API (toujours récupérer depuis l'API pour avoir les dernières données)
    try:
        response = requests.get(
            f"{API_URL}/prerequis-evaluation/threads/{thread_id}/state",
            timeout=10
        )
        response.raise_for_status()
        state_data = response.json()
        result = state_data.get("result", {})
        final_evaluations = result.get("final_evaluations", [])
        validated_prerequis_from_state = result.get("validated_prerequis", [])
        modified_evaluations_from_state = result.get("modified_evaluations", {})
        
        # Debug: afficher le nombre d'évaluations reçues
        if not final_evaluations:
            st.warning("⚠️ Aucune évaluation disponible.")
            return
        
        # Debug: vérifier que nous avons bien 5 évaluations
        if len(final_evaluations) != 5:
            st.warning(f"⚠️ Nombre d'évaluations incorrect : {len(final_evaluations)} au lieu de 5")
        
        # Trier les évaluations par prerequis_id
        sorted_evaluations = sorted(final_evaluations, key=lambda e: e.get("prerequis_id", 0) if isinstance(e, dict) else getattr(e, "prerequis_id", 0))
        
        # Stocker les évaluations dans session_state pour référence
        # Utiliser un hash pour détecter les changements sans boucle infinie
        current_evaluations_key = f"prerequis_current_evaluations_{thread_id}"
        current_evaluations_hash_key = f"prerequis_evaluations_hash_{thread_id}"
        
        # Créer un hash simple des évaluations pour détecter les changements
        import hashlib
        # Créer une représentation stable des évaluations pour le hash
        eval_data = []
        for eval_item in sorted_evaluations:
            if isinstance(eval_item, dict):
                eval_data.append({
                    "prerequis_id": eval_item.get("prerequis_id", 0),
                    "note": eval_item.get("note", 0.0),
                    "evaluation_text": eval_item.get("evaluation_text", "")
                })
            else:
                eval_data.append({
                    "prerequis_id": getattr(eval_item, "prerequis_id", 0),
                    "note": getattr(eval_item, "note", 0.0),
                    "evaluation_text": getattr(eval_item, "evaluation_text", "")
                })
        evaluations_str = json.dumps(eval_data, sort_keys=True, default=str)
        current_hash = hashlib.md5(evaluations_str.encode()).hexdigest()
        previous_hash = st.session_state.get(current_evaluations_hash_key)
        
        # Si le hash a changé, nettoyer les clés pour forcer la mise à jour
        if previous_hash is not None and current_hash != previous_hash:
            # Nouvelles données détectées après régénération
            for prerequis_id in range(1, 6):
                if f"prerequis_note_{prerequis_id}" in st.session_state:
                    del st.session_state[f"prerequis_note_{prerequis_id}"]
                if f"prerequis_text_{prerequis_id}" in st.session_state:
                    del st.session_state[f"prerequis_text_{prerequis_id}"]
                if f"prerequis_original_note_{prerequis_id}" in st.session_state:
                    del st.session_state[f"prerequis_original_note_{prerequis_id}"]
                if f"prerequis_original_text_{prerequis_id}" in st.session_state:
                    del st.session_state[f"prerequis_original_text_{prerequis_id}"]
                # Nettoyer aussi les checkboxes de validation
                checkbox_key = f"validate_prerequis_{prerequis_id}"
                if checkbox_key in st.session_state:
                    del st.session_state[checkbox_key]
            # Nettoyer le commentaire de régénération
            if "prerequis_regeneration_comment" in st.session_state:
                del st.session_state["prerequis_regeneration_comment"]
            # Incrémenter la version pour forcer la mise à jour des widgets
            version_key = f"prerequis_ui_version_{thread_id}"
            st.session_state[version_key] = st.session_state.get(version_key, 0) + 1
        
        # Mettre à jour le hash et les évaluations
        st.session_state[current_evaluations_hash_key] = current_hash
        st.session_state[current_evaluations_key] = sorted_evaluations
        
        # Récupérer la version UI pour forcer la mise à jour des widgets
        version_key = f"prerequis_ui_version_{thread_id}"
        ui_version = st.session_state.get(version_key, 0)
        
        # Afficher les prérequis avec checkboxes
        validated_prerequis = []
        
        # Séparer les prérequis validés et non validés
        prerequis_valides = []
        prerequis_non_valides = []
        
        for evaluation in sorted_evaluations:
            prerequis_id = evaluation.get("prerequis_id", 0) if isinstance(evaluation, dict) else getattr(evaluation, "prerequis_id", 0)
            if prerequis_id in validated_prerequis_from_state:
                prerequis_valides.append(evaluation)
            else:
                prerequis_non_valides.append(evaluation)
        
        # Afficher les prérequis déjà validés en texte simple
        if prerequis_valides:
            st.markdown("### ✅ Prérequis déjà validés :")
            # Afficher 2 par 2
            for i in range(0, len(prerequis_valides), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(prerequis_valides):
                        evaluation = prerequis_valides[i + j]
                        prerequis_id = evaluation.get("prerequis_id", 0) if isinstance(evaluation, dict) else getattr(evaluation, "prerequis_id", 0)
                        titre = evaluation.get("titre", "N/A") if isinstance(evaluation, dict) else getattr(evaluation, "titre", "N/A")
                        note = evaluation.get("note", 0.0) if isinstance(evaluation, dict) else getattr(evaluation, "note", 0.0)
                        evaluation_text = evaluation.get("evaluation_text", "") if isinstance(evaluation, dict) else getattr(evaluation, "evaluation_text", "")
                        
                        # Appliquer les modifications si elles existent (depuis l'état du workflow)
                        if prerequis_id in modified_evaluations_from_state:
                            mods = modified_evaluations_from_state[prerequis_id]
                            note = mods.get("note", note)
                            evaluation_text = mods.get("evaluation_text", evaluation_text)
                        
                        # Arrondir la note à 1 décimale pour l'affichage
                        note_rounded = round(note, 1)
                        
                        with col:
                            st.markdown(f"**{prerequis_id}. {titre}** ✅ Validé")
                            st.markdown(f"**Note : {note_rounded}/5**")
                            st.markdown(f"**Évaluation :**")
                            st.markdown(evaluation_text)
                            st.markdown("---")
            
            st.markdown("---")
        
        # Afficher les prérequis à valider avec champs éditables
        if prerequis_non_valides:
            st.markdown("### Prérequis à valider :")
            
            # Stocker les modifications dans un dictionnaire
            modified_evaluations = {}
            
            # Afficher 2 par 2
            for i in range(0, len(prerequis_non_valides), 2):
                cols = st.columns(2)
                for j, col in enumerate(cols):
                    if i + j < len(prerequis_non_valides):
                        evaluation = prerequis_non_valides[i + j]
                        prerequis_id = evaluation.get("prerequis_id", 0) if isinstance(evaluation, dict) else getattr(evaluation, "prerequis_id", 0)
                        titre = evaluation.get("titre", "N/A") if isinstance(evaluation, dict) else getattr(evaluation, "titre", "N/A")
                        note = evaluation.get("note", 0.0) if isinstance(evaluation, dict) else getattr(evaluation, "note", 0.0)
                        evaluation_text = evaluation.get("evaluation_text", "") if isinstance(evaluation, dict) else getattr(evaluation, "evaluation_text", "")
                        
                        # Clés uniques pour chaque prérequis
                        note_key = f"prerequis_note_{prerequis_id}"
                        text_key = f"prerequis_text_{prerequis_id}"
                        original_note_key = f"prerequis_original_note_{prerequis_id}"
                        original_text_key = f"prerequis_original_text_{prerequis_id}"
                        
                        # Vérifier si les données de l'API ont changé (après régénération)
                        # Si les valeurs originales ont changé, mettre à jour les champs éditables
                        # On compare avec une tolérance pour les floats
                        original_note = st.session_state.get(original_note_key)
                        original_text = st.session_state.get(original_text_key)
                        
                        note_changed = original_note is None or abs(original_note - note) > 0.01
                        text_changed = original_text is None or original_text != evaluation_text
                        
                        if note_changed:
                            st.session_state[note_key] = note
                            st.session_state[original_note_key] = note
                        
                        if text_changed:
                            st.session_state[text_key] = evaluation_text
                            st.session_state[original_text_key] = evaluation_text
                        
                        # Si les clés n'existent toujours pas, les initialiser
                        if note_key not in st.session_state:
                            st.session_state[note_key] = note
                            st.session_state[original_note_key] = note
                        
                        if text_key not in st.session_state:
                            st.session_state[text_key] = evaluation_text
                            st.session_state[original_text_key] = evaluation_text
                        
                        with col:
                            st.markdown(f"**{prerequis_id}. {titre}**")
                            
                            # Champ éditable pour la note (utiliser la version UI dans la clé pour forcer la mise à jour)
                            modified_note = st.number_input(
                                f"**Note (sur 5)**",
                                min_value=0.0,
                                max_value=5.0,
                                value=st.session_state[note_key],
                                step=0.1,
                                key=f"{note_key}_v{ui_version}",
                                help="Modifiez la note si nécessaire"
                            )
                            
                            # Arrondir la note à 1 décimale pour éviter les erreurs de précision
                            modified_note = round(modified_note, 1)
                            
                            # Champ éditable pour le texte d'évaluation (utiliser la version UI dans la clé)
                            st.markdown(f"**Évaluation :**")
                            modified_text = st.text_area(
                                "Texte d'évaluation",
                                value=st.session_state[text_key],
                                key=f"{text_key}_v{ui_version}",
                                height=150,
                                help="Modifiez le texte d'évaluation si nécessaire",
                                label_visibility="collapsed"
                            )
                            
                            # Synchroniser les valeurs modifiées avec les clés de base pour la prochaine itération
                            # (utile si l'utilisateur modifie puis régénère)
                            if modified_note != st.session_state.get(note_key, note):
                                st.session_state[note_key] = round(modified_note, 1)
                            if modified_text != st.session_state.get(text_key, evaluation_text):
                                st.session_state[text_key] = modified_text
                            
                            # Stocker les modifications
                            modified_evaluations[prerequis_id] = {
                                "note": modified_note,
                                "evaluation_text": modified_text
                            }
                            
                            checkbox_key = f"validate_prerequis_{prerequis_id}_v{ui_version}"
                            if st.checkbox(f"✅ Valider ce prérequis", key=checkbox_key):
                                validated_prerequis.append(prerequis_id)
                            
                            st.markdown("---")
        
        # Si tous les prérequis sont validés, afficher un message
        if not prerequis_non_valides:
            st.info("✅ Tous les prérequis sont validés !")
        
        st.markdown("---")
        
        # Champ pour le commentaire de régénération (utiliser la version UI dans la clé)
        st.markdown("### 💬 Commentaire pour la régénération")
        st.markdown("Ce commentaire sera ajouté aux prompts des prérequis non validés lors de la régénération.")
        regeneration_comment = st.text_area(
            "Commentaire de régénération",
            key=f"prerequis_regeneration_comment_v{ui_version}",
            height=100,
            help="Commentaire qui sera ajouté aux prompts des prérequis non validés",
            value=st.session_state.get("prerequis_regeneration_comment", "")
        )
        
        st.markdown("---")
        
        # Bouton pour valider
        if st.button("✅ Valider et continuer", type="primary", use_container_width=True):
            # Combiner les prérequis déjà validés avec les nouveaux validés
            all_validated_prerequis = list(set(validated_prerequis_from_state + validated_prerequis))
            
            if not all_validated_prerequis:
                st.warning("⚠️ Veuillez valider au moins un prérequis.")
            else:
                # Envoyer le feedback à l'API
                try:
                    with st.spinner("Envoi de la validation..."):
                        # Préparer les modifications pour les prérequis validés uniquement
                        modified_evaluations_to_send = {}
                        for prerequis_id in all_validated_prerequis:
                            if prerequis_id in modified_evaluations:
                                modified_evaluations_to_send[prerequis_id] = modified_evaluations[prerequis_id]
                        
                        response = requests.post(
                            f"{API_URL}/prerequis-evaluation/threads/{thread_id}/validate",
                            json={
                                "validated_prerequis": all_validated_prerequis,
                                "regeneration_comment": regeneration_comment,
                                "modified_evaluations": modified_evaluations_to_send if modified_evaluations_to_send else None
                            },
                            timeout=600
                        )
                        response.raise_for_status()
                        
                        result = response.json()
                        
                        # Vérifier si on est encore en attente de validation (nouvelle boucle)
                        if result.get("validation_pending", False):
                            st.success("✅ Validation envoyée. Régénération terminée.")
                            # Nettoyer les clés de session_state pour forcer le rafraîchissement
                            for prerequis_id in range(1, 6):
                                if f"prerequis_note_{prerequis_id}" in st.session_state:
                                    del st.session_state[f"prerequis_note_{prerequis_id}"]
                                if f"prerequis_text_{prerequis_id}" in st.session_state:
                                    del st.session_state[f"prerequis_text_{prerequis_id}"]
                                if f"prerequis_original_note_{prerequis_id}" in st.session_state:
                                    del st.session_state[f"prerequis_original_note_{prerequis_id}"]
                                if f"prerequis_original_text_{prerequis_id}" in st.session_state:
                                    del st.session_state[f"prerequis_original_text_{prerequis_id}"]
                                # Nettoyer aussi les checkboxes de validation
                                checkbox_key = f"validate_prerequis_{prerequis_id}"
                                # Nettoyer toutes les versions de la checkbox
                                for key in list(st.session_state.keys()):
                                    if key.startswith(checkbox_key):
                                        del st.session_state[key]
                            # Nettoyer aussi les clés de hash pour forcer la détection de changement
                            if f"prerequis_evaluations_hash_{thread_id}" in st.session_state:
                                del st.session_state[f"prerequis_evaluations_hash_{thread_id}"]
                            if f"prerequis_current_evaluations_{thread_id}" in st.session_state:
                                del st.session_state[f"prerequis_current_evaluations_{thread_id}"]
                            # Nettoyer le commentaire de régénération
                            if "prerequis_regeneration_comment" in st.session_state:
                                del st.session_state["prerequis_regeneration_comment"]
                            # Incrémenter la version UI pour forcer la mise à jour des widgets
                            version_key = f"prerequis_ui_version_{thread_id}"
                            st.session_state[version_key] = st.session_state.get(version_key, 0) + 1
                            # Attendre un peu plus longtemps pour que les données soient disponibles dans l'API
                            # Faire plusieurs tentatives pour récupérer les nouvelles données
                            max_retries = 5
                            for attempt in range(max_retries):
                                time.sleep(2)
                                try:
                                    response = requests.get(
                                        f"{API_URL}/prerequis-evaluation/threads/{thread_id}/state",
                                        timeout=10
                                    )
                                    response.raise_for_status()
                                    state_data = response.json()
                                    result = state_data.get("result", {})
                                    new_evaluations = result.get("final_evaluations", [])
                                    if new_evaluations:
                                        # Mettre à jour les valeurs dans session_state avec les nouvelles données
                                        for eval_item in new_evaluations:
                                            prerequis_id = eval_item.get("prerequis_id", 0) if isinstance(eval_item, dict) else getattr(eval_item, "prerequis_id", 0)
                                            note = eval_item.get("note", 0.0) if isinstance(eval_item, dict) else getattr(eval_item, "note", 0.0)
                                            evaluation_text = eval_item.get("evaluation_text", "") if isinstance(eval_item, dict) else getattr(eval_item, "evaluation_text", "")
                                            note_key = f"prerequis_note_{prerequis_id}"
                                            text_key = f"prerequis_text_{prerequis_id}"
                                            st.session_state[note_key] = note
                                            st.session_state[text_key] = evaluation_text
                                            st.session_state[f"prerequis_original_note_{prerequis_id}"] = note
                                            st.session_state[f"prerequis_original_text_{prerequis_id}"] = evaluation_text
                                        # Nettoyer le hash pour forcer la détection de changement
                                        if f"prerequis_evaluations_hash_{thread_id}" in st.session_state:
                                            del st.session_state[f"prerequis_evaluations_hash_{thread_id}"]
                                        break
                                except Exception as e:
                                    if attempt == max_retries - 1:
                                        st.warning(f"⚠️ Impossible de récupérer les nouvelles données après {max_retries} tentatives")
                            st.rerun()
                        else:
                            # Tout est validé, afficher les résultats finaux
                            final_result = result.get("result", {})
                            st.session_state.prerequis_workflow_state = {
                                "final_evaluations": final_result.get("final_evaluations", []),
                                "synthese_globale": final_result.get("synthese_globale", ""),
                                "prerequis_markdown": final_result.get("prerequis_markdown", "")
                            }
                            st.session_state.prerequis_workflow_completed = True
                            st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'envoi de la validation : {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des évaluations : {str(e)}")


def display_prerequis_final_results():
    """Affiche les résultats finaux de l'évaluation des prérequis en texte simple"""
    workflow_state = st.session_state.get("prerequis_workflow_state", {})
    
    if not workflow_state:
        st.warning("⚠️ Aucun résultat disponible.")
        return
    
    # Sauvegarder dans la base de données si pas déjà fait
    project_id = st.session_state.get("current_project_id")
    if project_id:
        save_key = "prerequis_saved_to_db"
        if not st.session_state.get(save_key, False):
            try:
                final_evaluations = workflow_state.get("final_evaluations", [])
                synthese_globale = workflow_state.get("synthese_globale", "")
                
                if final_evaluations:
                    # Préparer les données pour la sauvegarde
                    prerequis_data = {
                        "evaluations": [
                            {
                                "prerequis_id": eval_item.get("prerequis_id") if isinstance(eval_item, dict) else getattr(eval_item, "prerequis_id", None),
                                "titre": eval_item.get("titre") if isinstance(eval_item, dict) else getattr(eval_item, "titre", ""),
                                "note": round(eval_item.get("note", 0.0) if isinstance(eval_item, dict) else getattr(eval_item, "note", 0.0), 1),
                                "evaluation_text": eval_item.get("evaluation_text") if isinstance(eval_item, dict) else getattr(eval_item, "evaluation_text", "")
                            }
                            for eval_item in final_evaluations
                        ],
                        "synthese_globale": synthese_globale
                    }
                    
                    result_id = save_agent_result(
                        project_id=project_id,
                        workflow_type="prerequis_evaluation",
                        result_type="prerequis",
                        data=prerequis_data,
                        status="validated"
                    )
                    
                    if result_id:
                        st.session_state[save_key] = True
                        st.success("✅ Résultats sauvegardés dans la base de données")
            except Exception as e:
                st.error(f"❌ Erreur lors de la sauvegarde : {str(e)}")
    
    st.success("✅ Évaluation des prérequis terminée !")
    st.markdown("---")
    
    # Afficher les évaluations
    final_evaluations = workflow_state.get("final_evaluations", [])
    synthese_globale = workflow_state.get("synthese_globale", "")
    
    if not final_evaluations:
        st.warning("⚠️ Aucune évaluation disponible.")
        return
    
    # Trier les évaluations par prerequis_id pour garantir l'ordre
    sorted_evaluations = sorted(final_evaluations, key=lambda e: e.get("prerequis_id", 0) if isinstance(e, dict) else getattr(e, "prerequis_id", 0))
    
    st.markdown("## 📊 Tous les Prérequis Validés")
    st.markdown("---")
    
    # Afficher tous les prérequis validés en texte simple (2 par 2)
    for i in range(0, len(sorted_evaluations), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            if i + j < len(sorted_evaluations):
                evaluation = sorted_evaluations[i + j]
                # Gérer dict ou objet
                if isinstance(evaluation, dict):
                    prerequis_id = evaluation.get("prerequis_id", "N/A")
                    titre = evaluation.get("titre", "N/A")
                    note = evaluation.get("note", 0.0)
                    evaluation_text = evaluation.get("evaluation_text", "")
                else:
                    prerequis_id = getattr(evaluation, "prerequis_id", "N/A")
                    titre = getattr(evaluation, "titre", "N/A")
                    note = getattr(evaluation, "note", 0.0)
                    evaluation_text = getattr(evaluation, "evaluation_text", "")
                
                with col:
                    # Arrondir la note à 1 décimale pour l'affichage
                    note_rounded = round(note, 1)
                    st.markdown(f"### {prerequis_id}. {titre}")
                    st.markdown(f"**Note : {note_rounded}/5**")
                    st.markdown(f"**Évaluation :**")
                    st.markdown(evaluation_text)
                    st.markdown("---")
    
    # Afficher la synthèse globale
    if synthese_globale:
        st.markdown("## 📋 Synthèse Globale")
        st.markdown(synthese_globale)


if __name__ == "__main__":
    main()

