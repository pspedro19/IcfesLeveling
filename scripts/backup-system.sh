#!/bin/bash

# Comprehensive backup and recovery system for ICFES Leveling Platform
# This script handles database backups, volume backups, and system recovery

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_BASE_DIR="backups"
COMPOSE_FILE="docker-compose.prod.yml"
LOG_FILE="logs/backup-$(date +%Y%m%d_%H%M%S).log"
ENCRYPTION_ENABLED=${BACKUP_ENCRYPTION:-true}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
COMPRESSION_LEVEL=${BACKUP_COMPRESSION_LEVEL:-6}

# Create necessary directories
mkdir -p logs backups/{daily,weekly,monthly}

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
    log "Checking backup prerequisites..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    # Check if services are running
    if ! docker-compose -f $COMPOSE_FILE ps | grep -q "Up"; then
        warning "Some services may not be running. Backup may be incomplete."
    fi
    
    # Check available disk space
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$available_space" -lt 5 ]; then
        error "Insufficient disk space. At least 5GB required for backup."
        exit 1
    fi
    
    # Check if encryption tools are available
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        if ! command -v openssl &> /dev/null; then
            error "OpenSSL is required for encryption but not installed."
            exit 1
        fi
        
        if [ -z "$BACKUP_ENCRYPTION_KEY" ]; then
            error "BACKUP_ENCRYPTION_KEY environment variable is required for encryption."
            exit 1
        fi
    fi
    
    log "Prerequisites check passed ✅"
}

# Get backup encryption key
get_encryption_key() {
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        if [ -n "$BACKUP_ENCRYPTION_KEY" ]; then
            echo "$BACKUP_ENCRYPTION_KEY"
        elif [ -f ".env.secrets" ]; then
            grep "^BACKUP_ENCRYPTION_KEY=" .env.secrets | cut -d'=' -f2
        else
            error "Encryption key not found. Set BACKUP_ENCRYPTION_KEY environment variable."
            exit 1
        fi
    fi
}

# Create timestamped backup directory
create_backup_dir() {
    local backup_type=${1:-manual}
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="$BACKUP_BASE_DIR/$backup_type/backup_$timestamp"
    
    mkdir -p "$backup_dir"
    echo "$backup_dir"
}

# Backup PostgreSQL database
backup_database() {
    local backup_dir=$1
    log "Backing up PostgreSQL database..."
    
    # Create database dump
    info "Creating database dump..."
    docker-compose -f $COMPOSE_FILE exec -T postgres pg_dumpall -c -U gameplay > "$backup_dir/database_full.sql"
    
    # Create individual database backups
    docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U gameplay -d gameplay_db --format=custom --compress=$COMPRESSION_LEVEL > "$backup_dir/gameplay_db.dump"
    
    # Backup database schema only
    docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U gameplay -d gameplay_db --schema-only > "$backup_dir/schema_only.sql"
    
    # Get database statistics
    docker-compose -f $COMPOSE_FILE exec -T postgres psql -U gameplay -d gameplay_db -c "
        SELECT 
            schemaname,
            tablename,
            n_tup_ins as inserts,
            n_tup_upd as updates,
            n_tup_del as deletes,
            n_live_tup as live_tuples,
            n_dead_tup as dead_tuples
        FROM pg_stat_user_tables;
    " > "$backup_dir/db_statistics.txt"
    
    log "Database backup completed ✅"
}

# Backup Redis data
backup_redis() {
    local backup_dir=$1
    log "Backing up Redis data..."
    
    # Create Redis backup
    info "Creating Redis backup..."
    docker-compose -f $COMPOSE_FILE exec -T redis redis-cli BGSAVE
    
    # Wait for backup to complete
    while [ "$(docker-compose -f $COMPOSE_FILE exec -T redis redis-cli LASTSAVE)" == "$(docker-compose -f $COMPOSE_FILE exec -T redis redis-cli LASTSAVE)" ]; do
        sleep 1
    done
    
    # Copy Redis data
    docker run --rm -v icfes_redis_data:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
    
    # Get Redis info
    docker-compose -f $COMPOSE_FILE exec -T redis redis-cli INFO > "$backup_dir/redis_info.txt"
    
    log "Redis backup completed ✅"
}

