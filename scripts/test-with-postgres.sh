#!/usr/bin/env bash
# =============================================================================
# test-with-postgres.sh — Run backend tests against a real PostgreSQL instance
#
# Prerequisites: Docker Desktop running, docker compose available
#
# Usage:
#   bash scripts/test-with-postgres.sh
#   bash scripts/test-with-postgres.sh tests/test_game_engine.py  # specific file
# =============================================================================
set -euo pipefail

COMPOSE_FILE="docker-compose.yml"
PG_HOST="localhost"
PG_PORT="5433"
PG_USER="gameplay"
PG_PASS="gameplay123"
PG_DB="gameplay_db_test"
MAX_RETRIES=30
RETRY_INTERVAL=2

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

cleanup() {
    info "Stopping containers..."
    docker compose -f "$COMPOSE_FILE" stop postgres redis 2>/dev/null || true
}

# ----- 1. Start only postgres + redis -----
info "Starting PostgreSQL and Redis..."
docker compose -f "$COMPOSE_FILE" up -d postgres redis

# ----- 2. Wait for PostgreSQL to be ready -----
info "Waiting for PostgreSQL to be ready (max ${MAX_RETRIES} attempts)..."
for i in $(seq 1 "$MAX_RETRIES"); do
    if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U "$PG_USER" -d "$PG_USER" >/dev/null 2>&1; then
        info "PostgreSQL is ready (attempt $i)"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        error "PostgreSQL did not become ready in time"
        cleanup
        exit 1
    fi
    sleep "$RETRY_INTERVAL"
done

# ----- 3. Create a separate test database -----
info "Creating test database '${PG_DB}'..."
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U "$PG_USER" -d postgres -c "DROP DATABASE IF EXISTS ${PG_DB};" 2>/dev/null || true
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U "$PG_USER" -d postgres -c "CREATE DATABASE ${PG_DB};" 2>/dev/null

# ----- 4. Run tests -----
TEST_TARGET="${1:-tests/}"

export DATABASE_URL="postgresql://${PG_USER}:${PG_PASS}@${PG_HOST}:${PG_PORT}/${PG_DB}"
export USE_POSTGRES=1
export ENVIRONMENT=testing
export JWT_SECRET="test-secret-key-that-is-at-least-32-characters-long-for-validation"
export SECRET_KEY="test-secret-key-that-is-at-least-32-characters-long-for-validation"
export REDIS_URL="redis://localhost:6379"

info "Running tests against PostgreSQL..."
info "DATABASE_URL=${DATABASE_URL}"
info "Target: ${TEST_TARGET}"

cd apps/backend

EXIT_CODE=0
python -m pytest "$TEST_TARGET" -v --tb=short || EXIT_CODE=$?

cd ../..

# ----- 5. Report -----
echo ""
if [ "$EXIT_CODE" -eq 0 ]; then
    info "All tests PASSED against PostgreSQL!"
else
    error "Some tests FAILED (exit code: ${EXIT_CODE})"
fi

# ----- 6. Clean up test database -----
info "Dropping test database '${PG_DB}'..."
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    psql -U "$PG_USER" -d postgres -c "DROP DATABASE IF EXISTS ${PG_DB};" 2>/dev/null || true

exit "$EXIT_CODE"
