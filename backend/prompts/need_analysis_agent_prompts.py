"""
Prompts pour NeedAnalysisAgent

FR: Prompts LLM pour générer les 10 besoins avec citations
"""

# TODO (FR): Copier et adapter les prompts depuis OLD/prompts/need_analysis_agent_prompts.py

# ⚠️ Structure des prompts (voir OLD/prompts/need_analysis_agent_prompts.py) :

# SYSTEM_PROMPT (Lignes 5-74 de l'ancien fichier)
# - Toujours utilisé
# - Définit les règles d'analyse
# - ⚠️ CRITIQUE : Workshop + Transcript = sources PRINCIPALES
# - Web Search = contexte uniquement, PAS de besoins génériques
# - Citations sans source interdites (pas de "- Transcript")
# - Thèmes uniques (pas de doublons)

# USER_PROMPT_INITIAL (Lignes 76-101 de l'ancien fichier)
# - Utilisé pour la 1ère itération
# - Génération initiale de ~10 besoins
# - Format de sortie JSON

# USER_PROMPT_REGENERATE (Lignes 113-179 de l'ancien fichier)
# - Utilisé pour les régénérations
# - Génère 10 nouveaux besoins COMPLÈTEMENT DIFFÉRENTS
# - Exclut les besoins précédents (non validés)
# - Prend en compte le commentaire utilisateur

# Références :
# - OLD/prompts/need_analysis_agent_prompts.py lignes 5-74 (System)
# - OLD/prompts/need_analysis_agent_prompts.py lignes 76-101 (Initial)
# - OLD/prompts/need_analysis_agent_prompts.py lignes 113-179 (Regenerate)

# TODO (FR): Variables SYSTEM_PROMPT, USER_PROMPT_INITIAL, USER_PROMPT_REGENERATE
# SYSTEM_PROMPT = """
# Votre rôle...
# ⚠️ Sources principales : Workshop + Transcript
# ⚠️ Web Search = contexte uniquement
# """
#
# USER_PROMPT_INITIAL = """
# Générez 10 besoins...
# """
#
# USER_PROMPT_REGENERATE = """
# Générez 10 nouveaux besoins différents...
# Besoins à exclure : {excluded_needs}
# Commentaire utilisateur : {user_comment}
# """

