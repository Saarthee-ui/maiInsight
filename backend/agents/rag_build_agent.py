"""RAG Build Agent - Guides users through creating transformation flows using RAG documents, vectors, and LLM."""

from typing import Dict, List, Optional, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from agents.base_agent import BaseAgent
from storage.document_vector_store import DocumentVectorStore
from storage.build_vector_store import BuildVectorStore
import structlog
from enum import Enum

logger = structlog.get_logger()
json_parser = JsonOutputParser()


def invoke_with_timeout(chain, input_data, timeout=30):
    """Invoke a chain with timeout to prevent hanging."""
    import threading
    result_container = [None]
    exception_container = [None]
    
    def invoke_chain():
        try:
            result_container[0] = chain.invoke(input_data)
        except Exception as e:
            exception_container[0] = e
    
    thread = threading.Thread(target=invoke_chain)
    thread.daemon = True
    thread.start()
    thread.join(timeout)
    
    if thread.is_alive():
        raise TimeoutError(f"LLM call timed out after {timeout} seconds")
    
    if exception_container[0]:
        raise exception_container[0]
    
    return result_container[0]


def get_warehouse():
    """Lazy import of warehouse to avoid initialization issues."""
    try:
        from tools.warehouse import get_warehouse_instance
        warehouse = get_warehouse_instance()
        if warehouse and hasattr(warehouse, 'connected') and warehouse.connected:
            return warehouse
        return None
    except Exception as e:
        logger.warning("Failed to import warehouse", error=str(e))
        return None


class ConversationStage(str, Enum):
    """Stages of the build conversation - Smart Assistant Flow."""
    INITIAL_GREETING = "initial_greeting"  # Show initial greeting with options
    INTENT_CAPTURE = "intent_capture"  # Understand what user wants
    AUTO_DISCOVERY = "auto_discovery"  # Automatically discover and suggest everything
    QUICK_CONFIRMATION = "confirmation"  # Show everything, allow quick changes (use 'confirmation' for frontend compatibility)
    COMPLETE = "complete"  # Setup complete


