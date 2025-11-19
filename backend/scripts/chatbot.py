"""Chatbot CLI - Interactive data query interface."""

import sys
import time
from pathlib import Path
import threading

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.chatbot_workflow import run_chatbot_query
from agents.auto_refresh_agent import AutoRefreshAgent
import structlog

logger = structlog.get_logger()


def display_data(formatted_display: dict):
    """Display formatted data in console."""
    if not formatted_display:
        return
    
    print("\n" + "=" * 80)
    print("📊 DATA TABLE")
    print("=" * 80)
    
    # Display summary
    summary = formatted_display.get("summary", "")
    print(f"\n{summary}\n")
    
    # Display data
    data = formatted_display.get("formatted_data", [])
    columns = formatted_display.get("columns", [])
    
    if not data:
        print("No data to display.")
        return
    
    # Print header
    header = " | ".join([f"{col:15}" for col in columns])
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in data:
        row_str = " | ".join([f"{str(row.get(col, '')):15}" for col in columns])
        print(row_str)
    
    metadata = formatted_display.get("metadata", {})
    if metadata.get("has_more"):
        print(f"\n... and {metadata['total_rows'] - metadata['displayed_rows']} more rows")
    
    print("\n" + "=" * 80)
    print("💡 Data auto-refreshes when PostgreSQL table is updated")
    print("📜 Historical snapshots are saved automatically")
    print("=" * 80 + "\n")


def run_refresh_monitor(monitor_id: str):
    """Background thread to monitor for changes."""
    auto_refresh = AutoRefreshAgent()
    
    while True:
        try:
            changed = auto_refresh.check_for_changes(monitor_id)
            if changed:
                print("\n🔄 Data updated! Refreshing...")
                # In real app, this would trigger UI update
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error("Monitor error", error=str(e))
            break


def main():
    """Main chatbot interface."""
    print("=" * 80)
    print("🤖 SaarInsights Data Chatbot")
    print("=" * 80)
    print("\nAsk me about your data tables!")
    print("Examples:")
    print("  - 'Show me orders data'")
    print("  - 'Display customers table'")
    print("  - 'Show me recent orders'")
    print("\nType 'exit' to quit\n")
    
    schema_name = "bronze"  # Default schema
    
    while True:
        try:
            # Get user input
            user_query = input("You: ").strip()
            
            if user_query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_query:
                continue
            
            # Run workflow
            print("\n🔍 Processing your query...")
            result = run_chatbot_query(user_query, schema_name)
            
            # Check for errors
            if result.get("errors"):
                print("\n❌ Error occurred:")
                for error in result["errors"]:
                    print(f"   - {error}")
                continue
            
            # Display data
            formatted_display = result.get("formatted_display")
            if formatted_display:
                display_data(formatted_display)
                
                # Start auto-refresh if monitor_id exists
                monitor_id = result.get("monitor_id")
                if monitor_id:
                    print(f"✅ Auto-refresh enabled (monitoring every 30 seconds)")
                    print("   (In production, this would update the UI automatically)\n")
            else:
                print("\n⚠️  No data to display")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error("Chatbot error", error=str(e))
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

