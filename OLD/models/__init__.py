"""
Modèles Pydantic pour structured outputs avec OpenAI Response API
"""

from .need_analysis_models import NeedAnalysisResponse, Need, NeedSummary
from .use_case_analysis_models import UseCaseAnalysisResponse, QuickWin, StructurationIA, UseCaseSummary
from .transcript_models import SemanticAnalysisResponse
from .web_search_models import CompanyInfo

__all__ = [
    "NeedAnalysisResponse",
    "Need",
    "NeedSummary",
    "UseCaseAnalysisResponse",
    "QuickWin",
    "StructurationIA",
    "UseCaseSummary",
    "SemanticAnalysisResponse",
    "CompanyInfo",
]

