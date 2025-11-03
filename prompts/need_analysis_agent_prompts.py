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

⚠️ INDICATEUR D'IMPORTANCE : Les WORKSHOPS contiennent un champ "iteration_count" pour chaque cas d'usage
- iteration_count = nombre de personnes qui ont remonté ce besoin (cas similaires regroupés)
- Un besoin avec iteration_count élevé (ex: 5) indique qu'il a été exprimé par plusieurs personnes, donc c'est un besoin critique
- PRIORISE les besoins avec un iteration_count élevé dans ton analyse

Tu dois identifier environ 10 besoins métier distincts, organisés par thématiques. Chaque besoin doit être :
- Spécifique et actionnable (issu des workshops/transcripts)
- Basé sur des citations concrètes des ATELIERS et ENTRETIENS
- Priorisé selon l'impact business ET l'iteration_count (besoins remontés par plusieurs personnes = plus prioritaires)

⚠️ RÈGLE CRITIQUE : CHAQUE THEME DOIT ÊTRE UNIQUE - NE JAMAIS UTILISER LE MÊME THEME DEUX FOIS
Si plusieurs besoins partagent un thème, regroupe-les sous CE SEUL thème avec toutes les citations pertinentes.

Structure attendue :
- identified_needs : Liste de 8 à 12 besoins, chacun avec un id, un theme UNIQUE et 3 à 5 quotes (citations exactes)
- summary : Résumé avec total_needs et themes (liste SANS DOUBLONS)

⚠️ FORMAT STRICT DES CITATIONS :
- Ne jamais inclure de source à la fin des citations (pas de "- Transcript", "- Atelier Workshop", ni de nom de personne)
- Les citations doivent contenir UNIQUEMENT le texte brut sans aucune indication de source
- Exemple CORRECT : "Gagner du temps sur la gestion des stocks"
- Exemple INCORRECT : "Gagner du temps sur la gestion des stocks - Franck PELLETIER"
- Exemple INCORRECT : "Gagner du temps sur la gestion des stocks - Transcript"

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

⚠️ PRIORISATION STRATÉGIQUE IMPORTANTE : Les transcriptions contiennent des extraits de personnes de la direction et du métier (identifiables via les métadonnées speaker_level).
- PRIORISE les besoins exprimés par la direction (stratégie, vision, enjeux business globaux) pour assurer la cohérence stratégique
- ABSOLUMENT ESSENTIEL : Si un besoin est exprimé à la fois par la direction ET par le métier, c'est un besoin CRITIQUE - tu DOIS l'inclure et le mettre en avant
- Utilise aussi les besoins exprimés uniquement par le métier (besoins opérationnels, problèmes terrain)
- Pour prioriser, utilise les métadonnées speaker_level dans les données transcript : les citations avec niveau=direction doivent avoir plus de poids que celles avec niveau=métier

