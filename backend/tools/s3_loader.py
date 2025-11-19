"""S3 file loading utilities for PostgreSQL."""

import pandas as pd
from typing import Optional
from sqlalchemy import create_engine, text, inspect
from config import settings
from tools.s3_reader import S3Reader
import structlog

logger = structlog.get_logger()


class S3PostgresLoader:
    """Load files from S3 into PostgreSQL Bronze schema."""
    
    def __init__(self):
        """Initialize S3 PostgreSQL loader."""
        self.logger = logger
        self.s3_reader = S3Reader()
        self.engine = self._create_connection()
    
    def _create_connection(self):
        """Create PostgreSQL connection."""
        if settings.warehouse_type.lower() != "postgres":
            raise ValueError("S3 loader requires WAREHOUSE_TYPE=postgres")
        
        if settings.postgres_state_store_url:
            connection_string = settings.postgres_state_store_url
        else:
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
    
    def load_s3_file_to_postgres(
        self,
        bucket: str,
        key: str,
        schema_name: str = "bronze",
        table_name: Optional[str] = None,
        if_exists: str = "replace"
    ) -> str:
        """
        Load file from S3 into PostgreSQL Bronze schema.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (file path)
            schema_name: Target schema (default: "bronze")
            table_name: Target table name (default: filename)
            if_exists: What to do if table exists ("replace", "append", "fail")
            
        Returns:
            Created table name
        """
        self.logger.info("Loading S3 file to PostgreSQL", 
                        bucket=bucket, 
                        key=key, 
                        schema=schema_name)
        
        # Determine table name
        if not table_name:
            table_name = self.s3_reader._get_table_name_from_key(key)
        
        # Create schema if needed
        self.create_schema_if_not_exists(schema_name)
        
        # Read file from S3
        df = self.s3_reader.read_s3_file_data(bucket, key)
        
        # Load to PostgreSQL
        df.to_sql(
            name=table_name,
            con=self.engine,
            schema=schema_name,
            if_exists=if_exists,
            index=False,
            method='multi'  # Faster for large datasets
        )
        
        self.logger.info("S3 file loaded successfully", 
                        table=f"{schema_name}.{table_name}",
                        rows=len(df))
        
        return table_name
    
    def get_table_metadata(self, schema_name: str, table_name: str):
        """Get metadata for a table in PostgreSQL."""
        from tools.warehouse import warehouse
        
        return warehouse.get_table_metadata(schema_name, table_name)
    
    def list_tables(self, schema_name: str):
        """List all tables in a schema."""
        inspector = inspect(self.engine)
        return inspector.get_table_names(schema=schema_name)

