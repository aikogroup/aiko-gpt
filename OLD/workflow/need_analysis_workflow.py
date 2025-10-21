"""
Workflow LangGraph pour l'analyse des besoins
"""

import os
import json
from typing import Dict, List, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
# Streamlit supprimé - plus utilisé

# Import des agents
import sys
sys.path.append('/home/addeche/aiko/aikoGPT')
from need_analysis.need_analysis_agent import NeedAnalysisAgent
from process_atelier.workshop_agent import WorkshopAgent
from process_transcript.transcript_agent import TranscriptAgent
from web_search.web_search_agent import WebSearchAgent
# StreamlitValidationInterface supprimé - plus utilisé
from use_case_analysis.use_case_analysis_agent import UseCaseAnalysisAgent
# StreamlitUseCaseValidation supprimé - plus utilisé
from utils.token_tracker import TokenTracker


class WorkflowState(TypedDict):
    """État du workflow LangGraph"""
    messages: Annotated[List[BaseMessage], add_messages]
    # Fichiers d'entrée
    workshop_files: List[str]
    transcript_files: List[str]
    company_info: Dict[str, Any]
    # Résultats des agents
    workshop_results: Dict[str, Any]
    transcript_results: List[Dict[str, Any]]
    web_search_results: Dict[str, Any]
    # Flag pour skip agents si résultats pré-calculés
    skip_agents: bool
    # Données agrégées pour l'analyse (seulement transcript_data car il contient une transformation utile)
    transcript_data: List[Dict[str, Any]]
    # Résultats de l'analyse des besoins
    identified_needs: List[Dict[str, Any]]
    # Validation humaine des besoins
    validated_needs: List[Dict[str, Any]]
    rejected_needs: List[Dict[str, Any]]
    user_feedback: str
    validation_result: Dict[str, Any]
    # État du workflow des besoins
    final_needs: List[Dict[str, Any]]
    success: bool
    iteration_count: int
    max_iterations: int
    workflow_paused: bool
    # Résultats de l'analyse des use cases
    proposed_quick_wins: List[Dict[str, Any]]
    proposed_structuration_ia: List[Dict[str, Any]]
    # Validation humaine des use cases
    validated_quick_wins: List[Dict[str, Any]]
    validated_structuration_ia: List[Dict[str, Any]]
    rejected_quick_wins: List[Dict[str, Any]]
    rejected_structuration_ia: List[Dict[str, Any]]
    use_case_user_feedback: str
    use_case_validation_result: Dict[str, Any]
    # État du workflow des use cases
    final_quick_wins: List[Dict[str, Any]]
    final_structuration_ia: List[Dict[str, Any]]
    use_case_success: bool
    use_case_iteration: int
    max_use_case_iterations: int
    use_case_workflow_paused: bool


