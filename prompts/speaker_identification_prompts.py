"""
Prompts pour l'identification et l'extraction des speakers et leurs rôles
"""

SPEAKER_IDENTIFICATION_AND_ROLE_EXTRACTION_PROMPT = """Analyse cette transcription de réunion et identifie les vrais noms de personnes (speakers), leur titre de poste/rôle professionnel, et leur niveau hiérarchique.

Liste de tous les speakers extraits par le parser (certains peuvent être des fragments de texte erronés):
{candidate_speakers}

Interventions complètes de chaque speaker:
{all_interventions}
{known_roles_text}
Pour chaque speaker, identifie:
1. Si c'est un VRAI nom de personne (rejette les fragments comme "mais pas à ceux", "qu'il est celui", etc.)
2. Son titre de poste/rôle professionnel s'il est mentionné dans ses interventions
3. Son niveau hiérarchique basé sur son poste:
   - "direction" : si le poste est stratégique/management (DG, Directeur général, CEO, PDG, CTO, Directeur de [fonction], etc.)
   - "métier" : si le poste est opérationnel (collaborateur, responsable opérationnel, etc.)
   - "inconnu" : si aucun poste clair n'est mentionné dans les interventions

FORMAT DE RÉPONSE (JSON strict):
{{
  "speakers": [
    {{"name": "Nom complet", "role": "Titre de poste", "level": "direction"}},
    {{"name": "Autre nom", "role": "NON_TROUVE", "level": "inconnu"}}
  ]
}}

Règle importante : Si le rôle est "NON_TROUVE", le level doit être "inconnu".

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

EXTRACT_ROLES_FOR_JSON_SPEAKERS_PROMPT = """Analyse cette transcription de réunion et extrait les rôles et niveaux hiérarchiques pour les speakers suivants (déjà identifiés depuis le JSON).

Liste des speakers à analyser (déjà identifiés depuis le JSON):
{json_speakers}

Interventions complètes de chaque speaker:
{all_interventions}
{known_roles_text}

Pour chaque speaker de la liste, identifie:
1. Son titre de poste/rôle professionnel s'il est mentionné dans ses interventions
2. Son niveau hiérarchique basé sur son poste:
   - "direction" : si le poste est stratégique/management (DG, Directeur général, CEO, PDG, CTO, Directeur de [fonction], etc.)
   - "métier" : si le poste est opérationnel (collaborateur, responsable opérationnel, etc.)
   - "inconnu" : si aucun poste clair n'est mentionné dans les interventions

IMPORTANT: Tu dois retourner UNE entrée pour CHAQUE speaker de la liste, même si tu ne trouves pas de rôle.

FORMAT DE RÉPONSE (JSON strict):
{{
  "speakers": [
    {{"name": "Nom exact du speaker", "role": "Titre de poste", "level": "direction"}},
    {{"name": "Autre nom exact", "role": "NON_TROUVE", "level": "inconnu"}}
  ]
}}

Règle importante : Si le rôle est "NON_TROUVE", le level doit être "inconnu".

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

