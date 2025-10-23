# Codebase Overview

## Général

| Fichier | Rôle |
| ------- | ----- |
| backend/api/app.py | Initialise FastAPI, monte les routeurs techniques (/api/upload, /api/report). |
| backend/api/upload_routes.py | Upload des fichiers (Excel, PDF/JSON), génération du `thread_id`. |
| backend/api/report_routes.py | Expose le téléchargement du rapport Word généré par LangGraph. |
| backend/agents/workshop_agent_impl.py | Parsing Excel et appel OpenAI pour structurer l’atelier. |
| backend/agents/transcript_agent_impl.py | Parsing PDF/JSON + filtrage sémantique des transcriptions. |
| backend/agents/web_search_agent_impl.py | Recherche Perplexity et consolidation du contexte entreprise. |
| backend/agents/need_analysis_agent_impl.py | Génération des besoins (10 items, citations). |
| backend/agents/use_case_analysis_agent_impl.py | Génération des cas d’usage (Quick Wins / Structuration IA). |
| backend/agents/report_agent_impl.py | Création du rapport Word final. |
| backend/models/graph_state.py | Définition du state partagé LangGraph (entrées/sorties workflow). |
| backend/prompts/*.py | Prompts LLM versionnés pour chaque agent. |
| backend/utils/report_generator.py | (legacy) Stub historique, logique report déplacée dans l’agent. |
| frontend/src/app/page.tsx | Page Next.js d’upload initial et déclenchement du workflow. |
| frontend/src/app/needs/page.tsx | Sélection/régénération des besoins. |
| frontend/src/app/usecases/page.tsx | Sélection/régénération des cas d’usage. |
| frontend/src/app/results/page.tsx | Synthèse + téléchargement du rapport. |
| frontend/src/lib/store.ts | Zustand store (thread, besoins, cas d’usage, état UI). |
| frontend/src/styles/globals.css | Styles Tailwind globaux. |
| docker-compose.yml | Orchestration Docker backend/frontend. |
| README.md | Présentation générale du projet. |

## Spécifiques LangGraph SDK

| Fichier | Rôle |
| ------- | ----- |
| backend/graph_factory.py | Construction du graphe LangGraph (`StateGraph`) et export `need_analysis`. |
| backend/agents/nodes.py | Liaison entre le graphe et les implémentations d’agents. |
| backend/api/upload_routes.py | Génère le `thread_id` (UUID) utilisé par LangGraph. |
| backend/api/report_routes.py | Sert les rapports générés dans `/outputs`. |
| frontend/src/lib/api-client.ts | Client SDK LangGraph (`client.threads`, `client.runs.wait`). |
| frontend/src/lib/schemas.ts | Types alignés sur l’état LangGraph (inputs/outputs). |
| frontend/src/app/page.tsx | Lance `generateNeeds` et stocke le thread retourné par LangGraph. |
| frontend/src/app/needs/page.tsx | Utilise le thread persistant pour `regenerate_needs`. |
| frontend/src/app/usecases/page.tsx | Idem pour `generate_use_cases` / `regenerate_use_cases`. |

