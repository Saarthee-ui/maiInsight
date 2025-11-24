"""Flask web application for Build Summary Agent."""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from agents.rag_build_agent import RAGBuildAgent
from storage.build_retrieval_storage import BuildRetrievalStorage
from flasgger import Swagger
import structlog
import uuid

logger = structlog.get_logger()

app = Flask(__name__, template_folder='../frontend/templates')
CORS(app)  # Enable CORS for frontend
swagger = Swagger(app)

# Global state
build_summary_agent = None  # Keeping name for backward compatibility
build_storage = None

# Initialize RAG build agent - CRITICAL: Must succeed for app to work
print("\n" + "="*60)
print("Initializing RAGBuildAgent...")
print("="*60)

try:
    from config import settings
    # Debug: Check if API key is set (without exposing the key)
    api_key_set = bool(settings.openai_api_key or settings.anthropic_api_key)
    logger.info("API key check", 
                llm_provider=settings.llm_provider,
                api_key_configured=api_key_set,
                openai_set=bool(settings.openai_api_key),
                anthropic_set=bool(settings.anthropic_api_key))
    
    print(f"LLM Provider: {settings.llm_provider}")
    print(f"API Key Configured: {api_key_set}")
    
    build_summary_agent = RAGBuildAgent(allow_no_llm=True)
    
    if build_summary_agent is None:
        raise RuntimeError("RAGBuildAgent() returned None")
    
    if build_summary_agent.llm:
        logger.info("RAGBuildAgent initialized successfully with LLM")
        print("[OK] Agent initialized with LLM")
    else:
        logger.warning("RAGBuildAgent initialized without LLM - API key not configured or invalid")
        print("[WARNING] Agent initialized without LLM")
        print("   Agent will work but will show errors when LLM is needed")
        
except Exception as e:
    logger.error("CRITICAL: RAGBuildAgent failed to initialize", error=str(e), exc_info=True)
    print(f"[ERROR] Agent initialization failed: {e}")
    print("Attempting fallback initialization...")
    
    # Fallback attempt
    try:
        build_summary_agent = RAGBuildAgent(allow_no_llm=True)
        if build_summary_agent:
            print("[OK] Agent initialized on fallback attempt")
            logger.info("Agent initialized on fallback attempt")
        else:
            raise RuntimeError("Fallback initialization returned None")
    except Exception as e2:
        logger.error("CRITICAL: Fallback initialization also failed", error=str(e2), exc_info=True)
        print(f"[ERROR] Fallback also failed: {e2}")
        build_summary_agent = None

# Final verification
print("="*60)
if build_summary_agent is None:
    print("[CRITICAL ERROR] RAGBuildAgent is None!")
    print("The application will not work properly.")
    print("Check the error messages above for details.")
    logger.error("CRITICAL: RAGBuildAgent is None - application will not work!")
else:
    print("[SUCCESS] RAGBuildAgent is ready!")
    print(f"   - Agent Name: {build_summary_agent.name}")
    print(f"   - Has LLM: {build_summary_agent.llm is not None}")
    # Check vector stores
    doc_store_available = build_summary_agent.document_store.is_available() if hasattr(build_summary_agent, 'document_store') else False
    build_store_available = build_summary_agent.build_store.is_available() if hasattr(build_summary_agent, 'build_store') else False
    print(f"   - Document Vector Store: {'✅ Available' if doc_store_available else '❌ Not Available'}")
    print(f"   - Build Vector Store: {'✅ Available' if build_store_available else '❌ Not Available'}")
    logger.info("RAGBuildAgent is ready", 
                name=build_summary_agent.name,
                has_llm=build_summary_agent.llm is not None,
                doc_store_available=doc_store_available,
                build_store_available=build_store_available)
print("="*60 + "\n")

# Initialize storage
try:
    build_storage = BuildRetrievalStorage()
    logger.info("BuildRetrievalStorage initialized successfully")
except Exception as e:
    logger.error("BuildRetrievalStorage failed to initialize", error=str(e), exc_info=True)
    build_storage = None


@app.route("/")
def index():
    """Serve the main chat interface."""
    return render_template("chatbot.html")


