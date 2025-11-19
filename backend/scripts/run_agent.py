"""CLI script to run chatbot agents."""

import argparse
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from orchestration.chatbot_workflow import run_chatbot_query
import structlog

logger = structlog.get_logger()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Chatbot Data Viewer - Query PostgreSQL tables")
    parser.add_argument(
        "query",
        help="Your question about the data (e.g., 'Show me orders data')"
    )
    parser.add_argument(
        "--schema",
        default="bronze",
        help="Schema name to search in (default: bronze)"
    )
    
    args = parser.parse_args()
    
    logger.info("Running chatbot query", query=args.query, schema=args.schema)
    
    try:
        result = run_chatbot_query(args.query, args.schema)
        
        if result.get("errors"):
            print("\n❌ Errors occurred:")
            for error in result["errors"]:
                print(f"   - {error}")
            sys.exit(1)
        
        # Display results
        formatted = result.get("formatted_display", {})
        
        if formatted:
            print("\n" + "=" * 80)
            print("📊 DATA TABLE")
            print("=" * 80)
            
            # Summary
            if formatted.get("summary"):
                print(f"\n{formatted['summary']}\n")
            
            # Data table
            data = formatted.get("formatted_data", [])
            columns = formatted.get("columns", [])
            
            if data and columns:
                # Print header
                header = " | ".join([f"{col:15}" for col in columns])
                print(header)
                print("-" * len(header))
                
                # Print rows
                for row in data:
                    row_str = " | ".join([f"{str(row.get(col, '')):15}" for col in columns])
                    print(row_str)
                
                # Metadata
                metadata = formatted.get("metadata", {})
                if metadata.get("has_more"):
                    print(f"\n... and {metadata['total_rows'] - metadata['displayed_rows']} more rows")
            
            # Monitor info
            if result.get("monitor_id"):
                print("\n✅ Auto-refresh enabled (monitoring every 30 seconds)")
                print("   Historical snapshots are being saved automatically")
        else:
            print("\n⚠️  No data to display")
        
        print("\n" + "=" * 80)
        
    except Exception as e:
        logger.error("Chatbot query failed", error=str(e))
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
