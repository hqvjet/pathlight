#!/bin/bash

# PathLight Application Startup Script
# This script will start all services using Docker Compose

set -e

echo "🚀 Starting PathLight Application..."
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first."
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env..."
    export $(cat .env | grep -v '#' | xargs)
else
    echo "⚠️  No .env file found. Using default values."
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans

# Clean up old images (optional)
read -p "🗑️  Do you want to clean up old Docker images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Cleaning up old Docker images..."
    docker system prune -f
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

services=("postgres:5433" "auth-service:8001" "api-gateway:8000")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    echo -n "   Checking $name:$port... "
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            echo "✅ Ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        echo "❌ Failed to start"
    fi
done

# Display service URLs
echo ""
echo "🌐 Service URLs:"
echo "=================================="
echo "   API Gateway:     http://localhost:8000"
echo "   API Gateway Docs: http://localhost:8000/docs"
echo "   Auth Service:     http://localhost:8001"
echo "   Auth Service Docs: http://localhost:8001/docs"
echo "   Frontend:         http://localhost:3000"
echo "   Database:         postgresql://postgres:1210@localhost:5433/pathlight_db"
echo ""

# Display API endpoints
echo "🔗 Available API Endpoints:"
echo "=================================="
echo "   POST /api/v1/signup              - User registration"
echo "   GET  /api/v1/verify-email        - Email verification"
echo "   POST /api/v1/signin              - User login"
echo "   GET  /api/v1/signout             - User logout"
echo "   POST /api/v1/forget-password     - Forget password"
echo "   POST /api/v1/reset-password/:token - Reset password"
echo "   POST /api/v1/oauth-signin        - OAuth login"
echo "   POST /api/v1/user/change-password - Change password"
echo "   POST /api/v1/admin/signin        - Admin login"
echo ""

# Show logs
echo "📋 Starting to show logs (Ctrl+C to stop)..."
echo "=================================="
docker-compose logs -f
