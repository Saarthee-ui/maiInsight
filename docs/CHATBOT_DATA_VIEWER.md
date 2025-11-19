# Chatbot Data Viewer Guide

## Overview

This feature allows users to query data tables through a chatbot interface. The system:
1. **Understands user questions** and identifies which table to show
2. **Reads data from PostgreSQL** tables
3. **Displays data** (10 rows preview)
4. **Auto-refreshes** when PostgreSQL table is updated
5. **Saves historical snapshots** of data changes

## Architecture

```
User Query (Chatbot)
    ↓
ChatbotAgent (understands query)
    ↓
DataReaderAgent (reads from PostgreSQL)
    ↓
DataDisplayAgent (formats for display)
    ↓
AutoRefreshAgent (monitors for changes)
    ↓
HistoricalDataAgent (saves snapshots)
```

## Components

### 1. ChatbotAgent
- Understands natural language queries
- Identifies which table user wants
- Extracts filters and conditions

### 2. DataReaderAgent
- Reads data from PostgreSQL tables
- Supports filtering and limiting
- Returns structured data

### 3. DataDisplayAgent
- Formats data for display
- Creates user-friendly summaries
- Handles data presentation

### 4. AutoRefreshAgent
- Monitors PostgreSQL tables for changes
- Triggers refresh when data updates
- Runs in background (checks every 30 seconds)

### 5. HistoricalDataAgent
- Saves snapshots when data changes
- Stores in `history.data_snapshots` table
- Enables data versioning

## Usage

### Interactive Chatbot

```bash
python scripts/chatbot.py
```

Example conversation:
```
You: Show me orders data
🔍 Processing your query...

📊 DATA TABLE
================================================================================
Showing 10 of 1000 rows from orders. Data refreshes automatically when the table is updated.

order_id      | customer_id   | order_date    | total_amount   | status        
--------------------------------------------------------------------------------
1             | 101          | 2024-01-15    | 150.50         | completed     
2             | 102          | 2024-01-16    | 200.75         | pending       
...

✅ Auto-refresh enabled (monitoring every 30 seconds)
```

### Programmatic Usage

```python
from orchestration.chatbot_workflow import run_chatbot_query

# User asks question
result = run_chatbot_query("Show me orders data", schema_name="bronze")

# Get formatted display
formatted = result["formatted_display"]
print(formatted["summary"])
print(formatted["formatted_data"])  # List of rows
```

## Auto-Refresh Mechanism

### How It Works

1. **Initial Load**: User asks for data → System reads and displays
2. **Monitoring Starts**: AutoRefreshAgent starts monitoring the table
3. **Change Detection**: Every 30 seconds, checks if row count changed
4. **Auto-Refresh**: When change detected:
   - Reads new data
   - Saves snapshot to history
   - Updates display (in UI)

### Configuration

```python
# Check interval (seconds)
check_interval = 30  # Default: check every 30 seconds

# Start monitoring
from agents.auto_refresh_agent import AutoRefreshAgent

agent = AutoRefreshAgent()
monitor_id = agent.start_monitoring(
    schema_name="bronze",
    table_name="orders",
    refresh_callback=your_callback_function,
    check_interval=30
)
```

## Historical Data Storage

### How It Works

1. **Initial Snapshot**: When user first views table, snapshot is saved
2. **Change Detection**: When AutoRefreshAgent detects change
3. **Snapshot Saved**: New snapshot saved to `history.data_snapshots`
4. **Version History**: All previous versions are preserved

### Storage Structure

```sql
history.data_snapshots
├── snapshot_id (auto-increment)
├── schema_name
├── table_name
├── snapshot_timestamp
├── row_count
├── snapshot_data (JSONB - actual data)
├── change_type (initial, update, insert, delete)
└── created_at
```

### Accessing History

```python
from agents.historical_data_agent import HistoricalDataAgent

agent = HistoricalDataAgent()

# Get recent snapshots
snapshots = agent.get_snapshots("bronze", "orders", limit=10)

# Get specific snapshot
snapshot = agent.get_snapshot(snapshot_id=123)

# Compare snapshots
comparison = agent.compare_snapshots(snapshot_id_1=100, snapshot_id_2=101)
```

## Example Workflows

### Workflow 1: Simple Query

```
User: "Show me orders"
    ↓
ChatbotAgent: Identifies "orders" table
    ↓
DataReaderAgent: Reads 10 rows from bronze.orders
    ↓
DataDisplayAgent: Formats and displays
    ↓
AutoRefreshAgent: Starts monitoring
    ↓
HistoricalDataAgent: Saves initial snapshot
```

### Workflow 2: Data Changes

```
PostgreSQL: bronze.orders table updated (new row inserted)
    ↓
AutoRefreshAgent: Detects change (row count increased)
    ↓
DataReaderAgent: Reads new data
    ↓
HistoricalDataAgent: Saves new snapshot
    ↓
UI: Auto-updates display (in production)
```

## Integration with UI

### For Web Application

```python
from orchestration.chatbot_workflow import run_chatbot_query

# API endpoint
@app.route("/api/chatbot/query", methods=["POST"])
def chatbot_query():
    user_query = request.json["query"]
    result = run_chatbot_query(user_query)
    
    return {
        "data": result["formatted_display"]["formatted_data"],
        "summary": result["formatted_display"]["summary"],
        "monitor_id": result["monitor_id"],
    }

# WebSocket for auto-refresh
@socketio.on('start_monitoring')
def handle_monitoring(monitor_id):
    # Start monitoring and push updates to client
    pass
```

## Configuration

### PostgreSQL Setup

```sql
-- History schema is created automatically
-- But you can create manually:
CREATE SCHEMA IF NOT EXISTS history;
```

### Environment Variables

```env
WAREHOUSE_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=saarinsights
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

## Features

✅ **Natural Language Queries**: "Show me orders", "Display customers"  
✅ **Auto-Refresh**: Monitors and updates when data changes  
✅ **Historical Snapshots**: Saves all data versions  
✅ **Filtering**: Supports filters from user queries  
✅ **Limit Rows**: Shows 10 rows by default (configurable)  
✅ **Error Handling**: Graceful error messages  

## Next Steps

1. **Web UI Integration**: Connect to your frontend
2. **WebSocket Updates**: Real-time data refresh
3. **Advanced Filtering**: More complex query parsing
4. **Data Comparison**: Show what changed between snapshots
5. **Export Options**: Download data as CSV/JSON

See `scripts/chatbot.py` for interactive example.

