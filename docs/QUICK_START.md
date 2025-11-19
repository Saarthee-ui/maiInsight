# Quick Start Guide

## Setup (5 minutes)

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```bash
# Copy example
cp .env.example .env

# Edit .env with your settings
```

**Minimum required settings:**
- `LLM_PROVIDER=openai` (or `ollama` for local)
- `OPENAI_API_KEY=your_key` (if using OpenAI)
- Warehouse connection details (Snowflake example):
  - `SNOWFLAKE_ACCOUNT=your_account`
  - `SNOWFLAKE_USER=your_user`
  - `SNOWFLAKE_PASSWORD=your_password`
  - `SNOWFLAKE_WAREHOUSE=your_warehouse`
  - `SNOWFLAKE_DATABASE=your_database`

### 3. Test Connection

```python
from tools.warehouse import warehouse
from config import settings

# Test warehouse connection
tables = warehouse.list_tables(settings.snowflake_schema_bronze)
print(f"Found {len(tables)} tables in Bronze")
```

## Your First Transformation

### Option 1: Using CLI

```bash
python scripts/run_agent.py bronze-to-silver --schema BRONZE --table orders
```

### Option 2: Using Python

```python
from orchestration import run_bronze_to_silver

result = run_bronze_to_silver("BRONZE", "orders")
print(result)
```

### Option 3: Step-by-Step (for learning)

```python
from agents.schema_agent import SchemaUnderstandingAgent
from agents.datavault_agent import DataVaultModelingAgent
from agents.etl_agent import ETLCodeGenerationAgent

# 1. Analyze schema
schema_agent = SchemaUnderstandingAgent()
metadata = schema_agent.analyze_table("BRONZE", "orders")

# 2. Generate Data Vault model
dv_agent = DataVaultModelingAgent()
model = dv_agent.generate_model(metadata)

# 3. Generate ETL code
etl_agent = ETLCodeGenerationAgent()
result = etl_agent.generate_etl_code(model)
```

## What Gets Generated

After running the workflow, you'll have:

1. **Data Vault Model** (in memory/Pydantic):
   - Hub definitions
   - Link definitions
   - Satellite definitions

2. **dbt Models** (in `./dbt_project/models/silver/`):
   - `hub_*.sql` - Hub loading models
   - `link_*.sql` - Link loading models
   - `sat_*.sql` - Satellite loading models (SCD Type 2)

3. **Execution Plan**:
   - Incremental load logic
   - Merge/upsert patterns
   - Data quality checks

## Next Steps

1. **Review Generated Models**:
   ```bash
   ls -la dbt_project/models/silver/
   ```

2. **Run dbt**:
   ```bash
   cd dbt_project
   dbt run --models silver
   ```

3. **Verify Results**:
   ```sql
   SELECT * FROM SILVER.HUB_ORDERS LIMIT 10;
   ```

## Troubleshooting

### "LLM API key not set"
- Check `.env` file
- Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set

### "Warehouse not connected"
- Verify warehouse credentials in `.env`
- Test connection manually:
  ```python
  from tools.warehouse import warehouse
  warehouse._connect()
  ```

### "Table not found"
- Verify table exists in Bronze schema
- Check schema name (case-sensitive for Snowflake)

### "dbt models not generated"
- Check `dbt_project_dir` in settings
- Verify write permissions

## Using Local LLM (Ollama)

For development/testing without API costs:

1. **Install Ollama**:
   ```bash
   # Visit https://ollama.ai
   # Download and install
   ```

2. **Pull model**:
   ```bash
   ollama pull llama3.1
   ```

3. **Configure**:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. **Test**:
   ```python
   from agents.schema_agent import SchemaUnderstandingAgent
   agent = SchemaUnderstandingAgent()  # Will use Ollama
   ```

## Advanced Usage

See `examples/bronze_to_silver_example.py` for more examples.

