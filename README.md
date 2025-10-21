# 🧠 aikoGPT - Analyse Besoins & Génération Cas d'Usage IA

> Plateforme d'analyse de besoins et génération automatique de cas d'usage IA, propulsée par **LangGraph SDK**

---

## 📖 Description

aikoGPT est une plateforme moderne qui analyse les données d'ateliers, transcriptions et informations d'entreprise pour générer automatiquement :
- **10 besoins** structurés avec citations sources
- **Cas d'usage IA** en deux catégories (Quick Wins & Structuration IA)
- **Rapport Word** professionnel téléchargeable

### Pourquoi ce projet ?

Ce projet remplace une ancienne API maison par une architecture moderne basée sur **LangGraph SDK** pour :
- ✅ Orchestrer intelligemment des agents IA
- ✅ Faciliter la maintenance et l'évolution
- ✅ Garantir la traçabilité et la modularité

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Frontend Next.js + TS           │
│   Upload → Besoins → Use Cases → Rapport│
└─────────────┬───────────────────────────┘
              │ HTTP API
              ↓
┌─────────────────────────────────────────┐
│     Backend Python + LangGraph SDK      │
│                                         │
│  WorkshopAgent → TranscriptAgent →     │
│  WebSearchAgent → NeedAnalysisAgent →  │
│  UseCaseAnalysisAgent → ReportAgent    │
└─────────────┬───────────────────────────┘
              │
              ↓
      ┌───────────────┐
      │ OpenAI API    │
      │ Perplexity API│
      └───────────────┘
```

---

## ⚙️ Stack Technique

| Composant | Technologie |
|-----------|-------------|
| **Frontend** | Next.js 14 + TypeScript |
| **Backend** | Python 3.11 |
| **Orchestration** | **LangGraph SDK** ⭐ |
| **LLM** | OpenAI API (gpt-4) |
| **Web Search** | Perplexity API |
| **State Management** | Zustand |
| **Environnement** | UV (Python) + Docker |
| **Conteneurisation** | Docker + Docker Compose |

---

## 🚀 Installation

### Prérequis

- **Docker Desktop** installé et lancé
- **Git** pour cloner le repository
- Clés API :
  - OpenAI API Key
  - Perplexity API Key

### Étapes d'installation

1. **Cloner le repository**
   ```bash
   git clone <repository-url>
   cd aikoGPT
   ```

2. **Configurer les variables d'environnement**
   ```bash
   cp .env.example .env
   ```
   
   Puis éditer `.env` et remplir les clés API :
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   PERPLEXITY_API_KEY=pplx-your-key-here
   OPENAI_MODEL=gpt-4
   ```

3. **Lancer l'application**
   ```bash
   docker compose up --build
   ```

4. **Accéder à l'application**
   - Frontend : [http://localhost:3000](http://localhost:3000)
   - Backend API : [http://localhost:8000](http://localhost:8000)

---

## 📁 Structure du Projet

```
aikoGPT/
├── .env.example              # Template variables d'environnement
├── .gitignore               # Fichiers exclus du Git
├── docker-compose.yml       # Configuration Docker
├── README.md                # Ce fichier
├── AGENTS.md                # Documentation complète du projet
│
├── OLD/                     # Ancien code (temporaire)
│
├── backend/                 # Backend Python + LangGraph
│   ├── Dockerfile
│   ├── main.py             # Point d'entrée
│   ├── requirements.txt    # Dépendances Python
│   ├── api/                # Routes HTTP
│   ├── process_atelier/    # Agent Excel
│   ├── process_transcript/ # Agents PDF/JSON
│   ├── web_search/         # Agent Perplexity
│   ├── need_analysis/      # Agent génération besoins
│   ├── use_case_analysis/  # Agent génération cas d'usage
│   ├── prompts/            # Tous les prompts LLM
│   ├── workflow/           # Workflows LangGraph
│   ├── utils/              # Utilitaires (report, tokens)
│   └── models/             # Modèles Pydantic
│
├── frontend/                # Frontend Next.js
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── public/             # Assets statiques
│   └── src/
│       ├── app/            # Pages Next.js
│       │   ├── page.tsx           # Page 1: Upload
│       │   ├── needs/page.tsx     # Page 2: Besoins
│       │   ├── usecases/page.tsx  # Page 3: Cas d'usage
│       │   └── results/page.tsx   # Page 4: Résultats
│       ├── components/     # Composants réutilisables
│       ├── lib/            # API client, store, schemas
│       └── styles/         # Styles globaux
│
└── documents/               # Fichiers exemples
```

---

## 🔄 Workflow Utilisateur

### 1️⃣ Page Upload (Accueil)
- Upload fichier Excel (ateliers)
- Upload fichiers PDF/JSON (transcriptions)
- Saisir nom d'entreprise
- Clic "Analyser" → Lancement du workflow LangGraph

### 2️⃣ Page Besoins
- Affichage de 10 besoins générés
- Chaque besoin : titre + 5 citations sources
- Sélection/édition des besoins
- Bouton "Générer" : nouveaux besoins différents
- Bouton "Valider" : passer aux cas d'usage

### 3️⃣ Page Cas d'Usage
- **Quick Wins** (8) : ROI < 3 mois
- **Structuration IA** (10) : ROI 3-12 mois
- Sélection des cas d'usage pertinents
- Bouton "Compléter" : régénération intelligente
- Bouton "Valider" : voir les résultats

### 4️⃣ Page Résultats
- Synthèse besoins et cas d'usage sélectionnés
- Bouton "Télécharger" : rapport Word final

---

## 🛠️ Développement

### Lancer en mode développement

```bash
# Backend seul
cd backend
uv pip install -r requirements.txt
python main.py

# Frontend seul
cd frontend
npm install
npm run dev
```

### Conventions de code

- **Code** : Anglais
- **Commentaires** : Français
- **Commits** : Format `[TYPE] Description en français`
- **Typage strict** : Python (mypy) + TypeScript
- **Style** : PEP8 (Python) + ESLint/Prettier (Frontend)

### Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test
```

---

## 📚 Documentation Complète

Pour une documentation détaillée sur :
- L'architecture LangGraph
- Les agents et leurs prompts
- Le flux de données
- Les modèles de données
- Les standards de qualité

👉 Voir **[AGENTS.md](./AGENTS.md)**

---

## 🔑 Variables d'Environnement

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `OPENAI_API_KEY` | Clé API OpenAI | ✅ |
| `OPENAI_MODEL` | Modèle LLM (ex: gpt-4) | ✅ |
| `PERPLEXITY_API_KEY` | Clé API Perplexity | ✅ |
| `BACKEND_PORT` | Port backend (défaut: 8000) | ❌ |
| `ENVIRONMENT` | dev/staging/prod | ❌ |
| `LOG_LEVEL` | INFO/DEBUG/ERROR | ❌ |

---

## 🤝 Contribution

Ce projet suit des conventions strictes :
1. Code en anglais, commentaires en français
2. Typage strict obligatoire
3. Tests pour nouvelles fonctionnalités
4. Documentation à jour

---

## 📝 Licence

© 2025 Aiko Technologies. Tous droits réservés.

---

## 🆘 Support

Pour toute question ou problème :
- Consulter [AGENTS.md](./AGENTS.md) pour la documentation technique
- Vérifier les logs : `docker compose logs`
- Issues GitHub : (à définir)

---

**Développé avec ❤️ par l'équipe Aiko**
