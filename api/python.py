#!/usr/bin/env python3
"""
Vercel Python serverless function for the RAG pipeline.
This is a simplified version that works with Vercel's serverless environment.
"""

import os
import sys
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import your RAG pipeline and storage
from src.backend.chain.rag_pipeline_supabase import RAGPipelineSupabase
from src.backend.storage.query_storage import QueryStorageService

# Initialize the RAG pipeline and query storage (this will be cached across requests)
rag_pipeline = None
query_storage = None

def get_rag_pipeline():
    """Get or initialize the RAG pipeline."""
    global rag_pipeline
    
    if rag_pipeline is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured")
        
        try:
            rag_pipeline = RAGPipelineSupabase(api_key=api_key)
        except Exception as e:
            raise Exception(f"Failed to initialize RAG pipeline: {str(e)}")
    
    return rag_pipeline

def get_query_storage():
    """Get or initialize the query storage service."""
    global query_storage
    
    if query_storage is None:
        try:
            query_storage = QueryStorageService()
        except Exception as e:
            raise Exception(f"Failed to initialize query storage: {str(e)}")
    
    return query_storage

def handler(request, context):
    """Vercel serverless function handler."""
    import time
    
    try:
        # Parse the request
        if request.get('httpMethod') == 'GET':
            path = request.get('path', '')
            if path == '/api/python/health':
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"status": "healthy", "message": "Python API is running"})
                }
            else:
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"message": "Thinkubator RAG Python API is running"})
                }
        
        elif request.get('httpMethod') == 'POST':
            path = request.get('path', '')
            
            if path == '/api/python/query':
                # Parse request body
                body = request.get('body', '{}')
                if isinstance(body, str):
                    body = json.loads(body)
                
                query = body.get('query', '')
                if not query:
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({"detail": "Query is required"})
                    }
                
                start_time = time.time()
                session_id = None
                
                try:
                    pipeline = get_rag_pipeline()
                    storage = get_query_storage()
                    
                    # Retrieve chunks
                    retrieved_chunks = pipeline.retrieve(query)
                    
                    # Generate answer
                    answer = pipeline.generate_answer(query)
                    
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
                            query=query,
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
                    
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            "answer": answer,
                            "chunks": formatted_chunks,
                            "session_id": session_id,
                            "processing_time_ms": processing_time_ms
                        })
                    }
                    
                except Exception as e:
                    return {
                        'statusCode': 500,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({"detail": f"Query processing failed: {str(e)}"})
                    }
            
            else:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"detail": "Endpoint not found"})
                }
        
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"detail": "Method not allowed"})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"detail": f"Internal server error: {str(e)}"})
        }
