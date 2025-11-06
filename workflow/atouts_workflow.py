"""
Workflow dédié à l'identification des atouts de l'entreprise.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from process_atelier.workshop_agent import WorkshopAgent
from process_transcript.transcript_agent import TranscriptAgent
from web_search.web_search_agent import WebSearchAgent

from atouts.atouts_agent import AtoutsAgent
from utils.token_tracker import TokenTracker


class AtoutsWorkflow:
    """Orchestre la collecte des données et l'analyse des atouts."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY doit être défini pour AtoutsWorkflow")

        self.api_key = api_key
        self.workshop_agent = WorkshopAgent(api_key)
        self.transcript_agent = TranscriptAgent(api_key)
        self.web_search_agent = WebSearchAgent()
        self.tracker = TokenTracker(output_dir="outputs/token_tracking")
        self.atouts_agent = AtoutsAgent(api_key, tracker=self.tracker)

    @staticmethod
    def _serialize_workshop_results(workshop_results: Optional[List[Any]]) -> List[Dict[str, Any]]:
        serialized: List[Dict[str, Any]] = []
        if not workshop_results:
            return serialized

        for item in workshop_results:
            if hasattr(item, "model_dump"):
                serialized.append(item.model_dump())
            elif isinstance(item, dict):
                serialized.append(item)
        return serialized

    @staticmethod
    def _serialize_transcript_results(transcript_results: Optional[Any]) -> List[Dict[str, Any]]:
        if not transcript_results:
            return []

        if isinstance(transcript_results, dict):
            entries = transcript_results.get("results", [])
        elif isinstance(transcript_results, list):
            entries = transcript_results
        else:
            entries = []

        serialized: List[Dict[str, Any]] = []
        for transcript in entries:
            if not isinstance(transcript, dict):
                continue

            semantic = transcript.get("semantic_analysis") or {}
            summary = transcript.get("summary") or {}
            interesting = transcript.get("interesting_parts", {}).get("interventions", [])

            quotes: List[str] = []
            for part in interesting[:5]:
                if isinstance(part, dict):
                    text = part.get("text") or part.get("content") or part.get("excerpt")
                    if text and isinstance(text, str):
                        quotes.append(text.strip())

            serialized.append(
                {
                    "file_path": transcript.get("file_path") or transcript.get("pdf_path"),
                    "semantic_analysis": semantic,
                    "summary": summary,
                    "quotes": quotes,
                }
            )

        return serialized

    def run(
        self,
        company_name: Optional[str] = None,
        workshop_files: Optional[List[str]] = None,
        transcript_files: Optional[List[str]] = None,
        workshop_results: Optional[List[Any]] = None,
        transcript_results: Optional[Any] = None,
        web_search_results: Optional[Dict[str, Any]] = None,
        additional_context: str = "",
    ) -> Dict[str, Any]:
        """Exécute le workflow complet et retourne les atouts."""

        workshop_files = workshop_files or []
        transcript_files = transcript_files or []

        collected_workshops: List[Any] = workshop_results or []
        collected_transcripts: Any = transcript_results or []
        web_results: Dict[str, Any] = web_search_results or {}

        errors: List[str] = []

        # 1. Traitement des ateliers si nécessaire
        if not collected_workshops and workshop_files:
            aggregated: List[Any] = []
            for file_path in workshop_files:
                try:
                    aggregated.extend(self.workshop_agent.process_workshop_file(file_path))
                except Exception as exc:  # pragma: no cover - dépend d'entrées utilisateur
                    errors.append(f"Erreur workshop ({file_path}): {exc}")
            collected_workshops = aggregated

        # 2. Traitement des transcripts si nécessaire
        if not collected_transcripts and transcript_files:
            try:
                collected_transcripts = self.transcript_agent.process_multiple_files(transcript_files)
            except Exception as exc:  # pragma: no cover
                errors.append(f"Erreur transcript: {exc}")
                collected_transcripts = []

        # 3. Recherche web si on a un nom d'entreprise
        company_display = (company_name or "").strip()
        if not web_results and company_display:
            try:
                web_results = self.web_search_agent.search_company_info(company_display)
            except Exception as exc:  # pragma: no cover
                errors.append(f"Erreur recherche web: {exc}")
                web_results = {}

        # 4. Préparation des données pour l'agent
        workshop_context = self._serialize_workshop_results(collected_workshops)
        transcript_context = self._serialize_transcript_results(collected_transcripts)

        # 5. Analyse des atouts
        analysis = self.atouts_agent.analyze_strengths(
            company_name=company_display,
            workshop_data=workshop_context,
            transcript_data=transcript_context,
            web_search_data=web_results,
            additional_context=additional_context,
        )

        success = analysis.get("success", False) and not errors

        result_payload = {
            "company_name": analysis.get("company_name", company_display or "Entreprise"),
            "text": analysis.get("text", ""),
            "workshop_context": workshop_context,
            "transcript_context": transcript_context,
            "web_search_results": web_results,
            "errors": analysis.get("error"),
        }

        warnings = analysis.get("warnings") or []
        if errors:
            warnings.extend(errors)
        if warnings:
            result_payload["warnings"] = warnings

        return {
            "success": success,
            "result": result_payload,
        }


