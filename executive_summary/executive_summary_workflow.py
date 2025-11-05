"""
Workflow LangGraph pour l'Executive Summary
"""

import os
import json
from typing import Dict, List, Any, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
import sys
sys.path.append('/home/addeche/aiko/aikoGPT')

from executive_summary.word_report_extractor import WordReportExtractor
from executive_summary.transcript_enjeux_agent import TranscriptEnjeuxAgent
from executive_summary.workshop_enjeux_agent import WorkshopEnjeuxAgent
from executive_summary.transcript_maturite_agent import TranscriptMaturiteAgent
from executive_summary.workshop_maturite_agent import WorkshopMaturiteAgent
from executive_summary.executive_summary_agent import ExecutiveSummaryAgent
from utils.token_tracker import TokenTracker


class ExecutiveSummaryState(TypedDict):
    """État du workflow LangGraph pour Executive Summary"""
    messages: Annotated[List[BaseMessage], add_messages]
    # Fichiers
    word_report_path: str
    transcript_files: List[str]
    workshop_files: List[str]
    company_name: str
    interviewer_note: str
    # Extraction Word
    extracted_needs: List[Dict]
    extracted_quick_wins: List[Dict]
    extracted_structuration_ia: List[Dict]
    # Citations extraites
    transcript_enjeux_citations: List[Dict]
    workshop_enjeux_citations: List[Dict]
    transcript_maturite_citations: List[Dict]
    workshop_maturite_citations: List[Dict]
    # Résultats Enjeux
    identified_challenges: List[Dict]
    validated_challenges: List[Dict]
    rejected_challenges: List[Dict]
    challenges_feedback: str
    challenges_iteration_count: int
    max_challenges_iterations: int
    challenges_success: bool
    # Résultats Maturité
    maturity_score: int
    maturity_summary: str
    # Résultats Recommandations
    recommendations: List[str]
    validated_recommendations: List[str]
    rejected_recommendations: List[str]
    recommendations_feedback: str
    recommendations_iteration_count: int
    max_recommendations_iterations: int
    recommendations_success: bool
    # Validation
    workflow_paused: bool
    validation_type: str  # "challenges" ou "recommendations"
    validation_result: Dict[str, Any]


