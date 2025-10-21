# 🧠 Projet – Refonte LangGraph SDK

---

# 📖 1. CONTEXTE

## 🎯 Objectif général

Nous repartons **de zéro** pour reconstruire un projet propre, modulaire et documenté, basé sur **LangGraph SDK** comme moteur d'orchestration et d'analyse.

### Pourquoi ce projet ?

Le projet précédent utilisait une **API maison** complexe et difficile à maintenir. Nous voulons :
- Remplacer cette API par **LangGraph SDK**, un framework moderne et puissant pour orchestrer des agents IA
- Créer un **frontend Next.js** moderne, réactif et intuitif
- Structurer un **backend Python** clair où **LangGraph gère toute la logique métier**
- Faciliter la maintenance et l'évolution future du code

> ⚠️ L'ancien code sera déplacé dans un dossier `/OLD` pour référence temporaire, puis supprimé à la fin du projet.

## 🧩 Logique métier du projet

### Données d'entrée

L'application prend en entrée trois types de sources :

1. **Fichier Excel** (ateliers)
   - Colonne A : nom de l'atelier
   - Colonne B : cas d'usage
   - Colonne C : objectif ou gain

2. **Fichiers PDF et/ou JSON** (transcriptions, feedbacks)
   - Citations des utilisateurs
   - Frustrations exprimées
   - Besoins identifiés

3. **Nom d'entreprise**
   - Pour recherche contextuelle via Perplexity
   - Informations sur le secteur, la taille, les actualités

### Traitement

Ces sources sont analysées par **LangGraph** à travers un workflow orchestré d'agents IA qui :
- Parsent et structurent les données
- Extraient les informations clés
- Génèrent du contenu analytique

### Données de sortie

Le système produit :

1. **10 besoins** par itération
   - Titre clair résumant l'apport
   - 5 citations issues des fichiers sources (Excel + PDF/JSON)
   - Éditables et sélectionnables par l'utilisateur

2. **Cas d'usage** en deux catégories
   - **Quick Wins** : projets simples, ROI rapide (< 3 mois)
   - **Structuration IA** : projets ambitieux, ROI moyen/long terme (3-12 mois)
   - Chaque cas d'usage contient : titre, description, technologies IA

3. **Rapport Word final**
   - Compile les besoins et cas d'usage sélectionnés
   - Téléchargeable depuis l'interface

---

# ⚙️ 2. STACK TECHNIQUE

| Composant | Technologie | Version / Détails |
| --- | --- | --- |
| **Frontend** | Next.js + TypeScript | Framework React moderne |
| **Backend** | Python | Langage principal backend |
| **Orchestration** | **LangGraph SDK** | ⭐ Cœur du projet - gestion des agents |
| **LLM** | OpenAI API | Modèle configurable via `.env` |
| **Web Search** | Perplexity API | Recherche contextuelle entreprise |
| **Environnement Python** | UV | Gestionnaire de dépendances moderne |
| **Variables d'environnement** | `.env` | Clés API, configuration |
| **Conteneurisation** | Docker Desktop + Docker Compose | Déploiement et exécution |
| **Langue du code** | Anglais | Conventions internationales |
| **Commentaires** | Français | Pour faciliter la collaboration |

### Choix technologiques clés

- **LangGraph SDK** : obligatoire, gère 100% de la logique métier
- **Next.js** : interface moderne avec routing intégré
- **UV** : environnement Python plus rapide que pip/venv
- **Docker** : garantit la reproductibilité et facilite le déploiement

# 🛠️ 3. OUTILS

## LangGraph SDK ⭐

**LangGraph SDK** est le moteur central du backend et le cœur de l'intelligence du projet.

### Rôle principal

LangGraph permet de :
- **Orchestrer** plusieurs agents (Workshop, Transcript, WebSearch, NeedAnalysis, UseCase, Report)
- **Gérer le flux de données** entre les agents (chaînage automatique des entrées/sorties)
- **Définir des workflows** logiques d'analyse pilotés par le LLM
- **Centraliser la logique métier** sans dépendre d'un framework API classique

### Pourquoi LangGraph ?

✅ **Modularité** : chaque agent est isolé et testable  
✅ **Maintenabilité** : la logique métier est séparée de l'API  
✅ **Évolutivité** : facile d'ajouter de nouveaux agents  
✅ **Traçabilité** : suivi du flux de données entre agents

> 📚 **Ressource** : Utiliser DeepWiki pour approfondir la maîtrise de LangGraph SDK

## OpenAI API

- **Modèle** : Configurable via `.env` (ex: `gpt-4`, `gpt-5-nano`)
- **Usage** : Analyse des documents, génération de besoins et cas d'usage
- **Règles** : Toujours utiliser l'**OpenAI Response API**, jamais `chat.completion`

## Perplexity API

- **Usage** : Recherche contextuelle sur l'entreprise
- **Données récupérées** : secteur, taille, actualités
- **Règle importante** : ⚠️ Fournit uniquement le **contexte**, ne génère **jamais** de besoins

## Outils de développement

| Outil | Usage |
| --- | --- |
| **UV** | Gestionnaire d'environnement Python moderne |
| **Docker Desktop** | Conteneurisation et exécution locale |
| **ESLint + Prettier** | Linting et formatage frontend |
| **mypy** | Typage strict Python (PEP8) |

---

# 📊 4. DATA

## Structure des données

### Fichier Excel (Workshop)

**Format d'entrée :**
```
| Colonne A          | Colonne B           | Colonne C              |
|--------------------|---------------------|------------------------|
| Nom de l'atelier   | Cas d'usage         | Objectif ou gain       |
```

**Traitement :**
- Parsing des 3 colonnes
- Extraction des cas d'usage initiaux
- Analyse LLM pour structuration

