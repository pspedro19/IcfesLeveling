-- =====================================================
-- MIGRACIÓN 003: ICFES VIDEO LEARNING SYSTEM
-- =====================================================
-- Sistema completo de tracking de videos, progreso y analytics
-- =====================================================

-- Tabla para tracking de progreso de videos
CREATE TABLE IF NOT EXISTS video_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(20) NOT NULL, -- YouTube ID
    plan_id UUID NOT NULL,
    unit_number INTEGER NOT NULL,
    codigo_tema VARCHAR(50) NOT NULL,
    watched_seconds FLOAT NOT NULL DEFAULT 0,
    watched_percentage FLOAT NOT NULL DEFAULT 0,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    replay_count INTEGER NOT NULL DEFAULT 0,
    speed_preference VARCHAR(10) DEFAULT '1.0', -- 0.5, 1.0, 1.5, 2.0
    last_watched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Índices para consultas rápidas
    CONSTRAINT unique_user_video UNIQUE(user_id, video_id)
);

-- Tabla para progreso de planes de estudio
CREATE TABLE IF NOT EXISTS plan_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    plan_id UUID NOT NULL,
    unit_number INTEGER NOT NULL,
    weighted_progress FLOAT NOT NULL DEFAULT 0,
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Índices
    CONSTRAINT unique_user_plan_unit UNIQUE(user_id, plan_id, unit_number)
);

-- Tabla para contenido de unidades con pesos
CREATE TABLE IF NOT EXISTS unit_content (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    unit_number INTEGER NOT NULL,
    codigo_tema VARCHAR(50) NOT NULL,
    content_type VARCHAR(20) NOT NULL, -- 'video', 'exercise', 'quiz'
    content_id VARCHAR(255) NOT NULL,
    video_weight FLOAT NOT NULL DEFAULT 0.33,
    difficulty_level INTEGER NOT NULL DEFAULT 1, -- 1-5
    estimated_duration_minutes INTEGER,
    prerequisites TEXT[], -- Array de codigo_tema prerequisitos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Índices
    CONSTRAINT unique_unit_content UNIQUE(unit_number, codigo_tema, content_type)
);

-- Tabla para eventos de seguridad
CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(20),
    alert_type VARCHAR(50) NOT NULL, -- 'INVALID_HASH', 'SUSPICIOUS_JUMP', 'MULTIPLE_TAB_SWITCHES'
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para analytics de videos
CREATE TABLE IF NOT EXISTS video_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id VARCHAR(20) NOT NULL,
    codigo_tema VARCHAR(50) NOT NULL,
    total_views INTEGER NOT NULL DEFAULT 0,
    total_watch_time_seconds BIGINT NOT NULL DEFAULT 0,
    average_completion_rate FLOAT NOT NULL DEFAULT 0,
    difficult_segments JSONB, -- Array de segmentos problemáticos
    learning_style_preferences JSONB, -- Preferencias por estilo de aprendizaje
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Índices
    CONSTRAINT unique_video_analytics UNIQUE(video_id)
);

-- Tabla para recomendaciones de videos
CREATE TABLE IF NOT EXISTS video_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id VARCHAR(20) NOT NULL,
    codigo_tema VARCHAR(50) NOT NULL,
    recommendation_reason TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 1, -- 1-5, donde 5 es más alto
    is_watched BOOLEAN NOT NULL DEFAULT FALSE,
    recommended_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    watched_at TIMESTAMP WITH TIME ZONE,
    
    -- Índices
    CONSTRAINT unique_user_video_recommendation UNIQUE(user_id, video_id)
);

-- Tabla para métricas de engagement en tiempo real
CREATE TABLE IF NOT EXISTS engagement_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR(255) NOT NULL,
    current_video_id VARCHAR(20),
    engagement_score FLOAT NOT NULL DEFAULT 0, -- 0-100
    focus_time_seconds INTEGER NOT NULL DEFAULT 0,
    tab_switches INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Índices
    CONSTRAINT unique_user_session UNIQUE(user_id, session_id)
);

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

