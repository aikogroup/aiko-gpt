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
from typing import List, Dict, Any
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
        logo_path = config.get_logo_path()
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
    if 'rappel_mission' not in st.session_state:
        st.session_state.rappel_mission = ""
    if 'rappel_mission_company' not in st.session_state:
        st.session_state.rappel_mission_company = ""

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

def start_workflow_api_call(workshop_files: List[str], transcript_files: List[str], company_name: str, company_url: str, company_description: str, interviewer_names: List[str], additional_context: str, result_queue: queue.Queue):
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
        
        if "human_validation" in next_nodes:
            return "waiting_validation"
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
                                      user_feedback: str, thread_id: str, result_queue: queue.Queue):
    """
    Envoie le feedback de validation à l'API dans un thread séparé.
    """
    try:
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/validation",
            json={
                "validated_needs": validated_needs,
                "rejected_needs": rejected_needs,
                "user_feedback": user_feedback
            },
            timeout=600  # 10 minutes pour la validation et la reprise du workflow
        )
        response.raise_for_status()
        result_queue.put((True, None))
    
    except Exception as e:
        result_queue.put((False, str(e)))

def send_use_case_validation_feedback_api_call(validated_qw: List[Dict], validated_sia: List[Dict],
                                                rejected_qw: List[Dict], rejected_sia: List[Dict], 
                                                user_feedback: str, thread_id: str, result_queue: queue.Queue):
    """
    Envoie le feedback de validation des use cases à l'API dans un thread séparé.
    """
    try:
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/use-case-validation",
            json={
                "validated_quick_wins": validated_qw,
                "validated_structuration_ia": validated_sia,
                "rejected_quick_wins": rejected_qw,
                "rejected_structuration_ia": rejected_sia,
                "user_feedback": user_feedback
            },
            timeout=600  # 10 minutes pour la validation finale
        )
        response.raise_for_status()
        
        result = response.json()
        result_queue.put((True, result.get("success"), None))
    
    except Exception as e:
        result_queue.put((False, None, str(e)))

# ==================== INTERFACE STREAMLIT ====================

def display_home_page():
    """Affiche la page d'accueil avec le logo et le message de bienvenue"""
    # Charger le logo depuis config.py (détection automatique)
    import config
    logo_path = config.get_logo_path()
    
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
    st.header("🎯 Génération des Enjeux et Recommandations")
    
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

def display_recommendations_section():
    """Affiche la section de génération des recommandations (placeholder)"""
    st.header("📋 Génération des Enjeux et Recommandations")
    st.info("💡 Cette section sera disponible prochainement.")
    st.markdown("""
    Cette fonctionnalité permettra de générer des enjeux et recommandations personnalisées
    basées sur les analyses précédentes.
    """)

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
            ["Upload de documents", "Configuration des Intervieweurs"],
            index=0 if st.session_state.current_page == "Upload de documents" else (1 if st.session_state.current_page == "Configuration des Intervieweurs" else None),
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
            ["Génération des Enjeux et Recommandations", "Rappel de la mission"],
            index=0 if st.session_state.current_page == "Génération des Enjeux et Recommandations" else (1 if st.session_state.current_page == "Rappel de la mission" else None),
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
        
        # Nom de l'entreprise
        company_name = st.session_state.get("company_name", "")
        if company_name:
            st.success(f"🏢 {company_name}")
        else:
            st.info("🏢 Aucune entreprise sélectionnée")
        
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

