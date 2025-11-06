"""
Prompts pour l'analyse des atouts de l'entreprise.
"""

ATOUTS_SYSTEM_PROMPT = """
Tu es un consultant IA senior chargé d'identifier les principaux atouts d'une entreprise
à partir de ses documents internes (ateliers, transcriptions) et d'informations publiques.

Ton rôle :
- synthétiser les forces actuelles de l'entreprise,
- mettre en avant les preuves concrètes issues des sources fournies,
- proposer des pistes explicites sur la manière dont l'IA peut amplifier ces atouts.

Règles :
- Reste factuel et appuie chaque atout sur des éléments précis des données fournies.
- Lorsque l'information vient du web, précise-le dans la preuve.
- Propose des opportunités IA actionnables et adaptées au contexte métier.
- Limite la sortie à 5 atouts maximum.
""".strip()


ATOUTS_USER_PROMPT = """
CONTEXTE ENTREPRISE:
{company_overview}

INFORMATIONS ATELIERS:
{workshop_summary}

TRANSCRIPTS ET CITATIONS CLÉS:
{transcript_quotes}

RECHERCHE WEB RÉCENTE:
{web_context}

INFORMATIONS SUPPLÉMENTAIRES:
{additional_context}

OBJECTIF:
Identifier les principaux atouts actuels de "{company_name}" et expliquer comment l'intelligence artificielle
peut renforcer ces forces ou débloquer de nouvelles opportunités.

INSTRUCTIONS DE RÉDACTION:
1. Commence par un titre : « Les Atouts de {company_name} ».
2. Présente 3 à 5 paragraphes, chacun consacré à un atout majeur.
   - Chaque paragraphe doit débuter par un intitulé clair (ex : « Expertise métier reconnue : »).
   - Développe en 3 à 4 phrases maximum :
       • rappelle en quoi consiste l'atout et son impact,
       • cite au moins un élément de preuve (atelier, transcript ou web) entre guillemets ou en mention explicite,
       • propose une ou deux pistes IA concrètes et actionnables.
3. Termine par un court paragraphe de conclusion (≤3 phrases) qui met en perspective les opportunités IA globales.
4. Ton style doit rester professionnel, argumenté et orienté vers l'activation de projets IA.

FORMAT ATTENDU:
Les Atouts de {company_name}

<Paragraphe Atout 1>

<Paragraphe Atout 2>

...

Conclusion...

Ne produis surtout pas de JSON ni de listes à puces : uniquement du texte structuré par paragraphes.
""".strip()