class NeedAnalysisWorkflow:
    """
    Workflow LangGraph pour l'analyse des besoins métier
    """
    
    def __init__(self, api_key: str, dev_mode: bool = False, debug_mode: bool = False):
        """
        Initialise le workflow avec la clé API OpenAI.
        
        Args:
            api_key: Clé API OpenAI
            dev_mode: Mode développement (utilise les données mockées)
            debug_mode: Mode debugging avec LangGraph Studio
        """
        self.api_key = api_key
        self.dev_mode = dev_mode
        self.debug_mode = debug_mode
        model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key
        )
        
        # Initialisation du tracker de tokens et coûts
        self.tracker = TokenTracker(output_dir="outputs/token_tracking")
        print("📊 Token Tracker initialisé - Suivi des coûts activé\n")
        
        # Initialisation des agents AVEC le tracker pour ceux qui le supportent
        self.workshop_agent = WorkshopAgent(api_key)
        self.transcript_agent = TranscriptAgent(api_key)
        self.web_search_agent = WebSearchAgent()  # Pas de paramètre
        self.need_analysis_agent = NeedAnalysisAgent(api_key, tracker=self.tracker)
        # Interfaces Streamlit supprimées - plus utilisées
        self.human_interface = None
        # Nouveaux agents pour l'analyse des use cases
        self.use_case_analysis_agent = UseCaseAnalysisAgent(api_key, tracker=self.tracker)
        self.use_case_validation_interface = None
        
        # Configuration du checkpointer pour le debugging
        self.checkpointer = self._setup_checkpointer()
        
        # Création du graphe
        self.graph = self._create_graph()
    
    def _print_tracker_stats(self, agent_name: str = None):
        """
        Affiche les statistiques de tokens du tracker.
        
        Args:
            agent_name: Nom de l'agent qui vient de s'exécuter (optionnel)
        """
        if not self.tracker:
            return
        
        summary = self.tracker.get_session_summary()
        
        print("\n" + "─"*70)
        if agent_name:
            print(f"📊 TOKENS APRÈS {agent_name.upper()}")
        else:
            print("📊 TOKENS CUMULÉS")
        print("─"*70)
        
        # Tokens cumulés
        total_tokens = summary['total_tokens']
        input_tokens = summary['total_input_tokens']
        output_tokens = summary['total_output_tokens']
        
        print(f"🔤 Tokens cumulés: {total_tokens:,}")
        print(f"   ├─ Input:  {input_tokens:,}")
        print(f"   └─ Output: {output_tokens:,}")
        
        # Détails par agent
        if summary['calls_by_agent']:
            print(f"\n📊 Détails par agent:")
            for name, stats in summary['calls_by_agent'].items():
                print(f"   • {name}:")
                print(f"     ├─ Total: {stats['total_tokens']:,} tokens")
                print(f"     ├─ Input: {stats['input_tokens']:,}")
                print(f"     └─ Output: {stats['output_tokens']:,}")
        
        print("─"*70 + "\n")
    
    def _setup_checkpointer(self):
        """
        Configure le checkpointer pour le debugging avec LangGraph Studio.
        
        Returns:
            Checkpointer configuré
        """
        if self.debug_mode:
            # Mode debugging - utiliser MemorySaver pour la persistance
            return MemorySaver()
        else:
            # Mode normal - pas de checkpointer
            return None
    
    def _create_graph(self) -> StateGraph:
        """
        Crée le graphe LangGraph pour le workflow d'analyse des besoins.
        NOUVELLE VERSION: Avec parallélisation des agents.
        
        Returns:
            StateGraph configuré
        """
        # Création du graphe
        workflow = StateGraph(WorkflowState)
        
        # Ajout des nœuds - Phase 1 : Analyse des besoins
        # NOUVEAU: Dispatcher et agents parallèles
        workflow.add_node("dispatcher", self._dispatcher_node)
        workflow.add_node("workshop_agent", self._workshop_agent_node)
        workflow.add_node("transcript_agent", self._transcript_agent_node)
        workflow.add_node("web_search_agent", self._web_search_agent_node)
        workflow.add_node("collect_data", self._collect_data_node)
        workflow.add_node("analyze_needs", self._analyze_needs_node)
        workflow.add_node("human_validation", self._human_validation_node)
        workflow.add_node("check_success", self._check_success_node)
        workflow.add_node("finalize_results", self._finalize_results_node)
        
        # Ajout des nœuds - Phase 2 : Analyse des use cases
        workflow.add_node("analyze_use_cases", self._analyze_use_cases_node)
        workflow.add_node("validate_use_cases", self._validate_use_cases_node)
        workflow.add_node("check_use_case_success", self._check_use_case_success_node)
        workflow.add_node("finalize_use_cases", self._finalize_use_cases_node)
        
        # Définition du flux - point d'entrée selon le mode
        if self.dev_mode:
            workflow.set_entry_point("collect_data")
        else:
            workflow.set_entry_point("dispatcher")
        
        # NOUVEAU: Flux parallèle - Phase 1 : Collecte de données
        # Dispatcher → 3 agents en parallèle → collect_data
        workflow.add_edge("dispatcher", "workshop_agent")
        workflow.add_edge("dispatcher", "transcript_agent")
        workflow.add_edge("dispatcher", "web_search_agent")
        workflow.add_edge("workshop_agent", "collect_data")
        workflow.add_edge("transcript_agent", "collect_data")
        workflow.add_edge("web_search_agent", "collect_data")
        
        # Flux séquentiel - Phase 1 : Analyse des besoins
        workflow.add_edge("collect_data", "analyze_needs")
        workflow.add_edge("analyze_needs", "human_validation")
        workflow.add_edge("human_validation", "check_success")
        
        # Conditions de branchement - Phase 1
        workflow.add_conditional_edges(
            "check_success",
            self._should_continue,
            {
                "continue": "analyze_needs",
                "success": "finalize_results",
                "max_iterations": END
            }
        )
        
        # Transition vers Phase 2 : Analyse des use cases
        workflow.add_edge("finalize_results", "analyze_use_cases")
        workflow.add_edge("analyze_use_cases", "validate_use_cases")
        workflow.add_edge("validate_use_cases", "check_use_case_success")
        
        # Conditions de branchement - Phase 2
        workflow.add_conditional_edges(
            "check_use_case_success",
            self._should_continue_use_cases,
            {
                "continue": "analyze_use_cases",
                "success": "finalize_use_cases",
                "max_iterations": END
            }
        )
        
        workflow.add_edge("finalize_use_cases", END)
        
        # Configuration: LangGraph Platform gère le checkpointer via langgraph.json (Postgres)
        # On ne définit PAS de checkpointer ici pour éviter les conflits
        # Les interrupts sont gérés automatiquement par LangGraph Platform
        return workflow.compile()
    
    # ==================== NOUVEAUX NŒUDS POUR LA PARALLÉLISATION ====================
    
    def _dispatcher_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud dispatcher qui prépare et distribue le travail aux 3 agents en parallèle.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        print(f"\n🚀 [PARALLÉLISATION] dispatcher_node - DÉBUT")
        print(f"📊 État d'entrée:")
        print(f"   - workshop_files: {len(state.get('workshop_files', []))}")
        print(f"   - transcript_files: {len(state.get('transcript_files', []))}")
        print(f"   - company_info: {bool(state.get('company_info', {}))}")
        print(f"   - Résultats pré-calculés:")
        print(f"     • workshop_results: {bool(state.get('workshop_results', {}))}")
        print(f"     • transcript_results: {bool(state.get('transcript_results', []))}")
        print(f"     • web_search_results: {bool(state.get('web_search_results', {}))}")
        
        try:
            # Vérifier si les résultats sont déjà présents (calculés dans Streamlit)
            if state.get("workshop_results") or state.get("transcript_results") or state.get("web_search_results"):
                print(f"✅ [PARALLÉLISATION] Résultats pré-calculés détectés - skip des agents")
                # Marquer que nous n'avons pas besoin d'exécuter les agents
                state["skip_agents"] = True
            else:
                print(f"🔄 [PARALLÉLISATION] Aucun résultat pré-calculé - les 3 agents vont s'exécuter en PARALLÈLE")
                state["skip_agents"] = False
            
            print(f"✅ [PARALLÉLISATION] dispatcher_node - FIN")
            return state
            
        except Exception as e:
            print(f"❌ [PARALLÉLISATION] Erreur dans dispatcher_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur dispatcher: {str(e)}")]
            return state
    
    def _workshop_agent_node(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Nœud workshop agent - s'exécute en PARALLÈLE avec les autres agents.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            Dictionnaire partiel avec seulement workshop_results (pour éviter les conflits de fusion)
        """
        print(f"\n📝 [PARALLÈLE-1/3] workshop_agent_node - DÉBUT")
        
        try:
            # Si les résultats sont pré-calculés, skip
            if state.get("skip_agents", False):
                print(f"⏩ [PARALLÈLE-1/3] Résultats pré-calculés - skip")
                return {}
            
            workshop_files = state.get("workshop_files", [])
            
            if workshop_files:
                print(f"🔄 [PARALLÈLE-1/3] Traitement de {len(workshop_files)} fichiers workshop...")
                all_results = []
                for file_path in workshop_files:
                    file_results = self.workshop_agent.process_workshop_file(file_path)
                    all_results.extend(file_results)
                print(f"✅ [PARALLÈLE-1/3] {len(all_results)} workshops traités")
                print(f"✅ [PARALLÈLE-1/3] workshop_agent_node - FIN")
                return {"workshop_results": {"workshops": all_results}}
            else:
                print(f"⚠️ [PARALLÈLE-1/3] Aucun fichier workshop fourni")
                print(f"✅ [PARALLÈLE-1/3] workshop_agent_node - FIN")
                return {"workshop_results": {}}
            
        except Exception as e:
            print(f"❌ [PARALLÈLE-1/3] Erreur dans workshop_agent_node: {str(e)}")
            return {
                "workshop_results": {},
                "messages": [HumanMessage(content=f"Erreur workshop agent: {str(e)}")]
            }
    
    def _transcript_agent_node(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Nœud transcript agent - s'exécute en PARALLÈLE avec les autres agents.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            Dictionnaire partiel avec seulement transcript_results (pour éviter les conflits de fusion)
        """
        print(f"\n📄 [PARALLÈLE-2/3] transcript_agent_node - DÉBUT")
        
        try:
            # Si les résultats sont pré-calculés, skip
            if state.get("skip_agents", False):
                print(f"⏩ [PARALLÈLE-2/3] Résultats pré-calculés - skip")
                return {}
            
            transcript_files = state.get("transcript_files", [])
            
            if transcript_files:
                print(f"🔄 [PARALLÈLE-2/3] Traitement de {len(transcript_files)} PDFs...")
                results = self.transcript_agent.process_multiple_pdfs(transcript_files)
                print(f"✅ [PARALLÈLE-2/3] {len(results.get('results', []))} transcripts traités")
                print(f"✅ [PARALLÈLE-2/3] transcript_agent_node - FIN")
                return {"transcript_results": results}
            else:
                print(f"⚠️ [PARALLÈLE-2/3] Aucun fichier transcript fourni")
                print(f"✅ [PARALLÈLE-2/3] transcript_agent_node - FIN")
                return {"transcript_results": []}
            
        except Exception as e:
            print(f"❌ [PARALLÈLE-2/3] Erreur dans transcript_agent_node: {str(e)}")
            return {
                "transcript_results": [],
                "messages": [HumanMessage(content=f"Erreur transcript agent: {str(e)}")]
            }
    
    def _web_search_agent_node(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Nœud web search agent - s'exécute en PARALLÈLE avec les autres agents.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            Dictionnaire partiel avec seulement web_search_results (pour éviter les conflits de fusion)
        """
        print(f"\n🌐 [PARALLÈLE-3/3] web_search_agent_node - DÉBUT")
        
        try:
            # Si les résultats sont pré-calculés, skip
            if state.get("skip_agents", False):
                print(f"⏩ [PARALLÈLE-3/3] Résultats pré-calculés - skip")
                return {}
            
            company_info = state.get("company_info", {})
            
            if company_info:
                company_name = company_info.get("company_name", "")
                if company_name:
                    print(f"🔄 [PARALLÈLE-3/3] Recherche web pour: {company_name}")
                    results = self.web_search_agent.search_company_info(company_name)
                    print(f"✅ [PARALLÈLE-3/3] Recherche web terminée")
                    print(f"✅ [PARALLÈLE-3/3] web_search_agent_node - FIN")
                    return {"web_search_results": results}
                else:
                    print(f"⚠️ [PARALLÈLE-3/3] Nom d'entreprise non fourni")
                    print(f"✅ [PARALLÈLE-3/3] web_search_agent_node - FIN")
                    return {"web_search_results": {}}
            else:
                print(f"⚠️ [PARALLÈLE-3/3] Aucune information entreprise fournie")
                print(f"✅ [PARALLÈLE-3/3] web_search_agent_node - FIN")
                return {"web_search_results": {}}
            
        except Exception as e:
            print(f"❌ [PARALLÈLE-3/3] Erreur dans web_search_agent_node: {str(e)}")
            return {
                "web_search_results": {},
                "messages": [HumanMessage(content=f"Erreur web search agent: {str(e)}")]
            }
    
    # ==================== ANCIEN NŒUD (LEGACY - conservé pour compatibilité) ====================
    
    def _start_agents_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de démarrage qui utilise les résultats pré-calculés ou lance les agents si nécessaire.
        NOUVELLE APPROCHE: Les résultats sont calculés dans Streamlit et passés directement.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        print(f"\n🚀 [DEBUG] _start_agents_node - DÉBUT")
        print(f"📊 État d'entrée: workshop_results={len(state.get('workshop_results', {}).get('workshops', []))}, transcript_results={len(state.get('transcript_results', []))}, web_search_results présent={bool(state.get('web_search_results', {}))}")
        
        try:
            # VÉRIFIER SI LES RÉSULTATS SONT DÉJÀ PRÉSENTS (calculés dans Streamlit)
            if state.get("workshop_results") or state.get("transcript_results") or state.get("web_search_results"):
                print(f"✅ [DEBUG] Résultats pré-calculés détectés - utilisation directe")
                print(f"📊 workshop_results: {len(state.get('workshop_results', {}).get('workshops', []))} workshops")
                print(f"📊 transcript_results: {len(state.get('transcript_results', []))} transcripts")
                print(f"📊 web_search_results: {len(state.get('web_search_results', {}))} recherches")
                
                # Les résultats sont déjà dans l'état, on les utilise directement
                # Pas besoin de relancer les agents
                print(f"✅ [DEBUG] _start_agents_node - FIN (résultats pré-calculés utilisés)")
                return state
            
            # SINON, lancer les agents (mode legacy / fichiers fournis)
            print(f"⚠️ [DEBUG] Aucun résultat pré-calculé - lancement des agents")
            workshop_files = state.get("workshop_files", [])
            transcript_files = state.get("transcript_files", [])
            company_info = state.get("company_info", {})
            
            # Workshop Agent
            if workshop_files:
                all_results = []
                for file_path in workshop_files:
                    file_results = self.workshop_agent.process_workshop_file(file_path)
                    all_results.extend(file_results)
                state["workshop_results"] = {"workshops": all_results}
            else:
                state["workshop_results"] = {}
                state["messages"] = state.get("messages", []) + [HumanMessage(content="Aucun fichier workshop fourni")]
            
            # Transcript Agent
            if transcript_files:
                results = self.transcript_agent.process_multiple_pdfs(transcript_files)
                state["transcript_results"] = results
            else:
                state["transcript_results"] = []
                state["messages"] = state.get("messages", []) + [HumanMessage(content="Aucun fichier transcript fourni")]
            
            # Web Search Agent
            if company_info:
                company_name = company_info.get("company_name", "")
                if company_name:
                    results = self.web_search_agent.search_company_info(company_name)
                    state["web_search_results"] = results
                else:
                    state["web_search_results"] = {}
                    state["messages"] = state.get("messages", []) + [HumanMessage(content="Nom d'entreprise non fourni")]
            else:
                state["web_search_results"] = {}
                state["messages"] = state.get("messages", []) + [HumanMessage(content="Aucune information entreprise fournie")]
            
            print(f"✅ [DEBUG] _start_agents_node - FIN")
            print(f"📊 Résultats: {len(state.get('workshop_results', {}).get('workshops', []))} workshops, {len(state.get('transcript_results', []))} transcripts, {len(state.get('web_search_results', {}))} recherches web")
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _start_agents_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur démarrage agents: {str(e)}")]
            return state
    
    
    def _collect_data_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud d'agrégation des données des 3 agents.
        NOUVEAU: Attend que les 3 agents parallèles aient terminé.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        print(f"\n📊 [CONVERGENCE] collect_data_node - DÉBUT")
        print(f"🔄 Mode dev: {self.dev_mode}")
        print(f"📊 Résultats des agents parallèles:")
        print(f"   • workshop_results: {len(state.get('workshop_results', {}).get('workshops', []))} workshops")
        print(f"   • transcript_results: {len(state.get('transcript_results', {}).get('results', []) if isinstance(state.get('transcript_results', {}), dict) else state.get('transcript_results', []))} transcripts")
        print(f"   • web_search_results: {bool(state.get('web_search_results', {}))}")
        
        try:
            if self.dev_mode:
                # Mode développement - charger les données mockées
                import json
                try:
                    # Charger les données mockées avec gestion d'erreur robuste
                    with open('/home/addeche/aiko/aikoGPT/workshop_results.json', 'r', encoding='utf-8') as f:
                        workshop_data = json.load(f)
                    
                    # Charger transcript_results avec gestion des caractères de contrôle
                    try:
                        with open('/home/addeche/aiko/aikoGPT/transcript_results.json', 'r', encoding='utf-8') as f:
                            transcript_data = json.load(f)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ [DEBUG] Erreur parsing transcript_results.json: {e}")
                        # Essayer avec une approche plus robuste
                        with open('/home/addeche/aiko/aikoGPT/transcript_results.json', 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Nettoyer les caractères de contrôle
                            import re
                            content = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', content)
                            transcript_data = json.loads(content)
                    
                    with open('/home/addeche/aiko/aikoGPT/web_search_cousin_surgery.json', 'r', encoding='utf-8') as f:
                        web_search_data = json.load(f)
                    
                    # Agrégation des données mockées
                    # SIMPLIFICATION: Utiliser directement workshop_results au lieu de workshop_data
                    state["workshop_results"] = {"workshops": workshop_data}
                    
                    # OPTIMISATION: Ne garder que semantic_analysis dans transcript_data
                    # pour éviter le doublon avec interesting_parts
                    
                    # Extraire la liste "results" du dictionnaire transcript_data
                    transcript_results = transcript_data.get("results", [])
                    
                    filtered_transcripts = []
                    for transcript in transcript_results:
                        # Vérifier que transcript est bien un dictionnaire
                        if not isinstance(transcript, dict):
                            print(f"⚠️ [DEBUG] Transcript ignoré (type incorrect): {type(transcript)}")
                            continue
                        
                        filtered_transcript = {
                            "pdf_path": transcript.get("pdf_path"),
                            "status": transcript.get("status"),
                            "semantic_analysis": transcript.get("semantic_analysis", {})
                        }
                        filtered_transcripts.append(filtered_transcript)
                    
                    state["transcript_data"] = filtered_transcripts
                    
                    # Sauvegarder les résultats (web_search_data déjà sauvegardé plus haut)
                    state["transcript_results"] = transcript_data  # Garder la structure complète
                    state["web_search_results"] = web_search_data
                    
                    print(f"🔍 [DEBUG] Transcripts filtrés: {len(filtered_transcripts)} transcripts (semantic_analysis uniquement)")
                    
                except Exception as e:
                    state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur chargement données mockées: {str(e)}")]
                    return state
            else:
                # Mode normal - agrégation des résultats des 3 agents PARALLÈLES
                print(f"📊 [CONVERGENCE] Agrégation des résultats des agents parallèles")
                
                # SIMPLIFICATION: Utiliser directement workshop_results et web_search_results
                # Seule transformation nécessaire : filtrer transcript_data pour garder seulement semantic_analysis
                
                # OPTIMISATION: Ne garder que semantic_analysis dans transcript_data
                transcript_results_raw = state.get("transcript_results", {})
                
                print(f"🔍 [CONVERGENCE] Type de transcript_results_raw: {type(transcript_results_raw)}")
                if isinstance(transcript_results_raw, dict):
                    print(f"🔍 [CONVERGENCE] Clés du dictionnaire: {list(transcript_results_raw.keys())}")
                
                # Extraire la liste "results" si c'est un dictionnaire avec cette clé
                if isinstance(transcript_results_raw, dict) and "results" in transcript_results_raw:
                    transcript_results = transcript_results_raw.get("results", [])
                    print(f"✅ [CONVERGENCE] Extraction de la clé 'results': {len(transcript_results)} transcripts")
                elif isinstance(transcript_results_raw, list):
                    transcript_results = transcript_results_raw
                    print(f"✅ [CONVERGENCE] transcript_results est déjà une liste: {len(transcript_results)} éléments")
                else:
                    transcript_results = []
                    print(f"⚠️ [CONVERGENCE] Format inattendu, utilisation d'une liste vide")
                
                filtered_transcripts = []
                for transcript in transcript_results:
                    # Vérifier que transcript est bien un dictionnaire
                    if not isinstance(transcript, dict):
                        print(f"⚠️ [CONVERGENCE] Transcript ignoré (type incorrect): {type(transcript)}")
                        continue
                    
                    filtered_transcript = {
                        "pdf_path": transcript.get("pdf_path"),
                        "status": transcript.get("status"),
                        "semantic_analysis": transcript.get("semantic_analysis", {})
                    }
                    filtered_transcripts.append(filtered_transcript)
                
                state["transcript_data"] = filtered_transcripts
                
                print(f"🔍 [CONVERGENCE] Transcripts filtrés: {len(filtered_transcripts)} transcripts (semantic_analysis uniquement)")
            
            # Initialisation des compteurs
            state["iteration_count"] = 0
            state["max_iterations"] = 3
            
            print(f"✅ [CONVERGENCE] collect_data_node - FIN")
            print(f"📊 Données agrégées: {len(state.get('workshop_results', {}).get('workshops', []))} workshops, {len(state.get('transcript_data', []))} transcripts, recherche web={bool(state.get('web_search_results', {}))}")
            print(f"🎯 [CONVERGENCE] Les 3 agents parallèles ont terminé avec succès")
            
            return state
            
        except Exception as e:
            print(f"❌ [CONVERGENCE] Erreur dans collect_data_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur collecte données: {str(e)}")]
            return state
    
    def _analyze_needs_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud d'analyse des besoins.
        MODE DEV: Charge les besoins depuis un JSON au lieu de les générer.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        print(f"\n🔍 [DEBUG] _analyze_needs_node - DÉBUT")
        print(f"📊 Besoins déjà validés: {len(state.get('validated_needs', []))}")
        print(f"🔄 Itération: {state.get('iteration_count', 0)}/{state.get('max_iterations', 3)}")
        print(f"🔧 Mode dev: {self.dev_mode}")
        
        try:
            # Vérifier s'il y a des besoins déjà validés
            validated_count = len(state.get("validated_needs", []))
            remaining_needs = max(0, 10 - validated_count)
            
            if remaining_needs <= 0:
                # Tous les besoins sont validés
                print(f"✅ [DEBUG] Tous les besoins sont déjà validés ({validated_count})")
                state["identified_needs"] = []
                return state
            
            # MODE DEV: Charger les besoins depuis le JSON
            if self.dev_mode:
                print(f"🔧 [DEBUG] Mode dev activé - chargement des besoins depuis le JSON")
                try:
                    with open('/home/addeche/aiko/aikoGPT/need_analysis_results_mock.json', 'r', encoding='utf-8') as f:
                        mock_data = json.load(f)
                    
                    identified_needs = mock_data.get("identified_needs", [])
                    
                    # Limiter le nombre de besoins selon les besoins restants
                    if len(identified_needs) > remaining_needs:
                        identified_needs = identified_needs[:remaining_needs]
                    
                    state["identified_needs"] = identified_needs
                    
                    print(f"✅ [DEBUG] Besoins chargés depuis le JSON: {len(identified_needs)}")
                    print(f"📊 [DEBUG] Besoins identifiés: {len(identified_needs)}")
                    print(f"🎯 [DEBUG] Besoins validés total: {len(state.get('validated_needs', []))}")
                    
                    return state
                    
                except Exception as e:
                    print(f"❌ [DEBUG] Erreur lors du chargement du JSON: {str(e)}")
                    # Continuer en mode normal si le chargement échoue
            
            # MODE NORMAL: Génération des besoins avec l'IA
            print(f"🤖 [DEBUG] Mode normal - génération des besoins avec l'IA")
            
            # Analyse des besoins avec feedback si disponible
            user_feedback = state.get("user_feedback", "")
            rejected_needs = state.get("rejected_needs", [])
            previous_needs = state.get("identified_needs", [])
            iteration = state.get("iteration_count", 0) + 1
            
            if user_feedback or rejected_needs:
                print(f"\n🔄 Génération de {remaining_needs} nouvelles propositions...")
                if user_feedback:
                    print(f"💬 En tenant compte du feedback: {user_feedback}")
                if rejected_needs:
                    print(f"🚫 Besoins rejetés à éviter: {len(rejected_needs)}")
            
            # 💰 OPTIMISATION: Filtrer les quotes des previous_needs et rejected_needs pour économiser les tokens
            # Les quotes sont déjà dans workshop/transcript, pas besoin de les dupliquer au LLM
            previous_needs_light = None
            rejected_needs_light = None
            
            if iteration > 1 and previous_needs:
                previous_needs_light = [
                    {"id": need.get("id"), "theme": need.get("theme")}
                    for need in previous_needs
                ]
                print(f"💰 [OPTIMISATION] Previous needs allégés: {len(previous_needs)} besoins sans quotes")
            
            if iteration > 1 and rejected_needs:
                rejected_needs_light = [
                    {"id": need.get("id"), "theme": need.get("theme")}
                    for need in rejected_needs
                ]
                print(f"💰 [OPTIMISATION] Rejected needs allégés: {len(rejected_needs)} besoins sans quotes")
            
            analysis_result = self.need_analysis_agent.analyze_needs(
                workshop_data=state["workshop_results"],  # SIMPLIFICATION: utiliser directement workshop_results
                transcript_data=state["transcript_data"],
                web_search_data=state["web_search_results"],  # SIMPLIFICATION: utiliser directement web_search_results
                iteration=iteration,
                previous_needs=previous_needs_light,
                rejected_needs=rejected_needs_light,
                user_feedback=user_feedback,
                validated_needs_count=validated_count
            )
            
            if "error" in analysis_result:
                state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse: {analysis_result['error']}")]
                return state
            
            # Limiter le nombre de besoins générés
            identified_needs = analysis_result.get("identified_needs", [])
            if len(identified_needs) > remaining_needs:
                identified_needs = identified_needs[:remaining_needs]
            
            state["identified_needs"] = identified_needs
            
            print(f"✅ [DEBUG] _analyze_needs_node - FIN")
            print(f"📊 Besoins identifiés: {len(identified_needs)}")
            print(f"🎯 Besoins validés total: {len(state.get('validated_needs', []))}")
            
            # Affichage des coûts après l'analyse des besoins
            self._print_tracker_stats(agent_name="need_analysis")
            
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _analyze_needs_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse besoins: {str(e)}")]
            return state
    
    def _human_validation_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de validation humaine SIMPLIFIÉ.
        
        NOUVELLE ARCHITECTURE avec interrupts natifs :
        - Le workflow s'arrête AVANT ce nœud (interrupt_before)
        - L'API/Streamlit détecte que le workflow est en pause
        - Streamlit affiche l'interface de validation
        - L'utilisateur valide et renvoie le feedback
        - Le feedback est injecté dans l'état via l'API
        - Le workflow reprend et ce nœud traite le feedback
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour avec les besoins validés/rejetés
        """
        print(f"\n🛑 [INTERRUPT] human_validation_node - DÉBUT")
        print(f"📊 identified_needs: {len(state.get('identified_needs', []))}")
        print(f"📊 validated_needs existants: {len(state.get('validated_needs', []))}")
        
        try:
            # Vérifier si on a reçu le feedback (injecté par l'API)
            if "validation_result" in state and state["validation_result"]:
                print(f"✅ [RESUME] Feedback reçu via API")
                validation_data = state["validation_result"]
                
                # Traiter les résultats de validation
                existing_validated = state.get("validated_needs", [])
                newly_validated = validation_data.get("validated_needs", [])
                
                # Éviter les doublons
                existing_ids = [need.get("theme", "") for need in existing_validated]
                unique_newly_validated = [need for need in newly_validated if need.get("theme", "") not in existing_ids]
                
                state["validated_needs"] = existing_validated + unique_newly_validated
                
                # Même logique pour les rejets
                existing_rejected = state.get("rejected_needs", [])
                newly_rejected = validation_data.get("rejected_needs", [])
                
                existing_rejected_ids = [need.get("theme", "") for need in existing_rejected]
                unique_newly_rejected = [need for need in newly_rejected if need.get("theme", "") not in existing_rejected_ids]
                
                state["rejected_needs"] = existing_rejected + unique_newly_rejected
                state["user_feedback"] = validation_data.get("user_feedback", "")
                
                # Nettoyer le flag
                state["validation_result"] = {}
                
                print(f"📊 [RESUME] Besoins nouvellement validés: {len(unique_newly_validated)}")
                print(f"📊 [RESUME] Total besoins validés: {len(state['validated_needs'])}")
                print(f"▶️ [RESUME] Workflow continue...")
                
                return state
            else:
                # Première fois : le workflow va s'arrêter ici (interrupt_before)
                print(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                print(f"💡 [INTERRUPT] L'API détectera cet arrêt et Streamlit affichera l'interface")
                
                # Juste retourner l'état
                # Le workflow s'arrête automatiquement car interrupt_before
                return state
            
        except Exception as e:
            print(f"❌ [ERROR] Erreur dans human_validation_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur validation: {str(e)}")]
            return state
    
    def _check_success_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de vérification du succès.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            print(f"\n🔄 [DEBUG] _check_success_node - DÉBUT")
            
            # NE PAS vérifier workflow_paused ici car nous sommes APRÈS validation
            # Cette vérification empêchait le workflow de progresser
            
            # Vérification du succès
            validated_count = len(state.get("validated_needs", []))
            success = validated_count >= 5
            
            state["success"] = success
            
            print(f"📊 Besoins validés: {validated_count}/5")
            print(f"🎯 Succès: {success}")
            
            if not success:
                # Incrémenter le compteur d'itérations
                state["iteration_count"] = state.get("iteration_count", 0) + 1
                
                print(f"🔄 Itération {state['iteration_count']}/{state.get('max_iterations', 3)}")
                print(f"💬 Feedback: {state.get('user_feedback', 'Aucun')}")
            else:
                print(f"✅ Objectif atteint ! {validated_count} besoins validés")
            
            print(f"✅ [DEBUG] _check_success_node - FIN")
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _check_success_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur vérification: {str(e)}")]
            return state
    
    def _finalize_results_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de finalisation des résultats.
        VERSION CORRIGÉE: Utilise directement les besoins validés.
        MODE DEV: Charge les besoins depuis need_analysis_results.json si disponible.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            print(f"\n🔍 [DEBUG] _finalize_results_node - DÉBUT")
            print(f"🔧 [DEBUG] Mode dev: {self.dev_mode}")
            print(f"📊 [DEBUG] validation_result présent: {'validation_result' in state}")
            print(f"📊 [DEBUG] validated_needs dans state: {len(state.get('validated_needs', []))}")
            
            # MODE DEV: Charger les besoins depuis le JSON si disponible
            if self.dev_mode:
                try:
                    print(f"🔧 [DEBUG] Mode dev activé - tentative de chargement depuis need_analysis_results.json")
                    with open('/home/addeche/aiko/aikoGPT/need_analysis_results.json', 'r', encoding='utf-8') as f:
                        need_data = json.load(f)
                    
                    final_needs = need_data.get("final_needs", [])
                    if final_needs:
                        state["final_needs"] = final_needs
                        print(f"✅ [DEBUG] Besoins chargés depuis le JSON: {len(final_needs)}")
                        
                        # Debug: Afficher les thèmes des besoins
                        print(f"📋 [DEBUG] Thèmes des besoins validés:")
                        for i, need in enumerate(final_needs, 1):
                            print(f"   {i}. {need.get('theme', 'N/A')}")
                        
                        # Sauvegarde des résultats
                        self._save_results(state)
                        
                        print(f"✅ [DEBUG] _finalize_results_node - FIN")
                        return state
                except Exception as e:
                    print(f"⚠️ [DEBUG] Erreur lors du chargement du JSON: {str(e)}")
                    # Continuer en mode normal si le chargement échoue
            
            # MODE NORMAL: Utiliser directement les besoins validés depuis l'état
            validated_needs = state.get("validated_needs", [])
            
            # Si pas de besoins validés dans l'état, essayer depuis validation_result
            if not validated_needs and "validation_result" in state and state["validation_result"]:
                validation_result = state["validation_result"]
                validated_needs = validation_result.get("validated_needs", [])
                print(f"📊 [DEBUG] Besoins récupérés depuis validation_result: {len(validated_needs)}")
            
            # Si toujours pas de besoins, utiliser tous les besoins identifiés
            if not validated_needs:
                validated_needs = state.get("identified_needs", [])
                print(f"📊 [DEBUG] Utilisation de tous les besoins identifiés: {len(validated_needs)}")
            
            state["final_needs"] = validated_needs
            print(f"📊 [DEBUG] Final needs définis: {len(validated_needs)}")
            
            # Debug: Afficher les thèmes des besoins
            if validated_needs:
                print(f"📋 [DEBUG] Thèmes des besoins validés:")
                for i, need in enumerate(validated_needs, 1):
                    print(f"   {i}. {need.get('theme', 'N/A')}")
            
            # Sauvegarde des résultats
            self._save_results(state)
            
            print(f"✅ [DEBUG] _finalize_results_node - FIN")
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _finalize_results_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur finalisation: {str(e)}")]
            return state
    
    def _should_continue(self, state: WorkflowState) -> str:
        """
        Détermine si le workflow doit continuer.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            Direction à prendre
        """
        if state.get("success", False):
            return "success"
        
        if state.get("iteration_count", 0) >= state.get("max_iterations", 3):
            return "max_iterations"
        
        return "continue"
    
    def _save_results(self, state: WorkflowState) -> None:
        """
        Sauvegarde les résultats dans le dossier outputs.
        
        Args:
            state: État final du workflow
        """
        try:
            from datetime import datetime
            # Sauvegarde des besoins finaux
            results = {
                "final_needs": state.get("final_needs", []),
                "success": state.get("success", False),
                "iteration_count": state.get("iteration_count", 0),
                "timestamp": datetime.now().isoformat()
            }
            
            # Sauvegarde en JSON
            output_path = "/home/addeche/aiko/aikoGPT/outputs/need_analysis_results.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # Génération du graph PNG
            self._generate_graph_png()
            
        except Exception as e:
            print(f"Erreur sauvegarde: {str(e)}")
    
    def _generate_graph_png(self) -> None:
        """
        Génère et sauvegarde le graph du workflow en PNG en utilisant LangGraph.
        """
        try:
            # Utilisation de la méthode LangGraph pour générer le graph
            png = self.graph.get_graph().draw_mermaid_png()
            
            # Sauvegarde du PNG
            output_path = "/home/addeche/aiko/aikoGPT/outputs/workflow_graph.png"
            with open(output_path, 'wb') as f:
                f.write(png)
            
        except Exception as e:
            print(f"Erreur génération graph: {str(e)}")
    
    def run(self, workshop_files: List[str] = None, transcript_files: List[str] = None, company_info: Dict[str, Any] = None, 
            workshop_results: Dict[str, Any] = None, transcript_results: List[Dict[str, Any]] = None, web_search_results: Dict[str, Any] = None,
            thread_id: str = None) -> Dict[str, Any]:
        """
        Exécute le workflow complet.
        NOUVELLE ARCHITECTURE: Exécution MANUELLE des nœuds jusqu'à human_validation.
        MODE DEV: Charge les besoins depuis need_analysis_results.json et passe directement aux use cases.
        
        Args:
            workshop_files: Liste des fichiers Excel des ateliers (legacy)
            transcript_files: Liste des fichiers PDF des transcriptions (legacy)
            company_info: Informations sur l'entreprise pour la recherche web
            workshop_results: Résultats pré-calculés du workshop agent (NOUVEAU)
            transcript_results: Résultats pré-calculés du transcript agent (NOUVEAU)
            web_search_results: Résultats pré-calculés du web search agent (NOUVEAU)
            thread_id: ID du thread pour le checkpointer (optionnel, généré automatiquement si non fourni)
            
        Returns:
            Résultats du workflow
        """
        print(f"\n🚀 [DEBUG] run() appelé - NOUVELLE ARCHITECTURE")
        print(f"🔧 [DEBUG] Mode dev: {self.dev_mode}")
        print(f"📊 [DEBUG] Résultats pré-calculés: workshop={bool(workshop_results)}, transcript={bool(transcript_results)}, web_search={bool(web_search_results)}")
        print(f"🔑 [DEBUG] Thread ID fourni: {thread_id}")
        
        try:
            # État initial avec les fichiers d'entrée ET les résultats pré-calculés
            state = WorkflowState(
                messages=[],
                # Fichiers d'entrée (legacy)
                workshop_files=workshop_files or [],
                transcript_files=transcript_files or [],
                company_info=company_info or {},
                # Résultats des agents (pré-calculés OU vides)
                workshop_results=workshop_results or {},
                transcript_results=transcript_results or [],
                web_search_results=web_search_results or {},
                # Flag pour parallélisation
                skip_agents=False,
                # Données agrégées (seulement transcript_data car transformation utile)
                transcript_data=[],
                # Résultats de l'analyse des besoins
                identified_needs=[],
                # Validation humaine des besoins
                validated_needs=[],
                rejected_needs=[],
                user_feedback="",
                validation_result={},
                # État du workflow des besoins
                final_needs=[],
                success=False,
                iteration_count=0,
                max_iterations=3,
                workflow_paused=False,
                # Résultats de l'analyse des use cases
                proposed_quick_wins=[],
                proposed_structuration_ia=[],
                # Validation humaine des use cases
                validated_quick_wins=[],
                validated_structuration_ia=[],
                rejected_quick_wins=[],
                rejected_structuration_ia=[],
                use_case_user_feedback="",
                use_case_validation_result={},
                # État du workflow des use cases
                final_quick_wins=[],
                final_structuration_ia=[],
                use_case_success=False,
                use_case_iteration=0,
                max_use_case_iterations=3,
                use_case_workflow_paused=False
            )
            
            # MODE DEV: Vérifier si need_analysis_results.json existe
            if self.dev_mode:
                try:
                    print(f"🔧 [DEBUG] Mode dev activé - tentative de chargement depuis need_analysis_results.json")
                    with open('/home/addeche/aiko/aikoGPT/need_analysis_results.json', 'r', encoding='utf-8') as f:
                        need_data = json.load(f)
                    
                    final_needs = need_data.get("final_needs", [])
                    if final_needs:
                        print(f"✅ [DEBUG] Besoins chargés depuis le JSON: {len(final_needs)}")
                        
                        # Charger les données mockées pour le contexte
                        state = self._collect_data_node(state)
                        
                        # Définir les besoins finaux et marquer comme succès
                        state["final_needs"] = final_needs
                        state["validated_needs"] = final_needs
                        state["success"] = True
                        
                        # PASSER DIRECTEMENT À L'ANALYSE DES USE CASES
                        print(f"🚀 [DEBUG] Passage direct à l'analyse des use cases")
                        
                        # Analyser les use cases
                        state = self._analyze_use_cases_node(state)
                        
                        # Afficher l'interface de validation des use cases
                        state = self._validate_use_cases_node(state)
                        
                        print(f"⏸️ [DEBUG] Workflow en pause - en attente de validation des use cases")
                        
                        # Retourner un état "en pause" pour les use cases
                        return {
                            "success": False,
                            "final_needs": final_needs,
                            "summary": {
                                "total_needs": len(final_needs),
                                "themes": [need.get("theme", "") for need in final_needs],
                            },
                            "iteration_count": state.get("iteration_count", 0),
                            "workshop_results": state.get("workshop_results", {}),
                            "transcript_results": state.get("transcript_results", []),
                            "web_search_results": state.get("web_search_results", {}),
                            "messages": ["Workflow en pause - en attente de validation des use cases"]
                        }
                        
                except FileNotFoundError:
                    print(f"⚠️ [DEBUG] Fichier need_analysis_results.json non trouvé - exécution normale")
                    # Continuer en mode normal
                except Exception as e:
                    print(f"⚠️ [DEBUG] Erreur lors du chargement du JSON: {str(e)}")
                    # Continuer en mode normal
            
            # MODE NORMAL: Exécution standard AVEC PARALLÉLISATION
            print(f"🔄 [DEBUG] Exécution avec PARALLÉLISATION des agents...")
            
            # NOUVEAU: Utiliser le graphe compilé pour bénéficier de la parallélisation
            # Le graphe va exécuter : dispatcher → 3 agents en parallèle → collect_data → analyze_needs → human_validation (STOP)
            
            # Utiliser le thread_id fourni ou en générer un nouveau
            if thread_id is None:
                import uuid
                thread_id = str(uuid.uuid4())
                print(f"🔑 [DEBUG] Thread ID généré automatiquement: {thread_id}")
            
            config = {"configurable": {"thread_id": thread_id}}
            
            # Exécuter le workflow jusqu'à l'interrupt (human_validation)
            print(f"🚀 [DEBUG] Exécution du graphe avec thread_id: {thread_id}")
            
            # Le workflow va s'arrêter à human_validation car c'est défini dans interrupt_before
            final_state = None
            for chunk in self.graph.stream(state, config):
                print(f"📊 [DEBUG] Chunk reçu: {list(chunk.keys())}")
                # Chaque chunk contient l'état mis à jour par un nœud
                for node_name, node_state in chunk.items():
                    print(f"  • Nœud '{node_name}' exécuté")
                    final_state = node_state
            
            # Le workflow s'est arrêté à human_validation
            print(f"⏸️ [DEBUG] Workflow arrêté avant human_validation - en attente de validation")
            
            # IMPORTANT : Récupérer l'état complet depuis le checkpointer après l'interrupt
            # car le dernier chunk (__interrupt__) ne contient pas l'état complet
            snapshot = self.graph.get_state(config)
            state = snapshot.values
            
            print(f"📊 [DEBUG] État récupéré depuis le checkpointer:")
            print(f"📊 [DEBUG] Besoins identifiés: {len(state.get('identified_needs', []))}")
            print(f"📊 [DEBUG] Besoins validés: {len(state.get('validated_needs', []))}")
            
            # Retourner un état "en pause" AVEC les besoins identifiés
            return {
                "success": False,
                "workflow_paused": True,  # ← AJOUTÉ
                "identified_needs": state.get("identified_needs", []),  # ← AJOUTÉ
                "validated_needs": state.get("validated_needs", []),  # ← AJOUTÉ
                "final_needs": [],
                "summary": {
                    "total_needs": 0,
                    "themes": [],
                },
                "iteration_count": state.get("iteration_count", 0),
                "workshop_results": state.get("workshop_results", {}),
                "transcript_results": state.get("transcript_results", []),
                "web_search_results": state.get("web_search_results", {}),
                "messages": ["Workflow en pause - en attente de validation"]
            }
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans run(): {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "final_needs": [],
                "iteration_count": 0,
                "messages": [f"Erreur workflow: {str(e)}"]
            }
    
    # Fonction resume_workflow supprimée - était spécifique à Streamlit
    def resume_workflow_removed(self) -> Dict[str, Any]:
        """
        FONCTION SUPPRIMÉE - était spécifique à Streamlit.
        La validation humaine se fait maintenant via l'API FastAPI.
        """
        return {
            "success": False,
            "error": "Fonction supprimée - utilisez l'API FastAPI pour la validation",
            "final_needs": [],
            "iteration_count": 0,
            "messages": ["Fonction obsolète"]
        }
    
    # ==================== NOUVEAUX NŒUDS POUR L'ANALYSE DES USE CASES ====================
    
    def _analyze_use_cases_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud d'analyse des cas d'usage IA à partir des besoins validés.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        print(f"\n🔬 [DEBUG] _analyze_use_cases_node - DÉBUT")
        print(f"📊 Besoins validés en entrée: {len(state.get('final_needs', []))}")
        
        try:
            # Initialiser les compteurs si première itération
            if "use_case_iteration" not in state:
                state["use_case_iteration"] = 0
                state["max_use_case_iterations"] = 3
                state["validated_quick_wins"] = []
                state["validated_structuration_ia"] = []
                state["rejected_quick_wins"] = []
                state["rejected_structuration_ia"] = []
            
            # Incrémenter l'itération au début de l'analyse
            state["use_case_iteration"] = state.get("use_case_iteration", 0) + 1
            
            print(f"🔄 Itération use case: {state.get('use_case_iteration', 0)}/{state.get('max_use_case_iterations', 3)}")
            
            # Récupérer les besoins validés
            validated_needs = state.get("final_needs", [])
            
            if not validated_needs:
                print(f"⚠️ [DEBUG] Aucun besoin validé trouvé")
                state["proposed_quick_wins"] = []
                state["proposed_structuration_ia"] = []
                return state
            
            # Calculer les cas d'usage déjà validés
            validated_qw_count = len(state.get("validated_quick_wins", []))
            validated_sia_count = len(state.get("validated_structuration_ia", []))
            
            print(f"📊 [DEBUG] Quick Wins validés: {validated_qw_count}/5")
            print(f"📊 [DEBUG] Structuration IA validés: {validated_sia_count}/5")
            
            # Préparer les données pour la génération
            iteration = state.get("use_case_iteration", 1)
            previous_use_cases = None
            rejected_quick_wins = state.get("rejected_quick_wins", [])
            rejected_structuration_ia = state.get("rejected_structuration_ia", [])
            user_feedback = state.get("use_case_user_feedback", "")
            
            if iteration > 1:
                # Régénération avec feedback
                previous_use_cases = {
                    "quick_wins": state.get("proposed_quick_wins", []),
                    "structuration_ia": state.get("proposed_structuration_ia", [])
                }
                
                if user_feedback:
                    print(f"💬 [DEBUG] Commentaires utilisateur : {user_feedback[:100]}...")
                if rejected_quick_wins:
                    print(f"🚫 [DEBUG] Quick Wins rejetés à éviter : {len(rejected_quick_wins)}")
                if rejected_structuration_ia:
                    print(f"🚫 [DEBUG] Structuration IA rejetés à éviter : {len(rejected_structuration_ia)}")
            
            # Récupérer les données sources pour enrichir le contexte
            # SIMPLIFICATION: Utiliser directement les résultats au lieu des copies
            workshop_results = state.get("workshop_results", {})
            transcript_data = state.get("transcript_data", [])
            web_search_results = state.get("web_search_results", {})
            
            print(f"🔍 [DEBUG] Données de contexte: {len(workshop_results.get('workshops', []))} workshops, "
                  f"{len(transcript_data)} transcripts, web_search présent={bool(web_search_results)}")
            
            # 💰 OPTIMISATION: Filtrer les quotes des validated_needs pour économiser les tokens
            # Les quotes sont déjà dans workshop/transcript, pas besoin de les dupliquer au LLM
            validated_needs_light = [
                {"id": need.get("id"), "theme": need.get("theme"), "description": need.get("description", "")}
                for need in validated_needs
            ]
            print(f"💰 [OPTIMISATION] Validated needs allégés: {len(validated_needs)} besoins sans quotes")
            
            # Appeler l'agent d'analyse des use cases avec les données de contexte
            print(f"🤖 [DEBUG] Appel à l'agent d'analyse des use cases")
            result = self.use_case_analysis_agent.analyze_use_cases(
                validated_needs=validated_needs_light,
                workshop_data=workshop_results,
                transcript_data=transcript_data,
                web_search_data=web_search_results,
                iteration=iteration,
                previous_use_cases=previous_use_cases,
                rejected_quick_wins=rejected_quick_wins if iteration > 1 else None,
                rejected_structuration_ia=rejected_structuration_ia if iteration > 1 else None,
                user_feedback=user_feedback,
                validated_quick_wins_count=validated_qw_count,
                validated_structuration_ia_count=validated_sia_count
            )
            
            if "error" in result:
                print(f"❌ [DEBUG] Erreur lors de l'analyse: {result['error']}")
                state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse use cases: {result['error']}")]
                return state
            
            # Mettre à jour l'état avec les résultats
            state["proposed_quick_wins"] = result.get("quick_wins", [])
            state["proposed_structuration_ia"] = result.get("structuration_ia", [])
            
            print(f"✅ [DEBUG] _analyze_use_cases_node - FIN")
            print(f"📊 Quick Wins proposés: {len(state['proposed_quick_wins'])}")
            print(f"📊 Structuration IA proposés: {len(state['proposed_structuration_ia'])}")
            
            # Affichage des coûts après l'analyse des cas d'usage
            self._print_tracker_stats(agent_name="use_case_analysis")
            
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _analyze_use_cases_node: {str(e)}")
            import traceback
            traceback.print_exc()
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse use cases: {str(e)}")]
            return state
    
    def _validate_use_cases_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de validation humaine des cas d'usage SIMPLIFIÉ.
        
        NOUVELLE ARCHITECTURE avec interrupts natifs :
        - Le workflow s'arrête AVANT ce nœud (interrupt_before)
        - L'API/Streamlit détecte que le workflow est en pause
        - Streamlit affiche l'interface de validation des use cases
        - L'utilisateur valide et renvoie le feedback
        - Le feedback est injecté dans l'état via l'API
        - Le workflow reprend et ce nœud traite le feedback
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour avec les use cases validés/rejetés
        """
        print(f"\n🛑 [INTERRUPT] validate_use_cases_node - DÉBUT")
        print(f"📊 Quick Wins proposés: {len(state.get('proposed_quick_wins', []))}")
        print(f"📊 Structuration IA proposés: {len(state.get('proposed_structuration_ia', []))}")
        print(f"📊 Quick Wins validés existants: {len(state.get('validated_quick_wins', []))}")
        print(f"📊 Structuration IA validés existants: {len(state.get('validated_structuration_ia', []))}")
        
        try:
            # Vérifier si on a reçu le feedback (injecté par l'API)
            if "use_case_validation_result" in state and state["use_case_validation_result"]:
                print(f"✅ [RESUME] Feedback use cases reçu via API")
                validation_data = state["use_case_validation_result"]
                
                # Traiter les résultats de validation
                existing_qw = state.get("validated_quick_wins", [])
                newly_validated_qw = validation_data.get("validated_quick_wins", [])
                
                existing_sia = state.get("validated_structuration_ia", [])
                newly_validated_sia = validation_data.get("validated_structuration_ia", [])
                
                # Éviter les doublons
                existing_qw_ids = [uc.get("titre", "") for uc in existing_qw]
                unique_qw = [uc for uc in newly_validated_qw if uc.get("titre", "") not in existing_qw_ids]
                
                existing_sia_ids = [uc.get("titre", "") for uc in existing_sia]
                unique_sia = [uc for uc in newly_validated_sia if uc.get("titre", "") not in existing_sia_ids]
                
                state["validated_quick_wins"] = existing_qw + unique_qw
                state["validated_structuration_ia"] = existing_sia + unique_sia
                
                # Même chose pour les rejetés
                existing_rejected_qw = state.get("rejected_quick_wins", [])
                newly_rejected_qw = validation_data.get("rejected_quick_wins", [])
                state["rejected_quick_wins"] = existing_rejected_qw + newly_rejected_qw
                
                existing_rejected_sia = state.get("rejected_structuration_ia", [])
                newly_rejected_sia = validation_data.get("rejected_structuration_ia", [])
                state["rejected_structuration_ia"] = existing_rejected_sia + newly_rejected_sia
                
                state["use_case_user_feedback"] = validation_data.get("user_feedback", "")
                
                # Nettoyer le flag
                state["use_case_validation_result"] = {}
                
                print(f"📊 [RESUME] Quick Wins nouvellement validés: {len(unique_qw)}")
                print(f"📊 [RESUME] Structuration IA nouvellement validés: {len(unique_sia)}")
                print(f"📊 [RESUME] Total Quick Wins validés: {len(state['validated_quick_wins'])}")
                print(f"📊 [RESUME] Total Structuration IA validés: {len(state['validated_structuration_ia'])}")
                print(f"▶️ [RESUME] Workflow continue...")
                
                return state
            else:
                # Première fois : le workflow va s'arrêter ici (interrupt_before)
                print(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                print(f"💡 [INTERRUPT] L'API détectera cet arrêt et Streamlit affichera l'interface")
                
                # Juste retourner l'état
                # Le workflow s'arrête automatiquement car interrupt_before
                return state
            
        except Exception as e:
            print(f"❌ [ERROR] Erreur dans validate_use_cases_node: {str(e)}")
            import traceback
            traceback.print_exc()
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur validation use cases: {str(e)}")]
            return state
    
    def _check_use_case_success_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de vérification du succès de la validation des use cases.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            print(f"\n🔄 [DEBUG] _check_use_case_success_node - DÉBUT")
            
            # Vérification du succès
            validated_qw_count = len(state.get("validated_quick_wins", []))
            validated_sia_count = len(state.get("validated_structuration_ia", []))
            
            success = self.use_case_analysis_agent.check_validation_success(
                validated_qw_count,
                validated_sia_count
            )
            
            state["use_case_success"] = success
            
            print(f"📊 Quick Wins validés: {validated_qw_count}/5")
            print(f"📊 Structuration IA validés: {validated_sia_count}/5")
            print(f"🎯 Succès: {success}")
            
            if not success:
                # L'incrémentation est maintenant faite au début de _analyze_use_cases_node
                print(f"🔄 Itération {state['use_case_iteration']}/{state.get('max_use_case_iterations', 3)}")
                print(f"💬 Feedback: {state.get('use_case_user_feedback', 'Aucun')}")
            else:
                print(f"✅ Objectif atteint ! {validated_qw_count} Quick Wins et {validated_sia_count} Structuration IA validés")
            
            print(f"✅ [DEBUG] _check_use_case_success_node - FIN")
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _check_use_case_success_node: {str(e)}")
            import traceback
            traceback.print_exc()
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur vérification use cases: {str(e)}")]
            return state
    
    def _finalize_use_cases_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de finalisation des cas d'usage.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            print(f"\n🔍 [DEBUG] _finalize_use_cases_node - DÉBUT")
            print(f"📊 [DEBUG] Quick Wins validés: {len(state.get('validated_quick_wins', []))}")
            print(f"📊 [DEBUG] Structuration IA validés: {len(state.get('validated_structuration_ia', []))}")
            
            # Utiliser directement les cas d'usage validés depuis l'état
            validated_qw = state.get("validated_quick_wins", [])
            validated_sia = state.get("validated_structuration_ia", [])
            
            state["final_quick_wins"] = validated_qw
            state["final_structuration_ia"] = validated_sia
            
            print(f"📊 [DEBUG] Final Quick Wins définis: {len(validated_qw)}")
            print(f"📊 [DEBUG] Final Structuration IA définis: {len(validated_sia)}")
            
            # Debug: Afficher les titres des cas d'usage
            if validated_qw:
                print(f"📋 [DEBUG] Titres des Quick Wins validés:")
                for i, uc in enumerate(validated_qw, 1):
                    print(f"   {i}. {uc.get('titre', 'N/A')}")
            
            if validated_sia:
                print(f"📋 [DEBUG] Titres des Structuration IA validés:")
                for i, uc in enumerate(validated_sia, 1):
                    print(f"   {i}. {uc.get('titre', 'N/A')}")
            
            # Sauvegarde des résultats
            self._save_use_case_results(state)
            
            print(f"✅ [DEBUG] _finalize_use_cases_node - FIN")
            
            # Affichage du rapport final des coûts
            print("\n" + "="*70)
            print("📊 RAPPORT FINAL DES COÛTS")
            print("="*70)
            self.tracker.print_summary()
            
            # Sauvegarde du rapport de tracking
            report_path = self.tracker.save_report()
            print(f"📄 Rapport de coûts sauvegardé: {report_path}\n")
            
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _finalize_use_cases_node: {str(e)}")
            import traceback
            traceback.print_exc()
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur finalisation use cases: {str(e)}")]
            return state
    
    def _should_continue_use_cases(self, state: WorkflowState) -> str:
        """
        Détermine si le workflow des use cases doit continuer.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            Direction à prendre
        """
        if state.get("use_case_success", False):
            return "success"
        
        if state.get("use_case_iteration", 0) >= state.get("max_use_case_iterations", 3):
            return "max_iterations"
        
        return "continue"
    
    def _save_use_case_results(self, state: WorkflowState) -> None:
        """
        Sauvegarde les résultats des cas d'usage dans le dossier outputs.
        
        Args:
            state: État final du workflow
        """
        try:
            from datetime import datetime
            # Sauvegarde des cas d'usage finaux
            results = {
                "final_quick_wins": state.get("final_quick_wins", []),
                "final_structuration_ia": state.get("final_structuration_ia", []),
                "use_case_success": state.get("use_case_success", False),
                "use_case_iteration": state.get("use_case_iteration", 0),
                "timestamp": datetime.now().isoformat(),
                # Inclure aussi les besoins pour référence
                "source_needs": state.get("final_needs", [])
            }
            
            # Sauvegarde en JSON
            output_path = "/home/addeche/aiko/aikoGPT/outputs/use_case_analysis_results.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"💾 [DEBUG] Résultats sauvegardés dans {output_path}")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde use cases: {str(e)}")
    
    def resume_workflow_with_feedback(self, validated_needs: List[Dict[str, Any]], 
                                       rejected_needs: List[Dict[str, Any]], 
                                       user_feedback: str,
                                       thread_id: str) -> Dict[str, Any]:
        """
        Reprend le workflow après validation humaine avec le feedback.
        NOUVELLE VERSION pour architecture API avec LangGraph checkpointer.
        
        Args:
            validated_needs: Besoins validés par l'utilisateur
            rejected_needs: Besoins rejetés par l'utilisateur
            user_feedback: Commentaires de l'utilisateur
            thread_id: ID du thread pour récupérer l'état depuis le checkpointer
        
        Returns:
            Résultats du workflow
        """
        print(f"\n🔄 [API] resume_workflow_with_feedback() appelé")
        print(f"✅ Validés: {len(validated_needs)}")
        print(f"❌ Rejetés: {len(rejected_needs)}")
        print(f"💬 Feedback: {user_feedback[:100] if user_feedback else 'Aucun'}")
        print(f"🔑 Thread ID: {thread_id}")
        
        try:
            # Configuration pour récupérer l'état depuis le checkpointer
            config = {"configurable": {"thread_id": thread_id}}
            
            # Récupérer l'état actuel depuis le checkpointer
            snapshot = self.graph.get_state(config)
            state = snapshot.values
            
            print(f"📊 [API] État récupéré depuis le checkpointer")
            print(f"📊 [API] Besoins identifiés: {len(state.get('identified_needs', []))}")
            print(f"📊 [API] Besoins déjà validés: {len(state.get('validated_needs', []))}")
            
            # Créer le résultat de validation
            validation_result = {
                "validated_needs": validated_needs,
                "rejected_needs": rejected_needs,
                "user_feedback": user_feedback
            }
            
            # Mettre à jour l'état avec le feedback de validation
            self.graph.update_state(
                config,
                {
                    "validation_result": validation_result
                }
            )
            
            print(f"✅ [API] État mis à jour avec le feedback de validation")
            
            # Reprendre l'exécution du workflow
            print(f"▶️ [API] Reprise du workflow...")
            
            final_state = None
            for chunk in self.graph.stream(None, config):
                print(f"📊 [API] Chunk reçu: {list(chunk.keys())}")
                for node_name, node_state in chunk.items():
                    print(f"  • Nœud '{node_name}' exécuté")
                    final_state = node_state
            
            # Récupérer l'état final depuis le checkpointer
            snapshot = self.graph.get_state(config)
            state = snapshot.values
            
            print(f"📊 [API] Workflow terminé ou en pause")
            print(f"📊 [API] Next nodes: {snapshot.next}")
            
            # Vérifier si le workflow est terminé ou en pause
            # Note: snapshot.next peut être une liste ou un tuple
            next_nodes = list(snapshot.next) if snapshot.next else []
            
            if len(next_nodes) == 0:
                # Workflow terminé
                print(f"✅ [API] Workflow terminé avec succès")
                return {
                    "success": True,
                    "final_needs": state.get("final_needs", []),
                    "summary": {
                        "total_needs": len(state.get("final_needs", [])),
                        "themes": list(set([need.get("theme", "") for need in state.get("final_needs", []) if need.get("theme")])),
                    },
                    "iteration_count": state.get("iteration_count", 0),
                    "workshop_results": state.get("workshop_results", {}),
                    "transcript_results": state.get("transcript_results", []),
                    "web_search_results": state.get("web_search_results", {}),
                    "messages": ["Phase 1 terminée - transition vers Phase 2"]
                }
            elif "human_validation" in next_nodes:
                # En attente d'une nouvelle validation
                print(f"⏸️ [API] Workflow en pause - nouvelle validation requise")
                return {
                    "success": False,
                    "workflow_paused": True,
                    "identified_needs": state.get("identified_needs", []),
                    "validated_needs": state.get("validated_needs", []),
                    "final_needs": [],
                    "summary": {
                        "total_needs": 0,
                        "themes": [],
                    },
                    "iteration_count": state.get("iteration_count", 0),
                    "workshop_results": state.get("workshop_results", {}),
                    "transcript_results": state.get("transcript_results", []),
                    "web_search_results": state.get("web_search_results", {}),
                    "messages": ["Nouvelle validation requise"]
                }
            elif "validate_use_cases" in next_nodes:
                # Transition vers validation des use cases
                print(f"⏸️ [API] Workflow en pause - validation des use cases requise")
                return {
                    "success": False,
                    "workflow_paused": True,
                    "use_case_workflow_paused": True,
                    "final_needs": state.get("final_needs", []),
                    "proposed_quick_wins": state.get("proposed_quick_wins", []),
                    "proposed_structuration_ia": state.get("proposed_structuration_ia", []),
                    "summary": {
                        "total_needs": len(state.get("final_needs", [])),
                        "themes": list(set([need.get("theme", "") for need in state.get("final_needs", []) if need.get("theme")])),
                    },
                    "iteration_count": state.get("iteration_count", 0),
                    "workshop_results": state.get("workshop_results", {}),
                    "transcript_results": state.get("transcript_results", []),
                    "web_search_results": state.get("web_search_results", {}),
                    "messages": ["Phase 1 terminée - validation des use cases requise"]
                }
            else:
                # Autre cas
                print(f"⚠️ [API] État inattendu: {next_nodes}")
                return {
                    "success": False,
                    "error": f"État inattendu: {next_nodes}",
                    "final_needs": [],
                    "iteration_count": state.get("iteration_count", 0),
                    "messages": [f"État inattendu: {next_nodes}"]
                }
        
        except Exception as e:
            print(f"❌ [API] Erreur dans resume_workflow_with_feedback(): {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "final_needs": [],
                "iteration_count": 0,
                "messages": [f"Erreur reprise workflow: {str(e)}"]
            }
    
    def resume_use_case_workflow_with_feedback(self, validated_quick_wins: List[Dict[str, Any]],
                                                validated_structuration_ia: List[Dict[str, Any]],
                                                rejected_quick_wins: List[Dict[str, Any]],
                                                rejected_structuration_ia: List[Dict[str, Any]],
                                                user_feedback: str,
                                                thread_id: str) -> Dict[str, Any]:
        """
        Reprend le workflow après validation des use cases avec le feedback.
        NOUVELLE VERSION pour architecture API avec LangGraph checkpointer.
        
        Args:
            validated_quick_wins: Quick Wins validés
            validated_structuration_ia: Structuration IA validés
            rejected_quick_wins: Quick Wins rejetés
            rejected_structuration_ia: Structuration IA rejetés
            user_feedback: Commentaires de l'utilisateur
            thread_id: ID du thread pour récupérer l'état depuis le checkpointer
        
        Returns:
            Résultats finaux du workflow
        """
        print(f"\n🔄 [API] resume_use_case_workflow_with_feedback() appelé")
        print(f"✅ Quick Wins validés: {len(validated_quick_wins)}")
        print(f"✅ Structuration IA validés: {len(validated_structuration_ia)}")
        print(f"🔑 Thread ID: {thread_id}")
        
        try:
            # Configuration pour récupérer l'état depuis le checkpointer
            config = {"configurable": {"thread_id": thread_id}}
            
            # Récupérer l'état actuel depuis le checkpointer
            snapshot = self.graph.get_state(config)
            state = snapshot.values
            
            print(f"📊 [API] État récupéré depuis le checkpointer")
            print(f"📊 [API] Quick Wins proposés: {len(state.get('proposed_quick_wins', []))}")
            print(f"📊 [API] Structuration IA proposés: {len(state.get('proposed_structuration_ia', []))}")
            print(f"📊 [API] Quick Wins déjà validés: {len(state.get('validated_quick_wins', []))}")
            print(f"📊 [API] Structuration IA déjà validés: {len(state.get('validated_structuration_ia', []))}")
            
            # Créer le résultat de validation
            validation_result = {
                "validated_quick_wins": validated_quick_wins,
                "validated_structuration_ia": validated_structuration_ia,
                "rejected_quick_wins": rejected_quick_wins,
                "rejected_structuration_ia": rejected_structuration_ia,
                "user_feedback": user_feedback
            }
            
            # Mettre à jour l'état avec le feedback de validation
            self.graph.update_state(
                config,
                {
                    "use_case_validation_result": validation_result
                }
            )
            
            print(f"✅ [API] État mis à jour avec le feedback de validation use cases")
            
            # Reprendre l'exécution du workflow
            print(f"▶️ [API] Reprise du workflow use cases...")
            
            final_state = None
            for chunk in self.graph.stream(None, config):
                print(f"📊 [API] Chunk reçu: {list(chunk.keys())}")
                for node_name, node_state in chunk.items():
                    print(f"  • Nœud '{node_name}' exécuté")
                    final_state = node_state
            
            # Récupérer l'état final depuis le checkpointer
            snapshot = self.graph.get_state(config)
            state = snapshot.values
            
            print(f"📊 [API] Workflow use cases terminé ou en pause")
            print(f"📊 [API] Next nodes: {snapshot.next}")
            
            # Vérifier si le workflow est terminé ou en pause
            # Note: snapshot.next peut être une liste ou un tuple
            next_nodes = list(snapshot.next) if snapshot.next else []
            
            if len(next_nodes) == 0:
                # Workflow terminé
                print(f"✅ [API] Workflow use cases terminé avec succès")
                
                # Affichage du rapport final des coûts
                print("\n" + "="*70)
                print("📊 RAPPORT FINAL DES COÛTS")
                print("="*70)
                self.tracker.print_summary()
                
                # Sauvegarde du rapport de tracking
                report_path = self.tracker.save_report()
                print(f"📄 Rapport de coûts sauvegardé: {report_path}\n")
                
                return {
                    "success": True,
                    "final_needs": state.get("final_needs", []),
                    "final_quick_wins": state.get("final_quick_wins", []),
                    "final_structuration_ia": state.get("final_structuration_ia", []),
                    "summary": {
                        "total_needs": len(state.get("final_needs", [])),
                        "total_quick_wins": len(state.get("final_quick_wins", [])),
                        "total_structuration_ia": len(state.get("final_structuration_ia", [])),
                        "themes": list(set([need.get("theme", "") for need in state.get("final_needs", []) if need.get("theme")])),
                    },
                    "iteration_count": state.get("iteration_count", 0),
                    "use_case_iteration": state.get("use_case_iteration", 0),
                    "workshop_results": state.get("workshop_results", {}),
                    "transcript_results": state.get("transcript_results", []),
                    "web_search_results": state.get("web_search_results", {}),
                    "messages": ["Workflow terminé avec succès !"]
                }
            elif "validate_use_cases" in next_nodes:
                # En attente d'une nouvelle validation use cases
                print(f"⏸️ [API] Workflow en pause - nouvelle validation use cases requise")
                return {
                    "success": False,
                    "use_case_workflow_paused": True,
                    "final_needs": state.get("final_needs", []),
                    "proposed_quick_wins": state.get("proposed_quick_wins", []),
                    "proposed_structuration_ia": state.get("proposed_structuration_ia", []),
                    "validated_quick_wins": state.get("validated_quick_wins", []),
                    "validated_structuration_ia": state.get("validated_structuration_ia", []),
                    "summary": {
                        "total_needs": len(state.get("final_needs", [])),
                        "themes": list(set([need.get("theme", "") for need in state.get("final_needs", []) if need.get("theme")])),
                    },
                    "iteration_count": state.get("iteration_count", 0),
                    "use_case_iteration": state.get("use_case_iteration", 0),
                    "workshop_results": state.get("workshop_results", {}),
                    "transcript_results": state.get("transcript_results", []),
                    "web_search_results": state.get("web_search_results", {}),
                    "messages": ["Nouvelle validation use cases requise"]
                }
            else:
                # Autre cas
                print(f"⚠️ [API] État inattendu: {next_nodes}")
                return {
                    "success": False,
                    "error": f"État inattendu: {next_nodes}",
                    "final_needs": [],
                    "final_quick_wins": [],
                    "final_structuration_ia": [],
                    "iteration_count": state.get("iteration_count", 0),
                    "use_case_iteration": state.get("use_case_iteration", 0),
                    "messages": [f"État inattendu: {next_nodes}"]
                }
        
        except Exception as e:
            print(f"❌ [API] Erreur dans resume_use_case_workflow_with_feedback(): {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "final_needs": [],
                "final_quick_wins": [],
                "final_structuration_ia": [],
                "iteration_count": 0,
                "use_case_iteration": 0,
                "messages": [f"Erreur reprise workflow use cases: {str(e)}"]
            }
    
    # Fonction resume_use_case_workflow supprimée - était spécifique à Streamlit
    def resume_use_case_workflow_removed(self) -> Dict[str, Any]:
        """
        FONCTION SUPPRIMÉE - était spécifique à Streamlit.
        La validation humaine se fait maintenant via l'API FastAPI.
        """
        return {
            "success": False,
            "error": "Fonction supprimée - utilisez l'API FastAPI pour la validation",
            "final_quick_wins": [],
            "final_structuration_ia": [],
            "messages": ["Fonction obsolète"]
        }
    
    # ==================== FIN DU NETTOYAGE STREAMLIT ====================
