# Getting Started Checklist

## ✅ Step 1: Review Architecture (15 minutes)

1. Read `docs/ARCHITECTURE_DECISION.md` - Understand when agentic AI is beneficial
2. Read `docs/MULTI_AGENT_ARCHITECTURE.md` - Understand agent design
3. Read `docs/SUMMARY.md` - Get the big picture

## ✅ Step 2: Set Up Environment (10 minutes)

1. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Create `.env` file** (copy from template below):
   ```bash
   # Minimum required for testing
   LLM_PROVIDER=ollama  # or openai
   OPENAI_API_KEY=your_key_here  # if using OpenAI
   
   # Warehouse (Snowflake example)
   WAREHOUSE_TYPE=snowflake
   SNOWFLAKE_ACCOUNT=your_account
   SNOWFLAKE_USER=your_user
   SNOWFLAKE_PASSWORD=your_password
   SNOWFLAKE_WAREHOUSE=your_warehouse
   SNOWFLAKE_DATABASE=your_database
   SNOWFLAKE_SCHEMA_BRONZE=BRONZE
   SNOWFLAKE_SCHEMA_SILVER=SILVER
   SNOWFLAKE_SCHEMA_GOLD=GOLD
   ```

## ✅ Step 3: Test Local LLM (Optional, 5 minutes)

If you want to test without API costs:

1. **Install Ollama**: https://ollama.ai
2. **Pull model**:
   ```bash
   ollama pull llama3.1
   ```
3. **Test**:
   ```bash
   ollama run llama3.1 "Hello"
   ```
4. **Update `.env`**:
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   ```

## ✅ Step 4: Test Warehouse Connection (5 minutes)

```python
from tools.warehouse import warehouse
from config import settings

# List tables in Bronze
tables = warehouse.list_tables(settings.snowflake_schema_bronze)
print(f"Found {len(tables)} tables")

# Test metadata extraction
if tables:
    metadata = warehouse.get_table_metadata(
        settings.snowflake_schema_bronze, 
        tables[0]
    )
    print(f"Table: {metadata.name}")
    print(f"Columns: {len(metadata.columns)}")
```

## ✅ Step 5: Run Your First Transformation (10 minutes)

### Option A: Using CLI

```bash
python scripts/run_agent.py bronze-to-silver --schema BRONZE --table orders
```

### Option B: Using Python Script

```bash
python examples/bronze_to_silver_example.py
```

### Option C: Using Python API

```python
from orchestration import run_bronze_to_silver

result = run_bronze_to_silver("BRONZE", "orders")
print(result)
```

## ✅ Step 6: Review Generated Code (5 minutes)

1. **Check generated dbt models**:
   ```bash
   ls -la dbt_project/models/silver/
   ```

2. **Review a model**:
   ```bash
   cat dbt_project/models/silver/hub_orders.sql
   ```

3. **Run dbt** (if dbt is configured):
   ```bash
   cd dbt_project
   dbt run --models silver
   ```

## ✅ Step 7: Customize for Your Use Case (30+ minutes)

1. **Modify Data Vault patterns**:
   - Edit `agents/datavault_agent.py` prompts
   - Add custom templates in `templates/datavault/`

2. **Customize dbt generation**:
   - Edit `tools/dbt_generator.py`
   - Add your SQL patterns

3. **Add custom validation**:
   - Extend `agents/base_agent.py` validation methods

## 🎯 What You Have Now

✅ **Working Phase 1 MVP**:
- Bronze Schema Understanding Agent
- Data Vault Modeling Agent  
- ETL Code Generation Agent
- LangGraph orchestration
- CLI interface

✅ **Ready to Extend**:
- Query Monitoring Agent (Phase 2)
- Gold Optimization Agent (Phase 2)
- Anomaly Detection Agent (Phase 3)
- Business Question Agent (Phase 3)

## 📚 Next Steps

1. **Read the docs** in `docs/` folder
2. **Experiment** with different Bronze tables
3. **Customize** prompts and templates
4. **Extend** with Phase 2 agents when ready

## 🆘 Troubleshooting

### "Module not found"
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`

### "LLM API key not set"
- Check `.env` file exists
- Verify `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is set
- Or use `LLM_PROVIDER=ollama` for local testing

### "Warehouse connection failed"
- Verify credentials in `.env`
- Test connection manually with SQLAlchemy
- Check network/firewall settings

### "Table not found"
- Verify table exists in Bronze schema
- Check schema name (case-sensitive for Snowflake)
- List tables: `warehouse.list_tables("BRONZE")`

## 💡 Tips

1. **Start with Ollama** for development (free, fast iteration)
2. **Use GPT-4o** for production (better quality)
3. **Review generated models** before running dbt
4. **Customize prompts** for your domain
5. **Add validation** for your specific requirements

## 🎓 Learning Path

1. **Week 1**: Understand architecture, test with sample tables
2. **Week 2**: Customize prompts, add domain-specific patterns
3. **Week 3**: Implement Phase 2 (Query Monitoring + Gold Optimization)
4. **Week 4**: Production deployment, monitoring, optimization

Good luck! 🚀

