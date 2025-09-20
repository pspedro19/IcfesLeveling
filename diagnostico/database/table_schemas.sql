-- ===========================================
-- ESQUEMAS DE TABLAS - SISTEMA DE RECOMENDACIONES
-- ICFES Leveling Platform
-- ===========================================

-- ******************************************
-- 1. TABLA SUBJECTS - Materias/Asignaturas
-- ******************************************
CREATE TABLE subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    icon_url VARCHAR(500),
    color VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_subjects_name ON subjects(name);

-- ******************************************
-- 2. TABLA QUESTIONS - Banco de Preguntas
-- ******************************************
CREATE TABLE questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    topic_id UUID,

    -- Contenido de la pregunta
    question_text TEXT NOT NULL,
    pregunta_texto TEXT,
    pregunta_imagen VARCHAR(500),

    -- Opciones múltiples
    opcion_a_texto TEXT,
    opcion_a_imagen VARCHAR(500),
    opcion_b_texto TEXT,
    opcion_b_imagen VARCHAR(500),
    opcion_c_texto TEXT,
    opcion_c_imagen VARCHAR(500),
    opcion_d_texto TEXT,
    opcion_d_imagen VARCHAR(500),

    -- Respuesta y explicación
    correct_answer VARCHAR(10) NOT NULL,
    respuesta_correcta VARCHAR(1),
    explanation TEXT,
    hint TEXT,

    -- Parámetros IRT 3PL
    parametro_irt_a DOUBLE PRECISION DEFAULT 1.0,    -- Discriminación
    parametro_irt_b DOUBLE PRECISION DEFAULT 0.0,    -- Dificultad
    parametro_irt_c DOUBLE PRECISION DEFAULT 0.25,   -- Adivinanza

    -- Metadatos educativos
    difficulty INTEGER CHECK (difficulty >= 1 AND difficulty <= 10),
    question_type VARCHAR(50) DEFAULT 'multiple_choice',
    tags TEXT[],

    -- Estadísticas
    puntos_xp INTEGER DEFAULT 10,
    indice_discriminacion DOUBLE PRECISION DEFAULT 0.5,
    power_stats JSONB DEFAULT '{"success_rate": 0.6, "discrimination_index": 0.5}',
    options JSONB NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance y búsqueda
CREATE INDEX idx_questions_subject ON questions(subject_id);
CREATE INDEX idx_questions_difficulty ON questions(difficulty);
CREATE INDEX idx_questions_irt_params ON questions(parametro_irt_a, parametro_irt_b, parametro_irt_c);
CREATE INDEX idx_questions_pregunta_texto ON questions(pregunta_texto);
CREATE INDEX idx_questions_topic ON questions(topic_id);

-- ******************************************
-- 3. TABLA DIAGNOSTIC_TESTS - Tests Diagnósticos
-- ******************************************
CREATE TABLE diagnostic_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,

    -- Configuración del test
    test_type VARCHAR(50) DEFAULT 'diagnostic',
    status VARCHAR(20) DEFAULT 'in_progress',

    -- Resultados básicos
    total_questions INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    score_percentage NUMERIC(5,2) DEFAULT 0.00,

    -- Tiempo
    time_taken_seconds INTEGER DEFAULT 0,
    time_spent_seconds INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Análisis avanzado
    strengths JSONB DEFAULT '[]',
    weaknesses JSONB DEFAULT '[]',
    recommendations JSONB DEFAULT '[]',
    score_by_topic JSONB DEFAULT '{}',

    -- Reassessment tracking
    is_monthly_reassessment BOOLEAN DEFAULT false,
    original_test_id UUID REFERENCES diagnostic_tests(id),
    reassessment_type VARCHAR(50),
    days_since_initial INTEGER,
    comparison_with_initial JSONB,

    -- Flags
    plan_regenerated BOOLEAN DEFAULT false,
    new_goals_generated BOOLEAN DEFAULT false,
    notification_sent BOOLEAN DEFAULT false,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para performance
CREATE INDEX idx_diagnostic_tests_user ON diagnostic_tests(user_id);
CREATE INDEX idx_diagnostic_tests_subject ON diagnostic_tests(subject_id);
CREATE INDEX idx_diagnostic_tests_status ON diagnostic_tests(status);
CREATE INDEX idx_diagnostic_tests_monthly_reassessment ON diagnostic_tests(user_id, subject_id, is_monthly_reassessment, created_at);

-- ******************************************
-- 4. TABLA DIAGNOSTIC_TEST_ANSWERS - Respuestas Diagnóstico
-- ******************************************
CREATE TABLE diagnostic_test_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    diagnostic_test_id UUID REFERENCES diagnostic_tests(id) ON DELETE CASCADE,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,

    -- Respuesta del estudiante
    user_answer VARCHAR(10) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    response_time_ms INTEGER,

    -- Análisis IRT
    theta_before DECIMAL(8,4),
    theta_after DECIMAL(8,4),
    information_gained DECIMAL(8,4),
    item_information DECIMAL(8,4),

    -- Metadatos
    question_difficulty INTEGER,
    topic_analyzed VARCHAR(255),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para análisis de patrones
