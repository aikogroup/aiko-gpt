"""
Prompts pour les agents de traitement des transcriptions
"""

# Prompt pour l'analyse sémantique avec GPT-5-nano
SEMANTIC_ANALYSIS_PROMPT = """
Analyse cette transcription et identifie :

– Les besoins exprimés par le client
– Les frustrations ou blocages
– Les attentes implicites  
– Les opportunités d'amélioration ou d'automatisation

Transcription :
{transcript_text}

Réponds au format JSON avec les clés suivantes :
- "besoins_exprimes": liste des besoins clairement exprimés
- "frustrations_blocages": liste des frustrations et blocages identifiés
- "attentes_implicites": liste des attentes non explicitement dites
- "opportunites_amelioration": liste des opportunités d'amélioration
- "opportunites_automatisation": liste des opportunités d'automatisation
- "citations_cles": liste des citations importantes avec le nom du speaker
"""

# Prompt système pour l'analyse sémantique
SEMANTIC_ANALYSIS_SYSTEM_PROMPT = """
Tu es un expert en analyse de besoins business spécialisé dans l'identification des opportunités d'automatisation et d'amélioration des processus.

Ton rôle est d'analyser les transcriptions de réunions de conseil pour :
1. Identifier les besoins explicites et implicites du client
2. Détecter les frustrations et blocages dans les processus actuels
3. Repérer les opportunités d'automatisation et d'amélioration
4. Extraire les citations clés qui illustrent ces points

Tu dois être précis et factuel, en te basant uniquement sur le contenu de la transcription.
"""

# Mots-clés pour identifier les parties intéressantes
INTEREST_KEYWORDS = [
    # Besoins et problèmes
    "besoin", "besoins", "problème", "problèmes", "difficulté", "difficultés",
    "challenge", "challenges", "défi", "défis", "enjeu", "enjeux",
    "frustration", "frustrations", "blocage", "blocages", "obstacle", "obstacles",
    
    # Processus et améliorations
    "processus", "process", "amélioration", "améliorations", "optimisation",
    "automatisation", "automatiser", "digitalisation", "digitaliser",
    "transformation", "modernisation", "efficacité", "performance",
    
    # Temps et coûts
    "temps", "rapidité", "lenteur", "délai", "délais", "urgence",
    "coût", "coûts", "budget", "économies", "rentabilité",
    
    # Qualité et erreurs
    "qualité", "erreur", "erreurs", "précision", "fiabilité",
    "contrôle", "vérification", "validation", "traçabilité",
    
    # Ressources humaines
    "équipe", "personnel", "formation", "compétences", "savoir-faire",
    "collaboration", "communication", "coordination",
    
    # Secteur spécifique (biotech/pharma)
    "réglementaire", "conformité", "audit", "inspection", "norme", "normes",
    "production", "qualité", "batch", "lot", "traçabilité", "documentation",
    "supply chain", "logistique", "stock", "inventaire"
]

# Mots-clés pour exclure les parties non pertinentes
EXCLUDE_KEYWORDS = [
    "merci", "au revoir", "bonjour", "bonsoir", "salut",
    "pause", "café", "déjeuner", "rendez-vous", "prochaine fois",
    "technique", "technique", "connexion", "micro", "son"
]

# Noms des consultants (à adapter selon les projets)
CONSULTANT_NAMES = [
    "christella", "adrien", "aiko", "consultant", "conseil"
]

# Prompt pour le filtrage des interventions intéressantes
INTERESTING_PARTS_FILTER_PROMPT = """
Tu es un expert en analyse de besoins business. Analyse cette transcription de réunion de conseil et identifie les interventions qui contiennent des informations pertinentes pour comprendre :

- Les besoins du client
- Les problèmes et frustrations exprimés
- Les processus actuels et leurs difficultés
- Les opportunités d'amélioration ou d'automatisation
- Les besoins en formation ou compétences
- Les enjeux business et opérationnels

Transcription :
{transcript_text}

Réponds UNIQUEMENT avec une liste des numéros d'intervention (entre crochets) qui sont intéressantes, séparés par des virgules.
Exemple : [0], [3], [7], [12]

Ne réponds que les numéros, rien d'autre.
"""

# Prompt système pour le filtrage des interventions
INTERESTING_PARTS_SYSTEM_PROMPT = """
Tu es un expert en analyse de besoins business. Tu identifies les parties pertinentes des transcriptions de réunions.
"""

# Prompt pour l'analyse sémantique (version améliorée)
SEMANTIC_ANALYSIS_PROMPT_V2 = """
Analyse cette transcription et identifie :

– Les besoins exprimés par le client
– Les frustrations ou blocages
– Les attentes implicites  
– Les opportunités d'amélioration ou d'automatisation

Transcription :
{transcript_text}

Réponds au format JSON avec les clés suivantes :
- "besoins_exprimes": liste des besoins clairement exprimés
- "frustrations_blocages": liste des frustrations et blocages identifiés
- "attentes_implicites": liste des attentes non explicitement dites
- "opportunites_amelioration": liste des opportunités d'amélioration
- "opportunites_automatisation": liste des opportunités d'automatisation
- "citations_cles": liste des citations importantes avec le nom du speaker
"""

# Prompt système pour l'analyse sémantique (version améliorée)
SEMANTIC_ANALYSIS_SYSTEM_PROMPT_V2 = """
Tu es un expert en analyse de besoins business spécialisé dans l'identification des opportunités d'automatisation et d'amélioration des processus.

Ton rôle est d'analyser les transcriptions de réunions de conseil pour :
1. Identifier les besoins explicites et implicites du client
2. Détecter les frustrations et blocages dans les processus actuels
3. Repérer les opportunités d'automatisation et d'amélioration
4. Extraire les citations clés qui illustrent ces points

Tu dois être précis et factuel, en te basant uniquement sur le contenu de la transcription.
"""
