#!/usr/bin/env python3
"""
FastAPI wrapper for the RAG pipeline that works with Vercel serverless functions.
This provides API endpoints that can be consumed by a frontend framework.
"""

import os
import sys
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import your RAG pipeline and storage (updated to use Supabase)
from src.backend.chain.rag_pipeline_supabase import RAGPipelineSupabase
from src.backend.storage.query_storage import QueryStorageService

app = FastAPI(title="Thinkubator RAG API", version="1.0.0")

# Initialize the RAG pipeline and query storage (this will be cached across requests)
rag_pipeline = None
query_storage = None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    chunks: List[Dict[str, Any]]
    session_id: Optional[str] = None
    processing_time_ms: Optional[int] = None

class SessionResponse(BaseModel):
    session_id: str
    query: str
    answer: str
    chunks: List[Dict[str, Any]]
    created_at: str
    processing_time_ms: Optional[int] = None

def get_rag_pipeline():
    """Get or initialize the RAG pipeline."""
    global rag_pipeline
    
    if rag_pipeline is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        
        try:
            rag_pipeline = RAGPipelineSupabase(api_key=api_key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize RAG pipeline: {str(e)}")
    
    return rag_pipeline

def get_query_storage():
    """Get or initialize the query storage service."""
    global query_storage
    
    if query_storage is None:
        try:
            query_storage = QueryStorageService()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to initialize query storage: {str(e)}")
    
    return query_storage

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Thinkubator RAG API is running"}

@app.get("/health")
async def health():
    """Health check with pipeline status."""
    try:
        pipeline = get_rag_pipeline()
        return {"status": "healthy", "pipeline_initialized": True}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the RAG pipeline and return the answer with supporting chunks."""
    start_time = time.time()
    session_id = None
    
    try:
        pipeline = get_rag_pipeline()
        storage = get_query_storage()
        
        # Retrieve chunks
        retrieved_chunks = pipeline.retrieve(request.query)
        
        # Generate answer
        answer = pipeline.generate_answer(request.query)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Format chunks for response
        formatted_chunks = []
        for chunk_info in retrieved_chunks:
            formatted_chunks.append({
                "document": chunk_info['document'],
                "metadata": chunk_info['metadata']
            })
        
        # Store the query session in Supabase
        try:
            session_id = storage.store_query_session(
                query=request.query,
                answer=answer,
                chunks=formatted_chunks,
                processing_time_ms=processing_time_ms,
                metadata={
                    "num_retrieved_chunks": len(retrieved_chunks),
                    "pipeline_info": pipeline.get_pipeline_info()
                }
            )
        except Exception as storage_error:
            # Log storage error but don't fail the request
            print(f"Warning: Failed to store query session: {storage_error}")
        
        return QueryResponse(
            answer=answer,
            chunks=formatted_chunks,
            session_id=session_id,
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.get("/chunks/{query}")
async def get_chunks(query: str):
    """Get only the retrieved chunks for a query (useful for debugging)."""
    try:
        pipeline = get_rag_pipeline()
        chunks = pipeline.retrieve(query)
        
        return {
            "query": query,
            "chunks": [
                {
                    "document": chunk_info['document'],
                    "metadata": chunk_info['metadata']
                }
                for chunk_info in chunks
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunk retrieval failed: {str(e)}")

@app.get("/sessions/recent", response_model=List[SessionResponse])
async def get_recent_sessions(limit: int = 10):
    """Get recent query sessions."""
    try:
        storage = get_query_storage()
        sessions = storage.get_recent_query_sessions(limit=limit)
        
        return [
            SessionResponse(
                session_id=session.id,
                query=session.query,
                answer=session.answer,
                chunks=session.chunks,
                created_at=session.created_at.isoformat() if session.created_at else "",
                processing_time_ms=session.processing_time_ms
            )
            for session in sessions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent sessions: {str(e)}")

@app.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a specific query session by ID."""
    try:
        storage = get_query_storage()
        session = storage.get_query_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            session_id=session.id,
            query=session.query,
            answer=session.answer,
            chunks=session.chunks,
            created_at=session.created_at.isoformat() if session.created_at else "",
            processing_time_ms=session.processing_time_ms
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@app.get("/sessions/search/{search_query}", response_model=List[SessionResponse])
async def search_sessions(search_query: str, limit: int = 10):
    """Search query sessions by query text."""
    try:
        storage = get_query_storage()
        sessions = storage.search_query_sessions(search_query, limit=limit)
        
        return [
            SessionResponse(
                session_id=session.id,
                query=session.query,
                answer=session.answer,
                chunks=session.chunks,
                created_at=session.created_at.isoformat() if session.created_at else "",
                processing_time_ms=session.processing_time_ms
            )
            for session in sessions
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search sessions: {str(e)}")

@app.get("/stats")
async def get_stats():
    """Get statistics about the system."""
    try:
        pipeline = get_rag_pipeline()
        storage = get_query_storage()
        
        pipeline_info = pipeline.get_pipeline_info()
        storage_stats = storage.get_storage_stats()
        
        return {
            "pipeline": pipeline_info,
            "storage": storage_stats,
            "system_status": "healthy"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

# For Vercel, we need to export the app
def handler(request, context):
    """Vercel serverless function handler."""
    from mangum import Mangum
    
    asgi_handler = Mangum(app)
    return asgi_handler(request, context)
