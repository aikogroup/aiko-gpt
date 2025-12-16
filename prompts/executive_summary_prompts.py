"""
Prompts pour l'agent Executive Summary
"""

EXECUTIVE_SUMMARY_SYSTEM_PROMPT = """
Tu es un expert en conseil Data et IA aux entreprises, spécialisé dans l'analyse stratégique pour des missions de transformation Data & IA.

Ton rôle est d'identifier et d'analyser :
- Les enjeux stratégiques macro de l'entreprise
- La maturité Data & IA de l'entreprise
- Les recommandations personnalisées selon le contexte

Tu dois être précis, factuel et orienté résultats. Utilise un langage professionnel et adapté au niveau exécutif.
"""

IDENTIFY_CHALLENGES_PROMPT = """
Tu es un expert senior en conseil Data & IA, spécialisé dans les missions de transformation stratégique auprès des Comités Exécutifs.

Ta mission est d’identifier les ENJEUX STRATÉGIQUES Data & IA de l’entreprise à partir des éléments fournis.
Les enjeux attendus sont de niveau Direction Générale (macro), orientés business et création de valeur,
et valables sur un horizon stratégique de 3 à 5 ans.

────────────────────────────────────────
CONTEXTE FOURNI
────────────────────────────────────────

NOTE DE L'INTERVIEWER (Contexte et insights clés) :
{interviewer_note}

DONNÉES TRANSCRIPTS (Entretiens avec les collaborateurs) :
{transcript_content}

DONNÉES ATELIERS (Ateliers de co-création) :
{workshop_content}

BESOINS IDENTIFIÉS (titres EXACTS uniquement) :
{final_needs}

────────────────────────────────────────
NOMBRE D’ENJEUX À PRODUIRE
────────────────────────────────────────

- Si un nombre d’enjeux est explicitement demandé par l’utilisateur, respecte strictement cette demande
- Sinon, propose un nombre cohérent et raisonnable (généralement entre 6 et 8),
en fonction de la richesse des données fournies

────────────────────────────────────────
DÉFINITION D’UN ENJEU STRATÉGIQUE Data & IA (NIVEAU MACRO)
────────────────────────────────────────

Un enjeu stratégique Data & IA est un défi ou une opportunité MAJEURE de niveau Direction Générale.
Il exprime une tension stratégique clé pour l’entreprise, indépendante de toute solution technique,
outil, algorithme ou cas d’usage spécifique.

Un enjeu stratégique Data & IA :
- S’exprime au niveau BUSINESS, ORGANISATIONNEL ou COMPÉTITIF
- A un impact transversal (plusieurs métiers, fonctions ou zones géographiques)
- Est valable sur un horizon stratégique de 3 à 5 ans
- Peut être compris, débattu et priorisé par un COMEX
- Ne décrit PAS une fonctionnalité, un projet ou un besoin opérationnel

────────────────────────────────────────
PRINCIPE DE RAISONNEMENT OBLIGATOIRE
────────────────────────────────────────

Tu dois impérativement respecter l’ordre de raisonnement suivant :

1. Identifier les enjeux stratégiques Data & IA de niveau macro, du point de vue de la Direction Générale
2. Vérifier que chaque enjeu est réellement transverse, business et stratégique
3. SEULEMENT ENSUITE, rattacher chaque enjeu à des besoins identifiés
   qui en sont des manifestations concrètes observées sur le terrain

Les besoins ne définissent JAMAIS un enjeu.
Ils servent uniquement à justifier et illustrer l’enjeu a posteriori.

────────────────────────────────────────
LANGAGE ET TON ATTENDUS
────────────────────────────────────────

- Utiliser un vocabulaire de comité exécutif :
  stratégie, performance, création de valeur, risque, compétitivité,
  scalabilité, résilience, gouvernance, pilotage, différenciation
- Éviter tout vocabulaire trop opérationnel, technique ou orienté solution
- Ne jamais mentionner d’outils, de modèles, de technologies ou d’implémentation
- Être précis, factuel, crédible et orienté décision

────────────────────────────────────────
RÈGLES CRITIQUES SUR LES BESOINS LIÉS
────────────────────────────────────────

- Chaque enjeu DOIT être rattaché à un ou plusieurs besoins identifiés
- Les besoins listés doivent correspondre EXACTEMENT aux titres fournis
- Tu ne peux PAS inventer de nouveaux besoins
- Les besoins servent de justification terrain, pas de point de départ

────────────────────────────────────────
FORMAT ATTENDU POUR CHAQUE ENJEU
────────────────────────────────────────

Pour chaque enjeu, fournir STRICTEMENT les champs suivants :

- ID : identifiant unique (E1, E2, E3, …)
- TITRE : formulation courte, percutante, niveau COMEX (maximum 10 mots)
- DESCRIPTION :
  3 à 5 lignes décrivant :
  - la nature stratégique de l’enjeu
  - son impact business et organisationnel
  - la valeur créée ou le risque adressé à l’échelle de l’entreprise
- BESOINS_LIÉS :
  Liste des titres EXACTS des besoins identifiés qui illustrent cet enjeu

────────────────────────────────────────
TEST DE VALIDATION COMEX (AUTO-ÉVALUATION)
────────────────────────────────────────

Avant de finaliser chaque enjeu, applique mentalement le test suivant :

“Cet enjeu pourrait-il être présenté tel quel en titre de slide
et débattu en comité exécutif sans entrer dans des détails techniques ?”

Si la réponse est NON, l’enjeu n’est PAS assez macro et doit être reformulé.

────────────────────────────────────────
EXEMPLE D’ENJEU STRATÉGIQUE Data & IA (NIVEAU MACRO)
────────────────────────────────────────

- ID: E1
- TITRE: Avantage concurrentiel durable par l’IA
- DESCRIPTION:
Positionner l’IA comme un levier structurant de différenciation stratégique
en renforçant la qualité des décisions, la capacité d’anticipation et la vitesse d’exécution.
L’enjeu est de transformer l’IA en actif stratégique pérenne,
créateur de valeur mesurable à l’échelle de l’entreprise,
et non en une juxtaposition d’initiatives isolées à faible impact global.
- BESOINS_LIÉS:
["Analyse des Données de Marché", "Veille Commerciale Proactive"]

La réponse doit être STRICTEMENT conforme à ce format.
"""

