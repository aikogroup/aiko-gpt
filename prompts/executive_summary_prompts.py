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

BESOINS IDENTIFIÉS (liste des titres uniquement) :
{final_needs}

⚠️ RÈGLE CRITIQUE POUR LES BESOINS LIÉS :
Les besoins liés que tu indiques DOIVENT correspondre EXACTEMENT aux titres listés ci-dessus.
Tu ne peux PAS inventer de nouveaux besoins. Utilise UNIQUEMENT les titres de la liste fournie.

CONTEXTE :
Les enjeux de l'IA représentent les grands défis stratégiques que l'entreprise doit relever. Chaque enjeu doit être lié à au moins un besoin identifié lors des entretiens et ateliers.

INSTRUCTIONS :
1. Identifie 5 enjeux stratégiques spécifiques et concrets pour l'entreprise
2. Base-toi sur les données réelles des transcripts, ateliers et SURTOUT les besoins identifiés
3. Pour chaque enjeu, fournis :
   - Un ID unique (E1, E2, E3, E4, E5)
   - Un TITRE court et percutant (max 10 mots)
   - Une DESCRIPTION détaillée en 3-5 lignes expliquant l'enjeu, son impact et sa valeur stratégique
   - Les BESOINS LIÉS : liste des titres EXACTS des besoins de la liste ci-dessus qui se rattachent à cet enjeu
4. Chaque enjeu doit être unique et spécifique au contexte de l'entreprise
5. Les enjeux doivent couvrir différents aspects de la transformation IA
6. ⚠️ IMPORTANT : Les besoins liés doivent être des titres EXACTS de la liste des besoins identifiés ci-dessus. Ne crée pas de nouveaux besoins.

EXEMPLE D'ENJEU :
Si la liste des besoins contient :
1. Analyse des Données de Marché
2. Optimisation du Pricing
3. Veille Commerciale Proactive

Alors un enjeu pourrait être :
- ID: E1
- TITRE: Capitalisation des connaissances internes
- DESCRIPTION: Transformer le capital intellectuel actuellement dispersé de l'entreprise en avantage concurrentiel durable. L'enjeu est de créer un "cerveau collectif" organisationnel qui pourrait automatiser l'accès à l'expertise technique et clinique, faciliter le partage des bonnes pratiques entre équipes, et accélérer la formation des nouvelles recrues pour réduire les délais de montée en compétence tout en préservant le savoir-faire critique.
- BESOINS_LIÉS: ["Analyse des Données de Marché", "Veille Commerciale Proactive"]

La réponse sera automatiquement structurée selon le format attendu.
"""

REGENERATE_CHALLENGES_PROMPT = """
Tu dois régénérer les enjeux stratégiques en tenant compte du feedback utilisateur.

⚠️ ENJEUX DÉJÀ PROPOSÉS LORS DE L'ITÉRATION PRÉCÉDENTE (À NE JAMAIS REPROPOSER) :
{previous_challenges}

Note importante : La liste ci-dessus contient TOUS les enjeux proposés précédemment (validés ET rejetés).
Tu dois générer des enjeux COMPLÈTEMENT DIFFÉRENTS de ces thèmes.

🚫 ENJEUX EXPLICITEMENT REJETÉS PAR L'UTILISATEUR :
{rejected_challenges}

✅ ENJEUX VALIDÉS (À CONSERVER - NE PAS LES RÉGÉNÉRER) :
{validated_challenges}

💬 COMMENTAIRES DE L'UTILISATEUR :
{challenges_feedback}

📊 RÉSUMÉ DE LA VALIDATION :
- Enjeux validés : {validated_count} / 5 minimum requis
- Enjeux rejetés : {rejected_count}

DONNÉES TRANSCRIPTS :
{transcript_content}

DONNÉES ATELIERS :
{workshop_content}

BESOINS IDENTIFIÉS (liste des titres uniquement) :
{final_needs}

