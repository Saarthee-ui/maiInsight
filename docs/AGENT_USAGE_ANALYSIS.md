# Agent Usage Analysis for Chatbot Data Viewer

## 🎯 Purpose
This document explains which agents are used for the **Chatbot Data Viewer** functionality (read from PostgreSQL, display on screen, create historical data) and which agents are NOT used for this specific feature.

---

## ✅ AGENTS USED FOR CHATBOT DATA VIEWER

### 1. **ChatbotAgent** (`agents/chatbot_agent.py`)
**Purpose**: Understands user queries and identifies which table to show

**Used in**:
- `orchestration/chatbot_workflow.py` - Step 1: `understand_query()`
- `app.py` - Indirectly through workflow

**What it does**:
- Parses natural language: "Show me orders data" → identifies "orders" table
- Extracts filters and conditions from user query
- Returns table name, schema, limit, filters

**Status**: ✅ **ACTIVELY USED**

---

### 2. **DataReaderAgent** (`agents/data_reader_agent.py`)
**Purpose**: Reads data from PostgreSQL tables

**Used in**:
- `orchestration/chatbot_workflow.py` - Step 2: `read_data()`
- `orchestration/chatbot_workflow.py` - Auto-refresh callback
- `app.py` - Manual refresh endpoint

**What it does**:
- Executes SQL queries to read table data
- Supports filtering and limiting (shows 10 rows by default)
- Returns structured data (list of rows with columns)

**Status**: ✅ **ACTIVELY USED**

---

### 3. **DataDisplayAgent** (`agents/data_display_agent.py`)
**Purpose**: Formats data for display in chatbot/UI

**Used in**:
- `orchestration/chatbot_workflow.py` - Step 3: `format_display()`
- `orchestration/chatbot_workflow.py` - Auto-refresh callback
- `app.py` - Indirectly through workflow

**What it does**:
- Formats data as table structure
- Creates user-friendly summary messages
- Handles metadata (total rows, displayed rows)

**Status**: ✅ **ACTIVELY USED**

---

### 4. **AutoRefreshAgent** (`agents/auto_refresh_agent.py`)
**Purpose**: Monitors PostgreSQL tables and triggers refresh when data changes

**Used in**:
- `orchestration/chatbot_workflow.py` - Step 4: `setup_auto_refresh()`
- `app.py` - Background monitoring thread

**What it does**:
- Monitors table row counts every 30 seconds
- Detects when data changes
- Triggers refresh callback automatically
- Tracks multiple tables simultaneously

**Status**: ✅ **ACTIVELY USED**

---

### 5. **HistoricalDataAgent** (`agents/historical_data_agent.py`)
**Purpose**: Stores snapshots of data when it changes

**Used in**:
- `orchestration/chatbot_workflow.py` - Step 5: `save_initial_snapshot()`
- `orchestration/chatbot_workflow.py` - Auto-refresh callback
- `app.py` - History endpoint

**What it does**:
- Saves snapshots to `history.data_snapshots` table
- Stores actual data as JSONB
- Tracks change types (initial, update, insert, delete)
- Enables data versioning

**Status**: ✅ **ACTIVELY USED**

---

## ❌ AGENTS NOT USED FOR CHATBOT DATA VIEWER

These agents are **NOT** used in the chatbot data viewer workflow, but they serve other purposes:

### 1. **FileLoaderAgent** (`agents/file_loader_agent.py`)
**Purpose**: Loads local files (CSV, JSON, Excel) into PostgreSQL

**Used for**: 
- Bronze layer data ingestion from local files
- Initial data loading workflow

**NOT used in**: Chatbot data viewer (only reads existing PostgreSQL data)

**Status**: ⚠️ **NOT USED** for chatbot, but used for other workflows

---

### 2. **S3LoaderAgent** (`agents/s3_loader_agent.py`)
**Purpose**: Loads files from AWS S3 into PostgreSQL

**Used for**:
- Bronze layer data ingestion from S3
- Cloud-based data loading workflow

**NOT used in**: Chatbot data viewer (only reads existing PostgreSQL data)

**Status**: ⚠️ **NOT USED** for chatbot, but used for other workflows

