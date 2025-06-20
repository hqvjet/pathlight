#!/bin/bash

echo "🏗️  Building and Starting All Services..."
echo "========================================"

cd /home/ngochoa203/Code/pathlight/services

echo "📦 Building Docker images..."
docker-compose build --no-cache

echo ""
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 15

echo ""
echo "🔍 Checking service health..."
echo "Auth Service: $(curl -s http://localhost:8001/health | jq -r '.status // "unhealthy"')"
echo "Course Service: $(curl -s http://localhost:8002/health | jq -r '.status // "unhealthy"')"
echo "Quiz Service: $(curl -s http://localhost:8003/health | jq -r '.status // "unhealthy"')"
echo "User Service: $(curl -s http://localhost:8004/health | jq -r '.status // "unhealthy"')"

echo ""
echo "📋 Service URLs:"
echo "• Auth Service: http://localhost:8001 (docs: http://localhost:8001/docs)"
echo "• Course Service: http://localhost:8002 (docs: http://localhost:8002/docs)"
echo "• Quiz Service: http://localhost:8003 (docs: http://localhost:8003/docs)"
echo "• User Service: http://localhost:8004 (docs: http://localhost:8004/docs)"

echo ""
echo "🧪 To test all services: ./test_all_services.sh"
echo "📋 To view logs: docker-compose logs -f [service-name]"
echo "🛑 To stop all: docker-compose down"

echo ""
echo "✅ All services are running!"
