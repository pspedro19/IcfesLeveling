-- Enhanced YouTube Catalog Tables (Fallback version without pgvector)
-- Created for video recommendation system
-- Fallback version using TEXT columns instead of vector for embeddings

-- Helper functions for checking PostgreSQL extensions and types
CREATE OR REPLACE FUNCTION check_extension_exists(ext_name text) RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM pg_extension WHERE extname = ext_name);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION check_type_exists(type_name text) RETURNS boolean AS $$
BEGIN
    RETURN EXISTS (SELECT 1 FROM pg_type WHERE typname = type_name);
END;
$$ LANGUAGE plpgsql;

-- Enhanced YouTube Catalog table with semantic search capabilities (fallback version)
CREATE TABLE IF NOT EXISTS youtube_catalog (
    id SERIAL PRIMARY KEY,
    video_id VARCHAR(20) UNIQUE NOT NULL, -- YouTube video ID
    title VARCHAR(500) NOT NULL,
    description TEXT,
    url VARCHAR(500) NOT NULL,
    embed_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    
    -- Video metadata
    duration_seconds INTEGER,
    channel VARCHAR(200),
    published_at TIMESTAMP,
    view_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    
    -- Educational content classification
    subject_id INTEGER REFERENCES subjects(id),
    topic_id INTEGER REFERENCES topics(id),
    difficulty_level VARCHAR(20) DEFAULT 'medium',
    target_audience VARCHAR(50) DEFAULT 'students',
    
    -- IRT Parameters for difficulty matching
    difficulty_parameter DECIMAL(10, 6) DEFAULT 0.0, -- b parameter in IRT
    discrimination_parameter DECIMAL(10, 6) DEFAULT 1.0, -- a parameter in IRT
    guessing_parameter DECIMAL(10, 6) DEFAULT 0.0, -- c parameter in IRT
    
    -- Quality and recommendation scores
    quality_score DECIMAL(5, 3) DEFAULT 0.0, -- 0.0 to 1.0
    educational_value DECIMAL(5, 3) DEFAULT 0.0, -- 0.0 to 1.0
    engagement_score DECIMAL(5, 3) DEFAULT 0.0, -- 0.0 to 1.0
    
    -- Content analysis (using TEXT for embeddings fallback)
    title_embedding TEXT, -- Serialized embedding vector as JSON
    description_embedding TEXT, -- Serialized embedding vector as JSON
    combined_embedding TEXT, -- Combined title + description embedding
    
    -- Keywords and tags for text-based matching
    keywords TEXT[], -- Array of keywords extracted from content
    learning_objectives TEXT[], -- Learning objectives this video addresses
    prerequisite_topics TEXT[], -- Prerequisites for understanding this video
    related_concepts TEXT[], -- Related mathematical/educational concepts
    
    -- Content categorization
    video_type VARCHAR(50) DEFAULT 'instructional', -- instructional, practice, review, example
    explanation_style VARCHAR(50) DEFAULT 'standard', -- visual, auditory, step-by-step, conceptual
    language VARCHAR(10) DEFAULT 'es', -- es, en, etc.
    
    -- Estimated learning metrics
    estimated_study_time INTEGER DEFAULT 0, -- Minutes needed to study this content
    complexity_level INTEGER DEFAULT 1, -- 1-5 scale
    prerequisite_level INTEGER DEFAULT 0, -- Required knowledge level (0-10)
    
    -- Administrative fields
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false, -- Whether content has been verified by educators
    verification_notes TEXT,
    content_warnings TEXT[], -- Any warnings about content
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_analyzed_at TIMESTAMP WITH TIME ZONE, -- When content was last analyzed for embeddings
    
    -- Indexes for performance
    CONSTRAINT valid_quality_score CHECK (quality_score >= 0.0 AND quality_score <= 1.0),
    CONSTRAINT valid_educational_value CHECK (educational_value >= 0.0 AND educational_value <= 1.0),
    CONSTRAINT valid_engagement_score CHECK (engagement_score >= 0.0 AND engagement_score <= 1.0),
    CONSTRAINT valid_complexity_level CHECK (complexity_level >= 1 AND complexity_level <= 5),
    CONSTRAINT valid_prerequisite_level CHECK (prerequisite_level >= 0 AND prerequisite_level <= 10)
);

