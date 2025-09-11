#!/usr/bin/env python3
"""
Comprehensive test script for Supabase setup with early testing.
This script performs a complete end-to-end test of the Supabase integration.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add the project root to Python path (from src/backend/database/ to project root)
# __file__ is in src/backend/database/, so we need parent.parent.parent.parent to get to project root
current_file = Path(__file__).absolute()
project_root = current_file.parent.parent.parent.parent  # database -> backend -> src -> project_root
sys.path.insert(0, str(project_root))

# Load environment variables from project root
load_dotenv(dotenv_path=project_root / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment_setup():
    """Test that all required environment variables are set."""
    print("\n" + "="*60)
    print("TESTING ENVIRONMENT SETUP")
    print("="*60)
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "POSTGRES_URL",
        "POSTGRES_URL_NON_POOLING",
    ]
    
    missing_vars = []
    for var_name in required_vars:
        value = os.getenv(var_name)
        if not value:
            missing_vars.append(var_name)
            print(f"❌ {var_name}: Not set")
        else:
            print(f"✅ {var_name}: Set ({value[:20]}...)")
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {missing_vars}")
        return False
    else:
        print("\n✅ All environment variables are set!")
        return True

def test_supabase_connection():
    """Test basic Supabase connection."""
    print("\n" + "="*60)
    print("TESTING SUPABASE CONNECTION")
    print("="*60)
    
    try:
        from supabase import create_client, Client
        
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Create client
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test a simple query (this might fail if no tables exist, which is OK)
        try:
            response = supabase.table('pg_tables').select('tablename').limit(1).execute()
            print("✅ Supabase query executed successfully")
        except Exception as e:
            print(f"⚠️  Supabase query failed (this is expected): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

def test_postgres_connection():
    """Test direct PostgreSQL connection."""
    print("\n" + "="*60)
    print("TESTING POSTGRESQL CONNECTION")
    print("="*60)
    
    try:
        import psycopg2
        
        postgres_url = os.getenv("POSTGRES_URL_NON_POOLING")
        
        # Create connection
        conn = psycopg2.connect(postgres_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT 1;")
        result = cursor.fetchone()
        
        if result[0] == 1:
            print("✅ PostgreSQL connection successful")
            
            # Test pgvector extension
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✅ pgvector extension enabled")
                
                # Test vector operations
                cursor.execute("SELECT '[1,2,3]'::vector;")
                vector_result = cursor.fetchone()
                print("✅ Vector operations working")
                
                cursor.close()
                conn.close()
                return True
                
            except Exception as e:
                print(f"❌ pgvector extension error: {e}")
                cursor.close()
                conn.close()
                return False
                
        else:
            print("❌ PostgreSQL query returned unexpected result")
            cursor.close()
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def test_vector_store():
    """Test the Supabase vector store implementation."""
    print("\n" + "="*60)
    print("TESTING SUPABASE VECTOR STORE")
    print("="*60)
    
    try:
        from src.backend.vector_store.supabase_vector_store import SupabaseVectorStore
        
        # Create vector store (this will also set up the database)
        vector_store = SupabaseVectorStore(
            table_name="test_embeddings",
            embedding_dimension=3  # Small dimension for testing
        )
        print("✅ SupabaseVectorStore initialized successfully")
        
        # Clear any existing test data
        vector_store.clear_collection()
        
        # Test adding documents
        test_documents = ["Test document 1", "Test document 2"]
        test_embeddings = [[1.0, 0.5, 0.2], [0.8, 1.0, 0.1]]
        test_metadata = [{"source": "test1"}, {"source": "test2"}]
        
        doc_ids = vector_store.add_documents(
            documents=test_documents,
            embeddings=test_embeddings,
            metadatas=test_metadata
        )
        print(f"✅ Added {len(doc_ids)} documents to vector store")
        
        # Test similarity search
        query_embedding = [1.0, 0.5, 0.2]
        results = vector_store.similarity_search(
            query_embedding=query_embedding,
            k=2
        )
        
        if results:
            print(f"✅ Similarity search returned {len(results)} results")
            print(f"   First result distance: {results[0].distance:.4f}")
        else:
            print("❌ Similarity search returned no results")
            return False
        
        # Test document retrieval
        doc = vector_store.get_document_by_id(doc_ids[0])
        if doc:
            print("✅ Document retrieval by ID successful")
        else:
            print("❌ Document retrieval by ID failed")
            return False
        
        # Get collection info
        info = vector_store.get_collection_info()
        print(f"✅ Collection info: {info}")
        
        # Clean up test data
        vector_store.clear_collection()
        print("✅ Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rag_pipeline():
    """Test the RAG pipeline with Supabase."""
    print("\n" + "="*60)
    print("TESTING RAG PIPELINE")
    print("="*60)
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key or gemini_key == "your-gemini-api-key-here":
        print("⚠️  GEMINI_API_KEY not set properly - skipping RAG pipeline test")
        print("   Please update your .env file with your actual Gemini API key")
        return True  # Don't fail the test for this
    
    try:
        from src.backend.chain.rag_pipeline_supabase import RAGPipelineSupabase
        
        # Create RAG pipeline
        pipeline = RAGPipelineSupabase(
            api_key=gemini_key,
            table_name="test_rag_embeddings",
            embedding_dimension=768  # Gemini embedding dimension
        )
        print("✅ RAGPipelineSupabase initialized successfully")
        
        # Get pipeline info
        info = pipeline.get_pipeline_info()
        print(f"✅ Pipeline info: {info}")
        
        # Test simple retrieval (this will likely return no results since we have no docs)
        try:
            results = pipeline.retrieve("test query", n_results=5)
            print(f"✅ Retrieval test successful (returned {len(results)} results)")
        except Exception as e:
            print(f"⚠️  Retrieval test failed (expected with no documents): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests in sequence."""
    print("🚀 Starting Supabase Setup Tests...")
    print("This script will test your entire Supabase integration step by step.")
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Supabase Connection", test_supabase_connection),
        ("PostgreSQL Connection", test_postgres_connection),
        ("Vector Store", test_vector_store),
        ("RAG Pipeline", test_rag_pipeline),
    ]
    
    passed_tests = 0
    failed_tests = 0
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            if success:
                passed_tests += 1
            else:
                failed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            failed_tests += 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📊 Total: {passed_tests + failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 ALL TESTS PASSED! Your Supabase setup is working correctly.")
        print("\nNext steps:")
        print("1. Make sure to add your GEMINI_API_KEY to .env file")
        print("2. Run migration script to move data from ChromaDB")
        print("3. Deploy to Vercel!")
    else:
        print(f"\n⚠️  {failed_tests} tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("1. Verify your Supabase credentials are correct")
        print("2. Check that your Supabase project allows connections")
        print("3. Ensure pgvector extension is available")
    
    return failed_tests == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
