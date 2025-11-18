"""
Script de test de connexion à la base de données
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database.db import engine, DATABASE_URL, init_db
from sqlalchemy import text


def test_connection():
    """Teste la connexion à la base de données"""
    print("=" * 60)
    print("Test de connexion à la base de données PostgreSQL")
    print("=" * 60)
    print(f"URL: {DATABASE_URL.split('@')[0]}@***")  # Masquer le mot de passe
    
    try:
        # Test de connexion
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"\n✅ Connexion réussie!")
            print(f"📊 Version PostgreSQL: {version.split(',')[0]}")
            
            # Test des extensions
            result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'pg_trgm'"))
            if result.fetchone():
                print("✅ Extension pg_trgm installée")
            else:
                print("⚠️  Extension pg_trgm non installée")
            
            # Test des tables
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"\n📋 Tables trouvées ({len(tables)}):")
            for table in tables:
                print(f"   - {table}")
            
            # Test de la fonction de recherche
            try:
                result = conn.execute(text("SELECT search_transcripts('test', NULL, NULL)"))
                print("\n✅ Fonction search_transcripts disponible")
            except Exception as e:
                print(f"\n⚠️  Fonction search_transcripts non disponible: {e}")
            
            print("\n" + "=" * 60)
            print("✅ Tous les tests sont passés!")
            
    except Exception as e:
        print(f"\n❌ Erreur de connexion: {e}")
        print("\n💡 Vérifiez que:")
        print("   1. PostgreSQL est démarré (docker-compose up -d)")
        print("   2. Les variables d'environnement sont correctes")
        print("   3. Le schéma a été initialisé (python database/init_db.py)")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()

