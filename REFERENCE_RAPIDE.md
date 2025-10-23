# 📖 Référence Rapide - aikoGPT

> Index rapide pour retrouver n'importe quelle fonction, API ou concept dans le projet

---

## 🎯 Où trouver quoi ?

### Vous voulez comprendre...

| Sujet | Fichier à lire | Section |
|-------|---------------|---------|
| **Comment LangGraph orchestre le workflow** | `backend/graph_factory.py` | Fonction `create_need_analysis_graph()` |
| **La structure du State partagé** | `backend/models/graph_state.py` | Classe `NeedAnalysisState` |
| **Comment un agent est appelé** | `backend/agents/nodes.py` | Toutes les fonctions |
| **Parsing du fichier Excel** | `backend/agents/workshop_agent_impl.py` | Fonction `parse_excel_file()` |
| **Génération des besoins** | `backend/agents/need_analysis_agent_impl.py` | Fonction `generate_needs_with_openai()` |
| **Comment fonctionne Perplexity** | `backend/agents/web_search_agent_impl.py` | Tout le fichier |
| **Génération du rapport Word** | `backend/utils/report_generator.py` | Tout le fichier |
| **Routes API custom** | `backend/api/upload_routes.py` | Routes d'upload |
| **Configuration LangGraph Server** | `langgraph.json` | Configuration complète |
| **Architecture complète** | `GUIDE_COMPLET_PROJET.md` | Tout le guide |
| **Schémas visuels** | `SCHEMA_VISUEL_COMPLET.md` | Diagrammes ASCII |

---

## 📊 APIs LangGraph - Référence

### StateGraph

```python
from langgraph.graph import StateGraph

workflow = StateGraph(NeedAnalysisState)
```

**Fichier :** `backend/graph_factory.py` ligne 85  
**Doc :** Crée le container du workflow

---

### add_node()

```python
workflow.add_node("workshop", workshop_agent)
```

**Fichier :** `backend/graph_factory.py` lignes 100-105  
**Doc :** Ajoute un agent au graphe  
**Signature agent :**
```python
def agent(state: State, config: RunnableConfig) -> Dict[str, Any]
```

---

### set_entry_point()

```python
workflow.set_entry_point("workshop")
```

**Fichier :** `backend/graph_factory.py` ligne 120  
**Doc :** Définit le point d'entrée du workflow

---

### add_edge()

```python
workflow.add_edge("workshop", "transcript")
```

**Fichier :** `backend/graph_factory.py` lignes 123-147  
**Doc :** Connecte deux agents (flux séquentiel)

---

### compile()

```python
graph = workflow.compile()
```

**Fichier :** `backend/graph_factory.py` ligne 188  
**Doc :** Compile le workflow en graphe exécutable

---

## 🤖 Agents - Référence rapide

### 1. WorkshopAgent

| Aspect | Détail |
|--------|--------|
| **Fichier implémentation** | `backend/agents/workshop_agent_impl.py` |
| **Fichier node** | `backend/agents/nodes.py` lignes 22-44 |
| **Prompts** | `backend/prompts/workshop_agent_prompts.py` |
| **Input (State)** | `excel_file_path` |
| **Output (State)** | `workshop_data` |
| **Technologies** | openpyxl, OpenAI API |
| **Rôle** | Parse Excel + Analyse avec LLM |

**Fonctions principales :**
- `parse_excel_file()` : Lignes 24-73
- `analyze_with_openai()` : Lignes 76-126
- `workshop_agent()` : Lignes 129-204

---

### 2. TranscriptAgent

| Aspect | Détail |
|--------|--------|
| **Fichier implémentation** | `backend/agents/transcript_agent_impl.py` |
| **Fichier node** | `backend/agents/nodes.py` lignes 47-69 |
| **Prompts** | `backend/prompts/transcript_agent_prompts.py` |
| **Input (State)** | `pdf_json_file_paths` |
| **Output (State)** | `transcript_data` |
| **Technologies** | PyPDF2, json, OpenAI API |
| **Rôle** | Parse PDF/JSON + Filtre sémantique |

**Parsers :**
- `backend/process_transcript/pdf_parser.py`
- `backend/process_transcript/json_parser.py`

---

### 3. WebSearchAgent

