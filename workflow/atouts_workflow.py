"""
Workflow LangGraph pour l'extraction des atouts de l'entreprise
"""

from typing import TypedDict, Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging

from process_transcript.interesting_parts_agent import InterestingPartsAgent
from atouts.atouts_agent import AtoutsAgent

logger = logging.getLogger(__name__)


class AtoutsState(TypedDict, total=False):
    """État du workflow d'extraction des atouts"""
    
    # Inputs
    transcript_document_ids: List[int]  # IDs des documents transcripts dans la DB
    company_info: Dict[str, Any]
    validated_speakers: List[Dict[str, str]]  # NOUVEAU: Speakers validés par l'utilisateur
    
    # Intermediate results
    interesting_interventions: List[Dict[str, Any]]
    citations_atouts: Dict[str, Any]
    
    # Contexte additionnel avant génération
    atouts_additional_context: str
    
    # Résultats de synthèse
    atouts: Dict[str, Any]
    proposed_atouts: List[Dict[str, Any]]
    
    # Validation humaine des atouts
    validated_atouts: List[Dict[str, Any]]
    rejected_atouts: List[Dict[str, Any]]
    atouts_user_feedback: str
    atouts_validation_result: Dict[str, Any]
    
    # Contrôle du workflow
    atouts_user_action: str  # "continue_atouts" ou "finalize_atouts"
    atouts_workflow_paused: bool
    iteration_count: int
    
    # Résultats finaux
    final_atouts: List[Dict[str, Any]]
    atouts_markdown: str
    success: bool
    error: str


