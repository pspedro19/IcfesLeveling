-- ICFES LEVELING - ClickHouse Analytics Initialization

-- Create database
CREATE DATABASE IF NOT EXISTS gameplay_analytics;

-- Use the database
USE gameplay_analytics;

-- Create events table for analytics
CREATE TABLE IF NOT EXISTS game_events (
    event_time DateTime64(3) DEFAULT now(),
    user_id String,
    event_type String,
    event_data String,
    session_id String,
    ip_address String,
    user_agent String,
    platform String DEFAULT 'web',
    version String DEFAULT '1.0.0'
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, user_id, event_type)
TTL event_time + INTERVAL 1 YEAR;

-- Create battle analytics table
CREATE TABLE IF NOT EXISTS battle_analytics (
    battle_id String,
    user_id String,
    battle_type String,
    enemy_name String,
    enemy_level UInt8,
    questions_answered UInt16,
    correct_answers UInt16,
    total_damage_dealt UInt32,
    total_damage_received UInt32,
    experience_gained UInt32,
    orbs_gained UInt32,
    duration_seconds UInt32,
    status String,
    created_at DateTime64(3) DEFAULT now(),
    completed_at DateTime64(3)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (created_at, user_id, battle_type)
TTL created_at + INTERVAL 1 YEAR;

-- Create question performance table
CREATE TABLE IF NOT EXISTS question_performance (
    question_id String,
    user_id String,
    subject_id String,
    topic_id String,
    difficulty UInt8,
    user_answer String,
    correct_answer String,
    is_correct UInt8,
    response_time_ms UInt32,
    damage_dealt UInt16,
    damage_received UInt16,
    critical_hit UInt8,
    battle_id String,
    created_at DateTime64(3) DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(created_at)
ORDER BY (created_at, question_id, user_id)
TTL created_at + INTERVAL 1 YEAR;

-- Create user progression table
CREATE TABLE IF NOT EXISTS user_progression (
    user_id String,
    level UInt16,
    experience UInt32,
    rank String,
    hp UInt16,
    mp UInt16,
    power UInt16,
    wisdom UInt16,
    speed UInt16,
    orbs UInt32,
    crystals UInt32,
    streak_days UInt16,
    recorded_at DateTime64(3) DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(recorded_at)
ORDER BY (recorded_at, user_id)
TTL recorded_at + INTERVAL 1 YEAR;

-- Create daily metrics table
CREATE TABLE IF NOT EXISTS daily_metrics (
    date Date,
    total_users UInt32,
    active_users UInt32,
    total_battles UInt32,
    total_questions_answered UInt32,
    correct_answers UInt32,
    total_experience_gained UInt64,
    total_orbs_gained UInt64,
    avg_session_duration UInt32,
    retention_rate Float32
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(date)
ORDER BY (date)
TTL date + INTERVAL 1 YEAR;

-- Insert sample analytics data
INSERT INTO game_events (user_id, event_type, event_data, session_id, ip_address, user_agent) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', 'user_login', '{"platform": "web", "browser": "chrome"}', 'session_001', '192.168.1.1', 'Mozilla/5.0'),
('aa0e8400-e29b-41d4-a716-446655440001', 'battle_started', '{"battle_type": "dungeon", "enemy_level": 5}', 'session_001', '192.168.1.1', 'Mozilla/5.0'),
('aa0e8400-e29b-41d4-a716-446655440002', 'level_up', '{"old_level": 17, "new_level": 18, "experience_gained": 500}', 'session_002', '192.168.1.2', 'Mozilla/5.0'),
('aa0e8400-e29b-41d4-a716-446655440003', 'item_acquired', '{"item_name": "Poción de Sabiduría", "rarity": "rare"}', 'session_003', '192.168.1.3', 'Mozilla/5.0');

INSERT INTO battle_analytics (battle_id, user_id, battle_type, enemy_name, enemy_level, questions_answered, correct_answers, total_damage_dealt, total_damage_received, experience_gained, orbs_gained, duration_seconds, status) VALUES
('bb0e8400-e29b-41d4-a716-446655440001', 'aa0e8400-e29b-41d4-a716-446655440001', 'dungeon', 'Goblin Matemático', 5, 8, 7, 140, 30, 120, 50, 240, 'completed'),
('bb0e8400-e29b-41d4-a716-446655440002', 'aa0e8400-e29b-41d4-a716-446655440002', 'tower', 'Guardián de la Torre', 12, 12, 10, 200, 40, 180, 75, 360, 'completed'),
('bb0e8400-e29b-41d4-a716-446655440003', 'aa0e8400-e29b-41d4-a716-446655440003', 'dungeon', 'Esqueleto Científico', 8, 10, 6, 120, 40, 100, 40, 300, 'completed');

INSERT INTO question_performance (question_id, user_id, subject_id, topic_id, difficulty, user_answer, correct_answer, is_correct, response_time_ms, damage_dealt, damage_received, critical_hit, battle_id) VALUES
('770e8400-e29b-41d4-a716-446655440001', 'aa0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 1, 'A', 'A', 1, 5000, 25, 0, 1, 'bb0e8400-e29b-41d4-a716-446655440001'),
('770e8400-e29b-41d4-a716-446655440002', 'aa0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 2, 'B', 'B', 1, 8000, 20, 0, 0, 'bb0e8400-e29b-41d4-a716-446655440001'),
('770e8400-e29b-41d4-a716-446655440003', 'aa0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440002', 1, 'C', 'C', 1, 3000, 30, 0, 1, 'bb0e8400-e29b-41d4-a716-446655440001'),
('770e8400-e29b-41d4-a716-446655440004', 'aa0e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440005', 1, 'B', 'A', 0, 12000, 0, 15, 0, 'bb0e8400-e29b-41d4-a716-446655440001');

INSERT INTO user_progression (user_id, level, experience, rank, hp, mp, power, wisdom, speed, orbs, crystals, streak_days) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', 25, 12500, 'B', 150, 75, 25, 30, 20, 5000, 100, 5),
('aa0e8400-e29b-41d4-a716-446655440002', 18, 8500, 'C', 120, 60, 20, 35, 15, 3000, 50, 3),
('aa0e8400-e29b-41d4-a716-446655440003', 12, 6000, 'D', 100, 50, 15, 25, 18, 2000, 25, 1),
('aa0e8400-e29b-41d4-a716-446655440004', 8, 3500, 'E', 90, 45, 12, 20, 22, 1500, 10, 0),
('aa0e8400-e29b-41d4-a716-446655440005', 1, 0, 'E', 100, 50, 10, 10, 10, 1000, 0, 0);

INSERT INTO daily_metrics (date, total_users, active_users, total_battles, total_questions_answered, correct_answers, total_experience_gained, total_orbs_gained, avg_session_duration, retention_rate) VALUES
('2024-01-15', 5, 3, 4, 40, 28, 500, 265, 300, 0.6),
('2024-01-14', 5, 4, 6, 60, 42, 750, 400, 280, 0.8),
('2024-01-13', 5, 2, 2, 20, 15, 250, 150, 320, 0.4); 