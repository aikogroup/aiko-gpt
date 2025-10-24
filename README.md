# AIKO GPT - Générateur de rapports assisté par IA

Générateur de rapports assisté par IA pour société de conseil spécialisée en Intelligence Artificielle.

## Prérequis

- Fichier `.env` avec au minimum:
  - `OPENAI_API_KEY=...`
  - Optionnel: `OPENAI_MODEL=gpt-4o-mini`

## Installation

```bash
uv sync
```

## Lancement (mode actuel)

1) Démarrer l'API LangGraph (port 2025)
```bash
uv run python api/start_api.py
```

2) Démarrer l'UI Streamlit (port 8501)
```bash
uv run python app/run_api.py
```

## Utilisation de l'UI

Dans l'interface Streamlit:
- Déposer un fichier Excel (colonnes: A=Atelier, B=Use Case, C=Objectif)
- Déposer un ou plusieurs fichiers de transcription (PDF/JSON)
- Saisir le nom de l'entreprise
- Lancer l'analyse: les agents tournent en parallèle, validation humaine, puis génération de rapport (JSON/Word)

## Notes

- Les agents utilisent l'API OpenAI (Responses) avec le modèle `gpt-4o-mini`.
- LangGraph Studio (optionnel) peut être lancé séparément si nécessaire.

