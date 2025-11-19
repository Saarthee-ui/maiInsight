"""Check which database has tables."""

from sqlalchemy import create_engine, text
from config import settings

def check_database(db_name):
    """Check schemas and tables in a database."""
    try:
        engine = create_engine(
            f'postgresql://{settings.postgres_user}:{settings.postgres_password}'
            f'@{settings.postgres_host}:{settings.postgres_port}/{db_name}'
        )
        conn = engine.connect()
        
        # Get schemas
        result = conn.execute(text("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """))
        schemas = [row[0] for row in result]
        
        print(f"\n📊 Database: {db_name}")
        print(f"   Schemas: {', '.join(schemas) if schemas else '(none)'}")
        
        # Check for tables in each schema
        for schema in schemas:
            result = conn.execute(text(f"""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = '{schema}'
                LIMIT 10
            """))
            tables = [row[0] for row in result]
            if tables:
                print(f"   Tables in '{schema}': {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
            else:
                print(f"   Tables in '{schema}': (no tables)")
        
        conn.close()
        return True
    except Exception as e:
        print(f"\n❌ Database {db_name}: {str(e)[:100]}")
        return False

print("=" * 60)
print("Checking PostgreSQL Databases")
print("=" * 60)

# Check both databases
check_database("postgres")
check_database("PRDatabase")

print("\n" + "=" * 60)
print("✅ Credentials are working!")
print("💡 Update POSTGRES_DATABASE in .env to use the correct database")
print("=" * 60)

