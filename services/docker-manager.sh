#!/bin/bash
# =============================================================================
# 🐳 PathLight - Master Docker Manager
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${PURPLE}[HEADER]${NC} $1"
}

print_service() {
    echo -e "${CYAN}[SERVICE]${NC} $1"
}

# Service definitions
declare -A SERVICES=(
    ["auth"]="auth-service:8001"
    ["user"]="user-service:8002"
    ["course"]="course-service:8003"
    ["quiz"]="quiz-service:8004"
)

# Function to show usage
show_usage() {
    print_header "🐳 PathLight - Master Docker Manager"
    echo "====================================="
    echo ""
    echo "Usage: $0 [command] [service(s)]"
    echo ""
    echo "Commands:"
    echo "  start-all    - Start all services in correct order"
    echo "  stop-all     - Stop all services"
    echo "  restart-all  - Restart all services"
    echo "  status-all   - Show status of all services"
    echo "  clean-all    - Clean all services and networks"
    echo "  clean-db     - Clean database and volumes"
    echo ""
    echo "  start [service]   - Start specific service"
    echo "  stop [service]    - Stop specific service"
    echo "  restart [service] - Restart specific service"
    echo "  status [service]  - Show status of specific service"
    echo "  logs [service]    - Show logs of specific service"
    echo ""
    echo "Services:"
    echo "  auth     - Auth Service (port 8001)"
    echo "  user     - User Service (port 8002)"
    echo "  course   - Course Service (port 8003)"
    echo "  quiz     - Quiz Service (port 8004)"
    echo ""
    echo "Examples:"
    echo "  $0 start-all"
    echo "  $0 start auth user"
    echo "  $0 stop user"
    echo "  $0 logs auth"
    echo "  $0 status-all"
    echo "  $0 clean-db"
    echo ""
}

# Function to check if service directory exists
check_service_dir() {
    local service="$1"
    if [ ! -d "$service" ]; then
        print_error "Service directory '$service' not found"
        return 1
    fi
    return 0
}

# Function to start a single service
start_service() {
    local service="$1"
    local service_dir="${service}-service"
    
    check_service_dir "$service_dir" || return 1
    
    print_service "Starting $service service..."
    cd "$service_dir"
    
    if [ ! -f "docker-manager.sh" ]; then
        print_error "docker-manager.sh not found in $service_dir"
        cd ..
        return 1
    fi
    
    chmod +x docker-manager.sh
    ./docker-manager.sh start
    cd ..
    
    print_success "$service service started"
}

# Function to stop a single service
stop_service() {
    local service="$1"
    local service_dir="${service}-service"
    
    check_service_dir "$service_dir" || return 1
    
    print_service "Stopping $service service..."
    cd "$service_dir"
    
    if [ -f "docker-manager.sh" ]; then
        chmod +x docker-manager.sh
        ./docker-manager.sh stop
    fi
    cd ..
    
    print_success "$service service stopped"
}

# Function to show status of a single service
status_service() {
    local service="$1"
    local service_dir="${service}-service"
    
    check_service_dir "$service_dir" || return 1
    
    print_service "Status of $service service:"
    cd "$service_dir"
    
    if [ -f "docker-manager.sh" ]; then
        chmod +x docker-manager.sh
        ./docker-manager.sh status
    fi
    cd ..
}

# Function to show logs of a single service
logs_service() {
    local service="$1"
    local service_dir="${service}-service"
    
    check_service_dir "$service_dir" || return 1
    
    print_service "Logs of $service service:"
    cd "$service_dir"
    
    if [ -f "docker-manager.sh" ]; then
        chmod +x docker-manager.sh
        ./docker-manager.sh logs
    fi
    cd ..
}

# Function to start all services in correct order
start_all_services() {
    print_header "🚀 Starting all PathLight services..."
    
    # Start backend services
    for service in auth user course quiz; do
        start_service "$service"
        sleep 2  # Small delay between services
    done
    
    print_header "✅ All services started!"
    echo ""
    echo "🔗 Service URLs:"
    echo "   🔑 Auth Service: http://localhost:8001"
    echo "   👤 User Service: http://localhost:8002"
    echo "   📚 Course Service: http://localhost:8003"
    echo "   🧠 Quiz Service: http://localhost:8004"
    echo ""
    echo "📚 API Documentation:"
    echo "   🔑 Auth: http://localhost:8001/docs"
    echo "   👤 User: http://localhost:8002/docs"
    echo "   📚 Course: http://localhost:8003/docs"
    echo "   🧠 Quiz: http://localhost:8004/docs"
}