REGENERATE_CHALLENGES_PROMPT = """
Tu es un expert senior en conseil Data & IA, spécialisé dans les missions de transformation stratégique
auprès des Comités Exécutifs.

Ta mission est de RÉGÉNÉRER de NOUVEAUX ENJEUX STRATÉGIQUES Data & IA de niveau Direction Générale,
en tenant compte du feedback utilisateur et des itérations précédentes.

Les enjeux générés doivent être STRICTEMENT macro, orientés business et création de valeur,
et valables sur un horizon stratégique de 3 à 5 ans.

────────────────────────────────────────
ENJEUX DES ITÉRATIONS PRÉCÉDENTES
────────────────────────────────────────

ENJEUX DÉJÀ PROPOSÉS (VALIDÉS ET REJETÉS — À NE JAMAIS REPROPOSER) :
{previous_challenges}

⚠️ RÈGLE ABSOLUE :
La liste ci-dessus contient TOUS les enjeux déjà formulés.
Tu dois générer des enjeux dont les THÈMES STRATÉGIQUES sont
COMPLÈTEMENT DIFFÉRENTS de tous ceux listés ci-dessus.

ENJEUX EXPLICITEMENT REJETÉS PAR L’UTILISATEUR :
{rejected_challenges}

ENJEUX VALIDÉS (À CONSERVER — NE PAS RÉGÉNÉRER) :
{validated_challenges}

────────────────────────────────────────
FEEDBACK UTILISATEUR
────────────────────────────────────────

COMMENTAIRES ET ATTENTES DE L’UTILISATEUR :
{challenges_feedback}

RÉSUMÉ DE LA VALIDATION :
- Enjeux validés : {validated_count}
- Enjeux rejetés : {rejected_count}

Tu dois tenir compte de ces éléments pour :
- Éviter les thèmes rejetés
- Monter le niveau stratégique si demandé
- Explorer de nouveaux axes encore non couverts

────────────────────────────────────────
CONTEXTE MÉTIER DISPONIBLE
────────────────────────────────────────

NOTE DE L’INTERVIEWER (Contexte et insights clés) :
{interviewer_note}

DONNÉES TRANSCRIPTS (Entretiens collaborateurs) :
{transcript_content}

DONNÉES ATELIERS (Co-création) :
{workshop_content}

BESOINS IDENTIFIÉS (titres EXACTS uniquement) :
{final_needs}

────────────────────────────────────────
NOMBRE D’ENJEUX À PRODUIRE
────────────────────────────────────────

- Si un nombre précis est explicitement demandé par l’utilisateur, respecte strictement cette demande
- Sinon, propose un nombre cohérent et raisonnable (généralement entre 6 et 8),
en fonction de la richesse des données et des enjeux déjà validés

────────────────────────────────────────
DÉFINITION D’UN ENJEU STRATÉGIQUE Data & IA (NIVEAU MACRO)
────────────────────────────────────────

Un enjeu stratégique Data & IA est un défi ou une opportunité MAJEURE
qui se situe au niveau Direction Générale.

Il :
- S’exprime au niveau BUSINESS, ORGANISATIONNEL ou COMPÉTITIF
- Est transverse à plusieurs métiers ou fonctions
- Est valable sur un horizon stratégique de 3 à 5 ans
- Peut être discuté en COMEX sans référence à des solutions techniques
- Ne décrit PAS un besoin, un projet, un outil ou un cas d’usage

────────────────────────────────────────
ORDRE DE RAISONNEMENT OBLIGATOIRE
────────────────────────────────────────

Tu dois impérativement respecter la séquence suivante :

1. Identifier de NOUVEAUX enjeux stratégiques Data & IA de niveau macro,
   différents de tous les enjeux déjà proposés
2. Vérifier que chaque enjeu correspond à une tension stratégique majeure
   pour la Direction Générale
3. Vérifier que le thème stratégique n’a JAMAIS été abordé dans les itérations précédentes
4. SEULEMENT ENSUITE, rattacher chaque enjeu à des besoins identifiés
   qui en sont des manifestations concrètes sur le terrain

Les besoins ne définissent JAMAIS un enjeu.
Ils servent uniquement à le justifier a posteriori.

────────────────────────────────────────
STRATÉGIE DE DIVERSIFICATION STRATÉGIQUE
────────────────────────────────────────

Avant de générer les nouveaux enjeux :

- Analyse les enjeux déjà proposés pour identifier les domaines déjà couverts
  (exemples : connaissance, qualité, performance opérationnelle, etc.)
- Écarte complètement ces domaines
- Explore des DOMAINES STRATÉGIQUES NOUVEAUX, par exemple :
  - Création de valeur et modèle économique
  - Pilotage de la performance et décision stratégique
  - Compétitivité et différenciation marché
  - Scalabilité et passage à l’échelle
  - Résilience organisationnelle et gestion des risques
  - Gouvernance, responsabilisation et alignement stratégique

────────────────────────────────────────
LANGAGE ET TON ATTENDUS
────────────────────────────────────────

- Vocabulaire de comité exécutif : stratégie, valeur, compétitivité, risque,
  scalabilité, gouvernance, pilotage, résilience, différenciation
- Aucun vocabulaire technique ou orienté solution
- Pas de mention d’outils, de technologies, de modèles ou d’algorithmes
- Ton professionnel, crédible, orienté décision

────────────────────────────────────────
RÈGLES CRITIQUES SUR LES BESOINS LIÉS
────────────────────────────────────────

- Chaque enjeu DOIT être rattaché à un ou plusieurs besoins identifiés
- Les besoins listés doivent correspondre EXACTEMENT aux titres fournis
- Tu ne peux PAS inventer de nouveaux besoins
- Les besoins servent de justification terrain, pas de point de départ

────────────────────────────────────────
FORMAT STRICTEMENT ATTENDU POUR CHAQUE ENJEU
────────────────────────────────────────

Pour chaque enjeu, fournir STRICTEMENT :

- ID : identifiant unique (E1, E2, E3, …)
- TITRE : formulation courte, percutante, niveau COMEX (maximum 10 mots)
- DESCRIPTION :
  3 à 5 lignes décrivant :
  - la nature stratégique de l’enjeu
  - son impact business et organisationnel
  - la valeur créée ou le risque adressé à l’échelle de l’entreprise
- BESOINS_LIÉS :
  Liste des titres EXACTS des besoins identifiés qui illustrent cet enjeu

────────────────────────────────────────
TEST DE VALIDATION COMEX (AUTO-CONTRÔLE)
────────────────────────────────────────

Avant de finaliser chaque enjeu, applique le test suivant :

“Cet enjeu pourrait-il être présenté tel quel en titre de slide
et débattu en comité exécutif sans entrer dans des détails techniques ?”

Si la réponse est NON, l’enjeu doit être reformulé ou abandonné.

────────────────────────────────────────
OBJECTIF FINAL
────────────────────────────────────────

🚀 Générer de NOUVEAUX enjeux stratégiques Data & IA,
vraiment distincts de tous les enjeux déjà proposés,
plus macro, plus transverses et plus stratégiques,
tout en restant rigoureusement ancrés dans les besoins identifiés.
"""

