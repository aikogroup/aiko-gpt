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
        
        # Configuration du checkpointer pour le debugging
        self.checkpointer = self._setup_checkpointer()
        
        # Création du graphe
        self.graph = self._create_graph()
    
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
        
        # Configuration pour le debugging
        compile_kwargs = {}
        if self.debug_mode and self.checkpointer:
            compile_kwargs["checkpointer"] = self.checkpointer
            # Points d'interruption pour le debugging
            compile_kwargs["interrupt_before"] = ["analyze_needs", "human_validation"]
            compile_kwargs["interrupt_after"] = ["start_agents", "collect_data"]
            # Mode debug activé
            compile_kwargs["debug"] = True
        
        return workflow.compile(**compile_kwargs)
    
    def _start_agents_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de démarrage qui lance les 3 agents en parallèle.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        print(f"\n🚀 [DEBUG] _start_agents_node - DÉBUT")
        print(f"📊 État d'entrée: {len(state.get('workshop_files', []))} fichiers workshop, {len(state.get('transcript_files', []))} fichiers transcript")
        
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
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        print(f"\n📊 [DEBUG] _collect_data_node - DÉBUT")
        print(f"🔄 Mode dev: {self.dev_mode}")
        
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
                    # Les données JSON sont déjà des dictionnaires, pas besoin de conversion
                    state["workshop_data"] = {"workshops": workshop_data}
                    state["transcript_data"] = transcript_data.get("results", [])
                    state["web_search_data"] = web_search_data
                    
                    # AUSSI sauvegarder dans les champs de résultats pour la cohérence
                    state["workshop_results"] = {"workshops": workshop_data}
                    state["transcript_results"] = transcript_data.get("results", [])
                    state["web_search_results"] = web_search_data
                    
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
            
            print(f"✅ [DEBUG] _collect_data_node - FIN")
            print(f"📊 Données agrégées: {len(state.get('workshop_data', {}).get('workshops', []))} workshops, {len(state.get('transcript_data', []))} transcripts, {len(state.get('web_search_data', {}))} recherches")
            
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _collect_data_node: {str(e)}")
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
        print(f"\n🔍 [DEBUG] _analyze_needs_node - DÉBUT")
        print(f"📊 Besoins déjà validés: {len(state.get('validated_needs', []))}")
        print(f"🔄 Itération: {state.get('iteration_count', 0)}/{state.get('max_iterations', 3)}")
        
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
            
            print(f"✅ [DEBUG] _analyze_needs_node - FIN")
            print(f"📊 Besoins identifiés: {len(identified_needs)}")
            print(f"🎯 Besoins validés total: {len(state.get('validated_needs', []))}")
            
            return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _analyze_needs_node: {str(e)}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur analyse besoins: {str(e)}")]
            return state
    
    def _human_validation_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de validation humaine via Streamlit.
        NOUVELLE APPROCHE: Utilise session_state pour gérer l'interruption.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        print(f"\n🛑 [DEBUG] ===== _human_validation_node - DÉBUT =====")
        print(f"📊 identified_needs: {len(state.get('identified_needs', []))}")
        print(f"📊 validated_needs: {len(state.get('validated_needs', []))}")
        print(f"🔄 [DEBUG] Session state avant validation: {list(st.session_state.keys()) if 'st' in globals() else 'Streamlit non disponible'}")
        
        try:
            # Sauvegarder l'état du workflow dans session_state
            print(f"💾 [DEBUG] Sauvegarde de l'état du workflow")
            # Sauvegarder toutes les données importantes
            workflow_state = {
                "messages": state.get("messages", []),
                "workshop_files": state.get("workshop_files", []),
                "transcript_files": state.get("transcript_files", []),
                "company_info": state.get("company_info", {}),
                "workshop_results": state.get("workshop_results", {}),
                "transcript_results": state.get("transcript_results", []),
                "web_search_results": state.get("web_search_results", {}),
                "workshop_data": state.get("workshop_data", {}),
                "transcript_data": state.get("transcript_data", []),
                "web_search_data": state.get("web_search_data", {}),
                "identified_needs": state.get("identified_needs", []),
                "validated_needs": state.get("validated_needs", []),
                "rejected_needs": state.get("rejected_needs", []),
                "user_feedback": state.get("user_feedback", ""),
                "validation_result": state.get("validation_result", {}),
                "final_needs": state.get("final_needs", []),
                "success": state.get("success", False),
                "iteration_count": state.get("iteration_count", 0),
                "max_iterations": state.get("max_iterations", 3),
                "workflow_paused": state.get("workflow_paused", False)
            }
            st.session_state.workflow_state = workflow_state
            st.session_state.workflow_paused = True
            st.session_state.waiting_for_validation = True
            print(f"💾 [DEBUG] État sauvegardé avec {len(workflow_state)} clés")
            
            # Vérifier si on a déjà des résultats de validation
            if "validation_result" in st.session_state and st.session_state.validation_result:
                print(f"✅ [DEBUG] Résultats de validation trouvés dans session_state")
                validation_data = st.session_state.validation_result
                
                # Traiter les résultats de validation
                if validation_data and "validated_needs" in validation_data:
                    # Accumuler les besoins validés
                    existing_validated = state.get("validated_needs", [])
                    newly_validated = validation_data.get("validated_needs", [])
                    state["validated_needs"] = existing_validated + newly_validated
                    
                    # Accumuler les besoins rejetés
                    existing_rejected = state.get("rejected_needs", [])
                    newly_rejected = validation_data.get("rejected_needs", [])
                    state["rejected_needs"] = existing_rejected + newly_rejected
                    
                    state["user_feedback"] = validation_data.get("user_feedback", "")
                    state["validation_result"] = validation_data
                    
                    print(f"📊 [DEBUG] Besoins validés total: {len(state['validated_needs'])}")
                    print(f"📊 [DEBUG] Besoins rejetés total: {len(state['rejected_needs'])}")
                
                # Nettoyer l'état de validation
                if "validation_result" in st.session_state:
                    del st.session_state.validation_result
                
                # Reprendre le workflow
                state["workflow_paused"] = False
                st.session_state.workflow_paused = False
                st.session_state.waiting_for_validation = False
                print(f"▶️ [DEBUG] Workflow repris après validation")
                print(f"🛑 [DEBUG] ===== _human_validation_node - FIN =====")
                
                return state
            else:
                # Première fois : afficher l'interface de validation
                print(f"⏸️ [DEBUG] Affichage de l'interface de validation")
                
                # Afficher l'interface de validation
                self.human_interface.display_needs_for_validation(
                    state["identified_needs"],
                    len(state.get("validated_needs", []))
                )
                
                # En attente de validation - retourner l'état actuel
                print(f"⏳ [DEBUG] En attente de validation - workflow en pause")
                return state
            
        except Exception as e:
            print(f"❌ [DEBUG] Erreur dans _human_validation_node: {str(e)}")
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
            # Vérifier si on est en attente de validation
            if state.get("workflow_paused", False) or st.session_state.get("waiting_for_validation", False):
                print(f"⏳ [DEBUG] Workflow en pause - en attente de validation")
                return state
            
            # Vérification du succès
            validated_count = len(state.get("validated_needs", []))
            success = validated_count >= 5
            
            state["success"] = success
            
            # CORRECTION: Afficher les logs APRÈS la validation, pas avant
            print(f"\n🔄 [DEBUG] _check_success_node - APRÈS validation")
            print(f"📊 Besoins validés: {validated_count}/5")
            print(f"🎯 Succès: {success}")
            
            if not success:
                # Incrémenter le compteur d'itérations
                state["iteration_count"] = state.get("iteration_count", 0) + 1
                
                print(f"🔄 Itération {state['iteration_count']}/{state.get('max_iterations', 3)}")
                print(f"💬 Feedback: {state.get('user_feedback', 'Aucun')}")
            else:
                print(f"✅ Objectif atteint ! {validated_count} besoins validés")
            
            return state
            
        except Exception as e:
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur vérification: {str(e)}")]
            return state
    
    def _finalize_results_node(self, state: WorkflowState) -> WorkflowState:
        """
        Nœud de finalisation des résultats.
        VERSION CORRIGÉE: Utilise directement les besoins validés.
        
        Args:
            state: État actuel du workflow
            
        Returns:
            État mis à jour
        """
        try:
            print(f"🔍 [DEBUG] _finalize_results_node - DÉBUT")
            print(f"📊 [DEBUG] validation_result présent: {'validation_result' in state}")
            print(f"📊 [DEBUG] validated_needs dans state: {len(state.get('validated_needs', []))}")
            
            # Utiliser directement les besoins validés depuis l'état
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
        NOUVELLE ARCHITECTURE: Le workflow s'arrête au nœud human_validation.
        
        Args:
            workshop_files: Liste des fichiers Excel des ateliers
            transcript_files: Liste des fichiers PDF des transcriptions
            company_info: Informations sur l'entreprise pour la recherche web
            
        Returns:
            Résultats du workflow
        """
        print(f"\n🚀 [DEBUG] run() appelé - NOUVELLE ARCHITECTURE")
        
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
            
            print(f"🔄 [DEBUG] Exécution du workflow jusqu'au nœud human_validation...")
            
            # Exécution du workflow JUSQU'AU NŒUD HUMAN_VALIDATION
            # Le workflow va s'arrêter là et attendre la validation humaine
            final_state = self.graph.invoke(initial_state)
            
            print(f"✅ [DEBUG] Workflow terminé après validation humaine")
            print(f"📊 [DEBUG] Success: {final_state.get('success', False)}")
            print(f"📊 [DEBUG] Final needs: {len(final_state.get('final_needs', []))}")
            
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
            print(f"❌ [DEBUG] Erreur dans run(): {str(e)}")
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
            
            # Mettre à jour l'état avec les résultats de validation
            workflow_state["validated_needs"] = validation_result.get("validated_needs", [])
            workflow_state["rejected_needs"] = validation_result.get("rejected_needs", [])
            workflow_state["user_feedback"] = validation_result.get("user_feedback", "")
            workflow_state["validation_result"] = validation_result
            
            # Exécuter les nœuds suivants manuellement
            print(f"🔄 [DEBUG] Exécution des nœuds suivants après validation...")
            
            # 1. Vérifier le succès
            print(f"🔍 [DEBUG] _check_success_node - DÉBUT")
            workflow_state = self._check_success_node(workflow_state)
            print(f"✅ [DEBUG] _check_success_node - FIN")
            
            # 2. Déterminer la suite selon le résultat
            should_continue = self._should_continue(workflow_state)
            print(f"📊 [DEBUG] Décision de continuation: {should_continue}")
            
            if should_continue == "success":
                # 3. Finaliser les résultats
                print(f"🔍 [DEBUG] _finalize_results_node - DÉBUT")
                workflow_state = self._finalize_results_node(workflow_state)
                print(f"✅ [DEBUG] _finalize_results_node - FIN")
                
                print(f"✅ [DEBUG] Workflow terminé avec succès")
                print(f"📊 [DEBUG] Success: {workflow_state.get('success', False)}")
                print(f"📊 [DEBUG] Final needs: {len(workflow_state.get('final_needs', []))}")
                
                return {
                    "success": workflow_state.get("success", False),
                    "final_needs": workflow_state.get("final_needs", []),
                    "summary": {
                        "total_needs": len(workflow_state.get("final_needs", [])),
                        "themes": list(set([need.get("theme", "") for need in workflow_state.get("final_needs", []) if need.get("theme")])),
                        "high_priority_count": 0
                    },
                    "iteration_count": workflow_state.get("iteration_count", 0),
                    "workshop_results": workflow_state.get("workshop_results", {}),
                    "transcript_results": workflow_state.get("transcript_results", []),
                    "web_search_results": workflow_state.get("web_search_results", {}),
                    "messages": [msg.content for msg in workflow_state.get("messages", [])]
                }
            elif should_continue == "continue":
                # 4. Continuer avec une nouvelle analyse
                print(f"🔍 [DEBUG] _analyze_needs_node - DÉBUT (nouvelle itération)")
                workflow_state = self._analyze_needs_node(workflow_state)
                print(f"✅ [DEBUG] _analyze_needs_node - FIN")
                
                # 5. Nouvelle validation humaine
                print(f"🛑 [DEBUG] ===== _human_validation_node - DÉBUT (nouvelle validation) =====")
                workflow_state = self._human_validation_node(workflow_state)
                print(f"⏳ [DEBUG] Workflow en pause - nouvelle validation requise")
                
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
