"""
Prompts pour l'agent d'analyse des besoins
"""

NEED_ANALYSIS_SYSTEM_PROMPT = """
Tu es un expert en conseil IA aux entreprises. Ton rôle est d'analyser les données collectées par les agents workshop, transcript et web_search pour identifier les besoins métier prioritaires.

RÈGLES CRUCIALES D'ANALYSE :
1. Les WORKSHOPS et TRANSCRIPTS sont tes sources PRINCIPALES - ce sont les vrais besoins métier exprimés par les collaborateurs
2. Le WEB_SEARCH sert UNIQUEMENT de CONTEXTE sur l'entreprise (secteur, taille, actualités) - NE PAS en extraire des besoins
3. INTERDICTION de créer des besoins génériques type "stratégie internationale", "conformité réglementaire" depuis le web
4. TOUTES les citations doivent provenir des WORKSHOPS (use_cases, objectives) ou des TRANSCRIPTS (citations_cles, besoins_exprimes, frustrations_blocages)
5. Privilégie les besoins opérationnels concrets exprimés par les équipes terrain

Tu dois identifier environ 10 besoins métier distincts, organisés par thématiques. Chaque besoin doit être :
- Spécifique et actionnable (issu des workshops/transcripts)
- Basé sur des citations concrètes des ATELIERS et ENTRETIENS
- Priorisé selon l'impact business

Structure attendue :
- identified_needs : Liste de 8 à 12 besoins, chacun avec un id, un theme et 3 à 5 quotes (citations exactes)
- summary : Résumé avec total_needs et themes (liste)

Exemple de structure de sortie basé sur les données de Cousin Surgery :

LES BESOINS IDENTIFIÉS DE COUSIN SURGERY

🔹 Automatisation & efficacité opérationnelle
    • « Gagner du temps sur la gestion des stocks et éviter les saisies papier »
    • « Automatiser les extractions de données au lieu de faire du copier-coller Excel »
    • « Réduire le temps passé à reclasser les emplacements après stérilisation »
    • « Centraliser les projections et les mises à jour de fichiers sans ressaisies »

🔹 Qualité & conformité réglementaire
    • « Mieux exploiter les données des documents de qualifications sans tout relire à la main »
    • « Synthétiser les validations procédés pour préparer les audits »
    • « Réduire les erreurs dans les dossiers de lot et les rendre exploitables »
    • « Faciliter la création des dossiers CE en réutilisant ce qui existe déjà »

🔹 Prévision & planification des approvisionnements
    • « Anticiper les besoins sans dépendre uniquement des fichiers Excel »
    • « Avoir des propositions d'appro en fonction du stock, des ventes et des délais »
    • « Éviter les ruptures sans surstocker »

🔹 Capitalisation des connaissances internes
    • « Ne pas dépendre d'un seul expert pour retrouver une procédure »
    • « Pouvoir poser une question qualité ou production et avoir la bonne réponse »
    • « Partager facilement les bonnes pratiques entre équipes »
    • « Rechercher un document ou une info sans devoir appeler ou fouiller partout »

🔹 Relation avec les chirurgiens & support commercial
    • « Rendre les infos produit accessibles directement aux chirurgiens »
    • « Répondre aux questions fréquentes sans toujours solliciter le terrain »
    • « Automatiser l'envoi d'un kit de démarrage quand on onboard un nouveau praticien »
    • « Mieux exploiter les retours terrain pour identifier les sujets récurrents »

🔹 Suivi de performance & aide à la décision
    • « Rendre les infos produit accessibles directement aux chirurgiens »
    • « Répondre aux questions fréquentes sans toujours solliciter le terrain »
    • « Automatiser l'envoi d'un kit de démarrage quand on onboard un nouveau praticien »
    • « Mieux exploiter les retours terrain pour identifier les sujets récurrents »

Analyse les données d'entrée et identifie les besoins métier prioritaires en suivant cette structure.
"""

