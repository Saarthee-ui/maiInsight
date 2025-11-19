"""Test script to verify the setup is working correctly."""

import sys

def test_imports():
    """Test that all required packages can be imported."""
    print("Testing package imports...")
    
    try:
        import langgraph
        print("✅ LangGraph imported")
    except ImportError as e:
        print(f"❌ LangGraph import failed: {e}")
        return False
    
    try:
        import langchain
        print("✅ LangChain imported")
    except ImportError as e:
        print(f"❌ LangChain import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import dbt
        print("✅ dbt imported")
    except ImportError as e:
        print(f"❌ dbt import failed: {e}")
        return False
    
    try:
        import pydantic
        print("✅ Pydantic imported")
    except ImportError as e:
        print(f"❌ Pydantic import failed: {e}")
        return False
    
    try:
        import structlog
        print("✅ Structlog imported")
    except ImportError as e:
        print(f"❌ Structlog import failed: {e}")
        return False
    
    return True

def test_project_structure():
    """Test that project modules can be imported."""
    print("\nTesting project structure...")
    
    try:
        from config import settings
        print("✅ Config module imported")
        print(f"   LLM Provider: {settings.llm_provider}")
        print(f"   Warehouse Type: {settings.warehouse_type}")
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False
    
    try:
        from models import schemas
        print("✅ Models module imported")
    except Exception as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from agents.base_agent import BaseAgent
        print("✅ Agents module imported")
    except Exception as e:
        print(f"❌ Agents import failed: {e}")
        return False
    
    try:
        from tools.warehouse import WarehouseConnection
        print("✅ Tools module imported")
    except Exception as e:
        print(f"❌ Tools import failed: {e}")
        return False
    
    return True

def test_agent_creation():
    """Test that agents can be instantiated (without LLM calls)."""
    print("\nTesting agent structure...")
    
    try:
        from agents.schema_agent import SchemaUnderstandingAgent
        from agents.datavault_agent import DataVaultModelingAgent
        from agents.etl_agent import ETLCodeGenerationAgent
        
        print("✅ Agent classes imported")
        print("   - SchemaUnderstandingAgent")
        print("   - DataVaultModelingAgent")
        print("   - ETLCodeGenerationAgent")
        
        # Note: We won't actually create agents here because they need LLM config
        # But we can verify the classes exist
        
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("SaarInsights Setup Verification")
    print("=" * 60)
    print(f"Python version: {sys.version.split()[0]}\n")
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_project_structure():
        all_passed = False
    
    if not test_agent_creation():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Setup is ready.")
        print("\nNext steps:")
        print("1. Create .env file with your credentials")
        print("2. Configure LLM provider (OpenAI/Anthropic/Ollama)")
        print("3. Configure warehouse connection (Snowflake/BigQuery)")
        print("4. Run: python examples/bronze_to_silver_example.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
