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

logger = logging.getLogger(__name__)

class TranscriptAgent:
    """Agent principal pour traiter les transcriptions (PDF ou JSON)"""
    
    def __init__(self, openai_api_key: str = None):
        self.pdf_parser = PDFParser()
        self.json_parser = JSONParser()
        self.interesting_parts_agent = InterestingPartsAgent(openai_api_key)
        self.semantic_filter_agent = SemanticFilterAgent(openai_api_key)
        
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
            
            # Étape 2: Filtrage des parties intéressantes (sur les données déjà parsées)
            logger.info("Étape 2: Filtrage des parties intéressantes")
            interesting_interventions = self.interesting_parts_agent._filter_interesting_parts(interventions)
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
                    "interventions": interventions  # Garder les interventions originales
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
        
        logger.info(f"Analyse consolidée: {consolidated['statistics']}")
        return consolidated
