# 🚀 QuickStart - aikoGPT

Guide rapide pour lancer l'application avec **LangGraph**.

## 📋 Prérequis

- **Python 3.11+**
- **Node.js 20+** (pour le frontend)
- **UV** (gestionnaire de dépendances Python)
- **LangGraph CLI** (`pip install langgraph-cli`)
- **Docker Desktop** (optionnel, pour `langgraph up`)

## ⚡ Installation rapide

### 1. Cloner et installer les dépendances

```bash
# Cloner le repo
cd /Users/julliardcyril/Projets/aikoGPT

# Installer les dépendances backend avec UV
cd backend
uv pip install -e .

# Installer les dépendances frontend
cd ../frontend
npm install

cd ..
```

### 2. Configurer les variables d'environnement

Le fichier `.env` existe déjà à la racine avec vos clés API configurées.

Vérifiez que ces variables sont présentes :
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini-2024-07-18
PERPLEXITY_API_KEY=pplx-...
LANGSMITH_API_KEY=lsv2_pt_...  # Optionnel
```

## 🧪 Test rapide du graphe

```bash
# Depuis la racine du projet
python test_graph.py
```

Cela va :
- ✅ Créer le graphe LangGraph
- ✅ Exécuter le workflow avec des données de test
- ✅ Afficher les résultats (besoins, cas d'usage)

## 🚀 Lancer l'application

### Option 1 : Développement local (recommandé pour débuter)

```bash
# Terminal 1 - Backend LangGraph
langgraph dev

# Terminal 2 - Frontend Next.js
cd frontend
npm run dev
```

- **Backend** : http://localhost:2024
- **Frontend** : http://localhost:3000

### Option 2 : Avec Docker

```bash
# Lance LangGraph + Redis + PostgreSQL
langgraph up

# Dans un autre terminal, lancer le frontend
cd frontend
npm run dev
```

## 📊 Accéder à l'application

1. **Frontend** : http://localhost:3000
   - Upload fichiers Excel + PDF/JSON
   - Saisir nom entreprise
   - Lancer analyse

2. **API LangGraph** : http://localhost:2024
   - Docs auto : http://localhost:2024/docs
   - Health check : http://localhost:2024/health

3. **LangSmith** (monitoring) : https://smith.langchain.com
   - Si `LANGSMITH_API_KEY` configuré

## 🔍 Tester l'API directement

### Créer un thread

```bash
curl -X POST http://localhost:2024/threads \
  -H "Content-Type: application/json"
```

Réponse :
```json
{
  "thread_id": "abc-123-def-456"
}
```

### Lancer le workflow

```bash
curl -X POST http://localhost:2024/threads/{thread_id}/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "need_analysis",
    "input": {
      "excel_file_path": "./documents/atelier_exemple.xlsx",
      "pdf_json_file_paths": ["./documents/test.pdf"],
      "company_name": "Cousin Biotech",
      "action": "generate_needs"
    }
  }'
```

### Streamer les résultats

```bash
curl -X GET "http://localhost:2024/threads/{thread_id}/runs/{run_id}/stream" \
  -H "Accept: text/event-stream"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (Next.js)              │
│         http://localhost:3000           │
└─────────────────┬───────────────────────┘
                  │
                  │ HTTP API
                  ↓
┌─────────────────────────────────────────┐
│    LangGraph Server                     │
│    http://localhost:2024                │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   StateGraph Workflow             │ │
│  │                                   │ │
│  │   Workshop → Transcript →        │ │
│  │   WebSearch → NeedAnalysis →     │ │
│  │   UseCaseAnalysis → Report       │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## 📚 Documentation

- [Agents.md](./AGENTS.md) - Documentation complète du projet
- [Backend README](./backend/README.md) - Documentation backend
- [LangGraph Docs](https://langchain-ai.github.io/langgraph/)

## 🛠️ Développement

### Structure des fichiers importants

```
.
├── backend/
│   ├── graph_factory.py       # 🔥 Définition du graphe LangGraph
│   ├── agents/nodes.py        # 🔥 Tous les agents (workshop, transcript, etc.)
│   ├── models/graph_state.py  # 🔥 État partagé du workflow
│   └── ...
├── frontend/
│   └── src/
│       ├── app/               # Pages Next.js
│       └── components/        # Composants React
├── langgraph.json             # 🔥 Configuration LangGraph
├── .env                       # Variables d'environnement (non versionné)
└── test_graph.py              # Script de test rapide
```

### Modifier le workflow

1. Éditer `backend/graph_factory.py`
2. Ajouter/modifier des nodes dans `backend/agents/nodes.py`
3. Le serveur se recharge automatiquement avec `langgraph dev`

### Ajouter un agent

```python
# Dans backend/agents/nodes.py
def mon_nouvel_agent(state: NeedAnalysisState) -> Dict[str, Any]:
    logger.info("Mon agent s'exécute")
    return {"current_step": "mon_etape"}

# Dans backend/graph_factory.py
workflow.add_node("mon_agent", mon_nouvel_agent)
workflow.add_edge("agent_precedent", "mon_agent")
```

## 🐛 Dépannage

### LangGraph CLI non trouvé

```bash
pip install langgraph-cli
```

### Erreur d'import de modules

```bash
# Vérifier que vous êtes dans le bon environnement
which python

# Réinstaller les dépendances
cd backend
uv pip install -e .
```

### Port 2024 déjà utilisé

```bash
# Tuer le processus sur le port 2024
lsof -ti:2024 | xargs kill -9
```

## ✅ Checklist de démarrage

- [ ] Python 3.11+ installé
- [ ] UV installé (`pip install uv`)
- [ ] LangGraph CLI installé (`pip install langgraph-cli`)
- [ ] Fichier `.env` configuré avec les clés API
- [ ] Dépendances backend installées (`uv pip install -e .`)
- [ ] Test du graphe réussi (`python test_graph.py`)
- [ ] Backend lancé (`langgraph dev`)
- [ ] Frontend lancé (`npm run dev`)

## 🎉 Prêt !

Vous pouvez maintenant :
1. Accéder au frontend sur http://localhost:3000
2. Uploader vos fichiers
3. Lancer l'analyse
4. Consulter les résultats
5. Télécharger le rapport Word