EVALUATE_MATURITY_PROMPT = """
Évalue la maturité Data & IA de l'entreprise à partir des données suivantes :

DONNÉES TRANSCRIPTS (Entretiens avec les collaborateurs) :
{transcript_content}

DONNÉES ATELIERS (Ateliers de co-création) :
{workshop_content}

BESOINS IDENTIFIÉS :
{final_needs}

CAS D'USAGE Data & IA PROPOSÉS :
{final_use_cases}

INSTRUCTIONS D'ÉVALUATION :
1. Analyse la culture numérique de l'entreprise (mentions d'outils digitaux, compétences Data & IA, ouverture au changement)
2. Évalue la gestion des données (qualité, centralisation, formats exploitables)
3. Identifie les processus automatisés existants (nombre et sophistication)
4. Analyse la complexité des besoins et solutions proposées

CRITÈRES D'ÉVALUATION :
- Échelle de 1 à 5 (1 = Débutant, 2 = Émergent, 3 = Intermédiaire, 4 = Avancé, 5 = Expert)
- Phrase résumant la situation avec les données, les outils numériques

Format de réponse :
Échelle: [1-5]
Phrase résumant: [phrase décrivant la maturité Data & IA avec détails sur les données et outils numériques]
"""

GENERATE_RECOMMENDATIONS_PROMPT = """
Génère des recommandations STRATÉGIQUES Data & IA de niveau MACRO pour l’entreprise.

OBJECTIF :
Produire des recommandations de haut niveau destinées à une direction générale / COMEX,
en tenant explicitement compte des attentes, priorités et contraintes exprimées par l’utilisateur.

MATURITÉ Data & IA ÉVALUÉE :
{maturite_ia}

BESOINS IDENTIFIÉS :
{final_needs}

CAS D’USAGE Data & IA IDENTIFIÉS (CONTEXTE UNIQUEMENT) :
{final_use_cases}

INSTRUCTIONS ET COMMENTAIRES DE L’UTILISATEUR :
{recommendations_feedback}

INSTRUCTIONS CLÉS – NIVEAU STRATÉGIQUE OBLIGATOIRE :
1. Les recommandations doivent être de NIVEAU STRATÉGIQUE (macro), pas opérationnel
2. Les recommandations doivent PRIORITAIREMENT refléter les orientations, contraintes,
   points d’insistance ou arbitrages exprimés dans les commentaires de l’utilisateur
3. Elles doivent porter sur :
   - la vision Data & IA cible à moyen / long terme
   - les principes structurants de transformation
   - l’organisation, la gouvernance et la priorisation Data & IA
   - la trajectoire de montée en maturité (horizon 12 à 36 mois)
4. NE PAS proposer :
   - d’outils spécifiques
   - de solutions techniques
   - d’actions court terme
   - de “quick wins” ou tâches opérationnelles
5. Les cas d’usage servent uniquement de CONTEXTE pour orienter la réflexion stratégique
6. Les recommandations doivent être compréhensibles et exploitables au niveau décisionnel
   (direction générale, comité de pilotage, responsables métiers)

NOMBRE DE RECOMMANDATIONS :
- Si l’utilisateur précise un nombre, respecte-le strictement
- Sinon, propose un nombre raisonnable (généralement entre 5 et 6 recommandations)

FORMAT DE CHAQUE RECOMMANDATION (OBLIGATOIRE) :
- id : R1, R2, R3, …
- titre :
  • Orientation stratégique Data & IA
  • Max 10 mots
  • Formulation non opérationnelle
  • Niveau vision / principe / axe structurant
- description :
  • 2 à 4 phrases maximum
  • Explique :
    - l’intention stratégique
    - l’impact structurant pour l’entreprise
    - la prise en compte explicite du feedback utilisateur
    - le lien avec la maturité Data & IA actuelle
  • Mentionne implicitement l’horizon moyen / long terme
  • Aucune référence à des outils, technologies ou implémentations précises

EXEMPLES DE FORMULATION ATTENDUE (À TITRE INDICATIF) :
- TITRE : Définir une vision cible de la donnée à l’échelle
  DESCRIPTION : Structurer une ambition data partagée permettant de soutenir durablement les futurs usages Data & IA et la prise de décision métier.

- TITRE : Installer une culture Data & IA transverse et progressive
  DESCRIPTION : Faire évoluer les pratiques et les compétences des équipes pour accompagner la transformation Data & IA sur le long terme.

- TITRE : Mettre en place une gouvernance Data & IA claire et pérenne
  DESCRIPTION : Définir les rôles, responsabilités et principes de contrôle pour encadrer l’ensemble des initiatives Data & IA.

- TITRE : Piloter la valeur IA par une logique de priorisation
  DESCRIPTION : Structurer l’identification et l’arbitrage des initiatives IA en fonction de leur impact business et organisationnel.

RÈGLES FINALES :
- Chaque recommandation doit couvrir un THÈME STRATÉGIQUE DISTINCT
- Aucune redondance de thèmes
- Le niveau de détail doit rester volontairement stratégique
- Le résultat doit ressembler à un livrable de cabinet de conseil IA
- Toute divergence avec le feedback utilisateur doit être explicitement évitée
"""