| Aspect | Détail |
|--------|--------|
| **Fichier implémentation** | `backend/agents/web_search_agent_impl.py` |
| **Fichier node** | `backend/agents/nodes.py` lignes 72-98 |
| **Prompts** | `backend/prompts/web_search_agent_prompts.py` |
| **Input (State)** | `company_name` |
| **Output (State)** | `web_search_data` |
| **Technologies** | Perplexity API, OpenAI API |
| **Rôle** | Recherche contexte entreprise |

⚠️ **IMPORTANT :** Fournit uniquement le CONTEXTE, ne génère PAS de besoins

---

### 4. NeedAnalysisAgent ⭐

| Aspect | Détail |
|--------|--------|
| **Fichier implémentation** | `backend/agents/need_analysis_agent_impl.py` |
| **Fichier node** | `backend/agents/nodes.py` lignes 101-132 |
| **Prompts** | `backend/prompts/need_analysis_agent_prompts.py` |
| **Input (State)** | `workshop_data`, `transcript_data`, `web_search_data`, `action`, `excluded_needs`, `user_comment` |
| **Output (State)** | `needs` (10 besoins) |
| **Technologies** | OpenAI API |
| **Rôle** | Génère 10 besoins avec 5 citations |

**Fonctions principales :**
- `format_workshop_data_for_prompt()` : Lignes 23-57
- `format_transcript_data_for_prompt()` : Lignes 60-96
- `format_web_search_data_for_prompt()` : Lignes 99-136
- `generate_needs_with_openai()` : Lignes 139-239 ⭐
- `need_analysis_agent()` : Lignes 242-305

**Prompts :**
- `NEED_ANALYSIS_SYSTEM_PROMPT` : Rôle et règles
- `NEED_ANALYSIS_INITIAL_USER_PROMPT` : Génération initiale
- `NEED_ANALYSIS_REGENERATION_USER_PROMPT` : Régénération avec exclusions

---

### 5. UseCaseAnalysisAgent

| Aspect | Détail |
|--------|--------|
| **Fichier implémentation** | `backend/agents/use_case_analysis_agent_impl.py` |
| **Fichier node** | `backend/agents/nodes.py` lignes 135-178 |
| **Prompts** | `backend/prompts/use_case_analysis_prompts.py` |
| **Input (State)** | `validated_needs`, `workshop_data`, `transcript_data`, `web_search_data` |
| **Output (State)** | `quick_wins` (8), `structuration_ia` (10) |
| **Technologies** | OpenAI API |
| **Rôle** | Génère Quick Wins + Structuration IA |

**Logique de régénération :**
- Si >= 5 validés dans une catégorie → ne régénère RIEN

---

### 6. ReportAgent

| Aspect | Détail |
|--------|--------|
| **Fichier implémentation** | `backend/agents/report_agent_impl.py` |
| **Fichier node** | `backend/agents/nodes.py` lignes 181-203 |
| **Utilitaire** | `backend/utils/report_generator.py` |
| **Input (State)** | `needs`, `quick_wins`, `structuration_ia` |
| **Output (State)** | `report_path` |
| **Technologies** | python-docx |
| **Rôle** | Génère rapport Word final |

---

## 📦 Le State (NeedAnalysisState)

**Fichier :** `backend/models/graph_state.py`

### Structure complète

```python
class NeedAnalysisState(TypedDict):
    # Inputs
    excel_file_path: Optional[str]
    pdf_json_file_paths: Annotated[List[str], add]
    company_name: Optional[str]
    
    # Données parsées
    workshop_data: Optional[Dict]
    transcript_data: Optional[List[Dict]]
    web_search_data: Optional[Dict]
    
    # Besoins
    needs: Optional[List[Dict]]
    validated_needs: Annotated[List[Dict], add]
    excluded_needs: Annotated[List[str], add]
    
    # Cas d'usage
    quick_wins: Optional[List[Dict]]
    structuration_ia: Optional[List[Dict]]
    validated_quick_wins: Annotated[List[Dict], add]
    validated_structuration_ia: Annotated[List[Dict], add]
    
    # Rapport
    report_path: Optional[str]
    
    # Métadonnées
    user_comment: Optional[str]
    action: Optional[str]
    errors: Annotated[List[str], add]
    current_step: Optional[str]
```

