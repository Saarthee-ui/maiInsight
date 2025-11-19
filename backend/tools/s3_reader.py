"""S3 file reading utilities for agents."""

import pandas as pd
import json
import io
from typing import Optional
from models.schemas import TableMetadata, ColumnMetadata
from tools.file_reader import FileReader
import structlog
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from config import settings

logger = structlog.get_logger()


class S3Reader:
    """Read and analyze files from Amazon S3."""
    
    def __init__(self):
        """Initialize S3 reader."""
        self.logger = logger
        self.file_reader = FileReader()  # Reuse file reader for parsing
        self.s3_client = self._create_s3_client()
    
    def _create_s3_client(self):
        """Create S3 client from configuration."""
        try:
            # Use credentials from settings or environment variables
            aws_access_key = getattr(settings, 'aws_access_key_id', '') or ''
            aws_secret_key = getattr(settings, 'aws_secret_access_key', '') or ''
            aws_region = getattr(settings, 'aws_region', 'us-east-1') or 'us-east-1'
            
            if aws_access_key and aws_secret_key:
                return boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
            else:
                # Use default credentials (from environment, IAM role, etc.)
                return boto3.client('s3', region_name=aws_region)
        except NoCredentialsError:
            raise ValueError(
                "AWS credentials not found. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
                "in .env or use AWS IAM role."
            )
    
    def read_s3_file_metadata(self, bucket: str, key: str) -> TableMetadata:
        """
        Read file from S3 and extract metadata (schema).
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (file path in bucket)
            
        Returns:
            TableMetadata object
        """
        self.logger.info("Reading file from S3", bucket=bucket, key=key)
        
        # Download file to memory
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            file_content = response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: s3://{bucket}/{key}")
            raise
        
        # Determine file type from key extension
        key_lower = key.lower()
        if key_lower.endswith('.csv'):
            return self._read_csv_from_bytes(file_content, key)
        elif key_lower.endswith('.json'):
            return self._read_json_from_bytes(file_content, key)
        elif key_lower.endswith('.parquet'):
            return self._read_parquet_from_bytes(file_content, key)
        elif key_lower.endswith(('.xlsx', '.xls')):
            return self._read_excel_from_bytes(file_content, key)
        else:
            raise ValueError(f"Unsupported file type: {key}")
    
    def _read_csv_from_bytes(self, content: bytes, key: str) -> TableMetadata:
        """Read CSV from bytes and extract metadata."""
        df = pd.read_csv(io.BytesIO(content), nrows=1000)
        
        columns = []
        for col_name, col_type in df.dtypes.items():
            columns.append(
                ColumnMetadata(
                    name=col_name,
                    data_type=str(col_type),
                    nullable=df[col_name].isna().any(),
                    is_primary_key=False,
                    is_foreign_key=False,
                )
            )
        
        # Get approximate row count (read full file for count)
        full_df = pd.read_csv(io.BytesIO(content))
        total_rows = len(full_df)
        
        return TableMetadata(
            name=self._get_table_name_from_key(key),
            schema_name="S3",
            columns=columns,
            row_count=total_rows,
        )
    
    def _read_json_from_bytes(self, content: bytes, key: str) -> TableMetadata:
        """Read JSON from bytes and extract metadata."""
        data = json.loads(content.decode('utf-8'))
        
        if isinstance(data, list) and len(data) > 0:
            first_item = data[0]
            columns = []
            for col_key, value in first_item.items():
                col_type = type(value).__name__
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
                        name=col_key,
                        data_type=sql_type,
                        nullable=True,
                    )
                )
            
            return TableMetadata(
                name=self._get_table_name_from_key(key),
                schema_name="S3",
                columns=columns,
                row_count=len(data),
            )
        else:
            raise ValueError("JSON file must contain an array of objects")
    
    def _read_parquet_from_bytes(self, content: bytes, key: str) -> TableMetadata:
        """Read Parquet from bytes and extract metadata."""
        df = pd.read_parquet(io.BytesIO(content))
        
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
            name=self._get_table_name_from_key(key),
            schema_name="S3",
            columns=columns,
            row_count=len(df),
        )
    
    def _read_excel_from_bytes(self, content: bytes, key: str) -> TableMetadata:
        """Read Excel from bytes and extract metadata."""
        df = pd.read_excel(io.BytesIO(content), nrows=1000)
        
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
            name=self._get_table_name_from_key(key),
            schema_name="S3",
            columns=columns,
            row_count=None,
        )
    
    def read_s3_file_data(self, bucket: str, key: str, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Read file data from S3 into pandas DataFrame.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key
            limit: Optional row limit
            
        Returns:
            pandas DataFrame
        """
        self.logger.info("Reading file data from S3", bucket=bucket, key=key)
        
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            file_content = response['Body'].read()
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: s3://{bucket}/{key}")
            raise
        
        key_lower = key.lower()
        
        if key_lower.endswith('.csv'):
            return pd.read_csv(io.BytesIO(file_content), nrows=limit)
        elif key_lower.endswith('.json'):
            data = json.loads(file_content.decode('utf-8'))
            df = pd.DataFrame(data)
            return df.head(limit) if limit else df
        elif key_lower.endswith('.parquet'):
            df = pd.read_parquet(io.BytesIO(file_content))
            return df.head(limit) if limit else df
        elif key_lower.endswith(('.xlsx', '.xls')):
            return pd.read_excel(io.BytesIO(file_content), nrows=limit)
        else:
            raise ValueError(f"Unsupported file type: {key}")
    
    def list_s3_files(self, bucket: str, prefix: str = "") -> list:
        """
        List files in S3 bucket with given prefix.
        
        Args:
            bucket: S3 bucket name
            prefix: Prefix to filter files (e.g., "data/bronze/")
            
        Returns:
            List of file keys
        """
        try:
            response = self.s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
            
            if 'Contents' not in response:
                return []
            
            return [obj['Key'] for obj in response['Contents']]
        except ClientError as e:
            self.logger.error("Failed to list S3 files", error=str(e))
            raise
    
    def _get_table_name_from_key(self, key: str) -> str:
        """Extract table name from S3 key."""
        # Get filename without extension
        import os
        filename = os.path.basename(key)
        return filename.rsplit('.', 1)[0].lower().replace(" ", "_")

