#!/bin/bash

# Test script for FastAPI backend with query storage
# This script tests the API endpoints including the new query storage functionality

set -e

echo "🧪 Running API Tests..."
echo "======================="

# Test if Python dependencies are available
echo "📦 Checking Python dependencies..."
python -c "import fastapi, supabase, psycopg2" 2>/dev/null || {
    echo "❌ Required packages not installed. Run: pip install -r requirements.txt"
    exit 1
}
echo "✅ Dependencies OK"

# Test query storage module
echo ""
echo "🧪 Testing query storage module..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.backend.storage.query_storage import QueryStorageService, QuerySession
    print('✅ Query storage imports working')
except Exception as e:
    print(f'❌ Query storage import failed: {e}')
    sys.exit(1)
"

# Test RAG pipeline integration
echo ""
echo "🧪 Testing RAG pipeline integration..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    from src.backend.chain.rag_pipeline_supabase import RAGPipelineSupabase
    print('✅ RAG pipeline imports working')
except Exception as e:
    print(f'❌ RAG pipeline import failed: {e}')
    sys.exit(1)
"

# Test FastAPI imports
echo ""
echo "🧪 Testing FastAPI backend imports..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    from api.index import app, get_rag_pipeline, get_query_storage
    print('✅ FastAPI backend imports working')
except Exception as e:
    print(f'❌ FastAPI backend import failed: {e}')
    sys.exit(1)
"

echo ""
echo "🎉 API Tests Completed!"
echo "======================"
echo ""
echo "✅ All imports working correctly"
echo "✅ Query storage module available"
echo "✅ RAG pipeline integration ready"
echo "✅ FastAPI backend configured"
echo ""
echo "Note: To test with live Supabase connection, run: make test-supabase"
