#!/bin/bash

# Production initialization script for ICFES Leveling Platform
# This script initializes the production environment with all necessary data

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LOG_FILE="logs/init-production-$(date +%Y%m%d_%H%M%S).log"
DATA_DIR="database/seed_data"
COMPOSE_FILE="docker-compose.prod.yml"

# Create logs directory
mkdir -p logs

# Logging functions
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
    log "Checking prerequisites for production initialization..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Production compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    # Check if environment file exists
    if [ ! -f ".env.production" ]; then
        error "Production environment file not found. Run generate-secrets.sh first."
        exit 1
    fi
    
    # Check if data directory exists
    if [ ! -d "$DATA_DIR" ]; then
        warning "Seed data directory not found: $DATA_DIR"
        mkdir -p "$DATA_DIR"
    fi
    
    log "Prerequisites check passed ✅"
}

# Wait for services to be ready
wait_for_services() {
    log "Waiting for services to be ready..."
    
    # Wait for PostgreSQL
    info "Waiting for PostgreSQL to be ready..."
    for i in {1..60}; do
        if docker-compose -f $COMPOSE_FILE exec -T postgres pg_isready -U gameplay -d gameplay_db &> /dev/null; then
            log "PostgreSQL is ready ✅"
            break
        else
            if [ $i -eq 60 ]; then
                error "PostgreSQL failed to start after 60 attempts"
                exit 1
            fi
            sleep 2
        fi
    done
    
    # Wait for Redis
    info "Waiting for Redis to be ready..."
    for i in {1..30}; do
        if docker-compose -f $COMPOSE_FILE exec -T redis redis-cli ping | grep -q PONG; then
            log "Redis is ready ✅"
            break
        else
            if [ $i -eq 30 ]; then
                error "Redis failed to start after 30 attempts"
                exit 1
            fi
            sleep 2
        fi
    done
    
    # Wait for ClickHouse
    info "Waiting for ClickHouse to be ready..."
    for i in {1..30}; do
        if docker-compose -f $COMPOSE_FILE exec -T clickhouse clickhouse-client --query "SELECT 1" &> /dev/null; then
            log "ClickHouse is ready ✅"
            break
        else
            if [ $i -eq 30 ]; then
                warning "ClickHouse failed to start after 30 attempts"
                # Continue without ClickHouse as it's optional for core functionality
            fi
            sleep 2
        fi
    done
}

# Initialize database schema
initialize_database() {
    log "Initializing database schema..."
    
    # Run database initialization scripts
    init_scripts=(
        "database/init/01-init.sql"
        "database/init/02-seed-data.sql"
        "database/init/03-admin-user.sql"
        "database/init/03-boss-tables.sql"
        "database/init/03-import-icfes-data.sql"
        "database/init/04-import-study-plan-templates.sql"
        "database/init/05-youtube-links.sql"
        "database/init/06-guild-system.sql"
        "database/init/07-achievement-system.sql"
        "database/init/08-virtual-economy.sql"
        "database/init/09-question-enhancements.sql"
        "database/init/10-study-plans-icfes.sql"
        "database/init/11-diagnostic-analytics.sql"
        "database/init/16-gamification-complete.sql"
        "database/init/17-gamification-sample-data.sql"
    )
    
    for script in "${init_scripts[@]}"; do
        if [ -f "$script" ]; then
            info "Running database script: $script"
            docker-compose -f $COMPOSE_FILE exec -T postgres psql -U gameplay -d gameplay_db -f "/docker-entrypoint-initdb.d/$(basename $script)" || warning "Failed to run $script"
        else
            warning "Database script not found: $script"
        fi
    done
    
    log "Database schema initialized ✅"
}

# Initialize ClickHouse analytics
initialize_clickhouse() {
    log "Initializing ClickHouse analytics..."
    
    clickhouse_scripts=(
        "database/clickhouse-init/01-init.sql"
        "database/clickhouse-init/01-analytics-setup.sql"
    )
    
    for script in "${clickhouse_scripts[@]}"; do
        if [ -f "$script" ]; then
            info "Running ClickHouse script: $script"
            docker-compose -f $COMPOSE_FILE exec -T clickhouse clickhouse-client --multiquery < "$script" || warning "Failed to run ClickHouse script $script"
        else
            warning "ClickHouse script not found: $script"
        fi
    done
    
    log "ClickHouse analytics initialized ✅"
}

