-- ICFES Video Learning System - Database Migration
-- This script creates all necessary tables for the video learning system

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Function to update updated_at column automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to calculate engagement score
CREATE OR REPLACE FUNCTION calculate_engagement_score(
    watch_time_seconds INTEGER,
    total_video_duration INTEGER,
    interaction_count INTEGER,
    completion_rate DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    -- Base score from watch time (0-50 points)
    DECLARE
        watch_score DECIMAL;
        interaction_score DECIMAL;
        completion_score DECIMAL;
        final_score DECIMAL;
    BEGIN
        -- Watch time score (0-50 points)
        IF total_video_duration > 0 THEN
            watch_score := LEAST(50, (watch_time_seconds::DECIMAL / total_video_duration) * 50);
        ELSE
            watch_score := 0;
        END IF;
        
        -- Interaction score (0-30 points)
        interaction_score := LEAST(30, interaction_count * 5);
        
        -- Completion score (0-20 points)
        completion_score := completion_rate * 20;
        
        -- Final score (0-100)
        final_score := watch_score + interaction_score + completion_score;
        
        RETURN LEAST(100, GREATEST(0, final_score));
    END;
END;
$$ LANGUAGE plpgsql;

-- Video tracking table
CREATE TABLE IF NOT EXISTS video_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(50) NOT NULL,
    yml_plan_id UUID,
    module_id VARCHAR(100),
    topic_code VARCHAR(50),
    current_time_seconds INTEGER DEFAULT 0,
    total_duration_seconds INTEGER,
    watch_progress_percentage DECIMAL(5,2) DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    last_watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Plan progress table
CREATE TABLE IF NOT EXISTS plan_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    yml_plan_id UUID NOT NULL,
    module_id VARCHAR(100) NOT NULL,
    topic_code VARCHAR(50) NOT NULL,
    completion_percentage DECIMAL(5,2) DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    videos_completed INTEGER DEFAULT 0,
    exercises_completed INTEGER DEFAULT 0,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, yml_plan_id, module_id, topic_code)
);

-- Unit content table
CREATE TABLE IF NOT EXISTS unit_content (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    yml_plan_id UUID NOT NULL,
    module_id VARCHAR(100) NOT NULL,
    topic_code VARCHAR(50) NOT NULL,
    content_type VARCHAR(50) NOT NULL, -- 'video', 'exercise', 'reading'
    content_id VARCHAR(100),
    content_metadata JSONB,
    order_index INTEGER DEFAULT 0,
    estimated_duration_minutes INTEGER DEFAULT 0,
    difficulty_level VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security events table
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'tab_switch', 'time_jump', 'multiple_tabs', 'suspicious_activity'
    event_data JSONB,
    severity VARCHAR(20) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video analytics table
CREATE TABLE IF NOT EXISTS video_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(50) NOT NULL,
    session_id UUID NOT NULL,
    watch_start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    watch_end_time TIMESTAMP,
    total_watch_time_seconds INTEGER DEFAULT 0,
    engagement_score DECIMAL(5,2),
    interaction_count INTEGER DEFAULT 0,
    completion_rate DECIMAL(5,2) DEFAULT 0,
    heatmap_data JSONB, -- Store time-based interaction data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Video recommendations table
CREATE TABLE IF NOT EXISTS video_recommendations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(50) NOT NULL,
    recommendation_reason VARCHAR(200),
    confidence_score DECIMAL(5,2) DEFAULT 0,
    learning_style VARCHAR(50),
    topic_code VARCHAR(50),
    difficulty_level VARCHAR(20),
    is_watched BOOLEAN DEFAULT FALSE,
    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    watched_at TIMESTAMP
);

-- Engagement metrics table
CREATE TABLE IF NOT EXISTS engagement_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    total_watch_time_minutes INTEGER DEFAULT 0,
    videos_completed INTEGER DEFAULT 0,
    average_engagement_score DECIMAL(5,2) DEFAULT 0,
    learning_streak_days INTEGER DEFAULT 0,
    topics_covered INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, date)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_video_tracking_user_id ON video_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_video_tracking_video_id ON video_tracking(video_id);
CREATE INDEX IF NOT EXISTS idx_video_tracking_yml_plan ON video_tracking(yml_plan_id);
CREATE INDEX IF NOT EXISTS idx_video_tracking_topic ON video_tracking(topic_code);

CREATE INDEX IF NOT EXISTS idx_plan_progress_user_plan ON plan_progress(user_id, yml_plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_progress_topic ON plan_progress(topic_code);

CREATE INDEX IF NOT EXISTS idx_video_analytics_user_video ON video_analytics(user_id, video_id);
CREATE INDEX IF NOT EXISTS idx_video_analytics_session ON video_analytics(session_id);

CREATE INDEX IF NOT EXISTS idx_video_recommendations_user ON video_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_video_recommendations_topic ON video_recommendations(topic_code);

CREATE INDEX IF NOT EXISTS idx_engagement_metrics_user_date ON engagement_metrics(user_id, date);

-- Create triggers for updated_at columns
CREATE TRIGGER update_video_tracking_updated_at 
    BEFORE UPDATE ON video_tracking 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plan_progress_updated_at 
    BEFORE UPDATE ON plan_progress 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_engagement_metrics_updated_at 
    BEFORE UPDATE ON engagement_metrics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO unit_content (yml_plan_id, module_id, topic_code, content_type, content_id, content_metadata, order_index, estimated_duration_minutes, difficulty_level)
VALUES 
    (uuid_generate_v4(), 'algebra_basica', 'ALG001', 'video', 'dQw4w9WgXcQ', '{"title": "Introducción al Álgebra", "description": "Conceptos básicos del álgebra"}', 1, 15, 'beginner'),
    (uuid_generate_v4(), 'ecuaciones_lineales', 'ALG002', 'video', 'dQw4w9WgXcQ', '{"title": "Ecuaciones Lineales", "description": "Resolución de ecuaciones de primer grado"}', 2, 20, 'intermediate');

-- Grant permissions (if using custom roles)
-- Note: This will work with the default 'gameplay' user from docker-compose


