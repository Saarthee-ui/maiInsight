# File Loading Guide - PostgreSQL

This guide explains how to use the file loading functionality with PostgreSQL.

## Overview

The platform now supports:
1. **Loading files into PostgreSQL** (CSV, JSON, Parquet, Excel)
2. **Analyzing files** without loading
3. **Complete workflow from file to Silver** (file → analysis → Data Vault → dbt)

## Setup

### 1. Install PostgreSQL

**Windows:**
- Download from https://www.postgresql.org/download/windows/
- Install with default settings
- Remember the password you set

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql

# Mac
brew install postgresql
```

### 2. Create Database

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE saarinsights;

-- Create schemas
\c saarinsights
CREATE SCHEMA bronze;
CREATE SCHEMA silver;
CREATE SCHEMA gold;
```

### 3. Configure .env

```env
# Warehouse Configuration
WAREHOUSE_TYPE=postgres

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=saarinsights
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_SCHEMA_BRONZE=bronze
POSTGRES_SCHEMA_SILVER=silver
POSTGRES_SCHEMA_GOLD=gold
```

## Usage

### Option 1: Load File into PostgreSQL

```bash
# Load CSV file
python scripts/run_agent.py load-file --file data/orders.csv

# Load JSON file
python scripts/run_agent.py load-file --file data/customers.json

# Load to custom schema
python scripts/run_agent.py load-file --file data/orders.csv --target-schema bronze
```

### Option 2: Analyze File (No Loading)

```python
from agents.schema_agent import SchemaUnderstandingAgent

agent = SchemaUnderstandingAgent()
metadata = agent.analyze_file("data/orders.csv")

print(f"Columns: {len(metadata.columns)}")
print(f"Business Keys: {metadata.business_keys}")
```

### Option 3: Complete Workflow from File

```bash
# Run Bronze → Silver from file
python scripts/run_agent.py bronze-to-silver --file data/orders.csv
```

Or in Python:

```python
from orchestration import run_bronze_to_silver_from_file

result = run_bronze_to_silver_from_file("data/orders.csv")
```

### Option 4: Load File Then Process

```python
# Step 1: Load file
from agents.file_loader_agent import FileLoaderAgent

loader = FileLoaderAgent()
result = loader.load_file("data/orders.csv", schema_name="bronze")
# Creates: bronze.orders table

# Step 2: Process from PostgreSQL
from orchestration import run_bronze_to_silver

result = run_bronze_to_silver("bronze", "orders")
```

## Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Most common, UTF-8 encoding |
| JSON | `.json` | Array of objects |
| Parquet | `.parquet` | Efficient, compressed |
| Excel | `.xlsx`, `.xls` | First sheet only |

## Examples

### Example 1: Load CSV

```python
from agents.file_loader_agent import FileLoaderAgent

loader = FileLoaderAgent()
result = loader.load_file("data/orders.csv", schema_name="bronze")

# Result:
# {
#   "status": "success",
#   "table_name": "orders",
#   "row_count": 1000,
#   "columns": 5
# }
```

### Example 2: Analyze File

```python
from agents.schema_agent import SchemaUnderstandingAgent

agent = SchemaUnderstandingAgent()
metadata = agent.analyze_file("data/orders.csv")

# Returns TableMetadata with:
# - columns (names, types)
# - business_keys (inferred)
# - table_type (transactional, reference, etc.)
# - description
```

### Example 3: Complete Workflow

```python
from orchestration import run_bronze_to_silver_from_file

# Analyzes file → Generates Data Vault → Creates dbt models
result = run_bronze_to_silver_from_file("data/orders.csv")
```

## File Structure Requirements

### CSV Files
```csv
order_id,customer_id,order_date,total_amount,status
1,101,2024-01-15,150.50,completed
2,102,2024-01-16,200.75,pending
```

### JSON Files
```json
[
  {
    "order_id": 1,
    "customer_id": 101,
    "order_date": "2024-01-15",
    "total_amount": 150.50,
    "status": "completed"
  },
  {
    "order_id": 2,
    "customer_id": 102,
    "order_date": "2024-01-16",
    "total_amount": 200.75,
    "status": "pending"
  }
]
```

## Troubleshooting

### "PostgreSQL connection failed"
- Check PostgreSQL is running: `pg_isready`
- Verify credentials in `.env`
- Test connection: `psql -U postgres -d saarinsights`

### "File not found"
- Use absolute path or relative to project root
- Check file exists: `ls data/orders.csv`

### "Schema does not exist"
- Create schema: `CREATE SCHEMA bronze;`
- Or use `--target-schema` to specify existing schema

### "Permission denied"
- Check PostgreSQL user has CREATE privileges
- Grant permissions: `GRANT ALL ON SCHEMA bronze TO postgres;`

## Best Practices

1. **Use consistent naming**: Lowercase table names, underscores
2. **Handle large files**: Use Parquet for > 100MB files
3. **Validate data**: Check file before loading
4. **Use schemas**: Separate bronze/silver/gold schemas
5. **Monitor storage**: PostgreSQL has size limits

## Next Steps

After loading files:
1. Analyze with SchemaUnderstandingAgent
2. Generate Data Vault models
3. Create Silver layer with dbt
4. Build Gold layer for analytics

See `examples/file_loading_example.py` for complete examples.