CREATE INDEX idx_diagnostic_answers_test ON diagnostic_test_answers(diagnostic_test_id);
CREATE INDEX idx_diagnostic_answers_question ON diagnostic_test_answers(question_id);
CREATE INDEX idx_diagnostic_answers_incorrect ON diagnostic_test_answers(diagnostic_test_id) WHERE is_correct = false;
CREATE INDEX idx_diagnostic_answers_theta ON diagnostic_test_answers(theta_after);

-- ******************************************
-- 5. TABLA YOUTUBE_CATALOG - Catálogo Videos
-- ******************************************
CREATE TABLE youtube_catalog (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    url VARCHAR(500) NOT NULL,
    description TEXT,

    -- Clasificación
    subject_id UUID REFERENCES subjects(id),
    topic VARCHAR(255),

    -- Metadatos educativos
    duration_minutes INTEGER DEFAULT 15,
    difficulty_level INTEGER DEFAULT 5,
    xp_reward INTEGER DEFAULT 100,

    -- Canal y calidad
    channel_name VARCHAR(255) DEFAULT 'ICFES Prep',
    quality_score DECIMAL(3,2) DEFAULT 0.80,
    engagement_rate DECIMAL(3,2) DEFAULT 0.70,

    -- Estadísticas de uso
    view_count INTEGER DEFAULT 0,
    recommendation_count INTEGER DEFAULT 0,
    completion_rate DECIMAL(3,2) DEFAULT 0.65,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsqueda y recomendación
CREATE INDEX idx_youtube_catalog_subject ON youtube_catalog(subject_id);
CREATE INDEX idx_youtube_catalog_topic ON youtube_catalog(topic);
CREATE INDEX idx_youtube_catalog_difficulty ON youtube_catalog(difficulty_level);
CREATE INDEX idx_youtube_catalog_subject_difficulty ON youtube_catalog(subject_id, difficulty_level);
CREATE INDEX idx_youtube_catalog_quality ON youtube_catalog(quality_score DESC);

-- ******************************************
-- 6. TABLA CONTENT_EMBEDDINGS - Embeddings Vectoriales
-- ******************************************
CREATE TABLE content_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identificación del contenido
    content_type VARCHAR(50) NOT NULL, -- 'question', 'video', 'topic'
    content_id VARCHAR(255) NOT NULL,

    -- Vector embedding (OpenAI text-embedding-3-large)
    embedding_vector FLOAT8[] NOT NULL, -- Array de 3072 dimensiones

    -- Metadatos del modelo
    model_name VARCHAR(100) DEFAULT 'text-embedding-3-large',
    model_version VARCHAR(50) DEFAULT 'v1',
    vector_dimensions INTEGER DEFAULT 3072,

    -- Hash para verificación de integridad
    content_hash VARCHAR(64),

    -- Estadísticas de uso
    similarity_searches_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para búsqueda vectorial
CREATE INDEX idx_content_embeddings_type_id ON content_embeddings(content_type, content_id);
CREATE INDEX idx_content_embeddings_model ON content_embeddings(model_name);

-- Índice vectorial para similitud coseno (requiere extensión vector)
-- CREATE INDEX ON content_embeddings USING ivfflat (embedding_vector vector_cosine_ops);

-- ******************************************
-- 7. TABLA QUESTION_VIDEO_RECOMMENDATIONS - Mapeo Pregunta-Video
-- ******************************************
CREATE TABLE question_video_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES youtube_catalog(id) ON DELETE CASCADE,

    -- Scoring de similitud
    similarity_score DECIMAL(5,4) NOT NULL,
    confidence_score DECIMAL(5,4),

    -- Explicación de la recomendación
    recommendation_reason TEXT,
    algorithm_used VARCHAR(100),
    matching_keywords TEXT[],

    -- Metadatos del análisis
    semantic_similarity DECIMAL(5,4),
    keyword_match_score DECIMAL(5,4),
    difficulty_alignment DECIMAL(5,4),
    topic_relevance DECIMAL(5,4),

    -- Estadísticas de eficacia
    times_recommended INTEGER DEFAULT 0,
    student_engagement_rate DECIMAL(3,2),
    learning_improvement_score DECIMAL(3,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_recommended_at TIMESTAMP
);

-- Índices para recomendación rápida
CREATE INDEX idx_question_video_recommendations_question ON question_video_recommendations(question_id);
CREATE INDEX idx_question_video_recommendations_video ON question_video_recommendations(video_id);
CREATE INDEX idx_question_video_recommendations_score ON question_video_recommendations(similarity_score DESC);
CREATE INDEX idx_question_video_recommendations_confidence ON question_video_recommendations(confidence_score DESC);

-- ******************************************
-- 8. TABLA AI_EXPLANATION - Explicaciones IA
-- ******************************************
CREATE TABLE ai_explanation (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,

    -- Contenido de la explicación
    explanation_text TEXT NOT NULL,
    explanation_type VARCHAR(50), -- 'step_by_step', 'conceptual', 'hint', 'error_analysis'

    -- Personalización
    student_level VARCHAR(50),
    learning_style VARCHAR(50),
    difficulty_adaptation VARCHAR(50),

    -- Metadatos del modelo
    generated_by VARCHAR(100) DEFAULT 'gpt-4',
    model_version VARCHAR(50),
    confidence_score DECIMAL(5,4),
    tokens_used INTEGER,

    -- Contexto de la explicación
    student_answer VARCHAR(10),
    error_type VARCHAR(100),
    conceptual_gaps TEXT[],

    -- Eficacia
    student_rating INTEGER, -- 1-5 stars
    helped_understanding BOOLEAN,
    follow_up_questions TEXT[],

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para análisis de patrones
CREATE INDEX idx_ai_explanation_user ON ai_explanation(user_id);
CREATE INDEX idx_ai_explanation_question ON ai_explanation(question_id);
CREATE INDEX idx_ai_explanation_type ON ai_explanation(explanation_type);
CREATE INDEX idx_ai_explanation_confidence ON ai_explanation(confidence_score DESC);

-- ******************************************
-- 9. TABLA USER_LEARNING_ANALYTICS - Analytics de Aprendizaje
-- ******************************************
CREATE TABLE user_learning_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    subject_id UUID REFERENCES subjects(id),

    -- Métricas IRT
    current_theta DECIMAL(8,4),
    theta_progression JSONB, -- Array de valores theta históricos
    theta_confidence_interval JSONB,

    -- Patrones de aprendizaje
    learning_velocity DECIMAL(5,4), -- Qué tan rápido mejora
    retention_rate DECIMAL(3,2),
    consistency_score DECIMAL(3,2),

    -- Análisis de debilidades
    identified_weaknesses JSONB,
    weakness_improvement_rate JSONB,
    persistent_difficulties TEXT[],

    -- Recomendaciones históricas
    recommendations_received INTEGER DEFAULT 0,
    recommendations_followed INTEGER DEFAULT 0,
    video_completion_rate DECIMAL(3,2),

    -- Fechas de análisis
    analysis_period_start DATE,
    analysis_period_end DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para análisis longitudinal
CREATE INDEX idx_user_learning_analytics_user ON user_learning_analytics(user_id);
CREATE INDEX idx_user_learning_analytics_subject ON user_learning_analytics(subject_id);
CREATE INDEX idx_user_learning_analytics_theta ON user_learning_analytics(current_theta);

-- ******************************************
-- TRIGGERS Y FUNCIONES
-- ******************************************

-- Función para actualizar theta después de cada respuesta
CREATE OR REPLACE FUNCTION update_theta_after_answer()
RETURNS TRIGGER AS $$
BEGIN
    -- Aquí iría la lógica de actualización de theta usando IRT
    -- Por simplicidad, se omite la implementación completa
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar theta automáticamente
CREATE TRIGGER trigger_update_theta
    AFTER INSERT ON diagnostic_test_answers
    FOR EACH ROW
    EXECUTE FUNCTION update_theta_after_answer();

-- ******************************************
-- CONSTRAINTS ADICIONALES
-- ******************************************

-- Validar que los parámetros IRT estén en rangos válidos
ALTER TABLE questions
ADD CONSTRAINT check_irt_a
CHECK (parametro_irt_a >= 0.1 AND parametro_irt_a <= 3.0);

ALTER TABLE questions
ADD CONSTRAINT check_irt_b
CHECK (parametro_irt_b >= -4.0 AND parametro_irt_b <= 4.0);

ALTER TABLE questions
ADD CONSTRAINT check_irt_c
CHECK (parametro_irt_c >= 0.0 AND parametro_irt_c <= 0.5);

-- Validar scores de similitud
ALTER TABLE question_video_recommendations
ADD CONSTRAINT check_similarity_score
CHECK (similarity_score >= 0.0 AND similarity_score <= 1.0);

-- ******************************************
-- COMENTARIOS PARA DOCUMENTACIÓN
-- ******************************************

COMMENT ON TABLE questions IS 'Banco de preguntas con parámetros IRT 3PL para evaluación adaptativa';
COMMENT ON COLUMN questions.parametro_irt_a IS 'Discriminación: capacidad de la pregunta para diferenciar estudiantes (0.1-3.0)';
COMMENT ON COLUMN questions.parametro_irt_b IS 'Dificultad: nivel de habilidad necesario para responder correctamente (-4.0 a 4.0)';
COMMENT ON COLUMN questions.parametro_irt_c IS 'Adivinanza: probabilidad de respuesta correcta por azar (0.0-0.5)';

COMMENT ON TABLE content_embeddings IS 'Embeddings vectoriales OpenAI para análisis semántico y recomendaciones inteligentes';
COMMENT ON COLUMN content_embeddings.embedding_vector IS 'Vector de 3072 dimensiones usando text-embedding-3-large';

COMMENT ON TABLE question_video_recommendations IS 'Mapeo inteligente pregunta-video usando algoritmos ML y embeddings semánticos';
COMMENT ON COLUMN question_video_recommendations.similarity_score IS 'Score de similitud semántica calculado con cosine similarity (0.0-1.0)';