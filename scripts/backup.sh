#!/bin/bash
set -euo pipefail

# =============================================================================
# PostgreSQL Backup Script
# =============================================================================
# Creates a compressed backup of the PostgreSQL database, verifies integrity,
# and removes backups older than the configured retention period.
#
# Environment variables (all optional, defaults suited for Docker):
#   DB_HOST         - Database host            (default: postgres)
#   DB_PORT         - Database port            (default: 5432)
#   DB_NAME         - Database name            (default: gameplay_db)
#   DB_USER         - Database user            (default: gameplay)
#   DB_PASSWORD     - Database password        (default: empty)
#   BACKUP_DIR      - Directory for backups    (default: /backups)
#   RETENTION_DAYS  - Days to keep backups     (default: 30)
# =============================================================================

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-gameplay_db}"
DB_USER="${DB_USER:-gameplay}"
DB_PASSWORD="${DB_PASSWORD:-}"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
timestamp() {
    date '+%Y-%m-%d %H:%M:%S'
}

log() {
    echo "[$(timestamp)] $*"
}

log_error() {
    echo "[$(timestamp)] ERROR: $*" >&2
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    log "===== PostgreSQL Backup Started ====="
    log "Host: ${DB_HOST}:${DB_PORT} | Database: ${DB_NAME} | User: ${DB_USER}"
    log "Backup directory: ${BACKUP_DIR} | Retention: ${RETENTION_DAYS} days"

    # Create backup directory if it does not exist
    if [ ! -d "${BACKUP_DIR}" ]; then
        log "Creating backup directory: ${BACKUP_DIR}"
        mkdir -p "${BACKUP_DIR}"
    fi

    # Build the backup filename
    local backup_filename="${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"
    local backup_file="${BACKUP_DIR}/${backup_filename}"

    log "Backup file: ${backup_file}"

    # Perform the backup
    log "Running pg_dump..."
    if ! PGPASSWORD="${DB_PASSWORD}" pg_dump \
            -h "${DB_HOST}" \
            -p "${DB_PORT}" \
            -U "${DB_USER}" \
            -d "${DB_NAME}" | gzip > "${backup_file}"; then
        log_error "pg_dump failed."
        # Remove partial file if it was created
        rm -f "${backup_file}"
        log "===== PostgreSQL Backup FAILED ====="
        exit 1
    fi

    # Verify the backup file exists and is not empty
    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file was not created: ${backup_file}"
        log "===== PostgreSQL Backup FAILED ====="
        exit 1
    fi

    local file_size
    file_size=$(stat -c%s "${backup_file}" 2>/dev/null || stat -f%z "${backup_file}" 2>/dev/null || echo "0")

    if [ "${file_size}" -eq 0 ]; then
        log_error "Backup file is empty (0 bytes): ${backup_file}"
        rm -f "${backup_file}"
        log "===== PostgreSQL Backup FAILED ====="
        exit 1
    fi

    log "Backup created successfully (${file_size} bytes)."

    # Clean up old backups
    log "Removing backups older than ${RETENTION_DAYS} days..."
    local deleted_count
    deleted_count=$(find "${BACKUP_DIR}" -maxdepth 1 -name "${DB_NAME}_*.sql.gz" -type f -mtime +"${RETENTION_DAYS}" -print -delete | wc -l)
    log "Deleted ${deleted_count} old backup(s)."

    log "===== PostgreSQL Backup Completed Successfully ====="
    exit 0
}

main "$@"
