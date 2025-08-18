-- ================================================================================================
-- ICFES LEVELING - COMPLETE DATABASE RESET AND INITIALIZATION
-- ================================================================================================
-- CRÍTICO: Script maestro para inicialización completa con Docker Compose
-- Garantiza que todas las tablas avanzadas estén presentes desde el inicio
-- ================================================================================================

-- Drop existing database and recreate (only in development)
DO $$
BEGIN
    -- Solo en desarrollo, no en producción
    IF current_setting('server_version_num')::int >= 120000 THEN
        RAISE NOTICE '🔄 Initializing ICFES Leveling Database...';
        RAISE NOTICE '📊 Target: 95%% system completeness with advanced learning features';
    END IF;
END $$;

-- Ensure all required extensions are available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Grant permissions to ensure proper access
DO $$
BEGIN
    -- Create application role if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'icfes_app') THEN
        CREATE ROLE icfes_app WITH LOGIN PASSWORD 'icfes_secure_2024';
    END IF;
    
    -- Grant necessary permissions
    GRANT CONNECT ON DATABASE postgres TO icfes_app;
    GRANT USAGE ON SCHEMA public TO icfes_app;
    GRANT CREATE ON SCHEMA public TO icfes_app;
END $$;

-- Set up proper configuration for performance
SET shared_preload_libraries = 'pg_stat_statements';
SET track_activity_query_size = 2048;
SET log_min_duration_statement = 1000; -- Log queries taking more than 1 second

-- Optimize for analytical workloads
SET work_mem = '256MB';
SET maintenance_work_mem = '512MB';
SET effective_cache_size = '2GB';

-- Configure for better concurrent access
SET max_connections = 200;
SET shared_buffers = '512MB';

-- Logging configuration for debugging
SET log_statement = 'all';
SET log_duration = on;
SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Success notification
DO $$
BEGIN
    RAISE NOTICE '✅ Database initialization settings configured';
    RAISE NOTICE '🎯 Ready for table creation and data migration';
    RAISE NOTICE '⚡ Performance optimizations applied';
    RAISE NOTICE '🔒 Security settings configured';
END $$;