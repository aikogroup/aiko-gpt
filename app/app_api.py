"""
Application Streamlit PURE INTERFACE - communique avec l'API LangGraph
Architecture propre : Streamlit = UI, API LangGraph = Logique métier
"""

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
from utils.report_generator import ReportGenerator
from human_in_the_loop.streamlit_validation_interface import StreamlitValidationInterface
from use_case_analysis.streamlit_use_case_validation import StreamlitUseCaseValidation

# Configuration de l'API
API_URL = "http://localhost:2025"

# Initialisation des interfaces de validation
validation_interface = StreamlitValidationInterface()
use_case_validation = StreamlitUseCaseValidation()

# Configuration de la page
st.set_page_config(
    page_title="aiko - Analyse des Besoins IA",
    page_icon="🤖",
    layout="wide"
)

def init_session_state():
    """Initialise l'état de session"""
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = None
    if 'workflow_status' not in st.session_state:
        st.session_state.workflow_status = None
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}
    if 'workflow_state' not in st.session_state:
        st.session_state.workflow_state = {}

def upload_files_to_api(files: List[Any]) -> Dict[str, List[str]]:
    """
    Upload les fichiers vers l'API.
    
    Returns:
        {"workshop": [paths], "transcript": [paths]}
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
        return result["file_types"]
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'upload: {str(e)}")
        return {"workshop": [], "transcript": []}

def start_workflow_api_call(workshop_files: List[str], transcript_files: List[str], company_name: str, interviewer_names: List[str], additional_context: str, result_queue: queue.Queue):
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

def main():
    st.title("🤖 aiko - Analyse des Besoins IA")
    
    init_session_state()
    
    # Vérifier que l'API est accessible
    try:
        response = requests.get(f"{API_URL}/", timeout=60)  # Augmenté à 60 secondes
        if response.status_code != 200:
            st.error(f"❌ L'API n'est pas accessible à {API_URL}")
            st.info("💡 Lancez l'API avec : `uv run python api/start_api.py`")
            return
    except Exception as e:
        st.error(f"❌ Impossible de se connecter à l'API : {str(e)}")
        st.info("💡 Lancez l'API avec : `uv run python api/start_api.py`")
        return
    
    # Si le workflow n'est pas démarré, afficher l'interface d'upload
    if not st.session_state.thread_id or st.session_state.workflow_status is None:
        # Afficher le statut de l'API uniquement sur la première page
        st.success("✅ API connectée")
        display_upload_interface()
    else:
        # Workflow en cours, afficher le statut
        display_workflow_progress()

def display_upload_interface():
    """Affiche l'interface d'upload et de configuration"""
    
    st.markdown("---")
    
    # Upload des fichiers en deux colonnes côte à côte
    col1, col2 = st.columns(2)
    
    with col1:
        # Zone 1 : Upload fichiers Excel
        st.header("📝 Ateliers (Fichiers Excel)")
        excel_files = st.file_uploader(
            "Uploadez vos fichiers d'ateliers",
            type=["xlsx"],
            accept_multiple_files=True,
            key="excel_uploader"
        )
    
    with col2:
        # Zone 2 : Upload fichiers de transcription (PDF ou JSON)
        st.header("📄 Transcriptions (Fichiers PDF ou JSON)")
        pdf_files = st.file_uploader(
            "Uploadez vos transcriptions",
            type=["pdf", "json"],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
    
    # Zone 3 : Configuration des interviewers
    st.header("👥 Configuration des Interviewers")
    st.info("💡 Par défaut : Christella Umuhoza et Adrien Fabry. Vous pouvez ajouter d'autres noms d'interviewers.")
    
    # Initialiser la liste des interviewers dans session_state si nécessaire
    if 'interviewer_names' not in st.session_state:
        st.session_state.interviewer_names = ["Christella Umuhoza", "Adrien Fabry"]
    
    # Interface pour gérer les interviewers
    col_interviewers_1, col_interviewers_2 = st.columns([3, 1])
    
    with col_interviewers_1:
        new_interviewer = st.text_input(
            "Ajouter un nom d'interviewer",
            placeholder="Ex: Jean Dupont",
            key="new_interviewer_input"
        )
    
    with col_interviewers_2:
        if st.button("➕ Ajouter", key="add_interviewer_btn"):
            if new_interviewer and new_interviewer.strip() and new_interviewer.strip() not in st.session_state.interviewer_names:
                st.session_state.interviewer_names.append(new_interviewer.strip())
                st.success(f"✅ {new_interviewer.strip()} ajouté")
                st.rerun()
            elif new_interviewer and new_interviewer.strip() in st.session_state.interviewer_names:
                st.warning("⚠️ Ce nom est déjà dans la liste")
    
    # Afficher la liste actuelle avec possibilité de suppression
    if st.session_state.interviewer_names:
        st.markdown("**Interviewers configurés :**")
        for idx, interviewer in enumerate(st.session_state.interviewer_names):
            col_display, col_delete = st.columns([4, 1])
            with col_display:
                st.text(f"• {interviewer}")
            with col_delete:
                if st.button("🗑️", key=f"delete_interviewer_{idx}"):
                    st.session_state.interviewer_names.remove(interviewer)
                    st.success(f"✅ {interviewer} retiré")
                    st.rerun()
    
    # Zone 4 : Nom de l'entreprise
    st.header("🏢 Informations Entreprise")
    company_name = st.text_input(
        "Nom de l'entreprise",
        placeholder="Ex: Cousin Surgery"
    )
    
    # Zone 5 : Informations supplémentaires
    st.header("💡 Informations Supplémentaires")
    st.info("💡 Vous pouvez ajouter ici des informations complémentaires qui ne sont pas présentes dans les transcriptions ou les ateliers, mais qui sont nécessaires pour la génération des besoins et des cas d'usage.")
    additional_context = st.text_area(
        "Informations supplémentaires",
        placeholder="Ex: L'entreprise souhaite prioriser les solutions IA pour la R&D. Il y a également un projet de fusion prévu pour 2025 qui impacte la stratégie.",
        height=150,
        key="additional_context_input"
    )
    
    # Bouton de démarrage
    st.markdown("---")
    
    if excel_files or pdf_files:
        if st.button("🚀 Démarrer l'Analyse des Besoins", type="primary", use_container_width=True):
            # Étape 1 : Upload des fichiers
            with st.spinner("📤 Upload des fichiers vers l'API..."):
                all_files = list(excel_files) + list(pdf_files)
                file_types = upload_files_to_api(all_files)
                st.session_state.uploaded_files = file_types
            
            # Étape 2 : Démarrage du workflow avec messages rotatifs
            messages = display_rotating_messages(company_name)
            status_placeholder = st.empty()
            
            # Créer une queue pour récupérer le résultat
            result_queue = queue.Queue()
            
            # Récupérer les interviewer_names depuis session_state
            interviewer_names = st.session_state.get("interviewer_names", ["Christella Umuhoza", "Adrien Fabry"])
            
            # Lancer l'appel API dans un thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    start_workflow_api_call,
                    file_types.get("workshop", []),
                    file_types.get("transcript", []),
                    company_name,
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
                        if company_name and company_name.strip():
                            st.session_state.company_name_input = company_name.strip()
                            print(f"💾 [APP] Nom d'entreprise sauvegardé dans session_state: {company_name.strip()}")
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
    
    elif status == "waiting_use_case_validation":
        st.warning("⏸️ **Validation des cas d'usage requise !**")
        display_use_cases_validation_interface()
    
    elif status == "completed":
        st.success("✅ **Workflow terminé avec succès !**")
        display_final_results()
    
    elif status == "error":
        st.error("❌ Une erreur s'est produite")
    
    else:
        st.warning(f"⚠️ Statut inconnu: {status}")

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
                    use_container_width=True
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
                use_container_width=True
            )
        
        with col2:
            # Bouton de génération de rapport Word
            if st.button("📄 Générer le rapport Word", type="primary", use_container_width=True):
                generate_word_report()
    
    st.markdown("---")
    
    # Bouton pour recommencer
    if st.button("🔄 Nouvelle Analyse", use_container_width=True):
        st.session_state.thread_id = None
        st.session_state.workflow_status = None
        st.session_state.uploaded_files = {}
        st.session_state.workflow_state = {}
        st.rerun()

if __name__ == "__main__":
    main()

