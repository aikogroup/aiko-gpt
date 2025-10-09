"""
Prompts pour le Workshop Agent
"""

WORKSHOP_ANALYSIS_PROMPT = """
Vous êtes un expert en analyse de cas d'usage IA pour une société de conseil.

Votre mission est d'analyser les cas d'usage identifiés lors d'un atelier et de les structurer de manière cohérente et professionnelle.

Instructions:
1. Identifiez le thème principal de l'atelier
2. Regroupez les cas d'usage similaires pour éviter les doublons
3. Structurez chaque cas d'usage avec un titre clair, un objectif précis et des bénéfices identifiés
4. Priorisez les cas d'usage les plus impactants
5. Utilisez un langage professionnel et technique approprié

Format de réponse attendu (JSON uniquement):
{{
    "theme": "Thème principal de l'atelier",
    "use_cases": [
        {{
            "title": "Titre du cas d'usage",
            "objective": "Objectif principal et mesurable",
            "benefits": ["bénéfice 1", "bénéfice 2", "bénéfice 3"]
        }}
    ]
}}
"""

USE_CASE_CONSOLIDATION_PROMPT = """
Analysez les cas d'usage suivants pour l'atelier "{atelier_name}" et structurez-les de manière cohérente.

Cas d'usage identifiés:
{use_cases_text}

Consignes:
- Regroupez les cas d'usage similaires
- Évitez les doublons
- Identifiez les synergies entre les cas d'usage
- Priorisez par impact business
- Utilisez un vocabulaire professionnel

Retournez uniquement le JSON structuré sans commentaires supplémentaires.
"""

WORKSHOP_THEME_IDENTIFICATION_PROMPT = """
Identifiez le thème principal de l'atelier "{atelier_name}" basé sur les cas d'usage suivants:

{use_cases_text}

Le thème doit être:
- Concis et précis
- Orienté business
- Cohérent avec l'ensemble des cas d'usage
- Professionnel et technique

Exemples de thèmes appropriés:
- "Optimisation des processus métier"
- "Automatisation des tâches répétitives"
- "Amélioration de la prise de décision"
- "Digitalisation des processus RH"
- "Optimisation de la chaîne d'approvisionnement"
"""


