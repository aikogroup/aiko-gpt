# 🎯 Schéma Visuel Complet - aikoGPT

> **Diagramme complet** du flux de données et de l'architecture LangGraph

---

## 📊 Vue d'ensemble du système

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│                         UTILISATEUR (Frontend)                       │
│                                                                      │
│   📤 Uploads:                                                        │
│   - atelier.xlsx (Excel)                                            │
│   - transcript1.pdf, feedback.json                                  │
│   - "ACME Corporation" (nom entreprise)                            │
│                                                                      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            │ POST /api/upload
                            ↓
┌──────────────────────────────────────────────────────────────────────┐
│                        API BACKEND (FastAPI)                         │
│                                                                      │
│   📥 Route: POST /api/upload                                         │
│   - Sauvegarde fichiers dans /uploads/                             │
│   - Retourne file_paths                                             │
│                                                                      │
│   ✅ Route: GET /health                                              │
│   - Health check du serveur                                         │
│                                                                      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            │ Fichiers sauvegardés
                            ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH SERVER (Port 2024)                      │
│                                                                      │
│   🚀 POST /threads (créer une session)                               │
│   📊 POST /threads/{id}/runs (exécuter le workflow)                  │
│   📖 GET /threads/{id}/state (récupérer l'état)                      │
│                                                                      │
│   Configuration: langgraph.json                                     │
│   {                                                                  │
│     "graphs": {                                                      │
│       "need_analysis": "graph_factory:need_analysis"                │
│     },                                                               │
│     "http": {                                                        │
│       "app": "api.app:app"  ← Routes FastAPI custom                │
│     }                                                                │
│   }                                                                  │
│                                                                      │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            │ Exécution du graphe LangGraph
                            ↓
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│            📊 WORKFLOW LANGGRAPH (graph_factory.py)                  │
│                                                                      │
│  ╔═══════════════════════════════════════════════════════════════╗  │
│  ║                                                               ║  │
│  ║   StateGraph(NeedAnalysisState) ← État partagé typé          ║  │
│  ║                                                               ║  │
│  ║   ┌─────────────┐                                             ║  │
│  ║   │   START     │                                             ║  │
│  ║   └──────┬──────┘                                             ║  │
│  ║          │                                                     ║  │
│  ║          │ set_entry_point("workshop")                        ║  │
│  ║          ↓                                                     ║  │
│  ║   ┌──────────────────────┐                                    ║  │
│  ║   │  1️⃣ WorkshopAgent    │  Parse Excel + Analyse OpenAI     ║  │
│  ║   │  (workshop_agent)    │  ↓ workshop_data                  ║  │
│  ║   └──────────┬───────────┘                                    ║  │
│  ║              │ add_edge("workshop", "transcript")             ║  │
│  ║              ↓                                                 ║  │
│  ║   ┌──────────────────────┐                                    ║  │
│  ║   │  2️⃣ TranscriptAgent  │  Parse PDF/JSON                   ║  │
│  ║   │  (transcript_agent)  │  ↓ transcript_data                ║  │
│  ║   └──────────┬───────────┘                                    ║  │
│  ║              │ add_edge("transcript", "web_search")           ║  │
│  ║              ↓                                                 ║  │
│  ║   ┌──────────────────────┐                                    ║  │
│  ║   │  3️⃣ WebSearchAgent   │  Perplexity + OpenAI              ║  │
│  ║   │  (web_search_agent)  │  ↓ web_search_data (CONTEXTE)     ║  │
│  ║   └──────────┬───────────┘                                    ║  │
│  ║              │ add_edge("web_search", "need_analysis")        ║  │
│  ║              ↓                                                 ║  │
│  ║   ┌──────────────────────────┐                                ║  │
│  ║   │  4️⃣ NeedAnalysisAgent   │  ⭐ Génère 10 besoins          ║  │
│  ║   │  (need_analysis_agent)   │  ↓ needs (titre + citations)  ║  │
│  ║   └──────────┬───────────────┘                                ║  │
│  ║              │ add_edge("need_analysis", "use_case_analysis") ║  │
│  ║              ↓                                                 ║  │
│  ║   ┌──────────────────────────────┐                            ║  │
│  ║   │  5️⃣ UseCaseAnalysisAgent    │  8 QW + 10 SIA             ║  │
│  ║   │  (use_case_analysis_agent)   │  ↓ quick_wins +           ║  │
│  ║   │                              │    structuration_ia        ║  │
│  ║   └──────────┬───────────────────┘                            ║  │
│  ║              │ add_edge("use_case_analysis", "report")        ║  │
│  ║              ↓                                                 ║  │
│  ║   ┌──────────────────────┐                                    ║  │
│  ║   │  6️⃣ ReportAgent      │  Génère Word                      ║  │
│  ║   │  (report_agent)      │  ↓ report_path                    ║  │
│  ║   └──────────┬───────────┘                                    ║  │
│  ║              │ add_edge("report", END)                        ║  │
│  ║              ↓                                                 ║  │
│  ║   ┌──────────────────────┐                                    ║  │
│  ║   │       END            │                                    ║  │
│  ║   └──────────────────────┘                                    ║  │
│  ║                                                               ║  │
│  ║   workflow.compile() → CompiledGraph                          ║  │
│  ║                                                               ║  │
│  ╚═══════════════════════════════════════════════════════════════╝  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Flux de données : Le State en action

```
┌────────────────────────────────────────────────────────────────┐
│                  INITIALISATION DU STATE                       │
└────────────────────────────────────────────────────────────────┘

{
  "excel_file_path": "/uploads/atelier_20251022.xlsx",
  "pdf_json_file_paths": ["/uploads/doc1.pdf"],
  "company_name": "ACME Corp",
  "action": "generate_needs"
}

                            ↓
┌────────────────────────────────────────────────────────────────┐
│                  1️⃣ WORKSHOPAGENT                              │
│                                                                │
│  Reçoit: State (avec excel_file_path)                         │
│                                                                │
│  Traite:                                                       │
│    - Parse Excel avec openpyxl                                │
│    - Analyse avec OpenAI GPT-4o-mini                          │
│                                                                │
│  Retourne: {                                                   │
│    "workshop_data": {                                          │
│      "workshop_name": "Atelier Innovation IA",                │
│      "use_cases": [...],                                       │
│      "objectives": [...],                                      │
│      "gains": [...]                                            │
│    },                                                          │
│    "current_step": "workshop_completed"                        │
│  }                                                             │
└────────────────────────────────────────────────────────────────┘
                            ↓
                   LangGraph MERGE ↓

State = {
  "excel_file_path": "...",
  "company_name": "...",
  "workshop_data": {...},  ← NOUVEAU
  "current_step": "workshop_completed"  ← NOUVEAU
}

                            ↓
┌────────────────────────────────────────────────────────────────┐
│                  2️⃣ TRANSCRIPTAGENT                            │
│                                                                │
│  Reçoit: State (avec pdf_json_file_paths)                     │
│                                                                │
│  Traite:                                                       │
│    - Parse PDF avec PyPDF2                                    │
│    - Parse JSON                                                │
│    - Filtre sémantique avec OpenAI                            │
│                                                                │
│  Retourne: {                                                   │
│    "transcript_data": [                                        │
│      {                                                         │
│        "source": "doc1.pdf",                                   │
│        "citations": [...],                                     │
│        "frustrations": [...],                                  │
│        "expressed_needs": [...]                                │
│      }                                                         │
│    ],                                                          │
│    "current_step": "transcript_completed"                      │
│  }                                                             │
└────────────────────────────────────────────────────────────────┘
                            ↓
                   LangGraph MERGE ↓

State = {
  ...,
  "workshop_data": {...},
  "transcript_data": [...],  ← NOUVEAU
  "current_step": "transcript_completed"
}

                            ↓
┌────────────────────────────────────────────────────────────────┐
│                  3️⃣ WEBSEARCHAGENT                             │
│                                                                │
│  Reçoit: State (avec company_name)                            │
│                                                                │
│  Traite:                                                       │
│    - Recherche Perplexity API                                 │
│    - Structuration OpenAI                                     │
│                                                                │
│  Retourne: {                                                   │
│    "web_search_data": {                                        │
│      "company_name": "ACME Corp",                             │
│      "sector": "Industrie",                                    │
│      "size": "PME",                                            │
│      "context_summary": "...",                                 │
│      "fetched": true                                           │
│    },                                                          │
│    "current_step": "web_search_completed"                      │
│  }                                                             │
└────────────────────────────────────────────────────────────────┘
                            ↓
                   LangGraph MERGE ↓

State = {
  ...,
  "workshop_data": {...},
  "transcript_data": [...],
  "web_search_data": {...},  ← NOUVEAU (CONTEXTE)
  "current_step": "web_search_completed"
}

                            ↓
┌────────────────────────────────────────────────────────────────┐
│                  4️⃣ NEEDANALYSISAGENT ⭐                        │
│                                                                │
│  Reçoit: State COMPLET (workshop, transcript, web_search)     │
│                                                                │
│  Traite:                                                       │
│    - Formate workshop_data en texte                           │
│    - Formate transcript_data en citations                     │
│    - Formate web_search_data en contexte                      │
│    - Appelle OpenAI avec prompt structuré                     │
│    - Temperature 0.7 (créativité)                             │
│    - Force JSON output                                         │
│                                                                │
│  Retourne: {                                                   │
│    "needs": [                                                  │
│      {                                                         │
│        "id": "need_001",                                       │
│        "title": "Automatiser la saisie...",                   │
│        "citations": [                                          │
│          "Citation 1 - Source: Atelier",                      │
│          "Citation 2 - Source: doc1.pdf",                     │
│          ...  (5 au total)                                     │
│        ]                                                       │
│      },                                                        │
│      ... (10 au total)                                         │
│    ],                                                          │
│    "current_step": "needs_generated"                           │
│  }                                                             │
└────────────────────────────────────────────────────────────────┘
                            ↓
                   LangGraph MERGE ↓

State = {
  ...,
  "workshop_data": {...},
  "transcript_data": [...],
  "web_search_data": {...},
  "needs": [...],  ← NOUVEAU (10 besoins)
  "current_step": "needs_generated"
}

                            ↓
┌────────────────────────────────────────────────────────────────┐
│                  5️⃣ USECASEANALYSISAGENT                       │
│                                                                │
│  Reçoit: State (needs validés + contexte)                     │
│                                                                │
│  Traite:                                                       │
│    - Vérifie minimum 5 besoins validés                        │
│    - Génère 8 Quick Wins (ROI < 3 mois)                       │
│    - Génère 10 Structuration IA (ROI 3-12 mois)               │
│    - Technologies IA concrètes                                 │
│                                                                │
│  Retourne: {                                                   │
│    "quick_wins": [...],  (8)                                   │
│    "structuration_ia": [...],  (10)                            │
│    "current_step": "use_cases_generated"                       │
│  }                                                             │
└────────────────────────────────────────────────────────────────┘
                            ↓
                   LangGraph MERGE ↓

State = {
  ...,
  "needs": [...],
  "quick_wins": [...],  ← NOUVEAU
  "structuration_ia": [...],  ← NOUVEAU
  "current_step": "use_cases_generated"
}

                            ↓
┌────────────────────────────────────────────────────────────────┐
│                  6️⃣ REPORTAGENT                                │
│                                                                │
│  Reçoit: State (needs + use_cases sélectionnés)               │
│                                                                │
│  Traite:                                                       │
│    - Filtre éléments sélectionnés                             │
│    - Génère rapport Word avec python-docx                     │
│    - Sauvegarde dans /outputs                                 │
│                                                                │
│  Retourne: {                                                   │
│    "report_path": "/outputs/Rapport_..._.docx",               │
│    "current_step": "report_generated"                          │
│  }                                                             │
└────────────────────────────────────────────────────────────────┘
                            ↓
                   LangGraph MERGE ↓

STATE FINAL = {
  "excel_file_path": "...",
  "pdf_json_file_paths": [...],
  "company_name": "...",
  "workshop_data": {...},
  "transcript_data": [...],
  "web_search_data": {...},
  "needs": [...],
  "quick_wins": [...],
  "structuration_ia": [...],
  "report_path": "...",  ← NOUVEAU
  "current_step": "report_generated"
}
                            ↓
                     RETOUR FRONTEND
```

---

## 🔧 APIs LangGraph utilisées

### 1. StateGraph

```python
from langgraph.graph import StateGraph

workflow = StateGraph(NeedAnalysisState)
```

**Rôle :** Crée le container du workflow avec un état typé

**Fichier :** `backend/graph_factory.py` ligne 85

---

### 2. add_node()

```python
workflow.add_node("workshop", workshop_agent)
workflow.add_node("transcript", transcript_agent)
# ... etc
```

**Rôle :** Ajoute un agent comme nœud du graphe

**Signature :**
```python
def workshop_agent(
    state: NeedAnalysisState, 
    config: RunnableConfig
) -> Dict[str, Any]:
    # Retourne les champs à mettre à jour
    return {"workshop_data": {...}}
```

**Fichier :** `backend/graph_factory.py` lignes 100-105

---

### 3. set_entry_point() + add_edge()

```python
workflow.set_entry_point("workshop")
workflow.add_edge("workshop", "transcript")
workflow.add_edge("transcript", "web_search")
# ... etc
```

**Rôle :** Définit le flux d'exécution séquentiel

**Fichier :** `backend/graph_factory.py` lignes 120-147

---

### 4. compile()

```python
graph = workflow.compile()
```

**Rôle :** 
- Compile le workflow en graphe exécutable
- Valide la structure
- Optimise l'exécution

**Fichier :** `backend/graph_factory.py` ligne 188

---

### 5. LangGraph Server

**Commande :**
```bash
uv run langgraph dev
```

**Configuration :** `langgraph.json`

**Rôle :**
- Expose le graphe via HTTP
- Gère la persistence (threads)
- Intègre routes FastAPI custom
- Fournit API complète

**Endpoints générés :**
- `POST /threads` : Créer thread
- `POST /threads/{id}/runs` : Exécuter
- `GET /threads/{id}/state` : Récupérer état
- `GET /docs` : Documentation interactive

---

## 📝 Fichiers clés du projet

```
backend/
├── graph_factory.py              ⭐ Création du workflow LangGraph
│   ├── create_need_analysis_graph()
│   ├── StateGraph(NeedAnalysisState)
│   ├── add_node() × 6
│   ├── add_edge() × 6
│   └── compile()
│
├── agents/
│   ├── nodes.py                  🔗 Wrappers des agents
│   │   ├── workshop_agent()
│   │   ├── transcript_agent()
│   │   ├── web_search_agent()
│   │   ├── need_analysis_agent()
│   │   ├── use_case_analysis_agent()
│   │   └── report_agent()
│   │
│   ├── workshop_agent_impl.py    📊 Implémentation WorkshopAgent
│   │   ├── parse_excel_file()
│   │   ├── analyze_with_openai()
│   │   └── workshop_agent()
│   │
│   ├── transcript_agent_impl.py  📄 Implémentation TranscriptAgent
│   ├── web_search_agent_impl.py  🌐 Implémentation WebSearchAgent
│   ├── need_analysis_agent_impl.py 💡 Implémentation NeedAnalysisAgent
│   ├── use_case_analysis_agent_impl.py 🚀 Implémentation UseCaseAgent
│   └── report_agent_impl.py      📝 Implémentation ReportAgent
│
├── models/
│   └── graph_state.py            📦 NeedAnalysisState (TypedDict)
│
├── prompts/
│   ├── workshop_agent_prompts.py
│   ├── transcript_agent_prompts.py
│   ├── web_search_agent_prompts.py
│   ├── need_analysis_agent_prompts.py  ⭐ Prompts critiques
│   └── use_case_analysis_prompts.py
│
├── api/
│   ├── app.py                    🔌 Application FastAPI
│   └── upload_routes.py          📤 Routes upload fichiers
│
└── utils/
    ├── report_generator.py       📝 Génération Word
    └── token_tracker.py          📊 Suivi tokens (optionnel)

langgraph.json                    ⚙️ Configuration LangGraph Server
```

---

## 🎯 Points clés à retenir

### 1. LangGraph est le cerveau

```
✅ 100% de la logique métier dans le workflow
✅ Agents autonomes et orchestrés
✅ State partagé automatiquement
✅ API backend minimaliste
```

### 2. Le State est central

```
✅ Une seule source de vérité
✅ Chaque agent lit ET écrit
✅ LangGraph merge automatiquement
✅ Persistence gérée par LangGraph Server
```

### 3. Les agents sont simples

```
Signature:
  def agent(state: State, config: Config) -> Dict[str, Any]

Input:
  state : État complet (lecture)
  config : Configuration (modèle, etc.)

Output:
  Dict : Champs à mettre à jour dans le State
```

### 4. Le workflow est déclaratif

```python
# Définition claire et lisible
workflow = StateGraph(State)
workflow.add_node("a", agent_a)
workflow.add_node("b", agent_b)
workflow.set_entry_point("a")
workflow.add_edge("a", "b")
graph = workflow.compile()

# LangGraph gère TOUT automatiquement
```

### 5. LangGraph Server = Production ready

```
✅ API HTTP complète
✅ Persistence threads
✅ Streaming results
✅ Routes custom FastAPI
✅ Documentation auto
✅ Monitoring intégré
```

---

## 🚀 Commandes essentielles

```bash
# Lancer le projet complet (Docker)
docker compose up --build

# Accès
Frontend:  http://localhost:3000
Backend:   http://localhost:2024
API Docs:  http://localhost:2024/docs

# Logs
docker compose logs -f backend
docker compose logs -f frontend

# Arrêter
docker compose down
```

---

## 📚 Documentation

- **Guide complet :** `GUIDE_COMPLET_PROJET.md`
- **Ce schéma :** `SCHEMA_VISUEL_COMPLET.md`
- **Code commenté :**
  - `backend/graph_factory.py`
  - `backend/models/graph_state.py`
  - Tous les agents `_impl.py`

---

**Créé le :** 22 octobre 2025  
**Version :** 1.0  
**Projet :** aikoGPT - Analyse de besoins IA avec LangGraph

