-- Enhanced YouTube Catalog with Vector Embeddings
-- Extends the existing youtube_links table with semantic search capabilities

-- Enable pgvector extension for semantic search
CREATE EXTENSION IF NOT EXISTS vector;

-- Enhanced YouTube catalog table with embeddings and analytics
CREATE TABLE IF NOT EXISTS youtube_catalog (
    id SERIAL PRIMARY KEY,
    video_id SERIAL UNIQUE NOT NULL,
    
    -- YouTube video information
    youtube_id VARCHAR(20) NOT NULL UNIQUE,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    channel VARCHAR(255),
    channel_id VARCHAR(50),
    
    -- Educational categorization
    subject_id INTEGER NOT NULL,
    topic_id INTEGER,
    competence VARCHAR(100),
    component VARCHAR(100),
    language VARCHAR(10) DEFAULT 'es',
    
    -- Video metadata
    duration_sec INTEGER DEFAULT 0,
    view_count BIGINT DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    
    -- IRT and difficulty parameters
    irt_b FLOAT, -- Difficulty parameter from IRT model
    cognitive_level VARCHAR(50) DEFAULT 'understand', -- bloom_level: remember, understand, apply, analyze, evaluate, create
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 10) DEFAULT 5,
    
    -- Quality and engagement metrics
    quality_score DECIMAL(3,2) DEFAULT 0.80,
    relevance_score DECIMAL(3,2) DEFAULT 0.85,
    instructor_verified BOOLEAN DEFAULT FALSE,
    
    -- Vector embeddings for semantic search
    title_embedding vector(1536), -- OpenAI text-embedding-ada-002 dimensions
    description_embedding vector(1536),
    combined_embedding vector(1536), -- Combined title + description + metadata
    
    -- Learning metadata
    estimated_study_minutes INTEGER DEFAULT 15,
    prerequisite_topics TEXT[],
    learning_objectives TEXT[],
    xp_points INTEGER DEFAULT 50,
    
    -- Status and versioning
    is_active BOOLEAN DEFAULT TRUE,
    content_status VARCHAR(20) DEFAULT 'active', -- active, pending, rejected, outdated
    last_validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Foreign key constraints
    CONSTRAINT fk_youtube_catalog_subject FOREIGN KEY (subject_id) REFERENCES subjects(id),
    CONSTRAINT fk_youtube_catalog_topic FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- Video engagement statistics table (separate for performance)
CREATE TABLE IF NOT EXISTS video_stats (
    video_id INTEGER PRIMARY KEY REFERENCES youtube_catalog(video_id) ON DELETE CASCADE,
    
    -- 7-day rolling metrics
    ctr_7d DECIMAL(5,4) DEFAULT 0.0, -- Click-through rate
    completion_rate_7d DECIMAL(5,4) DEFAULT 0.0, -- Completion rate
    avg_watch_sec_7d INTEGER DEFAULT 0, -- Average watch time
    unique_views_7d INTEGER DEFAULT 0,
    
    -- 30-day rolling metrics
    ctr_30d DECIMAL(5,4) DEFAULT 0.0,
    completion_rate_30d DECIMAL(5,4) DEFAULT 0.0,
    avg_watch_sec_30d INTEGER DEFAULT 0,
    unique_views_30d INTEGER DEFAULT 0,
    
    -- All-time metrics
    total_views INTEGER DEFAULT 0,
    total_completions INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2) DEFAULT 0.0,
    total_ratings INTEGER DEFAULT 0,
    
    -- Learning effectiveness
    avg_improvement_score DECIMAL(5,4) DEFAULT 0.0, -- Average performance improvement
    helpful_votes INTEGER DEFAULT 0,
    unhelpful_votes INTEGER DEFAULT 0,
    
    -- Last updated
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Student video interactions for personalized recommendations
CREATE TABLE IF NOT EXISTS student_video_interactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id INTEGER NOT NULL REFERENCES youtube_catalog(video_id) ON DELETE CASCADE,
    
    -- Interaction data
    clicked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    watch_start_time TIMESTAMP WITH TIME ZONE,
    watch_end_time TIMESTAMP WITH TIME ZONE,
    total_watch_seconds INTEGER DEFAULT 0,
    completion_percentage DECIMAL(5,2) DEFAULT 0.0,
    
    -- Learning context
    question_id UUID, -- If clicked from a specific question
    session_id UUID, -- Study session
    recommendation_source VARCHAR(50), -- 'failed_question', 'topic_review', 'suggested', 'search'
    
    -- Feedback
    was_helpful BOOLEAN,
    difficulty_rating INTEGER CHECK (difficulty_rating BETWEEN 1 AND 5),
    quality_rating INTEGER CHECK (quality_rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    
    -- Performance tracking
    performance_before DECIMAL(5,4), -- Performance on topic before watching
    performance_after DECIMAL(5,4), -- Performance on topic after watching
    improvement_delta DECIMAL(5,4), -- Calculated improvement
    
    UNIQUE(student_id, video_id, clicked_at) -- Prevent duplicate clicks in same second
);

-- Indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_subject_topic ON youtube_catalog(subject_id, topic_id);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_difficulty ON youtube_catalog(difficulty_level, irt_b);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_quality ON youtube_catalog(quality_score DESC, relevance_score DESC);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_active ON youtube_catalog(is_active, content_status);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_language ON youtube_catalog(language);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_cognitive ON youtube_catalog(cognitive_level);

