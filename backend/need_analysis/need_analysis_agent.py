"""
NeedAnalysisAgent - Génération des besoins

FR: Agent LangGraph pour générer 10 besoins avec citations
⚠️ Sources PRINCIPALES : Workshop + Transcript
⚠️ Web Search = CONTEXTE uniquement
"""

# TODO (FR): Importer les dépendances
# - LangGraph SDK
# - OpenAI API
# - Prompts depuis prompts/need_analysis_agent_prompts.py
# - Modèles depuis models/need_analysis_models.py
# - typing, logging

# Références code existant :
# - OLD/need_analysis/need_analysis_agent.py
# - Prompts : OLD/prompts/need_analysis_agent_prompts.py
#   * Lignes 5-74 : System Prompt (toujours utilisé)
#   * Lignes 76-101 : User Prompt (1ère itération)
#   * Lignes 113-179 : User Prompt (régénération)

# TODO (FR): Créer la classe NeedAnalysisAgent
# - Hériter de la classe Agent de LangGraph
# - Définir les input :
#   * workshop_data (dict) : cas d'usage, objectifs, bénéfices
#   * transcript_data (list) : citations, frustrations, besoins exprimés
#   * web_search_data (dict) : contexte (secteur, taille) ⚠️ PAS de besoins
#   * excluded_needs (list, optionnel) : besoins à ne pas régénérer
#   * user_comment (str, optionnel) : consignes utilisateur
# - Définir l'output :
#   * needs (list[Need]) : 10 besoins avec titre + 5 citations

# TODO (FR): Méthode generate_initial_needs()
# - Utiliser System Prompt (lignes 5-74)
# - Utiliser User Prompt initial (lignes 76-101)
# - Combiner workshop_data + transcript_data (sources PRINCIPALES)
# - Utiliser web_search_data comme CONTEXTE uniquement
# - Générer 10 besoins uniques
# - Chaque besoin :
#   * Titre clair résumant l'apport
#   * 5 citations issues de Workshop ET Transcript
#   * ⚠️ Pas de citations sans source
#   * ⚠️ Pas de "- Transcript" générique
# - Retourner liste de 10 besoins

# TODO (FR): Méthode regenerate_needs()
# - Utiliser System Prompt (lignes 5-74)
# - Utiliser User Prompt régénération (lignes 113-179)
# - Exclure les besoins précédents (excluded_needs)
# - Prendre en compte user_comment
# - Générer 10 NOUVEAUX besoins DIFFÉRENTS
# - Même règles de génération que generate_initial_needs()
# - Retourner liste de 10 nouveaux besoins

# TODO (FR): Méthode validate_needs(needs: list) -> bool
# - Vérifier que chaque besoin a :
#   * Un titre non vide
#   * 5 citations avec sources
#   * Pas de doublons de thèmes
# - Logger les validations échouées
# - Retourner True si valide, False sinon

# TODO (FR): Méthode run() (point d'entrée LangGraph)
# - Déterminer si c'est génération initiale ou régénération
# - Appeler generate_initial_needs() ou regenerate_needs()
# - Valider les besoins générés
# - Retourner needs pour UseCaseAnalysisAgent
# - Logger chaque étape

# ⚠️ RÈGLES CRITIQUES ⚠️
# 1. Workshop + Transcript = sources PRINCIPALES pour citations
# 2. Web Search = CONTEXTE uniquement (secteur, taille, actualités)
# 3. Pas de citations sans source identifiable
# 4. Thèmes uniques (pas de doublons)
# 5. Exactement 10 besoins par génération

