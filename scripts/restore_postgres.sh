#!/bin/bash

# PostgreSQL Restore Script
# Restores database from backup file

set -e

# Configuration
BACKUP_DIR="/backups/postgres"
DB_NAME="icfes_leveling"
DB_USER="gameplay"
DB_HOST="postgres"
DB_PORT="5432"
LOG_FILE="/var/log/restore_postgres.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Usage
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file|latest|timestamp>"
    echo "Examples:"
    echo "  $0 latest                    # Restore from latest backup"
    echo "  $0 20250109_120000           # Restore from specific timestamp"
    echo "  $0 /path/to/backup.sql.gz    # Restore from specific file"
    exit 1
fi

RESTORE_TARGET="$1"

# Determine backup file
if [ "$RESTORE_TARGET" == "latest" ]; then
    log "Finding latest backup..."
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/backup_${DB_NAME}_*.sql.gz 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        log "ERROR: No backup files found"
        exit 1
    fi
elif [[ "$RESTORE_TARGET" =~ ^[0-9]{8}_[0-9]{6}$ ]]; then
    log "Looking for backup with timestamp: $RESTORE_TARGET"
    BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${RESTORE_TARGET}.sql.gz"
    if [ ! -f "$BACKUP_FILE" ]; then
        # Try S3
        if [ -n "$AWS_ACCESS_KEY_ID" ]; then
            log "Backup not found locally, checking S3..."
            aws s3 cp "s3://${S3_BUCKET}/postgres/${RESTORE_TARGET}/backup_${DB_NAME}_${RESTORE_TARGET}.sql.gz" "$BACKUP_FILE"
        else
            log "ERROR: Backup file not found: $BACKUP_FILE"
            exit 1
        fi
    fi
else
    BACKUP_FILE="$RESTORE_TARGET"
    if [ ! -f "$BACKUP_FILE" ]; then
        log "ERROR: Backup file not found: $BACKUP_FILE"
        exit 1
    fi
fi

log "Restore target: $BACKUP_FILE"

# Verify backup file
log "Verifying backup file integrity..."
gunzip -t "$BACKUP_FILE"
if [ $? -ne 0 ]; then
    log "ERROR: Backup file is corrupted"
    exit 1
fi

# Create safety backup before restore
SAFETY_BACKUP="$BACKUP_DIR/pre_restore_$(date +%Y%m%d_%H%M%S).sql.gz"
log "Creating safety backup before restore: $SAFETY_BACKUP"
PGPASSWORD="${DATABASE_PASSWORD}" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    | gzip -9 > "$SAFETY_BACKUP"

# Confirm restore
echo -n "This will replace all data in database '$DB_NAME'. Continue? (yes/no): "
read -r CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    log "Restore cancelled by user"
    exit 0
fi

# Perform restore
log "Starting database restore..."
log "Dropping existing connections..."

# Terminate existing connections
PGPASSWORD="${DATABASE_PASSWORD}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d postgres \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DB_NAME}' AND pid <> pg_backend_pid();" \
    >/dev/null 2>&1 || true

# Restore database
log "Restoring database from backup..."
gunzip -c "$BACKUP_FILE" | PGPASSWORD="${DATABASE_PASSWORD}" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -v ON_ERROR_STOP=1

if [ $? -eq 0 ]; then
    log "Database restore completed successfully"
    
    # Run post-restore validations
    log "Running post-restore validations..."
    
    # Check table counts
    TABLE_COUNT=$(PGPASSWORD="${DATABASE_PASSWORD}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
    
    log "Restored tables: $TABLE_COUNT"
    
    # Verify critical tables
    for table in questions users student_progress game_sessions; do
        ROW_COUNT=$(PGPASSWORD="${DATABASE_PASSWORD}" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            -t -c "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo 0)
        log "Table $table: $ROW_COUNT rows"
    done
    
    # Update sequences
    log "Updating sequences..."
    PGPASSWORD="${DATABASE_PASSWORD}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -c "SELECT setval(pg_get_serial_sequence(table_name, column_name), 
            COALESCE(MAX(column_name::text::bigint), 1), false) 
            FROM information_schema.columns 
            WHERE column_default LIKE 'nextval%';" \
        >/dev/null 2>&1 || true
    
    # Analyze tables for optimizer
    log "Analyzing tables..."
    PGPASSWORD="${DATABASE_PASSWORD}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -c "ANALYZE;" \
        >/dev/null 2>&1
    
    log "Restore process completed successfully"
    
    # Send notification
    curl -X POST https://api.icfesleveling.com/api/v1/alerts \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"restore_success\",\"message\":\"Database restored successfully from ${BACKUP_FILE}\",\"timestamp\":\"$(date -Iseconds)\"}" \
        2>/dev/null || true
else
    log "ERROR: Database restore failed"
    log "Attempting to restore safety backup..."
    
    gunzip -c "$SAFETY_BACKUP" | PGPASSWORD="${DATABASE_PASSWORD}" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        >/dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        log "Safety backup restored successfully"
    else
        log "CRITICAL: Failed to restore safety backup. Manual intervention required!"
    fi
    
    exit 1
fi

exit 0