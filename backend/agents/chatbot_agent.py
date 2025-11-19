"""Chatbot Agent - Understands user questions and identifies data tables."""

from typing import Dict, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.base_agent import BaseAgent
from tools.warehouse import warehouse
import structlog

logger = structlog.get_logger()
json_parser = JsonOutputParser()


class ChatbotAgent(BaseAgent):
    """Agent that understands user questions and identifies which tables to display."""
    
    def __init__(self, **kwargs):
        """Initialize chatbot agent."""
        super().__init__(name="ChatbotAgent", **kwargs)
    
    def understand_query(self, user_query: str, schema_name: str = "public") -> Dict:
        """
        Understand user query and identify which table/data they want.
        
        Args:
            user_query: User's question/request (e.g., "Show me orders data")
            schema_name: Schema to search in (default: "bronze")
            
        Returns:
            Dictionary with:
            - table_name: Identified table name
            - schema_name: Schema name
            - query_type: Type of query (view, filter, aggregate, etc.)
            - filters: Optional filters from query
            - limit: Number of rows to show (default: 10)
        """
        self.log("info", "Understanding user query", query=user_query)
        
        # List available tables
        available_tables = warehouse.list_tables(schema_name)
        
        # Use LLM to understand query and identify table
        result = self._identify_table_from_query(user_query, available_tables, schema_name)
        
        self.log("info", "Query understood", 
                table=result.get("table_name"),
                query_type=result.get("query_type"))
        
        return result
    
    def _identify_table_from_query(
        self, 
        user_query: str, 
        available_tables: List[str],
        schema_name: str
    ) -> Dict:
        """Use LLM to identify which table user wants."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful data assistant. Users ask questions about data tables.

Your task:
1. Identify which table the user wants to see
2. Understand what they want (view data, filter, aggregate, etc.)
3. Extract any filters or conditions from the query

Available tables: {available_tables}

Return JSON with:
- table_name: The table name from available_tables (or null if not found)
- schema_name: Schema name
- query_type: "view" (just show data), "filter" (with conditions), "aggregate" (count, sum, etc.)
- filters: Optional dict with filter conditions (e.g., {{"status": "completed"}})
- limit: Number of rows to show (default: 10)
- message: Friendly response message
"""),
            ("user", """User query: {user_query}

Identify the table and understand what they want.""")
        ])
        
        chain = prompt | self.llm | json_parser
        
        try:
            result = chain.invoke({
                "user_query": user_query,
                "available_tables": ", ".join(available_tables),
            })
            
            # Validate table exists - try case-insensitive and partial matching
            requested_table = result.get("table_name")
            if requested_table:
                # Try exact match first
                if requested_table in available_tables:
                    result["table_name"] = requested_table
                else:
                    # Try case-insensitive match
                    requested_lower = requested_table.lower()
                    matched = None
                    for table in available_tables:
                        if table.lower() == requested_lower:
                            matched = table
                            break
                        # Try partial match (e.g., "orders" matches "order_bz")
                        if requested_lower in table.lower() or table.lower() in requested_lower:
                            matched = table
                            break
                    
                    if matched:
                        result["table_name"] = matched
                        self.log("info", "Table matched (case-insensitive/partial)", 
                                requested=requested_table,
                                matched=matched)
                    else:
                        self.log("warning", "Table not found, using first available", 
                                requested=requested_table,
                                available=available_tables)
                        result["table_name"] = available_tables[0] if available_tables else None
            
            # Set defaults
            result.setdefault("schema_name", schema_name)
            result.setdefault("query_type", "view")
            result.setdefault("limit", 10)
            result.setdefault("filters", {})
            
            return result
        except Exception as e:
            self.log("error", "Query understanding failed", error=str(e))
            # Fallback: return first table
            return {
                "table_name": available_tables[0] if available_tables else None,
                "schema_name": schema_name,
                "query_type": "view",
                "limit": 10,
                "filters": {},
                "message": f"I'll show you data from the available tables.",
            }
    
    def execute(self, user_query: str, schema_name: str = "public") -> Dict:
        """Execute query understanding."""
        return self.understand_query(user_query, schema_name)

