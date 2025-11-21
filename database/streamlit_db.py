"""
Fonctions utilitaires pour l'intégration de la base de données dans Streamlit
"""

import streamlit as st
from typing import List, Optional, Dict, Any
from database.db import get_db_context
from database.repository import (
    ProjectRepository,
    DocumentRepository,
    TranscriptRepository,
    AgentResultRepository,
)
from database.schemas import (
    ProjectCreate,
    DocumentCreate,
    TranscriptBatchCreate,
    TranscriptBase,
    AgentResultCreate,
    AgentResultUpdate,
)
from pathlib import Path
import json


# ============================================================================
# Gestion de projet
# ============================================================================

@st.cache_data(ttl=300)  # Cache 5 minutes
def load_project_list() -> List[Dict[str, Any]]:
    """
    Charge la liste de tous les projets (avec cache Streamlit).
    
    Returns:
        Liste de dictionnaires avec id, company_name, created_at
    """
    try:
        with get_db_context() as db:
            projects = ProjectRepository.get_all(db)
            return [
                {
                    "id": p.id,
                    "company_name": p.company_name,
                    "created_at": p.created_at,
                }
                for p in projects
            ]
    except Exception as e:
        error_str = str(e)
        # Détecter les erreurs de connexion réseau/DNS
        if "could not translate host name" in error_str or "Name or service not known" in error_str:
            st.error("❌ **Erreur de connexion à la base de données**")
            st.warning("""
            **Problème de résolution DNS/Connexion réseau détecté**
            
            Causes possibles :
            - Problème de connexion Internet
            - URL de base de données Supabase incorrecte ou expirée
            - Problème DNS temporaire
            
            **Solutions :**
            1. Vérifiez votre connexion Internet
            2. Vérifiez la variable d'environnement `DATABASE_URL` dans votre fichier `.env`
            3. Si vous utilisez Supabase, vérifiez que l'URL est correcte et que le projet est actif
            4. Pour utiliser une base de données locale, utilisez : `postgresql://aiko_user:aiko_password@localhost:5432/aiko_db`
            """)
        else:
            st.error(f"❌ Erreur lors du chargement des projets: {error_str}")
        return []


def create_new_project(company_name: str, company_info: Optional[Dict[str, Any]] = None) -> Optional[int]:
    """
    Crée un nouveau projet.
    
    Args:
        company_name: Nom de l'entreprise
        company_info: Informations supplémentaires (optionnel)
    
    Returns:
        ID du projet créé, ou None en cas d'erreur
    """
    try:
        with get_db_context() as db:
            project_data = ProjectCreate(
                company_name=company_name,
                company_info=company_info or {},
                created_by=None,  # Pour l'instant, pas d'utilisateur
            )
            project = ProjectRepository.create(db, project_data)
            # Invalider le cache
            load_project_list.clear()
            return project.id
    except Exception as e:
        st.error(f"❌ Erreur lors de la création du projet: {str(e)}")
        return None


