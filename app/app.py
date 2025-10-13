"""
Application Streamlit pour le traitement d'ateliers IA et de transcriptions
"""

import streamlit as st
import pandas as pd
import json
import tempfile
import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

from process_atelier.workshop_agent import WorkshopAgent
from process_transcript.transcript_agent import TranscriptAgent
from web_search.web_search_agent import WebSearchAgent
from workflow.need_analysis_workflow import NeedAnalysisWorkflow

def init_session_state():
    """Initialise l'état de session Streamlit"""
    if 'workshop_results' not in st.session_state:
        st.session_state.workshop_results = None
    if 'transcript_results' not in st.session_state:
        st.session_state.transcript_results = None
    if 'web_search_results' not in st.session_state:
        st.session_state.web_search_results = None
    if 'need_analysis_results' not in st.session_state:
        st.session_state.need_analysis_results = None
    
    # Nouveaux états pour l'interface
    if 'excel_files_uploaded' not in st.session_state:
        st.session_state.excel_files_uploaded = False
    if 'pdf_files_uploaded' not in st.session_state:
        st.session_state.pdf_files_uploaded = False
    if 'company_name' not in st.session_state:
        st.session_state.company_name = ""
    if 'workflow_started' not in st.session_state:
        st.session_state.workflow_started = False
    
    # Mode développement
    if 'dev_mode' not in st.session_state:
        st.session_state.dev_mode = os.getenv('DEV_MODE') == 'true'

