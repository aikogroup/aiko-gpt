"""
Agent principal pour le traitement des transcriptions (PDF ou JSON)
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from .pdf_parser import PDFParser
from .json_parser import JSONParser
from .interesting_parts_agent import InterestingPartsAgent
from .semantic_filter_agent import SemanticFilterAgent
from .speaker_classifier import SpeakerClassifier

logger = logging.getLogger(__name__)

class TranscriptAgent:
    """Agent principal pour traiter les transcriptions (PDF ou JSON)"""
    
    def __init__(self, openai_api_key: str = None, interviewer_names: List[str] = None):
        self.pdf_parser = PDFParser()
        self.json_parser = JSONParser()
        self.interesting_parts_agent = InterestingPartsAgent(openai_api_key)
        self.semantic_filter_agent = SemanticFilterAgent(openai_api_key)
        self.speaker_classifier = SpeakerClassifier(openai_api_key, interviewer_names)
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def process_single_file(self, file_path: str) -> Dict[str, Any]:
        """
        Traite un seul fichier de transcription (PDF ou JSON) de manière optimisée
        
        Args:
            file_path: Chemin vers le fichier (PDF ou JSON)
            
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        logger.info(f"=== Début du traitement du fichier: {file_path} ===")
        
        try:
            # Détecter le type de fichier et parser en conséquence
            file_extension = Path(file_path).suffix.lower()
            
            # Étape 1: Parsing du fichier (UNE SEULE FOIS)
            if file_extension == '.json':
                logger.info("Étape 1: Parsing du fichier JSON")
                interventions = self.json_parser.parse_transcript(file_path)
                parser_used = self.json_parser
            elif file_extension == '.pdf':
                logger.info("Étape 1: Parsing du fichier PDF")
                interventions = self.pdf_parser.parse_transcript(file_path)
                parser_used = self.pdf_parser
            else:
                raise ValueError(f"Format de fichier non supporté: {file_extension}. Utilisez .pdf ou .json")
            
            logger.info(f"✓ {len(interventions)} interventions extraites")
            
            # Étape 1.5: Classification des speakers (interviewer/interviewé, direction/métier)
            logger.info("Étape 1.5: Classification des speakers")
            enriched_interventions = self.speaker_classifier.classify_speakers(interventions)
            logger.info(f"✓ {len(enriched_interventions)} interventions classifiées")
            
            # Étape 2: Filtrage des parties intéressantes (sur les données déjà parsées et classifiées)
            logger.info("Étape 2: Filtrage des parties intéressantes")
            interesting_interventions = self.interesting_parts_agent._filter_interesting_parts(enriched_interventions)
            logger.info(f"✓ {len(interesting_interventions)} interventions intéressantes identifiées")
            
            # Étape 3: Analyse sémantique (sur les données déjà filtrées)
            logger.info("Étape 3: Analyse sémantique avec GPT-5-nano")
            semantic_analysis = self.semantic_filter_agent._perform_semantic_analysis(
                self.semantic_filter_agent._prepare_text_for_analysis(interesting_interventions)
            )
            logger.info("✓ Analyse sémantique terminée")
            
            # Résultat final
            result = {
                "file_path": file_path,
                "file_type": file_extension,
                "status": "success",
                "parsing": {
                    "total_interventions": len(interventions),
                    "speakers": parser_used.get_speakers(interventions),
                    "interventions": enriched_interventions  # Garder les interventions enrichies avec métadonnées
                },
                "interesting_parts": {
                    "count": len(interesting_interventions),
                    "interventions": interesting_interventions
                },
                "semantic_analysis": semantic_analysis,
                "summary": self.semantic_filter_agent.get_summary({"semantic_analysis": semantic_analysis})
            }
            
            logger.info(f"=== Traitement terminé avec succès ===")
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier {file_path}: {e}")
            return {
                "file_path": file_path,
                "status": "error",
                "error": str(e)
            }
    
    def process_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Traite un seul PDF de transcription de manière optimisée
        
        [DEPRECATED] Utilisez process_single_file() à la place
        Cette méthode est conservée pour la rétrocompatibilité
        """
        logger.warning("process_single_pdf() est déprécié, utilisez process_single_file() à la place")
        return self.process_single_file(pdf_path)
    
    def process_multiple_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Traite plusieurs fichiers de transcriptions (PDF ou JSON)
        """
        logger.info(f"=== Début du traitement de {len(file_paths)} fichiers ===")
        
        results = []
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            result = self.process_single_file(file_path)
            results.append(result)
            
            if result["status"] == "success":
                successful += 1
            else:
                failed += 1
        
        # Résumé global
        summary = {
            "total_files": len(file_paths),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
        logger.info(f"=== Traitement terminé: {successful} succès, {failed} échecs ===")
        return summary
    
    def process_multiple_pdfs(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """
        Traite plusieurs PDFs de transcriptions
        
        [DEPRECATED] Utilisez process_multiple_files() à la place
        Cette méthode est conservée pour la rétrocompatibilité
        """
        logger.warning("process_multiple_pdfs() est déprécié, utilisez process_multiple_files() à la place")
        return self.process_multiple_files(pdf_paths)
    
    def process_directory(self, directory_path: str, file_types: List[str] = None) -> Dict[str, Any]:
        """
        Traite tous les fichiers de transcription d'un répertoire
        
        Args:
            directory_path: Chemin du répertoire
            file_types: Liste des extensions à traiter (ex: ['.pdf', '.json'])
                       Par défaut: ['.pdf', '.json']
        """
        if file_types is None:
            file_types = ['.pdf', '.json']
        
        directory = Path(directory_path)
        
        # Collecter tous les fichiers des types spécifiés
        all_files = []
        for file_type in file_types:
            files = list(directory.glob(f"*{file_type}"))
            all_files.extend(files)
        
        if not all_files:
            logger.warning(f"Aucun fichier de transcription trouvé dans {directory_path}")
            return {
                "status": "no_files",
                "directory": directory_path,
                "files": []
            }
        
        file_paths = [str(file) for file in all_files]
        logger.info(f"Traitement de {len(file_paths)} fichiers du répertoire {directory_path}")
        
        return self.process_multiple_files(file_paths)
    
    def get_consolidated_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Consolide les analyses de plusieurs PDFs
        """
        logger.info("Consolidation des analyses")
        
        all_needs = []
        all_frustrations = []
        all_opportunities = []
        all_citations = []
        
        for result in results:
            if result["status"] == "success":
                analysis = result.get("semantic_analysis", {})
                
                all_needs.extend(analysis.get("besoins_exprimes", []))
                all_frustrations.extend(analysis.get("frustrations_blocages", []))
                all_opportunities.extend(analysis.get("opportunites_automatisation", []))
                all_citations.extend(analysis.get("citations_cles", []))
        
        # Déduplication
        consolidated = {
            "besoins_exprimes": list(set(all_needs)),
            "frustrations_blocages": list(set(all_frustrations)),
            "opportunites_automatisation": list(set(all_opportunities)),
            "citations_cles": list(set(all_citations)),
            "statistics": {
                "total_needs": len(set(all_needs)),
                "total_frustrations": len(set(all_frustrations)),
                "total_opportunities": len(set(all_opportunities)),
                "total_citations": len(set(all_citations))
            }
        }
        
        # Compter les citations par niveau de speaker (si métadonnées disponibles)
        citations_direction = 0
        citations_metier = 0
        citations_interviewer_confirmees = 0
        
        for result in results:
            if result["status"] == "success":
                # Analyser les interventions pour compter par niveau
                parsing_data = result.get("parsing", {})
                interventions_data = parsing_data.get("interventions", [])
                
                for intervention in interventions_data:
                    speaker_level = intervention.get("speaker_level")
                    speaker_type = intervention.get("speaker_type")
                    
                    # Pour les citations, on compte si l'intervention est dans les parties intéressantes
                    interesting_interventions = result.get("interesting_parts", {}).get("interventions", [])
                    if any(
                        intv.get("speaker") == intervention.get("speaker") and
                        intv.get("text") == intervention.get("text")
                        for intv in interesting_interventions
                    ):
                        if speaker_level == "direction":
                            citations_direction += 1
                        elif speaker_level == "métier":
                            citations_metier += 1
                        
                        # Détection approximative des citations interviewer confirmées
                        # (basée sur la présence d'une citation de l'interviewer suivie d'une confirmation)
                        if speaker_type == "interviewer":
                            # Vérifier les interventions suivantes pour une confirmation
                            idx = interventions_data.index(intervention) if intervention in interventions_data else -1
                            if idx >= 0 and idx + 1 < len(interventions_data):
                                next_intervention = interventions_data[idx + 1]
                                if next_intervention.get("speaker_type") == "interviewé":
                                    text_lower = next_intervention.get("text", "").lower()
                                    confirmations = ["tout à fait", "exactement", "oui", "c'est ça", "absolument", "effectivement"]
                                    if any(conf in text_lower for conf in confirmations):
                                        citations_interviewer_confirmees += 1
        
        consolidated["statistics"]["citations_direction"] = citations_direction
        consolidated["statistics"]["citations_metier"] = citations_metier
        consolidated["statistics"]["citations_interviewer_confirmees"] = citations_interviewer_confirmees
        
        logger.info(f"Analyse consolidée: {consolidated['statistics']}")
        return consolidated
