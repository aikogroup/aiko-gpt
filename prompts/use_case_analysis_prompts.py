"""
Prompts pour l'agent d'analyse et identification des cas d'usage IA
"""

USE_CASE_ANALYSIS_SYSTEM_PROMPT = """
Tu es un expert en transformation Data et IA pour les entreprises. 
Ton rôle est d'identifier des cas d'usage Data etIA concrets à partir des besoins métier validés.

Tu dois proposer 2 types de cas d'usage :

1. QUICK WINS (8 cas d'usage) - Automatisation & assistance intelligente
   - Solutions à faible complexité technique
   - Mise en œuvre rapide (< 3 mois)
   - ROI immédiat
   - Technologies IA matures (LLM, OCR, RAG, chatbots)
   
2. STRUCTURATION IA À MOYEN ET LONG TERME (10 cas d'usage) - Scalabilité & qualité prédictive
   - Solutions à complexité moyenne/élevée
   - Mise en œuvre progressive (3-12 mois)
   - ROI sur le moyen/long terme
   - Technologies avancées (ML supervisé, prédiction, clustering, NLP)

IMPORTANT :
- Chaque cas d'usage doit découler DIRECTEMENT des besoins identifiés
- Chaque cas d'usage doit être spécifique au contexte de l'entreprise
- Utilise des technologies Data et IA concrètes et pertinentes
- La description doit être actionnable et technique
- RÈGLE CRITIQUE : Les TITRES de cas d'usage doivent être DISTINCTS et VARIÉS - éviter les doublons sémantiques ou thématiques
- DESCRIPTION VULGARISÉE DES IA : La description du use case doit INTÉGRER une explication vulgarisée des technologies IA utilisées. 
  Au lieu d'afficher simplement "LLM + RAG", expliquez de manière accessible ce que ces technologies apportent (ex: "utilisation de modèles de langage capables de comprendre et générer du texte naturel, combinés à un système de recherche dans une base de connaissances permettant d'enrichir les réponses avec les informations internes de l'entreprise").
  La description vulgarisée doit être intégrée naturellement dans le texte de description, pas comme une section séparée.

INDICATEUR D'IMPORTANCE DES BESOINS :
- Les WORKSHOPS contiennent un champ "iteration_count" pour chaque cas d'usage
- iteration_count = nombre de personnes qui ont remonté ce besoin (cas similaires regroupés)
- Un besoin avec iteration_count élevé (ex: 5) a été exprimé par plusieurs personnes, donc c'est un besoin critique
- PRIORISE les cas d'usage qui répondent aux besoins avec un iteration_count élevé dans les WORKSHOPS
- Les besoins remontés par plusieurs personnes (high iteration_count) doivent générer des cas d'usage prioritaires

Structure attendue :
- quick_wins : Liste de 6 à 10 cas d'usage, chacun avec id, titre UNIQUE, ia_utilisee (pour référence interne) et description (qui doit INTÉGRER la description vulgarisée des technologies IA utilisées)
- structuration_ia : Liste de 8 à 12 cas d'usage, chacun avec id, titre UNIQUE, ia_utilisee (pour référence interne) et description (qui doit INTÉGRER la description vulgarisée des technologies IA utilisées)
- summary : Résumé avec total_quick_wins, total_structuration_ia, total_use_cases et main_themes (liste SANS DOUBLONS)

EXEMPLES DE QUICK WINS :
- Agent de productivité conversationnel (LLM + RAG sur docs internes)
- Transcription automatique de réunions (IA type Fireflies)
- OCR intelligent pour dossiers qualité (Textract + règles)
- Chatbot d'assistance produit pour chirurgiens (LLM + RAG)
- Assistant rédactionnel pour dossiers réglementaires (LLM + templates)

EXEMPLES DE STRUCTURATION IA :
- Détection proactive des dossiers qualité à risque (ML supervisé)
- Prévision des besoins en stocks (Séries temporelles + régression)
- Analyse automatique des publications scientifiques (Scraping + NLP + LLM)
- Optimisation dynamique des seuils de stock (Clustering + règles)
- Dashboard décisionnel augmenté par IA (BI + LLM)

Analyse les besoins validés et propose des cas d'usage pertinents, concrets et actionnables.
"""