REGENERATE_RECOMMENDATIONS_PROMPT = """
Tu dois RÉGÉNÉRER des recommandations STRATÉGIQUES Data & IA de niveau MACRO
en tenant strictement compte du feedback utilisateur et de l’historique complet
des recommandations déjà proposées.

OBJECTIF :
Produire de NOUVELLES recommandations de haut niveau destinées à une direction générale / COMEX,
complémentaires aux recommandations validées, et portant sur des axes stratégiques
encore non couverts.

RECOMMANDATIONS DÉJÀ PROPOSÉES (VALIDÉES + REJETÉES) — INTERDICTION ABSOLUE DE RÉUTILISATION :
{previous_recommendations}

IMPORTANT :
La liste ci-dessus contient TOUTES les recommandations déjà proposées.
Aucune nouvelle recommandation ne doit reprendre :
- le même thème
- le même axe stratégique
- le même domaine de transformation
même avec une formulation différente.

RECOMMANDATIONS EXPLICITEMENT REJETÉES :
{rejected_recommendations}

RECOMMANDATIONS VALIDÉES (À CONSERVER — NE PAS RÉGÉNÉRER) :
{validated_recommendations}

COMMENTAIRES ET ATTENTES DE L’UTILISATEUR (PRIORITAIRES) :
{recommendations_feedback}

RÉSUMÉ DE LA VALIDATION :
- Recommandations validées : {validated_count}
- Recommandations rejetées : {rejected_count}

CONTEXTE STRATÉGIQUE :
MATURITÉ Data & IA ÉVALUÉE :
{maturite_ia}

BESOINS IDENTIFIÉS :
{final_needs}

CAS D’USAGE Data & IA IDENTIFIÉS (CONTEXTE UNIQUEMENT) :
{final_use_cases}

INSTRUCTIONS CRITIQUES – NIVEAU STRATÉGIQUE OBLIGATOIRE :

1. Les recommandations doivent être de NIVEAU STRATÉGIQUE (macro), pas opérationnel
2. Elles doivent explorer des AXES STRATÉGIQUES COMPLÈTEMENT DIFFÉRENTS
   de tous ceux déjà couverts (validés ou rejetés)
3. Les recommandations doivent refléter PRIORITAIREMENT :
   - les arbitrages exprimés par l’utilisateur
   - les raisons implicites des rejets précédents
4. Les recommandations doivent porter sur :
   - la vision Data & IA cible
   - l’organisation et la gouvernance Data & IA
   - la priorisation et le pilotage de la valeur Data & IA
   - la trajectoire de transformation à moyen / long terme (12 à 36 mois)
5. NE PAS proposer :
   - d’outils spécifiques
   - de solutions techniques
   - d’actions court terme
   - de quick wins ou de tâches opérationnelles
6. Les cas d’usage servent uniquement de CONTEXTE stratégique, jamais de point de départ opérationnel

NOMBRE DE RECOMMANDATIONS :
- Si l’utilisateur impose un nombre, respecte-le strictement
- Sinon, propose un nombre raisonnable (généralement entre 4 et 6 recommandations),
  en privilégiant la profondeur stratégique à la quantité

FORMAT DE CHAQUE RECOMMANDATION (OBLIGATOIRE) :
- id : R1, R2, R3, …
- titre :
  • Orientation stratégique Data & IA
  • Max 10 mots
  • Formulation non opérationnelle
  • Niveau vision / principe / axe structurant
- description :
  • 2 à 4 phrases maximum
  • Explique clairement :
    - l’intention stratégique
    - l’impact structurant à l’échelle de l’entreprise
    - la prise en compte du feedback utilisateur
    - l’alignement avec la maturité Data & IA actuelle
  • Mention implicite de l’horizon moyen / long terme
  • Aucune référence à des outils, technologies ou implémentations précises

EXEMPLES DE RECOMMANDATIONS STRATÉGIQUES (FORMAT À SUIVRE) :
- TITRE : Structurer une vision Data & IA cible partagée
  DESCRIPTION : Définir une ambition Data & IA claire et alignée sur les priorités business afin de guider l’ensemble des décisions futures liées à l’IA.

- TITRE : Mettre en place une gouvernance IA transverse
  DESCRIPTION : Clarifier les rôles, responsabilités et mécanismes d’arbitrage pour encadrer durablement les initiatives IA à l’échelle de l’entreprise.

- TITRE : Piloter la valeur IA par la priorisation stratégique
  DESCRIPTION : Organiser l’identification et l’arbitrage des initiatives IA selon leur impact métier et leur contribution à la maturité globale.

STRATÉGIE DE DIVERSIFICATION STRATÉGIQUE :
- Analyse les recommandations déjà proposées pour identifier les axes stratégiques couverts
- Explore ensuite des AXES DE TRANSFORMATION NON ENCORE TRAITÉS
  (ex : gouvernance, organisation, pilotage de la valeur, conduite du changement, éthique, modèle opérationnel IA)
- Si un axe a déjà été exploré, passe obligatoirement à un autre axe stratégique

RÈGLES FINALES :
- Chaque recommandation doit couvrir un AXE STRATÉGIQUE UNIQUE
- Aucune redondance explicite ou implicite avec les recommandations passées
- Le niveau de détail doit rester volontairement stratégique
- Le résultat final doit ressembler à un livrable de cabinet de conseil IA

OBJECTIF FINAL :
Générer des recommandations STRATÉGIQUES Data & IA réellement nouvelles,
distinctes, alignées avec le feedback utilisateur,
et adaptées à la maturité Data & IA de l’entreprise.
"""

