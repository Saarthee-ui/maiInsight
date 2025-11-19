"""Auto-Refresh Agent - Monitors PostgreSQL tables for changes."""

from typing import Dict, Optional, Callable
from datetime import datetime
from agents.base_agent import BaseAgent
from tools.warehouse import warehouse
from sqlalchemy import text
import structlog
import time

logger = structlog.get_logger()


class AutoRefreshAgent(BaseAgent):
    """Agent that monitors PostgreSQL tables and triggers refresh when data changes."""
    
    def __init__(self, **kwargs):
        """Initialize auto-refresh agent."""
        super().__init__(name="AutoRefreshAgent", **kwargs)
        self.monitored_tables: Dict[str, Dict] = {}  # Track monitored tables
    
    def start_monitoring(
        self,
        schema_name: str,
        table_name: str,
        refresh_callback: Optional[Callable] = None,
        check_interval: int = 18000  # Check every 5 hours (5 * 60 * 60 seconds)
    ) -> str:
        """
        Start monitoring a table for changes.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            refresh_callback: Function to call when data changes
            check_interval: How often to check (seconds)
            
        Returns:
            Monitor ID
        """
        monitor_id = f"{schema_name}.{table_name}"
        
        self.log("info", "Starting table monitoring", 
                schema=schema_name,
                table=table_name,
                interval=check_interval)
        
        # Get initial state
        initial_state = self._get_table_state(schema_name, table_name)
        
        self.monitored_tables[monitor_id] = {
            "schema_name": schema_name,
            "table_name": table_name,
            "last_state": initial_state,
            "refresh_callback": refresh_callback,
            "check_interval": check_interval,
            "last_check": datetime.now(),
            "is_active": True,
        }
        
        return monitor_id
    
    def stop_monitoring(self, monitor_id: str):
        """Stop monitoring a table."""
        if monitor_id in self.monitored_tables:
            self.monitored_tables[monitor_id]["is_active"] = False
            del self.monitored_tables[monitor_id]
            self.log("info", "Stopped monitoring", monitor_id=monitor_id)
    
    def check_for_changes(self, monitor_id: str) -> bool:
        """
        Check if monitored table has changed.
        
        Args:
            monitor_id: Monitor ID
            
        Returns:
            True if data changed, False otherwise
        """
        if monitor_id not in self.monitored_tables:
            return False
        
        monitor = self.monitored_tables[monitor_id]
        
        if not monitor["is_active"]:
            return False
        
        # Get current state
        current_state = self._get_table_state(
            monitor["schema_name"],
            monitor["table_name"]
        )
        
        # Compare with last state
        if current_state != monitor["last_state"]:
            self.log("info", "Table data changed", 
                    monitor_id=monitor_id,
                    old_row_count=monitor["last_state"].get("row_count"),
                    new_row_count=current_state.get("row_count"))
            
            # Update state
            monitor["last_state"] = current_state
            monitor["last_check"] = datetime.now()
            
            # Trigger refresh callback
            if monitor["refresh_callback"]:
                try:
                    monitor["refresh_callback"](
                        monitor["schema_name"],
                        monitor["table_name"],
                        current_state
                    )
                except Exception as e:
                    self.log("error", "Refresh callback failed", error=str(e))
            
            return True
        
        monitor["last_check"] = datetime.now()
        return False
    
    def check_all_monitored_tables(self):
        """Check all monitored tables for changes."""
        for monitor_id in list(self.monitored_tables.keys()):
            self.check_for_changes(monitor_id)
    
    def _get_table_state(self, schema_name: str, table_name: str) -> Dict:
        """Get current state of table (row count, last update, etc.)."""
        try:
            # Get row count
            count_query = f'SELECT COUNT(*) as total FROM "{schema_name}"."{table_name}"'
            count_result = warehouse.execute_query(count_query)
            row_count = count_result[0]["total"] if count_result else 0
            
            # Try to get last update timestamp (if table has update timestamp column)
            # This is a simple check - you might need to customize based on your schema
            metadata = warehouse.get_table_metadata(schema_name, table_name)
            has_timestamp = any(
                "timestamp" in col.name.lower() or "updated" in col.name.lower()
                for col in metadata.columns
            )
            
            return {
                "row_count": row_count,
                "has_timestamp": has_timestamp,
                "checked_at": datetime.now().isoformat(),
            }
        except Exception as e:
            self.log("error", "Failed to get table state", error=str(e))
            return {"row_count": 0, "checked_at": datetime.now().isoformat()}
    
    def execute(self, monitor_id: str) -> bool:
        """Execute change check."""
        return self.check_for_changes(monitor_id)

