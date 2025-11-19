"""
Workflow LangGraph pour l'extraction de la chaîne de valeur
"""

from typing import TypedDict, Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import logging
import json

from value_chain.value_chain_agent import ValueChainAgent
from models.value_chain_models import Team, Activity, FrictionPoint

logger = logging.getLogger(__name__)


class ValueChainState(TypedDict, total=False):
    """État du workflow d'extraction de la chaîne de valeur"""
    
    # Inputs
    transcript_document_ids: List[int]  # IDs des documents transcripts dans la DB
    company_info: Dict[str, Any]
    
    # Intermediate results
    all_interventions: List[Dict[str, Any]]  # Interventions chargées depuis la DB
    
    # Résultats d'extraction
    proposed_teams: List[Dict[str, Any]]
    proposed_activities: List[Dict[str, Any]]
    proposed_friction_points: List[Dict[str, Any]]
    
    # Validation humaine
    validated_teams: List[Dict[str, Any]]
    rejected_teams: List[Dict[str, Any]]
    teams_validation_result: Dict[str, Any]
    
    validated_activities: List[Dict[str, Any]]
    rejected_activities: List[Dict[str, Any]]
    activities_validation_result: Dict[str, Any]
    
    validated_friction_points: List[Dict[str, Any]]
    rejected_friction_points: List[Dict[str, Any]]
    friction_points_validation_result: Dict[str, Any]
    
    # Contrôle du workflow
    teams_user_action: str  # "continue_teams" ou "continue_to_activities"
    activities_user_action: str  # "continue_activities" ou "continue_to_friction"
    friction_points_user_action: str  # "continue_friction" ou "finalize"
    workflow_paused: bool
    validation_type: str  # "teams", "activities", "friction_points"
    
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
        workflow.add_node("extract_teams", self._extract_teams_node)
        workflow.add_node("validate_teams", self._validate_teams_node)
        workflow.add_node("check_teams_action", self._check_teams_action_node)
        workflow.add_node("extract_activities", self._extract_activities_node)
        workflow.add_node("validate_activities", self._validate_activities_node)
        workflow.add_node("check_activities_action", self._check_activities_action_node)
        workflow.add_node("extract_friction_points", self._extract_friction_points_node)
        workflow.add_node("validate_friction_points", self._validate_friction_points_node)
        workflow.add_node("check_friction_points_action", self._check_friction_points_action_node)
        workflow.add_node("finalize_value_chain", self._finalize_value_chain_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Définir les edges
        workflow.set_entry_point("load_interventions")
        workflow.add_edge("load_interventions", "extract_teams")
        workflow.add_edge("extract_teams", "validate_teams")
        workflow.add_edge("validate_teams", "check_teams_action")
        
        # Router conditionnel après validation des équipes
        def route_after_teams(state: ValueChainState) -> str:
            action = state.get("teams_user_action", "")
            if action == "continue_teams":
                return "extract_teams"
            else:
                return "extract_activities"
        
        workflow.add_conditional_edges(
            "check_teams_action",
            route_after_teams,
            {
                "extract_teams": "extract_teams",
                "extract_activities": "extract_activities"
            }
        )
        
        workflow.add_edge("extract_activities", "validate_activities")
        workflow.add_edge("validate_activities", "check_activities_action")
        
        # Router conditionnel après validation des activités
        def route_after_activities(state: ValueChainState) -> str:
            action = state.get("activities_user_action", "")
            if action == "continue_activities":
                return "extract_activities"
            else:
                return "extract_friction_points"
        
        workflow.add_conditional_edges(
            "check_activities_action",
            route_after_activities,
            {
                "extract_activities": "extract_activities",
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
            interrupt_before=["validate_teams", "validate_activities", "validate_friction_points"]
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
    
    def _extract_teams_node(self, state: ValueChainState) -> ValueChainState:
        """Extrait les équipes depuis les interventions"""
        all_interventions = state.get("all_interventions", [])
        company_info = state.get("company_info", {})
        validated_teams = state.get("validated_teams", [])
        rejected_teams = state.get("rejected_teams", [])
        
        if not all_interventions:
            logger.warning("Aucune intervention à analyser")
            state["proposed_teams"] = []
            return state
        
        try:
            # Convertir les équipes validées en objets Team pour le prompt
            teams_objects = []
            for team_dict in validated_teams:
                teams_objects.append(Team(**team_dict))
            
            # Extraire les équipes
            teams_response = self.value_chain_agent.extract_teams(
                all_interventions,
                company_info
            )
            
            # Convertir en dict pour le state
            proposed_teams = [team.model_dump() for team in teams_response.teams]
            
            # Filtrer les équipes déjà validées/rejetées (éviter les doublons)
            validated_names = {t.get("nom", "") for t in validated_teams}
            rejected_names = {t.get("nom", "") for t in rejected_teams}
            
            filtered_teams = [
                t for t in proposed_teams
                if t.get("nom", "") not in validated_names and t.get("nom", "") not in rejected_names
            ]
            
            state["proposed_teams"] = filtered_teams
            logger.info(f"Extrait {len(filtered_teams)} nouvelles équipes proposées")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des équipes: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["proposed_teams"] = []
            return state
    
    def _validate_teams_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de validation humaine des équipes"""
        logger.info(f"\n🛑 [INTERRUPT] validate_teams_node - DÉBUT")
        logger.info(f"📊 Équipes proposées: {len(state.get('proposed_teams', []))}")
        
        try:
            if "teams_validation_result" in state and state["teams_validation_result"]:
                logger.info(f"✅ [RESUME] Feedback équipes reçu via API")
                validation_data = state["teams_validation_result"]
                
                # Traiter les résultats de validation
                existing_validated = state.get("validated_teams", [])
                newly_validated = validation_data.get("validated_teams", [])
                state["validated_teams"] = existing_validated + newly_validated
                
                existing_rejected = state.get("rejected_teams", [])
                newly_rejected = validation_data.get("rejected_teams", [])
                state["rejected_teams"] = existing_rejected + newly_rejected
                
                state["teams_user_action"] = validation_data.get("teams_user_action", "continue_to_activities")
                state["teams_validation_result"] = {}
                
                logger.info(f"📊 [RESUME] Équipes nouvellement validées: {len(newly_validated)}")
                logger.info(f"▶️ [RESUME] Workflow continue...")
                
                return state
            else:
                logger.info(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                state["validation_type"] = "teams"
                state["workflow_paused"] = True
                return state
                
        except Exception as e:
            logger.error(f"❌ [ERROR] Erreur dans validate_teams_node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _check_teams_action_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de décision : continuer avec équipes ou passer aux activités"""
        logger.info(f"\n🔍 [DEBUG] check_teams_action_node - DÉBUT")
        teams_user_action = state.get("teams_user_action", "")
        logger.info(f"🎯 Action utilisateur: {teams_user_action}")
        return state
    
    def _extract_activities_node(self, state: ValueChainState) -> ValueChainState:
        """Extrait les activités pour chaque équipe validée"""
        all_interventions = state.get("all_interventions", [])
        validated_teams = state.get("validated_teams", [])
        validated_activities = state.get("validated_activities", [])
        rejected_activities = state.get("rejected_activities", [])
        
        if not all_interventions or not validated_teams:
            logger.warning("Aucune intervention ou équipe validée")
            state["proposed_activities"] = []
            return state
        
        try:
            # Convertir les équipes validées en objets Team
            teams_objects = [Team(**team_dict) for team_dict in validated_teams]
            
            # Extraire les activités
            activities_response = self.value_chain_agent.extract_activities(
                all_interventions,
                teams_objects
            )
            
            # Convertir en dict pour le state
            proposed_activities = [activity.model_dump() for activity in activities_response.activities]
            logger.info(f"🔍 [DEBUG] Extrait {len(proposed_activities)} activités brutes depuis le LLM")
            
            # DEBUG: Afficher les team_id des activités extraites
            extracted_team_ids = {a.get("team_id", "") for a in proposed_activities}
            logger.info(f"🔍 [DEBUG] Team IDs dans activités extraites: {extracted_team_ids}")
            if proposed_activities:
                logger.info(f"🔍 [DEBUG] Détail des activités extraites:")
                for act in proposed_activities:
                    logger.info(f"   - team_id: '{act.get('team_id', '')}', resume: '{act.get('resume', '')[:50]}...'")
            
            # Filtrer les activités déjà validées/rejetées
            validated_team_noms = {a.get("team_nom", "") for a in validated_activities}
            rejected_team_noms = {a.get("team_nom", "") for a in rejected_activities}
            
            logger.info(f"🔍 [DEBUG] Team noms déjà validés: {validated_team_noms}")
            logger.info(f"🔍 [DEBUG] Team noms déjà rejetés: {rejected_team_noms}")
            
            filtered_activities = [
                a for a in proposed_activities
                if a.get("team_nom", "") not in validated_team_noms and a.get("team_nom", "") not in rejected_team_noms
            ]
            logger.info(f"🔍 [DEBUG] Activités après filtrage validés/rejetés: {len(filtered_activities)}")
            
            # Garantir une seule activité par équipe
            # Si plusieurs activités pour la même équipe, fusionner les résumés
            activities_by_team = {}
            for activity in filtered_activities:
                team_nom = activity.get("team_nom", "")
                if not team_nom:
                    logger.warning(f"🔍 [DEBUG] Activité sans team_nom ignorée: {activity}")
                    continue
                    
                if team_nom not in activities_by_team:
                    activities_by_team[team_nom] = activity
                else:
                    # Fusionner les résumés si plusieurs activités pour la même équipe
                    existing_resume = activities_by_team[team_nom].get("resume", "")
                    new_resume = activity.get("resume", "")
                    if existing_resume and new_resume:
                        merged_resume = f"{existing_resume}, {new_resume}"
                    else:
                        merged_resume = existing_resume or new_resume
                    activities_by_team[team_nom]["resume"] = merged_resume
            
            logger.info(f"🔍 [DEBUG] Activités groupées par team_nom: {list(activities_by_team.keys())}")
            
            # Ne garder que les équipes validées qui n'ont pas encore d'activité
            validated_teams_noms = {t.get("nom", "") for t in validated_teams}
            logger.info(f"�� [DEBUG] Noms des équipes validées: {validated_teams_noms}")
            if validated_teams:
                logger.info(f"�� [DEBUG] Détail des équipes validées:")
                for team in validated_teams:
                    logger.info(f"   - nom: '{team.get('nom', '')}', id: '{team.get('id', '')}'")
            
            final_activities = [
                activity for team_nom, activity in activities_by_team.items()
                if team_nom in validated_teams_noms
            ]
            
            logger.info(f"🔍 [DEBUG] Activités finales après filtrage par équipes validées: {len(final_activities)}")
            if len(final_activities) == 0 and len(activities_by_team) > 0:
                logger.error(f"❌ [ERROR] Aucune activité ne correspond aux équipes validées!")
                logger.error(f"   Team noms dans activités: {list(activities_by_team.keys())}")
                logger.error(f"   Noms équipes validées: {validated_teams_noms}")
                # Si aucun match, on prend toutes les activités groupées (fallback)
                final_activities = list(activities_by_team.values())
                logger.warning(f"⚠️ [FALLBACK] Utilisation de toutes les activités extraites: {len(final_activities)}")
            
            state["proposed_activities"] = final_activities
            logger.info(f"Extrait {len(final_activities)} activités proposées (une par équipe)")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction des activités: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["proposed_activities"] = []
            return state
    
    def _validate_activities_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de validation humaine des activités"""
        logger.info(f"\n🛑 [INTERRUPT] validate_activities_node - DÉBUT")
        logger.info(f"📊 Activités proposées: {len(state.get('proposed_activities', []))}")
        
        try:
            if "activities_validation_result" in state and state["activities_validation_result"]:
                logger.info(f"✅ [RESUME] Feedback activités reçu via API")
                validation_data = state["activities_validation_result"]
                
                existing_validated = state.get("validated_activities", [])
                newly_validated = validation_data.get("validated_activities", [])
                state["validated_activities"] = existing_validated + newly_validated
                
                existing_rejected = state.get("rejected_activities", [])
                newly_rejected = validation_data.get("rejected_activities", [])
                state["rejected_activities"] = existing_rejected + newly_rejected
                
                state["activities_user_action"] = validation_data.get("activities_user_action", "continue_to_friction")
                state["activities_validation_result"] = {}
                
                logger.info(f"📊 [RESUME] Activités nouvellement validées: {len(newly_validated)}")
                logger.info(f"▶️ [RESUME] Workflow continue...")
                
                return state
            else:
                logger.info(f"⏸️ [INTERRUPT] Aucun feedback - le workflow va s'arrêter")
                state["validation_type"] = "activities"
                state["workflow_paused"] = True
                return state
                
        except Exception as e:
            logger.error(f"❌ [ERROR] Erreur dans validate_activities_node: {str(e)}")
            state["error"] = str(e)
            return state
    
    def _check_activities_action_node(self, state: ValueChainState) -> ValueChainState:
        """Nœud de décision : continuer avec activités ou passer aux points de friction"""
        logger.info(f"\n🔍 [DEBUG] check_activities_action_node - DÉBUT")
        activities_user_action = state.get("activities_user_action", "")
        logger.info(f"🎯 Action utilisateur: {activities_user_action}")
        return state
    
    def _extract_friction_points_node(self, state: ValueChainState) -> ValueChainState:
        """Extrait les points de friction pour chaque équipe validée"""
        all_interventions = state.get("all_interventions", [])
        validated_teams = state.get("validated_teams", [])
        validated_friction_points = state.get("validated_friction_points", [])
        rejected_friction_points = state.get("rejected_friction_points", [])
        
        if not all_interventions or not validated_teams:
            logger.warning("Aucune intervention ou équipe validée")
            state["proposed_friction_points"] = []
            return state
        
        try:
            # Convertir les équipes validées en objets Team
            teams_objects = [Team(**team_dict) for team_dict in validated_teams]
            
            # Extraire les points de friction
            friction_points_response = self.value_chain_agent.extract_friction_points(
                all_interventions,
                teams_objects
            )
            
            # Convertir en dict pour le state
            proposed_friction_points = [fp.model_dump() for fp in friction_points_response.friction_points]
            
            # Filtrer les points de friction déjà validés/rejetés (basé sur team_nom et citation)
            validated_keys = {(fp.get("team_nom", ""), fp.get("citation", "")) for fp in validated_friction_points}
            rejected_keys = {(fp.get("team_nom", ""), fp.get("citation", "")) for fp in rejected_friction_points}
            
            filtered_friction_points = [
                fp for fp in proposed_friction_points
                if (fp.get("team_nom", ""), fp.get("citation", "")) not in validated_keys
                and (fp.get("team_nom", ""), fp.get("citation", "")) not in rejected_keys
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
            
            validated_teams = state.get("validated_teams", [])
            validated_activities = state.get("validated_activities", [])
            validated_friction_points = state.get("validated_friction_points", [])
            
            logger.info(f"📊 Équipes validées: {len(validated_teams)}")
            logger.info(f"📊 Activités validées: {len(validated_activities)}")
            logger.info(f"📊 Points de friction validés: {len(validated_friction_points)}")
            
            # Structurer les données finales
            final_value_chain = {
                "teams": validated_teams,
                "activities": validated_activities,
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
            
            teams = final_value_chain.get("teams", [])
            activities = final_value_chain.get("activities", [])
            friction_points = final_value_chain.get("friction_points", [])
            
            if not teams:
                state["value_chain_markdown"] = f"# Chaîne de valeur de {company_name}\n\nAucune équipe identifiée."
                state["value_chain_json"] = json.dumps(final_value_chain, ensure_ascii=False, indent=2)
                state["success"] = True
                return state
            
            # Construire le markdown
            markdown_parts = [f"# Chaîne de valeur de {company_name}\n"]
            
            # Grouper les équipes par type
            equipes_metier = [t for t in teams if t.get("type") == "equipe_metier"]
            equipes_support = [t for t in teams if t.get("type") == "equipe_support"]
            
            # Équipes métier
            if equipes_metier:
                markdown_parts.append("## Équipes métier\n")
                for team in equipes_metier:
                    team_id = team.get("id", "")
                    team_name = team.get("nom", "")
                    team_desc = team.get("description", "")
                    markdown_parts.append(f"### {team_name}\n")
                    markdown_parts.append(f"{team_desc}\n")
                    
                    # Activités de cette équipe
                    team_activities = [a for a in activities if a.get("team_nom") == team_name]
                    if team_activities:
                        for activity in team_activities:
                            markdown_parts.append(f"- **Activités** : {activity.get('resume', '')}\n")
                    
                    # Points de friction de cette équipe
                    team_friction = [fp for fp in friction_points if fp.get("team_nom") == team_name]
                    if team_friction:
                        markdown_parts.append(f"\n**Points de friction (gestion des données)** :\n")
                        for fp in team_friction:
                            markdown_parts.append(f"- *\"{fp.get('citation', '')}\"* - {fp.get('description', '')}\n")
                    
                    markdown_parts.append("")  # Ligne vide
            
            # Équipes support
            if equipes_support:
                markdown_parts.append("## Équipes support\n")
                for team in equipes_support:
                    team_id = team.get("id", "")
                    team_name = team.get("nom", "")
                    team_desc = team.get("description", "")
                    markdown_parts.append(f"### {team_name}\n")
                    markdown_parts.append(f"{team_desc}\n")
                    
                    # Activités de cette équipe
                    team_activities = [a for a in activities if a.get("team_nom") == team_name]
                    if team_activities:
                        for activity in team_activities:
                            markdown_parts.append(f"- **Activités** : {activity.get('resume', '')}\n")
                    
                    # Points de friction de cette équipe
                    team_friction = [fp for fp in friction_points if fp.get("team_nom") == team_name]
                    if team_friction:
                        markdown_parts.append(f"\n**Points de friction (gestion des données)** :\n")
                        for fp in team_friction:
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
            "validated_teams": [],
            "rejected_teams": [],
            "validated_activities": [],
            "rejected_activities": [],
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
        if any(node in next_nodes for node in ["validate_teams", "validate_activities", "validate_friction_points"]):
            # Le workflow s'est arrêté à une validation
            validation_type = state.get("validation_type", "")
            logger.info(f"⏸️ Workflow arrêté pour validation: {validation_type}")
            return {
                "success": False,
                "workflow_paused": True,
                "validation_type": validation_type,
                "proposed_teams": state.get("proposed_teams", []),
                "proposed_activities": state.get("proposed_activities", []),
                "proposed_friction_points": state.get("proposed_friction_points", []),
                "validated_teams": state.get("validated_teams", []),
                "validated_activities": state.get("validated_activities", []),
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
                "validated_teams": state.get("validated_teams", []),
                "validated_activities": state.get("validated_activities", []),
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
            validation_type: Type de validation ("teams", "activities", "friction_points")
            validated_items: Items validés par l'utilisateur
            rejected_items: Items rejetés par l'utilisateur
            user_action: Action demandée ("continue_teams", "continue_to_activities", etc.)
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
        if validation_type == "teams":
            updated_values["teams_validation_result"] = {
                "validated_teams": validated_items,
                "rejected_teams": rejected_items
            }
            updated_values["teams_user_action"] = user_action
        elif validation_type == "activities":
            updated_values["activities_validation_result"] = {
                "validated_activities": validated_items,
                "rejected_activities": rejected_items
            }
            updated_values["activities_user_action"] = user_action
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
        if any(node in next_nodes for node in ["validate_teams", "validate_activities", "validate_friction_points"]):
            validation_type = state.get("validation_type", "")
            logger.info(f"⏸️ Workflow arrêté pour validation: {validation_type}")
            return {
                "success": False,
                "workflow_paused": True,
                "validation_type": validation_type,
                "proposed_teams": state.get("proposed_teams", []),
                "proposed_activities": state.get("proposed_activities", []),
                "proposed_friction_points": state.get("proposed_friction_points", []),
                "validated_teams": state.get("validated_teams", []),
                "validated_activities": state.get("validated_activities", []),
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
                "validated_teams": state.get("validated_teams", []),
                "validated_activities": state.get("validated_activities", []),
                "validated_friction_points": state.get("validated_friction_points", []),
                "messages": ["Workflow terminé avec succès"]
            }

