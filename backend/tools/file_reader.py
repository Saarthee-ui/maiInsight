"""File reading utilities for agents."""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from models.schemas import TableMetadata, ColumnMetadata
import structlog

logger = structlog.get_logger()


class FileReader:
    """Read and analyze files for schema extraction."""
    
    def __init__(self):
        """Initialize file reader."""
        self.logger = logger
    
    def read_file_metadata(self, file_path: str) -> TableMetadata:
        """
        Read file and extract metadata (schema).
        
        Args:
            file_path: Path to file (CSV, JSON, Parquet, Excel)
            
        Returns:
            TableMetadata object
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type
        extension = file_path_obj.suffix.lower()
        
        if extension == '.csv':
            return self._read_csv_metadata(file_path)
        elif extension == '.json':
            return self._read_json_metadata(file_path)
        elif extension == '.parquet':
            return self._read_parquet_metadata(file_path)
        elif extension in ['.xlsx', '.xls']:
            return self._read_excel_metadata(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
    
    def _read_csv_metadata(self, file_path: str) -> TableMetadata:
        """Read CSV file and extract metadata."""
        # Read sample to infer schema
        df = pd.read_csv(file_path, nrows=1000)  # Read first 1000 rows
        
        columns = []
        for col_name, col_type in df.dtypes.items():
            columns.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=str(col_type),
                    nullable=df[col_name].isna().any(),
                    is_primary_key=False,  # Will be inferred
                    is_foreign_key=False,
                )
            )
        
        # Get total row count (approximate for large files)
        try:
            total_rows = sum(1 for _ in open(file_path, encoding='utf-8')) - 1  # Subtract header
        except:
            total_rows = len(df)  # Fallback to sample size
        
        return TableMetadata(
            name=Path(file_path).stem,  # Filename without extension
            schema_name="FILE",
            columns=columns,
            row_count=total_rows,
        )
    
    def _read_json_metadata(self, file_path: str) -> TableMetadata:
        """Read JSON file and extract metadata."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(data, list) and len(data) > 0:
            # Array of objects
            first_item = data[0]
            columns = []
            for key, value in first_item.items():
                col_type = type(value).__name__
                # Map Python types to SQL types
                type_map = {
                    'int': 'INTEGER',
                    'float': 'NUMERIC',
                    'str': 'VARCHAR',
                    'bool': 'BOOLEAN',
                    'dict': 'JSONB',
                    'list': 'JSONB',
                }
                sql_type = type_map.get(col_type, 'VARCHAR')
                
                columns.append(
                    ColumnMetadata(
                        name=key,
                        data_type=sql_type,
                        nullable=True,
                    )
                )
            
            return TableMetadata(
                name=Path(file_path).stem,
                schema_name="FILE",
                columns=columns,
                row_count=len(data),
            )
        else:
            raise ValueError("JSON file must contain an array of objects")
    
    def _read_parquet_metadata(self, file_path: str) -> TableMetadata:
        """Read Parquet file and extract metadata."""
        df = pd.read_parquet(file_path)
        
        columns = []
        for col_name, col_type in df.dtypes.items():
            columns.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=str(col_type),
                    nullable=df[col_name].isna().any(),
                )
            )
        
        return TableMetadata(
            name=Path(file_path).stem,
            schema_name="FILE",
            columns=columns,
            row_count=len(df),
        )
    
    def _read_excel_metadata(self, file_path: str) -> TableMetadata:
        """Read Excel file and extract metadata."""
        df = pd.read_excel(file_path, nrows=1000)
        
        columns = []
        for col_name, col_type in df.dtypes.items():
            columns.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=str(col_type),
                    nullable=df[col_name].isna().any(),
                )
            )
        
        return TableMetadata(
            name=Path(file_path).stem,
            schema_name="FILE",
            columns=columns,
            row_count=None,  # Excel can have multiple sheets
        )
    
    def read_file_data(self, file_path: str, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Read file data into pandas DataFrame.
        
        Args:
            file_path: Path to file
            limit: Optional row limit
            
        Returns:
            pandas DataFrame
        """
        file_path_obj = Path(file_path)
        extension = file_path_obj.suffix.lower()
        
        if extension == '.csv':
            return pd.read_csv(file_path, nrows=limit)
        elif extension == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            return df.head(limit) if limit else df
        elif extension == '.parquet':
            df = pd.read_parquet(file_path)
            return df.head(limit) if limit else df
        elif extension in ['.xlsx', '.xls']:
            return pd.read_excel(file_path, nrows=limit)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

