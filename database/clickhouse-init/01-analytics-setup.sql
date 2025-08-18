-- ClickHouse Analytics Database Setup
-- Creates optimized analytics tables for ICFES Leveling production

-- ==========================================
-- 1. CREATE ANALYTICS DATABASE
-- ==========================================

CREATE DATABASE IF NOT EXISTS icfes_analytics;
USE icfes_analytics;

-- ==========================================
-- 2. USER EVENTS TRACKING
-- ==========================================

CREATE TABLE IF NOT EXISTS user_events (
    event_id UUID DEFAULT generateUUIDv4(),
    user_id UUID,
    session_id String,
    event_type LowCardinality(String),
    event_data String,
    timestamp DateTime64(3) DEFAULT now64(),
    ip_address IPv4,
    user_agent String,
    page_url String,
    referrer String
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (event_type, timestamp, user_id)
TTL timestamp + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- ==========================================
-- 3. DIAGNOSTIC TEST ANALYTICS
-- ==========================================

CREATE TABLE IF NOT EXISTS diagnostic_analytics (
    test_id UUID,
    user_id UUID,
    subject_id UUID,
    start_time DateTime64(3),
    end_time DateTime64(3),
    score_percentage Float32,
    total_questions UInt16,
    correct_answers UInt16,
    time_spent_seconds UInt32,
    difficulty_level UInt8,
    completion_status LowCardinality(String),
    device_type LowCardinality(String),
    browser LowCardinality(String),
    created_at DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(start_time)
ORDER BY (subject_id, start_time, user_id)
TTL created_at + INTERVAL 5 YEAR
SETTINGS index_granularity = 8192;

-- ==========================================
-- 4. QUESTION PERFORMANCE ANALYTICS
-- ==========================================

CREATE TABLE IF NOT EXISTS question_analytics (
    question_id UUID,
    user_id UUID,
    test_id UUID,
    subject_id UUID,
    topic_id UUID,
    is_correct Boolean,
    time_spent_seconds UInt16,
    difficulty_level UInt8,
    answer_option String,
    hint_used Boolean DEFAULT false,
    timestamp DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (question_id, timestamp, user_id)
TTL timestamp + INTERVAL 3 YEAR
SETTINGS index_granularity = 8192;

-- ==========================================
-- 5. BATTLE SYSTEM ANALYTICS
-- ==========================================

CREATE TABLE IF NOT EXISTS battle_analytics (
    battle_id UUID,
    user_id UUID,
    opponent_id UUID,
    battle_type LowCardinality(String),
    start_time DateTime64(3),
    end_time DateTime64(3),
    winner_id UUID,
    user_score UInt16,
    opponent_score UInt16,
    total_rounds UInt8,
    experience_gained Int16,
    level_up Boolean DEFAULT false,
    created_at DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(start_time)
ORDER BY (battle_type, start_time, user_id)
TTL created_at + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- ==========================================
-- 6. LEARNING PROGRESSION ANALYTICS
-- ==========================================

CREATE TABLE IF NOT EXISTS learning_progression (
    user_id UUID,
    subject_id UUID,
    topic_id UUID,
    skill_level Float32,
    mastery_percentage Float32,
    study_time_minutes UInt32,
    questions_answered UInt32,
    questions_correct UInt32,
    streak_days UInt16,
    last_activity DateTime64(3),
    measurement_date Date DEFAULT today()
) ENGINE = ReplacingMergeTree(last_activity)
PARTITION BY toYYYYMM(measurement_date)
ORDER BY (user_id, subject_id, topic_id, measurement_date)
TTL measurement_date + INTERVAL 2 YEAR
SETTINGS index_granularity = 8192;

-- ==========================================
-- 7. PERFORMANCE MONITORING
-- ==========================================

CREATE TABLE IF NOT EXISTS performance_metrics (
    metric_name LowCardinality(String),
    metric_value Float64,
    service_name LowCardinality(String),
    endpoint String,
    method LowCardinality(String),
    status_code UInt16,
    response_time_ms UInt32,
    error_message String,
    timestamp DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMMDD(timestamp)
ORDER BY (service_name, metric_name, timestamp)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- ==========================================
-- 8. AI INTERACTIONS ANALYTICS
-- ==========================================

CREATE TABLE IF NOT EXISTS ai_interactions (
    interaction_id UUID DEFAULT generateUUIDv4(),
    user_id UUID,
    ai_service LowCardinality(String),
    request_type LowCardinality(String),
    prompt_tokens UInt32,
    completion_tokens UInt32,
    processing_time_ms UInt32,
    model_version String,
    success Boolean,
    error_code String,
    timestamp DateTime64(3) DEFAULT now64()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (ai_service, timestamp, user_id)
TTL timestamp + INTERVAL 1 YEAR
SETTINGS index_granularity = 8192;

-- ==========================================
-- 9. CREATE MATERIALIZED VIEWS FOR REAL-TIME ANALYTICS
-- ==========================================

-- Daily user activity summary
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_user_activity
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, user_id)
AS SELECT
    toDate(timestamp) as date,
    user_id,
    count() as events_count,
    uniq(session_id) as sessions_count,
    countIf(event_type = 'diagnostic_completed') as tests_completed,
    countIf(event_type = 'battle_won') as battles_won
FROM user_events
GROUP BY date, user_id;

-- Subject performance summary
CREATE MATERIALIZED VIEW IF NOT EXISTS subject_performance_summary
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date, subject_id)
AS SELECT
    toDate(start_time) as date,
    subject_id,
    count() as total_tests,
    avg(score_percentage) as avg_score,
    countIf(score_percentage >= 70) as passing_tests,
    avg(time_spent_seconds) as avg_time_spent
FROM diagnostic_analytics
WHERE completion_status = 'completed'
GROUP BY date, subject_id;

-- ==========================================
-- 10. CREATE INDEXES FOR BETTER PERFORMANCE
-- ==========================================

-- User events indexes
ALTER TABLE user_events ADD INDEX idx_user_events_user_id user_id TYPE bloom_filter(0.01) GRANULARITY 1;
ALTER TABLE user_events ADD INDEX idx_user_events_session session_id TYPE bloom_filter(0.01) GRANULARITY 1;

-- Diagnostic analytics indexes
ALTER TABLE diagnostic_analytics ADD INDEX idx_diagnostic_user_id user_id TYPE bloom_filter(0.01) GRANULARITY 1;
ALTER TABLE diagnostic_analytics ADD INDEX idx_diagnostic_score score_percentage TYPE minmax GRANULARITY 1;

-- Question analytics indexes
ALTER TABLE question_analytics ADD INDEX idx_question_user_id user_id TYPE bloom_filter(0.01) GRANULARITY 1;
ALTER TABLE question_analytics ADD INDEX idx_question_correct is_correct TYPE set(2) GRANULARITY 1;

-- ==========================================
-- 11. GRANT PERMISSIONS
-- ==========================================

-- Create analytics user
CREATE USER IF NOT EXISTS 'icfes_analytics' IDENTIFIED BY 'CHANGE_ME_CLICKHOUSE_PASSWORD';

-- Grant necessary permissions
GRANT SELECT, INSERT ON icfes_analytics.* TO 'icfes_analytics';
GRANT CREATE TEMPORARY TABLE ON icfes_analytics.* TO 'icfes_analytics';

-- Create read-only user for reporting
CREATE USER IF NOT EXISTS 'icfes_reporting' IDENTIFIED BY 'CHANGE_ME_REPORTING_PASSWORD';
GRANT SELECT ON icfes_analytics.* TO 'icfes_reporting';