# Function to stop all services
stop_all_services() {
    print_header "🛑 Stopping all PathLight services..."
    
    # Stop all services
    for service in quiz course user auth; do
        stop_service "$service" 2>/dev/null || true
    done
    
    print_header "✅ All services stopped!"
}

# Function to show status of all services
status_all_services() {
    print_header "📊 PathLight Services Status"
    echo "============================="
    echo ""
    
    for service in auth user course quiz; do
        status_service "$service"
        echo ""
    done
}

# Function to clean all services
clean_all_services() {
    print_header "🧹 Cleaning all PathLight services..."
    
    # Stop all services first
    stop_all_services
    
    # Clean each service
    for service in quiz course user auth; do
        local service_dir="${service}-service"
        
        if [ -d "$service_dir" ] && [ -f "$service_dir/docker-manager.sh" ]; then
            print_service "Cleaning $service service..."
            cd "$service_dir"
            chmod +x docker-manager.sh
            ./docker-manager.sh clean 2>/dev/null || true
            cd ..
        fi
    done
    
    # Clean shared network
    print_status "Cleaning shared network..."
    docker network rm pathlight-network 2>/dev/null || print_warning "Network already removed"
    
    print_header "✅ All services cleaned!"
}

# Function to clean database and volumes
clean_database() {
    print_header "🗑️ Cleaning PathLight database and volumes..."
    
    # Stop all services first
    stop_all_services
    
    # Stop and remove PostgreSQL container
    print_status "Stopping PostgreSQL container..."
    docker stop pathlight-postgres 2>/dev/null || print_warning "PostgreSQL container not running"
    docker rm pathlight-postgres 2>/dev/null || print_warning "PostgreSQL container not found"
    
    # Remove PostgreSQL volume
    print_status "Removing PostgreSQL volume..."
    docker volume rm postgres_data 2>/dev/null || print_warning "PostgreSQL volume not found"
    
    # Remove all PathLight related volumes
    print_status "Removing other volumes..."
    docker volume ls -q | grep -E "(pathlight|postgres)" | xargs -r docker volume rm 2>/dev/null || true
    
    # Clean unused volumes
    print_status "Cleaning unused volumes..."
    docker volume prune -f 2>/dev/null || true
    
    print_header "✅ Database and volumes cleaned!"
    print_warning "All data has been permanently deleted!"
}

# Main script logic
case "${1:-help}" in
    "start-all")
        start_all_services
        ;;
    "stop-all")
        stop_all_services
        ;;
    "restart-all")
        stop_all_services
        sleep 2
        start_all_services
        ;;
    "status-all")
        status_all_services
        ;;
    "clean-all")
        clean_all_services
        ;;
    "clean-db")
        clean_database
        ;;
    "start")
        shift
        if [ $# -eq 0 ]; then
            print_error "No service specified"
            show_usage
            exit 1
        fi
        for service in "$@"; do
            if [[ ! " ${!SERVICES[@]} " =~ " ${service} " ]]; then
                print_error "Unknown service: $service"
                continue
            fi
            start_service "$service"
        done
        ;;
    "stop")
        shift
        if [ $# -eq 0 ]; then
            print_error "No service specified"
            show_usage
            exit 1
        fi
        for service in "$@"; do
            if [[ ! " ${!SERVICES[@]} " =~ " ${service} " ]]; then
                print_error "Unknown service: $service"
                continue
            fi
            stop_service "$service"
        done
        ;;
    "restart")
        shift
        if [ $# -eq 0 ]; then
            print_error "No service specified"
            show_usage
            exit 1
        fi
        for service in "$@"; do
            if [[ ! " ${!SERVICES[@]} " =~ " ${service} " ]]; then
                print_error "Unknown service: $service"
                continue
            fi
            stop_service "$service"
            sleep 1
            start_service "$service"
        done
        ;;
    "status")
        shift
        if [ $# -eq 0 ]; then
            status_all_services
        else
            for service in "$@"; do
                if [[ ! " ${!SERVICES[@]} " =~ " ${service} " ]]; then
                    print_error "Unknown service: $service"
                    continue
                fi
                status_service "$service"
            done
        fi
        ;;
    "logs")
        shift
        if [ $# -eq 0 ]; then
            print_error "No service specified"
            show_usage
            exit 1
        fi
        service="$1"
        if [[ ! " ${!SERVICES[@]} " =~ " ${service} " ]]; then
            print_error "Unknown service: $service"
            exit 1
        fi
        logs_service "$service"
        ;;
    "help"|"--help"|"-h"|"")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
