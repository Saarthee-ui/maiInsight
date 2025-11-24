"""Document ingestion system for processing RAG documents."""

from pathlib import Path
from typing import List, Dict, Any, Optional
import structlog
from docx import Document as DocxDocument
from storage.document_vector_store import DocumentVectorStore

logger = structlog.get_logger()


class DocumentIngestion:
    """Handles ingestion of RAG documents into vector store."""
    
    def __init__(self, rag_folder: str = "rag_documents", chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize document ingestion.
        
        Args:
            rag_folder: Path to RAG documents folder
            chunk_size: Size of text chunks for embedding (characters)
            chunk_overlap: Overlap between chunks (characters)
        """
        self.rag_folder = Path(rag_folder)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store = DocumentVectorStore()
    
    def read_word_document(self, file_path: Path) -> str:
        """Read content from a Word document."""
        try:
            doc = DocxDocument(file_path)
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text.strip())
            return "\n\n".join(paragraphs)
        except Exception as e:
            logger.error("Failed to read Word document", file_path=str(file_path), error=str(e))
            return ""
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks for embedding.
        
        Args:
            text: Text to chunk
            
        Returns:
            List of text chunks
        """
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at paragraph boundary
            if end < len(text):
                # Look for paragraph break near the end
                last_break = text.rfind("\n\n", start, end)
                if last_break > start:
                    end = last_break + 2
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start with overlap
            start = end - self.chunk_overlap
            if start >= len(text):
                break
        
        return chunks
    
    def get_category_from_path(self, file_path: Path) -> str:
        """Determine document category from file path."""
        path_str = str(file_path)
        if "documentation" in path_str.lower():
            return "documentation"
        elif "schemas" in path_str.lower():
            return "schemas"
        elif "examples" in path_str.lower():
            return "examples"
        elif "rules" in path_str.lower():
            return "rules"
        return "general"
    
    def ingest_document(self, file_path: Path) -> bool:
        """
        Ingest a single document into the vector store.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if successful, False otherwise
        """
        if not file_path.exists():
            logger.warning("Document file not found", file_path=str(file_path))
            return False
        
        # Read document
        if file_path.suffix.lower() == ".docx":
            content = self.read_word_document(file_path)
        elif file_path.suffix.lower() in [".txt", ".md"]:
            content = file_path.read_text(encoding="utf-8")
        else:
            logger.warning("Unsupported file type", file_path=str(file_path), suffix=file_path.suffix)
            return False
        
        if not content:
            logger.warning("Document is empty", file_path=str(file_path))
            return False
        
        # Chunk the content
        chunks = self.chunk_text(content)
        category = self.get_category_from_path(file_path)
        
        # Add each chunk to vector store
        success_count = 0
        for i, chunk in enumerate(chunks):
            doc_id = f"{file_path.stem}_chunk_{i}"
            metadata = {
                "file_path": str(file_path),
                "file_name": file_path.name,
                "category": category,
                "chunk_index": i,
                "total_chunks": len(chunks)
            }
            
            if self.vector_store.add_document(chunk, metadata, doc_id):
                success_count += 1
        
        logger.info("Document ingested", 
                   file_path=str(file_path), 
                   chunks=len(chunks), 
                   successful=success_count)
        return success_count > 0
    
    def ingest_folder(self, folder_path: Optional[Path] = None) -> Dict[str, Any]:
        """
        Ingest all documents from a folder.
        
        Args:
            folder_path: Path to folder (defaults to rag_documents)
            
        Returns:
            Dictionary with ingestion results
        """
        if folder_path is None:
            folder_path = self.rag_folder
        
        if not folder_path.exists():
            logger.warning("RAG folder not found", folder_path=str(folder_path))
            return {"success": False, "message": f"Folder not found: {folder_path}"}
        
        results = {
            "success": True,
            "processed": 0,
            "failed": 0,
            "files": []
        }
        
        # Find all document files
        docx_files = list(folder_path.rglob("*.docx"))
        txt_files = list(folder_path.rglob("*.txt"))
        md_files = list(folder_path.rglob("*.md"))
        
        all_files = docx_files + txt_files + md_files
        
        logger.info("Starting document ingestion", 
                   folder=str(folder_path), 
                   total_files=len(all_files))
        
        for file_path in all_files:
            try:
                if self.ingest_document(file_path):
                    results["processed"] += 1
                    results["files"].append({"file": str(file_path), "status": "success"})
                else:
                    results["failed"] += 1
                    results["files"].append({"file": str(file_path), "status": "failed"})
            except Exception as e:
                logger.error("Error ingesting document", file_path=str(file_path), error=str(e))
                results["failed"] += 1
                results["files"].append({"file": str(file_path), "status": "error", "error": str(e)})
        
        logger.info("Document ingestion complete", 
                   processed=results["processed"], 
                   failed=results["failed"])
        
        return results
    
    def reingest_all(self) -> Dict[str, Any]:
        """Reingest all documents (clears and rebuilds vector store)."""
        logger.info("Starting full reingestion of RAG documents")
        return self.ingest_folder()

