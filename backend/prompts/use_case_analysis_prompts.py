"""
Prompts pour UseCaseAnalysisAgent

FR: Prompts LLM pour générer Quick Wins et Structuration IA
"""

# TODO (FR): Copier et adapter les prompts depuis OLD/prompts/use_case_analysis_prompts.py

# ⚠️ Structure des prompts (voir OLD/prompts/use_case_analysis_prompts.py) :

# SYSTEM_PROMPT (Lignes 5-50 de l'ancien fichier)
# - Toujours utilisé
# - Définit les 2 types de cas d'usage :
#   * Quick Wins (8) : Automatisation rapide, ROI immédiat (< 3 mois)
#   * Structuration IA (10) : Solutions avancées, ROI moyen/long terme (3-12 mois)
# - Technologies IA concrètes (LLM, RAG, OCR, ML supervisé, etc.)
# - Titres uniques (pas de doublons)

# USER_PROMPT_INITIAL (Lignes 52-77 de l'ancien fichier)
# - Utilisé pour la 1ère itération
# - Génération de 8 QW + 10 SIA
# - Format de sortie JSON

# USER_PROMPT_REGENERATE (Lignes 79-127 de l'ancien fichier)
# - Utilisé pour les régénérations
# - ⚠️ RÈGLE INTELLIGENTE :
#   * Si QW validés < 5 → Génère nouveaux QW
#   * Si SIA validés < 5 → Génère nouveaux SIA
#   * Si >= 5 validés dans une catégorie → NE RÉGÉNÈRE RIEN
# - Prend en compte le commentaire utilisateur

# Références :
# - OLD/prompts/use_case_analysis_prompts.py lignes 5-50 (System)
# - OLD/prompts/use_case_analysis_prompts.py lignes 52-77 (Initial)
# - OLD/prompts/use_case_analysis_prompts.py lignes 79-127 (Regenerate)

# TODO (FR): Variables SYSTEM_PROMPT, USER_PROMPT_INITIAL, USER_PROMPT_REGENERATE
# SYSTEM_PROMPT = """
# Votre rôle...
# Quick Wins : ROI < 3 mois
# Structuration IA : ROI 3-12 mois
# """
#
# USER_PROMPT_INITIAL = """
# Générez 8 Quick Wins et 10 Structuration IA...
# """
#
# USER_PROMPT_REGENERATE = """
# Régénérez les catégories manquantes...
# Si >= 5 validés dans une catégorie, ne régénérez rien.
# """

