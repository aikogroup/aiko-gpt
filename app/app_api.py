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

def start_workflow(workshop_files: List[str], transcript_files: List[str], company_name: str):
    """
    Démarre le workflow via l'API.
    """
    try:
        # Générer un thread_id
        thread_id = str(uuid.uuid4())
        st.session_state.thread_id = thread_id
        
        # Lancer le workflow
        response = requests.post(
            f"{API_URL}/threads/{thread_id}/runs",
            json={
                "workshop_files": workshop_files,
                "transcript_files": transcript_files,
                "company_name": company_name if company_name else None
            },
            timeout=300  # 5 minutes pour le traitement initial (ateliers + transcripts + web search + need analysis)
        )
        response.raise_for_status()
        
        result = response.json()
        st.session_state.workflow_status = result["status"]
        
        st.success(f"✅ Workflow démarré ! Thread ID: {thread_id[:8]}...")
        
        return True
    
    except Exception as e:
        st.error(f"❌ Erreur lors du démarrage: {str(e)}")
        return False

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

def send_validation_feedback(validated_needs: List[Dict], rejected_needs: List[Dict], user_feedback: str):
    """
    Envoie le feedback de validation à l'API et reprend le workflow.
    """
    try:
        response = requests.post(
            f"{API_URL}/threads/{st.session_state.thread_id}/validation",
            json={
                "validated_needs": validated_needs,
                "rejected_needs": rejected_needs,
                "user_feedback": user_feedback
            },
            timeout=120  # 2 minutes pour la validation et la reprise du workflow
        )
        response.raise_for_status()
        
        st.success("✅ Validation envoyée ! Le workflow reprend...")
        time.sleep(2)  # Pause pour laisser le workflow reprendre
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'envoi: {str(e)}")

def send_use_case_validation_feedback(validated_qw: List[Dict], validated_sia: List[Dict],
                                       rejected_qw: List[Dict], rejected_sia: List[Dict], user_feedback: str):
    """
    Envoie le feedback de validation des use cases à l'API.
    """
    try:
        response = requests.post(
            f"{API_URL}/threads/{st.session_state.thread_id}/use-case-validation",
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
        
        # Mettre à jour le statut en fonction de la réponse
        if result.get("success"):
            st.success("✅ Validation envoyée ! Le workflow est terminé !")
            st.session_state.workflow_status = "completed"
        else:
            st.warning("⏸️ Validation envoyée ! Nouvelle validation requise...")
            st.session_state.workflow_status = "paused"
        
        time.sleep(2)  # Pause pour laisser le workflow se terminer
        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Erreur lors de l'envoi: {str(e)}")

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
            with st.spinner("📤 Upload des fichiers vers l'API..."):
                all_files = list(excel_files) + list(pdf_files)
                file_types = upload_files_to_api(all_files)
                
                st.session_state.uploaded_files = file_types
            
            with st.spinner("🚀 Démarrage du workflow..."):
                success = start_workflow(
                    file_types.get("workshop", []),
                    file_types.get("transcript", []),
                    company_name
                )
                
                if success:
                    st.rerun()
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
    
    # Afficher un spinner si on est en train de valider
    if st.session_state.get('is_validating_needs', False):
        with st.spinner("Traitement de votre validation en cours..."):
            import time
            time.sleep(1)  # Délai pour que le spinner soit visible
        # Réinitialiser le flag
        st.session_state.is_validating_needs = False
    
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
            margin-bottom: 20px;
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
        
        st.markdown('<div style="margin-bottom: 15px;"></div>', unsafe_allow_html=True)
    
    # Zone de feedback
    user_feedback = st.text_area(
        "Commentaires (optionnel)",
        placeholder="Ajoutez vos commentaires ici...",
        key="user_feedback_needs"
    )
    
    # Bouton de validation
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Valider la Sélection", type="primary", use_container_width=True):
            # Activer le flag de validation pour afficher le spinner au prochain rerun
            st.session_state.is_validating_needs = True
            send_validation_feedback(validated_needs, rejected_needs, user_feedback)
            st.rerun()
    
    with col2:
        if st.button("Rafraîchir", use_container_width=True):
            st.rerun()

def display_use_cases_validation_interface():
    """Affiche l'interface de validation des use cases"""
    
    # Afficher un spinner si on est en train de valider
    if st.session_state.get('is_validating_uc', False):
        with st.spinner("Traitement de votre validation en cours..."):
            import time
            time.sleep(1)  # Délai pour que le spinner soit visible
        # Réinitialiser le flag
        st.session_state.is_validating_uc = False
    
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
            margin-bottom: 20px;
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
        
        st.markdown('<div style="margin-bottom: 15px;"></div>', unsafe_allow_html=True)
    
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
        
        st.markdown('<div style="margin-bottom: 15px;"></div>', unsafe_allow_html=True)
    
    # Zone de feedback
    user_feedback = st.text_area(
        "Commentaires (optionnel)",
        placeholder="Ajoutez vos commentaires ici...",
        key="user_feedback_use_cases"
    )
    
    # Bouton de validation
    st.markdown("---")
    if st.button("Valider et Terminer", type="primary", use_container_width=True):
        # Activer le flag de validation pour afficher le spinner au prochain rerun
        st.session_state.is_validating_uc = True
        send_use_case_validation_feedback(validated_qw, validated_sia, rejected_qw, rejected_sia, user_feedback)
        st.rerun()

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

