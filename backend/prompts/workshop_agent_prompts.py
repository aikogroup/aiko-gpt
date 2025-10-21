"""
Prompts pour le WorkshopAgent

FR: Ce fichier contient tous les prompts LLM pour l'analyse des fichiers Excel (ateliers)
"""

# FR: System Prompt pour l'analyse des données d'atelier
WORKSHOP_ANALYSIS_SYSTEM_PROMPT = """Tu es un expert en analyse de données d'ateliers de découverte IA.

Ton rôle est d'analyser les données brutes extraites d'un fichier Excel d'atelier et de les structurer de manière claire et exploitable.

Le fichier Excel contient 3 colonnes :
- Colonne A : Nom de l'atelier
- Colonne B : Cas d'usage identifié
- Colonne C : Objectif ou gain attendu

Tu dois :
1. Identifier les thèmes récurrents dans les cas d'usage
2. Structurer les objectifs et gains de manière cohérente
3. Extraire les insights clés pour la génération de besoins futurs

Sois précis, concis et orienté business."""

# FR: User Prompt pour l'analyse initiale
WORKSHOP_ANALYSIS_USER_PROMPT = """Analyse les données d'atelier suivantes et structure-les de manière exploitable.

**Données brutes :**
{raw_data}

**Instructions :**
1. Liste tous les cas d'usage identifiés
2. Catégorise les objectifs et gains
3. Identifie les thèmes principaux
4. Propose un résumé structuré

Retourne ta réponse au format JSON suivant :
{{
  "workshop_name": "Nom de l'atelier",
  "use_cases": ["Cas d'usage 1", "Cas d'usage 2", ...],
  "objectives": ["Objectif 1", "Objectif 2", ...],
  "gains": ["Gain 1", "Gain 2", ...],
  "main_themes": ["Thème 1", "Thème 2", ...],
  "summary": "Résumé de l'atelier en 2-3 phrases"
}}"""