---

### 3. **SchemaAgent** (`agents/schema_agent.py`)
**Purpose**: Analyzes database schemas and extracts metadata

**Used for**:
- Bronze → Silver transformation workflow
- Schema understanding for Data Vault modeling
- File/S3 schema analysis

**NOT used in**: Chatbot data viewer (ChatbotAgent handles table identification differently)

**Status**: ⚠️ **NOT USED** for chatbot, but used for Bronze→Silver workflow

---

### 4. **DataVaultAgent** (`agents/datavault_agent.py`)
**Purpose**: Creates Data Vault 2.0 models (Hubs, Links, Satellites)

**Used for**:
- Bronze → Silver transformation workflow
- Automated Data Vault model generation

**NOT used in**: Chatbot data viewer (only displays data, doesn't transform)

**Status**: ⚠️ **NOT USED** for chatbot, but used for Bronze→Silver workflow

---

### 5. **ETLAgent** (`agents/etl_agent.py`)
**Purpose**: Generates ETL/ELT code (dbt models) for Silver layer

**Used for**:
- Bronze → Silver transformation workflow
- Code generation for incremental loads

**NOT used in**: Chatbot data viewer (only reads data, doesn't transform)

**Status**: ⚠️ **NOT USED** for chatbot, but used for Bronze→Silver workflow

---

## 📊 Complete Flow Diagram

```
CHATBOT DATA VIEWER WORKFLOW
=============================

User Query: "Show me orders data"
    ↓
[1] ChatbotAgent
    → Understands query
    → Identifies "orders" table
    ↓
[2] DataReaderAgent
    → Reads 10 rows from PostgreSQL (bronze.orders)
    → Returns structured data
    ↓
[3] DataDisplayAgent
    → Formats data for display
    → Creates summary message
    ↓
[4] AutoRefreshAgent
    → Starts monitoring bronze.orders
    → Checks every 30 seconds for changes
    ↓
[5] HistoricalDataAgent
    → Saves initial snapshot
    → Stores in history.data_snapshots
    ↓
Display to User
    → Shows formatted table
    → Auto-refreshes when data changes

WHEN DATA CHANGES:
    ↓
AutoRefreshAgent detects change
    ↓
DataReaderAgent reads new data
    ↓
HistoricalDataAgent saves new snapshot
    ↓
DataDisplayAgent formats new data
    ↓
UI updates automatically
```

---

## 🎯 Summary

### For Chatbot Data Viewer:
✅ **5 Agents Used**:
1. ChatbotAgent
2. DataReaderAgent
3. DataDisplayAgent
4. AutoRefreshAgent
5. HistoricalDataAgent

### Not Used for Chatbot (but used elsewhere):
⚠️ **5 Agents Not Used**:
1. FileLoaderAgent (used for file ingestion)
2. S3LoaderAgent (used for S3 ingestion)
3. SchemaAgent (used for Bronze→Silver)
4. DataVaultAgent (used for Bronze→Silver)
5. ETLAgent (used for Bronze→Silver)

---

## 💡 Recommendation

**All agents are useful!** They serve different purposes:

- **Chatbot Data Viewer**: Uses 5 agents (query → read → display → monitor → history)
- **Bronze → Silver Workflow**: Uses SchemaAgent, DataVaultAgent, ETLAgent
- **Data Ingestion**: Uses FileLoaderAgent, S3LoaderAgent

**No agents are "useless"** - they're part of different workflows in your platform!

---

## 🔄 Agent Dependencies

```
Chatbot Workflow:
ChatbotAgent → DataReaderAgent → DataDisplayAgent
                ↓                    ↓
         AutoRefreshAgent    HistoricalDataAgent

Bronze→Silver Workflow:
SchemaAgent → DataVaultAgent → ETLAgent

Data Ingestion:
FileLoaderAgent / S3LoaderAgent → PostgreSQL
```

---

## 📝 Notes

- The chatbot workflow is **self-contained** - it only needs the 5 agents listed
- Other agents are used in **different workflows** (Bronze→Silver transformation)
- This is **good architecture** - each workflow uses only what it needs
- Agents can be **reused** across different workflows