### Champs importants

| Champ | Type | Rôle | Généré par | Utilisé par |
|-------|------|------|------------|-------------|
| `excel_file_path` | `Optional[str]` | Chemin Excel | Frontend | WorkshopAgent |
| `workshop_data` | `Optional[Dict]` | Données Excel structurées | WorkshopAgent | NeedAnalysisAgent |
| `transcript_data` | `Optional[List[Dict]]` | Citations PDF/JSON | TranscriptAgent | NeedAnalysisAgent |
| `web_search_data` | `Optional[Dict]` | Contexte entreprise | WebSearchAgent | NeedAnalysisAgent (contexte) |
| `needs` | `Optional[List[Dict]]` | 10 besoins générés | NeedAnalysisAgent | Frontend, UseCaseAgent |
| `excluded_needs` | `Annotated[List[str], add]` | Besoins à exclure | Frontend | NeedAnalysisAgent |
| `quick_wins` | `Optional[List[Dict]]` | 8 Quick Wins | UseCaseAgent | Frontend, ReportAgent |
| `structuration_ia` | `Optional[List[Dict]]` | 10 Structuration IA | UseCaseAgent | Frontend, ReportAgent |
| `report_path` | `Optional[str]` | Chemin rapport Word | ReportAgent | Frontend |

---

## 🔌 API Backend

### Routes

| Route | Méthode | Fichier | Rôle |
|-------|---------|---------|------|
| `/health` | GET | `backend/api/app.py` ligne 36 | Health check |
| `/api/upload` | POST | `backend/api/upload_routes.py` | Upload fichiers |
| `/threads` | POST | LangGraph Server (auto) | Créer thread |
| `/threads/{id}/runs` | POST | LangGraph Server (auto) | Exécuter workflow |
| `/threads/{id}/state` | GET | LangGraph Server (auto) | Récupérer état |
| `/docs` | GET | LangGraph Server (auto) | Documentation API |

### Configuration

**Fichier :** `langgraph.json`

```json
{
  "dependencies": ["./backend"],
  "graphs": {
    "need_analysis": "graph_factory:need_analysis"
  },
  "http": {
    "app": "api.app:app"
  },
  "env": ".env",
  "python_version": "3.11"
}
```

---

## 🎨 Frontend Next.js

### Pages

| Page | Fichier | Rôle |
|------|---------|------|
| Page 1 - Upload | `frontend/src/app/page.tsx` | Upload fichiers + nom entreprise |
| Page 2 - Besoins | `frontend/src/app/needs/page.tsx` | Affichage, sélection, régénération besoins |
| Page 3 - Cas d'usage | `frontend/src/app/usecases/page.tsx` | Affichage, sélection cas d'usage |
| Page 4 - Résultats | `frontend/src/app/results/page.tsx` | Téléchargement rapport |

### Composants

| Composant | Fichier | Rôle |
|-----------|---------|------|
| SideNav | `frontend/src/components/SideNav.tsx` | Navigation latérale |
| NeedCard | À créer | Carte besoin (titre + citations) |
| UseCaseCard | À créer | Carte cas d'usage |

### Lib

| Fichier | Rôle |
|---------|------|
| `frontend/src/lib/api-client.ts` | Appels API backend |
| `frontend/src/lib/store.ts` | State management (Zustand) |
| `frontend/src/lib/schemas.ts` | Types TypeScript |

---

## 📝 Prompts

Tous les prompts sont dans `backend/prompts/`

### NeedAnalysisAgent (CRITIQUE)

**Fichier :** `backend/prompts/need_analysis_agent_prompts.py`

| Prompt | Variable | Utilisation |
|--------|----------|-------------|
| System Prompt | `NEED_ANALYSIS_SYSTEM_PROMPT` | Toujours utilisé (rôle + règles) |
| User Prompt Initial | `NEED_ANALYSIS_INITIAL_USER_PROMPT` | Génération initiale |
| User Prompt Régénération | `NEED_ANALYSIS_REGENERATION_USER_PROMPT` | Régénération avec exclusions |

### WorkshopAgent

**Fichier :** `backend/prompts/workshop_agent_prompts.py`

