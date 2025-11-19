"""Historical Data Agent - Stores snapshots of data when it changes."""

from typing import Dict, List, Optional
from datetime import datetime
from agents.base_agent import BaseAgent
from tools.warehouse import warehouse
from sqlalchemy import text, create_engine
from config import settings
import structlog
import json

logger = structlog.get_logger()


class HistoricalDataAgent(BaseAgent):
    """Agent that stores historical snapshots of data."""
    
    def __init__(self, **kwargs):
        """Initialize historical data agent."""
        super().__init__(name="HistoricalDataAgent", **kwargs)
        self.engine = self._create_connection()
        self._ensure_history_schema()
    
    def _create_connection(self):
        """Create PostgreSQL connection for history storage."""
        if settings.warehouse_type.lower() != "postgres":
            raise ValueError("Historical data requires PostgreSQL")
        
        if settings.postgres_state_store_url:
            connection_string = settings.postgres_state_store_url
        else:
            connection_string = (
                f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
                f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
            )
        
        return create_engine(connection_string)
    
    def _ensure_history_schema(self):
        """Create history schema and table if they don't exist."""
        with self.engine.connect() as conn:
            # Create history schema
            conn.execute(text('CREATE SCHEMA IF NOT EXISTS history'))
            conn.commit()
            
            # Create history table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS history.data_snapshots (
                    snapshot_id SERIAL PRIMARY KEY,
                    schema_name VARCHAR(255) NOT NULL,
                    table_name VARCHAR(255) NOT NULL,
                    snapshot_timestamp TIMESTAMP NOT NULL,
                    row_count INTEGER NOT NULL,
                    snapshot_data JSONB,
                    change_type VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            
            # Create index for faster lookups
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_snapshots_table_time 
                ON history.data_snapshots(schema_name, table_name, snapshot_timestamp DESC)
            """))
            conn.commit()
    
    def save_snapshot(
        self,
        schema_name: str,
        table_name: str,
        data: List[Dict],
        change_type: str = "update"
    ) -> int:
        """
        Save a snapshot of current data.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            data: Current data to snapshot
            change_type: Type of change ("update", "insert", "delete")
            
        Returns:
            Snapshot ID
        """
        self.log("info", "Saving data snapshot", 
                schema=schema_name,
                table=table_name,
                rows=len(data))
        
        try:
            with self.engine.connect() as conn:
                # Insert snapshot
                result = conn.execute(
                    text("""
                        INSERT INTO history.data_snapshots 
                        (schema_name, table_name, snapshot_timestamp, row_count, snapshot_data, change_type)
                        VALUES (:schema_name, :table_name, :timestamp, :row_count, :data, :change_type)
                        RETURNING snapshot_id
                    """),
                    {
                        "schema_name": schema_name,
                        "table_name": table_name,
                        "timestamp": datetime.now(),
                        "row_count": len(data),
                        "data": json.dumps(data),
                        "change_type": change_type,
                    }
                )
                snapshot_id = result.scalar()
                conn.commit()
                
                self.log("info", "Snapshot saved", snapshot_id=snapshot_id)
                return snapshot_id
        except Exception as e:
            self.log("error", "Snapshot save failed", error=str(e))
            raise
    
    def get_snapshot(self, snapshot_id: int) -> Dict:
        """Get a specific snapshot by ID."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM history.data_snapshots
                    WHERE snapshot_id = :snapshot_id
                """),
                {"snapshot_id": snapshot_id}
            )
            row = result.fetchone()
            
            if row:
                # Handle JSONB data - it might already be parsed or still be a string
                snapshot_data = row[5]
                if snapshot_data:
                    if isinstance(snapshot_data, str):
                        snapshot_data = json.loads(snapshot_data)
                    # If it's already a list/dict, use it as is
                else:
                    snapshot_data = []
                
                return {
                    "snapshot_id": row[0],
                    "schema_name": row[1],
                    "table_name": row[2],
                    "snapshot_timestamp": row[3],
                    "row_count": row[4],
                    "snapshot_data": snapshot_data,
                    "change_type": row[6],
                }
            return None
    
    def get_snapshots(
        self,
        schema_name: str,
        table_name: str,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent snapshots for a table."""
        with self.engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM history.data_snapshots
                    WHERE schema_name = :schema_name AND table_name = :table_name
                    ORDER BY snapshot_timestamp DESC
                    LIMIT :limit
                """),
                {
                    "schema_name": schema_name,
                    "table_name": table_name,
                    "limit": limit,
                }
            )
            
            snapshots = []
            for row in result:
                # Handle JSONB data - it might already be parsed or still be a string
                snapshot_data = row[5]
                if snapshot_data:
                    if isinstance(snapshot_data, str):
                        snapshot_data = json.loads(snapshot_data)
                    # If it's already a list/dict, use it as is
                else:
                    snapshot_data = []
                
                snapshots.append({
                    "snapshot_id": row[0],
                    "schema_name": row[1],
                    "table_name": row[2],
                    "snapshot_timestamp": row[3],
                    "row_count": row[4],
                    "snapshot_data": snapshot_data,
                    "change_type": row[6],
                })
            
            return snapshots
    
    def compare_snapshots(self, snapshot_id_1: int, snapshot_id_2: int) -> Dict:
        """Compare two snapshots to show what changed."""
        snap1 = self.get_snapshot(snapshot_id_1)
        snap2 = self.get_snapshot(snapshot_id_2)
        
        if not snap1 or not snap2:
            raise ValueError("One or both snapshots not found")
        
        data1 = snap1["snapshot_data"]
        data2 = snap2["snapshot_data"]
        
        # Simple comparison (you can enhance this)
        return {
            "snapshot1": snap1,
            "snapshot2": snap2,
            "row_count_change": snap2["row_count"] - snap1["row_count"],
            "timestamp_diff": (snap2["snapshot_timestamp"] - snap1["snapshot_timestamp"]).total_seconds(),
        }
    
    def execute(self, schema_name: str, table_name: str, data: List[Dict], **kwargs) -> int:
        """Execute snapshot save."""
        return self.save_snapshot(schema_name, table_name, data, **kwargs)