@app.route("/api/", methods=["GET"])
def api_info():
    """API information endpoint."""
    return jsonify({
        "status": "ok",
        "message": "Mailytics API",
        "version": "1.0",
        "endpoints": {
            "health": "/api/health",
            "test": "/api/test",
            "build_chat": "/api/build/chat (POST)",
            "list_builds": "/api/build/list (GET)",
            "get_build": "/api/build/<id> (GET)",
            "reset_build": "/api/build/reset (POST)",
            "build_status": "/api/build/status (GET)"
        },
        "frontend": "http://localhost:5000/",
        "docs": "http://localhost:5000/api/docs/"
    })


@app.route("/api/docs/", methods=["GET"])
@app.route("/api/docs", methods=["GET"])
def api_docs():
    """API documentation endpoint."""
    return jsonify({
        "title": "Mailytics API Documentation",
        "version": "1.0",
        "base_url": "http://localhost:5000/api",
        "description": "API for Mailytics - Data transformation and build management",
        "endpoints": [
            {
                "path": "/api/health",
                "method": "GET",
                "description": "Health check endpoint to verify server and agent status",
                "parameters": None,
                "response": {
                    "status": "ok",
                    "agent_available": "boolean",
                    "agent_has_llm": "boolean",
                    "storage_available": "boolean",
                    "agent_name": "string"
                }
            },
            {
                "path": "/api/test",
                "method": "GET",
                "description": "Simple test endpoint to verify server is running",
                "parameters": None,
                "response": {
                    "status": "ok",
                    "message": "string",
                    "agent_status": "string"
                }
            },
            {
                "path": "/api/build/chat",
                "method": "POST",
                "description": "Handle build chatbot conversation",
                "parameters": {
                    "message": "string (required) - User's message",
                    "session_id": "string (optional) - Session identifier"
                },
                "request_body": {
                    "message": "string",
                    "session_id": "string (optional)"
                },
                "response": {
                    "success": "boolean",
                    "session_id": "string",
                    "message": "string",
                    "stage": "string",
                    "hints": "array",
                    "requires_input": "boolean",
                    "data": "object",
                    "build_id": "integer (optional)"
                }
            },
            {
                "path": "/api/build/list",
                "method": "GET",
                "description": "List all saved builds",
                "parameters": {
                    "limit": "integer (optional, default: 50) - Maximum number of builds to return"
                },
                "response": {
                    "success": "boolean",
                    "builds": "array"
                }
            },
            {
                "path": "/api/build/<build_id>",
                "method": "GET",
                "description": "Get a specific build by ID",
                "parameters": {
                    "build_id": "integer (path parameter) - Build ID"
                },
                "response": {
                    "success": "boolean",
                    "build": "object"
                }
            },
            {
                "path": "/api/build/reset",
                "method": "POST",
                "description": "Reset build chat session",
                "parameters": {
                    "session_id": "string (required) - Session ID to reset"
                },
                "request_body": {
                    "session_id": "string"
                },
                "response": {
                    "success": "boolean",
                    "message": "string"
                }
            },
            {
                "path": "/api/build/status",
                "method": "GET",
                "description": "Check build agent status and configuration",
                "parameters": None,
                "response": {
                    "success": "boolean",
                    "status": {
                        "agent_initialized": "boolean",
                        "storage_initialized": "boolean",
                        "llm_configured": "boolean",
                        "warehouse_configured": "boolean",
                        "errors": "array"
                    }
                }
            }
        ],
        "examples": {
            "health_check": "GET http://localhost:5000/api/health",
            "send_message": {
                "url": "POST http://localhost:5000/api/build/chat",
                "body": {
                    "message": "I want to create a sales dashboard",
                    "session_id": "optional-session-id"
                }
            },
            "list_builds": "GET http://localhost:5000/api/build/list?limit=10"
        }
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "agent_available": build_summary_agent is not None,
        "agent_has_llm": build_summary_agent.llm is not None if build_summary_agent else False,
        "storage_available": build_storage is not None,
        "agent_name": build_summary_agent.name if build_summary_agent else None,
        "message": "Server is running" if build_summary_agent else "Agent not initialized"
    })


