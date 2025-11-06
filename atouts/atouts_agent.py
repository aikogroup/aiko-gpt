"""
Agent chargé d'identifier les atouts d'une entreprise et les opportunités IA associées.
"""

import json
import os
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

from prompts.atouts_prompts import ATOUTS_SYSTEM_PROMPT, ATOUTS_USER_PROMPT

# Token tracker (optionnel)
import sys
sys.path.append('/home/addeche/aiko/aikoGPT')
from utils.token_tracker import TokenTracker


load_dotenv()


class AtoutsAgent:
    """Agent qui fusionne les données internes et externes pour dégager les atouts clés."""

    def __init__(self, api_key: str, tracker: Optional[TokenTracker] = None) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY doit être fourni pour l'agent Atouts")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-nano")
        self.tracker = tracker

    @staticmethod
    def _safe_serialize(obj: Any) -> Any:
        """Convertit récursivement les objets complexes en structures sérialisables."""

        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        if isinstance(obj, dict):
            return {key: AtoutsAgent._safe_serialize(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [AtoutsAgent._safe_serialize(item) for item in obj]
        return obj

    def analyze_strengths(
        self,
        company_name: str,
        workshop_data: List[Dict[str, Any]],
        transcript_data: List[Dict[str, Any]],
        web_search_data: Dict[str, Any],
        additional_context: str = ""
    ) -> Dict[str, Any]:
        """Génère la liste des atouts et les opportunités IA associées."""

        company_display = company_name.strip() or "Entreprise"

        try:
            workshop_serialized = json.dumps(
                self._safe_serialize(workshop_data), ensure_ascii=False, indent=2
            ) or "Aucune donnée atelier disponible."

            transcript_serialized = json.dumps(
                self._safe_serialize(transcript_data), ensure_ascii=False, indent=2
            ) or "Aucune donnée transcript disponible."

            web_serialized = json.dumps(
                self._safe_serialize(web_search_data), ensure_ascii=False, indent=2
            ) or "Aucune donnée web disponible."

            additional_context = additional_context.strip() or "Aucune information supplémentaire fournie."

            user_prompt = ATOUTS_USER_PROMPT.format(
                company_name=company_display,
                company_overview=web_serialized,
                workshop_summary=workshop_serialized,
                transcript_quotes=transcript_serialized,
                web_context=web_serialized,
                additional_context=additional_context,
            )

            response = self.client.responses.create(
                model=self.model,
                instructions=ATOUTS_SYSTEM_PROMPT,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": user_prompt,
                            }
                        ],
                    }
                ],
            )

            if self.tracker:
                self.tracker.track_response(
                    response,
                    agent_name="atouts",
                    operation="atouts_analysis",
                    model=self.model,
                )

            if hasattr(response, "output_text") and response.output_text:
                output_text = response.output_text.strip()
            else:
                output_text = self._extract_text(response).strip()
            
            return {
                "success": True,
                "company_name": company_display,
                "text": output_text,
            }

        except Exception as error:  # pragma: no cover - gestion runtime
            return {
                "success": False,
                "error": f"Erreur lors de l'analyse des atouts: {error}",
                "company_name": company_display,
                "text": "",
            }

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Extrait le texte d'une réponse Responses API."""

        try:
            output = getattr(response, "output", None)
            if not output:
                return ""

            texts: List[str] = []
            for item in output:
                contents = getattr(item, "content", [])
                for content in contents:
                    if getattr(content, "type", "") == "output_text":
                        text_value = getattr(content, "text", "")
                        if text_value:
                            texts.append(text_value)

            return "\n".join(texts)

        except Exception:
            return ""


