"""
Workflow LangGraph pour l'Executive Summary
"""

import os
import json
from typing import Dict, List, Any, TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
import sys
sys.path.append('/home/addeche/aiko/aikoGPT')
import config as project_config

from executive_summary.transcript_enjeux_agent import TranscriptEnjeuxAgent
from executive_summary.workshop_enjeux_agent import WorkshopEnjeuxAgent
from executive_summary.transcript_maturite_agent import TranscriptMaturiteAgent
from executive_summary.workshop_maturite_agent import WorkshopMaturiteAgent
from executive_summary.executive_summary_agent import ExecutiveSummaryAgent
from utils.token_tracker import TokenTracker


class ExecutiveSummaryState(TypedDict):
    """État du workflow LangGraph pour Executive Summary"""
    messages: Annotated[List[BaseMessage], add_messages]
    # Document IDs (depuis la base de données)
    transcript_document_ids: List[int]
    workshop_document_ids: List[int]
    company_name: str
    interviewer_note: str
    # Données validées (depuis "Validation des besoins et use cases")
    extracted_needs: List[Dict]  # Besoins validés depuis la BDD
    extracted_use_cases: List[Dict]  # Use cases validés depuis la BDD
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
    # Action demandée par l'utilisateur (pour les boutons)
    challenges_user_action: str  # "continue_challenges" ou "continue_to_maturity"
    # Résultats Maturité
    maturity_score: int
    maturity_summary: str
    # Résultats Recommandations
    recommendations: List[Dict]
    validated_recommendations: List[Dict]
    rejected_recommendations: List[Dict]
    recommendations_feedback: str
    # Action demandée par l'utilisateur (pour les boutons)
    recommendations_user_action: str  # "continue_recommendations" ou "continue_to_finalize"
    # Validation
    workflow_paused: bool
    validation_type: str  # "challenges" ou "recommendations"
    validation_result: Dict[str, Any]


