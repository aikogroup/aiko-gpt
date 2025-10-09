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

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

from process_atelier.workshop_agent import WorkshopAgent
from process_transcript.transcript_agent import TranscriptAgent
from web_search.web_search_agent import WebSearchAgent

def main():
    """Fonction principale de l'application Streamlit"""
    
    # Configuration de la page
    st.set_page_config(
        page_title="AIKO - Traitement d'Ateliers IA & Transcriptions",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Titre principal
    st.title("🤖 AIKO - Traitement d'Ateliers IA & Transcriptions")
    st.markdown("---")
    
    # Onglets pour les trois phases
    tab1, tab2, tab3 = st.tabs(["📊 Phase 1: Ateliers IA", "📄 Phase 2: Transcriptions PDF", "🔍 Phase 3: Recherche Web"])
    
    with tab1:
        process_workshop_phase()
    
    with tab2:
        process_transcript_phase()
    
    with tab3:
        process_web_search_phase()

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

if __name__ == "__main__":
    main()
