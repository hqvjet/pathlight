#!/bin/bash
# =============================================================================
# 🐳 PathLight API Gateway - Docker Manager
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "🐳 PathLight API Gateway - Docker Manager"
    echo "========================================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start    - Start API Gateway service"
    echo "  stop     - Stop and remove gateway container"
    echo "  restart  - Stop and start gateway service"
    echo "  status   - Show status of container"
    echo "  logs     - Show logs of gateway service"
    echo "  clean    - Stop, remove container and clean network"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 logs"
    echo ""
    echo "Note: API Gateway connects to other services via external URLs"
    echo "      Make sure other services are running on their respective ports"
}

# Function to load environment variables
load_env() {
    local env_file=""
    
    # Find .env.local file
    if [ -f ".env.local" ]; then
        env_file=".env.local"
    elif [ -f "../.env.local" ]; then
        env_file="../.env.local"
    elif [ -f "../../.env.local" ]; then
        env_file="../../.env.local"
    else
        print_error "No .env.local file found!"
        print_error "Please create .env.local with the following variables:"
        echo "  API_GATEWAY_PORT=8000"
        echo "  AUTH_SERVICE_URL=http://auth-service:8001"
        echo "  USER_SERVICE_URL=http://user-service:8002"
        echo "  COURSE_SERVICE_URL=http://course-service:8003"
        echo "  QUIZ_SERVICE_URL=http://quiz-service:8004"
        echo ""
        print_error "You can copy from .env.example and modify the values."
        exit 1
    fi
    
    print_status "Loading environment variables from $env_file..."
    
    # Validate .env.local syntax before sourcing
    if ! grep -q "^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*=" "$env_file" 2>/dev/null; then
        print_error "Invalid .env.local file format!"
        print_error "Please check that all lines follow the format: VARIABLE_NAME=value"
        exit 1
    fi
    
    # Check for problematic lines
    if grep -n "^[[:space:]]*[^#].*[[:space:]].*=" "$env_file" 2>/dev/null; then
        print_error "Found problematic lines in $env_file:"
        grep -n "^[[:space:]]*[^#].*[[:space:]].*=" "$env_file" || true
        print_error "Please remove spaces around the '=' sign"
        exit 1
    fi
    
    # Source the file safely
    set -a  # Automatically export all variables
    if ! source "$env_file"; then
        print_error "Failed to load environment variables from $env_file"
        print_error "Please check the file syntax"
        exit 1
    fi
    set +a
    
    # Set default values if not provided
    export API_GATEWAY_PORT=${API_GATEWAY_PORT:-8000}
}

# Function to start services
start_services() {
    echo "🚀 Starting PathLight API Gateway with Docker..."
    
    # Load environment variables
    load_env
    
    # Create network if it doesn't exist
    print_status "Creating Docker network..."
    docker network create pathlight-network 2>/dev/null || print_warning "Network pathlight-network already exists"

    # Stop and remove existing container
    print_status "Cleaning up existing container..."
    docker stop pathlight-api-gateway 2>/dev/null || true
    docker rm pathlight-api-gateway 2>/dev/null || true

    # Build gateway service image
    print_status "Building API Gateway image..."
    docker build -t pathlight-api-gateway .

    # Run gateway service
    print_status "Starting API Gateway container..."
    docker run --name pathlight-api-gateway \
        --network pathlight-network \
        --env-file .env.local \
        -p "${API_GATEWAY_PORT:-8000}:8000" \
        -d pathlight-api-gateway

    # Wait for gateway service to be ready
    print_status "Waiting for API Gateway to be ready..."
    for i in {1..30}; do
        if curl -f "http://localhost:${API_GATEWAY_PORT:-8000}/health" >/dev/null 2>&1; then
            print_success "API Gateway is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "API Gateway health check failed, but container is running"
            break
        fi
        sleep 1
    done

    print_success "API Gateway started successfully!"
    echo ""
    echo "🌐 API Gateway: http://localhost:${API_GATEWAY_PORT:-8000}"
    echo "🏥 Health Check: http://localhost:${API_GATEWAY_PORT:-8000}/health"
    echo "📚 API Docs: http://localhost:${API_GATEWAY_PORT:-8000}/docs"
    echo ""
    echo "📋 View logs: docker logs -f pathlight-api-gateway"
    echo "🛑 Stop service: $0 stop"
    echo "🧹 Clean up: $0 clean"
    echo ""
    echo "⚠️  Note: Make sure backend services are running:"
    echo "   - Auth Service: http://localhost:8001"
    echo "   - User Service: http://localhost:8002"
    echo "   - Course Service: http://localhost:8003"
    echo "   - Quiz Service: http://localhost:8004"
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping PathLight API Gateway..."
    
    # Stop container
    print_status "Stopping container..."
    docker stop pathlight-api-gateway 2>/dev/null || print_warning "Container was not running"

    # Remove container  
    print_status "Removing container..."
    docker rm pathlight-api-gateway 2>/dev/null || print_warning "Container was already removed"

    print_success "API Gateway stopped successfully!"
    echo ""
    echo "💡 To restart service, run: $0 start"
}

# Function to clean everything
clean_services() {
    echo "🧹 Cleaning PathLight API Gateway..."
    
    # Stop container
    print_status "Stopping container..."
    docker stop pathlight-api-gateway 2>/dev/null || print_warning "Container was not running"

    # Remove container  
    print_status "Removing container..."
    docker rm pathlight-api-gateway 2>/dev/null || print_warning "Container was already removed"

    # Remove network
    print_status "Removing network..."
    docker network rm pathlight-network 2>/dev/null || print_warning "Network was already removed"

    print_success "Everything cleaned successfully!"
    echo ""
    echo "💡 To start service, run: $0 start"
}

# Function to show status
show_status() {
    echo "📊 PathLight API Gateway Status"
    echo "==============================="
    echo ""
    
    echo "🐳 Docker Container:"
    docker ps -a --filter "name=pathlight-api-gateway" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "🌐 Docker Networks:"
    docker network ls --filter "name=pathlight-network" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
    
    echo ""
    echo "🔗 Service Endpoints:"
    if docker ps --filter "name=pathlight-api-gateway" --filter "status=running" | grep -q pathlight-api-gateway; then
        echo "   ✅ API Gateway: http://localhost:${API_GATEWAY_PORT:-8000}"
        echo "   ✅ Health Check: http://localhost:${API_GATEWAY_PORT:-8000}/health"
        echo "   ✅ API Docs: http://localhost:${API_GATEWAY_PORT:-8000}/docs"
    else
        echo "   ❌ API Gateway: Not running"
    fi
    
    echo ""
    echo "🔗 Backend Services (should be running separately):"
    echo "   🔑 Auth Service: http://localhost:8001"
    echo "   👤 User Service: http://localhost:8002"  
    echo "   📚 Course Service: http://localhost:8003"
    echo "   🧠 Quiz Service: http://localhost:8004"
}

# Function to show logs
show_logs() {
    echo "📋 Showing API Gateway Logs (Ctrl+C to exit)..."
    echo "================================================"
    docker logs -f pathlight-api-gateway
}

# Main script logic
case "${1:-help}" in
    "start")
        start_services
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        echo ""
        start_services
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "clean")
        clean_services
        ;;
    "help"|"--help"|"-h"|"")
        show_usage
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
