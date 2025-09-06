#!/bin/bash

# Production deployment script for ICFES Leveling Platform
# This script handles the complete production deployment process

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEPLOY_ENV=${1:-production}
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
COMPOSE_FILE="docker-compose.prod.yml"
LOG_FILE="logs/deployment-$(date +%Y%m%d_%H%M%S).log"

# Create necessary directories
mkdir -p logs backups

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO $(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if required files exist
    required_files=(
        "$COMPOSE_FILE"
        ".env.production"
        "apps/backend/Dockerfile.production"
        "apps/frontend/Dockerfile.production"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            error "Required file not found: $file"
            exit 1
        fi
    done
    
    log "Prerequisites check passed ✅"
}

# Create backup of current deployment
create_backup() {
    if [ "$DEPLOY_ENV" = "production" ]; then
        log "Creating backup before deployment..."
        
        # Create backup directory
        mkdir -p "$BACKUP_DIR"
        
        # Backup database
        docker-compose -f $COMPOSE_FILE exec -T postgres pg_dumpall -c -U gameplay > "$BACKUP_DIR/database.sql" || warning "Failed to backup database"
        
        # Backup volumes
        docker run --rm -v icfes_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/postgres_data.tar.gz -C /data . || warning "Failed to backup postgres volume"
        docker run --rm -v icfes_redis_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/redis_data.tar.gz -C /data . || warning "Failed to backup redis volume"
        docker run --rm -v icfes_clickhouse_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/clickhouse_data.tar.gz -C /data . || warning "Failed to backup clickhouse volume"
        
        # Backup configuration files
        cp .env.production "$BACKUP_DIR/"
        cp $COMPOSE_FILE "$BACKUP_DIR/"
        
        log "Backup created at $BACKUP_DIR ✅"
    fi
}

# Build and test images
build_images() {
    log "Building production images..."
    
    # Set environment variables for build
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    
    # Build backend image
    info "Building backend image..."
    docker build -f apps/backend/Dockerfile.production -t icfes-backend:latest apps/backend/
    
    # Build frontend image
    info "Building frontend image..."
    docker build -f apps/frontend/Dockerfile.production -t icfes-frontend:latest apps/frontend/
    
    # Build AI service image
    info "Building AI service image..."
    docker build -f apps/ai-service/Dockerfile.production -t icfes-ai-service:latest apps/ai-service/
    
    # Build WebSocket service image
    info "Building WebSocket service image..."
    docker build -f apps/websocket/Dockerfile.production -t icfes-websocket:latest apps/websocket/
    
    log "All images built successfully ✅"
}

# Run health checks
run_health_checks() {
    log "Running health checks..."
    
    # Check if services are responding
    services=(
        "http://localhost:4001/api/health:Frontend"
        "http://localhost:4000/health:Backend"
        "http://localhost:8003/health:WebSocket"
    )
    
    for service_info in "${services[@]}"; do
        IFS=":" read -r url name <<< "$service_info"
        info "Checking $name health at $url"
        
        for i in {1..30}; do
            if curl -f -s "$url" > /dev/null 2>&1; then
                log "$name is healthy ✅"
                break
            else
                if [ $i -eq 30 ]; then
                    error "$name health check failed after 30 attempts"
                    return 1
                fi
                sleep 2
            fi
        done
    done
    
    log "All health checks passed ✅"
}

# Database migration and initialization
run_migrations() {
    log "Running database migrations..."
    
    # Wait for database to be ready
    info "Waiting for database to be ready..."
    docker-compose -f $COMPOSE_FILE exec backend python -c "
import time
import psycopg2
from app.core.config import settings

max_retries = 30
for i in range(max_retries):
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        conn.close()
        print('Database is ready!')
        break
    except Exception as e:
        if i == max_retries - 1:
            raise e
        time.sleep(2)
"
    
    # Run migrations
    docker-compose -f $COMPOSE_FILE exec backend python -m alembic upgrade head || error "Migration failed"
    
    # Initialize data
    docker-compose -f $COMPOSE_FILE exec backend python -m scripts.initialize_all_data || warning "Data initialization had warnings"
    
    log "Database migrations completed ✅"
}

# SSL and security setup
setup_ssl() {
    log "Setting up SSL and security..."
    
    # Generate SSL certificates if they don't exist
    if [ ! -f "config/nginx/ssl/cert.pem" ]; then
        info "Generating SSL certificates..."
        mkdir -p config/nginx/ssl
        
        # Generate self-signed certificate for development
        # In production, use proper certificates from Let's Encrypt or CA
        openssl req -x509 -newkey rsa:4096 -keyout config/nginx/ssl/key.pem -out config/nginx/ssl/cert.pem -days 365 -nodes -subj "/CN=icfes-leveling.com"
    fi
    
    # Set proper permissions
    chmod 600 config/nginx/ssl/key.pem
    chmod 644 config/nginx/ssl/cert.pem
    
    log "SSL setup completed ✅"
}

# Deploy services
deploy_services() {
    log "Deploying services..."
    
    # Copy production environment file
    cp .env.production .env
    
    # Pull latest images if using registry
    # docker-compose -f $COMPOSE_FILE pull
    
    # Deploy with zero-downtime if possible
    if docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        info "Performing rolling update..."
        
        # Update services one by one
        services=("backend" "frontend" "websocket" "ai-service")
        for service in "${services[@]}"; do
            info "Updating $service..."
            docker-compose -f $COMPOSE_FILE up -d --no-deps "$service"
            
            # Wait for service to be healthy
            sleep 10
        done
    else
        info "Starting all services..."
        docker-compose -f $COMPOSE_FILE up -d
    fi
    
    # Wait for services to stabilize
    sleep 30
    
    log "Services deployed successfully ✅"
}

# Cleanup old images and containers
cleanup() {
    log "Cleaning up old images and containers..."
    
    # Remove old containers
    docker container prune -f
    
    # Remove old images
    docker image prune -f
    
    # Remove unused volumes (be careful in production)
    if [ "$DEPLOY_ENV" != "production" ]; then
        docker volume prune -f
    fi
    
    log "Cleanup completed ✅"
}

# Performance optimization
optimize_performance() {
    log "Applying performance optimizations..."
    
    # Set kernel parameters for better performance
    if [ -f /proc/sys/vm/overcommit_memory ]; then
        echo 1 | sudo tee /proc/sys/vm/overcommit_memory > /dev/null
    fi
    
    # Optimize Docker daemon settings
    if [ -f /etc/docker/daemon.json ]; then
        info "Docker daemon already configured"
    else
        info "Configuring Docker daemon for production..."
        sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "storage-driver": "overlay2",
    "live-restore": true
}
EOF
        sudo systemctl restart docker
    fi
    
    log "Performance optimization completed ✅"
}

