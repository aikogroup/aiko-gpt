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
import streamlit as st

# Import des agents
import sys
sys.path.append('/home/addeche/aiko/aikoGPT')
import config as project_config
from need_analysis.need_analysis_agent import NeedAnalysisAgent
from process_atelier.workshop_agent import WorkshopAgent
from process_transcript.transcript_agent import TranscriptAgent
from web_search.web_search_agent import WebSearchAgent
from human_in_the_loop.streamlit_validation_interface import StreamlitValidationInterface
from use_case_analysis.use_case_analysis_agent import UseCaseAnalysisAgent
from use_case_analysis.streamlit_use_case_validation import StreamlitUseCaseValidation
from utils.token_tracker import TokenTracker


class WorkflowState(TypedDict):
    """État du workflow LangGraph"""
    messages: Annotated[List[BaseMessage], add_messages]
    # IDs de documents dans la BDD
    workshop_document_ids: List[int]
    transcript_document_ids: List[int]
    company_info: Dict[str, Any]
    # Informations supplémentaires fournies par l'utilisateur
    additional_context: str
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
    workflow_paused: bool
    # Action demandée par l'utilisateur (pour les boutons)
    user_action: str  # "continue_needs" ou "continue_to_use_cases"
    # Résultats de l'analyse des use cases
    proposed_use_cases: List[Dict[str, Any]]
    # Contexte additionnel pour la génération des use cases
    use_case_additional_context: str
    # Validation humaine des use cases
    validated_use_cases: List[Dict[str, Any]]
    rejected_use_cases: List[Dict[str, Any]]
    use_case_user_feedback: str
    use_case_validation_result: Dict[str, Any]
    # Action demandée par l'utilisateur pour les use cases (pour les boutons)
    use_case_user_action: str  # "continue_use_cases" ou "finalize_use_cases"
    # État du workflow des use cases
    final_use_cases: List[Dict[str, Any]]
    use_case_workflow_paused: bool