⚠️ RÈGLE CRITIQUE POUR LES BESOINS LIÉS :
Les besoins liés que tu indiques DOIVENT correspondre EXACTEMENT aux titres listés ci-dessus.
Tu ne peux PAS inventer de nouveaux besoins. Utilise UNIQUEMENT les titres de la liste fournie.

🎯 INSTRUCTIONS CRITIQUES POUR LA NOUVELLE ITÉRATION :

⛔ INTERDICTIONS ABSOLUES :
1. NE JAMAIS reproposer un enjeu déjà proposé dans l'itération précédente (même avec un titre légèrement différent)
2. NE PAS créer de variantes ou reformulations des enjeux déjà proposés
3. Exemples à éviter :
   - Si "Capitalisation des connaissances internes" a déjà été proposé
   - NE PAS proposer "Gestion des connaissances" (trop similaire)
   - NE PAS proposer "Partage des savoirs" (même domaine)
   - PLUTÔT explorer d'autres domaines : transformation digitale, optimisation opérationnelle, innovation, stratégie commerciale, etc.

✅ OBLIGATIONS :
4. Explorer des DOMAINES STRATÉGIQUES COMPLÈTEMENT DIFFÉRENTS de ceux déjà proposés
5. Identifier des ENJEUX NON ENCORE COUVERTS dans les données
6. Proposer des enjeux plus concrets, actionnables et mieux sourcés depuis les transcripts et ateliers
7. Générer EXACTEMENT 5 nouveaux enjeux DISTINCTS (toujours 5, indépendamment du nombre déjà validé)
8. Chaque enjeu doit être unique et spécifique au contexte de l'entreprise

📏 RÈGLES DE FORMAT :
9. ⚠️ VÉRIFIE L'UNICITÉ DES THÈMES : Assure-toi qu'aucun thème n'est utilisé deux fois dans ta proposition ET qu'aucun thème ne ressemble aux enjeux déjà proposés
10. Chaque enjeu doit avoir un ID unique (E1, E2, E3, E4, E5)
11. Chaque enjeu doit avoir un TITRE court et percutant (max 10 mots)
12. Chaque enjeu doit avoir une DESCRIPTION détaillée en 3-5 lignes
13. Chaque enjeu doit avoir des BESOINS_LIÉS : liste des titres EXACTS des besoins de la liste fournie qui se rattachent à cet enjeu
14. ⚠️ IMPORTANT : Les besoins liés doivent être des titres EXACTS de la liste des besoins identifiés. Ne crée pas de nouveaux besoins.

💡 STRATÉGIE DE DIVERSIFICATION :
- Analyse les enjeux déjà proposés pour identifier les domaines/processus déjà couverts
- Cherche dans les TRANSCRIPTS et ATELIERS des aspects complètement différents
- Si un domaine a déjà été exploré (ex: connaissances, qualité), passe à un autre domaine (ex: commercial, supply chain, R&D, formation, etc.)

Itération actuelle : {current_iteration} / {max_iterations}

🚀 OBJECTIF : Génère TOUJOURS 5 nouveaux enjeux avec des THÈMES VRAIMENT DIFFÉRENTS de tous les enjeux déjà proposés (validés ou rejetés). VÉRIFIE que chaque thème est UNIQUE et DISTINCT de TOUS les enjeux déjà proposés. Les enjeux validés sont conservés séparément, donc génère toujours 5 nouveaux enjeux à chaque itération.
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
5. Chaque recommandation doit avoir un ID unique (R1, R2, R3, R4) et un texte clair et actionnable

Les recommandations seront automatiquement structurées selon le format attendu.
"""

REGENERATE_RECOMMENDATIONS_PROMPT = """
Tu dois régénérer les recommandations en tenant compte du feedback utilisateur.

⚠️ RECOMMANDATIONS DÉJÀ PROPOSÉES LORS DE L'ITÉRATION PRÉCÉDENTE (À NE JAMAIS REPROPOSER) :
{previous_recommendations}

