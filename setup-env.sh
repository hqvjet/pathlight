#!/bin/bash
# =============================================================================
# 🚀 PathLight - Environment Setup Script
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}[SETUP]${NC} $1"
}

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

# Function to generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
}

# Function to generate JWT secret
generate_jwt_secret() {
    openssl rand -hex 32
}

# Main setup function
setup_environment() {
    print_header "🚀 Welcome to PathLight Environment Setup!"
    echo ""
    
    # Check if .env.local already exists
    if [ -f ".env.local" ]; then
        print_warning ".env.local already exists!"
        echo ""
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Setup cancelled. Existing .env.local preserved."
            exit 0
        fi
    fi
    
    print_status "Creating .env.local from template..."
    cp .env.local.template .env.local
    
    print_status "Configuring database credentials..."
    
    # Get database configuration
    echo ""
    echo "🗄️ Database Configuration:"
    read -p "Enter PostgreSQL username (default: pathlight_user): " db_user
    db_user=${db_user:-pathlight_user}
    
    read -p "Enter PostgreSQL database name (default: pathlight_db): " db_name
    db_name=${db_name:-pathlight_db}
    
    echo ""
    read -p "Generate random password? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        read -s -p "Enter PostgreSQL password: " db_password
        echo ""
    else
        db_password=$(generate_password)
        print_success "Generated random password: $db_password"
    fi
    
    # Generate JWT secrets
    print_status "Generating JWT secrets..."
    jwt_secret=$(generate_jwt_secret)
    jwt_refresh_secret=$(generate_jwt_secret)
    
    # Generate admin password
    echo ""
    read -p "Generate random admin password? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        read -s -p "Enter admin password: " admin_password
        echo ""
    else
        admin_password=$(generate_password)
        print_success "Generated random admin password: $admin_password"
    fi
    
    # Update .env.local with values
    sed -i "s/your_db_user/$db_user/g" .env.local
    sed -i "s/your_secure_password/$db_password/g" .env.local
    sed -i "s/pathlight_db/$db_name/g" .env.local
    sed -i "s/your_jwt_secret_key_here/$jwt_secret/g" .env.local
    sed -i "s/your_jwt_refresh_secret_key_here/$jwt_refresh_secret/g" .env.local
    sed -i "s/your_admin_password/$admin_password/g" .env.local
    
    print_success "Environment configuration completed!"
    echo ""
    echo "📋 Configuration Summary:"
    echo "  Database User: $db_user"
    echo "  Database Name: $db_name"
    echo "  Database Password: $db_password"
    echo "  Admin Password: $admin_password"
    echo ""
    echo "📁 Configuration saved to: .env.local"
    echo ""
    print_warning "⚠️  IMPORTANT: Keep your .env.local file secure and never commit it to version control!"
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Review and customize .env.local if needed"
    echo "  2. Run: cd services && ./docker-manager.sh start-all"
    echo "  3. Or start individual services: cd services/auth-service && ./docker-manager.sh start"
    echo ""
}

# Check if running from correct directory
if [ ! -f ".env.local.template" ]; then
    print_error "Please run this script from the PathLight project root directory"
    print_error "The .env.local.template file is required"
    exit 1
fi

# Check required tools
if ! command -v openssl &> /dev/null; then
    print_error "openssl is required but not installed"
    print_error "Please install openssl first"
    exit 1
fi

# Run setup
setup_environment
