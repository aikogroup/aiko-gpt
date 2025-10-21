# Backend aikoGPT - LangGraph

## 🏗️ Architecture

Ce backend utilise **LangGraph** pour orchestrer tous les agents d'analyse.

### Pourquoi LangGraph ?

- ✅ **Pas de FastAPI nécessaire** : LangGraph Server gère les APIs HTTP
- ✅ **Orchestration native** : Workflow défini comme un graphe de nodes
- ✅ **State Management** : État partagé entre tous les agents
- ✅ **Streaming support** : Événements en temps réel
- ✅ **Human-in-the-loop** : Validation utilisateur intégrée

## 📁 Structure

```
backend/
├── graph_factory.py          # Définition du graphe LangGraph
├── main.py                   # Configuration et logging
├── agents/
│   ├── nodes.py              # Tous les agents (workshop, transcript, etc.)
│   └── __init__.py
├── models/
│   ├── graph_state.py        # État partagé du workflow
│   ├── need_analysis_models.py
│   ├── use_case_analysis_models.py
│   └── ...
├── prompts/                  # Prompts LLM versionnés
├── utils/                    # Utilitaires (report_generator, etc.)
└── ...
```

## 🔄 Workflow du graphe

```
START
  ↓
WorkshopAgent (Parse Excel)
  ↓
TranscriptAgent (Parse PDF/JSON)
  ↓
WebSearchAgent (Contexte entreprise)
  ↓
NeedAnalysisAgent (Génère 10 besoins)
  ↓
UseCaseAnalysisAgent (Génère QW + SIA)
  ↓
ReportAgent (Génère rapport Word)
  ↓
END
```

## 🚀 Lancer le serveur

### Développement local

```bash
# Depuis la racine du projet
langgraph dev
```

Le serveur LangGraph démarre sur `http://localhost:2024` par défaut.

### Avec Docker

```bash
# Lance LangGraph + Redis + PostgreSQL
langgraph up
```

## 🧪 Tester le graphe

### 1. Via l'API HTTP (LangGraph Server)

```bash
# Créer un thread
curl -X POST http://localhost:2024/threads

# Lancer le workflow
curl -X POST http://localhost:2024/threads/{thread_id}/runs \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "excel_file_path": "./documents/atelier_exemple.xlsx",
      "pdf_json_file_paths": ["./documents/test.pdf"],
      "company_name": "Cousin Biotech"
    }
  }'
```

### 2. Via Python

```python
from graph_factory import need_analysis

# État initial
initial_state = {
    "excel_file_path": "./documents/atelier_exemple.xlsx",
    "pdf_json_file_paths": ["./documents/test.pdf"],
    "company_name": "Cousin Biotech"
}

# Exécuter le graphe
result = need_analysis.invoke(initial_state)

print(result["needs"])  # 10 besoins générés
```

## 🔑 Variables d'environnement

Créez un fichier `.env` à la racine avec :

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini-2024-07-18

# Perplexity
PERPLEXITY_API_KEY=pplx-...

# LangSmith (optionnel, pour monitoring)
LANGSMITH_API_KEY=lsv2_pt_...

# Logging
LOG_LEVEL=INFO
```

## 📊 Monitoring avec LangSmith

Si vous avez configuré `LANGSMITH_API_KEY`, vous pouvez suivre l'exécution du graphe sur :
https://smith.langchain.com/

## 🛠️ Développement

### Ajouter un nouveau agent

1. Créer une fonction dans `agents/nodes.py`
2. Ajouter le node dans `graph_factory.py`
3. Définir les edges (transitions)

```python
# agents/nodes.py
def mon_nouvel_agent(state: NeedAnalysisState) -> Dict[str, Any]:
    logger.info("Mon agent s'exécute")
    return {"current_step": "completed"}

# graph_factory.py
workflow.add_node("mon_agent", mon_nouvel_agent)
workflow.add_edge("previous_agent", "mon_agent")
```

## 📚 Ressources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [DeepWiki LangGraph](https://deepwiki.com/langchain-ai/langgraph)
- [Agents.md du projet](../AGENTS.md)

