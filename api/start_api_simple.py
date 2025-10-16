#!/usr/bin/env python
"""
Script SIMPLE pour démarrer l'API LangGraph (sans reload)
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
parent_dir = str(Path(__file__).parent.parent)
sys.path.insert(0, parent_dir)

if __name__ == "__main__":
    import uvicorn
    from api.langgraph_api import app
    
    print("🚀 Démarrage de l'API LangGraph AIKO (mode simple)...")
    print("📍 URL: http://localhost:2025")
    print("📖 Documentation: http://localhost:2025/docs")
    print("ℹ️  LangGraph Studio utilise le port 2024")
    print("🛑 Ctrl+C pour arrêter")
    print()
    
    # Lancer sans reload
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=2025,
        log_level="info"
    )

