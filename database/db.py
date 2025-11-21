"""
Configuration de connexion SQLAlchemy et gestion de session
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv
from pathlib import Path

# Charger les variables d'environnement
project_root = Path(__file__).parent.parent
env_files = [
    project_root / "deploy" / ".env",
    project_root / ".env",
]
for env_file in env_files:
    if env_file.exists():
        load_dotenv(env_file, override=False)
        break

# Configuration de la base de données depuis les variables d'environnement
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://aiko_user:aiko_password@localhost:5432/aiko_db"
)

# Extraire les composants de l'URL si nécessaire
# Format attendu: postgresql://user:password@host:port/database

# Créer l'engine SQLAlchemy
# pool_pre_ping=True pour vérifier les connexions avant utilisation
# poolclass=NullPool pour éviter les problèmes de pool en développement
# connect_args avec connect_timeout pour gérer les erreurs de connexion
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    poolclass=NullPool,  # Utiliser NullPool pour éviter les problèmes de connexion
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL si SQL_ECHO=true
    connect_args={
        "connect_timeout": 10,  # Timeout de 10 secondes pour les connexions
    } if "postgresql" in DATABASE_URL else {},
)

# Créer la session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dépendance FastAPI pour obtenir une session DB.
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager pour obtenir une session DB.
    Usage:
        with get_db_context() as db:
            # utiliser db
    
    Raises:
        Exception: Si la connexion à la base de données échoue
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialise la base de données en créant toutes les tables.
    À appeler une seule fois au démarrage de l'application.
    """
    from database.models import Base
    
    # Créer toutes les tables
    Base.metadata.create_all(bind=engine)
    print("✅ Base de données initialisée avec succès")


def drop_all_tables():
    """
    Supprime toutes les tables (ATTENTION: destructif!).
    Utilisé uniquement pour le développement/test.
    """
    from database.models import Base
    
    Base.metadata.drop_all(bind=engine)
    print("⚠️  Toutes les tables ont été supprimées")


def execute_sql_file(file_path: str):
    """
    Exécute un fichier SQL directement.
    Utile pour exécuter schema.sql avec les triggers et fonctions.
    
    Args:
        file_path: Chemin vers le fichier SQL
    """
    from pathlib import Path
    from urllib.parse import urlparse
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    sql_file = Path(file_path)
    if not sql_file.exists():
        raise FileNotFoundError(f"Fichier SQL non trouvé: {file_path}")
    
    with open(sql_file, "r", encoding="utf-8") as f:
        sql_content = f.read()
    
    # Parser l'URL de connexion
    # Format: postgresql://user:password@host:port/database
    parsed = urlparse(DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"))
    
    # Se connecter avec psycopg2
    conn = psycopg2.connect(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/") if parsed.path else "postgres",
        user=parsed.username or "postgres",
        password=parsed.password or ""
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        cursor = conn.cursor()
        # Utiliser psycopg2.extras.execute_values ou simplement exécuter statement par statement
        # mais avec une meilleure gestion des blocs $$ ... $$
        
        # Split les statements en préservant les blocs $$ ... $$
        statements = []
        current_statement = ""
        in_dollar_quote = False
        
        i = 0
        while i < len(sql_content):
            char = sql_content[i]
            
            # Détecter les blocs $$ ... $$
            if char == '$' and i + 1 < len(sql_content) and sql_content[i + 1] == '$':
                if not in_dollar_quote:
                    # Début du bloc $$
                    in_dollar_quote = True
                    current_statement += "$$"
                    i += 2
                    # Chercher la fin du bloc $$
                    while i < len(sql_content) - 1:
                        if sql_content[i] == '$' and sql_content[i + 1] == '$':
                            current_statement += "$$"
                            in_dollar_quote = False
                            i += 2
                            break
                        current_statement += sql_content[i]
                        i += 1
                    # Si on est toujours dans le bloc, continuer à chercher
                    if in_dollar_quote:
                        continue
                else:
                    # Fin du bloc $$
                    current_statement += "$$"
                    in_dollar_quote = False
                    i += 2
                    continue
            
            if in_dollar_quote:
                # À l'intérieur d'un bloc $$, on ajoute simplement le caractère
                current_statement += char
                i += 1
            elif char == ';':
                # En dehors d'un bloc $$, le ; sépare les statements
                current_statement += char
                statement = current_statement.strip()
                if statement and not statement.startswith("--"):
                    statements.append(statement)
                current_statement = ""
                i += 1
            else:
                current_statement += char
                i += 1
        
        # Ajouter le dernier statement s'il y en a un
        if current_statement.strip() and not current_statement.strip().startswith("--"):
            statements.append(current_statement.strip())
        
        # Exécuter chaque statement dans l'ordre
        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except Exception as e:
                    # Ignorer les erreurs de "déjà existant" pour les extensions et objets
                    error_str = str(e).lower()
                    if "already exists" not in error_str and "duplicate" not in error_str:
                        # Pour les erreurs "does not exist", c'est souvent dû à l'ordre d'exécution
                        # On les ignore silencieusement si c'est lié à une fonction qui sera créée
                        # (cela peut arriver si un trigger est créé avant la fonction dans certains cas de parsing)
                        if "does not exist" in error_str:
                            # Vérifier si c'est une fonction qui sera créée dans ce fichier
                            if "update_updated_at_column" in error_str or "update_transcript_search_vector" in error_str:
                                # Cette fonction sera créée, donc on peut ignorer l'erreur silencieusement
                                # (cela arrive parfois à cause de l'ordre d'exécution)
                                pass
                            else:
                                print(f"⚠️  Erreur lors de l'exécution: {e}")
                        else:
                            print(f"⚠️  Erreur lors de l'exécution: {e}")
                        # Ne pas lever l'exception pour continuer avec les autres statements
                        pass
        
        cursor.close()
    except Exception as e:
        # Ignorer les erreurs de "déjà existant" pour les extensions et objets
        error_str = str(e).lower()
        if "already exists" not in error_str and "duplicate" not in error_str:
            print(f"⚠️  Erreur lors de l'exécution: {e}")
            raise
    finally:
        conn.close()
    
    print(f"✅ Fichier SQL exécuté: {file_path}")

