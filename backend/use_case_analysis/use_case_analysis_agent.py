"""
UseCaseAnalysisAgent - Génération des cas d'usage

FR: Agent LangGraph pour générer Quick Wins et Structuration IA
⚠️ Règle intelligente : Si >= 5 validés dans une catégorie, ne régénère rien
"""

# TODO (FR): Importer les dépendances
# - LangGraph SDK
# - OpenAI API
# - Prompts depuis prompts/use_case_analysis_prompts.py
# - Modèles depuis models/use_case_analysis_models.py
# - typing, logging

# Références code existant :
# - OLD/use_case_analysis/use_case_analysis_agent.py
# - Prompts : OLD/prompts/use_case_analysis_prompts.py
#   * Lignes 5-50 : System Prompt
#   * Lignes 52-77 : User Prompt (1ère itération)
#   * Lignes 79-127 : User Prompt (régénération)

# TODO (FR): Créer la classe UseCaseAnalysisAgent
# - Hériter de la classe Agent de LangGraph
# - Définir les input :
#   * validated_needs (list) : Besoins validés page 2 (minimum 5)
#   * workshop_data (dict) : Contexte
#   * transcript_data (list) : Contexte
#   * web_search_data (dict) : Contexte
#   * validated_quick_wins (list, optionnel) : QW déjà validés
#   * validated_structuration_ia (list, optionnel) : SIA déjà validés
#   * user_comment (str, optionnel) : Consignes utilisateur
# - Définir l'output :
#   * quick_wins (list[UseCase]) : 8 cas d'usage Quick Wins
#   * structuration_ia (list[UseCase]) : 10 cas d'usage Structuration IA

# TODO (FR): Méthode generate_initial_use_cases()
# - Vérifier qu'il y a au moins 5 validated_needs
# - Utiliser System Prompt (lignes 5-50)
# - Utiliser User Prompt initial (lignes 52-77)
# - Générer 8 Quick Wins :
#   * Projets simples, automatisation rapide
#   * ROI immédiat (< 3 mois)
#   * Technologies IA concrètes (LLM, RAG, OCR, ML, etc.)
#   * Titres uniques
# - Générer 10 Structuration IA :
#   * Solutions avancées et ambitieuses
#   * Projets structurants
#   * ROI moyen/long terme (3-12 mois)
#   * Technologies IA avancées
#   * Titres uniques
# - Retourner dict {quick_wins: [...], structuration_ia: [...]}

# TODO (FR): Méthode regenerate_use_cases()
# - Utiliser System Prompt (lignes 5-50)
# - Utiliser User Prompt régénération (lignes 79-127)
# - ⚠️ RÈGLE INTELLIGENTE :
#   * Si len(validated_quick_wins) >= 5 → NE RÉGÉNÈRE RIEN pour QW
#   * Si len(validated_structuration_ia) >= 5 → NE RÉGÉNÈRE RIEN pour SIA
#   * Sinon, génère pour compléter la catégorie manquante
# - Prendre en compte user_comment
# - Générer UNIQUEMENT les catégories nécessaires
# - Retourner dict {quick_wins: [...], structuration_ia: [...]}

# TODO (FR): Méthode validate_use_cases(use_cases: dict) -> bool
# - Vérifier chaque cas d'usage :
#   * Titre non vide et unique
#   * Description claire
#   * Technologies IA pertinentes et concrètes
#   * Pas de doublons
# - Logger les validations échouées
# - Retourner True si valide, False sinon

# TODO (FR): Méthode run() (point d'entrée LangGraph)
# - Vérifier présence de validated_needs (minimum 5)
# - Déterminer si génération initiale ou régénération
# - Appeler generate_initial_use_cases() ou regenerate_use_cases()
# - Valider les cas d'usage générés
# - Retourner use_cases pour ReportAgent
# - Logger chaque étape

# ⚠️ RÈGLES CRITIQUES ⚠️
# 1. Minimum 5 validated_needs requis
# 2. Technologies IA concrètes et pertinentes
# 3. Titres uniques (pas de doublons)
# 4. Si >= 5 validés dans une catégorie → NE RÉGÉNÈRE RIEN
# 5. Quick Wins : ROI < 3 mois
# 6. Structuration IA : ROI 3-12 mois

