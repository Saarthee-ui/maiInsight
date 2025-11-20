"""Build Summary Agent - Guides users through creating transformation flows."""

from typing import Dict, List, Optional, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.base_agent import BaseAgent
from tools.warehouse import warehouse
import structlog
from enum import Enum

logger = structlog.get_logger()
json_parser = JsonOutputParser()


class ConversationStage(str, Enum):
    """Stages of the build conversation."""
    INITIAL = "initial"  # Ask what user wants to accomplish
    SUMMARY = "summary"  # Present summary with hints
    DATABASE_SELECTION = "database_selection"  # Ask for database(s)
    TRANSFORMATION_NAME = "transformation_name"  # Ask for transformation name
    CONNECTION_DETAILS = "connection_details"  # Ask for connection details
    CONFIRMATION = "confirmation"  # Final confirmation
    COMPLETE = "complete"  # Setup complete


class BuildSummaryAgent(BaseAgent):
    """Agent that guides users through creating transformation flows."""
    
    def __init__(self, **kwargs):
        """Initialize build summary agent."""
        super().__init__(name="BuildSummaryAgent", **kwargs)
        self.conversation_state = {}  # Store conversation state per session
    
    def start_conversation(self, session_id: str, user_input: str) -> Dict:
        """
        Start or continue a conversation about building a transformation.
        
        Args:
            session_id: Unique session identifier
            user_input: User's input message
            
        Returns:
            Dictionary with:
            - stage: Current conversation stage
            - message: Agent's response message
            - hints: Optional hints/suggestions
            - requires_input: Whether agent needs user input
            - data: Collected data so far
        """
        self.log("info", "Processing build conversation", session_id=session_id, input=user_input)
        
        # Get or initialize session state
        if session_id not in self.conversation_state:
            self.conversation_state[session_id] = {
                "stage": ConversationStage.INITIAL,
                "data": {},
                "messages": []
            }
        
        state = self.conversation_state[session_id]
        state["messages"].append({"role": "user", "content": user_input})
        
        # Process based on current stage
        if state["stage"] == ConversationStage.INITIAL:
            return self._handle_initial(user_input, state)
        elif state["stage"] == ConversationStage.SUMMARY:
            return self._handle_summary_confirmation(user_input, state)
        elif state["stage"] == ConversationStage.DATABASE_SELECTION:
            return self._handle_database_selection(user_input, state)
        elif state["stage"] == ConversationStage.TRANSFORMATION_NAME:
            return self._handle_transformation_name(user_input, state)
        elif state["stage"] == ConversationStage.CONNECTION_DETAILS:
            return self._handle_connection_details(user_input, state)
        elif state["stage"] == ConversationStage.CONFIRMATION:
            return self._handle_final_confirmation(user_input, state)
        else:
            return {
                "stage": state["stage"],
                "message": "Setup is already complete. Would you like to create another transformation?",
                "requires_input": True,
                "data": state["data"]
            }
    
    def _handle_initial(self, user_input: str, state: Dict) -> Dict:
        """Handle initial stage - understand what user wants to accomplish."""
        # Check if LLM is available
        if not self.llm:
            return {
                "stage": ConversationStage.INITIAL.value,
                "message": "❌ Error: LLM API key is not configured. Please check your .env file and ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set.",
                "requires_input": True,
                "data": state["data"]
            }
        
        # Use LLM to understand user intent and generate summary
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful AI Data Engineer assistant. Your job is to understand what the user wants to build and suggest a clear summary.

Based on the user's input, create a summary that:
1. Clearly states what they want to accomplish
2. Suggests 2-3 specific hints/options they might want

Examples:
- User: "I want to create Sales Dashboard"
  Summary: "Create a Sales Dashboard?"
  Hints: ["Create a Sales Dashboard", "Create a Performance Dashboard"]

- User: "I need performance monitoring"
  Summary: "Create a Performance Dashboard?"
  Hints: ["Create a Performance Dashboard", "Create a Sales Dashboard"]

