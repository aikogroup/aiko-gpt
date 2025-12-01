"""
Workflow LangGraph pour l'évaluation des 5 prérequis de transformation IA
"""

from typing import TypedDict, Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from prerequis_evaluation.prerequis_evaluation_agent import PrerequisEvaluationAgent
from models.prerequis_evaluation_models import (
    PrerequisEvaluation,
    PrerequisDocumentEvaluation
)

logger = logging.getLogger(__name__)


class PrerequisEvaluationState(TypedDict, total=False):
    """État du workflow d'évaluation des prérequis"""
    
    # Inputs
    transcript_document_ids: List[int]  # IDs des documents transcripts dans la DB
    company_info: Dict[str, Any]
    validated_use_cases: List[Dict[str, Any]]  # Cas d'usage validés (obligatoire)
    comments: Dict[str, str]  # Dictionnaire avec les 6 commentaires (comment_general, comment_1 à comment_5)
    
    # Interventions chargées (filtrées par speaker_level)
    interventions_direction: List[Dict[str, Any]]  # Interventions direction
    interventions_metier: List[Dict[str, Any]]  # Interventions métier
    all_interventions: List[Dict[str, Any]]  # Toutes les interventions (pour prerequis 4 et 5)
    
    # Résultats d'évaluation
    evaluation_prerequis_1: Optional[PrerequisEvaluation]
    evaluation_prerequis_2: Optional[PrerequisEvaluation]
    evaluation_prerequis_3: Optional[PrerequisEvaluation]
    
    # Évaluations par document (prerequis 4 et 5)
    evaluations_prerequis_4_by_doc: List[PrerequisDocumentEvaluation]
    evaluations_prerequis_5_by_doc: List[PrerequisDocumentEvaluation]
    
    # Synthèses
    evaluation_prerequis_4: Optional[PrerequisEvaluation]
    evaluation_prerequis_5: Optional[PrerequisEvaluation]
    synthese_globale: str
    
    # Validation
    validated_prerequis: List[int]  # Liste des IDs des prérequis validés (1 à 5)
    regeneration_comment: str  # Commentaire pour la régénération des prérequis non validés
    validation_pending: bool  # Flag pour savoir si on attend une validation
    
    # Résultats finaux
    final_evaluations: List[PrerequisEvaluation]
    prerequis_markdown: str
    success: bool
    error: str


