#!/bin/bash

# Comprehensive test script that runs all tests
# Includes backend, frontend, and integration tests

set -e

echo "🚀 Running All Tests..."
echo "======================"

# Backend tests
echo ""
echo "🧪 Running Backend Tests..."
echo "----------------------------"
pytest src/backend/tests/chain/ -v

# Supabase tests
echo ""
echo "🧪 Running Supabase Tests..."
echo "----------------------------"
bash make/test_supabase.sh

# Frontend tests
echo ""
echo "🧪 Running Frontend Tests..."
echo "----------------------------"
bash make/test_frontend.sh

echo ""
echo "🎉 ALL TESTS COMPLETED!"
echo "======================"
echo ""
echo "✅ Backend tests: PASSED"
echo "✅ Supabase tests: PASSED"  
echo "✅ Frontend tests: PASSED"
echo ""
echo "Your application is ready for deployment! 🚀"