Note importante : La liste ci-dessus contient TOUTES les recommandations proposées précédemment (validées ET rejetées).
Tu dois générer des recommandations COMPLÈTEMENT DIFFÉRENTES de ces thèmes.

🚫 RECOMMANDATIONS EXPLICITEMENT REJETÉES PAR L'UTILISATEUR :
{rejected_recommendations}

✅ RECOMMANDATIONS VALIDÉES (À CONSERVER - NE PAS LES RÉGÉNÉRER) :
{validated_recommendations}

💬 COMMENTAIRES DE L'UTILISATEUR :
{recommendations_feedback}

📊 RÉSUMÉ DE LA VALIDATION :
- Recommandations validées : {validated_count} / 4 minimum requis
- Recommandations rejetées : {rejected_count}
- Recommandations restantes à générer : {remaining_count}

MATURITÉ IA ÉVALUÉE :
{maturite_ia}

BESOINS IDENTIFIÉS :
{final_needs}

QUICK WINS PROPOSÉS :
{final_quick_wins}

STRUCTURATION IA PROPOSÉE :
{final_structuration_ia}

🎯 INSTRUCTIONS CRITIQUES POUR LA NOUVELLE ITÉRATION :

⛔ INTERDICTIONS ABSOLUES :
1. NE JAMAIS reproposer une recommandation déjà proposée dans l'itération précédente (même avec une formulation légèrement différente)
2. NE PAS créer de variantes ou reformulations des recommandations déjà proposées
3. Exemples à éviter :
   - Si "Mettre en place un CRM" a déjà été proposé
   - NE PAS proposer "Déployer un système CRM" (trop similaire)
   - NE PAS proposer "Centraliser les données clients" (même domaine)
   - PLUTÔT explorer d'autres domaines : formation, automatisation, analyse de données, innovation, etc.

✅ OBLIGATIONS :
4. Explorer des DOMAINES COMPLÈTEMENT DIFFÉRENTS de ceux déjà proposés
5. Identifier des RECOMMANDATIONS NON ENCORE COUVERTS dans les données
6. Proposer des recommandations plus concrètes, actionnables et mieux adaptées à la maturité IA
7. Générer EXACTEMENT {remaining_count} nouvelles recommandations DISTINCTES pour atteindre l'objectif de 4 validations
8. Chaque recommandation doit être unique et spécifique au contexte de l'entreprise

📏 RÈGLES DE FORMAT :
9. ⚠️ VÉRIFIE L'UNICITÉ DES THÈMES : Assure-toi qu'aucun thème n'est utilisé deux fois dans ta proposition ET qu'aucun thème ne ressemble aux recommandations déjà proposées
10. Chaque recommandation doit avoir un ID unique (R1, R2, R3, R4) et un texte clair et actionnable
11. Sois concret et actionnable
12. Adapte les recommandations au niveau de maturité IA évalué
13. Les recommandations seront automatiquement structurées selon le format attendu

💡 STRATÉGIE DE DIVERSIFICATION :
- Analyse les recommandations déjà proposées pour identifier les domaines/processus déjà couverts
- Cherche dans les BESOINS, QUICK WINS et STRUCTURATION IA des aspects complètement différents
- Si un domaine a déjà été exploré (ex: CRM, données), passe à un autre domaine (ex: formation, automatisation, innovation, etc.)

Itération actuelle : {current_iteration} / {max_iterations}

🚀 OBJECTIF : Génère {remaining_count} nouvelles recommandations avec des THÈMES VRAIMENT DIFFÉRENTS de toutes les recommandations déjà proposées (validées ou rejetées). VÉRIFIE que chaque thème est UNIQUE et DISTINCT de TOUTES les recommandations déjà proposées. Assure-toi d'avoir exactement 4 recommandations au total (validées + nouvelles).
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