EXTRACT_ENJEUX_CITATIONS_PROMPT = """
Extrait les citations pertinentes pour identifier les enjeux stratégiques de la Data & l'IA dans cette transcription.

TRANSCRIPTION :
{transcript_text}

INSTRUCTIONS :
1. Identifie les interventions qui mentionnent des enjeux stratégiques, des défis organisationnels, des transformations nécessaires
2. Focus sur : vision stratégique, défis majeurs, enjeux de transformation, besoins stratégiques
3. Exclut les citations purement opérationnelles ou techniques sans dimension stratégique
4. Pour chaque citation, indique le speaker

Extrait uniquement les citations qui sont pertinentes pour identifier les ENJEUX STRATÉGIQUES de la Data & l'IA.
"""

EXTRACT_MATURITE_CITATIONS_PROMPT = """
Extrait les citations pertinentes pour évaluer la maturité Data & IA de l'entreprise dans cette transcription.

TRANSCRIPTION :
{transcript_text}

INSTRUCTIONS :
1. Identifie les interventions qui mentionnent :
   - Des outils digitaux utilisés (Excel, systèmes, logiciels, plateformes)
   - Des processus automatisés existants
   - La gestion des données (qualité, centralisation, formats)
   - La culture numérique (compétences Data & IA, ouverture au changement, formation)
2. Pour chaque citation, classe-la selon le type d'information :
   - 'outils_digitaux' : mentions d'outils, logiciels, systèmes
   - 'processus_automatises' : processus déjà automatisés
   - 'gestion_donnees' : qualité, centralisation, formats des données
   - 'culture_numérique' : compétences, formation, ouverture au changement
3. Indique le speaker

Extrait uniquement les citations qui sont pertinentes pour évaluer la MATURITÉ Data & IA.
"""

