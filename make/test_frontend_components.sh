#!/bin/bash

# Frontend Component Testing Script
# Tests frontend components and UI in Vercel dev environment

set -e

echo "🎨 Frontend Component Testing"
echo "============================="

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

# Navigate to frontend directory
cd src/frontend

# Check if Vercel dev is running
if ! curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    if ! curl -s -f http://localhost:3001 > /dev/null 2>&1; then
        echo "❌ Vercel dev is not running on http://localhost:3000 or http://localhost:3001"
        echo "   Please run 'make run-frontend' in another terminal first"
        exit 1
    fi
fi

echo "✅ Vercel dev is running"
echo ""

# Run frontend component tests
echo "🧪 Running frontend component tests..."
npm run test:frontend

echo ""
echo "🎉 Frontend component testing completed!"
