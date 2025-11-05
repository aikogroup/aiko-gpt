"""
Prompts pour l'agent Executive Summary
"""

EXECUTIVE_SUMMARY_SYSTEM_PROMPT = """
Tu es un expert en conseil IA aux entreprises, spécialisé dans l'analyse stratégique pour des missions de transformation IA.

Ton rôle est d'identifier et d'analyser :
- Les enjeux stratégiques de l'entreprise
- La maturité IA de l'entreprise
- Les recommandations personnalisées selon le contexte

Tu dois être précis, factuel et orienté résultats. Utilise un langage professionnel et adapté au niveau exécutif.
"""

IDENTIFY_CHALLENGES_PROMPT = """
Analyse les données suivantes et identifie 5 enjeux stratégiques de l'IA pour l'entreprise, en te mettant dans la peau d'un expert en transformation digitale.

DONNÉES TRANSCRIPTS (Entretiens avec les collaborateurs) :
{transcript_content}

DONNÉES ATELIERS (Ateliers de co-création) :
{workshop_content}

BESOINS IDENTIFIÉS :
{final_needs}

CONTEXTE :
Les enjeux de l'IA représentent les grands défis stratégiques que l'entreprise doit relever. Chaque enjeu doit être lié à au moins un besoin identifié lors des entretiens et ateliers.

INSTRUCTIONS :
1. Identifie 5 enjeux stratégiques spécifiques et concrets pour l'entreprise
2. Base-toi sur les données réelles des transcripts, ateliers et SURTOUT les besoins identifiés
3. Pour chaque enjeu, fournis :
   - Un ID unique (E1, E2, E3, E4, E5)
   - Un TITRE court et percutant (max 10 mots)
   - Une DESCRIPTION détaillée en 3-5 lignes expliquant l'enjeu, son impact et sa valeur stratégique
   - Les BESOINS LIÉS (IDs ou titres des besoins qui se rattachent à cet enjeu)
4. Chaque enjeu doit être unique et spécifique au contexte de l'entreprise
5. Les enjeux doivent couvrir différents aspects de la transformation IA

EXEMPLE D'ENJEU :
- ID: E1
- TITRE: Capitalisation des connaissances internes
- DESCRIPTION: Transformer le capital intellectuel actuellement dispersé de l'entreprise en avantage concurrentiel durable. L'enjeu est de créer un "cerveau collectif" organisationnel qui pourrait automatiser l'accès à l'expertise technique et clinique, faciliter le partage des bonnes pratiques entre équipes, et accélérer la formation des nouvelles recrues pour réduire les délais de montée en compétence tout en préservant le savoir-faire critique.
- BESOINS_LIÉS: [B001, B002, "Centraliser les connaissances techniques"]

La réponse sera automatiquement structurée selon le format attendu.
"""

REGENERATE_CHALLENGES_PROMPT = """
Tu dois régénérer les enjeux stratégiques en tenant compte du feedback utilisateur.

ENJEUX PRÉCÉDENTS (REJETÉS) :
{rejected_challenges}

FEEDBACK UTILISATEUR :
{challenges_feedback}

ENJEUX VALIDÉS (À CONSERVER) :
{validated_challenges}

DONNÉES TRANSCRIPTS :
{transcript_content}

DONNÉES ATELIERS :
{workshop_content}

BESOINS IDENTIFIÉS :
{final_needs}

INSTRUCTIONS :
1. Analyse le feedback utilisateur pour comprendre ce qui doit être modifié
2. Conserve les enjeux validés (ne les régénère pas)
3. Régénère uniquement les enjeux rejetés en tenant compte du feedback
4. Assure-toi d'avoir exactement 5 enjeux au total (validés + nouveaux)
5. Si le feedback indique qu'il manque des enjeux, génère-en de nouveaux
6. Si le feedback indique que certains enjeux doivent être fusionnés ou séparés, adapte en conséquence

Génère 5 enjeux stratégiques au format structuré.
"""

EVALUATE_MATURITY_PROMPT = """
Évalue la maturité IA de l'entreprise à partir des données suivantes :

DONNÉES TRANSCRIPTS (Entretiens avec les collaborateurs) :
{transcript_content}

DONNÉES ATELIERS (Ateliers de co-création) :
{workshop_content}

BESOINS IDENTIFIÉS :
{final_needs}

QUICK WINS PROPOSÉS :
{final_quick_wins}

STRUCTURATION IA PROPOSÉE :
{final_structuration_ia}

INSTRUCTIONS D'ÉVALUATION :
1. Analyse la culture numérique de l'entreprise (mentions d'outils digitaux, compétences IA, ouverture au changement)
2. Évalue la gestion des données (qualité, centralisation, formats exploitables)
3. Identifie les processus automatisés existants (nombre et sophistication)
4. Analyse la complexité des besoins et solutions proposées

CRITÈRES D'ÉVALUATION :
- Échelle de 1 à 5 (1 = Débutant, 2 = Émergent, 3 = Intermédiaire, 4 = Avancé, 5 = Expert)
- Phrase résumant la situation avec les données, les outils numériques

Format de réponse :
Échelle: [1-5]
Phrase résumant: [phrase décrivant la maturité IA avec détails sur les données et outils numériques]
"""

