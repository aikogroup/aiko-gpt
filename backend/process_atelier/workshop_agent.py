"""
WorkshopAgent - Agent LangGraph pour analyse fichier Excel

FR: Parse et analyse les fichiers Excel contenant les données d'ateliers
"""

# TODO (FR): Importer les dépendances
# - LangGraph SDK (définition agent)
# - pandas ou openpyxl pour parsing Excel
# - OpenAI pour analyse LLM
# - Prompts depuis prompts/workshop_agent_prompts.py
# - Modèles Pydantic pour typage

# TODO (FR): Créer la classe WorkshopAgent
# - Hériter de la classe Agent de LangGraph
# - Définir les input/output (Pydantic models)

# TODO (FR): Méthode parse_excel_file()
# - Lire le fichier Excel
# - Extraire les 3 colonnes :
#   * Colonne A : Nom de l'atelier
#   * Colonne B : Cas d'usage
#   * Colonne C : Objectif ou gain
# - Structurer les données en dictionnaire
# - Gérer les erreurs (fichier manquant, format invalide, colonnes vides)

# Références code existant :
# - OLD/process_atelier/workshop_agent.py lignes 56-94 (parsing)
# - OLD/process_atelier/workshop_agent.py lignes 134-181 (analyse LLM)

# TODO (FR): Méthode analyze_with_llm()
# - Utiliser les prompts depuis prompts/workshop_agent_prompts.py
# - Envoyer les données parsées à OpenAI
# - Extraire et structurer les cas d'usage initiaux
# - Retourner workshop_data (dict)

# TODO (FR): Méthode run() (point d'entrée LangGraph)
# - Recevoir le chemin du fichier Excel
# - Appeler parse_excel_file()
# - Appeler analyze_with_llm()
# - Retourner workshop_data pour le prochain agent
# - Logger chaque étape

