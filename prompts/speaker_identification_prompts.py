"""
Prompts pour l'identification et l'extraction des speakers et leurs rôles
"""

SPEAKER_IDENTIFICATION_AND_ROLE_EXTRACTION_PROMPT = """Analyse cette transcription de réunion et identifie les vrais noms de personnes (speakers) ainsi que leur titre de poste/rôle professionnel.

Liste de tous les speakers extraits par le parser (certains peuvent être des fragments de texte erronés):
{candidate_speakers}

Interventions complètes de chaque speaker:
{all_interventions}
{known_roles_text}
Pour chaque speaker, identifie:
1. Si c'est un VRAI nom de personne (rejette les fragments comme "mais pas à ceux", "qu'il est celui", etc.)
2. Son titre de poste/rôle professionnel s'il est mentionné dans ses interventions

FORMAT DE RÉPONSE (JSON strict):
{{
  "speakers": [
    {{"name": "Nom complet", "role": "Titre de poste"}},
    {{"name": "Autre nom", "role": "NON_TROUVE"}}
  ]
}}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

