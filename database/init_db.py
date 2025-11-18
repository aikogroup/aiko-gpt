"""
Script d'initialisation de la base de données PostgreSQL
Crée les tables et fait une première insertion de test
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from database.db import (
    engine,
    SessionLocal,
    init_db,
    execute_sql_file,
    DATABASE_URL,
)
from database.models import Project, Document, Transcript, WorkflowState, AgentResult
from datetime import datetime


def main():
    """Fonction principale d'initialisation"""
    print("=" * 60)
    print("Initialisation de la base de données PostgreSQL")
    print("=" * 60)
    print(f"URL de connexion: {DATABASE_URL.split('@')[0]}@***")  # Masquer le mot de passe
    
    try:
        # Étape 1: Exécuter le fichier SQL pour créer les tables, triggers, fonctions
        print("\n📝 Étape 1: Exécution du schéma SQL...")
        schema_file = Path(__file__).parent / "schema.sql"
        if schema_file.exists():
            execute_sql_file(str(schema_file))
        else:
            print(f"⚠️  Fichier schema.sql non trouvé: {schema_file}")
            print("   Création des tables via SQLAlchemy...")
            init_db()
        
        # Étape 2: Créer les tables via SQLAlchemy (au cas où)
        print("\n📝 Étape 2: Vérification des tables via SQLAlchemy...")
        init_db()
        
        # Étape 3: Insertion de test
        print("\n📝 Étape 3: Insertion de données de test...")
        db = SessionLocal()
        try:
            # Vérifier si un projet de test existe déjà
            existing_project = db.query(Project).filter(
                Project.company_name == "Entreprise Test"
            ).first()
            
            if existing_project:
                print("   ⚠️  Projet de test déjà existant, skip insertion")
            else:
                # Créer un projet de test
                test_project = Project(
                    company_name="Entreprise Test",
                    company_info={
                        "nom": "Entreprise Test",
                        "secteur": "Technologie",
                        "chiffre_affaires": "1M EUR",
                        "nombre_employes": "10-50",
                        "description": "Entreprise de test pour aikoGPT"
                    },
                    created_by="system"
                )
                db.add(test_project)
                db.commit()
                db.refresh(test_project)
                print(f"   ✅ Projet créé: {test_project.company_name} (ID: {test_project.id})")
                
                # Créer un document de test
                test_document = Document(
                    project_id=test_project.id,
                    file_name="test_transcript.pdf",
                    file_type="transcript",
                    file_path="/tmp/test_transcript.pdf",
                    extracted_text="Ceci est un texte de test pour vérifier le fonctionnement de la base de données.",
                    file_metadata={"test": True}
                )
                db.add(test_document)
                db.commit()
                db.refresh(test_document)
                print(f"   ✅ Document créé: {test_document.file_name} (ID: {test_document.id})")
                
                # Créer quelques transcripts de test
                test_transcripts = [
                    Transcript(
                        document_id=test_document.id,
                        speaker="Alice",
                        timestamp="10:00",
                        text="Bonjour, je suis Alice et je vais vous présenter notre entreprise.",
                        speaker_type="interviewé"
                    ),
                    Transcript(
                        document_id=test_document.id,
                        speaker="Bob",
                        timestamp="10:05",
                        text="Merci Alice. Pouvez-vous nous parler de vos besoins en IA?",
                        speaker_type="interviewer"
                    ),
                    Transcript(
                        document_id=test_document.id,
                        speaker="Alice",
                        timestamp="10:10",
                        text="Nous souhaitons automatiser nos processus de reporting pour gagner du temps.",
                        speaker_type="interviewé"
                    ),
                ]
                
                for transcript in test_transcripts:
                    db.add(transcript)
                db.commit()
                print(f"   ✅ {len(test_transcripts)} transcripts créés")
                
                # Créer un workflow state de test
                test_workflow = WorkflowState(
                    project_id=test_project.id,
                    workflow_type="need_analysis",
                    thread_id="test-thread-123",
                    state_data={
                        "messages": [],
                        "company_info": test_project.company_info,
                        "workflow_paused": False
                    },
                    status="completed"
                )
                db.add(test_workflow)
                db.commit()
                print(f"   ✅ Workflow state créé: {test_workflow.workflow_type} (ID: {test_workflow.id})")
                
                # Créer un agent result de test
                test_agent_result = AgentResult(
                    project_id=test_project.id,
                    workflow_type="need_analysis",
                    result_type="needs",
                    data={
                        "identified_needs": [
                            {
                                "id": "need_1",
                                "theme": "Automatisation",
                                "quotes": ["Nous souhaitons automatiser nos processus"]
                            }
                        ]
                    },
                    status="validated",
                    iteration_count=1
                )
                db.add(test_agent_result)
                db.commit()
                print(f"   ✅ Agent result créé: {test_agent_result.result_type} (ID: {test_agent_result.id})")
            
            # Afficher un résumé
            print("\n" + "=" * 60)
            print("Résumé de la base de données:")
            print("=" * 60)
            projects_count = db.query(Project).count()
            documents_count = db.query(Document).count()
            transcripts_count = db.query(Transcript).count()
            workflows_count = db.query(WorkflowState).count()
            agent_results_count = db.query(AgentResult).count()
            
            print(f"   📊 Projets: {projects_count}")
            print(f"   📄 Documents: {documents_count}")
            print(f"   💬 Transcripts: {transcripts_count}")
            print(f"   🔄 Workflows: {workflows_count}")
            print(f"   🤖 Résultats d'agents: {agent_results_count}")
            print("=" * 60)
            print("✅ Initialisation terminée avec succès!")
            
        except Exception as e:
            db.rollback()
            print(f"❌ Erreur lors de l'insertion de test: {e}")
            raise
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

