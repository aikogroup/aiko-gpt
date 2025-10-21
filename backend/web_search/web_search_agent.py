"""
WebSearchAgent - Recherche contextuelle via Perplexity

FR: Agent LangGraph pour récupérer le contexte entreprise
⚠️ ATTENTION : Fournit uniquement le CONTEXTE, ne génère JAMAIS de besoins
"""

# TODO (FR): Importer les dépendances
# - LangGraph SDK
# - Perplexity API client
# - OpenAI API (pour contexte additionnel)
# - Prompts depuis prompts/web_search_agent_prompts.py
# - Modèles Pydantic

# Références code existant :
# - OLD/web_search/web_search_agent.py
# - Lignes 69-75 : Recherche Perplexity
# - Lignes 121-137 : Contexte additionnel OpenAI

# TODO (FR): Créer la classe WebSearchAgent
# - Hériter de la classe Agent de LangGraph
# - Définir les input/output (company_name → web_search_data)
# - Initialiser clients Perplexity et OpenAI

# TODO (FR): Méthode search_with_perplexity(company_name: str) -> dict
# - Effectuer la recherche sur Perplexity
# - Récupérer :
#   * Secteur d'activité
#   * Taille de l'entreprise (nb employés, CA)
#   * Actualités récentes
#   * Localisation
# - Gérer les erreurs API
# - Retourner dict structuré

# TODO (FR): Méthode enrich_with_openai(perplexity_data: dict) -> dict
# - Utiliser OpenAI pour enrichir le contexte
# - Synthétiser les informations
# - Ajouter du contexte métier si pertinent
# - Retourner le contexte enrichi

# TODO (FR): Méthode run() (point d'entrée LangGraph)
# - Recevoir company_name
# - Appeler search_with_perplexity()
# - Appeler enrich_with_openai()
# - Retourner web_search_data pour NeedAnalysisAgent
# - ⚠️ Logger clairement : "Contexte uniquement, pas de génération de besoins"
# - Logger chaque étape

# ⚠️ RÈGLE CRITIQUE ⚠️
# Ce agent fournit UNIQUEMENT le contexte (secteur, taille, actualités)
# Il ne génère JAMAIS de besoins
# Les besoins sont générés UNIQUEMENT par NeedAnalysisAgent

