#!/bin/bash

# Test script for Supabase setup
# This script runs all Supabase-related tests

set -e

echo "🧪 Running Supabase Tests..."
echo "=============================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found! Please create it first."
    exit 1
fi

# Check if required dependencies are installed
echo "📦 Checking dependencies..."
python -c "import supabase, psycopg2, pgvector" 2>/dev/null || {
    echo "❌ Required packages not installed. Run: pip install -r requirements.txt"
    exit 1
}
echo "✅ Dependencies OK"

# Run comprehensive setup test
echo ""
echo "🚀 Running comprehensive Supabase setup test..."
python src/backend/database/test_supabase_setup.py

# Run pytest tests
echo ""
echo "🧪 Running pytest tests..."
python -m pytest src/backend/tests/test_supabase_connection.py -v
echo ""
python -m pytest src/backend/tests/test_supabase_vector_store.py -v

echo ""
echo "🎉 All Supabase tests completed!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Add your GEMINI_API_KEY to .env file if you haven't already"
echo "2. Run migration script if you have existing ChromaDB data"
echo "3. Deploy to Vercel!"