class ExecutiveSummaryWorkflow:
    """Workflow LangGraph pour l'Executive Summary"""
    
    def __init__(self, api_key: str, dev_mode: bool = False, debug_mode: bool = False):
        """
        Initialise le workflow.
        
        Args:
            api_key: Clé API OpenAI
            dev_mode: Mode développement
            debug_mode: Mode debugging
        """
        self.api_key = api_key
        self.dev_mode = dev_mode
        self.debug_mode = debug_mode
        
        model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key
        )
        
        # Initialiser les agents
        self.word_extractor = WordReportExtractor(api_key=api_key)
        self.transcript_enjeux_agent = TranscriptEnjeuxAgent(api_key=api_key)
        self.workshop_enjeux_agent = WorkshopEnjeuxAgent(api_key=api_key)
        self.transcript_maturite_agent = TranscriptMaturiteAgent(api_key=api_key)
        self.workshop_maturite_agent = WorkshopMaturiteAgent(api_key=api_key)
        self.executive_agent = ExecutiveSummaryAgent(api_key=api_key)
        
        # Token tracker
        self.tracker = TokenTracker()
        
        # Compiler le graphe
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Crée le graphe LangGraph"""
        workflow = StateGraph(ExecutiveSummaryState)
        
        # Ajout des nœuds
        workflow.add_node("dispatcher", self._dispatcher_node)
        workflow.add_node("extract_word", self._extract_word_node)
        workflow.add_node("transcript_enjeux", self._transcript_enjeux_node)
        workflow.add_node("workshop_enjeux", self._workshop_enjeux_node)
        workflow.add_node("transcript_maturite", self._transcript_maturite_node)
        workflow.add_node("workshop_maturite", self._workshop_maturite_node)
        workflow.add_node("collect_citations", self._collect_citations_node)
        workflow.add_node("identify_challenges", self._identify_challenges_node)
        workflow.add_node("human_validation_enjeux", self._human_validation_enjeux_node)
        workflow.add_node("check_challenges_success", self._check_challenges_success_node)
        workflow.add_node("evaluate_maturity", self._evaluate_maturity_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("human_validation_recommendations", self._human_validation_recommendations_node)
        workflow.add_node("check_recommendations_success", self._check_recommendations_success_node)
        workflow.add_node("finalize_results", self._finalize_results_node)
        
        # Point d'entrée
        workflow.set_entry_point("dispatcher")
        
        # Flux parallèle : extraction Word + 4 agents spécialisés
        workflow.add_edge("dispatcher", "extract_word")
        workflow.add_edge("dispatcher", "transcript_enjeux")
        workflow.add_edge("dispatcher", "workshop_enjeux")
        workflow.add_edge("dispatcher", "transcript_maturite")
        workflow.add_edge("dispatcher", "workshop_maturite")
        
        # Convergence vers collect_citations
        workflow.add_edge("extract_word", "collect_citations")
        workflow.add_edge("transcript_enjeux", "collect_citations")
        workflow.add_edge("workshop_enjeux", "collect_citations")
        workflow.add_edge("transcript_maturite", "collect_citations")
        workflow.add_edge("workshop_maturite", "collect_citations")
        
        # Flux séquentiel : Enjeux
        workflow.add_edge("collect_citations", "identify_challenges")
        workflow.add_edge("identify_challenges", "human_validation_enjeux")
        workflow.add_edge("human_validation_enjeux", "check_challenges_success")
        
        # Conditions de branchement - Enjeux
        workflow.add_conditional_edges(
            "check_challenges_success",
            self._should_continue_challenges,
            {
                "continue": "identify_challenges",
                "success": "evaluate_maturity",
                "max_iterations": END
            }
        )
        
        # Flux séquentiel : Maturité et Recommandations
        workflow.add_edge("evaluate_maturity", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "human_validation_recommendations")
        workflow.add_edge("human_validation_recommendations", "check_recommendations_success")
        
        # Conditions de branchement - Recommandations
        workflow.add_conditional_edges(
            "check_recommendations_success",
            self._should_continue_recommendations,
            {
                "continue": "generate_recommendations",
                "success": "finalize_results",
                "max_iterations": END
            }
        )
        
        workflow.add_edge("finalize_results", END)
        
        # Configuration avec checkpointer et interrupts
        compile_kwargs = {
            "checkpointer": MemorySaver(),
            "interrupt_before": ["human_validation_enjeux", "human_validation_recommendations"]
        }
        
        if self.debug_mode:
            compile_kwargs["interrupt_after"] = ["dispatcher", "collect_citations"]
            compile_kwargs["debug"] = True
        
        return workflow.compile(**compile_kwargs)
    
    def run(
        self,
        word_report_path: str,
        transcript_files: List[str],
        workshop_files: List[str],
        company_name: str,
        interviewer_note: str = "",
        thread_id: str = None
    ) -> Dict[str, Any]:
        """
        Exécute le workflow.
        
        Args:
            word_report_path: Chemin vers le fichier Word
            transcript_files: Liste des fichiers de transcript
            workshop_files: Liste des fichiers d'ateliers
            company_name: Nom de l'entreprise
            interviewer_note: Note de l'intervieweur
            thread_id: ID du thread pour la persistance
            
        Returns:
            État final du workflow
        """
        initial_state = {
            "messages": [],
            "word_report_path": word_report_path,
            "transcript_files": transcript_files or [],
            "workshop_files": workshop_files or [],
            "company_name": company_name,
            "interviewer_note": interviewer_note,
            "extracted_needs": [],
            "extracted_quick_wins": [],
            "extracted_structuration_ia": [],
            "transcript_enjeux_citations": [],
            "workshop_enjeux_citations": [],
            "transcript_maturite_citations": [],
            "workshop_maturite_citations": [],
            "identified_challenges": [],
            "validated_challenges": [],
            "rejected_challenges": [],
            "challenges_feedback": "",
            "challenges_iteration_count": 0,
            "max_challenges_iterations": 3,
            "challenges_success": False,
            "maturity_score": 3,
            "maturity_summary": "",
            "recommendations": [],
            "validated_recommendations": [],
            "rejected_recommendations": [],
            "recommendations_feedback": "",
            "recommendations_iteration_count": 0,
            "max_recommendations_iterations": 3,
            "recommendations_success": False,
            "workflow_paused": False,
            "validation_type": "",
            "validation_result": {}
        }
        
        config = {"configurable": {"thread_id": thread_id or "default"}} if thread_id else {}
        
        # Exécuter le workflow jusqu'à l'interrupt (human_validation_enjeux ou human_validation_recommendations)
        print(f"🚀 [EXECUTIVE] Exécution du workflow avec thread_id: {config.get('configurable', {}).get('thread_id', 'default')}")
        
        # Le workflow va s'arrêter à human_validation car c'est défini dans interrupt_before
        final_state = None
        for chunk in self.graph.stream(initial_state, config):
            print(f"📊 [EXECUTIVE] Chunk reçu: {list(chunk.keys())}")
            # Chaque chunk contient l'état mis à jour par un nœud
            for node_name, node_state in chunk.items():
                print(f"  • Nœud '{node_name}' exécuté")
                final_state = node_state
        
        # IMPORTANT : Récupérer l'état complet depuis le checkpointer après l'interrupt
        # car le dernier chunk (__interrupt__) ne contient pas l'état complet
        snapshot = self.graph.get_state(config)
        if snapshot and snapshot.values:
            state = snapshot.values
            print(f"📊 [EXECUTIVE] État récupéré depuis le checkpointer")
            print(f"📊 [EXECUTIVE] Enjeux identifiés: {len(state.get('identified_challenges', []))}")
            print(f"📊 [EXECUTIVE] Enjeux validés: {len(state.get('validated_challenges', []))}")
            
            # Si on est à un interrupt, déterminer le type de validation
            if snapshot.next:
                next_nodes = list(snapshot.next) if hasattr(snapshot.next, '__iter__') else [snapshot.next]
                if "human_validation_enjeux" in next_nodes:
                    state["workflow_paused"] = True
                    state["validation_type"] = "challenges"
                    print(f"🛑 [EXECUTIVE] Workflow en pause pour validation des enjeux")
                elif "human_validation_recommendations" in next_nodes:
                    state["workflow_paused"] = True
                    state["validation_type"] = "recommendations"
                    print(f"🛑 [EXECUTIVE] Workflow en pause pour validation des recommandations")
            
            print(f"📊 [EXECUTIVE] Workflow paused: {state.get('workflow_paused', False)}")
            print(f"📊 [EXECUTIVE] Validation type: {state.get('validation_type', '')}")
            
            # Mettre à jour l'état dans le checkpointer si on a modifié les flags
            if state.get("workflow_paused") or state.get("validation_type"):
                self.graph.update_state(config, state)
            
            return state
        else:
            # Fallback si pas d'état dans le checkpointer
            return final_state if final_state else initial_state
    
    # ==================== NŒUDS DU WORKFLOW ====================
    
    def _dispatcher_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Nœud dispatcher qui prépare le travail"""
        print(f"\n🚀 [EXECUTIVE] dispatcher_node - DÉBUT")
        print(f"📊 Fichiers: Word={bool(state.get('word_report_path'))}, "
              f"Transcripts={len(state.get('transcript_files', []))}, "
              f"Workshops={len(state.get('workshop_files', []))}")
        return state
    
    def _extract_word_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait les données depuis le fichier Word"""
        print(f"\n📄 [EXECUTIVE] extract_word_node - DÉBUT")
        try:
            word_path = state.get("word_report_path", "")
            if not word_path:
                print("⚠️ Aucun fichier Word fourni")
                return {}
            
            extracted = self.word_extractor.extract_from_word(word_path)
            
            extracted_needs = extracted.get("final_needs", [])
            extracted_quick_wins = extracted.get("final_quick_wins", [])
            extracted_structuration_ia = extracted.get("final_structuration_ia", [])
            
            print(f"✅ Extraction: {len(extracted_needs)} besoins, "
                  f"{len(extracted_quick_wins)} Quick Wins, "
                  f"{len(extracted_structuration_ia)} Structuration IA")
            
            # Afficher le détail des Quick Wins et Structuration IA
            print(f"\n📊 [EXECUTIVE] DÉTAIL DES QUICK WINS ({len(extracted_quick_wins)}):")
            for i, qw in enumerate(extracted_quick_wins, 1):
                titre = qw.get("titre", "N/A")
                print(f"   {i}. {titre}")
            
            print(f"\n📊 [EXECUTIVE] DÉTAIL DES STRUCTURATION IA ({len(extracted_structuration_ia)}):")
            for i, sia in enumerate(extracted_structuration_ia, 1):
                titre = sia.get("titre", "N/A")
                print(f"   {i}. {titre}")
            
            return {
                "extracted_needs": extracted_needs,
                "extracted_quick_wins": extracted_quick_wins,
                "extracted_structuration_ia": extracted_structuration_ia
            }
            
        except Exception as e:
            print(f"❌ Erreur extraction Word: {e}")
            return {
                "messages": [HumanMessage(content=f"Erreur extraction Word: {str(e)}")]
            }
    
    def _transcript_enjeux_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait citations enjeux depuis transcripts"""
        print(f"\n📝 [EXECUTIVE] transcript_enjeux_node - DÉBUT")
        try:
            transcript_files = state.get("transcript_files", [])
            if not transcript_files:
                print("⚠️ Aucun fichier transcript")
                return {"transcript_enjeux_citations": []}
            
            citations = self.transcript_enjeux_agent.extract_citations(transcript_files)
            print(f"✅ {len(citations)} citations d'enjeux extraites")
            
            return {"transcript_enjeux_citations": citations}
            
        except Exception as e:
            print(f"❌ Erreur transcript_enjeux: {e}")
            return {"transcript_enjeux_citations": []}
    
    def _workshop_enjeux_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait informations enjeux depuis ateliers"""
        print(f"\n📊 [EXECUTIVE] workshop_enjeux_node - DÉBUT")
        try:
            workshop_files = state.get("workshop_files", [])
            if not workshop_files:
                print("⚠️ Aucun fichier workshop")
                return {"workshop_enjeux_citations": []}
            
            informations = self.workshop_enjeux_agent.extract_informations(workshop_files)
            print(f"✅ {len(informations)} informations d'enjeux extraites")
            
            return {"workshop_enjeux_citations": informations}
            
        except Exception as e:
            print(f"❌ Erreur workshop_enjeux: {e}")
            return {"workshop_enjeux_citations": []}
    
    def _transcript_maturite_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait citations maturité depuis transcripts"""
        print(f"\n📝 [EXECUTIVE] transcript_maturite_node - DÉBUT")
        try:
            transcript_files = state.get("transcript_files", [])
            if not transcript_files:
                print("⚠️ Aucun fichier transcript")
                return {"transcript_maturite_citations": []}
            
            citations = self.transcript_maturite_agent.extract_citations(transcript_files)
            print(f"✅ {len(citations)} citations de maturité extraites")
            
            return {"transcript_maturite_citations": citations}
            
        except Exception as e:
            print(f"❌ Erreur transcript_maturite: {e}")
            return {"transcript_maturite_citations": []}
    
    def _workshop_maturite_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait informations maturité depuis ateliers"""
        print(f"\n📊 [EXECUTIVE] workshop_maturite_node - DÉBUT")
        try:
            workshop_files = state.get("workshop_files", [])
            if not workshop_files:
                print("⚠️ Aucun fichier workshop")
                return {"workshop_maturite_citations": []}
            
            informations = self.workshop_maturite_agent.extract_informations(workshop_files)
            print(f"✅ {len(informations)} informations de maturité extraites")
            
            return {"workshop_maturite_citations": informations}
            
        except Exception as e:
            print(f"❌ Erreur workshop_maturite: {e}")
            return {"workshop_maturite_citations": []}
    
    def _collect_citations_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Agrège toutes les citations collectées"""
        print(f"\n🔄 [EXECUTIVE] collect_citations_node - DÉBUT")
        print(f"📊 Citations collectées:")
        print(f"   - Enjeux transcripts: {len(state.get('transcript_enjeux_citations', []))}")
        print(f"   - Enjeux workshops: {len(state.get('workshop_enjeux_citations', []))}")
        print(f"   - Maturité transcripts: {len(state.get('transcript_maturite_citations', []))}")
        print(f"   - Maturité workshops: {len(state.get('workshop_maturite_citations', []))}")
        
        # Afficher le contenu détaillé
        print(f"\n📝 [EXECUTIVE] DÉTAIL DES ENJEUX TRANSCRIPTS:")
        for i, cit in enumerate(state.get('transcript_enjeux_citations', []), 1):
            speaker = cit.get("speaker", "N/A")
            citation = cit.get("citation", "N/A")
            print(f"   {i}. [{speaker}] {citation[:100]}...")
        
        print(f"\n📊 [EXECUTIVE] DÉTAIL DES ENJEUX WORKSHOPS:")
        for i, info in enumerate(state.get('workshop_enjeux_citations', []), 1):
            atelier = info.get("atelier", "N/A")
            use_case = info.get("use_case", "N/A")
            objectif = info.get("objectif", "N/A")
            print(f"   {i}. [{atelier}] {use_case}: {objectif[:100]}...")
        
        print(f"\n📝 [EXECUTIVE] DÉTAIL DE LA MATURITÉ TRANSCRIPTS:")
        for i, cit in enumerate(state.get('transcript_maturite_citations', []), 1):
            speaker = cit.get("speaker", "N/A")
            citation = cit.get("citation", "N/A")
            type_info = cit.get("type_info", "N/A")
            print(f"   {i}. [{type_info}] [{speaker}] {citation[:100]}...")
        
        print(f"\n📊 [EXECUTIVE] DÉTAIL DE LA MATURITÉ WORKSHOPS:")
        for i, info in enumerate(state.get('workshop_maturite_citations', []), 1):
            atelier = info.get("atelier", "N/A")
            use_case = info.get("use_case", "N/A")
            type_info = info.get("type_info", "N/A")
            print(f"   {i}. [{type_info}] [{atelier}] {use_case}")
        
        return state
    
    def _identify_challenges_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Identifie les 5 enjeux stratégiques"""
        print(f"\n🎯 [EXECUTIVE] identify_challenges_node - DÉBUT")
        try:
            # Préparer le contenu
            transcript_content = self._format_citations(state.get("transcript_enjeux_citations", []))
            workshop_content = self._format_workshop_info(state.get("workshop_enjeux_citations", []))
            final_needs = state.get("extracted_needs", [])
            
            # Récupérer les enjeux rejetés et validés pour régénération
            rejected = state.get("rejected_challenges", [])
            validated = state.get("validated_challenges", [])
            feedback = state.get("challenges_feedback", "")
            
            result = self.executive_agent.identify_challenges(
                transcript_content=transcript_content,
                workshop_content=workshop_content,
                final_needs=final_needs,
                rejected_challenges=rejected if rejected else None,
                validated_challenges=validated if validated else None,
                challenges_feedback=feedback
            )
            
            state["identified_challenges"] = result.get("challenges", [])
            print(f"✅ {len(state['identified_challenges'])} enjeux identifiés")
            
            return state
            
        except Exception as e:
            print(f"❌ Erreur identification enjeux: {e}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur identification: {str(e)}")]
            return state
    
    def _human_validation_enjeux_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Nœud de validation humaine des enjeux"""
        print(f"\n🛑 [EXECUTIVE] human_validation_enjeux_node - DÉBUT")
        print(f"📊 identified_challenges: {len(state.get('identified_challenges', []))}")
        
        try:
            if "validation_result" in state and state["validation_result"]:
                print(f"✅ [RESUME] Feedback reçu via API")
                validation_data = state["validation_result"]
                
                existing_validated = state.get("validated_challenges", [])
                newly_validated = validation_data.get("validated_challenges", [])
                
                existing_ids = [ch.get("id", "") for ch in existing_validated]
                unique_newly_validated = [ch for ch in newly_validated if ch.get("id", "") not in existing_ids]
                
                state["validated_challenges"] = existing_validated + unique_newly_validated
                state["rejected_challenges"] = validation_data.get("rejected_challenges", [])
                state["challenges_feedback"] = validation_data.get("challenges_feedback", "")
                state["validation_result"] = {}
                state["validation_type"] = ""
                
                print(f"📊 Enjeux nouvellement validés: {len(unique_newly_validated)}")
                print(f"📊 Total enjeux validés: {len(state['validated_challenges'])}")
                
                return state
            else:
                print(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                state["validation_type"] = "challenges"
                state["workflow_paused"] = True
                return state
                
        except Exception as e:
            print(f"❌ Erreur validation enjeux: {e}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur validation: {str(e)}")]
            return state
    
    def _check_challenges_success_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Vérifie le succès de la validation des enjeux"""
        print(f"\n🔄 [EXECUTIVE] check_challenges_success_node - DÉBUT")
        
        validated_count = len(state.get("validated_challenges", []))
        success = validated_count >= 5
        
        state["challenges_success"] = success
        
        print(f"📊 Enjeux validés: {validated_count}/5")
        print(f"🎯 Succès: {success}")
        
        if not success:
            state["challenges_iteration_count"] = state.get("challenges_iteration_count", 0) + 1
            print(f"🔄 Itération {state['challenges_iteration_count']}/{state.get('max_challenges_iterations', 3)}")
        else:
            print(f"✅ Objectif atteint ! {validated_count} enjeux validés")
        
        return state
    
    def _evaluate_maturity_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Évalue la maturité IA"""
        print(f"\n📊 [EXECUTIVE] evaluate_maturity_node - DÉBUT")
        try:
            transcript_content = self._format_maturite_citations(state.get("transcript_maturite_citations", []))
            workshop_content = self._format_workshop_maturite(state.get("workshop_maturite_citations", []))
            final_needs = state.get("extracted_needs", [])
            final_quick_wins = state.get("extracted_quick_wins", [])
            final_structuration_ia = state.get("extracted_structuration_ia", [])
            
            print(f"📊 [EXECUTIVE] Données pour évaluation maturité:")
            print(f"   - Quick Wins: {len(final_quick_wins)}")
            print(f"   - Structuration IA: {len(final_structuration_ia)}")
            
            result = self.executive_agent.evaluate_maturity(
                transcript_content=transcript_content,
                workshop_content=workshop_content,
                final_needs=final_needs,
                final_quick_wins=final_quick_wins,
                final_structuration_ia=final_structuration_ia
            )
            
            state["maturity_score"] = result.get("echelle", 3)
            state["maturity_summary"] = result.get("phrase_resumant", "")
            
            print(f"✅ Maturité IA: {state['maturity_score']}/5")
            print(f"📝 Phrase descriptive: {state['maturity_summary']}")
            
            return state
            
        except Exception as e:
            print(f"❌ Erreur évaluation maturité: {e}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur maturité: {str(e)}")]
            return state
    
    def _generate_recommendations_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Génère les 4 recommandations"""
        print(f"\n💡 [EXECUTIVE] generate_recommendations_node - DÉBUT")
        try:
            maturite_ia = {
                "echelle": state.get("maturity_score", 3),
                "phrase_resumant": state.get("maturity_summary", "")
            }
            final_needs = state.get("extracted_needs", [])
            final_quick_wins = state.get("extracted_quick_wins", [])
            final_structuration_ia = state.get("extracted_structuration_ia", [])
            
            rejected = state.get("rejected_recommendations", [])
            validated = state.get("validated_recommendations", [])
            feedback = state.get("recommendations_feedback", "")
            
            result = self.executive_agent.generate_recommendations(
                maturite_ia=maturite_ia,
                final_needs=final_needs,
                final_quick_wins=final_quick_wins,
                final_structuration_ia=final_structuration_ia,
                rejected_recommendations=rejected if rejected else None,
                validated_recommendations=validated if validated else None,
                recommendations_feedback=feedback
            )
            
            state["recommendations"] = result.get("recommendations", [])
            print(f"✅ {len(state['recommendations'])} recommandations générées")
            
            return state
            
        except Exception as e:
            print(f"❌ Erreur génération recommandations: {e}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur recommandations: {str(e)}")]
            return state
    
    def _human_validation_recommendations_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Nœud de validation humaine des recommandations"""
        print(f"\n🛑 [EXECUTIVE] human_validation_recommendations_node - DÉBUT")
        print(f"📊 recommendations: {len(state.get('recommendations', []))}")
        
        try:
            if "validation_result" in state and state["validation_result"]:
                print(f"✅ [RESUME] Feedback reçu via API")
                validation_data = state["validation_result"]
                
                existing_validated = state.get("validated_recommendations", [])
                newly_validated = validation_data.get("validated_recommendations", [])
                
                # Éviter les doublons
                unique_newly_validated = [r for r in newly_validated if r not in existing_validated]
                
                state["validated_recommendations"] = existing_validated + unique_newly_validated
                state["rejected_recommendations"] = validation_data.get("rejected_recommendations", [])
                state["recommendations_feedback"] = validation_data.get("recommendations_feedback", "")
                state["validation_result"] = {}
                state["validation_type"] = ""
                
                print(f"📊 Recommandations nouvellement validées: {len(unique_newly_validated)}")
                print(f"📊 Total recommandations validées: {len(state['validated_recommendations'])}")
                
                return state
            else:
                print(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                state["validation_type"] = "recommendations"
                state["workflow_paused"] = True
                return state
                
        except Exception as e:
            print(f"❌ Erreur validation recommandations: {e}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur validation: {str(e)}")]
            return state
    
    def _check_recommendations_success_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Vérifie le succès de la validation des recommandations"""
        print(f"\n🔄 [EXECUTIVE] check_recommendations_success_node - DÉBUT")
        
        validated_count = len(state.get("validated_recommendations", []))
        success = validated_count >= 4
        
        state["recommendations_success"] = success
        
        print(f"📊 Recommandations validées: {validated_count}/4")
        print(f"🎯 Succès: {success}")
        
        if not success:
            state["recommendations_iteration_count"] = state.get("recommendations_iteration_count", 0) + 1
            print(f"🔄 Itération {state['recommendations_iteration_count']}/{state.get('max_recommendations_iterations', 3)}")
        else:
            print(f"✅ Objectif atteint ! {validated_count} recommandations validées")
        
        return state
    
    def _finalize_results_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Finalise les résultats"""
        print(f"\n✅ [EXECUTIVE] finalize_results_node - DÉBUT")
        print(f"📊 Résultats finaux:")
        print(f"   - Enjeux validés: {len(state.get('validated_challenges', []))}")
        print(f"   - Maturité IA: {state.get('maturity_score', 3)}/5")
        print(f"   - Recommandations validées: {len(state.get('validated_recommendations', []))}")
        
        # Sauvegarder les résultats
        self._save_results(state)
        
        return state
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def _should_continue_challenges(self, state: ExecutiveSummaryState) -> str:
        """Détermine si on continue les itérations pour les enjeux"""
        success = state.get("challenges_success", False)
        iteration = state.get("challenges_iteration_count", 0)
        max_iterations = state.get("max_challenges_iterations", 3)
        
        if success:
            return "success"
        elif iteration >= max_iterations:
            return "max_iterations"
        else:
            return "continue"
    
    def _should_continue_recommendations(self, state: ExecutiveSummaryState) -> str:
        """Détermine si on continue les itérations pour les recommandations"""
        success = state.get("recommendations_success", False)
        iteration = state.get("recommendations_iteration_count", 0)
        max_iterations = state.get("max_recommendations_iterations", 3)
        
        if success:
            return "success"
        elif iteration >= max_iterations:
            return "max_iterations"
        else:
            return "continue"
    
    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Formate les citations pour le prompt"""
        if not citations:
            return "Aucune citation disponible"
        
        formatted = []
        for cit in citations:
            speaker = cit.get("speaker", "")
            citation = cit.get("citation", "")
            formatted.append(f"{speaker}: {citation}")
        
        return "\n".join(formatted)
    
    def _format_workshop_info(self, informations: List[Dict[str, Any]]) -> str:
        """Formate les informations d'ateliers pour le prompt"""
        if not informations:
            return "Aucune information d'atelier disponible"
        
        formatted = []
        for info in informations:
            atelier = info.get("atelier", "")
            use_case = info.get("use_case", "")
            objectif = info.get("objectif", "")
            formatted.append(f"{atelier} - {use_case}: {objectif}")
        
        return "\n".join(formatted)
    
    def _format_maturite_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Formate les citations de maturité pour le prompt"""
        if not citations:
            return "Aucune citation de maturité disponible"
        
        formatted = []
        for cit in citations:
            speaker = cit.get("speaker", "")
            citation = cit.get("citation", "")
            type_info = cit.get("type_info", "")
            formatted.append(f"[{type_info}] {speaker}: {citation}")
        
        return "\n".join(formatted)
    
    def _format_workshop_maturite(self, informations: List[Dict[str, Any]]) -> str:
        """Formate les informations de maturité d'ateliers pour le prompt"""
        if not informations:
            return "Aucune information de maturité d'atelier disponible"
        
        formatted = []
        for info in informations:
            atelier = info.get("atelier", "")
            use_case = info.get("use_case", "")
            type_info = info.get("type_info", "")
            formatted.append(f"[{type_info}] {atelier} - {use_case}")
        
        return "\n".join(formatted)
    
    def _save_results(self, state: ExecutiveSummaryState) -> None:
        """Sauvegarde les résultats dans un fichier JSON"""
        try:
            output_dir = "/home/addeche/aiko/aikoGPT/outputs"
            os.makedirs(output_dir, exist_ok=True)
            
            results = {
                "validated_challenges": state.get("validated_challenges", []),
                "maturity_score": state.get("maturity_score", 3),
                "maturity_summary": state.get("maturity_summary", ""),
                "validated_recommendations": state.get("validated_recommendations", [])
            }
            
            output_path = os.path.join(output_dir, "executive_summary_results.json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Résultats sauvegardés: {output_path}")
            
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde résultats: {e}")

