"""Data Reader Agent - Reads data from PostgreSQL tables."""

from typing import Dict, List, Optional, Any
from agents.base_agent import BaseAgent
from tools.warehouse import warehouse
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


class DataReaderAgent(BaseAgent):
    """Agent that reads data from PostgreSQL tables."""
    
    def __init__(self, **kwargs):
        """Initialize data reader agent."""
        super().__init__(name="DataReaderAgent", **kwargs)
    
    def read_table_data(
        self,
        schema_name: str,
        table_name: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None
    ) -> Dict:
        """
        Read data from PostgreSQL table.
        
        Args:
            schema_name: Schema name
            table_name: Table name
            limit: Number of rows to return (default: 10)
            filters: Optional filters (e.g., {"status": "completed"})
            order_by: Optional ORDER BY clause (e.g., "order_date DESC")
            
        Returns:
            Dictionary with:
            - data: List of rows (as dicts)
            - columns: Column names
            - row_count: Total rows in table
            - displayed_rows: Number of rows returned
        """
        self.log("info", "Reading table data", 
                schema=schema_name, 
                table=table_name,
                limit=limit)
        
        try:
            # Build SQL query
            query = self._build_query(schema_name, table_name, limit, filters, order_by)
            
            # Execute query
            rows = warehouse.execute_query(query)
            
            # Get total row count
            count_query = f'SELECT COUNT(*) as total FROM "{schema_name}"."{table_name}"'
            if filters:
                where_clause = self._build_where_clause(filters)
                count_query += f" WHERE {where_clause}"
            
            total_count_result = warehouse.execute_query(count_query)
            total_count = total_count_result[0]["total"] if total_count_result else len(rows)
            
            # Get column names from first row
            columns = list(rows[0].keys()) if rows else []
            
            self.log("info", "Data read successfully", 
                    rows_returned=len(rows),
                    total_rows=total_count)
            
            return {
                "data": rows,
                "columns": columns,
                "row_count": total_count,
                "displayed_rows": len(rows),
                "schema_name": schema_name,
                "table_name": table_name,
            }
        except Exception as e:
            self.log("error", "Data reading failed", error=str(e))
            raise
    
    def _build_query(
        self,
        schema_name: str,
        table_name: str,
        limit: int,
        filters: Optional[Dict],
        order_by: Optional[str]
    ) -> str:
        """Build SQL SELECT query."""
        query = f'SELECT * FROM "{schema_name}"."{table_name}"'
        
        # Add WHERE clause if filters provided
        if filters:
            where_clause = self._build_where_clause(filters)
            query += f" WHERE {where_clause}"
        
        # Add ORDER BY
        if order_by:
            query += f" ORDER BY {order_by}"
        else:
            # Default: order by first column (usually ID)
            query += f' ORDER BY (SELECT column_name FROM information_schema.columns WHERE table_schema = \'{schema_name}\' AND table_name = \'{table_name}\' LIMIT 1) DESC'
        
        # Add LIMIT
        query += f" LIMIT {limit}"
        
        return query
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> str:
        """Build WHERE clause from filters."""
        conditions = []
        for key, value in filters.items():
            if isinstance(value, str):
                conditions.append(f'"{key}" = \'{value}\'')
            else:
                conditions.append(f'"{key}" = {value}')
        return " AND ".join(conditions)
    
    def get_table_schema(self, schema_name: str, table_name: str) -> Dict:
        """Get table schema information."""
        metadata = warehouse.get_table_metadata(schema_name, table_name)
        
        return {
            "table_name": table_name,
            "schema_name": schema_name,
            "columns": [
                {
                    "name": col.name,
                    "type": col.data_type,
                    "nullable": col.nullable,
                }
                for col in metadata.columns
            ],
            "row_count": metadata.row_count,
        }
    
    def execute(self, schema_name: str, table_name: str, limit: int = 10, **kwargs) -> Dict:
        """Execute data reading."""
        return self.read_table_data(schema_name, table_name, limit, **kwargs)

