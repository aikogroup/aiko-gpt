"""
Exemple d'utilisation du TokenTracker avec les agents
"""

import sys
sys.path.append('/home/addeche/aiko/aikoGPT')

from utils.token_tracker import TokenTracker

# Exemple 1: Utilisation basique du tracker
def example_basic_tracking():
    """Exemple d'utilisation basique avec tracking manuel"""
    
    # Créer le tracker
    tracker = TokenTracker()
    
    print("🚀 Simulation d'un appel API avec tracking...\n")
    
    # Simulation d'un objet response (comme celui retourné par OpenAI)
    mock_response = {
        'usage': {
            'input_tokens': 5000,
            'output_tokens': 3000
        }
    }
    
    # Tracker la réponse
    tracker.track_response(
        mock_response, 
        agent_name="need_analysis",
        operation="analyze_needs",
        model="gpt-5-nano"
    )
    
    # Afficher le résumé
    tracker.print_summary()
    
    # Sauvegarder le rapport
    report_path = tracker.save_report()
    print(f"✅ Rapport sauvegardé: {report_path}")


# Exemple 2: Tracking dans un workflow complet
def example_workflow_tracking():
    """Exemple de tracking dans un workflow complet"""
    
    tracker = TokenTracker(output_dir="outputs/token_tracking")
    
    print("📊 Simulation d'un workflow complet avec tracking\n")
    
    # Simulation de plusieurs appels d'agents
    agents_calls = [
        ("workshop", "parse_excel", 1500, 800),
        ("workshop", "aggregate_use_cases", 2000, 1200),
        ("transcript", "parse_pdf", 3000, 1500),
        ("transcript", "semantic_analysis", 4000, 2000),
        ("web_search", "search_company", 500, 300),
        ("need_analysis", "analyze_needs", 5000, 3000),
        ("use_case_analysis", "analyze_use_cases", 6000, 3500),
    ]
    
    for agent_name, operation, input_tokens, output_tokens in agents_calls:
        # Simulation d'un objet response
        mock_response = {
            'usage': {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            }
        }
        
        tracker.track_response(
            mock_response, 
            agent_name, 
            operation, 
            model="gpt-5-nano"
        )
    
    # Afficher le résumé final
    tracker.print_summary()
    
    # Sauvegarder le rapport
    report_path = tracker.save_report()
    print(f"✅ Rapport complet sauvegardé: {report_path}")


# Exemple 3: Intégration dans un agent (modification du code agent)
def example_agent_integration():
    """
    Exemple de comment modifier un agent pour intégrer le tracking.
    
    AVANT dans l'agent:
    ```python
    response = self.client.responses.parse(
        model=self.model,
        input=[...],
        text_format=NeedAnalysisResponse
    )
    parsed_response = response.output_parsed
    ```
    
    APRÈS avec tracking:
    ```python
    response = self.client.responses.parse(
        model=self.model,
        input=[...],
        text_format=NeedAnalysisResponse
    )
    
    # AJOUT: Tracking des tokens
    if hasattr(self, 'tracker') and self.tracker:
        self.tracker.track_response(
            response, 
            agent_name="need_analysis",
            operation="analyze_needs",
            model=self.model
        )
    
    parsed_response = response.output_parsed
    ```
    """
    print("""
    📝 GUIDE D'INTÉGRATION DANS LES AGENTS
    
    1. Ajouter le tracker comme attribut de classe:
       
       from utils.token_tracker import TokenTracker
       
       class NeedAnalysisAgent:
           def __init__(self, api_key: str, tracker: TokenTracker = None):
               self.tracker = tracker
               ...
    
    2. Après chaque appel API, tracker la réponse:
       
       response = self.client.responses.parse(...)
       
       if self.tracker:
           self.tracker.track_response(
               response,
               agent_name="need_analysis",
               operation="analyze_needs",
               model=self.model
           )
    
    3. Dans le workflow, créer et passer le tracker:
       
       tracker = TokenTracker()
       agent = NeedAnalysisAgent(api_key=api_key, tracker=tracker)
       
       # À la fin du workflow
       tracker.print_summary()
       tracker.save_report()
    """)


if __name__ == "__main__":
    print("="*70)
    print("🎯 EXEMPLES D'UTILISATION DU TOKEN TRACKER")
    print("="*70 + "\n")
    
    # Exemple 1: Tracking basique
    # example_basic_tracking()
    
    # Exemple 2: Simulation d'un workflow complet
    example_workflow_tracking()
    
    # Exemple 3: Guide d'intégration
    print("\n")
    example_agent_integration()

