#!/usr/bin/env python3
"""
Query storage service for storing user queries, answers, and metadata in Supabase.
This tracks all interactions with the RAG system for analytics and improvements.
"""

import os
import logging
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class QuerySession:
    """Represents a complete query session with query, answer, and chunks."""
    id: str
    query: str
    answer: str
    chunks: List[Dict[str, Any]]
    processing_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class QueryStorageService:
    """
    Service for storing and retrieving query sessions in Supabase.
    Creates a complete audit trail of all RAG interactions.
    """
    
    def __init__(self, table_name: str = "query_sessions"):
        """
        Initialize the query storage service.
        
        Args:
            table_name: Name of the table to store query sessions
        """
        self.table_name = table_name
        
        # Initialize Supabase client
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize direct PostgreSQL connection
        self.postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
        if not self.postgres_url:
            raise ValueError("POSTGRES_URL_NON_POOLING must be set")
        
        # Initialize the database
        self._setup_database()
    
    def _get_postgres_connection(self):
        """Get a direct PostgreSQL connection."""
        return psycopg2.connect(
            self.postgres_url,
            cursor_factory=RealDictCursor
        )
    
    def _setup_database(self):
        """Set up the database table for storing query sessions."""
        try:
            with self._get_postgres_connection() as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    
                    # Create the query sessions table
                    logger.info(f"Creating {self.table_name} table...")
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            id TEXT PRIMARY KEY,
                            query TEXT NOT NULL,
                            answer TEXT NOT NULL,
                            chunks JSONB NOT NULL DEFAULT '[]',
                            processing_time_ms INTEGER,
                            metadata JSONB DEFAULT '{{}}',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """)
                    
                    # Create indexes for better query performance
                    logger.info("Creating indexes for query sessions table...")
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {self.table_name}_created_at_idx 
                        ON {self.table_name} (created_at DESC);
                    """)
                    
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {self.table_name}_query_idx 
                        ON {self.table_name} USING GIN (to_tsvector('english', query));
                    """)
                    
                    logger.info("Query storage database setup completed successfully")
                    
        except Exception as e:
            logger.error(f"Failed to set up query storage database: {e}")
            raise
    
    def store_query_session(self, 
                           query: str, 
                           answer: str, 
                           chunks: List[Dict[str, Any]],
                           processing_time_ms: Optional[int] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a complete query session in Supabase.
        
        Args:
            query: The user's query
            answer: The generated answer
            chunks: List of retrieved document chunks with metadata
            processing_time_ms: Time taken to process the query in milliseconds
            metadata: Additional metadata about the session
            
        Returns:
            The session ID
        """
        session_id = str(uuid.uuid4())
        
        if metadata is None:
            metadata = {}
        
        # Add some automatic metadata
        metadata.update({
            "num_chunks": len(chunks),
            "query_length": len(query),
            "answer_length": len(answer),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        try:
            with self._get_postgres_connection() as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    
                    cursor.execute(f"""
                        INSERT INTO {self.table_name} 
                        (id, query, answer, chunks, processing_time_ms, metadata)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        session_id,
                        query,
                        answer,
                        json.dumps(chunks),
                        processing_time_ms,
                        json.dumps(metadata)
                    ))
                    
                    logger.info(f"Successfully stored query session {session_id}")
                    return session_id
                    
        except Exception as e:
            logger.error(f"Failed to store query session: {e}")
            raise
    
    def get_query_session(self, session_id: str) -> Optional[QuerySession]:
        """
        Retrieve a query session by ID.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            QuerySession object if found, None otherwise
        """
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT id, query, answer, chunks, processing_time_ms, metadata, created_at
                        FROM {self.table_name}
                        WHERE id = %s
                    """, [session_id])
                    
                    row = cursor.fetchone()
                    if row:
                        return QuerySession(
                            id=row['id'],
                            query=row['query'],
                            answer=row['answer'],
                            chunks=row['chunks'] or [],
                            processing_time_ms=row['processing_time_ms'],
                            created_at=row['created_at'],
                            metadata=row['metadata'] or {}
                        )
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get query session: {e}")
            raise
    
    def get_recent_query_sessions(self, limit: int = 10) -> List[QuerySession]:
        """
        Get recent query sessions.
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of QuerySession objects
        """
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT id, query, answer, chunks, processing_time_ms, metadata, created_at
                        FROM {self.table_name}
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, [limit])
                    
                    rows = cursor.fetchall()
                    sessions = []
                    
                    for row in rows:
                        sessions.append(QuerySession(
                            id=row['id'],
                            query=row['query'],
                            answer=row['answer'],
                            chunks=row['chunks'] or [],
                            processing_time_ms=row['processing_time_ms'],
                            created_at=row['created_at'],
                            metadata=row['metadata'] or {}
                        ))
                    
                    return sessions
                    
        except Exception as e:
            logger.error(f"Failed to get recent query sessions: {e}")
            raise
    
    def search_query_sessions(self, search_query: str, limit: int = 10) -> List[QuerySession]:
        """
        Search query sessions by query text.
        
        Args:
            search_query: Text to search for in queries
            limit: Maximum number of sessions to return
            
        Returns:
            List of matching QuerySession objects
        """
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT id, query, answer, chunks, processing_time_ms, metadata, created_at
                        FROM {self.table_name}
                        WHERE to_tsvector('english', query) @@ plainto_tsquery('english', %s)
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, [search_query, limit])
                    
                    rows = cursor.fetchall()
                    sessions = []
                    
                    for row in rows:
                        sessions.append(QuerySession(
                            id=row['id'],
                            query=row['query'],
                            answer=row['answer'],
                            chunks=row['chunks'] or [],
                            processing_time_ms=row['processing_time_ms'],
                            created_at=row['created_at'],
                            metadata=row['metadata'] or {}
                        ))
                    
                    return sessions
                    
        except Exception as e:
            logger.error(f"Failed to search query sessions: {e}")
            raise
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored queries.
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT 
                            COUNT(*) as total_sessions,
                            AVG(processing_time_ms) as avg_processing_time,
                            MAX(created_at) as last_query_time,
                            MIN(created_at) as first_query_time
                        FROM {self.table_name}
                    """)
                    
                    result = cursor.fetchone()
                    
                    return {
                        "table_name": self.table_name,
                        "total_sessions": result['total_sessions'] if result else 0,
                        "avg_processing_time_ms": float(result['avg_processing_time']) if result and result['avg_processing_time'] else 0,
                        "last_query_time": result['last_query_time'].isoformat() if result and result['last_query_time'] else None,
                        "first_query_time": result['first_query_time'].isoformat() if result and result['first_query_time'] else None
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            raise