-- Vector similarity search indexes
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_combined_embedding ON youtube_catalog 
USING ivfflat (combined_embedding vector_cosine_ops) WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_youtube_catalog_title_embedding ON youtube_catalog 
USING ivfflat (title_embedding vector_cosine_ops) WITH (lists = 100);

-- Video stats indexes
CREATE INDEX IF NOT EXISTS idx_video_stats_ctr_7d ON video_stats(ctr_7d DESC);
CREATE INDEX IF NOT EXISTS idx_video_stats_completion_7d ON video_stats(completion_rate_7d DESC);
CREATE INDEX IF NOT EXISTS idx_video_stats_effectiveness ON video_stats(avg_improvement_score DESC);

-- Student interactions indexes
CREATE INDEX IF NOT EXISTS idx_student_video_interactions_student ON student_video_interactions(student_id);
CREATE INDEX IF NOT EXISTS idx_student_video_interactions_video ON student_video_interactions(video_id);
CREATE INDEX IF NOT EXISTS idx_student_video_interactions_question ON student_video_interactions(question_id);
CREATE INDEX IF NOT EXISTS idx_student_video_interactions_source ON student_video_interactions(recommendation_source);
CREATE INDEX IF NOT EXISTS idx_student_video_interactions_performance ON student_video_interactions(improvement_delta DESC);

-- Triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_youtube_catalog_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_youtube_catalog_updated_at
    BEFORE UPDATE ON youtube_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_youtube_catalog_updated_at();

-- Function to calculate video engagement score
CREATE OR REPLACE FUNCTION calculate_video_engagement_score(
    p_video_id INTEGER
) RETURNS DECIMAL AS $$
DECLARE
    v_ctr DECIMAL;
    v_completion DECIMAL;
    v_improvement DECIMAL;
    v_final_score DECIMAL;
BEGIN
    SELECT 
        COALESCE(ctr_7d, 0),
        COALESCE(completion_rate_7d, 0),
        COALESCE(avg_improvement_score, 0)
    INTO v_ctr, v_completion, v_improvement
    FROM video_stats 
    WHERE video_id = p_video_id;
    
    -- Weighted combination: 30% CTR, 40% completion, 30% learning improvement
    v_final_score := (v_ctr * 0.3) + (v_completion * 0.4) + (v_improvement * 0.3);
    
    RETURN LEAST(1.0, GREATEST(0.0, v_final_score));
END;
$$ LANGUAGE plpgsql;

-- Function to get semantic similarity between embeddings
CREATE OR REPLACE FUNCTION cosine_similarity(
    embedding1 vector(1536),
    embedding2 vector(1536)
) RETURNS FLOAT AS $$
BEGIN
    RETURN 1 - (embedding1 <=> embedding2);
END;
$$ LANGUAGE plpgsql;

-- View for video recommendations with calculated scores
CREATE OR REPLACE VIEW vw_video_recommendations AS
SELECT 
    yc.video_id,
    yc.youtube_id,
    yc.url,
    yc.title,
    yc.description,
    yc.channel,
    yc.subject_id,
    yc.topic_id,
    yc.competence,
    yc.component,
    yc.duration_sec,
    yc.irt_b,
    yc.cognitive_level,
    yc.difficulty_level,
    yc.quality_score,
    yc.relevance_score,
    yc.estimated_study_minutes,
    yc.xp_points,
    yc.is_active,
    -- Engagement metrics
    vs.ctr_7d,
    vs.completion_rate_7d,
    vs.avg_watch_sec_7d,
    vs.avg_improvement_score,
    vs.helpful_votes,
    vs.unhelpful_votes,
    -- Calculated engagement score
    calculate_video_engagement_score(yc.video_id) as engagement_score,
    -- Subject and topic names
    s.name as subject_name,
    t.name as topic_name
FROM youtube_catalog yc
LEFT JOIN video_stats vs ON yc.video_id = vs.video_id
LEFT JOIN subjects s ON yc.subject_id = s.id
LEFT JOIN topics t ON yc.topic_id = t.id
WHERE yc.is_active = TRUE 
  AND yc.content_status = 'active';

-- Insert initial sample data (will be populated by migration script)
INSERT INTO youtube_catalog (
    youtube_id, url, title, description, channel, subject_id, 
    duration_sec, difficulty_level, cognitive_level, quality_score
) VALUES 
('dQw4w9WgXcQ', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 
 'Introducción al Álgebra Básica', 
 'Conceptos fundamentales del álgebra para estudiantes de secundaria',
 'MatemáticasFácil', 1, 900, 3, 'understand', 0.85),
('sample123ABC', 'https://www.youtube.com/watch?v=sample123ABC',
 'Ecuaciones Lineales - Paso a Paso',
 'Aprende a resolver ecuaciones lineales con métodos sistemáticos',
 'AlgebraVirtual', 1, 1200, 4, 'apply', 0.90)
ON CONFLICT (youtube_id) DO NOTHING;

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON youtube_catalog TO gameplay;
GRANT SELECT, INSERT, UPDATE, DELETE ON video_stats TO gameplay;
GRANT SELECT, INSERT, UPDATE, DELETE ON student_video_interactions TO gameplay;
GRANT USAGE, SELECT ON SEQUENCE youtube_catalog_id_seq TO gameplay;
GRANT USAGE, SELECT ON SEQUENCE youtube_catalog_video_id_seq TO gameplay;