@app.route("/api/test", methods=["GET"])
def test_endpoint():
    """Simple test endpoint to verify server is running."""
    return jsonify({
        "status": "ok",
        "message": "Server is running and responding",
        "agent_status": "available" if build_summary_agent else "not available"
    })


@app.route("/api/build/chat", methods=["POST"])
def build_chat():
    """Handle build chatbot conversation."""
    try:
        data = request.json
        user_input = data.get("message", "").strip()
        session_id = data.get("session_id")
        
        # Allow empty message for initial greeting
        if not user_input:
            user_input = ""  # Allow empty string for initial greeting
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not build_summary_agent:
            logger.error("CRITICAL: Build chat called but agent is None!")
            logger.error("This means the agent failed to initialize at startup")
            return jsonify({
                "error": "Build summary agent not available",
                "success": False,
                "message": "Error: Build summary agent is not initialized. Please check server startup logs and restart the server."
            }), 503
        
        # Process conversation
        try:
            result = build_summary_agent.start_conversation(session_id, user_input)
        except Exception as e:
            logger.error("Build conversation failed", error=str(e), exc_info=True)
            return jsonify({
                "success": False,
                "error": f"Failed to process conversation: {str(e)}",
                "message": f"❌ Error: {str(e)}"
            }), 500
        
        # If conversation is complete, save to database
        build_id = None
        if result.get("stage") == "complete" and "build_data" in result:
            try:
                if build_storage:
                    # Save to build_retrievals table
                    build_id = build_storage.save_build(result["build_data"])
                    result["build_id"] = build_id
                    
                    # Save to buildCaptureTable when user confirms (satisfied button)
                    user_id = data.get("user_id")  # Get from frontend request
                    organization_name = data.get("organization_name")  # Get from frontend request
                    lock_status = data.get("lock_status", "unlocked")  # Default to unlocked
                    
                    try:
                        capture_id = build_storage.save_to_build_capture_table(
                            session_id=session_id,
                            build_data=result["build_data"],
                            user_id=user_id,
                            organization_name=organization_name,
                            lock_status=lock_status
                        )
                        logger.info("Build saved to buildCaptureTable", capture_id=capture_id, session_id=session_id)
                    except Exception as e:
                        logger.error("Failed to save to buildCaptureTable", error=str(e), exc_info=True)
                        # Don't fail the whole request if buildCaptureTable save fails
                else:
                    logger.warning("Build storage not available, cannot save build")
                    result["message"] += "\n\n(Note: Setup completed but failed to save to database - storage not available)"
            except Exception as e:
                logger.error("Failed to save build", error=str(e), exc_info=True)
                result["message"] += f"\n\n(Note: Setup completed but failed to save to database: {str(e)})"
        
        response = {
            "success": True,
            "session_id": session_id,
            "message": result.get("message", ""),
            "stage": result.get("stage", ""),
            "hints": result.get("hints", []),
            "requires_input": result.get("requires_input", True),
            "data": result.get("data", {}),
            "build_id": build_id
        }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error("Build chat failed", error=str(e), exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e),
            "message": f"❌ Error: {str(e)}"
        }), 500