class ExecutiveSummaryWorkflow:
    """Workflow LangGraph pour l'Executive Summary"""
    
    def __init__(self, api_key: str, dev_mode: bool = False):
        """
        Initialise le workflow.
        
        Args:
            api_key: Clé API OpenAI
            dev_mode: Mode développement
        """
        self.api_key = api_key
        self.dev_mode = dev_mode
        
        model = os.getenv('OPENAI_MODEL', 'gpt-5-nano')
        self.llm = ChatOpenAI(
            model=model,
            api_key=api_key
        )
        
        # Initialiser les agents
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
        workflow.add_node("load_validated_data", self._load_validated_data_node)
        workflow.add_node("transcript_enjeux", self._transcript_enjeux_node)
        workflow.add_node("workshop_enjeux", self._workshop_enjeux_node)
        workflow.add_node("transcript_maturite", self._transcript_maturite_node)
        workflow.add_node("workshop_maturite", self._workshop_maturite_node)
        workflow.add_node("collect_citations", self._collect_citations_node)
        workflow.add_node("identify_challenges", self._identify_challenges_node)
        workflow.add_node("human_validation_enjeux", self._human_validation_enjeux_node)
        workflow.add_node("pre_recommendations_interrupt", self._pre_recommendations_interrupt_node)
        workflow.add_node("evaluate_maturity", self._evaluate_maturity_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("human_validation_recommendations", self._human_validation_recommendations_node)
        workflow.add_node("finalize_results", self._finalize_results_node)
        
        # Point d'entrée
        workflow.set_entry_point("dispatcher")
        
        # Flux parallèle : chargement données validées + 4 agents spécialisés
        workflow.add_edge("dispatcher", "load_validated_data")
        workflow.add_edge("dispatcher", "transcript_enjeux")
        workflow.add_edge("dispatcher", "workshop_enjeux")
        workflow.add_edge("dispatcher", "transcript_maturite")
        workflow.add_edge("dispatcher", "workshop_maturite")
        
        # Convergence vers collect_citations
        workflow.add_edge("load_validated_data", "collect_citations")
        workflow.add_edge("transcript_enjeux", "collect_citations")
        workflow.add_edge("workshop_enjeux", "collect_citations")
        workflow.add_edge("transcript_maturite", "collect_citations")
        workflow.add_edge("workshop_maturite", "collect_citations")
        
        # Flux séquentiel : Enjeux
        workflow.add_edge("collect_citations", "identify_challenges")
        workflow.add_edge("identify_challenges", "human_validation_enjeux")
        
        # Conditions de branchement - Enjeux (basé sur l'action utilisateur)
        workflow.add_conditional_edges(
            "human_validation_enjeux",
            self._should_continue_challenges,
            {
                "continue_challenges": "identify_challenges",
                "continue_to_maturity": "pre_recommendations_interrupt"
            }
        )
        
        # Nœud de pause avant la génération des recommandations
        workflow.add_edge("pre_recommendations_interrupt", "evaluate_maturity")
        
        # Flux séquentiel : Maturité et Recommandations
        workflow.add_edge("evaluate_maturity", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "human_validation_recommendations")
        
        # Conditions de branchement - Recommandations (basé sur l'action utilisateur)
        workflow.add_conditional_edges(
            "human_validation_recommendations",
            self._should_continue_recommendations,
            {
                "continue_recommendations": "generate_recommendations",
                "continue_to_finalize": "finalize_results"
            }
        )
        
        workflow.add_edge("finalize_results", END)
        
        # Configuration avec checkpointer et interrupts
        compile_kwargs = {
            "checkpointer": MemorySaver(),
            "interrupt_before": ["human_validation_enjeux", "pre_recommendations_interrupt", "human_validation_recommendations"]
        }
        
        return workflow.compile(**compile_kwargs)
    
    def run(
        self,
        transcript_document_ids: List[int],
        workshop_document_ids: List[int],
        company_name: str,
        interviewer_note: str = "",
        thread_id: str = None,
        validated_needs: Optional[List[Dict[str, Any]]] = None,
        validated_use_cases: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Exécute le workflow.
        
        Args:
            transcript_document_ids: Liste des IDs de documents transcript dans la BDD
            workshop_document_ids: Liste des IDs de documents workshop dans la BDD
            company_name: Nom de l'entreprise
            interviewer_note: Note de l'intervieweur
            thread_id: ID du thread pour la persistance
            validated_needs: Besoins validés par l'utilisateur (depuis "Validation des besoins et use cases")
            validated_use_cases: Cas d'usage validés par l'utilisateur (depuis "Validation des besoins et use cases")
            
        Returns:
            État final du workflow
        """
        initial_state = {
            "messages": [],
            "transcript_document_ids": transcript_document_ids or [],
            "workshop_document_ids": workshop_document_ids or [],
            "company_name": company_name,
            "interviewer_note": interviewer_note,
            "extracted_needs": validated_needs or [],
            "extracted_use_cases": validated_use_cases or [],
            "transcript_enjeux_citations": [],
            "workshop_enjeux_citations": [],
            "transcript_maturite_citations": [],
            "workshop_maturite_citations": [],
            "identified_challenges": [],
            "validated_challenges": [],
            "rejected_challenges": [],
            "challenges_feedback": "",
            "challenges_user_action": "",
            "maturity_score": 3,
            "maturity_summary": "",
            "recommendations": [],
            "validated_recommendations": [],
            "rejected_recommendations": [],
            "recommendations_feedback": "",
            "recommendations_user_action": "",
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
        print(f"📊 Document IDs: Transcripts={len(state.get('transcript_document_ids', []))}, "
              f"Workshops={len(state.get('workshop_document_ids', []))}")
        print(f"📊 Données validées: Besoins={len(state.get('extracted_needs', []))}, "
              f"Use cases={len(state.get('extracted_use_cases', []))}")
        return state
    
    def _load_validated_data_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Charge les données validées depuis la base de données ou utilise celles déjà présentes"""
        print(f"\n📄 [EXECUTIVE] load_validated_data_node - DÉBUT")
        try:
            # Vérifier si des données validées sont déjà présentes dans l'état
            extracted_needs = state.get("extracted_needs", [])
            extracted_use_cases = state.get("extracted_use_cases", [])
            
            # Si les données sont déjà présentes (validées par l'utilisateur), les utiliser
            if extracted_needs or extracted_use_cases:
                print(f"✅ Utilisation des données validées: {len(extracted_needs)} besoins, "
                      f"{len(extracted_use_cases)} cas d'usage")
                
                # Afficher le détail des cas d'usage
                if extracted_use_cases:
                    print(f"\n📊 [EXECUTIVE] DÉTAIL DES CAS D'USAGE ({len(extracted_use_cases)}):")
                    for i, uc in enumerate(extracted_use_cases, 1):
                        titre = uc.get("titre", "N/A")
                        famille = uc.get("famille")
                        if famille:
                            print(f"   {i}. [{famille}] {titre}")
                        else:
                            print(f"   {i}. {titre}")
                
                return {
                    "extracted_needs": extracted_needs,
                    "extracted_use_cases": extracted_use_cases
                }
            
            # Si aucune donnée validée n'est fournie, essayer de charger depuis la BDD
            # (Cette fonctionnalité peut être ajoutée plus tard si nécessaire)
            print("⚠️ Aucune donnée validée fournie. Les besoins et use cases doivent être validés dans 'Validation des besoins et use cases' avant de lancer ce workflow.")
            return {
                "extracted_needs": [],
                "extracted_use_cases": []
            }
            
        except Exception as e:
            print(f"❌ Erreur chargement données validées: {e}")
            return {
                "messages": [HumanMessage(content=f"Erreur chargement données: {str(e)}")]
            }
    
    def _transcript_enjeux_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait citations enjeux depuis transcripts"""
        print(f"\n📝 [EXECUTIVE] transcript_enjeux_node - DÉBUT")
        try:
            transcript_document_ids = state.get("transcript_document_ids", [])
            if not transcript_document_ids:
                print("⚠️ Aucun document transcript")
                return {"transcript_enjeux_citations": []}
            
            citations = self.transcript_enjeux_agent.extract_citations(transcript_document_ids)
            print(f"✅ {len(citations)} citations d'enjeux extraites")
            
            return {"transcript_enjeux_citations": citations}
            
        except Exception as e:
            print(f"❌ Erreur transcript_enjeux: {e}")
            return {"transcript_enjeux_citations": []}
    
    def _workshop_enjeux_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait informations enjeux depuis ateliers"""
        print(f"\n📊 [EXECUTIVE] workshop_enjeux_node - DÉBUT")
        try:
            workshop_document_ids = state.get("workshop_document_ids", [])
            if not workshop_document_ids:
                print("⚠️ Aucun document workshop")
                return {"workshop_enjeux_citations": []}
            
            informations = self.workshop_enjeux_agent.extract_informations(workshop_document_ids)
            print(f"✅ {len(informations)} informations d'enjeux extraites")
            
            return {"workshop_enjeux_citations": informations}
            
        except Exception as e:
            print(f"❌ Erreur workshop_enjeux: {e}")
            return {"workshop_enjeux_citations": []}
    
    def _transcript_maturite_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait citations maturité depuis transcripts"""
        print(f"\n📝 [EXECUTIVE] transcript_maturite_node - DÉBUT")
        try:
            transcript_document_ids = state.get("transcript_document_ids", [])
            if not transcript_document_ids:
                print("⚠️ Aucun document transcript")
                return {"transcript_maturite_citations": []}
            
            citations = self.transcript_maturite_agent.extract_citations(transcript_document_ids)
            print(f"✅ {len(citations)} citations de maturité extraites")
            
            return {"transcript_maturite_citations": citations}
            
        except Exception as e:
            print(f"❌ Erreur transcript_maturite: {e}")
            return {"transcript_maturite_citations": []}
    
    def _workshop_maturite_node(self, state: ExecutiveSummaryState) -> Dict[str, Any]:
        """Extrait informations maturité depuis ateliers"""
        print(f"\n📊 [EXECUTIVE] workshop_maturite_node - DÉBUT")
        try:
            workshop_document_ids = state.get("workshop_document_ids", [])
            if not workshop_document_ids:
                print("⚠️ Aucun document workshop")
                return {"workshop_maturite_citations": []}
            
            informations = self.workshop_maturite_agent.extract_informations(workshop_document_ids)
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
        import time
        start_time = time.time()
        print(f"\n🎯 [EXECUTIVE] identify_challenges_node - DÉBUT ({time.strftime('%H:%M:%S.%f', time.localtime(start_time))[:-3]})")
        try:
            # Préparer le contenu
            transcript_content = self._format_citations(state.get("transcript_enjeux_citations", []))
            workshop_content = self._format_workshop_info(state.get("workshop_enjeux_citations", []))
            final_needs = state.get("extracted_needs", [])
            interviewer_note = state.get("interviewer_note", "")
            
            # Récupérer les enjeux rejetés et validés pour régénération
            rejected = state.get("rejected_challenges", [])
            validated = state.get("validated_challenges", [])
            feedback = state.get("challenges_feedback", "")
            
            result = self.executive_agent.identify_challenges(
                transcript_content=transcript_content,
                workshop_content=workshop_content,
                final_needs=final_needs,
                interviewer_note=interviewer_note,
                rejected_challenges=rejected if rejected else None,
                validated_challenges=validated if validated else None,
                challenges_feedback=feedback
            )
            
            state["identified_challenges"] = result.get("challenges", [])
            end_time = time.time()
            duration = end_time - start_time
            print(f"✅ {len(state['identified_challenges'])} enjeux identifiés")
            print(f"⏱️ [TIMING] identify_challenges_node: {duration:.3f}s")
            
            return state
            
        except Exception as e:
            print(f"❌ Erreur identification enjeux: {e}")
            state["messages"] = state.get("messages", []) + [HumanMessage(content=f"Erreur identification: {str(e)}")]
            return state
    
    def _human_validation_enjeux_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Nœud de validation humaine des enjeux"""
        import time
        start_time = time.time()
        print(f"\n🛑 [EXECUTIVE] human_validation_enjeux_node - DÉBUT ({time.strftime('%H:%M:%S.%f', time.localtime(start_time))[:-3]})")
        print(f"📊 identified_challenges: {len(state.get('identified_challenges', []))}")
        
        try:
            if "validation_result" in state and state["validation_result"]:
                print(f"✅ [RESUME] Feedback reçu via API")
                validation_data = state["validation_result"]
                
                existing_validated = state.get("validated_challenges", [])
                newly_validated = validation_data.get("validated_challenges", [])
                
                # Conserver les IDs originaux (E1, E2, etc.) s'ils existent
                # Ne régénérer que si l'ID est vide
                existing_ids = [ch.get("id", "") for ch in existing_validated]
                
                for i, challenge in enumerate(newly_validated):
                    challenge_id = challenge.get("id", "")
                    
                    # Seulement régénérer si l'ID est complètement vide
                    if not challenge_id:
                        # Générer un nouvel ID au format E{n}
                        new_index = len(existing_validated) + i + 1
                        challenge["id"] = f"E{new_index}"
                    # Si l'ID existe mais est en conflit, ajouter un suffixe
                    elif challenge_id in existing_ids:
                        challenge["id"] = f"{challenge_id}_bis"
                
                # Ajouter tous les nouveaux enjeux validés
                state["validated_challenges"] = existing_validated + newly_validated
                
                # Accumuler les rejetés (ne pas remplacer, mais ajouter)
                existing_rejected = state.get("rejected_challenges", [])
                newly_rejected = validation_data.get("rejected_challenges", [])
                existing_rejected_ids = [ch.get("id", "") for ch in existing_rejected]
                unique_newly_rejected = [ch for ch in newly_rejected if ch.get("id", "") not in existing_rejected_ids]
                state["rejected_challenges"] = existing_rejected + unique_newly_rejected
                
                state["challenges_feedback"] = validation_data.get("challenges_feedback", "")
                state["challenges_user_action"] = validation_data.get("challenges_user_action", "continue_challenges")
                state["validation_result"] = {}
                state["validation_type"] = ""
                
                end_time = time.time()
                duration = end_time - start_time
                print(f"📊 Enjeux nouvellement validés: {len(newly_validated)}")
                print(f"📊 Total enjeux validés: {len(state['validated_challenges'])}")
                print(f"⏱️ [TIMING] human_validation_enjeux_node: {duration:.3f}s")
                
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
    
    
    def _pre_recommendations_interrupt_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """
        Nœud d'interrupt avant la génération des recommandations.
        Permet à l'utilisateur de voir les enjeux validés et d'ajouter des commentaires.
        """
        print(f"\n⏸️ [EXECUTIVE] pre_recommendations_interrupt_node - DÉBUT")
        print(f"📊 Enjeux validés: {len(state.get('validated_challenges', []))}")
        
        # Ce nœud ne fait rien, il sert juste d'interrupt
        # L'utilisateur va voir l'interface avec les enjeux validés et pourra ajouter un commentaire
        # Le commentaire sera stocké dans recommendations_feedback
        
        return state
    
    def _evaluate_maturity_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Évalue la maturité IA"""
        print(f"\n📊 [EXECUTIVE] evaluate_maturity_node - DÉBUT")
        try:
            transcript_content = self._format_maturite_citations(state.get("transcript_maturite_citations", []))
            workshop_content = self._format_workshop_maturite(state.get("workshop_maturite_citations", []))
            final_needs = state.get("extracted_needs", [])
            final_use_cases = state.get("extracted_use_cases", [])
            
            print(f"📊 [EXECUTIVE] Données pour évaluation maturité:")
            print(f"   - Cas d'usage: {len(final_use_cases)}")
            
            result = self.executive_agent.evaluate_maturity(
                transcript_content=transcript_content,
                workshop_content=workshop_content,
                final_needs=final_needs,
                final_use_cases=final_use_cases
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
            final_use_cases = state.get("extracted_use_cases", [])
            
            rejected = state.get("rejected_recommendations", [])
            validated = state.get("validated_recommendations", [])
            feedback = state.get("recommendations_feedback", "")
            
            # Logs avant la génération
            if feedback:
                print(f"📝 [GENERATION] Feedback utilisateur reçu: {feedback[:100]}...")
            if validated:
                print(f"📊 [REGENERATION] Recommandations validées ({len(validated)}):")
                for i, rec in enumerate(validated, 1):
                    if isinstance(rec, dict):
                        titre = rec.get("titre", "")
                        print(f"   {i}. {titre}")
                    else:
                        rec_str = str(rec)
                        print(f"   {i}. {rec_str[:100]}..." if len(rec_str) > 100 else f"   {i}. {rec_str}")
            
            if rejected:
                print(f"📊 [REGENERATION] Recommandations rejetées ({len(rejected)}):")
                for i, rec in enumerate(rejected, 1):
                    if isinstance(rec, dict):
                        titre = rec.get("titre", "")
                        print(f"   {i}. {titre}")
                    else:
                        rec_str = str(rec)
                        print(f"   {i}. {rec_str[:100]}..." if len(rec_str) > 100 else f"   {i}. {rec_str}")
            
            result = self.executive_agent.generate_recommendations(
                maturite_ia=maturite_ia,
                final_needs=final_needs,
                final_use_cases=final_use_cases,
                rejected_recommendations=rejected if rejected else None,
                validated_recommendations=validated if validated else None,
                recommendations_feedback=feedback
            )
            
            state["recommendations"] = result.get("recommendations", [])
            print(f"✅ {len(state['recommendations'])} recommandations générées")
            
            # Logs après la génération
            print(f"📊 [REGENERATION] Nouvelles recommandations générées ({len(state['recommendations'])}):")
            for i, rec in enumerate(state["recommendations"], 1):
                if isinstance(rec, dict):
                    titre = rec.get("titre", "")
                    description = rec.get("description", "")
                    print(f"   {i}. {titre}")
                    if description:
                        print(f"      {description[:80]}..." if len(description) > 80 else f"      {description}")
                else:
                    rec_str = str(rec)
                    print(f"   {i}. {rec_str[:100]}..." if len(rec_str) > 100 else f"   {i}. {rec_str}")
            
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
                
                # Ajouter les nouvelles recommandations validées (garde-fou : éviter les doublons)
                newly_validated_filtered = [r for r in newly_validated if r not in existing_validated]
                
                state["validated_recommendations"] = existing_validated + newly_validated_filtered
                
                # Accumuler les rejetées (ne pas remplacer, mais ajouter)
                existing_rejected = state.get("rejected_recommendations", [])
                newly_rejected = validation_data.get("rejected_recommendations", [])
                newly_rejected_filtered = [r for r in newly_rejected if r not in existing_rejected]
                state["rejected_recommendations"] = existing_rejected + newly_rejected_filtered
                
                state["recommendations_feedback"] = validation_data.get("recommendations_feedback", "")
                state["recommendations_user_action"] = validation_data.get("recommendations_user_action", "continue_recommendations")
                state["validation_result"] = {}
                state["validation_type"] = ""
                
                print(f"📊 Recommandations nouvellement validées: {len(newly_validated_filtered)}")
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
    
    
    def _finalize_results_node(self, state: ExecutiveSummaryState) -> ExecutiveSummaryState:
        """Finalise les résultats"""
        print(f"\n✅ [EXECUTIVE] finalize_results_node - DÉBUT")
        print(f"📊 Résultats finaux:")
        print(f"   - Enjeux validés: {len(state.get('validated_challenges', []))}")
        print(f"   - Maturité IA: {state.get('maturity_score', 3)}/5")
        print(f"   - Recommandations validées: {len(state.get('validated_recommendations', []))}")
        
        # Sauvegarder les résultats
        self._save_results(state)
        
        # Marquer le workflow comme terminé (plus de pause)
        state["workflow_paused"] = False
        state["validation_type"] = ""
        
        return state
    
    # ==================== MÉTHODES UTILITAIRES ====================
    
    def _should_continue_challenges(self, state: ExecutiveSummaryState) -> str:
        """Détermine la direction du workflow basée sur l'action de l'utilisateur pour les enjeux"""
        user_action = state.get("challenges_user_action", "")
        
        if user_action == "continue_to_maturity":
            return "continue_to_maturity"
        else:
            # Par défaut, continuer avec les enjeux
            return "continue_challenges"
    
    def _should_continue_recommendations(self, state: ExecutiveSummaryState) -> str:
        """Détermine la direction du workflow basée sur l'action de l'utilisateur pour les recommandations"""
        user_action = state.get("recommendations_user_action", "")
        
        if user_action == "continue_to_finalize":
            return "continue_to_finalize"
        else:
            # Par défaut, continuer avec les recommandations
            return "continue_recommendations"
    
    def _format_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Formate les citations pour le prompt, triées par speaker"""
        if not citations:
            return "Aucune citation disponible"
        
        # Trier les citations par speaker
        sorted_citations = sorted(
            citations,
            key=lambda c: c.get("speaker", "").lower()
        )
        
        formatted = []
        for cit in sorted_citations:
            speaker = cit.get("speaker", "")
            citation = cit.get("citation", "")
            formatted.append(f"{speaker}: {citation}")
        
        return "\n".join(formatted)
    
    def _format_workshop_info(self, informations: List[Dict[str, Any]]) -> str:
        """Formate les informations d'ateliers pour le prompt, triées par atelier puis par use_case"""
        if not informations:
            return "Aucune information d'atelier disponible"
        
        # Trier les informations : d'abord par atelier, puis par use_case
        sorted_informations = sorted(
            informations,
            key=lambda info: (
                info.get("atelier", "").lower(),
                info.get("use_case", "").lower()
            )
        )
        
        formatted = []
        for info in sorted_informations:
            atelier = info.get("atelier", "")
            use_case = info.get("use_case", "")
            objectif = info.get("objectif", "")
            formatted.append(f"{atelier} - {use_case}: {objectif}")
        
        return "\n".join(formatted)
    
    def _format_maturite_citations(self, citations: List[Dict[str, Any]]) -> str:
        """Formate les citations de maturité pour le prompt, triées par type_info puis par speaker"""
        if not citations:
            return "Aucune citation de maturité disponible"
        
        # Trier les citations : d'abord par type_info, puis par speaker
        sorted_citations = sorted(
            citations,
            key=lambda c: (
                c.get("type_info", "").lower(),  # Type d'info en premier
                c.get("speaker", "").lower()  # Puis speaker
            )
        )
        
        formatted = []
        for cit in sorted_citations:
            speaker = cit.get("speaker", "")
            citation = cit.get("citation", "")
            type_info = cit.get("type_info", "")
            formatted.append(f"[{type_info}] {speaker}: {citation}")
        
        return "\n".join(formatted)
    
    def _format_workshop_maturite(self, informations: List[Dict[str, Any]]) -> str:
        """Formate les informations de maturité d'ateliers pour le prompt, triées par type_info puis par atelier"""
        if not informations:
            return "Aucune information de maturité d'atelier disponible"
        
        # Trier les informations : d'abord par type_info, puis par atelier, puis par use_case
        sorted_informations = sorted(
            informations,
            key=lambda info: (
                info.get("type_info", "").lower(),  # Type d'info en premier
                info.get("atelier", "").lower(),  # Puis atelier
                info.get("use_case", "").lower()  # Puis use_case
            )
        )
        
        formatted = []
        for info in sorted_informations:
            atelier = info.get("atelier", "")
            use_case = info.get("use_case", "")
            type_info = info.get("type_info", "")
            formatted.append(f"[{type_info}] {atelier} - {use_case}")
        
        return "\n".join(formatted)
    
    def _save_results(self, state: ExecutiveSummaryState) -> None:
        """Sauvegarde les résultats dans un fichier JSON"""
        try:
            output_dir = str(project_config.ensure_outputs_dir())
            
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

