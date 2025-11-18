"""
Exemple d'intégration de la base de données dans Streamlit
"""

import streamlit as st
from database.db import get_db_context, init_db
from database.repository import (
    ProjectRepository,
    DocumentRepository,
    TranscriptRepository,
    AgentResultRepository,
)
from database.schemas import ProjectCreate, DocumentCreate, TranscriptBatchCreate


def init_database():
    """Initialise la base de données si nécessaire"""
    if 'db_initialized' not in st.session_state:
        try:
            init_db()
            st.session_state.db_initialized = True
        except Exception as e:
            st.error(f"Erreur lors de l'initialisation de la BDD: {e}")


def display_projects():
    """Affiche la liste des projets"""
    st.subheader("📁 Projets existants")
    
    with get_db_context() as db:
        projects = ProjectRepository.get_all(db, limit=100)
        
        if not projects:
            st.info("Aucun projet trouvé. Créez-en un nouveau ci-dessous.")
            return None
        
        # Sélecteur de projet
        project_names = [f"{p.id} - {p.company_name}" for p in projects]
        selected = st.selectbox(
            "Sélectionner un projet",
            options=project_names,
            key="project_selector"
        )
        
        if selected:
            project_id = int(selected.split(" - ")[0])
            project = ProjectRepository.get_by_id(db, project_id)
            return project
    
    return None


def create_project_form():
    """Formulaire pour créer un nouveau projet"""
    st.subheader("➕ Créer un nouveau projet")
    
    with st.form("create_project_form"):
        company_name = st.text_input("Nom de l'entreprise *", key="new_company_name")
        company_sector = st.text_input("Secteur d'activité", key="new_company_sector")
        company_ca = st.text_input("Chiffre d'affaires", key="new_company_ca")
        company_employees = st.text_input("Nombre d'employés", key="new_company_employees")
        company_description = st.text_area("Description", key="new_company_description")
        created_by = st.text_input("Créé par", value=st.session_state.get("username", "user"), key="new_created_by")
        
        submitted = st.form_submit_button("Créer le projet")
        
        if submitted:
            if not company_name:
                st.error("Le nom de l'entreprise est obligatoire")
                return
            
            company_info = {}
            if company_sector:
                company_info["secteur"] = company_sector
            if company_ca:
                company_info["chiffre_affaires"] = company_ca
            if company_employees:
                company_info["nombre_employes"] = company_employees
            if company_description:
                company_info["description"] = company_description
            
            try:
                with get_db_context() as db:
                    project = ProjectRepository.create(db, ProjectCreate(
                        company_name=company_name,
                        company_info=company_info if company_info else None,
                        created_by=created_by
                    ))
                    st.success(f"✅ Projet créé: {project.company_name} (ID: {project.id})")
                    st.rerun()
            except Exception as e:
                st.error(f"Erreur lors de la création: {e}")


def display_project_details(project):
    """Affiche les détails d'un projet"""
    if not project:
        return
    
    st.subheader(f"🏢 {project.company_name}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("ID", project.id)
        st.metric("Créé le", project.created_at.strftime("%Y-%m-%d %H:%M"))
    with col2:
        if project.company_info:
            if "secteur" in project.company_info:
                st.metric("Secteur", project.company_info["secteur"])
            if "nombre_employes" in project.company_info:
                st.metric("Employés", project.company_info["nombre_employes"])
    
    # Afficher les documents
    with get_db_context() as db:
        documents = DocumentRepository.get_by_project(db, project.id)
        if documents:
            st.subheader("📄 Documents")
            for doc in documents:
                with st.expander(f"{doc.file_name} ({doc.file_type})"):
                    st.write(f"**Type:** {doc.file_type}")
                    st.write(f"**Créé le:** {doc.created_at.strftime('%Y-%m-%d %H:%M')}")
                    if doc.extracted_text:
                        st.text_area("Texte extrait", doc.extracted_text, height=100, disabled=True)
        
        # Afficher les résultats d'agents
        agent_results = AgentResultRepository.get_by_project(db, project.id)
        if agent_results:
            st.subheader("🤖 Résultats d'agents")
            for result in agent_results:
                with st.expander(f"{result.workflow_type} - {result.result_type} ({result.status})"):
                    st.json(result.data)


def search_transcripts_form(project_id):
    """Formulaire de recherche full-text dans les transcripts"""
    st.subheader("🔍 Recherche dans les transcripts")
    
    search_query = st.text_input("Requête de recherche", key="transcript_search")
    speaker_filter = st.text_input("Filtrer par speaker (optionnel)", key="transcript_speaker")
    
    if st.button("Rechercher", key="search_transcripts"):
        if not search_query:
            st.warning("Veuillez entrer une requête de recherche")
            return
        
        try:
            with get_db_context() as db:
                results = TranscriptRepository.search_fulltext(
                    db,
                    search_query=search_query,
                    project_id=project_id,
                    speaker=speaker_filter if speaker_filter else None,
                    limit=50
                )
                
                if results:
                    st.success(f"✅ {len(results)} résultat(s) trouvé(s)")
                    for i, result in enumerate(results, 1):
                        with st.expander(f"Résultat {i} - {result.get('speaker', 'N/A')} (rank: {result.get('rank', 0):.4f})"):
                            st.write(f"**Speaker:** {result.get('speaker', 'N/A')}")
                            st.write(f"**Timestamp:** {result.get('timestamp', 'N/A')}")
                            st.write(f"**Texte:** {result.get('text', '')}")
                else:
                    st.info("Aucun résultat trouvé")
        except Exception as e:
            st.error(f"Erreur lors de la recherche: {e}")


# Exemple d'utilisation dans Streamlit
def main():
    """Fonction principale d'exemple"""
    st.title("🗄️ Base de données aikoGPT")
    
    # Initialiser la BDD
    init_database()
    
    # Onglets
    tab1, tab2, tab3 = st.tabs(["Projets", "Créer un projet", "Recherche"])
    
    with tab1:
        project = display_projects()
        if project:
            display_project_details(project)
    
    with tab2:
        create_project_form()
    
    with tab3:
        project = display_projects()
        if project:
            search_transcripts_form(project.id)
        else:
            st.info("Sélectionnez d'abord un projet dans l'onglet 'Projets'")


if __name__ == "__main__":
    main()

