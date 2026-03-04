#!/bin/bash
set -euo pipefail

# =============================================================================
# Initial SSL Certificate Setup
# =============================================================================
# Run this ONCE on a fresh server to obtain Let's Encrypt certificates.
# After this, the certbot container handles automatic renewal.
#
# Usage: ./scripts/init-ssl.sh your-email@example.com
# =============================================================================

DOMAIN="${DOMAIN:-api.icfesleveling.com}"
EMAIL="${1:?Usage: $0 <email>}"
COMPOSE_FILE=docker-compose.prod.yml

echo "==> Obtaining SSL certificate for ${DOMAIN} (email: ${EMAIL})"

# Step 1: Start nginx without SSL to serve ACME challenge
echo "==> Starting nginx (HTTP only)..."
docker compose -f "${COMPOSE_FILE}" --env-file .env up -d nginx

# Step 2: Request certificate
echo "==> Requesting certificate from Let's Encrypt..."
docker compose -f "${COMPOSE_FILE}" --env-file .env run --rm certbot \
    certbot certonly --webroot \
    -w /var/www/certbot \
    -d "${DOMAIN}" \
    --email "${EMAIL}" \
    --agree-tos \
    --no-eff-email

# Step 3: Restart nginx to pick up the new certificate
echo "==> Restarting nginx with SSL..."
docker compose -f "${COMPOSE_FILE}" --env-file .env restart nginx

echo "==> SSL certificate obtained successfully for ${DOMAIN}"
echo "==> Certificate renewal is handled automatically by the certbot container."
