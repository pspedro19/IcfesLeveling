-- Production Database Initialization Script
-- Creates secure production database with proper user management

-- ==========================================
-- 1. CREATE SECURE PRODUCTION USERS
-- ==========================================

-- Create production user with limited privileges
CREATE USER icfes_prod_user WITH PASSWORD 'CHANGE_ME_STRONG_DB_PASSWORD';

-- Create read-only user for monitoring/analytics
CREATE USER icfes_readonly WITH PASSWORD 'CHANGE_ME_READONLY_PASSWORD';

-- Create backup user
CREATE USER icfes_backup WITH PASSWORD 'CHANGE_ME_BACKUP_PASSWORD';

-- ==========================================
-- 2. CREATE PRODUCTION DATABASE
-- ==========================================

-- Create production database
CREATE DATABASE icfes_production OWNER icfes_prod_user;

-- Connect to production database to set up permissions
\c icfes_production;

-- ==========================================
-- 3. REVOKE DEFAULT PERMISSIONS
-- ==========================================

-- Revoke default permissions for security
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE icfes_production FROM PUBLIC;

-- ==========================================
-- 4. GRANT APPROPRIATE PERMISSIONS
-- ==========================================

-- Grant permissions to production user
GRANT CONNECT ON DATABASE icfes_production TO icfes_prod_user;
GRANT USAGE, CREATE ON SCHEMA public TO icfes_prod_user;

-- Grant read-only access to readonly user
GRANT CONNECT ON DATABASE icfes_production TO icfes_readonly;
GRANT USAGE ON SCHEMA public TO icfes_readonly;

-- Grant backup permissions
GRANT CONNECT ON DATABASE icfes_production TO icfes_backup;
GRANT USAGE ON SCHEMA public TO icfes_backup;

-- ==========================================
-- 5. SET DEFAULT PRIVILEGES FOR FUTURE TABLES
-- ==========================================

-- Set default privileges for tables created by production user
ALTER DEFAULT PRIVILEGES FOR ROLE icfes_prod_user IN SCHEMA public 
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO icfes_prod_user;

ALTER DEFAULT PRIVILEGES FOR ROLE icfes_prod_user IN SCHEMA public 
    GRANT SELECT ON TABLES TO icfes_readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE icfes_prod_user IN SCHEMA public 
    GRANT SELECT ON TABLES TO icfes_backup;

-- Set default privileges for sequences
ALTER DEFAULT PRIVILEGES FOR ROLE icfes_prod_user IN SCHEMA public 
    GRANT USAGE, SELECT ON SEQUENCES TO icfes_prod_user;

-- ==========================================
-- 6. ENABLE REQUIRED EXTENSIONS
-- ==========================================

-- Enable UUID extension for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgcrypto for encryption functions
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Enable pg_stat_statements for query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- ==========================================
-- 7. CREATE SECURITY LOG TABLE
-- ==========================================

CREATE TABLE IF NOT EXISTS security_log (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    user_name VARCHAR(255),
    ip_address INET,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details JSONB,
    severity VARCHAR(20) DEFAULT 'INFO'
);

-- Grant permissions on security log
GRANT INSERT, SELECT ON security_log TO icfes_prod_user;
GRANT SELECT ON security_log TO icfes_readonly;

-- ==========================================
-- 8. SET SECURE DATABASE CONFIGURATION
-- ==========================================

-- Enable connection logging
ALTER DATABASE icfes_production SET log_connections = on;
ALTER DATABASE icfes_production SET log_disconnections = on;

-- Set logging for data modification statements
ALTER DATABASE icfes_production SET log_statement = 'mod';

-- Set minimum duration for logging slow queries (1 second)
ALTER DATABASE icfes_production SET log_min_duration_statement = 1000;

-- Set detailed log line prefix
ALTER DATABASE icfes_production SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Set timezone to UTC for consistency
ALTER DATABASE icfes_production SET timezone = 'UTC';

-- Increase statement timeout for production
ALTER DATABASE icfes_production SET statement_timeout = '300s';

-- Set work memory for complex queries
ALTER DATABASE icfes_production SET work_mem = '16MB';

-- Set maintenance work memory
ALTER DATABASE icfes_production SET maintenance_work_mem = '256MB';

COMMIT;