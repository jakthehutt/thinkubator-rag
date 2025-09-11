#!/usr/bin/env python3
"""
FastAPI application for the RAG backend service.
"""

import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.backend.api.unified_handler import UnifiedRAGHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global handler instance
rag_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    global rag_handler
    logger.info("🚀 Starting RAG Backend Service...")
    
    # Initialize RAG handler
    try:
        rag_handler = UnifiedRAGHandler()
        logger.info("✅ RAG pipeline initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG pipeline: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("🔄 Shutting down RAG Backend Service...")

# Create FastAPI app
app = FastAPI(
    title="Thinkubator RAG API",
    description="RAG (Retrieval-Augmented Generation) API for circular economy research",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",  # Frontend (host)
        "http://frontend:3000",   # Frontend (Docker internal)
        "http://localhost:3000",  # Fallback
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    max_chunks: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    chunks: List[Dict[str, Any]]
    processing_time_ms: int
    session_id: Optional[str] = None

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    global rag_handler
    
    status = {
        "status": "healthy",
        "service": "rag-backend",
        "pipeline_initialized": rag_handler is not None and rag_handler.rag_pipeline is not None
    }
    
    if not status["pipeline_initialized"]:
        status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    return status

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a RAG query."""
    global rag_handler
    
    if not rag_handler:
        raise HTTPException(status_code=503, detail="RAG handler not initialized")
    
    try:
        # Process query using unified handler
        response = rag_handler.process_query(request.query)
        
        # Parse the response (unified handler returns dict with statusCode, body, etc.)
        if response.get("statusCode") != 200:
            error_detail = "Failed to process query"
            if "body" in response:
                import json
                try:
                    body = json.loads(response["body"])
                    error_detail = body.get("detail", error_detail)
                except:
                    pass
            raise HTTPException(status_code=response.get("statusCode", 500), detail=error_detail)
        
        # Extract data from response body
        import json
        body_data = json.loads(response["body"])
        
        return QueryResponse(
            answer=body_data["answer"],
            chunks=body_data["chunks"],
            processing_time_ms=body_data["processing_time_ms"],
            session_id=body_data.get("session_id")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/info")
async def get_system_info():
    """Get system information."""
    global rag_handler
    
    if not rag_handler or not rag_handler.rag_pipeline:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    
    try:
        info = rag_handler.rag_pipeline.get_pipeline_info()
        return {"system_info": info}
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get system info: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development",
        log_level="info"
    )
