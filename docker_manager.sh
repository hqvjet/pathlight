#!/bin/bash

# ==============================================================================
# 🐳 PATHLIGHT DOCKER MANAGEMENT SCRIPT
# ==============================================================================
# All-in-one Docker management tool for PathLight project
# Direct service access architecture
# 
# Usage: ./docker_manager.sh [command]
# Commands:
#   status    - Show comprehensive status of all services
#   services  - Show all service URLs and endpoints
#   restart   - Restart all services (preserves data)  
#   cleanup   - Clean unused Docker resources
#   reset     - Complete reset (DESTROYS ALL DATA!)
#   logs      - Show recent logs from all services
#   build     - Rebuild all images
#   help      - Show this help message
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

# Helper functions
print_header() {
    echo -e "${BLUE}🐳 PathLight Docker Manager${NC}"
    echo -e "${BLUE}==============================${NC}"
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

# Command functions
show_status() {
    print_header
    print_section "1️⃣ Container Status"
    
    if docker-compose ps 2>/dev/null; then
        print_success "Container list retrieved"
    else
        print_error "Could not get container status"
        return 1
    fi
    
    echo ""
    print_section "2️⃣ Service Architecture"
    print_info "Direct service access - each service runs independently:"
    echo "   📊 Auth Service    → http://localhost:8001"
    echo "   👤 User Service    → http://localhost:8002" 
    echo "   📚 Course Service  → http://localhost:8003"
    echo "   📝 Quiz Service    → http://localhost:8004"
    echo "   🤖 Agentic Service → http://localhost:8005"
    
    echo ""
    print_section "3️⃣ Service Health Checks"
    
    services=(
        "auth-service:8001:/health" 
        "user-service:8002:/health"
        "course-service:8003:/health"
        "quiz-service:8004:/health"
        "agentic-service:8005:/health"
    )

    for service in "${services[@]}"; do
        IFS=':' read -r name port endpoint <<< "$service"
        echo -n "   $name: "
        
        if curl -s -f "http://localhost:$port$endpoint" > /dev/null 2>&1; then
            response=$(curl -s "http://localhost:$port$endpoint" | head -c 100)
            print_success "Healthy - $response"
        else
            print_error "Not responding"
        fi
    done

    echo ""
    print_section "4️⃣ Database Status"
    
    if docker exec pathlight-postgres-1 pg_isready -U postgres > /dev/null 2>&1; then
        print_success "PostgreSQL is running"
        
        echo "   Database statistics:"
        docker exec pathlight-postgres-1 psql -U postgres -d pathlight -c "
            SELECT 
                'Users' as table_name, COUNT(*) as records 
            FROM users
            UNION ALL
            SELECT 
                'Admins' as table_name, COUNT(*) as records 
            FROM admins
            ORDER BY table_name;
        " 2>/dev/null | sed 's/^/   /' || print_warning "Could not retrieve database statistics"
    else
        print_error "PostgreSQL is not responding"
    fi

    echo ""
    print_section "5️⃣ Resource Usage"
    
    if docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" $(docker ps --format "{{.Names}}" | grep pathlight) 2>/dev/null; then
        print_success "Resource usage retrieved"
    else
        print_warning "No PathLight containers running"
    fi

    echo ""
    print_info "Quick Access URLs:"
    echo "   - Auth Service: http://localhost:8001/docs"
    echo "   - User Service: http://localhost:8002/docs"
    echo "   - Course Service: http://localhost:8003/docs"
    echo "   - Quiz Service: http://localhost:8004/docs"
    echo "   - Agentic Service: http://localhost:8005/docs"
}

restart_services() {
    print_header
    print_section "🔄 Restarting PathLight Services"
    
    echo "1️⃣ Stopping all services..."
    docker-compose down
    print_success "All services stopped"

    read -p "Do you want to rebuild images? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "2️⃣ Rebuilding images..."
        docker-compose build --no-cache
        print_success "Images rebuilt"
    else
        echo "2️⃣ Skipping image rebuild"
    fi

    echo "3️⃣ Starting all services..."
    docker-compose up -d
    print_success "Services started"

    echo "4️⃣ Waiting for services to be ready..."
    sleep 10

    echo "5️⃣ Checking service health..."
    show_health_check

    print_success "Restart completed!"
}

cleanup_resources() {
    print_header
    print_section "🧹 Cleaning Up Docker Resources"
    
    echo "1️⃣ Removing unused containers..."
    UNUSED_CONTAINERS=$(docker ps -aq --filter "status=exited")
    if [ ! -z "$UNUSED_CONTAINERS" ]; then
        docker rm $UNUSED_CONTAINERS
        print_success "Removed unused containers"
    else
        print_info "No unused containers found"
    fi

    echo "2️⃣ Removing unused images..."
    UNUSED_IMAGES=$(docker images -f "dangling=true" -q)
    if [ ! -z "$UNUSED_IMAGES" ]; then
        docker rmi $UNUSED_IMAGES
        print_success "Removed dangling images"
    else
        print_info "No dangling images found"
    fi

    echo "3️⃣ Removing unused volumes..."
    docker volume prune -f > /dev/null
    print_success "Removed unused volumes"

    echo "4️⃣ Removing unused networks..."
    docker network prune -f > /dev/null
    print_success "Removed unused networks"

    echo "5️⃣ Running system cleanup..."
    docker system prune -f > /dev/null
    print_success "System cleanup completed"

    echo ""
    print_info "Disk space saved:"
    docker system df
}

reset_all() {
    print_header
    print_section "⚠️  COMPLETE DOCKER RESET"
    
    print_warning "This will completely reset your Docker environment!"
    echo "    - Stop all containers"
    echo "    - Remove all containers" 
    echo "    - Remove all volumes (DATABASE WILL BE LOST!)"
    echo "    - Remove all networks"
    echo "    - Remove all images"
    echo ""

    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Operation cancelled."
        return 0
    fi

    echo ""
    print_section "🔄 Starting Docker reset process"

    echo "1️⃣ Stopping all containers..."
    docker-compose down --remove-orphans || print_warning "Some containers may not exist"

    echo "2️⃣ Removing all containers..."
    CONTAINERS=$(docker ps -aq --filter "name=pathlight")
    if [ ! -z "$CONTAINERS" ]; then
        docker rm -f $CONTAINERS
        print_success "Removed containers: $CONTAINERS"
    else
        print_info "No PathLight containers found"
    fi

    echo "3️⃣ Removing all volumes..."
    VOLUMES=$(docker volume ls -q --filter "name=pathlight")
    if [ ! -z "$VOLUMES" ]; then
        docker volume rm -f $VOLUMES
        print_success "Removed volumes: $VOLUMES"
    else
        print_info "No PathLight volumes found"
    fi

    echo "4️⃣ Removing all networks..."
    NETWORKS=$(docker network ls -q --filter "name=pathlight")
    if [ ! -z "$NETWORKS" ]; then
        docker network rm $NETWORKS
        print_success "Removed networks: $NETWORKS"
    else
        print_info "No PathLight networks found"
    fi

    echo "5️⃣ Removing all images..."
    IMAGES=$(docker images -q --filter "reference=pathlight*")
    if [ ! -z "$IMAGES" ]; then
        docker rmi -f $IMAGES
        print_success "Removed images: $IMAGES"
    else
        print_info "No PathLight images found"
    fi

    echo "6️⃣ Cleaning up Docker system..."
    docker system prune -af --volumes

    print_success "Docker reset completed successfully!"
    echo ""
    print_info "Next steps:"
    echo "   1. Run: ./docker_manager.sh build"
    echo "   2. Run: docker-compose up -d"
    echo "   3. Run database migrations if needed"
}

show_logs() {
    print_header
    print_section "📋 Recent Service Logs"
    
    containers=$(docker ps --format "{{.Names}}" | grep pathlight)
    if [ -z "$containers" ]; then
        print_warning "No PathLight containers running"
        return 1
    fi
    
    for container in $containers; do
        echo ""
        print_section "$container"
        docker logs --tail 10 "$container" 2>/dev/null | sed 's/^/   /' || print_warning "Could not retrieve logs for $container"
    done
}

build_images() {
    print_header
    print_section "🔨 Building All Images"
    
    echo "Building PathLight images..."
    docker-compose build --no-cache
    print_success "All images built successfully!"
    
    echo ""
    print_info "Built images:"
    docker images --filter "reference=pathlight*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
}

show_health_check() {
    services=(
        "auth-service:8001"
        "user-service:8002"
        "course-service:8003"
        "quiz-service:8004"
        "agentic-service:8005"
    )

    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        echo -n "   $name: "
        
        if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1; then
            print_success "Healthy"
        else
            print_error "Not responding"
        fi
    done
}

show_services() {
    print_header
    print_section "🌐 Pathlight Services (Direct Access)"
    
    echo "📊 Authentication Service:"
    echo "   URL: http://localhost:8001"
    echo "   API: http://localhost:8001/docs"
    echo "   Health: http://localhost:8001/health"
    echo ""
    
    echo "👤 User Management Service:"
    echo "   URL: http://localhost:8002"
    echo "   API: http://localhost:8002/docs"
    echo "   Health: http://localhost:8002/health"
    echo ""
    
    echo "📚 Course Service:"
    echo "   URL: http://localhost:8003"
    echo "   API: http://localhost:8003/docs"
    echo "   Health: http://localhost:8003/health"
    echo ""
    
    echo "📝 Quiz Service:"
    echo "   URL: http://localhost:8004"
    echo "   API: http://localhost:8004/docs"
    echo "   Health: http://localhost:8004/health"
    echo ""
    
    echo "🤖 Agentic Service:"
    echo "   URL: http://localhost:8005"
    echo "   API: http://localhost:8005/docs"
    echo "   Health: http://localhost:8005/health"
    echo ""
    
    echo "🗃️ Database:"
    echo "   PostgreSQL: localhost:5432"
    echo "   Database: pathlight"
    echo ""
    
    print_info "All services are accessible directly"
}

show_help() {
    print_header
    echo "Usage: $0 [command]"
    echo ""
    echo "🏗️ Architecture: Direct Service Access"
    echo "   Each service runs independently on its own port"
    echo ""
    echo "Commands:"
    echo "  status    - Show comprehensive status of all services"
    echo "  services  - Show all service URLs and endpoints"
    echo "  restart   - Restart all services (preserves data)"  
    echo "  cleanup   - Clean unused Docker resources"
    echo "  reset     - Complete reset (DESTROYS ALL DATA!)"
    echo "  logs      - Show recent logs from all services"
    echo "  build     - Rebuild all images"
    echo "  help      - Show this help message"
    echo ""
    echo "🌐 Quick Service Access:"
    echo "  Auth Service:    http://localhost:8001/docs"
    echo "  User Service:    http://localhost:8002/docs"
    echo "  Course Service:  http://localhost:8003/docs"
    echo "  Quiz Service:    http://localhost:8004/docs"
    echo "  Agentic Service: http://localhost:8005/docs"
    echo ""
    echo "Examples:"
    echo "  $0 status                    # Check service status"
    echo "  $0 services                  # Show all service URLs"
    echo "  $0 restart                   # Restart services"
    echo "  $0 cleanup                   # Clean up resources"
    echo "  $0 reset                     # Reset everything"
    echo ""
    print_info "For more information, visit: https://github.com/pathlight"
}

# Main script logic
case "${1:-help}" in
    "status"|"s")
        show_status
        ;;
    "services"|"urls"|"sv")
        show_services
        ;;
    "restart"|"r")
        restart_services
        ;;
    "cleanup"|"c")
        cleanup_resources
        ;;
    "reset"|"hard-reset")
        reset_all
        ;;
    "logs"|"l")
        show_logs
        ;;
    "build"|"b")
        build_images
        ;;
    "help"|"h"|*)
        show_help
        ;;
esac
