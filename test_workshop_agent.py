#!/usr/bin/env python3
"""
Script de test pour le Workshop Agent
"""

from process_atelier.workshop_agent import WorkshopAgent
import json
from pathlib import Path

def main():
    """Test complet du Workshop Agent"""
    print("🧪 TEST DU WORKSHOP AGENT")
    print("=" * 50)
    
    # Configuration
    input_file = "inputs/atelier_exemple.xlsx"
    output_file = "outputs/workshop_results_test.json"
    
    # Création du dossier de sortie si nécessaire
    Path("outputs").mkdir(exist_ok=True)
    
    # Initialisation de l'agent
    print("🔧 Initialisation de l'agent...")
    agent = WorkshopAgent()
    
    try:
        print(f"📊 Traitement du fichier: {input_file}")
        results = agent.process_workshop_file(input_file)
        
        print(f"\n✅ Traitement terminé avec succès!")
        print(f"📈 Statistiques:")
        print(f"   - Nombre d'ateliers: {len(results)}")
        
        total_use_cases = sum(len(result.use_cases) for result in results)
        print(f"   - Total cas d'usage: {total_use_cases}")
        
        # Affichage détaillé des résultats
        print(f"\n📋 DÉTAIL DES ATELIERS:")
        print("-" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"\n🏢 Atelier {i}: {result.theme}")
            print(f"   ID: {result.workshop_id}")
            print(f"   Cas d'usage: {len(result.use_cases)}")
            
            # Affichage des premiers cas d'usage
            for j, use_case in enumerate(result.use_cases[:3], 1):
                print(f"   {j}. {use_case.title}")
                if use_case.objective:
                    print(f"      → Objectif: {use_case.objective}")
                if use_case.benefits:
                    print(f"      → Bénéfices: {', '.join(use_case.benefits)}")
            
            if len(result.use_cases) > 3:
                print(f"   ... et {len(result.use_cases) - 3} autres cas d'usage")
        
        # Sauvegarde des résultats
        print(f"\n💾 Sauvegarde des résultats...")
        agent.save_results(results, output_file)
        
        # Vérification du fichier JSON
        with open(output_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        
        print(f"✅ Fichier JSON sauvegardé: {output_file}")
        print(f"   - Taille: {Path(output_file).stat().st_size} bytes")
        print(f"   - Ateliers sauvegardés: {len(saved_data)}")
        
        print(f"\n🎉 Test terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        raise

if __name__ == "__main__":
    main()