# Monitoring setup
setup_monitoring() {
    log "Setting up monitoring and alerting..."
    
    # Start monitoring stack
    if [ -f "monitoring/docker-compose.monitoring.yml" ]; then
        docker-compose -f monitoring/docker-compose.monitoring.yml up -d
        
        # Wait for Prometheus and Grafana to be ready
        sleep 30
        
        info "Monitoring dashboard available at http://localhost:3000 (admin/admin)"
        info "Prometheus available at http://localhost:9090"
    else
        warning "Monitoring configuration not found, skipping..."
    fi
    
    log "Monitoring setup completed ✅"
}

# Rollback function
rollback() {
    error "Deployment failed. Initiating rollback..."
    
    if [ -d "$BACKUP_DIR" ]; then
        # Stop current services
        docker-compose -f $COMPOSE_FILE down
        
        # Restore database
        if [ -f "$BACKUP_DIR/database.sql" ]; then
            info "Restoring database..."
            docker-compose -f $COMPOSE_FILE up -d postgres
            sleep 10
            cat "$BACKUP_DIR/database.sql" | docker-compose -f $COMPOSE_FILE exec -T postgres psql -U gameplay -d gameplay_db
        fi
        
        # Restore volumes
        if [ -f "$BACKUP_DIR/postgres_data.tar.gz" ]; then
            docker run --rm -v icfes_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
        fi
        
        # Restore configuration
        cp "$BACKUP_DIR/.env.production" .env
        
        # Restart services with old configuration
        docker-compose -f $COMPOSE_FILE up -d
        
        log "Rollback completed ✅"
    else
        error "No backup found for rollback"
    fi
}

# Main deployment flow
main() {
    log "🚀 Starting ICFES Leveling Platform production deployment..."
    log "Deployment environment: $DEPLOY_ENV"
    
    # Trap errors and rollback
    trap rollback ERR
    
    # Run deployment steps
    check_prerequisites
    create_backup
    build_images
    setup_ssl
    deploy_services
    run_migrations
    run_health_checks
    optimize_performance
    setup_monitoring
    cleanup
    
    log "🎉 Deployment completed successfully!"
    log "Platform is now running at:"
    log "  - Frontend: https://localhost:4001"
    log "  - Backend API: https://localhost:4000"
    log "  - WebSocket: wss://localhost:8003"
    log "  - Monitoring: http://localhost:3000"
    
    info "Deployment log saved to: $LOG_FILE"
    info "Backup created at: $BACKUP_DIR"
}

# Command line options
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        if [ -z "$2" ]; then
            error "Please specify backup directory for rollback"
            exit 1
        fi
        BACKUP_DIR="$2"
        rollback
        ;;
    "health-check")
        run_health_checks
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        create_backup
        ;;
    *)
        echo "Usage: $0 {deploy|rollback <backup_dir>|health-check|cleanup|backup}"
        echo ""
        echo "Commands:"
        echo "  deploy        - Deploy the application (default)"
        echo "  rollback      - Rollback to a specific backup"
        echo "  health-check  - Check service health"
        echo "  cleanup       - Clean up old containers and images"
        echo "  backup        - Create backup only"
        exit 1
        ;;
esac