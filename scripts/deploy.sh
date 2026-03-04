#!/bin/bash
set -euo pipefail

##############################################################################
# Production deployment script for ICFES Leveling
##############################################################################

DEPLOY_DIR=/opt/icfes-leveling
COMPOSE_FILE=docker-compose.prod.yml
ENV_FILE=.env

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "========== Starting production deployment =========="

# ------------------------------------------------------------------
# Pre-flight check: .env must exist
# ------------------------------------------------------------------
if [ ! -f "${DEPLOY_DIR}/.env" ]; then
    log "ERROR: .env file not found in ${DEPLOY_DIR}. Aborting."
    exit 1
fi
log ".env file found."

cd "${DEPLOY_DIR}"

# ------------------------------------------------------------------
# Step 1: Pull latest code
# ------------------------------------------------------------------
log "Pulling latest code from origin main..."
git pull origin main
log "Code pull complete."

# ------------------------------------------------------------------
# Step 2: Pull updated Docker images
# ------------------------------------------------------------------
log "Pulling latest Docker images..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" pull
log "Image pull complete."

# ------------------------------------------------------------------
# Step 3: Bring services up
# ------------------------------------------------------------------
log "Starting services with docker compose..."
docker compose -f "${COMPOSE_FILE}" --env-file "${ENV_FILE}" up -d --remove-orphans
log "Services started."

# ------------------------------------------------------------------
# Step 4: Clean up dangling images
# ------------------------------------------------------------------
log "Pruning unused Docker images..."
docker image prune -f
log "Image prune complete."

# ------------------------------------------------------------------
# Step 5: Health check - retry up to 3 times with 10s sleep
# ------------------------------------------------------------------
log "Running health check against backend /health endpoint..."

HEALTH_URL="http://localhost:4000/health"
MAX_RETRIES=3
RETRY_DELAY=10

for attempt in $(seq 1 "${MAX_RETRIES}"); do
    log "Health check attempt ${attempt}/${MAX_RETRIES}..."
    if curl -sf "${HEALTH_URL}" > /dev/null 2>&1; then
        log "Health check passed."
        log "========== Deployment completed successfully =========="
        exit 0
    fi
    if [ "${attempt}" -lt "${MAX_RETRIES}" ]; then
        log "Health check failed. Retrying in ${RETRY_DELAY}s..."
        sleep "${RETRY_DELAY}"
    fi
done

log "ERROR: Health check failed after ${MAX_RETRIES} attempts."
log "========== Deployment finished with errors =========="
exit 1
