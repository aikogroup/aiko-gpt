# 🧠 aikoGPT - Analyse IA et Génération de Cas d'Usage

> **Projet basé sur LangGraph SDK**  
> Analyse d'ateliers et transcriptions pour générer des besoins métier et cas d'usage IA

---

## 🎯 Description

aikoGPT est une application d'analyse intelligente qui :
- 📊 Parse des fichiers Excel (ateliers d'entreprise)
- 📄 Analyse des transcriptions PDF/JSON
- 🔍 Recherche du contexte entreprise (Perplexity)
- 💡 Génère 10 besoins métier avec citations
- 🎯 Propose des cas d'usage IA (Quick Wins + Structuration)
- 📝 Exporte un rapport Word professionnel

---

## 🏗️ Architecture

### Stack technique

- **Backend** : Python + LangGraph SDK
- **Frontend** : Next.js 15 + TypeScript
- **LLM** : OpenAI GPT-4
- **Web Search** : Perplexity API
- **Conteneurisation** : Docker + Docker Compose
- **Gestion Python** : UV

### Agents LangGraph

1. **WorkshopAgent** - Parse et analyse Excel
2. **TranscriptAgent** - Parse PDF/JSON + filtrage sémantique
3. **WebSearchAgent** - Recherche contexte entreprise (Perplexity)
4. **NeedAnalysisAgent** - Génère 10 besoins avec citations
5. **UseCaseAnalysisAgent** - Génère Quick Wins + Structuration IA
6. **ReportAgent** - Génère rapport Word final

---

## 🚀 Installation

### Prérequis

- Python 3.11+
- Node.js 18+
- UV (gestionnaire Python)
- Docker Desktop (optionnel)

### Installation backend

```bash
cd backend
uv sync
```

### Installation frontend

```bash
cd frontend
npm install
```

---

## ⚙️ Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine :

```bash
# OpenAI (obligatoire)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini-2024-07-18

# Perplexity (optionnel - fallback OpenAI si absent)
PERPLEXITY_API_KEY=pplx-...

# LangSmith (optionnel - monitoring)
LANGSMITH_API_KEY=lsv2_pt_...
```

---

## 🎮 Lancement

### Backend (LangGraph Server)

```bash
cd /Users/julliardcyril/Projets/aikoGPT
uv run langgraph dev
```

**URLs** :
- API : http://localhost:2024
- API Docs : http://localhost:2024/docs
- Debugger : https://smith.langchain.com/studio/?baseUrl=http://localhost:2024

### Frontend

```bash
cd frontend
npm run dev
```

**URL** : http://localhost:3000

---

## 🧪 Tests

### Tests backend

```bash
# Tests structure
uv run python tests/backend/test_minimal.py

# Tests workflow complet
USE_CHECKPOINTER=true uv run python tests/backend/test_graph.py

# Tests Perplexity
uv run python tests/backend/test_perplexity.py
```

### Résultats attendus

- ✅ Tous les agents s'exécutent sans erreur
- ✅ WorkshopAgent : ~34 cas d'usage extraits
- ✅ TranscriptAgent : ~5-6 citations extraites
- ✅ WebSearchAgent : Contexte entreprise récupéré
- ✅ NeedAnalysisAgent : 10 besoins générés
- ✅ Workflow complet : ~80 secondes

---

## 📁 Structure du projet

```
aikoGPT/
├── backend/                    # Backend Python + LangGraph
│   ├── agents/                 # Implémentations agents
│   ├── prompts/                # Prompts LLM versionnés
│   ├── models/                 # Modèles Pydantic
│   ├── utils/                  # Utilitaires
│   ├── workflow/               # Workflows LangGraph
│   ├── graph_factory.py        # Graphe principal
│   └── pyproject.toml          # Dépendances UV
├── frontend/                   # Frontend Next.js
│   ├── src/app/                # Pages App Router
│   ├── src/components/         # Composants réutilisables
│   └── src/lib/                # Logique métier
├── tests/backend/              # Tests backend
├── documents/                  # Fichiers exemple
├── langgraph.json              # Config LangGraph
├── .env                        # Variables d'environnement
└── README.md                   # Ce fichier
```

---

## 📊 Workflow

```
1. Upload fichiers (Excel, PDF/JSON) + nom entreprise
   ↓
2. WorkshopAgent → Parse Excel
   ↓
3. TranscriptAgent → Parse PDF/JSON
   ↓
4. WebSearchAgent → Recherche Perplexity
   ↓
5. NeedAnalysisAgent → Génère 10 besoins
   ↓ (validation utilisateur)
6. UseCaseAnalysisAgent → Génère cas d'usage
   ↓ (sélection utilisateur)
7. ReportAgent → Génère rapport Word
   ↓
8. Téléchargement rapport .docx
```

---

## 🎯 Fonctionnalités clés

### Génération de besoins

- **10 besoins** par itération
- **5 citations** par besoin (Excel + PDF/JSON)
- **Règles strictes** : Unicité, sources valides, pas de doublons
- **Régénération** : Exclusion des besoins non retenus

### Cas d'usage IA

- **8 Quick Wins** : ROI < 3 mois
- **10 Structuration IA** : ROI 3-12 mois
- **Technologies IA** concrètes (LLM, RAG, OCR, ML, etc.)
- **Régénération intelligente** : Si ≥ 5 validés → skip catégorie

### Persistence

- **LangGraph Server** : Persistence automatique
- **Thread management** : Support multi-utilisateurs
- **InMemorySaver** : Mode test avec `USE_CHECKPOINTER=true`

---

## 🔧 Dépannage

### Backend ne démarre pas

```bash
# Vérifier les dépendances
cd backend && uv sync

# Vérifier .env
cat .env | grep OPENAI_API_KEY
```

### Perplexity échoue (erreur 400)

Le système utilise **automatiquement OpenAI comme fallback**. Pour activer Perplexity :
1. Obtenir une clé API sur https://www.perplexity.ai/api-platform/
2. Ajouter `PERPLEXITY_API_KEY=pplx-...` dans `.env`
3. Configurer la facturation

### Tests échouent

```bash
# Nettoyer et réinstaller
cd backend
rm -rf .venv
uv sync
```

---

## 📚 Documentation

- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Perplexity API](https://docs.perplexity.ai/)
- [Next.js Docs](https://nextjs.org/docs)

---

## ✅ Status du projet

### Backend : **100% fonctionnel**

- ✅ 6 agents opérationnels
- ✅ LangGraph Server démarré
- ✅ Tests passent (structure + workflow)
- ✅ Perplexity corrigé
- ✅ Fallback OpenAI fonctionnel

### Frontend : **À configurer**

- ⏳ Structure Next.js créée
- ⏳ Composants à implémenter
- ⏳ API client à configurer

---

## 🤝 Contribution

Code : **Anglais**  
Commentaires : **Français**  
Documentation : **Français**

---

## 📞 Support

Pour toute question sur l'implémentation :
- Consulter les tests dans `/tests/backend/`
- Lire les prompts dans `/backend/prompts/`
- Vérifier les logs LangGraph Server

---

**Projet réalisé avec LangGraph SDK** 🚀