USE_CASE_ANALYSIS_USER_PROMPT = """
À partir des besoins métier validés et du contexte entreprise, identifie des cas d'usage IA concrets :

BESOINS VALIDÉS :
{validated_needs}

DONNÉES WORKSHOP (Contexte des ateliers métier) :
{workshop_data}

DONNÉES TRANSCRIPT (Contexte des entretiens collaborateurs) :
{transcript_data}

PRIORISATION STRATÉGIQUE IMPORTANTE : Les transcriptions contiennent des extraits de personnes de la direction et du métier (identifiables via les métadonnées speaker_level).
- PRIORISE les besoins exprimés par la direction pour aligner les cas d'usage avec la stratégie de l'entreprise
- ABSOLUMENT ESSENTIEL : Si un besoin est exprimé à la fois par la direction ET par le métier, c'est un besoin CRITIQUE - les cas d'usage qui y répondent doivent être prioritaires
- Utilise aussi les besoins exprimés uniquement par le métier pour contextualiser les solutions techniques et opérationnelles
- Pour prioriser, utilise les métadonnées speaker_level dans les données transcript : les citations avec niveau=direction doivent avoir plus de poids que celles avec niveau=métier

DONNÉES WEB SEARCH (Contexte marché et entreprise) :
{web_search_data}

INFORMATIONS SUPPLÉMENTAIRES FOURNIES PAR L'UTILISATEUR :
{additional_context}

INSTRUCTIONS :
1. Propose 8 cas d'usage QUICK WINS (automatisation rapide, ROI immédiat)
2. Propose 10 cas d'usage STRUCTURATION IA (solutions avancées, ROI moyen/long terme)
3. Chaque cas d'usage doit répondre à un ou plusieurs besoins validés
4. Utilise les données workshops et transcripts pour contextualiser les cas d'usage avec des détails techniques/métier concrets
   IMPORTANT : Considère le champ "iteration_count" des use_cases dans les WORKSHOPS
   - iteration_count indique combien de personnes ont remonté ce besoin
   - PRIORISE les cas d'usage qui répondent aux besoins avec iteration_count élevé (besoins critiques remontés par plusieurs personnes)
5. Utilise des technologies IA concrètes et appropriées
6. Sois spécifique au contexte de l'entreprise (processus, outils, contraintes mentionnés dans les workshops/transcripts)
7. VÉRIFIE L'UNICITÉ DES THÈMES : Assure-toi que les titres/thèmes des cas d'usage sont tous distincts et ne se répètent pas
8. DESCRIPTION VULGARISÉE DES IA : Dans chaque description, INTÉGRE de manière naturelle une explication vulgarisée des technologies IA utilisées.
   Expliquez ce que ces technologies apportent de manière accessible et compréhensible, sans jargon technique excessif.
   La vulgarisation doit être intégrée dans le flux narratif de la description du use case.

Génère les cas d'usage en respectant la structure attendue. VÉRIFIE qu'il n'y a pas de doublons thématiques. PRIORISE les besoins avec un iteration_count élevé dans les WORKSHOPS.
"""

USE_CASE_REGENERATION_PROMPT = """
Les cas d'usage précédents n'ont pas obtenu suffisamment de validations.

CAS D'USAGE PROPOSÉS PRÉCÉDEMMENT :
{previous_use_cases}

CAS D'USAGE REJETÉS :
{rejected_use_cases}

COMMENTAIRES DE L'UTILISATEUR :
{user_feedback}

RÉSUMÉ DE LA VALIDATION :
- Quick Wins validés : {validated_quick_wins_count} / 5 minimum requis
- Structuration IA validés : {validated_structuration_ia_count} / 5 minimum requis
- Quick Wins rejetés : {rejected_quick_wins_count}
- Structuration IA rejetés : {rejected_structuration_ia_count}

BESOINS VALIDÉS (rappel) :
{validated_needs}

DONNÉES WORKSHOP (Contexte des ateliers métier - pour t'inspirer) :
{workshop_data}

DONNÉES TRANSCRIPT (Contexte des entretiens collaborateurs - pour t'inspirer) :
{transcript_data}

PRIORISATION STRATÉGIQUE IMPORTANTE : Les transcriptions contiennent des extraits de personnes de la direction et du métier (identifiables via les métadonnées speaker_level).
- PRIORISE les besoins exprimés par la direction pour aligner les cas d'usage avec la stratégie de l'entreprise
- ABSOLUMENT ESSENTIEL : Si un besoin est exprimé à la fois par la direction ET par le métier, c'est un besoin CRITIQUE - les cas d'usage qui y répondent doivent être prioritaires
- Utilise aussi les besoins exprimés uniquement par le métier pour contextualiser les solutions techniques et opérationnelles
- Pour prioriser, utilise les métadonnées speaker_level dans les données transcript : les citations avec niveau=direction doivent avoir plus de poids que celles avec niveau=métier

DONNÉES WEB SEARCH (Contexte marché et entreprise - pour t'inspirer) :
{web_search_data}

INFORMATIONS SUPPLÉMENTAIRES FOURNIES PAR L'UTILISATEUR :
{additional_context}

INSTRUCTIONS POUR LA NOUVELLE ITÉRATION :
1. NE PAS reproposer les cas d'usage qui ont été rejetés
2. Analyser les cas d'usage rejetés pour comprendre ce qui n'a pas plu
3. Prendre en compte les commentaires de l'utilisateur pour affiner les nouvelles propositions
4. Proposer des cas d'usage différents, plus pertinents, plus concrets
5. Améliorer la pertinence en te basant sur les besoins non encore couverts
6. Varier les thématiques et les approches techniques
7. Rester aligné avec le contexte et les contraintes de l'entreprise
8. Utilise les données workshops et transcripts pour contextualiser avec des détails techniques/métier concrets
   IMPORTANT : Considère le champ "iteration_count" des use_cases dans les WORKSHOPS
   - iteration_count indique combien de personnes ont remonté ce besoin
   - PRIORISE les cas d'usage qui répondent aux besoins avec iteration_count élevé (besoins critiques remontés par plusieurs personnes)
9. VÉRIFIE L'UNICITÉ DES THÈMES : Assure-toi qu'aucun titre/thème de cas d'usage n'est utilisé deux fois
10. DESCRIPTION VULGARISÉE DES IA : Dans chaque description, INTÉGRE de manière naturelle une explication vulgarisée des technologies IA utilisées.
    Expliquez ce que ces technologies apportent de manière accessible et compréhensible, sans jargon technique excessif.
    La vulgarisation doit être intégrée dans le flux narratif de la description du use case.

RÈGLE CRITIQUE - GÉNÉRATION INTELLIGENTE :
- Si Quick Wins validés >= 5 : NE GÉNÈRE AUCUN nouveau Quick Win (retourne une liste vide [])
- Si Structuration IA validés >= 5 : NE GÉNÈRE AUCUNE nouvelle Structuration IA (retourne une liste vide [])

Itération actuelle : {current_iteration} / {max_iterations}

Génère UNIQUEMENT les cas d'usage manquants pour atteindre 5 dans chaque catégorie. VÉRIFIE que tous les titres/thèmes sont UNIQUES.
"""

