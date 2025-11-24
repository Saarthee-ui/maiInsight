"""Warehouse connection and utilities."""

import structlog
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any, Optional
from config import settings
from models.schemas import TableMetadata, ColumnMetadata
import threading
import time

logger = structlog.get_logger()


class TimeoutError(Exception):
    """Timeout error for database queries."""
    pass


class WarehouseConnection:
    """Warehouse connection manager."""
    
    def __init__(self):
        """Initialize warehouse connection."""
        self.engine: Optional[Engine] = None
        self.connected = False
        self._connect()
    
    def _connect(self):
        """Create database connection based on warehouse type."""
        try:
            warehouse_type = settings.warehouse_type.lower()
            
            # Check if credentials are configured
            if warehouse_type == "snowflake":
                if not all([settings.snowflake_account, settings.snowflake_user, 
                           settings.snowflake_password, settings.snowflake_database]):
                    logger.warning("Snowflake credentials not fully configured, warehouse will not be available")
                    return
                connection_string = (
                    f"snowflake://{settings.snowflake_user}:{settings.snowflake_password}"
                    f"@{settings.snowflake_account}/{settings.snowflake_database}"
                    f"?warehouse={settings.snowflake_warehouse}"
                )
            elif warehouse_type == "postgres":
                # PostgreSQL connection string
                if settings.postgres_state_store_url:
                    connection_string = settings.postgres_state_store_url
                else:
                    # Check if credentials are configured
                    if not settings.postgres_database:
                        logger.warning("PostgreSQL database not configured, warehouse will not be available")
                        return
                    # Build from individual settings
                    connection_string = (
                        f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
                        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
                    )
            else:
                logger.warning(f"Unsupported warehouse type: {warehouse_type}")
                return
            
            # Create engine with connection timeout
            self.engine = create_engine(
                connection_string,
                connect_args={"connect_timeout": 5} if warehouse_type == "postgres" else {},
                pool_pre_ping=True  # Verify connections before using
            )
            self.connected = True
            logger.info("Warehouse connection established", warehouse=warehouse_type)
        except Exception as e:
            logger.warning("Failed to initialize warehouse connection", error=str(e))
            self.engine = None
            self.connected = False
    
    def get_table_metadata(self, schema_name: str, table_name: str) -> TableMetadata:
        """
        Get metadata for a specific table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            
        Returns:
            TableMetadata object
        """
        if not self.engine:
            raise RuntimeError("Warehouse not connected")
        
        inspector = inspect(self.engine)
        
        # Get columns
        columns_info = inspector.get_columns(table_name, schema=schema_name)
        primary_keys = inspector.get_pk_constraint(table_name, schema=schema_name)
        foreign_keys = inspector.get_foreign_keys(table_name, schema=schema_name)
        
        pk_set = set(primary_keys.get("constrained_columns", []))
        fk_map = {
            fk["constrained_columns"][0]: fk["referred_table"]
            for fk in foreign_keys
        }
        
        columns = []
        for col in columns_info:
            col_name = col["name"]
            columns.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=str(col["type"]),
                    nullable=col.get("nullable", True),
                    is_primary_key=col_name in pk_set,
                    is_foreign_key=col_name in fk_map,
                    foreign_key_table=fk_map.get(col_name),
                )
            )
        
        # Get row count (handle different SQL dialects)
        with self.engine.connect() as conn:
            # PostgreSQL uses different quoting than Snowflake
            if settings.warehouse_type.lower() == "postgres":
                result = conn.execute(
                    text(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')
                )
            else:
                result = conn.execute(
                    text(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"')
                )
            row_count = result.scalar()
        
        return TableMetadata(
            name=table_name,
            schema_name=schema_name,
            columns=columns,
            business_keys=[col.name for col in columns if col.is_primary_key],
            row_count=row_count,
        )
    
    def list_tables(self, schema_name: str) -> List[str]:
        """List all tables in a schema."""
        if not self.engine or not self.connected:
            raise RuntimeError("Warehouse not connected")
        
        try:
            inspector = inspect(self.engine)
            # Use a simple timeout wrapper
            result = [None]
            exception = [None]
            
            def query_tables():
                try:
                    result[0] = inspector.get_table_names(schema=schema_name)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=query_tables)
            thread.daemon = True
            thread.start()
            thread.join(5)  # 5 second timeout
            
            if thread.is_alive():
                logger.warning(f"list_tables timed out for schema {schema_name}")
                raise RuntimeError("Query timed out after 5 seconds")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        except Exception as e:
            logger.warning(f"Failed to list tables for schema {schema_name}", error=str(e))
            raise RuntimeError(f"Failed to list tables: {str(e)}")
    
    def list_schemas(self) -> List[str]:
        """List all available schemas/databases."""
        if not self.engine or not self.connected:
            raise RuntimeError("Warehouse not connected")
        
        try:
            if settings.warehouse_type.lower() == "postgres":
                # PostgreSQL: query information_schema
                result = self.execute_query("""
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1', 'pg_toast_temp_1')
                    ORDER BY schema_name
                """, timeout=5)
                return [row['schema_name'] for row in result]
            elif settings.warehouse_type.lower() == "snowflake":
                # Snowflake: use SHOW SCHEMAS
                result = self.execute_query("SHOW SCHEMAS", timeout=5)
                return [row['name'] for row in result if row.get('name')]
            else:
                # Fallback: try inspector
                inspector = inspect(self.engine)
                result = [None]
                exception = [None]
                
                def query_schemas():
                    try:
                        result[0] = inspector.get_schema_names()
                    except Exception as e:
                        exception[0] = e
                
                thread = threading.Thread(target=query_schemas)
                thread.daemon = True
                thread.start()
                thread.join(5)
                
                if thread.is_alive():
                    raise RuntimeError("Query timed out after 5 seconds")
                if exception[0]:
                    raise exception[0]
                
                return result[0]
        except Exception as e:
            logger.warning("Failed to list schemas", error=str(e))
            return []
    
    def execute_query(self, query: str, timeout: int = 5) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.engine or not self.connected:
            raise RuntimeError("Warehouse not connected")
        
        try:
            result = [None]
            exception = [None]
            
            def execute():
                try:
                    with self.engine.connect() as conn:
                        query_result = conn.execute(text(query))
                        columns = query_result.keys()
                        result[0] = [dict(zip(columns, row)) for row in query_result]
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=execute)
            thread.daemon = True
            thread.start()
            thread.join(timeout)
            
            if thread.is_alive():
                logger.warning("Query execution timed out", query=query[:100])
                raise RuntimeError(f"Query timed out after {timeout} seconds")
            
            if exception[0]:
                raise exception[0]
            
            return result[0]
        except Exception as e:
            logger.warning("Query execution failed", error=str(e), query=query[:100])
            raise RuntimeError(f"Query execution failed: {str(e)}")
    
    def close(self):
        """Close connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Warehouse connection closed")


# Global warehouse instance - initialize lazily to avoid blocking
warehouse = None

def get_warehouse_instance():
    """Get or create warehouse instance."""
    global warehouse
    if warehouse is None:
        try:
            warehouse = WarehouseConnection()
        except Exception as e:
            logger.warning("Failed to create warehouse instance", error=str(e))
            # Create a dummy instance that will fail gracefully
            class DummyWarehouse:
                def __init__(self):
                    self.engine = None
                    self.connected = False
                def list_schemas(self):
                    raise RuntimeError("Warehouse not connected")
                def list_tables(self, schema):
                    raise RuntimeError("Warehouse not connected")
            warehouse = DummyWarehouse()
    return warehouse

# Initialize on import but don't fail if it doesn't work
try:
    warehouse = WarehouseConnection()
except Exception as e:
    logger.warning("Warehouse initialization failed at import time", error=str(e))
    warehouse = None
