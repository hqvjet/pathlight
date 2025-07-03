#!/bin/bash

# ==============================================================================
# 🚀 PATHLIGHT SERVICE MANAGEMENT SCRIPT
# ==============================================================================
# Comprehensive service management tool for PathLight project
# 
# Usage: ./start_all.sh [command] [service_name]
# Commands:
#   start [service]    - Start all services or specific service
#   stop [service]     - Stop all services or specific service  
#   restart [service]  - Restart all services or specific service
#   status             - Show status of all services
#   logs [service]     - Show logs from all or specific service
#   follow [service]   - Follow logs in real-time
#   health             - Check health of all services
#   build [service]    - Build all or specific service images
#   cleanup            - Clean up Docker resources
#   reset              - Reset all services (DESTROYS DATA!)
#   help               - Show this help message
# ==============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Service definitions
declare -A SERVICES=(
    ["postgres"]="Database"
    ["api-gateway"]="API Gateway"
    ["auth-service"]="Authentication Service" 
    ["user-service"]="User Management Service"
    ["course-service"]="Course Management Service"
    ["quiz-service"]="Quiz Management Service"
)

declare -A SERVICE_PORTS=(
    ["api-gateway"]="8000"
    ["auth-service"]="8001"
    ["user-service"]="8002"
    ["course-service"]="8003"
    ["quiz-service"]="8004"
    ["postgres"]="5432"
)

# Helper functions
print_header() {
    echo -e "${BLUE}🚀 PathLight Service Manager${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_section() {
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}$(echo "$1" | sed 's/./=/g')${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${WHITE}ℹ️  $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        if [ -f .env.example ]; then
            cp .env.example .env
            print_info "Please edit .env file with your configurations"
        else
            print_error ".env.example file not found. Please create .env file manually."
            exit 1
        fi
    fi
}

# Validate service name
validate_service() {
    local service=$1
    if [ -n "$service" ] && [ -z "${SERVICES[$service]}" ]; then
        print_error "Unknown service: $service"
        echo "Available services: ${!SERVICES[@]}"
        exit 1
    fi
}

# Start services
start_services() {
    local service=$1
    print_header
    
    if [ -n "$service" ]; then
        print_section "🚀 Starting $service (${SERVICES[$service]})"
        docker-compose up -d "$service"
        print_success "$service started"
        
        # Wait and check health for specific service
        if [ "$service" != "postgres" ]; then
            echo "Waiting for service to be ready..."
            sleep 5
            check_service_health "$service"
        fi
    else
        print_section "🚀 Starting All Services"
        echo "1️⃣ Starting database..."
        docker-compose up -d postgres
        
        echo "2️⃣ Waiting for database to be ready..."
        wait_for_postgres
        
        echo "3️⃣ Starting core services..."
        docker-compose up -d auth-service user-service course-service quiz-service
        
        echo "4️⃣ Starting API gateway..."
        docker-compose up -d api-gateway
        
        echo "5️⃣ Waiting for all services to be ready..."
        sleep 10
        
        print_section "📊 Service Status"
        check_all_health
        
        print_success "All services started successfully!"
        print_service_urls
    fi
}

# Stop services
stop_services() {
    local service=$1
    print_header
    
    if [ -n "$service" ]; then
        print_section "🛑 Stopping $service (${SERVICES[$service]})"
        docker-compose stop "$service"
        print_success "$service stopped"
    else
        print_section "🛑 Stopping All Services"
        docker-compose down
        print_success "All services stopped"
    fi
}

# Restart services
restart_services() {
    local service=$1
    print_header
    
    if [ -n "$service" ]; then
        print_section "🔄 Restarting $service (${SERVICES[$service]})"
        docker-compose restart "$service"
        print_success "$service restarted"
        
        if [ "$service" != "postgres" ]; then
            echo "Waiting for service to be ready..."
            sleep 5
            check_service_health "$service"
        fi
    else
        print_section "🔄 Restarting All Services"
        stop_services
        echo ""
        start_services
    fi
}

# Show service status
show_status() {
    print_header
    print_section "📊 Service Status"
    
    echo "Container Status:"
    docker-compose ps
    
    echo ""
    print_section "🏥 Health Checks"
    check_all_health
    
    echo ""
    print_section "📈 Resource Usage"
    show_resource_usage
}

# Check health of all services
check_all_health() {
    for service in "${!SERVICE_PORTS[@]}"; do
        if [ "$service" != "postgres" ]; then
            check_service_health "$service"
        fi
    done
    
    # Check postgres separately
    check_postgres_health
}

# Check health of specific service
check_service_health() {
    local service=$1
    local port=${SERVICE_PORTS[$service]}
    echo -n "   $service: "
    
    if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
        print_success "Healthy"
    else
        print_error "Not responding"
    fi
}

# Check postgres health
check_postgres_health() {
    echo -n "   postgres: "
    if docker exec pathlight-postgres-1 pg_isready -U postgres > /dev/null 2>&1; then
        print_success "Database is ready"
    else
        print_error "Database not responding"
    fi
}

# Wait for postgres to be ready
wait_for_postgres() {
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if docker exec pathlight-postgres-1 pg_isready -U postgres > /dev/null 2>&1; then
            print_success "Database is ready"
            return 0
        fi
        
        echo "   Waiting for database... ($attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    print_error "Database failed to start within timeout"
    return 1
}

