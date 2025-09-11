#!/bin/bash

# PostgreSQL Automated Backup Script
# Runs daily via cron, stores backups locally and uploads to S3

set -e

# Configuration
BACKUP_DIR="/backups/postgres"
S3_BUCKET="icfes-leveling-backups"
DB_NAME="icfes_leveling"
DB_USER="gameplay"
DB_HOST="postgres"
DB_PORT="5432"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_${DB_NAME}_${TIMESTAMP}.sql.gz"
LOG_FILE="/var/log/backup_postgres.log"

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "ERROR: Backup failed at line $1"
    
    # Send alert (implement your alerting mechanism)
    curl -X POST https://api.icfesleveling.com/api/v1/alerts \
        -H "Content-Type: application/json" \
        -d "{\"type\":\"backup_failure\",\"message\":\"PostgreSQL backup failed\",\"timestamp\":\"$(date -Iseconds)\"}" \
        2>/dev/null || true
    
    exit 1
}

trap 'handle_error $LINENO' ERR

# Start backup
log "Starting PostgreSQL backup for database: $DB_NAME"

# Perform backup
log "Creating backup file: $BACKUP_FILE"
PGPASSWORD="${DATABASE_PASSWORD}" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --verbose \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    --format=plain \
    --encoding=UTF8 \
    | gzip -9 > "$BACKUP_FILE"

# Check backup file size
BACKUP_SIZE=$(stat -c%s "$BACKUP_FILE")
BACKUP_SIZE_MB=$((BACKUP_SIZE / 1048576))
log "Backup completed. Size: ${BACKUP_SIZE_MB}MB"

# Verify backup integrity
log "Verifying backup integrity..."
gunzip -t "$BACKUP_FILE"
if [ $? -eq 0 ]; then
    log "Backup verification successful"
else
    log "ERROR: Backup verification failed"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# Upload to S3 (if configured)
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    log "Uploading backup to S3..."
    aws s3 cp "$BACKUP_FILE" "s3://${S3_BUCKET}/postgres/${TIMESTAMP}/" \
        --storage-class STANDARD_IA \
        --server-side-encryption AES256 \
        --metadata "timestamp=${TIMESTAMP},database=${DB_NAME},size=${BACKUP_SIZE}"
    
    if [ $? -eq 0 ]; then
        log "S3 upload successful"
        
        # Create a restore point marker
        echo "{\"timestamp\":\"${TIMESTAMP}\",\"file\":\"${BACKUP_FILE}\",\"size\":${BACKUP_SIZE}}" \
            > "$BACKUP_DIR/latest_backup.json"
    else
        log "WARNING: S3 upload failed, keeping local backup"
    fi
fi

# Clean up old local backups
log "Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
DELETED_COUNT=$(find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -mtime +${RETENTION_DAYS} | wc -l)
log "Deleted ${DELETED_COUNT} old backup files"

# Clean up old S3 backups (if configured)
if [ -n "$AWS_ACCESS_KEY_ID" ]; then
    log "Cleaning up old S3 backups..."
    aws s3 ls "s3://${S3_BUCKET}/postgres/" \
        | awk '{print $2}' \
        | while read -r folder; do
            folder_date=$(echo "$folder" | cut -d'_' -f1)
            if [ -n "$folder_date" ]; then
                folder_timestamp=$(date -d "${folder_date:0:8}" +%s 2>/dev/null || echo 0)
                cutoff_timestamp=$(date -d "${RETENTION_DAYS} days ago" +%s)
                
                if [ "$folder_timestamp" -lt "$cutoff_timestamp" ] && [ "$folder_timestamp" -gt 0 ]; then
                    log "Deleting old S3 backup: $folder"
                    aws s3 rm "s3://${S3_BUCKET}/postgres/${folder}" --recursive
                fi
            fi
        done
fi

# Generate backup report
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/backup_${DB_NAME}_*.sql.gz 2>/dev/null | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log "Backup process completed successfully"
log "Summary: ${BACKUP_COUNT} backups, Total size: ${TOTAL_SIZE}"

# Send success notification
curl -X POST https://api.icfesleveling.com/api/v1/metrics \
    -H "Content-Type: application/json" \
    -d "{
        \"metric\":\"backup_success\",
        \"value\":1,
        \"tags\":{
            \"database\":\"${DB_NAME}\",
            \"size_mb\":${BACKUP_SIZE_MB},
            \"duration_seconds\":${SECONDS}
        },
        \"timestamp\":\"$(date -Iseconds)\"
    }" \
    2>/dev/null || true

exit 0