@st.cache_data(ttl=300)
def load_project_data(project_id: int) -> Dict[str, Any]:
    """
    Charge toutes les données d'un projet (avec cache Streamlit).
    
    Args:
        project_id: ID du projet
    
    Returns:
        Dictionnaire avec toutes les données du projet:
        - project: informations du projet
        - documents: liste des documents (métadonnées uniquement)
        - workshops: données des workshops par document
        - word_extractions: données des word extractions par document
        - agent_results: résultats validés uniquement
    """
    try:
        from database.repository import (
            WorkshopRepository, 
            WordExtractionRepository,
            TranscriptRepository,
            SpeakerRepository
        )
        from database.models import Speaker
            
        with get_db_context() as db:
            # Charger le projet
            project = ProjectRepository.get_by_id(db, project_id)
            if not project:
                return {}
            
            # Charger les documents (métadonnées uniquement)
            documents = DocumentRepository.get_by_project(db, project_id)
            documents_data = []
            workshops_data = {}
            word_extractions_data = {}
            transcripts_data = {}  # NOUVEAU: Stocker les transcripts par document_id
            
            for d in documents:
                documents_data.append({
                    "id": d.id,
                    "file_name": d.file_name,
                    "file_type": d.file_type,
                    "file_metadata": d.file_metadata,
                })
                
                # Charger les workshops pour ce document
                if d.file_type == "workshop":
                    workshops = WorkshopRepository.get_by_document(db, d.id)
                    workshops_data[d.id] = [
                        {
                            "id": w.id,
                            "atelier_name": w.atelier_name,
                            "raw_extract": w.raw_extract,
                            "aggregate": w.aggregate,
                        }
                        for w in workshops
                    ]
                
                # Charger les word_extractions pour ce document
                if d.file_type == "word_report":
                    extractions = WordExtractionRepository.get_by_document(db, d.id)
                    word_extractions_data[d.id] = [
                        {
                            "id": e.id,
                            "extraction_type": e.extraction_type,
                            "data": e.data,
                        }
                        for e in extractions
                    ]
                
                # NOUVEAU: Charger les transcripts pour ce document
                if d.file_type == "transcript":
                    # Charger les speakers uniques pour ce document via les transcripts
                    transcripts = TranscriptRepository.get_by_document(db, d.id)
                    # Récupérer les speaker_ids uniques
                    speaker_ids = set()
                    for t in transcripts:
                        if t.speaker_id:
                            speaker_ids.add(t.speaker_id)
                    
                    # Charger les speakers depuis la table speakers
                    speakers_list = []
                    if speaker_ids:
                        speakers = db.query(Speaker).filter(Speaker.id.in_(speaker_ids)).all()
                        speakers_list = [
                            {
                                "id": s.id,
                                "name": s.name,
                                "role": s.role,
                                "level": s.level,
                                "speaker_type": s.speaker_type,
                                "is_interviewer": s.speaker_type == "interviewer",
                            }
                            for s in speakers
                        ]
                    
                    # Stocker les données du transcript avec ses speakers
                    transcripts_data[d.id] = {
                        "document_id": d.id,
                        "file_name": d.file_name,
                        "speakers": speakers_list,
                        "intervention_count": len(transcripts),
                    }
            
            # Charger les résultats validés uniquement
            agent_results = AgentResultRepository.get_by_project(
                db, project_id, status="validated"
            )
            results_data = {}
            for result in agent_results:
                key = f"{result.workflow_type}_{result.result_type}"
                results_data[key] = {
                    "id": result.id,
                    "workflow_type": result.workflow_type,
                    "result_type": result.result_type,
                    "data": result.data,
                    "status": result.status,
                }
            
            return {
                "project": {
                    "id": project.id,
                    "company_name": project.company_name,
                    "company_info": project.company_info,
                    "created_at": project.created_at,
                },
                "documents": documents_data,
                "workshops": workshops_data,
                "word_extractions": word_extractions_data,
                "transcripts": transcripts_data,  # NOUVEAU: Ajouter les transcripts
                "agent_results": results_data,
            }
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des données du projet: {str(e)}")
        return {}


# ============================================================================
# Sauvegarde des documents (avec texte extrait)
# ============================================================================

