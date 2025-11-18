# Base de données PostgreSQL pour aikoGPT

## Vue d'ensemble

Cette base de données PostgreSQL stocke :
- **Projets** : Un projet = une entreprise (company_name)
- **Documents** : Métadonnées et texte extrait (workshop, transcript, word_report)
- **Transcripts** : Interventions extraites avec recherche full-text
- **Workflow States** : Checkpoints LangGraph pour partage entre workflows
- **Agent Results** : Résultats structurés des agents (needs, use_cases, atouts, etc.)

## Installation

### 1. Démarrer PostgreSQL avec Docker

```bash
docker-compose up -d
```

Cela démarre un container PostgreSQL avec :
- User: `aiko_user`
- Password: `aiko_password`
- Database: `aiko_db`
- Port: `5432`

### 2. Configurer la connexion

Ajouter dans votre fichier `.env` :

```env
DATABASE_URL=postgresql://aiko_user:aiko_password@localhost:5432/aiko_db
```

### 3. Initialiser la base de données

```bash
python database/init_db.py
```

Cela :
- Crée toutes les tables
- Exécute les triggers et fonctions SQL
- Insère des données de test

## Structure du schéma

### Tables principales

1. **users** : Utilisateurs (préparé pour migration future)
2. **projects** : Projets (1 projet = 1 entreprise)
3. **documents** : Documents avec métadonnées et texte extrait
4. **transcripts** : Interventions avec recherche full-text (TSVECTOR)
5. **workflow_states** : États des workflows LangGraph
6. **agent_results** : Résultats des agents IA

### Relations

```
projects (1) ──< documents (N)
documents (1) ──< transcripts (N)
projects (1) ──< workflow_states (N)
projects (1) ──< agent_results (N)
```

## Utilisation

### Connexion à la base de données

```python
from database.db import get_db, SessionLocal

# Dans FastAPI
@app.get("/items")
def read_items(db: Session = Depends(get_db)):
    # Utiliser db
    pass

# En dehors de FastAPI
with get_db_context() as db:
    # Utiliser db
    pass
```

### Repository Pattern

Utiliser les repositories pour les opérations CRUD :

```python
from database.repository import ProjectRepository, DocumentRepository

# Créer un projet
project = ProjectRepository.create(db, ProjectCreate(
    company_name="Ma Société",
    company_info={"secteur": "Tech"},
    created_by="user1"
))

# Récupérer un projet
project = ProjectRepository.get_by_company_name(db, "Ma Société")

# Recherche full-text
results = TranscriptRepository.search_fulltext(
    db, 
    search_query="automatisation",
    project_id=1,
    limit=10
)
```

### API Endpoints

Les endpoints sont disponibles sous `/db` :

- `POST /db/projects` : Créer un projet
- `GET /db/projects` : Lister les projets
- `GET /db/projects/{id}` : Récupérer un projet
- `POST /db/documents` : Créer un document
- `POST /db/transcripts/batch` : Créer plusieurs transcripts
- `GET /db/transcripts/search` : Recherche full-text
- `POST /db/workflow-states` : Sauvegarder un état de workflow
- `POST /db/agent-results` : Sauvegarder un résultat d'agent

## Recherche full-text

La recherche full-text utilise PostgreSQL TSVECTOR avec la langue française :

```sql
SELECT * FROM search_transcripts(
    'automatisation reporting',
    project_id => 1,
    speaker => 'Alice'
);
```

Via l'API :

```python
GET /db/transcripts/search?search_query=automatisation&project_id=1
```

## Migration future

### Authentification complète

Pour migrer vers une authentification complète :

1. Remplir la table `users` avec les vrais utilisateurs
2. Ajouter une colonne `user_id` dans `projects`
3. Migrer les données de `created_by` (string) vers `user_id` (FK)
4. Supprimer la colonne `created_by`

### Checkpointer PostgreSQL pour LangGraph

Pour utiliser PostgreSQL comme checkpointer LangGraph :

1. Créer un checkpointer personnalisé utilisant la table `workflow_states`
2. Remplacer `MemorySaver` par ce checkpointer dans les workflows

## Maintenance

### Sauvegardes

```bash
docker exec aiko_postgres pg_dump -U aiko_user aiko_db > backup.sql
```

### Restauration

```bash
docker exec -i aiko_postgres psql -U aiko_user aiko_db < backup.sql
```

### Vérifier la santé

```bash
docker exec aiko_postgres pg_isready -U aiko_user -d aiko_db
```

## Index et performance

- **Index GIN** sur JSONB (agent_results.data, workflow_states.state_data)
- **Index GIN** sur TSVECTOR (transcripts.search_vector)
- **Index B-tree** sur les clés étrangères et dates
- **Index composite** pour les requêtes fréquentes

## Troubleshooting

### Erreur de connexion

Vérifier que PostgreSQL est démarré :
```bash
docker-compose ps
```

### Erreur "relation does not exist"

Exécuter le script d'initialisation :
```bash
python database/init_db.py
```

### Erreur de recherche full-text

Vérifier que l'extension `pg_trgm` est installée :
```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
```

