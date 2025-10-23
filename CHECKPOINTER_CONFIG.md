# 🗄️ Configuration du Checkpointer - InMemorySaver

> **Date** : 21 octobre 2025  
> **Status** : ✅ Simplifié - InMemory uniquement

---

## 📋 Vue d'ensemble

Le projet utilise **InMemorySaver**, le checkpointer intégré à LangGraph pour la gestion de l'état.

### Avantages InMemorySaver
- ✅ **Aucune dépendance externe** (inclus dans langgraph)
- ✅ **Configuration automatique** (pas de setup)
- ✅ **Parfait pour développement** et tests
- ✅ **Simplifie le code** (pas de gestion BDD)

### Limitations
- ⚠️ **Persistence en mémoire uniquement** (perte au redémarrage)
- ⚠️ **Non adapté pour production** avec multi-processus

---

## 🔧 Implémentation

Le checkpointer est configuré automatiquement dans `backend/graph_factory.py` :

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
graph = workflow.compile(checkpointer=checkpointer)
```

**C'est tout !** Aucune configuration supplémentaire nécessaire.

---

## 🚀 Utilisation

### Avec thread_id (persistence entre appels)

```python
from graph_factory import need_analysis

# Première exécution
config = {"configurable": {"thread_id": "user-123"}}
result1 = need_analysis.invoke(state1, config)

# Deuxième exécution (reprend le state précédent)
result2 = need_analysis.invoke(state2, config)
```

### Sans thread_id (stateless)

```python
# Chaque appel repart de zéro
result = need_analysis.invoke(state)
```

---

## 🎯 Cas d'usage

### ✅ Parfait pour :
- Développement local
- Tests automatisés
- Prototypage rapide
- Applications simples
- Single-process

### ❌ Non recommandé pour :
- Production multi-processus
- Persistence entre redémarrages
- Applications distribuées

---

## 💡 Pour aller plus loin

Si besoin de **persistence durable** en production :
- **SQLite** : Fichier local (single-process)
- **PostgreSQL** : Base de données (multi-process)

Voir la [documentation LangGraph](https://langchain-ai.github.io/langgraph/concepts/persistence/) pour plus d'options.

---

**InMemorySaver simplifie le développement tout en offrant la persistence nécessaire pour les workflows multi-étapes !** 🎉
