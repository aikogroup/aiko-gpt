"""
Workflow LangGraph pour l'extraction de la chaîne de valeur
"""

from typing import TypedDict, Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging
import json

from value_chain.value_chain_agent import ValueChainAgent
from models.value_chain_models import Function, Mission, FrictionPoint

logger = logging.getLogger(__name__)


class ValueChainState(TypedDict, total=False):
    """État du workflow d'extraction de la chaîne de valeur"""
    
    # Inputs
    transcript_document_ids: List[int]  # IDs des documents transcripts dans la DB
    company_info: Dict[str, Any]
    
    # Intermediate results
    all_interventions: List[Dict[str, Any]]  # Interventions chargées depuis la DB
    
    # Résultats d'extraction
    proposed_functions: List[Dict[str, Any]]
    proposed_missions: List[Dict[str, Any]]
    proposed_friction_points: List[Dict[str, Any]]
    
    # Validation humaine
    validated_functions: List[Dict[str, Any]]
    rejected_functions: List[Dict[str, Any]]
    functions_validation_result: Dict[str, Any]
    
    validated_missions: List[Dict[str, Any]]
    rejected_missions: List[Dict[str, Any]]
    missions_validation_result: Dict[str, Any]
    
    validated_friction_points: List[Dict[str, Any]]
    rejected_friction_points: List[Dict[str, Any]]
    friction_points_validation_result: Dict[str, Any]
    
    # Contrôle du workflow
    functions_user_action: str  # "continue_functions" ou "continue_to_missions"
    missions_user_action: str  # "continue_missions" ou "continue_to_friction"
    friction_points_user_action: str  # "continue_friction" ou "finalize"
    workflow_paused: bool
    validation_type: str  # "functions", "missions", "friction_points"
    
    # Résultats finaux
    final_value_chain: Dict[str, Any]
    value_chain_markdown: str
    value_chain_json: str
    success: bool
    error: str


