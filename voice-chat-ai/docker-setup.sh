#!/bin/bash

# Enhanced AI Interviewer Bot Docker Setup Script
# Automates the complete Docker deployment process

set -e  # Exit on any error

echo "🚀 Enhanced AI Interviewer Bot - Docker Setup"
echo "=============================================="

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

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Docker and Docker Compose are installed"
}

# Create environment file
setup_environment() {
    print_status "Setting up environment variables..."
    
    if [ ! -f .env ]; then
        if [ -f env.docker.example ]; then
            cp env.docker.example .env
            print_success "Created .env file from template"
            print_warning "Please update .env with your actual API keys before continuing"
            echo ""
            echo "Required variables to update in .env:"
            echo "- OPENAI_API_KEY=your_actual_key"
            echo "- POSTGRES_PASSWORD=your_secure_password"
            echo ""
            read -p "Have you updated the .env file? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_error "Please update .env file and run the script again"
                exit 1
            fi
        else
            print_error "env.docker.example not found. Please create .env file manually."
            exit 1
        fi
    else
        print_success ".env file already exists"
    fi
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p outputs interview-outputs models logs database monitoring/grafana monitoring/prometheus nginx/ssl
    
    # Create .gitkeep files for empty directories
    touch outputs/.gitkeep interview-outputs/.gitkeep models/.gitkeep logs/.gitkeep
    
    print_success "Directories created"
}

# Create NGINX configuration
create_nginx_config() {
    print_status "Creating NGINX configuration..."
    
    mkdir -p nginx
    
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream interview_app {
        server app:8000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        client_max_body_size 100M;
        
        location / {
            proxy_pass http://interview_app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF
    
    print_success "NGINX configuration created"
}

# Create monitoring configurations
create_monitoring_configs() {
    print_status "Creating monitoring configurations..."
    
    # Prometheus configuration
    cat > monitoring/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'interview-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'elasticsearch'
    static_configs:
      - targets: ['elasticsearch:9200']
EOF

    print_success "Monitoring configurations created"
}

# Build and start services
start_services() {
    print_status "Building and starting Docker services..."
    
    # Build the application image
    print_status "Building application image..."
    docker-compose build --no-cache
    
    # Start infrastructure services first
    print_status "Starting infrastructure services..."
    docker-compose up -d postgres redis elasticsearch
    
    # Wait for services to be healthy
    print_status "Waiting for infrastructure services to be ready..."
    
    # Wait for PostgreSQL
    echo -n "Waiting for PostgreSQL"
    while ! docker-compose exec postgres pg_isready -U interview_admin -d interview_bot > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "PostgreSQL is ready"
    
    # Wait for Redis
    echo -n "Waiting for Redis"
    while ! docker-compose exec redis redis-cli ping > /dev/null 2>&1; do
        echo -n "."
        sleep 2
    done
    echo ""
    print_success "Redis is ready"
    
    # Wait for Elasticsearch
    echo -n "Waiting for Elasticsearch"
    while ! curl -s http://localhost:9200/_cluster/health > /dev/null 2>&1; do
        echo -n "."
        sleep 5
    done
    echo ""
    print_success "Elasticsearch is ready"
    
    # Start application
    print_status "Starting application..."
    docker-compose up -d app
    
    # Wait for application to be ready
    echo -n "Waiting for application"
    while ! curl -s http://localhost:8000/api/enhanced/system/health > /dev/null 2>&1; do
        echo -n "."
        sleep 3
    done
    echo ""
    print_success "Application is ready"
}

# Initialize the enhanced system
initialize_system() {
    print_status "Initializing enhanced system..."
    
    # Run setup script inside container
    docker-compose exec app python setup_enhanced_system.py
    
    print_success "Enhanced system initialized"
}

# Display service information
show_services() {
    echo ""
    echo "🎉 Enhanced AI Interviewer Bot is now running!"
    echo "=============================================="
    echo ""
    echo "📋 Service URLs:"
    echo "  🤖 AI Interviewer API:    http://localhost:8000"
    echo "  📊 API Documentation:     http://localhost:8000/docs"
    echo "  🗄️  PostgreSQL:           localhost:5432"
    echo "  ⚡ Redis:                 localhost:6379"
    echo "  🔍 Elasticsearch:         http://localhost:9200"
    echo ""
    echo "🔧 Management Commands:"
    echo "  View logs:                docker-compose logs -f app"
    echo "  Stop services:            docker-compose down"
    echo "  Restart app:              docker-compose restart app"
    echo "  Database shell:           docker-compose exec postgres psql -U interview_admin -d interview_bot"
    echo "  Redis shell:              docker-compose exec redis redis-cli"
    echo ""
    echo "📈 Optional Monitoring (run with --profile monitoring):"
    echo "  Kibana (Elasticsearch):   http://localhost:5601"
    echo "  Redis Commander:          http://localhost:8081"
    echo ""
    echo "🧪 Test the system:"
    echo "  Health check:             curl http://localhost:8000/api/enhanced/system/health"
    echo "  System stats:             curl http://localhost:8000/api/enhanced/system/stats"
}

# Main execution
main() {
    echo ""
    print_status "Starting setup process..."
    
    check_docker
    setup_environment
    create_directories
    create_nginx_config
    create_monitoring_configs
    start_services
    initialize_system
    show_services
    
    echo ""
    print_success "Setup completed successfully! 🎉"
}

# Handle script arguments
case "${1:-}" in
    "prod")
        print_status "Using production configuration..."
        export COMPOSE_FILE=docker-compose.prod.yml
        ;;
    "monitoring")
        print_status "Starting with monitoring services..."
        export COMPOSE_PROFILES=monitoring
        ;;
    "clean")
        print_status "Cleaning up Docker resources..."
        docker-compose down -v
        docker system prune -f
        print_success "Cleanup completed"
        exit 0
        ;;
    "logs")
        docker-compose logs -f
        exit 0
        ;;
    "restart")
        print_status "Restarting services..."
        docker-compose restart
        print_success "Services restarted"
        exit 0
        ;;
    "help"|"-h"|"--help")
        echo "Enhanced AI Interviewer Bot Docker Setup"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  (none)      Start development environment"
        echo "  prod        Start production environment"
        echo "  monitoring  Start with monitoring services"
        echo "  clean       Clean up Docker resources"
        echo "  logs        Show application logs"
        echo "  restart     Restart all services"
        echo "  help        Show this help message"
        exit 0
        ;;
esac

# Run main function
main