class AtoutsWorkflow:
    """Workflow pour extraire les atouts de l'entreprise"""
    
    def __init__(self, interviewer_names: Optional[List[str]] = None, checkpointer: Optional[MemorySaver] = None) -> None:
        self.interesting_parts_agent = InterestingPartsAgent()
        self.atouts_agent = AtoutsAgent()
        self.checkpointer = checkpointer or MemorySaver()
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Crée le graphe du workflow avec HITL"""
        workflow = StateGraph(AtoutsState)
        
        # Ajouter les nœuds
        workflow.add_node("extract_interesting_parts", self._extract_interesting_parts_node)
        workflow.add_node("extract_citations", self._extract_citations_node)
        workflow.add_node("synthesize_atouts", self._synthesize_atouts_node)
        workflow.add_node("validate_atouts", self._validate_atouts_node)
        workflow.add_node("check_atouts_success", self._check_atouts_success_node)
        workflow.add_node("finalize_atouts", self._finalize_atouts_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Définir les edges
        workflow.set_entry_point("extract_interesting_parts")
        workflow.add_edge("extract_interesting_parts", "extract_citations")
        workflow.add_edge("extract_citations", "synthesize_atouts")
        workflow.add_edge("synthesize_atouts", "validate_atouts")
        workflow.add_edge("validate_atouts", "check_atouts_success")
        
        # Router conditionnel après check_atouts_success
        def route_after_validation(state: AtoutsState) -> str:
            """Route selon l'action utilisateur"""
            action = state.get("atouts_user_action", "")
            if action == "continue_atouts":
                # Régénérer de nouveaux atouts
                return "synthesize_atouts"
            else:
                # Finaliser
                return "finalize_atouts"
        
        workflow.add_conditional_edges(
            "check_atouts_success",
            route_after_validation,
            {
                "synthesize_atouts": "synthesize_atouts",
                "finalize_atouts": "finalize_atouts"
            }
        )
        
        workflow.add_edge("finalize_atouts", "format_output")
        workflow.add_edge("format_output", END)
        
        # Compiler avec checkpointer et interrupts
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["validate_atouts"]
        )
    
    def _extract_interesting_parts_node(self, state: AtoutsState) -> AtoutsState:
        """Extrait les parties intéressantes depuis la DB (déjà enrichies)"""
        transcript_document_ids = state.get("transcript_document_ids", [])
        validated_speakers = state.get("validated_speakers", [])
        
        if not transcript_document_ids:
            logger.warning("Aucun document transcript fourni")
            state["interesting_interventions"] = []
            return state
        
        try:
            from database.db import get_db_context
            from database.repository import TranscriptRepository
            
            all_interventions = []
            
            with get_db_context() as db:
                for document_id in transcript_document_ids:
                    logger.info(f"Chargement du document {document_id}")
                    
                    # Récupérer directement les interventions enrichies depuis la DB
                    # (déjà filtrées pour exclure les interviewers)
                    enriched_interventions = TranscriptRepository.get_enriched_by_document(
                        db, document_id, filter_interviewers=True
                    )
                    
                    logger.info(f"✓ {len(enriched_interventions)} interventions enrichies chargées")
                    
                    # Adapter le format pour compatibilité avec interesting_parts_agent
                    formatted_interventions = []
                    for interv in enriched_interventions:
                        formatted_interv = {
                            "speaker": interv.get("speaker_name") or interv.get("speaker"),
                            "timestamp": interv.get("timestamp"),
                            "text": interv.get("text"),
                            "speaker_type": interv.get("speaker_type"),
                            "speaker_level": interv.get("speaker_level"),
                        }
                        formatted_interventions.append(formatted_interv)
                    
                    # Filtrer UNIQUEMENT les speakers validés par l'utilisateur (si fourni)
                    if validated_speakers:
                        validated_names = {s["name"] for s in validated_speakers}
                        logger.info(f"🔍 Filtrage sur {len(validated_names)} speakers validés")
                        
                        formatted_interventions = [
                            interv for interv in formatted_interventions
                            if interv.get("speaker") in validated_names
                        ]
                        
                        logger.info(f"✓ {len(formatted_interventions)} interventions après filtrage")
                    
                    # Filtrer les parties intéressantes
                    logger.info("Filtrage des parties intéressantes...")
                    interesting_interventions = self.interesting_parts_agent._filter_interesting_parts(
                        formatted_interventions
                    )
                    logger.info(f"✓ {len(interesting_interventions)} interventions intéressantes")
                    
                    all_interventions.extend(interesting_interventions)
            
            state["interesting_interventions"] = all_interventions
            logger.info(f"Total: {len(all_interventions)} interventions intéressantes d'interviewés")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des parties intéressantes: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["interesting_interventions"] = []
            return state
    
    def _extract_citations_node(self, state: AtoutsState) -> AtoutsState:
        """Extrait les citations révélant les atouts"""
        interesting_interventions = state.get("interesting_interventions", [])
        
        if not interesting_interventions:
            logger.warning("Aucune intervention intéressante à analyser")
            state["citations_atouts"] = {"citations": []}
            return state
        
        try:
            citations_response = self.atouts_agent.extract_citations_from_transcript(
                interesting_interventions
            )
            
            # Convertir en dict pour le state
            state["citations_atouts"] = citations_response.model_dump()
            logger.info(f"Extrait {len(citations_response.citations)} citations d'atouts")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des citations: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["citations_atouts"] = {"citations": []}
            return state
    
    def _synthesize_atouts_node(self, state: AtoutsState) -> AtoutsState:
        """Synthétise les atouts de l'entreprise (avec gestion des itérations)"""
        citations_dict = state.get("citations_atouts", {"citations": []})
        company_info = state.get("company_info", {})
        validated_atouts = state.get("validated_atouts", [])
        rejected_atouts = state.get("rejected_atouts", [])
        user_feedback = state.get("atouts_user_feedback", "")
        additional_context = state.get("atouts_additional_context", "")
        iteration_count = state.get("iteration_count", 0)
        
        try:
            # Reconstruire l'objet CitationsAtoutsResponse
            from models.atouts_models import CitationsAtoutsResponse
            citations_response = CitationsAtoutsResponse(**citations_dict)
            
            # Déterminer si c'est une régénération ou la première génération
            if iteration_count > 0:
                # Régénération : utiliser le prompt spécial qui évite les doublons
                logger.info(f"🔄 Régénération d'atouts (itération {iteration_count})")
                logger.info(f"📊 Atouts validés à éviter: {len(validated_atouts)}")
                logger.info(f"📊 Atouts rejetés à éviter: {len(rejected_atouts)}")
                
                atouts_response = self.atouts_agent.regenerate_atouts(
                    citations_response,
                    company_info,
                    validated_atouts,
                    rejected_atouts,
                    user_feedback,
                    additional_context
                )
            else:
                # Première génération
                logger.info(f"✨ Première génération d'atouts")
                atouts_response = self.atouts_agent.synthesize_atouts(
                    citations_response,
                    company_info,
                    additional_context
                )
            
            # Convertir en dict pour le state
            state["atouts"] = atouts_response.model_dump()
            
            # Stocker aussi dans proposed_atouts pour la validation
            state["proposed_atouts"] = [atout.model_dump() for atout in atouts_response.atouts]
            
            logger.info(f"Synthétisé {len(atouts_response.atouts)} atouts")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse des atouts: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["atouts"] = {"atouts": []}
            state["proposed_atouts"] = []
            return state
    
    def _format_output_node(self, state: AtoutsState) -> AtoutsState:
        """Formate la sortie en markdown"""
        # Utiliser final_atouts au lieu de atouts pour le formatage final
        final_atouts_list = state.get("final_atouts", [])
        company_info = state.get("company_info", {})
        
        try:
            company_name = company_info.get("nom", "l'entreprise")
            
            if not final_atouts_list:
                state["atouts_markdown"] = f"# Les atouts de {company_name}\n\nAucun atout identifié."
                state["success"] = True
                return state
            
            # Construire le markdown
            markdown_parts = [f"# Les atouts de {company_name}\n"]
            
            for atout in final_atouts_list:
                markdown_parts.append(f"## {atout['id']}. {atout['titre']}\n")
                markdown_parts.append(f"{atout['description']}\n")
                markdown_parts.append("")  # Ligne vide entre les atouts
            
            state["atouts_markdown"] = "\n".join(markdown_parts)
            state["success"] = True
            logger.info("Formatage markdown terminé")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors du formatage: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["atouts_markdown"] = ""
            return state
    
    def _validate_atouts_node(self, state: AtoutsState) -> AtoutsState:
        """
        Nœud de validation humaine des atouts SIMPLIFIÉ.
        
        ARCHITECTURE avec interrupts natifs :
        - Le workflow s'arrête AVANT ce nœud (interrupt_before)
        - L'API/Streamlit détecte que le workflow est en pause
        - Streamlit affiche l'interface de validation
        - L'utilisateur valide et renvoie le feedback
        - Le feedback est injecté dans l'état via l'API
        - Le workflow reprend et ce nœud traite le feedback
        """
        logger.info(f"\n🛑 [INTERRUPT] validate_atouts_node - DÉBUT")
        logger.info(f"📊 Atouts proposés: {len(state.get('proposed_atouts', []))}")
        logger.info(f"📊 Atouts validés existants: {len(state.get('validated_atouts', []))}")
        
        try:
            # Vérifier si on a reçu le feedback (injecté par l'API)
            if "atouts_validation_result" in state and state["atouts_validation_result"]:
                logger.info(f"✅ [RESUME] Feedback atouts reçu via API")
                validation_data = state["atouts_validation_result"]
                
                # Traiter les résultats de validation
                existing_validated = state.get("validated_atouts", [])
                newly_validated = validation_data.get("validated_atouts", [])
                
                # Ajouter directement les nouveaux atouts validés (pas de filtre de doublons)
                # Car lors des régénérations, les IDs sont réinitialisés (1, 2, 3, 4...)
                # mais ce sont de NOUVEAUX atouts différents
                state["validated_atouts"] = existing_validated + newly_validated
                
                # Même chose pour les rejetés
                existing_rejected = state.get("rejected_atouts", [])
                newly_rejected = validation_data.get("rejected_atouts", [])
                
                state["rejected_atouts"] = existing_rejected + newly_rejected
                state["atouts_user_feedback"] = validation_data.get("user_feedback", "")
                
                # Incrémenter le compteur d'itération
                state["iteration_count"] = state.get("iteration_count", 0) + 1
                logger.info(f"🔄 [DEBUG] iteration_count incrémenté à {state['iteration_count']}")
                
                # Nettoyer le flag
                state["atouts_validation_result"] = {}
                
                logger.info(f"📊 [RESUME] Atouts nouvellement validés: {len(newly_validated)}")
                logger.info(f"📊 [RESUME] Total atouts validés: {len(state['validated_atouts'])}")
                logger.info(f"▶️ [RESUME] Workflow continue...")
                
                return state
            else:
                # Première fois : le workflow va s'arrêter ici (interrupt_before)
                logger.info(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                logger.info(f"💡 [INTERRUPT] L'API détectera cet arrêt et Streamlit affichera l'interface")
                
                # Juste retourner l'état
                # Le workflow s'arrête automatiquement car interrupt_before
                return state
            
        except Exception as e:
            logger.error(f"❌ [ERROR] Erreur dans validate_atouts_node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _check_atouts_success_node(self, state: AtoutsState) -> AtoutsState:
        """
        Nœud de décision : continuer la régénération ou finaliser.
        """
        logger.info(f"\n🔍 [DEBUG] check_atouts_success_node - DÉBUT")
        
        atouts_user_action = state.get("atouts_user_action", "")
        logger.info(f"🎯 Action utilisateur: {atouts_user_action}")
        
        # L'action est déjà dans l'état, on la laisse pour le router
        return state
    
    def _finalize_atouts_node(self, state: AtoutsState) -> AtoutsState:
        """
        Nœud de finalisation des atouts.
        Renuméroter les atouts pour avoir une numérotation continue.
        """
        try:
            logger.info(f"\n🔍 [DEBUG] _finalize_atouts_node - DÉBUT")
            logger.info(f"📊 [DEBUG] Atouts validés: {len(state.get('validated_atouts', []))}")
            
            # Utiliser directement les atouts validés depuis l'état
            validated_atouts = state.get("validated_atouts", [])
            
            # Renuméroter les atouts pour avoir une séquence continue (1, 2, 3, 4, ...)
            final_atouts = []
            for i, atout in enumerate(validated_atouts, 1):
                atout_copy = atout.copy()
                atout_copy["id"] = i
                final_atouts.append(atout_copy)
            
            state["final_atouts"] = final_atouts
            
            logger.info(f"📊 [DEBUG] Final atouts définis: {len(final_atouts)}")
            
            # Debug: Afficher les titres des atouts
            if final_atouts:
                logger.info(f"📋 [DEBUG] Titres des atouts validés:")
                for atout in final_atouts:
                    logger.info(f"   {atout.get('id')}. {atout.get('titre', 'N/A')}")
            
            logger.info(f"✅ [DEBUG] _finalize_atouts_node - FIN")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [DEBUG] Erreur dans _finalize_atouts_node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def run(
        self,
        transcript_document_ids: List[int],
        company_info: Dict[str, Any],
        thread_id: Optional[str] = None,
        atouts_additional_context: str = "",
        validated_speakers: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Exécute le workflow d'extraction des atouts
        
        Args:
            transcript_document_ids: Liste des IDs de documents transcripts dans la DB
            company_info: Informations sur l'entreprise depuis web search
            thread_id: ID du thread pour la persistance (optionnel)
            atouts_additional_context: Contexte additionnel fourni dès le démarrage
            validated_speakers: Liste des speakers validés par l'utilisateur
            
        Returns:
            État final du workflow avec les atouts extraits
        """
        initial_state: AtoutsState = {
            "transcript_document_ids": transcript_document_ids,
            "company_info": company_info,
            "validated_speakers": validated_speakers or [],
            "iteration_count": 0,
            "validated_atouts": [],
            "rejected_atouts": [],
            "atouts_user_feedback": "",
            "atouts_additional_context": atouts_additional_context
        }
        
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())
            logger.info(f"🔑 Thread ID généré automatiquement: {thread_id}")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Exécuter le workflow
        logger.info(f"🚀 Exécution du graphe avec thread_id: {thread_id}")
        logger.info(f"📝 Contexte additionnel: {len(atouts_additional_context)} caractères")
        
        final_state = None
        for chunk in self.graph.stream(initial_state, config):
            logger.info(f"📊 Chunk reçu: {list(chunk.keys())}")
            for node_name, node_state in chunk.items():
                logger.info(f"  • Nœud '{node_name}' exécuté")
                final_state = node_state
        
        # Récupérer l'état complet depuis le checkpointer
        snapshot = self.graph.get_state(config)
        state = snapshot.values
        next_nodes = list(snapshot.next) if snapshot.next else []
        
        logger.info(f"📊 État récupéré depuis le checkpointer:")
        logger.info(f"📊 Next nodes: {next_nodes}")
        
        # Vérifier où le workflow s'est arrêté
        if "validate_atouts" in next_nodes:
            # Le workflow s'est arrêté à validate_atouts (normal)
            logger.info(f"⏸️ Workflow arrêté avant validate_atouts - en attente de validation")
            return {
                "success": False,
                "atouts_workflow_paused": True,
                "citations_atouts": state.get("citations_atouts", {}),
                "interesting_interventions": state.get("interesting_interventions", []),
                "proposed_atouts": state.get("proposed_atouts", []),
                "validated_atouts": state.get("validated_atouts", []),
                "final_atouts": [],
                "iteration_count": state.get("iteration_count", 0),
                "messages": ["Workflow en pause - en attente de validation des atouts"]
            }
        elif len(next_nodes) == 0:
            # Le workflow est terminé
            logger.info(f"✅ Workflow terminé")
            return {
                "success": True,
                "atouts_workflow_paused": False,
                "final_atouts": state.get("final_atouts", []),
                "atouts_markdown": state.get("atouts_markdown", ""),
                "validated_atouts": state.get("validated_atouts", []),
                "iteration_count": state.get("iteration_count", 0),
                "messages": ["Workflow terminé avec succès"]
            }
        else:
            # Autre état (ne devrait pas arriver)
            logger.warning(f"⚠️ Workflow dans un état inattendu: {next_nodes}")
            return {
                "success": False,
                "atouts_workflow_paused": True,
                "citations_atouts": state.get("citations_atouts", {}),
                "interesting_interventions": state.get("interesting_interventions", []),
                "proposed_atouts": state.get("proposed_atouts", []),
                "validated_atouts": state.get("validated_atouts", []),
                "final_atouts": [],
                "iteration_count": state.get("iteration_count", 0),
                "messages": [f"Workflow en pause - next_nodes: {next_nodes}"]
            }
    
    def resume_workflow_with_validation(
        self,
        validated_atouts: List[Dict[str, Any]],
        rejected_atouts: List[Dict[str, Any]],
        user_feedback: str,
        atouts_user_action: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Reprend le workflow après validate_atouts avec le feedback de validation.
        
        Args:
            validated_atouts: Atouts validés par l'utilisateur
            rejected_atouts: Atouts rejetés par l'utilisateur
            user_feedback: Commentaires de l'utilisateur
            atouts_user_action: Action demandée ("continue_atouts" ou "finalize_atouts")
            thread_id: ID du thread
            
        Returns:
            État du workflow
        """
        logger.info(f"\n🔄 resume_workflow_with_validation() appelé")
        logger.info(f"✅ Validés: {len(validated_atouts)}")
        logger.info(f"❌ Rejetés: {len(rejected_atouts)}")
        logger.info(f"🎯 Action: {atouts_user_action}")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Mettre à jour l'état avec le feedback
        current_state = self.graph.get_state(config)
        updated_values = {
            **current_state.values,
            "atouts_validation_result": {
                "validated_atouts": validated_atouts,
                "rejected_atouts": rejected_atouts,
                "user_feedback": user_feedback
            },
            "atouts_user_action": atouts_user_action
        }
        
        # Reprendre le workflow
        self.graph.update_state(config, updated_values)
        
        # Continuer l'exécution
        final_state = None
        for chunk in self.graph.stream(None, config):
            logger.info(f"📊 Chunk reçu: {list(chunk.keys())}")
            for node_name, node_state in chunk.items():
                logger.info(f"  • Nœud '{node_name}' exécuté")
                final_state = node_state
        
        # Récupérer l'état final
        snapshot = self.graph.get_state(config)
        state = snapshot.values
        next_nodes = list(snapshot.next) if snapshot.next else []
        
        logger.info(f"📊 Next nodes: {next_nodes}")
        
        # Si on doit continuer (validate_atouts dans next_nodes)
        if "validate_atouts" in next_nodes:
            logger.info(f"⏸️ Workflow arrêté avant validate_atouts - nouvelle validation requise")
            return {
                "success": False,
                "atouts_workflow_paused": True,
                "proposed_atouts": state.get("proposed_atouts", []),
                "validated_atouts": state.get("validated_atouts", []),
                "iteration_count": state.get("iteration_count", 0),
                "messages": ["Workflow en pause - en attente de validation"]
            }
        else:
            # Workflow terminé
            logger.info(f"✅ Workflow terminé")
            return {
                "success": True,
                "atouts_workflow_paused": False,
                "final_atouts": state.get("final_atouts", []),
                "atouts_markdown": state.get("atouts_markdown", ""),
                "validated_atouts": state.get("validated_atouts", []),
                "iteration_count": state.get("iteration_count", 0),
                "messages": ["Workflow terminé avec succès"]
            }

