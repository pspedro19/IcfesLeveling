-- ICFES LEVELING - Database Initialization
-- PostgreSQL 16

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    level INTEGER DEFAULT 1,
    experience INTEGER DEFAULT 0,
    rank VARCHAR(10) DEFAULT 'E',
    hp INTEGER DEFAULT 100,
    mp INTEGER DEFAULT 50,
    power INTEGER DEFAULT 10,
    wisdom INTEGER DEFAULT 10,
    speed INTEGER DEFAULT 10,
    orbs INTEGER DEFAULT 0,
    crystals INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hero classes table
CREATE TABLE hero_classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) NOT NULL,
    description TEXT,
    avatar_url VARCHAR(500),
    stats_boost JSONB DEFAULT '{}',
    special_ability VARCHAR(200),
    element VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    hero_class_id UUID REFERENCES hero_classes(id),
    personality_answers JSONB,
    avatar_customization JSONB DEFAULT '{}',
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Subjects table
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    color VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Topics table
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions table
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'multiple_choice',
    difficulty INTEGER CHECK (difficulty >= 1 AND difficulty <= 10),
    correct_answer VARCHAR(10) NOT NULL,
    options JSONB NOT NULL,
    explanation TEXT,
    hint TEXT,
    tags TEXT[],
    power_stats JSONB DEFAULT '{"discrimination_index": 0.5, "success_rate": 0.6}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Battles table
CREATE TABLE battles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    battle_type VARCHAR(50) NOT NULL, -- 'dungeon', 'tower', 'pvp'
    enemy_name VARCHAR(100),
    enemy_level INTEGER,
    enemy_hp INTEGER,
    user_hp_start INTEGER,
    user_hp_end INTEGER,
    questions_answered INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    total_damage_dealt INTEGER DEFAULT 0,
    total_damage_received INTEGER DEFAULT 0,
    experience_gained INTEGER DEFAULT 0,
    orbs_gained INTEGER DEFAULT 0,
    items_dropped JSONB DEFAULT '[]',
    duration_seconds INTEGER,
    status VARCHAR(20) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Battle answers table
