"""Flask web application for Build Summary Agent."""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from agents.build_summary_agent import BuildSummaryAgent
from storage.build_retrieval_storage import BuildRetrievalStorage
import structlog
import uuid

logger = structlog.get_logger()

app = Flask(__name__, template_folder='../frontend/templates')
CORS(app)  # Enable CORS for frontend

# Global state
build_summary_agent = None
build_storage = None

# Initialize build summary agent
try:
    build_summary_agent = BuildSummaryAgent(allow_no_llm=True)
    if build_summary_agent.llm:
        logger.info("BuildSummaryAgent initialized successfully")
    else:
        logger.warning("BuildSummaryAgent initialized without LLM - API key not configured")
except Exception as e:
    logger.error("BuildSummaryAgent failed to initialize", error=str(e), exc_info=True)
    build_summary_agent = None

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


@app.route("/api/build/chat", methods=["POST"])
def build_chat():
    """Handle build chatbot conversation."""
    try:
        data = request.json
        user_input = data.get("message", "").strip()
        session_id = data.get("session_id")
        
        if not user_input:
            return jsonify({"error": "Message is required", "success": False}), 400
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        if not build_summary_agent:
            return jsonify({
                "error": "Build summary agent not available",
                "success": False
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
                    build_id = build_storage.save_build(result["build_data"])
                    result["build_id"] = build_id
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