-- Índices para video_tracking
CREATE INDEX IF NOT EXISTS idx_video_tracking_user_id ON video_tracking(user_id);
CREATE INDEX IF NOT EXISTS idx_video_tracking_video_id ON video_tracking(video_id);
CREATE INDEX IF NOT EXISTS idx_video_tracking_codigo_tema ON video_tracking(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_video_tracking_created_at ON video_tracking(created_at);

-- Índices para plan_progress
CREATE INDEX IF NOT EXISTS idx_plan_progress_user_id ON plan_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_plan_progress_plan_id ON plan_progress(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_progress_unit_number ON plan_progress(unit_number);

-- Índices para unit_content
CREATE INDEX IF NOT EXISTS idx_unit_content_unit_number ON unit_content(unit_number);
CREATE INDEX IF NOT EXISTS idx_unit_content_codigo_tema ON unit_content(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_unit_content_content_type ON unit_content(content_type);

-- Índices para security_events
CREATE INDEX IF NOT EXISTS idx_security_events_user_id ON security_events(user_id);
CREATE INDEX IF NOT EXISTS idx_security_events_alert_type ON security_events(alert_type);
CREATE INDEX IF NOT EXISTS idx_security_events_created_at ON security_events(created_at);

-- Índices para video_analytics
CREATE INDEX IF NOT EXISTS idx_video_analytics_video_id ON video_analytics(video_id);
CREATE INDEX IF NOT EXISTS idx_video_analytics_codigo_tema ON video_analytics(codigo_tema);

-- Índices para video_recommendations
CREATE INDEX IF NOT EXISTS idx_video_recommendations_user_id ON video_recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_video_recommendations_priority ON video_recommendations(priority);
CREATE INDEX IF NOT EXISTS idx_video_recommendations_is_watched ON video_recommendations(is_watched);

-- Índices para engagement_metrics
CREATE INDEX IF NOT EXISTS idx_engagement_metrics_user_id ON engagement_metrics(user_id);
CREATE INDEX IF NOT EXISTS idx_engagement_metrics_session_id ON engagement_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_engagement_metrics_is_active ON engagement_metrics(is_active);

-- =====================================================
-- FUNCIONES Y TRIGGERS
-- =====================================================

-- Función para actualizar timestamp automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar timestamps
CREATE TRIGGER update_video_tracking_updated_at 
    BEFORE UPDATE ON video_tracking 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plan_progress_updated_at 
    BEFORE UPDATE ON plan_progress 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_video_analytics_updated_at 
    BEFORE UPDATE ON video_analytics 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Función para calcular engagement score
CREATE OR REPLACE FUNCTION calculate_engagement_score(
    focus_time_seconds INTEGER,
    tab_switches INTEGER,
    total_session_time_seconds INTEGER
) RETURNS FLOAT AS $$
BEGIN
    -- Fórmula: (focus_time / total_time) * (1 - tab_switches * 0.1)
    -- Máximo score: 100, Mínimo: 0
    RETURN GREATEST(0, LEAST(100, 
        (focus_time_seconds::FLOAT / GREATEST(total_session_time_seconds, 1)) * 100 * 
        GREATEST(0, 1 - tab_switches * 0.1)
    ));
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- DATOS INICIALES DE EJEMPLO
-- =====================================================

-- Insertar algunos contenidos de unidad de ejemplo
INSERT INTO unit_content (unit_number, codigo_tema, content_type, content_id, video_weight, difficulty_level, estimated_duration_minutes) VALUES
(1, 'MATH_001', 'video', 'dQw4w9WgXcQ', 0.4, 1, 15),
(1, 'MATH_001', 'exercise', 'ex_001', 0.3, 1, 10),
(1, 'MATH_001', 'quiz', 'quiz_001', 0.3, 1, 5),
(2, 'MATH_002', 'video', '9bZkp7q19f0', 0.5, 2, 20),
(2, 'MATH_002', 'exercise', 'ex_002', 0.3, 2, 15),
(2, 'MATH_002', 'quiz', 'quiz_002', 0.2, 2, 10)
ON CONFLICT (unit_number, codigo_tema, content_type) DO NOTHING;

-- Insertar analytics de videos de ejemplo
INSERT INTO video_analytics (video_id, codigo_tema, total_views, total_watch_time_seconds, average_completion_rate) VALUES
('dQw4w9WgXcQ', 'MATH_001', 0, 0, 0.0),
('9bZkp7q19f0', 'MATH_002', 0, 0, 0.0)
ON CONFLICT (video_id) DO NOTHING;

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE video_tracking IS 'Tracking detallado del progreso de videos por usuario';
COMMENT ON TABLE plan_progress IS 'Progreso ponderado de planes de estudio por usuario y unidad';
COMMENT ON TABLE unit_content IS 'Contenido de cada unidad con pesos y prerequisitos';
COMMENT ON TABLE security_events IS 'Eventos de seguridad y detección de trampas';
COMMENT ON TABLE video_analytics IS 'Analytics agregados de videos para insights';
COMMENT ON TABLE video_recommendations IS 'Recomendaciones personalizadas de videos';
COMMENT ON TABLE engagement_metrics IS 'Métricas de engagement en tiempo real';

COMMENT ON COLUMN video_tracking.watched_percentage IS 'Porcentaje del video visto (0-100)';
COMMENT ON COLUMN video_tracking.replay_count IS 'Número de veces que se repitió el video';
COMMENT ON COLUMN video_tracking.speed_preference IS 'Velocidad preferida de reproducción';
COMMENT ON COLUMN unit_content.video_weight IS 'Peso del video en el cálculo de progreso de la unidad';
COMMENT ON COLUMN unit_content.prerequisites IS 'Array de temas que deben completarse antes';
COMMENT ON COLUMN engagement_metrics.engagement_score IS 'Puntuación de engagement (0-100)';

-- =====================================================
-- FIN DE LA MIGRACIÓN
-- =====================================================