class RAGBuildAgent(BaseAgent):
    """Agent that guides users through creating transformation flows using RAG documents, vectors, and LLM."""
    
    def __init__(self, **kwargs):
        """Initialize RAG build agent."""
        super().__init__(name="RAGBuildAgent", **kwargs)
        self.conversation_state = {}  # Store conversation state per session
        # Initialize vector stores for RAG
        self.document_store = DocumentVectorStore()
        self.build_store = BuildVectorStore()
        self.log("info", "RAGBuildAgent initialized with document and build vector stores")
    
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
                "stage": ConversationStage.INITIAL_GREETING,
                "data": {},
                "messages": []
            }
        
        state = self.conversation_state[session_id]
        
        # If it's the first message and stage is initial greeting, show greeting
        if state["stage"] == ConversationStage.INITIAL_GREETING and len(state["messages"]) == 0:
            # Show greeting for empty message or greeting keywords
            if not user_input or user_input.strip() == "":
                return self._handle_initial_greeting(state)
            # If user sends greeting, show options
            greeting_keywords = ["hi", "hello", "hey", "greetings", "start", "begin"]
            if any(keyword in user_input.lower().strip() for keyword in greeting_keywords):
                state["messages"].append({"role": "user", "content": user_input})
                return self._handle_initial_greeting(state)
        
        # Append user message if not empty
        if user_input:
            state["messages"].append({"role": "user", "content": user_input})
        
        # Process based on current stage
        if state["stage"] == ConversationStage.INITIAL_GREETING:
            return self._handle_option_selection(user_input, state)
        elif state["stage"] == ConversationStage.INTENT_CAPTURE:
            return self._handle_intent_capture(user_input, state)
        elif state["stage"] == ConversationStage.AUTO_DISCOVERY:
            return self._handle_auto_discovery(user_input, state)
        elif state["stage"] == ConversationStage.QUICK_CONFIRMATION:
            return self._handle_quick_confirmation(user_input, state)
        elif state["stage"] == ConversationStage.COMPLETE:
            return {
                "stage": ConversationStage.COMPLETE.value,
                "message": "Setup is already complete. Would you like to create another transformation?",
                "requires_input": True,
                "data": state["data"]
            }
        else:
            # Fallback: reset to intent capture
            state["stage"] = ConversationStage.INTENT_CAPTURE
            return self._handle_intent_capture(user_input, state)
    
    def _handle_initial_greeting(self, state: Dict) -> Dict:
        """Show initial greeting with options."""
        greeting_message = """Hi, How can I help you?

Please select one of the following options:

1. Do you want to build a Report?
2. Do you want to do the full refresh?
3. Do you want to make changes to existing Workflow?
4. Do you want to create report from existing Silver layer?
5. Do you want to build Gold layer on existing Silver Layer?
6. Do you want to do bulk migration of report?

Please reply with the option number (1-6) or the option text."""
        
        return {
            "stage": ConversationStage.INITIAL_GREETING.value,
            "message": greeting_message,
            "requires_input": True,
            "data": state["data"],
            "hints": [
                "1. Build a Report",
                "2. Full refresh",
                "3. Make changes to existing Workflow",
                "4. Create report from existing Silver layer",
                "5. Build Gold layer on existing Silver Layer",
                "6. Bulk migration of report"
            ]
        }
    
    def _handle_option_selection(self, user_input: str, state: Dict) -> Dict:
        """Handle user's selection from initial greeting options."""
        user_lower = user_input.lower().strip()
        
        # Handle greeting messages - show options again
        greeting_keywords = ["hi", "hello", "hey", "greetings", "start", "begin"]
        if any(keyword in user_lower for keyword in greeting_keywords) and len(user_lower.split()) <= 3:
            return self._handle_initial_greeting(state)
        
        # Map options to intents
        option_mapping = {
            "1": "build a report",
            "build a report": "build a report",
            "report": "build a report",
            "2": "full refresh",
            "full refresh": "full refresh",
            "refresh": "full refresh",
            "3": "make changes to existing workflow",
            "make changes to existing workflow": "make changes to existing workflow",
            "changes to workflow": "make changes to existing workflow",
            "workflow": "make changes to existing workflow",
            "4": "create report from existing silver layer",
            "create report from existing silver layer": "create report from existing silver layer",
            "silver layer report": "create report from existing silver layer",
            "silver": "create report from existing silver layer",
            "5": "build gold layer on existing silver layer",
            "build gold layer on existing silver layer": "build gold layer on existing silver layer",
            "gold layer": "build gold layer on existing silver layer",
            "gold": "build gold layer on existing silver layer",
            "6": "bulk migration of report",
            "bulk migration of report": "bulk migration of report",
            "bulk migration": "bulk migration of report",
            "migration": "bulk migration of report"
        }
        
        # Find matching option
        selected_intent = None
        for key, intent in option_mapping.items():
            if key in user_lower:
                selected_intent = intent
                break
        
        if selected_intent:
            # Store the selected option/intent
            state["data"]["selected_option"] = selected_intent
            state["data"]["intent"] = selected_intent
            state["stage"] = ConversationStage.INTENT_CAPTURE
            
            # Provide context-specific message based on selection
            context_messages = {
                "build a report": "Great! I'll help you build a report. Please tell me more about what kind of report you want to create.",
                "full refresh": "I'll help you with a full refresh. Please provide details about what needs to be refreshed.",
                "make changes to existing workflow": "I'll help you make changes to an existing workflow. Please tell me which workflow you want to modify.",
                "create report from existing silver layer": "I'll help you create a report from an existing Silver layer. Please provide details about the Silver layer and the report you want to create.",
                "build gold layer on existing silver layer": "I'll help you build a Gold layer on an existing Silver layer. Please provide details about the Silver layer and the Gold layer requirements.",
                "bulk migration of report": "I'll help you with bulk migration of reports. Please provide details about the reports you want to migrate."
            }
            
            message = context_messages.get(selected_intent, f"I understand you want to {selected_intent}. Please provide more details.")
            
            return {
                "stage": ConversationStage.INTENT_CAPTURE.value,
                "message": message,
                "requires_input": True,
                "data": state["data"]
            }
        else:
            # Invalid selection, show options again
            return {
                "stage": ConversationStage.INITIAL_GREETING.value,
                "message": "I didn't understand your selection. Please choose one of the following options:\n\n1. Do you want to build a Report?\n2. Do you want to do the full refresh?\n3. Do you want to make changes to existing Workflow?\n4. Do you want to create report from existing Silver layer?\n5. Do you want to build Gold layer on existing Silver Layer?\n6. Do you want to do bulk migration of report?\n\nPlease reply with the option number (1-6) or the option text.",
                "requires_input": True,
                "data": state["data"],
                "hints": [
                    "1. Build a Report",
                    "2. Full refresh",
                    "3. Make changes to existing Workflow",
                    "4. Create report from existing Silver layer",
                    "5. Build Gold layer on existing Silver Layer",
                    "6. Bulk migration of report"
                ]
            }
    
    def _retrieve_rag_context(self, query: str, categories: Optional[List[str]] = None) -> str:
        """Retrieve relevant RAG documents and similar builds for context."""
        context_parts = []
        
        # Retrieve relevant RAG documents
        if self.document_store and self.document_store.is_available():
            if categories:
                for category in categories:
                    docs = self.document_store.search_documents(query, k=3, category=category)
                    if docs:
                        context_parts.append(f"\n--- Relevant {category.upper()} Documentation ---")
                        for i, doc in enumerate(docs, 1):
                            context_parts.append(f"\n[{i}] {doc['metadata'].get('file_name', 'Document')} (Score: {doc['similarity_score']:.2f})")
                            context_parts.append(f"{doc['content'][:500]}...")  # First 500 chars
            else:
                docs = self.document_store.search_documents(query, k=5)
                if docs:
                    context_parts.append("\n--- Relevant Documentation ---")
                    for i, doc in enumerate(docs, 1):
                        context_parts.append(f"\n[{i}] {doc['metadata'].get('file_name', 'Document')} ({doc['metadata'].get('category', 'general')})")
                        context_parts.append(f"{doc['content'][:400]}...")
        
        # Retrieve similar past builds
        if self.build_store and self.build_store.is_available():
            similar_builds = self.build_store.search_similar_builds(query, top_k=3)
            if similar_builds:
                context_parts.append("\n--- Similar Past Builds ---")
                for i, build in enumerate(similar_builds, 1):
                    context_parts.append(f"\n[{i}] {build.get('transformation_name', 'Unnamed')} (Score: {build.get('similarity_score', 0):.2f})")
                    context_parts.append(f"Intent: {build.get('intent', 'N/A')}")
                    context_parts.append(f"Databases: {', '.join(build.get('databases', []))}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _handle_intent_capture(self, user_input: str, state: Dict) -> Dict:
        """Handle intent capture - understand what user wants and move to auto-discovery with RAG context."""
        # Check if LLM is available
        if not self.llm:
            return {
                "stage": ConversationStage.INTENT_CAPTURE.value,
                "message": "❌ Error: LLM API key is not configured. Please check your .env file and ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set.",
                "requires_input": True,
                "data": state["data"]
            }
        
        # Retrieve RAG context
        rag_context = self._retrieve_rag_context(user_input, categories=["documentation", "examples", "rules"])
        
        # Use LLM to understand user intent with RAG context
        system_prompt = """You are a helpful AI Data Engineer assistant. Your job is to understand what the user wants to build.

Extract from the user's input:
1. What they want to accomplish (intent)
2. Any mentioned databases or data sources
3. Any mentioned tables or data entities
4. The type of transformation (dashboard, report, pipeline, etc.)

Use the provided documentation and similar past builds as context to better understand the user's intent and suggest appropriate transformations.

Return JSON with:
- intent: What the user wants to accomplish (brief description)
- mentioned_databases: List of database names mentioned (if any)
- mentioned_tables: List of table names mentioned (if any)
- transformation_type: Type of transformation (dashboard, report, pipeline, analytics, etc.)
- keywords: List of key words that might help match to databases/tables
"""
        
        if rag_context:
            system_prompt += f"\n\nRelevant Context:{rag_context}"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "User input: {user_input}\n\nExtract the intent and any mentioned databases/tables.")
        ])
        
        chain = prompt | self.llm | json_parser
        
        try:
            result = invoke_with_timeout(chain, {"user_input": user_input}, timeout=30)
            
            state["data"]["intent"] = result.get("intent", user_input)
            state["data"]["mentioned_databases"] = result.get("mentioned_databases", [])
            state["data"]["mentioned_tables"] = result.get("mentioned_tables", [])
            state["data"]["transformation_type"] = result.get("transformation_type", "transformation")
            state["data"]["keywords"] = result.get("keywords", [])
            
            # Immediately perform auto-discovery
            state["stage"] = ConversationStage.AUTO_DISCOVERY
            discovery_result = self._perform_auto_discovery(state)
            
            # Prepend a friendly message
            discovery_result["message"] = f"I'll create a {result.get('transformation_type', 'transformation')} for you. Let me gather what I need...\n\n" + discovery_result["message"]
            
            return discovery_result
        except Exception as e:
            self.log("error", "Failed to process intent", error=str(e), exc_info=True)
            error_msg = str(e)
            if "API key" in error_msg or "authentication" in error_msg.lower():
                return {
                    "stage": ConversationStage.INTENT_CAPTURE.value,
                    "message": "❌ Error: LLM API key is not configured. Please check your .env file and ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set.",
                    "requires_input": True,
                    "data": state["data"]
                }
            return {
                "stage": ConversationStage.INTENT_CAPTURE.value,
                "message": f"I understand you want to create something. Could you tell me more about what you'd like to build?\n\n(Error: {error_msg})",
                "requires_input": True,
                "data": state["data"]
            }
    
    def _handle_auto_discovery(self, user_input: str, state: Dict) -> Dict:
        """Handle auto-discovery - if not done yet, do it; otherwise move to confirmation."""
        # If auto-discovery hasn't been done, do it now
        if "databases" not in state["data"]:
            return self._perform_auto_discovery(state)
        
        # Auto-discovery already done, move to quick confirmation
        # If user input is empty or just whitespace, show confirmation again
        if not user_input or not user_input.strip():
            state["stage"] = ConversationStage.QUICK_CONFIRMATION
            return self._build_quick_confirmation_message(state)
        
        state["stage"] = ConversationStage.QUICK_CONFIRMATION
        return self._handle_quick_confirmation(user_input, state)
    
    def _perform_auto_discovery(self, state: Dict) -> Dict:
        """Perform automatic discovery of databases, tables, name, and connection."""
        intent = state["data"].get("intent", "")
        keywords = state["data"].get("keywords", [])
        mentioned_databases = state["data"].get("mentioned_databases", [])
        
        # Get all available schemas
        available_schemas = self._get_available_schemas()
        schema_details = self._get_schema_details(available_schemas)
        
        # Smart database matching using LLM
        selected_databases = self._smart_match_databases(
            intent, keywords, mentioned_databases, available_schemas, schema_details
        )
        
        # If no match found, use first available or mentioned
        if not selected_databases:
            if mentioned_databases:
                # Try to match mentioned databases
                for mentioned in mentioned_databases:
                    for schema in available_schemas:
                        if mentioned.lower() in schema.lower() or schema.lower() in mentioned.lower():
                            selected_databases.append(schema)
                            break
            if not selected_databases and available_schemas:
                selected_databases = [available_schemas[0]]  # Use first available
        
        # Get tables for selected databases
        selected_tables = []
        for db in selected_databases:
            tables = schema_details.get(db, [])
            # Smart table selection based on intent
            relevant_tables = self._smart_select_tables(intent, keywords, tables)
            if not relevant_tables and tables:
                relevant_tables = tables[:3]  # Default to first 3 tables
            # Store as tuples (database, table) for easy grouping
            for table in relevant_tables:
                selected_tables.append((db, table))
        
        # Generate transformation name
        transformation_name = self._generate_transformation_name_auto(intent, selected_databases)
        sanitized_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in transformation_name)
        sanitized_name = sanitized_name.replace(' ', '_').upper()
        
        # Check connection - default to existing
        use_existing_connection = True
        connection_details = {}
        
        # Store discovered data
        state["data"]["databases"] = selected_databases
        state["data"]["tables"] = selected_tables
        state["data"]["transformation_name"] = transformation_name
        state["data"]["transformation_name_sanitized"] = sanitized_name
        state["data"]["use_existing_connection"] = use_existing_connection
        state["data"]["connection_details"] = connection_details
        state["available_schemas"] = available_schemas
        state["schema_details"] = schema_details
        
        # Move to quick confirmation
        state["stage"] = ConversationStage.QUICK_CONFIRMATION
        
        return self._build_quick_confirmation_message(state)
    
    def _smart_match_databases(self, intent: str, keywords: List[str], mentioned: List[str], 
                              available_schemas: List[str], schema_details: Dict[str, List[str]]) -> List[str]:
        """Use LLM to intelligently match intent to databases with RAG context."""
        if not available_schemas:
            return []
        
        # If LLM not available, use simple keyword matching
        if not self.llm:
            # Try to match based on keywords and mentioned databases
            matched = []
            intent_lower = intent.lower()
            keywords_lower = [k.lower() for k in keywords] if keywords else []
            
            for schema in available_schemas:
                schema_lower = schema.lower()
                # Check if schema name matches keywords or intent
                if any(keyword in schema_lower for keyword in keywords_lower if keyword):
                    matched.append(schema)
                elif any(word in schema_lower for word in intent_lower.split() if len(word) > 3):
                    matched.append(schema)
                # Check mentioned databases
                for mentioned_db in mentioned:
                    if mentioned_db.lower() in schema_lower or schema_lower in mentioned_db.lower():
                        matched.append(schema)
            
            return list(set(matched))[:3]  # Remove duplicates and limit
        
        try:
            # Retrieve RAG context for database matching
            search_query = f"{intent} {' '.join(keywords)} {' '.join(mentioned)}"
            rag_context = self._retrieve_rag_context(search_query, categories=["schemas", "documentation"])
            
            # Build context about available schemas
            schema_info = []
            for schema in available_schemas[:10]:
                tables = schema_details.get(schema, [])
                schema_info.append(f"{schema} (has {len(tables)} tables: {', '.join(tables[:3])})")
            
            system_prompt = """You are a helpful AI assistant that matches user intent to database schemas.
Use the provided documentation to understand database structures and naming conventions.

Given the user's intent and available schemas, select the most relevant database(s).

Return JSON with:
- selected_databases: List of schema names that match the intent (1-3 schemas)
- reasoning: Brief explanation of why these schemas were selected
"""
            
            if rag_context:
                system_prompt += f"\n\nRelevant Documentation:{rag_context}"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", """User Intent: {intent}
