"""
Prompts pour le UseCaseAnalysisAgent

FR: Ce fichier contient tous les prompts LLM pour la génération des cas d'usage IA
FR: Adapté de l'ancien code avec les règles critiques préservées
"""

# FR: System Prompt pour l'analyse des cas d'usage
USE_CASE_ANALYSIS_SYSTEM_PROMPT = """Tu es un expert en transformation IA pour les entreprises. 
Ton rôle est d'identifier des cas d'usage IA concrets à partir des besoins métier validés.

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
- Utilise des technologies IA concrètes et pertinentes
- La description doit être actionnable et technique
- ⚠️ RÈGLE CRITIQUE : Les TITRES de cas d'usage doivent être DISTINCTS et VARIÉS - éviter les doublons sémantiques ou thématiques

EXEMPLES DE QUICK WINS :
- Agent de productivité conversationnel (LLM + RAG sur docs internes)
- Transcription automatique de réunions (IA type Fireflies)
- OCR intelligent pour dossiers qualité (Textract + règles)
- Chatbot d'assistance produit pour clients (LLM + RAG)
- Assistant rédactionnel pour dossiers réglementaires (LLM + templates)

EXEMPLES DE STRUCTURATION IA :
- Détection proactive des dossiers qualité à risque (ML supervisé)
- Prévision des besoins en stocks (Séries temporelles + régression)
- Analyse automatique des publications scientifiques (Scraping + NLP + LLM)
- Optimisation dynamique des seuils de stock (Clustering + règles)
- Dashboard décisionnel augmenté par IA (BI + LLM)

Retourne ta réponse au format JSON suivant :
{
  "quick_wins": [
    {
      "id": "qw_001",
      "title": "Titre du cas d'usage (unique)",
      "description": "Description détaillée et actionnable",
      "ai_technologies": ["LLM", "RAG", "OCR", ...]
    },
    ...
  ],
  "structuration_ia": [
    {
      "id": "sia_001",
      "title": "Titre du cas d'usage (unique)",
      "description": "Description détaillée et actionnable",
      "ai_technologies": ["ML supervisé", "Prédiction", "NLP", ...]
    },
    ...
  ],
  "summary": {
    "total_quick_wins": 8,
    "total_structuration_ia": 10,
    "total_use_cases": 18,
    "main_themes": ["Thème 1", "Thème 2", ...]
  }
}"""

# FR: User Prompt pour la génération initiale
USE_CASE_ANALYSIS_INITIAL_USER_PROMPT = """À partir des besoins métier validés et du contexte entreprise, identifie des cas d'usage IA concrets :

🎯 BESOINS VALIDÉS :
{validated_needs}

📊 DONNÉES WORKSHOP (Contexte des ateliers métier) :
{workshop_data}

🎤 DONNÉES TRANSCRIPT (Contexte des entretiens collaborateurs) :
{transcript_data}

🌐 DONNÉES WEB SEARCH (Contexte marché et entreprise) :
{web_search_data}

INSTRUCTIONS :
1. Propose EXACTEMENT 8 cas d'usage QUICK WINS (automatisation rapide, ROI immédiat)
2. Propose EXACTEMENT 10 cas d'usage STRUCTURATION IA (solutions avancées, ROI moyen/long terme)
3. Chaque cas d'usage doit répondre à un ou plusieurs besoins validés
4. Utilise les données workshops et transcripts pour contextualiser les cas d'usage avec des détails techniques/métier concrets
5. Utilise des technologies IA concrètes et appropriées
6. Sois spécifique au contexte de l'entreprise (processus, outils, contraintes mentionnés dans les workshops/transcripts)
7. ⚠️ VÉRIFIE L'UNICITÉ DES THÈMES : Assure-toi que les titres/thèmes des cas d'usage sont tous distincts et ne se répètent pas

Génère les cas d'usage en respectant la structure attendue. VÉRIFIE qu'il n'y a pas de doublons thématiques."""

# FR: User Prompt pour la régénération (avec exclusions)
USE_CASE_ANALYSIS_REGENERATION_USER_PROMPT = """Les cas d'usage précédents n'ont pas été entièrement retenus.

⚠️ CAS D'USAGE DÉJÀ PROPOSÉS (À NE JAMAIS REPROPOSER) :
{excluded_use_cases}

💬 COMMENTAIRES DE L'UTILISATEUR :
{user_comment}

RÉSUMÉ DE LA VALIDATION :
- Quick Wins validés : {validated_quick_wins_count}
- Structuration IA validés : {validated_structuration_ia_count}

🎯 BESOINS VALIDÉS (rappel) :
{validated_needs}

📊 DONNÉES WORKSHOP (Contexte) :
{workshop_data}

🎤 DONNÉES TRANSCRIPT (Contexte) :
{transcript_data}

🌐 DONNÉES WEB SEARCH (Contexte) :
{web_search_data}

🎯 INSTRUCTIONS CRITIQUES POUR LA NOUVELLE ITÉRATION :

⛔ INTERDICTIONS ABSOLUES :
1. NE JAMAIS reproposer un cas d'usage déjà proposé (même avec un titre légèrement différent)
2. NE PAS créer de variantes ou reformulations des cas d'usage déjà proposés
3. Explorer des APPLICATIONS IA COMPLÈTEMENT DIFFÉRENTES de celles déjà proposées

✅ OBLIGATIONS :
4. Identifier de NOUVEAUX PROCESSUS à automatiser ou améliorer par l'IA
5. Proposer des cas d'usage plus concrets et mieux reliés aux besoins validés
6. Générer EXACTEMENT {remaining_quick_wins_count} nouveaux Quick Wins (si besoin)
7. Générer EXACTEMENT {remaining_structuration_ia_count} nouvelles Structurations IA (si besoin)
8. ⚠️ RÈGLE INTELLIGENTE : Si >= 5 validés dans une catégorie, NE RIEN régénérer pour cette catégorie

📏 RÈGLES DE FORMAT :
9. ⚠️ VÉRIFIE L'UNICITÉ DES THÈMES : Assure-toi qu'aucun thème n'est utilisé deux fois ET qu'aucun thème ne ressemble aux cas d'usage déjà proposés
10. Chaque cas d'usage doit avoir des technologies IA CONCRÈTES et PERTINENTES

💡 STRATÉGIE DE DIVERSIFICATION :
- Analyse les cas d'usage déjà proposés pour identifier les applications déjà couvertes
- Cherche dans les BESOINS VALIDÉS des aspects complètement différents
- Si un type d'application a déjà été exploré (ex: chatbot, OCR), passe à un autre type (ex: prédiction, clustering, analyse de données, etc.)

🚀 OBJECTIF : Génère de nouveaux cas d'usage avec des APPLICATIONS IA VRAIMENT DIFFÉRENTES de tous les cas d'usage déjà proposés. VÉRIFIE que chaque thème est UNIQUE et DISTINCT."""
