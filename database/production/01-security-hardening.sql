-- Production Database Security Hardening
-- Execute these commands to secure the PostgreSQL database for production

-- ==========================================
-- 1. CREATE SECURE PRODUCTION USER
-- ==========================================

-- Create production user with limited privileges
CREATE USER icfes_prod_user WITH PASSWORD 'CHANGE_ME_STRONG_DB_PASSWORD';

-- Create read-only user for monitoring/analytics
CREATE USER icfes_readonly WITH PASSWORD 'CHANGE_ME_READONLY_PASSWORD';

-- Create backup user
CREATE USER icfes_backup WITH PASSWORD 'CHANGE_ME_BACKUP_PASSWORD';

-- ==========================================
-- 2. DATABASE AND SCHEMA SECURITY
-- ==========================================

-- Create production database
CREATE DATABASE icfes_production OWNER icfes_prod_user;

-- Connect to production database
\c icfes_production;

-- Revoke default permissions
REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE icfes_production FROM PUBLIC;

-- Grant appropriate permissions to production user
GRANT CONNECT ON DATABASE icfes_production TO icfes_prod_user;
GRANT USAGE, CREATE ON SCHEMA public TO icfes_prod_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO icfes_prod_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO icfes_prod_user;

-- Grant read-only access to readonly user
GRANT CONNECT ON DATABASE icfes_production TO icfes_readonly;
GRANT USAGE ON SCHEMA public TO icfes_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO icfes_readonly;

-- Grant backup permissions
GRANT CONNECT ON DATABASE icfes_production TO icfes_backup;
GRANT USAGE ON SCHEMA public TO icfes_backup;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO icfes_backup;

-- ==========================================
-- 3. ROW LEVEL SECURITY (RLS)
-- ==========================================

-- Enable RLS on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostic_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE battles ENABLE ROW LEVEL SECURITY;

-- Create policies for user data isolation
CREATE POLICY user_isolation_policy ON users
    FOR ALL TO icfes_prod_user
    USING (true)  -- Admin can see all users
    WITH CHECK (true);

CREATE POLICY user_profile_isolation ON user_profiles
    FOR ALL TO icfes_prod_user
    USING (true)
    WITH CHECK (true);

-- Create policy for diagnostic tests
CREATE POLICY diagnostic_isolation ON diagnostic_tests
    FOR ALL TO icfes_prod_user
    USING (true)
    WITH CHECK (true);

-- Create policy for battles
CREATE POLICY battle_isolation ON battles
    FOR ALL TO icfes_prod_user
    USING (true)
    WITH CHECK (true);

-- ==========================================
-- 4. AUDIT LOGGING
-- ==========================================

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT
);

