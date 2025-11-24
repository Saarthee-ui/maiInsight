"""Vector store for build retrieval using embeddings and RAG."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import structlog

logger = structlog.get_logger()


class BuildVectorStore:
    """Vector store for storing and retrieving build embeddings using RAG."""
    
    def __init__(self, persist_directory: str = "./storage/build_vectors"):
        """Initialize vector store."""
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
                    logger.warning("OpenAI API key not found, vector store will use fallback")
                    self.embeddings = None
                
                # Initialize ChromaDB
                client = chromadb.PersistentClient(
                    path=str(self.persist_directory),
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # Create or get collection
                collection = client.get_or_create_collection(
                    name="build_embeddings",
                    metadata={"description": "Build transformation embeddings"}
                )
                
                # Create LangChain Chroma wrapper
                if self.embeddings:
                    self.vector_store = Chroma(
                        client=client,
                        collection_name="build_embeddings",
                        embedding_function=self.embeddings
                    )
                    logger.info("Vector store initialized with ChromaDB", path=str(self.persist_directory))
                else:
                    logger.warning("Vector store initialized but embeddings not available")
                    
            except ImportError:
                logger.warning("ChromaDB not installed, using fallback storage")
                self.vector_store = None
                self.embeddings = None
                
        except Exception as e:
            logger.warning("Failed to initialize vector store", error=str(e))
            self.vector_store = None
            self.embeddings = None
    
    def _create_build_text(self, build_data: Dict) -> str:
        """Create searchable text from build data."""
        parts = []
        
        if build_data.get("intent"):
            parts.append(f"Intent: {build_data['intent']}")
        
        if build_data.get("transformation_name"):
            parts.append(f"Transformation: {build_data['transformation_name']}")
        
        if build_data.get("databases"):
            databases = build_data["databases"]
            if isinstance(databases, list):
                parts.append(f"Databases: {', '.join(databases)}")
            else:
                parts.append(f"Databases: {databases}")
        
        if build_data.get("tables"):
            tables = build_data["tables"]
            if isinstance(tables, list):
                # Handle list of tuples (database, table)
                table_names = [t[1] if isinstance(t, tuple) else str(t) for t in tables]
                parts.append(f"Tables: {', '.join(table_names)}")
            else:
                parts.append(f"Tables: {tables}")
        
        if build_data.get("transformation_type"):
            parts.append(f"Type: {build_data['transformation_type']}")
        
        return " | ".join(parts)
    
    def store_build(self, build_id: int, build_data: Dict) -> bool:
        """
        Store build in vector store.
        
        Args:
            build_id: Build ID from database
            build_data: Build data dictionary
            
        Returns:
            True if stored successfully, False otherwise
        """
        if not self.vector_store or not self.embeddings:
            logger.warning("Vector store not available, skipping storage")
            return False
        
        try:
            # Create searchable text
            text = self._create_build_text(build_data)
            
            # Create metadata
            metadata = {
                "build_id": str(build_id),
                "intent": build_data.get("intent", ""),
                "transformation_name": build_data.get("transformation_name", ""),
                "transformation_type": build_data.get("transformation_type", ""),
                "databases": json.dumps(build_data.get("databases", [])),
                "created_at": datetime.now().isoformat()
            }
            
            # Store in vector database
            self.vector_store.add_texts(
                texts=[text],
                metadatas=[metadata],
                ids=[f"build_{build_id}"]
            )
            
            logger.info("Build stored in vector store", build_id=build_id)
            return True
            
        except Exception as e:
            logger.error("Failed to store build in vector store", error=str(e), build_id=build_id)
            return False
    
    def search_similar_builds(
        self, 
        query: str, 
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar builds using vector similarity.
        
        Args:
            query: Search query (user intent, keywords, etc.)
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of similar builds with metadata and scores
        """
        if not self.vector_store or not self.embeddings:
            logger.warning("Vector store not available, returning empty results")
            return []
        
        try:
            # Search for similar builds
            results = self.vector_store.similarity_search_with_score(
                query,
                k=top_k
            )
            
            # Format results
            similar_builds = []
            for doc, score in results:
                # Lower score is better in some vector stores, so we normalize
                similarity_score = 1.0 - min(score, 1.0) if score <= 1.0 else 1.0 / (1.0 + score)
                
                if similarity_score >= min_score:
                    metadata = doc.metadata
                    similar_builds.append({
                        "build_id": int(metadata.get("build_id", 0)),
                        "intent": metadata.get("intent", ""),
                        "transformation_name": metadata.get("transformation_name", ""),
                        "transformation_type": metadata.get("transformation_type", ""),
                        "databases": json.loads(metadata.get("databases", "[]")),
                        "similarity_score": similarity_score,
                        "text": doc.page_content
                    })
            
            logger.info("Found similar builds", count=len(similar_builds), query=query[:50])
            return similar_builds
            
        except Exception as e:
            logger.error("Failed to search vector store", error=str(e))
            return []
    
    def update_build(self, build_id: int, build_data: Dict) -> bool:
        """Update build in vector store."""
        # Delete old and add new
        try:
            if self.vector_store:
                # Try to delete old entry
                try:
                    self.vector_store.delete(ids=[f"build_{build_id}"])
                except:
                    pass  # Ignore if not found
                
                # Add updated entry
                return self.store_build(build_id, build_data)
            return False
        except Exception as e:
            logger.error("Failed to update build in vector store", error=str(e))
            return False
    
    def delete_build(self, build_id: int) -> bool:
        """Delete build from vector store."""
        try:
            if self.vector_store:
                self.vector_store.delete(ids=[f"build_{build_id}"])
                logger.info("Build deleted from vector store", build_id=build_id)
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete build from vector store", error=str(e))
            return False
    
    def is_available(self) -> bool:
        """Check if vector store is available."""
        return self.vector_store is not None and self.embeddings is not None

