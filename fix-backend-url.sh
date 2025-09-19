#!/bin/bash

# Fix Backend URL Configuration for Production
# This script adds the missing NEXT_PUBLIC_BACKEND_URL to .env.production

echo "🔧 Fixing Backend URL Configuration..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found. Make sure you're in /opt/rag-app"
    exit 1
fi

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ Error: .env.production file not found"
    exit 1
fi

# Check current configuration
echo "📋 Current backend URL configuration:"
grep -n "NEXT_PUBLIC_BACKEND_URL" .env.production || echo "   (not set)"

# Get the domain from the existing configuration
DOMAIN=$(grep "^DOMAIN=" .env.production | cut -d'=' -f2)

if [ -z "$DOMAIN" ]; then
    echo "❌ Error: DOMAIN not found in .env.production"
    exit 1
fi

echo "🌐 Found domain: $DOMAIN"

# Check if NEXT_PUBLIC_BACKEND_URL is already set
if grep -q "^NEXT_PUBLIC_BACKEND_URL=" .env.production; then
    echo "✅ NEXT_PUBLIC_BACKEND_URL already exists, updating..."
    sed -i "s|^NEXT_PUBLIC_BACKEND_URL=.*|NEXT_PUBLIC_BACKEND_URL=https://api.$DOMAIN|" .env.production
else
    echo "➕ Adding NEXT_PUBLIC_BACKEND_URL to .env.production..."
    echo "" >> .env.production
    echo "# Frontend Backend URL" >> .env.production
    echo "NEXT_PUBLIC_BACKEND_URL=https://api.$DOMAIN" >> .env.production
fi

# Verify the change
echo "✅ Updated configuration:"
grep -n "NEXT_PUBLIC_BACKEND_URL" .env.production

# Restart the frontend service to apply new environment variables
echo "🔄 Restarting frontend service..."
docker compose up -d --build frontend

echo "✅ Backend URL configuration fixed!"
echo "🌐 Frontend will now connect to: https://api.$DOMAIN"
echo ""
echo "🧪 Test the fix by visiting: https://$DOMAIN"
