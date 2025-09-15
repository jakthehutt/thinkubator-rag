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
    
    # Initialize RAG handler (resilient startup)
    try:
        rag_handler = UnifiedRAGHandler()
        logger.info("✅ RAG pipeline initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG pipeline: {e}")
        logger.info("⚠️ Starting in degraded mode - some features may be unavailable")
        rag_handler = None
    
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
    global rag_handler, query_storage
    
    pipeline_ready = rag_handler is not None and rag_handler.rag_pipeline is not None
    storage_ready = query_storage is not None
    
    status = {
        "status": "healthy" if pipeline_ready else "degraded",
        "service": "rag-backend",
        "pipeline_initialized": pipeline_ready,
        "storage_initialized": storage_ready,
        "features": {
            "query_processing": pipeline_ready,
            "chat_history": storage_ready,
            "user_management": True  # Mock user service always works
        }
    }
    
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

# Import user service and storage service for new endpoints
from src.backend.services.user_service import user_service
from src.backend.storage.query_storage import QueryStorageService

# Global query storage instance
query_storage = None

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global query_storage
    try:
        logger.info("🚀 Initializing query storage service...")
        query_storage = QueryStorageService()
        logger.info("✅ Query storage service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize query storage: {e}")
        query_storage = None

@app.get("/user/current")
async def get_current_user():
    """Get current user information."""
    try:
        # For now, return mock user
        user = user_service.get_mock_user()
        return {
            "id": user.id,
            "name": user.full_name,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")

@app.get("/user/current/sessions")
async def get_current_user_sessions(limit: int = 50):
    """Get all query sessions for the current user."""
    global query_storage
    
    try:
        user = user_service.get_mock_user()
        
        # Check if storage is available
        if not query_storage:
            # Try to initialize storage on demand
            try:
                logger.info("🔄 Initializing query storage on demand...")
                query_storage = QueryStorageService()
                logger.info("✅ Query storage initialized on demand")
            except Exception as e:
                logger.error(f"❌ Failed to initialize query storage on demand: {e}")
                # Return empty sessions instead of failing
                logger.info("📄 Returning empty sessions list due to storage unavailability")
                return {
                    "sessions": [],
                    "total": 0,
                    "user_id": user.id,
                    "message": "Chat history temporarily unavailable - storage service offline",
                    "storage_available": False
                }
        
        # Try to get sessions
        sessions = query_storage.get_user_sessions(user.id, limit)
        
        # Format sessions for frontend
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                "id": session.id,
                "query": session.query,
                "answer": session.answer,
                "user_id": session.user_id,
                "user_name": session.user_name,
                "processing_time_ms": session.processing_time_ms,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "chunks_count": len(session.chunks),
                "preview": session.query[:100] + "..." if len(session.query) > 100 else session.query
            })
        
        return {
            "sessions": formatted_sessions,
            "total": len(formatted_sessions),
            "user_id": user.id,
            "storage_available": True
        }
        
    except Exception as e:
        logger.error(f"Error in get_current_user_sessions: {e}")
        # Return empty sessions with error message instead of HTTP error
        try:
            user = user_service.get_mock_user()
            return {
                "sessions": [],
                "total": 0,
                "user_id": user.id,
                "message": f"Chat history temporarily unavailable: {str(e)}",
                "storage_available": False
            }
        except Exception as user_error:
            raise HTTPException(status_code=500, detail=f"Failed to get current user sessions: {str(e)}")

@app.get("/user/{user_id}/sessions")
async def get_user_sessions(user_id: str, limit: int = 50):
    """Get all query sessions for a user."""
    global query_storage
    
    # Initialize storage if not available
    if not query_storage:
        try:
            logger.info("🔄 Initializing query storage on demand...")
            query_storage = QueryStorageService()
            logger.info("✅ Query storage initialized on demand")
        except Exception as e:
            logger.error(f"❌ Failed to initialize query storage on demand: {e}")
            raise HTTPException(status_code=503, detail="Storage service initialization failed")
    
    try:
        sessions = query_storage.get_user_sessions(user_id, limit)
        
        # Format sessions for frontend
        formatted_sessions = []
        for session in sessions:
            formatted_sessions.append({
                "id": session.id,
                "query": session.query,
                "answer": session.answer,
                "user_id": session.user_id,
                "user_name": session.user_name,
                "processing_time_ms": session.processing_time_ms,
                "created_at": session.created_at.isoformat() if session.created_at else None,
                "chunks_count": len(session.chunks),
                "preview": session.query[:100] + "..." if len(session.query) > 100 else session.query
            })
        
        return {
            "sessions": formatted_sessions,
            "total": len(formatted_sessions),
            "user_id": user_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get a specific session by ID."""
    global query_storage
    
    # Initialize storage if not available
    if not query_storage:
        try:
            logger.info("🔄 Initializing query storage on demand...")
            query_storage = QueryStorageService()
            logger.info("✅ Query storage initialized on demand")
        except Exception as e:
            logger.error(f"❌ Failed to initialize query storage on demand: {e}")
            raise HTTPException(status_code=503, detail="Storage service initialization failed")
    
    try:
        session = query_storage.get_query_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "id": session.id,
            "query": session.query,
            "answer": session.answer,
            "chunks": session.chunks,
            "user_id": session.user_id,
            "user_name": session.user_name,
            "processing_time_ms": session.processing_time_ms,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "metadata": session.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a specific session by ID. Only allows deleting user's own sessions."""
    global query_storage
    
    # Initialize storage if not available
    if not query_storage:
        try:
            logger.info("🔄 Initializing query storage on demand...")
            query_storage = QueryStorageService()
            logger.info("✅ Query storage initialized on demand")
        except Exception as e:
            logger.error(f"❌ Failed to initialize query storage on demand: {e}")
            raise HTTPException(status_code=503, detail="Storage service initialization failed")
    
    try:
        # Get current user for security
        user = user_service.get_mock_user()
        
        # Delete session with user_id check for security
        success = query_storage.delete_session(session_id, user_id=user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found or access denied")
        
        logger.info(f"Session {session_id} deleted by user {user.id}")
        
        return {
            "message": "Session deleted successfully",
            "session_id": session_id,
            "deleted_by": user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

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
