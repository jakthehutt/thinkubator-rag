#!/usr/bin/env python3
"""
Vercel Python serverless function with comprehensive logging for debugging.
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
    print(f"🔍 [EMBEDDING] Starting embedding generation for text length: {len(text)}")
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ [EMBEDDING] GEMINI_API_KEY not configured")
            raise Exception("GEMINI_API_KEY not configured")
        
        print(f"✅ [EMBEDDING] API key found (first 10 chars): {api_key[:10]}...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/embedding-001:embedContent?key={api_key}"
        print(f"🔍 [EMBEDDING] API URL: {url[:100]}...")
        
        payload = {
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        print("🔍 [EMBEDDING] Making API request...")
        response = requests.post(url, json=payload)
        print(f"🔍 [EMBEDDING] Response status: {response.status_code}")
        
        response.raise_for_status()
        
        result = response.json()
        embedding = result['embedding']['values']
        print(f"✅ [EMBEDDING] Success! Embedding dimension: {len(embedding)}")
        return embedding
        
    except Exception as e:
        print(f"❌ [EMBEDDING] Error: {str(e)}")
        raise Exception(f"Failed to generate embedding: {str(e)}")

def search_supabase(query_embedding, k=5):
    """Search Supabase using direct HTTP calls."""
    print(f"🔍 [SUPABASE] Starting search for {k} documents...")
    
    try:
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
        
        print(f"🔍 [SUPABASE] URL: {supabase_url}")
        print(f"🔍 [SUPABASE] Has service role key: {bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY'))}")
        print(f"🔍 [SUPABASE] Has anon key: {bool(os.environ.get('SUPABASE_ANON_KEY'))}")
        print(f"🔍 [SUPABASE] Using key (first 10 chars): {supabase_key[:10] if supabase_key else 'None'}...")
        
        if not supabase_url or not supabase_key:
            print("❌ [SUPABASE] Credentials not configured")
            raise Exception("Supabase credentials not configured")
        
        # Use the match_documents RPC function
        url = f"{supabase_url}/rest/v1/rpc/match_documents"
        print(f"🔍 [SUPABASE] RPC URL: {url}")
        
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
        
        print(f"🔍 [SUPABASE] Payload: threshold={payload['match_threshold']}, count={payload['match_count']}")
        print("🔍 [SUPABASE] Making RPC request...")
        
        response = requests.post(url, json=payload, headers=headers)
        print(f"🔍 [SUPABASE] Response status: {response.status_code}")
        
        if response.status_code != 200:
            error_text = response.text
            print(f"❌ [SUPABASE] Error response: {error_text}")
        
        response.raise_for_status()
        
        results = response.json()
        print(f"✅ [SUPABASE] Success! Found {len(results)} documents")
        
        # Format results to match expected structure
        formatted_results = []
        for i, result in enumerate(results):
            doc_name = result.get("metadata", {}).get("document_name", "Unknown")
            print(f"🔍 [SUPABASE] Document {i+1}: {doc_name}")
            formatted_results.append({
                "content": result.get("content", ""),
                "metadata": result.get("metadata", {})
            })
        
        return formatted_results
        
    except Exception as e:
        print(f"❌ [SUPABASE] Error: {str(e)}")
        raise Exception(f"Failed to search Supabase: {str(e)}")

def generate_answer(query, retrieved_chunks):
    """Generate answer using direct Google AI API call."""
    print(f"🔍 [ANSWER] Starting answer generation for {len(retrieved_chunks)} chunks...")
    
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("❌ [ANSWER] GEMINI_API_KEY not configured")
            raise Exception("GEMINI_API_KEY not configured")
        
        print(f"✅ [ANSWER] API key found (first 10 chars): {api_key[:10]}...")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        print(f"🔍 [ANSWER] API URL: {url[:100]}...")
        
        # Prepare context from retrieved chunks
        context = "\n\n".join([chunk['content'] for chunk in retrieved_chunks])
        context_length = len(context)
        print(f"🔍 [ANSWER] Context length: {context_length} characters")
        
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
        
        print("🔍 [ANSWER] Making generation request...")
        response = requests.post(url, json=payload)
        print(f"🔍 [ANSWER] Response status: {response.status_code}")
        
        response.raise_for_status()
        
        result = response.json()
        answer = result['candidates'][0]['content']['parts'][0]['text']
        answer_length = len(answer)
        print(f"✅ [ANSWER] Success! Answer length: {answer_length} characters")
        return answer
        
    except Exception as e:
        print(f"❌ [ANSWER] Error: {str(e)}")
        raise Exception(f"Failed to generate answer: {str(e)}")

# Standard Vercel Python function handler
def handler(request):
    """Standard Vercel serverless function handler."""
    
    print("=" * 60)
    print("🚀 [HANDLER] Vercel Python Function Started")
    print("=" * 60)
    
    try:
        # Get request method and path
        method = request.get('method', 'GET')
        path = request.get('path', '/')
        
        print(f"🔍 [HANDLER] Method: {method}")
        print(f"🔍 [HANDLER] Path: {path}")
        print(f"🔍 [HANDLER] Request keys: {list(request.keys())}")
        
        # Environment diagnostics
        print("🔍 [HANDLER] Environment Variables:")
        print(f"  - NODE_ENV: {os.environ.get('NODE_ENV', 'not_set')}")
        print(f"  - VERCEL: {os.environ.get('VERCEL', 'not_set')}")
        print(f"  - VERCEL_URL: {os.environ.get('VERCEL_URL', 'not_set')}")
        print(f"  - Has GEMINI_API_KEY: {bool(os.environ.get('GEMINI_API_KEY'))}")
        print(f"  - Has SUPABASE_URL: {bool(os.environ.get('SUPABASE_URL'))}")
        print(f"  - Has SUPABASE_SERVICE_ROLE_KEY: {bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY'))}")
        print(f"  - Has SUPABASE_ANON_KEY: {bool(os.environ.get('SUPABASE_ANON_KEY'))}")
        
        if method == 'GET':
            print("✅ [HANDLER] Handling GET request")
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    "message": "Thinkubator RAG Vercel Python Function is running",
                    "path": path,
                    "environment": {
                        "node_env": os.environ.get('NODE_ENV', 'not_set'),
                        "vercel": os.environ.get('VERCEL', 'not_set'),
                        "has_env_vars": {
                            "gemini": bool(os.environ.get('GEMINI_API_KEY')),
                            "supabase_url": bool(os.environ.get('SUPABASE_URL')),
                            "supabase_key": bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY'))
                        }
                    }
                })
            }
        
        elif method == 'POST':
            print("🔍 [HANDLER] Handling POST request")
            
            # Parse request body
            body = request.get('body', '{}')
            print(f"🔍 [HANDLER] Raw body type: {type(body)}")
            print(f"🔍 [HANDLER] Raw body: {str(body)[:100]}...")
            
            if isinstance(body, str):
                body = json.loads(body)
            
            query = body.get('query', '')
            print(f"🔍 [HANDLER] Extracted query: '{query}'")
            
            if not query:
                print("❌ [HANDLER] Empty query")
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({"detail": "Query is required"})
                }
            
            start_time = time.time()
            
            try:
                print("🚀 [HANDLER] Starting RAG pipeline...")
                
                # Generate query embedding
                query_embedding = generate_embedding(query)
                
                # Retrieve similar documents
                similar_docs = search_supabase(query_embedding, k=5)
                
                if not similar_docs:
                    print("⚠️ [HANDLER] No documents found")
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
                
                print(f"✅ [HANDLER] RAG pipeline completed in {processing_time_ms}ms")
                print(f"✅ [HANDLER] Answer length: {len(answer)} characters")
                print(f"✅ [HANDLER] Chunks: {len(similar_docs)}")
                
                response_data = {
                    "answer": answer,
                    "chunks": similar_docs,
                    "session_id": None,
                    "processing_time_ms": processing_time_ms
                }
                
                print("✅ [HANDLER] Returning successful response")
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(response_data)
                }
                
            except Exception as e:
                processing_time_ms = int((time.time() - start_time) * 1000)
                print(f"❌ [HANDLER] RAG pipeline error: {str(e)}")
                print(f"❌ [HANDLER] Error type: {type(e).__name__}")
                
                # Fallback response
                fallback_response = {
                    "answer": f"I encountered an issue accessing the document database for your query \"{query}\". This appears to be a temporary technical issue. Please try again later or contact support if the problem persists.",
                    "chunks": [],
                    "session_id": None,
                    "processing_time_ms": processing_time_ms,
                    "error_fallback": True,
                    "error_details": str(e)
                }
                
                print("🔄 [HANDLER] Returning fallback response")
                return {
                    'statusCode': 200,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps(fallback_response)
                }
        
        else:
            print(f"❌ [HANDLER] Method not allowed: {method}")
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"detail": "Method not allowed"})
            }
    
    except Exception as e:
        print(f"❌ [HANDLER] General error: {str(e)}")
        print(f"❌ [HANDLER] Error type: {type(e).__name__}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"detail": f"Internal server error: {str(e)}"})
        }
    finally:
        print("🏁 [HANDLER] Function execution completed")
        print("=" * 60)
