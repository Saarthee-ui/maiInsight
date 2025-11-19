"""Flask web application for Chatbot Data Viewer."""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from orchestration.chatbot_workflow import run_chatbot_query
from agents.auto_refresh_agent import AutoRefreshAgent
from agents.data_reader_agent import DataReaderAgent
from agents.data_display_agent import DataDisplayAgent
from agents.historical_data_agent import HistoricalDataAgent
import structlog
import threading
import time

logger = structlog.get_logger()

app = Flask(__name__, template_folder='../frontend/templates')
CORS(app)  # Enable CORS for frontend

# Global state for monitoring
active_monitors = {}
refresh_agent = None
data_reader = None
data_display = None
historical_agent = None

# Initialize agents (with error handling)
try:
    refresh_agent = AutoRefreshAgent()
    data_reader = DataReaderAgent()
    data_display = DataDisplayAgent()
    historical_agent = HistoricalDataAgent()
    logger.info("All agents initialized successfully")
except Exception as e:
    logger.warning("Some agents failed to initialize", error=str(e))
    logger.warning("Frontend will start but database features may not work")


@app.route("/")
def index():
    """Serve the main chat interface."""
    # Check if database connection is available
    db_available = data_reader is not None
    return render_template("chatbot.html", db_available=db_available)


@app.route("/api/chatbot/query", methods=["POST"])
def chatbot_query():
    """Handle chatbot query and return data."""
    try:
        # Check if database is available
        if not data_reader:
            return jsonify({
                "error": "Database connection not available. Please check your PostgreSQL configuration.",
                "success": False
            }), 503
        
        data = request.json
        user_query = data.get("query", "")
        schema_name = data.get("schema", "public")
        
        if not user_query:
            return jsonify({"error": "Query is required"}), 400
        
        logger.info("Processing chatbot query", query=user_query, schema=schema_name)
        
        # Run workflow
        result = run_chatbot_query(user_query, schema_name)
        
        # Check for errors
        if result.get("errors"):
            return jsonify({
                "error": "; ".join(result["errors"]),
                "success": False
            }), 400
        
        # Extract formatted display
        formatted_display = result.get("formatted_display", {})
        
        response = {
            "success": True,
            "data": formatted_display.get("formatted_data", []),
            "columns": formatted_display.get("columns", []),
            "summary": formatted_display.get("summary", ""),
            "metadata": formatted_display.get("metadata", {}),
            "monitor_id": result.get("monitor_id"),
            "query_understanding": result.get("query_understanding", {}),
        }
        
        # Store monitor info for auto-refresh
        monitor_id = result.get("monitor_id")
        if monitor_id:
            active_monitors[monitor_id] = {
                "schema": schema_name,
                "table": result.get("query_understanding", {}).get("table_name"),
                "query_info": result.get("query_understanding", {}),
                "last_data": formatted_display.get("formatted_data", []),
            }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error("Chatbot query failed", error=str(e))
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/chatbot/refresh/<monitor_id>", methods=["GET"])
def refresh_data(monitor_id):
    """Manually trigger data refresh for a monitored table."""
    try:
        if monitor_id not in active_monitors:
            return jsonify({"error": "Monitor not found"}), 404
        
        monitor_info = active_monitors[monitor_id]
        
        # Read fresh data
        data = data_reader.read_table_data(
            schema_name=monitor_info["schema"],
            table_name=monitor_info["table"],
            limit=monitor_info["query_info"].get("limit", 10),
            filters=monitor_info["query_info"].get("filters", {}),
        )
        
        # Format for display
        formatted = data_display.format_data_for_display(data)
        
        # Save snapshot
        historical_agent.save_snapshot(
            schema_name=monitor_info["schema"],
            table_name=monitor_info["table"],
            data=data.get("data", []),
            change_type="manual_refresh"
        )
        
        # Update monitor info
        active_monitors[monitor_id]["last_data"] = formatted.get("formatted_data", [])
        
        return jsonify({
            "success": True,
            "data": formatted.get("formatted_data", []),
            "columns": formatted.get("columns", []),
            "summary": formatted.get("summary", ""),
            "metadata": formatted.get("metadata", {}),
        })
    
    except Exception as e:
        logger.error("Refresh failed", error=str(e))
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/chatbot/history/<schema>/<table>", methods=["GET"])
def get_history(schema, table):
    """Get historical snapshots for a table."""
    try:
        if not historical_agent:
            return jsonify({"error": "Historical data agent not available", "success": False}), 503
        
        limit = request.args.get("limit", 10, type=int)
        snapshots = historical_agent.get_snapshots(schema, table, limit=limit)
        
        return jsonify({
            "success": True,
            "snapshots": [
                {
                    "snapshot_id": s["snapshot_id"],
                    "timestamp": s["snapshot_timestamp"].isoformat() if hasattr(s["snapshot_timestamp"], "isoformat") else str(s["snapshot_timestamp"]),
                    "row_count": s["row_count"],
                    "change_type": s["change_type"],
                }
                for s in snapshots
            ]
        })
    
    except Exception as e:
        logger.error("History fetch failed", error=str(e))
        return jsonify({"error": str(e), "success": False}), 500


@app.route("/api/chatbot/snapshot/<int:snapshot_id>", methods=["GET"])
def get_snapshot(snapshot_id):
    """Get a specific snapshot by ID."""
    try:
        if not historical_agent:
            return jsonify({"error": "Historical data agent not available", "success": False}), 503
        
        snapshot = historical_agent.get_snapshot(snapshot_id)
        
        if not snapshot:
            return jsonify({"error": "Snapshot not found", "success": False}), 404
        
        return jsonify({
            "success": True,
            "snapshot": {
                "snapshot_id": snapshot["snapshot_id"],
                "timestamp": snapshot["snapshot_timestamp"].isoformat() if hasattr(snapshot["snapshot_timestamp"], "isoformat") else str(snapshot["snapshot_timestamp"]),
                "row_count": snapshot["row_count"],
                "change_type": snapshot["change_type"],
                "snapshot_data": snapshot["snapshot_data"],
                "schema_name": snapshot["schema_name"],
                "table_name": snapshot["table_name"],
            }
        })
    
    except Exception as e:
        logger.error("Snapshot fetch failed", error=str(e))
        return jsonify({"error": str(e), "success": False}), 500


def background_monitor():
    """Background thread to check for data changes."""
    while True:
        try:
            for monitor_id in list(active_monitors.keys()):
                changed = refresh_agent.check_for_changes(monitor_id)
                if changed:
                    logger.info("Data changed detected", monitor_id=monitor_id)
                    # In production, you'd push this via WebSocket
        except Exception as e:
            logger.error("Monitor error", error=str(e))
        
        time.sleep(18000)  # Check every 5 hours (5 * 60 * 60 seconds)


if __name__ == "__main__":
    # Start background monitoring thread
    monitor_thread = threading.Thread(target=background_monitor, daemon=True)
    monitor_thread.start()
    
    # Run Flask app
    app.run(debug=True, host="0.0.0.0", port=5000)

