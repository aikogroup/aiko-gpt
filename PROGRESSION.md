# 📊 Progression du développement - aikoGPT

> **Dernière mise à jour** : Session en cours
> **Architecture** : LangGraph SDK (sans FastAPI)

---

## ✅ Terminé

### 1. **Architecture LangGraph** ✅
- [x] Suppression de FastAPI (remplacé par LangGraph Server)
- [x] `langgraph.json` configuré correctement
- [x] State partagé défini (`NeedAnalysisState`)
- [x] Graphe défini dans `graph_factory.py`
- [x] 6 agents créés comme nodes

### 2. **State Management** ✅
- [x] `backend/models/graph_state.py` - État partagé TypedDict
- [x] Utilisation correcte de `Annotated` avec `add` pour les listes
- [x] Structure complète (inputs, données parsées, besoins, cas d'usage)

### 3. **Prompts LLM** ✅
- [x] `prompts/workshop_agent_prompts.py` - Analyse Excel
- [x] `prompts/transcript_agent_prompts.py` - Filtrage sémantique
- [x] `prompts/web_search_agent_prompts.py` - Structuration contexte
- [x] `prompts/need_analysis_agent_prompts.py` - Génération besoins (CRITIQUE!)
- [x] `prompts/use_case_analysis_prompts.py` - Génération cas d'usage

**Note importante** : Les prompts préservent toute la logique métier critique de l'ancien code :
- Règles d'unicité des thèmes
- Format strict des citations
- Distinction sources principales (workshop/transcript) vs contexte (web)

### 4. **Workshop Agent** ✅
- [x] `agents/workshop_agent_impl.py` - Implémentation complète
- [x] Parsing Excel avec `openpyxl`
- [x] Analyse avec OpenAI
- [x] Gestion d'erreurs robuste
- [x] Intégration dans `agents/nodes.py`

### 5. **Documentation** ✅
- [x] `QUICKSTART.md` - Guide de démarrage rapide
- [x] `ARCHITECTURE_LANGGRAPH.md` - Architecture détaillée
- [x] `backend/README.md` - Doc backend
- [x] `test_graph.py` - Script de test
- [x] `PROGRESSION.md` - Ce fichier

### 6. **Configuration** ✅
- [x] `.env` - Variables d'environnement configurées
- [x] `backend/pyproject.toml` - Dépendances pour UV
- [x] `.dockerignore` - Pour backend et frontend

---

## 🚧 En cours

### 7. **Transcript Agent** 🔄
- [ ] `agents/transcript_agent_impl.py` - Implémentation
- [ ] Parsing PDF avec `pypdfium2` ou `PyPDF2`
- [ ] Parsing JSON
- [ ] Filtrage sémantique avec OpenAI
- [ ] Intégration dans `agents/nodes.py`

### 8. **Web Search Agent** 🔄
- [ ] `agents/web_search_agent_impl.py` - Implémentation
- [ ] Appel Perplexity API
- [ ] Enrichissement OpenAI
- [ ] Structuration des résultats
- [ ] Intégration dans `agents/nodes.py`

---

## ⏳ À faire

### 9. **Need Analysis Agent** ⏳
- [ ] `agents/need_analysis_agent_impl.py` - Implémentation
- [ ] Génération initiale de 10 besoins
- [ ] Régénération avec exclusions
- [ ] Respect règles critiques (unicité, citations)
- [ ] Intégration dans `agents/nodes.py`

### 10. **Use Case Analysis Agent** ⏳
- [ ] `agents/use_case_analysis_agent_impl.py` - Implémentation
- [ ] Génération 8 Quick Wins
- [ ] Génération 10 Structuration IA
- [ ] Logique intelligente de régénération (>= 5 validés)
- [ ] Intégration dans `agents/nodes.py`

### 11. **Report Agent** ⏳
- [ ] `agents/report_agent_impl.py` - Implémentation
- [ ] Génération document Word avec `python-docx`
- [ ] Template professionnel
- [ ] Intégration besoins + cas d'usage
- [ ] Intégration dans `agents/nodes.py`

### 12. **Checkpointer & Persistence** ⏳
- [ ] Ajouter checkpointer dans `graph_factory.py`
- [ ] Configuration PostgreSQL (production) ou SQLite (dev)
- [ ] Test de persistance entre runs
- [ ] Thread management

### 13. **Human-in-the-Loop** ⏳
- [ ] Configurer `interrupt_before` / `interrupt_after` dans `langgraph.json`
- [ ] Validation utilisateur après `need_analysis`
- [ ] Sélection besoins avant `use_case_analysis`
- [ ] Routes API pour validation

### 14. **Frontend Next.js** ⏳
- [ ] Adapter `api-client.ts` pour LangGraph Server API
- [ ] Appels vers `POST /threads/{id}/runs`
- [ ] Streaming events avec SSE
- [ ] Gestion des interruptions (human-in-the-loop)

### 15. **Tests** ⏳
- [ ] Tests unitaires des agents
- [ ] Tests d'intégration du workflow
- [ ] Test avec fichiers exemples réels
- [ ] CI/CD

---

## 📋 Checklist technique

### Backend
- [x] LangGraph SDK correctement utilisé
- [x] State partagé TypedDict
- [x] Prompts versionnés et isolés
- [x] Agents comme fonctions nodes
- [x] Configuration `langgraph.json`
- [ ] Checkpointer configuré
- [ ] Error handling complet
- [ ] Logging structuré

### Agents implémentés
- [x] WorkshopAgent (parsing Excel + OpenAI) ✅
- [ ] TranscriptAgent (parsing PDF/JSON + filtrage)
- [ ] WebSearchAgent (Perplexity + OpenAI)
- [ ] NeedAnalysisAgent (génération 10 besoins)
- [ ] UseCaseAnalysisAgent (QW + SIA)
- [ ] ReportAgent (génération Word)

### Prompts
- [x] Tous les prompts créés ✅
- [x] Logique métier critique préservée ✅
- [x] Format JSON pour réponses structurées ✅

### Tests
- [ ] `test_graph.py` fonctionnel
- [ ] Tests avec fichiers réels
- [ ] Tests de régénération

---

## 🎯 Prochaines étapes prioritaires

1. **Implémenter TranscriptAgent** (parsing PDF/JSON + filtrage)
2. **Implémenter WebSearchAgent** (Perplexity + OpenAI)
3. **Implémenter NeedAnalysisAgent** (génération besoins)
4. **Implémenter UseCaseAnalysisAgent** (génération cas d'usage)
5. **Ajouter checkpointer** (persistance state)
6. **Tester le workflow complet** avec fichiers exemples

---

## 📚 Ressources utilisées

- **DeepWiki LangGraph** : Recherches approfondies sur l'architecture
- **Ancien code (OLD/)** : Préservation de la logique métier
- **LangGraph Docs** : Bonnes pratiques State, Command, Checkpointing

---

## 🚀 Comment lancer (quand terminé)

```bash
# Backend
langgraph dev  # ou langgraph up pour Docker

# Frontend
cd frontend && npm run dev

# Test rapide
python3 test_graph.py
```

---

## ⚠️ Points d'attention

1. **Prompts** : Ne jamais modifier sans tester, logique métier critique
2. **Citations** : Format strict (pas de source à la fin)
3. **Web Search** : CONTEXTE uniquement, jamais de besoins directs
4. **Unicité thèmes** : Règle critique dans need_analysis et use_case
5. **Checkpointer** : Essentiel pour human-in-the-loop

---

## 📝 Notes techniques

- **Python Version** : 3.11+ (défini dans `langgraph.json`)
- **LangGraph** : Pas de FastAPI, LangGraph Server gère tout
- **State** : TypedDict avec `Annotated` pour reducers
- **Config** : `RunnableConfig` pour passer model, settings
- **Errors** : Liste dans state, pas d'exceptions bloquantes

