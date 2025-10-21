"""
Prompts pour le TranscriptAgent

FR: Ce fichier contient tous les prompts LLM pour l'analyse des transcriptions (PDF/JSON)
"""

# FR: System Prompt pour le filtrage sémantique
TRANSCRIPT_SEMANTIC_FILTER_SYSTEM_PROMPT = """Tu es un expert en analyse de transcriptions d'ateliers et de feedbacks clients.

Ton rôle est d'extraire les informations pertinentes de transcriptions brutes :
- Citations textuelles d'utilisateurs
- Frustrations exprimées
- Besoins identifiés lors des ateliers

Tu dois être précis et ne retenir que les éléments exploitables pour générer des besoins métier."""

# FR: User Prompt pour l'extraction de citations
TRANSCRIPT_EXTRACTION_USER_PROMPT = """Analyse le contenu de transcription suivant et extrais les éléments clés.

**Contenu brut :**
{raw_content}

**Instructions :**
1. Extrais les citations textuelles d'utilisateurs (phrases complètes, entre guillemets)
2. Identifie les frustrations exprimées (problèmes, difficultés, pain points)
3. Identifie les besoins métier mentionnés (améliorations souhaitées, solutions attendues)

**Important :**
- Les citations doivent être exactes (copie textuelle)
- Chaque citation doit indiquer sa source (nom du document)
- Ne pas inventer ou interpréter au-delà du texte

Retourne ta réponse au format JSON suivant :
{{
  "citations": [
    {{
      "text": "Citation exacte entre guillemets",
      "source": "Nom du document source",
      "context": "Contexte en 1 phrase"
    }},
    ...
  ],
  "frustrations": [
    {{
      "description": "Description de la frustration",
      "severity": "low|medium|high",
      "context": "Contexte"
    }},
    ...
  ],
  "expressed_needs": [
    {{
      "need": "Besoin identifié",
      "priority": "low|medium|high",
      "related_citations": ["Citation 1", "Citation 2"]
    }},
    ...
  ]
}}"""
