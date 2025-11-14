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

# Configuration de l'API
# Utiliser la variable d'environnement API_URL si disponible, sinon utiliser localhost pour le développement
API_URL = os.getenv("API_URL", "http://localhost:2025")

# Initialisation des interfaces de validation
validation_interface = StreamlitValidationInterface()
use_case_validation = StreamlitUseCaseValidation()

# Configuration de la page
st.set_page_config(
    page_title="aiko - Analyse des Besoins IA",
    page_icon="🤖",
    layout="wide"
)

# Chemin vers le fichier de configuration des intervieweurs
CONFIG_DIR = Path(__file__).parent.parent / "config"
INTERVIEWERS_CONFIG_FILE = CONFIG_DIR / "interviewers.json"
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
    Charge la liste des intervieweurs depuis le fichier JSON.
    
    Returns:
        Liste des noms d'intervieweurs
    """
    try:
        if INTERVIEWERS_CONFIG_FILE.exists():
            with open(INTERVIEWERS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                interviewers = config.get("interviewers", DEFAULT_INTERVIEWERS)
                # Si la liste est vide, utiliser les valeurs par défaut
                if not interviewers:
                    interviewers = DEFAULT_INTERVIEWERS
                    save_interviewers(interviewers)
                return interviewers
        else:
            # Créer le fichier avec les valeurs par défaut
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            save_interviewers(DEFAULT_INTERVIEWERS)
            return DEFAULT_INTERVIEWERS
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des intervieweurs : {str(e)}")
        return DEFAULT_INTERVIEWERS

def save_interviewers(interviewers: List[str]) -> bool:
    """
    Sauvegarde la liste des intervieweurs dans le fichier JSON.
    
    Args:
        interviewers: Liste des noms d'intervieweurs à sauvegarder
    
    Returns:
        True si la sauvegarde a réussi, False sinon
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = {"interviewers": interviewers}
        with open(INTERVIEWERS_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
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
        for uploaded_file in files:
            files_data.append(
                ("files", (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type))
            )
        
        response = requests.post(
            f"{API_URL}/files/upload",
            files=files_data
        )
        response.raise_for_status()
        
        result = response.json()
        # Retourner à la fois file_types et file_paths pour gérer les fichiers Word
        return {
            "workshop": result.get("file_types", {}).get("workshop", []),
            "transcript": result.get("file_types", {}).get("transcript", []),
            "file_paths": result.get("file_paths", [])
        }
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'upload: {str(e)}")
        return {"workshop": [], "transcript": [], "file_paths": []}

def start_workflow_api_call(workshop_files: List[str], transcript_files: List[str], company_name: str, company_url: str, company_description: str, validated_company_info: Optional[Dict[str, Any]], interviewer_names: List[str], additional_context: str, result_queue: queue.Queue):
    """
    Fait l'appel API dans un thread séparé.
    Met le résultat dans la queue : (success: bool, thread_id: str, error_msg: str)
    """
    try:
        # Générer un thread_id
        thread_id = str(uuid.uuid4())
        
        # Lancer le workflow
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/runs",
            json={
                "workshop_files": workshop_files,
                "transcript_files": transcript_files,
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
        result_queue.put((True, None))
    
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
        
        # Section Diag - Synthèse de mission
        st.markdown("**Génération du rapport**")
        page_diag = st.radio(
            "Navigation Génération du rapport",
            ["Génération des Enjeux et Recommandations", "Rappel de la mission", "Atouts de l'entreprise"],
            index=0 if st.session_state.current_page == "Génération des Enjeux et Recommandations" else (1 if st.session_state.current_page == "Rappel de la mission" else (2 if st.session_state.current_page == "Atouts de l'entreprise" else None)),
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

def display_diagnostic_section():
    """Affiche la section de génération du diagnostic (utilise fichiers depuis session_state)"""
    st.header("🔍 Générer les Use Cases")
    
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
                # Extraire les file_paths depuis la nouvelle structure
                transcript_file_paths = get_transcript_file_paths(st.session_state.uploaded_transcripts)
                future = executor.submit(
                    start_workflow_api_call,
                    st.session_state.uploaded_workshops,
                    transcript_file_paths,
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
        display_final_results()
    
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
                success, error_msg = result_queue.get(timeout=1)
                
                if success:
                    # Déterminer le message selon l'action
                    if use_case_user_action == "finalize_use_cases":
                        st.session_state.workflow_status = "completed"
                        status_placeholder.success("✅ Validation envoyée ! Le workflow est terminé !")
                    else:
                        status_placeholder.success("✅ Validation envoyée ! Régénération des use cases en cours...")
                    time.sleep(1)
                    st.rerun()
                else:
                    status_placeholder.error(f"❌ Erreur : {error_msg}")
            
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

def display_final_results():
    """Affiche les résultats finaux"""
    
    st.markdown("### Résultats Finaux")
    
    final_needs = st.session_state.workflow_state.get("final_needs", [])
    final_use_cases = st.session_state.workflow_state.get("final_use_cases", [])
    
    # Affichage des métriques
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("📋 Besoins Validés", len(final_needs))
    
    with col2:
        st.metric("🎯 Cas d'Usage Validés", len(final_use_cases))
    
    # Afficher les besoins validés
    if final_needs:
        with st.expander("📋 Voir les besoins validés", expanded=True):
            for i, need in enumerate(final_needs, 1):
                st.markdown(f"### {i}. {need.get('theme', 'N/A')}")
                quotes = need.get('quotes', [])
                if quotes:
                    st.markdown("**Citations clés :**")
                    for quote in quotes:
                        st.markdown(f"• {quote}")
                st.markdown("---")
    
    # Afficher les cas d'usage validés
    if final_use_cases:
        with st.expander("🎯 Voir les cas d'usage validés", expanded=True):
            for i, uc in enumerate(final_use_cases, 1):
                st.markdown(f"### {i}. {uc.get('titre', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                # Afficher la famille si elle existe
                famille = uc.get('famille', '')
                if famille:
                    st.markdown(f"**Famille :** {famille}")
                st.markdown("---")
    
    # Boutons de téléchargement
    if final_needs or final_use_cases:
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
                width="stretch"
            )
        
        with col2:
            # Bouton de génération de rapport Word
            if st.button("📄 Générer le rapport Word", type="primary", width="stretch"):
                generate_word_report()
    
    st.markdown("---")
    
    # Bouton pour recommencer
    if st.button("Nouvelle Analyse", width="stretch"):
        st.session_state.thread_id = None
        st.session_state.workflow_status = None
        st.session_state.uploaded_files = {}
        st.session_state.workflow_state = {}
        st.rerun()

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
            
            col1, col2, col3, col4 = st.columns([3, 3, 1, 1])
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
            with col3:
                is_interviewer = speaker.get("is_interviewer", False)
                if is_interviewer:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("Interviewer")
                else:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.caption("Participant")
            with col4:
                # Bouton supprimer (sauf pour les interviewers)
                if not is_interviewer:
                    if st.button("🗑️", key=f"delete_speaker_{speaker_unique_id}", help="Supprimer ce speaker"):
                        st.session_state.delete_speaker_id = speaker_unique_id
                        st.rerun()
            
            updated_speakers.append({
                "name": speaker_name,
                "role": speaker_role,
                "is_interviewer": is_interviewer,
                "unique_id": speaker_unique_id
            })
        
        st.session_state.current_transcript_speakers = updated_speakers
        
        # Bouton pour ajouter un nouveau speaker
        st.markdown("---")
        with st.expander("➕ Ajouter un speaker manuellement"):
            col1, col2 = st.columns(2)
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
            
            if st.button("➕ Ajouter ce speaker", key="add_new_speaker_btn"):
                if new_speaker_name and new_speaker_name.strip():
                    new_speaker = {
                        "name": new_speaker_name.strip(),
                        "role": new_speaker_role.strip() if new_speaker_role else "",
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
                # Sauvegarder le transcript dans la liste
                transcript_data = {
                    "file_path": st.session_state.current_transcript_file_path,
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
            col1, col2 = st.columns([4, 1])
            with col1:
                filename = os.path.basename(transcript.get("file_path", ""))
                st.markdown(f"**{filename}**")
                speakers_text = " | ".join([
                    f"{s.get('name', '')} | {s.get('role', '')}"
                    for s in transcript.get("speakers", [])
                ])
                if speakers_text:
                    st.caption(f"Intervenants: {speakers_text}")
            with col2:
                if st.button("🗑️", key=f"delete_transcript_{idx}", help="Supprimer"):
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
            
            # Ajouter les nouveaux chemins aux workshops existants
            existing_workshops = st.session_state.get("uploaded_workshops", [])
            st.session_state.uploaded_workshops = existing_workshops + new_paths
            
            # Marquer les fichiers comme uploadés
            for f in new_workshops:
                st.session_state.uploaded_file_names.add(f.name)
            
            st.success(f"✅ {len(new_workshops)} nouveau(x) fichier(s) d'atelier sauvegardé(s)")
            # Forcer la mise à jour de la sidebar
            st.rerun()
    
    # Afficher les workshops déjà uploadés
    if st.session_state.uploaded_workshops:
        st.markdown("**Fichiers d'ateliers sauvegardés :**")
        for path in st.session_state.uploaded_workshops:
            filename = os.path.basename(path)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(f"• {filename}")
            with col2:
                if st.button("🗑️", key=f"delete_workshop_{path}", help="Supprimer"):
                    st.session_state.uploaded_workshops.remove(path)
                    # Retirer aussi le nom du fichier du tracking si on peut le retrouver
                    file_basename = os.path.basename(path)
                    # Chercher le nom original dans uploaded_file_names
                    for name in list(st.session_state.uploaded_file_names):
                        if file_basename.endswith(name) or name in file_basename:
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
            placeholder="Ex: Cousin Surgery",
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
    
    # Si le workflow est en cours, afficher la progression
    if st.session_state.get("executive_thread_id") and st.session_state.get("executive_workflow_status") is not None:
        display_executive_workflow_progress()
        return
    
    # Vérifier que les fichiers sont uploadés
    if not st.session_state.uploaded_transcripts and not st.session_state.uploaded_workshops:
        st.warning("⚠️ Veuillez d'abord uploader des fichiers dans la section 'Upload de documents'.")
        return
    
    if not st.session_state.company_name:
        st.warning("⚠️ Veuillez d'abord saisir le nom de l'entreprise dans la section 'Upload de documents'.")
        return
    
    # Upload fichier Word
    st.subheader("📄 Rapport Word (Généré précédemment)")
    word_file = st.file_uploader(
        "Uploadez le rapport Word généré (fichier .docx)",
        type=["docx"],
        key="word_report_upload"
    )
    
    if not word_file:
        st.warning("⚠️ Veuillez uploader le fichier Word du rapport généré précédemment.")
        return
    
    # Vérifier si le fichier a changé
    current_file_name = word_file.name if word_file else None
    previous_file_name = st.session_state.get("word_file_name")
    
    if current_file_name != previous_file_name:
        # Le fichier a changé, réinitialiser l'extraction
        st.session_state.word_extraction_validated = False
        st.session_state.word_extraction_data = None
        st.session_state.word_path = None
        st.session_state.word_file_name = current_file_name
    
    # Vérifier si l'extraction a déjà été faite et validée
    if st.session_state.get("word_extraction_validated") and st.session_state.get("word_extraction_data"):
        st.success("✅ Extraction validée")
        if st.button("🔄 Ré-extraire le fichier Word", type="secondary"):
            st.session_state.word_extraction_validated = False
            st.session_state.word_extraction_data = None
            st.session_state.word_path = None
            st.rerun()
    else:
        # Upload et extraction du fichier Word
        if st.session_state.get("word_path") is None:
            with st.spinner("📤 Upload du fichier Word..."):
                try:
                    word_paths = upload_files_to_api([word_file])
                    # Le fichier Word sera dans file_paths (tous les fichiers uploadés)
                    all_paths = word_paths.get("file_paths", [])
                    if all_paths:
                        word_path = all_paths[0]  # Prendre le premier fichier uploadé
                    else:
                        # Fallback: chercher dans workshop (car l'API met les .docx dans workshop)
                        workshop_paths = word_paths.get("workshop", [])
                        if workshop_paths:
                            word_path = workshop_paths[0]
                        else:
                            word_path = None
                    
                    if not word_path:
                        st.error("❌ Erreur lors de l'upload du fichier Word")
                        return
                    
                    st.session_state.word_path = word_path
                    st.session_state.word_file_name = current_file_name
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'upload du fichier Word: {str(e)}")
                    return
        else:
            word_path = st.session_state.word_path
        
        # Extraction des données du Word via l'API
        if st.session_state.get("word_extraction_data") is None:
            # Option pour forcer l'extraction LLM
            force_llm = st.session_state.get("force_llm_extraction", False)
            
            with st.spinner("🔍 Extraction des données du rapport Word..."):
                try:
                    # Appeler l'API pour extraire les données (le fichier est sur le serveur API)
                    response = requests.post(
                        f"{API_URL}/word/extract",
                        json={
                            "word_path": word_path,
                            "force_llm": force_llm
                        },
                        timeout=300  # 5 minutes max pour l'extraction
                    )
                    response.raise_for_status()
                    extracted_data = response.json()
                    st.session_state.word_extraction_data = extracted_data
                    
                    # Afficher la méthode d'extraction utilisée
                    extraction_method = extracted_data.get("extraction_method", "unknown")
                    if extraction_method == "structured":
                        st.success("✅ Extraction réussie via parsing structuré")
                    elif extraction_method == "llm_fallback":
                        st.info("ℹ️ Extraction réussie via LLM (fallback automatique)")
                    elif extraction_method == "llm_forced":
                        st.info("🤖 Extraction réussie via LLM (forcé par l'utilisateur)")
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'extraction: {str(e)}")
                    return
        
        # Afficher l'interface de validation
        executive_validation = StreamlitExecutiveValidation()
        
        validation_result = executive_validation.display_word_extraction_for_validation(
            st.session_state.word_extraction_data,
            key_suffix="word_extraction"
        )
        
        # Bouton pour ré-extraire avec LLM si l'extraction structurée n'a pas donné de bons résultats
        extraction_method = st.session_state.word_extraction_data.get("extraction_method", "unknown")
        if extraction_method == "structured":
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🤖 Ré-extraire avec LLM", help="Force l'extraction via LLM si les résultats ne sont pas satisfaisants"):
                    st.session_state.force_llm_extraction = True
                    st.session_state.word_extraction_data = None
                    st.rerun()
        
        if validation_result:
            # Stocker les données validées
            st.session_state.word_extraction_validated = True
            st.session_state.validated_word_extraction = validation_result
            st.rerun()
        
        # Ne pas afficher le reste tant que l'extraction n'est pas validée
        return
    
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
    if st.button("🚀 Démarrer la Génération Executive Summary", type="primary", width="stretch"):
        word_path = st.session_state.get("word_path")
        if not word_path:
            st.error("❌ Erreur : chemin du fichier Word non trouvé")
            return
        
        # Récupérer les données validées
        validated_data = st.session_state.get("validated_word_extraction", {})
        validated_needs = validated_data.get("validated_needs", [])
        validated_use_cases = validated_data.get("validated_use_cases", [])
        
        # Démarrer le workflow Executive Summary
        with st.spinner("🚀 Démarrage du workflow Executive Summary..."):
            try:
                # Créer un thread_id unique
                thread_id = str(uuid.uuid4())
                st.session_state.executive_thread_id = thread_id
                
                # NOUVEAU: Préparer les speakers validés depuis uploaded_transcripts
                validated_speakers = []
                for transcript in st.session_state.uploaded_transcripts:
                    validated_speakers.extend(transcript.get("speakers", []))
                
                # Appel API pour démarrer le workflow avec les données validées
                response = requests.post(
                    f"{API_URL}/executive-summary/threads/{thread_id}/runs",
                    json={
                        "word_report_path": word_path,
                        "transcript_files": get_transcript_file_paths(st.session_state.uploaded_transcripts),
                        "workshop_files": st.session_state.uploaded_workshops,
                        "company_name": st.session_state.company_name,
                        "interviewer_note": interviewer_note or "",
                        "validated_needs": validated_needs,
                        "validated_use_cases": validated_use_cases,
                        "validated_speakers": validated_speakers  # NOUVEAU
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
    
    # Si un workflow est en cours, afficher la progression
    if st.session_state.get("atouts_thread_id"):
        display_atouts_workflow_progress()
        return
    
    # Afficher les résultats finaux s'ils existent
    if st.session_state.get("atouts_workflow_completed"):
        display_atouts_final_results()
        return
    
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
                # Préparer les chemins des PDFs
                pdf_paths = get_transcript_file_paths(uploaded_transcripts)
                
                # Récupérer les noms des interviewers
                interviewer_names = load_interviewers()
                
                # NOUVEAU: Préparer les speakers validés depuis uploaded_transcripts
                validated_speakers = []
                for transcript in uploaded_transcripts:
                    validated_speakers.extend(transcript.get("speakers", []))
                
                # Appeler l'API pour démarrer le workflow avec le contexte
                response = requests.post(
                    f"{API_URL}/atouts-entreprise/threads/{thread_id}/runs",
                    json={
                        "pdf_paths": pdf_paths,
                        "company_info": validated_company_info,
                        "interviewer_names": interviewer_names,
                        "atouts_additional_context": additional_context,
                        "validated_speakers": validated_speakers  # NOUVEAU
                    },
                    timeout=600
                )
                response.raise_for_status()
                
                st.success("✅ Workflow démarré ! Analyse en cours...")
                time.sleep(1)
                st.rerun()
                    
        except requests.exceptions.Timeout:
            st.error("❌ La requête a expiré. Le traitement prend trop de temps. Veuillez réessayer.")
            st.session_state.atouts_thread_id = None
        except Exception as e:
            st.error(f"❌ Erreur lors du démarrage du workflow : {str(e)}")
            st.session_state.atouts_thread_id = None


if __name__ == "__main__":
    main()