Keywords: {keywords}
Mentioned Databases: {mentioned}
Available Schemas: {schemas}

Select the most relevant database(s) for this intent.""")
            ])
            
            chain = prompt | self.llm | json_parser
            result = invoke_with_timeout(chain, {
                "intent": intent,
                "keywords": ", ".join(keywords) if keywords else "none",
                "mentioned": ", ".join(mentioned) if mentioned else "none",
                "schemas": "\n".join(schema_info)
            }, timeout=30)
            
            selected = result.get("selected_databases", [])
            # Validate that selected schemas exist
            valid_schemas = [s for s in selected if s in available_schemas]
            return valid_schemas[:3]  # Limit to 3 databases
        except Exception as e:
            self.log("warning", "Failed to smart match databases", error=str(e))
            return []
    
    def _smart_select_tables(self, intent: str, keywords: List[str], tables: List[str]) -> List[str]:
        """Select relevant tables based on intent and keywords."""
        if not tables:
            return []
        
        # Simple keyword matching
        intent_lower = intent.lower()
        keywords_lower = [k.lower() for k in keywords]
        
        relevant = []
        for table in tables:
            table_lower = table.lower()
            # Check if table name matches keywords or intent
            if any(keyword in table_lower for keyword in keywords_lower if keyword):
                relevant.append(table)
            elif any(word in table_lower for word in intent_lower.split() if len(word) > 3):
                relevant.append(table)
        
        # If no matches, return first few tables
        return relevant[:5] if relevant else tables[:3]
    
    def _generate_transformation_name_auto(self, intent: str, databases: List[str]) -> str:
        """Automatically generate transformation name."""
        # Try AI first
        if self.llm and databases:
            suggestions = self._generate_transformation_name_suggestions_ai(intent, databases)
            if suggestions:
                return suggestions[0]  # Use first suggestion
        
        # Fallback to keyword-based
        suggestions = self._generate_transformation_name_suggestions(intent)
        if suggestions:
            return suggestions[0]
        
        # Last resort
        return "TRANSFORMATION"
    
    def _build_quick_confirmation_message(self, state: Dict) -> Dict:
        """Build the quick confirmation message showing everything with RAG context."""
        databases = state["data"].get("databases", [])
        tables = state["data"].get("tables", [])
        transformation_name = state["data"].get("transformation_name", "")
        intent = state["data"].get("intent", "")
        use_existing = state["data"].get("use_existing_connection", True)
        
        # Build message
        message_parts = []
        message_parts.append(f"I found {len(databases)} database(s): {', '.join(databases)}")
        
        if tables:
            # Group tables by database
            tables_by_db = {}
            for db, table in tables:
                if db not in tables_by_db:
                    tables_by_db[db] = []
                tables_by_db[db].append(table)
            
            table_info = []
            for db, table_list in tables_by_db.items():
                table_info.append(f"{db}: {', '.join(table_list[:5])}{'...' if len(table_list) > 5 else ''}")
            
            if table_info:
                message_parts.append(f"I'll use these tables:\n" + "\n".join(f"  - {info}" for info in table_info))
        
        message_parts.append(f"Name: {transformation_name}")
        message_parts.append(f"Connection: {'Using existing connection' if use_existing else 'New connection'}")
        
        # Add RAG context suggestions
        if intent:
            search_query = f"{intent} {transformation_name} {' '.join(databases)}"
            rag_docs = self.document_store.search_documents(search_query, k=2, category="examples") if self.document_store and self.document_store.is_available() else []
            similar_builds = self.build_store.search_similar_builds(search_query, top_k=2) if self.build_store and self.build_store.is_available() else []
            
            if rag_docs or similar_builds:
                message_parts.append("\n💡 Suggestions based on similar builds and documentation:")
                if similar_builds:
                    for build in similar_builds[:2]:
                        message_parts.append(f"  - Similar build: {build.get('transformation_name', 'Unnamed')} (Intent: {build.get('intent', 'N/A')[:50]}...)")
                if rag_docs:
                    for doc in rag_docs[:1]:
                        message_parts.append(f"  - See: {doc['metadata'].get('file_name', 'Document')} for examples")
        
        message_parts.append("\nSound good? (Say 'yes' to proceed, or tell me what to change)")
        
        return {
            "stage": ConversationStage.QUICK_CONFIRMATION.value,  # This will be "confirmation"
            "message": "\n".join(message_parts),
            "requires_input": True,
            "data": state["data"],
            "hints": []  # Add hints field for frontend compatibility
        }
    
    def _handle_quick_confirmation(self, user_input: str, state: Dict) -> Dict:
        """Handle quick confirmation - allow changes or proceed."""
        user_lower = user_input.lower().strip()
        
        # Check for confirmation
        confirmation_keywords = ["yes", "y", "proceed", "ok", "okay", "sure", "confirm", "go ahead", "create", "sounds good"]
        if any(keyword in user_lower for keyword in confirmation_keywords):
            # Save and complete
            build_data = {
                "intent": state["data"].get("intent", ""),
                "databases": state["data"].get("databases", []),
                "transformation_name": state["data"].get("transformation_name", ""),
                "transformation_name_sanitized": state["data"].get("transformation_name_sanitized", ""),
                "connection_details": state["data"].get("connection_details", {}),
                "use_existing_connection": state["data"].get("use_existing_connection", False),
                "created_at": None
            }
            
            state["stage"] = ConversationStage.COMPLETE
            state["data"]["build_id"] = "pending"
            
            return {
                "stage": ConversationStage.COMPLETE.value,
                "message": f"Perfect! I'm creating your transformation '{state['data'].get('transformation_name', '')}' now. This will be saved to the buildRetrieval database.\n\nSetup complete! 🎉",
                "requires_input": False,
                "data": state["data"],
                "build_data": build_data
            }
        
        # Check for changes
        changes = self._parse_quick_changes(user_input, state)
        if changes:
            # Apply changes
            self._apply_quick_changes(changes, state)
            # Show updated confirmation
            result = self._build_quick_confirmation_message(state)
            result["message"] = "Updated! " + result["message"]
            return result
        
        # If no clear action, ask for clarification
        return {
            "stage": ConversationStage.QUICK_CONFIRMATION.value,
            "message": "I didn't understand. You can:\n- Say 'yes' to proceed\n- Say 'change name to X' to change the name\n- Say 'use database X' to change databases\n- Say 'add table X' to add tables",
            "requires_input": True,
            "data": state["data"],
            "hints": []
        }
    
    def _parse_quick_changes(self, user_input: str, state: Dict) -> Dict:
        """Parse user input for quick changes."""
        changes = {}
        user_lower = user_input.lower()
        
        # Change name
        if "change name" in user_lower or "name to" in user_lower:
            import re
            match = re.search(r'(?:name to|name is|call it)\s+([^\.,!?]+)', user_input, re.IGNORECASE)
            if match:
                changes["name"] = match.group(1).strip()
        
        # Change database
        if "use database" in user_lower or "database" in user_lower:
            available_schemas = state.get("available_schemas", [])
            for schema in available_schemas:
                if schema.lower() in user_lower:
                    changes["databases"] = [schema]
                    break
        
        # Add table
        if "add table" in user_lower or "include table" in user_lower:
            import re
            match = re.search(r'(?:table|table:)\s+([^\.,!?]+)', user_input, re.IGNORECASE)
            if match:
                changes["add_table"] = match.group(1).strip()
        
        return changes
    
    def _apply_quick_changes(self, changes: Dict, state: Dict):
        """Apply quick changes to state."""
        if "name" in changes:
            new_name = changes["name"]
            state["data"]["transformation_name"] = new_name
            sanitized = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in new_name)
            state["data"]["transformation_name_sanitized"] = sanitized.replace(' ', '_').upper()
        
        if "databases" in changes:
            state["data"]["databases"] = changes["databases"]
            # Re-select tables for new databases
            schema_details = state.get("schema_details", {})
            new_tables = []
            for db in changes["databases"]:
                tables = schema_details.get(db, [])
                new_tables.extend([(db, table) for table in tables[:3]])
            state["data"]["tables"] = new_tables
        
        if "add_table" in changes:
            table_name = changes["add_table"]
            current_tables = state["data"].get("tables", [])
            # Find which database this table belongs to
            schema_details = state.get("schema_details", {})
            for db, tables in schema_details.items():
                if table_name.lower() in [t.lower() for t in tables]:
                    current_tables.append((db, table_name))
                    break
            state["data"]["tables"] = current_tables
    
    def _get_available_schemas(self) -> List[str]:
        """Get list of available database schemas."""
        try:
            warehouse = get_warehouse()
            if warehouse and hasattr(warehouse, 'list_schemas') and hasattr(warehouse, 'connected') and warehouse.connected:
                # Use timeout wrapper for warehouse query
                import threading
                result_container = [None]
                exception_container = [None]
                
                def query_schemas():
                    try:
                        result_container[0] = warehouse.list_schemas()
                    except Exception as e:
                        exception_container[0] = e
                
                thread = threading.Thread(target=query_schemas)
                thread.daemon = True
                thread.start()
                thread.join(5)  # 5 second timeout
                
                if thread.is_alive():
                    self.log("warning", "Warehouse list_schemas timed out, using defaults")
                    return ["public", "sales", "customer", "orders"]
                
                if exception_container[0]:
                    raise exception_container[0]
                
                schemas = result_container[0]
                return schemas if schemas else ["public", "sales", "customer", "orders"]
            else:
                return ["public", "sales", "customer", "orders"]
        except Exception as e:
            self.log("warning", "Failed to get schemas from warehouse", error=str(e))
            return ["public", "sales", "customer", "orders"]
    
    def _get_schema_details(self, schemas: List[str]) -> Dict[str, List[str]]:
        """Get schema details including tables for hints."""
        schema_details = {}
        warehouse = get_warehouse()
        if not warehouse or not (hasattr(warehouse, 'connected') and warehouse.connected):
            return {schema: [] for schema in schemas[:10]}
        
        for schema in schemas[:10]:  # Limit to first 10 schemas
            try:
                # Use timeout wrapper for warehouse query
                import threading
                result_container = [None]
                exception_container = [None]
                
                def query_tables():
                    try:
                        result_container[0] = warehouse.list_tables(schema)
                    except Exception as e:
                        exception_container[0] = e
                
                thread = threading.Thread(target=query_tables)
                thread.daemon = True
                thread.start()
                thread.join(3)  # 3 second timeout per schema
                
                if thread.is_alive():
                    self.log("warning", f"list_tables timed out for schema {schema}")
                    schema_details[schema] = []
                    continue
                
                if exception_container[0]:
                    raise exception_container[0]
                
                tables = result_container[0]
                schema_details[schema] = tables[:5] if tables else []  # Limit to first 5 tables per schema
            except Exception as e:
                self.log("warning", f"Failed to get tables for schema {schema}", error=str(e))
                schema_details[schema] = []
        return schema_details
    
    def _generate_transformation_name_suggestions_ai(self, intent: str, databases: List[str]) -> List[str]:
        """Generate transformation name suggestions using AI with RAG context."""
        if not self.llm:
            return []
        
        try:
            # Retrieve RAG context for naming conventions
            search_query = f"naming conventions transformation {intent}"
            rag_context = self._retrieve_rag_context(search_query, categories=["rules", "documentation"])
            
            system_prompt = """You are a helpful AI assistant that generates transformation names based on user intent and database names.

Generate 3 transformation name suggestions in UPPERCASE with underscores (e.g., SALES_DASHBOARD, PERFORMANCE_MONITORING).

The names should be:
- Descriptive and clear
- Related to the intent and databases
- Professional and concise
- In UPPERCASE with underscores

Return JSON with:
- suggestions: List of 3 transformation name strings
"""
            
            if rag_context:
                system_prompt += f"\n\nNaming Guidelines:{rag_context}"
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", "Intent: {intent}\nDatabases: {databases}\n\nGenerate 3 transformation name suggestions.")
            ])
            
            chain = prompt | self.llm | json_parser
            result = invoke_with_timeout(chain, {
                "intent": intent,
                "databases": ", ".join(databases)
            }, timeout=30)
            
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
        self.log("info", "Session reset", session_id=session_id)