def display_diagnostic_section():
    """Affiche la section de génération du diagnostic (utilise fichiers depuis session_state)"""
    st.header("🔍 Générer les Use Cases")
    
    # Si le workflow est en cours, afficher la progression
    if st.session_state.thread_id and st.session_state.workflow_status is not None:
        display_workflow_progress()
        return
    
    st.info("💡 Cette section génère l'analyse des besoins et des cas d'usage. Les fichiers sont chargés depuis la section 'Upload de documents'.")
    
    # Vérifier que les fichiers sont uploadés
    if not st.session_state.uploaded_transcripts and not st.session_state.uploaded_workshops:
        st.warning("⚠️ Veuillez d'abord uploader des fichiers dans la section 'Upload de documents'.")
        return
    
    if not st.session_state.company_name:
        st.warning("⚠️ Veuillez d'abord saisir le nom de l'entreprise dans la section 'Upload de documents'.")
        return
    
    # Afficher les fichiers sélectionnés
    st.subheader("📋 Fichiers sélectionnés")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Transcriptions", len(st.session_state.uploaded_transcripts))
        if st.session_state.uploaded_transcripts:
            with st.expander("Voir les fichiers"):
                for path in st.session_state.uploaded_transcripts:
                    st.text(f"• {os.path.basename(path)}")
    with col2:
        st.metric("Ateliers", len(st.session_state.uploaded_workshops))
        if st.session_state.uploaded_workshops:
            with st.expander("Voir les fichiers"):
                for path in st.session_state.uploaded_workshops:
                    st.text(f"• {os.path.basename(path)}")
    
    st.metric("Entreprise", st.session_state.company_name)
    
    # Zone : Informations supplémentaires
    st.subheader("💡 Informations Supplémentaires")
    st.info("💡 Vous pouvez ajouter ici des informations complémentaires qui ne sont pas présentes dans les transcriptions ou les ateliers.")
    additional_context = st.text_area(
        "Informations supplémentaires",
        placeholder="Ex: L'entreprise souhaite prioriser les solutions IA pour la R&D. Il y a également un projet de fusion prévu pour 2025 qui impacte la stratégie.",
        height=150,
        key="additional_context_input"
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
                future = executor.submit(
                    start_workflow_api_call,
                    st.session_state.uploaded_workshops,
                    st.session_state.uploaded_transcripts,
                    st.session_state.company_name,
                    st.session_state.get("company_url", ""),
                    st.session_state.get("company_description", ""),
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
        st.warning("⏸️ **Validation requise !**")
        display_needs_validation_interface()
        # Pas de rerun automatique ici, l'utilisateur doit valider
    
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

def display_needs_validation_interface():
    """
    Affiche l'interface de validation des besoins.
    Utilise StreamlitValidationInterface et envoie le résultat à l'API.
    """
    
    st.markdown("### Validation des Besoins Identifiés")
    
    identified_needs = st.session_state.workflow_state.get("identified_needs", [])
    validated_count = len(st.session_state.workflow_state.get("validated_needs", []))
    iteration_count = st.session_state.workflow_state.get("iteration_count", 0)
    
    # Nettoyer les anciennes clés de checkbox de l'itération précédente
    if 'last_needs_iteration' not in st.session_state or st.session_state.last_needs_iteration != iteration_count:
        # Nouvelle itération - nettoyer UNIQUEMENT les anciennes clés (avec l'ancien iteration_count)
        if 'last_needs_iteration' in st.session_state:
            old_iteration = st.session_state.last_needs_iteration
            for key in list(st.session_state.keys()):
                if key.startswith("validate_need_") and key.endswith(f"_{old_iteration}"):
                    del st.session_state[key]
        st.session_state.last_needs_iteration = iteration_count
    
    # Affichage du message de progression
    remaining_to_validate = max(0, 5 - validated_count)
    
    if iteration_count == 0:
        st.info(f"**Première proposition** : {len(identified_needs)} besoins identifiés - Veuillez en valider au moins 5")
    else:
        st.info(f"**Itération {iteration_count}** : Vous avez déjà validé **{validated_count}/5** besoins. "
                f"Il vous reste **{remaining_to_validate} besoins à valider** parmi les **{len(identified_needs)} nouveaux besoins** proposés.")
    
    st.markdown("---")
    
    # ✅ UTILISER LA CLASSE pour afficher l'interface de validation
    # La classe retourne le résultat si l'utilisateur clique sur "Valider"
    result = validation_interface.display_needs_for_validation(
        identified_needs=identified_needs,
        validated_count=validated_count,
        key_suffix=str(iteration_count)  # Utiliser iteration_count comme suffixe
    )
    
    # Si un résultat est retourné, envoyer à l'API avec messages rotatifs
    if result is not None:
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
                    time.sleep(1)
                    st.rerun()
                else:
                    status_placeholder.error(f"❌ Erreur : {error_msg}")
            
            except queue.Empty:
                status_placeholder.error("❌ Timeout lors de la validation")

def display_use_cases_validation_interface():
    """
    Affiche l'interface de validation des use cases.
    Utilise StreamlitUseCaseValidation et envoie le résultat à l'API.
    """
    
    st.markdown("### Validation des Cas d'Usage IA")
    
    proposed_qw = st.session_state.workflow_state.get("proposed_quick_wins", [])
    proposed_sia = st.session_state.workflow_state.get("proposed_structuration_ia", [])
    validated_qw_count = len(st.session_state.workflow_state.get("validated_quick_wins", []))
    validated_sia_count = len(st.session_state.workflow_state.get("validated_structuration_ia", []))
    use_case_iteration = st.session_state.workflow_state.get("use_case_iteration", 0)
    
    # Nettoyer les anciennes clés de checkbox de l'itération précédente
    if 'last_uc_iteration' not in st.session_state or st.session_state.last_uc_iteration != use_case_iteration:
        # Nouvelle itération - nettoyer UNIQUEMENT les anciennes clés
        if 'last_uc_iteration' in st.session_state:
            old_iteration = st.session_state.last_uc_iteration
            for key in list(st.session_state.keys()):
                if (key.startswith("validate_qw_") or key.startswith("validate_sia_")) and key.endswith(f"_{old_iteration}"):
                    del st.session_state[key]
        st.session_state.last_uc_iteration = use_case_iteration
    
    # Message de progression
    remaining_qw = max(0, 5 - validated_qw_count)
    remaining_sia = max(0, 5 - validated_sia_count)
    
    st.info(f"**Quick Wins** : {validated_qw_count}/5 validés (encore {remaining_qw} requis) | "
            f"**Structuration IA** : {validated_sia_count}/5 validés (encore {remaining_sia} requis)")
    
    st.markdown("---")
    
    # ✅ UTILISER LA CLASSE pour afficher l'interface de validation
    # La classe retourne le résultat si l'utilisateur clique sur "Valider"
    result = use_case_validation.display_use_cases_for_validation(
        quick_wins=proposed_qw,
        structuration_ia=proposed_sia,
        validated_qw_count=validated_qw_count,
        validated_sia_count=validated_sia_count,
        key_suffix=str(use_case_iteration)  # Utiliser use_case_iteration comme suffixe
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
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                send_use_case_validation_feedback_api_call,
                result['validated_quick_wins'],
                result['validated_structuration_ia'],
                result['rejected_quick_wins'],
                result['rejected_structuration_ia'],
                result['user_feedback'],
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
                success, is_completed, error_msg = result_queue.get(timeout=1)
                
                if success:
                    if is_completed:
                        st.session_state.workflow_status = "completed"
                        status_placeholder.success("✅ Validation envoyée ! Le workflow est terminé !")
                    else:
                        st.session_state.workflow_status = "paused"
                        status_placeholder.warning("⏸️ Validation envoyée ! Nouvelle validation requise...")
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
            final_quick_wins = workflow_state.get('final_quick_wins', [])
            final_structuration_ia = workflow_state.get('final_structuration_ia', [])
            
            # Vérifier qu'on a au moins des données à exporter
            if not final_needs and not final_quick_wins and not final_structuration_ia:
                st.warning("⚠️ Aucune donnée à exporter. Veuillez d'abord valider des besoins et des cas d'usage.")
                return
            
            # Initialiser le générateur de rapport
            report_generator = ReportGenerator()
            
            # Générer le rapport
            output_path = report_generator.generate_report(
                company_name=company_name,
                final_needs=final_needs,
                final_quick_wins=final_quick_wins,
                final_structuration_ia=final_structuration_ia
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
    final_qw = st.session_state.workflow_state.get("final_quick_wins", [])
    final_sia = st.session_state.workflow_state.get("final_structuration_ia", [])
    
    # Affichage des métriques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 Besoins Validés", len(final_needs))
    
    with col2:
        st.metric("⚡ Quick Wins", len(final_qw))
    
    with col3:
        st.metric("🏗️ Structuration IA", len(final_sia))
    
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
    
    # Afficher les Quick Wins
    if final_qw:
        with st.expander("⚡ Voir les Quick Wins validés", expanded=True):
            for i, uc in enumerate(final_qw, 1):
                st.markdown(f"### {i}. {uc.get('titre', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                st.markdown("---")
    
    # Afficher les Structuration IA
    if final_sia:
        with st.expander("🏗️ Voir les Structuration IA validés", expanded=True):
            for i, uc in enumerate(final_sia, 1):
                st.markdown(f"### {i}. {uc.get('titre', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                st.markdown("---")
    
    # Boutons de téléchargement
    if final_needs or final_qw or final_sia:
        col1, col2 = st.columns(2)
        
        with col1:
            # Bouton de téléchargement JSON
            results_json = {
                "final_needs": final_needs,
                "final_quick_wins": final_qw,
                "final_structuration_ia": final_sia
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
    if st.button("🔄 Nouvelle Analyse", width="stretch"):
        st.session_state.thread_id = None
        st.session_state.workflow_status = None
        st.session_state.uploaded_files = {}
        st.session_state.workflow_state = {}
        st.rerun()

def display_upload_documents_section():
    """Section pour uploader et gérer les documents de manière persistante (session)"""
    st.header("📁 Upload de Documents")
    st.info("💡 Uploadez vos fichiers ici. Ils seront conservés pendant toute la session et réutilisables dans les workflows.")
    
    # Initialiser le tracking des fichiers déjà uploadés
    if 'uploaded_file_names' not in st.session_state:
        st.session_state.uploaded_file_names = set()
    
    # Upload Transcripts
    st.subheader("📄 Transcriptions (PDF ou JSON)")
    uploaded_transcripts = st.file_uploader(
        "Uploadez vos transcriptions",
        type=["pdf", "json"],
        accept_multiple_files=True,
        key="upload_transcripts_persistent"
    )
    
    if uploaded_transcripts:
        # Filtrer uniquement les nouveaux fichiers (ceux qui n'ont pas encore été uploadés)
        new_transcripts = [
            f for f in uploaded_transcripts 
            if f.name not in st.session_state.uploaded_file_names
        ]
        
        if new_transcripts:
            # Sauvegarder dans session_state
            transcript_paths = upload_files_to_api(new_transcripts)
            new_paths = transcript_paths.get("transcript", [])
            
            # Ajouter les nouveaux chemins aux transcripts existants
            existing_transcripts = st.session_state.get("uploaded_transcripts", [])
            st.session_state.uploaded_transcripts = existing_transcripts + new_paths
            
            # Marquer les fichiers comme uploadés
            for f in new_transcripts:
                st.session_state.uploaded_file_names.add(f.name)
            
            st.success(f"✅ {len(new_transcripts)} nouveau(x) fichier(s) de transcription sauvegardé(s)")
            # Forcer la mise à jour de la sidebar
            st.rerun()
    
    # Afficher les transcripts déjà uploadés
    if st.session_state.uploaded_transcripts:
        st.markdown("**Fichiers de transcription sauvegardés :**")
        for path in st.session_state.uploaded_transcripts:
            filename = os.path.basename(path)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text(f"• {filename}")
            with col2:
                if st.button("🗑️", key=f"delete_transcript_{path}", help="Supprimer"):
                    st.session_state.uploaded_transcripts.remove(path)
                    # Retirer aussi le nom du fichier du tracking si on peut le retrouver
                    file_basename = os.path.basename(path)
                    # Chercher le nom original dans uploaded_file_names
                    for name in list(st.session_state.uploaded_file_names):
                        if file_basename.endswith(name) or name in file_basename:
                            st.session_state.uploaded_file_names.discard(name)
                            break
                    st.rerun()
    
    st.markdown("---")
    
    # Upload Workshops
    st.subheader("📝 Ateliers (Fichiers Excel)")
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
    
    st.markdown("---")
    
    # Informations sur l'entreprise
    st.subheader("🏢 Informations sur l'Entreprise")
    
    # Initialiser les variables pour suivre les changements
    if 'previous_company_name' not in st.session_state:
        st.session_state.previous_company_name = st.session_state.get("company_name", "")
    if 'previous_company_url' not in st.session_state:
        st.session_state.previous_company_url = st.session_state.get("company_url", "")
    if 'previous_company_description' not in st.session_state:
        st.session_state.previous_company_description = st.session_state.get("company_description", "")
    
    # Créer 3 colonnes côte à côte
    col1, col2, col3 = st.columns(3)
    
    with col1:
        company_name = st.text_input(
            "Nom de l'entreprise",
            value=st.session_state.company_name,
            placeholder="Ex: Cousin Surgery",
            key="company_name_persistent"
        )
    
    with col2:
        company_url = st.text_input(
            "URL de l'entreprise (optionnel)",
            value=st.session_state.company_url,
            placeholder="Ex: https://www.example.com",
            key="company_url_persistent"
        )
    
    with col3:
        company_description = st.text_input(
            "Description de l'activité (optionnel)",
            value=st.session_state.company_description,
            placeholder="Ex: Fabricant de dispositifs médicaux",
            key="company_description_persistent"
        )
    
    # Normaliser les valeurs (strip si non vide, sinon chaîne vide)
    normalized_name = company_name.strip() if company_name else ""
    normalized_url = company_url.strip() if company_url else ""
    normalized_description = company_description.strip() if company_description else ""
    
    # Vérifier si les valeurs ont changé
    name_changed = normalized_name != st.session_state.previous_company_name
    url_changed = normalized_url != st.session_state.previous_company_url
    description_changed = normalized_description != st.session_state.previous_company_description
    
    # Mettre à jour le session_state si les valeurs ont changé
    if name_changed or url_changed or description_changed:
        st.session_state.company_name = normalized_name
        st.session_state.previous_company_name = normalized_name
        st.session_state.company_url = normalized_url
        st.session_state.previous_company_url = normalized_url
        st.session_state.company_description = normalized_description
        st.session_state.previous_company_description = normalized_description
        # Forcer la mise à jour de la sidebar seulement si une valeur a changé
        st.rerun()
    
    # Afficher le message de succès seulement si un nom est saisi
    if company_name and company_name.strip():
        st.success(f"🏢 {company_name.strip()}")

def display_recommendations_section():
    """Section pour générer l'Executive Summary (enjeux et recommandations)"""
    st.header("🎯 Génération des Enjeux et Recommandations")
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
    
    # Note de l'intervieweur
    st.subheader("📝 Note de l'Intervieweur")
    interviewer_note = st.text_area(
        "Note ou commentaire supplémentaire de l'intervieweur",
        placeholder="Ex: Les entretiens se sont bien déroulés, l'entreprise est ouverte à l'IA...",
        height=100,
        key="interviewer_note"
    )
    
    # Résumé des fichiers sélectionnés
    st.subheader("📋 Résumé")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Transcriptions", len(st.session_state.uploaded_transcripts))
        st.metric("Ateliers", len(st.session_state.uploaded_workshops))
    with col2:
        st.metric("Entreprise", st.session_state.company_name)
        st.metric("Fichier Word", "✅ Uploadé" if word_file else "❌ Manquant")
    
    # Bouton de démarrage
    st.markdown("---")
    if st.button("🚀 Démarrer la Génération Executive Summary", type="primary", width="stretch"):
        # Upload le fichier Word
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
            except Exception as e:
                st.error(f"❌ Erreur lors de l'upload du fichier Word: {str(e)}")
                return
        
        if not word_path:
            st.error("❌ Erreur lors de l'upload du fichier Word")
            return
        
        # Démarrer le workflow Executive Summary
        with st.spinner("🚀 Démarrage du workflow Executive Summary..."):
            try:
                # Créer un thread_id unique
                thread_id = str(uuid.uuid4())
                st.session_state.executive_thread_id = thread_id
                
                # Appel API pour démarrer le workflow
                response = requests.post(
                    f"{API_URL}/executive-summary/threads/{thread_id}/runs",
                    json={
                        "word_report_path": word_path,
                        "transcript_files": st.session_state.uploaded_transcripts,
                        "workshop_files": st.session_state.uploaded_workshops,
                        "company_name": st.session_state.company_name,
                        "interviewer_note": interviewer_note or ""
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
    
    # Si le workflow est déjà terminé dans session_state, ne plus poller
    if st.session_state.get("executive_workflow_status") == "completed":
        display_executive_results()
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
    
    elif status == "waiting_validation_recommendations":
        st.warning("⏸️ **Validation des recommandations requise !**")
        display_recommendations_validation_interface()
        # Pas de rerun automatique ici, l'utilisateur doit valider
    
    elif status == "completed":
        # Ne plus faire de rerun automatique quand le workflow est terminé
        display_executive_results()
    
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
    extracted_needs = workflow_state.get("extracted_needs", [])
    iteration_count = workflow_state.get("challenges_iteration_count", 0)
    
    # Nettoyer les anciennes clés de checkbox de l'itération précédente
    if 'last_challenges_iteration' not in st.session_state or st.session_state.last_challenges_iteration != iteration_count:
        # Nouvelle itération - nettoyer UNIQUEMENT les anciennes clés
        if 'last_challenges_iteration' in st.session_state:
            old_iteration = st.session_state.last_challenges_iteration
            for key in list(st.session_state.keys()):
                if key.startswith("validate_challenge_") and key.endswith(f"_{old_iteration}"):
                    del st.session_state[key]
        st.session_state.last_challenges_iteration = iteration_count
    
    # Affichage du message de progression
    validated_count = len(validated_challenges)
    remaining_to_validate = max(0, 5 - validated_count)
    
    if iteration_count == 0:
        st.info(f"**Première proposition** : {len(identified_challenges)} enjeux identifiés - Veuillez en valider au moins 5")
    else:
        st.info(f"**Itération {iteration_count}** : Vous avez déjà validé **{validated_count}/5** enjeux. "
                f"Il vous reste **{remaining_to_validate} enjeux à valider** parmi les **{len(identified_challenges)} nouveaux enjeux** proposés.")
    
    st.markdown("---")
    
    # Utiliser la classe pour afficher l'interface de validation
    result = validation_interface.display_challenges_for_validation(
        identified_challenges=identified_challenges,
        validated_challenges=validated_challenges,
        key_suffix=str(iteration_count)
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
                    time.sleep(1)
                    st.rerun()
                else:
                    status_placeholder.error(f"❌ Erreur : {error_msg}")
            
            except queue.Empty:
                status_placeholder.error("❌ Timeout lors de la validation")

def display_recommendations_validation_interface():
    """Affiche l'interface de validation des recommandations"""
    from executive_summary.streamlit_validation_executive import StreamlitExecutiveValidation
    
    validation_interface = StreamlitExecutiveValidation()
    
    # Récupérer les données depuis session_state (pas d'appel API direct)
    workflow_state = st.session_state.executive_workflow_state
    recommendations = workflow_state.get("recommendations", [])
    validated_recommendations = workflow_state.get("validated_recommendations", [])
    iteration_count = workflow_state.get("recommendations_iteration_count", 0)
    
    # Nettoyer les anciennes clés de checkbox, texte et commentaires de l'itération précédente
    if 'last_recommendations_iteration' not in st.session_state or st.session_state.last_recommendations_iteration != iteration_count:
        # Nouvelle itération - nettoyer UNIQUEMENT les anciennes clés (avec l'ancien iteration_count)
        if 'last_recommendations_iteration' in st.session_state:
            old_iteration = st.session_state.last_recommendations_iteration
            for key in list(st.session_state.keys()):
                if (key.startswith("validate_recommendation_") or 
                    key.startswith("recommendation_text_") or 
                    key.startswith("recommendations_comments_")) and key.endswith(f"_{old_iteration}"):
                    del st.session_state[key]
        st.session_state.last_recommendations_iteration = iteration_count
    
    # Affichage du message de progression
    remaining_to_validate = max(0, 4 - len(validated_recommendations))
    
    if iteration_count == 0:
        st.info(f"💡 Validez au moins 4 recommandations parmi les {len(recommendations)} proposées.")
    else:
        st.warning(f"🔄 Itération {iteration_count + 1} : {remaining_to_validate} recommandation(s) supplémentaire(s) à valider.")
    
    result = validation_interface.display_recommendations_for_validation(
        recommendations=recommendations,
        validated_recommendations=validated_recommendations,
        key_suffix=str(iteration_count)
    )
    
    # Si un résultat est retourné, envoyer à l'API avec messages rotatifs
    if result is not None:
        thread_id = st.session_state.get("executive_thread_id")
        if not thread_id:
            st.error("❌ Aucun thread ID disponible")
            return
        
        # Vérifier si on a atteint le minimum requis
        total_validated = result.get("total_validated", 0)
        if total_validated < 4:
            # Pas encore assez de recommandations validées - régénération nécessaire
            validation_messages = [
                "📤 Envoi de votre validation...",
                "🔄 Régénération des recommandations...",
                "🤖 L'IA analyse votre feedback...",
                "💡 Génération de nouvelles recommandations..."
            ]
        else:
            # Assez de recommandations validées - finalisation
            validation_messages = [
                "📤 Envoi de votre validation finale...",
                "🤖 L'IA finalise l'analyse...",
                "📊 Génération du rapport final...",
                "⚙️ Derniers ajustements..."
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
                    if total_validated >= 4:
                        status_placeholder.success("✅ Validation envoyée ! Le workflow est terminé !")
                        st.session_state.executive_workflow_status = "completed"
                    else:
                        status_placeholder.success("✅ Validation envoyée ! Le workflow reprend...")
                        st.session_state.executive_workflow_status = "running"
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

def display_executive_results():
    """Affiche les résultats finaux de l'Executive Summary avec un résumé clair"""
    # Forcer une dernière récupération de l'état depuis l'API pour être sûr d'avoir les dernières données
    thread_id = st.session_state.get("executive_thread_id")
    if thread_id:
        try:
            # Récupérer l'état complet depuis l'API
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
        except Exception as e:
            st.warning(f"⚠️ Impossible de récupérer l'état final depuis l'API: {str(e)}")
            # Continuer avec l'état en cache
    
    # Récupérer les données depuis session_state
    workflow_state = st.session_state.executive_workflow_state
    
    validated_challenges = workflow_state.get("validated_challenges", [])
    maturity_score = workflow_state.get("maturity_score", 3)
    maturity_summary = workflow_state.get("maturity_summary", "")
    validated_recommendations = workflow_state.get("validated_recommendations", [])
    
    # Debug: afficher ce qui a été récupéré
    if st.session_state.get("debug_mode", False):
        with st.expander("🔍 Debug - État récupéré", expanded=False):
            st.json({
                "validated_challenges_count": len(validated_challenges),
                "validated_recommendations_count": len(validated_recommendations),
                "validated_recommendations": validated_recommendations,
                "maturity_score": maturity_score
            })
    
    # Afficher un message de succès en haut
    st.success("✅ **Workflow terminé avec succès !**")
    st.markdown("---")
    
    # Titre principal
    st.title("📊 Résumé Executive Summary")
    st.markdown("")
    
    # Section Enjeux identifiés
    st.header("🎯 Enjeux identifiés")
    if validated_challenges:
        for i, ch in enumerate(validated_challenges, 1):
            # Afficher l'ID et le titre si disponibles, sinon juste le numéro
            challenge_id = ch.get('id', '')
            challenge_titre = ch.get('titre', '')
            challenge_desc = ch.get('description', '')
            
            if challenge_id and challenge_titre:
                st.markdown(f"**{i}. {challenge_id} - {challenge_titre}**")
            elif challenge_titre:
                st.markdown(f"**{i}. {challenge_titre}**")
            else:
                st.markdown(f"**{i}. Enjeu {i}**")
            
            if challenge_desc:
                st.markdown(challenge_desc)
            
            if i < len(validated_challenges):
                st.markdown("")
    else:
        st.warning("⚠️ Aucun enjeu validé")
    
    st.markdown("---")
    
    # Section Recommandations clés
    st.header("💡 Recommandations clés")
    if validated_recommendations:
        # S'assurer que les recommandations sont bien des chaînes de caractères
        for i, rec in enumerate(validated_recommendations, 1):
            # Si c'est un dictionnaire, extraire le texte
            if isinstance(rec, dict):
                rec_text = rec.get("text", rec.get("recommendation", str(rec)))
            else:
                rec_text = str(rec)
            
            st.markdown(f"**{i}. {rec_text}**")
            if i < len(validated_recommendations):
                st.markdown("")
    else:
        st.warning("⚠️ Aucune recommandation validée")
        # Debug: afficher l'état complet pour comprendre le problème
        with st.expander("🔍 Debug - Pourquoi aucune recommandation ?", expanded=False):
            st.json({
                "workflow_state_keys": list(workflow_state.keys()),
                "validated_recommendations_type": type(validated_recommendations).__name__,
                "validated_recommendations_value": validated_recommendations,
                "recommendations_count": len(workflow_state.get("recommendations", [])),
                "full_workflow_state": workflow_state
            })
    
    st.markdown("---")
    
    # Section Maturité IA (optionnelle, en plus petit)
    with st.expander("📊 Évaluation de la maturité IA", expanded=False):
        if maturity_score is not None and maturity_summary:
            st.metric("Score de maturité", f"{maturity_score}/5")
            st.info("💡 " + maturity_summary)
        elif maturity_score is not None:
            st.metric("Score de maturité", f"{maturity_score}/5")
            st.warning("⚠️ Phrase descriptive de maturité non disponible")
        else:
            st.warning("⚠️ Évaluation de maturité non disponible")
    
    st.markdown("---")
    
    # Bouton de téléchargement
    results_json = {
        "validated_challenges": validated_challenges,
        "maturity_score": maturity_score,
        "maturity_summary": maturity_summary,
        "validated_recommendations": validated_recommendations
    }
    st.download_button(
        label="📥 Télécharger les résultats (JSON)",
        data=json.dumps(results_json, indent=2, ensure_ascii=False),
        file_name="executive_summary_results.json",
        mime="application/json",
        width="stretch"
    )

def display_rappel_mission():
    """Affiche le rappel de la mission"""
    st.header("Rappel de la mission")
    saved_company_name = (st.session_state.get("company_name") or "").strip()
    if not saved_company_name:
        saved_company_name = (st.session_state.get("company_name_input") or "").strip()

    if saved_company_name:
        st.info(f"Entreprise sélectionnée : {saved_company_name}")
    else:
        st.session_state.setdefault("rappel_mission_company_input", "")
        st.text_input(
            "Nom de l'entreprise",
            key="rappel_mission_company_input",
            placeholder="Ex : Cousin Surgery"
        )

    if st.button("📥 Générer le rappel de la mission", type="primary"):
        company_to_use = saved_company_name or st.session_state.get("rappel_mission_company_input", "").strip()

        if not company_to_use:
            st.warning("Veuillez indiquer le nom de l'entreprise pour générer le rappel.")
        else:
            thread_id = str(uuid.uuid4())
            try:
                with st.spinner("Recherche des informations de l'entreprise..."):
                    response = requests.post(
                        f"{API_URL}/rappel-mission/threads/{thread_id}/runs",
                        json={"company_name": company_to_use},
                        timeout=120
                    )
                    response.raise_for_status()
                    data = response.json()
                    result = data.get("result", {})
                    mission_markdown = result.get("mission_markdown", "")

                if mission_markdown:
                    st.session_state.rappel_mission = mission_markdown
                    st.session_state.rappel_mission_company = company_to_use
                    st.success("Rappel de la mission mis à jour.")
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
        st.info("Générez le rappel de la mission pour afficher les informations de l'entreprise.")

if __name__ == "__main__":
    main()

