"""
Agent principal pour le traitement des transcriptions (PDF ou JSON)
"""
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    
    def process_from_db(
        self,
        document_id: int,
        validated_speakers: Optional[List[Dict[str, str]]] = None,
        filter_interviewers: bool = True
    ) -> Dict[str, Any]:
        """
        Traite un transcript depuis la base de données.
        
        Les interventions sont déjà enrichies avec speaker_type, role, level depuis la DB.
        Plus besoin de classification LLM.
        
        Args:
            document_id: ID du document dans la table documents
            validated_speakers: Liste optionnelle des speakers validés par l'utilisateur
                              Format: [{"name": "...", "role": "..."}, ...]
            filter_interviewers: Si True, exclut les interventions des interviewers (défaut: True)
            
        Returns:
            Dictionnaire contenant les résultats de l'analyse
        """
        logger.info(f"=== Début du traitement depuis la BDD pour document_id={document_id} ===")
        
        try:
            from database.db import get_db_context
            from database.repository import TranscriptRepository
            
            # Charger les interventions enrichies depuis la BDD
            with get_db_context() as db:
                enriched_interventions = TranscriptRepository.get_enriched_by_document(
                    db, document_id, filter_interviewers=filter_interviewers
                )
            
            if not enriched_interventions:
                logger.warning(f"Aucune intervention trouvée pour document_id={document_id}")
                return {
                    "document_id": document_id,
                    "status": "error",
                    "error": "Aucune intervention trouvée"
                }
            
            logger.info(f"✓ {len(enriched_interventions)} interventions enrichies chargées depuis la BDD")
            
            # Adapter le format pour compatibilité avec les agents
            # Convertir speaker_level en speaker_level (même nom, mais s'assurer qu'il est présent)
            formatted_interventions = []
            for interv in enriched_interventions:
                formatted_interv = {
                    "speaker": interv.get("speaker_name") or interv.get("speaker"),  # Utiliser nom validé si disponible
                    "timestamp": interv.get("timestamp"),
                    "text": interv.get("text"),
                    "speaker_type": interv.get("speaker_type"),
                    "speaker_level": interv.get("speaker_level"),  # Déjà présent depuis speakers
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
            
            # Plus besoin de classify_speakers() - les données sont déjà enrichies !
            
            # Étape 2: Filtrage des parties intéressantes
            logger.info("Étape 2: Filtrage des parties intéressantes")
            interesting_interventions = self.interesting_parts_agent._filter_interesting_parts(formatted_interventions)
            logger.info(f"✓ {len(interesting_interventions)} interventions intéressantes identifiées")
            
            # Étape 3: Analyse sémantique
            logger.info("Étape 3: Analyse sémantique avec GPT-5-nano")
            semantic_analysis = self.semantic_filter_agent._perform_semantic_analysis(
                self.semantic_filter_agent._prepare_text_for_analysis(interesting_interventions)
            )
            logger.info("✓ Analyse sémantique terminée")
            
            # Extraire les speakers uniques
            speakers = list(set(
                interv.get("speaker") 
                for interv in formatted_interventions 
                if interv.get("speaker")
            ))
            
            # Résultat final
            result = {
                "document_id": document_id,
                "status": "success",
                "parsing": {
                    "total_interventions": len(formatted_interventions),
                    "speakers": speakers,
                    "interventions": formatted_interventions  # Déjà enrichies !
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
            logger.error(f"Erreur lors du traitement depuis la BDD document_id={document_id}: {e}")
            return {
                "document_id": document_id,
                "status": "error",
                "error": str(e)
            }
    
    def process_single_file(self, file_path: str, validated_speakers: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Traite un seul fichier de transcription (PDF ou JSON) de manière optimisée
        
        Args:
            file_path: Chemin vers le fichier (PDF ou JSON)
            validated_speakers: Liste optionnelle des speakers validés par l'utilisateur
                              Format: [{"name": "...", "role": "..."}, ...]
            
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
            
            # Filtrer UNIQUEMENT les speakers validés par l'utilisateur
            if validated_speakers:
                validated_names = {s["name"] for s in validated_speakers}
                logger.info(f"🔍 Filtrage sur {len(validated_names)} speakers validés")
                
                interventions = [
                    interv for interv in interventions
                    if interv.get("speaker") in validated_names
                ]
                
                logger.info(f"✓ {len(interventions)} interventions après filtrage des speakers validés")
            
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
    
    def get_interesting_parts_only(self, file_path: str, validated_speakers: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Traite un fichier de transcription et retourne uniquement les parties intéressantes
        SANS effectuer l'analyse sémantique (plus rapide et moins coûteux).
        
        Cette méthode est optimisée pour les cas où on a besoin seulement des interventions
        intéressantes, comme pour l'extraction de citations spécifiques (enjeux, maturité, etc.)
        
        Args:
            file_path: Chemin vers le fichier (PDF ou JSON)
            validated_speakers: Liste optionnelle des speakers validés par l'utilisateur
                              Format: [{"name": "...", "role": "..."}, ...]
            
        Returns:
            Dictionnaire contenant uniquement les parties intéressantes avec métadonnées
        """
        logger.info(f"=== Début du traitement (sans analyse sémantique): {file_path} ===")
        
        try:
            # Détecter le type de fichier et parser en conséquence
            file_extension = Path(file_path).suffix.lower()
            
            # Étape 1: Parsing du fichier
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
            
            # Filtrer UNIQUEMENT les speakers validés par l'utilisateur
            if validated_speakers:
                validated_names = {s["name"] for s in validated_speakers}
                logger.info(f"🔍 Filtrage sur {len(validated_names)} speakers validés")
                
                interventions = [
                    interv for interv in interventions
                    if interv.get("speaker") in validated_names
                ]
                
                logger.info(f"✓ {len(interventions)} interventions après filtrage des speakers validés")
            
            # Étape 1.5: Classification des speakers (interviewer/interviewé, direction/métier)
            logger.info("Étape 1.5: Classification des speakers")
            enriched_interventions = self.speaker_classifier.classify_speakers(interventions)
            logger.info(f"✓ {len(enriched_interventions)} interventions classifiées")
            
            # Étape 2: Filtrage des parties intéressantes (sur les données déjà parsées et classifiées)
            logger.info("Étape 2: Filtrage des parties intéressantes")
            interesting_interventions = self.interesting_parts_agent._filter_interesting_parts(enriched_interventions)
            logger.info(f"✓ {len(interesting_interventions)} interventions intéressantes identifiées")
            
            # Résultat final (SANS analyse sémantique)
            result = {
                "file_path": file_path,
                "file_type": file_extension,
                "status": "success",
                "parsing": {
                    "total_interventions": len(interventions),
                    "speakers": parser_used.get_speakers(interventions),
                    "interventions": enriched_interventions
                },
                "interesting_parts": {
                    "count": len(interesting_interventions),
                    "interventions": interesting_interventions
                }
            }
            
            logger.info(f"=== Traitement terminé avec succès (sans analyse sémantique) ===")
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
        PARALLÉLISÉ : Traite tous les fichiers en parallèle pour gagner du temps
        """
        logger.info(f"=== Début du traitement de {len(file_paths)} fichiers (PARALLÉLISÉ) ===")
        
        results = []
        successful = 0
        failed = 0
        
        # 🚀 PARALLÉLISATION : Traiter tous les fichiers en même temps
        # Limiter le nombre de workers pour éviter de surcharger le système
        # Avec beaucoup de fichiers, on limite à un nombre raisonnable de threads
        max_workers = min(len(file_paths), 10)  # Maximum 10 threads en parallèle
        logger.info(f"Parallélisation avec {max_workers} workers pour {len(file_paths)} fichiers")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre tous les fichiers pour traitement parallèle
            future_to_file = {}
            for file_path in file_paths:
                future = executor.submit(self.process_single_file, file_path)
                future_to_file[future] = file_path
            
            # Récupérer les résultats au fur et à mesure
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result["status"] == "success":
                        successful += 1
                    else:
                        failed += 1
                    
                    logger.info(f"✓ Fichier '{file_path}' terminé: {result['status']}")
                except Exception as e:
                    logger.error(f"❌ Erreur lors du traitement de '{file_path}': {e}")
                    failed += 1
                    results.append({
                        "file_path": file_path,
                        "status": "error",
                        "error": str(e)
                    })
        
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
        
        # Fonction helper pour dédupliquer par texte (compatible avec strings et dicts)
        def deduplicate_by_text(items):
            seen_texts = set()
            unique_items = []
            for item in items:
                # Extraire le texte : soit directement si string, soit depuis le champ "text" si dict
                text = item if isinstance(item, str) else item.get("text", str(item))
                if text not in seen_texts:
                    seen_texts.add(text)
                    unique_items.append(item)
            return unique_items
        
        # Déduplication par texte
        consolidated = {
            "besoins_exprimes": deduplicate_by_text(all_needs),
            "frustrations_blocages": deduplicate_by_text(all_frustrations),
            "opportunites_automatisation": deduplicate_by_text(all_opportunities),
            "citations_cles": deduplicate_by_text(all_citations),
            "statistics": {
                "total_needs": len(deduplicate_by_text(all_needs)),
                "total_frustrations": len(deduplicate_by_text(all_frustrations)),
                "total_opportunities": len(deduplicate_by_text(all_opportunities)),
                "total_citations": len(deduplicate_by_text(all_citations))
            }
        }
        
        # Compter les citations par niveau de speaker (si métadonnées disponibles)
        citations_direction = 0
        citations_metier = 0
        citations_interviewer_confirmees = 0
        
        # Compter depuis les citations consolidées (qui ont maintenant les métadonnées)
        for citation in consolidated["citations_cles"]:
            if isinstance(citation, dict):
                speaker_level = citation.get("speaker_level")
                speaker_type = citation.get("speaker_type")
                
                if speaker_level == "direction":
                    citations_direction += 1
                elif speaker_level == "métier":
                    citations_metier += 1
                
                # Les citations d'interviewer confirmées sont déjà incluses dans citations_cles
                # avec speaker_type="interviewer" (car confirmées par l'interviewé)
                if speaker_type == "interviewer":
                    citations_interviewer_confirmees += 1
        
        # Compter aussi depuis les besoins et frustrations
        for besoin in consolidated["besoins_exprimes"]:
            if isinstance(besoin, dict):
                speaker_level = besoin.get("speaker_level")
                if speaker_level == "direction":
                    citations_direction += 1
                elif speaker_level == "métier":
                    citations_metier += 1
        
        for frustration in consolidated["frustrations_blocages"]:
            if isinstance(frustration, dict):
                speaker_level = frustration.get("speaker_level")
                if speaker_level == "direction":
                    citations_direction += 1
                elif speaker_level == "métier":
                    citations_metier += 1
        
        consolidated["statistics"]["citations_direction"] = citations_direction
        consolidated["statistics"]["citations_metier"] = citations_metier
        consolidated["statistics"]["citations_interviewer_confirmees"] = citations_interviewer_confirmees
        
        logger.info(f"Analyse consolidée: {consolidated['statistics']}")
        logger.info(f"Analyse entière: {consolidated}")
        return consolidated