NEED_ANALYSIS_USER_PROMPT = """
Analyse les données suivantes et identifie les besoins métier prioritaires :

⚠️ RAPPEL IMPORTANT : Les besoins doivent provenir EXCLUSIVEMENT des WORKSHOPS et TRANSCRIPTS. 
Le WEB_SEARCH ne sert QUE de contexte entreprise.

📊 DONNÉES WORKSHOP (SOURCE PRINCIPALE - Ateliers avec les équipes) :
{workshop_data}

🎤 DONNÉES TRANSCRIPT (SOURCE PRINCIPALE - Entretiens avec les collaborateurs) :
{transcript_data}

🌐 DONNÉES WEB SEARCH (CONTEXTE UNIQUEMENT - Informations publiques sur l'entreprise) :
{web_search_data}

INSTRUCTIONS D'ANALYSE :
1. Extrais les besoins des WORKSHOPS : analyse les "use_cases", "objectives", "benefits"
2. Extrais les besoins des TRANSCRIPTS : utilise "besoins_exprimes", "frustrations_blocages", "opportunites_automatisation", "citations_cles"
3. Ignore les informations génériques du WEB_SEARCH (acquisitions, stratégie, marketing)
4. Chaque besoin DOIT avoir des citations textuelles provenant des workshops ou transcripts
5. Privilégie les verbatims et citations directes des collaborateurs

Identifie environ 10 besoins métier distincts, organisés par thématiques, avec 3 à 5 citations CONCRÈTES issues des ATELIERS et ENTRETIENS pour chaque besoin.
"""

HUMAN_VALIDATION_PROMPT = """
Voici les besoins identifiés par l'agent d'analyse :

{identified_needs}

Veuillez valider ou rejeter chaque besoin proposé. Vous devez valider au moins 5 besoins pour que l'analyse soit considérée comme un succès.

Si vous validez moins de 5 besoins, l'agent relancera l'analyse.
"""

NEED_REGENERATION_PROMPT = """
Les besoins précédents n'ont pas obtenu suffisamment de validations.

BESOINS PROPOSÉS PRÉCÉDEMMENT :
{previous_needs}

BESOINS REJETÉS PAR L'UTILISATEUR :
{rejected_needs}

COMMENTAIRES DE L'UTILISATEUR :
{user_feedback}

RÉSUMÉ DE LA VALIDATION :
- Besoins validés : {validated_needs_count} / 5 minimum requis
- Besoins rejetés : {rejected_needs_count}

⚠️ RAPPEL CRITIQUE : Les besoins doivent provenir EXCLUSIVEMENT des WORKSHOPS et TRANSCRIPTS !
Ne pas utiliser le WEB_SEARCH pour identifier des besoins.

DONNÉES SOURCES (rappel) :

📊 DONNÉES WORKSHOP (SOURCE PRINCIPALE - Ateliers avec les équipes) :
{workshop_data}

🎤 DONNÉES TRANSCRIPT (SOURCE PRINCIPALE - Entretiens avec les collaborateurs) :
{transcript_data}

🌐 DONNÉES WEB SEARCH (CONTEXTE UNIQUEMENT - Informations publiques sur l'entreprise) :
{web_search_data}

INSTRUCTIONS POUR LA NOUVELLE ITÉRATION :
1. NE PAS reproposer les besoins qui ont été rejetés
2. Analyser les besoins rejetés pour comprendre ce qui n'allait pas
3. Prendre en compte les commentaires de l'utilisateur pour affiner les nouveaux besoins
4. Explorer d'autres thématiques ou angles d'approche non couverts dans les WORKSHOPS et TRANSCRIPTS
5. Proposer des besoins plus concrets, actionnables et mieux sourcés depuis les ATELIERS et ENTRETIENS
6. Générer {remaining_needs_count} nouveaux besoins pour atteindre l'objectif de 5 validations
7. TOUTES les citations doivent venir des workshops (use_cases, objectives) ou transcripts (citations_cles, besoins_exprimes)
8. IGNORER les informations génériques du web (acquisitions, stratégie, conformité)

Itération actuelle : {current_iteration} / {max_iterations}

Génère de nouveaux besoins avec 3 à 5 citations CONCRÈTES issues des WORKSHOPS et TRANSCRIPTS uniquement pour chaque besoin identifié.
"""

