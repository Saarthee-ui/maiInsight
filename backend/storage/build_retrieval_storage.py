"""Storage for Build Retrieval data."""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class BuildRetrievalStorage:
    """Storage for build retrieval data."""
    
    def __init__(self, db_path: str = "./storage/build_retrieval.db"):
        """Initialize storage."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS build_retrievals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                intent TEXT NOT NULL,
                databases TEXT NOT NULL,
                transformation_name TEXT NOT NULL,
                transformation_name_sanitized TEXT NOT NULL,
                connection_details TEXT,
                use_existing_connection INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)
        
        # Create buildCaptureTable for storing confirmed builds
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buildCaptureTable (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                SessionID TEXT NOT NULL,
                UserID TEXT,
                TimeStamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                LockStatus TEXT DEFAULT 'unlocked',
                DatabaseName TEXT,
                ConnectionURL TEXT,
                ConnectionUsername TEXT,
                ConnectionPassword TEXT,
                ConnectionPort TEXT,
                OrganizationName TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Build retrieval database initialized", path=str(self.db_path))
    
    def save_build(self, build_data: Dict, store_in_vector: bool = True) -> int:
        """
        Save build retrieval data.
        
        Args:
            build_data: Dictionary with build information
            
        Returns:
            ID of saved build
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        databases_json = json.dumps(build_data.get("databases", []))
        connection_json = json.dumps(build_data.get("connection_details", {}))
        
        cursor.execute("""
            INSERT INTO build_retrievals 
            (intent, databases, transformation_name, transformation_name_sanitized, 
             connection_details, use_existing_connection, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            build_data.get("intent", ""),
            databases_json,
            build_data.get("transformation_name", ""),
            build_data.get("transformation_name_sanitized", ""),
            connection_json,
            1 if build_data.get("use_existing_connection", False) else 0,
            "completed"
        ))
        
        build_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Store in vector store if enabled
        if store_in_vector:
            try:
                from storage.build_vector_store import BuildVectorStore
                vector_store = BuildVectorStore()
                if vector_store.is_available():
                    vector_store.store_build(build_id, build_data)
                    logger.info("Build stored in vector store", build_id=build_id)
            except Exception as e:
                logger.warning("Failed to store build in vector store", error=str(e), build_id=build_id)
        
        logger.info("Build retrieval saved", build_id=build_id, transformation=build_data.get("transformation_name"))
        return build_id
    
    def get_build(self, build_id: int) -> Optional[Dict]:
        """Get build by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM build_retrievals WHERE id = ?", (build_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def list_builds(self, limit: int = 50) -> List[Dict]:
        """List all builds."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM build_retrievals 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """Convert database row to dictionary."""
        return {
            "id": row["id"],
            "intent": row["intent"],
            "databases": json.loads(row["databases"]),
            "transformation_name": row["transformation_name"],
            "transformation_name_sanitized": row["transformation_name_sanitized"],
            "connection_details": json.loads(row["connection_details"] or "{}"),
            "use_existing_connection": bool(row["use_existing_connection"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "status": row["status"]
        }
    
    def save_to_build_capture_table(
        self,
        session_id: str,
        build_data: Dict,
        user_id: Optional[str] = None,
        organization_name: Optional[str] = None,
        lock_status: str = "unlocked"
    ) -> int:
        """
        Save build data to buildCaptureTable when user confirms/satisfied.
        
        Args:
            session_id: Session identifier
            build_data: Dictionary with build information
            user_id: Optional user ID
            organization_name: Optional organization name
            lock_status: Lock status (default: "unlocked")
            
        Returns:
            ID of saved record
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract connection details
        connection_details = build_data.get("connection_details", {})
        if isinstance(connection_details, str):
            try:
                connection_details = json.loads(connection_details)
            except:
                connection_details = {}
        
        # Get database names (comma-separated)
        databases = build_data.get("databases", [])
        if isinstance(databases, str):
            try:
                databases = json.loads(databases)
            except:
                databases = [databases] if databases else []
        database_name = ", ".join(databases) if databases else ""
        
        # Extract connection information
        connection_url = connection_details.get("host") or connection_details.get("url") or connection_details.get("connection_url") or ""
        connection_username = connection_details.get("user") or connection_details.get("username") or connection_details.get("user_name") or ""
        connection_password = connection_details.get("password") or connection_details.get("pwd") or ""
        connection_port = str(connection_details.get("port") or connection_details.get("connection_port") or "")
        
        cursor.execute("""
            INSERT INTO buildCaptureTable 
            (SessionID, UserID, TimeStamp, LockStatus, DatabaseName, 
             ConnectionURL, ConnectionUsername, ConnectionPassword, ConnectionPort, OrganizationName)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            user_id or "",
            datetime.now().isoformat(),
            lock_status,
            database_name,
            connection_url,
            connection_username,
            connection_password,
            connection_port,
            organization_name or ""
        ))
        
        capture_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info("Build saved to buildCaptureTable", 
                   capture_id=capture_id, 
                   session_id=session_id,
                   user_id=user_id)
        return capture_id