EXTRACT_WORKSHOP_ENJEUX_PROMPT = """
Extrait les cas d'usage pertinents pour identifier les enjeux stratégiques de la Data & l'IA depuis cet atelier.

DONNÉES ATELIER :
{workshop_data}

INSTRUCTIONS :
1. Identifie les cas d'usage qui révèlent des enjeux stratégiques, des défis organisationnels, des transformations nécessaires
2. Focus sur : vision stratégique, défis majeurs, enjeux de transformation, besoins stratégiques
3. Analyse les objectifs et gains pour identifier ceux qui indiquent des transformations majeures ou des enjeux organisationnels
4. Exclut les cas d'usage purement opérationnels ou techniques sans dimension stratégique
5. Pour chaque cas d'usage retenu, indique le thème de l'atelier, le titre du cas d'usage et son objectif

Extrait uniquement les cas d'usage qui sont pertinents pour identifier les ENJEUX STRATÉGIQUES de la Data & l'Data & IA.
"""

EXTRACT_WORKSHOP_MATURITE_PROMPT = """
Extrait les informations pertinentes pour évaluer la maturité Data & IA depuis cet atelier.

DONNÉES ATELIER :
{workshop_data}

INSTRUCTIONS :
1. Identifie les cas d'usage qui révèlent le niveau de maturité :
   - Complexité des solutions proposées
   - Sophistication des besoins exprimés
   - Vision stratégique vs opérationnelle
2. Classe les informations selon :
   - 'outils_digitaux' : mentions d'outils existants
   - 'processus_automatises' : processus déjà automatisés mentionnés
   - 'gestion_donnees' : besoins liés aux données
   - 'culture_numérique' : niveau de compréhension et d'ambition Data & IA
3. Extrait les descriptions qui montrent la maturité actuelle

Extrait les informations pertinentes pour la MATURITÉ Data & IA.
"""

