"""
Backend principal - Configuration et logging

FR: Configuration de base pour le backend LangGraph
⚠️ NOTE: LangGraph Server gère les APIs HTTP automatiquement
         Ce fichier n'est plus un point d'entrée principal
"""

import os
import logging
from dotenv import load_dotenv

# FR: Charger les variables d'environnement
load_dotenv()

# FR: Configuration du logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logger.info("✅ Configuration backend chargée")
logger.info(f"📊 Environnement: {os.getenv('ENVIRONMENT', 'development')}")
logger.info(f"🔑 OpenAI Model: {os.getenv('OPENAI_MODEL', 'gpt-4o-mini-2024-07-18')}")
logger.info(f"🔍 Perplexity API: {'Configuré' if os.getenv('PERPLEXITY_API_KEY') else 'Non configuré'}")

# FR: Le graphe LangGraph est défini dans graph_factory.py
# FR: Pour lancer le serveur, utilisez : langgraph dev
# FR: Ou pour Docker : langgraph up