# Load ICFES data
load_icfes_data() {
    log "Loading ICFES data..."
    
    # Check if Excel file exists
    excel_files=(
        "apps/backend/ICFES2.xlsx"
        "ICFES2.xlsx"
        "database/seed_data/ICFES2.xlsx"
    )
    
    excel_file=""
    for file in "${excel_files[@]}"; do
        if [ -f "$file" ]; then
            excel_file="$file"
            break
        fi
    done
    
    if [ -n "$excel_file" ]; then
        info "Found Excel file: $excel_file"
        info "Running Excel import script..."
        docker-compose -f $COMPOSE_FILE exec backend python -m scripts.import_icfes_excel || warning "ICFES Excel import had warnings"
    else
        warning "ICFES Excel file not found, skipping Excel import"
    fi
    
    # Load CSV catalogs
    csv_files=(
        "01_icfes_topics_catalog.csv"
        "01_icfes_youtube_catalog.csv"
        "topics_catalog.csv"
        "youtube_catalog_extendido_enriquecido.csv"
    )
    
    for csv_file in "${csv_files[@]}"; do
        csv_paths=(
            "database/seed_data/$csv_file"
            "database/$csv_file"
            "apps/backend/database/$csv_file"
        )
        
        found_csv=""
        for path in "${csv_paths[@]}"; do
            if [ -f "$path" ]; then
                found_csv="$path"
                break
            fi
        done
        
        if [ -n "$found_csv" ]; then
            info "Loading CSV file: $found_csv"
            docker-compose -f $COMPOSE_FILE exec backend python -m scripts.load_icfes_catalog --file="$csv_file" || warning "Failed to load $csv_file"
        else
            warning "CSV file not found: $csv_file"
        fi
    done
    
    log "ICFES data loading completed ✅"
}

# Initialize study plan templates
initialize_study_plans() {
    log "Initializing study plan templates..."
    
    # Run study plan initialization
    docker-compose -f $COMPOSE_FILE exec backend python -c "
from app.services.study_plan_service import StudyPlanService
from app.core.database import get_db

try:
    db = next(get_db())
    service = StudyPlanService(db)
    
    # Create default study plan templates
    templates = [
        {
            'name': 'Matemáticas Básica',
            'subject_id': 1,
            'difficulty_level': 1,
            'estimated_weeks': 8,
            'topics': ['Aritmética', 'Álgebra básica', 'Geometría básica']
        },
        {
            'name': 'Lectura Crítica Intermedia',
            'subject_id': 2,
            'difficulty_level': 2,
            'estimated_weeks': 6,
            'topics': ['Comprensión textual', 'Análisis crítico', 'Argumentación']
        },
        {
            'name': 'Ciencias Naturales Avanzada',
            'subject_id': 3,
            'difficulty_level': 3,
            'estimated_weeks': 10,
            'topics': ['Biología', 'Química', 'Física']
        }
    ]
    
    for template in templates:
        try:
            service.create_template(template)
            print(f'Created template: {template[\"name\"]}')
        except Exception as e:
            print(f'Warning: Failed to create template {template[\"name\"]}: {e}')
    
    print('Study plan template initialization completed')
    
except Exception as e:
    print(f'Error initializing study plans: {e}')
    exit(1)
" || warning "Study plan initialization had warnings"
    
    log "Study plan templates initialized ✅"
}

# Create admin user
create_admin_user() {
    log "Creating admin user..."
    
    docker-compose -f $COMPOSE_FILE exec backend python -c "
from app.models.user import User
from app.core.database import get_db
from app.core.security import hash_password
import uuid

try:
    db = next(get_db())
    
    # Check if admin user already exists
    admin_user = db.query(User).filter(User.username == 'admin').first()
    
    if not admin_user:
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            username='admin',
            email='admin@icfes-leveling.com',
            password_hash=hash_password('admin123!'),  # Change this in production
            display_name='Administrator',
            rank='S',
            level=99,
            xp=999999,
            hp=999,
            mp=999,
            power=99,
            wisdom=99,
            speed=99,
            resistance=99,
            credits=999999,
            gems=9999,
            is_active=True,
            is_premium=True,
            is_admin=True
        )
        
        db.add(admin_user)
        db.commit()
        print(f'Admin user created with ID: {admin_user.id}')
        print('Username: admin')
        print('Password: admin123! (CHANGE THIS IN PRODUCTION)')
    else:
        print('Admin user already exists')
        
except Exception as e:
    print(f'Error creating admin user: {e}')
    exit(1)
" || warning "Admin user creation had warnings"
    
    log "Admin user created ✅"
}

