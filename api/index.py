#!/usr/bin/env python3
"""
FastAPI wrapper for the RAG pipeline that works with Vercel serverless functions.
This provides API endpoints that can be consumed by a frontend framework.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import json

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import your RAG pipeline (updated to use Supabase)
from src.backend.chain.rag_pipeline_supabase import RAGPipelineSupabase

app = FastAPI(title="Thinkubator RAG API", version="1.0.0")

# Initialize the RAG pipeline (this will be cached across requests)
rag_pipeline = None

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    chunks: List[Dict[str, Any]]

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
    try:
        pipeline = get_rag_pipeline()
        
        # Retrieve chunks
        retrieved_chunks = pipeline.retrieve(request.query)
        
        # Generate answer
        answer = pipeline.generate_answer(request.query)
        
        # Format chunks for response
        formatted_chunks = []
        for chunk_info in retrieved_chunks:
            formatted_chunks.append({
                "document": chunk_info['document'],
                "metadata": chunk_info['metadata']
            })
        
        return QueryResponse(
            answer=answer,
            chunks=formatted_chunks
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

# For Vercel, we need to export the app
def handler(request, context):
    """Vercel serverless function handler."""
    from mangum import Mangum
    
    asgi_handler = Mangum(app)
    return asgi_handler(request, context)
