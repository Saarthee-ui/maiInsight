"""
Script to ingest RAG documents into the vector store.

This script processes all documents in the rag_documents folder and 
ingests them into the ChromaDB vector store for use with RAGBuildAgent.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from storage.document_ingestion import DocumentIngestion
import structlog

logger = structlog.get_logger()


def main():
    """Ingest RAG documents into vector store."""
    print("\n" + "="*60)
    print("RAG Document Ingestion Script")
    print("="*60)
    print()
    
    # Initialize ingestion
    rag_folder = Path("rag_documents")
    
    if not rag_folder.exists():
        print(f"❌ Error: RAG documents folder not found: {rag_folder}")
        print("   Please ensure the 'rag_documents' folder exists.")
        return 1
    
    print(f"📁 RAG Folder: {rag_folder.absolute()}")
    print()
    
    # Count documents
    docx_files = list(rag_folder.rglob("*.docx"))
    txt_files = list(rag_folder.rglob("*.txt"))
    md_files = list(rag_folder.rglob("*.md"))
    total_files = len(docx_files) + len(txt_files) + len(md_files)
    
    print(f"📄 Found {total_files} documents:")
    print(f"   - {len(docx_files)} Word documents (.docx)")
    print(f"   - {len(txt_files)} Text files (.txt)")
    print(f"   - {len(md_files)} Markdown files (.md)")
    print()
    
    if total_files == 0:
        print("⚠️  No documents found to ingest.")
        return 0
    
    # Check for OpenAI API key first
    import os
    env_file = Path(".env")
    if not env_file.exists():
        env_file = Path("backend/.env")
    
    openai_key_configured = False
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                if 'OPENAI_API_KEY' in content or 'openai_api_key' in content:
                    openai_key_configured = True
        except:
            pass
    
    # Also check environment variable
    if os.getenv('OPENAI_API_KEY'):
        openai_key_configured = True
    
    if not openai_key_configured:
        print("⚠️  Warning: OpenAI API key not found.")
        print("   Please configure your OpenAI API key:")
        print("   1. Create a .env file in the project root (if it doesn't exist)")
        print("   2. Add: OPENAI_API_KEY=your_api_key_here")
        print()
        print("   Without the API key, embeddings cannot be created and documents cannot be stored.")
        print()
        response = input("Continue anyway? (Documents will not be stored) (y/n): ").strip().lower()
        if response != 'y':
            print("Cancelled.")
            return 0
    
    # Initialize ingestion system
    print("🔧 Initializing document ingestion system...")
    try:
        ingestion = DocumentIngestion(rag_folder=str(rag_folder))
        print("✅ Document ingestion system initialized")
        print()
    except Exception as e:
        print(f"❌ Error initializing ingestion system: {e}")
        return 1
    
    # Check if vector store is available
    if not ingestion.vector_store.is_available():
        print("❌ Error: Vector store is not available.")
        print()
        print("This might be because:")
        print("   - OpenAI API key is not configured correctly")
        print("   - ChromaDB is not installed")
        print("   - Embeddings model is not available")
        print()
        print("Please ensure:")
        print("   1. OpenAI API key is configured in .env file: OPENAI_API_KEY=your_key")
        print("   2. ChromaDB is installed: pip install chromadb")
        print("   3. The API key is valid and has access to embeddings")
        print()
        return 1
    
    # Ingest documents
    print("📥 Starting document ingestion...")
    print()
    
    try:
        results = ingestion.ingest_folder()
        
        print("="*60)
        print("Ingestion Results")
        print("="*60)
        print()
        print(f"✅ Successfully processed: {results['processed']} files")
        print(f"❌ Failed: {results['failed']} files")
        print()
        
        if results['files']:
            print("File Details:")
            print("-" * 60)
            for file_info in results['files']:
                status_icon = "✅" if file_info['status'] == 'success' else "❌"
                print(f"{status_icon} {file_info['file']}")
                if file_info['status'] == 'error' and 'error' in file_info:
                    print(f"   Error: {file_info['error']}")
            print()
        
        if results['success'] and results['processed'] > 0:
            print("🎉 Document ingestion completed successfully!")
            print()
            print("Next steps:")
            print("1. Update app.py to use RAGBuildAgent instead of BuildSummaryAgent")
            print("2. Restart the server to use the RAG-enhanced agent")
            print("3. Test the agent with queries that should use RAG context")
            return 0
        elif results['failed'] > 0:
            print("⚠️  Some documents failed to ingest. Please check the errors above.")
            return 1
        else:
            print("⚠️  No documents were processed.")
            return 0
            
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
        logger.error("Ingestion failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)