# Initialize cache
initialize_cache() {
    log "Initializing cache..."
    
    # Warm up cache with frequently accessed data
    docker-compose -f $COMPOSE_FILE exec backend python -c "
from app.services.cache_service import CacheService
from app.core.database import get_db
from app.models import Subject, Topic, Question
import redis

try:
    # Connect to Redis
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    cache_service = CacheService(r)
    
    # Get database connection
    db = next(get_db())
    
    # Cache subjects
    subjects = db.query(Subject).filter(Subject.is_active == True).all()
    for subject in subjects:
        cache_key = f'subject:{subject.id}'
        cache_service.set(cache_key, {
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'description': subject.description
        }, ttl=3600)
    
    print(f'Cached {len(subjects)} subjects')
    
    # Cache topics
    topics = db.query(Topic).filter(Topic.is_active == True).all()
    for topic in topics:
        cache_key = f'topic:{topic.id}'
        cache_service.set(cache_key, {
            'id': topic.id,
            'name': topic.name,
            'subject_id': topic.subject_id,
            'difficulty_level': topic.difficulty_level
        }, ttl=3600)
    
    print(f'Cached {len(topics)} topics')
    
    print('Cache initialization completed')
    
except Exception as e:
    print(f'Warning: Cache initialization failed: {e}')
" || warning "Cache initialization had warnings"
    
    log "Cache initialized ✅"
}

# Verify installation
verify_installation() {
    log "Verifying installation..."
    
    # Check if services are responding
    services=(
        "http://localhost:4000/health:Backend API"
        "http://localhost:4001/api/health:Frontend"
        "http://localhost:8003/health:WebSocket"
    )
    
    for service_info in "${services[@]}"; do
        IFS=":" read -r url name <<< "$service_info"
        info "Checking $name at $url"
        
        if curl -f -s "$url" > /dev/null 2>&1; then
            log "$name is responding ✅"
        else
            warning "$name is not responding at $url"
        fi
    done
    
    # Check database connectivity
    info "Checking database connectivity..."
    if docker-compose -f $COMPOSE_FILE exec -T backend python -c "
from app.core.database import get_db
from app.models import User, Subject, Topic

try:
    db = next(get_db())
    user_count = db.query(User).count()
    subject_count = db.query(Subject).count()
    topic_count = db.query(Topic).count()
    
    print(f'Users: {user_count}')
    print(f'Subjects: {subject_count}')
    print(f'Topics: {topic_count}')
    
    if user_count > 0 and subject_count > 0:
        print('Database verification passed')
    else:
        print('Warning: Database may not be properly initialized')
        exit(1)
        
except Exception as e:
    print(f'Database verification failed: {e}')
    exit(1)
"; then
        log "Database verification passed ✅"
    else
        warning "Database verification failed"
    fi
    
    log "Installation verification completed ✅"
}

# Show final status
show_final_status() {
    log "🎉 Production initialization completed!"
    echo ""
    info "Services Status:"
    info "  - Frontend: http://localhost:4001"
    info "  - Backend API: http://localhost:4000"
    info "  - API Documentation: http://localhost:4000/docs"
    info "  - WebSocket: ws://localhost:8003"
    info "  - Database: PostgreSQL on port 5432"
    info "  - Cache: Redis on port 6379"
    info "  - Analytics: ClickHouse on port 8123"
    echo ""
    info "Admin Access:"
    info "  - Username: admin"
    info "  - Password: admin123! (CHANGE THIS IMMEDIATELY)"
    echo ""
    warning "IMPORTANT: Change the admin password immediately!"
    warning "Review all security settings before going live!"
    echo ""
    info "Logs saved to: $LOG_FILE"
    echo ""
}

# Error handling
handle_error() {
    error "An error occurred during initialization"
    error "Check the logs at: $LOG_FILE"
    error "You may need to run: docker-compose -f $COMPOSE_FILE down && docker-compose -f $COMPOSE_FILE up -d"
    exit 1
}

# Set up error trap
trap handle_error ERR

# Main initialization flow
main() {
    log "🚀 Starting ICFES Leveling Platform production initialization..."
    
    check_prerequisites
    wait_for_services
    initialize_database
    initialize_clickhouse
    load_icfes_data
    initialize_study_plans
    create_admin_user
    initialize_cache
    verify_installation
    show_final_status
}

# Command line options
case "${1:-init}" in
    "init")
        main
        ;;
    "database")
        wait_for_services
        initialize_database
        log "Database initialization completed ✅"
        ;;
    "data")
        wait_for_services
        load_icfes_data
        log "Data loading completed ✅"
        ;;
    "cache")
        wait_for_services
        initialize_cache
        log "Cache initialization completed ✅"
        ;;
    "verify")
        verify_installation
        log "Verification completed ✅"
        ;;
    *)
        echo "Usage: $0 {init|database|data|cache|verify}"
        echo ""
        echo "Commands:"
        echo "  init      - Full initialization (default)"
        echo "  database  - Initialize database schema only"
        echo "  data      - Load ICFES data only"
        echo "  cache     - Initialize cache only"
        echo "  verify    - Verify installation only"
        exit 1
        ;;
esac