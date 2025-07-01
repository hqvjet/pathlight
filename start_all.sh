#!/bin/bash

# PathLight - Smart Startup Script
# Automatically loads environment variables and starts services

set -e

echo "🚀 PathLight - Starting All Services"
echo "======================================"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "📝 Please copy .env.example to .env and configure it:"
    echo "   cp .env.example .env"
    echo "   nano .env"
    exit 1
fi

# Load environment variables
echo "📋 Loading environment variables from .env..."
source .env

# Validate required variables
required_vars=("POSTGRES_PASSWORD" "JWT_SECRET_KEY" "JWT_REFRESH_SECRET_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set!"
        echo "📝 Please update your .env file"
        exit 1
    fi
done

echo "✅ Environment variables loaded successfully"

# Check if Docker is running  
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "🐳 Docker is running"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! command -v docker &> /dev/null; then
    echo "❌ docker-compose or docker compose is not available."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping existing containers..."
docker compose down --remove-orphans 2>/dev/null || docker-compose down --remove-orphans 2>/dev/null

# Build and start services
echo "� Building and starting services..."
echo "   - PostgreSQL Database (Port: $POSTGRES_PORT)"
echo "   - Auth Service (Port: $AUTH_SERVICE_PORT)"
echo "   - User Service (Port: $USER_SERVICE_PORT)"
echo "   - Course Service (Port: $COURSE_SERVICE_PORT)"
echo "   - Quiz Service (Port: $QUIZ_SERVICE_PORT)"
echo "   - API Gateway (Port: $API_GATEWAY_PORT)"

# Start with Docker Compose
docker compose up -d --build 2>/dev/null || docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
services=("api-gateway:$API_GATEWAY_PORT" "auth-service:$AUTH_SERVICE_PORT" "user-service:$USER_SERVICE_PORT")
all_healthy=true

for service_port in "${services[@]}"; do
    service=$(echo $service_port | cut -d: -f1)
    port=$(echo $service_port | cut -d: -f2)
    
    if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "✅ $service is healthy (port $port)"
    else
        echo "⚠️  $service is not responding (port $port)"
        all_healthy=false
    fi
done

echo ""
if [ "$all_healthy" = true ]; then
    echo "🎉 All services are running successfully!"
    echo ""
    echo "📍 Service URLs:"
    echo "   🌐 API Gateway:    http://localhost:$API_GATEWAY_PORT"
    echo "   🔐 Auth Service:   http://localhost:$AUTH_SERVICE_PORT"
    echo "   👤 User Service:   http://localhost:$USER_SERVICE_PORT"
    echo "   📚 Course Service: http://localhost:$COURSE_SERVICE_PORT"
    echo "   📝 Quiz Service:   http://localhost:$QUIZ_SERVICE_PORT"
    echo "   🗄️  Database:      localhost:$POSTGRES_PORT"
    echo ""
    echo "🔑 Admin Credentials:"
    echo "   Username: $ADMIN_USERNAME"
    echo "   Password: $ADMIN_PASSWORD"
    echo ""
    echo "📖 API Documentation: http://localhost:$API_GATEWAY_PORT/docs"
else
    echo "⚠️  Some services are not responding. Check logs with:"
    echo "   docker compose logs [service-name]"
fi

echo ""
echo "🛠️  Useful Commands:"
echo "   docker compose logs -f          # View all logs"
echo "   docker compose down             # Stop all services"
echo "   docker compose restart         # Restart all services"
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
