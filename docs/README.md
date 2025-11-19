# SaarInsights: Agentic Medallion Architecture Platform

An intelligent, agent-driven data platform that automates Bronze → Silver → Gold transformations using a multi-agent system built on LangGraph and modern data tools.

## 🎯 Overview

This platform implements a **hybrid agentic AI system** that:
- **Automates** Data Vault model generation from Bronze schemas
- **Generates** ETL/ELT code (dbt models) for Silver layer
- **Monitors** query patterns and optimizes Gold layer on-demand
- **Detects** anomalies and self-heals pipeline issues
- **Answers** business questions using natural language

## 🏗️ Architecture

### Medallion Layers

- **🥉 Bronze**: Source-aligned, CDC-based raw data replica
- **🥈 Silver**: Business-aligned Data Vault 2.0 model (normalized, historized)
- **🥇 Gold**: Dimensional/analytics model (optimized for queries)

### Multi-Agent System

1. **Bronze Schema Understanding Agent**: Analyzes incoming schemas
2. **Data Vault Modeling Agent**: Generates Hub/Link/Satellite designs
3. **ETL Code Generation Agent**: Creates dbt models for Silver
4. **Query Monitoring Agent**: Tracks Silver query patterns
5. **Gold Optimization Agent**: Decides when to create Gold structures
6. **Anomaly Detection Agent**: Monitors data quality and pipeline health
7. **Business Question Agent**: Translates NL to SQL
8. **Orchestration Agent**: Coordinates all agents

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Access to a data warehouse (Snowflake, BigQuery, or PostgreSQL)
- LLM API key (OpenAI, Anthropic, or local Ollama)

### Installation

1. **Clone and setup**:
```bash
git clone <repo>
cd saarInsights
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Run your first Bronze → Silver transformation**:
```bash
python scripts/run_agent.py bronze-to-silver --schema BRONZE --table orders
```

## 📁 Project Structure

```
saarInsights/
├── agents/              # Agent implementations
├── tools/               # Utility tools (warehouse, dbt, etc.)
├── orchestration/       # LangGraph workflows
├── models/              # Pydantic data models
├── config/              # Configuration management
├── storage/             # State persistence
├── templates/           # Code templates
├── docs/                # Architecture documentation
└── scripts/             # CLI scripts
```

## 📚 Documentation

- **[Architecture Decision](./docs/ARCHITECTURE_DECISION.md)**: Agentic AI vs Deterministic
- **[Multi-Agent Architecture](./docs/MULTI_AGENT_ARCHITECTURE.md)**: Detailed agent specs
- **[Tooling Recommendations](./docs/TOOLING_RECOMMENDATIONS.md)**: Tech stack and tools
- **[Implementation Blueprint](./docs/IMPLEMENTATION_BLUEPRINT.md)**: Step-by-step guide

## 🛠️ Technology Stack

- **LangGraph**: Agent orchestration
- **LangChain**: LLM integration
- **dbt Core**: SQL transformations
- **SQLAlchemy**: Warehouse access
- **Great Expectations**: Data quality
- **Pydantic**: Data validation

## 💰 Cost Estimation

- **Development**: $0/month (using Ollama locally)
- **Production (Low)**: $50-125/month (GPT-4o API)
- **Production (High)**: $200-650/month

**ROI**: Saves 10-20 hours/month of manual work → Highly cost-effective

## 🔄 Workflows

### Bronze → Silver (Automated)

```python
from orchestration import run_bronze_to_silver

result = run_bronze_to_silver("BRONZE", "orders")
# Generates: Data Vault model + dbt models
```

### Gold-On-Demand (Coming Soon)

Query Monitoring Agent continuously monitors Silver queries and automatically creates Gold structures when beneficial.

## 📝 Example Usage

```python
# Analyze a Bronze table
from agents.schema_agent import SchemaUnderstandingAgent

agent = SchemaUnderstandingAgent()
metadata = agent.analyze_table("BRONZE", "orders")
print(f"Business keys: {metadata.business_keys}")

# Generate Data Vault model
from agents.datavault_agent import DataVaultModelingAgent

dv_agent = DataVaultModelingAgent()
model = dv_agent.generate_model(metadata)
print(f"Hubs: {len(model.hubs)}, Satellites: {len(model.satellites)}")
```

## 🧪 Development

```bash
# Run tests (when implemented)
pytest

# Format code
black .

# Type checking
mypy .
```

## 📊 Roadmap

- [x] Phase 1: Bronze → Silver automation (MVP)
- [ ] Phase 2: Query monitoring + Gold-on-demand
- [ ] Phase 3: Anomaly detection + Self-healing
- [ ] Phase 4: Business question agent

## 🤝 Contributing

This is an internal project. For questions or issues, contact the data platform team.

## 📄 License

Proprietary - Saarthee Internal Use Only
