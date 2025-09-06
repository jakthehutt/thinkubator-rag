#!/usr/bin/env python3
"""
Ultra-minimal Vercel Python serverless function that proxies to the backend API.
This maintains Vercel compatibility while using the full backend RAG pipeline.
"""

import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Backend API configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

def call_backend_api(query):
    """Call the backend API for RAG processing."""
    try:
        response = requests.post(
            f"{BACKEND_URL}/query",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise Exception(f"Backend API call failed: {str(e)}")

# Standard Vercel Python function handler
def handler(request):
    """Standard Vercel serverless function handler."""
    
    try:
        # Get request method and path
        method = request.get('method', 'GET')
        path = request.get('path', '/')
        
        print(f"=== Vercel Python Function Debug ===")
        print(f"Method: {method}")
        print(f"Path: {path}")
        print(f"Backend URL: {BACKEND_URL}")
        print("=====================================")
        
        if method == 'GET':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "message": "Thinkubator RAG Vercel Python Proxy is running",
                    "path": path,
                    "backend_url": BACKEND_URL
                })
            }
        
        elif method == 'POST':
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
            
            try:
                # Call backend API
                print(f"📡 Calling backend API for query: {query}")
                backend_response = call_backend_api(query)
                
                # Calculate processing time
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Transform response to match expected format
                transformed_response = {
                    "answer": backend_response.get("answer", ""),
                    "chunks": backend_response.get("chunks", []),
                    "session_id": backend_response.get("session_id"),
                    "processing_time_ms": processing_time_ms
                }
                
                print(f"✅ Backend API call completed in {processing_time_ms}ms")
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(transformed_response)
                }
                
            except Exception as e:
                processing_time_ms = int((time.time() - start_time) * 1000)
                print(f"❌ Backend API error: {e}")
                
                # Fallback response
                fallback_response = {
                    "answer": f"I encountered an issue accessing the document database for your query \"{query}\". This appears to be a temporary technical issue. Please try again later or contact support if the problem persists.",
                    "chunks": [],
                    "session_id": None,
                    "processing_time_ms": processing_time_ms,
                    "error_fallback": True
                }
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(fallback_response)
                }
        
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"detail": "Method not allowed"})
            }
    
    except Exception as e:
        print(f"Handler error: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"detail": f"Internal server error: {str(e)}"})
        }