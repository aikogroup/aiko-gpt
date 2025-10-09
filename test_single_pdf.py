"""
Test avec un seul PDF pour voir l'analyse sémantique complète
"""
import os
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
        
        # Afficher l'analyse sémantique si disponible
        if 'semantic_analysis' in result and result['semantic_analysis']:
            print("\n=== Analyse sémantique ===")
            analysis = result['semantic_analysis']
            if 'besoins_exprimes' in analysis:
                print(f"Besoins exprimés: {analysis['besoins_exprimes']}")
            if 'frustrations_blocages' in analysis:
                print(f"Frustrations/Blocages: {analysis['frustrations_blocages']}")
            if 'opportunites_automatisation' in analysis:
                print(f"Opportunités d'automatisation: {analysis['opportunites_automatisation']}")
    else:
        print(f"Erreur: {result.get('error', 'Erreur inconnue')}")

if __name__ == "__main__":
    test_single_pdf()
