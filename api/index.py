#!/usr/bin/env python3
"""
Local FastAPI backend for development.
This provides a local server for frontend development while maintaining
the Vercel serverless function for production deployment.
"""

import os
import sys
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import backend components
from src.backend.chain.rag_pipeline_supabase import RAGPipelineSupabase

app = FastAPI(title="Thinkubator RAG API", version="1.0.0")

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    chunks: List[Dict[str, Any]]
    session_id: Optional[str] = None
    processing_time_ms: int

# Initialize RAG pipeline (cached)
rag_pipeline = None

def get_rag_pipeline():
    """Get or initialize the RAG pipeline."""
    global rag_pipeline
    
    if rag_pipeline is None:
        try:
            rag_pipeline = RAGPipelineSupabase()
            print("✅ RAG pipeline initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize RAG pipeline: {e}")
            raise HTTPException(status_code=500, detail=f"Pipeline initialization failed: {str(e)}")
    
    return rag_pipeline

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Thinkubator RAG API is running",
        "version": "1.0.0",
        "environment": "local_development"
    }

@app.get("/health")
async def health_check():
    """Detailed health check."""
    try:
        pipeline = get_rag_pipeline()
        return {
            "status": "healthy",
            "message": "All systems operational",
            "pipeline": "initialized",
            "environment": "local_development"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": str(e),
            "environment": "local_development"
        }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a RAG query."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    start_time = time.time()
    
    try:
        # Get RAG pipeline
        pipeline = get_rag_pipeline()
        
        # Process the query using the RAG pipeline
        # First retrieve relevant chunks
        chunks = pipeline.retrieve(request.query, n_results=5)
        
        # Generate answer using retrieved chunks
        answer = pipeline.generate_answer(request.query, top_k_chunks=5)
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Format chunks to match expected structure
        formatted_chunks = []
        for chunk in chunks:
            formatted_chunks.append({
                "content": chunk.get("document", ""),
                "metadata": chunk.get("metadata", {})
            })
        
        # Format response to match Vercel function format
        return QueryResponse(
            answer=answer,
            chunks=formatted_chunks,
            session_id=None,  # TODO: Implement session storage
            processing_time_ms=processing_time_ms
        )
        
    except Exception as e:
        processing_time_ms = int((time.time() - start_time) * 1000)
        print(f"Query processing error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Query processing failed: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Thinkubator RAG API...")
    print("📍 URL: http://localhost:8000")
    print("📍 Docs: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    
    uvicorn.run(
        "api.index:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
