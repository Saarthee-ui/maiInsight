# ✅ Chatbot Data Viewer - Implementation Complete

## What Was Built

A complete chatbot-driven data viewing system with:
1. **Natural language query understanding**
2. **Data reading from PostgreSQL**
3. **Data display (10 rows preview)**
4. **Auto-refresh when data changes**
5. **Historical data snapshots**

## Components Created

### 1. ChatbotAgent (`agents/chatbot_agent.py`)
**Purpose**: Understands user questions and identifies which table to show.

**What it does**:
- Parses natural language queries ("Show me orders data")
- Identifies table name from available tables
- Extracts filters and conditions
- Determines query type (view, filter, aggregate)

**Example**:
```python
agent = ChatbotAgent()
result = agent.understand_query("Show me orders data")
# Returns: {"table_name": "orders", "limit": 10, "query_type": "view"}
```

---

### 2. DataReaderAgent (`agents/data_reader_agent.py`)
**Purpose**: Reads data from PostgreSQL tables.

**What it does**:
- Executes SQL queries to read table data
- Supports filtering and limiting
- Returns structured data (list of rows)
- Gets total row count

**Example**:
```python
agent = DataReaderAgent()
data = agent.read_table_data("bronze", "orders", limit=10)
# Returns: {"data": [...], "columns": [...], "row_count": 1000}
```

---

### 3. DataDisplayAgent (`agents/data_display_agent.py`)
**Purpose**: Formats data for display in chatbot/UI.

**What it does**:
- Formats data as table structure
- Creates user-friendly summary messages
- Handles metadata (total rows, displayed rows)

**Example**:
```python
agent = DataDisplayAgent()
formatted = agent.format_data_for_display(data_result)
# Returns: {"formatted_data": [...], "summary": "...", "metadata": {...}}
```

---

### 4. AutoRefreshAgent (`agents/auto_refresh_agent.py`)
**Purpose**: Monitors PostgreSQL tables and triggers refresh when data changes.

**What it does**:
- Monitors table row counts
- Checks for changes every 30 seconds (configurable)
- Triggers callback when data changes
- Tracks multiple tables simultaneously

**How it works**:
```python
agent = AutoRefreshAgent()

def refresh_callback(schema, table, new_state):
    # This function is called when data changes
    print(f"Data in {schema}.{table} changed!")

monitor_id = agent.start_monitoring(
    schema_name="bronze",
    table_name="orders",
    refresh_callback=refresh_callback,
    check_interval=30
)

# Later, check for changes
agent.check_for_changes(monitor_id)
```

---

### 5. HistoricalDataAgent (`agents/historical_data_agent.py`)
**Purpose**: Stores snapshots of data when it changes.

**What it does**:
- Saves snapshots to `history.data_snapshots` table
- Stores actual data as JSONB
- Tracks change types (initial, update, insert, delete)
- Enables data versioning

**Storage**:
```sql
history.data_snapshots
- snapshot_id (auto-increment)
- schema_name, table_name
- snapshot_timestamp
- row_count
- snapshot_data (JSONB - full data)
- change_type
```

**Example**:
```python
agent = HistoricalDataAgent()
snapshot_id = agent.save_snapshot(
    schema_name="bronze",
    table_name="orders",
    data=[...],  # Current data
    change_type="update"
)

# Get history
snapshots = agent.get_snapshots("bronze", "orders", limit=10)
```

---

### 6. Chatbot Workflow (`orchestration/chatbot_workflow.py`)
**Purpose**: Orchestrates the complete chatbot → data display flow.

**Workflow Steps**:
1. **Understand Query** → ChatbotAgent identifies table
2. **Read Data** → DataReaderAgent reads from PostgreSQL
3. **Format Display** → DataDisplayAgent formats data
4. **Setup Auto-Refresh** → AutoRefreshAgent starts monitoring
5. **Save Snapshot** → HistoricalDataAgent saves initial snapshot

**Usage**:
```python
from orchestration.chatbot_workflow import run_chatbot_query

result = run_chatbot_query("Show me orders data", schema_name="bronze")
formatted = result["formatted_display"]
```

---

### 7. Chatbot CLI (`scripts/chatbot.py`)
**Purpose**: Interactive command-line chatbot interface.

**Usage**:
```bash
python scripts/chatbot.py
```

**Example Session**:
```
You: Show me orders data
🔍 Processing your query...

📊 DATA TABLE
Showing 10 of 1000 rows from orders...

✅ Auto-refresh enabled
```

---

## Complete Flow

### Step-by-Step Process

```
1. User asks: "Show me orders data"
   ↓
2. ChatbotAgent.understand_query()
   → Identifies: table="orders", limit=10
   ↓
3. DataReaderAgent.read_table_data()
   → Reads 10 rows from bronze.orders
   → Returns: {"data": [...], "row_count": 1000}
   ↓
4. DataDisplayAgent.format_data_for_display()
   → Formats as table
   → Creates summary: "Showing 10 of 1000 rows..."
   ↓
5. AutoRefreshAgent.start_monitoring()
   → Starts monitoring bronze.orders
   → Checks every 30 seconds for changes
   ↓
6. HistoricalDataAgent.save_snapshot()
   → Saves initial snapshot to history.data_snapshots
   ↓
7. Display to user
   → Shows formatted data
   → User sees 10 rows
```

### When Data Changes

