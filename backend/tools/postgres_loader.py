"""PostgreSQL file loading utilities."""

import pandas as pd
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, text, inspect
from config import settings
from tools.file_reader import FileReader
import structlog

logger = structlog.get_logger()


class PostgresFileLoader:
    """Load files into PostgreSQL and manage Bronze schema."""
    
    def __init__(self):
        """Initialize PostgreSQL file loader."""
        self.logger = logger
        self.file_reader = FileReader()
        self.engine = self._create_connection()
    
    def _create_connection(self):
        """Create PostgreSQL connection."""
        if settings.warehouse_type.lower() != "postgres":
            raise ValueError("PostgreSQL loader requires WAREHOUSE_TYPE=postgres")
        
        # Build connection string from settings
        if settings.postgres_state_store_url:
            connection_string = settings.postgres_state_store_url
        else:
            # Build from individual settings
            connection_string = (
                f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
                f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
            )
        
        return create_engine(connection_string)
    
    def create_schema_if_not_exists(self, schema_name: str):
        """Create schema if it doesn't exist."""
        with self.engine.connect() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
            conn.commit()
        self.logger.info("Schema created/verified", schema=schema_name)
    
    def load_file_to_postgres(
        self,
        file_path: str,
        schema_name: str = "bronze",
        table_name: Optional[str] = None,
        if_exists: str = "replace"
    ) -> str:
        """
        Load file into PostgreSQL Bronze schema.
        
        Args:
            file_path: Path to file (CSV, JSON, Parquet, Excel)
            schema_name: Target schema (default: "bronze")
            table_name: Target table name (default: filename)
            if_exists: What to do if table exists ("replace", "append", "fail")
            
        Returns:
            Created table name
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine table name
        if not table_name:
            table_name = file_path_obj.stem.lower().replace(" ", "_")
        
        self.logger.info("Loading file to PostgreSQL", 
                        file=file_path, 
                        schema=schema_name, 
                        table=table_name)
        
        # Create schema if needed
        self.create_schema_if_not_exists(schema_name)
        
        # Read file
        df = self.file_reader.read_file_data(file_path)
        
        # Load to PostgreSQL
        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=schema_name,
            if_exists=if_exists,
            index=False,
            method='multi'  # Faster for large datasets
        )
        
        self.logger.info("File loaded successfully", 
                        table=f"{schema_name}.{table_name}",
                        rows=len(df))
        
        return table_name
    
    def get_table_metadata(self, schema_name: str, table_name: str):
        """Get metadata for a table in PostgreSQL."""
        from tools.warehouse import warehouse
        
        # Use warehouse connection to get metadata
        return warehouse.get_table_metadata(schema_name, table_name)
    
    def list_tables(self, schema_name: str):
        """List all tables in a schema."""
        inspector = inspect(self.engine)
        return inspector.get_table_names(schema=schema_name)

