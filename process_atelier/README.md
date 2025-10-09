# Workshop Agent

Agent de traitement des fichiers Excel d'ateliers IA pour le générateur de rapports AIKO.

## 🎯 Fonctionnalités

- **Parsing Excel** : Traitement automatique des fichiers Excel avec 3 colonnes (Atelier, Use Case, Objective)
- **Groupement par atelier** : Organisation automatique des cas d'usage par atelier
- **Agrégation LLM** : Utilisation d'un LLM pour structurer et consolider les cas d'usage
- **Export JSON** : Sauvegarde des résultats structurés

## 📁 Structure des données

### Entrée (Excel)
- **Colonne A** : Nom de l'atelier
- **Colonne B** : Cas d'usage
- **Colonne C** : Objectif ou gain

### Sortie (JSON)
```json
{
  "workshop_id": "W001",
  "theme": "Direction commerciale",
  "use_cases": [
    {
      "title": "IA qui croise et analyse les données des marché",
      "objective": "Anticiper et prioriser les marchés",
      "benefits": ["gain de temps", "moins d'erreurs"]
    }
  ]
}
```

## 🚀 Utilisation

### Installation des dépendances
```bash
uv sync
```

### Utilisation basique
```python
from process_atelier.workshop_agent import WorkshopAgent

# Initialisation
agent = WorkshopAgent()

# Traitement d'un fichier
results = agent.process_workshop_file("inputs/atelier_exemple.xlsx")

# Sauvegarde
agent.save_results(results, "outputs/workshop_results.json")
```

### Test complet
```bash
uv run python test_workshop_agent.py
```

## ⚙️ Configuration

### Avec clé API OpenAI
```python
agent = WorkshopAgent(openai_api_key="your_api_key")
```

### Sans clé API (mode fallback)
```python
agent = WorkshopAgent()  # Utilise le mode fallback
```

## 📊 Logs

L'agent génère des logs détaillés :
- Parsing du fichier Excel
- Groupement par atelier
- Traitement LLM (si configuré)
- Sauvegarde des résultats

## 🔧 Architecture

```
process_atelier/
├── __init__.py
├── workshop_agent.py      # Agent principal
└── README.md

prompts/
└── workshop_agent_prompts.py  # Prompts pour le LLM

outputs/
└── workshop_results.json  # Résultats générés
```

## 📈 Exemple de sortie

Le test avec `atelier_exemple.xlsx` génère :
- **3 ateliers** identifiés
- **107 cas d'usage** au total
- **Fichier JSON** structuré de ~20KB

## 🎯 Prochaines étapes

1. Intégration avec les autres agents (Transcript, Web Search)
2. Amélioration des prompts LLM
3. Interface Streamlit
4. Validation humaine