```
PostgreSQL: bronze.orders table updated (new row inserted)
   ↓
AutoRefreshAgent.check_for_changes()
   → Detects row count changed (1000 → 1001)
   ↓
Refresh callback triggered:
   → DataReaderAgent.read_table_data() (reads new data)
   → HistoricalDataAgent.save_snapshot() (saves new version)
   → DataDisplayAgent.format_data_for_display() (formats)
   ↓
UI updates automatically (in production)
   → User sees refreshed data
   → Historical snapshot saved
```

---

## Usage Examples

### Example 1: Simple Query

```python
from orchestration.chatbot_workflow import run_chatbot_query

result = run_chatbot_query("Show me orders data")

# Display data
formatted = result["formatted_display"]
print(formatted["summary"])
for row in formatted["formatted_data"]:
    print(row)
```

### Example 2: With Filters

```python
# User: "Show me completed orders"
result = run_chatbot_query("Show me completed orders")

# ChatbotAgent extracts: filters={"status": "completed"}
# DataReaderAgent applies filter
# Shows only completed orders
```

### Example 3: Auto-Refresh Setup

```python
from agents.auto_refresh_agent import AutoRefreshAgent
from agents.data_reader_agent import DataReaderAgent

def on_data_changed(schema, table, new_state):
    # Read new data
    reader = DataReaderAgent()
    new_data = reader.read_table_data(schema, table, limit=10)
    
    # Update UI (in your application)
    update_ui_display(new_data)

# Start monitoring
refresh_agent = AutoRefreshAgent()
monitor_id = refresh_agent.start_monitoring(
    schema_name="bronze",
    table_name="orders",
    refresh_callback=on_data_changed,
    check_interval=30
)
```

### Example 4: Access Historical Data

```python
from agents.historical_data_agent import HistoricalDataAgent

agent = HistoricalDataAgent()

# Get all snapshots for a table
snapshots = agent.get_snapshots("bronze", "orders", limit=10)

for snapshot in snapshots:
    print(f"Snapshot {snapshot['snapshot_id']}: {snapshot['row_count']} rows at {snapshot['snapshot_timestamp']}")

# Compare two snapshots
comparison = agent.compare_snapshots(snapshot_id_1=100, snapshot_id_2=101)
print(f"Row count changed by: {comparison['row_count_change']}")
```

---

## Features

✅ **Natural Language Understanding**: "Show me orders" → identifies table  
✅ **Data Reading**: Reads from PostgreSQL tables  
✅ **Display Formatting**: User-friendly data presentation  
✅ **Auto-Refresh**: Monitors and updates when data changes  
✅ **Historical Snapshots**: Saves all data versions  
✅ **Filtering Support**: Extracts filters from queries  
✅ **Configurable Limits**: Shows 10 rows (customizable)  
✅ **Error Handling**: Graceful error messages  

---

## Database Schema

### History Table (Auto-Created)

```sql
CREATE SCHEMA IF NOT EXISTS history;

CREATE TABLE history.data_snapshots (
    snapshot_id SERIAL PRIMARY KEY,
    schema_name VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    snapshot_timestamp TIMESTAMP NOT NULL,
    row_count INTEGER NOT NULL,
    snapshot_data JSONB,  -- Full data snapshot
    change_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_snapshots_table_time 
ON history.data_snapshots(schema_name, table_name, snapshot_timestamp DESC);
```

---

## Integration Points

### For Web Application

```python
# API Endpoint
@app.route("/api/chatbot/query", methods=["POST"])
def chatbot_query():
    user_query = request.json["query"]
    result = run_chatbot_query(user_query, schema_name="bronze")
    
    return jsonify({
        "data": result["formatted_display"]["formatted_data"],
        "summary": result["formatted_display"]["summary"],
        "monitor_id": result["monitor_id"],
    })

# WebSocket for auto-refresh
@socketio.on('start_monitoring')
def handle_monitoring(monitor_id):
    # Start background monitoring
    # Push updates to client via WebSocket
    pass
```

---

## Configuration

### Required Setup

1. **PostgreSQL**: Must be configured in `.env`
2. **History Schema**: Created automatically on first use
3. **Tables**: Client's data tables should be in PostgreSQL

### Environment Variables

```env
WAREHOUSE_TYPE=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=saarinsights
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

---

## Testing

### Test the Chatbot

```bash
python scripts/chatbot.py
```

Then try:
- "Show me orders data"
- "Display customers table"
- "Show me recent orders"

### Test Individual Agents

```python
# Test ChatbotAgent
from agents.chatbot_agent import ChatbotAgent
agent = ChatbotAgent()
result = agent.understand_query("Show me orders")

# Test DataReaderAgent
from agents.data_reader_agent import DataReaderAgent
agent = DataReaderAgent()
data = agent.read_table_data("bronze", "orders", limit=10)
```

---

## Next Steps

1. **Connect to your UI**: Integrate with your frontend
2. **WebSocket Updates**: Real-time data refresh
3. **Advanced Queries**: More complex filtering
4. **Data Comparison**: Show diffs between snapshots
5. **Export Features**: Download data as CSV/JSON

---

## Summary

✅ **5 New Agents Created**:
- ChatbotAgent (query understanding)
- DataReaderAgent (read from PostgreSQL)
- DataDisplayAgent (format display)
- AutoRefreshAgent (monitor changes)
- HistoricalDataAgent (save snapshots)

✅ **Complete Workflow**: User query → Data display → Auto-refresh → History

✅ **Ready to Use**: All components integrated and working

Everything is ready! Your users can now ask for data tables through a chatbot, see the data, and it will auto-refresh with historical tracking! 🚀

