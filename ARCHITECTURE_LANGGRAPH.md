# 🏗️ Architecture LangGraph - aikoGPT

## ✅ Ce qui a été fait

### 1. **Suppression de FastAPI** ❌
- FastAPI **n'est plus nécessaire**
- LangGraph Server gère les APIs HTTP automatiquement
- `backend/main.py` est maintenant un simple fichier de configuration

### 2. **État partagé (State)** ✅
- **Fichier** : `backend/models/graph_state.py`
- **Type** : `NeedAnalysisState` (TypedDict)
- **Contenu** :
  - Inputs (excel, pdf/json, company_name)
  - Données parsées (workshop_data, transcript_data, web_search_data)
  - Besoins et cas d'usage générés
  - Métadonnées (action, errors, current_step)

### 3. **Agents comme Nodes** ✅
- **Fichier** : `backend/agents/nodes.py`
- **Agents créés** :
  1. `workshop_agent` - Parse fichier Excel
  2. `transcript_agent` - Parse PDF/JSON
  3. `web_search_agent` - Recherche contexte (Perplexity)
  4. `need_analysis_agent` - Génère 10 besoins
  5. `use_case_analysis_agent` - Génère QW + SIA
  6. `report_agent` - Génère rapport Word

**Note** : Pour l'instant, les agents retournent des données de test. La logique métier sera implémentée progressivement.

### 4. **Graphe LangGraph** ✅
- **Fichier** : `backend/graph_factory.py`
- **Type** : `StateGraph`
- **Workflow** :

```
START
  ↓
workshop (Parse Excel)
  ↓
transcript (Parse PDF/JSON)
  ↓
web_search (Contexte entreprise)
  ↓
need_analysis (Génère 10 besoins)
  ↓
use_case_analysis (Génère QW + SIA)
  ↓
report (Génère rapport Word)
  ↓
END
```

### 5. **Configuration** ✅
- **langgraph.json** : Configuré pour pointer vers `backend/graph_factory.py:need_analysis`
- **pyproject.toml** : Dépendances pour UV
- **.env** : Variables d'environnement déjà configurées

### 6. **Documentation** ✅
- `backend/README.md` - Guide backend
- `QUICKSTART.md` - Guide de démarrage rapide
- `test_graph.py` - Script de test

## 🔍 Comment LangGraph fonctionne

### Architecture

```
┌─────────────────────────────────────────────┐
│          langgraph.json                     │
│  {                                          │
│    "graphs": {                              │
│      "need_analysis": "backend/graph_factory.py:need_analysis"
│    }                                        │
│  }                                          │
└─────────────────┬───────────────────────────┘
                  │
                  │ Charge le graphe
                  ↓
┌─────────────────────────────────────────────┐
│       LangGraph Server                      │
│                                             │
│  Expose automatiquement :                   │
│  - POST /threads (créer un thread)          │
│  - POST /threads/{id}/runs (lancer)         │
│  - GET /threads/{id}/runs/{id}/stream      │
│  - ...                                      │
└─────────────────────────────────────────────┘
```

### Flux d'exécution

1. **Client** (frontend ou curl) → POST `/threads/{id}/runs`
2. **LangGraph Server** → Charge le graphe `need_analysis`
3. **Graphe** → Exécute les nodes dans l'ordre défini
4. **Chaque node** :
   - Reçoit le state actuel
   - Effectue son traitement
   - Retourne un dict de mise à jour du state
5. **State** → Fusionné automatiquement par LangGraph
6. **Résultat** → Retourné au client

### Exemple de state entre nodes

```python
# Après workshop_agent
{
  "excel_file_path": "./documents/atelier.xlsx",
  "workshop_data": { ... },  # ✅ Ajouté par workshop
  "current_step": "workshop_completed"
}

# Après transcript_agent
{
  "excel_file_path": "./documents/atelier.xlsx",
  "workshop_data": { ... },
  "transcript_data": [ ... ],  # ✅ Ajouté par transcript
  "current_step": "transcript_completed"
}

# Et ainsi de suite...
```

## 🚀 Prochaines étapes

### Étape 4.1 : Tester le graphe localement

```bash
# Option 1 : Test Python direct
python test_graph.py

# Option 2 : Lancer LangGraph Server
langgraph dev
```

### Étape 4.2 : Implémenter la logique métier des agents

Pour chaque agent, implémenter :
1. **workshop_agent** : Parsing Excel réel (openpyxl)
2. **transcript_agent** : Parsing PDF/JSON réel (pypdfium2, json)
3. **web_search_agent** : Appels Perplexity API
4. **need_analysis_agent** : Génération avec OpenAI (prompts/)
5. **use_case_analysis_agent** : Génération avec OpenAI (prompts/)
6. **report_agent** : Génération Word (python-docx)

### Étape 4.3 : Ajouter les interruptions humaines

Dans `langgraph.json` :
```json
{
  "graphs": {
    "need_analysis": {
      "path": "./backend/graph_factory.py:need_analysis",
      "interrupt_before": ["use_case_analysis"],
      "interrupt_after": ["need_analysis"]
    }
  }
}
```

Cela permettra :
- Pause après `need_analysis` pour validation utilisateur
- Pause avant `use_case_analysis` pour sélection besoins

## 📊 Différences clés avec l'ancienne approche

| Aspect | Ancienne approche | Nouvelle approche LangGraph |
|--------|-------------------|----------------------------|
| **API HTTP** | FastAPI manuel | LangGraph Server automatique |
| **Orchestration** | Code custom | StateGraph déclaratif |
| **State** | Variables locales | State partagé typé |
| **Streaming** | À implémenter | Natif LangGraph |
| **Monitoring** | À implémenter | LangSmith intégré |
| **Human-in-the-loop** | À implémenter | `interrupt_before/after` |
| **Retry** | À implémenter | Natif LangGraph |
| **Persistance** | À implémenter | Checkpointer natif |

## 🎯 Avantages de l'architecture LangGraph

1. ✅ **Moins de code** : Pas besoin de FastAPI
2. ✅ **Plus maintenable** : Workflow déclaratif
3. ✅ **Streaming natif** : Événements en temps réel
4. ✅ **Monitoring gratuit** : LangSmith
5. ✅ **Human-in-the-loop** : Built-in
6. ✅ **Testable** : Chaque node isolé
7. ✅ **Scalable** : Déploiement LangGraph Platform

## 🔧 Commandes utiles

```bash
# Développement local avec hot reload
langgraph dev

# Production avec Docker
langgraph up

# Test du graphe Python
python test_graph.py

# Vérifier la configuration
langgraph config show

# Voir les logs
tail -f .langgraph/logs/server.log
```

## 📚 Ressources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [DeepWiki LangGraph](https://deepwiki.com/langchain-ai/langgraph)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)
- [LangSmith (Monitoring)](https://smith.langchain.com/)

