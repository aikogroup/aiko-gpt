"""
Web Search Agent pour la collecte d'informations contextuelles sur les entreprises.
"""

# Import direct pour éviter les problèmes de module
try:
    from .web_search_agent import WebSearchAgent
    __all__ = ["WebSearchAgent"]
except ImportError:
    # Fallback si l'import échoue
    __all__ = []
