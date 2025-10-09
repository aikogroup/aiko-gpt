# Workflow d'Analyse des Besoins

## Description

Workflow LangGraph pour l'analyse des besoins métier à partir des données collectées par les agents workshop, transcript et web_search.

## Fonctionnalités

- ✅ Analyse des besoins métier (environ 12 besoins)
- ✅ Validation humaine avec seuil de 5 besoins minimum
- ✅ Boucle de retry si validation insuffisante
- ✅ Génération de graph PNG du workflow
- ✅ Sauvegarde des résultats en JSON

## Utilisation

```python
from workflow.need_analysis_workflow import NeedAnalysisWorkflow

# Initialisation
workflow = NeedAnalysisWorkflow(api_key)

# Exécution
results = workflow.run()
```

## Fichiers générés

- `outputs/workflow_graph.png` - Graph du workflow
- `outputs/need_analysis_results.json` - Résultats finaux

