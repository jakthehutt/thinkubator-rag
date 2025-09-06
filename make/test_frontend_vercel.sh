#!/bin/bash

# Frontend Vercel Dev Testing Script
# Integrates with the main Makefile testing system

set -e

echo "🎨 Frontend Vercel Dev Testing"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo "❌ Error: Must be run from project root directory"
    exit 1
fi

# Navigate to frontend directory
cd src/frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Check if Vercel dev is running
echo "🔍 Checking if Vercel dev is running..."
if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Vercel dev is running"
    VERCEL_RUNNING=true
else
    echo "⚠️  Vercel dev is not running"
    VERCEL_RUNNING=false
fi

# If Vercel dev is not running, provide instructions
if [ "$VERCEL_RUNNING" = false ]; then
    echo ""
    echo "📋 To run frontend tests, you need Vercel dev running:"
    echo "   1. Open a new terminal"
    echo "   2. cd src/frontend"
    echo "   3. npm run dev"
    echo "   4. Wait for 'Ready' message"
    echo "   5. Run 'make test-frontend-vercel' again"
    echo ""
    echo "🚀 Starting Vercel dev now..."
    echo "   (This will run in the background)"
    
    # Start Vercel dev in background
    nohup npm run dev > vercel-dev.log 2>&1 &
    VERCEL_PID=$!
    echo "   Vercel dev started with PID: $VERCEL_PID"
    
    # Wait for Vercel dev to be ready
    echo "   Waiting for Vercel dev to be ready..."
    for i in {1..30}; do
        if curl -s -f http://localhost:3000 > /dev/null 2>&1; then
            echo "   ✅ Vercel dev is ready after ${i} seconds"
            VERCEL_RUNNING=true
            break
        fi
        sleep 1
    done
    
    if [ "$VERCEL_RUNNING" = false ]; then
        echo "   ❌ Vercel dev failed to start within 30 seconds"
        echo "   Check vercel-dev.log for details"
        exit 1
    fi
fi

# Run the test suite
echo ""
echo "🧪 Running Frontend Test Suite..."
echo "================================="

# Run all frontend tests
npm run test

# Clean up if we started Vercel dev
if [ -n "$VERCEL_PID" ]; then
    echo ""
    echo "🧹 Cleaning up..."
    kill $VERCEL_PID 2>/dev/null || true
    echo "   Stopped Vercel dev (PID: $VERCEL_PID)"
fi

echo ""
echo "🎉 Frontend Vercel dev testing completed!"
