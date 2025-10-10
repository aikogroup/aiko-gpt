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

# Import des agents
import sys
sys.path.append('/home/addeche/aiko/aikoGPT')
from need_analysis.need_analysis_agent import NeedAnalysisAgent
from process_atelier.workshop_agent import WorkshopAgent
from process_transcript.transcript_agent import TranscriptAgent
from web_search.web_search_agent import WebSearchAgent
from human_in_the_loop.streamlit_validation_interface import StreamlitValidationInterface


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
    # Données agrégées pour l'analyse
    workshop_data: Dict[str, Any]
    transcript_data: List[Dict[str, Any]]
    web_search_data: Dict[str, Any]
    # Résultats de l'analyse
    identified_needs: List[Dict[str, Any]]
    # Validation humaine
    validated_needs: List[Dict[str, Any]]
    rejected_needs: List[Dict[str, Any]]
    user_feedback: str
    validation_result: Dict[str, Any]
    # État du workflow
    final_needs: List[Dict[str, Any]]
    success: bool
    iteration_count: int
    max_iterations: int
    workflow_paused: bool


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
        self.llm = ChatOpenAI(
            model="gpt-5-nano",
            api_key=api_key
        )
        
        # Initialisation des agents
        self.workshop_agent = WorkshopAgent(api_key)
        self.transcript_agent = TranscriptAgent(api_key)
        self.web_search_agent = WebSearchAgent()  # Pas de paramètre
        self.need_analysis_agent = NeedAnalysisAgent(api_key)
        self.human_interface = StreamlitValidationInterface()
        
        # Création du graphe
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """
        Crée le graphe LangGraph pour le workflow d'analyse des besoins.
        
        Returns:
            StateGraph configuré
        """
        # Création du graphe
        workflow = StateGraph(WorkflowState)
        
        # Ajout des nœuds
        workflow.add_node("start_agents", self._start_agents_node)
        workflow.add_node("collect_data", self._collect_data_node)
        workflow.add_node("analyze_needs", self._analyze_needs_node)
        workflow.add_node("human_validation", self._human_validation_node)
        workflow.add_node("check_success", self._check_success_node)
        workflow.add_node("finalize_results", self._finalize_results_node)
        
        # Définition du flux - point d'entrée selon le mode
        if self.dev_mode:
            workflow.set_entry_point("collect_data")
        else:
            workflow.set_entry_point("start_agents")
        
        # Flux séquentiel
        workflow.add_edge("start_agents", "collect_data")
        
        # Suite du flux
        workflow.add_edge("collect_data", "analyze_needs")
        workflow.add_edge("analyze_needs", "human_validation")
        workflow.add_edge("human_validation", "check_success")
        
        # Conditions de branchement
        workflow.add_conditional_edges(
            "check_success",
            self._should_continue,
            {
                "continue": "analyze_needs",
                "success": "finalize_results",
                "max_iterations": END
            }
        )
        
        workflow.add_edge("finalize_results", END)
        
        return workflow.compile()
    
    def _start_agents_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de démarrage qui lance les 3 agents en parallèle.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            # Exécution des 3 agents en parallèle
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
            
            return state
            
        except Exception as e:
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur démarrage agents: {str(e)}")]
            return state
    
    
    def _collect_data_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud d'agrégation des données des 3 agents.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            if self.dev_mode:
                # Mode développement - charger les données mockées
                import json
                try:
                    # Charger les données mockées
                    with open('/home/addeche/aiko/aikoGPT/workshop_results.json', 'r', encoding='utf-8') as f:
                        workshop_data = json.load(f)
                    
                    with open('/home/addeche/aiko/aikoGPT/transcript_results.json', 'r', encoding='utf-8') as f:
                        transcript_data = json.load(f)
                    
                    with open('/home/addeche/aiko/aikoGPT/web_search_cousin_surgery.json', 'r', encoding='utf-8') as f:
                        web_search_data = json.load(f)
                    
                    # Agrégation des données mockées
                    state["workshop_data"] = {"workshops": workshop_data}
                    state["transcript_data"] = transcript_data.get("results", [])
                    state["web_search_data"] = web_search_data
                    
                except Exception as e:
                    state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur chargement données mockées: {str(e)}")]
                    return state
            else:
                # Mode normal - agrégation des résultats des 3 agents
                state["workshop_data"] = state.get("workshop_results", {})
                state["transcript_data"] = state.get("transcript_results", [])
                state["web_search_data"] = state.get("web_search_results", {})
            
            # Initialisation des compteurs
            state["iteration_count"] = 0
            state["max_iterations"] = 3
            
            return state
            
        except Exception as e:
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur collecte données: {str(e)}")]
            return state
    
    def _analyze_needs_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud d'analyse des besoins.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            # Vérifier s'il y a des besoins déjà validés
            validated_count = len(state.get("validated_needs", []))
            remaining_needs = max(0, 10 - validated_count)
            
            if remaining_needs <= 0:
                # Tous les besoins sont validés
                state["identified_needs"] = []
                return state
            
            # Analyse des besoins avec feedback si disponible
            user_feedback = state.get("user_feedback", "")
            rejected_needs = state.get("rejected_needs", [])
            
            if user_feedback or rejected_needs:
                print(f"\n🔄 Génération de {remaining_needs} nouvelles propositions...")
                if user_feedback:
                    print(f"💬 En tenant compte du feedback: {user_feedback}")
            
            analysis_result = self.need_analysis_agent.analyze_needs(
                state["workshop_data"],
                state["transcript_data"],
                state["web_search_data"]
            )
            
            if "error" in analysis_result:
                state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse: {analysis_result['error']}")]
                return state
            
            # Limiter le nombre de besoins générés
            identified_needs = analysis_result.get("identified_needs", [])
            if len(identified_needs) > remaining_needs:
                identified_needs = identified_needs[:remaining_needs]
            
            state["identified_needs"] = identified_needs
            
            return state
            
        except Exception as e:
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse besoins: {str(e)}")]
            return state
    
    def _human_validation_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de validation humaine via Streamlit.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            # Validation humaine via Streamlit
            validation_result = self.human_interface.validate_needs(
                state["identified_needs"],
                state.get("validated_needs", [])
            )
            
            # Mettre à jour l'état avec les résultats
            state["validated_needs"] = validation_result.get("validated_needs", [])
            state["rejected_needs"] = validation_result.get("rejected_needs", [])
            state["user_feedback"] = validation_result.get("user_feedback", "")
            state["validation_result"] = validation_result
            
            # Sauvegarder l'état pour la reprise
            self.human_interface.save_workflow_state(dict(state))
            
            return state
            
        except Exception as e:
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
            # Vérification du succès
            validated_count = len(state.get("validated_needs", []))
            success = validated_count >= 5
            
            state["success"] = success
            
            if not success:
                # Incrémenter le compteur d'itérations
                state["iteration_count"] = state.get("iteration_count", 0) + 1
                
                print(f"\n🔄 Itération {state['iteration_count']}/{state.get('max_iterations', 3)}")
                print(f"📊 Besoins validés: {validated_count}/5")
                print(f"💬 Feedback: {state.get('user_feedback', 'Aucun')}")
            
            return state
            
        except Exception as e:
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur vérification: {str(e)}")]
            return state
    
    def _finalize_results_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de finalisation des résultats.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            # Filtrage des besoins validés
            validated_needs = []
            if "validation_result" in state and state["validation_result"]:
                validated_ids = state["validation_result"].get("validated_needs", [])
                validated_needs = [
                    need for need in state["identified_needs"]
                    if need.get("id") in validated_ids
                ]
            else:
                # Si pas de validation humaine, utiliser tous les besoins identifiés
                validated_needs = state.get("identified_needs", [])
            
            state["final_needs"] = validated_needs
            
            # Sauvegarde des résultats
            self._save_results(state)
            
            return state
            
        except Exception as e:
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
    
    def run(self, workshop_files: List[str] = None, transcript_files: List[str] = None, company_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Exécute le workflow complet.
        
        Args:
            workshop_files: Liste des fichiers Excel des ateliers
            transcript_files: Liste des fichiers PDF des transcriptions
            company_info: Informations sur l'entreprise pour la recherche web
            
        Returns:
            Résultats du workflow
        """
        try:
            # État initial avec les fichiers d'entrée
            initial_state = WorkflowState(
                messages=[],
                # Fichiers d'entrée
                workshop_files=workshop_files or [],
                transcript_files=transcript_files or [],
                company_info=company_info or {},
                # Résultats des agents (vides au début)
                workshop_results={},
                transcript_results=[],
                web_search_results={},
                # Données agrégées (vides au début)
                workshop_data={},
                transcript_data=[],
                web_search_data={},
                # Résultats de l'analyse
                identified_needs=[],
                # Validation humaine
                validated_needs=[],
                rejected_needs=[],
                user_feedback="",
                validation_result={},
                # État du workflow
                final_needs=[],
                success=False,
                iteration_count=0,
                max_iterations=3,
                workflow_paused=False
            )
            
            # Exécution du workflow
            final_state = self.graph.invoke(initial_state)
            
            return {
                "success": final_state.get("success", False),
                "final_needs": final_state.get("final_needs", []),
                "summary": {
                    "total_needs": len(final_state.get("final_needs", [])),
                    "themes": list(set([need.get("theme", "") for need in final_state.get("final_needs", []) if need.get("theme")])),
                    "high_priority_count": 0  # Pas de priorité dans la structure simplifiée
                },
                "iteration_count": final_state.get("iteration_count", 0),
                "workshop_results": final_state.get("workshop_results", {}),
                "transcript_results": final_state.get("transcript_results", []),
                "web_search_results": final_state.get("web_search_results", {}),
                "messages": [msg.content for msg in final_state.get("messages", [])]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "final_needs": [],
                "iteration_count": 0,
                "messages": [f"Erreur workflow: {str(e)}"]
            }
