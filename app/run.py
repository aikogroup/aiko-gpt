"""
Script de lancement de l'application Streamlit
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Lance l'application Streamlit"""
    
    # Chemin vers l'application
    app_path = Path(__file__).parent / "app.py"
    
    # Commande pour lancer Streamlit avec uv
    cmd = [
        "uv", "run", "streamlit", "run", 
        str(app_path),
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ]
    
    print("🚀 Lancement de l'application AIKO...")
    print(f"📱 Interface disponible sur: http://localhost:8501")
    print("🛑 Appuyez sur Ctrl+C pour arrêter l'application")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n👋 Application arrêtée")
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