# Backup ClickHouse data
backup_clickhouse() {
    local backup_dir=$1
    log "Backing up ClickHouse data..."
    
    # Create ClickHouse backup
    info "Creating ClickHouse backup..."
    
    # Get list of databases
    docker-compose -f $COMPOSE_FILE exec -T clickhouse clickhouse-client --query "SHOW DATABASES" > "$backup_dir/clickhouse_databases.txt"
    
    # Backup gameplay_analytics database
    docker-compose -f $COMPOSE_FILE exec -T clickhouse clickhouse-client --query "
        SELECT * FROM system.tables WHERE database = 'gameplay_analytics' FORMAT TabSeparated
    " > "$backup_dir/clickhouse_tables.txt"
    
    # Create data backup
    docker run --rm -v icfes_clickhouse_data:/data -v $(pwd)/$backup_dir:/backup alpine tar czf /backup/clickhouse_data.tar.gz -C /data .
    
    # Export analytics data
    if docker-compose -f $COMPOSE_FILE exec -T clickhouse clickhouse-client --query "EXISTS TABLE gameplay_analytics.user_events" | grep -q "1"; then
        docker-compose -f $COMPOSE_FILE exec -T clickhouse clickhouse-client --query "
            SELECT * FROM gameplay_analytics.user_events 
            WHERE event_date >= today() - INTERVAL 30 DAY
            FORMAT CSV
        " > "$backup_dir/user_events_30days.csv"
    fi
    
    log "ClickHouse backup completed ✅"
}

