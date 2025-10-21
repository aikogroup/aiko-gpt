"""
Routes HTTP API

FR: Endpoints pour interagir avec le frontend
⚠️ Pas de logique métier - seulement des appels à LangGraph
"""

# TODO (FR): Importer les dépendances
# - Framework HTTP (FastAPI recommandé)
# - LangGraph graph instance
# - Modèles de validation (Pydantic)

# TODO (FR): Route POST /api/upload
# - Recevoir fichiers Excel, PDF, JSON
# - Valider les formats (.xlsx, .pdf, .json)
# - Stocker temporairement les fichiers
# - Retourner les IDs des fichiers uploadés
# ⚠️ Pas de parsing ici - c'est le rôle des agents

# TODO (FR): Route POST /api/run
# - Recevoir action + paramètres (files_ids, company_name, etc.)
# - Actions possibles :
#   * "generate_needs" : Génération initiale des besoins
#   * "regenerate_needs" : Régénération avec exclusions
#   * "generate_use_cases" : Génération cas d'usage
#   * "regenerate_use_cases" : Régénération cas d'usage
# - Déclencher l'exécution du graphe LangGraph
# - Retourner les résultats (needs, use_cases, etc.)

# TODO (FR): Route GET /api/report
# - Recevoir IDs des besoins et cas d'usage validés
# - Déclencher ReportAgent via LangGraph
# - Retourner le fichier .docx en téléchargement