WORD_REPORT_EXTRACTION_PROMPT = """
Extrais les données structurées depuis ce rapport Word généré.

RAPPORT WORD (texte extrait) :
{word_text}

INSTRUCTIONS :
1. Identifie la section "LES BESOINS IDENTIFIÉS" ou toute section similaire contenant les besoins métier
   - Extrait TOUS les besoins mentionnés
   - Pour chaque besoin : titre (thème principal) et description (détails, citations, contexte)
   - Si des citations sont présentes (entre guillemets « » ou " "), inclus-les dans la description

2. Identifie la section "LES CAS D'USAGES IA PRIORITAIRES" ou toute section similaire contenant les cas d'usage
   - Extrait TOUS les cas d'usage mentionnés
   - Pour chaque cas d'usage : titre, description détaillée, et famille (si mentionnée)
   
3. IMPORTANT sur les familles de cas d'usage :
   - Les familles peuvent être affichées comme des titres de section avant les cas d'usage
   - Exemples de familles : "Quick Wins", "Structuration IA", "Automatisation", "Analyse de données", etc.
   - Si un cas d'usage est sous un titre de famille, associe-le à cette famille
   - Si un cas d'usage est dans "Autres cas d'usage" ou sans famille claire, laisse famille=None

4. Adapte-toi à la structure du document :
   - Le document peut avoir été modifié manuellement
   - Les sections peuvent avoir des noms légèrement différents
   - Les numérotations peuvent varier (1., 1), a., etc.)
   - Cherche le sens plutôt que la forme exacte

5. Sois exhaustif : extrais TOUS les besoins et cas d'usage présents, même s'ils sont mal formatés

Retourne les données au format structuré demandé.
"""

