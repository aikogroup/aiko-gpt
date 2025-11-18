"""
Script utilitaire pour corriger les documents existants qui n'ont pas d'extracted_text
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.db import get_db_context
from database.repository import DocumentRepository
from database.streamlit_db import extract_text_from_file, parse_and_save_transcripts
from database.schemas import DocumentUpdate


def fix_documents_without_extracted_text():
    """
    Corrige tous les documents qui n'ont pas d'extracted_text en réextrayant le texte.
    """
    print("🔍 Recherche des documents sans extracted_text...")
    
    with get_db_context() as db:
        # Récupérer tous les documents
        all_documents = DocumentRepository.get_all(db)
        
        documents_to_fix = [
            doc for doc in all_documents 
            if not doc.extracted_text and doc.file_path
        ]
        
        print(f"📄 {len(documents_to_fix)} document(s) à corriger")
        
        for doc in documents_to_fix:
            print(f"\n📝 Traitement de: {doc.file_name} (ID: {doc.id})")
            print(f"   Type: {doc.file_type}")
            print(f"   Chemin: {doc.file_path}")
            
            # Vérifier que le fichier existe
            if not Path(doc.file_path).exists():
                print(f"   ⚠️  Le fichier n'existe pas, ignoré")
                continue
            
            # Extraire le texte
            extracted_text = extract_text_from_file(doc.file_path, doc.file_type)
            
            if extracted_text:
                # Mettre à jour le document
                update_data = DocumentUpdate(extracted_text=extracted_text)
                updated = DocumentRepository.update(db, doc.id, update_data)
                
                if updated:
                    print(f"   ✅ extracted_text mis à jour ({len(extracted_text)} caractères)")
                    
                    # Si c'est un transcript, parser et sauvegarder dans la table transcripts
                    if doc.file_type == "transcript":
                        print(f"   🔄 Parsing des interventions...")
                        # Note: parse_and_save_transcripts utilise st.success qui nécessite Streamlit
                        # On va créer une version sans Streamlit pour le script
                        try:
                            from process_transcript.pdf_parser import PDFParser
                            from process_transcript.json_parser import JSONParser
                            from database.repository import TranscriptRepository
                            from database.schemas import TranscriptBatchCreate, TranscriptBase
                            
                            file_extension = Path(doc.file_path).suffix.lower()
                            interventions = []
                            
                            if file_extension == ".pdf":
                                parser = PDFParser()
                                interventions = parser.parse_transcript(doc.file_path)
                            elif file_extension == ".json":
                                parser = JSONParser()
                                interventions = parser.parse_transcript(doc.file_path)
                            
                            if interventions:
                                # Vérifier si des transcripts existent déjà pour ce document
                                existing_transcripts = TranscriptRepository.get_by_document(db, doc.id)
                                if existing_transcripts:
                                    print(f"   ℹ️  {len(existing_transcripts)} interventions existent déjà, ignoré")
                                else:
                                    # Créer les objets TranscriptBase
                                    transcript_bases = [
                                        TranscriptBase(
                                            speaker=intervention.get("speaker"),
                                            timestamp=intervention.get("timestamp"),
                                            text=intervention.get("text", ""),
                                            speaker_type=None,
                                        )
                                        for intervention in interventions
                                    ]
                                    
                                    # Créer le batch
                                    batch = TranscriptBatchCreate(
                                        document_id=doc.id,
                                        transcripts=transcript_bases,
                                    )
                                    
                                    # Sauvegarder en batch
                                    TranscriptRepository.create_batch(db, batch)
                                    print(f"   ✅ {len(interventions)} interventions sauvegardées dans la table transcripts")
                        except Exception as e:
                            print(f"   ⚠️  Erreur lors du parsing: {str(e)}")
                else:
                    print(f"   ❌ Erreur lors de la mise à jour")
            else:
                print(f"   ⚠️  Impossible d'extraire le texte")
        
        print(f"\n✅ Correction terminée !")


if __name__ == "__main__":
    fix_documents_without_extracted_text()

