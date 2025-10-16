#!/usr/bin/env python
"""
Script pour lancer l'application Streamlit avec l'architecture API
"""

import subprocess
import sys

if __name__ == "__main__":
    print("🚀 Lancement de l'application AIKO (Architecture API)...")
    print("📱 Interface disponible sur: http://localhost:8501")
    print("🛑 Appuyez sur Ctrl+C pour arrêter l'application")
    print()
    print("⚠️  IMPORTANT : L'API LangGraph doit être lancée en parallèle !")
    print("   Lancez dans un autre terminal : uv run python api/start_api.py")
    print()
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "app/app_api.py",
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ])