class PrerequisEvaluationWorkflow:
    """Workflow pour évaluer les 5 prérequis de transformation IA"""
    
    def __init__(self, checkpointer: Optional[MemorySaver] = None) -> None:
        self.agent = PrerequisEvaluationAgent()
        self.checkpointer = checkpointer or MemorySaver()
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Crée le graphe du workflow"""
        workflow = StateGraph(PrerequisEvaluationState)
        
        # Ajouter les nœuds
        workflow.add_node("load_interventions", self._load_interventions_node)
        workflow.add_node("evaluate_prerequis_1", self._evaluate_prerequis_1_node)
        workflow.add_node("evaluate_prerequis_2", self._evaluate_prerequis_2_node)
        workflow.add_node("evaluate_prerequis_3", self._evaluate_prerequis_3_node)
        workflow.add_node("sync_prerequis_1_3", self._sync_prerequis_1_3_node)
        workflow.add_node("evaluate_prerequis_4_docs", self._evaluate_prerequis_4_docs_node)
        workflow.add_node("synthesize_prerequis_4", self._synthesize_prerequis_4_node)
        workflow.add_node("evaluate_prerequis_5_docs", self._evaluate_prerequis_5_docs_node)
        workflow.add_node("synthesize_prerequis_5", self._synthesize_prerequis_5_node)
        workflow.add_node("synthesize_global", self._synthesize_global_node)
        workflow.add_node("human_validation", self._human_validation_node)
        workflow.add_node("regenerate_prerequis", self._regenerate_prerequis_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Définir les edges
        workflow.set_entry_point("load_interventions")
        
        # Après chargement, évaluer prerequis 1, 2, 3 en parallèle
        workflow.add_edge("load_interventions", "evaluate_prerequis_1")
        workflow.add_edge("load_interventions", "evaluate_prerequis_2")
        workflow.add_edge("load_interventions", "evaluate_prerequis_3")
        
        # Tous les prerequis 1-3 pointent vers le nœud de synchronisation
        workflow.add_edge("evaluate_prerequis_1", "sync_prerequis_1_3")
        workflow.add_edge("evaluate_prerequis_2", "sync_prerequis_1_3")
        workflow.add_edge("evaluate_prerequis_3", "sync_prerequis_1_3")
        
        # Après synchronisation, vérifier si on peut continuer
        def route_after_sync(state: PrerequisEvaluationState) -> str:
            """Route après synchronisation : vérifier que tous les prerequis sont terminés"""
            evaluation_1 = state.get("evaluation_prerequis_1")
            evaluation_2 = state.get("evaluation_prerequis_2")
            evaluation_3 = state.get("evaluation_prerequis_3")
            
            if evaluation_1 and evaluation_2 and evaluation_3:
                return "evaluate_prerequis_4_docs"
            else:
                # Attendre encore (ce nœud sera rappelé)
                return "sync_prerequis_1_3"
        
        workflow.add_conditional_edges(
            "sync_prerequis_1_3",
            route_after_sync,
            {
                "evaluate_prerequis_4_docs": "evaluate_prerequis_4_docs",
                "sync_prerequis_1_3": "sync_prerequis_1_3"
            }
        )
        
        # Séquence pour prerequis 4 et 5
        workflow.add_edge("evaluate_prerequis_4_docs", "synthesize_prerequis_4")
        workflow.add_edge("synthesize_prerequis_4", "evaluate_prerequis_5_docs")
        workflow.add_edge("evaluate_prerequis_5_docs", "synthesize_prerequis_5")
        workflow.add_edge("synthesize_prerequis_5", "synthesize_global")
        workflow.add_edge("synthesize_global", "human_validation")
        
        # Route conditionnelle après validation
        def route_after_validation(state: PrerequisEvaluationState) -> str:
            """Route après validation : régénérer ou finaliser"""
            validated = state.get("validated_prerequis", [])
            if len(validated) == 5:
                # Tous validés, finaliser
                return "format_output"
            else:
                # Certains non validés, régénérer
                return "regenerate_prerequis"
        
        workflow.add_conditional_edges(
            "human_validation",
            route_after_validation,
            {
                "format_output": "format_output",
                "regenerate_prerequis": "regenerate_prerequis"
            }
        )
        
        # Après régénération, retourner à la synthèse globale
        workflow.add_edge("regenerate_prerequis", "synthesize_global")
        
        workflow.add_edge("format_output", END)
        
        # Compiler avec checkpointer et interrupt
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["human_validation"]
        )
    
    def _load_interventions_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Charge les interventions depuis la DB avec filtrage par speaker_level"""
        transcript_document_ids = state.get("transcript_document_ids", [])
        
        if not transcript_document_ids:
            logger.warning("Aucun document transcript fourni")
            return {
                "interventions_direction": [],
                "interventions_metier": [],
                "all_interventions": []
            }
        
        try:
            from database.db import get_db_context
            from database.repository import TranscriptRepository
            
            all_interventions = []
            interventions_direction = []
            interventions_metier = []
            
            def load_document_interventions(document_id: int) -> tuple:
                """Charge les interventions d'un document"""
                try:
                    with get_db_context() as db:
                        logger.info(f"Chargement du document {document_id}")
                        
                        # Récupérer les interventions enrichies
                        enriched_interventions = TranscriptRepository.get_enriched_by_document(
                            db, document_id, filter_interviewers=True
                        )
                        
                        logger.info(f"✓ Document {document_id}: {len(enriched_interventions)} interventions enrichies")
                        
                        # Formater les interventions
                        formatted_interventions = []
                        for interv in enriched_interventions:
                            formatted_interv = {
                                "text": interv.get("text"),
                                "speaker_level": interv.get("speaker_level"),
                                "speaker_role": interv.get("speaker_role"),
                                "speaker_type": interv.get("speaker_type"),
                            }
                            formatted_interventions.append(formatted_interv)
                        
                        return formatted_interventions
                        
                except Exception as e:
                    logger.error(f"❌ Erreur lors du chargement du document {document_id}: {e}")
                    return []
            
            # PARALLÉLISATION : Charger tous les documents en parallèle
            if len(transcript_document_ids) > 1:
                logger.info(f"🚀 Chargement parallèle de {len(transcript_document_ids)} documents")
                max_workers = min(len(transcript_document_ids), 10)
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_doc = {
                        executor.submit(load_document_interventions, doc_id): doc_id
                        for doc_id in transcript_document_ids
                    }
                    
                    for future in as_completed(future_to_doc):
                        doc_id = future_to_doc[future]
                        try:
                            interventions = future.result()
                            all_interventions.extend(interventions)
                            logger.info(f"✓ Document {doc_id} terminé: {len(interventions)} interventions")
                        except Exception as e:
                            logger.error(f"❌ Erreur document {doc_id}: {e}")
            else:
                # Traitement séquentiel si un seul document
                for doc_id in transcript_document_ids:
                    interventions = load_document_interventions(doc_id)
                    all_interventions.extend(interventions)
            
            # Filtrer par speaker_level et compter les documents uniques
            docs_with_direction = set()
            docs_with_metier = set()
            
            # Créer un mapping document_id -> interventions pour compter les documents
            doc_interventions_map = {}
            for doc_id in transcript_document_ids:
                doc_interventions_map[doc_id] = []
            
            # Parcourir toutes les interventions et les trier
            for interv in all_interventions:
                speaker_level = interv.get("speaker_level", "")
                if speaker_level == "direction":
                    interventions_direction.append(interv)
                    # Trouver le document d'origine (on doit le faire différemment)
                    # Pour l'instant, on va juste compter les types
                elif speaker_level == "métier":
                    interventions_metier.append(interv)
            
            # Compter les documents qui ont au moins une intervention de chaque type
            # On va recharger juste pour compter (mais c'est plus simple que de tracker pendant le chargement)
            for doc_id in transcript_document_ids:
                with get_db_context() as db:
                    enriched_interventions = TranscriptRepository.get_enriched_by_document(
                        db, doc_id, filter_interviewers=True
                    )
                    for interv in enriched_interventions:
                        speaker_level = interv.get("speaker_level", "")
                        if speaker_level == "direction":
                            docs_with_direction.add(doc_id)
                        elif speaker_level == "métier":
                            docs_with_metier.add(doc_id)
            
            logger.info(f"Total: {len(all_interventions)} interventions depuis {len(transcript_document_ids)} transcript(s)")
            logger.info(f"Direction: {len(interventions_direction)} interventions depuis {len(docs_with_direction)} transcript(s) avec direction")
            logger.info(f"Métier: {len(interventions_metier)} interventions depuis {len(docs_with_metier)} transcript(s) avec métier")
            
            return {
                "all_interventions": all_interventions,
                "interventions_direction": interventions_direction,
                "interventions_metier": interventions_metier
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des interventions: {e}")
            return {
                "success": False,
                "error": str(e),
                "interventions_direction": [],
                "interventions_metier": [],
                "all_interventions": []
            }
    
    def _evaluate_prerequis_1_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Évalue le prérequis 1 : Vision claire des leaders"""
        interventions_direction = state.get("interventions_direction", [])
        company_info = state.get("company_info", {})
        transcript_document_ids = state.get("transcript_document_ids", [])
        comments = state.get("comments", {})
        
        logger.info(f"📊 [PREREQUIS 1] Utilisation de {len(interventions_direction)} interventions direction depuis {len(transcript_document_ids)} transcript(s)")
        
        try:
            evaluation_response = self.agent.evaluate_prerequis_1(
                interventions_direction,
                company_info,
                comment_general=comments.get("comment_general", ""),
                comment_specific=comments.get("comment_1", "")
            )
            
            logger.info(f"✅ Prérequis 1 évalué : note {evaluation_response.evaluation.note}/5")
            # Retourner uniquement les clés modifiées pour éviter les conflits concurrents
            return {"evaluation_prerequis_1": evaluation_response.evaluation}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 1: {e}")
            return {"error": str(e)}
    
    def _evaluate_prerequis_2_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Évalue le prérequis 2 : Équipe projet complète"""
        interventions_metier = state.get("interventions_metier", [])
        company_info = state.get("company_info", {})
        transcript_document_ids = state.get("transcript_document_ids", [])
        comments = state.get("comments", {})
        
        logger.info(f"📊 [PREREQUIS 2] Utilisation de {len(interventions_metier)} interventions métier depuis {len(transcript_document_ids)} transcript(s)")
        
        try:
            evaluation_response = self.agent.evaluate_prerequis_2(
                interventions_metier,
                company_info,
                comment_general=comments.get("comment_general", ""),
                comment_specific=comments.get("comment_2", "")
            )
            
            logger.info(f"✅ Prérequis 2 évalué : note {evaluation_response.evaluation.note}/5")
            # Retourner uniquement les clés modifiées pour éviter les conflits concurrents
            return {"evaluation_prerequis_2": evaluation_response.evaluation}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 2: {e}")
            return {"error": str(e)}
    
    def _sync_prerequis_1_3_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Nœud de synchronisation : attend que les prerequis 1, 2, 3 soient terminés"""
        # Ce nœud est appelé plusieurs fois (une fois par chaque prerequis qui se termine)
        # On vérifie simplement que les 3 évaluations sont présentes
        evaluation_1 = state.get("evaluation_prerequis_1")
        evaluation_2 = state.get("evaluation_prerequis_2")
        evaluation_3 = state.get("evaluation_prerequis_3")
        
        if evaluation_1 and evaluation_2 and evaluation_3:
            logger.info("✅ Tous les prerequis 1-3 sont terminés")
        else:
            logger.info(f"⏳ En attente des prerequis 1-3 (1:{bool(evaluation_1)}, 2:{bool(evaluation_2)}, 3:{bool(evaluation_3)})")
        
        # Retourner un dictionnaire vide car ce nœud ne modifie rien
        return {}
    
    def _evaluate_prerequis_3_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Évalue le prérequis 3 : Cas d'usage important"""
        validated_use_cases = state.get("validated_use_cases", [])
        company_info = state.get("company_info", {})
        comments = state.get("comments", {})
        
        logger.info(f"📊 [PREREQUIS 3] Utilisation de {len(validated_use_cases)} cas d'usage validé(s) (pas de transcripts)")
        
        if not validated_use_cases:
            logger.warning("Aucun cas d'usage validé fourni")
            # Retourner uniquement les clés modifiées pour éviter les conflits concurrents
            return {
                "evaluation_prerequis_3": PrerequisEvaluation(
                    prerequis_id=3,
                    titre="Cas d'usage important pour le business",
                    evaluation_text="Aucun cas d'usage validé disponible.",
                    note=0.0
                )
            }
        
        try:
            evaluation_response = self.agent.evaluate_prerequis_3(
                validated_use_cases,
                company_info,
                comment_general=comments.get("comment_general", ""),
                comment_specific=comments.get("comment_3", "")
            )
            
            logger.info(f"✅ Prérequis 3 évalué : note {evaluation_response.evaluation.note}/5")
            # Retourner uniquement les clés modifiées pour éviter les conflits concurrents
            return {"evaluation_prerequis_3": evaluation_response.evaluation}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 3: {e}")
            return {"error": str(e)}
    
    def _evaluate_prerequis_4_docs_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Évalue le prérequis 4 document par document (parallélisé)"""
        transcript_document_ids = state.get("transcript_document_ids", [])
        all_interventions = state.get("all_interventions", [])
        company_info = state.get("company_info", {})
        comments = state.get("comments", {})
        
        logger.info(f"📊 [PREREQUIS 4] Évaluation de {len(transcript_document_ids)} transcript(s) document par document")
        
        if not transcript_document_ids:
            logger.warning("Aucun document transcript fourni")
            return {"evaluations_prerequis_4_by_doc": []}
        
        try:
            # Grouper les interventions par document
            from database.db import get_db_context
            from database.repository import TranscriptRepository
            
            evaluations_by_doc = []
            
            def evaluate_document(document_id: int) -> Optional[PrerequisDocumentEvaluation]:
                """Évalue un document pour le prérequis 4"""
                try:
                    with get_db_context() as db:
                        # Récupérer les interventions de ce document
                        enriched_interventions = TranscriptRepository.get_enriched_by_document(
                            db, document_id, filter_interviewers=True
                        )
                        
                        formatted_interventions = []
                        for interv in enriched_interventions:
                            formatted_interv = {
                                "text": interv.get("text"),
                                "speaker_level": interv.get("speaker_level"),
                                "speaker_role": interv.get("speaker_role"),
                                "speaker_type": interv.get("speaker_type"),
                            }
                            formatted_interventions.append(formatted_interv)
                        
                        # Évaluer ce document
                        evaluation_response = self.agent.evaluate_prerequis_4_document(
                            document_id,
                            formatted_interventions,
                            company_info,
                            comment_general=comments.get("comment_general", ""),
                            comment_specific=comments.get("comment_4", "")
                        )
                        
                        return evaluation_response.evaluation
                        
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'évaluation du document {document_id}: {e}")
                    return None
            
            # PARALLÉLISATION : Évaluer tous les documents en parallèle
            if len(transcript_document_ids) > 1:
                logger.info(f"🚀 Évaluation parallèle prerequis 4 sur {len(transcript_document_ids)} documents")
                max_workers = min(len(transcript_document_ids), 10)
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_doc = {
                        executor.submit(evaluate_document, doc_id): doc_id
                        for doc_id in transcript_document_ids
                    }
                    
                    for future in as_completed(future_to_doc):
                        doc_id = future_to_doc[future]
                        try:
                            evaluation = future.result()
                            if evaluation:
                                evaluations_by_doc.append(evaluation)
                                logger.info(f"✅ Document {doc_id} évalué : note {evaluation.note}/5")
                        except Exception as e:
                            logger.error(f"❌ Erreur document {doc_id}: {e}")
            else:
                # Traitement séquentiel si un seul document
                for doc_id in transcript_document_ids:
                    evaluation = evaluate_document(doc_id)
                    if evaluation:
                        evaluations_by_doc.append(evaluation)
            
            logger.info(f"✅ Prérequis 4 : {len(evaluations_by_doc)} documents évalués")
            return {"evaluations_prerequis_4_by_doc": evaluations_by_doc}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 4 par document: {e}")
            return {
                "error": str(e),
                "evaluations_prerequis_4_by_doc": []
            }
    
    def _synthesize_prerequis_4_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Synthétise les évaluations du prérequis 4"""
        evaluations_by_doc = state.get("evaluations_prerequis_4_by_doc", [])
        company_info = state.get("company_info", {})
        
        try:
            evaluation_response = self.agent.synthesize_prerequis_4(
                evaluations_by_doc,
                company_info
            )
            
            logger.info(f"✅ Prérequis 4 synthétisé : note {evaluation_response.evaluation.note}/5")
            return {"evaluation_prerequis_4": evaluation_response.evaluation}
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse du prérequis 4: {e}")
            return {"error": str(e)}
    
    def _evaluate_prerequis_5_docs_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Évalue le prérequis 5 document par document (parallélisé)"""
        transcript_document_ids = state.get("transcript_document_ids", [])
        company_info = state.get("company_info", {})
        comments = state.get("comments", {})
        
        logger.info(f"📊 [PREREQUIS 5] Évaluation de {len(transcript_document_ids)} transcript(s) document par document")
        
        if not transcript_document_ids:
            logger.warning("Aucun document transcript fourni")
            return {"evaluations_prerequis_5_by_doc": []}
        
        try:
            evaluations_by_doc = []
            
            def evaluate_document(document_id: int) -> Optional[PrerequisDocumentEvaluation]:
                """Évalue un document pour le prérequis 5"""
                try:
                    from database.db import get_db_context
                    from database.repository import TranscriptRepository
                    
                    with get_db_context() as db:
                        # Récupérer les interventions de ce document
                        enriched_interventions = TranscriptRepository.get_enriched_by_document(
                            db, document_id, filter_interviewers=True
                        )
                        
                        formatted_interventions = []
                        for interv in enriched_interventions:
                            formatted_interv = {
                                "text": interv.get("text"),
                                "speaker_level": interv.get("speaker_level"),
                                "speaker_role": interv.get("speaker_role"),
                                "speaker_type": interv.get("speaker_type"),
                            }
                            formatted_interventions.append(formatted_interv)
                        
                        # Évaluer ce document
                        evaluation_response = self.agent.evaluate_prerequis_5_document(
                            document_id,
                            formatted_interventions,
                            company_info,
                            comment_general=comments.get("comment_general", ""),
                            comment_specific=comments.get("comment_5", "")
                        )
                        
                        return evaluation_response.evaluation
                        
                except Exception as e:
                    logger.error(f"❌ Erreur lors de l'évaluation du document {document_id}: {e}")
                    return None
            
            # PARALLÉLISATION : Évaluer tous les documents en parallèle
            if len(transcript_document_ids) > 1:
                logger.info(f"🚀 Évaluation parallèle prerequis 5 sur {len(transcript_document_ids)} documents")
                max_workers = min(len(transcript_document_ids), 10)
                
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    future_to_doc = {
                        executor.submit(evaluate_document, doc_id): doc_id
                        for doc_id in transcript_document_ids
                    }
                    
                    for future in as_completed(future_to_doc):
                        doc_id = future_to_doc[future]
                        try:
                            evaluation = future.result()
                            if evaluation:
                                evaluations_by_doc.append(evaluation)
                                logger.info(f"✅ Document {doc_id} évalué : note {evaluation.note}/5")
                        except Exception as e:
                            logger.error(f"❌ Erreur document {doc_id}: {e}")
            else:
                # Traitement séquentiel si un seul document
                for doc_id in transcript_document_ids:
                    evaluation = evaluate_document(doc_id)
                    if evaluation:
                        evaluations_by_doc.append(evaluation)
            
            logger.info(f"✅ Prérequis 5 : {len(evaluations_by_doc)} documents évalués")
            return {"evaluations_prerequis_5_by_doc": evaluations_by_doc}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du prérequis 5 par document: {e}")
            return {
                "error": str(e),
                "evaluations_prerequis_5_by_doc": []
            }
    
    def _synthesize_prerequis_5_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Synthétise les évaluations du prérequis 5"""
        evaluations_by_doc = state.get("evaluations_prerequis_5_by_doc", [])
        company_info = state.get("company_info", {})
        
        try:
            evaluation_response = self.agent.synthesize_prerequis_5(
                evaluations_by_doc,
                company_info
            )
            
            logger.info(f"✅ Prérequis 5 synthétisé : note {evaluation_response.evaluation.note}/5")
            return {"evaluation_prerequis_5": evaluation_response.evaluation}
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse du prérequis 5: {e}")
            return {"error": str(e)}
    
    def _synthesize_global_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Synthétise globalement les 5 évaluations"""
        evaluation_1 = state.get("evaluation_prerequis_1")
        evaluation_2 = state.get("evaluation_prerequis_2")
        evaluation_3 = state.get("evaluation_prerequis_3")
        evaluation_4 = state.get("evaluation_prerequis_4")
        evaluation_5 = state.get("evaluation_prerequis_5")
        company_info = state.get("company_info", {})
        
        # Collecter toutes les évaluations
        evaluations = []
        if evaluation_1:
            evaluations.append(evaluation_1)
        if evaluation_2:
            evaluations.append(evaluation_2)
        if evaluation_3:
            evaluations.append(evaluation_3)
        if evaluation_4:
            evaluations.append(evaluation_4)
        if evaluation_5:
            evaluations.append(evaluation_5)
        
        if len(evaluations) != 5:
            logger.warning(f"Nombre d'évaluations incorrect : {len(evaluations)} au lieu de 5")
        
        try:
            synthesis_response = self.agent.synthesize_global_evaluation(
                evaluations,
                company_info
            )
            
            logger.info("✅ Synthèse globale terminée")
            return {
                "synthese_globale": synthesis_response.synthese_text,
                "final_evaluations": evaluations,
                "validation_pending": True  # Marquer qu'on attend une validation
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse globale: {e}")
            return {
                "error": str(e),
                "synthese_globale": f"Erreur lors de la synthèse globale : {str(e)}",
                "final_evaluations": evaluations,
                "validation_pending": True
            }
    
    def _human_validation_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """
        Nœud de validation humaine.
        
        Le workflow s'arrête AVANT ce nœud (interrupt_before).
        L'API/Streamlit détecte que le workflow est en pause.
        Streamlit affiche l'interface de validation.
        L'utilisateur valide et renvoie le feedback.
        Le feedback est injecté dans l'état via l'API.
        Le workflow reprend et ce nœud traite le feedback.
        """
        logger.info("🛑 [VALIDATION] human_validation_node - DÉBUT")
        
        # Vérifier si on a reçu le feedback (injecté par l'API via resume_workflow_with_validation)
        validated_prerequis = state.get("validated_prerequis", [])
        regeneration_comment = state.get("regeneration_comment", "")
        
        if not validated_prerequis:
            # Première fois : le workflow va s'arrêter ici (interrupt_before)
            logger.info("⏸️ [VALIDATION] En attente de validation utilisateur")
            return {
                "validation_pending": True
            }
        
        # Le feedback a été injecté, on continue
        logger.info(f"✅ [VALIDATION] Prérequis validés : {validated_prerequis}")
        logger.info(f"💬 [VALIDATION] Commentaire de régénération : {regeneration_comment[:50]}..." if regeneration_comment else "💬 [VALIDATION] Pas de commentaire")
        
        # Retourner l'état mis à jour
        return {
            "validation_pending": False
        }
    
    def _regenerate_prerequis_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Régénère uniquement les prérequis non validés avec le commentaire de régénération"""
        validated_prerequis = state.get("validated_prerequis", [])
        regeneration_comment = state.get("regeneration_comment", "")
        comments = state.get("comments", {})
        company_info = state.get("company_info", {})
        
        logger.info(f"🔄 [RÉGÉNÉRATION] Régénération des prérequis non validés")
        logger.info(f"✅ Prérequis validés : {validated_prerequis}")
        
        # Déterminer les prérequis à régénérer (1 à 5)
        all_prerequis_ids = [1, 2, 3, 4, 5]
        prerequis_to_regenerate = [pid for pid in all_prerequis_ids if pid not in validated_prerequis]
        
        if not prerequis_to_regenerate:
            logger.info("✅ Tous les prérequis sont validés, pas de régénération nécessaire")
            return {}
        
        logger.info(f"🔄 Prérequis à régénérer : {prerequis_to_regenerate}")
        
        # Construire le commentaire combiné (commentaire spécifique + commentaire de régénération)
        combined_comments = comments.copy()
        for prerequis_id in prerequis_to_regenerate:
            comment_key = f"comment_{prerequis_id}"
            original_comment = comments.get(comment_key, "")
            if regeneration_comment:
                if original_comment:
                    combined_comments[comment_key] = f"{original_comment}\n\nCOMMENTAIRE POUR RÉGÉNÉRATION :\n{regeneration_comment}"
                else:
                    combined_comments[comment_key] = f"COMMENTAIRE POUR RÉGÉNÉRATION :\n{regeneration_comment}"
        
        # Régénérer chaque prérequis non validé
        try:
            # Prérequis 1
            if 1 in prerequis_to_regenerate:
                interventions_direction = state.get("interventions_direction", [])
                evaluation_response = self.agent.evaluate_prerequis_1(
                    interventions_direction,
                    company_info,
                    comment_general=combined_comments.get("comment_general", ""),
                    comment_specific=combined_comments.get("comment_1", "")
                )
                state["evaluation_prerequis_1"] = evaluation_response.evaluation
                logger.info(f"✅ Prérequis 1 régénéré : note {evaluation_response.evaluation.note}/5")
            
            # Prérequis 2
            if 2 in prerequis_to_regenerate:
                interventions_metier = state.get("interventions_metier", [])
                evaluation_response = self.agent.evaluate_prerequis_2(
                    interventions_metier,
                    company_info,
                    comment_general=combined_comments.get("comment_general", ""),
                    comment_specific=combined_comments.get("comment_2", "")
                )
                state["evaluation_prerequis_2"] = evaluation_response.evaluation
                logger.info(f"✅ Prérequis 2 régénéré : note {evaluation_response.evaluation.note}/5")
            
            # Prérequis 3
            if 3 in prerequis_to_regenerate:
                validated_use_cases = state.get("validated_use_cases", [])
                evaluation_response = self.agent.evaluate_prerequis_3(
                    validated_use_cases,
                    company_info,
                    comment_general=combined_comments.get("comment_general", ""),
                    comment_specific=combined_comments.get("comment_3", "")
                )
                state["evaluation_prerequis_3"] = evaluation_response.evaluation
                logger.info(f"✅ Prérequis 3 régénéré : note {evaluation_response.evaluation.note}/5")
            
            # Prérequis 4
            if 4 in prerequis_to_regenerate:
                transcript_document_ids = state.get("transcript_document_ids", [])
                evaluations_by_doc = []
                
                def evaluate_document(document_id: int):
                    try:
                        from database.db import get_db_context
                        from database.repository import TranscriptRepository
                        
                        with get_db_context() as db:
                            enriched_interventions = TranscriptRepository.get_enriched_by_document(
                                db, document_id, filter_interviewers=True
                            )
                            
                            formatted_interventions = []
                            for interv in enriched_interventions:
                                formatted_interv = {
                                    "text": interv.get("text"),
                                    "speaker_level": interv.get("speaker_level"),
                                    "speaker_role": interv.get("speaker_role"),
                                    "speaker_type": interv.get("speaker_type"),
                                }
                                formatted_interventions.append(formatted_interv)
                            
                            evaluation_response = self.agent.evaluate_prerequis_4_document(
                                document_id,
                                formatted_interventions,
                                company_info,
                                comment_general=combined_comments.get("comment_general", ""),
                                comment_specific=combined_comments.get("comment_4", "")
                            )
                            return evaluation_response.evaluation
                    except Exception as e:
                        logger.error(f"❌ Erreur lors de l'évaluation du document {document_id}: {e}")
                        return None
                
                # Paralléliser si plusieurs documents
                if len(transcript_document_ids) > 1:
                    with ThreadPoolExecutor(max_workers=min(len(transcript_document_ids), 10)) as executor:
                        future_to_doc = {
                            executor.submit(evaluate_document, doc_id): doc_id
                            for doc_id in transcript_document_ids
                        }
                        
                        for future in as_completed(future_to_doc):
                            doc_id = future_to_doc[future]
                            try:
                                evaluation = future.result()
                                if evaluation:
                                    evaluations_by_doc.append(evaluation)
                            except Exception as e:
                                logger.error(f"❌ Erreur document {doc_id}: {e}")
                else:
                    for doc_id in transcript_document_ids:
                        evaluation = evaluate_document(doc_id)
                        if evaluation:
                            evaluations_by_doc.append(evaluation)
                
                # Synthétiser
                if evaluations_by_doc:
                    evaluation_response = self.agent.synthesize_prerequis_4(
                        evaluations_by_doc,
                        company_info
                    )
                    state["evaluation_prerequis_4"] = evaluation_response.evaluation
                    state["evaluations_prerequis_4_by_doc"] = evaluations_by_doc
                    logger.info(f"✅ Prérequis 4 régénéré : note {evaluation_response.evaluation.note}/5")
            
            # Prérequis 5
            if 5 in prerequis_to_regenerate:
                transcript_document_ids = state.get("transcript_document_ids", [])
                evaluations_by_doc = []
                
                def evaluate_document(document_id: int):
                    try:
                        from database.db import get_db_context
                        from database.repository import TranscriptRepository
                        
                        with get_db_context() as db:
                            enriched_interventions = TranscriptRepository.get_enriched_by_document(
                                db, document_id, filter_interviewers=True
                            )
                            
                            formatted_interventions = []
                            for interv in enriched_interventions:
                                formatted_interv = {
                                    "text": interv.get("text"),
                                    "speaker_level": interv.get("speaker_level"),
                                    "speaker_role": interv.get("speaker_role"),
                                    "speaker_type": interv.get("speaker_type"),
                                }
                                formatted_interventions.append(formatted_interv)
                            
                            evaluation_response = self.agent.evaluate_prerequis_5_document(
                                document_id,
                                formatted_interventions,
                                company_info,
                                comment_general=combined_comments.get("comment_general", ""),
                                comment_specific=combined_comments.get("comment_5", "")
                            )
                            return evaluation_response.evaluation
                    except Exception as e:
                        logger.error(f"❌ Erreur lors de l'évaluation du document {document_id}: {e}")
                        return None
                
                # Paralléliser si plusieurs documents
                if len(transcript_document_ids) > 1:
                    with ThreadPoolExecutor(max_workers=min(len(transcript_document_ids), 10)) as executor:
                        future_to_doc = {
                            executor.submit(evaluate_document, doc_id): doc_id
                            for doc_id in transcript_document_ids
                        }
                        
                        for future in as_completed(future_to_doc):
                            doc_id = future_to_doc[future]
                            try:
                                evaluation = future.result()
                                if evaluation:
                                    evaluations_by_doc.append(evaluation)
                            except Exception as e:
                                logger.error(f"❌ Erreur document {doc_id}: {e}")
                else:
                    for doc_id in transcript_document_ids:
                        evaluation = evaluate_document(doc_id)
                        if evaluation:
                            evaluations_by_doc.append(evaluation)
                
                # Synthétiser
                if evaluations_by_doc:
                    evaluation_response = self.agent.synthesize_prerequis_5(
                        evaluations_by_doc,
                        company_info
                    )
                    state["evaluation_prerequis_5"] = evaluation_response.evaluation
                    state["evaluations_prerequis_5_by_doc"] = evaluations_by_doc
                    logger.info(f"✅ Prérequis 5 régénéré : note {evaluation_response.evaluation.note}/5")
            
            logger.info(f"✅ Régénération terminée pour les prérequis : {prerequis_to_regenerate}")
            return {}
            
        except Exception as e:
            logger.error(f"Erreur lors de la régénération : {e}")
            return {"error": str(e)}
    
    def _format_output_node(self, state: PrerequisEvaluationState) -> PrerequisEvaluationState:
        """Formate la sortie en markdown"""
        final_evaluations = state.get("final_evaluations", [])
        synthese_globale = state.get("synthese_globale", "")
        company_info = state.get("company_info", {})
        
        try:
            company_name = company_info.get("nom") or company_info.get("company_name", "l'entreprise")
            
            if not final_evaluations or len(final_evaluations) != 5:
                return {
                    "prerequis_markdown": f"# Évaluation des 5 prérequis pour {company_name}\n\nÉvaluation incomplète.",
                    "success": False
                }
            
            # Construire le markdown
            markdown_parts = [f"# Évaluation des 5 prérequis pour {company_name}\n"]
            
            # Ajouter chaque évaluation
            for evaluation in final_evaluations:
                markdown_parts.append(f"## {evaluation.prerequis_id}. {evaluation.titre}\n")
                markdown_parts.append(f"{evaluation.evaluation_text}\n")
                markdown_parts.append(f"\n**Note : {evaluation.note}/5**\n")
                markdown_parts.append("")  # Ligne vide
            
            # Ajouter la synthèse globale
            if synthese_globale:
                markdown_parts.append("## Synthèse globale\n")
                markdown_parts.append(f"{synthese_globale}\n")
            
            logger.info("Formatage markdown terminé")
            return {
                "prerequis_markdown": "\n".join(markdown_parts),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du formatage: {e}")
            return {
                "success": False,
                "error": str(e),
                "prerequis_markdown": ""
            }
    
    def run(
        self,
        transcript_document_ids: List[int],
        company_info: Dict[str, Any],
        validated_use_cases: List[Dict[str, Any]],
        thread_id: Optional[str] = None,
        comments: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Exécute le workflow d'évaluation des prérequis
        
        Args:
            transcript_document_ids: Liste des IDs de documents transcripts dans la DB
            company_info: Informations sur l'entreprise
            validated_use_cases: Liste des cas d'usage validés (obligatoire)
            thread_id: ID du thread pour la persistance (optionnel)
            
        Returns:
            État final du workflow avec les évaluations
        """
        if not validated_use_cases:
            return {
                "success": False,
                "error": "validated_use_cases est obligatoire"
            }
        
        initial_state: PrerequisEvaluationState = {
            "transcript_document_ids": transcript_document_ids,
            "company_info": company_info,
            "validated_use_cases": validated_use_cases,
            "comments": comments or {},
            "interventions_direction": [],
            "interventions_metier": [],
            "all_interventions": [],
            "evaluations_prerequis_4_by_doc": [],
            "evaluations_prerequis_5_by_doc": [],
            "validated_prerequis": [],
            "regeneration_comment": "",
            "validation_pending": False,
            "final_evaluations": [],
            "synthese_globale": ""
        }
        
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())
            logger.info(f"🔑 Thread ID généré automatiquement: {thread_id}")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Exécuter le workflow
        logger.info(f"🚀 Exécution du workflow avec thread_id: {thread_id}")
        
        final_state = None
        for chunk in self.graph.stream(initial_state, config):
            logger.info(f"📊 Chunk reçu: {list(chunk.keys())}")
            for node_name, node_state in chunk.items():
                logger.info(f"  • Nœud '{node_name}' exécuté")
                final_state = node_state
        
        # Récupérer l'état complet depuis le checkpointer
        snapshot = self.graph.get_state(config)
        state = snapshot.values
        
        # Vérifier si le workflow est en attente de validation
        if state.get("validation_pending", False):
            logger.info("⏸️ Workflow en attente de validation")
            return {
                "success": True,
                "validation_pending": True,
                "final_evaluations": [eval.model_dump() if hasattr(eval, 'model_dump') else eval for eval in state.get("final_evaluations", [])],
                "synthese_globale": state.get("synthese_globale", ""),
                "prerequis_markdown": "",
                "error": ""
            }
        
        logger.info(f"✅ Workflow terminé")
        return {
            "success": state.get("success", False),
            "validation_pending": False,
            "final_evaluations": [eval.model_dump() if hasattr(eval, 'model_dump') else eval for eval in state.get("final_evaluations", [])],
            "synthese_globale": state.get("synthese_globale", ""),
            "prerequis_markdown": state.get("prerequis_markdown", ""),
            "error": state.get("error", "")
        }
    
    def resume_workflow_with_validation(
        self,
        validated_prerequis: List[int],
        regeneration_comment: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Reprend le workflow après validation utilisateur
        
        Args:
            validated_prerequis: Liste des IDs des prérequis validés (1 à 5)
            regeneration_comment: Commentaire pour la régénération des prérequis non validés
            thread_id: ID du thread
            
        Returns:
            État final du workflow
        """
        logger.info(f"🔄 Reprise du workflow avec validation pour thread {thread_id}")
        logger.info(f"✅ Prérequis validés : {validated_prerequis}")
        logger.info(f"💬 Commentaire de régénération : {regeneration_comment[:50]}..." if regeneration_comment else "💬 Pas de commentaire")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Récupérer l'état actuel
        snapshot = self.graph.get_state(config)
        if not snapshot:
            raise ValueError(f"Thread {thread_id} non trouvé")
        
        # Mettre à jour l'état avec le feedback
        current_state = snapshot.values
        current_state["validated_prerequis"] = validated_prerequis
        current_state["regeneration_comment"] = regeneration_comment
        current_state["validation_pending"] = False
        
        # Mettre à jour l'état dans le checkpointer
        self.graph.update_state(config, current_state)
        
        # Reprendre l'exécution
        final_state = None
        for chunk in self.graph.stream(None, config):
            logger.info(f"📊 Chunk reçu: {list(chunk.keys())}")
            for node_name, node_state in chunk.items():
                logger.info(f"  • Nœud '{node_name}' exécuté")
                final_state = node_state
        
        # Récupérer l'état final
        snapshot = self.graph.get_state(config)
        state = snapshot.values
        
        # Vérifier si on est encore en attente de validation (nouvelle boucle)
        if state.get("validation_pending", False):
            logger.info("⏸️ Workflow en attente de validation (nouvelle boucle)")
            return {
                "success": True,
                "validation_pending": True,
                "final_evaluations": [eval.model_dump() if hasattr(eval, 'model_dump') else eval for eval in state.get("final_evaluations", [])],
                "synthese_globale": state.get("synthese_globale", ""),
                "prerequis_markdown": "",
                "error": ""
            }
        
        logger.info(f"✅ Workflow terminé après validation")
        return {
            "success": state.get("success", False),
            "validation_pending": False,
            "final_evaluations": [eval.model_dump() if hasattr(eval, 'model_dump') else eval for eval in state.get("final_evaluations", [])],
            "synthese_globale": state.get("synthese_globale", ""),
            "prerequis_markdown": state.get("prerequis_markdown", ""),
            "error": state.get("error", "")
        }

