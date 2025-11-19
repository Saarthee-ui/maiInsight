"""Quick test script to verify PostgreSQL connection."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.warehouse import warehouse
from config import settings
import structlog

logger = structlog.get_logger()


def test_connection():
    """Test PostgreSQL connection."""
    print("=" * 60)
    print("PostgreSQL Connection Test")
    print("=" * 60)
    print()
    
    # Show configuration
    print("📋 Configuration:")
    print(f"   Warehouse Type: {settings.warehouse_type}")
    print(f"   Host: {settings.postgres_host}")
    print(f"   Port: {settings.postgres_port}")
    print(f"   Database: {settings.postgres_database}")
    print(f"   User: {settings.postgres_user}")
    print(f"   Schema (Bronze): {settings.postgres_schema_bronze}")
    print()
    
    # Test 1: Basic connection
    print("🔌 Test 1: Basic Connection")
    try:
        result = warehouse.execute_query("SELECT 1 as test")
        print(f"   ✅ Connection successful!")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Check PostgreSQL is running")
        print("   2. Verify .env file has correct credentials")
        print("   3. Check firewall/network settings")
        return False
    print()
    
    # Test 2: List schemas
    print("📂 Test 2: List Available Schemas")
    try:
        result = warehouse.execute_query("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
            ORDER BY schema_name
        """)
        schemas = [row['schema_name'] for row in result]
        print(f"   ✅ Found {len(schemas)} schemas:")
        for schema in schemas:
            print(f"      - {schema}")
    except Exception as e:
        print(f"   ⚠️  Could not list schemas: {e}")
    print()
    
    # Test 3: Check target schema exists
    print(f"🎯 Test 3: Check Target Schema ('{settings.postgres_schema_bronze}')")
    try:
        result = warehouse.execute_query(f"""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name = '{settings.postgres_schema_bronze}'
        """)
        if result:
            print(f"   ✅ Schema '{settings.postgres_schema_bronze}' exists")
        else:
            print(f"   ⚠️  Schema '{settings.postgres_schema_bronze}' does not exist")
            print(f"   💡 Create it with: CREATE SCHEMA IF NOT EXISTS {settings.postgres_schema_bronze};")
    except Exception as e:
        print(f"   ⚠️  Could not check schema: {e}")
    print()
    
    # Test 4: List tables in target schema
    print(f"📊 Test 4: List Tables in '{settings.postgres_schema_bronze}' Schema")
    try:
        tables = warehouse.list_tables(settings.postgres_schema_bronze)
        if tables:
            print(f"   ✅ Found {len(tables)} tables:")
            for table in tables:
                print(f"      - {table}")
        else:
            print(f"   ⚠️  No tables found in '{settings.postgres_schema_bronze}' schema")
            print(f"   💡 Create a test table or load data into this schema")
    except Exception as e:
        print(f"   ⚠️  Could not list tables: {e}")
    print()
    
    # Test 5: Test reading from a table (if exists)
    print(f"📖 Test 5: Test Reading from Table")
    try:
        tables = warehouse.list_tables(settings.postgres_schema_bronze)
        if tables:
            test_table = tables[0]
            print(f"   Testing with table: {test_table}")
            
            # Get row count
            count_result = warehouse.execute_query(
                f'SELECT COUNT(*) as total FROM "{settings.postgres_schema_bronze}"."{test_table}"'
            )
            row_count = count_result[0]['total'] if count_result else 0
            print(f"   ✅ Table has {row_count} rows")
            
            # Read sample data
            if row_count > 0:
                sample = warehouse.execute_query(
                    f'SELECT * FROM "{settings.postgres_schema_bronze}"."{test_table}" LIMIT 3'
                )
                print(f"   ✅ Sample data (first 3 rows):")
                for i, row in enumerate(sample, 1):
                    print(f"      Row {i}: {dict(row)}")
            else:
                print(f"   ⚠️  Table is empty (no data to read)")
        else:
            print(f"   ⚠️  No tables to test")
    except Exception as e:
        print(f"   ⚠️  Could not read table: {e}")
    print()
    
    # Summary
    print("=" * 60)
    print("✅ Connection Test Complete!")
    print("=" * 60)
    print()
    print("💡 Next Steps:")
    print("   1. If connection works, you can use the chatbot:")
    print("      python scripts/run_agent.py 'Show me orders data'")
    print()
    print("   2. Or start the web app:")
    print("      python app.py")
    print()
    print("   3. Make sure you have tables in the 'bronze' schema")
    print("      (or whatever schema you configured)")
    print()
    
    return True


if __name__ == "__main__":
    try:
        test_connection()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