-- Video statistics and analytics table
CREATE TABLE IF NOT EXISTS video_stats (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES youtube_catalog(id) ON DELETE CASCADE,
    
    -- Recommendation statistics
    total_recommendations INTEGER DEFAULT 0,
    successful_recommendations INTEGER DEFAULT 0, -- When student actually watched/engaged
    recommendation_success_rate DECIMAL(5, 3) DEFAULT 0.0,
    
    -- Student engagement metrics
    total_views INTEGER DEFAULT 0,
    unique_viewers INTEGER DEFAULT 0,
    average_watch_time_seconds INTEGER DEFAULT 0,
    completion_rate DECIMAL(5, 3) DEFAULT 0.0, -- Percentage of video watched on average
    
    -- Educational effectiveness
    helped_count INTEGER DEFAULT 0, -- Students who marked as helpful
    not_helpful_count INTEGER DEFAULT 0, -- Students who marked as not helpful
    helpfulness_score DECIMAL(5, 3) DEFAULT 0.0,
    
    -- Performance improvement tracking
    students_improved INTEGER DEFAULT 0, -- Students who improved after watching
    average_score_improvement DECIMAL(5, 3) DEFAULT 0.0,
    
    -- Temporal metrics
    last_recommended_at TIMESTAMP WITH TIME ZONE,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_video_stats UNIQUE(video_id),
    CONSTRAINT valid_completion_rate CHECK (completion_rate >= 0.0 AND completion_rate <= 1.0),
    CONSTRAINT valid_helpfulness_score CHECK (helpfulness_score >= 0.0 AND helpfulness_score <= 1.0)
);

-- Student video interactions tracking
CREATE TABLE IF NOT EXISTS student_video_interactions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES youtube_catalog(id) ON DELETE CASCADE,
    question_id INTEGER REFERENCES questions(id) ON DELETE SET NULL, -- Question that led to this recommendation
    
    -- Interaction details
    recommended_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    first_viewed_at TIMESTAMP WITH TIME ZONE,
    last_viewed_at TIMESTAMP WITH TIME ZONE,
    total_view_time_seconds INTEGER DEFAULT 0,
    max_progress_seconds INTEGER DEFAULT 0, -- Furthest point reached in video
    view_count INTEGER DEFAULT 0,
    
    -- Student feedback
    is_helpful BOOLEAN, -- NULL = no feedback, TRUE = helpful, FALSE = not helpful
    feedback_text TEXT,
    rating INTEGER, -- 1-5 star rating
    feedback_given_at TIMESTAMP WITH TIME ZONE,
    
    -- Learning outcome tracking
    watched_before_retry BOOLEAN DEFAULT false, -- Did student watch before retrying question?
    score_before_video DECIMAL(5, 3), -- Score on question before watching video
    score_after_video DECIMAL(5, 3), -- Score on question after watching video (if retried)
    improvement_score DECIMAL(5, 3), -- Calculated improvement
    
    -- Recommendation context
    recommendation_type VARCHAR(50), -- error_remediation, skill_building, concept_review, direct_practice
    recommendation_confidence DECIMAL(5, 3), -- How confident the algorithm was (0.0-1.0)
    recommendation_rank INTEGER, -- Position in recommendation list (1-N)
    
    -- Status tracking
    is_completed BOOLEAN DEFAULT false, -- Whether student watched significant portion
    completion_percentage DECIMAL(5, 3) DEFAULT 0.0, -- Percentage of video watched
    
    CONSTRAINT unique_student_video_interaction UNIQUE(student_id, video_id, question_id),
    CONSTRAINT valid_rating CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT valid_improvement_score CHECK (improvement_score >= -1.0 AND improvement_score <= 1.0),
    CONSTRAINT valid_recommendation_confidence CHECK (recommendation_confidence >= 0.0 AND recommendation_confidence <= 1.0),
    CONSTRAINT valid_completion_percentage CHECK (completion_percentage >= 0.0 AND completion_percentage <= 1.0)
);