# Backup application files and configuration
backup_application_files() {
    local backup_dir=$1
    log "Backing up application files..."
    
    # Create application files backup
    info "Creating application files backup..."
    
    # Backup configuration files
    mkdir -p "$backup_dir/config"
    cp -r config/* "$backup_dir/config/" 2>/dev/null || warning "No config directory found"
    
    # Backup environment files (excluding secrets)
    cp .env.production "$backup_dir/" 2>/dev/null || warning "No .env.production found"
    cp docker-compose.prod.yml "$backup_dir/" 2>/dev/null || warning "No production compose file found"
    
    # Backup uploaded files if they exist
    if [ -d "uploads" ]; then
        info "Backing up uploaded files..."
        tar czf "$backup_dir/uploads.tar.gz" uploads/
    fi
    
    # Backup mathimg directory
    if [ -d "mathimg" ]; then
        info "Backing up mathimg directory..."
        tar czf "$backup_dir/mathimg.tar.gz" mathimg/
    fi
    
    # Backup logs (last 7 days)
    if [ -d "logs" ]; then
        info "Backing up recent logs..."
        find logs -name "*.log" -mtime -7 -exec tar czf "$backup_dir/logs_recent.tar.gz" {} +
    fi
    
    # Create system information snapshot
    info "Creating system information snapshot..."
    {
        echo "=== System Information ==="
        date
        echo "Docker version: $(docker --version)"
        echo "Docker Compose version: $(docker-compose --version)"
        echo "Hostname: $(hostname)"
        echo "Uptime: $(uptime)"
        echo ""
        echo "=== Docker Containers ==="
        docker-compose -f $COMPOSE_FILE ps
        echo ""
        echo "=== Docker Images ==="
        docker images | grep icfes
        echo ""
        echo "=== Volume Information ==="
        docker volume ls | grep icfes
    } > "$backup_dir/system_info.txt"
    
    log "Application files backup completed ✅"
}

# Encrypt backup if enabled
encrypt_backup() {
    local backup_dir=$1
    
    if [ "$ENCRYPTION_ENABLED" = "true" ]; then
        log "Encrypting backup..."
        
        local encryption_key=$(get_encryption_key)
        local encrypted_file="${backup_dir}.tar.gz.enc"
        
        # Create compressed archive
        tar czf "${backup_dir}.tar.gz" -C "$(dirname $backup_dir)" "$(basename $backup_dir)"
        
        # Encrypt the archive
        openssl enc -aes-256-cbc -salt -in "${backup_dir}.tar.gz" -out "$encrypted_file" -pass "pass:$encryption_key"
        
        # Remove unencrypted files
        rm -rf "$backup_dir" "${backup_dir}.tar.gz"
        
        log "Backup encrypted and saved as: $encrypted_file ✅"
        echo "$encrypted_file"
    else
        # Just compress without encryption
        tar czf "${backup_dir}.tar.gz" -C "$(dirname $backup_dir)" "$(basename $backup_dir)"
        rm -rf "$backup_dir"
        
        log "Backup compressed and saved as: ${backup_dir}.tar.gz ✅"
        echo "${backup_dir}.tar.gz"
    fi
}

# Decrypt backup if needed
decrypt_backup() {
    local backup_file=$1
    local output_dir=$2
    
    if [[ "$backup_file" == *.enc ]]; then
        log "Decrypting backup..."
        
        local encryption_key=$(get_encryption_key)
        local decrypted_file="${backup_file%.enc}"
        
        # Decrypt the file
        openssl enc -aes-256-cbc -d -in "$backup_file" -out "$decrypted_file" -pass "pass:$encryption_key"
        
        # Extract the archive
        tar xzf "$decrypted_file" -C "$output_dir"
        
        # Clean up decrypted file
        rm "$decrypted_file"
        
        log "Backup decrypted and extracted ✅"
    else
        # Just extract
        tar xzf "$backup_file" -C "$output_dir"
        log "Backup extracted ✅"
    fi
}

# Perform full backup
perform_backup() {
    local backup_type=${1:-manual}
    log "Starting full backup ($backup_type)..."
    
    check_prerequisites
    
    # Create backup directory
    local backup_dir=$(create_backup_dir "$backup_type")
    log "Backup directory: $backup_dir"
    
    # Perform backups
    backup_database "$backup_dir"
    backup_redis "$backup_dir"
    backup_clickhouse "$backup_dir"
    backup_application_files "$backup_dir"
    
    # Encrypt and compress backup
    local final_backup=$(encrypt_backup "$backup_dir")
    
    # Calculate backup size
    local backup_size=$(du -h "$final_backup" | cut -f1)
    
    # Create backup manifest
    {
        echo "ICFES Leveling Platform Backup Manifest"
        echo "========================================"
        echo "Backup Type: $backup_type"
        echo "Created: $(date)"
        echo "File: $(basename $final_backup)"
        echo "Size: $backup_size"
        echo "Encryption: $ENCRYPTION_ENABLED"
        echo "Compression Level: $COMPRESSION_LEVEL"
        echo ""
        echo "Contents:"
        echo "- PostgreSQL database (full dump + custom format)"
        echo "- Redis data and configuration"
        echo "- ClickHouse analytics data"
        echo "- Application configuration files"
        echo "- Uploaded files and static assets"
        echo "- System information snapshot"
        echo ""
        echo "Restore with: $0 restore $(basename $final_backup)"
    } > "${final_backup}.manifest"
    
    log "🎉 Backup completed successfully!"
    log "Backup file: $final_backup ($backup_size)"
    log "Manifest: ${final_backup}.manifest"
}

# List available backups
list_backups() {
    log "Available backups:"
    echo ""
    
    for backup_type in daily weekly monthly manual; do
        if [ -d "$BACKUP_BASE_DIR/$backup_type" ] && [ "$(ls -A $BACKUP_BASE_DIR/$backup_type 2>/dev/null)" ]; then
            echo "=== $backup_type backups ==="
            for backup in "$BACKUP_BASE_DIR/$backup_type"/*; do
                if [ -f "$backup" ]; then
                    local size=$(du -h "$backup" | cut -f1)
                    local date=$(stat -c %y "$backup" | cut -d' ' -f1)
                    echo "  $(basename $backup) ($size) - $date"
                fi
            done
            echo ""
        fi
    done
}

# Restore from backup
restore_backup() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        error "Please specify a backup file to restore from"
        list_backups
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log "Starting restore from backup: $backup_file"
    
    # Create temporary restore directory
    local restore_dir="restore_temp_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$restore_dir"
    
    # Decrypt and extract backup
    decrypt_backup "$backup_file" "$restore_dir"
    
    # Find the extracted backup directory
    local backup_content_dir=$(find "$restore_dir" -maxdepth 1 -type d -name "backup_*" | head -1)
    
    if [ -z "$backup_content_dir" ]; then
        error "Invalid backup file structure"
        rm -rf "$restore_dir"
        exit 1
    fi
    
    log "Backup extracted to: $backup_content_dir"
    
    # Stop services before restore
    warning "Stopping services for restore..."
    docker-compose -f $COMPOSE_FILE down
    
    # Restore database
    if [ -f "$backup_content_dir/database_full.sql" ]; then
        log "Restoring PostgreSQL database..."
        docker-compose -f $COMPOSE_FILE up -d postgres
        sleep 10
        cat "$backup_content_dir/database_full.sql" | docker-compose -f $COMPOSE_FILE exec -T postgres psql -U gameplay -d postgres
    fi
    
    # Restore Redis data
    if [ -f "$backup_content_dir/redis_data.tar.gz" ]; then
        log "Restoring Redis data..."
        docker volume rm icfes_redis_data || true
        docker volume create icfes_redis_data
        docker run --rm -v icfes_redis_data:/data -v $(pwd)/$backup_content_dir:/backup alpine tar xzf /backup/redis_data.tar.gz -C /data
    fi
    
    # Restore ClickHouse data
    if [ -f "$backup_content_dir/clickhouse_data.tar.gz" ]; then
        log "Restoring ClickHouse data..."
        docker volume rm icfes_clickhouse_data || true
        docker volume create icfes_clickhouse_data
        docker run --rm -v icfes_clickhouse_data:/data -v $(pwd)/$backup_content_dir:/backup alpine tar xzf /backup/clickhouse_data.tar.gz -C /data
    fi
    
    # Restore configuration files
    if [ -d "$backup_content_dir/config" ]; then
        log "Restoring configuration files..."
        cp -r "$backup_content_dir/config"/* config/ 2>/dev/null || warning "Config restore had issues"
    fi
    
    # Restore uploads
    if [ -f "$backup_content_dir/uploads.tar.gz" ]; then
        log "Restoring uploaded files..."
        tar xzf "$backup_content_dir/uploads.tar.gz"
    fi
    
    # Restore mathimg
    if [ -f "$backup_content_dir/mathimg.tar.gz" ]; then
        log "Restoring mathimg directory..."
        tar xzf "$backup_content_dir/mathimg.tar.gz"
    fi
    
    # Clean up restore directory
    rm -rf "$restore_dir"
    
    # Start services
    log "Starting services..."
    docker-compose -f $COMPOSE_FILE up -d
    
    # Wait for services to be ready
    sleep 30
    
    # Verify restore
    if docker-compose -f $COMPOSE_FILE exec -T postgres psql -U gameplay -d gameplay_db -c "SELECT COUNT(*) FROM users;" &> /dev/null; then
        log "🎉 Restore completed successfully!"
    else
        warning "Restore may have issues. Please check the services."
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
    
    for backup_type in daily weekly monthly manual; do
        if [ -d "$BACKUP_BASE_DIR/$backup_type" ]; then
            find "$BACKUP_BASE_DIR/$backup_type" -name "backup_*" -mtime +$RETENTION_DAYS -exec rm -f {} \;
            find "$BACKUP_BASE_DIR/$backup_type" -name "backup_*.manifest" -mtime +$RETENTION_DAYS -exec rm -f {} \;
        fi
    done
    
    log "Cleanup completed ✅"
}

# Verify backup integrity
verify_backup() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        error "Please specify a backup file to verify"
        exit 1
    fi
    
    log "Verifying backup integrity: $backup_file"
    
    # Create temporary directory for verification
    local verify_dir="verify_temp_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$verify_dir"
    
    # Try to decrypt and extract
    if decrypt_backup "$backup_file" "$verify_dir" &> /dev/null; then
        local backup_content_dir=$(find "$verify_dir" -maxdepth 1 -type d -name "backup_*" | head -1)
        
        if [ -n "$backup_content_dir" ]; then
            log "Backup structure is valid ✅"
            
            # Check for essential files
            local essential_files=("database_full.sql" "system_info.txt")
            local missing_files=0
            
            for file in "${essential_files[@]}"; do
                if [ ! -f "$backup_content_dir/$file" ]; then
                    warning "Missing file: $file"
                    missing_files=$((missing_files + 1))
                fi
            done
            
            if [ $missing_files -eq 0 ]; then
                log "All essential files present ✅"
            else
                warning "$missing_files essential files are missing"
            fi
        else
            error "Invalid backup structure"
        fi
    else
        error "Failed to decrypt/extract backup"
    fi
    
    # Clean up
    rm -rf "$verify_dir"
}

# Main command handler
case "${1:-backup}" in
    "backup")
        perform_backup "${2:-manual}"
        ;;
    "restore")
        if [ -z "$2" ]; then
            error "Please specify a backup file to restore from"
            list_backups
            exit 1
        fi
        restore_backup "$2"
        ;;
    "list")
        list_backups
        ;;
    "cleanup")
        cleanup_old_backups
        ;;
    "verify")
        verify_backup "$2"
        ;;
    "daily")
        perform_backup "daily"
        cleanup_old_backups
        ;;
    "weekly")
        perform_backup "weekly"
        cleanup_old_backups
        ;;
    "monthly")
        perform_backup "monthly"
        cleanup_old_backups
        ;;
    *)
        echo "Usage: $0 {backup|restore|list|cleanup|verify|daily|weekly|monthly} [options]"
        echo ""
        echo "Commands:"
        echo "  backup [type]    - Create backup (default: manual)"
        echo "  restore <file>   - Restore from backup file"
        echo "  list             - List available backups"
        echo "  cleanup          - Remove old backups"
        echo "  verify <file>    - Verify backup integrity"
        echo "  daily            - Create daily backup and cleanup"
        echo "  weekly           - Create weekly backup and cleanup"
        echo "  monthly          - Create monthly backup and cleanup"
        echo ""
        echo "Examples:"
        echo "  $0 backup                                    # Manual backup"
        echo "  $0 restore backups/daily/backup_20241201.tar.gz.enc  # Restore"
        echo "  $0 verify backups/daily/backup_20241201.tar.gz.enc   # Verify"
        exit 1
        ;;
esac