# Guide LangGraph Studio

## 🚀 Démarrage rapide

### 1. Préparer l'environnement
```bash
./setup_langgraph.sh
```

### 2. Lancer LangGraph Studio
```bash
uv run langgraph dev --allow-blocking
```

### 3. Ouvrir l'interface
Ouvrez votre navigateur : **http://127.0.0.1:2024**

> **Note** : Votre API FastAPI utilise le port 2025, LangGraph Studio utilise le port 2024

---

## 📊 Utilisation avec vos documents

### Option A : Chemins de fichiers (recommandé)

Dans l'interface LangGraph Studio, configurez l'état initial avec :

```json
{
  "workshop_files": [
    "/home/addeche/aiko/aikoGPT/inputs/atelier_exemple.xlsx"
  ],
  "transcript_files": [
    "/home/addeche/aiko/aikoGPT/inputs/-Cousin-Biotech-x-aiko-Echange-Production-b04e9caa-d79c.pdf",
    "/home/addeche/aiko/aikoGPT/inputs/-Cousin-x-aiko-Echange-Equipe-Technique-64264037-0daa.pdf"
  ],
  "company_info": {
    "company_name": "Cousin Biotech",
    "sector": "Médical",
    "size": "50-100 employés"
  }
}
```

### Option B : Données pré-traitées (démo rapide)

Si vous avez déjà exécuté le workflow une fois, vous pouvez passer directement les résultats :

```json
{
  "workshop_results": {...},
  "transcript_results": [...],
  "web_search_results": {...}
}
```

---

## 🔍 Fonctionnalités de LangGraph Studio

### Visualisation du workflow
- Graph interactif montrant tous les nœuds
- Flèches indiquant le flux de données
- Nœuds conditionnels avec leurs branches

### Inspection des données
- **Par nœud** : Cliquez sur un nœud pour voir son état
- **Input/Output** : Voyez ce qui entre et sort de chaque nœud
- **Tokens** : Compteurs de tokens affichés par nœud (si tracker activé)

### Debugging
- **Points d'interruption** : Pause entre les nœuds
- **Time travel** : Revenez à un état précédent
- **Replay** : Rejouez le workflow depuis n'importe quel point

### Logs en temps réel
- Chaque nœud affiche ses logs
- Progression visible
- Erreurs mises en évidence

---

## 🎯 Structure du workflow

```
start_agents (parallèle)
├─ Workshop Agent (Excel)    →┐
├─ Transcript Agent (PDFs)    →├→ collect_data
└─ Web Search Agent (API)     →┘
                                 ↓
                          analyze_needs
                                 ↓
                          human_validation
                                 ↓
                          check_success
                          /     |      \
                    continue  success  max_iterations
                       ↓        ↓          ↓
                analyze_needs  finalize   END
```

---

## ⚙️ Configuration avancée

### Modifier les points d'interruption

Dans `workflow/need_analysis_workflow.py` ligne 237 :

```python
compile_kwargs["interrupt_before"] = ["analyze_needs", "human_validation"]
compile_kwargs["interrupt_after"] = ["start_agents", "collect_data"]
```

### Désactiver le mode debug

Dans `graph_factory.py` ligne 29 :

```python
workflow = NeedAnalysisWorkflow(
    api_key=api_key,
    dev_mode=False,    # Mode production
    debug_mode=False   # Pas de checkpointing
)
```

---

## ❓ FAQ

### Pourquoi `--allow-blocking` ?

Le projet utilise des opérations de fichiers (mkdir, save_report) qui sont bloquantes dans un contexte ASGI. Le flag permet de les utiliser en développement.

**Solutions alternatives :**
1. Convertir en async (meilleure approche long terme)
2. Utiliser `asyncio.to_thread()` pour les I/O
3. Désactiver le token tracking en mode debug

### Les fichiers doivent-ils être sur le serveur ?

Oui, pour l'instant les chemins de fichiers doivent être accessibles depuis le serveur LangGraph. Une future amélioration pourrait ajouter un upload via l'interface.

### Comment voir les tokens consommés ?

Les statistiques de tokens s'affichent :
1. Dans les logs du terminal
2. Dans l'état du workflow (clé `tracker_stats`)
3. Dans les fichiers `outputs/token_tracking/*.json`

### Puis-je tester sans fichiers ?

Oui ! Activez le mode `dev_mode=True` qui utilise des données mockées. Les résultats viennent de `need_analysis_results_mock.json`.

---

## 🐛 Dépannage

### Le serveur ne démarre pas
```bash
# Vérifier que le port 2024 est libre
lsof -i :2024

# Si occupé, tuer le processus
kill -9 <PID>
```

**Architecture des ports :**
- Port **2024** : LangGraph Studio (visualisation/debug)
- Port **2025** : Votre API FastAPI (Streamlit/production)

### Erreur "Blocking call"
Vérifiez que vous utilisez bien `--allow-blocking` :
```bash
uv run langgraph dev --allow-blocking
```

### Erreur "OPENAI_API_KEY not found"
Créez un fichier `.env` :
```bash
echo "OPENAI_API_KEY=votre_cle_api" > .env
```

---

## 📚 Ressources

- [Documentation LangGraph](https://langchain-ai.github.io/langgraph/)
- [LangGraph Studio](https://github.com/langchain-ai/langgraph-studio)
- [Documentation LangChain](https://python.langchain.com/)