CREATE TABLE battle_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    battle_id UUID REFERENCES battles(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    user_answer VARCHAR(10),
    is_correct BOOLEAN,
    response_time_ms INTEGER,
    damage_dealt INTEGER DEFAULT 0,
    damage_received INTEGER DEFAULT 0,
    critical_hit BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Items table
CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    item_type VARCHAR(50) NOT NULL, -- 'weapon', 'armor', 'consumable', 'special'
    rarity VARCHAR(20) DEFAULT 'common', -- 'common', 'rare', 'epic', 'legendary'
    power_boost INTEGER DEFAULT 0,
    wisdom_boost INTEGER DEFAULT 0,
    speed_boost INTEGER DEFAULT 0,
    hp_boost INTEGER DEFAULT 0,
    mp_boost INTEGER DEFAULT 0,
    drop_rate DECIMAL(5,4) DEFAULT 0.1,
    sell_price INTEGER DEFAULT 0,
    icon_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User items table
CREATE TABLE user_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    is_equipped BOOLEAN DEFAULT FALSE,
    obtained_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quests table
CREATE TABLE quests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    quest_type VARCHAR(50) NOT NULL, -- 'daily', 'weekly', 'achievement', 'story'
    requirements JSONB,
    rewards JSONB,
    experience_reward INTEGER DEFAULT 0,
    orbs_reward INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User quests table
CREATE TABLE user_quests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quest_id UUID REFERENCES quests(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Leaderboard table
CREATE TABLE leaderboard (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0,
    rank_position INTEGER,
    season VARCHAR(20) DEFAULT 'current',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI explanations table
CREATE TABLE ai_explanations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    explanation_text TEXT NOT NULL,
    ai_model VARCHAR(50) DEFAULT 'gpt-4',
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Personality questions table
CREATE TABLE personality_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_text TEXT NOT NULL,
    question_type VARCHAR(50) DEFAULT 'multiple_choice',
    options JSONB NOT NULL,
    weight_factors JSONB, -- Factores de peso para cada clase
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diagnostic tests table
CREATE TABLE diagnostic_tests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    test_type VARCHAR(50) DEFAULT 'diagnostic',
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    score DECIMAL(5,2) DEFAULT 0.00,
    time_taken_seconds INTEGER DEFAULT 0,
    strengths JSONB DEFAULT '[]',
    weaknesses JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diagnostic test answers table
CREATE TABLE diagnostic_test_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnostic_test_id UUID REFERENCES diagnostic_tests(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    user_answer VARCHAR(10),
    is_correct BOOLEAN,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Study plans table
CREATE TABLE study_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    plan_name VARCHAR(200) NOT NULL,
    plan_data JSONB NOT NULL, -- Contiene el YML generado
    total_units INTEGER DEFAULT 8,
    completed_units INTEGER DEFAULT 0,
    progress_percentage DECIMAL(5,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plan progress table
CREATE TABLE plan_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id UUID REFERENCES study_plans(id) ON DELETE CASCADE,
    unit_number INTEGER NOT NULL,
    unit_name VARCHAR(200) NOT NULL,
    unit_description TEXT,
    unit_content JSON, -- Videos, ejercicios, recursos
    is_completed BOOLEAN DEFAULT FALSE,
    completion_date TIMESTAMP,
    score DECIMAL(5,2) DEFAULT 0.00,
    weighted_progress JSONB DEFAULT '{
      "videos": {"completed": 0, "total": 0, "weight": 0.3},
      "exercises": {"completed": 0, "total": 0, "weight": 0.5},
      "readings": {"completed": 0, "total": 0, "weight": 0.2}
    }',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video tracking table
CREATE TABLE video_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES study_plans(id) ON DELETE CASCADE,
    unit_number INTEGER NOT NULL,
    youtube_url VARCHAR(500) NOT NULL,
    video_title VARCHAR(200),
    video_duration_seconds INTEGER,
    watched_seconds INTEGER DEFAULT 0,
    watch_percentage DECIMAL(5,2) DEFAULT 0.00,
    is_completed BOOLEAN DEFAULT FALSE,
    completion_threshold DECIMAL(5,2) DEFAULT 80.00, -- 80% mínimo para completar
    last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- YML Storage table for personalized study plans
CREATE TABLE user_yml_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    subject VARCHAR(50) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,
    storage_type VARCHAR(20) DEFAULT 'local', -- 'local', 's3', 'spaces'
    file_size INTEGER DEFAULT 0,
    file_hash VARCHAR(64) NOT NULL,
    version VARCHAR(20) DEFAULT '1.0.0',
    generation_method VARCHAR(50) DEFAULT 'ai_generated',
    diagnostic_based BOOLEAN DEFAULT FALSE,
    diagnostic_id UUID REFERENCES diagnostic_tests(id),
    cache_key VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_outdated BOOLEAN DEFAULT FALSE,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- YML Usage Statistics table (optional)
CREATE TABLE yml_usage_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    yml_plan_id UUID NOT NULL REFERENCES user_yml_plans(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_type VARCHAR(20) DEFAULT 'view', -- 'view', 'download', 'regenerate'
    access_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address INET,
    session_id VARCHAR(100)
);

-- Quiz system tables
CREATE TABLE quizzes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES study_plans(id) ON DELETE CASCADE,
    unit_number INTEGER NOT NULL,
    quiz_name VARCHAR(200) NOT NULL,
    total_questions INTEGER DEFAULT 10,
    passing_score DECIMAL(5,2) DEFAULT 80.00, -- 80% para aprobar
    time_limit_minutes INTEGER DEFAULT 15,
    status VARCHAR(20) DEFAULT 'in_progress', -- 'in_progress', 'completed', 'failed'
    score DECIMAL(5,2) DEFAULT 0.00,
    correct_answers INTEGER DEFAULT 0,
    time_taken_seconds INTEGER DEFAULT 0,
    ai_feedback JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Quiz answers table
CREATE TABLE quiz_answers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    quiz_id UUID REFERENCES quizzes(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    user_answer VARCHAR(10),
    is_correct BOOLEAN,
    response_time_ms INTEGER,
    ai_explanation TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_level ON users(level);
CREATE INDEX idx_questions_subject ON questions(subject_id);
CREATE INDEX idx_questions_topic ON questions(topic_id);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_battles_user ON battles(user_id);
CREATE INDEX idx_battles_status ON battles(status);
CREATE INDEX idx_battle_answers_battle ON battle_answers(battle_id);
CREATE INDEX idx_user_items_user ON user_items(user_id);
CREATE INDEX idx_user_quests_user ON user_quests(user_id);
CREATE INDEX idx_leaderboard_score ON leaderboard(score DESC);
CREATE INDEX idx_ai_explanations_question ON ai_explanations(question_id);
CREATE INDEX idx_diagnostic_tests_user ON diagnostic_tests(user_id);
CREATE INDEX idx_diagnostic_test_answers_test ON diagnostic_test_answers(diagnostic_test_id);
CREATE INDEX idx_study_plans_user ON study_plans(user_id);
CREATE INDEX idx_plan_progress_plan ON plan_progress(plan_id);
CREATE INDEX idx_plan_progress_unit ON plan_progress(plan_id, unit_number);
CREATE INDEX idx_video_tracking_user ON video_tracking(user_id);
CREATE INDEX idx_video_tracking_plan ON video_tracking(plan_id);
CREATE INDEX idx_video_tracking_unit ON video_tracking(plan_id, unit_number);
CREATE INDEX idx_video_tracking_youtube ON video_tracking(youtube_url);

-- YML Storage indexes
CREATE INDEX idx_user_yml_plans_user ON user_yml_plans(user_id);
CREATE INDEX idx_user_yml_plans_subject ON user_yml_plans(subject);
CREATE INDEX idx_user_yml_plans_user_subject ON user_yml_plans(user_id, subject, is_active);
CREATE INDEX idx_user_yml_plans_generated_at ON user_yml_plans(generated_at DESC);
CREATE INDEX idx_user_yml_plans_storage_type ON user_yml_plans(storage_type);
CREATE INDEX idx_user_yml_plans_cache_key ON user_yml_plans(cache_key);
CREATE INDEX idx_user_yml_plans_diagnostic ON user_yml_plans(diagnostic_id);

-- YML Usage Statistics indexes
CREATE INDEX idx_yml_usage_stats_yml_plan ON yml_usage_stats(yml_plan_id);
CREATE INDEX idx_yml_usage_stats_user ON yml_usage_stats(user_id);
CREATE INDEX idx_yml_usage_stats_timestamp ON yml_usage_stats(access_timestamp DESC);

CREATE INDEX idx_quizzes_user ON quizzes(user_id);
CREATE INDEX idx_quizzes_plan ON quizzes(plan_id);
CREATE INDEX idx_quizzes_unit ON quizzes(plan_id, unit_number);
CREATE INDEX idx_quiz_answers_quiz ON quiz_answers(quiz_id);

-- Function to calculate weighted progress
CREATE OR REPLACE FUNCTION calculate_weighted_progress(progress_id UUID)
RETURNS DECIMAL AS $$
DECLARE
  weighted_data JSONB;
  total_progress DECIMAL;
BEGIN
  SELECT weighted_progress INTO weighted_data
  FROM plan_progress WHERE id = progress_id;
  
  total_progress := 
    (weighted_data->'videos'->>'completed')::DECIMAL / 
    NULLIF((weighted_data->'videos'->>'total')::DECIMAL, 0) * 0.3 +
    (weighted_data->'exercises'->>'completed')::DECIMAL / 
    NULLIF((weighted_data->'exercises'->>'total')::DECIMAL, 0) * 0.5 +
    (weighted_data->'readings'->>'completed')::DECIMAL / 
    NULLIF((weighted_data->'readings'->>'total')::DECIMAL, 0) * 0.2;
    
  RETURN COALESCE(total_progress * 100, 0);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_leaderboard_updated_at BEFORE UPDATE ON leaderboard FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_yml_plans_updated_at BEFORE UPDATE ON user_yml_plans FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 