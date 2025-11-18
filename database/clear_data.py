"""
Script pour supprimer toutes les données de la base de données
ATTENTION: Ce script supprime TOUTES les données mais garde les tables !
Pour repartir de zéro, utilisez ce script.
"""

import sys
import argparse
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent))

from database.db import get_db_context
from sqlalchemy import text


def clear_all_data(skip_confirmation: bool = False):
    """
    Supprime toutes les données de toutes les tables.
    Les tables et leur structure sont conservées.
    
    Args:
        skip_confirmation: Si True, ne demande pas de confirmation
    """
    print("⚠️  ATTENTION: Cette opération va supprimer TOUTES les données de la base de données !")
    print("   Les tables seront conservées, seules les données seront supprimées.")
    
    if not skip_confirmation:
        response = input("Êtes-vous sûr de vouloir continuer ? (tapez 'OUI' pour confirmer): ")
        
        if response != "OUI":
            print("❌ Opération annulée")
            return False
    
    print("\n🗑️  Suppression de toutes les données...")
    
    try:
        with get_db_context() as db:
            # Ordre de suppression : d'abord les tables enfants, puis les tables parentes
            # TRUNCATE CASCADE supprime automatiquement les données liées
            tables = [
                # Tables enfants (avec clés étrangères)
                "agent_results",
                "workflow_states",
                "transcripts",
                "word_extractions",
                "workshops",
                "documents",
                "speakers",
                # Tables parentes
                "projects",
                "users",
            ]
            
            # Désactiver temporairement les contraintes de clés étrangères pour éviter les problèmes
            print("📋 Désactivation temporaire des contraintes...")
            db.execute(text("SET session_replication_role = 'replica';"))
            db.commit()
            
            # Supprimer les données de chaque table
            deleted_counts = {}
            for table in tables:
                try:
                    # Compter avant suppression
                    count_result = db.execute(text(f"SELECT COUNT(*) FROM {table};"))
                    count_before = count_result.scalar()
                    
                    # Supprimer toutes les données
                    db.execute(text(f"TRUNCATE TABLE {table} CASCADE;"))
                    db.commit()
                    
                    deleted_counts[table] = count_before
                    print(f"  ✓ {table}: {count_before} ligne(s) supprimée(s)")
                except Exception as e:
                    print(f"  ⚠️  Erreur pour {table}: {e}")
                    db.rollback()
            
            # Réactiver les contraintes
            print("\n📋 Réactivation des contraintes...")
            db.execute(text("SET session_replication_role = 'origin';"))
            db.commit()
            
            # Afficher un résumé
            print("\n" + "=" * 60)
            print("Résumé de la suppression:")
            print("=" * 60)
            total_deleted = sum(deleted_counts.values())
            for table, count in deleted_counts.items():
                if count > 0:
                    print(f"  📊 {table}: {count} ligne(s) supprimée(s)")
            print(f"\n  ✅ Total: {total_deleted} ligne(s) supprimée(s)")
            print("=" * 60)
            print("✅ Toutes les données ont été supprimées avec succès !")
            print("   Les tables sont toujours présentes et prêtes à être utilisées.")
        
        return True
            
    except Exception as e:
        print(f"\n❌ Erreur lors de la suppression: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supprime toutes les données de la base de données")
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Supprime les données sans demander de confirmation"
    )
    args = parser.parse_args()
    
    clear_all_data(skip_confirmation=args.yes)