class NeedAnalysisWorkflow:
    """
    Workflow LangGraph pour l'analyse des besoins métier
    """
    
    def __init__(self, api_key: str, dev_mode: bool = False):
        """
        Initialise le workflow avec la clé API OpenAI.
        
        Args:
            api_key: Clé API OpenAI
            dev_mode: Mode développement (utilise les données mockées)
        """
        self.api_key = api_key
        self.dev_mode = dev_mode
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
        self.human_interface = StreamlitValidationInterface()
        # Nouveaux agents pour l'analyse des use cases
        self.use_case_analysis_agent = UseCaseAnalysisAgent(api_key, tracker=self.tracker)
        self.use_case_validation_interface = StreamlitUseCaseValidation()
        
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
        # Toujours utiliser MemorySaver pour gérer les interrupts
        return MemorySaver()
    
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
        workflow.add_node("finalize_results", self._finalize_results_node)
        
        # Ajout des nœuds - Phase 2 : Analyse des use cases
        workflow.add_node("pre_use_case_interrupt", self._pre_use_case_interrupt_node)
        workflow.add_node("analyze_use_cases", self._analyze_use_cases_node)
        workflow.add_node("validate_use_cases", self._validate_use_cases_node)
        workflow.add_node("finalize_use_cases", self._finalize_use_cases_node)
        
        # Définition du flux - toujours commencer par dispatcher
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
        
        # Conditions de branchement - Phase 1 (basé sur l'action utilisateur)
        workflow.add_conditional_edges(
            "human_validation",
            self._should_continue_needs,
            {
                "continue_needs": "analyze_needs",
                "continue_to_use_cases": "finalize_results"
            }
        )
        
        # Transition vers Phase 2 : Analyse des use cases
        workflow.add_edge("finalize_results", "pre_use_case_interrupt")
        workflow.add_edge("pre_use_case_interrupt", "analyze_use_cases")
        workflow.add_edge("analyze_use_cases", "validate_use_cases")
        
        # Conditions de branchement - Phase 2 (basé sur l'action utilisateur)
        workflow.add_conditional_edges(
            "validate_use_cases",
            self._should_continue_use_cases,
            {
                "continue_use_cases": "analyze_use_cases",
                "finalize_use_cases": "finalize_use_cases"
            }
        )
        
        workflow.add_edge("finalize_use_cases", END)
        
        # Configuration avec checkpointer et interrupts
        # NOUVEAU: Toujours utiliser checkpointer et interrupts (pas seulement en debug)
        compile_kwargs = {
            "checkpointer": MemorySaver(),  # Toujours actif pour gérer les interrupts
            "interrupt_before": ["human_validation", "pre_use_case_interrupt", "validate_use_cases"]  # Points d'arrêt pour validation humaine
        }
        
        # Pas d'options supplémentaires en mode dev
        
        return workflow.compile(**compile_kwargs)
    
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
        print(f"   - workshop_document_ids: {len(state.get('workshop_document_ids', []))}")
        print(f"   - transcript_document_ids: {len(state.get('transcript_document_ids', []))}")
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
            
            # MODE DEV: Charger les données mockées depuis le fichier JSON
            if project_config.is_agent_dev_mode("workshop"):
                print(f"🔧 [PARALLÈLE-1/3] Mode dev WORKSHOP_DEV_MODE activé - chargement des données mockées")
                try:
                    mock_data = project_config.load_mock_data()
                    workshop_data = mock_data.get("workshop", {})
                    print(f"✅ [PARALLÈLE-1/3] Données mockées chargées: {len(workshop_data.get('workshops', []))} workshops")
                    return {"workshop_results": workshop_data}
                except Exception as e:
                    print(f"⚠️ [PARALLÈLE-1/3] Erreur lors du chargement des données mockées: {str(e)}")
                    return {"workshop_results": {"workshops": []}}
            
            # Fallback sur dev_mode global pour compatibilité
            if self.dev_mode:
                print(f"🔧 [PARALLÈLE-1/3] Mode dev global - retour de données mockées vides")
                return {"workshop_results": {"workshops": []}}
            
            workshop_document_ids = state.get("workshop_document_ids", [])
            
            if workshop_document_ids:
                print(f"🔄 [PARALLÈLE-1/3] Traitement de {len(workshop_document_ids)} workshops depuis la BDD...")
                all_results = []
                for document_id in workshop_document_ids:
                    file_results = self.workshop_agent.process_workshop_from_db(document_id)
                    all_results.extend(file_results)
                print(f"✅ [PARALLÈLE-1/3] {len(all_results)} workshops traités")
                print(f"✅ [PARALLÈLE-1/3] workshop_agent_node - FIN")
                return {"workshop_results": {"workshops": all_results}}
            else:
                print(f"⚠️ [PARALLÈLE-1/3] Aucun workshop fourni")
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
            
            # MODE DEV: Charger les données mockées depuis le fichier JSON
            if project_config.is_agent_dev_mode("transcript"):
                print(f"🔧 [PARALLÈLE-2/3] Mode dev TRANSCRIPT_DEV_MODE activé - chargement des données mockées")
                try:
                    mock_data = project_config.load_mock_data()
                    transcript_data = mock_data.get("transcript", {})
                    print(f"✅ [PARALLÈLE-2/3] Données mockées chargées: {len(transcript_data.get('results', []))} transcripts")
                    return {"transcript_results": transcript_data}
                except Exception as e:
                    print(f"⚠️ [PARALLÈLE-2/3] Erreur lors du chargement des données mockées: {str(e)}")
                    return {"transcript_results": {"results": []}}
            
            # Fallback sur dev_mode global pour compatibilité
            if self.dev_mode:
                print(f"🔧 [PARALLÈLE-2/3] Mode dev global - retour de données mockées vides")
                return {"transcript_results": {"results": []}}
            
            transcript_document_ids = state.get("transcript_document_ids", [])
            
            if transcript_document_ids:
                print(f"🔄 [PARALLÈLE-2/3] Traitement de {len(transcript_document_ids)} transcripts depuis la BDD...")
                results = []
                for document_id in transcript_document_ids:
                    result = self.transcript_agent.process_from_db(document_id)
                    results.append(result)
                print(f"✅ [PARALLÈLE-2/3] {len(results)} transcripts traités")
                print(f"✅ [PARALLÈLE-2/3] transcript_agent_node - FIN")
                return {"transcript_results": {"results": results}}
            else:
                print(f"⚠️ [PARALLÈLE-2/3] Aucun transcript fourni")
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
            
            # MODE DEV: Charger les données mockées depuis le fichier JSON
            if project_config.is_agent_dev_mode("web_search"):
                print(f"🔧 [PARALLÈLE-3/3] Mode dev WEB_SEARCH_DEV_MODE activé - chargement des données mockées")
                try:
                    mock_data = project_config.load_mock_data()
                    web_search_data = mock_data.get("web_search", {})
                    print(f"✅ [PARALLÈLE-3/3] Données mockées chargées pour: {web_search_data.get('nom', 'N/A')}")
                    return {"web_search_results": web_search_data}
                except Exception as e:
                    print(f"⚠️ [PARALLÈLE-3/3] Erreur lors du chargement des données mockées: {str(e)}")
                    return {"web_search_results": {}}
            
            # Fallback sur dev_mode global pour compatibilité
            if self.dev_mode:
                print(f"🔧 [PARALLÈLE-3/3] Mode dev global - retour de données mockées vides")
                return {"web_search_results": {}}
            
            company_info = state.get("company_info", {})
            
            if company_info:
                # Vérifier si company_info contient déjà les clés de CompanyInfo (validated_company_info)
                # Les clés de CompanyInfo sont: nom, secteur, chiffre_affaires, nombre_employes, description
                if "nom" in company_info or "secteur" in company_info:
                    # C'est un validated_company_info, l'utiliser directement
                    print(f"✅ [PARALLÈLE-3/3] Utilisation des informations validées (validated_company_info)")
                    print(f"✅ [PARALLÈLE-3/3] web_search_agent_node - FIN")
                    return {"web_search_results": company_info}
                
                # Sinon, c'est l'ancien format avec company_name, company_url, etc.
                company_name = company_info.get("company_name", "")
                if company_name:
                    company_url = company_info.get("company_url")
                    company_description = company_info.get("company_description")
                    print(f"🔄 [PARALLÈLE-3/3] Recherche web pour: {company_name}")
                    results = self.web_search_agent.search_company_info(
                        company_name,
                        company_url=company_url,
                        company_description=company_description
                    )
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
            
            # SINON, lancer les agents depuis la BDD
            print(f"⚠️ [DEBUG] Aucun résultat pré-calculé - lancement des agents depuis la BDD")
            workshop_document_ids = state.get("workshop_document_ids", [])
            transcript_document_ids = state.get("transcript_document_ids", [])
            company_info = state.get("company_info", {})
            
            # Workshop Agent
            if workshop_document_ids:
                all_results = []
                for document_id in workshop_document_ids:
                    file_results = self.workshop_agent.process_workshop_from_db(document_id)
                    all_results.extend(file_results)
                state["workshop_results"] = {"workshops": all_results}
            else:
                state["workshop_results"] = {}
                state["messages"] = state.get("messages", []) + [HumanMessage(content="Aucun document workshop fourni")]
            
            # Transcript Agent
            if transcript_document_ids:
                results = []
                for document_id in transcript_document_ids:
                    result = self.transcript_agent.process_from_db(document_id)
                    results.append(result)
                state["transcript_results"] = {"results": results}
            else:
                state["transcript_results"] = []
                state["messages"] = state.get("messages", []) + [HumanMessage(content="Aucun document transcript fourni")]
            
            # Web Search Agent
            if company_info:
                company_name = company_info.get("company_name", "")
                if company_name:
                    company_url = company_info.get("company_url")
                    company_description = company_info.get("company_description")
                    results = self.web_search_agent.search_company_info(
                        company_name,
                        company_url=company_url,
                        company_description=company_description
                    )
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
            # MODE DEV: Les agents ont déjà retourné des données mockées, on utilise directement les résultats
            if self.dev_mode:
                print(f"🔧 [CONVERGENCE] Mode dev - utilisation des résultats mockés des agents")
                # Les agents ont déjà retourné des données mockées vides
                # On prépare juste transcript_data pour la suite
                transcript_results_raw = state.get("transcript_results", {})
                if isinstance(transcript_results_raw, dict) and "results" in transcript_results_raw:
                    transcript_results = transcript_results_raw.get("results", [])
                elif isinstance(transcript_results_raw, list):
                    transcript_results = transcript_results_raw
                else:
                    transcript_results = []
                
                filtered_transcripts = []
                for transcript in transcript_results:
                    if isinstance(transcript, dict):
                        filtered_transcript = {
                            "pdf_path": transcript.get("pdf_path"),
                            "status": transcript.get("status"),
                            "semantic_analysis": transcript.get("semantic_analysis", {})
                        }
                        filtered_transcripts.append(filtered_transcript)
                
                state["transcript_data"] = filtered_transcripts
                print(f"🔍 [CONVERGENCE] Transcripts filtrés: {len(filtered_transcripts)} transcripts")
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
            
            # MODE DEV: Charger les données mockées depuis le fichier JSON
            if project_config.is_agent_dev_mode("need_analysis"):
                print(f"🔧 [DEBUG] Mode dev NEED_ANALYSIS_DEV_MODE activé - chargement des données mockées")
                try:
                    mock_data = project_config.load_mock_data()
                    need_analysis_data = mock_data.get("need_analysis", {})
                    identified_needs = need_analysis_data.get("identified_needs", [])
                    state["identified_needs"] = identified_needs
                    print(f"✅ [DEBUG] Besoins mockés chargés: {len(identified_needs)}")
                    print(f"📊 [DEBUG] Besoins identifiés: {len(identified_needs)}")
                    print(f"🎯 [DEBUG] Besoins validés total: {len(state.get('validated_needs', []))}")
                    return state
                except Exception as e:
                    print(f"⚠️ [DEBUG] Erreur lors du chargement des données mockées: {str(e)}")
                    # Continuer en mode normal si le chargement échoue
            
            # Fallback sur dev_mode global pour compatibilité
            if self.dev_mode:
                print(f"🔧 [DEBUG] Mode dev global activé - utilisation de debug_needs")
                # Définir les besoins de debug (même structure que dans app_api.py)
                debug_needs = [
                    {
                        "theme": "Automatisation & Efficacité Opérationnelle",
                        "quotes": [
                            "Nous passons trop de temps sur les tâches administratives répétitives",
                            "L'automatisation nous ferait gagner beaucoup de temps"
                        ]
                    },
                    {
                        "theme": "Analyse de Données & Amélioration de la Performance",
                        "quotes": [
                            "Nous avons besoin de mieux suivre nos performances commerciales",
                            "Un dashboard en temps réel serait très utile"
                        ]
                    },
                    {
                        "theme": "Optimisation de la Gestion des Stocks",
                        "quotes": [
                            "Nous avons souvent des ruptures de stock",
                            "Une meilleure prévision nous aiderait"
                        ]
                    },
                    {
                        "theme": "Amélioration du Recrutement",
                        "quotes": [
                            "La formation de nos équipes est un enjeu majeur",
                            "Nous avons besoin d'un système de suivi des compétences"
                        ]
                    },
                    {
                        "theme": "Système d'Alerte pour Non-Conformité",
                        "quotes": [
                            "La conformité réglementaire est complexe",
                            "Nous devons améliorer notre traçabilité"
                        ]
                    }
                ]
                
                state["identified_needs"] = debug_needs
                
                print(f"✅ [DEBUG] Besoins debug utilisés: {len(debug_needs)}")
                print(f"📊 [DEBUG] Besoins identifiés: {len(debug_needs)}")
                print(f"🎯 [DEBUG] Besoins validés total: {len(state.get('validated_needs', []))}")
                
                return state
            
            # MODE NORMAL: Génération des besoins avec l'IA
            print(f"🤖 [DEBUG] Mode normal - génération des besoins avec l'IA")
            
            # Analyse des besoins avec feedback si disponible
            user_feedback = state.get("user_feedback", "")
            rejected_needs = state.get("rejected_needs", [])
            previous_needs = state.get("identified_needs", [])
            
            if user_feedback or rejected_needs:
                print(f"\n🔄 Génération de nouvelles propositions...")
                if user_feedback:
                    print(f"💬 En tenant compte du feedback: {user_feedback}")
                if rejected_needs:
                    print(f"🚫 Besoins rejetés à éviter: {len(rejected_needs)}")
            
            # 💰 OPTIMISATION: Filtrer les quotes des previous_needs et rejected_needs pour économiser les tokens
            # Les quotes sont déjà dans workshop/transcript, pas besoin de les dupliquer au LLM
            previous_needs_light = None
            rejected_needs_light = None
            
            if previous_needs:
                previous_needs_light = [
                    {"id": need.get("id"), "theme": need.get("theme")}
                    for need in previous_needs
                ]
                print(f"💰 [OPTIMISATION] Previous needs allégés: {len(previous_needs)} besoins sans quotes")
            
            if rejected_needs:
                rejected_needs_light = [
                    {"id": need.get("id"), "theme": need.get("theme")}
                    for need in rejected_needs
                ]
                print(f"💰 [OPTIMISATION] Rejected needs allégés: {len(rejected_needs)} besoins sans quotes")
            
            analysis_result = self.need_analysis_agent.analyze_needs(
                workshop_data=state["workshop_results"],  # SIMPLIFICATION: utiliser directement workshop_results
                transcript_data=state["transcript_data"],
                web_search_data=state["web_search_results"],  # SIMPLIFICATION: utiliser directement web_search_results
                previous_needs=previous_needs_light,
                rejected_needs=rejected_needs_light,
                user_feedback=user_feedback,
                validated_needs_count=validated_count,
                additional_context=state.get("additional_context", "")
            )
            
            if "error" in analysis_result:
                state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse: {analysis_result['error']}")]
                return state
            
            # Récupérer tous les besoins identifiés (pas de limite)
            identified_needs = analysis_result.get("identified_needs", [])
            
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
                
                # Incrémenter le compteur d'itération
                state["iteration_count"] = state.get("iteration_count", 0) + 1
                print(f"🔄 [DEBUG] iteration_count incrémenté à {state['iteration_count']}")
                
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
            
            # Initialiser le compteur d'itération pour les use cases
            state["use_case_iteration_count"] = 0
            print(f"🔄 [DEBUG] use_case_iteration_count initialisé à 0")
            
            print(f"✅ [DEBUG] _finalize_results_node - FIN")
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _finalize_results_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur finalisation: {str(e)}")]
            return state
    
    def _should_continue_needs(self, state: WorkflowState) -> str:
        """
        Détermine la direction du workflow basée sur l'action de l'utilisateur.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            Direction à prendre : "continue_needs" ou "continue_to_use_cases"
        """
        user_action = state.get("user_action", "")
        
        if user_action == "continue_to_use_cases":
            return "continue_to_use_cases"
        else:
            # Par défaut, continuer avec les besoins
            return "continue_needs"
    
    def _should_continue_use_cases(self, state: WorkflowState) -> str:
        """
        Détermine la direction du workflow des use cases basée sur l'action de l'utilisateur.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            Direction à prendre : "continue_use_cases" ou "finalize_use_cases"
        """
        use_case_user_action = state.get("use_case_user_action", "")
        
        if use_case_user_action == "finalize_use_cases":
            return "finalize_use_cases"
        else:
            # Par défaut, continuer avec les use cases (régénération)
            return "continue_use_cases"
    
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
                "timestamp": datetime.now().isoformat()
            }
            
            # Sauvegarde en JSON
            output_path = str(project_config.ensure_outputs_dir() / "need_analysis_results.json")
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
            output_path = str(project_config.ensure_outputs_dir() / "workflow_graph.png")
            with open(output_path, 'wb') as f:
                f.write(png)
            
        except Exception as e:
            print(f"Erreur génération graph: {str(e)}")
    
    def run(self, workshop_document_ids: List[int] = None, transcript_document_ids: List[int] = None,
            company_info: Dict[str, Any] = None, 
            workshop_results: Dict[str, Any] = None, transcript_results: List[Dict[str, Any]] = None, web_search_results: Dict[str, Any] = None,
            interviewer_names: List[str] = None, thread_id: str = None, additional_context: str = "") -> Dict[str, Any]:
        """
        Exécute le workflow complet.
        NOUVELLE ARCHITECTURE: Exécution MANUELLE des nœuds jusqu'à human_validation.
        MODE DEV: Charge les besoins depuis need_analysis_results.json et passe directement aux use cases.
        
        Args:
            workshop_document_ids: Liste des IDs de documents workshop dans la BDD
            transcript_document_ids: Liste des IDs de documents transcript dans la BDD
            company_info: Informations sur l'entreprise pour la recherche web
            workshop_results: Résultats pré-calculés du workshop agent
            transcript_results: Résultats pré-calculés du transcript agent
            web_search_results: Résultats pré-calculés du web search agent
            thread_id: ID du thread pour le checkpointer (optionnel, généré automatiquement si non fourni)
            
        Returns:
            Résultats du workflow
        """
        print(f"\n🚀 [DEBUG] run() appelé - NOUVELLE ARCHITECTURE")
        print(f"🔧 [DEBUG] Mode dev: {self.dev_mode}")
        print(f"📊 [DEBUG] Résultats pré-calculés: workshop={bool(workshop_results)}, transcript={bool(transcript_results)}, web_search={bool(web_search_results)}")
        print(f"🔑 [DEBUG] Thread ID fourni: {thread_id}")
        
        # Configurer les interviewer_names si fournis
        if interviewer_names:
            print(f"👥 [DEBUG] Configuration des interviewers: {interviewer_names}")
            self.transcript_agent.speaker_classifier.set_interviewer_names(interviewer_names)
        
        try:
            # État initial avec les fichiers d'entrée ET les résultats pré-calculés
            state = WorkflowState(
                messages=[],
                # IDs de documents dans la BDD
                workshop_document_ids=workshop_document_ids or [],
                transcript_document_ids=transcript_document_ids or [],
                company_info=company_info or {},
                # Informations supplémentaires fournies par l'utilisateur
                additional_context=additional_context or "",
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
                workflow_paused=False,
                # Action demandée par l'utilisateur (pour les boutons)
                user_action="",
                # Résultats de l'analyse des use cases
                proposed_use_cases=[],
                # Contexte additionnel pour la génération des use cases
                use_case_additional_context="",
                # Validation humaine des use cases
                validated_use_cases=[],
                rejected_use_cases=[],
                use_case_user_feedback="",
                use_case_validation_result={},
                # État du workflow des use cases
                final_use_cases=[],
                use_case_workflow_paused=False
            )
            
            # MODE DEV: Vérifier si need_analysis_results.json existe
            if self.dev_mode:
                try:
                    print(f"🔧 [DEBUG] Mode dev activé - tentative de chargement depuis need_analysis_results.json")
                    dev_json_path = str(project_config.OUTPUTS_DIR / "need_analysis_results.json")
                    if not os.path.exists(dev_json_path):
                        # Essayer aussi à la racine du projet (legacy)
                        dev_json_path = str(project_config.PROJECT_ROOT / "need_analysis_results.json")
                    with open(dev_json_path, 'r', encoding='utf-8') as f:
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
    
    def resume_workflow(self) -> Dict[str, Any]:
        """
        Reprend le workflow après validation humaine.
        VERSION CORRIGÉE: Reprend depuis le nœud check_success au lieu de repartir du début.
        
        Returns:
            Résultats du workflow
        """
        print(f"\n🔄 [DEBUG] resume_workflow() appelé")
        
        try:
            # Récupérer l'état du workflow depuis session_state
            if "workflow_state" not in st.session_state:
                print(f"❌ [DEBUG] Aucun état de workflow trouvé dans session_state")
                return {
                    "success": False,
                    "error": "Aucun état de workflow trouvé",
                    "final_needs": [],
                    "iteration_count": 0,
                    "messages": ["Erreur: Aucun état de workflow trouvé"]
                }
            
            # Récupérer l'état sauvegardé
            workflow_state = st.session_state.workflow_state
            print(f"📊 [DEBUG] État du workflow récupéré: {len(workflow_state)} clés")
            
            # Récupérer le résultat de validation depuis session_state
            if "validation_result" not in st.session_state:
                print(f"❌ [DEBUG] Aucun résultat de validation trouvé")
                return {
                    "success": False,
                    "error": "Aucun résultat de validation trouvé",
                    "final_needs": [],
                    "iteration_count": 0,
                    "messages": ["Erreur: Aucun résultat de validation trouvé"]
                }
            
            validation_result = st.session_state.validation_result
            print(f"📊 [DEBUG] Résultat de validation récupéré: {validation_result.get('total_validated', 0)} besoins validés")
            
            # CORRECTION: Ne pas écraser validated_needs, mais accumuler correctement
            # validation_result contient les besoins nouvellement validés
            existing_validated = workflow_state.get("validated_needs", [])
            newly_validated = validation_result.get("validated_needs", [])
            
            # Éviter les doublons
            existing_ids = [need.get("theme", "") for need in existing_validated]
            unique_newly_validated = [need for need in newly_validated if need.get("theme", "") not in existing_ids]
            
            workflow_state["validated_needs"] = existing_validated + unique_newly_validated
            
            # Même chose pour rejected_needs
            existing_rejected = workflow_state.get("rejected_needs", [])
            newly_rejected = validation_result.get("rejected_needs", [])
            
            existing_rejected_ids = [need.get("theme", "") for need in existing_rejected]
            unique_newly_rejected = [need for need in newly_rejected if need.get("theme", "") not in existing_rejected_ids]
            
            workflow_state["rejected_needs"] = existing_rejected + unique_newly_rejected
            
            workflow_state["user_feedback"] = validation_result.get("user_feedback", "")
            workflow_state["validation_result"] = validation_result
            
            print(f"📊 [DEBUG] Besoins nouvellement validés: {len(unique_newly_validated)}")
            print(f"📊 [DEBUG] Total besoins validés: {len(workflow_state['validated_needs'])}")
            
            # Exécuter les nœuds suivants manuellement
            print(f"🔄 [DEBUG] Exécution des nœuds suivants après validation...")
            
            # 1. Vérifier le succès
            workflow_state = self._check_success_node(workflow_state)
            
            # 2. Déterminer la suite selon le résultat
            should_continue = self._should_continue(workflow_state)
            print(f"📊 [DEBUG] Décision de continuation: {should_continue}")
            
            if should_continue == "success":
                # 3. Finaliser les résultats
                print(f"🔍 [DEBUG] _finalize_results_node - DÉBUT")
                workflow_state = self._finalize_results_node(workflow_state)
                print(f"✅ [DEBUG] _finalize_results_node - FIN")
                
                print(f"✅ [DEBUG] Phase 1 (besoins) terminée avec succès")
                print(f"📊 [DEBUG] Success: {workflow_state.get('success', False)}")
                print(f"📊 [DEBUG] Final needs: {len(workflow_state.get('final_needs', []))}")
                
                # NETTOYAGE DES FLAGS DE LA PHASE 1 ← NOUVEAU
                print(f"🧹 [DEBUG] Nettoyage des flags de la Phase 1")
                workflow_state["workflow_paused"] = False
                st.session_state.workflow_paused = False
                st.session_state.waiting_for_validation = False
                if "validation_result" in st.session_state:
                    del st.session_state.validation_result
                if "workflow_state" in st.session_state:
                    del st.session_state.workflow_state
                print(f"✅ [DEBUG] Flags de Phase 1 nettoyés")
                
                # CORRECTION: Continuer vers l'analyse des use cases au lieu de retourner
                print(f"🚀 [DEBUG] Passage à la Phase 2 : Analyse des use cases")
                
                # 4. Analyser les use cases
                workflow_state = self._analyze_use_cases_node(workflow_state)
                
                # 5. Afficher l'interface de validation des use cases
                workflow_state = self._validate_use_cases_node(workflow_state)
                
                print(f"⏸️ [DEBUG] Workflow en pause - en attente de validation des use cases")
                
                # Retourner un état "en pause" pour les use cases
                return {
                    "success": False,  # Pas encore terminé, on attend la validation use cases
                    "final_needs": workflow_state.get("final_needs", []),
                    "summary": {
                        "total_needs": len(workflow_state.get("final_needs", [])),
                        "themes": list(set([need.get("theme", "") for need in workflow_state.get("final_needs", []) if need.get("theme")])),
                    },
                    "iteration_count": workflow_state.get("iteration_count", 0),
                    "workshop_results": workflow_state.get("workshop_results", {}),
                    "transcript_results": workflow_state.get("transcript_results", []),
                    "web_search_results": workflow_state.get("web_search_results", {}),
                    "messages": ["Phase 1 terminée - en attente de validation des use cases"]
                }
            elif should_continue == "continue":
                # 4. Continuer avec une nouvelle analyse (pas encore 5 besoins validés)
                print(f"🔄 [DEBUG] Besoin de plus de besoins validés - génération d'une nouvelle itération")
                print(f"📊 [DEBUG] Besoins actuellement validés: {len(workflow_state.get('validated_needs', []))}/5")
                print(f"🔄 [DEBUG] Itération actuelle: {workflow_state.get('iteration_count', 0)}/{workflow_state.get('max_iterations', 3)}")
                
                # NOTE: L'incrémentation est déjà faite dans _check_success_node
                # Ne pas incrémenter ici pour éviter la double incrémentation !
                
                # CORRECTION: Nettoyer validation_result avant la nouvelle itération
                print(f"🧹 [DEBUG] Nettoyage de validation_result pour la nouvelle itération")
                if "validation_result" in st.session_state:
                    del st.session_state.validation_result
                print(f"✅ [DEBUG] validation_result nettoyé")
                
                # Analyser de nouveaux besoins
                workflow_state = self._analyze_needs_node(workflow_state)
                
                # Afficher l'interface de validation pour les nouveaux besoins
                workflow_state = self._human_validation_node(workflow_state)
                
                print(f"⏸️ [DEBUG] Workflow en pause - nouvelle validation requise")
                
                # Le workflow s'arrête à nouveau pour une nouvelle validation
                return {
                    "success": False,
                    "error": "Nouvelle validation requise",
                    "final_needs": [],
                    "iteration_count": workflow_state.get("iteration_count", 0),
                    "messages": ["Nouvelle validation requise"]
                }
            else:  # max_iterations
                print(f"❌ [DEBUG] Nombre maximum d'itérations atteint")
                return {
                    "success": False,
                    "error": "Nombre maximum d'itérations atteint",
                    "final_needs": [],
                    "iteration_count": workflow_state.get("iteration_count", 0),
                    "messages": ["Nombre maximum d'itérations atteint"]
                }
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans resume_workflow(): {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "final_needs": [],
                "iteration_count": 0,
                "messages": [f"Erreur reprise workflow: {str(e)}"]
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
            # Initialiser les listes si première fois
            if "validated_use_cases" not in state:
                state["validated_use_cases"] = []
                state["rejected_use_cases"] = []
            
            # Récupérer les besoins validés
            validated_needs = state.get("final_needs", [])
            
            if not validated_needs:
                print(f"⚠️ [DEBUG] Aucun besoin validé trouvé")
                state["proposed_use_cases"] = []
                return state
            
            # Préparer les données pour la génération
            previous_use_cases = state.get("proposed_use_cases", [])
            rejected_use_cases = state.get("rejected_use_cases", [])
            user_feedback = state.get("use_case_user_feedback", "")
            additional_context = state.get("use_case_additional_context", "")
            
            if previous_use_cases:
                print(f"💬 [DEBUG] Régénération avec feedback")
                if user_feedback:
                    print(f"💬 [DEBUG] Commentaires utilisateur : {user_feedback[:100]}...")
                if rejected_use_cases:
                    print(f"🚫 [DEBUG] Cas d'usage rejetés à éviter : {len(rejected_use_cases)}")
            
            # MODE DEV: Charger les données mockées depuis le fichier JSON
            if project_config.is_agent_dev_mode("use_case_analysis"):
                print(f"🔧 [DEBUG] Mode dev USE_CASE_ANALYSIS_DEV_MODE activé - chargement des données mockées")
                try:
                    mock_data = project_config.load_mock_data()
                    use_case_analysis_data = mock_data.get("use_case_analysis", {})
                    proposed_use_cases = use_case_analysis_data.get("use_cases", [])
                    state["proposed_use_cases"] = proposed_use_cases
                    print(f"✅ [DEBUG] Cas d'usage mockés chargés: {len(proposed_use_cases)}")
                    print(f"✅ [DEBUG] _analyze_use_cases_node - FIN")
                    return state
                except Exception as e:
                    print(f"⚠️ [DEBUG] Erreur lors du chargement des données mockées: {str(e)}")
                    # Continuer en mode normal si le chargement échoue
            
            # Récupérer les données sources pour enrichir le contexte
            workshop_results = state.get("workshop_results", {})
            transcript_data = state.get("transcript_data", [])
            web_search_results = state.get("web_search_results", {})
            
            print(f"🔍 [DEBUG] Données de contexte: {len(workshop_results.get('workshops', []))} workshops, "
                  f"{len(transcript_data)} transcripts, web_search présent={bool(web_search_results)}")
            
            # 💰 OPTIMISATION: Filtrer les quotes des validated_needs pour économiser les tokens
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
                previous_use_cases=previous_use_cases if previous_use_cases else None,
                rejected_use_cases=rejected_use_cases if rejected_use_cases else None,
                user_feedback=user_feedback,
                additional_context=additional_context
            )
            
            if "error" in result:
                print(f"❌ [DEBUG] Erreur lors de l'analyse: {result['error']}")
                state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse use cases: {result['error']}")]
                return state
            
            # Mettre à jour l'état avec les résultats
            proposed_use_cases = result.get("use_cases", [])
            
            # Filtrer les use cases déjà validés pour ne pas les reproposer
            existing_validated = state.get("validated_use_cases", [])
            if existing_validated:
                validated_ids = {uc.get("id", "") for uc in existing_validated}
                original_count = len(proposed_use_cases)
                proposed_use_cases = [uc for uc in proposed_use_cases if uc.get("id", "") not in validated_ids]
                filtered_count = original_count - len(proposed_use_cases)
                if filtered_count > 0:
                    print(f"🔍 [FILTER] {filtered_count} cas d'usage déjà validés filtrés ({len(proposed_use_cases)} restants)")
            
            state["proposed_use_cases"] = proposed_use_cases
            
            print(f"✅ [DEBUG] _analyze_use_cases_node - FIN")
            print(f"📊 Cas d'usage proposés: {len(state['proposed_use_cases'])}")
            
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
        print(f"📊 Cas d'usage proposés: {len(state.get('proposed_use_cases', []))}")
        print(f"📊 Cas d'usage validés existants: {len(state.get('validated_use_cases', []))}")
        
        try:
            # Vérifier si on a reçu le feedback (injecté par l'API)
            if "use_case_validation_result" in state and state["use_case_validation_result"]:
                print(f"✅ [RESUME] Feedback use cases reçu via API")
                validation_data = state["use_case_validation_result"]
                
                # Traiter les résultats de validation
                existing_validated = state.get("validated_use_cases", [])
                newly_validated = validation_data.get("validated_use_cases", [])
                
                # Éviter les doublons
                existing_ids = [uc.get("id", "") for uc in existing_validated]
                unique_newly_validated = [uc for uc in newly_validated if uc.get("id", "") not in existing_ids]
                
                state["validated_use_cases"] = existing_validated + unique_newly_validated
                
                # Même chose pour les rejetés
                existing_rejected = state.get("rejected_use_cases", [])
                newly_rejected = validation_data.get("rejected_use_cases", [])
                
                existing_rejected_ids = [uc.get("id", "") for uc in existing_rejected]
                unique_newly_rejected = [uc for uc in newly_rejected if uc.get("id", "") not in existing_rejected_ids]
                
                state["rejected_use_cases"] = existing_rejected + unique_newly_rejected
                state["use_case_user_feedback"] = validation_data.get("user_feedback", "")
                
                # Incrémenter le compteur d'itération
                state["use_case_iteration_count"] = state.get("use_case_iteration_count", 0) + 1
                print(f"🔄 [DEBUG] use_case_iteration_count incrémenté à {state['use_case_iteration_count']}")
                
                # Nettoyer le flag
                state["use_case_validation_result"] = {}
                
                print(f"📊 [RESUME] Cas d'usage nouvellement validés: {len(unique_newly_validated)}")
                print(f"📊 [RESUME] Total cas d'usage validés: {len(state['validated_use_cases'])}")
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
    
    def _pre_use_case_interrupt_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud d'interrupt avant la génération des use cases.
        Affiche un résumé des besoins validés et attend un contexte additionnel.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour avec le contexte additionnel
        """
        print(f"\n🛑 [INTERRUPT] pre_use_case_interrupt_node - DÉBUT")
        print(f"📊 Besoins validés: {len(state.get('final_needs', []))}")
        
        try:
            # Vérifier si on a reçu le contexte additionnel (injecté par l'API)
            if "use_case_additional_context" in state:
                context = state.get("use_case_additional_context", "")
                print(f"✅ [RESUME] Contexte additionnel reçu: {len(context)} caractères")
                return state
            else:
                # Première fois : le workflow va s'arrêter ici (interrupt_before)
                print(f"⏸️ [INTERRUPT] Aucun contexte - le workflow va s'arrêter")
                print(f"💡 [INTERRUPT] L'API détectera cet arrêt et Streamlit affichera l'interface")
                return state
            
        except Exception as e:
            print(f"❌ [ERROR] Erreur dans pre_use_case_interrupt_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur interrupt: {str(e)}")]
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
            print(f"📊 [DEBUG] Cas d'usage validés: {len(state.get('validated_use_cases', []))}")
            
            # Utiliser directement les cas d'usage validés depuis l'état
            validated_use_cases = state.get("validated_use_cases", [])
            
            state["final_use_cases"] = validated_use_cases
            
            print(f"📊 [DEBUG] Final cas d'usage définis: {len(validated_use_cases)}")
            
            # Debug: Afficher les titres des cas d'usage
            if validated_use_cases:
                print(f"📋 [DEBUG] Titres des cas d'usage validés:")
                for i, uc in enumerate(validated_use_cases, 1):
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
                "final_use_cases": state.get("final_use_cases", []),
                "timestamp": datetime.now().isoformat(),
                # Inclure aussi les besoins pour référence
                "source_needs": state.get("final_needs", [])
            }
            
            # Sauvegarde en JSON
            output_path = str(project_config.ensure_outputs_dir() / "use_case_analysis_results.json")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"💾 [DEBUG] Résultats sauvegardés dans {output_path}")
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde use cases: {str(e)}")
    
    def resume_workflow_with_feedback(self, validated_needs: List[Dict[str, Any]], 
                                       rejected_needs: List[Dict[str, Any]], 
                                       user_feedback: str,
                                       user_action: str,
                                       thread_id: str) -> Dict[str, Any]:
        """
        Reprend le workflow après validation humaine avec le feedback.
        NOUVELLE VERSION pour architecture API avec LangGraph checkpointer.
        
        Args:
            validated_needs: Besoins validés par l'utilisateur
            rejected_needs: Besoins rejetés par l'utilisateur
            user_feedback: Commentaires de l'utilisateur
            user_action: Action demandée par l'utilisateur ("continue_needs" ou "continue_to_use_cases")
            thread_id: ID du thread pour récupérer l'état depuis le checkpointer
        
        Returns:
            Résultats du workflow
        """
        print(f"\n🔄 [API] resume_workflow_with_feedback() appelé")
        print(f"✅ Validés: {len(validated_needs)}")
        print(f"❌ Rejetés: {len(rejected_needs)}")
        print(f"💬 Feedback: {user_feedback[:100] if user_feedback else 'Aucun'}")
        print(f"🎯 Action: {user_action}")
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
            
            # Mettre à jour l'état avec le feedback de validation et l'action utilisateur
            self.graph.update_state(
                config,
                {
                    "validation_result": validation_result,
                    "user_action": user_action
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
                    "workshop_results": state.get("workshop_results", {}),
                    "transcript_results": state.get("transcript_results", []),
                    "web_search_results": state.get("web_search_results", {}),
                    "messages": ["Nouvelle validation requise"]
                }
            elif "pre_use_case_interrupt" in next_nodes:
                # Transition vers interrupt avant génération des use cases
                print(f"⏸️ [API] Workflow en pause - contexte additionnel requis")
                return {
                    "success": False,
                    "workflow_paused": True,
                    "final_needs": state.get("final_needs", []),
                    "summary": {
                        "total_needs": len(state.get("final_needs", [])),
                        "themes": list(set([need.get("theme", "") for need in state.get("final_needs", []) if need.get("theme")])),
                    },
                    "workshop_results": state.get("workshop_results", {}),
                    "transcript_results": state.get("transcript_results", []),
                    "web_search_results": state.get("web_search_results", {}),
                    "messages": ["Phase 1 terminée - contexte additionnel requis pour génération des use cases"]
                }
            elif "validate_use_cases" in next_nodes:
                # Transition vers validation des use cases
                print(f"⏸️ [API] Workflow en pause - validation des use cases requise")
                return {
                    "success": False,
                    "workflow_paused": True,
                    "use_case_workflow_paused": True,
                    "final_needs": state.get("final_needs", []),
                    "proposed_use_cases": state.get("proposed_use_cases", []),
                    "summary": {
                        "total_needs": len(state.get("final_needs", [])),
                        "themes": list(set([need.get("theme", "") for need in state.get("final_needs", []) if need.get("theme")])),
                    },
                    "workshop_results": state.get("workshop_results", {}),
                    "transcript_results": state.get("transcript_results", []),
                    "web_search_results": state.get("web_search_results", {}),
                    "messages": ["Validation des use cases requise"]
                }
            else:
                # Autre cas
                print(f"⚠️ [API] État inattendu: {next_nodes}")
                return {
                    "success": False,
                    "error": f"État inattendu: {next_nodes}",
                    "final_needs": [],
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
                "messages": [f"Erreur reprise workflow: {str(e)}"]
            }
    
    def resume_pre_use_case_interrupt_with_context(self, use_case_additional_context: str, thread_id: str) -> Dict[str, Any]:
        """
        Reprend le workflow après l'interrupt pre_use_case_interrupt avec le contexte additionnel.
        
        Args:
            use_case_additional_context: Contexte additionnel pour la génération des use cases
            thread_id: ID du thread pour récupérer l'état depuis le checkpointer
        
        Returns:
            Résultats du workflow
        """
        print(f"\n🔄 [API] resume_pre_use_case_interrupt_with_context() appelé")
        print(f"💡 Contexte: {len(use_case_additional_context)} caractères")
        print(f"🔑 Thread ID: {thread_id}")
        
        try:
            # Configuration pour récupérer l'état depuis le checkpointer
            config = {"configurable": {"thread_id": thread_id}}
            
            # Récupérer l'état actuel depuis le checkpointer
            snapshot = self.graph.get_state(config)
            state = snapshot.values
            
            print(f"📊 [API] État récupéré depuis le checkpointer")
            
            # Mettre à jour l'état avec le contexte additionnel
            self.graph.update_state(
                config,
                {
                    "use_case_additional_context": use_case_additional_context
                }
            )
            
            print(f"✅ [API] État mis à jour avec le contexte additionnel")
            
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
            next_nodes = list(snapshot.next) if snapshot.next else []
            
            if "validate_use_cases" in next_nodes:
                # En attente de validation des use cases
                print(f"⏸️ [API] Workflow en pause - validation des use cases requise")
                return {
                    "success": False,
                    "workflow_paused": True,
                    "use_case_workflow_paused": True,
                    "final_needs": state.get("final_needs", []),
                    "proposed_use_cases": state.get("proposed_use_cases", []),
                    "messages": ["Validation des use cases requise"]
                }
            else:
                # Autre cas
                print(f"⚠️ [API] État inattendu: {next_nodes}")
                return {
                    "success": False,
                    "error": f"État inattendu: {next_nodes}",
                    "messages": [f"État inattendu: {next_nodes}"]
                }
        
        except Exception as e:
            print(f"❌ [API] Erreur dans resume_pre_use_case_interrupt_with_context(): {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "messages": [f"Erreur reprise workflow: {str(e)}"]
            }
    
    def resume_use_case_workflow_with_feedback(self, validated_use_cases: List[Dict[str, Any]],
                                                rejected_use_cases: List[Dict[str, Any]],
                                                user_feedback: str,
                                                use_case_user_action: str,
                                                thread_id: str) -> Dict[str, Any]:
        """
        Reprend le workflow après validation des use cases avec le feedback.
        NOUVELLE VERSION pour architecture API avec LangGraph checkpointer.
        
        Args:
            validated_use_cases: Cas d'usage validés
            rejected_use_cases: Cas d'usage rejetés
            user_feedback: Commentaires de l'utilisateur
            use_case_user_action: Action demandée par l'utilisateur ("continue_use_cases" ou "finalize_use_cases")
            thread_id: ID du thread pour récupérer l'état depuis le checkpointer
        
        Returns:
            Résultats finaux du workflow
        """
        print(f"\n🔄 [API] resume_use_case_workflow_with_feedback() appelé")
        print(f"✅ Cas d'usage validés: {len(validated_use_cases)}")
        print(f"🎯 Action: {use_case_user_action}")
        print(f"🔑 Thread ID: {thread_id}")
        
        try:
            # Configuration pour récupérer l'état depuis le checkpointer
            config = {"configurable": {"thread_id": thread_id}}
            
            # Récupérer l'état actuel depuis le checkpointer
            snapshot = self.graph.get_state(config)
            state = snapshot.values
            
            print(f"📊 [API] État récupéré depuis le checkpointer")
            print(f"📊 [API] Cas d'usage proposés: {len(state.get('proposed_use_cases', []))}")
            print(f"📊 [API] Cas d'usage déjà validés: {len(state.get('validated_use_cases', []))}")
            
            # Créer le résultat de validation
            validation_result = {
                "validated_use_cases": validated_use_cases,
                "rejected_use_cases": rejected_use_cases,
                "user_feedback": user_feedback
            }
            
            # Mettre à jour l'état avec le feedback de validation et l'action utilisateur
            self.graph.update_state(
                config,
                {
                    "use_case_validation_result": validation_result,
                    "use_case_user_action": use_case_user_action
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
                    "final_use_cases": state.get("final_use_cases", []),
                    "summary": {
                        "total_needs": len(state.get("final_needs", [])),
                        "total_use_cases": len(state.get("final_use_cases", [])),
                        "themes": list(set([need.get("theme", "") for need in state.get("final_needs", []) if need.get("theme")])),
                    },
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
                    "proposed_use_cases": state.get("proposed_use_cases", []),
                    "validated_use_cases": state.get("validated_use_cases", []),
                    "summary": {
                        "total_needs": len(state.get("final_needs", [])),
                        "themes": list(set([need.get("theme", "") for need in state.get("final_needs", []) if need.get("theme")])),
                    },
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
                    "final_use_cases": [],
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
                "final_use_cases": [],
                "messages": [f"Erreur reprise workflow use cases: {str(e)}"]
            }
    
    def resume_use_case_workflow(self) -> Dict[str, Any]:
        """
        Reprend le workflow après validation humaine des use cases.
        
        Returns:
            Résultats du workflow
        """
        print(f"\n🔄 [DEBUG] resume_use_case_workflow() appelé")
        
        try:
            # Récupérer l'état du workflow depuis session_state
            if "use_case_workflow_state" not in st.session_state:
                print(f"❌ [DEBUG] Aucun état de workflow use case trouvé dans session_state")
                return {
                    "success": False,
                    "error": "Aucun état de workflow use case trouvé",
                    "final_quick_wins": [],
                    "final_structuration_ia": [],
                    "messages": ["Erreur: Aucun état de workflow use case trouvé"]
                }
            
            # Récupérer l'état sauvegardé
            workflow_state = st.session_state.use_case_workflow_state
            print(f"📊 [DEBUG] État du workflow récupéré: {len(workflow_state)} clés")
            
            # Récupérer le résultat de validation depuis session_state
            if "use_case_validation_result" not in st.session_state:
                print(f"❌ [DEBUG] Aucun résultat de validation trouvé")
                return {
                    "success": False,
                    "error": "Aucun résultat de validation trouvé",
                    "final_quick_wins": [],
                    "final_structuration_ia": [],
                    "messages": ["Erreur: Aucun résultat de validation trouvé"]
                }
            
            validation_result = st.session_state.use_case_validation_result
            print(f"📊 [DEBUG] Résultat de validation récupéré")
            
            # Accumuler les validations
            existing_qw = workflow_state.get("validated_quick_wins", [])
            newly_validated_qw = validation_result.get("validated_quick_wins", [])
            
            existing_sia = workflow_state.get("validated_structuration_ia", [])
            newly_validated_sia = validation_result.get("validated_structuration_ia", [])
            
            # Éviter les doublons
            existing_qw_ids = [uc.get("titre", "") for uc in existing_qw]
            unique_qw = [uc for uc in newly_validated_qw if uc.get("titre", "") not in existing_qw_ids]
            
            existing_sia_ids = [uc.get("titre", "") for uc in existing_sia]
            unique_sia = [uc for uc in newly_validated_sia if uc.get("titre", "") not in existing_sia_ids]
            
            workflow_state["validated_quick_wins"] = existing_qw + unique_qw
            workflow_state["validated_structuration_ia"] = existing_sia + unique_sia
            
            # Même chose pour les rejetés
            existing_rejected_qw = workflow_state.get("rejected_quick_wins", [])
            newly_rejected_qw = validation_result.get("rejected_quick_wins", [])
            workflow_state["rejected_quick_wins"] = existing_rejected_qw + newly_rejected_qw
            
            existing_rejected_sia = workflow_state.get("rejected_structuration_ia", [])
            newly_rejected_sia = validation_result.get("rejected_structuration_ia", [])
            workflow_state["rejected_structuration_ia"] = existing_rejected_sia + newly_rejected_sia
            
            workflow_state["use_case_user_feedback"] = validation_result.get("user_feedback", "")
            workflow_state["use_case_validation_result"] = validation_result
            
            print(f"📊 [DEBUG] Quick Wins nouvellement validés: {len(unique_qw)}")
            print(f"📊 [DEBUG] Structuration IA nouvellement validés: {len(unique_sia)}")
            print(f"📊 [DEBUG] Total Quick Wins validés: {len(workflow_state['validated_quick_wins'])}")
            print(f"📊 [DEBUG] Total Structuration IA validés: {len(workflow_state['validated_structuration_ia'])}")
            
            # Exécuter les nœuds suivants manuellement
            print(f"🔄 [DEBUG] Exécution des nœuds suivants après validation...")
            
            # 1. Vérifier le succès
            workflow_state = self._check_use_case_success_node(workflow_state)
            
            # 2. Déterminer la suite selon le résultat
            should_continue = self._should_continue_use_cases(workflow_state)
            print(f"📊 [DEBUG] Décision de continuation: {should_continue}")
            
            if should_continue == "success":
                # 3. Finaliser les résultats
                print(f"🔍 [DEBUG] _finalize_use_cases_node - DÉBUT")
                workflow_state = self._finalize_use_cases_node(workflow_state)
                print(f"✅ [DEBUG] _finalize_use_cases_node - FIN")
                
                print(f"✅ [DEBUG] Workflow use cases terminé avec succès")
                print(f"📊 [DEBUG] Success: {workflow_state.get('use_case_success', False)}")
                print(f"📊 [DEBUG] Final Quick Wins: {len(workflow_state.get('final_quick_wins', []))}")
                print(f"📊 [DEBUG] Final Structuration IA: {len(workflow_state.get('final_structuration_ia', []))}")
                
                return {
                    "success": workflow_state.get("use_case_success", False),
                    "final_quick_wins": workflow_state.get("final_quick_wins", []),
                    "final_structuration_ia": workflow_state.get("final_structuration_ia", []),
                    "use_case_iteration": workflow_state.get("use_case_iteration", 0),
                    "final_needs": workflow_state.get("final_needs", []),
                    "messages": ["Analyse des use cases terminée avec succès"]
                }
            elif should_continue == "continue":
                # 4. Continuer avec une nouvelle analyse
                print(f"🔄 [DEBUG] Besoin de plus de use cases validés - génération d'une nouvelle itération")
                print(f"📊 [DEBUG] Quick Wins actuellement validés: {len(workflow_state.get('validated_quick_wins', []))}/5")
                print(f"📊 [DEBUG] Structuration IA actuellement validés: {len(workflow_state.get('validated_structuration_ia', []))}/5")
                print(f"🔄 [DEBUG] Itération actuelle: {workflow_state.get('use_case_iteration', 0)}/{workflow_state.get('max_use_case_iterations', 3)}")
                
                # Nettoyer validation_result avant la nouvelle itération
                print(f"🧹 [DEBUG] Nettoyage de use_case_validation_result pour la nouvelle itération")
                if "use_case_validation_result" in st.session_state:
                    del st.session_state.use_case_validation_result
                print(f"✅ [DEBUG] use_case_validation_result nettoyé")
                
                # Analyser de nouveaux use cases
                workflow_state = self._analyze_use_cases_node(workflow_state)
                
                # Afficher l'interface de validation pour les nouveaux use cases
                workflow_state = self._validate_use_cases_node(workflow_state)
                
                print(f"⏸️ [DEBUG] Workflow en pause - nouvelle validation use cases requise")
                
                # Le workflow s'arrête à nouveau pour une nouvelle validation
                return {
                    "success": False,
                    "error": "Nouvelle validation use cases requise",
                    "final_quick_wins": [],
                    "final_structuration_ia": [],
                    "use_case_iteration": workflow_state.get("use_case_iteration", 0),
                    "messages": ["Nouvelle validation use cases requise"]
                }
            else:  # max_iterations
                print(f"❌ [DEBUG] Nombre maximum d'itérations atteint")
                return {
                    "success": False,
                    "error": "Nombre maximum d'itérations atteint",
                    "final_quick_wins": [],
                    "final_structuration_ia": [],
                    "use_case_iteration": workflow_state.get("use_case_iteration", 0),
                    "messages": ["Nombre maximum d'itérations atteint"]
                }
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans resume_use_case_workflow(): {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "final_quick_wins": [],
                "final_structuration_ia": [],
                "messages": [f"Erreur reprise workflow use cases: {str(e)}"]
            }
