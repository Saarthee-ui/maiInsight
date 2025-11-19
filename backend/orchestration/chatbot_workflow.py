"""Chatbot workflow - User query → Data display with auto-refresh."""

from typing import TypedDict, Annotated, Optional, Callable
from langgraph.graph import StateGraph, END
from agents.chatbot_agent import ChatbotAgent
from agents.data_reader_agent import DataReaderAgent
from agents.data_display_agent import DataDisplayAgent
from agents.auto_refresh_agent import AutoRefreshAgent
from agents.historical_data_agent import HistoricalDataAgent
import structlog

logger = structlog.get_logger()


class ChatbotWorkflowState(TypedDict):
    """Chatbot workflow state."""
    user_query: str
    schema_name: str
    identified_table: Optional[str]
    query_understanding: Optional[dict]
    table_data: Optional[dict]
    formatted_display: Optional[dict]
    monitor_id: Optional[str]
    errors: Annotated[list, lambda x, y: x + y]


def create_chatbot_workflow():
    """Create chatbot workflow for data viewing."""
    
    # Initialize agents
    chatbot_agent = ChatbotAgent()
    data_reader_agent = DataReaderAgent()
    data_display_agent = DataDisplayAgent()
    auto_refresh_agent = AutoRefreshAgent()
    historical_agent = HistoricalDataAgent()
    
    # Define workflow steps
    def understand_query(state: ChatbotWorkflowState) -> ChatbotWorkflowState:
        """Step 1: Understand user query and identify table."""
        try:
            result = chatbot_agent.understand_query(
                state["user_query"],
                state["schema_name"]
            )
            
            return {
                **state,
                "query_understanding": result,
                "identified_table": result.get("table_name"),
                "errors": [],
            }
        except Exception as e:
            return {
                **state,
                "errors": [f"Query understanding failed: {str(e)}"],
            }
    
    def read_data(state: ChatbotWorkflowState) -> ChatbotWorkflowState:
        """Step 2: Read data from identified table."""
        if state.get("errors"):
            return state
        
        try:
            query_info = state["query_understanding"]
            table_name = query_info.get("table_name")
            
            if not table_name:
                return {
                    **state,
                    "errors": state.get("errors", []) + ["No table identified"],
                }
            
            data = data_reader_agent.read_table_data(
                schema_name=state["schema_name"],
                table_name=table_name,
                limit=query_info.get("limit", 10),
                filters=query_info.get("filters"),
            )
            
            return {
                **state,
                "table_data": data,
            }
        except Exception as e:
            return {
                **state,
                "errors": state.get("errors", []) + [f"Data reading failed: {str(e)}"],
            }
    
    def format_display(state: ChatbotWorkflowState) -> ChatbotWorkflowState:
        """Step 3: Format data for display."""
        if state.get("errors") or not state.get("table_data"):
            return state
        
        try:
            formatted = data_display_agent.format_data_for_display(state["table_data"])
            
            return {
                **state,
                "formatted_display": formatted,
            }
        except Exception as e:
            return {
                **state,
                "errors": state.get("errors", []) + [f"Display formatting failed: {str(e)}"],
            }
    
    def setup_auto_refresh(state: ChatbotWorkflowState) -> ChatbotWorkflowState:
        """Step 4: Set up auto-refresh monitoring."""
        if state.get("errors") or not state.get("table_data"):
            return state
        
        try:
            query_info = state["query_understanding"]
            table_name = query_info.get("table_name")
            
            # Define refresh callback
            def refresh_callback(schema: str, table: str, new_state: dict):
                """Callback when data changes."""
                logger.info("Data changed, refreshing", schema=schema, table=table)
                
                # Read new data
                new_data = data_reader_agent.read_table_data(
                    schema_name=schema,
                    table_name=table,
                    limit=query_info.get("limit", 10),
                    filters=query_info.get("filters"),
                )
                
                # Save snapshot to history
                historical_agent.save_snapshot(
                    schema_name=schema,
                    table_name=table,
                    data=new_data.get("data", []),
                    change_type="update"
                )
                
                # Format and return (in real app, this would update UI)
                formatted = data_display_agent.format_data_for_display(new_data)
                logger.info("Data refreshed", rows=len(new_data.get("data", [])))
            
            # Start monitoring
            monitor_id = auto_refresh_agent.start_monitoring(
                schema_name=state["schema_name"],
                table_name=table_name,
                refresh_callback=refresh_callback,
                check_interval=18000  # Check every 5 hours (5 * 60 * 60 seconds)
            )
            
            return {
                **state,
                "monitor_id": monitor_id,
            }
        except Exception as e:
            logger.warning("Auto-refresh setup failed", error=str(e))
            # Don't fail workflow if auto-refresh fails
            return state
    
    def save_initial_snapshot(state: ChatbotWorkflowState) -> ChatbotWorkflowState:
        """Step 5: Save initial snapshot to history."""
        if state.get("errors") or not state.get("table_data"):
            return state
        
        try:
            query_info = state["query_understanding"]
            table_name = query_info.get("table_name")
            
            historical_agent.save_snapshot(
                schema_name=state["schema_name"],
                table_name=table_name,
                data=state["table_data"].get("data", []),
                change_type="initial"
            )
        except Exception as e:
            logger.warning("Initial snapshot save failed", error=str(e))
            # Don't fail workflow
        
        return state
    
    # Build workflow graph
    workflow = StateGraph(ChatbotWorkflowState)
    
    workflow.add_node("understand_query", understand_query)
    workflow.add_node("read_data", read_data)
    workflow.add_node("format_display", format_display)
    workflow.add_node("setup_refresh", setup_auto_refresh)
    workflow.add_node("save_snapshot", save_initial_snapshot)
    
    # Define edges
    workflow.set_entry_point("understand_query")
    workflow.add_edge("understand_query", "read_data")
    workflow.add_edge("read_data", "format_display")
    workflow.add_edge("format_display", "setup_refresh")
    workflow.add_edge("setup_refresh", "save_snapshot")
    workflow.add_edge("save_snapshot", END)
    
    return workflow.compile()


def run_chatbot_query(user_query: str, schema_name: str = "public") -> dict:
    """
    Run chatbot query workflow.
    
    Args:
        user_query: User's question (e.g., "Show me orders data")
        schema_name: Schema to search in
        
    Returns:
        Workflow result with formatted data
    """
    workflow = create_chatbot_workflow()
    
    initial_state: ChatbotWorkflowState = {
        "user_query": user_query,
        "schema_name": schema_name,
        "identified_table": None,
        "query_understanding": None,
        "table_data": None,
        "formatted_display": None,
        "monitor_id": None,
        "errors": [],
    }
    
    result = workflow.invoke(initial_state)
    return result

