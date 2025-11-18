"""
Script pour réinitialiser complètement la base de données PostgreSQL
ATTENTION: Ce script supprime TOUTES les données !
Utilise Alembic pour gérer les migrations.
"""

import os
import sys
import subprocess
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from database.db import get_db_context, execute_sql_file
from sqlalchemy import text

def reset_database():
    """
    Réinitialise complètement la base de données en utilisant Alembic :
    1. Supprime toutes les migrations (downgrade base)
    2. Recrée toutes les tables via Alembic (upgrade head)
    3. Ajoute les fonctions, triggers et commentaires depuis schema.sql
    """
    print("⚠️  ATTENTION: Cette opération va supprimer TOUTES les données de la base de données !")
    response = input("Êtes-vous sûr de vouloir continuer ? (tapez 'OUI' pour confirmer): ")
    
    if response != "OUI":
        print("❌ Opération annulée")
        return False
    
    print("\n🔄 Réinitialisation de la base de données...")
    
    try:
        # 1. Supprimer toutes les migrations (downgrade jusqu'à la base)
        print("📋 Suppression des tables existantes via Alembic...")
        try:
            result = subprocess.run(
                ["uv", "run", "alembic", "downgrade", "base"],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                print("  ✓ Tables supprimées")
            else:
                # Si downgrade base échoue, essayer de supprimer directement les tables
                if "Can't locate revision identified by 'base'" not in result.stderr:
                    print(f"  ⚠️  Erreur lors du downgrade Alembic: {result.stderr}")
                    print("  🔄 Tentative de suppression directe des tables...")
                    try:
                        from database.db import drop_all_tables
                        drop_all_tables()
                        print("  ✓ Tables supprimées directement")
                    except Exception as e2:
                        print(f"  ⚠️  Erreur lors de la suppression directe: {e2}")
                        # Continuer quand même, les tables peuvent déjà être supprimées
        except Exception as e:
            print(f"  ⚠️  Avertissement lors du downgrade: {e}")
            # Essayer de supprimer directement les tables
            try:
                from database.db import drop_all_tables
                drop_all_tables()
                print("  ✓ Tables supprimées directement")
            except Exception as e2:
                print(f"  ⚠️  Erreur lors de la suppression directe: {e2}")
        
        # 2. Supprimer manuellement les fonctions et triggers qui ne sont pas gérés par Alembic
        print("\n📋 Suppression des fonctions et triggers...")
        with get_db_context() as db:
            try:
                db.execute(text("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;"))
                db.execute(text("DROP FUNCTION IF EXISTS update_transcript_search_vector() CASCADE;"))
                db.execute(text("DROP FUNCTION IF EXISTS search_transcripts(TEXT, BIGINT, VARCHAR) CASCADE;"))
                db.commit()
                print("  ✓ Fonctions supprimées")
            except Exception as e:
                print(f"  ⚠️  Avertissement: {e}")
        
        # 3. Appliquer toutes les migrations Alembic
        print("\n📋 Création des tables via Alembic...")
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True,
            check=True
        )
        print("  ✓ Tables créées")
        
        # 4. Exécuter le fichier schema.sql pour les fonctions, triggers et commentaires
        # (ces éléments ne sont pas encore dans les migrations Alembic)
        print("\n📋 Création des fonctions, triggers et commentaires...")
        schema_file = Path(__file__).parent / "schema.sql"
        if schema_file.exists():
            execute_sql_file(str(schema_file))
            print("  ✓ Fonctions, triggers et commentaires créés")
        else:
            print("  ⚠️  Fichier schema.sql non trouvé, ignoré")
        
        print("\n✅ Base de données réinitialisée avec succès !")
        print("📊 Tables créées:")
        tables = [
            "users",
            "projects",
            "documents",
            "workshops",
            "word_extractions",
            "transcripts",
            "workflow_states",
            "agent_results",
        ]
        for table in tables:
            print(f"  ✓ {table}")
        
        return True
            
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erreur lors de l'exécution d'Alembic: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Erreur lors de la réinitialisation: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    reset_database()

