# 🚀 Workflow d'Analyse des Cas d'Usage IA

## 📋 Vue d'ensemble

Ce module implémente la **Phase 2** du workflow : l'analyse et l'identification des cas d'usage IA à partir des besoins métier validés.

## ✨ Fonctionnalités

### Génération de cas d'usage
- **8 Quick Wins** - Solutions à faible complexité, ROI immédiat (< 3 mois)
- **10 Structuration IA** - Solutions avancées, ROI moyen/long terme (3-12 mois)

### Validation humaine simultanée
- Interface Streamlit permettant de valider les deux familles en même temps
- Minimum requis : **5 Quick Wins validés** ET **5 Structuration IA validés**
- Maximum **3 itérations** pour atteindre l'objectif

### Régénération intelligente
- Feedback utilisateur pris en compte
- Conservation des cas d'usage validés
- Proposition de nouvelles alternatives pour les cas rejetés

## 📁 Structure des fichiers

```
use_case_analysis/
├── __init__.py                              # Initialisation du module
├── use_case_analysis_agent.py               # Agent d'analyse (génération des use cases)
└── streamlit_use_case_validation.py         # Interface de validation humaine

prompts/
└── use_case_analysis_prompts.py             # Prompts pour l'agent

workflow/
└── need_analysis_workflow.py                # Workflow intégré (Phase 1 + Phase 2)

test_use_case_analysis.py                    # Tests unitaires
```

## 🔧 Architecture

### Agent d'analyse
```python
UseCaseAnalysisAgent(api_key)
  └─ analyze_use_cases(
       validated_needs,        # Besoins validés
       iteration=1,            # Numéro d'itération
       previous_use_cases,     # Use cases précédents (si régénération)
       validated_qw_count,     # Nombre de QW validés
       validated_sia_count     # Nombre de SIA validés
     )
```

### Interface de validation
```python
StreamlitUseCaseValidation()
  └─ display_use_cases_for_validation(
       quick_wins,               # Liste des Quick Wins proposés
       structuration_ia,         # Liste des Structuration IA proposés
       validated_qw_count,       # Nombre de QW déjà validés
       validated_sia_count       # Nombre de SIA déjà validés
     )
```

## 🎯 Format des cas d'usage

```json
{
  "quick_wins": [
    {
      "id": "qw_1",
      "titre": "Nom du cas d'usage",
      "ia_utilisee": "Technologies IA (ex: LLM + RAG)",
      "description": "Description détaillée..."
    }
  ],
  "structuration_ia": [
    {
      "id": "sia_1",
      "titre": "Nom du cas d'usage",
      "ia_utilisee": "Technologies IA (ex: XGBoost + NLP)",
      "description": "Description détaillée..."
    }
  ],
  "summary": {
    "total_quick_wins": 8,
    "total_structuration_ia": 10,
    "total_use_cases": 18,
    "main_themes": ["Automatisation", "Qualité", "Prédiction"]
  }
}
```

## 🔄 Workflow complet

```
Phase 1 : Analyse des besoins
  ↓
finalize_results (besoins validés)
  ↓
Phase 2 : Analyse des use cases
  ├─ analyze_use_cases         # Génération des 18 use cases
  ├─ validate_use_cases         # Validation humaine (Streamlit)
  ├─ check_use_case_success     # Vérification (5 QW + 5 SIA validés ?)
  └─ finalize_use_cases         # Sauvegarde des résultats

Si validation insuffisante :
  → Retour à analyze_use_cases (max 3 itérations)
```

## 📊 Résultats

Les résultats sont sauvegardés dans :
```
outputs/use_case_analysis_results.json
```

Structure :
```json
{
  "final_quick_wins": [...],
  "final_structuration_ia": [...],
  "use_case_success": true,
  "use_case_iteration": 1,
  "timestamp": "2025-10-13T11:27:59.682000",
  "source_needs": [...]
}
```

## 🧪 Tests

### Exécuter les tests
```bash
uv run python test_use_case_analysis.py
```

### Tests inclus
1. **Test 1** : Génération initiale des cas d'usage
2. **Test 2** : Vérification de la validation (partielle et complète)
3. **Test 3** : Régénération avec feedback

## 🔑 Configuration

### Variables d'environnement
```bash
OPENAI_API_KEY=your_api_key_here
```

### Modèle utilisé
- **gpt-5-nano** via l'API OpenAI Response

## 📝 Notes techniques

### Gestion des erreurs JSON
L'agent implémente un parsing robuste pour gérer :
- Caractères de contrôle invalides (`\x00-\x1f`)
- Trailing commas (`,}` → `}`)
- Extraction de JSON depuis du texte mixte

### Logs
Tous les logs sont préfixés avec :
- `🔬` : Analyse use cases
- `📊` : Statistiques
- `⚡` : Quick Wins
- `🧠` : Structuration IA
- `✅` : Succès
- `❌` : Erreur

## 🎯 Exemples de cas d'usage générés

### Quick Wins
1. Agent de productivité conversationnel (LLM + RAG)
2. Transcription automatique de réunions (Speech-to-Text + LLM)
3. OCR intelligent pour dossiers qualité (Textract + NLP)
4. Chatbot d'assistance produit (LLM + RAG)
5. Assistant rédactionnel réglementaire (LLM + templates)

### Structuration IA
1. Détection proactive des dossiers qualité à risque (XGBoost)
2. Prévision des besoins en stocks (Séries temporelles + régression)
3. Analyse automatique des publications scientifiques (Scraping + NLP)
4. Optimisation dynamique des seuils de stock (Clustering + règles)
5. Dashboard décisionnel augmenté par IA (BI + LLM)

## 🚀 Prochaines étapes

1. Intégrer dans l'application Streamlit principale (`app/app.py`)
2. Créer un agent rédactionnel pour générer le rapport final
3. Ajouter des métriques de suivi (ROI estimé, complexité, prérequis)
4. Implémenter un système de priorisation des use cases

## 📚 Documentation

Pour plus d'informations sur le workflow complet :
- `workflow/README.md` - Documentation du workflow LangGraph
- `workflow/WORKFLOW_DIAGRAM.md` - Diagramme du workflow
- `DEBUG_GUIDE.md` - Guide de debugging

## 👥 Auteurs

AIKO - Transformation IA pour les entreprises