def extract_text_from_file(file_path: str, file_type: str) -> Optional[str]:
    """
    Extrait le texte depuis un fichier selon son type.
    
    Args:
        file_path: Chemin vers le fichier
        file_type: Type de fichier (transcript, workshop, word_report)
    
    Returns:
        Texte extrait, ou None en cas d'erreur
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None
        
        # Détecter l'extension du fichier
        file_extension = path.suffix.lower()
        
        if file_type == "word_report":
            # Pour les fichiers Word, on peut utiliser python-docx
            try:
                from docx import Document as DocxDocument
                doc = DocxDocument(file_path)
                text_parts = []
                for para in doc.paragraphs:
                    if para.text.strip():
                        text_parts.append(para.text)
                return "\n".join(text_parts)
            except Exception as e:
                st.warning(f"⚠️ Impossible d'extraire le texte du Word: {e}")
                return None
        
        elif file_type in ["transcript", "workshop"]:
            # Si c'est un PDF, utiliser PDFParser
            if file_extension == ".pdf":
                try:
                    from process_transcript.pdf_parser import PDFParser
                    parser = PDFParser()
                    return parser.extract_text_from_pdf(file_path)
                except Exception as e:
                    st.warning(f"⚠️ Impossible d'extraire le texte du PDF: {e}")
                    return None
            # Si c'est un fichier Excel, utiliser pandas
            elif file_extension in [".xlsx", ".xls"]:
                try:
                    import pandas as pd
                    # Lire le fichier Excel
                    df = pd.read_excel(file_path)
                    # Convertir le DataFrame en texte avec noms de colonnes explicites
                    text_parts = []
                    # Ajouter les noms de colonnes en en-tête
                    text_parts.append(" | ".join(str(col) for col in df.columns))
                    # Ajouter les lignes avec format "Colonne: Valeur" pour chaque cellule
                    for _, row in df.iterrows():
                        row_parts = []
                        for col_name, val in zip(df.columns, row):
                            val_str = str(val) if pd.notna(val) else ""
                            if val_str.strip():  # Ne pas ajouter si vide
                                row_parts.append(f"{col_name}: {val_str}")
                        if row_parts:  # Ne pas ajouter de ligne vide
                            text_parts.append(" | ".join(row_parts))
                    return "\n".join(text_parts)
                except Exception as e:
                    st.warning(f"⚠️ Impossible d'extraire le texte du fichier Excel: {e}")
                    return None
            else:
                # Pour les fichiers texte, lire directement
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        return f.read()
                except UnicodeDecodeError:
                    # Essayer avec d'autres encodages
                    try:
                        with open(file_path, "r", encoding="latin-1") as f:
                            return f.read()
                    except Exception as e:
                        st.warning(f"⚠️ Impossible de lire le fichier texte: {e}")
                        return None
        
        return None
    except Exception as e:
        st.warning(f"⚠️ Erreur lors de l'extraction du texte: {e}")
        return None


def save_document(
    project_id: int,
    file_name: str,
    file_type: str,
    file_path: Optional[str] = None,
    extracted_text: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Optional[int]:
    """
    Sauvegarde un document dans la base de données.
    
    Args:
        project_id: ID du projet
        file_name: Nom du fichier
        file_type: Type (transcript, workshop, word_report)
        file_path: Chemin vers le fichier (optionnel)
        extracted_text: Texte extrait (obligatoire pour transcript, workshop, word_report)
        metadata: Métadonnées supplémentaires (optionnel)
    
    Returns:
        ID du document créé, ou None en cas d'erreur
    """
    try:
        with get_db_context() as db:
            document_data = DocumentCreate(
                project_id=project_id,
                file_name=file_name,
                file_type=file_type,
                file_path=file_path,
                extracted_text=extracted_text,
                file_metadata=metadata or {},
            )
            document = DocumentRepository.create(db, document_data)
            # Invalider le cache
            load_project_data.clear()
            return document.id
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde du document: {str(e)}")
        return None


def delete_document_by_path(project_id: int, file_path: str, file_type: Optional[str] = None) -> bool:
    """
    Supprime un document de la base de données en utilisant le file_path.
    Note: Maintenant on cherche par file_name (basename du file_path) car file_path n'existe plus.
    
    Args:
        project_id: ID du projet
        file_path: Chemin vers le fichier (utilisé pour extraire le file_name)
        file_type: Type de fichier (optionnel, pour filtrage)
    
    Returns:
        True si succès, False sinon
    """
    try:
        from pathlib import Path
        file_name = Path(file_path).name
        
        with get_db_context() as db:
            # Trouver le document par project_id et file_name
            documents = DocumentRepository.get_by_project(db, project_id, file_type)
            document_to_delete = None
            
            for doc in documents:
                if doc.file_name == file_name:
                    document_to_delete = doc
                    break
            
            if document_to_delete:
                success = DocumentRepository.delete(db, document_to_delete.id)
                if success:
                    # Invalider le cache
                    load_project_data.clear()
                    return True
            return False
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression du document: {str(e)}")
        return False


def delete_document_by_id(document_id: int) -> bool:
    """
    Supprime un document de la base de données par son ID.
    
    Args:
        document_id: ID du document
    
    Returns:
        True si succès, False sinon
    """
    try:
        with get_db_context() as db:
            success = DocumentRepository.delete(db, document_id)
            if success:
                # Invalider le cache
                load_project_data.clear()
                return True
            return False
    except Exception as e:
        st.error(f"❌ Erreur lors de la suppression du document: {str(e)}")
        return False


def parse_and_save_transcripts(document_id: int, file_path: str, file_type: str = "transcript") -> bool:
    """
    Parse un document transcript et sauvegarde les interventions dans la table transcripts.
    
    Args:
        document_id: ID du document dans la table documents
        file_path: Chemin vers le fichier
        file_type: Type de fichier (transcript par défaut)
    
    Returns:
        True si succès, False sinon
    """
    try:
        path = Path(file_path)
        if not path.exists():
            st.warning(f"⚠️ Le fichier n'existe pas: {file_path}")
            return False
        
        file_extension = path.suffix.lower()
        interventions = []
        
        # Parser selon le type de fichier
        if file_extension == ".pdf":
            from process_transcript.pdf_parser import PDFParser
            parser = PDFParser()
            interventions = parser.parse_transcript(file_path)
        elif file_extension == ".json":
            from process_transcript.json_parser import JSONParser
            parser = JSONParser()
            interventions = parser.parse_transcript(file_path)
        else:
            # Pour les fichiers texte, essayer de parser comme transcript simple
            # (format basique: une intervention par ligne ou format similaire)
            st.warning(f"⚠️ Format de fichier non supporté pour le parsing: {file_extension}")
            return False
        
        if not interventions:
            st.warning(f"⚠️ Aucune intervention trouvée dans le fichier")
            return False
        
        # Sauvegarder les interventions dans la table transcripts
        with get_db_context() as db:
            # Créer les objets TranscriptBase
            transcript_bases = [
                TranscriptBase(
                    speaker=intervention.get("speaker"),
                    timestamp=intervention.get("timestamp"),
                    text=intervention.get("text", ""),
                    speaker_type=None,  # Peut être déterminé plus tard
                )
                for intervention in interventions
            ]
            
            # Créer le batch
            batch = TranscriptBatchCreate(
                document_id=document_id,
                transcripts=transcript_bases,
            )
            
            # Sauvegarder en batch
            TranscriptRepository.create_batch(db, batch)
            
            st.success(f"✅ {len(interventions)} interventions sauvegardées dans la table transcripts")
            return True
            
    except Exception as e:
        st.error(f"❌ Erreur lors du parsing et de la sauvegarde des transcripts: {str(e)}")
        return False


# ============================================================================
# Sauvegarde des résultats finaux (validés uniquement)
# ============================================================================

def save_agent_result(
    project_id: int,
    workflow_type: str,
    result_type: str,
    data: Dict[str, Any],
    status: str = "validated",
) -> Optional[int]:
    """
    Sauvegarde un résultat d'agent (final validé uniquement).
    
    Args:
        project_id: ID du projet
        workflow_type: Type de workflow (word_validation, need_analysis, executive_summary, etc.)
        result_type: Type de résultat (needs, use_cases, challenges, recommendations, etc.)
        data: Données structurées (JSONB)
        status: Statut (par défaut "validated")
    
    Returns:
        ID du résultat créé, ou None en cas d'erreur
    """
    try:
        with get_db_context() as db:
            # Vérifier si un résultat existe déjà
            existing = AgentResultRepository.get_latest(
                db, project_id, workflow_type, result_type, status="validated"
            )
            
            if existing:
                # Mettre à jour le résultat existant
                update_data = AgentResultUpdate(
                    data=data,
                    status=status,
                )
                updated = AgentResultRepository.update(db, existing.id, update_data)
                if updated:
                    # Invalider le cache
                    load_project_data.clear()
                    return updated.id
            else:
                # Créer un nouveau résultat
                result_data = AgentResultCreate(
                    project_id=project_id,
                    workflow_type=workflow_type,
                    result_type=result_type,
                    data=data,
                    status=status,
                    iteration_count=0,
                )
                result = AgentResultRepository.create(db, result_data)
                # Invalider le cache
                load_project_data.clear()
                return result.id
    except Exception as e:
        st.error(f"❌ Erreur lors de la sauvegarde du résultat: {str(e)}")
        return None


def has_validated_results(
    project_id: int,
    workflow_type: str,
    result_type: str,
) -> bool:
    """
    Vérifie si des résultats validés existent pour un projet/workflow/type.
    
    Args:
        project_id: ID du projet
        workflow_type: Type de workflow
        result_type: Type de résultat
    
    Returns:
        True si des résultats validés existent
    """
    try:
        with get_db_context() as db:
            result = AgentResultRepository.get_latest(
                db, project_id, workflow_type, result_type, status="validated"
            )
            return result is not None
    except Exception:
        return False


def load_agent_results(
    project_id: int,
    workflow_type: str,
    result_type: str,
    status: str = "validated",
) -> Optional[Dict[str, Any]]:
    """
    Charge les résultats validés pour un projet/workflow/type.
    
    Args:
        project_id: ID du projet
        workflow_type: Type de workflow
        result_type: Type de résultat
        status: Statut (par défaut "validated")
    
    Returns:
        Données du résultat, ou None si non trouvé
    """
    try:
        with get_db_context() as db:
            result = AgentResultRepository.get_latest(
                db, project_id, workflow_type, result_type, status=status
            )
            if result:
                return result.data
            return None
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement des résultats: {str(e)}")
        return None


def reject_agent_results(
    project_id: int,
    workflow_type: str,
    result_type: str,
) -> bool:
    """
    Marque les résultats existants comme "rejected" (pour régénération).
    
    Args:
        project_id: ID du projet
        workflow_type: Type de workflow
        result_type: Type de résultat
    
    Returns:
        True si succès
    """
    try:
        with get_db_context() as db:
            results = AgentResultRepository.get_by_project(
                db, project_id, workflow_type, result_type, status="validated"
            )
            for result in results:
                update_data = AgentResultUpdate(status="rejected")
                AgentResultRepository.update(db, result.id, update_data)
            # Invalider le cache
            load_project_data.clear()
            return True
    except Exception as e:
        st.error(f"❌ Erreur lors du rejet des résultats: {str(e)}")
        return False

