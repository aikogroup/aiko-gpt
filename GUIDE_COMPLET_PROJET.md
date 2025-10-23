# 📖 Guide Complet du Projet aikoGPT

> **Guide technique complet** pour comprendre l'architecture, LangGraph, les agents, et le flux de données

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture Générale](#architecture-générale)
3. [LangGraph : Le Cœur du Projet](#langgraph--le-cœur-du-projet)
4. [Les 6 Agents du Workflow](#les-6-agents-du-workflow)
5. [Le State Partagé](#le-state-partagé)
6. [Flux de Données Complet](#flux-de-données-complet)
7. [API Backend](#api-backend)
8. [Frontend Next.js](#frontend-nextjs)
9. [Fichiers Clés et leur Rôle](#fichiers-clés-et-leur-rôle)

---

## 🎯 Vue d'ensemble

### Objectif du projet

aikoGPT est un **outil d'analyse automatisée** qui :
1. **Analyse** des fichiers Excel (ateliers) et PDF/JSON (transcriptions)
2. **Recherche** le contexte de l'entreprise via Perplexity
3. **Génère** 10 besoins métier avec citations
4. **Propose** des cas d'usage IA (Quick Wins + Structuration)
5. **Produit** un rapport Word téléchargeable

### Technologies principales

| Technologie | Version | Rôle |
|------------|---------|------|
| **LangGraph SDK** | 0.4.44 | ⭐ **Orchestration des agents** |
| **OpenAI API** | GPT-4o-mini | Analyse et génération |
| **Perplexity API** | - | Recherche contextuelle |
| **FastAPI** | - | Serveur HTTP backend |
| **Next.js** | 14.2.33 | Interface utilisateur |
| **Docker** | - | Conteneurisation |

---

## 🏗️ Architecture Générale

### Schéma global

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │  Upload  │→ │  Besoins │→ │Use Cases │→ │Résultats││
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘│
└────────────────────────┬────────────────────────────────┘
                         │ HTTP API
                         ↓
┌─────────────────────────────────────────────────────────┐
│              BACKEND (LangGraph Server)                 │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │         LANGGRAPH WORKFLOW (Graphe)             │  │
│  │                                                  │  │
│  │  ┌──────────┐      ┌──────────┐                │  │
│  │  │Workshop  │      │Transcript│                │  │
│  │  │Agent     │      │Agent     │                │  │
│  │  └────┬─────┘      └────┬─────┘                │  │
│  │       └────────┬─────────┘                      │  │
│  │                ↓                                 │  │
│  │       ┌────────────────┐                        │  │
│  │       │ WebSearch      │                        │  │
│  │       │ Agent          │                        │  │
│  │       └────────┬───────┘                        │  │
│  │                ↓                                 │  │
│  │       ┌────────────────┐                        │  │
│  │       │ NeedAnalysis   │                        │  │
│  │       │ Agent          │                        │  │
│  │       └────────┬───────┘                        │  │
│  │                ↓                                 │  │
│  │       ┌────────────────┐                        │  │
│  │       │ UseCaseAnalysis│                        │  │
│  │       │ Agent          │                        │  │
│  │       └────────┬───────┘                        │  │
│  │                ↓                                 │  │
│  │       ┌────────────────┐                        │  │
│  │       │ Report         │                        │  │
│  │       │ Agent          │                        │  │
│  │       └────────────────┘                        │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                         │
                         ↓
              ┌──────────────────┐
              │  SERVICES IA     │
              │  - OpenAI        │
              │  - Perplexity    │
              └──────────────────┘
```

### Principe fondamental

🔑 **LangGraph gère 100% de la logique métier**
- L'API backend est **uniquement technique** (upload fichiers, déclenchement)
- **Toute l'intelligence** est dans le workflow LangGraph
- Les agents sont **autonomes et orchestrés** automatiquement

---

## ⚡ LangGraph : Le Cœur du Projet

### Qu'est-ce que LangGraph ?

**LangGraph** est un framework pour créer des **workflows d'agents IA**. Il permet de :
- ✅ Définir un **graphe de tâches** (nodes + edges)
- ✅ Orchestrer plusieurs **agents autonomes**
- ✅ Partager un **état commun** entre agents
- ✅ Gérer les **flux conditionnels**
- ✅ Tracer et débugger facilement

### APIs LangGraph utilisées dans le projet

#### 1. **StateGraph** - Création du graphe

```python
from langgraph.graph import StateGraph, END

# FR: Création du graphe avec un état typé
workflow = StateGraph(NeedAnalysisState)
```

**Fichier :** `backend/graph_factory.py` ligne 57

**Rôle :** 
- Crée le conteneur du workflow
- Définit le type d'état partagé (`NeedAnalysisState`)

#### 2. **add_node()** - Ajouter des agents

```python
# FR: Ajouter les agents comme nodes
workflow.add_node("workshop", workshop_agent)
workflow.add_node("transcript", transcript_agent)
workflow.add_node("web_search", web_search_agent)
workflow.add_node("need_analysis", need_analysis_agent)
workflow.add_node("use_case_analysis", use_case_analysis_agent)
workflow.add_node("report", report_agent)
```

**Fichier :** `backend/graph_factory.py` lignes 60-65

**Rôle :**
- Chaque agent devient un **nœud** du graphe
- Nom du nœud (ex: `"workshop"`) + fonction Python

#### 3. **add_edge()** - Définir le flux

```python
# FR: Définir le flux d'exécution (edges)
workflow.set_entry_point("workshop")  # Point d'entrée
workflow.add_edge("workshop", "transcript")  # workshop → transcript
workflow.add_edge("transcript", "web_search")
workflow.add_edge("web_search", "need_analysis")
workflow.add_edge("need_analysis", "use_case_analysis")
workflow.add_edge("use_case_analysis", "report")
workflow.add_edge("report", END)  # Fin du workflow
```

**Fichier :** `backend/graph_factory.py` lignes 69-82

**Rôle :**
- Définit l'**ordre d'exécution** des agents
- Les données **circulent automatiquement** entre les nœuds via le State

#### 4. **compile()** - Compiler le graphe

```python
# FR: Compiler le graphe pour le rendre exécutable
graph = workflow.compile()
```

**Fichier :** `backend/graph_factory.py` ligne 103

**Rôle :**
- Transforme la définition en **graphe exécutable**
- Valide la structure (pas de boucles infinies, etc.)
- Prépare pour l'exécution

#### 5. **LangGraph Server** - Déploiement

Le serveur LangGraph est lancé via la commande :
```bash
uv run langgraph dev
```

**Configuration :** `langgraph.json`
```json
{
  "dependencies": ["./backend"],
  "graphs": {
    "need_analysis": "graph_factory:need_analysis"
  },
  "http": {
    "app": "api.app:app"
  }
}
```

**Rôle du serveur :**
- ✅ Expose le graphe via **API HTTP**
- ✅ Gère la **persistance** automatique
- ✅ Fournit un **endpoint** `/runs` pour exécuter
- ✅ Permet le **streaming** des résultats
- ✅ Intègre les **routes custom** FastAPI

### Comment LangGraph orchestre le workflow

#### Étape 1 : Initialisation du State

```python
initial_state = {
    "excel_file_path": "/uploads/atelier.xlsx",
    "pdf_json_file_paths": ["/uploads/doc1.pdf"],
    "company_name": "ACME Corp"
}
```

#### Étape 2 : Exécution séquentielle

```
START
  ↓
workshop_agent(state) 
  → Lit excel_file_path
  → Parse Excel
  → Appelle OpenAI
  → Retourne {"workshop_data": {...}}
  → LangGraph MERGE automatiquement dans state
  ↓
transcript_agent(state)
  → Lit pdf_json_file_paths
  → Parse PDF/JSON
  → Retourne {"transcript_data": [...]}
  → MERGE dans state
  ↓
web_search_agent(state)
  → Lit company_name
  → Appelle Perplexity
  → Retourne {"web_search_data": {...}}
  → MERGE dans state
  ↓
need_analysis_agent(state)
  → Lit workshop_data, transcript_data, web_search_data
  → Génère 10 besoins
  → Retourne {"needs": [...]}
  → MERGE dans state
  ↓
use_case_analysis_agent(state)
  → Lit needs (validés)
  → Génère Quick Wins + Structuration IA
  → Retourne {"quick_wins": [...], "structuration_ia": [...]}
  → MERGE dans state
  ↓
report_agent(state)
  → Lit needs, quick_wins, structuration_ia
  → Génère rapport Word
  → Retourne {"report_path": "/outputs/rapport.docx"}
  → MERGE dans state
  ↓
END
```

#### Étape 3 : State final

À la fin, le State contient **toutes les données** :
```python
{
    "excel_file_path": "...",
    "company_name": "...",
    "workshop_data": {...},
    "transcript_data": [...],
    "web_search_data": {...},
    "needs": [...],
    "quick_wins": [...],
    "structuration_ia": [...],
    "report_path": "/outputs/rapport.docx"
}
```

---

## 🤖 Les 6 Agents du Workflow

### 1. WorkshopAgent 🏭

**Fichier implémentation :** `backend/agents/workshop_agent_impl.py`
**Fichier node :** `backend/agents/nodes.py` lignes 22-44
**Prompts :** `backend/prompts/workshop_agent_prompts.py`

**Rôle :**
- Parse le fichier **Excel** (ateliers)
- Extrait 3 colonnes : nom_atelier, cas_usage, objectif_gain
- Analyse via **OpenAI** pour structurer

**Input (du State) :**
```python
{
    "excel_file_path": "/uploads/atelier.xlsx"
}
```

**Traitement :**
1. **Parsing Excel** (lignes 24-73)
   - Utilise `openpyxl`
   - Ignore les lignes vides
   - Extrait colonnes A, B, C

2. **Analyse OpenAI** (lignes 76-126)
   - Appelle GPT-4o-mini
   - Utilise `WORKSHOP_ANALYSIS_SYSTEM_PROMPT`
   - Force réponse JSON avec `response_format={"type": "json_object"}`

**Output (ajouté au State) :**
```python
{
    "workshop_data": {
        "workshop_name": "Atelier Innovation IA",
        "use_cases": ["Automatiser la saisie", "Analyser les feedbacks"],
        "objectives": ["Gagner du temps", "Améliorer la qualité"],
        "gains": ["30% de temps économisé"],
        "main_themes": ["Automatisation", "Analyse"],
        "summary": "Résumé de l'atelier...",
        "raw_data": [...]  # Données brutes Excel
    },
    "current_step": "workshop_completed"
}
```

**Technologies :**
- `openpyxl` : parsing Excel
- `OpenAI API` : analyse LLM

---

### 2. TranscriptAgent 📄

**Fichier implémentation :** `backend/agents/transcript_agent_impl.py`
**Fichier node :** `backend/agents/nodes.py` lignes 47-69
**Parsers :** 
- `backend/process_transcript/pdf_parser.py`
- `backend/process_transcript/json_parser.py`
**Prompts :** `backend/prompts/transcript_agent_prompts.py`

**Rôle :**
- Parse les fichiers **PDF** et **JSON** (transcriptions)
- Extrait citations, frustrations, besoins exprimés
- Filtre via **OpenAI** (sémantique)

**Input (du State) :**
```python
{
    "pdf_json_file_paths": [
        "/uploads/transcript1.pdf",
        "/uploads/feedback.json"
    ]
}
```

**Traitement :**
1. **Parsing PDF** (avec PyPDF2)
2. **Parsing JSON** (extraction citations)
3. **Filtrage sémantique** (OpenAI)

**Output (ajouté au State) :**
```python
{
    "transcript_data": [
        {
            "source": "transcript1.pdf",
            "citations": [
                "On perd trop de temps sur la saisie manuelle",
                "Les erreurs sont fréquentes dans les rapports"
            ],
            "frustrations": [
                "Processus répétitif et chronophage"
            ],
            "expressed_needs": [
                "Automatisation de la saisie"
            ]
        },
        {
            "source": "feedback.json",
            "citations": [...],
            ...
        }
    ],
    "current_step": "transcript_completed"
}
```

**Technologies :**
- `PyPDF2` : parsing PDF
- `json` : parsing JSON
- `OpenAI API` : filtrage sémantique

---

### 3. WebSearchAgent 🌐

**Fichier implémentation :** `backend/agents/web_search_agent_impl.py`
**Fichier node :** `backend/agents/nodes.py` lignes 72-98
**Prompts :** `backend/prompts/web_search_agent_prompts.py`

**Rôle :**
- Recherche contexte entreprise via **Perplexity**
- Enrichit avec **OpenAI** pour structurer
- ⚠️ **CONTEXTE UNIQUEMENT** - ne génère PAS de besoins

**Input (du State) :**
```python
{
    "company_name": "ACME Corporation"
}
```

**Traitement :**
1. **Recherche Perplexity** (API Sonar)
2. **Structuration OpenAI** (secteur, taille, actualités)

**Output (ajouté au State) :**
```python
{
    "web_search_data": {
        "company_name": "ACME Corporation",
        "sector": "Industrie manufacturière",
        "size": "PME (150 employés)",
        "location": "France, Lyon",
        "recent_news": [
            "Lancement nouvelle gamme de produits",
            "Investissement dans la transformation digitale"
        ],
        "sector_challenges": [
            "Concurrence internationale accrue",
            "Besoin d'optimisation des processus"
        ],
        "context_summary": "ACME est une PME industrielle...",
        "fetched": true
    },
    "current_step": "web_search_completed"
}
```

**Technologies :**
- `Perplexity API` : recherche contextuelle
- `OpenAI API` : structuration

---

### 4. NeedAnalysisAgent 💡 (AGENT CRITIQUE)

**Fichier implémentation :** `backend/agents/need_analysis_agent_impl.py`
**Fichier node :** `backend/agents/nodes.py` lignes 101-132
**Prompts :** `backend/prompts/need_analysis_agent_prompts.py`

**Rôle :**
- **Génère 10 besoins métier** avec 5 citations chacun
- Gère la **régénération** (exclusion de besoins)
- ⭐ **Cœur de la valeur métier**

**Input (du State) :**
```python
{
    "workshop_data": {...},       # Données Excel
    "transcript_data": [...],     # Données PDF/JSON
    "web_search_data": {...},     # Contexte entreprise
    "action": "generate_needs",   # ou "regenerate_needs"
    "excluded_needs": [],         # Titres à exclure
    "user_comment": ""            # Instructions utilisateur
}
```

**Traitement :**

1. **Formatage des données** (lignes 23-136)
   - Convertit workshop_data en texte lisible
   - Convertit transcript_data en citations
   - Convertit web_search_data en contexte

2. **Appel OpenAI** (lignes 139-239)
   - **Si génération initiale :** `NEED_ANALYSIS_INITIAL_USER_PROMPT`
   - **Si régénération :** `NEED_ANALYSIS_REGENERATION_USER_PROMPT` + excluded_needs
   - Temperature 0.7 (créativité)
   - Force réponse JSON

3. **Validation** (lignes 207-216)
   - Max 10 besoins
   - Max 5 citations par besoin
   - Normalisation IDs

**Output (ajouté au State) :**
```python
{
    "needs": [
        {
            "id": "need_001",
            "title": "Automatiser la saisie des données produit",
            "citations": [
                "On passe 2h par jour sur la saisie manuelle - Atelier Innovation",
                "Les erreurs de saisie coûtent cher - transcript1.pdf",
                "Besoin d'un système intelligent - feedback.json",
                "La saisie est répétitive et source d'erreurs - Atelier",
                "Automatisation prioritaire selon l'équipe - transcript2.pdf"
            ],
            "selected": false,
            "edited": false
        },
        // ... 9 autres besoins
    ],
    "current_step": "needs_generated"
}
```

**Règles métier critiques :**
- ✅ Citations issues de **workshop_data + transcript_data** (sources PRINCIPALES)
- ✅ web_search_data = **CONTEXTE uniquement**
- ✅ Pas de citations sans source
- ✅ Thèmes uniques (pas de doublons)

**Technologies :**
- `OpenAI API` : génération intelligente

---

### 5. UseCaseAnalysisAgent 🚀

**Fichier implémentation :** `backend/agents/use_case_analysis_agent_impl.py`
**Fichier node :** `backend/agents/nodes.py` lignes 135-178
**Prompts :** `backend/prompts/use_case_analysis_prompts.py`

**Rôle :**
- Génère **8 Quick Wins** (ROI < 3 mois)
- Génère **10 Structuration IA** (ROI 3-12 mois)
- Gère la **régénération intelligente**

**Input (du State) :**
```python
{
    "validated_needs": [...],     # Besoins validés (min 5)
    "workshop_data": {...},
    "transcript_data": [...],
    "web_search_data": {...},
    "action": "generate_use_cases",
    "validated_quick_wins": [],
    "validated_structuration_ia": []
}
```

**Traitement :**

1. **Vérification minimale** (au moins 5 besoins validés)

2. **Appel OpenAI**
   - Génère 8 Quick Wins
   - Génère 10 Structuration IA
   - Technologies IA concrètes (LLM, RAG, OCR, ML, NLP, etc.)

3. **Logique de régénération intelligente**
   ```python
   if len(validated_quick_wins) >= 5:
       # Ne régénère RIEN pour Quick Wins
       pass
   else:
       # Régénère Quick Wins manquants
   ```

**Output (ajouté au State) :**
```python
{
    "quick_wins": [
        {
            "id": "uc_qw_001",
            "category": "quick_win",
            "title": "Chatbot FAQ automatisé",
            "description": "Implémenter un chatbot pour répondre...",
            "ai_technologies": ["LLM", "RAG", "Embeddings"],
            "selected": false
        },
        // ... 7 autres Quick Wins
    ],
    "structuration_ia": [
        {
            "id": "uc_sia_001",
            "category": "structuration_ia",
            "title": "Plateforme de knowledge management IA",
            "description": "Créer une plateforme centralisée...",
            "ai_technologies": ["RAG", "Vector Database", "LLM"],
            "selected": false
        },
        // ... 9 autres Structuration IA
    ],
    "current_step": "use_cases_generated"
}
```

**Technologies :**
- `OpenAI API` : génération cas d'usage

---

### 6. ReportAgent 📝

**Fichier implémentation :** `backend/agents/report_agent_impl.py`
**Fichier node :** `backend/agents/nodes.py` lignes 181-203
**Utilitaire :** `backend/utils/report_generator.py`

**Rôle :**
- Génère le **rapport Word final**
- Formate professionnellement
- Inclut besoins + cas d'usage sélectionnés

**Input (du State) :**
```python
{
    "needs": [...],              # Besoins sélectionnés
    "quick_wins": [...],         # QW sélectionnés
    "structuration_ia": [...]    # SIA sélectionnés
}
```

**Traitement :**

1. **Filtrage** (besoins/UC sélectionnés uniquement)
2. **Génération Word** avec `python-docx`
3. **Sauvegarde** dans `/outputs`

**Output (ajouté au State) :**
```python
{
    "report_path": "/outputs/Rapport_Besoins_IA_Entreprise_20251022_143919.docx",
    "current_step": "report_generated"
}
```

**Technologies :**
- `python-docx` : génération Word

---

## 📦 Le State Partagé

**Fichier :** `backend/models/graph_state.py`

### Structure complète

```python
class NeedAnalysisState(TypedDict):
    # FR: Inputs initiaux
    excel_file_path: Optional[str]
    pdf_json_file_paths: Annotated[List[str], add]
    company_name: Optional[str]
    
    # FR: Données parsées
    workshop_data: Optional[Dict]
    transcript_data: Optional[List[Dict]]
    web_search_data: Optional[Dict]
    
    # FR: Besoins
    needs: Optional[List[Dict]]
    validated_needs: Annotated[List[Dict], add]
    excluded_needs: Annotated[List[str], add]
    
    # FR: Cas d'usage
    quick_wins: Optional[List[Dict]]
    structuration_ia: Optional[List[Dict]]
    validated_quick_wins: Annotated[List[Dict], add]
    validated_structuration_ia: Annotated[List[Dict], add]
    
    # FR: Rapport
    report_path: Optional[str]
    
    # FR: Métadonnées
    user_comment: Optional[str]
    action: Optional[str]
    errors: Annotated[List[str], add]
    current_step: Optional[str]
```

### Annotations importantes

**`Annotated[List[...], add]`** :
- Indique à LangGraph de **fusionner** les listes (ne pas écraser)
- Exemple : `excluded_needs` s'accumule entre les exécutions

**`Optional[...]`** :
- Champ peut être vide initialement
- Rempli progressivement par les agents

---

## 🌊 Flux de Données Complet

### Scénario 1 : Génération initiale

```
USER (Frontend)
  ↓ Upload fichiers + nom entreprise
  ↓ POST /api/upload
API Backend
  ↓ Sauvegarde fichiers → /uploads/xxx
  ↓ Retourne file_paths
  ↓
USER (Frontend)  
  ↓ POST /threads/{thread_id}/runs
  ↓ Body: { 
      "assistant_id": "need_analysis",
      "input": {
        "excel_file_path": "/uploads/atelier.xlsx",
        "pdf_json_file_paths": ["/uploads/doc1.pdf"],
        "company_name": "ACME",
        "action": "generate_needs"
      }
    }
LangGraph Server
  ↓ Initialise State
  ↓ Exécute workflow :
  ↓   1. WorkshopAgent → workshop_data
  ↓   2. TranscriptAgent → transcript_data
  ↓   3. WebSearchAgent → web_search_data
  ↓   4. NeedAnalysisAgent → needs (10)
  ↓   5. UseCaseAnalysisAgent → quick_wins + structuration_ia
  ↓   6. ReportAgent → report_path
  ↓ Retourne State final
  ↓
Frontend
  ↓ Affiche les 10 besoins
  ↓ Page /needs
```

### Scénario 2 : Régénération besoins

```
USER (Frontend)
  ↓ Sélectionne 5 besoins
  ↓ Clique "Générer" avec commentaire
  ↓ POST /threads/{thread_id}/runs
  ↓ Body: {
      "assistant_id": "need_analysis",
      "input": {
        "action": "regenerate_needs",
        "excluded_needs": ["Titre besoin 1", "Titre besoin 2", ...],
        "user_comment": "Plus axé sur l'automatisation"
      }
    }
LangGraph Server
  ↓ Reprend State existant (workshop_data, transcript_data déjà là)
  ↓ Exécute NeedAnalysisAgent
  ↓   → Utilise REGENERATION_PROMPT
  ↓   → Exclut les besoins listés
  ↓   → Génère 10 NOUVEAUX besoins
  ↓ Retourne State mis à jour
  ↓
Frontend
  ↓ Affiche 10 nouveaux besoins
  ↓ L'utilisateur peut recommencer ou valider
```

### Scénario 3 : Génération cas d'usage

```
USER (Frontend)
  ↓ Valide 5+ besoins
  ↓ Navigue vers /usecases
  ↓ POST /threads/{thread_id}/runs
  ↓ Body: {
      "assistant_id": "need_analysis",
      "input": {
        "action": "generate_use_cases",
        "validated_needs": [...]  # 5+ besoins
      }
    }
LangGraph Server
  ↓ Exécute UseCaseAnalysisAgent
  ↓   → Génère 8 Quick Wins
  ↓   → Génère 10 Structuration IA
  ↓ Retourne quick_wins + structuration_ia
  ↓
Frontend
  ↓ Affiche les cas d'usage
  ↓ Page /usecases
```

---

## 🔌 API Backend

### Architecture API

```
backend/api/
├── app.py              # Application FastAPI principale
├── upload_routes.py    # Routes d'upload de fichiers
└── routes.py           # (vide - à implémenter si besoin)
```

### Routes disponibles

#### 1. GET `/health`

**Fichier :** `backend/api/app.py` ligne 36

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "aikoGPT"}
```

**Utilisation :** Vérifier que le serveur fonctionne

#### 2. POST `/api/upload`

**Fichier :** `backend/api/upload_routes.py`

**Rôle :** Upload de fichiers Excel, PDF, JSON

**Body (multipart/form-data) :**
```
excel_file: File
pdf_json_files: File[]
```

**Réponse :**
```json
{
  "excel_file_path": "/uploads/atelier_20251022_143919.xlsx",
  "pdf_json_file_paths": [
    "/uploads/doc1_20251022_143919.pdf",
    "/uploads/feedback_20251022_143919.json"
  ]
}
```

#### 3. LangGraph Routes (auto-générées)

LangGraph Server ajoute automatiquement :

**POST `/threads`**
- Créer un nouveau thread (session)

**POST `/threads/{thread_id}/runs`**
- Exécuter le workflow

**GET `/threads/{thread_id}/runs/{run_id}`**
- Récupérer le statut d'une exécution

**GET `/threads/{thread_id}/state`**
- Récupérer l'état actuel du thread

**Voir documentation complète :** http://localhost:2024/docs

---

## 💻 Frontend Next.js

### Structure

```
frontend/src/
├── app/
│   ├── page.tsx           # Page 1 : Upload
│   ├── needs/page.tsx     # Page 2 : Besoins
│   ├── usecases/page.tsx  # Page 3 : Cas d'usage
│   └── results/page.tsx   # Page 4 : Résultats
├── components/
│   ├── SideNav.tsx        # Navigation latérale
│   ├── NeedCard.tsx       # (à créer) Carte besoin
│   └── UseCaseCard.tsx    # (à créer) Carte cas d'usage
└── lib/
    ├── api-client.ts      # Appels API
    ├── store.ts           # State management (Zustand)
    └── schemas.ts         # Types TypeScript
```

### Communication Frontend ↔ Backend

**Fichier :** `frontend/src/lib/api-client.ts`

```typescript
// FR: Upload de fichiers
export async function uploadFiles(
  excelFile: File,
  pdfJsonFiles: File[]
): Promise<UploadResponse> {
  // POST /api/upload
}

// FR: Exécuter le workflow LangGraph
export async function runWorkflow(
  threadId: string,
  input: WorkflowInput
): Promise<WorkflowOutput> {
  // POST /threads/{threadId}/runs
}
```

---

## 📂 Fichiers Clés et leur Rôle

### Backend

| Fichier | Rôle | Lignes importantes |
|---------|------|-------------------|
| `backend/graph_factory.py` | **Créer le graphe LangGraph** | 57: StateGraph<br>60-65: add_node<br>69-82: add_edge<br>103: compile |
| `backend/agents/nodes.py` | **Wrapper des agents** (entry points) | 22-44: workshop<br>47-69: transcript<br>72-98: web_search<br>101-132: need_analysis<br>135-178: use_case<br>181-203: report |
| `backend/agents/workshop_agent_impl.py` | **Implémentation WorkshopAgent** | 24-73: parse_excel<br>76-126: analyze_openai<br>129-204: workshop_agent |
| `backend/agents/need_analysis_agent_impl.py` | **Implémentation NeedAnalysisAgent** ⭐ | 139-239: generate_needs_with_openai<br>242-305: need_analysis_agent |
| `backend/models/graph_state.py` | **Définition du State partagé** | 12-49: NeedAnalysisState |
| `backend/prompts/need_analysis_agent_prompts.py` | **Prompts génération besoins** | Tous les prompts système et user |
| `backend/api/app.py` | **Application FastAPI** | 17-30: Configuration<br>36-39: Health check |
| `backend/api/upload_routes.py` | **Routes upload** | Upload fichiers |
| `langgraph.json` | **Configuration LangGraph Server** | 6: Graphe<br>9: App FastAPI custom |

### Frontend

| Fichier | Rôle |
|---------|------|
| `frontend/src/lib/api-client.ts` | Appels API vers backend |
| `frontend/src/lib/store.ts` | State management global (Zustand) |
| `frontend/src/app/page.tsx` | Page 1 : Upload fichiers |
| `frontend/src/app/needs/page.tsx` | Page 2 : Gestion besoins |
| `frontend/src/app/usecases/page.tsx` | Page 3 : Cas d'usage |
| `frontend/src/app/results/page.tsx` | Page 4 : Téléchargement rapport |

### Configuration

| Fichier | Rôle |
|---------|------|
| `.env` | Clés API (OPENAI_API_KEY, PERPLEXITY_API_KEY) |
| `docker-compose.yml` | Configuration Docker (backend + frontend) |
| `Dockerfile.backend` | Image Docker backend |
| `Dockerfile.frontend` | Image Docker frontend |
| `backend/pyproject.toml` | Dépendances Python (uv) |
| `frontend/package.json` | Dépendances Node.js |

---

## 🎯 Points Clés à Retenir

### 1. LangGraph = Cerveau du projet

- ✅ **100% de la logique métier** dans le workflow
- ✅ Les agents sont **autonomes et orchestrés**
- ✅ Le State est **partagé automatiquement**
- ✅ L'API backend est **minimaliste** (upload + déclenchement)

### 2. Le State est central

- ✅ Chaque agent **lit** et **écrit** dans le State
- ✅ LangGraph **merge** automatiquement les updates
- ✅ Le State **persiste** entre les exécutions (threads)

### 3. Les prompts sont critiques

- ✅ Tous dans `/prompts` (versionnés)
- ✅ **System Prompt** : rôle et règles
- ✅ **User Prompt** : données + instructions
- ✅ Différents prompts pour génération vs régénération

### 4. Architecture modulaire

- ✅ Chaque agent = **1 responsabilité**
- ✅ Agents **testables isolément**
- ✅ Facile d'**ajouter de nouveaux agents**

### 5. Flux asynchrone

- ✅ Frontend → Upload fichiers
- ✅ Frontend → Déclenche workflow (thread)
- ✅ LangGraph → Exécute agents séquentiellement
- ✅ Frontend → Récupère résultats (polling ou streaming)

---

## 📚 Ressources

- **Documentation LangGraph :** https://langchain-ai.github.io/langgraph/
- **API LangGraph Server :** http://localhost:2024/docs (quand lancé)
- **DeepWiki LangGraph :** Utiliser l'outil MCP pour approfondir

---

## 🚀 Prochaines Étapes

1. ✅ **Projet lancé** - Backend + Frontend opérationnels
2. 🔄 **Tester le workflow complet** avec fichiers d'exemple
3. 📝 **Ajuster les prompts** si nécessaire
4. 🎨 **Améliorer l'UI** (NeedCard, UseCaseCard)
5. 🧪 **Tests unitaires** des agents
6. 📊 **Monitoring** et logs détaillés

---

**Créé le :** 22 octobre 2025
**Auteur :** Guide généré pour comprendre aikoGPT
**Version :** 1.0

