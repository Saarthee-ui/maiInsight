"""Configuration management for the agentic data platform."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    llm_provider: Literal["openai", "anthropic", "ollama"] = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    
    # Warehouse Configuration
    warehouse_type: Literal["snowflake", "bigquery", "postgres"] = "snowflake"
    snowflake_account: str = ""
    snowflake_user: str = ""
    snowflake_password: str = ""
    snowflake_warehouse: str = ""
    snowflake_database: str = ""
    snowflake_schema_bronze: str = "BRONZE"
    snowflake_schema_silver: str = "SILVER"
    snowflake_schema_gold: str = "GOLD"
    
    # PostgreSQL Configuration (for warehouse)
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_database: str = ""
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_schema_bronze: str = "bronze"
    postgres_schema_silver: str = "silver"
    postgres_schema_gold: str = "gold"
    
    # AWS S3 Configuration
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = ""  # Default bucket name
    
    # State Storage
    state_store_type: Literal["sqlite", "postgres"] = "sqlite"
    state_store_path: str = "./storage/state.db"
    postgres_state_store_url: str = ""
    
    # dbt Configuration
    dbt_project_dir: str = "./dbt_project"
    dbt_profiles_dir: str = "~/.dbt"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Agent Configuration
    agent_temperature: float = 0.1
    max_agent_retries: int = 3
    agent_timeout_seconds: int = 300


# Global settings instance
settings = Settings()
