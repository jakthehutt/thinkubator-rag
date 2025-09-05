#!/bin/bash

# Test script for Next.js frontend
# This script runs frontend tests and build verification

set -e

echo "🧪 Running Frontend Tests..."
echo "============================"

# Change to frontend directory
cd src/frontend

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Run TypeScript type checking
echo ""
echo "🔍 Running TypeScript type check..."
npx tsc --noEmit

# Run ESLint
echo ""
echo "🔍 Running ESLint..."
npm run lint

# Test build process
echo ""
echo "🏗️  Testing production build..."
npm run build

# If we had Jest tests, we'd run them here
# echo ""
# echo "🧪 Running unit tests..."
# npm test

echo ""
echo "🎉 All frontend tests completed!"
echo "================================"
echo ""
echo "Frontend is ready for deployment!"
