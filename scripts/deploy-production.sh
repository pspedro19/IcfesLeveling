#!/bin/bash
# ICFES Leveling Production Deployment Script
set -e

echo "🚀 ICFES Leveling Production Deployment"
echo "======================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check required commands
REQUIRED_COMMANDS=("docker" "docker-compose" "openssl" "curl")
for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v $cmd &> /dev/null; then
        print_error "$cmd is required but not installed"
        exit 1
    fi
done

print_status "All required commands found"

# Check environment file
if [[ ! -f ".env.production" ]]; then
    print_warning ".env.production not found"
    if [[ -f "scripts/generate-secrets.sh" ]]; then
        bash scripts/generate-secrets.sh
    else
        print_error "Please create .env.production with secure values"
        exit 1
    fi
fi

# Load environment
set -a
source .env.production
set +a

print_success "Environment variables loaded"

# Create directories
print_status "Creating production directories..."
mkdir -p logs/{nginx,postgres,redis,clickhouse,backend,frontend,websocket,ai-service}
mkdir -p backup

# Build images
print_status "Building production Docker images..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Database backup
if docker ps -a | grep -q "icfes_postgres"; then
    print_status "Creating database backup..."
    BACKUP_FILE="backup/database-$(date +%Y%m%d-%H%M%S).sql"
    docker exec icfes_postgres pg_dump -U gameplay -d gameplay_db > $BACKUP_FILE
    print_success "Database backed up to $BACKUP_FILE"
fi

# Deploy
print_status "Stopping development containers..."
docker-compose down

print_status "Starting production services..."
docker-compose -f docker-compose.prod.yml up -d

print_status "Waiting for services to start..."
sleep 30

# Health checks
print_status "Running health checks..."
docker-compose -f docker-compose.prod.yml ps

print_success "🎉 Production deployment completed!"
print_warning "Configure SSL, firewall, monitoring, and DNS"
