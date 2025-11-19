# Tooling & Package Recommendations

## Core Stack (Free/Open-Source)

### 1. Agent Framework: **LangGraph** (Recommended)

**Why LangGraph?**
- ✅ Free and open-source (Apache 2.0)
- ✅ Built for multi-agent workflows with state management
- ✅ Integrates seamlessly with LangChain
- ✅ Supports complex control flows (conditional, loops, parallel)
- ✅ State persistence and checkpointing
- ✅ Latest version: 0.2+ (as of 2024)

**Use Case**: Orchestrate agent workflows, manage state, handle agent communication.

**Cost**: Free (self-hosted)

**Integration**: Core orchestration layer for all agents.

---

### 2. LLM Integration: **LangChain** + **OpenAI/Anthropic/Ollama**

**Why LangChain?**
- ✅ Free and open-source
- ✅ Standard interface for multiple LLM providers
- ✅ Tool calling support (function calling)
- ✅ Prompt templates and chains
- ✅ Latest version: 0.2+

**LLM Options**:
- **OpenAI GPT-4/GPT-4o**: Best quality, ~$0.01-0.10 per agent decision
- **Anthropic Claude 3.5 Sonnet**: Excellent for code generation, similar pricing
- **Ollama (Local)**: Free, runs locally, good for development/testing
- **Llama 3.1 (via Ollama)**: Free, decent quality for schema understanding

**Recommendation**: Use **Ollama for development** (free), **GPT-4o for production** (cost-effective for critical decisions).

**Cost**: 
- Ollama: $0 (local)
- GPT-4o: ~$0.005-0.03 per 1K tokens
- Claude 3.5: ~$0.003-0.015 per 1K tokens

**Integration**: All agents use LangChain for LLM calls.

---

### 3. Data Transformation: **dbt Core**

**Why dbt?**
- ✅ Free and open-source
- ✅ SQL-based transformations (fits warehouse architecture)
- ✅ Incremental models support
- ✅ Testing and documentation
- ✅ Version control friendly
- ✅ Latest version: 1.8+

**Use Case**: Execute generated SQL transformations, manage Silver/Gold models.

**Cost**: Free (dbt Core)

**Integration**: ETL Code Generation Agent creates dbt models, Orchestration Agent runs `dbt run`.

---

### 4. Database/Warehouse Access: **SQLAlchemy** + **snowflake-sqlalchemy** / **pybigquery**

**Why SQLAlchemy?**
- ✅ Free and open-source
- ✅ Standard Python ORM/query interface
- ✅ Schema introspection
- ✅ Works with Snowflake, BigQuery, PostgreSQL, etc.
- ✅ Latest version: 2.0+

**Use Case**: Schema inspection, query execution, metadata queries.

**Cost**: Free

**Integration**: Bronze Schema Understanding Agent, Query Monitoring Agent, Business Question Agent.

---

### 5. Data Quality: **Great Expectations**

**Why Great Expectations?**
- ✅ Free and open-source
- ✅ Declarative data quality checks
- ✅ Integrates with dbt
- ✅ Automated profiling
- ✅ Latest version: 0.18+

**Use Case**: Anomaly Detection Agent uses it for data quality monitoring.

**Cost**: Free

**Integration**: Anomaly Detection Agent runs Great Expectations suites.

---

### 6. Query Analysis: **sqlparse** + **sqlglot**

**Why sqlparse/sqlglot?**
- ✅ Free and open-source
- ✅ SQL parsing and analysis
- ✅ Query pattern detection
- ✅ Latest versions: sqlparse 0.5+, sqlglot 24.0+

**Use Case**: Query Monitoring Agent analyzes SQL queries.

**Cost**: Free

**Integration**: Query Monitoring Agent parses and analyzes queries.

---

### 7. Task Queue (Optional): **Celery** or **RQ**

**Why Celery/RQ?**
- ✅ Free and open-source
- ✅ Async task execution
- ✅ Distributed task processing
- ✅ Latest versions: Celery 5.3+, RQ 1.15+

**Use Case**: Background agent tasks, long-running operations.

**Cost**: Free (requires Redis/RabbitMQ)

**Integration**: Orchestration Agent can use for async tasks.