| Prompt | Rôle |
|--------|------|
| `WORKSHOP_ANALYSIS_SYSTEM_PROMPT` | Rôle de l'agent |
| `WORKSHOP_ANALYSIS_USER_PROMPT` | Instructions d'analyse |

### UseCaseAnalysisAgent

**Fichier :** `backend/prompts/use_case_analysis_prompts.py`

| Prompt | Rôle |
|--------|------|
| `USE_CASE_ANALYSIS_SYSTEM_PROMPT` | Rôle + règles |
| `USE_CASE_INITIAL_USER_PROMPT` | Génération initiale |
| `USE_CASE_REGENERATION_USER_PROMPT` | Régénération |

---

## 🔍 Rechercher dans le code

### Par concept

| Concept | Rechercher dans |
|---------|----------------|
| **StateGraph** | `backend/graph_factory.py` |
| **add_node** | `backend/graph_factory.py` lignes 100-105 |
| **add_edge** | `backend/graph_factory.py` lignes 123-147 |
| **compile** | `backend/graph_factory.py` ligne 188 |
| **NeedAnalysisState** | `backend/models/graph_state.py` |
| **Parsing Excel** | `backend/agents/workshop_agent_impl.py` fonction `parse_excel_file()` |
| **Appel OpenAI** | Chercher `client.chat.completions.create` dans `backend/agents/*_impl.py` |
| **Perplexity** | `backend/agents/web_search_agent_impl.py` |
| **Génération besoins** | `backend/agents/need_analysis_agent_impl.py` fonction `generate_needs_with_openai()` |
| **Rapport Word** | `backend/utils/report_generator.py` |

### Par technologie

| Technologie | Fichiers |
|-------------|----------|
| **LangGraph** | `backend/graph_factory.py`, `backend/agents/nodes.py` |
| **OpenAI** | `backend/agents/*_agent_impl.py` |
| **Perplexity** | `backend/agents/web_search_agent_impl.py` |
| **openpyxl** | `backend/agents/workshop_agent_impl.py` |
| **PyPDF2** | `backend/process_transcript/pdf_parser.py` |
| **python-docx** | `backend/utils/report_generator.py` |
| **FastAPI** | `backend/api/app.py`, `backend/api/upload_routes.py` |
| **Next.js** | `frontend/src/app/**/*.tsx` |

---

## 🚀 Commandes utiles

### Docker

```bash
# Lancer tout
docker compose up --build

# Logs backend
docker compose logs -f backend

# Logs frontend
docker compose logs -f frontend

# Arrêter
docker compose down

# Nettoyer complètement
docker compose down --rmi all --volumes
```

### Développement local (sans Docker)

```bash
# Backend
cd backend
uv run langgraph dev  # Port 2024

# Frontend (autre terminal)
cd frontend
npm run dev  # Port 3000
```

### Tests

```bash
# Tests backend
cd backend
pytest tests/

# Test Perplexity
python tests/backend/test_perplexity.py
```

---

## 📚 Documentation complète

1. **GUIDE_COMPLET_PROJET.md** - Guide technique détaillé
2. **SCHEMA_VISUEL_COMPLET.md** - Schémas et diagrammes
3. **REFERENCE_RAPIDE.md** - Ce fichier (index rapide)
4. **README.md** - Instructions démarrage
5. **DEMARRAGE_SIMPLE.md** - Guide ultra simple

---

## 🎯 Checklist pour comprendre le projet

- [ ] Lire `GUIDE_COMPLET_PROJET.md` section "Vue d'ensemble"
- [ ] Regarder `SCHEMA_VISUEL_COMPLET.md` pour visualiser le flux
- [ ] Lire `backend/graph_factory.py` (commentaires détaillés)
- [ ] Lire `backend/models/graph_state.py` (comprendre le State)
- [ ] Lire `backend/agents/nodes.py` (wrappers agents)
- [ ] Lire un agent complet (ex: `workshop_agent_impl.py`)
- [ ] Tester le projet avec `docker compose up --build`
- [ ] Explorer l'API interactive : http://localhost:2024/docs
- [ ] Tester avec fichiers d'exemple dans `/documents`

---

**Créé le :** 22 octobre 2025  
**Version :** 1.0  
**Projet :** aikoGPT - Analyse de besoins IA avec LangGraph

