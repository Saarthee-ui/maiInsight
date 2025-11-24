"""Vector store for RAG documents using embeddings."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()


class DocumentVectorStore:
    """Vector store for storing and retrieving RAG document embeddings."""
    
    def __init__(self, persist_directory: str = "./storage/document_vectors"):
        """Initialize document vector store."""
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        self.vector_store = None
        self.embeddings = None
        self._init_vector_store()
    
    def _init_vector_store(self):
        """Initialize vector store and embeddings."""
        try:
            # Try to use ChromaDB if available
            try:
                import chromadb
                from chromadb.config import Settings
                from langchain_openai import OpenAIEmbeddings
                from langchain_community.vectorstores import Chroma
                from config import settings
                
                # Initialize embeddings
                if settings.openai_api_key:
                    self.embeddings = OpenAIEmbeddings(
                        model="text-embedding-3-small",
                        openai_api_key=settings.openai_api_key
                    )
                else:
                    logger.warning("OpenAI API key not found, document vector store will use fallback")
                    self.embeddings = None
                
                # Initialize ChromaDB
                client = chromadb.PersistentClient(
                    path=str(self.persist_directory),
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # Create or get collection for documents
                collection_name = "rag_documents"
                try:
                    collection = client.get_collection(collection_name)
                    logger.info("Loaded existing document collection", collection=collection_name)
                except:
                    collection = client.create_collection(collection_name)
                    logger.info("Created new document collection", collection=collection_name)
                
                # Create LangChain Chroma wrapper
                if self.embeddings:
                    self.vector_store = Chroma(
                        client=client,
                        collection_name=collection_name,
                        embedding_function=self.embeddings
                    )
                    logger.info("Document vector store initialized successfully with embeddings")
                else:
                    logger.warning("Document vector store initialized but embeddings not available - OpenAI API key may not be configured")
                    # Still create vector store but it won't work without embeddings
                    try:
                        from langchain_openai import OpenAIEmbeddings
                        # Try to create with default settings (might work if env var is set)
                        try:
                            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
                            self.vector_store = Chroma(
                                client=client,
                                collection_name=collection_name,
                                embedding_function=self.embeddings
                            )
                            logger.info("Document vector store initialized successfully with embeddings from environment")
                        except Exception:
                            logger.warning("Could not initialize embeddings from environment variables")
                            self.vector_store = None
                            self.embeddings = None
                    except Exception:
                        logger.warning("Could not create embeddings - vector store will not be functional")
                        self.vector_store = None
                        self.embeddings = None
                    
            except ImportError:
                logger.warning("ChromaDB not available, document vector store disabled")
                self.vector_store = None
                self.embeddings = None
                
        except Exception as e:
            logger.error("Failed to initialize document vector store", error=str(e))
            self.vector_store = None
            self.embeddings = None
    
    def add_document(self, document_text: str, metadata: Dict[str, Any], doc_id: Optional[str] = None) -> bool:
        """
        Add a document to the vector store.
        
        Args:
            document_text: The text content of the document
            metadata: Metadata about the document (file_path, category, etc.)
            doc_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        # Check if vector store and embeddings are available
        # Use explicit None check instead of truthiness since Chroma objects can be falsy
        if self.vector_store is None or self.embeddings is None:
            logger.warning("Vector store not available, cannot add document", 
                         has_vector_store=self.vector_store is not None,
                         has_embeddings=self.embeddings is not None)
            return False
        
        try:
            if not doc_id:
                doc_id = f"doc_{datetime.now().timestamp()}_{hash(document_text) % 10000}"
            
            self.vector_store.add_texts(
                texts=[document_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            logger.info("Document added to vector store", doc_id=doc_id, category=metadata.get("category", "unknown"))
            return True
        except Exception as e:
            logger.error("Failed to add document to vector store", error=str(e), doc_id=doc_id)
            return False
    
    def search_documents(self, query: str, k: int = 5, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents in the vector store.
        
        Args:
            query: Search query string
            k: Number of results to return
            category: Optional category filter (documentation, schemas, examples, rules)
            
        Returns:
            List of relevant documents with metadata and similarity scores
        """
        # Use explicit None check instead of truthiness since Chroma objects can be falsy
        if self.vector_store is None or self.embeddings is None:
            logger.warning("Vector store not available, cannot search documents")
            return []
        
        try:
            # Build filter if category specified
            where_filter = None
            if category:
                where_filter = {"category": category}
            
            # Search with optional filter
            if where_filter:
                results = self.vector_store.similarity_search_with_score(
                    query, 
                    k=k,
                    filter=where_filter
                )
            else:
                results = self.vector_store.similarity_search_with_score(query, k=k)
            
            documents = []
            for doc, score in results:
                doc_info = {
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "similarity_score": float(score)
                }
                documents.append(doc_info)
            
            logger.info("Searched documents", query=query, num_results=len(documents), category=category)
            return documents
        except Exception as e:
            logger.error("Failed to search documents", query=query, error=str(e))
            return []
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents from the vector store."""
        if not self.vector_store:
            return []
        
        try:
            # Get all documents from collection
            collection = self.vector_store._collection
            results = collection.get()
            
            documents = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"]):
                    metadata = results.get("metadatas", [{}])[i] if results.get("metadatas") else {}
                    documents.append({
                        "id": doc_id,
                        "metadata": metadata
                    })
            
            return documents
        except Exception as e:
            logger.error("Failed to get all documents", error=str(e))
            return []
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the vector store."""
        if not self.vector_store:
            return False
        
        try:
            self.vector_store._collection.delete(ids=[doc_id])
            logger.info("Document deleted from vector store", doc_id=doc_id)
            return True
        except Exception as e:
            logger.error("Failed to delete document", doc_id=doc_id, error=str(e))
            return False
    
    def is_available(self) -> bool:
        """Check if vector store is available and ready."""
        return self.vector_store is not None and self.embeddings is not None

