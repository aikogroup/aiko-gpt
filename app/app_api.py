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

# Configuration de l'API
API_URL = "http://localhost:2025"

# Configuration de la page
st.set_page_config(
    page_title="AIKO - Analyse des Besoins IA",
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

def start_workflow_api_call(workshop_files: List[str], transcript_files: List[str], company_name: str, result_queue: queue.Queue):
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
                "company_name": company_name if company_name else None
            },
            timeout=300  # 5 minutes pour le traitement initial
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
            timeout=30  # 30 secondes pour récupérer l'état
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
            timeout=120  # 2 minutes pour la validation et la reprise du workflow
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
            timeout=120  # 2 minutes pour la validation finale
        )
        response.raise_for_status()
        
        result = response.json()
        result_queue.put((True, result.get("success"), None))
    
    except Exception as e:
        result_queue.put((False, None, str(e)))

# ==================== INTERFACE STREAMLIT ====================

def main():
    st.title("🤖 AIKO - Analyse des Besoins IA")
    st.markdown("### Architecture Propre : Streamlit = Interface, API LangGraph = Logique")
    
    init_session_state()
    
    # Vérifier que l'API est accessible
    try:
        response = requests.get(f"{API_URL}/", timeout=30)  # Augmenté à 30 secondes
        if response.status_code != 200:
            st.error(f"❌ L'API n'est pas accessible à {API_URL}")
            st.info("💡 Lancez l'API avec : `uv run python api/start_api.py`")
            return
    except Exception as e:
        st.error(f"❌ Impossible de se connecter à l'API : {str(e)}")
        st.info("💡 Lancez l'API avec : `uv run python api/start_api.py`")
        return
    
    st.success(f"✅ API connectée : {API_URL}")
    
    # Si le workflow n'est pas démarré, afficher l'interface d'upload
    if not st.session_state.thread_id or st.session_state.workflow_status is None:
        display_upload_interface()
    else:
        # Workflow en cours, afficher le statut
        display_workflow_progress()

