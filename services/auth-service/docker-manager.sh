#!/bin/bash
# =============================================================================
# 🐳 PathLight Auth Service - Docker Manager
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
    echo "🐳 PathLight Auth Service - Docker Manager"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start    - Start all services (PostgreSQL + Auth Service)"
    echo "  stop     - Stop and remove all containers"
    echo "  restart  - Stop and start services"
    echo "  status   - Show status of containers"
    echo "  logs     - Show logs of auth service"
    echo "  clean    - Stop, remove containers and clean network"
    echo "  help     - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 stop"
    echo "  $0 logs"
    echo ""
}

# Function to load environment variables
load_env() {
    local env_file=""
    
    if [ -f ".env.local" ]; then
        env_file=".env.local"
    elif [ -f "../.env.local" ]; then
        env_file="../.env.local"
    elif [ -f "../../.env.local" ]; then
        env_file="../../.env.local"
    else
        print_error "No .env.local file found!"
        print_error "Please create .env.local with the following variables:"
        echo "  POSTGRES_USER=your_db_user"
        echo "  POSTGRES_PASSWORD=your_db_password"
        echo "  POSTGRES_DB=your_db_name"
        echo "  POSTGRES_HOST=pathlight-postgres"
        echo "  POSTGRES_PORT=5432"
        echo "  AUTH_SERVICE_PORT=8001"
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
    export POSTGRES_USER=${POSTGRES_USER:-postgres}
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-1210}
    export POSTGRES_DB=${POSTGRES_DB:-pathlight}
    export POSTGRES_HOST=${POSTGRES_HOST:-pathlight-postgres}
    export POSTGRES_PORT=${POSTGRES_PORT:-5432}
    export AUTH_SERVICE_PORT=${AUTH_SERVICE_PORT:-8001}
}

# Function to start services
start_services() {
    echo "🚀 Starting PathLight Auth Service with Docker..."
    
    # Load environment variables
    load_env
    
    # Create network if it doesn't exist
    print_status "Creating Docker network..."
    docker network create pathlight-network 2>/dev/null || print_warning "Network pathlight-network already exists"

    # Stop and remove existing containers
    print_status "Cleaning up existing containers..."
    docker stop pathlight-auth-service pathlight-postgres 2>/dev/null || true
    docker rm pathlight-auth-service pathlight-postgres 2>/dev/null || true

    # Start PostgreSQL
    print_status "Starting PostgreSQL container..."
    docker run --name pathlight-postgres \
        --network pathlight-network \
        -e POSTGRES_USER="$POSTGRES_USER" \
        -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
        -e POSTGRES_DB="$POSTGRES_DB" \
        -p "${POSTGRES_PORT}:5432" \
        -d postgres:15-alpine

    # Wait for PostgreSQL to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
        if docker exec pathlight-postgres pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
            print_success "PostgreSQL is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "PostgreSQL failed to start within 30 seconds"
            exit 1
        fi
        sleep 1
    done

    # Build auth service image
    print_status "Building auth service image..."
    docker build -t pathlight-auth-service .

    # Run auth service
    print_status "Starting auth service container..."
    docker run --name pathlight-auth-service \
        --network pathlight-network \
        --env-file .env.local \
        -e DATABASE_URL="postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}" \
        -p "${AUTH_SERVICE_PORT:-8001}:8000" \
        -d pathlight-auth-service

    # Wait for auth service to be ready
    print_status "Waiting for auth service to be ready..."
    for i in {1..30}; do
        if curl -f "http://localhost:${AUTH_SERVICE_PORT:-8001}/health" >/dev/null 2>&1; then
            print_success "Auth service is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            print_warning "Auth service health check failed, but container is running"
            break
        fi
        sleep 1
    done

    print_success "Services started successfully!"
    echo ""
    echo "🌐 Auth Service: http://localhost:${AUTH_SERVICE_PORT:-8001}"
    echo "🏥 Health Check: http://localhost:${AUTH_SERVICE_PORT:-8001}/health"
    echo "📊 Config Debug: http://localhost:${AUTH_SERVICE_PORT:-8001}/debug/config"
    echo "📚 API Docs: http://localhost:${AUTH_SERVICE_PORT:-8001}/docs"
    echo ""
    echo "📋 View logs: docker logs -f pathlight-auth-service"
    echo "🗄️ PostgreSQL logs: docker logs -f pathlight-postgres"
    echo "🛑 Stop services: $0 stop"
    echo "🧹 Clean up: $0 clean"
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping PathLight Auth Service..."
    
    # Stop containers
    print_status "Stopping containers..."
    docker stop pathlight-auth-service pathlight-postgres 2>/dev/null || print_warning "Some containers were not running"

    # Remove containers  
    print_status "Removing containers..."
    docker rm pathlight-auth-service pathlight-postgres 2>/dev/null || print_warning "Some containers were already removed"

    print_success "Services stopped successfully!"
    echo ""
    echo "💡 To restart services, run: $0 start"
}

# Function to clean everything
clean_services() {
    echo "🧹 Cleaning PathLight Auth Service..."
    
    # Stop containers
    print_status "Stopping containers..."
    docker stop pathlight-auth-service pathlight-postgres 2>/dev/null || print_warning "Some containers were not running"

    # Remove containers  
    print_status "Removing containers..."
    docker rm pathlight-auth-service pathlight-postgres 2>/dev/null || print_warning "Some containers were already removed"

    # Remove network
    print_status "Removing network..."
    docker network rm pathlight-network 2>/dev/null || print_warning "Network was already removed"

    print_success "Everything cleaned successfully!"
    echo ""
    echo "💡 To start services, run: $0 start"
}

# Function to show status
show_status() {
    echo "📊 PathLight Auth Service Status"
    echo "================================"
    echo ""
    
    echo "🐳 Docker Containers:"
    docker ps -a --filter "name=pathlight-auth-service" --filter "name=pathlight-postgres" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "🌐 Docker Networks:"
    docker network ls --filter "name=pathlight-network" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
    
    echo ""
    echo "🔗 Service Endpoints:"
    if docker ps --filter "name=pathlight-auth-service" --filter "status=running" | grep -q pathlight-auth-service; then
        echo "   ✅ Auth Service: http://localhost:8001"
        echo "   ✅ Health Check: http://localhost:8001/health"
        echo "   ✅ API Docs: http://localhost:8001/docs"
    else
        echo "   ❌ Auth Service: Not running"
    fi
    
    if docker ps --filter "name=pathlight-postgres" --filter "status=running" | grep -q pathlight-postgres; then
        echo "   ✅ PostgreSQL: localhost:5432"
    else
        echo "   ❌ PostgreSQL: Not running"
    fi
}

# Function to show logs
show_logs() {
    echo "📋 Showing Auth Service Logs (Ctrl+C to exit)..."
    echo "================================================"
    docker logs -f pathlight-auth-service
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
