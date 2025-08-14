-- ICFES LEVELING - Analítica detallada para tests diagnósticos
-- Este script crea tablas para almacenar estadísticas detalladas de los tests

-- Tabla para análisis detallados de tests diagnósticos
CREATE TABLE IF NOT EXISTS diagnostic_test_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    diagnostic_test_id UUID REFERENCES diagnostic_tests(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    
    -- Estadísticas básicas
    total_questions INTEGER NOT NULL,
    correct_answers INTEGER NOT NULL,
    wrong_answers INTEGER NOT NULL,
    unanswered_questions INTEGER DEFAULT 0,
    score_percentage DECIMAL(5,2) NOT NULL,
    
    -- Análisis por competencia y componente
    competency_scores JSONB DEFAULT '{}', -- Score por competencia del ICFES
    component_scores JSONB DEFAULT '{}',  -- Score por componente
    cognitive_process_scores JSONB DEFAULT '{}', -- Score por proceso cognitivo
    
    -- Análisis temporal
    total_time_seconds INTEGER NOT NULL,
    average_time_per_question DECIMAL(8,2),
    time_per_topic JSONB DEFAULT '{}',
    questions_with_slow_response JSONB DEFAULT '[]', -- IDs de preguntas con respuesta lenta
    questions_with_fast_response JSONB DEFAULT '[]', -- IDs de preguntas con respuesta rápida
    
    -- Análisis de dificultad
    difficulty_performance JSONB DEFAULT '{}', -- Performance por nivel de dificultad
    easy_questions_score DECIMAL(5,2) DEFAULT 0,
    medium_questions_score DECIMAL(5,2) DEFAULT 0,
    hard_questions_score DECIMAL(5,2) DEFAULT 0,
    
    -- Patrones de respuesta
    response_patterns JSONB DEFAULT '{}', -- Patrones de respuesta (ej: cambios de respuesta)
    confidence_indicators JSONB DEFAULT '{}', -- Indicadores de confianza
    
    -- Análisis comparativo
    percentile_rank DECIMAL(5,2), -- Percentil respecto a otros usuarios
    performance_vs_expected DECIMAL(5,2), -- Performance vs expectativa basada en historial
    
    -- Recomendaciones inteligentes
    recommended_topics TEXT[], -- Temas recomendados para estudio
    critical_weaknesses TEXT[], -- Debilidades críticas identificadas
    learning_style_indicators JSONB DEFAULT '{}', -- Indicadores de estilo de aprendizaje
    
    -- Metadatos
    analysis_version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para seguimiento de mejora en el tiempo
CREATE TABLE IF NOT EXISTS diagnostic_improvement_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    
    -- Métricas de mejora
    first_test_score DECIMAL(5,2),
    latest_test_score DECIMAL(5,2),
    improvement_percentage DECIMAL(5,2),
    tests_taken INTEGER DEFAULT 1,
    
    -- Análisis de tendencias
    score_trend JSONB DEFAULT '[]', -- Array de scores históricos
    topic_improvement JSONB DEFAULT '{}', -- Mejora por tema
    consistency_score DECIMAL(5,2), -- Qué tan consistente es el rendimiento
    
    -- Predicciones
    predicted_icfes_score DECIMAL(5,2), -- Score ICFES predicho
    confidence_level DECIMAL(5,2), -- Nivel de confianza en la predicción
    estimated_study_time_hours INTEGER, -- Tiempo estimado de estudio
    
    -- Hitos y objetivos
    milestones_achieved JSONB DEFAULT '[]', -- Hitos alcanzados
    next_milestone JSONB DEFAULT '{}', -- Próximo hito
    goal_score DECIMAL(5,2), -- Score objetivo
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para patrones de error comunes
CREATE TABLE IF NOT EXISTS diagnostic_error_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    
    -- Tipo de error
    error_type VARCHAR(100) NOT NULL, -- 'conceptual', 'procedural', 'computational', 'reading'
    error_description TEXT,
    frequency INTEGER DEFAULT 1,
    
    -- Contexto del error
    difficulty_level INTEGER,
    question_types TEXT[], -- Tipos de pregunta donde ocurre el error
    cognitive_process VARCHAR(100), -- Proceso cognitivo involucrado
    
    -- Soluciones sugeridas
    recommended_actions JSONB DEFAULT '[]',
    study_resources JSONB DEFAULT '[]',
    practice_exercises JSONB DEFAULT '[]',
    
    -- Seguimiento
    error_resolved BOOLEAN DEFAULT FALSE,
    last_occurrence TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolution_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_diagnostic_analytics_user_subject ON diagnostic_test_analytics(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_analytics_test ON diagnostic_test_analytics(diagnostic_test_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_analytics_score ON diagnostic_test_analytics(score_percentage);
CREATE INDEX IF NOT EXISTS idx_diagnostic_analytics_created ON diagnostic_test_analytics(created_at);

CREATE INDEX IF NOT EXISTS idx_improvement_tracking_user_subject ON diagnostic_improvement_tracking(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_improvement_tracking_score ON diagnostic_improvement_tracking(latest_test_score);

CREATE INDEX IF NOT EXISTS idx_error_patterns_user_subject ON diagnostic_error_patterns(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_error_patterns_topic ON diagnostic_error_patterns(topic_id);
CREATE INDEX IF NOT EXISTS idx_error_patterns_type ON diagnostic_error_patterns(error_type);

-- Trigger para actualizar timestamp
CREATE OR REPLACE FUNCTION update_diagnostic_analytics_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_diagnostic_analytics_timestamp
    BEFORE UPDATE ON diagnostic_test_analytics
    FOR EACH ROW
    EXECUTE FUNCTION update_diagnostic_analytics_timestamp();

CREATE TRIGGER update_improvement_tracking_timestamp
    BEFORE UPDATE ON diagnostic_improvement_tracking
    FOR EACH ROW
    EXECUTE FUNCTION update_diagnostic_analytics_timestamp();

-- Comentarios para documentación
COMMENT ON TABLE diagnostic_test_analytics IS 'Análisis detallado de cada test diagnóstico realizado';
COMMENT ON COLUMN diagnostic_test_analytics.competency_scores IS 'Puntuación por competencia ICFES (JSON)';
COMMENT ON COLUMN diagnostic_test_analytics.component_scores IS 'Puntuación por componente ICFES (JSON)';
COMMENT ON COLUMN diagnostic_test_analytics.cognitive_process_scores IS 'Puntuación por proceso cognitivo (JSON)';
COMMENT ON COLUMN diagnostic_test_analytics.percentile_rank IS 'Percentil respecto a otros usuarios del mismo nivel';

COMMENT ON TABLE diagnostic_improvement_tracking IS 'Seguimiento de mejora del usuario en el tiempo';
COMMENT ON COLUMN diagnostic_improvement_tracking.consistency_score IS 'Medida de consistencia en el rendimiento (0-100)';
COMMENT ON COLUMN diagnostic_improvement_tracking.predicted_icfes_score IS 'Score ICFES predicho basado en tendencias';

COMMENT ON TABLE diagnostic_error_patterns IS 'Patrones de errores comunes identificados por usuario y materia';
COMMENT ON COLUMN diagnostic_error_patterns.error_type IS 'Tipo de error: conceptual, procedural, computational, reading';