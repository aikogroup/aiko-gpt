# 📚 Explication des fichiers du dossier `database/`

## Vue d'ensemble

Le dossier `database/` contient toute l'infrastructure de base de données PostgreSQL pour aikoGPT. Voici le rôle de chaque fichier :

---

## 🔧 Fichiers de configuration et connexion

### `db.py`
**Rôle** : Configuration de la connexion SQLAlchemy et gestion des sessions

**Contenu** :
- Configuration de l'URL de connexion PostgreSQL (`DATABASE_URL`)
- Création de l'engine SQLAlchemy
- Factory de sessions (`SessionLocal`)
- Fonctions utilitaires :
  - `get_db()` : Dépendance FastAPI pour obtenir une session DB
  - `get_db_context()` : Context manager pour utiliser la DB en dehors de FastAPI
  - `init_db()` : Crée toutes les tables via SQLAlchemy
  - `execute_sql_file()` : Exécute un fichier SQL (pour les triggers/fonctions)

**Utilisation** :
```python
from database.db import get_db_context, init_db

# Initialiser les tables
init_db()

# Utiliser la DB
with get_db_context() as db:
    # Faire des requêtes
    pass
```

---

## 📊 Modèles de données

### `models.py`
**Rôle** : Définition des modèles SQLAlchemy ORM (Object-Relational Mapping)

**Contenu** :
- Classes Python représentant les tables PostgreSQL :
  - `User` : Utilisateurs (préparé pour migration future)
  - `Project` : Projets (1 projet = 1 entreprise)
  - `Document` : Documents avec métadonnées et texte extrait
  - `Transcript` : Interventions extraites avec recherche full-text
  - `WorkflowState` : Checkpoints LangGraph
  - `AgentResult` : Résultats structurés des agents IA

**Utilisation** :
```python
from database.models import Project, Document

# Les modèles sont utilisés par SQLAlchemy pour mapper Python ↔ PostgreSQL
```

---

### `schemas.py`
**Rôle** : Schémas Pydantic pour validation API (FastAPI)

**Contenu** :
- Schémas de validation pour les requêtes/réponses API :
  - `ProjectCreate`, `ProjectUpdate`, `Project`
  - `DocumentCreate`, `DocumentUpdate`, `Document`
  - `TranscriptCreate`, `TranscriptBatchCreate`, `Transcript`
  - `WorkflowStateCreate`, `WorkflowStateUpdate`, `WorkflowState`
  - `AgentResultCreate`, `AgentResultUpdate`, `AgentResult`

**Utilisation** :
```python
from database.schemas import ProjectCreate

# Validation automatique dans FastAPI
project = ProjectCreate(company_name="Ma Société", company_info={...})
```

---

## 🗄️ Schéma SQL

### `schema.sql`
**Rôle** : Schéma SQL PostgreSQL complet avec triggers et fonctions

**Contenu** :
- Définition des tables (CREATE TABLE)
- Index pour performance (GIN sur JSONB, TSVECTOR, etc.)
- Triggers pour mise à jour automatique :
  - `updated_at` automatique sur plusieurs tables
  - `search_vector` automatique sur transcripts
- Fonctions SQL :
  - `search_transcripts()` : Recherche full-text dans les transcripts

**Utilisation** :
```bash
# Exécuté automatiquement par init_db.py
python database/init_db.py
```

---

## 🔄 Repository Pattern

### `repository.py`
**Rôle** : Couche d'abstraction pour les opérations CRUD (Create, Read, Update, Delete)

**Contenu** :
- Classes Repository pour chaque modèle :
  - `ProjectRepository` : CRUD sur les projets
  - `DocumentRepository` : CRUD sur les documents
  - `TranscriptRepository` : CRUD + recherche full-text
  - `WorkflowStateRepository` : CRUD + upsert par thread
  - `AgentResultRepository` : CRUD + recherche par critères

**Avantages** :
- Séparation des préoccupations (business logic vs SQL)
- Réutilisable dans toute l'application
- Facilite les tests

