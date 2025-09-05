#!/usr/bin/env python3
"""
Ultra-minimal Vercel Python serverless function for the RAG pipeline.
Uses direct HTTP calls instead of heavy SDKs to stay under 250MB limit.
"""

import os
import json
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_embedding(text):
    """Generate embedding using direct Google AI API call."""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={api_key}"
        
        payload = {
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result['embedding']['values']
        
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")

def generate_answer(query, retrieved_chunks):
    """Generate answer using direct Google AI API call."""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        # Prepare context from retrieved chunks
        context = "\n\n".join([chunk['content'] for chunk in retrieved_chunks])
        
        # Create prompt
        prompt = f"""Based on the following context about circular economy and sustainability, please answer the question: {query}

Context:
{context}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to answer the question, please say so."""
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        result = response.json()
        return result['candidates'][0]['content']['parts'][0]['text']
        
    except Exception as e:
        raise Exception(f"Failed to generate answer: {str(e)}")

def search_supabase(query_embedding, k=5):
    """Search Supabase using direct HTTP calls."""
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise Exception("Supabase credentials not configured")
        
        # Convert embedding to string format for Supabase
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        url = f"{supabase_url}/rest/v1/rpc/match_documents"
        
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query_embedding": embedding_str,
            "match_threshold": 0.7,
            "match_count": k
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        results = response.json()
        
        # Format results to match expected structure
        formatted_results = []
        for result in results:
            formatted_results.append({
                "content": result.get("content", ""),
                "metadata": result.get("metadata", {})
            })
        
        return formatted_results
        
    except Exception as e:
        raise Exception(f"Failed to search Supabase: {str(e)}")

def store_query_session(query, answer, chunks, processing_time_ms):
    """Store query session in Supabase using direct HTTP calls."""
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            return None  # Don't fail if storage is not available
        
        url = f"{supabase_url}/rest/v1/query_sessions"
        
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "answer": answer,
            "chunks": json.dumps(chunks),
            "processing_time_ms": processing_time_ms,
            "metadata": json.dumps({
                "num_retrieved_chunks": len(chunks),
                "pipeline_info": "ultra_minimal_vercel_function"
            })
        }
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        return result[0]['id'] if result else None
        
    except Exception as e:
        print(f"Warning: Failed to store query session: {e}")
        return None

# Standard Vercel Python function handler
def handler(request):
    """Standard Vercel serverless function handler."""
    
    try:
        # Get request method and path
        method = request.get('method', 'GET')
        path = request.get('path', '/')
        
        print(f"=== Python Function Debug ===")
        print(f"Method: {method}")
        print(f"Path: {path}")
        print(f"Request keys: {list(request.keys())}")
        print("=============================")
        
        if method == 'GET':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"message": "Thinkubator RAG Ultra-Minimal Python API is running", "path": path})
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
                # Generate query embedding
                query_embedding = generate_embedding(query)
                
                # Retrieve similar documents
                similar_docs = search_supabase(query_embedding, k=5)
                
                if not similar_docs:
                    return {
                        'statusCode': 200,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({
                            "answer": "I do not have enough information to answer your question. No relevant documents were found.",
                            "chunks": [],
                            "session_id": None,
                            "processing_time_ms": int((time.time() - start_time) * 1000)
                        })
                    }
                
                # Generate answer
                answer = generate_answer(query, similar_docs)
                
                # Calculate processing time
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                # Store the query session
                session_id = store_query_session(query, answer, similar_docs, processing_time_ms)
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        "answer": answer,
                        "chunks": similar_docs,
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