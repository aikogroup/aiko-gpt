"""
Workflow LangGraph pour l'extraction des atouts de l'entreprise
"""

from typing import TypedDict, Dict, Any, Optional, List
from langgraph.graph import StateGraph, END
import logging
from pathlib import Path

from process_transcript.interesting_parts_agent import InterestingPartsAgent
from process_transcript.pdf_parser import PDFParser
from process_transcript.json_parser import JSONParser
from process_transcript.speaker_classifier import SpeakerClassifier
from atouts.atouts_agent import AtoutsAgent

logger = logging.getLogger(__name__)


class AtoutsState(TypedDict, total=False):
    """État du workflow d'extraction des atouts"""
    
    # Inputs
    pdf_paths: List[str]
    company_info: Dict[str, Any]
    
    # Intermediate results
    interesting_interventions: List[Dict[str, Any]]
    citations_atouts: Dict[str, Any]
    
    # Output
    atouts: Dict[str, Any]
    atouts_markdown: str
    success: bool
    error: str


class AtoutsWorkflow:
    """Workflow pour extraire les atouts de l'entreprise"""
    
    def __init__(self, interviewer_names: Optional[List[str]] = None) -> None:
        self.pdf_parser = PDFParser()
        self.json_parser = JSONParser()
        self.interesting_parts_agent = InterestingPartsAgent()
        self.speaker_classifier = SpeakerClassifier(interviewer_names=interviewer_names)
        self.atouts_agent = AtoutsAgent()
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """Crée le graphe du workflow"""
        workflow = StateGraph(AtoutsState)
        
        # Ajouter les nœuds
        workflow.add_node("extract_interesting_parts", self._extract_interesting_parts_node)
        workflow.add_node("extract_citations", self._extract_citations_node)
        workflow.add_node("synthesize_atouts", self._synthesize_atouts_node)
        workflow.add_node("format_output", self._format_output_node)
        
        # Définir les edges
        workflow.set_entry_point("extract_interesting_parts")
        workflow.add_edge("extract_interesting_parts", "extract_citations")
        workflow.add_edge("extract_citations", "synthesize_atouts")
        workflow.add_edge("synthesize_atouts", "format_output")
        workflow.add_edge("format_output", END)
        
        return workflow.compile()
    
    def _extract_interesting_parts_node(self, state: AtoutsState) -> AtoutsState:
        """Extrait les parties intéressantes des transcriptions avec classification des speakers"""
        pdf_paths = state.get("pdf_paths", [])
        
        if not pdf_paths:
            logger.warning("Aucun PDF fourni")
            state["interesting_interventions"] = []
            return state
        
        try:
            all_interventions = []
            
            for pdf_path in pdf_paths:
                logger.info(f"Traitement du PDF: {pdf_path}")
                
                # Étape 1: Parser le PDF selon son type
                file_extension = Path(pdf_path).suffix.lower()
                if file_extension == '.json':
                    interventions = self.json_parser.parse_transcript(pdf_path)
                elif file_extension == '.pdf':
                    interventions = self.pdf_parser.parse_transcript(pdf_path)
                else:
                    logger.warning(f"Format non supporté: {file_extension}, skip")
                    continue
                
                logger.info(f"Parsé {len(interventions)} interventions de {pdf_path}")
                
                # Étape 2: Classifier les speakers (interviewer/interviewé, direction/métier)
                logger.info("Classification des speakers...")
                enriched_interventions = self.speaker_classifier.classify_speakers(interventions)
                logger.info(f"✓ {len(enriched_interventions)} interventions classifiées")
                
                # Étape 3: Filtrer les parties intéressantes (sur les données enrichies)
                logger.info("Filtrage des parties intéressantes...")
                interesting_interventions = self.interesting_parts_agent._filter_interesting_parts(enriched_interventions)
                logger.info(f"✓ {len(interesting_interventions)} interventions intéressantes")
                
                # Étape 4: FILTRER les interviewers (ne garder que les interviewés)
                interviewee_interventions = [
                    interv for interv in interesting_interventions
                    if interv.get("speaker_type") == "interviewé"
                ]
                logger.info(f"✓ {len(interviewee_interventions)} interventions d'interviewés (interviewers filtrés)")
                
                all_interventions.extend(interviewee_interventions)
            
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
        """Synthétise les atouts de l'entreprise"""
        citations_dict = state.get("citations_atouts", {"citations": []})
        company_info = state.get("company_info", {})
        
        try:
            # Reconstruire l'objet CitationsAtoutsResponse
            from models.atouts_models import CitationsAtoutsResponse
            citations_response = CitationsAtoutsResponse(**citations_dict)
            
            atouts_response = self.atouts_agent.synthesize_atouts(
                citations_response,
                company_info
            )
            
            # Convertir en dict pour le state
            state["atouts"] = atouts_response.model_dump()
            logger.info(f"Synthétisé {len(atouts_response.atouts)} atouts")
            return state
            
        except Exception as e:
            logger.error(f"Erreur lors de la synthèse des atouts: {e}")
            state["success"] = False
            state["error"] = str(e)
            state["atouts"] = {"atouts": []}
            return state
    
    def _format_output_node(self, state: AtoutsState) -> AtoutsState:
        """Formate la sortie en markdown"""
        atouts_dict = state.get("atouts", {"atouts": []})
        company_info = state.get("company_info", {})
        
        try:
            company_name = company_info.get("nom", "l'entreprise")
            atouts_list = atouts_dict.get("atouts", [])
            
            if not atouts_list:
                state["atouts_markdown"] = f"# Les atouts de {company_name}\n\nAucun atout identifié."
                state["success"] = True
                return state
            
            # Construire le markdown
            markdown_parts = [f"# Les atouts de {company_name}\n"]
            
            for atout in atouts_list:
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
    
    def run(
        self,
        pdf_paths: List[str],
        company_info: Dict[str, Any],
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exécute le workflow d'extraction des atouts
        
        Args:
            pdf_paths: Liste des chemins vers les PDFs de transcription
            company_info: Informations sur l'entreprise depuis web search
            thread_id: ID du thread pour la persistance (optionnel)
            
        Returns:
            État final du workflow avec les atouts extraits
        """
        initial_state: AtoutsState = {
            "pdf_paths": pdf_paths,
            "company_info": company_info
        }
        
        config = {"configurable": {"thread_id": thread_id}} if thread_id else None
        final_state = self.graph.invoke(initial_state, config=config) if config else self.graph.invoke(initial_state)
        
        return dict(final_state)