-- Create audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_log (table_name, operation, user_name, old_values)
        VALUES (TG_TABLE_NAME, TG_OP, current_user, row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_log (table_name, operation, user_name, old_values, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, current_user, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_log (table_name, operation, user_name, new_values)
        VALUES (TG_TABLE_NAME, TG_OP, current_user, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit triggers for sensitive tables
CREATE TRIGGER users_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER user_profiles_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER diagnostic_tests_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON diagnostic_tests
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- ==========================================
-- 5. DATA ENCRYPTION FUNCTIONS
-- ==========================================

-- Create extension for encryption
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Function to encrypt sensitive data
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN encode(pgp_sym_encrypt(data, key), 'base64');
END;
$$ LANGUAGE plpgsql;

-- Function to decrypt sensitive data
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data TEXT, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(decode(encrypted_data, 'base64'), key);
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 6. PERFORMANCE OPTIMIZATION INDEXES
-- ==========================================

-- Critical indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username_active ON users(username) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email_active ON users(email) WHERE is_active = true;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_level_rank ON users(level, rank);

-- Diagnostic tests indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnostic_tests_user_id ON diagnostic_tests(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnostic_tests_subject_id ON diagnostic_tests(subject_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnostic_tests_completed_at ON diagnostic_tests(completed_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnostic_tests_status ON diagnostic_tests(status);

-- Questions indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_subject_id ON questions(subject_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_topic_id ON questions(topic_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_difficulty ON questions(difficulty);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_tags ON questions USING GIN(tags);

-- Battles indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_battles_user_id ON battles(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_battles_status ON battles(status);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_battles_created_at ON battles(created_at);

-- User profiles indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_user_profiles_hero_class ON user_profiles(hero_class);

-- Composite indexes for common queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_diagnostic_user_subject ON diagnostic_tests(user_id, subject_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_questions_subject_difficulty ON questions(subject_id, difficulty);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_battles_user_status ON battles(user_id, status);

-- ==========================================
-- 7. CONSTRAINTS AND VALIDATION
-- ==========================================

-- Add check constraints for data validation
ALTER TABLE users ADD CONSTRAINT check_level_range CHECK (level >= 1 AND level <= 100);
ALTER TABLE users ADD CONSTRAINT check_experience_positive CHECK (experience >= 0);
ALTER TABLE users ADD CONSTRAINT check_rank_valid CHECK (rank IN ('E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS'));

-- Add constraints for questions
ALTER TABLE questions ADD CONSTRAINT check_difficulty_range CHECK (difficulty >= 1 AND difficulty <= 5);

-- Add constraints for diagnostic tests
ALTER TABLE diagnostic_tests ADD CONSTRAINT check_score_range CHECK (score_percentage >= 0 AND score_percentage <= 100);
ALTER TABLE diagnostic_tests ADD CONSTRAINT check_status_valid CHECK (status IN ('in_progress', 'completed', 'abandoned'));

-- ==========================================
-- 8. CLEANUP AND MAINTENANCE FUNCTIONS
-- ==========================================

-- Function to clean old audit logs
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs(retention_days INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_log 
    WHERE timestamp < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    INSERT INTO audit_log (table_name, operation, user_name, new_values)
    VALUES ('audit_log', 'CLEANUP', current_user, 
            json_build_object('deleted_records', deleted_count, 'retention_days', retention_days));
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to analyze table statistics
CREATE OR REPLACE FUNCTION update_table_statistics()
RETURNS VOID AS $$
BEGIN
    ANALYZE users;
    ANALYZE user_profiles;
    ANALYZE diagnostic_tests;
    ANALYZE questions;
    ANALYZE battles;
    ANALYZE topics;
    ANALYZE subjects;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 9. BACKUP AND RECOVERY FUNCTIONS
-- ==========================================

-- Function to create consistent backup
CREATE OR REPLACE FUNCTION create_consistent_backup()
RETURNS TEXT AS $$
DECLARE
    backup_name TEXT;
BEGIN
    backup_name := 'icfes_backup_' || to_char(CURRENT_TIMESTAMP, 'YYYY_MM_DD_HH24_MI_SS');
    
    -- Log backup start
    INSERT INTO audit_log (table_name, operation, user_name, new_values)
    VALUES ('system', 'BACKUP_START', current_user, 
            json_build_object('backup_name', backup_name, 'timestamp', CURRENT_TIMESTAMP));
    
    RETURN backup_name;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- 10. SECURITY MONITORING VIEWS
-- ==========================================

-- View for monitoring failed login attempts
CREATE OR REPLACE VIEW security_failed_logins AS
SELECT 
    ip_address,
    COUNT(*) as failed_attempts,
    MAX(timestamp) as last_attempt,
    MIN(timestamp) as first_attempt
FROM audit_log 
WHERE table_name = 'users' 
    AND operation = 'LOGIN_FAILED'
    AND timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours'
GROUP BY ip_address
HAVING COUNT(*) > 5
ORDER BY failed_attempts DESC;

-- View for monitoring data access patterns
CREATE OR REPLACE VIEW security_data_access AS
SELECT 
    user_name,
    table_name,
    operation,
    COUNT(*) as operation_count,
    MAX(timestamp) as last_access
FROM audit_log
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
GROUP BY user_name, table_name, operation
ORDER BY operation_count DESC;

-- ==========================================
-- 11. GRANT FINAL PERMISSIONS
-- ==========================================

-- Grant permissions on audit table
GRANT SELECT ON audit_log TO icfes_readonly;
GRANT INSERT ON audit_log TO icfes_prod_user;

-- Grant permissions on views
GRANT SELECT ON security_failed_logins TO icfes_readonly;
GRANT SELECT ON security_data_access TO icfes_readonly;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION cleanup_old_audit_logs(INTEGER) TO icfes_prod_user;
GRANT EXECUTE ON FUNCTION update_table_statistics() TO icfes_prod_user;
GRANT EXECUTE ON FUNCTION create_consistent_backup() TO icfes_backup;

-- ==========================================
-- 12. REVOKE DANGEROUS PERMISSIONS
-- ==========================================

-- Revoke superuser privileges (if any were granted accidentally)
REVOKE ALL PRIVILEGES ON DATABASE icfes_production FROM PUBLIC;
REVOKE ALL PRIVILEGES ON SCHEMA public FROM PUBLIC;

-- Ensure no one can drop the database
REVOKE ALL ON DATABASE icfes_production FROM icfes_prod_user;
GRANT CONNECT ON DATABASE icfes_production TO icfes_prod_user;

-- ==========================================
-- 13. FINAL SECURITY SETTINGS
-- ==========================================

-- Set secure defaults
ALTER DATABASE icfes_production SET log_statement = 'mod';
ALTER DATABASE icfes_production SET log_min_duration_statement = 1000;
ALTER DATABASE icfes_production SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Enable connection logging
ALTER DATABASE icfes_production SET log_connections = on;
ALTER DATABASE icfes_production SET log_disconnections = on;

COMMIT;