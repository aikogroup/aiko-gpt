#!/usr/bin/env python
"""
Script pour démarrer l'API LangGraph
"""

import sys
import os
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Définir PYTHONPATH pour les subprocess d'uvicorn
os.environ['PYTHONPATH'] = parent_dir + os.pathsep + os.environ.get('PYTHONPATH', '')

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Démarrage de l'API LangGraph aiko...")
    print("📍 URL: http://localhost:2025")
    print("📖 Documentation: http://localhost:2025/docs")
    print("ℹ️  LangGraph Studio utilise le port 2024")
    print("🛑 Ctrl+C pour arrêter")
    print()
    
    # Utiliser une string pour activer le reload
    uvicorn.run(
        "api.langgraph_api:app",
        host="0.0.0.0",
        port=2025,
        reload=True,  # Auto-reload en développement
        log_level="info",
        reload_dirs=[parent_dir]  # Spécifier le répertoire à surveiller
    )