**Références code existant :**
- `process_atelier/workshop_agent.py` (lignes 56-94 parsing, 134-181 analyse)
- Prompts : `prompts/workshop_agent_prompts.py`
- Workflow : `workflow/need_analysis_workflow.py` ligne 332

### Fichiers PDF/JSON (Transcripts)

**Contenu :**
- Citations d'utilisateurs
- Frustrations exprimées
- Besoins identifiés lors d'ateliers

**Traitement :**
- Parsing PDF et JSON
- Extraction de citations clés
- Filtrage sémantique via LLM

**Références code existant :**
- Fichier principal : `process_transcript/transcript_agent.py`
- Parsers : `pdf_parser.py` et `json_parser.py`
- Analyse LLM : `semantic_filter_agent.py` (ligne 80)
- Prompts : `prompts/transcript_agent_prompts.py`
- Workflow : `workflow/need_analysis_workflow.py` ligne 356

### Nom d'entreprise (Web Search)

**Entrée :** Nom de l'entreprise (texte libre)

**Traitement :**
- Recherche Perplexity (lignes 69-75)
- Contexte additionnel OpenAI (lignes 121-137)

**Sortie :**
- Secteur d'activité
- Taille de l'entreprise
- Actualités récentes

**Références code existant :**
- `web_search/web_search_agent.py`
- Prompts : `prompts/web_search_agent_prompts.py`
- Workflow : `workflow/need_analysis_workflow.py` ligne 375

⚠️ **RÈGLE CRITIQUE** : Web Search = **CONTEXTE uniquement**, ne génère **JAMAIS** de besoins

### Besoins générés (Needs)

**Structure d'un besoin :**
```json
{
  "id": "need_001",
  "title": "Titre clair résumant l'apport",
  "citations": [
    "Citation 1 - Source: Atelier X",
    "Citation 2 - Source: Transcript Y",
    "Citation 3 - Source: Atelier Z",
    "Citation 4 - Source: Transcript W",
    "Citation 5 - Source: Atelier V"
  ],
  "selected": false,
  "edited": false
}
```

**Règles de génération :**
- **10 besoins** par itération
- Citations issues de **Workshop + Transcript** (sources principales)
- Web Search = contexte uniquement
- Pas de citations sans source (éviter "- Transcript" générique)
- Thèmes uniques (pas de doublons)

**Prompts associés :**
- System Prompt : `prompts/need_analysis_agent_prompts.py` lignes 5-74
- User Prompt initial : lignes 76-101
- User Prompt régénération : lignes 113-179

**Agent responsable :** `NeedAnalysisAgent`

**Entrées :**
- `workshop_data` (Excel) → cas d'usage, objectifs, bénéfices
- `transcript_data` (PDF/JSON) → besoins exprimés, frustrations, citations
- `web_search_data` (Perplexity) → ⚠️ CONTEXTE uniquement

### Cas d'usage générés (Use Cases)

**Deux catégories :**

#### 1. Quick Wins (8 générés)
- Projets simples à mettre en œuvre
- Automatisation rapide
- ROI immédiat (< 3 mois)

#### 2. Structuration IA (10 générés)
- Solutions avancées et ambitieuses
- Projets structurants
- ROI moyen/long terme (3-12 mois)

**Structure d'un cas d'usage :**
```json
{
  "id": "uc_qw_001",
  "category": "quick_win",
  "title": "Titre clair et concis",
  "description": "Description du projet",
  "ai_technologies": ["LLM", "RAG", "OCR", "ML supervisé"],
  "selected": false
}
```

**Règles de génération :**
- Technologies IA concrètes et pertinentes
- Titres uniques (pas de doublons)
- Si ≥ 5 validés dans une catégorie → ne régénère rien pour cette catégorie

**Prompts associés :**
- System Prompt : `prompts/use_case_analysis_prompts.py` lignes 5-50
- User Prompt initial : lignes 52-77
- User Prompt régénération : lignes 79-127

**Agent responsable :** `UseCaseAnalysisAgent`

**Entrées :**
- `validated_needs` → Besoins validés à la page 2 (minimum 5)
- `workshop_data`, `transcript_data`, `web_search_data` → Contexte

### Rapport Word final

**Contenu :**
- Besoins sélectionnés (titre + citations)
- Cas d'usage retenus (titre + description + technologies IA)
- Mise en forme professionnelle

**Références code existant :**
- `utils/report_generator.py` (lignes 163-189)

---

# 📁 5. FICHIERS

## Arborescence complète

