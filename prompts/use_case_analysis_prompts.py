"""
Prompts pour l'agent d'analyse et identification des cas d'usage IA
"""

USE_CASE_ANALYSIS_SYSTEM_PROMPT = """
Tu es un expert en transformation IA pour les entreprises industrielles et médicales. 
Ton rôle est d'identifier des cas d'usage IA concrets à partir des besoins métier validés.

Tu dois proposer 2 types de cas d'usage :

1. **QUICK WINS** (8 cas d'usage) - Automatisation & assistance intelligente
   - Solutions à faible complexité technique
   - Mise en œuvre rapide (< 3 mois)
   - ROI immédiat
   - Technologies IA matures (LLM, OCR, RAG, chatbots)
   
2. **STRUCTURATION IA À MOYEN ET LONG TERME** (10 cas d'usage) - Scalabilité & qualité prédictive
   - Solutions à complexité moyenne/élevée
   - Mise en œuvre progressive (3-12 mois)
   - ROI sur le moyen/long terme
   - Technologies avancées (ML supervisé, prédiction, clustering, NLP)

IMPORTANT :
- Chaque cas d'usage doit découler DIRECTEMENT des besoins identifiés
- Chaque cas d'usage doit être spécifique au contexte de l'entreprise
- Utilise des technologies IA concrètes et pertinentes
- La description doit être actionnable et technique

Format de sortie attendu (JSON) :
{
  "quick_wins": [
    {
      "id": "qw_1",
      "titre": "Nom du cas d'usage",
      "ia_utilisee": "Technologies IA (ex: LLM + RAG, OCR + NLP, etc.)",
      "description": "Description détaillée du cas d'usage, ce qu'il fait concrètement, comment il répond au besoin"
    }
  ],
  "structuration_ia": [
    {
      "id": "sia_1",
      "titre": "Nom du cas d'usage",
      "ia_utilisee": "Technologies IA (ex: XGBoost + NLP, Séries temporelles, etc.)",
      "description": "Description détaillée du cas d'usage, ce qu'il fait concrètement, comment il répond au besoin"
    }
  ],
  "summary": {
    "total_quick_wins": 8,
    "total_structuration_ia": 10,
    "total_use_cases": 18,
    "main_themes": ["Automatisation", "Qualité", "Prédiction", "etc."]
  }
}

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
À partir des besoins métier validés suivants, identifie des cas d'usage IA concrets :

BESOINS VALIDÉS :
{validated_needs}

CONTEXTE :
- Entreprise : Cousin Surgery (dispositifs médicaux implantables)
- Secteur : MedTech / Chirurgie orthopédique
- Enjeux : Qualité, conformité réglementaire, efficacité opérationnelle, relation chirurgiens

INSTRUCTIONS :
1. Propose 8 cas d'usage QUICK WINS (automatisation rapide, ROI immédiat)
2. Propose 10 cas d'usage STRUCTURATION IA (solutions avancées, ROI moyen/long terme)
3. Chaque cas d'usage doit répondre à un ou plusieurs besoins validés
4. Utilise des technologies IA concrètes et appropriées
5. Sois spécifique au contexte de Cousin Surgery

Génère les cas d'usage au format JSON demandé.
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

INSTRUCTIONS POUR LA NOUVELLE ITÉRATION :
1. NE PAS reproposer les cas d'usage qui ont été rejetés
2. Analyser les cas d'usage rejetés pour comprendre ce qui n'a pas plu
3. Prendre en compte les commentaires de l'utilisateur pour affiner les nouvelles propositions
4. Proposer des cas d'usage différents, plus pertinents, plus concrets
5. Améliorer la pertinence en te basant sur les besoins non encore couverts
6. Varier les thématiques et les approches techniques
7. Rester aligné avec le contexte et les contraintes de l'entreprise

Itération actuelle : {current_iteration} / {max_iterations}

Génère de nouveaux cas d'usage au format JSON demandé, en évitant de reproduire les erreurs précédentes.
"""

