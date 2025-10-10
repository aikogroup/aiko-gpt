# Guide de Debugging avec LangGraph Studio

## 🎯 Objectif
Ce guide vous explique comment utiliser LangGraph Studio pour débugger votre workflow d'analyse des besoins.

## 🚀 Démarrage Rapide

### 1. Démarrer le serveur de debugging
```bash
cd /home/addeche/aiko/aikoGPT
python start_debug_server.py
```

### 2. Accéder à LangGraph Studio
Ouvrez votre navigateur et allez à :
```
https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

### 3. Sélectionner votre workflow
- Cliquez sur "need_analysis" dans la liste des graphs
- Vous verrez la visualisation de votre workflow

## 🔧 Fonctionnalités de Debugging

### Visualisation du Graphe
- **Nœuds** : Chaque étape de votre workflow (start_agents, collect_data, analyze_needs, etc.)
- **Flux** : Les connexions entre les nœuds
- **État** : Les données passées entre les nœuds

### Points d'Interruption
Votre workflow est configuré avec des points d'interruption :
- **interrupt_before** : Avant `analyze_needs` et `human_validation`
- **interrupt_after** : Après `start_agents` et `collect_data`

### Inspection des États
- Cliquez sur un nœud pour voir son état d'entrée et de sortie
- Examinez les données à chaque étape
- Identifiez les problèmes de données

### Time-Travel Debugging
- Remontez à n'importe quel point d'exécution
- Rejouez l'exécution depuis un point spécifique
- Comparez les états entre les itérations

## 📊 Utilisation avec vos Données

### Mode Développement
Votre workflow est configuré pour utiliser les données mockées :
- `workshop_results.json`
- `transcript_results.json` 
- `web_search_cousin_surgery.json`

### Exécution Interactive
1. **Démarrer l'exécution** : Cliquez sur "Run" dans LangGraph Studio
2. **Pause automatique** : Le workflow s'arrêtera aux points d'interruption
3. **Inspection** : Examinez l'état à chaque pause
4. **Reprise** : Continuez l'exécution ou modifiez l'état

## 🛠️ Configuration Avancée

### Checkpointer
- **Type** : MemorySaver (en mémoire)
- **Persistance** : État sauvegardé entre les sessions
- **Time-travel** : Possibilité de revenir en arrière

### Logs de Debugging
Votre workflow inclut des logs détaillés :
```
🚀 [DEBUG] _start_agents_node - DÉBUT
📊 État d'entrée: 2 fichiers workshop, 1 fichiers transcript
✅ [DEBUG] _start_agents_node - FIN
📊 Résultats: 3 workshops, 2 transcripts, 1 recherches web
```

## 🔍 Dépannage

### Problèmes Courants

#### 1. Serveur ne démarre pas
```bash
# Vérifier que langgraph-cli est installé
uv run langgraph --version

# Réinstaller si nécessaire
uv add "langgraph-cli[inmem]"
```

#### 2. Erreur "debug_store" module
**Problème résolu** : Configuration corrigée dans `langgraph.json`
- Checkpointer : `"type": "memory"`
- Store : Supprimé (utilise la configuration par défaut)

#### 3. Erreur "Graph factory function must take exactly one argument"
**Problème résolu** : Factory function créée dans `graph_factory.py`
- Fonction `need_analysis(config: RunnableConfig)` 
- Configuration mise à jour dans `langgraph.json`

#### 4. Workflow non visible dans Studio
- Vérifiez que `langgraph.json` est présent
- Vérifiez que `graph_factory.py` existe
- Redémarrez le serveur
- Vérifiez les logs du serveur

#### 5. Erreurs d'import
```bash
# Réinstaller les dépendances
uv sync
```

### Logs Utiles
- **Serveur** : Logs dans le terminal où vous avez lancé `start_debug_server.py`
- **Workflow** : Logs avec préfixe `[DEBUG]` dans la console
- **Studio** : Logs dans la console du navigateur (F12)

## 📈 Optimisation

### Performance
- **Checkpointer** : Utilisez SQLite pour la persistance en production
- **Interruptions** : Réduisez les points d'interruption en production
- **Logs** : Désactivez les logs de debugging en production

### Debugging Efficace
1. **Identifiez le problème** : Utilisez la visualisation du graphe
2. **Isolez l'étape** : Utilisez les points d'interruption
3. **Inspectez les données** : Examinez l'état à chaque nœud
4. **Testez les corrections** : Utilisez le time-travel pour rejouer

## 🎯 Cas d'Usage Spécifiques

### Debugging des Agents
- **Workshop Agent** : Vérifiez les données d'entrée et de sortie
- **Transcript Agent** : Examinez le traitement des PDFs
- **Web Search Agent** : Contrôlez les requêtes et résultats
- **Need Analysis Agent** : Analysez la génération des besoins

### Debugging du Workflow
- **Flux de données** : Tracez le passage des données entre les nœuds
- **Conditions** : Vérifiez les conditions de branchement
- **Itérations** : Suivez les boucles et les compteurs
- **Validation humaine** : Testez l'interface de validation

## 🚀 Prochaines Étapes

1. **Testez votre workflow** avec LangGraph Studio
2. **Identifiez les problèmes** grâce à la visualisation
3. **Corrigez les bugs** en utilisant l'inspection des états
4. **Optimisez les performances** en analysant les goulots d'étranglement
5. **Déployez en production** avec la configuration optimisée

---

**Note** : Ce guide est spécifique à votre workflow d'analyse des besoins. Adaptez les instructions selon vos besoins spécifiques.