class ValueChainWorkflow:
    """Workflow pour extraire la chaîne de valeur de l'entreprise"""
    
    def __init__(self, checkpointer: Optional[MemorySaver] = None) -> None:
        self.value_chain_agent = ValueChainAgent()
        self.checkpointer = checkpointer or MemorySaver()
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Crée le graphe du workflow avec HITL"""
        workflow = StateGraph(ValueChainState)
        
        # Ajouter les nœuds
        workflow.add_node("load_interventions", self._load_interventions_node)
        workflow.add_node("extract_functions", self._extract_functions_node)
        workflow.add_node("validate_functions", self._validate_functions_node)
        workflow.add_node("check_functions_action", self._check_functions_action_node)
        workflow.add_node("extract_missions", self._extract_missions_node)
        workflow.add_node("validate_missions", self._validate_missions_node)
        workflow.add_node("check_missions_action", self._check_missions_action_node)
        workflow.add_node("extract_friction_points", self._extract_friction_points_node)
        workflow.add_node("validate_friction_points", self._validate_friction_points_node)
        workflow.add_node("check_friction_points_action", self._check_friction_points_action_node)
        workflow.add_node("finalize_value_chain", self._finalize_value_chain_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Définir les edges
        workflow.set_entry_point("load_interventions")
        workflow.add_edge("load_interventions", "extract_functions")
        workflow.add_edge("extract_functions", "validate_functions")
        workflow.add_edge("validate_functions", "check_functions_action")
        
        # Router conditionnel après validation des fonctions
        def route_after_functions(state: ValueChainState) -> str:
            action = state.get("functions_user_action", "")
            if action == "continue_functions":
                return "extract_functions"
            else:
                return "extract_missions"
        
        workflow.add_conditional_edges(
            "check_functions_action",
            route_after_functions,
            {
                "extract_functions": "extract_functions",
                "extract_missions": "extract_missions"
            }
        )
        
        workflow.add_edge("extract_missions", "validate_missions")
        workflow.add_edge("validate_missions", "check_missions_action")
        
        # Router conditionnel après validation des missions
        def route_after_missions(state: ValueChainState) -> str:
            action = state.get("missions_user_action", "")
            if action == "continue_missions":
                return "extract_missions"
            else:
                return "extract_friction_points"
        
        workflow.add_conditional_edges(
            "check_missions_action",
            route_after_missions,
            {
                "extract_missions": "extract_missions",
                "extract_friction_points": "extract_friction_points"
            }
        )
        
        workflow.add_edge("extract_friction_points", "validate_friction_points")
        workflow.add_edge("validate_friction_points", "check_friction_points_action")
        
        # Router conditionnel après validation des points de friction
        def route_after_friction(state: ValueChainState) -> str:
            action = state.get("friction_points_user_action", "")
            if action == "continue_friction":
                return "extract_friction_points"
            else:
                return "finalize_value_chain"
        
        workflow.add_conditional_edges(
            "check_friction_points_action",
            route_after_friction,
            {
                "extract_friction_points": "extract_friction_points",
                "finalize_value_chain": "finalize_value_chain"
            }
        )
        
        workflow.add_edge("finalize_value_chain", "format_output")
        workflow.add_edge("format_output", END)
        
        # Compiler avec checkpointer et interrupts
        return workflow.compile(
            checkpointer=self.checkpointer,
            interrupt_before=["validate_functions", "validate_missions", "validate_friction_points"]
        )
    
    def _load_interventions_node(self, state: ValueChainState) -> ValueChainState:
        """Charge les interventions depuis la DB (PARALLÉLISÉ)"""
        transcript_document_ids = state.get("transcript_document_ids", [])
        
        if not transcript_document_ids:
            logger.warning("Aucun document transcript fourni")
            state["all_interventions"] = []
            return state
        
        try:
            from database.db import get_db_context
            from database.repository import TranscriptRepository
            from concurrent.futures import ThreadPoolExecutor, as_completed
            
            all_interventions = []
            
            def load_document_interventions(document_id: int) -> List[Dict[str, Any]]:
                """Charge les interventions d'un document (fonction pour parallélisation)"""
                try:
                    with get_db_context() as db:
                        logger.info(f"Chargement du document {document_id}")
                        
                        # Récupérer directement les interventions enrichies depuis la DB
                        enriched_interventions = TranscriptRepository.get_enriched_by_document(
                            db, document_id, filter_interviewers=True
                        )
                        
                        logger.info(f"✓ Document {document_id}: {len(enriched_interventions)} interventions enrichies")
                        
                        # Formater les interventions (sans timestamp, avec role et level)
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
            
            state["all_interventions"] = all_interventions
            logger.info(f"Total: {len(all_interventions)} interventions chargées")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des interventions: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["all_interventions"] = []
            return state
    
    def _extract_functions_node(self, state: ValueChainState) -> ValueChainState:
        """Extrait les fonctions depuis les interventions"""
        all_interventions = state.get("all_interventions", [])
        company_info = state.get("company_info", {})
        validated_functions = state.get("validated_functions", [])
        rejected_functions = state.get("rejected_functions", [])
        
        if not all_interventions:
            logger.warning("Aucune intervention à analyser")
            state["proposed_functions"] = []
            return state
        
        try:
            # Convertir les fonctions validées en objets Function pour le prompt
            functions_objects = []
            for function_dict in validated_functions:
                functions_objects.append(Function(**function_dict))
            
            # Extraire les fonctions
            functions_response = self.value_chain_agent.extract_functions(
                all_interventions,
                company_info
            )
            
            # Convertir en dict pour le state
            proposed_functions = [function.model_dump() for function in functions_response.functions]
            
            # Filtrer les fonctions déjà validées/rejetées (éviter les doublons)
            validated_names = {f.get("nom", "") for f in validated_functions}
            rejected_names = {f.get("nom", "") for f in rejected_functions}
            
            filtered_functions = [
                f for f in proposed_functions
                if f.get("nom", "") not in validated_names and f.get("nom", "") not in rejected_names
            ]
            
            state["proposed_functions"] = filtered_functions
            logger.info(f"Extrait {len(filtered_functions)} nouvelles fonctions proposées")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des fonctions: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["proposed_functions"] = []
            return state
    
    def _validate_functions_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de validation humaine des fonctions"""
        logger.info(f"\n🛑 [INTERRUPT] validate_functions_node - DÉBUT")
        logger.info(f"📊 Fonctions proposées: {len(state.get('proposed_functions', []))}")
        
        try:
            if "functions_validation_result" in state and state["functions_validation_result"]:
                logger.info(f"✅ [RESUME] Feedback fonctions reçu via API")
                validation_data = state["functions_validation_result"]
                
                # Traiter les résultats de validation
                existing_validated = state.get("validated_functions", [])
                newly_validated = validation_data.get("validated_functions", [])
                state["validated_functions"] = existing_validated + newly_validated
                
                existing_rejected = state.get("rejected_functions", [])
                newly_rejected = validation_data.get("rejected_functions", [])
                state["rejected_functions"] = existing_rejected + newly_rejected
                
                state["functions_user_action"] = validation_data.get("functions_user_action", "continue_to_missions")
                state["functions_validation_result"] = {}
                
                logger.info(f"📊 [RESUME] Fonctions nouvellement validées: {len(newly_validated)}")
                logger.info(f"▶️ [RESUME] Workflow continue...")
                
                return state
            else:
                logger.info(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                state["validation_type"] = "functions"
                state["workflow_paused"] = True
                return state
                
        except Exception as e:
            logger.error(f"❌ [ERROR] Erreur dans validate_functions_node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _check_functions_action_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de décision : continuer avec fonctions ou passer aux missions"""
        logger.info(f"\n🔍 [DEBUG] check_functions_action_node - DÉBUT")
        functions_user_action = state.get("functions_user_action", "")
        logger.info(f"🎯 Action utilisateur: {functions_user_action}")
        return state
    
    def _extract_missions_node(self, state: ValueChainState) -> ValueChainState:
        """Extrait les missions pour chaque fonction validée"""
        all_interventions = state.get("all_interventions", [])
        validated_functions = state.get("validated_functions", [])
        validated_missions = state.get("validated_missions", [])
        rejected_missions = state.get("rejected_missions", [])
        
        if not all_interventions or not validated_functions:
            logger.warning("Aucune intervention ou équipe validée")
            state["proposed_missions"] = []
            return state
        
        try:
            # Convertir les fonctions validées en objets Function
            functions_objects = [Function(**function_dict) for function_dict in validated_functions]
            
            # Extraire les missions
            missions_response = self.value_chain_agent.extract_missions(
                all_interventions,
                functions_objects
            )
            
            # Convertir en dict pour le state
            proposed_missions = [mission.model_dump() for mission in missions_response.missions]
            logger.info(f"🔍 [DEBUG] Extrait {len(proposed_missions)} missions brutes depuis le LLM")
            
            # DEBUG: Afficher les function_nom des missions extraites
            extracted_function_noms = {a.get("function_nom", "") for a in proposed_missions}
            logger.info(f"🔍 [DEBUG] Function noms dans missions extraites: {extracted_function_noms}")
            if proposed_missions:
                logger.info(f"🔍 [DEBUG] Détail des missions extraites:")
                for act in proposed_missions:
                    logger.info(f"   - function_nom: '{act.get('function_nom', '')}', resume: '{act.get('resume', '')[:50]}...'")
            
            # Filtrer les missions déjà validées/rejetées
            validated_function_noms = {a.get("function_nom", "") for a in validated_missions}
            rejected_function_noms = {a.get("function_nom", "") for a in rejected_missions}
            
            logger.info(f"🔍 [DEBUG] Function noms déjà validés: {validated_function_noms}")
            logger.info(f"🔍 [DEBUG] Function noms déjà rejetés: {rejected_function_noms}")
            
            filtered_missions = [
                a for a in proposed_missions
                if a.get("function_nom", "") not in validated_function_noms and a.get("function_nom", "") not in rejected_function_noms
            ]
            logger.info(f"🔍 [DEBUG] Missions après filtrage validés/rejetés: {len(filtered_missions)}")
            
            # Garantir une seule mission par équipe
            # Si plusieurs missions pour la même équipe, fusionner les résumés
            missions_by_function = {}
            for mission in filtered_missions:
                function_nom = mission.get("function_nom", "")
                if not function_nom:
                    logger.warning(f"🔍 [DEBUG] Mission sans function_nom ignorée: {mission}")
                    continue
                    
                if function_nom not in missions_by_function:
                    missions_by_function[function_nom] = mission
                else:
                    # Fusionner les résumés si plusieurs missions pour la même équipe
                    existing_resume = missions_by_function[function_nom].get("resume", "")
                    new_resume = mission.get("resume", "")
                    if existing_resume and new_resume:
                        merged_resume = f"{existing_resume}, {new_resume}"
                    else:
                        merged_resume = existing_resume or new_resume
                    missions_by_function[function_nom]["resume"] = merged_resume
            
            logger.info(f"🔍 [DEBUG] Missions groupées par function_nom: {list(missions_by_function.keys())}")
            
            # Ne garder que les équipes validées qui n'ont pas encore d'mission
            validated_functions_noms = {t.get("nom", "") for t in validated_functions}
            logger.info(f"�� [DEBUG] Noms des équipes validées: {validated_functions_noms}")
            if validated_functions:
                logger.info(f"�� [DEBUG] Détail des équipes validées:")
                for function in validated_functions:
                    logger.info(f"   - nom: '{function.get('nom', '')}', id: '{function.get('id', '')}'")
            
            # Fonction de normalisation pour le matching (enlève espaces autour de &, normalise espaces)
            def normalize_for_matching(name: str) -> str:
                """Normalise un nom pour le matching uniquement (sans modifier la valeur originale)"""
                if not name:
                    return ""
                # Enlever espaces autour de &
                normalized = name.replace(" & ", "&").replace(" &", "&").replace("& ", "&")
                # Normaliser espaces multiples
                normalized = " ".join(normalized.split())
                return normalized.strip().lower()
            
            # Normaliser les noms des équipes validées pour le matching
            validated_functions_noms_normalized = {normalize_for_matching(nom) for nom in validated_functions_noms}
            
            # Matcher avec normalisation, mais garder le nom exact de l'équipe validée
            final_missions = []
            for function_nom, mission in missions_by_function.items():
                function_nom_normalized = normalize_for_matching(function_nom)
                if function_nom_normalized in validated_functions_noms_normalized:
                    # Trouver l'équipe validée correspondante pour utiliser son nom exact
                    matching_function = None
                    for function in validated_functions:
                        if normalize_for_matching(function.get("nom", "")) == function_nom_normalized:
                            matching_function = function
                            break
                    
                    if matching_function:
                        # Utiliser le nom exact de l'équipe validée
                        mission["function_nom"] = matching_function.get("nom", "")
                        final_missions.append(mission)
            
            logger.info(f"🔍 [DEBUG] Missions finales après filtrage par équipes validées: {len(final_missions)}")
            if len(final_missions) == 0 and len(missions_by_function) > 0:
                logger.error(f"❌ [ERROR] Aucune mission ne correspond aux équipes validées!")
                logger.error(f"   Function noms dans missions: {list(missions_by_function.keys())}")
                logger.error(f"   Noms équipes validées: {validated_functions_noms}")
                # Si aucun match, on prend toutes les missions groupées (fallback)
                final_missions = list(missions_by_function.values())
                logger.warning(f"⚠️ [FALLBACK] Utilisation de toutes les missions extraites: {len(final_missions)}")
            
            state["proposed_missions"] = final_missions
            logger.info(f"Extrait {len(final_missions)} missions proposées (une par équipe)")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des missions: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["proposed_missions"] = []
            return state
    
    def _validate_missions_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de validation humaine des missions"""
        logger.info(f"\n🛑 [INTERRUPT] validate_missions_node - DÉBUT")
        logger.info(f"📊 Missions proposées: {len(state.get('proposed_missions', []))}")
        
        try:
            if "missions_validation_result" in state and state["missions_validation_result"]:
                logger.info(f"✅ [RESUME] Feedback missions reçu via API")
                validation_data = state["missions_validation_result"]
                
                existing_validated = state.get("validated_missions", [])
                newly_validated = validation_data.get("validated_missions", [])
                state["validated_missions"] = existing_validated + newly_validated
                
                existing_rejected = state.get("rejected_missions", [])
                newly_rejected = validation_data.get("rejected_missions", [])
                state["rejected_missions"] = existing_rejected + newly_rejected
                
                state["missions_user_action"] = validation_data.get("missions_user_action", "continue_to_friction")
                state["missions_validation_result"] = {}
                
                logger.info(f"📊 [RESUME] Missions nouvellement validées: {len(newly_validated)}")
                logger.info(f"▶️ [RESUME] Workflow continue...")
                
                return state
            else:
                logger.info(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                state["validation_type"] = "missions"
                state["workflow_paused"] = True
                return state
                
        except Exception as e:
            logger.error(f"❌ [ERROR] Erreur dans validate_missions_node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _check_missions_action_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de décision : continuer avec missions ou passer aux points de friction"""
        logger.info(f"\n🔍 [DEBUG] check_missions_action_node - DÉBUT")
        missions_user_action = state.get("missions_user_action", "")
        logger.info(f"🎯 Action utilisateur: {missions_user_action}")
        return state
    
    def _extract_friction_points_node(self, state: ValueChainState) -> ValueChainState:
        """Extrait les points de friction pour chaque équipe validée"""
        all_interventions = state.get("all_interventions", [])
        validated_functions = state.get("validated_functions", [])
        validated_friction_points = state.get("validated_friction_points", [])
        rejected_friction_points = state.get("rejected_friction_points", [])
        
        if not all_interventions or not validated_functions:
            logger.warning("Aucune intervention ou équipe validée")
            state["proposed_friction_points"] = []
            return state
        
        try:
            # Convertir les fonctions validées en objets Function
            functions_objects = [Function(**function_dict) for function_dict in validated_functions]
            
            # Extraire les points de friction
            friction_points_response = self.value_chain_agent.extract_friction_points(
                all_interventions,
                functions_objects
            )
            
            # Convertir en dict pour le state
            proposed_friction_points = [fp.model_dump() for fp in friction_points_response.friction_points]
            
            # Fonction de normalisation pour le matching (enlève espaces autour de &, normalise espaces)
            def normalize_for_matching(name: str) -> str:
                """Normalise un nom pour le matching uniquement (sans modifier la valeur originale)"""
                if not name:
                    return ""
                # Enlever espaces autour de &
                normalized = name.replace(" & ", "&").replace(" &", "&").replace("& ", "&")
                # Normaliser espaces multiples
                normalized = " ".join(normalized.split())
                return normalized.strip().lower()
            
            # Créer un mapping ID -> équipe et nom -> équipe pour le matching
            functions_by_id = {t.get("id", ""): t for t in validated_functions}
            functions_by_nom = {t.get("nom", ""): t for t in validated_functions}
            functions_by_nom_normalized = {normalize_for_matching(nom): t for nom, t in functions_by_nom.items()}
            
            # Normaliser les function_nom des points de friction et les matcher avec les équipes validées
            for fp in proposed_friction_points:
                fp_function_nom = fp.get("function_nom", "")
                fp_function_nom_normalized = normalize_for_matching(fp_function_nom)
                
                # Trouver l'équipe validée correspondante
                # Essayer d'abord par ID (au cas où le LLM aurait utilisé l'ID)
                matching_function = functions_by_id.get(fp_function_nom)
                
                # Si pas trouvé par ID, essayer par nom normalisé
                if not matching_function:
                    matching_function = functions_by_nom_normalized.get(fp_function_nom_normalized)
                
                # Si toujours pas trouvé, essayer par nom exact
                if not matching_function:
                    matching_function = functions_by_nom.get(fp_function_nom)
                
                if matching_function:
                    # Utiliser le nom exact de l'équipe validée
                    fp["function_nom"] = matching_function.get("nom", "")
                    logger.debug(f"🔍 [FRICTION] Point de friction '{fp_function_nom}' → équipe '{matching_function.get('nom', '')}'")
                else:
                    logger.warning(f"🔍 [FRICTION] Point de friction avec function_nom '{fp_function_nom}' ne correspond à aucune équipe validée")
            
            # Filtrer les points de friction sans équipe valide (ceux qui n'ont pas pu être matchés)
            valid_friction_points = [
                fp for fp in proposed_friction_points
                if fp.get("function_nom", "") and fp.get("function_nom", "") in functions_by_nom
            ]
            
            # Filtrer les points de friction déjà validés/rejetés (basé sur function_nom et citation)
            validated_keys = {(fp.get("function_nom", ""), fp.get("citation", "")) for fp in validated_friction_points}
            rejected_keys = {(fp.get("function_nom", ""), fp.get("citation", "")) for fp in rejected_friction_points}
            
            filtered_friction_points = [
                fp for fp in valid_friction_points
                if (fp.get("function_nom", ""), fp.get("citation", "")) not in validated_keys
                and (fp.get("function_nom", ""), fp.get("citation", "")) not in rejected_keys
            ]
            
            state["proposed_friction_points"] = filtered_friction_points
            logger.info(f"Extrait {len(filtered_friction_points)} nouveaux points de friction proposés")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des points de friction: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["proposed_friction_points"] = []
            return state
    
    def _validate_friction_points_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de validation humaine des points de friction"""
        logger.info(f"\n🛑 [INTERRUPT] validate_friction_points_node - DÉBUT")
        logger.info(f"📊 Points de friction proposés: {len(state.get('proposed_friction_points', []))}")
        
        try:
            if "friction_points_validation_result" in state and state["friction_points_validation_result"]:
                logger.info(f"✅ [RESUME] Feedback points de friction reçu via API")
                validation_data = state["friction_points_validation_result"]
                
                existing_validated = state.get("validated_friction_points", [])
                newly_validated = validation_data.get("validated_friction_points", [])
                state["validated_friction_points"] = existing_validated + newly_validated
                
                existing_rejected = state.get("rejected_friction_points", [])
                newly_rejected = validation_data.get("rejected_friction_points", [])
                state["rejected_friction_points"] = existing_rejected + newly_rejected
                
                state["friction_points_user_action"] = validation_data.get("friction_points_user_action", "finalize")
                state["friction_points_validation_result"] = {}
                
                logger.info(f"📊 [RESUME] Points de friction nouvellement validés: {len(newly_validated)}")
                logger.info(f"▶️ [RESUME] Workflow continue...")
                
                return state
            else:
                logger.info(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                state["validation_type"] = "friction_points"
                state["workflow_paused"] = True
                return state
                
        except Exception as e:
            logger.error(f"❌ [ERROR] Erreur dans validate_friction_points_node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _check_friction_points_action_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de décision : continuer avec points de friction ou finaliser"""
        logger.info(f"\n🔍 [DEBUG] check_friction_points_action_node - DÉBUT")
        friction_points_user_action = state.get("friction_points_user_action", "")
        logger.info(f"🎯 Action utilisateur: {friction_points_user_action}")
        return state
    
    def _finalize_value_chain_node(self, state: ValueChainState) -> ValueChainState:
        """Finalise la chaîne de valeur"""
        try:
            logger.info(f"\n🔍 [DEBUG] _finalize_value_chain_node - DÉBUT")
            
            validated_functions = state.get("validated_functions", [])
            validated_missions = state.get("validated_missions", [])
            validated_friction_points = state.get("validated_friction_points", [])
            
            logger.info(f"📊 Fonctions validées: {len(validated_functions)}")
            logger.info(f"📊 Missions validées: {len(validated_missions)}")
            logger.info(f"📊 Points de friction validés: {len(validated_friction_points)}")
            
            # Structurer les données finales
            final_value_chain = {
                "functions": validated_functions,
                "missions": validated_missions,
                "friction_points": validated_friction_points
            }
            
            state["final_value_chain"] = final_value_chain
            logger.info(f"✅ [DEBUG] _finalize_value_chain_node - FIN")
            
            return state
            
        except Exception as e:
            logger.error(f"❌ [DEBUG] Erreur dans _finalize_value_chain_node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _format_output_node(self, state: ValueChainState) -> ValueChainState:
        """Formate la sortie en markdown et JSON"""
        final_value_chain = state.get("final_value_chain", {})
        company_info = state.get("company_info", {})
        
        try:
            company_name = company_info.get("nom", "l'entreprise")
            
            functions = final_value_chain.get("functions", [])
            missions = final_value_chain.get("missions", [])
            friction_points = final_value_chain.get("friction_points", [])
            
            if not functions:
                state["value_chain_markdown"] = f"# Chaîne de valeur de {company_name}\n\nAucune fonction identifiée."
                state["value_chain_json"] = json.dumps(final_value_chain, ensure_ascii=False, indent=2)
                state["success"] = True
                return state
            
            # Construire le markdown
            markdown_parts = [f"# Chaîne de valeur de {company_name}\n"]
            
            # Grouper les fonctions par type
            fonctions_metier = [f for f in functions if f.get("type") == "fonction_metier"]
            fonctions_support = [f for f in functions if f.get("type") == "fonction_support"]
            
            # Fonctions métier
            if fonctions_metier:
                markdown_parts.append("## Fonctions métier\n")
                for function in fonctions_metier:
                    function_id = function.get("id", "")
                    function_name = function.get("nom", "")
                    function_desc = function.get("description", "")
                    markdown_parts.append(f"### {function_name}\n")
                    markdown_parts.append(f"{function_desc}\n")
                    
                    # Missions de cette fonction
                    function_missions = [m for m in missions if m.get("function_nom") == function_name]
                    if function_missions:
                        for mission in function_missions:
                            markdown_parts.append(f"- **Mission** : {mission.get('resume', '')}\n")
                    
                    # Points de friction de cette fonction
                    function_friction = [fp for fp in friction_points if fp.get("function_nom") == function_name]
                    if function_friction:
                        markdown_parts.append(f"\n**Points de friction (gestion des données)** :\n")
                        for fp in function_friction:
                            markdown_parts.append(f"- *\"{fp.get('citation', '')}\"* - {fp.get('description', '')}\n")
                    
                    markdown_parts.append("")  # Ligne vide
            
            # Fonctions support
            if fonctions_support:
                markdown_parts.append("## Fonctions support\n")
                for function in fonctions_support:
                    function_id = function.get("id", "")
                    function_name = function.get("nom", "")
                    function_desc = function.get("description", "")
                    markdown_parts.append(f"### {function_name}\n")
                    markdown_parts.append(f"{function_desc}\n")
                    
                    # Missions de cette fonction
                    function_missions = [m for m in missions if m.get("function_nom") == function_name]
                    if function_missions:
                        for mission in function_missions:
                            markdown_parts.append(f"- **Mission** : {mission.get('resume', '')}\n")
                    
                    # Points de friction de cette fonction
                    function_friction = [fp for fp in friction_points if fp.get("function_nom") == function_name]
                    if function_friction:
                        markdown_parts.append(f"\n**Points de friction (gestion des données)** :\n")
                        for fp in function_friction:
                            markdown_parts.append(f"- *\"{fp.get('citation', '')}\"* - {fp.get('description', '')}\n")
                    
                    markdown_parts.append("")  # Ligne vide
            
            state["value_chain_markdown"] = "\n".join(markdown_parts)
            state["value_chain_json"] = json.dumps(final_value_chain, ensure_ascii=False, indent=2)
            state["success"] = True
            logger.info("Formatage markdown et JSON terminé")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors du formatage: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["value_chain_markdown"] = ""
            state["value_chain_json"] = ""
            return state
    
    def run(
        self,
        transcript_document_ids: List[int],
        company_info: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exécute le workflow d'extraction de la chaîne de valeur
        
        Args:
            transcript_document_ids: Liste des IDs de documents transcripts dans la DB
            company_info: Informations sur l'entreprise depuis web search
            thread_id: ID du thread pour la persistance (optionnel)
            
        Returns:
            État final du workflow avec la chaîne de valeur extraite
        """
        initial_state: ValueChainState = {
            "transcript_document_ids": transcript_document_ids,
            "company_info": company_info,
            "validated_functions": [],
            "rejected_functions": [],
            "validated_missions": [],
            "rejected_missions": [],
            "validated_friction_points": [],
            "rejected_friction_points": [],
            "workflow_paused": False,
            "validation_type": ""
        }
        
        if not thread_id:
            import uuid
            thread_id = str(uuid.uuid4())
            logger.info(f"🔑 Thread ID généré automatiquement: {thread_id}")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Exécuter le workflow
        logger.info(f"🚀 Exécution du graphe avec thread_id: {thread_id}")
        
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
        if any(node in next_nodes for node in ["validate_functions", "validate_missions", "validate_friction_points"]):
            # Le workflow s'est arrêté à une validation
            validation_type = state.get("validation_type", "")
            logger.info(f"⏸️ Workflow arrêté pour validation: {validation_type}")
            return {
                "success": False,
                "workflow_paused": True,
                "validation_type": validation_type,
                "proposed_functions": state.get("proposed_functions", []),
                "proposed_missions": state.get("proposed_missions", []),
                "proposed_friction_points": state.get("proposed_friction_points", []),
                "validated_functions": state.get("validated_functions", []),
                "validated_missions": state.get("validated_missions", []),
                "validated_friction_points": state.get("validated_friction_points", []),
                "messages": [f"Workflow en pause - en attente de validation: {validation_type}"]
            }
        elif len(next_nodes) == 0:
            # Le workflow est terminé
            logger.info(f"✅ Workflow terminé")
            return {
                "success": True,
                "workflow_paused": False,
                "final_value_chain": state.get("final_value_chain", {}),
                "value_chain_markdown": state.get("value_chain_markdown", ""),
                "value_chain_json": state.get("value_chain_json", ""),
                "validated_functions": state.get("validated_functions", []),
                "validated_missions": state.get("validated_missions", []),
                "validated_friction_points": state.get("validated_friction_points", []),
                "messages": ["Workflow terminé avec succès"]
            }
        else:
            # Autre état
            logger.warning(f"⚠️ Workflow dans un état inattendu: {next_nodes}")
            return {
                "success": False,
                "workflow_paused": True,
                "messages": [f"Workflow en pause - next_nodes: {next_nodes}"]
            }
    
    def resume_workflow_with_validation(
        self,
        validation_type: str,
        validated_items: List[Dict[str, Any]],
        rejected_items: List[Dict[str, Any]],
        user_action: str,
        thread_id: str
    ) -> Dict[str, Any]:
        """
        Reprend le workflow après validation avec le feedback.
        
        Args:
            validation_type: Type de validation ("teams", "missions", "friction_points")
            validated_items: Items validés par l'utilisateur
            rejected_items: Items rejetés par l'utilisateur
            user_action: Action demandée ("continue_teams", "continue_to_missions", etc.)
            thread_id: ID du thread
            
        Returns:
            État du workflow
        """
        logger.info(f"\n🔄 resume_workflow_with_validation() appelé")
        logger.info(f"✅ Validés: {len(validated_items)}")
        logger.info(f"❌ Rejetés: {len(rejected_items)}")
        logger.info(f"🎯 Action: {user_action}")
        
        config = {"configurable": {"thread_id": thread_id}}
        
        # Mettre à jour l'état avec le feedback
        current_state = self.graph.get_state(config)
        updated_values = {
            **current_state.values,
        }
        
        # Mettre à jour selon le type de validation
        if validation_type == "functions":
            updated_values["teams_validation_result"] = {
                "validated_functions": validated_items,
                "rejected_functions": rejected_items
            }
            updated_values["teams_user_action"] = user_action
        elif validation_type == "missions":
            updated_values["missions_validation_result"] = {
                "validated_missions": validated_items,
                "rejected_missions": rejected_items
            }
            updated_values["missions_user_action"] = user_action
        elif validation_type == "friction_points":
            updated_values["friction_points_validation_result"] = {
                "validated_friction_points": validated_items,
                "rejected_friction_points": rejected_items
            }
            updated_values["friction_points_user_action"] = user_action
        
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
        
        # Si on doit continuer (validation dans next_nodes)
        if any(node in next_nodes for node in ["validate_functions", "validate_missions", "validate_friction_points"]):
            validation_type = state.get("validation_type", "")
            logger.info(f"⏸️ Workflow arrêté pour validation: {validation_type}")
            return {
                "success": False,
                "workflow_paused": True,
                "validation_type": validation_type,
                "proposed_functions": state.get("proposed_functions", []),
                "proposed_missions": state.get("proposed_missions", []),
                "proposed_friction_points": state.get("proposed_friction_points", []),
                "validated_functions": state.get("validated_functions", []),
                "validated_missions": state.get("validated_missions", []),
                "validated_friction_points": state.get("validated_friction_points", []),
                "messages": [f"Workflow en pause - en attente de validation: {validation_type}"]
            }
        else:
            # Workflow terminé
            logger.info(f"✅ Workflow terminé")
            return {
                "success": True,
                "workflow_paused": False,
                "final_value_chain": state.get("final_value_chain", {}),
                "value_chain_markdown": state.get("value_chain_markdown", ""),
                "value_chain_json": state.get("value_chain_json", ""),
                "validated_functions": state.get("validated_functions", []),
                "validated_missions": state.get("validated_missions", []),
                "validated_friction_points": state.get("validated_friction_points", []),
                "messages": ["Workflow terminé avec succès"]
            }