```
root/
│
├── .env                          # Variables d'environnement (clés API, modèle LLM)
├── .env.example                  # Template pour .env
├── .gitignore                    # Fichiers à exclure du repo
├── docker-compose.yml            # Configuration Docker
├── README.md                     # Documentation principale du projet
│
├── OLD/                          # 📦 Code de l'ancien projet (temporaire)
│   └── [ancien code à déplacer]
│
├── backend/                      # 🐍 Backend Python + LangGraph
│   ├── main.py                   # Point d'entrée, initialisation LangGraph
│   │
│   ├── api/                      # Routes HTTP (couche technique uniquement)
│   │   ├── __init__.py
│   │   └── routes.py             # /upload, /run, /report
│   │
│   ├── process_atelier/          # Module : analyse fichier Excel
│   │   ├── __init__.py
│   │   └── workshop_agent.py     # Agent LangGraph pour Excel
│   │
│   ├── process_transcript/       # Module : analyse PDF/JSON
│   │   ├── __init__.py
│   │   ├── transcript_agent.py   # Agent principal
│   │   ├── pdf_parser.py         # Parser PDF
│   │   ├── json_parser.py        # Parser JSON
│   │   └── semantic_filter_agent.py  # Filtrage LLM
│   │
│   ├── web_search/               # Module : recherche entreprise
│   │   ├── __init__.py
│   │   └── web_search_agent.py   # Perplexity + OpenAI
│   │
│   ├── need_analysis/            # Module : génération besoins
│   │   ├── __init__.py
│   │   └── need_analysis_agent.py
│   │
│   ├── use_case_analysis/        # Module : génération cas d'usage
│   │   ├── __init__.py
│   │   └── use_case_analysis_agent.py
│   │
│   ├── prompts/                  # 📝 Tous les prompts LLM
│   │   ├── __init__.py
│   │   ├── workshop_agent_prompts.py
│   │   ├── transcript_agent_prompts.py
│   │   ├── web_search_agent_prompts.py
│   │   ├── need_analysis_agent_prompts.py
│   │   └── use_case_analysis_prompts.py
│   │
│   ├── workflow/                 # 🔄 Workflows LangGraph
│   │   ├── __init__.py
│   │   └── need_analysis_workflow.py  # Graphe d'exécution principal
│   │
│   ├── utils/                    # 🛠️ Utilitaires
│   │   ├── __init__.py
│   │   ├── report_generator.py   # Génération Word
│   │   └── token_tracker.py      # Suivi tokens (optionnel)
│   │
│   ├── models/                   # 📐 Modèles de données (Pydantic)
│   │   ├── __init__.py
│   │   ├── need_analysis_models.py
│   │   ├── use_case_analysis_models.py
│   │   └── web_search_models.py
│   │
│   └── requirements.txt          # Dépendances Python (ou pyproject.toml avec UV)
│
└── frontend/                     # 💻 Frontend Next.js + TypeScript
    ├── package.json              # Dépendances Node.js
    ├── tsconfig.json             # Configuration TypeScript
    ├── next.config.js            # Configuration Next.js
    ├── .eslintrc.json            # Configuration ESLint
    │
    ├── public/                   # Assets statiques
    │   └── logoAiko.jpeg         # Logo entreprise
    │
    └── src/
        ├── app/                  # Pages Next.js (App Router)
        │   ├── layout.tsx        # Layout principal
        │   ├── page.tsx          # Page 1 : Accueil (upload)
        │   │
        │   ├── needs/            # Page 2 : Besoins
        │   │   └── page.tsx
        │   │
        │   ├── usecases/         # Page 3 : Cas d'usage
        │   │   └── page.tsx
        │   │
        │   └── results/          # Page 4 : Résultats
        │       └── page.tsx
        │
        ├── components/           # Composants réutilisables
        │   ├── UploadZone.tsx    # Zone d'upload fichiers
        │   ├── NeedCard.tsx      # Carte besoin
        │   ├── UseCaseCard.tsx   # Carte cas d'usage
        │   ├── SideNav.tsx       # Navigation latérale
        │   └── Spinner.tsx       # Loader
        │
        ├── lib/                  # Logique métier frontend
        │   ├── api-client.ts     # Appels API backend
        │   ├── store.ts          # State management (Zustand)
        │   └── schemas.ts        # Types TypeScript
        │
        └── styles/               # Styles globaux
            └── globals.css
```

## Description des modules backend

### `backend/main.py` ⭐

**Rôle :** Point d'entrée du backend, initialise LangGraph

```python
# TODO (FR):
# Initialiser LangGraph ici
# - Charger les agents et leurs prompts
# - Définir les connexions :
#   Workshop → Transcript → WebSearch → NeedAnalysis → UseCase → Report
# - (Optionnel) Exposer 3 routes techniques :
#   /api/upload, /api/run, /api/report
# - Ne pas inclure de logique métier dans ces routes
```

### `process_atelier/workshop_agent.py`

**Rôle :** Agent LangGraph pour analyser le fichier Excel

**Entrée :** Fichier Excel (ateliers)
- Colonne A : nom de l'atelier
- Colonne B : cas d'usage
- Colonne C : objectif ou gain

**Traitement :**
- Parsing des 3 colonnes
- Extraction et structuration via LLM

**Références code existant :**
- Lignes 56-94 : parsing Excel
- Lignes 134-181 : analyse LLM

**Prompts :** `prompts/workshop_agent_prompts.py`

**Workflow :** `workflow/need_analysis_workflow.py` ligne 332

### `process_transcript/`

**Rôle :** Module pour analyser fichiers PDF/JSON (transcriptions)

**Fichiers :**
- `transcript_agent.py` : agent principal
- `pdf_parser.py` : extraction texte PDF
- `json_parser.py` : parsing JSON
- `semantic_filter_agent.py` : filtrage LLM (ligne 80)

**Entrée :** Fichiers PDF et/ou JSON

**Traitement :**
- Extraction de citations
- Identification des frustrations
- Filtrage sémantique

**Prompts :** `prompts/transcript_agent_prompts.py`

**Workflow :** `workflow/need_analysis_workflow.py` ligne 356

### `web_search/web_search_agent.py`

**Rôle :** Recherche contextuelle sur l'entreprise

**Entrée :** Nom de l'entreprise

**Traitement :**
- Recherche Perplexity (lignes 69-75)
- Contexte additionnel OpenAI (lignes 121-137)

**Sortie :**
- Secteur d'activité
- Taille de l'entreprise
- Actualités récentes

⚠️ **RÈGLE CRITIQUE :** Fournit uniquement le **CONTEXTE**, ne génère **JAMAIS** de besoins

**Prompts :** `prompts/web_search_agent_prompts.py`

**Workflow :** `workflow/need_analysis_workflow.py` ligne 375

### `need_analysis/need_analysis_agent.py`

**Rôle :** Agent LangGraph pour générer les besoins

