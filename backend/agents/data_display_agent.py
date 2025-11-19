"""Data Display Agent - Formats and displays data for users."""

from typing import Dict, List, Any
from agents.base_agent import BaseAgent
import structlog

logger = structlog.get_logger()


class DataDisplayAgent(BaseAgent):
    """Agent that formats and displays data in a user-friendly way."""
    
    def __init__(self, **kwargs):
        """Initialize data display agent."""
        super().__init__(name="DataDisplayAgent", **kwargs)
    
    def format_data_for_display(self, data_result: Dict) -> Dict:
        """
        Format data for display in chatbot/UI.
        
        Args:
            data_result: Result from DataReaderAgent
            
        Returns:
            Formatted data with:
            - formatted_data: HTML/JSON formatted data
            - summary: Summary message
            - metadata: Display metadata
        """
        self.log("info", "Formatting data for display", 
                table=data_result.get("table_name"),
                rows=len(data_result.get("data", [])))
        
        data = data_result.get("data", [])
        columns = data_result.get("columns", [])
        total_rows = data_result.get("row_count", 0)
        displayed_rows = data_result.get("displayed_rows", 0)
        
        # Format as table (can be converted to HTML/JSON)
        formatted_table = self._format_as_table(data, columns)
        
        # Create summary message
        summary = self._create_summary(
            data_result.get("table_name"),
            displayed_rows,
            total_rows
        )
        
        return {
            "formatted_data": formatted_table,
            "raw_data": data,
            "columns": columns,
            "summary": summary,
            "metadata": {
                "table_name": data_result.get("table_name"),
                "schema_name": data_result.get("schema_name"),
                "total_rows": total_rows,
                "displayed_rows": displayed_rows,
                "has_more": total_rows > displayed_rows,
            }
        }
    
    def _format_as_table(self, data: List[Dict], columns: List[str]) -> List[Dict]:
        """Format data as table structure."""
        return [
            {col: row.get(col, None) for col in columns}
            for row in data
        ]
    
    def _create_summary(self, table_name: str, displayed: int, total: int) -> str:
        """Create summary message."""
        if displayed < total:
            return f"Showing {displayed} of {total} rows from {table_name}. Data refreshes automatically when the table is updated."
        else:
            return f"Showing all {total} rows from {table_name}. Data refreshes automatically when the table is updated."
    
    def execute(self, data_result: Dict) -> Dict:
        """Execute data formatting."""
        return self.format_data_for_display(data_result)

