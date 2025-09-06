#!/usr/bin/env python3
"""
Vercel Python serverless function with correct handler format.
"""

import os
import json
import requests
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        print("🔍 [HANDLER] GET request received")
        
        response_data = {
            "message": "Thinkubator RAG Vercel Python Function is running",
            "method": "GET",
            "environment": {
                "node_env": os.environ.get('NODE_ENV', 'not_set'),
                "vercel": os.environ.get('VERCEL', 'not_set'),
                "has_env_vars": {
                    "gemini": bool(os.environ.get('GEMINI_API_KEY')),
                    "supabase_url": bool(os.environ.get('SUPABASE_URL')),
                    "supabase_key": bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY') or os.environ.get('SUPABASE_ANON_KEY'))
                }
            }
        }
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

    def do_POST(self):
        """Handle POST requests."""
        print("=" * 60)
        print("🚀 [HANDLER] Vercel Python Function POST Started")
        print("=" * 60)
        
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            print(f"🔍 [HANDLER] Content-Length: {content_length}")
            print(f"🔍 [HANDLER] Raw body: {post_data}")
            
            # Parse JSON body
            try:
                body = json.loads(post_data.decode('utf-8'))
                query = body.get('query', '')
                print(f"🔍 [HANDLER] Parsed query: '{query}'")
            except json.JSONDecodeError as e:
                print(f"❌ [HANDLER] JSON decode error: {e}")
                self._send_error_response(400, "Invalid JSON in request body")
                return
            
            if not query:
                print("❌ [HANDLER] Empty query")
                self._send_error_response(400, "Query is required")
                return
            
            # Environment diagnostics
            print("🔍 [HANDLER] Environment Variables:")
            print(f"  - NODE_ENV: {os.environ.get('NODE_ENV', 'not_set')}")
            print(f"  - VERCEL: {os.environ.get('VERCEL', 'not_set')}")
            print(f"  - VERCEL_URL: {os.environ.get('VERCEL_URL', 'not_set')}")
            print(f"  - Has GEMINI_API_KEY: {bool(os.environ.get('GEMINI_API_KEY'))}")
            print(f"  - Has SUPABASE_URL: {bool(os.environ.get('SUPABASE_URL'))}")
            print(f"  - Has SUPABASE_SERVICE_ROLE_KEY: {bool(os.environ.get('SUPABASE_SERVICE_ROLE_KEY'))}")
            print(f"  - Has SUPABASE_ANON_KEY: {bool(os.environ.get('SUPABASE_ANON_KEY'))}")
            
            start_time = time.time()
            
            try:
                print("🚀 [HANDLER] Starting RAG pipeline...")
                
                # Generate query embedding
                query_embedding = self.generate_embedding(query)
                
                # Retrieve similar documents
                similar_docs = self.search_supabase(query_embedding, k=5)
                
                if not similar_docs:
                    print("⚠️ [HANDLER] No documents found")
                    response_data = {
                        "answer": "I do not have enough information to answer your question. No relevant documents were found.",
                        "chunks": [],
                        "session_id": None,
                        "processing_time_ms": int((time.time() - start_time) * 1000)
                    }
                    self._send_success_response(response_data)
                    return
                
                # Generate answer
                answer = self.generate_answer(query, similar_docs)
                
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
                self._send_success_response(response_data)
                
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
                self._send_success_response(fallback_response)
                
        except Exception as e:
            print(f"❌ [HANDLER] General error: {str(e)}")
            print(f"❌ [HANDLER] Error type: {type(e).__name__}")
            self._send_error_response(500, f"Internal server error: {str(e)}")
        finally:
            print("🏁 [HANDLER] Function execution completed")
            print("=" * 60)

    def _send_success_response(self, data):
        """Send a successful JSON response."""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _send_error_response(self, status_code, message):
        """Send an error JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error_data = {"detail": message}
        self.wfile.write(json.dumps(error_data).encode())

    def generate_embedding(self, text):
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

    def search_supabase(self, query_embedding, k=5):
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

    def generate_answer(self, query, retrieved_chunks):
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
