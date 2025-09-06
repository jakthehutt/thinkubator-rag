#!/bin/bash

# Frontend End-to-End Testing Script
# Tests complete user workflows in Vercel dev environment

set -e

echo "🎬 Frontend End-to-End Testing"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

# Navigate to frontend directory
cd src/frontend

# Check if Vercel dev is running
if ! curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo "❌ Vercel dev is not running on http://localhost:3000"
    echo "   Please run 'make run-frontend' in another terminal first"
    exit 1
fi

echo "✅ Vercel dev is running"
echo ""

# Run E2E tests
echo "🧪 Running end-to-end workflow tests..."
npm run test:e2e

echo ""
echo "🎉 Frontend E2E testing completed!"
