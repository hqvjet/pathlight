#!/usr/bin/env bash
# =============================================================================
# 🐳 PathLight User Service - Docker Manager
# =============================================================================

set -e  # Exit on any error
set -u  # Exit on undefined variables
set -o pipefail  # Exit on pipe failures

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

# Function to clear terminal and reset cursor
clear_terminal() {
    # Clear screen and reset cursor position
    printf "\033[2J\033[H"
}

# Function to show usage
show_usage() {
    echo "🐳 PathLight User Service - Docker Manager"
    echo "=========================================="
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start    - Start user service (connects to shared PostgreSQL)"
    echo "  stop     - Stop user service (leave shared PostgreSQL running)"
    echo "  restart  - Stop and start user service"
    echo "  status   - Show status of containers"
    echo "  logs     - Show logs of user service"
    echo "  clean    - Stop and remove user service container"
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
    
    # Find environment file
    for possible_env in ".env.local" "../.env.local" "../../.env.local"; do
        if [[ -f "$possible_env" ]]; then
            env_file="$possible_env"
            break
        fi
    done
    
    if [[ -z "$env_file" ]]; then
        print_error "No .env.local file found!"
        print_error "Please create .env.local with the following variables:"
        echo "  POSTGRES_USER=your_db_user"
        echo "  POSTGRES_PASSWORD=your_db_password"
        echo "  POSTGRES_DB=your_db_name"
        echo "  POSTGRES_HOST=pathlight-postgres"
        echo "  POSTGRES_PORT=5432"
        echo "  USER_SERVICE_PORT=8002"
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
    if grep -qn "^[[:space:]]*[^#].*[[:space:]].*=" "$env_file" 2>/dev/null; then
        print_error "Found problematic lines in $env_file:"
        grep -n "^[[:space:]]*[^#].*[[:space:]].*=" "$env_file" || true
        print_error "Please remove spaces around the '=' sign"
        exit 1
    fi
    
    # Source the file safely
    set -a  # Automatically export all variables
    # shellcheck source=/dev/null
    if ! source "$env_file"; then
        print_error "Failed to load environment variables from $env_file"
        print_error "Please check the file syntax"
        exit 1
    fi
    set +a
    
    # Set default values if not provided
    export POSTGRES_USER=${POSTGRES_USER:-postgres}
    export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}
    export POSTGRES_DB=${POSTGRES_DB:-pathlight}
    export POSTGRES_HOST=${POSTGRES_HOST:-pathlight-postgres}
    export POSTGRES_PORT=${POSTGRES_PORT:-5432}
    export USER_SERVICE_PORT=${USER_SERVICE_PORT:-8002}
}

# Function to start services
start_services() {
    echo "🚀 Starting PathLight User Service with Docker..."
    
    # Load environment variables
    load_env
    
    # Create network if it doesn't exist
    print_status "Creating Docker network..."
    docker network create pathlight-network 2>/dev/null || print_warning "Network pathlight-network already exists"

    # Stop and remove existing user service container
    print_status "Cleaning up existing user service container..."
    docker stop pathlight-user-service 2>/dev/null || true
    docker rm pathlight-user-service 2>/dev/null || true

    # Check if PostgreSQL is available (shared container)
    print_status "Checking for PostgreSQL availability..."
    if ! docker exec pathlight-postgres pg_isready -U "$POSTGRES_USER" >/dev/null 2>&1; then
        print_warning "PostgreSQL container not available. Please ensure it's running."
        print_warning "You may need to start another service first (e.g., auth-service)."
    else
        print_success "PostgreSQL is ready!"
    fi

    # Build user service image
    print_status "Building user service image..."
    docker build -t pathlight-user-service .

    # Run user service
    print_status "Starting user service container..."
    docker run --name pathlight-user-service \
        --network pathlight-network \
        --env-file .env.local \
        -p "${USER_SERVICE_PORT}:${USER_SERVICE_PORT}" \
        -d pathlight-user-service

    # Wait for user service to be ready
    print_status "Waiting for user service to be ready..."
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f "http://localhost:${USER_SERVICE_PORT}/health" >/dev/null 2>&1; then
            print_success "User service is ready!"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            print_warning "User service health check failed after ${max_attempts} attempts"
            print_warning "Container may still be starting. Check logs with: docker logs pathlight-user-service"
            break
        fi
        
        printf "."
        sleep 1
        ((attempt++))
    done
    echo ""  # New line after dots

    print_success "Services started successfully!"
    echo ""
    echo "🌐 User Service: http://localhost:${USER_SERVICE_PORT}"
    echo "🏥 Health Check: http://localhost:${USER_SERVICE_PORT}/health"
    echo "📊 Config Debug: http://localhost:${USER_SERVICE_PORT}/debug/config"
    echo "📚 API Docs: http://localhost:${USER_SERVICE_PORT}/docs"
    echo ""
    echo "📋 View logs: docker logs -f pathlight-user-service"
    echo "🗄️ PostgreSQL logs: docker logs -f pathlight-postgres"
    echo "🛑 Stop services: $0 stop"
    echo "🧹 Clean up: $0 clean"
}

# Function to stop services
stop_services() {
    echo "🛑 Stopping PathLight User Service..."
    
    # Stop user service container only (leave shared PostgreSQL running)
    print_status "Stopping user service container..."
    docker stop pathlight-user-service 2>/dev/null || print_warning "User service container was not running"

    # Remove user service container  
    print_status "Removing user service container..."
    docker rm pathlight-user-service 2>/dev/null || print_warning "User service container was already removed"

    print_success "User service stopped successfully!"
    print_warning "Note: Shared PostgreSQL container is still running for other services"
    echo ""
    echo "💡 To restart user service, run: $0 start"
}

# Function to clean everything
clean_services() {
    echo "🧹 Cleaning PathLight User Service..."
    
    # Stop user service container only
    print_status "Stopping user service container..."
    docker stop pathlight-user-service 2>/dev/null || print_warning "User service container was not running"

    # Remove user service container  
    print_status "Removing user service container..."
    docker rm pathlight-user-service 2>/dev/null || print_warning "User service container was already removed"

    print_success "User service cleaned successfully!"
    print_warning "Note: Shared PostgreSQL container and network are preserved for other services"
    echo ""
    echo "💡 To start user service, run: $0 start"
}

# Function to show status
show_status() {
    echo "📊 PathLight User Service Status"
    echo "==============================="
    echo ""
    
    echo "🐳 Docker Containers:"
    docker ps -a --filter "name=pathlight-user-service" --filter "name=pathlight-postgres" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo "🌐 Docker Networks:"
    docker network ls --filter "name=pathlight-network" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
    
    echo ""
    echo "🔗 Service Endpoints:"
    if docker ps --filter "name=pathlight-user-service" --filter "status=running" | grep -q pathlight-user-service; then
        echo "   ✅ User Service: http://localhost:8002"
        echo "   ✅ Health Check: http://localhost:8002/health"
        echo "   ✅ API Docs: http://localhost:8002/docs"
    else
        echo "   ❌ User Service: Not running"
    fi
    
    if docker ps --filter "name=pathlight-postgres" --filter "status=running" | grep -q pathlight-postgres; then
        echo "   ✅ PostgreSQL: localhost:5432 (shared)"
    else
        echo "   ❌ PostgreSQL: Not running"
    fi
}

# Function to show logs
show_logs() {
    echo "📋 Showing User Service Logs (Ctrl+C to exit)..."
    echo "================================================="
    docker logs -f pathlight-user-service
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