GENERATE_RECOMMENDATIONS_PROMPT = """
Génère 4 recommandations clés personnalisées selon la maturité IA de l'entreprise :

MATURITÉ IA ÉVALUÉE :
{maturite_ia}

BESOINS IDENTIFIÉS :
{final_needs}

QUICK WINS PROPOSÉS :
{final_quick_wins}

STRUCTURATION IA PROPOSÉE :
{final_structuration_ia}

INSTRUCTIONS :
1. Génère 4 recommandations personnalisées selon la maturité IA évaluée
2. Adapte les recommandations au niveau de maturité de l'entreprise
3. Base-toi sur les besoins et cas d'usage identifiés
4. Sois concret et actionnable
5. Utilise le format : "1. [recommandation]", "2. [recommandation]", etc.

Génère les 4 recommandations en suivant exactement ce format :
1. [première recommandation personnalisée]
2. [deuxième recommandation personnalisée]
3. [troisième recommandation personnalisée]
4. [quatrième recommandation personnalisée]
"""

REGENERATE_RECOMMENDATIONS_PROMPT = """
Tu dois régénérer les recommandations en tenant compte du feedback utilisateur.

RECOMMANDATIONS PRÉCÉDENTES (REJETÉES) :
{rejected_recommendations}

FEEDBACK UTILISATEUR :
{recommendations_feedback}

RECOMMANDATIONS VALIDÉES (À CONSERVER) :
{validated_recommendations}

MATURITÉ IA ÉVALUÉE :
{maturite_ia}

BESOINS IDENTIFIÉS :
{final_needs}

QUICK WINS PROPOSÉS :
{final_quick_wins}

STRUCTURATION IA PROPOSÉE :
{final_structuration_ia}

INSTRUCTIONS :
1. Analyse le feedback utilisateur pour comprendre ce qui doit être modifié
2. Conserve les recommandations validées (ne les régénère pas)
3. Régénère uniquement les recommandations rejetées en tenant compte du feedback
4. Assure-toi d'avoir exactement 4 recommandations au total (validées + nouvelles)
5. Si le feedback indique qu'il manque des recommandations, génère-en de nouvelles
6. Adapte le ton et le contenu selon le feedback

Génère 4 recommandations au format structuré.
"""

EXTRACT_ENJEUX_CITATIONS_PROMPT = """
Extrait les citations pertinentes pour identifier les enjeux stratégiques de l'IA dans cette transcription.

TRANSCRIPTION :
{transcript_text}

INSTRUCTIONS :
1. Identifie les interventions qui mentionnent des enjeux stratégiques, des défis organisationnels, des transformations nécessaires
2. Focus sur : vision stratégique, défis majeurs, enjeux de transformation, besoins stratégiques
3. Exclut les citations purement opérationnelles ou techniques sans dimension stratégique
4. Pour chaque citation, indique le speaker, le contexte et l'horodatage si disponible

Extrait uniquement les citations qui sont pertinentes pour identifier les ENJEUX STRATÉGIQUES de l'IA.
"""

EXTRACT_MATURITE_CITATIONS_PROMPT = """
Extrait les citations pertinentes pour évaluer la maturité IA de l'entreprise dans cette transcription.

TRANSCRIPTION :
{transcript_text}

INSTRUCTIONS :
1. Identifie les interventions qui mentionnent :
   - Des outils digitaux utilisés (Excel, systèmes, logiciels, plateformes)
   - Des processus automatisés existants
   - La gestion des données (qualité, centralisation, formats)
   - La culture numérique (compétences IA, ouverture au changement, formation)
2. Pour chaque citation, classe-la selon le type d'information :
   - 'outils_digitaux' : mentions d'outils, logiciels, systèmes
   - 'processus_automatises' : processus déjà automatisés
   - 'gestion_donnees' : qualité, centralisation, formats des données
   - 'culture_numérique' : compétences, formation, ouverture au changement
3. Indique le speaker, le contexte et l'horodatage si disponible

Extrait uniquement les citations qui sont pertinentes pour évaluer la MATURITÉ IA.
"""

EXTRACT_WORKSHOP_ENJEUX_PROMPT = """
Extrait les informations pertinentes pour identifier les enjeux stratégiques depuis cet atelier.

DONNÉES ATELIER :
{workshop_data}

INSTRUCTIONS :
1. Identifie les cas d'usage qui révèlent des enjeux stratégiques
2. Focus sur les objectifs et gains qui indiquent des transformations majeures
3. Extrait les citations ou descriptions qui montrent des enjeux organisationnels ou stratégiques
4. Exclut les cas d'usage purement opérationnels sans dimension stratégique

Extrait les informations pertinentes pour les ENJEUX STRATÉGIQUES.
"""

EXTRACT_WORKSHOP_MATURITE_PROMPT = """
Extrait les informations pertinentes pour évaluer la maturité IA depuis cet atelier.

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
   - 'culture_numérique' : niveau de compréhension et d'ambition IA
3. Extrait les descriptions qui montrent la maturité actuelle

Extrait les informations pertinentes pour la MATURITÉ IA.
"""

WORD_REPORT_EXTRACTION_PROMPT = """
Extrais les données structurées depuis ce rapport Word généré.

RAPPORT WORD (texte extrait) :
{word_text}

INSTRUCTIONS :
1. Identifie la section "LES BESOINS IDENTIFIÉS" et extrait tous les besoins avec leurs citations
2. Identifie la section "LES CAS D'USAGES IA PRIORITAIRES" et extrais :
   - Les Quick Wins (famille "Quick Wins")
   - Les Structuration IA (famille "Structuration IA")
3. Pour chaque besoin, conserve : theme, quotes
4. Pour chaque cas d'usage, conserve : titre, description
5. Si le document a été modifié manuellement, adapte-toi à la structure actuelle

Extrais les données au format structuré.
"""

