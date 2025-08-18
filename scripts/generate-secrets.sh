#!/bin/bash

# Generate secure secrets for production environment
# Usage: ./scripts/generate-secrets.sh

echo "🔐 Generating secure secrets for ICFES Leveling production environment..."
echo ""

# Function to generate random secret
generate_secret() {
    openssl rand -base64 $1 | tr -d '\n'
}

# Generate secrets
JWT_SECRET=$(generate_secret 32)
SECRET_KEY=$(generate_secret 32)
DB_PASSWORD=$(generate_secret 24)
REDIS_PASSWORD=$(generate_secret 24)
CLICKHOUSE_PASSWORD=$(generate_secret 24)

# Create .env.production file
cat > .env.production << EOF
# Generated on $(date)
# ICFES Leveling Production Environment Variables
# ⚠️ DO NOT commit this file to version control!

# ====================
# GENERAL CONFIGURATION
# ====================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info

# ====================
# SECURITY SECRETS
# ====================
JWT_SECRET=$JWT_SECRET
SECRET_KEY=$SECRET_KEY

# ====================
# DATABASE CONFIGURATION
# ====================
DB_HOST=postgres
DB_NAME=gameplay_db
DB_USER=gameplay
DB_PASSWORD=$DB_PASSWORD
DB_PORT=5432
DATABASE_URL=postgresql://\${DB_USER}:\${DB_PASSWORD}@\${DB_HOST}:\${DB_PORT}/\${DB_NAME}

# ====================
# REDIS CONFIGURATION
# ====================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_URL=redis://:\${REDIS_PASSWORD}@\${REDIS_HOST}:\${REDIS_PORT}/0

# ====================
# CLICKHOUSE CONFIGURATION
# ====================
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=$CLICKHOUSE_PASSWORD
CLICKHOUSE_DB=gameplay_analytics

# ====================
# API CONFIGURATION
# ====================
API_V1_STR=/api/v1
BACKEND_CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# ====================
# SECURITY SETTINGS
# ====================
RATE_LIMIT_PER_MINUTE=60
LOGIN_RATE_LIMIT_PER_MINUTE=5
SESSION_LIFETIME_SECONDS=3600
REFRESH_TOKEN_LIFETIME_DAYS=7
FORCE_HTTPS=true
SECURE_COOKIES=true
SAME_SITE_COOKIES=strict

# ====================
# FEATURE FLAGS
# ====================
ENABLE_REGISTRATION=true
ENABLE_SOCIAL_LOGIN=false
ENABLE_AI_FEATURES=true
ENABLE_GAMIFICATION=true
EOF

echo "✅ Secrets generated successfully!"
echo ""
echo "📝 Generated secrets saved to .env.production"
echo ""
echo "⚠️  IMPORTANT REMINDERS:"
echo "1. Update BACKEND_CORS_ORIGINS with your actual domain"
echo "2. Update ALLOWED_HOSTS with your actual domain"
echo "3. Add this file to .gitignore: echo '.env.production' >> .gitignore"
echo "4. Keep this file secure and backed up safely"
echo "5. Update docker-compose.prod.yml to use these environment variables"
echo ""
echo "🔒 Security recommendations:"
echo "- Store these secrets in a secure password manager"
echo "- Use a secrets management service in production (AWS Secrets Manager, HashiCorp Vault, etc.)"
echo "- Rotate secrets regularly (every 90 days)"
echo "- Never share or commit these values to version control"