**Entrées :**
- `workshop_data` → cas d'usage, objectifs, bénéfices
- `transcript_data` → besoins exprimés, frustrations, citations
- `web_search_data` → contexte (secteur, taille) ⚠️ PAS de besoins

**Sortie :** 10 besoins (titre + 5 citations)

**Règles :**
- Citations issues de Workshop + Transcript (sources PRINCIPALES)
- Web Search = contexte uniquement
- Pas de citations sans source
- Thèmes uniques (pas de doublons)

**Prompts :** `prompts/need_analysis_agent_prompts.py`
- Lignes 5-74 : System Prompt (toujours utilisé)
- Lignes 76-101 : User Prompt (1ère itération)
- Lignes 113-179 : User Prompt (régénération)

### `use_case_analysis/use_case_analysis_agent.py`

**Rôle :** Agent LangGraph pour générer les cas d'usage

**Entrées :**
- `validated_needs` → Besoins validés page 2 (minimum 5)
- `workshop_data`, `transcript_data`, `web_search_data` → Contexte

**Sortie :**
- 8 Quick Wins (ROI < 3 mois)
- 10 Structuration IA (ROI 3-12 mois)

**Règles :**
- Technologies IA concrètes (LLM, RAG, OCR, ML, etc.)
- Titres uniques
- Si ≥ 5 validés dans une catégorie → ne régénère rien

**Prompts :** `prompts/use_case_analysis_prompts.py`
- Lignes 5-50 : System Prompt
- Lignes 52-77 : User Prompt (1ère itération)
- Lignes 79-127 : User Prompt (régénération)

### `workflow/need_analysis_workflow.py`

**Rôle :** Définit la séquence d'exécution LangGraph

**Workflow :**
1. Combine `workshop_data`, `transcript_data`, `web_search_data`
2. Produit `needs` → `use_cases` → `report`

### `utils/report_generator.py`

**Rôle :** Génère le document Word final

**Contenu :**
- Besoins sélectionnés (titre + citations)
- Cas d'usage retenus (titre + description + technologies)
- Mise en forme professionnelle

**Références code existant :** lignes 163-189

### `prompts/` (Dossier)

**Contenu :** Tous les prompts LLM versionnés

**Fichiers :**
- `workshop_agent_prompts.py`
- `transcript_agent_prompts.py`
- `web_search_agent_prompts.py`
- `need_analysis_agent_prompts.py`
- `use_case_analysis_prompts.py`

**Avantages :**
- Centralisation
- Versioning facile
- Itération rapide sur les prompts

## Description des pages frontend

### Page 1 : Accueil (Upload) - `app/page.tsx`

**Objectif :** Collecter toutes les données d'entrée

**Éléments :**
- Logo entreprise (en haut à gauche)
- Navbar (pages du site)
- Zone d'upload fichier Excel
- Zone d'upload fichiers PDF/JSON (multi-fichiers)
- Champ texte : nom de l'entreprise
- Bouton "Analyser" → lance `/api/run`

**TODOs :**
- Créer composant `UploadZone` multi-fichiers
- Validation formats (`.xlsx`, `.pdf`, `.json`)
- Loader pendant l'analyse
- Appel API `/api/run` pour lancer le graphe LangGraph
- Stocker résultats dans state global (Context API ou Zustand)

### Page 2 : Besoins - `app/needs/page.tsx`

**Objectif :** Afficher, éditer et sélectionner les 10 besoins générés

**Éléments :**
- Liste de 10 besoins (cartes)
- Chaque besoin :
  - Checkbox (sélection)
  - Titre éditable
  - 5 citations (Excel + PDF/JSON)
