# Diagramme du Workflow d'Analyse des Besoins

## Flux complet du workflow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Workshop Agent │    │ Transcript Agent│    │ Web Search Agent│
│   (Excel files) │    │   (PDF files)   │    │ (company info)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     collect_data_node     │
                    │    (Agrégation données)   │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     analyze_needs_node    │
                    │   (Analyse besoins IA)    │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │  human_validation_node   │
                    │  (Validation humaine)    │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │    check_success_node    │
                    │   (Vérification succès)   │
                    └─────────────┬─────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │  finalize_results_node   │
                    │ (Sauvegarde + Graph PNG)  │
                    └───────────────────────────┘
```

## Points d'entrée multiples

Le workflow démarre avec **3 points d'entrée parallèles** :
- `workshop_node` : Traitement des fichiers Excel
- `transcript_node` : Traitement des fichiers PDF  
- `web_search_node` : Recherche d'informations entreprise

## Convergence

Les 3 agents convergent vers `collect_data_node` qui agrège leurs résultats.

## Boucle de validation

Si la validation humaine échoue (< 5 besoins validés), le workflow retourne à `analyze_needs_node`.

## Sorties

- **Graph PNG** : `/outputs/workflow_graph.png`
- **Résultats JSON** : `/outputs/need_analysis_results.json`
- **Besoins validés** : Liste des besoins approuvés

## Utilisation

```python
workflow = NeedAnalysisWorkflow(api_key)

results = workflow.run(
    workshop_files=["file1.xlsx", "file2.xlsx"],
    transcript_files=["transcript1.pdf", "transcript2.pdf"],
    company_info={"company_name": "Mon Entreprise", "sector": "Tech"}
)
```

