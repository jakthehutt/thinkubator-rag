#!/usr/bin/env python3
"""
Minimal Vercel Python serverless function for the RAG pipeline.
Optimized to stay under 250MB size limit.
"""

import os
import sys
import json
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import only essential modules
from src.backend.vector_store.supabase_vector_store import SupabaseVectorStore
from src.backend.storage.query_storage import QueryStorageService

# Initialize components (this will be cached across requests)
vector_store = None
query_storage = None

def get_vector_store():
    """Get or initialize the vector store."""
    global vector_store
    
    if vector_store is None:
        try:
            vector_store = SupabaseVectorStore()
        except Exception as e:
            raise Exception(f"Failed to initialize vector store: {str(e)}")
    
    return vector_store

def get_query_storage():
    """Get or initialize the query storage service."""
    global query_storage
    
    if query_storage is None:
        try:
            query_storage = QueryStorageService()
        except Exception as e:
            raise Exception(f"Failed to initialize query storage: {str(e)}")
    
    return query_storage

def generate_embedding(text):
    """Generate embedding using Google Generative AI."""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=api_key)
        
        # Use the embedding model
        model = genai.EmbeddingModel('models/embedding-001')
        result = model.embed_content(text)
        return result['embedding']
        
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {str(e)}")

def generate_answer(query, retrieved_chunks):
    """Generate answer using Google Generative AI."""
    try:
        import google.generativeai as genai
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=api_key)
        
        # Prepare context from retrieved chunks
        context = "\n\n".join([chunk['document'] for chunk in retrieved_chunks])
        
        # Create prompt
        prompt = f"""Based on the following context about circular economy and sustainability, please answer the question: {query}

Context:
{context}

Please provide a comprehensive answer based on the context provided. If the context doesn't contain enough information to answer the question, please say so."""
        
        # Generate response
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        return response.text
        
    except Exception as e:
        raise Exception(f"Failed to generate answer: {str(e)}")

def handler(request, context):
    """Vercel serverless function handler."""
    
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
                    # Get components
                    vector_store = get_vector_store()
                    storage = get_query_storage()
                    
                    # Generate query embedding
                    query_embedding = generate_embedding(query)
                    
                    # Retrieve similar documents
                    similar_docs = vector_store.similarity_search(query_embedding, k=5)
                    
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
                    
                    # Format chunks for response
                    formatted_chunks = []
                    for doc in similar_docs:
                        formatted_chunks.append({
                            "document": doc.content,
                            "metadata": doc.metadata
                        })
                    
                    # Generate answer
                    answer = generate_answer(query, formatted_chunks)
                    
                    # Calculate processing time
                    processing_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Store the query session in Supabase
                    try:
                        session_id = storage.store_query_session(
                            query=query,
                            answer=answer,
                            chunks=formatted_chunks,
                            processing_time_ms=processing_time_ms,
                            metadata={
                                "num_retrieved_chunks": len(similar_docs),
                                "pipeline_info": "minimal_vercel_function"
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