- Besoins sélectionnés remontent en haut
- Champ commentaire (consignes pour régénération)
- Bouton "Générer" → génère de nouveaux besoins différents
- Bouton "Valider" → passe à page 3 (cas d'usage)

**TODOs :**
- Composant `NeedCard` (titre, citations, checkbox)
- Mise à jour temps réel du state
- Bouton Générer → POST `/api/run` (exclusion besoins précédents)
- Bouton Valider → navigation `/usecases`

**Prompts associés :** `prompts/need_analysis_agent_prompts.py`

### Page 3 : Cas d'usage - `app/usecases/page.tsx`

**Objectif :** Générer et sélectionner les cas d'usage

**Éléments :**
- Section **Quick Wins** (8 cas d'usage)
- Section **Structuration IA** (10 cas d'usage)
- Chaque cas d'usage :
  - Bouton sélection
  - Titre
  - Description
  - Technologies IA (LLM, RAG, OCR, etc.)
- Champ commentaire
- Bouton "Générer" → complète catégories manquantes
- Bouton "Valider" → passe à page 4 (résultats)

**Règle intelligente :** Si ≥ 5 validés dans une catégorie → ne régénère rien

**TODOs :**
- Composants `QuickWinCard` et `StructurationCard`
- Gestion état sélectionné
- Appel `/api/run` pour régénération
- Navigation `/results` après validation

**Prompts associés :** `prompts/use_case_analysis_prompts.py`

### Page 4 : Résultats - `app/results/page.tsx`

**Objectif :** Synthèse et téléchargement rapport Word

**Éléments :**
- Liste besoins validés
- Liste cas d'usage retenus
- Bouton "Télécharger" → appel `/api/report`

**TODOs :**
- Affichage dynamique éléments sélectionnés
- Feedback visuel téléchargement
- Relier à `utils/report_generator.py`

**Références code existant :**
- `utils/report_generator.py` (lignes 163-189)
- `frontend/src/app/results/page.tsx` (lignes 89-104)

## Fichiers de configuration

### `.env`

**Contenu obligatoire :**
```bash
# OpenAI API
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4  # ou gpt-5-nano selon les règles

# Perplexity API
PERPLEXITY_API_KEY=pplx-...

# LangGraph configuration
LANGGRAPH_API_URL=...

# Autres variables
ENVIRONMENT=development
```

### `.env.example`

Template du fichier `.env` sans valeurs sensibles, à versionner dans Git.

### `.gitignore`

**Doit exclure :**
```gitignore
# Environnement
.env
.venv/
venv/
*.pyc
__pycache__/

# Node modules
node_modules/
.next/

# Logs
*.log

# Docker volumes
volumes/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Outputs temporaires
outputs/
temp/
```

### `docker-compose.yml`

**Structure :**
- Service `backend` (Python + LangGraph)
- Service `frontend` (Next.js)
- Volumes pour persistance si nécessaire
- Network pour communication inter-services

### `README.md`

**Sections obligatoires :**
1. Description du projet
2. Prérequis (Docker Desktop, UV)
3. Installation
4. Commande de lancement : `docker compose up --build`
5. Architecture générale
6. Flux LangGraph
7. Conventions de qualité (code anglais, commentaires français, typage)

---

# 🏗️ 6. ARCHITECTURE

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                            │
│                      Next.js + TypeScript                   │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │  Upload  │→│  Besoins │→│ Use Cases│→│ Résultats│  │
│  │  (Page1) │  │ (Page2)  │  │ (Page3)  │  │ (Page4)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│                                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP API
                          │ /api/upload, /api/run, /api/report
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                         BACKEND                             │
│                   Python + LangGraph SDK                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              LANGGRAPH WORKFLOW                      │  │
│  │                                                       │  │
│  │  ┌─────────────┐      ┌──────────────┐             │  │
│  │  │ Workshop    │      │ Transcript   │             │  │
│  │  │ Agent       │      │ Agent        │             │  │
│  │  │ (Excel)     │      │ (PDF/JSON)   │             │  │
│  │  └──────┬──────┘      └──────┬───────┘             │  │
│  │         │                    │                      │  │
│  │         └────────┬───────────┘                      │  │
│  │                  │                                   │  │
│  │         ┌────────▼─────────┐                        │  │
│  │         │  Web Search      │                        │  │
│  │         │  Agent           │                        │  │
│  │         │  (Perplexity)    │                        │  │
│  │         └────────┬─────────┘                        │  │
│  │                  │                                   │  │
│  │         ┌────────▼──────────┐                       │  │
│  │         │  Need Analysis    │                       │  │
│  │         │  Agent            │                       │  │
│  │         │  (10 besoins)     │                       │  │
│  │         └────────┬──────────┘                       │  │
│  │                  │                                   │  │
│  │         ┌────────▼──────────┐                       │  │
│  │         │  UseCase Analysis │                       │  │
│  │         │  Agent            │                       │  │
│  │         │  (QW + SIA)       │                       │  │
│  │         └────────┬──────────┘                       │  │
│  │                  │                                   │  │
│  │         ┌────────▼──────────┐                       │  │
│  │         │  Report Agent     │                       │  │
│  │         │  (Word doc)       │                       │  │
│  │         └───────────────────┘                       │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓
                  ┌───────────────┐
                  │   EXTERNAL    │
                  │   SERVICES    │
                  │               │
                  │ - OpenAI API  │
                  │ - Perplexity  │
                  └───────────────┘
```

## Flux de données détaillé

### Étape 1 : Upload (Frontend → Backend)

1. Utilisateur upload fichiers (Excel, PDF/JSON) + nom entreprise
2. Frontend envoie à `/api/upload`
3. Backend stocke temporairement les fichiers
4. Retourne confirmation au frontend

### Étape 2 : Analyse initiale (Backend LangGraph)

Frontend appelle `/api/run` avec paramètres :
- `action: "generate_needs"`
- `files_ids: [...]`
- `company_name: "..."`

**LangGraph execute :**

```
WorkshopAgent (Excel)
    ↓
    Extrait : ateliers, cas d'usage, objectifs
    ↓
TranscriptAgent (PDF/JSON)
    ↓
    Extrait : citations, frustrations
    ↓
WebSearchAgent (Perplexity)
    ↓
    Récupère : secteur, taille, actualités
    ↓
NeedAnalysisAgent
    ↓
    Génère : 10 besoins (titre + 5 citations)
    ↓
Retour Frontend : { needs: [...] }
```

### Étape 3 : Régénération besoins (optionnel)

Frontend appelle `/api/run` avec :
- `action: "regenerate_needs"`
- `excluded_needs: [...]`  (besoins non retenus)
- `comment: "..."`  (instructions utilisateur)

**LangGraph execute :**
- Utilise le prompt de régénération
- Génère 10 nouveaux besoins **différents** des précédents

### Étape 4 : Génération cas d'usage

Frontend appelle `/api/run` avec :
- `action: "generate_use_cases"`
- `validated_needs: [...]`  (minimum 5)

**LangGraph execute :**

```
UseCaseAnalysisAgent
    ↓
    Input : validated_needs + workshop_data + transcript_data + web_search_data
    ↓
    Génère : 8 Quick Wins + 10 Structuration IA
    ↓
Retour Frontend : { quick_wins: [...], structuration_ia: [...] }
```

### Étape 5 : Régénération cas d'usage (optionnel)

Frontend appelle `/api/run` avec :
- `action: "regenerate_use_cases"`
- `validated_quick_wins: [...]`
- `validated_structuration_ia: [...]`
- `comment: "..."`

**Règle intelligente :**
- Si `validated_quick_wins.length >= 5` → ne régénère **rien** pour QW
- Si `validated_structuration_ia.length >= 5` → ne régénère **rien** pour SIA
- Sinon, génère pour compléter

### Étape 6 : Génération rapport Word

Frontend appelle `/api/report` avec :
- `validated_needs: [...]`
- `validated_use_cases: [...]`

**Backend execute :**

```
ReportAgent
    ↓
    Input : needs + use_cases
    ↓
    Génère document Word formaté
    ↓
Retour Frontend : fichier .docx en téléchargement
```

## Principes architecturaux

### Séparation des responsabilités

| Composant | Responsabilité |
| --- | --- |
| **Frontend** | Interface utilisateur, validation inputs, navigation |
| **API Backend** | Routes HTTP, upload/download fichiers |
| **LangGraph** | **100% de la logique métier** (analyse, génération) |
| **Prompts** | Instructions LLM, versionnées et isolées |

### Architecture LangGraph

**LangGraph** gère :
- ✅ Orchestration des agents
- ✅ Flux de données entre agents
- ✅ Logique conditionnelle (régénération, etc.)
- ✅ Gestion des erreurs

**API Backend** gère :
- ✅ Upload de fichiers
- ✅ Déclenchement du graphe LangGraph
- ✅ Téléchargement du rapport

⚠️ **RÈGLE IMPORTANTE** : L'API ne contient **AUCUNE** logique métier, seulement des appels à LangGraph

### Agents LangGraph

| Agent | Input | Output | LLM ? |
| --- | --- | --- | --- |
| **WorkshopAgent** | Fichier Excel | `workshop_data` (dict) | ✅ |
| **TranscriptAgent** | Fichiers PDF/JSON | `transcript_data` (list) | ✅ |
| **WebSearchAgent** | Nom entreprise | `web_search_data` (dict) | ✅ |
| **NeedAnalysisAgent** | `workshop_data` + `transcript_data` + `web_search_data` | `needs` (list[10]) | ✅ |
| **UseCaseAnalysisAgent** | `validated_needs` + contexte | `use_cases` (dict) | ✅ |
| **ReportAgent** | `needs` + `use_cases` | Fichier `.docx` | ❌ |

### Bonnes pratiques LangGraph

1. **Chaque agent = une responsabilité**
   - Parsing OU analyse, pas les deux

2. **Input/Output explicites**
   - Utiliser Pydantic pour typage strict

3. **Prompts versionnés**
   - Fichiers séparés dans `/prompts`
   - Commentaires français explicites

4. **Testabilité**
   - Chaque agent doit être testable isolément

---

# 🔧 7. STRUCTURE (Étapes de développement)

## Étape 1 : Mise en place initiale ✅

**Objectif :** Créer la structure complète du projet vide avec TODOs

**Actions :**
1. Déplacer ancien code dans `/OLD`
2. Créer arborescence complète (dossiers backend + frontend)
3. Créer fichiers vides avec TODOs en français
4. Créer fichiers de configuration :
   - `.gitignore`
   - `.env.example`
   - `docker-compose.yml`
   - `README.md`

**Validation :** Structure complète visible, projet s'ouvre dans IDE

---

## Étape 2 : Configuration Docker

**Objectif :** Projet lance avec `docker compose up --build`

**Actions :**
1. Dockerfile backend (Python + UV)
2. Dockerfile frontend (Next.js)
3. docker-compose.yml fonctionnel
4. Variables `.env` chargées correctement

**Validation :** `docker compose up` lance sans erreur

---

## Étape 3 : Frontend initial (pages vides)

**Objectif :** Navigation entre les 4 pages fonctionne

**Actions :**
1. Page 1 : Accueil (layout + logo + navbar)
2. Page 2 : Besoins (vide)
3. Page 3 : Cas d'usage (vide)
4. Page 4 : Résultats (vide)
5. Composant `SideNav` fonctionnel

**Validation :** Navigation fluide entre pages

---

## Étape 4 : LangGraph - Agents de base

**Objectif :** Agents LangGraph fonctionnels (sans logique)

**Actions :**
1. Initialiser LangGraph dans `main.py`
2. Créer agents vides :
   - WorkshopAgent
   - TranscriptAgent
   - WebSearchAgent
   - NeedAnalysisAgent
   - UseCaseAnalysisAgent
   - ReportAgent
3. Définir workflow de base
4. Tester appel simple

**Validation :** Workflow s'execute sans erreur

---

## Étape 5 : Parsers (Excel, PDF, JSON)

**Objectif :** Extraire données des fichiers

**Actions :**
1. Implémenter `workshop_agent.py` (parser Excel)
2. Implémenter `pdf_parser.py`
3. Implémenter `json_parser.py`
4. Tester avec fichiers exemples

**Validation :** Données extraites correctement

---

## Étape 6 : Web Search Agent

**Objectif :** Récupérer contexte entreprise

**Actions :**
1. Intégrer API Perplexity
2. Intégrer OpenAI pour contexte additionnel
3. Tester avec noms d'entreprises réelles

**Validation :** Données pertinentes récupérées

---

## Étape 7 : Need Analysis Agent

**Objectif :** Générer 10 besoins avec citations

**Actions :**
1. Implémenter prompts (System, User initial, User régénération)
2. Connecter aux données (workshop, transcript, web_search)
3. Tester génération initiale
4. Tester régénération avec exclusions

**Validation :** 10 besoins générés avec citations valides

---

## Étape 8 : Frontend Page 2 (Besoins)

**Objectif :** Interface complète pour besoins

**Actions :**
1. Composant `NeedCard`
2. État global (Zustand)
3. Boutons Générer / Valider
4. Champ commentaire

**Validation :** Interaction fluide, régénération fonctionne

---

## Étape 9 : UseCase Analysis Agent

**Objectif :** Générer Quick Wins + Structuration IA

**Actions :**
1. Implémenter prompts
2. Logique régénération intelligente (>= 5 validés)
3. Tester génération et régénération

**Validation :** Cas d'usage pertinents générés

---

## Étape 10 : Frontend Page 3 (Use Cases)

**Objectif :** Interface complète pour cas d'usage

**Actions :**
1. Composants `QuickWinCard` et `StructurationCard`
2. Gestion état sélectionné
3. Boutons Générer / Valider

**Validation :** Sélection et régénération fonctionnent

---

## Étape 11 : Report Generator

**Objectif :** Génération document Word final

**Actions :**
1. Implémenter `report_generator.py`
2. Template Word professionnel
3. Intégrer besoins et cas d'usage sélectionnés

**Validation :** Document Word téléchargeable et bien formaté

---

## Étape 12 : Frontend Page 4 (Résultats)

**Objectif :** Synthèse et téléchargement

**Actions :**
1. Affichage besoins validés
2. Affichage cas d'usage retenus
3. Bouton téléchargement rapport

**Validation :** Rapport se télécharge correctement

---

## Étape 13 : Polissage et tests

**Objectif :** Projet production-ready

**Actions :**
1. Gestion des erreurs
2. Feedbacks visuels (loaders, messages)
3. Tests unitaires agents
4. Documentation README complète

**Validation :** Projet stable et documenté

---

# ✅ 8. QUALITÉ ET STANDARDS

## Principes généraux

### 🌍 Conventions linguistiques

| Élément | Langue |
| --- | --- |
| **Code** (variables, fonctions, classes) | 🇬🇧 **Anglais** |
| **Commentaires** | 🇫🇷 **Français** |
| **Documentation** (README, TODO) | 🇫🇷 **Français** |
| **Messages de commit** | 🇫🇷 **Français** |

**Exemple :**
```python
# FR: Fonction qui génère des besoins à partir des données d'atelier
def generate_needs_from_workshop(workshop_data: dict) -> list:
    """
    FR: Génère une liste de besoins à partir des données d'atelier
    
    Args:
        workshop_data: Dictionnaire contenant les données parsées du fichier Excel
        
    Returns:
        Liste de 10 besoins avec titre et citations
    """
    # FR: Extraction des cas d'usage de la colonne B
    use_cases = workshop_data.get("use_cases", [])
    
    # FR: TODO - Implémenter la logique de génération
    pass
```

---

## Standards Backend (Python)

### 🐍 PEP8 et Typage

✅ **Obligatoire :**
- Respect strict de la **PEP8** (formatage, nommage, structure)
- **Typage strict** avec `mypy` pour toutes les fonctions
- Utilisation de **Pydantic** pour les modèles de données

**Exemple :**
```python
from pydantic import BaseModel
from typing import List, Dict, Optional

# FR: Modèle pour un besoin généré
class Need(BaseModel):
    id: str
    title: str
    citations: List[str]
    selected: bool = False
    edited: bool = False

# FR: Fonction typée strictement
def parse_excel_file(file_path: str) -> Dict[str, any]:
    """FR: Parse un fichier Excel et retourne les données structurées"""
    # FR: Logique de parsing
    pass
```

### 📦 Structure des modules

✅ **Règles :**
- Un module = une responsabilité claire
- Fichiers `__init__.py` avec exports explicites
- Maximum 300 lignes par fichier (si plus, découper)

### 🔧 Gestion des erreurs

✅ **Obligatoire :**
```python
import logging

logger = logging.getLogger(__name__)

# FR: Gestion des erreurs avec contexte clair
try:
    result = parse_pdf(file_path)
except FileNotFoundError:
    logger.error(f"FR: Fichier PDF introuvable : {file_path}")
    raise
except Exception as e:
    logger.error(f"FR: Erreur lors du parsing PDF : {str(e)}")
    raise
```

### 🧪 Tests

✅ **Recommandé :**
- Tests unitaires pour chaque agent
- Tests des parsers avec fichiers exemples
- Tests d'intégration du workflow LangGraph

---

## Standards Frontend (Next.js + TypeScript)

### 📐 TypeScript strict

✅ **Obligatoire :**
```typescript
// FR: Interface pour un besoin
interface Need {
  id: string;
  title: string;
  citations: string[];
  selected: boolean;
  edited: boolean;
}

// FR: Props typées pour composant
interface NeedCardProps {
  need: Need;
  onSelect: (id: string) => void;
  onEdit: (id: string, newTitle: string) => void;
}

// FR: Composant avec typage strict
const NeedCard: React.FC<NeedCardProps> = ({ need, onSelect, onEdit }) => {
  // FR: Logique du composant
};
```

### 🎨 ESLint + Prettier

✅ **Configuration :**
- ESLint avec règles React/Next.js
- Prettier pour formatage automatique
- Pre-commit hooks (optionnel)

### 🧩 Structure des composants

✅ **Règles :**
- Composants fonctionnels avec Hooks
- Props clairement typées
- Composants réutilisables dans `/components`
- Logique métier dans `/lib`

**Exemple :**
```typescript
// FR: Composant réutilisable pour carte de besoin
export const NeedCard: React.FC<NeedCardProps> = ({ need, onSelect }) => {
  // FR: État local pour édition
  const [isEditing, setIsEditing] = useState(false);
  
  // FR: Gestion de la sélection
  const handleSelect = () => {
    onSelect(need.id);
  };
  
  return (
    <div className="need-card">
      {/* FR: Interface carte besoin */}
    </div>
  );
};
```

---

## Standards LangGraph

### 🧠 Agents

✅ **Chaque agent doit avoir :**

1. **Un rôle unique et clair**
   ```python
   # FR: Agent responsable uniquement de la génération de besoins
   class NeedAnalysisAgent:
       """FR: Génère 10 besoins à partir des données combinées"""
       pass
   ```

2. **Input/Output explicites**
   ```python
   # FR: Input typé avec Pydantic
   class NeedAnalysisInput(BaseModel):
       workshop_data: Dict[str, any]
       transcript_data: List[Dict[str, any]]
       web_search_data: Dict[str, any]
   
   # FR: Output typé
   class NeedAnalysisOutput(BaseModel):
       needs: List[Need]
   ```

3. **Prompts versionnés**
   - Fichiers séparés dans `/prompts`
   - Commentaires français explicites
   - Historique des modifications

4. **Logging complet**
   ```python
   logger.info("FR: Début génération besoins")
   logger.debug(f"FR: Données workshop : {len(workshop_data)} ateliers")
   logger.info("FR: Génération besoins terminée : 10 besoins créés")
   ```

### 🔄 Workflows

✅ **Règles :**
- Workflow centralisé dans `/workflow`
- Chaînage explicite des agents
- Gestion des erreurs à chaque étape
- État partagé clair entre agents

---

## Standards Docker

### 🐳 Dockerfile

✅ **Bonnes pratiques :**
- Images officielles légères (`python:3.11-slim`, `node:20-alpine`)
- Multi-stage builds si possible
- `.dockerignore` pour exclure fichiers inutiles
- Variables d'environnement via `.env`

**Exemple Backend :**
```dockerfile
# FR: Image de base Python
FROM python:3.11-slim

# FR: Installation UV
RUN pip install uv

# FR: Copie des dépendances
COPY requirements.txt .
RUN uv pip install -r requirements.txt

# FR: Copie du code source
COPY . /app
WORKDIR /app

# FR: Commande de démarrage
CMD ["python", "main.py"]
```

### 🔧 docker-compose.yml

✅ **Structure :**
```yaml
version: '3.8'

services:
  # FR: Service backend Python + LangGraph
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend:/app
    networks:
      - app-network

  # FR: Service frontend Next.js
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    env_file:
      - .env
    depends_on:
      - backend
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

---

## Standards Git

### 📝 Messages de commit

✅ **Format :**
```
[TYPE] Description courte en français

Description détaillée si nécessaire
```

**Types :**
- `[FEAT]` : Nouvelle fonctionnalité
- `[FIX]` : Correction de bug
- `[REFACTOR]` : Refactorisation
- `[DOCS]` : Documentation
- `[STYLE]` : Formatage, style
- `[TEST]` : Tests

**Exemples :**
```
[FEAT] Ajout du NeedAnalysisAgent avec prompts de régénération
[FIX] Correction du parsing Excel pour colonnes vides
[REFACTOR] Séparation du code de parsing et d'analyse dans WorkshopAgent
```

### 🌿 Branches

✅ **Convention :**
- `main` : code stable
- `develop` : développement actif
- `feature/nom-feature` : nouvelle fonctionnalité
- `fix/nom-bug` : correction bug

---

## Checklist Qualité

### ✅ Backend

- [ ] Code en anglais, commentaires en français
- [ ] Typage strict avec mypy
- [ ] PEP8 respecté
- [ ] Modèles Pydantic pour données
- [ ] Logging complet
- [ ] Gestion erreurs explicite
- [ ] Tests unitaires agents
- [ ] Prompts versionnés

### ✅ Frontend

- [ ] Code TypeScript strict
- [ ] Props typées
- [ ] ESLint + Prettier configurés
- [ ] Composants réutilisables
- [ ] State management clair (Zustand)
- [ ] Gestion erreurs API
- [ ] Feedbacks visuels (loaders, messages)

### ✅ Docker

- [ ] Dockerfiles optimisés
- [ ] docker-compose.yml fonctionnel
- [ ] `.env` non versionné
- [ ] `.env.example` présent
- [ ] `.dockerignore` configuré

### ✅ Documentation

- [ ] README.md complet
- [ ] Installation claire
- [ ] Commande lancement : `docker compose up --build`
- [ ] Architecture expliquée
- [ ] Flux LangGraph documenté
- [ ] Conventions de code précisées

### ✅ Sécurité

- [ ] Aucune clé API hardcodée
- [ ] `.env` dans `.gitignore`
- [ ] Variables sensibles via environnement
- [ ] Validation inputs utilisateur

---

## 🎯 Mission Immédiate

### Objectif Étape 1 ✅

**Créer la structure complète du projet** avec :

1. **Dossiers :**
   - `/backend` avec tous les modules
   - `/frontend` avec structure Next.js
   - `/OLD` pour ancien code

2. **Fichiers de configuration :**
   - `.gitignore`
   - `.env.example`
   - `docker-compose.yml`
   - `README.md`

3. **Fichiers Python/TypeScript vides avec TODOs détaillés en français**

4. **Documentation initiale**

### Validation

- ✅ Structure visible dans l'IDE
- ✅ Fichiers de config présents
- ✅ TODOs clairs et actionnables
- ✅ README avec instructions de démarrage

---

> 🎯 **Mission pour Cursor**  
> 
> Générer la **structure complète du projet** selon les directives ci-dessus.  
> 
> **Règles impératives :**
> - Code en **anglais**, commentaires en **français**
> - **LangGraph SDK** obligatoire, gère 100% de la logique métier
> - Fichiers avec **TODOs explicites** en français
> - Architecture **modulaire** et **testable**
> - Documentation **complète** dès le départ
> 
> **Prochaines étapes :**
> 1. Valider la structure
> 2. Implémenter Docker
> 3. Créer le frontend (pages vides)
> 4. Implémenter les agents LangGraph étape par étape
> 
> L'objectif est de poser une **base solide** et prête à être développée **progressivement**.




