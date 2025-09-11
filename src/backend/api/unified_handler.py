#!/usr/bin/env python3
"""
Unified API handler that works for both FastAPI and Vercel.
This eliminates the dual backend problem by using the same logic everywhere.
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import the unified RAG pipeline
from src.backend.chain.rag_pipeline import RAGPipeline

class UnifiedRAGHandler:
    """Unified RAG handler that works in both FastAPI and Vercel environments."""
    
    def __init__(self):
        self.rag_pipeline = None
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the RAG pipeline."""
        try:
            self.rag_pipeline = RAGPipeline()
            print("✅ RAG pipeline initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize RAG pipeline: {e}")
            self.rag_pipeline = None
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a RAG query and return standardized response."""
        if not query or not query.strip():
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"detail": "Query cannot be empty"})
            }
        
        start_time = time.time()
        
        try:
            if not self.rag_pipeline:
                raise Exception("RAG pipeline not initialized")
            
            # Process the query using the RAG pipeline
            chunks = self.rag_pipeline.retrieve(query, n_results=5)
            answer = self.rag_pipeline.generate_answer(query, top_k_chunks=5)
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Format chunks to match expected structure
            formatted_chunks = []
            for chunk in chunks:
                formatted_chunks.append({
                    "content": chunk.get("document", ""),
                    "metadata": chunk.get("metadata", {})
                })
            
            # Standardized response format
            response_data = {
                "answer": answer,
                "chunks": formatted_chunks,
                "session_id": None,  # TODO: Implement session storage
                "processing_time_ms": processing_time_ms
            }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(response_data)
            }
            
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            print(f"Query processing error: {e}")
            
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "detail": f"Query processing failed: {str(e)}",
                    "processing_time_ms": processing_time_ms
                })
            }

# Global handler instance
rag_handler = UnifiedRAGHandler()

def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming request (works for both FastAPI and Vercel)."""
    
    # Extract method and path
    method = request.get('method', 'GET')
    path = request.get('path', '/')
    
    print(f"=== Unified Handler Debug ===")
    print(f"Method: {method}")
    print(f"Path: {path}")
    print(f"Request keys: {list(request.keys())}")
    print("=============================")
    
    if method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "message": "Thinkubator RAG Unified API is running",
                "path": path,
                "environment": "unified"
            })
        }
    
    elif method == 'POST':
        # Parse request body
        body = request.get('body', '{}')
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"detail": "Invalid JSON in request body"})
                }
        
        query = body.get('query', '')
        return rag_handler.process_query(query)
    
    else:
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"detail": "Method not allowed"})
        }

