-- ICFES LEVELING - Database Initialization
-- PostgreSQL 16

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    avatar_url VARCHAR(500),
    level INTEGER DEFAULT 1,
    experience INTEGER DEFAULT 0,
    rank VARCHAR(10) DEFAULT 'E',
    hp INTEGER DEFAULT 100,
    mp INTEGER DEFAULT 50,
    power INTEGER DEFAULT 10,
    wisdom INTEGER DEFAULT 10,
    speed INTEGER DEFAULT 10,
    orbs INTEGER DEFAULT 1000,
    crystals INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    color VARCHAR(7) DEFAULT '#3b0f6f',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    difficulty_level INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

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

CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    item_type VARCHAR(50) NOT NULL, -- 'consumable', 'cosmetic', 'pet'
    rarity VARCHAR(20) DEFAULT 'common', -- 'common', 'rare', 'epic', 'legendary'
    icon_url VARCHAR(500),
    effects JSONB DEFAULT '{}',
    drop_rate DECIMAL(5,4) DEFAULT 0.01,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    equipped BOOLEAN DEFAULT FALSE,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE daily_quests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    quest_type VARCHAR(50) NOT NULL, -- 'battles', 'correct_answers', 'streak'
    target_value INTEGER NOT NULL,
    reward_type VARCHAR(50) NOT NULL, -- 'experience', 'orbs', 'crystals', 'item'
    reward_value INTEGER NOT NULL,
    reward_item_id UUID REFERENCES items(id),
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_quests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    quest_id UUID REFERENCES daily_quests(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0,
    completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE leaderboard (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0,
    rank_position INTEGER,
    leaderboard_type VARCHAR(50) DEFAULT 'global', -- 'global', 'weekly', 'monthly'
    period_start DATE,
    period_end DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ai_explanations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    explanation_text TEXT NOT NULL,
    explanation_type VARCHAR(50) DEFAULT 'wrong_answer', -- 'wrong_answer', 'study_plan', 'hint'
    tokens_used INTEGER,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_level ON users(level);
CREATE INDEX idx_questions_subject_difficulty ON questions(subject_id, difficulty);
CREATE INDEX idx_questions_topic ON questions(topic_id);
CREATE INDEX idx_battles_user_created ON battles(user_id, created_at);
CREATE INDEX idx_battle_answers_battle ON battle_answers(battle_id);
CREATE INDEX idx_leaderboard_score ON leaderboard(score DESC);
CREATE INDEX idx_user_events_user_created ON user_events(user_id, created_at);

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