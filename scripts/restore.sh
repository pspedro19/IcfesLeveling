#!/bin/bash
set -euo pipefail

# =============================================================================
# PostgreSQL Restore Script
# =============================================================================
# Restores a PostgreSQL database from a compressed (.sql.gz) backup file.
#
# Usage:
#   ./restore.sh <backup_file>            # interactive confirmation
#   ./restore.sh --force <backup_file>    # skip confirmation
#   ./restore.sh <backup_file> --force    # skip confirmation (flag after file)
#
# Environment variables (all optional, defaults suited for Docker):
#   DB_HOST     - Database host     (default: postgres)
#   DB_PORT     - Database port     (default: 5432)
#   DB_NAME     - Database name     (default: gameplay_db)
#   DB_USER     - Database user     (default: gameplay)
#   DB_PASSWORD - Database password (default: empty)
# =============================================================================

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-gameplay_db}"
DB_USER="${DB_USER:-gameplay}"
DB_PASSWORD="${DB_PASSWORD:-}"

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

usage() {
    echo "Usage: $0 [--force] <backup_file.sql.gz>"
    echo ""
    echo "Options:"
    echo "  --force    Skip the interactive confirmation prompt"
    echo ""
    echo "Example:"
    echo "  $0 /backups/gameplay_db_20260218_120000.sql.gz"
    echo "  $0 --force /backups/gameplay_db_20260218_120000.sql.gz"
    exit 1
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
FORCE=false
BACKUP_FILE=""

for arg in "$@"; do
    case "${arg}" in
        --force)
            FORCE=true
            ;;
        -h|--help)
            usage
            ;;
        *)
            if [ -z "${BACKUP_FILE}" ]; then
                BACKUP_FILE="${arg}"
            else
                log_error "Unexpected argument: ${arg}"
                usage
            fi
            ;;
    esac
done

if [ -z "${BACKUP_FILE}" ]; then
    log_error "No backup file specified."
    usage
fi

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
main() {
    log "===== PostgreSQL Restore Started ====="
    log "Backup file: ${BACKUP_FILE}"
    log "Target: ${DB_HOST}:${DB_PORT} | Database: ${DB_NAME} | User: ${DB_USER}"

    # Validate that the backup file exists
    if [ ! -f "${BACKUP_FILE}" ]; then
        log_error "Backup file not found: ${BACKUP_FILE}"
        log "===== PostgreSQL Restore FAILED ====="
        exit 1
    fi

    # Validate that the file is not empty
    local file_size
    file_size=$(stat -c%s "${BACKUP_FILE}" 2>/dev/null || stat -f%z "${BACKUP_FILE}" 2>/dev/null || echo "0")

    if [ "${file_size}" -eq 0 ]; then
        log_error "Backup file is empty (0 bytes): ${BACKUP_FILE}"
        log "===== PostgreSQL Restore FAILED ====="
        exit 1
    fi

    log "Backup file size: ${file_size} bytes"

    # Confirmation prompt (unless --force is set)
    if [ "${FORCE}" = false ]; then
        echo ""
        echo "WARNING: This will restore the database '${DB_NAME}' on ${DB_HOST}:${DB_PORT}"
        echo "         from file: ${BACKUP_FILE}"
        echo ""
        echo "         Existing data in '${DB_NAME}' may be overwritten."
        echo ""
        read -rp "Are you sure you want to proceed? (yes/no): " confirmation
        if [ "${confirmation}" != "yes" ]; then
            log "Restore cancelled by user."
            exit 0
        fi
        echo ""
    fi

    # Perform the restore
    log "Decompressing and restoring database..."
    if ! gunzip -c "${BACKUP_FILE}" | PGPASSWORD="${DB_PASSWORD}" psql \
            -h "${DB_HOST}" \
            -p "${DB_PORT}" \
            -U "${DB_USER}" \
            -d "${DB_NAME}"; then
        log_error "Restore command failed."
        log "===== PostgreSQL Restore FAILED ====="
        exit 1
    fi

    log "Database restored successfully from: ${BACKUP_FILE}"
    log "===== PostgreSQL Restore Completed Successfully ====="
    exit 0
}

main
