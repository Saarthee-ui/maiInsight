"""Warehouse connection and utilities."""

import structlog
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from typing import List, Dict, Any, Optional
from config import settings
from models.schemas import TableMetadata, ColumnMetadata

logger = structlog.get_logger()


class WarehouseConnection:
    """Warehouse connection manager."""
    
    def __init__(self):
        """Initialize warehouse connection."""
        self.engine: Optional[Engine] = None
        self._connect()
    
    def _connect(self):
        """Create database connection based on warehouse type."""
        warehouse_type = settings.warehouse_type.lower()
        
        if warehouse_type == "snowflake":
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
                # Build from individual settings
                connection_string = (
                    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
                    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
                )
        else:
            raise ValueError(f"Unsupported warehouse type: {warehouse_type}")
        
        self.engine = create_engine(connection_string)
        logger.info("Warehouse connection established", warehouse=warehouse_type)
    
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
        if not self.engine:
            raise RuntimeError("Warehouse not connected")
        
        inspector = inspect(self.engine)
        return inspector.get_table_names(schema=schema_name)
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results."""
        if not self.engine:
            raise RuntimeError("Warehouse not connected")
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]
    
    def close(self):
        """Close connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Warehouse connection closed")


# Global warehouse instance
warehouse = WarehouseConnection()
