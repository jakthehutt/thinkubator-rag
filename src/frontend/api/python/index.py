#!/usr/bin/env python3
"""
Vercel Python serverless function with direct RAG implementation.
This function implements the RAG pipeline directly to avoid external dependencies.
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

def search_supabase(query_embedding, k=5):
    """Search Supabase using direct HTTP calls."""
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            raise Exception("Supabase credentials not configured")
        
        # Use the match_documents RPC function
        url = f"{supabase_url}/rest/v1/rpc/match_documents"
        
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query_embedding": query_embedding,
            "match_threshold": 0.5,
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

def generate_answer(query, retrieved_chunks):
    """Generate answer using direct Google AI API call."""
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
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
        print("=====================================")
        
        if method == 'GET':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "message": "Thinkubator RAG Vercel Python Function is running",
                    "path": path
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
                # Generate query embedding
                print(f"🔍 Generating embedding for query: {query}")
                query_embedding = generate_embedding(query)
                
                # Retrieve similar documents
                print(f"📚 Searching Supabase database...")
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
                print(f"🤖 Generating answer...")
                answer = generate_answer(query, similar_docs)
                
                # Calculate processing time
                processing_time_ms = int((time.time() - start_time) * 1000)
                
                print(f"✅ RAG pipeline completed in {processing_time_ms}ms")
                
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({
                        "answer": answer,
                        "chunks": similar_docs,
                        "session_id": None,
                        "processing_time_ms": processing_time_ms
                    })
                }
                
            except Exception as e:
                processing_time_ms = int((time.time() - start_time) * 1000)
                print(f"❌ RAG pipeline error: {e}")
                
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
