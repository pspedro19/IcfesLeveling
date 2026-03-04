-- 1. youtube_videos: Catálogo de videos
CREATE TABLE IF NOT EXISTS youtube_videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    youtube_id VARCHAR(20) UNIQUE NOT NULL, -- ID de YouTube (ej: "dQw4w9WgXcQ")

    -- Metadata
    title VARCHAR(500) NOT NULL,
    description TEXT,
    channel_name VARCHAR(200),
    channel_id VARCHAR(50),
    thumbnail_url VARCHAR(500),
    duration_seconds INTEGER,

    -- Clasificación educativa
    subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 10),

    -- Tags para búsqueda
    tags JSONB DEFAULT '[]', -- ["algebra", "ecuaciones", "lineal"]

    -- Métricas de calidad
    quality_score FLOAT DEFAULT 0.5, -- 0-1, calculado por views/likes
    view_count BIGINT DEFAULT 0,
    like_count INTEGER DEFAULT 0,

    -- Estado
    language VARCHAR(10) DEFAULT 'es',
    is_active BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. question_video_links: Mapeo pregunta ↔ video
CREATE TABLE IF NOT EXISTS question_video_links (
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES youtube_videos(id) ON DELETE CASCADE,

    relevance_score FLOAT DEFAULT 0.5, -- 0-1, qué tan relevante es
    link_type VARCHAR(30) DEFAULT 'explanation', -- 'explanation', 'theory', 'example', 'practice'
    is_primary BOOLEAN DEFAULT FALSE, -- Video principal para esta pregunta

    created_by VARCHAR(50) DEFAULT 'system', -- 'system', 'ai', 'manual'
    created_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (question_id, video_id)
);

-- 3. user_video_progress: Progreso del usuario en videos
CREATE TABLE IF NOT EXISTS user_video_progress (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES youtube_videos(id) ON DELETE CASCADE,

    -- Progreso
    watch_time_seconds INTEGER DEFAULT 0,
    completion_percentage FLOAT DEFAULT 0, -- 0-100
    last_position_seconds INTEGER DEFAULT 0,
    watch_count INTEGER DEFAULT 1,

    -- Interacción
    liked BOOLEAN,
    bookmarked BOOLEAN DEFAULT FALSE,
    notes TEXT,

    -- Fechas
    first_watched_at TIMESTAMPTZ DEFAULT NOW(),
    last_watched_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ, -- Cuando vio 90%+

    PRIMARY KEY (user_id, video_id)
);

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_youtube_videos_subject ON youtube_videos(subject_id);
CREATE INDEX IF NOT EXISTS idx_youtube_videos_topic ON youtube_videos(topic_id);
CREATE INDEX IF NOT EXISTS idx_youtube_videos_quality ON youtube_videos(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_question_video_links_question ON question_video_links(question_id);
CREATE INDEX IF NOT EXISTS idx_user_video_progress_user ON user_video_progress(user_id);