def load_mock_data():
    """Charge les données mockées pour le mode développement"""
    try:
        # Charger les résultats des ateliers
        with open('/home/addeche/aiko/aikoGPT/workshop_results.json', 'r', encoding='utf-8') as f:
            workshop_data = json.load(f)
        
        # Charger les résultats des transcriptions
        with open('/home/addeche/aiko/aikoGPT/transcript_results.json', 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        # Charger les résultats de recherche web
        with open('/home/addeche/aiko/aikoGPT/web_search_cousin_surgery.json', 'r', encoding='utf-8') as f:
            web_search_data = json.load(f)
        
        return {
            'workshop_results': workshop_data,
            'transcript_results': transcript_data,
            'web_search_results': web_search_data
        }
    except Exception as e:
        st.error(f"Erreur lors du chargement des données mockées: {str(e)}")
        return None

def display_dev_mode_interface():
    """Affiche l'interface en mode développement avec données simulées"""
    
    st.info("🔧 **Mode Développement Activé** - Utilisation des données mockées")
    st.markdown("---")
    
    # Zone 1: Fichiers Excel simulés
    with st.container():
        st.subheader("📊 Zone 1: Fichiers Excel des Ateliers")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success("✅ Fichier simulé: workshop_results.json")
            st.info("Données chargées depuis le fichier JSON")
        
        with col2:
            st.markdown("**Confirmation:**")
            st.success("✅ Fichiers Excel chargés")
    
    st.markdown("---")
    
    # Zone 2: Fichiers PDF simulés
    with st.container():
        st.subheader("📄 Zone 2: Fichiers PDF des Transcriptions")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success("✅ Fichiers simulés: transcript_results.json")
            st.info("Données chargées depuis le fichier JSON")
        
        with col2:
            st.markdown("**Confirmation:**")
            st.success("✅ Fichiers PDF chargés")
    
    st.markdown("---")
    
    # Zone 3: Nom de l'entreprise simulé
    with st.container():
        st.subheader("🏢 Zone 3: Informations sur l'Entreprise")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.success("✅ Entreprise: Cousin Surgery")
            st.info("Données chargées depuis web_search_cousin_surgery.json")
        
        with col2:
            st.markdown("**Confirmation:**")
            st.success("✅ Nom entreprise saisi")
    
    st.markdown("---")
    
    # Bouton de démarrage (toujours disponible en mode dev)
    st.subheader("🚀 Démarrage du Workflow")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success("✅ Fichiers Excel prêts")
    with col2:
        st.success("✅ Fichiers PDF prêts")
    with col3:
        st.success("✅ Nom entreprise saisi")
    
    # Bouton de démarrage
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Démarrer l'Analyse des Besoins", type="primary", use_container_width=True):
            start_workflow_dev_mode()

def start_workflow_dev_mode():
    """Démarre le workflow en mode développement avec données mockées"""
    
    st.session_state.workflow_started = True
    
    # Charger les données mockées
    mock_data = load_mock_data()
    if mock_data is None:
        st.error("❌ Impossible de charger les données mockées")
        return
    
    # Stocker les données dans session_state
    st.session_state.workshop_results = mock_data['workshop_results']
    st.session_state.transcript_results = mock_data['transcript_results']
    st.session_state.web_search_results = mock_data['web_search_results']
    
    try:
        # Lancement du workflow d'analyse (sans les agents)
        run_need_analysis_workflow()
        
    except Exception as e:
        st.error(f"❌ Erreur lors du traitement: {str(e)}")
        st.exception(e)
        st.session_state.workflow_started = False

def main():
    """Fonction principale de l'application Streamlit"""
    
    # Configuration de la page
    st.set_page_config(
        page_title="AIKO - Analyse des Besoins",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialisation de l'état de session
    init_session_state()
    
    # Titre principal
    st.title("🤖 AIKO - Analyse des Besoins")
    st.markdown("---")
    
    # Interface avec 3 zones distinctes
    display_upload_interface()

def display_upload_interface():
    """Affiche l'interface avec 3 zones distinctes"""
    
    # Vérifier si le workflow a déjà été lancé
    if st.session_state.workflow_started:
        display_workflow_results()
        return
    
    # Mode développement - simuler les uploads
    if st.session_state.dev_mode:
        display_dev_mode_interface()
        return
    
    # Zone 1: Upload des fichiers Excel
    with st.container():
        st.subheader("📊 Zone 1: Fichiers Excel des Ateliers")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            uploaded_excel = st.file_uploader(
                "Choisissez un fichier Excel",
                type=['xlsx', 'xls'],
                help="Format attendu: Colonnes 'Atelier', 'Use_Case', 'Objective'",
                key="excel_upload"
            )
            
            if uploaded_excel is not None:
                st.success(f"✅ Fichier sélectionné: {uploaded_excel.name}")
                st.info(f"Taille: {uploaded_excel.size} bytes")
                
                # Sauvegarder le fichier temporairement
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_excel.getvalue())
                    st.session_state.excel_file_path = tmp_file.name
            else:
                st.warning("⚠️ Veuillez sélectionner un fichier Excel")
        
        with col2:
            st.markdown("**Confirmation:**")
            excel_uploaded = st.checkbox(
                "J'ai uploadé tous les fichiers Excel",
                value=st.session_state.excel_files_uploaded,
                key="excel_checkbox"
            )
            st.session_state.excel_files_uploaded = excel_uploaded
    
    st.markdown("---")
    
    # Zone 2: Upload des fichiers PDF
    with st.container():
        st.subheader("📄 Zone 2: Fichiers PDF des Transcriptions")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            uploaded_pdfs = st.file_uploader(
                "Choisissez un ou plusieurs fichiers PDF",
                type=['pdf'],
                accept_multiple_files=True,
                help="Sélectionnez plusieurs fichiers PDF de transcriptions",
                key="pdf_upload"
            )
            
            if uploaded_pdfs:
                st.success(f"✅ {len(uploaded_pdfs)} fichier(s) sélectionné(s)")
                for file in uploaded_pdfs:
                    st.info(f"📄 {file.name} ({file.size} bytes)")
                
                # Sauvegarder les fichiers temporairement
                temp_files = []
                for uploaded_file in uploaded_pdfs:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_files.append(tmp_file.name)
                st.session_state.pdf_files_paths = temp_files
            else:
                st.warning("⚠️ Veuillez sélectionner un ou plusieurs fichiers PDF")
        
        with col2:
            st.markdown("**Confirmation:**")
            pdf_uploaded = st.checkbox(
                "J'ai uploadé tous les fichiers PDF",
                value=st.session_state.pdf_files_uploaded,
                key="pdf_checkbox"
            )
            st.session_state.pdf_files_uploaded = pdf_uploaded
    
    st.markdown("---")
    
    # Zone 3: Nom de l'entreprise
    with st.container():
        st.subheader("🏢 Zone 3: Informations sur l'Entreprise")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            company_name = st.text_input(
                "Nom de l'entreprise",
                value=st.session_state.company_name,
                placeholder="Ex: Cousin Surgery, Microsoft, Google...",
                help="Saisissez le nom de l'entreprise à analyser",
                key="company_input"
            )
            st.session_state.company_name = company_name
            
            if company_name:
                st.success(f"✅ Entreprise: {company_name}")
            else:
                st.warning("⚠️ Veuillez saisir le nom de l'entreprise")
        
        with col2:
            st.markdown("**Confirmation:**")
            st.info("✅ Nom saisi" if company_name else "❌ Nom requis")
    
    st.markdown("---")
    
    # Bouton de démarrage conditionnel
    display_start_button()

def display_start_button():
    """Affiche le bouton de démarrage si toutes les conditions sont remplies"""
    
    # Vérifier les conditions
    excel_ready = st.session_state.excel_files_uploaded and hasattr(st.session_state, 'excel_file_path')
    pdf_ready = st.session_state.pdf_files_uploaded and hasattr(st.session_state, 'pdf_files_paths')
    company_ready = st.session_state.company_name.strip() != ""
    
    all_ready = excel_ready and pdf_ready and company_ready
    
    # Affichage du statut
    st.subheader("🚀 Démarrage du Workflow")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if excel_ready:
            st.success("✅ Fichiers Excel prêts")
        else:
            st.warning("⚠️ Fichiers Excel requis")
    
    with col2:
        if pdf_ready:
            st.success("✅ Fichiers PDF prêts")
        else:
            st.warning("⚠️ Fichiers PDF requis")
    
    with col3:
        if company_ready:
            st.success("✅ Nom entreprise saisi")
        else:
            st.warning("⚠️ Nom entreprise requis")
    
    # Bouton de démarrage
    if all_ready:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Démarrer l'Analyse des Besoins", type="primary", use_container_width=True):
                start_workflow()
    else:
        st.info("👆 Veuillez compléter toutes les zones ci-dessus pour débloquer le bouton de démarrage")

def start_workflow():
    """Démarre le workflow d'analyse des besoins"""
    
    st.session_state.workflow_started = True
    
    # Afficher un spinner pendant le traitement
    with st.spinner("🔄 Analyse des besoins en cours..."):
        try:
            # Traitement des fichiers Excel
            if hasattr(st.session_state, 'excel_file_path'):
                agent = WorkshopAgent()
                workshop_results = agent.process_workshop_file(st.session_state.excel_file_path)
                st.session_state.workshop_results = workshop_results
                
                # Nettoyer le fichier temporaire
                os.unlink(st.session_state.excel_file_path)
            
            # Traitement des fichiers PDF
            if hasattr(st.session_state, 'pdf_files_paths'):
                agent = TranscriptAgent()
                transcript_results = agent.process_multiple_pdfs(st.session_state.pdf_files_paths)
                st.session_state.transcript_results = transcript_results
                
                # Nettoyer les fichiers temporaires
                for temp_file in st.session_state.pdf_files_paths:
                    os.unlink(temp_file)
            
            # Recherche web
            if st.session_state.company_name:
                agent = WebSearchAgent()
                web_search_results = agent.search_company_info(st.session_state.company_name)
                st.session_state.web_search_results = web_search_results
            
            # Lancement du workflow d'analyse
            run_need_analysis_workflow()
            
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement: {str(e)}")
            st.exception(e)
            st.session_state.workflow_started = False

def display_workflow_results():
    """Affiche les résultats du workflow ou l'interface de validation"""
    
    print(f"\n📊 [DEBUG] display_workflow_results - DÉBUT")
    print(f"🔍 [DEBUG] workflow_paused: {st.session_state.get('workflow_paused', False)}")
    print(f"🔍 [DEBUG] waiting_for_validation: {st.session_state.get('waiting_for_validation', False)}")
    print(f"🔍 [DEBUG] validation_result present: {'validation_result' in st.session_state}")
    
    # Vérifier si le workflow est en pause pour validation
    if st.session_state.get("workflow_paused", False) and st.session_state.get("waiting_for_validation", False):
        print(f"⏸️ [DEBUG] Workflow en pause - affichage de l'interface de validation")
        
        # Afficher l'interface de validation
        st.warning("⏸️ Workflow en pause - Validation des besoins requise")
        
        # Récupérer l'état du workflow
        workflow_state = st.session_state.get("workflow_state", {})
        identified_needs = workflow_state.get("identified_needs", [])
        validated_needs = workflow_state.get("validated_needs", [])
        
        print(f"📊 [DEBUG] identified_needs: {len(identified_needs)}")
        print(f"📊 [DEBUG] validated_needs: {len(validated_needs)}")
        
        # CORRECTION: Ne pas réafficher l'interface si la validation est déjà terminée
        if "validation_result" in st.session_state and st.session_state.validation_result:
            print(f"✅ [DEBUG] Validation terminée - bouton de reprise disponible")
            st.markdown("---")
            st.success("✅ Validation terminée !")
            
            # Bouton pour reprendre le workflow
            if st.button("▶️ Reprendre le workflow", type="primary", key="resume_workflow_btn"):
                print(f"▶️ [DEBUG] Bouton 'Reprendre le workflow' cliqué")
                resume_workflow_after_validation()
        else:
            # Afficher l'interface de validation seulement si pas encore validé
            print(f"📋 [DEBUG] Affichage de l'interface de validation")
            from human_in_the_loop.streamlit_validation_interface import StreamlitValidationInterface
            interface = StreamlitValidationInterface()
            interface.display_needs_for_validation(identified_needs, len(validated_needs))
        
        return
    
    # Workflow terminé - afficher les résultats
    print(f"✅ [DEBUG] Workflow terminé - affichage des résultats")
    st.success("✅ Workflow terminé !")
    st.markdown("---")
    
    # Affichage des résultats de l'analyse des besoins
    if st.session_state.need_analysis_results:
        display_need_analysis_results(st.session_state.need_analysis_results)
    
    # Bouton pour recommencer
    if st.button("🔄 Nouvelle Analyse", type="secondary"):
        # Reset de l'état
        st.session_state.workflow_started = False
        st.session_state.excel_files_uploaded = False
        st.session_state.pdf_files_uploaded = False
        st.session_state.company_name = ""
        st.session_state.workshop_results = None
        st.session_state.transcript_results = None
        st.session_state.web_search_results = None
        st.session_state.need_analysis_results = None
        st.session_state.workflow_paused = False
        st.session_state.waiting_for_validation = False
        if "validation_result" in st.session_state:
            del st.session_state.validation_result
        if "workflow_state" in st.session_state:
            del st.session_state.workflow_state
        st.rerun()

def process_workshop_phase():
    """Phase 1: Traitement des ateliers IA"""
    
    # Sidebar pour l'upload
    with st.sidebar:
        st.header("📁 Upload de fichier Excel")
        uploaded_file = st.file_uploader(
            "Choisissez un fichier Excel",
            type=['xlsx', 'xls'],
            help="Format attendu: Colonnes 'Atelier', 'Use_Case', 'Objective'",
            key="workshop_upload"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ Fichier sélectionné: {uploaded_file.name}")
            st.info(f"Taille: {uploaded_file.size} bytes")
        else:
            st.warning("⚠️ Veuillez sélectionner un fichier Excel")
    
    # Zone principale
    if uploaded_file is not None:
        # Bouton de traitement
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Traiter le fichier", type="primary", width='stretch', key="workshop_process"):
                process_workshop_file(uploaded_file)
    else:
        # Instructions d'utilisation
        st.info("👆 Veuillez sélectionner un fichier Excel dans la sidebar pour commencer")
        
        # Exemple de format attendu
        st.subheader("📋 Format de fichier attendu")
        st.markdown("""
        Votre fichier Excel doit contenir au moins 3 colonnes :
        - **Atelier** : Nom de l'atelier
        - **Use_Case** : Description du cas d'usage
        - **Objective** : Objectif du cas d'usage
        """)
        
        # Afficher un exemple
        example_data = {
            'Atelier': ['IA RH', 'IA RH', 'IA Supply Chain', 'IA Supply Chain'],
            'Use_Case': ['Optimisation recrutement', 'Formation personnalisée', 'Prévision demande', 'Optimisation stock'],
            'Objective': ['Réduire le temps de recrutement', 'Améliorer les compétences', 'Anticiper les besoins', 'Minimiser les coûts']
        }
        example_df = pd.DataFrame(example_data)
        st.dataframe(example_df, width='stretch')

def process_transcript_phase():
    """Phase 2: Traitement des transcriptions PDF"""
    
    # Sidebar pour l'upload multiple
    with st.sidebar:
        st.header("📁 Upload de fichiers PDF")
        uploaded_files = st.file_uploader(
            "Choisissez un ou plusieurs fichiers PDF",
            type=['pdf'],
            accept_multiple_files=True,
            help="Sélectionnez plusieurs fichiers PDF de transcriptions",
            key="transcript_upload"
        )
        
        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} fichier(s) sélectionné(s)")
            for file in uploaded_files:
                st.info(f"📄 {file.name} ({file.size} bytes)")
        else:
            st.warning("⚠️ Veuillez sélectionner un ou plusieurs fichiers PDF")
    
    # Zone principale
    if uploaded_files:
        # Bouton de traitement
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🚀 Traiter les PDFs", type="primary", width='stretch', key="transcript_process"):
                process_transcript_files(uploaded_files)
    else:
        # Instructions d'utilisation
        st.info("👆 Veuillez sélectionner un ou plusieurs fichiers PDF dans la sidebar pour commencer")
        
        # Description du traitement
        st.subheader("📋 Traitement des transcriptions PDF")
        st.markdown("""
        Le système va analyser vos fichiers PDF de transcriptions pour :
        - **Parser** le contenu et extraire les interventions
        - **Filtrer** les parties les plus intéressantes avec l'IA
        - **Analyser** sémantiquement pour identifier :
          - Besoins exprimés
          - Frustrations et blocages
          - Opportunités d'automatisation
          - Citations clés
        """)

def process_workshop_file(uploaded_file):
    """Traite le fichier uploadé avec WorkshopAgent"""
    
    # Afficher un spinner pendant le traitement
    with st.spinner("🔄 Traitement en cours..."):
        try:
            # Sauvegarder le fichier temporairement
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            # Initialiser l'agent
            agent = WorkshopAgent()
            
            # Traiter le fichier
            results = agent.process_workshop_file(tmp_file_path)
            
            # Nettoyer le fichier temporaire
            os.unlink(tmp_file_path)
            
            # Stocker les résultats dans session_state
            st.session_state.workshop_results = results
            
            # Afficher les résultats
            display_workshop_results(results)
            
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement: {str(e)}")
            st.exception(e)

def process_transcript_files(uploaded_files):
    """Traite les fichiers PDF uploadés avec TranscriptAgent"""
    
    # Afficher un spinner pendant le traitement
    with st.spinner("🔄 Traitement des PDFs en cours..."):
        try:
            # Sauvegarder les fichiers temporairement
            temp_files = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_files.append(tmp_file.name)
            
            # Initialiser l'agent
            agent = TranscriptAgent()
            
            # Traiter les fichiers
            results = agent.process_multiple_pdfs(temp_files)
            
            # Nettoyer les fichiers temporaires
            for temp_file in temp_files:
                os.unlink(temp_file)
            
            # Stocker les résultats dans session_state
            st.session_state.transcript_results = results
            
            # Afficher les résultats
            display_transcript_results(results)
            
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement: {str(e)}")
            st.exception(e)

def display_workshop_results(results):
    """Affiche les résultats du traitement des ateliers"""
    
    st.success(f"✅ Traitement terminé ! {len(results)} atelier(s) traité(s)")
    st.markdown("---")
    
    # Métriques globales
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nombre d'ateliers", len(results))
    with col2:
        total_use_cases = sum(len(w.use_cases) for w in results)
        st.metric("Total cas d'usage", total_use_cases)
    with col3:
        avg_use_cases = total_use_cases / len(results) if results else 0
        st.metric("Moyenne par atelier", f"{avg_use_cases:.1f}")
    
    st.markdown("---")
    
    # Affichage détaillé des résultats
    for i, workshop in enumerate(results, 1):
        with st.expander(f"🏢 {workshop.theme} (ID: {workshop.workshop_id})", expanded=True):
            
            # Informations de l'atelier
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**Thème:** {workshop.theme}")
            with col2:
                st.markdown(f"**Cas d'usage:** {len(workshop.use_cases)}")
            
            # Liste des cas d'usage
            if workshop.use_cases:
                st.markdown("**📋 Cas d'usage identifiés:**")
                for j, use_case in enumerate(workshop.use_cases, 1):
                    with st.container():
                        st.markdown(f"**{j}. {use_case.title}**")
                        st.markdown(f"   *Objectif:* {use_case.objective}")
                        if use_case.benefits:
                            st.markdown(f"   *Bénéfices:* {', '.join(use_case.benefits)}")
                        st.markdown("---")
            else:
                st.warning("Aucun cas d'usage identifié pour cet atelier")
    
    # Bouton de téléchargement des résultats
    st.markdown("---")
    st.subheader("💾 Télécharger les résultats")
    
    # Conversion en JSON pour le téléchargement
    results_dict = [result.model_dump() for result in results]
    json_str = json.dumps(results_dict, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📥 Télécharger en JSON",
        data=json_str,
        file_name="workshop_results.json",
        mime="application/json"
    )

def display_transcript_results(results):
    """Affiche les résultats du traitement des transcriptions"""
    
    st.success(f"✅ Traitement terminé ! {results['successful']} PDF(s) traité(s) avec succès")
    if results['failed'] > 0:
        st.warning(f"⚠️ {results['failed']} PDF(s) ont échoué")
    
    st.markdown("---")
    
    # Calcul des métriques globales
    total_chars = 0
    total_interesting_parts = 0
    total_needs = 0
    total_frustrations = 0
    total_opportunities = 0
    total_citations = 0
    
    successful_results = [r for r in results['results'] if r['status'] == 'success']
    
    for result in successful_results:
        # Compter les caractères
        if 'parsing' in result:
            total_chars += sum(len(intervention.get('text', '')) for intervention in result.get('parsing', {}).get('interventions', []))
        
        # Compter les parties intéressantes
        if 'interesting_parts' in result:
            total_interesting_parts += result['interesting_parts']['count']
        
        # Compter les éléments sémantiques
        if 'semantic_analysis' in result:
            analysis = result['semantic_analysis']
            total_needs += len(analysis.get('besoins_exprimes', []))
            total_frustrations += len(analysis.get('frustrations_blocages', []))
            total_opportunities += len(analysis.get('opportunites_automatisation', []))
            total_citations += len(analysis.get('citations_cles', []))
    
    # Métriques globales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("PDFs traités", results['successful'])
    with col2:
        st.metric("Caractères analysés", f"{total_chars:,}")
    with col3:
        st.metric("Parties sélectionnées", total_interesting_parts)
    with col4:
        st.metric("Besoins identifiés", total_needs)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Frustrations", total_frustrations)
    with col2:
        st.metric("Opportunités", total_opportunities)
    with col3:
        st.metric("Citations", total_citations)
    with col4:
        st.metric("Taux de sélection", f"{(total_interesting_parts/max(total_chars/1000, 1)):.1f}%")
    
    st.markdown("---")
    
    # Affichage détaillé par PDF
    for i, result in enumerate(successful_results, 1):
        pdf_name = Path(result['pdf_path']).name
        with st.expander(f"📄 {pdf_name}", expanded=False):
            
            # Métriques du PDF
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Interventions totales", result.get('parsing', {}).get('total_interventions', 0))
            with col2:
                st.metric("Parties intéressantes", result.get('interesting_parts', {}).get('count', 0))
            with col3:
                speakers = result.get('parsing', {}).get('speakers', [])
                st.metric("Intervenants", len(speakers))
            
            # Analyse sémantique
            if 'semantic_analysis' in result:
                analysis = result['semantic_analysis']
                
                if analysis.get('besoins_exprimes'):
                    st.markdown("**🎯 Besoins exprimés:**")
                    for besoin in analysis['besoins_exprimes']:
                        st.markdown(f"  - {besoin}")
                
                if analysis.get('frustrations_blocages'):
                    st.markdown("**😤 Frustrations/Blocages:**")
                    for frustration in analysis['frustrations_blocages']:
                        st.markdown(f"  - {frustration}")
                
                if analysis.get('opportunites_automatisation'):
                    st.markdown("**🤖 Opportunités d'automatisation:**")
                    for opp in analysis['opportunites_automatisation']:
                        st.markdown(f"  - {opp}")
                
                if analysis.get('citations_cles'):
                    st.markdown("**💬 Citations clés:**")
                    for citation in analysis['citations_cles']:
                        st.markdown(f"  - {citation}")
    
    # Bouton de téléchargement des résultats
    st.markdown("---")
    st.subheader("💾 Télécharger les résultats")
    
    # Conversion en JSON pour le téléchargement
    json_str = json.dumps(results, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📥 Télécharger en JSON",
        data=json_str,
        file_name="transcript_results.json",
        mime="application/json"
    )

def process_web_search_phase():
    """Phase 3: Recherche web d'informations sur les entreprises"""
    
    # Sidebar pour la saisie du nom d'entreprise
    with st.sidebar:
        st.header("🏢 Recherche d'entreprise")
        company_name = st.text_input(
            "Nom de l'entreprise",
            placeholder="Ex: Cousin Surgery, Microsoft, Google...",
            help="Saisissez le nom de l'entreprise à rechercher",
            key="company_name_input"
        )
        
        if company_name:
            st.success(f"✅ Entreprise sélectionnée: {company_name}")
        else:
            st.warning("⚠️ Veuillez saisir un nom d'entreprise")
    
    # Zone principale
    if company_name:
        # Bouton de recherche
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Rechercher des informations", type="primary", width='stretch', key="web_search_process"):
                process_web_search(company_name)
    else:
        # Instructions d'utilisation
        st.info("👆 Veuillez saisir un nom d'entreprise dans la sidebar pour commencer")
        
        # Description du traitement
        st.subheader("🔍 Recherche d'informations sur les entreprises")
        st.markdown("""
        Le système va rechercher des informations sur l'entreprise pour :
        - **Description** de l'entreprise et son secteur d'activité
        - **Taille** de l'entreprise (nombre d'employés)
        - **Chiffre d'affaires** et informations financières
        - **Actualités récentes** et développements
        - **Informations générales** sur l'activité
        """)
        
        # Exemple d'utilisation
        st.subheader("📋 Exemples d'entreprises")
        example_companies = [
            "Cousin Surgery",
            "Microsoft", 
            "Google",
            "Apple",
            "Tesla",
            "Amazon"
        ]
        
        cols = st.columns(3)
        for i, company in enumerate(example_companies):
            with cols[i % 3]:
                if st.button(f"🔍 {company}", key=f"example_{i}"):
                    st.session_state.company_name_input = company
                    st.rerun()

def process_web_search(company_name):
    """Traite la recherche web pour une entreprise"""
    
    # Afficher un spinner pendant la recherche
    with st.spinner(f"🔍 Recherche d'informations pour {company_name}..."):
        try:
            # Initialiser l'agent
            agent = WebSearchAgent()
            
            # Effectuer la recherche
            results = agent.search_company_info(company_name)
            
            # Stocker les résultats dans session_state
            st.session_state.web_search_results = results
            
            # Afficher les résultats
            display_web_search_results(results)
            
        except Exception as e:
            st.error(f"❌ Erreur lors de la recherche: {str(e)}")
            st.exception(e)

def display_web_search_results(results):
    """Affiche les résultats de la recherche web"""
    
    st.success(f"✅ Recherche terminée pour {results['company_name']}")
    st.markdown("---")
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Entreprise", results['company_name'])
    with col2:
        st.metric("Secteur", results.get('sector', 'Non identifié'))
    with col3:
        st.metric("Taille", results.get('size', 'Non disponible'))
    with col4:
        st.metric("CA", results.get('revenue', 'Non disponible'))
    
    st.markdown("---")
    
    # Description de l'entreprise
    st.subheader("📝 Description de l'entreprise")
    st.markdown(f"**{results['company_name']}**")
    st.write(results.get('description', 'Description non disponible'))
    
    # Informations détaillées
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏢 Informations générales")
        st.markdown(f"**Secteur d'activité:** {results.get('sector', 'Non identifié')}")
        st.markdown(f"**Taille de l'entreprise:** {results.get('size', 'Non disponible')}")
        st.markdown(f"**Chiffre d'affaires:** {results.get('revenue', 'Non disponible')}")
    
    with col2:
        st.subheader("📰 Actualités récentes")
        recent_news = results.get('recent_news', [])
        if recent_news and recent_news != ["Aucune actualité récente trouvée"]:
            for i, news in enumerate(recent_news[:3], 1):  # Afficher les 3 premières actualités
                st.markdown(f"**{i}.** {news}")
        else:
            st.info("Aucune actualité récente trouvée")
    
    # Bouton de téléchargement des résultats
    st.markdown("---")
    st.subheader("💾 Télécharger les résultats")
    
    # Conversion en JSON pour le téléchargement
    json_str = json.dumps(results, ensure_ascii=False, indent=2)
    
    st.download_button(
        label="📥 Télécharger en JSON",
        data=json_str,
        file_name=f"web_search_{results['company_name'].replace(' ', '_').lower()}.json",
        mime="application/json"
    )

def process_need_analysis_phase():
    """Phase 4: Analyse des besoins avec le workflow complet"""
    
    st.header("🧠 Phase 4: Analyse des Besoins")
    st.markdown("Cette phase utilise les résultats des 3 phases précédentes pour analyser les besoins métier.")
    
    # Vérification des prérequis
    workshop_available = st.session_state.workshop_results is not None
    transcript_available = st.session_state.transcript_results is not None
    web_search_available = st.session_state.web_search_results is not None
    
    # Affichage du statut des prérequis
    st.subheader("📋 Prérequis")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if workshop_available:
            st.success("✅ Phase 1: Ateliers IA terminée")
        else:
            st.warning("⚠️ Phase 1: Ateliers IA requise")
    
    with col2:
        if transcript_available:
            st.success("✅ Phase 2: Transcriptions PDF terminée")
        else:
            st.warning("⚠️ Phase 2: Transcriptions PDF requise")
    
    with col3:
        if web_search_available:
            st.success("✅ Phase 3: Recherche Web terminée")
        else:
            st.warning("⚠️ Phase 3: Recherche Web requise")
    
    # Vérification si tous les prérequis sont remplis
    all_prerequisites_met = workshop_available and transcript_available and web_search_available
    
    if not all_prerequisites_met:
        st.error("❌ Veuillez compléter les 3 phases précédentes avant de lancer l'analyse des besoins")
        st.info("👆 Utilisez les onglets ci-dessus pour traiter vos fichiers et effectuer la recherche web")
        return
    
    # Bouton de lancement du workflow
    st.markdown("---")
    st.subheader("🚀 Lancement de l'analyse des besoins")
    
    if st.button("🧠 Lancer l'analyse des besoins", type="primary", use_container_width=True):
        run_need_analysis_workflow()
    
    # Affichage des résultats si disponibles
    if st.session_state.need_analysis_results:
        display_need_analysis_results(st.session_state.need_analysis_results)

def resume_workflow_after_validation():
    """Reprend le workflow après validation humaine"""
    
    print(f"\n🔄 [DEBUG] resume_workflow_after_validation - DÉBUT")
    
    with st.spinner("🔄 Reprise du workflow..."):
        try:
            # Initialisation du workflow
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                st.error("❌ Clé API OpenAI non trouvée. Vérifiez votre fichier .env")
                return
            
            workflow = NeedAnalysisWorkflow(api_key=api_key, dev_mode=st.session_state.dev_mode)
            
            print(f"▶️ [DEBUG] Appel de resume_workflow()...")
            
            # Reprendre le workflow
            results = workflow.resume_workflow()
            
            print(f"📊 [DEBUG] Résultats de resume_workflow(): {results.get('success', False)}")
            
            # Vérifier si une nouvelle validation est nécessaire
            if results.get("error") == "Nouvelle validation requise":
                print(f"⏸️ [DEBUG] Nouvelle validation requise - workflow en pause")
                st.info("🔄 Nouvelle validation requise - le workflow est en pause")
                st.rerun()
            elif results.get("success"):
                print(f"✅ [DEBUG] Workflow terminé avec succès")
                # Workflow terminé avec succès
                st.session_state.need_analysis_results = results
                st.session_state.workflow_paused = False
                st.session_state.waiting_for_validation = False
                
                # Nettoyer les états temporaires
                if "validation_result" in st.session_state:
                    del st.session_state.validation_result
                
                st.success("✅ Analyse des besoins terminée !")
                st.rerun()
            else:
                print(f"❌ [DEBUG] Workflow terminé avec erreur: {results.get('error', 'Erreur inconnue')}")
                st.error(f"❌ Erreur: {results.get('error', 'Erreur inconnue')}")
                
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans resume_workflow_after_validation: {str(e)}")
            st.error(f"❌ Erreur lors de la reprise du workflow: {str(e)}")
            st.exception(e)
    
    print(f"✅ [DEBUG] resume_workflow_after_validation - FIN")

def run_need_analysis_workflow():
    """Lance le workflow d'analyse des besoins avec NOUVELLE ARCHITECTURE"""
    
    print(f"\n🚀 [DEBUG] run_need_analysis_workflow - NOUVELLE ARCHITECTURE")
    
    # Vérifier si on est déjà en attente de validation
    if st.session_state.get("workflow_paused", False):
        print(f"⏸️ [DEBUG] Workflow en pause - affichage interface de validation")
        return
    
    with st.spinner("🔄 Analyse des besoins en cours..."):
        try:
            # Préparation des données pour le workflow
            workshop_data = st.session_state.workshop_results
            transcript_data = st.session_state.transcript_results
            web_search_data = st.session_state.web_search_results
            
            # Initialisation du workflow
            import os
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                st.error("❌ Clé API OpenAI non trouvée. Vérifiez votre fichier .env")
                return
            
            workflow = NeedAnalysisWorkflow(api_key=api_key, dev_mode=st.session_state.dev_mode)
            
            print(f"🔄 [DEBUG] Exécution du workflow...")
            
            if st.session_state.dev_mode:
                # Mode développement - utiliser les données mockées directement
                # Conversion des données pour le workflow
                workshop_files = []  # Pas de fichiers en mode dev
                transcript_files = []  # Pas de fichiers en mode dev
                company_info = {"company_name": web_search_data.get("company_name", "")}
                
                # Exécution du workflow avec les données mockées
                results = workflow.run(
                    workshop_files=workshop_files,
                    transcript_files=transcript_files,
                    company_info=company_info
                )
                
                # Stockage des résultats
                st.session_state.need_analysis_results = results
                
            else:
                # Mode normal - utiliser les données traitées par les agents
                # Conversion des données pour le workflow
                workshop_files = []  # Les fichiers ne sont plus nécessaires, on a déjà les résultats
                transcript_files = []  # Idem
                company_info = {"company_name": web_search_data.get("company_name", "")}
                
                # Exécution du workflow avec les données déjà traitées
                results = workflow.run(
                    workshop_files=workshop_files,
                    transcript_files=transcript_files,
                    company_info=company_info
                )
                
                # Stockage des résultats
                st.session_state.need_analysis_results = results
            
            print(f"✅ [DEBUG] Workflow terminé - affichage des résultats")
            st.success("✅ Analyse des besoins terminée !")
            
            # Forcer l'affichage des résultats
            st.rerun()
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans run_need_analysis_workflow: {str(e)}")
            st.error(f"❌ Erreur lors de l'analyse des besoins: {str(e)}")
            st.exception(e)

def display_need_analysis_results(results):
    """Affiche les résultats de l'analyse des besoins"""
    
    st.header("📊 Résultats de l'analyse des besoins")
    st.markdown("---")
    
    # Métriques globales
    final_needs = results.get("final_needs", [])
    summary = results.get("summary", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Besoins identifiés", len(final_needs))
    with col2:
        st.metric("Thèmes", len(summary.get("themes", [])))
    with col3:
        st.metric("Priorité élevée", summary.get("high_priority_count", 0))
    with col4:
        st.metric("Total besoins", summary.get("total_needs", 0))
    
    st.markdown("---")
    
    # Affichage des besoins identifiés avec la nouvelle structure simplifiée
    if final_needs:
        st.subheader("🎯 Besoins identifiés")
        for i, need in enumerate(final_needs, 1):
            theme = need.get('theme', 'Thème non défini')
            quotes = need.get('quotes', [])
            
            with st.expander(f"🔹 {theme}", expanded=False):
                st.markdown(f"**Thème:** {theme}")
                if quotes:
                    st.markdown("**Citations:**")
                    for j, quote in enumerate(quotes, 1):
                        st.markdown(f"• {quote}")
                else:
                    st.info("Aucune citation disponible")
    else:
        st.warning("Aucun besoin identifié")
    
    # Résumé de l'analyse
    if summary:
        st.subheader("📈 Résumé de l'analyse")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Thèmes identifiés:**")
            for theme in summary.get("themes", []):
                st.write(f"- {theme}")
        
        with col2:
            st.write("**Statistiques:**")
            st.write(f"- Total besoins: {summary.get('total_needs', 0)}")
            st.write(f"- Priorité élevée: {summary.get('high_priority_count', 0)}")
    
    # Bouton de téléchargement
    st.markdown("---")
    st.subheader("💾 Télécharger les résultats")
    
    json_str = json.dumps(results, ensure_ascii=False, indent=2)
    st.download_button(
        label="📥 Télécharger l'analyse des besoins (JSON)",
        data=json_str,
        file_name="need_analysis_results.json",
        mime="application/json"
    )

if __name__ == "__main__":
    main()
