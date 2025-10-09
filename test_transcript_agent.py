"""
Script de test pour l'agent de traitement des transcriptions
"""
import os
import json
from pathlib import Path
from process_transcript.transcript_agent import TranscriptAgent

def test_single_pdf():
    """Test avec un seul PDF"""
    print("=== Test avec un seul PDF ===")
    
    # Initialiser l'agent
    agent = TranscriptAgent()
    
    # Chemin vers un PDF d'exemple
    pdf_path = "inputs/0404-Cousin-Biotech-x-aiko-Echange-IA-Booster-RH-DAF-6d981384-b94f.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Fichier PDF non trouvé: {pdf_path}")
        return
    
    # Traiter le PDF
    result = agent.process_single_pdf(pdf_path)
    
    # Afficher les résultats
    print(f"Statut: {result['status']}")
    if result['status'] == 'success':
        print(f"Interventions totales: {result['parsing']['total_interventions']}")
        print(f"Interventions intéressantes: {result['interesting_parts']['count']}")
        print(f"Speakers: {result['parsing']['speakers']}")
        print("\nRésumé de l'analyse:")
        print(result['summary'])
    else:
        print(f"Erreur: {result.get('error', 'Erreur inconnue')}")

def test_multiple_pdfs():
    """Test avec plusieurs PDFs"""
    print("\n=== Test avec plusieurs PDFs ===")
    
    # Initialiser l'agent
    agent = TranscriptAgent()
    
    # Trouver tous les PDFs dans le dossier inputs
    inputs_dir = Path("inputs")
    pdf_files = list(inputs_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("Aucun fichier PDF trouvé dans le dossier inputs")
        return
    
    # Prendre les 3 premiers PDFs pour le test
    pdf_paths = [str(pdf_file) for pdf_file in pdf_files[:3]]
    print(f"Traitement de {len(pdf_paths)} PDFs")
    
    # Traiter les PDFs
    results = agent.process_multiple_pdfs(pdf_paths)
    
    # Afficher les résultats
    print(f"Total PDFs: {results['total_pdfs']}")
    print(f"Succès: {results['successful']}")
    print(f"Échecs: {results['failed']}")
    
    # Consolider l'analyse
    successful_results = [r for r in results['results'] if r['status'] == 'success']
    if successful_results:
        consolidated = agent.get_consolidated_analysis(successful_results)
        print("\nAnalyse consolidée:")
        print(f"Besoins exprimés: {consolidated['statistics']['total_needs']}")
        print(f"Frustrations: {consolidated['statistics']['total_frustrations']}")
        print(f"Opportunités: {consolidated['statistics']['total_opportunities']}")
        print(f"Citations: {consolidated['statistics']['total_citations']}")

def test_directory():
    """Test avec un répertoire entier"""
    print("\n=== Test avec le répertoire inputs ===")
    
    # Initialiser l'agent
    agent = TranscriptAgent()
    
    # Traiter le répertoire
    result = agent.process_directory("inputs")
    
    if result.get('status') == 'no_files':
        print("Aucun fichier PDF trouvé dans le répertoire")
        return
    
    print(f"Total PDFs traités: {result['total_pdfs']}")
    print(f"Succès: {result['successful']}")
    print(f"Échecs: {result['failed']}")

if __name__ == "__main__":
    print("Test de l'agent de traitement des transcriptions")
    print("=" * 50)
    
    # Vérifier que la clé API OpenAI est configurée
    if not os.getenv("OPENAI_API_KEY"):
        print("ATTENTION: La clé API OpenAI n'est pas configurée.")
        print("L'analyse sémantique ne fonctionnera pas sans cette clé.")
        print("Configurez OPENAI_API_KEY dans votre environnement.")
        print()
    
    # Tests
    test_single_pdf()
    
    print("\n=== Tests terminés ===")