-- Create indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_subject_topic ON youtube_catalog(subject_id, topic_id);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_difficulty ON youtube_catalog(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_quality ON youtube_catalog(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_keywords ON youtube_catalog USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_learning_objectives ON youtube_catalog USING GIN(learning_objectives);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_active ON youtube_catalog(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_video_type ON youtube_catalog(video_type);

-- Indexes for video_stats
CREATE INDEX IF NOT EXISTS idx_video_stats_success_rate ON video_stats(recommendation_success_rate DESC);
CREATE INDEX IF NOT EXISTS idx_video_stats_helpfulness ON video_stats(helpfulness_score DESC);
CREATE INDEX IF NOT EXISTS idx_video_stats_improvement ON video_stats(average_score_improvement DESC);

-- Indexes for student_video_interactions
CREATE INDEX IF NOT EXISTS idx_student_interactions_student ON student_video_interactions(student_id);
CREATE INDEX IF NOT EXISTS idx_student_interactions_video ON student_video_interactions(video_id);
CREATE INDEX IF NOT EXISTS idx_student_interactions_question ON student_video_interactions(question_id);
CREATE INDEX IF NOT EXISTS idx_student_interactions_type ON student_video_interactions(recommendation_type);
CREATE INDEX IF NOT EXISTS idx_student_interactions_helpful ON student_video_interactions(is_helpful) WHERE is_helpful IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_student_interactions_completed ON student_video_interactions(is_completed) WHERE is_completed = true;

-- Create triggers for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_youtube_catalog_updated_at
    BEFORE UPDATE ON youtube_catalog
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_video_stats_updated_at
    BEFORE UPDATE ON video_stats
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function for calculating semantic similarity (fallback using text matching)
CREATE OR REPLACE FUNCTION calculate_text_similarity(text1 TEXT, text2 TEXT)
RETURNS DECIMAL(5, 3) AS $$
DECLARE
    common_words INTEGER;
    total_words INTEGER;
    similarity_score DECIMAL(5, 3);
BEGIN
    -- Simple word-based similarity calculation
    -- In production, this would be replaced with proper vector similarity
    
    -- Convert to lowercase and split into words
    -- Count common words between the two texts
    WITH words1 AS (
        SELECT unnest(string_to_array(lower(regexp_replace(text1, '[^a-záéíóúñ\s]', ' ', 'g')), ' ')) AS word
        WHERE trim(unnest(string_to_array(lower(regexp_replace(text1, '[^a-záéíóúñ\s]', ' ', 'g')), ' '))) != ''
    ),
    words2 AS (
        SELECT unnest(string_to_array(lower(regexp_replace(text2, '[^a-záéíóúñ\s]', ' ', 'g')), ' ')) AS word
        WHERE trim(unnest(string_to_array(lower(regexp_replace(text2, '[^a-záéíóúñ\s]', ' ', 'g')), ' '))) != ''
    ),
    word_stats AS (
        SELECT 
            (SELECT COUNT(DISTINCT w1.word) FROM words1 w1 WHERE w1.word IN (SELECT word FROM words2)) as common,
            (SELECT COUNT(DISTINCT word) FROM (SELECT word FROM words1 UNION SELECT word FROM words2) combined) as total
    )
    SELECT 
        CASE 
            WHEN total = 0 THEN 0.0
            ELSE ROUND((common::DECIMAL / total::DECIMAL), 3)
        END
    INTO similarity_score
    FROM word_stats;
    
    RETURN COALESCE(similarity_score, 0.0);
END;
$$ LANGUAGE plpgsql;

-- Function for finding videos similar to a question (fallback version)
CREATE OR REPLACE FUNCTION find_similar_videos_fallback(
    question_text TEXT,
    question_subject_id INTEGER DEFAULT NULL,
    question_topic_id INTEGER DEFAULT NULL,
    result_limit INTEGER DEFAULT 5
)
RETURNS TABLE(
    video_id INTEGER,
    title VARCHAR(500),
    similarity_score DECIMAL(5, 3),
    quality_score DECIMAL(5, 3),
    combined_score DECIMAL(5, 3)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        yc.id,
        yc.title,
        calculate_text_similarity(question_text, yc.title || ' ' || COALESCE(yc.description, '')) as sim_score,
        yc.quality_score,
        (
            calculate_text_similarity(question_text, yc.title || ' ' || COALESCE(yc.description, '')) * 0.5 +
            yc.quality_score * 0.3 +
            CASE 
                WHEN yc.subject_id = question_subject_id THEN 0.2
                ELSE 0.0
            END
        ) as combined
    FROM youtube_catalog yc
    WHERE yc.is_active = true
    AND (question_subject_id IS NULL OR yc.subject_id = question_subject_id)
    ORDER BY combined DESC, sim_score DESC, yc.quality_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Insert some sample data for testing
INSERT INTO youtube_catalog (
    video_id, title, description, url, embed_url, duration_seconds, channel,
    subject_id, difficulty_level, quality_score, educational_value, engagement_score,
    keywords, learning_objectives, video_type, estimated_study_time
) VALUES 
(
    'dQw4w9WgXcQ', 
    'Introducción al Álgebra: Conceptos Básicos',
    'Video educativo que explica los conceptos fundamentales del álgebra de manera clara y sencilla.',
    'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
    'https://www.youtube.com/embed/dQw4w9WgXcQ',
    600,
    'Matemáticas Fácil',
    1, -- Assuming math subject ID
    'medium',
    0.85,
    0.90,
    0.75,
    ARRAY['álgebra', 'matemáticas', 'básico', 'ecuaciones'],
    ARRAY['Entender variables', 'Resolver ecuaciones simples', 'Aplicar propiedades algebraicas'],
    'instructional',
    25
),
(
    'test123456', 
    'Geometría: Área y Perímetro',
    'Aprende a calcular el área y perímetro de figuras geométricas básicas.',
    'https://www.youtube.com/watch?v=test123456',
    'https://www.youtube.com/embed/test123456',
    450,
    'Geometría Visual',
    1, -- Assuming math subject ID
    'easy',
    0.80,
    0.85,
    0.80,
    ARRAY['geometría', 'área', 'perímetro', 'figuras'],
    ARRAY['Calcular área de rectángulos', 'Calcular perímetro de polígonos'],
    'instructional',
    20
) ON CONFLICT (video_id) DO NOTHING;

-- Initialize video_stats for sample videos
INSERT INTO video_stats (video_id, total_recommendations, successful_recommendations, total_views)
SELECT id, 0, 0, 0 FROM youtube_catalog 
ON CONFLICT (video_id) DO NOTHING;

-- Clean up helper functions (optional)
DROP FUNCTION IF EXISTS check_extension_exists(text);
DROP FUNCTION IF EXISTS check_type_exists(text);

-- Reset sequences to ensure proper auto-increment
SELECT setval('youtube_catalog_id_seq', COALESCE((SELECT MAX(id) FROM youtube_catalog), 1));
SELECT setval('youtube_catalog_video_id_seq', COALESCE((SELECT MAX(video_id) FROM youtube_catalog), 1));

-- Grant permissions (adjust as needed)
-- GRANT ALL PRIVILEGES ON youtube_catalog TO your_app_user;
-- GRANT ALL PRIVILEGES ON video_stats TO your_app_user;
-- GRANT ALL PRIVILEGES ON student_video_interactions TO your_app_user;

-- Final verification
SELECT 'Enhanced YouTube Catalog tables created successfully (fallback version)' as status;