# Show logs
show_logs() {
    local service=$1
    local lines=${2:-50}
    
    print_header
    
    if [ -n "$service" ]; then
        print_section "📋 Logs for $service (${SERVICES[$service]})"
        docker-compose logs --tail "$lines" "$service"
    else
        print_section "📋 Logs for All Services"
        for svc in "${!SERVICES[@]}"; do
            echo ""
            echo -e "${CYAN}=== $svc ===${NC}"
            docker-compose logs --tail 10 "$svc" 2>/dev/null || echo "No logs available"
        done
    fi
}

# Follow logs in real-time
follow_logs() {
    local service=$1
    
    print_header
    
    if [ -n "$service" ]; then
        print_section "📡 Following logs for $service (${SERVICES[$service]})"
        print_info "Press Ctrl+C to stop following logs"
        docker-compose logs -f "$service"
    else
        print_section "📡 Following logs for All Services"
        print_info "Press Ctrl+C to stop following logs"
        docker-compose logs -f
    fi
}

# Build images
build_images() {
    local service=$1
    print_header
    
    if [ -n "$service" ]; then
        print_section "🔨 Building $service"
        docker-compose build --no-cache "$service"
        print_success "$service image built"
    else
        print_section "🔨 Building All Images"
        docker-compose build --no-cache
        print_success "All images built"
    fi
}

# Show resource usage
show_resource_usage() {
    local containers=$(docker ps --filter "name=pathlight" --format "{{.Names}}")
    
    if [ -n "$containers" ]; then
        docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $containers
    else
        print_warning "No PathLight containers running"
    fi
}

# Print service URLs
print_service_urls() {
    echo ""
    print_info "Service URLs:"
    echo "   - API Gateway:    http://localhost:8000/docs"
    echo "   - Auth Service:   http://localhost:8001/docs"
    echo "   - User Service:   http://localhost:8002/docs"
    echo "   - Course Service: http://localhost:8003/docs"
    echo "   - Quiz Service:   http://localhost:8004/docs"
    echo "   - Database:       postgresql://localhost:5432"
}

# Cleanup Docker resources
cleanup_resources() {
    print_header
    print_section "🧹 Cleaning Up Docker Resources"
    
    echo "1️⃣ Removing stopped containers..."
    docker container prune -f
    
    echo "2️⃣ Removing unused images..."
    docker image prune -f
    
    echo "3️⃣ Removing unused volumes..."
    docker volume prune -f
    
    echo "4️⃣ Removing unused networks..."
    docker network prune -f
    
    print_success "Cleanup completed"
}

# Reset all services
reset_all() {
    print_header
    print_section "⚠️ COMPLETE RESET"
    
    print_warning "This will:"
    echo "   - Stop all services"
    echo "   - Remove all containers"
    echo "   - Remove all volumes (DATABASE WILL BE LOST!)"
    echo "   - Remove all images"
    echo ""
    
    read -p "Are you sure? Type 'yes' to continue: " confirm
    if [ "$confirm" != "yes" ]; then
        print_info "Reset cancelled"
        return 0
    fi
    
    echo "1️⃣ Stopping all services..."
    docker-compose down --volumes --remove-orphans
    
    echo "2️⃣ Removing PathLight images..."
    docker images --filter "reference=pathlight*" -q | xargs -r docker rmi -f
    
    echo "3️⃣ Cleaning up system..."
    docker system prune -af --volumes
    
    print_success "Reset completed"
    print_info "Run './start_all.sh build' and then './start_all.sh start' to rebuild"
}

# Show help
show_help() {
    print_header
    echo "Usage: $0 [command] [service_name] [options]"
    echo ""
    echo "Commands:"
    echo "  start [service]    - Start all services or specific service"
    echo "  stop [service]     - Stop all services or specific service"
    echo "  restart [service]  - Restart all services or specific service"
    echo "  status             - Show status of all services"
    echo "  logs [service] [lines] - Show logs (default: 50 lines)"
    echo "  follow [service]   - Follow logs in real-time"
    echo "  health             - Check health of all services"
    echo "  build [service]    - Build all or specific service images"
    echo "  cleanup            - Clean up Docker resources"
    echo "  reset              - Reset all services (DESTROYS DATA!)"
    echo "  help               - Show this help message"
    echo ""
    echo "Available services:"
    for service in "${!SERVICES[@]}"; do
        echo "  $service - ${SERVICES[$service]}"
    done
    echo ""
    echo "Examples:"
    echo "  $0 start                     # Start all services"
    echo "  $0 start auth-service        # Start only auth service"
    echo "  $0 stop                      # Stop all services"
    echo "  $0 restart user-service      # Restart user service"
    echo "  $0 logs api-gateway 100      # Show 100 lines of API gateway logs"
    echo "  $0 follow auth-service       # Follow auth service logs"
    echo "  $0 status                    # Show service status"
    echo "  $0 health                    # Check service health"
}

# Main script logic
main() {
    local command=${1:-help}
    local service=$2
    local option=$3
    
    # Check prerequisites
    check_docker
    check_env
    
    # Validate service name if provided
    if [ -n "$service" ]; then
        validate_service "$service"
    fi
    
    case "$command" in
        "start"|"up")
            start_services "$service"
            ;;
        "stop"|"down")
            stop_services "$service"
            ;;
        "restart"|"reboot")
            restart_services "$service"
            ;;
        "status"|"ps")
            show_status
            ;;
        "logs"|"log")
            show_logs "$service" "$option"
            ;;
        "follow"|"tail")
            follow_logs "$service"
            ;;
        "health"|"check")
            print_header
            print_section "🏥 Health Check"
            check_all_health
            ;;
        "build")
            build_images "$service"
            ;;
        "cleanup"|"clean")
            cleanup_resources
            ;;
        "reset"|"destroy")
            reset_all
            ;;
        "help"|"-h"|"--help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"