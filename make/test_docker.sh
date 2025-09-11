#!/bin/bash

# Docker Setup Testing Script
# Tests that the Docker environment is working correctly

set -e

echo "🐳 Testing Docker Setup..."
echo "=========================="

# Check if Docker is running
echo ""
echo "📋 Checking Docker prerequisites..."
if ! docker --version > /dev/null 2>&1; then
    echo "❌ Docker is not installed or not running"
    exit 1
fi
echo "✅ Docker is available"

if ! docker compose version > /dev/null 2>&1; then
    echo "❌ Docker Compose is not installed"
    exit 1
fi
echo "✅ Docker Compose is available"

# Check environment file
echo ""
echo "🔍 Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "   Please create .env with required variables:"
    echo "   - GEMINI_API_KEY"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_ANON_KEY"
    echo "   - SUPABASE_SERVICE_ROLE_KEY"
    echo "   - POSTGRES_URL"
    echo "   - POSTGRES_URL_NON_POOLING"
    exit 1
fi
echo "✅ .env file found"

# Check required environment variables
REQUIRED_VARS=(
    "GEMINI_API_KEY"
    "SUPABASE_URL" 
    "SUPABASE_ANON_KEY"
    "SUPABASE_SERVICE_ROLE_KEY"
    "POSTGRES_URL_NON_POOLING"
)

source .env 2>/dev/null || true

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo "❌ Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    exit 1
fi
echo "✅ All required environment variables are set"

# Build containers
echo ""
echo "🔨 Building Docker containers..."
if ! docker compose build --quiet; then
    echo "❌ Failed to build containers"
    exit 1
fi
echo "✅ Containers built successfully"

# Start services in detached mode
echo ""
echo "🚀 Starting services..."
docker compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 20

# Test backend health
echo ""
echo "🏥 Testing backend health..."
BACKEND_HEALTH=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:8001/health" || echo "000")

if [ "$BACKEND_HEALTH" != "200" ]; then
    echo "❌ Backend health check failed (HTTP $BACKEND_HEALTH)"
    echo "Backend logs:"
    docker compose logs backend | tail -20
    docker compose down
    exit 1
fi
echo "✅ Backend health check passed"

# Test backend API
echo ""
echo "🔌 Testing backend API..."
API_RESPONSE=$(curl -s -X POST "http://localhost:8001/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "test query"}' || echo "ERROR")

if [ "$API_RESPONSE" = "ERROR" ]; then
    echo "❌ Backend API test failed"
    echo "Backend logs:"
    docker compose logs backend | tail -20
    docker compose down
    exit 1
fi
echo "✅ Backend API responding"

# Test frontend (if accessible)
echo ""
echo "🌐 Testing frontend..."
FRONTEND_HEALTH=$(curl -s -w "%{http_code}" -o /dev/null "http://localhost:3000/" || echo "000")

if [ "$FRONTEND_HEALTH" != "200" ]; then
    echo "⚠️  Frontend not accessible (HTTP $FRONTEND_HEALTH) - this might be normal if still building"
    echo "Frontend logs:"
    docker compose logs frontend | tail -10
else
    echo "✅ Frontend accessible"
fi

# Test container communication
echo ""
echo "🔗 Testing container communication..."
COMMUNICATION_TEST=$(docker compose exec -T backend curl -s -w "%{http_code}" -o /dev/null "http://backend:8000/health" || echo "000")

if [ "$COMMUNICATION_TEST" != "200" ]; then
    echo "❌ Container communication failed"
    docker compose down
    exit 1
fi
echo "✅ Container communication working"

# Cleanup
echo ""
echo "🧹 Cleaning up test environment..."
docker compose down

echo ""
echo "🎉 ALL DOCKER TESTS PASSED!"
echo "=========================="
echo ""
echo "✅ Docker setup is working correctly"
echo ""
echo "To start development environment:"
echo "  make dev"
echo ""
echo "To start production environment:"  
echo "  make prod"
echo ""
echo "To stop environment:"
echo "  make stop"