**Alternative**: LangGraph's built-in async support may be sufficient for MVP.

---

### 8. State Storage: **PostgreSQL** or **SQLite**

**Why PostgreSQL/SQLite?**
- ✅ Free and open-source
- ✅ Reliable state persistence
- ✅ SQL interface
- ✅ Latest versions: PostgreSQL 16+, SQLite 3.45+

**Use Case**: Store agent state, task queue, metadata cache.

**Cost**: Free

**Integration**: LangGraph state persistence, agent metadata cache.

**Recommendation**: SQLite for development, PostgreSQL for production.

---

### 9. Vector Store (Optional): **Chroma** or **FAISS**

**Why Chroma/FAISS?**
- ✅ Free and open-source
- ✅ Embedding storage for schema/documentation
- ✅ Semantic search for similar patterns
- ✅ Latest versions: Chroma 0.4+, FAISS (via langchain)

**Use Case**: Store schema patterns, query patterns for similarity search.

**Cost**: Free

**Integration**: Optional enhancement for pattern matching.

---

### 10. Monitoring & Logging: **Python logging** + **structlog**

**Why structlog?**
- ✅ Free and open-source
- ✅ Structured logging
- ✅ Better debugging
- ✅ Latest version: 24.1+

**Use Case**: Agent execution logs, debugging.

**Cost**: Free

**Integration**: All agents use structured logging.

---

## Tool Integration Map

```
┌─────────────────────────────────────────────────────────┐
│                   Orchestration Layer                    │
│                      (LangGraph)                         │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐   ┌────────▼────────┐  ┌──────▼──────┐
│   Agents     │   │   LLM (LangChain)│  │   Tools     │
│              │   │                  │  │             │
│ - Schema     │───│ - OpenAI/Claude  │  │ - SQLAlchemy│
│ - Data Vault │   │ - Ollama (local) │  │ - dbt Core  │
│ - ETL Code   │   │                  │  │ - Great Ex  │
│ - Query Mon  │   └──────────────────┘  │ - sqlparse  │
│ - Gold Opt   │                          │ - PostgreSQL│
│ - Anomaly    │                          └─────────────┘
│ - Business Q │
│ - Orchestr.  │
└──────────────┘
```

---

## Cost Estimation

### Development Phase
- **Ollama (Local LLM)**: $0
- **SQLite**: $0
- **dbt Core**: $0
- **All other tools**: $0
- **Total**: **$0/month**

### Production Phase (Low Volume)
- **GPT-4o API**: ~$50-100/month (assuming 1000-2000 agent decisions)
- **PostgreSQL**: $0 (self-hosted) or $25/month (managed)
- **Compute**: $0 (runs on existing infrastructure)
- **Total**: **$50-125/month**

### Production Phase (High Volume)
- **GPT-4o API**: ~$200-500/month (assuming 5000-10000 agent decisions)
- **PostgreSQL**: $0-50/month
- **Compute**: $0-100/month (if separate infrastructure)
- **Total**: **$200-650/month**

**ROI**: Saves 10-20 hours/month of manual work → **Highly cost-effective**

---

## Version Compatibility

All tools are compatible with:
- **Python**: 3.10+
- **VS Code / Cursor**: Full support
- **Operating System**: Windows/Linux/macOS

---

## Installation Commands

See `requirements.txt` for exact versions. Quick install:

```bash
pip install langgraph langchain openai anthropic ollama
pip install dbt-core dbt-snowflake  # or dbt-bigquery
pip install sqlalchemy snowflake-sqlalchemy  # or pybigquery
pip install great-expectations
pip install sqlparse sqlglot
pip install structlog
pip install chromadb  # optional
```

---

## Alternative Tools (If Needed)

- **CrewAI**: Alternative to LangGraph (more opinionated, good for agent teams)
- **AutoGen**: Microsoft's multi-agent framework (more complex setup)
- **LlamaIndex**: Good for RAG, but overkill for this use case
- **Prefect/Airflow**: For workflow orchestration (LangGraph is simpler for agents)

**Recommendation**: Stick with LangGraph for agent orchestration, use Prefect/Airflow only if you need complex scheduling beyond agent workflows.

