
-- Error Recovery System Database Tables
-- Create tables for error logging and recovery tracking

CREATE TABLE IF NOT EXISTS error_logs (
    id SERIAL PRIMARY KEY,
    error_id VARCHAR(36) UNIQUE NOT NULL,
    endpoint VARCHAR(500) NOT NULL,
    method VARCHAR(10) NOT NULL,
    query_params TEXT,
    error_type VARCHAR(50) NOT NULL,
    error_message TEXT NOT NULL,
    error_traceback TEXT,
    user_agent TEXT,
    ip_address VARCHAR(45),
    processing_time FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_error_logs_endpoint_timestamp ON error_logs(endpoint, timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_error_type_timestamp ON error_logs(error_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_error_logs_ip_timestamp ON error_logs(ip_address, timestamp);

CREATE TABLE IF NOT EXISTS error_patterns (
    id SERIAL PRIMARY KEY,
    pattern_id VARCHAR(36) UNIQUE DEFAULT gen_random_uuid(),
    endpoint_pattern VARCHAR(500),
    error_type_pattern VARCHAR(50),
    frequency_threshold INTEGER DEFAULT 5,
    occurrence_count INTEGER DEFAULT 0,
    first_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    recovery_strategy VARCHAR(100),
    recovery_success_rate FLOAT DEFAULT 0.0,
    auto_recovery_enabled VARCHAR(10) DEFAULT 'true',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS system_health (
    id SERIAL PRIMARY KEY,
    health_id VARCHAR(36) UNIQUE DEFAULT gen_random_uuid(),
    service_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    response_time_avg FLOAT,
    error_rate FLOAT DEFAULT 0.0,
    uptime_percentage FLOAT DEFAULT 100.0,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT,
    active_connections INTEGER,
    circuit_breaker_state VARCHAR(20) DEFAULT 'closed',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recovery_actions (
    id SERIAL PRIMARY KEY,
    action_id VARCHAR(36) UNIQUE DEFAULT gen_random_uuid(),
    action_type VARCHAR(50) NOT NULL,
    target_service VARCHAR(100) NOT NULL,
    trigger_error_type VARCHAR(50),
    action_parameters TEXT,
    execution_status VARCHAR(20) DEFAULT 'pending',
    execution_start TIMESTAMP,
    execution_end TIMESTAMP,
    execution_duration FLOAT,
    success VARCHAR(10) DEFAULT 'unknown',
    result_message TEXT,
    error_rate_before FLOAT,
    error_rate_after FLOAT,
    recovery_effectiveness FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
