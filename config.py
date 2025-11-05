"""
Configuration centralisée du projet aikoGPT.
Détecte automatiquement le répertoire de base du projet, fonctionne en local et en conteneur.
"""

import os
from pathlib import Path
from typing import Optional


def get_project_root() -> Path:
    """
    Retourne le répertoire racine du projet.
    
    Détection automatique :
    1. Vérifie la variable d'environnement BASE_DIR (pour conteneurs)
    2. Sinon, remonte depuis ce fichier jusqu'à trouver la racine du projet
       (identifiée par la présence de pyproject.toml)
    
    Returns:
        Path: Chemin vers la racine du projet
    """
    # 1. Vérifier la variable d'environnement (priorité pour conteneurs)
    base_dir = os.getenv("BASE_DIR")
    if base_dir:
        return Path(base_dir).resolve()
    
    # 2. Détection automatique depuis ce fichier (config.py à la racine)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent
    
    # Vérifier que c'est bien la racine (présence de pyproject.toml)
    if (project_root / "pyproject.toml").exists():
        return project_root
    
    # Fallback : si on est dans un conteneur et que pyproject.toml n'est pas trouvé,
    # on utilise /app comme fallback
    if str(project_root).startswith("/app"):
        return Path("/app")
    
    return project_root


# Chemins de base (détectés automatiquement)
PROJECT_ROOT = get_project_root()
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
ASSETS_DIR = PROJECT_ROOT / "assets"
CONFIG_DIR = PROJECT_ROOT / "config"


def ensure_outputs_dir() -> Path:
    """
    Crée le répertoire outputs/ s'il n'existe pas et le retourne.
    
    Returns:
        Path: Chemin vers le dossier outputs/
    """
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUTS_DIR


def get_logo_path() -> Path:
    """
    Retourne le chemin vers le logo Aiko.
    
    Returns:
        Path: Chemin vers assets/aiko_logo.png
    """
    return ASSETS_DIR / "aiko_logo.png"