🌐 DONNÉES WEB SEARCH (CONTEXTE UNIQUEMENT - Informations publiques sur l'entreprise) :
{web_search_data}

💡 INFORMATIONS SUPPLÉMENTAIRES FOURNIES PAR L'UTILISATEUR :
{additional_context}

INSTRUCTIONS D'ANALYSE :
1. Extrais les besoins des WORKSHOPS : analyse les "use_cases", "objectives", "benefits"
   ⚠️ IMPORTANT : Considère le champ "iteration_count" de chaque use_case des WORKSHOPS
   - iteration_count indique combien de personnes ont remonté ce besoin
   - Un besoin avec iteration_count élevé est plus critique et doit être priorisé
2. Extrais les besoins des TRANSCRIPTS : utilise "besoins_exprimes", "frustrations_blocages", "opportunites_automatisation", "citations_cles"
3. Ignore les informations génériques du WEB_SEARCH (acquisitions, stratégie, marketing)
4. Chaque besoin DOIT avoir des citations textuelles provenant des workshops ou transcripts
5. Privilégie les verbatims et citations directes des collaborateurs
6. ⚠️ VÉRIFIE L'UNICITÉ DES THÈMES : Chaque thème ne doit apparaître QU'UNE SEULE FOIS dans ta liste de besoins
7. ⚠️ FORMAT STRICT : Les citations doivent contenir UNIQUEMENT le texte, SANS mention de source (pas de "- Transcript", "- Nom de personne", etc.)
8. PRIORISATION : Les besoins remontés par plusieurs personnes (high iteration_count dans workshops) sont plus importants

Identifie environ 10 besoins métier distincts, organisés par thématiques UNIQUES (sans doublons de thèmes), avec 3 à 5 citations CONCRÈTES issues des ATELIERS et ENTRETIENS pour chaque besoin. Les citations doivent être du texte pur, sans indication de source. PRIORISE les besoins avec un iteration_count élevé dans les WORKSHOPS.
"""

HUMAN_VALIDATION_PROMPT = """
Voici les besoins identifiés par l'agent d'analyse :

{identified_needs}

Veuillez valider ou rejeter chaque besoin proposé. Vous devez valider au moins 5 besoins pour que l'analyse soit considérée comme un succès.

Si vous validez moins de 5 besoins, l'agent relancera l'analyse.
"""

NEED_REGENERATION_PROMPT = """
Les besoins précédents n'ont pas obtenu suffisamment de validations.

⚠️ BESOINS DÉJÀ PROPOSÉS LORS DE L'ITÉRATION PRÉCÉDENTE (À NE JAMAIS REPROPOSER) :
{previous_needs}

Note importante : La liste ci-dessus contient TOUS les besoins proposés précédemment (validés ET rejetés).
Tu dois générer des besoins COMPLÈTEMENT DIFFÉRENTS de ces thèmes.

🚫 BESOINS EXPLICITEMENT REJETÉS PAR L'UTILISATEUR :
{rejected_needs}

💬 COMMENTAIRES DE L'UTILISATEUR :
{user_feedback}

📊 RÉSUMÉ DE LA VALIDATION :
- Besoins validés : {validated_needs_count} / 5 minimum requis
- Besoins rejetés : {rejected_needs_count}
- Besoins restants à générer : {remaining_needs_count}

⚠️ RAPPEL CRITIQUE : Les besoins doivent provenir EXCLUSIVEMENT des WORKSHOPS et TRANSCRIPTS !
Ne pas utiliser le WEB_SEARCH pour identifier des besoins.

DONNÉES SOURCES (rappel) :

📊 DONNÉES WORKSHOP (SOURCE PRINCIPALE - Ateliers avec les équipes) :
{workshop_data}

🎤 DONNÉES TRANSCRIPT (SOURCE PRINCIPALE - Entretiens avec les collaborateurs) :
{transcript_data}

⚠️ PRIORISATION STRATÉGIQUE IMPORTANTE : Les transcriptions contiennent des extraits de personnes de la direction et du métier (identifiables via les métadonnées speaker_level).
- PRIORISE les besoins exprimés par la direction (stratégie, vision, enjeux business globaux) pour assurer la cohérence stratégique
- ABSOLUMENT ESSENTIEL : Si un besoin est exprimé à la fois par la direction ET par le métier, c'est un besoin CRITIQUE - tu DOIS l'inclure et le mettre en avant
- Utilise aussi les besoins exprimés uniquement par le métier (besoins opérationnels, problèmes terrain)
- Pour prioriser, utilise les métadonnées speaker_level dans les données transcript : les citations avec niveau=direction doivent avoir plus de poids que celles avec niveau=métier

🌐 DONNÉES WEB SEARCH (CONTEXTE UNIQUEMENT - Informations publiques sur l'entreprise) :
{web_search_data}

💡 INFORMATIONS SUPPLÉMENTAIRES FOURNIES PAR L'UTILISATEUR :
{additional_context}

🎯 INSTRUCTIONS CRITIQUES POUR LA NOUVELLE ITÉRATION :

⛔ INTERDICTIONS ABSOLUES :
1. NE JAMAIS reproposer un besoin déjà proposé dans l'itération précédente (même avec un thème légèrement différent)
2. NE PAS créer de variantes ou reformulations des besoins déjà proposés
3. Exemples à éviter :
   - Si "Automatisation des processus de contrôle qualité" a déjà été proposé
   - NE PAS proposer "Automatisation des contrôles qualité" (trop similaire)
   - NE PAS proposer "Optimisation du contrôle qualité" (même domaine)
   - PLUTÔT explorer d'autres domaines : R&D, commercial, supply chain, RH, etc.

✅ OBLIGATIONS :
4. Explorer des DOMAINES MÉTIER COMPLÈTEMENT DIFFÉRENTS de ceux déjà proposés
5. Identifier des PROCESSUS ou SERVICES NON ENCORE COUVERTS dans les workshops/transcripts
6. Proposer des besoins plus concrets, actionnables et mieux sourcés depuis les ATELIERS et ENTRETIENS
7. Générer EXACTEMENT {remaining_needs_count} nouveaux besoins DISTINCTS pour atteindre l'objectif de 5 validations
8. TOUTES les citations doivent venir des workshops (use_cases, objectives) ou transcripts (citations_cles, besoins_exprimes, frustrations_blocages, opportunites_automatisation)
9. IGNORER les informations génériques du web (acquisitions, stratégie, conformité)

📏 RÈGLES DE FORMAT :
10. ⚠️ VÉRIFIE L'UNICITÉ DES THÈMES : Assure-toi qu'aucun thème n'est utilisé deux fois dans ta proposition ET qu'aucun thème ne ressemble aux besoins déjà proposés
11. ⚠️ FORMAT STRICT : Les citations doivent contenir UNIQUEMENT le texte, SANS mention de source (pas de "- Transcript", "- Nom de personne", etc.)
12. Chaque besoin doit avoir 3 à 5 citations CONCRÈTES et DIFFÉRENTES

💡 STRATÉGIE DE DIVERSIFICATION :
- Analyse les besoins déjà proposés pour identifier les domaines/processus déjà couverts
- Cherche dans les WORKSHOPS et TRANSCRIPTS des aspects complètement différents
- Si un domaine a déjà été exploré (ex: qualité, automatisation), passe à un autre domaine (ex: formation, collaboration, prévision, analyse de données, communication, etc.)

Itération actuelle : {current_iteration} / {max_iterations}

🚀 OBJECTIF : Génère {remaining_needs_count} nouveaux besoins avec des THÈMES VRAIMENT DIFFÉRENTS de tous les besoins déjà proposés, avec 3 à 5 citations CONCRÈTES issues des WORKSHOPS et TRANSCRIPTS uniquement. VÉRIFIE que chaque thème est UNIQUE et DISTINCT de TOUS les besoins déjà proposés (validés ou rejetés). Les citations doivent être du texte pur, sans indication de source.
"""

