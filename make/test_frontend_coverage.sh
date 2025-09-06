#!/bin/bash

# Frontend Document Coverage Testing Script
# Tests if system is retrieving documents from real database vs mock data

set -e

echo "📚 Frontend Document Coverage Testing"
echo "===================================="

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

# Navigate to frontend directory
cd src/frontend

# Check if Vercel dev is running (try both ports)
VERCEL_PORT=""
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    VERCEL_PORT="3000"
elif curl -s -f http://localhost:3001 > /dev/null 2>&1; then
    VERCEL_PORT="3001"
else
    echo "❌ Vercel dev is not running on http://localhost:3000 or http://localhost:3001"
    echo "   Please run 'make run-frontend' in another terminal first"
    exit 1
fi

echo "✅ Vercel dev is running on port $VERCEL_PORT"
echo ""

# Update the test to use the correct port if needed
if [ "$VERCEL_PORT" = "3000" ]; then
    sed -i.bak 's/localhost:3001/localhost:3000/g' tests/test-document-coverage.js
fi

# Run document coverage tests
echo "🧪 Running document coverage tests..."
npm run test:coverage

echo ""
echo "🎉 Document coverage testing completed!"
