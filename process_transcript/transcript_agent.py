"""
Agent principal pour le traitement des transcriptions PDF
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from .pdf_parser import PDFParser
from .interesting_parts_agent import InterestingPartsAgent
from .semantic_filter_agent import SemanticFilterAgent

logger = logging.getLogger(__name__)

class TranscriptAgent:
    """Agent principal pour traiter les transcriptions PDF"""
    
    def __init__(self, openai_api_key: str = None):
        self.pdf_parser = PDFParser()
        self.interesting_parts_agent = InterestingPartsAgent(openai_api_key)
        self.semantic_filter_agent = SemanticFilterAgent(openai_api_key)
        
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def process_single_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Traite un seul PDF de transcription de manière optimisée
        """
        logger.info(f"=== Début du traitement du PDF: {pdf_path} ===")
        
        try:
            # Étape 1: Parsing du PDF (UNE SEULE FOIS)
            logger.info("Étape 1: Parsing du PDF")
            interventions = self.pdf_parser.parse_transcript(pdf_path)
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
                "pdf_path": pdf_path,
                "status": "success",
                "parsing": {
                    "total_interventions": len(interventions),
                    "speakers": self.pdf_parser.get_speakers(interventions),
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
            logger.error(f"Erreur lors du traitement du PDF {pdf_path}: {e}")
            return {
                "pdf_path": pdf_path,
                "status": "error",
                "error": str(e)
            }
    
    def process_multiple_pdfs(self, pdf_paths: List[str]) -> Dict[str, Any]:
        """
        Traite plusieurs PDFs de transcriptions
        """
        logger.info(f"=== Début du traitement de {len(pdf_paths)} PDFs ===")
        
        results = []
        successful = 0
        failed = 0
        
        for pdf_path in pdf_paths:
            result = self.process_single_pdf(pdf_path)
            results.append(result)
            
            if result["status"] == "success":
                successful += 1
            else:
                failed += 1
        
        # Résumé global
        summary = {
            "total_pdfs": len(pdf_paths),
            "successful": successful,
            "failed": failed,
            "results": results
        }
        
        logger.info(f"=== Traitement terminé: {successful} succès, {failed} échecs ===")
        return summary
    
    def process_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        Traite tous les PDFs d'un répertoire
        """
        directory = Path(directory_path)
        pdf_files = list(directory.glob("*.pdf"))
        
        if not pdf_files:
            logger.warning(f"Aucun fichier PDF trouvé dans {directory_path}")
            return {
                "status": "no_files",
                "directory": directory_path,
                "pdf_files": []
            }
        
        pdf_paths = [str(pdf_file) for pdf_file in pdf_files]
        logger.info(f"Traitement de {len(pdf_paths)} PDFs du répertoire {directory_path}")
        
        return self.process_multiple_pdfs(pdf_paths)
    
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