Return JSON with:
- summary: A clear summary statement ending with a question mark
- hints: List of 2-3 suggested transformation names (e.g., "Create a Sales Dashboard", "Create a Performance Dashboard")
- intent: What the user wants to accomplish (brief description)
"""),
            ("user", "User input: {user_input}\n\nUnderstand their intent and create a summary with hints.")
        ])
        
        chain = prompt | self.llm | json_parser
        
        try:
            result = chain.invoke({"user_input": user_input})
            
            state["data"]["intent"] = result.get("intent", user_input)
            state["data"]["summary"] = result.get("summary", "")
            state["data"]["suggested_hints"] = result.get("hints", [])
            state["stage"] = ConversationStage.SUMMARY
            
            hints_text = "\n".join([f"- {hint}" for hint in result.get("hints", [])])
            
            return {
                "stage": ConversationStage.SUMMARY.value,
                "message": f"{result.get('summary', '')}\n\nWould you like me to do that?\n\nSuggested options:\n{hints_text}",
                "hints": result.get("hints", []),
                "requires_input": True,
                "data": state["data"]
            }
        except Exception as e:
            self.log("error", "Failed to process initial input", error=str(e), exc_info=True)
            error_msg = str(e)
            if "API key" in error_msg or "authentication" in error_msg.lower():
                return {
                    "stage": ConversationStage.INITIAL.value,
                    "message": "❌ Error: LLM API key is not configured. Please check your .env file and ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set.",
                    "requires_input": True,
                    "data": state["data"]
                }
            return {
                "stage": ConversationStage.INITIAL.value,
                "message": f"I understand you want to create something. Could you tell me more about what you'd like to build?\n\n(Error: {error_msg})",
                "requires_input": True,
                "data": state["data"]
            }
    
    def _handle_summary_confirmation(self, user_input: str, state: Dict) -> Dict:
        """Handle summary confirmation - move to database selection."""
        # Check if user confirmed (yes, proceed, ok, etc.)
        confirmation_keywords = ["yes", "y", "proceed", "ok", "okay", "sure", "confirm", "correct"]
        user_lower = user_input.lower().strip()
        
        if any(keyword in user_lower for keyword in confirmation_keywords):
            # Get available databases/schemas with table details
            available_schemas = self._get_available_schemas()
            schema_details = self._get_schema_details(available_schemas)
            
            state["stage"] = ConversationStage.DATABASE_SELECTION
            state["available_schemas"] = available_schemas
            state["schema_details"] = schema_details
            
            # Build hints from schema details
            hints = []
            for schema, tables in schema_details.items():
                if tables:
                    hints.append(f"{schema} Database (has {len(tables)} tables: {', '.join(tables[:3])}{'...' if len(tables) > 3 else ''})")
                else:
                    hints.append(f"{schema} Database")
            
            hints_text = "\n".join([f"- {hint}" for hint in hints[:5]]) if hints else "- Sales Database\n- Customer Database"
            
            return {
                "stage": ConversationStage.DATABASE_SELECTION.value,
                "message": f"Great! Please confirm which database(s) I should connect to.\n\nAvailable databases:\n{hints_text}\n\nFor example: 'Sales and Customer Database' or 'Sales, Customer'",
                "requires_input": True,
                "data": state["data"],
                "available_schemas": available_schemas,
                "hints": hints
            }
        else:
            # User might have provided more details or wants to change
            return self._handle_initial(user_input, state)
    
    def _handle_database_selection(self, user_input: str, state: Dict) -> Dict:
        """Handle database selection - validate and move to transformation name."""
        # Extract database names from user input
        available_schemas = state.get("available_schemas", [])
        databases = self._extract_databases(user_input, available_schemas)
        
        # Validate: non-empty and plausible
        if not databases:
            schema_list = ", ".join(available_schemas[:5]) if available_schemas else "Sales, Customer, Orders"
            return {
                "stage": ConversationStage.DATABASE_SELECTION.value,
                "message": f"I couldn't identify the databases from your input. Please specify which database(s) to connect to.\n\nAvailable options: {schema_list}\n\nFor example: 'Sales and Customer Database' or 'Sales, Customer'",
                "requires_input": True,
                "data": state["data"]
            }
        
        # Echo back for confirmation
        databases_str = ", ".join(databases)
        state["data"]["databases"] = databases
        state["stage"] = ConversationStage.TRANSFORMATION_NAME
        
        # Generate transformation name suggestions using AI
        suggested_names = self._generate_transformation_name_suggestions_ai(
            state["data"].get("intent", ""),
            databases
        )
        if not suggested_names:
            suggested_names = state["data"].get("suggested_hints", [])
        if not suggested_names:
            suggested_names = self._generate_transformation_name_suggestions(state["data"].get("intent", ""))
        
        hints_text = "\n".join([f"- {name}" for name in suggested_names])
        
        return {
            "stage": ConversationStage.TRANSFORMATION_NAME.value,
            "message": f"Confirmed: I'll connect to {databases_str} Database(s).\n\nWhat transformation name should I use? I'll create a folder for it.\n\nSuggestions:\n{hints_text}",
            "hints": suggested_names,
            "requires_input": True,
            "data": state["data"]
        }
    
    def _handle_transformation_name(self, user_input: str, state: Dict) -> Dict:
        """Handle transformation name - validate and move to connection details."""
        transformation_name = user_input.strip()
        
        # Validate: non-empty and plausible (at least 3 characters, not just numbers)
        if not transformation_name or len(transformation_name) < 3:
            return {
                "stage": ConversationStage.TRANSFORMATION_NAME.value,
                "message": "Please provide a valid transformation name (at least 3 characters).",
                "requires_input": True,
                "data": state["data"]
            }
        
        if transformation_name.isdigit():
            return {
                "stage": ConversationStage.TRANSFORMATION_NAME.value,
                "message": "Please provide a meaningful transformation name (not just numbers).",
                "requires_input": True,
                "data": state["data"]
            }
        
        # Sanitize name (remove special characters, spaces -> underscores)
        sanitized_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in transformation_name)
        sanitized_name = sanitized_name.replace(' ', '_').upper()
        
        # Echo back for confirmation
        state["data"]["transformation_name"] = transformation_name
        state["data"]["transformation_name_sanitized"] = sanitized_name
        state["stage"] = ConversationStage.CONNECTION_DETAILS
        
        return {
            "stage": ConversationStage.CONNECTION_DETAILS.value,
            "message": f"Transformation name confirmed: {transformation_name} (folder: {sanitized_name})\n\nCan you share or confirm the connection details (host, user, credentials)? I'll store them securely.\n\nPlease provide:\n- Host\n- User\n- Database name\n- Port (optional, default: 5432 for PostgreSQL)\n\nOr say 'use existing' if you want to use configured credentials.",
            "requires_input": True,
            "data": state["data"]
        }
    
    def _handle_connection_details(self, user_input: str, state: Dict) -> Dict:
        """Handle connection details - validate and move to confirmation."""
        user_lower = user_input.lower().strip()
        
        if "use existing" in user_lower or "existing" in user_lower:
            # Use existing configuration
            state["data"]["use_existing_connection"] = True
            state["data"]["connection_details"] = {}
            connection_type = "existing configuration"
        else:
            # Try to extract connection details
            connection_details = self._extract_connection_details(user_input)
            
            # Validate: at least host must be provided
            if not connection_details.get("host"):
                return {
                    "stage": ConversationStage.CONNECTION_DETAILS.value,
                    "message": "I need at least a host address. Please provide connection details in format:\nHost: <host>\nUser: <user>\nDatabase: <database>\nPort: <port> (optional)\n\nOr say 'use existing' to use configured credentials.",
                    "requires_input": True,
                    "data": state["data"]
                }
            
            # Validate host format (basic check)
            host = connection_details.get("host", "")
            if len(host) < 3 or not any(c.isalnum() or c in ('.', '-', '_') for c in host):
                return {
                    "stage": ConversationStage.CONNECTION_DETAILS.value,
                    "message": "The host address doesn't look valid. Please provide a valid host (e.g., localhost, 192.168.1.1, db.example.com).",
                    "requires_input": True,
                    "data": state["data"]
                }
            
            state["data"]["connection_details"] = connection_details
            state["data"]["use_existing_connection"] = False
            connection_type = f"host: {connection_details.get('host')}"
        
        # Echo back for confirmation
        state["stage"] = ConversationStage.CONFIRMATION
        
        # Build summary
        databases = ", ".join(state["data"].get("databases", []))
        transformation_name = state["data"].get("transformation_name", "")
        connection_info = connection_type if "connection_type" in locals() else ("existing configuration" if state["data"].get("use_existing_connection") else f"host: {state['data']['connection_details'].get('host', 'N/A')}")
        
        return {
            "stage": ConversationStage.CONFIRMATION.value,
            "message": f"I'll connect to {databases}, create a folder named {transformation_name}, and use {connection_info}. Shall I proceed?",
            "requires_input": True,
            "data": state["data"]
        }
    
    def _handle_final_confirmation(self, user_input: str, state: Dict) -> Dict:
        """Handle final confirmation - save and complete."""
        confirmation_keywords = ["yes", "y", "proceed", "ok", "okay", "sure", "confirm", "go ahead", "create"]
        user_lower = user_input.lower().strip()
        
        if any(keyword in user_lower for keyword in confirmation_keywords):
            # Save to buildRetrieval database
            build_data = {
                "intent": state["data"].get("intent", ""),
                "databases": state["data"].get("databases", []),
                "transformation_name": state["data"].get("transformation_name", ""),
                "transformation_name_sanitized": state["data"].get("transformation_name_sanitized", ""),
                "connection_details": state["data"].get("connection_details", {}),
                "use_existing_connection": state["data"].get("use_existing_connection", False),
                "created_at": None  # Will be set when saving
            }
            
            state["stage"] = ConversationStage.COMPLETE
            state["data"]["build_id"] = "pending"  # Will be set after saving
            
            return {
                "stage": ConversationStage.COMPLETE.value,
                "message": f"Perfect! I'm creating your transformation '{state['data'].get('transformation_name', '')}' now. This will be saved to the buildRetrieval database.\n\nSetup complete! 🎉",
                "requires_input": False,
                "data": state["data"],
                "build_data": build_data  # For saving
            }
        else:
            return {
                "stage": ConversationStage.CONFIRMATION.value,
                "message": "Would you like to make any changes before proceeding? Or say 'yes' to confirm.",
                "requires_input": True,
                "data": state["data"]
            }
    
    def _get_available_schemas(self) -> List[str]:
        """Get list of available database schemas."""
        try:
            # Try to get schemas from warehouse
            if hasattr(warehouse, 'list_schemas'):
                schemas = warehouse.list_schemas()
                return schemas if schemas else ["public", "sales", "customer", "orders"]
            else:
                return ["public", "sales", "customer", "orders"]
        except Exception as e:
            self.log("warning", "Failed to get schemas from warehouse", error=str(e))
            return ["public", "sales", "customer", "orders"]
    
    def _get_schema_details(self, schemas: List[str]) -> Dict[str, List[str]]:
        """Get schema details including tables for hints."""
        schema_details = {}
        for schema in schemas[:10]:  # Limit to first 10 schemas
            try:
                tables = warehouse.list_tables(schema)
                schema_details[schema] = tables[:5]  # Limit to first 5 tables per schema
            except Exception as e:
                self.log("warning", f"Failed to get tables for schema {schema}", error=str(e))
                schema_details[schema] = []
        return schema_details
    
    def _generate_transformation_name_suggestions_ai(self, intent: str, databases: List[str]) -> List[str]:
        """Generate transformation name suggestions using AI based on intent and databases."""
        if not self.llm:
            return []
        
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a helpful AI assistant that generates transformation names based on user intent and database names.

Generate 3 transformation name suggestions in UPPERCASE with underscores (e.g., SALES_DASHBOARD, PERFORMANCE_MONITORING).

The names should be:
- Descriptive and clear
- Related to the intent and databases
- Professional and concise
- In UPPERCASE with underscores

Return JSON with:
- suggestions: List of 3 transformation name strings
"""),
                ("user", "Intent: {intent}\nDatabases: {databases}\n\nGenerate 3 transformation name suggestions.")
            ])
            
            chain = prompt | self.llm | json_parser
            result = chain.invoke({
                "intent": intent,
                "databases": ", ".join(databases)
            })
            
            suggestions = result.get("suggestions", [])
            return suggestions[:3] if suggestions else []
        except Exception as e:
            self.log("warning", "Failed to generate AI suggestions", error=str(e))
            return []
    
    def _extract_databases(self, user_input: str, available_schemas: List[str]) -> List[str]:
        """Extract database names from user input."""
        # Simple extraction - look for common patterns
        databases = []
        user_lower = user_input.lower()
        
        # Check against available schemas
        for schema in available_schemas:
            if schema.lower() in user_lower:
                databases.append(schema)
        
        # If no matches, try to extract from common patterns
        if not databases:
            # Look for "X and Y Database" or "X, Y, Z"
            import re
            # Pattern: "X and Y" or "X, Y"
            patterns = [
                r'(\w+)\s+and\s+(\w+)',
                r'(\w+),\s*(\w+)(?:,\s*(\w+))?'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, user_input, re.IGNORECASE)
                if matches:
                    for match in matches:
                        databases.extend([m for m in match if m])
                    break
        
        # If still nothing, return first word as database
        if not databases:
            words = user_input.split()
            databases = [words[0]] if words else []
        
        return list(set(databases))  # Remove duplicates
    
    def _generate_transformation_name_suggestions(self, intent: str) -> List[str]:
        """Generate transformation name suggestions based on intent."""
        # Simple keyword-based suggestions
        suggestions = []
        intent_lower = intent.lower()
        
        if "sales" in intent_lower:
            suggestions.extend(["SALES_DASHBOARD", "SALES_REPORT", "SALES_ANALYTICS"])
        if "performance" in intent_lower or "monitor" in intent_lower:
            suggestions.extend(["PERFORMANCE_MONITORING", "PERFORMANCE_REPORT", "PERFORMANCE_ANALYTICS"])
        if "customer" in intent_lower:
            suggestions.extend(["CUSTOMER_ANALYTICS", "CUSTOMER_REPORT", "CUSTOMER_DASHBOARD"])
        
        if not suggestions:
            suggestions = ["TRANSFORMATION_1", "DATA_PIPELINE", "ANALYTICS_REPORT"]
        
        return suggestions[:3]
    
    def _extract_connection_details(self, user_input: str) -> Dict:
        """Extract connection details from user input."""
        details = {}
        
        # Look for patterns like "Host: xyz" or "host=xyz"
        import re
        patterns = {
            "host": r'(?:host|server|address)[\s:=]+([^\s,]+)',
            "user": r'(?:user|username|userid)[\s:=]+([^\s,]+)',
            "database": r'(?:database|db|database name)[\s:=]+([^\s,]+)',
            "port": r'(?:port)[\s:=]+(\d+)',
            "password": r'(?:password|pwd|pass)[\s:=]+([^\s,]+)'
        }
        
        user_lower = user_input.lower()
        for key, pattern in patterns.items():
            match = re.search(pattern, user_lower, re.IGNORECASE)
            if match:
                details[key] = match.group(1)
        
        return details
    
    def execute(self, session_id: str, user_input: str) -> Dict:
        """Execute build summary conversation."""
        return self.start_conversation(session_id, user_input)
    
    def reset_session(self, session_id: str):
        """Reset a conversation session."""
        if session_id in self.conversation_state:
            del self.conversation_state[session_id]

