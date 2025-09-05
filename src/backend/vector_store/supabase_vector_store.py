#!/usr/bin/env python3
"""
Supabase Vector Store implementation to replace ChromaDB.
Provides vector storage and similarity search using Supabase with pgvector.
"""

import os
import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from supabase import create_client, Client
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class VectorDocument:
    """Document with vector embedding and metadata."""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]
    distance: Optional[float] = None


class SupabaseVectorStore:
    """
    Vector store implementation using Supabase with pgvector extension.
    Provides similar interface to ChromaDB for easy migration.
    """
    
    def __init__(self, 
                 table_name: str = "document_embeddings",
                 embedding_dimension: int = 768):
        """
        Initialize Supabase vector store.
        
        Args:
            table_name: Name of the table to store embeddings
            embedding_dimension: Dimension of the embeddings
        """
        self.table_name = table_name
        self.embedding_dimension = embedding_dimension
        
        # Initialize Supabase client
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Initialize direct PostgreSQL connection for vector operations
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
        """Set up the database with pgvector extension and tables."""
        try:
            with self._get_postgres_connection() as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    
                    # Enable pgvector extension
                    logger.info("Enabling pgvector extension...")
                    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                    
                    # Create the embeddings table
                    logger.info(f"Creating {self.table_name} table...")
                    cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.table_name} (
                            id TEXT PRIMARY KEY,
                            content TEXT NOT NULL,
                            embedding vector({self.embedding_dimension}),
                            metadata JSONB DEFAULT '{{}}',
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                        );
                    """)
                    
                    # Create index for vector similarity search
                    logger.info("Creating vector similarity index...")
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
                        ON {self.table_name} 
                        USING ivfflat (embedding vector_cosine_ops)
                        WITH (lists = 100);
                    """)
                    
                    logger.info("Database setup completed successfully")
                    
        except Exception as e:
            logger.error(f"Failed to set up database: {e}")
            raise
    
    def add_documents(self, 
                     documents: List[str],
                     embeddings: List[List[float]],
                     metadatas: Optional[List[Dict[str, Any]]] = None,
                     ids: Optional[List[str]] = None) -> List[str]:
        """
        Add documents with embeddings to the vector store.
        
        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: List of document IDs (will generate if None)
        
        Returns:
            List of document IDs that were added
        """
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents and embeddings must match")
        
        if metadatas and len(metadatas) != len(documents):
            raise ValueError("Number of metadatas must match number of documents")
        
        if ids and len(ids) != len(documents):
            raise ValueError("Number of IDs must match number of documents")
        
        # Generate IDs if not provided
        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        # Default metadatas if not provided
        if not metadatas:
            metadatas = [{}] * len(documents)
        
        try:
            with self._get_postgres_connection() as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    
                    # Prepare data for batch insert
                    data_to_insert = []
                    for i, (doc, embedding, metadata, doc_id) in enumerate(zip(documents, embeddings, metadatas, ids)):
                        # Validate embedding dimension
                        if len(embedding) != self.embedding_dimension:
                            raise ValueError(f"Embedding dimension mismatch: expected {self.embedding_dimension}, got {len(embedding)}")
                        
                        # Ensure ID is a string (not UUID)
                        data_to_insert.append((
                            str(doc_id),
                            doc,
                            embedding,
                            json.dumps(metadata)
                        ))
                    
                    # Batch insert
                    cursor.executemany(f"""
                        INSERT INTO {self.table_name} (id, content, embedding, metadata)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            content = EXCLUDED.content,
                            embedding = EXCLUDED.embedding,
                            metadata = EXCLUDED.metadata,
                            created_at = NOW()
                    """, data_to_insert)
                    
                    logger.info(f"Successfully added {len(documents)} documents to vector store")
                    return ids
                    
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def similarity_search(self, 
                         query_embedding: List[float],
                         k: int = 10,
                         filter_metadata: Optional[Dict[str, Any]] = None) -> List[VectorDocument]:
        """
        Perform similarity search using vector embeddings.
        
        Args:
            query_embedding: Query vector embedding
            k: Number of similar documents to return
            filter_metadata: Metadata filters to apply
        
        Returns:
            List of similar documents with distances
        """
        if len(query_embedding) != self.embedding_dimension:
            raise ValueError(f"Query embedding dimension mismatch: expected {self.embedding_dimension}, got {len(query_embedding)}")
        
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    
                    # Build the query
                    query = f"""
                        SELECT 
                            id,
                            content,
                            embedding,
                            metadata,
                            embedding <-> %s::vector AS distance
                        FROM {self.table_name}
                    """
                    
                    params = [query_embedding]
                    
                    # Add metadata filters if provided
                    if filter_metadata:
                        conditions = []
                        for key, value in filter_metadata.items():
                            conditions.append(f"metadata->>{repr(key)} = %s")
                            params.append(str(value))
                        
                        query += " WHERE " + " AND ".join(conditions)
                    
                    query += f" ORDER BY embedding <-> %s::vector LIMIT %s"
                    params.extend([query_embedding, k])
                    
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    # Convert results to VectorDocument objects
                    documents = []
                    for row in results:
                        doc = VectorDocument(
                            id=str(row['id']),
                            content=row['content'],
                            embedding=list(row['embedding']),
                            metadata=row['metadata'] or {},
                            distance=float(row['distance'])
                        )
                        documents.append(doc)
                    
                    logger.info(f"Found {len(documents)} similar documents")
                    return documents
                    
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {e}")
            raise
    
    def get_document_by_id(self, doc_id: str) -> Optional[VectorDocument]:
        """
        Retrieve a document by its ID.
        
        Args:
            doc_id: Document ID
        
        Returns:
            VectorDocument if found, None otherwise
        """
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT id, content, embedding, metadata
                        FROM {self.table_name}
                        WHERE id = %s
                    """, [doc_id])
                    
                    row = cursor.fetchone()
                    if row:
                        return VectorDocument(
                            id=str(row['id']),
                            content=row['content'],
                            embedding=list(row['embedding']),
                            metadata=row['metadata'] or {}
                        )
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get document by ID: {e}")
            raise
    
    def delete_documents(self, ids: List[str]) -> int:
        """
        Delete documents by their IDs.
        
        Args:
            ids: List of document IDs to delete
        
        Returns:
            Number of documents deleted
        """
        try:
            with self._get_postgres_connection() as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        DELETE FROM {self.table_name}
                        WHERE id = ANY(%s)
                    """, [ids])
                    
                    deleted_count = cursor.rowcount
                    logger.info(f"Deleted {deleted_count} documents")
                    return deleted_count
                    
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the collection/table.
        
        Returns:
            Dictionary with collection information
        """
        try:
            with self._get_postgres_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(f"""
                        SELECT COUNT(*) as total_documents
                        FROM {self.table_name}
                    """)
                    
                    result = cursor.fetchone()
                    
                    return {
                        "table_name": self.table_name,
                        "embedding_dimension": self.embedding_dimension,
                        "total_documents": result['total_documents'] if result else 0
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            raise
    
    def clear_collection(self):
        """
        Clear all documents from the collection.
        WARNING: This will delete all data!
        """
        try:
            with self._get_postgres_connection() as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    cursor.execute(f"TRUNCATE TABLE {self.table_name}")
                    logger.info("Collection cleared successfully")
                    
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise
