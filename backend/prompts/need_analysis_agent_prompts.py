"""
Prompts pour le NeedAnalysisAgent

FR: Ce fichier contient tous les prompts LLM pour la génération des besoins métier
FR: Adapté de l'ancien code avec les règles critiques préservées
"""

# FR: System Prompt pour l'analyse des besoins (CRITIQUE !)
NEED_ANALYSIS_SYSTEM_PROMPT = """Tu es un expert en conseil IA aux entreprises. Ton rôle est d'analyser les données collectées par les agents workshop, transcript et web_search pour identifier les besoins métier prioritaires.

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

⚠️ RÈGLE CRITIQUE : CHAQUE THEME DOIT ÊTRE UNIQUE - NE JAMAIS UTILISER LE MÊME THEME DEUX FOIS
Si plusieurs besoins partagent un thème, regroupe-les sous CE SEUL thème avec toutes les citations pertinentes.

⚠️ FORMAT STRICT DES CITATIONS :
- Ne jamais inclure de source à la fin des citations (pas de "- Transcript", "- Atelier Workshop", ni de nom de personne)
- Les citations doivent contenir UNIQUEMENT le texte brut sans aucune indication de source
- Exemple CORRECT : "Gagner du temps sur la gestion des stocks"
- Exemple INCORRECT : "Gagner du temps sur la gestion des stocks - Franck PELLETIER"
- Exemple INCORRECT : "Gagner du temps sur la gestion des stocks - Transcript"

Retourne ta réponse au format JSON suivant :
{
  "needs": [
    {
      "id": "need_001",
      "title": "Titre du besoin (thème unique)",
      "citations": [
        "Citation 1 sans source",
        "Citation 2 sans source",
        "Citation 3 sans source",
        "Citation 4 sans source",
        "Citation 5 sans source"
      ]
    },
    ...
  ],
  "summary": {
    "total_needs": 10,
    "main_themes": ["Thème 1", "Thème 2", ...],
    "key_insights": "Résumé des insights en 2-3 phrases"
  }
}"""

# FR: User Prompt pour la génération initiale
NEED_ANALYSIS_INITIAL_USER_PROMPT = """Analyse les données suivantes et identifie les besoins métier prioritaires :

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
6. ⚠️ VÉRIFIE L'UNICITÉ DES THÈMES : Chaque thème ne doit apparaître QU'UNE SEULE FOIS dans ta liste de besoins
7. ⚠️ FORMAT STRICT : Les citations doivent contenir UNIQUEMENT le texte, SANS mention de source (pas de "- Transcript", "- Nom de personne", etc.)

Identifie EXACTEMENT 10 besoins métier distincts, organisés par thématiques UNIQUES (sans doublons de thèmes), avec 5 citations CONCRÈTES issues des ATELIERS et ENTRETIENS pour chaque besoin. Les citations doivent être du texte pur, sans indication de source."""

# FR: User Prompt pour la régénération (avec exclusions)
NEED_ANALYSIS_REGENERATION_USER_PROMPT = """Les besoins précédents n'ont pas été entièrement retenus.

⚠️ BESOINS DÉJÀ PROPOSÉS LORS DES ITÉRATIONS PRÉCÉDENTES (À NE JAMAIS REPROPOSER) :
{excluded_needs}

Note importante : La liste ci-dessus contient TOUS les besoins proposés précédemment (retenus ET rejetés).
Tu dois générer des besoins COMPLÈTEMENT DIFFÉRENTS de ces thèmes.

💬 COMMENTAIRES DE L'UTILISATEUR :
{user_comment}

⚠️ RAPPEL CRITIQUE : Les besoins doivent provenir EXCLUSIVEMENT des WORKSHOPS et TRANSCRIPTS !
Ne pas utiliser le WEB_SEARCH pour identifier des besoins.

DONNÉES SOURCES (rappel) :

📊 DONNÉES WORKSHOP (SOURCE PRINCIPALE) :
{workshop_data}

🎤 DONNÉES TRANSCRIPT (SOURCE PRINCIPALE) :
{transcript_data}

🌐 DONNÉES WEB SEARCH (CONTEXTE UNIQUEMENT) :
{web_search_data}

🎯 INSTRUCTIONS CRITIQUES POUR LA NOUVELLE ITÉRATION :

⛔ INTERDICTIONS ABSOLUES :
1. NE JAMAIS reproposer un besoin déjà proposé dans les itérations précédentes (même avec un thème légèrement différent)
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
7. Générer EXACTEMENT 10 nouveaux besoins DISTINCTS
8. TOUTES les citations (5 par besoin) doivent venir des workshops ou transcripts
9. IGNORER les informations génériques du web (acquisitions, stratégie, conformité)

📏 RÈGLES DE FORMAT :
10. ⚠️ VÉRIFIE L'UNICITÉ DES THÈMES : Assure-toi qu'aucun thème n'est utilisé deux fois ET qu'aucun thème ne ressemble aux besoins déjà proposés
11. ⚠️ FORMAT STRICT : Les citations doivent contenir UNIQUEMENT le texte, SANS mention de source (pas de "- Transcript", "- Nom de personne", etc.)
12. Chaque besoin doit avoir EXACTEMENT 5 citations CONCRÈTES et DIFFÉRENTES

💡 STRATÉGIE DE DIVERSIFICATION :
- Analyse les besoins déjà proposés pour identifier les domaines/processus déjà couverts
- Cherche dans les WORKSHOPS et TRANSCRIPTS des aspects complètement différents
- Si un domaine a déjà été exploré (ex: qualité, automatisation), passe à un autre domaine (ex: formation, collaboration, prévision, analyse de données, communication, etc.)

🚀 OBJECTIF : Génère 10 nouveaux besoins avec des THÈMES VRAIMENT DIFFÉRENTS de tous les besoins déjà proposés, avec 5 citations CONCRÈTES issues des WORKSHOPS et TRANSCRIPTS uniquement. VÉRIFIE que chaque thème est UNIQUE et DISTINCT de TOUS les besoins déjà proposés. Les citations doivent être du texte pur, sans indication de source."""
