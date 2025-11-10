"""
Workflow LangGraph dédié au rappel de la mission.
"""

from typing import TypedDict, Dict, Any, Optional

from langgraph.graph import StateGraph, END

from web_search.web_search_agent import WebSearchAgent


class RappelMissionState(TypedDict, total=False):
    """État du workflow rappel de la mission."""

    company_name: str
    validated_company_info: Optional[Dict[str, Any]]
    web_search_results: Dict[str, Any]
    mission_markdown: str
    success: bool
    error: str


class RappelMissionWorkflow:
    """Workflow minimal pour générer le rappel de la mission."""

    def __init__(self) -> None:
        self.web_search_agent = WebSearchAgent()
        self.graph = self._create_graph()

    def _create_graph(self) -> StateGraph:
        workflow = StateGraph(RappelMissionState)

        workflow.add_node("web_search", self._web_search_node)
        workflow.add_node("format_output", self._format_output_node)

        workflow.set_entry_point("web_search")
        workflow.add_edge("web_search", "format_output")
        workflow.add_edge("format_output", END)

        return workflow.compile()

    def _web_search_node(self, state: RappelMissionState) -> RappelMissionState:
        # Si validated_company_info est fourni, l'utiliser directement
        validated_company_info = state.get("validated_company_info")
        if validated_company_info:
            # Utiliser directement les informations validées
            state["web_search_results"] = validated_company_info
            return state
        
        # Sinon, faire une recherche web comme avant
        company_name = (state.get("company_name") or "").strip()
        if not company_name:
            state["success"] = False
            state["error"] = "Aucun nom d'entreprise fourni"
            return state

        try:
            state["web_search_results"] = self.web_search_agent.search_company_info(company_name)
            return state
        except Exception as error:  # pragma: no cover - gestion d'erreur runtime
            state["success"] = False
            state["error"] = str(error)
            return state

    def _format_output_node(self, state: RappelMissionState) -> RappelMissionState:
        if not state.get("web_search_results"):
            state.setdefault("success", False)
            state.setdefault("mission_markdown", "")
            return state

        info = state["web_search_results"]
        # Utiliser "nom" au lieu de "company_name" car c'est la clé dans CompanyInfo
        company_name = (info.get("nom") or state.get("company_name") or "Entreprise").strip()

        description = (info.get("description") or "").strip()

        if not description:
            description = f"Informations sur {company_name} non disponibles."

        state["mission_markdown"] = description
        state["success"] = True
        return state

    def run(self, company_name: str, validated_company_info: Optional[Dict[str, Any]] = None, thread_id: Optional[str] = None) -> Dict[str, Any]:
        initial_state: RappelMissionState = {"company_name": company_name.strip()}
        if validated_company_info:
            initial_state["validated_company_info"] = validated_company_info

        config = {"configurable": {"thread_id": thread_id}} if thread_id else None
        final_state = self.graph.invoke(initial_state, config=config) if config else self.graph.invoke(initial_state)

        return dict(final_state)

