"""Pydantic models for data structures."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class TableType(str, Enum):
    """Table classification types."""
    TRANSACTIONAL = "transactional"
    REFERENCE = "reference"
    SNAPSHOT = "snapshot"
    CDC = "cdc"


class ColumnMetadata(BaseModel):
    """Column metadata."""
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_table: Optional[str] = None
    description: Optional[str] = None


class TableMetadata(BaseModel):
    """Table metadata."""
    name: str
    schema_name: str
    columns: List[ColumnMetadata]
    table_type: Optional[TableType] = None
    business_keys: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    row_count: Optional[int] = None


class HubDefinition(BaseModel):
    """Data Vault Hub definition."""
    name: str
    business_key: str
    source_table: str
    description: Optional[str] = None


class LinkDefinition(BaseModel):
    """Data Vault Link definition."""
    name: str
    hub_keys: List[str]  # List of hub names this link connects
    source_tables: List[str]
    description: Optional[str] = None


class SatelliteDefinition(BaseModel):
    """Data Vault Satellite definition."""
    name: str
    parent_hub: Optional[str] = None  # Hub or Link this satellite belongs to
    parent_link: Optional[str] = None
    attributes: List[str]  # Column names
    effective_date_column: str = "EFFECTIVE_DATE"
    end_date_column: Optional[str] = "END_DATE"
    description: Optional[str] = None


class DataVaultModel(BaseModel):
    """Complete Data Vault model specification."""
    hubs: List[HubDefinition] = Field(default_factory=list)
    links: List[LinkDefinition] = Field(default_factory=list)
    satellites: List[SatelliteDefinition] = Field(default_factory=list)
    source_tables: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)


class QueryPattern(BaseModel):
    """Query pattern analysis."""
    query_text: str
    execution_time_ms: int
    rows_scanned: Optional[int] = None
    cost_estimate: Optional[float] = None
    frequency: int = 1
    tables_accessed: List[str] = Field(default_factory=list)
    operation_types: List[str] = Field(default_factory=list)  # SELECT, JOIN, GROUP BY, etc.


class GoldOptimizationCandidate(BaseModel):
    """Gold optimization candidate."""
    query_pattern: QueryPattern
    estimated_cost_reduction: float
    estimated_storage_cost: float
    roi_score: float
    recommended_structure: str  # e.g., "materialized_view", "aggregate_table"
    recommended_sql: Optional[str] = None


class AnomalyAlert(BaseModel):
    """Anomaly detection alert."""
    alert_type: str  # "data_quality", "schema_drift", "pipeline_failure"
    severity: str  # "low", "medium", "high", "critical"
    message: str
    affected_tables: List[str] = Field(default_factory=list)
    detected_at: datetime = Field(default_factory=datetime.now)
    remediation_suggestion: Optional[str] = None