def display_upload_interface():
    """Affiche l'interface d'upload et de configuration"""
    
    st.markdown("---")
    
    # Zone 1 : Upload fichiers Excel
    st.header("📝 Zone 1 : Ateliers (Fichiers Excel)")
    excel_files = st.file_uploader(
        "Uploadez vos fichiers d'ateliers",
        type=["xlsx"],
        accept_multiple_files=True,
        key="excel_uploader"
    )
    
    # Zone 2 : Upload fichiers de transcription (PDF ou JSON)
    st.header("📄 Zone 2 : Transcriptions (Fichiers PDF ou JSON)")
    pdf_files = st.file_uploader(
        "Uploadez vos transcriptions",
        type=["pdf", "json"],
        accept_multiple_files=True,
        key="pdf_uploader"
    )
    
    # Zone 3 : Nom de l'entreprise
    st.header("🏢 Zone 3 : Informations Entreprise")
    company_name = st.text_input(
        "Nom de l'entreprise",
        placeholder="Ex: Cousin Surgery"
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
            
            # Lancer l'appel API dans un thread
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    start_workflow_api_call,
                    file_types.get("workshop", []),
                    file_types.get("transcript", []),
                    company_name,
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
    """Affiche l'interface de validation des besoins"""
    
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
    
    # Message clair sur la progression
    remaining_to_validate = max(0, 5 - validated_count)
    
    if iteration_count == 0:
        st.info(f"**Première proposition** : {len(identified_needs)} besoins identifiés - Veuillez en valider au moins 5")
    else:
        st.info(f"**Itération {iteration_count}** : Vous avez déjà validé **{validated_count}/5** besoins. "
                f"Il vous reste **{remaining_to_validate} besoins à valider** parmi les **{len(identified_needs)} nouveaux besoins** proposés.")
    
    st.markdown("---")
    
    # CSS pour améliorer la séparation visuelle
    st.markdown("""
        <style>
        .need-container {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 5px;
            background-color: #fafafa;
            min-height: 200px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Afficher chaque besoin avec un checkbox (SANS expander, 2 colonnes)
    validated_needs = []
    rejected_needs = []
    
    # Créer 2 colonnes pour l'affichage
    for i in range(0, len(identified_needs), 2):
        col1, col2 = st.columns(2)
        
        # Besoin de gauche
        with col1:
            if i < len(identified_needs):
                need = identified_needs[i]
                st.markdown('<div class="need-container">', unsafe_allow_html=True)
                st.markdown(f"#### {need.get('theme', 'N/A')}")
                
                quotes = need.get('quotes', [])
                if quotes:
                    st.markdown("**Citations clés :**")
                    for quote in quotes[:3]:  # Limiter à 3 citations pour la lisibilité
                        st.markdown(f"• _{quote}_")
                else:
                    st.markdown("_Aucune citation disponible_")
                
                validated = st.checkbox(
                    "Valider ce besoin",
                    key=f"validate_need_{i}_{iteration_count}",  # Clé unique par itération
                    value=False
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                if validated:
                    validated_needs.append(need)
                else:
                    rejected_needs.append(need)
        
        # Besoin de droite
        with col2:
            if i + 1 < len(identified_needs):
                need = identified_needs[i + 1]
                st.markdown('<div class="need-container">', unsafe_allow_html=True)
                st.markdown(f"#### {need.get('theme', 'N/A')}")
                
                quotes = need.get('quotes', [])
                if quotes:
                    st.markdown("**Citations clés :**")
                    for quote in quotes[:3]:  # Limiter à 3 citations
                        st.markdown(f"• _{quote}_")
                else:
                    st.markdown("_Aucune citation disponible_")
                
                validated = st.checkbox(
                    "Valider ce besoin",
                    key=f"validate_need_{i+1}_{iteration_count}",  # Clé unique par itération
                    value=False
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                if validated:
                    validated_needs.append(need)
                else:
                    rejected_needs.append(need)
    
    # Zone de feedback
    user_feedback = st.text_area(
        "Commentaires (optionnel)",
        placeholder="Ajoutez vos commentaires ici...",
        key="user_feedback_needs"
    )
    
    # Bouton de validation
    st.markdown("---")
    if st.button("✅ Valider la Sélection", type="primary", use_container_width=True):
        # Messages d'attente pour la validation
        validation_messages = [
            "📤 Envoi de votre validation...",
            "🤖 L'IA analyse vos retours...",
            "🔄 Génération de nouveaux besoins...",
            "⚙️ Traitement en cours..."
        ]
        
        status_placeholder = st.empty()
        result_queue = queue.Queue()
        
        # Lancer l'appel API dans un thread
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                send_validation_feedback_api_call,
                validated_needs,
                rejected_needs,
                user_feedback,
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
    """Affiche l'interface de validation des use cases"""
    
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
    
    # CSS pour améliorer la séparation visuelle
    st.markdown("""
        <style>
        .usecase-container {
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 5px;
            background-color: #fafafa;
            min-height: 250px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Quick Wins - 2 colonnes côte à côte
    st.subheader("Quick Wins - Automatisation & assistance intelligente")
    st.caption("Solutions à faible complexité technique, mise en œuvre rapide (< 3 mois), ROI immédiat")
    validated_qw = []
    rejected_qw = []
    
    for i in range(0, len(proposed_qw), 2):
        col1, col2 = st.columns(2)
        
        # Quick Win de gauche
        with col1:
            if i < len(proposed_qw):
                uc = proposed_qw[i]
                st.markdown('<div class="usecase-container">', unsafe_allow_html=True)
                st.markdown(f"#### {uc.get('titre', 'N/A')}")
                st.markdown(f"**IA utilisée :** {uc.get('ia_utilisee', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                
                validated = st.checkbox(
                    "Valider ce Quick Win",
                    key=f"validate_qw_{i}_{use_case_iteration}",
                    value=False
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                if validated:
                    validated_qw.append(uc)
                else:
                    rejected_qw.append(uc)
        
        # Quick Win de droite
        with col2:
            if i + 1 < len(proposed_qw):
                uc = proposed_qw[i + 1]
                st.markdown('<div class="usecase-container">', unsafe_allow_html=True)
                st.markdown(f"#### {uc.get('titre', 'N/A')}")
                st.markdown(f"**IA utilisée :** {uc.get('ia_utilisee', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                
                validated = st.checkbox(
                    "Valider ce Quick Win",
                    key=f"validate_qw_{i+1}_{use_case_iteration}",
                    value=False
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                if validated:
                    validated_qw.append(uc)
                else:
                    rejected_qw.append(uc)
    
    # Structuration IA - 2 colonnes côte à côte
    st.subheader("Structuration IA à moyen et long terme - Scalabilité & qualité prédictive")
    st.caption("Solutions à complexité moyenne/élevée, mise en œuvre progressive (3-12 mois), ROI moyen/long terme")
    validated_sia = []
    rejected_sia = []
    
    for i in range(0, len(proposed_sia), 2):
        col1, col2 = st.columns(2)
        
        # Structuration IA de gauche
        with col1:
            if i < len(proposed_sia):
                uc = proposed_sia[i]
                st.markdown('<div class="usecase-container">', unsafe_allow_html=True)
                st.markdown(f"#### {uc.get('titre', 'N/A')}")
                st.markdown(f"**IA utilisée :** {uc.get('ia_utilisee', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                
                validated = st.checkbox(
                    "Valider ce cas d'usage",
                    key=f"validate_sia_{i}_{use_case_iteration}",
                    value=False
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                if validated:
                    validated_sia.append(uc)
                else:
                    rejected_sia.append(uc)
        
        # Structuration IA de droite
        with col2:
            if i + 1 < len(proposed_sia):
                uc = proposed_sia[i + 1]
                st.markdown('<div class="usecase-container">', unsafe_allow_html=True)
                st.markdown(f"#### {uc.get('titre', 'N/A')}")
                st.markdown(f"**IA utilisée :** {uc.get('ia_utilisee', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                
                validated = st.checkbox(
                    "Valider ce cas d'usage",
                    key=f"validate_sia_{i+1}_{use_case_iteration}",
                    value=False
                )
                st.markdown('</div>', unsafe_allow_html=True)
                
                if validated:
                    validated_sia.append(uc)
                else:
                    rejected_sia.append(uc)
    
    # Zone de feedback
    user_feedback = st.text_area(
        "Commentaires (optionnel)",
        placeholder="Ajoutez vos commentaires ici...",
        key="user_feedback_use_cases"
    )
    
    # Bouton de validation
    st.markdown("---")
    if st.button("✅ Valider et Terminer", type="primary", use_container_width=True):
        # Messages d'attente pour la validation finale
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
                validated_qw,
                validated_sia,
                rejected_qw,
                rejected_sia,
                user_feedback,
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
                st.markdown(f"**IA utilisée :** {uc.get('ia_utilisee', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                st.markdown("---")
    
    # Afficher les Structuration IA
    if final_sia:
        with st.expander("🏗️ Voir les Structuration IA validés", expanded=True):
            for i, uc in enumerate(final_sia, 1):
                st.markdown(f"### {i}. {uc.get('titre', 'N/A')}")
                st.markdown(f"**IA utilisée :** {uc.get('ia_utilisee', 'N/A')}")
                st.markdown(f"**Description :** {uc.get('description', 'N/A')}")
                st.markdown("---")
    
    # Bouton de téléchargement JSON
    if final_needs or final_qw or final_sia:
        import json
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
    
    # Bouton pour recommencer
    if st.button("🔄 Nouvelle Analyse", use_container_width=True):
        st.session_state.thread_id = None
        st.session_state.workflow_status = None
        st.session_state.uploaded_files = {}
        st.session_state.workflow_state = {}
        st.rerun()

if __name__ == "__main__":
    main()