@app.route("/api/build/list", methods=["GET"])
def list_builds():
    """List all saved builds."""
    try:
        if not build_storage:
            return jsonify({"error": "Build storage not available", "success": False}), 503
        
        limit = request.args.get("limit", 50, type=int)
        builds = build_storage.list_builds(limit=limit)
        
        return jsonify({
            "success": True,
            "builds": builds
        })
    
    except Exception as e:
        logger.error("List builds failed", error=str(e))
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/build/<int:build_id>", methods=["GET"])
def get_build(build_id):
    """Get a specific build by ID."""
    try:
        if not build_storage:
            return jsonify({"error": "Build storage not available", "success": False}), 503
        
        build = build_storage.get_build(build_id)
        
        if not build:
            return jsonify({"error": "Build not found", "success": False}), 404
        
        return jsonify({
            "success": True,
            "build": build
        })
    
    except Exception as e:
        logger.error("Get build failed", error=str(e))
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/build/reset", methods=["POST"])
def reset_build_chat():
    """Reset build chat session."""
    try:
        data = request.json
        session_id = data.get("session_id")
        
        if not session_id:
            return jsonify({"error": "Session ID is required", "success": False}), 400
        
        if not build_summary_agent:
            return jsonify({
                "error": "Build summary agent not available",
                "success": False
            }), 503
        
        build_summary_agent.reset_session(session_id)
        
        return jsonify({
            "success": True,
            "message": "Session reset successfully"
        })
    
    except Exception as e:
        logger.error("Reset build chat failed", error=str(e))
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/build/satisfied", methods=["POST"])
def build_satisfied():
    """Handle satisfied button - save to buildCaptureTable."""
    try:
        data = request.json
        session_id = data.get("session_id")
        user_id = data.get("user_id")
        organization_name = data.get("organization_name")
        lock_status = data.get("lock_status", "unlocked")
        
        if not session_id:
            return jsonify({"error": "Session ID is required", "success": False}), 400
        
        if not build_storage:
            return jsonify({
                "error": "Build storage not available",
                "success": False
            }), 503
        
        # Get the build data from the session
        if not build_summary_agent:
            return jsonify({
                "error": "Build agent not available",
                "success": False
            }), 503
        
        # Get build data from agent's conversation state
        state = build_summary_agent.conversation_state.get(session_id, {})
        build_data = state.get("data", {})
        
        # If no build data in state, try to get from build_retrievals
        if not build_data.get("databases"):
            # Try to get from last build
            builds = build_storage.list_builds(limit=1)
            if builds:
                build = builds[0]
                build_data = {
                    "databases": build.get("databases", []),
                    "connection_details": build.get("connection_details", {}),
                    "transformation_name": build.get("transformation_name", ""),
                    "intent": build.get("intent", "")
                }
        
        # Save to buildCaptureTable
        try:
            capture_id = build_storage.save_to_build_capture_table(
                session_id=session_id,
                build_data=build_data,
                user_id=user_id,
                organization_name=organization_name,
                lock_status=lock_status
            )
            
            return jsonify({
                "success": True,
                "message": "Build saved to buildCaptureTable successfully",
                "capture_id": capture_id
            })
        except Exception as e:
            logger.error("Failed to save to buildCaptureTable", error=str(e), exc_info=True)
            return jsonify({
                "success": False,
                "error": f"Failed to save to buildCaptureTable: {str(e)}"
            }), 500
    
    except Exception as e:
        logger.error("Build satisfied failed", error=str(e), exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/build/status", methods=["GET"])
def build_agent_status():
    """Check build agent status and configuration."""
    try:
        status = {
            "agent_initialized": build_summary_agent is not None,
            "storage_initialized": build_storage is not None,
            "llm_configured": False,
            "warehouse_configured": False,
            "errors": []
        }
        
        if build_summary_agent:
            try:
                # Check if LLM is configured
                if hasattr(build_summary_agent, 'llm') and build_summary_agent.llm:
                    status["llm_configured"] = True
                else:
                    status["errors"].append("LLM not configured in agent")
            except Exception as e:
                status["errors"].append(f"LLM check failed: {str(e)}")
            
            try:
                # Check warehouse connection
                from tools.warehouse import warehouse
                if hasattr(warehouse, 'engine') and warehouse.engine:
                    status["warehouse_configured"] = True
                else:
                    status["errors"].append("Warehouse not connected")
            except Exception as e:
                status["errors"].append(f"Warehouse check failed: {str(e)}")
        else:
            status["errors"].append("Build summary agent not initialized")
        
        return jsonify({
            "success": True,
            "status": status
        })
    
    except Exception as e:
        logger.error("Build status check failed", error=str(e))
        return jsonify({
            "success": False,
            "error": str(e),
            "status": {
                "agent_initialized": False,
                "storage_initialized": False,
                "llm_configured": False,
                "warehouse_configured": False,
                "errors": [str(e)]
            }
        }), 500


if __name__ == "__main__":
    # Run Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)