**Utilisation** :
```python
from database.repository import ProjectRepository
from database.schemas import ProjectCreate

with get_db_context() as db:
    # Créer un projet
    project = ProjectRepository.create(db, ProjectCreate(
        company_name="Ma Société",
        company_info={"secteur": "Tech"}
    ))
    
    # Récupérer un projet
    project = ProjectRepository.get_by_company_name(db, "Ma Société")
```

---

## 🚀 Initialisation

### `init_db.py`
**Rôle** : Script d'initialisation de la base de données

**Contenu** :
1. Exécute `schema.sql` pour créer tables/triggers/fonctions
2. Vérifie les tables via SQLAlchemy
3. Insère des données de test (projet, document, transcripts, etc.)

**Utilisation** :
```bash
python database/init_db.py
```

**Ce qu'il fait** :
- ✅ Crée toutes les tables
- ✅ Exécute les triggers et fonctions SQL
- ✅ Insère des données de test (si pas déjà présentes)

---

## 🧪 Tests et exemples

### `test_connection.py`
**Rôle** : Script de test de connexion à la base de données

**Contenu** :
- Test de connexion PostgreSQL
- Vérification de la version
- Vérification de l'extension `pg_trgm`
- Liste des tables créées
- Test de la fonction `search_transcripts()`

**Utilisation** :
```bash
python database/test_connection.py
```

**Utile pour** :
- Vérifier que PostgreSQL est démarré
- Vérifier que le schéma est initialisé
- Diagnostiquer les problèmes de connexion

---

### `streamlit_example.py`
**Rôle** : Exemple d'intégration de la base de données dans Streamlit

**Contenu** :
- Exemple complet d'interface Streamlit utilisant la DB :
  - Affichage des projets
  - Création de projets
  - Recherche full-text dans les transcripts

**Utilisation** :
```bash
streamlit run database/streamlit_example.py
```

**Note** : C'est un **exemple** - pas encore intégré dans `app/app_api.py`

---

## 📦 Module Python

### `__init__.py`
**Rôle** : Fichier d'initialisation du module Python

**Contenu** :
- Exporte tous les éléments importants du module :
  - `engine`, `SessionLocal`, `get_db`, `get_db_context`
  - `init_db`, `drop_all_tables`, `execute_sql_file`
  - Tous les modèles (`Project`, `Document`, etc.)

**Utilisation** :
```python
# Permet d'importer directement depuis database
from database import Project, get_db_context, ProjectRepository
```

---

## 📖 Documentation

### `README.md`
**Rôle** : Documentation complète de la base de données

**Contenu** :
- Vue d'ensemble
- Instructions d'installation
- Structure du schéma
- Exemples d'utilisation
- Guide de migration future
- Troubleshooting

---

## 🔗 Relations entre fichiers

```
┌─────────────┐
│  schema.sql │  ← Définit la structure SQL brute
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  models.py  │  ← Mappe SQL → Python (SQLAlchemy ORM)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ schemas.py  │  ← Validation API (Pydantic)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│repository.py│  ← Couche d'abstraction CRUD
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    db.py    │  ← Connexion et sessions
└─────────────┘
```

---

## 🎯 Résumé rapide

| Fichier | Type | Rôle principal |
|---------|------|----------------|
| `db.py` | Configuration | Connexion PostgreSQL + sessions |
| `models.py` | ORM | Modèles Python ↔ Tables SQL |
| `schemas.py` | Validation | Schémas Pydantic pour API |
| `schema.sql` | SQL | Structure complète (tables, triggers, fonctions) |
| `repository.py` | Abstraction | Opérations CRUD réutilisables |
| `init_db.py` | Script | Initialisation automatique |
| `test_connection.py` | Test | Vérification de la connexion |
| `streamlit_example.py` | Exemple | Intégration Streamlit |
| `__init__.py` | Module | Exports Python |
| `README.md` | Doc | Documentation complète |

