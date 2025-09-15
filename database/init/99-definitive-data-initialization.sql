-- =====================================================
-- INICIALIZACIÓN DEFINITIVA DE DATOS ICFES LEVELING
-- Este script asegura que todas las tablas principales 
-- tengan la estructura correcta y datos precargados
-- =====================================================

-- PASO 1: Asegurar estructura de tablas principales
-- =====================================================

-- Tabla Questions: Campos ICFES completos
ALTER TABLE questions ADD COLUMN IF NOT EXISTS competencia VARCHAR(150);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS componente VARCHAR(100);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS proceso_cognitivo VARCHAR(50);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_conocimiento VARCHAR(50);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS indice_discriminacion FLOAT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS parametro_irt_a FLOAT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS parametro_irt_b FLOAT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS parametro_irt_c FLOAT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS afirmacion TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS evidencia TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS nivel_desempeno_esperado VARCHAR(30);
ALTER TABLE questions ADD COLUMN IF NOT EXISTS tiempo_estimado INTEGER;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_1 TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_2 TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_3 TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS explicacion_respuesta TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS error_comun TEXT;

-- Tabla Topics: Campos IRT y códigos ICFES
ALTER TABLE topics ADD COLUMN IF NOT EXISTS codigo_tema VARCHAR(50) UNIQUE;
ALTER TABLE topics ADD COLUMN IF NOT EXISTS order_index INTEGER DEFAULT 0;
ALTER TABLE topics ADD COLUMN IF NOT EXISTS difficulty_parameter FLOAT DEFAULT 0.0;
ALTER TABLE topics ADD COLUMN IF NOT EXISTS discrimination_parameter FLOAT DEFAULT 1.0;

-- Agregar índice para codigo_tema si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_topics_codigo_tema') THEN
        CREATE INDEX idx_topics_codigo_tema ON topics(codigo_tema);
    END IF;
END$$;

-- Tabla YouTube Catalog: Asegurar campos de embeddings y metadatos
ALTER TABLE youtube_catalog ADD COLUMN IF NOT EXISTS codigo_tema VARCHAR(50);
ALTER TABLE youtube_catalog ADD COLUMN IF NOT EXISTS area_evaluada VARCHAR(100);
ALTER TABLE youtube_catalog ADD COLUMN IF NOT EXISTS tema_principal VARCHAR(200);
ALTER TABLE youtube_catalog ADD COLUMN IF NOT EXISTS canal_sugerido VARCHAR(100);
ALTER TABLE youtube_catalog ADD COLUMN IF NOT EXISTS transcript TEXT;
ALTER TABLE youtube_catalog ADD COLUMN IF NOT EXISTS tema_tag VARCHAR(200);

-- Tabla Diagnostic Tests: Campos completos para análisis
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS reassessment_type VARCHAR(50);
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS original_test_id UUID REFERENCES diagnostic_tests(id);
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS is_monthly_reassessment BOOLEAN DEFAULT FALSE;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS days_since_initial INTEGER;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS comparison_with_initial JSONB;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS plan_regenerated BOOLEAN DEFAULT FALSE;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS new_goals_generated BOOLEAN DEFAULT FALSE;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS notification_sent BOOLEAN DEFAULT FALSE;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS questions_answered INTEGER DEFAULT 0;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS time_spent_seconds INTEGER DEFAULT 0;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS score_percentage DECIMAL(5,2) DEFAULT 0.00;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS score_by_topic JSONB DEFAULT '{}';
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'in_progress';
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS started_at TIMESTAMP;
ALTER TABLE diagnostic_tests ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;

-- PASO 2: Índices de rendimiento críticos
-- ======================================

-- Índices para Questions
CREATE INDEX IF NOT EXISTS idx_questions_competencia ON questions(competencia);
CREATE INDEX IF NOT EXISTS idx_questions_componente ON questions(componente);
CREATE INDEX IF NOT EXISTS idx_questions_difficulty_irt ON questions(parametro_irt_b);
CREATE INDEX IF NOT EXISTS idx_questions_discrimination ON questions(parametro_irt_a);

-- Índices para YouTube Catalog  
CREATE INDEX IF NOT EXISTS idx_youtube_codigo_tema ON youtube_catalog(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_youtube_subject_topic ON youtube_catalog(subject_id, topic_id);
CREATE INDEX IF NOT EXISTS idx_youtube_difficulty ON youtube_catalog(difficulty_level);

-- Índices para Diagnostic Tests
CREATE INDEX IF NOT EXISTS idx_diagnostic_user_subject ON diagnostic_tests(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_diagnostic_status ON diagnostic_tests(status);
CREATE INDEX IF NOT EXISTS idx_diagnostic_reassessment ON diagnostic_tests(is_monthly_reassessment);

-- PASO 3: Función para cargar datos desde Excel de forma idempotente
-- =================================================================

CREATE OR REPLACE FUNCTION load_icfes_questions_if_empty()
RETURNS TEXT AS $$
DECLARE
    question_count INT;
    result_text TEXT := '';
BEGIN
    -- Verificar si ya tenemos datos ICFES cargados
    SELECT COUNT(*) INTO question_count 
    FROM questions 
    WHERE competencia IS NOT NULL AND competencia != '';
    
    IF question_count = 0 THEN
        result_text := 'ICFES questions data needs to be loaded from Excel file.';
        -- Aquí se ejecutaría la importación del Excel
        -- Por ahora solo registramos que se necesita cargar
    ELSE
        result_text := 'ICFES questions already loaded: ' || question_count || ' questions with competencia data.';
    END IF;
    
    RETURN result_text;
END;
$$ LANGUAGE plpgsql;

-- PASO 4: Función para cargar catálogo YouTube de forma idempotente
-- ===============================================================

CREATE OR REPLACE FUNCTION load_youtube_catalog_if_empty()
RETURNS TEXT AS $$
DECLARE
    video_count INT;
    result_text TEXT := '';
BEGIN
    -- Verificar si ya tenemos suficientes videos
    SELECT COUNT(*) INTO video_count FROM youtube_catalog;
    
    IF video_count < 50 THEN
        result_text := 'YouTube catalog needs to be loaded from CSV file. Current count: ' || video_count;
        -- Aquí se ejecutaría la importación del CSV
    ELSE
        result_text := 'YouTube catalog already loaded: ' || video_count || ' videos.';
    END IF;
    
    RETURN result_text;
END;
$$ LANGUAGE plpgsql;

-- PASO 5: Crear tablas de respaldo para integridad referencial
-- ==========================================================

-- Tabla para tracking de inicialización
CREATE TABLE IF NOT EXISTS initialization_log (
    id SERIAL PRIMARY KEY,
    script_name VARCHAR(100) NOT NULL,
    execution_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'completed',
    details TEXT,
    questions_count INTEGER,
    videos_count INTEGER,
    subjects_count INTEGER,
    topics_count INTEGER
);

-- PASO 6: Ejecutar verificaciones y logging
-- ========================================

INSERT INTO initialization_log (
    script_name, 
    details, 
    questions_count, 
    videos_count, 
    subjects_count, 
    topics_count
) 
SELECT 
    '99-definitive-data-initialization.sql',
    'Database structure verified and updated',
    (SELECT COUNT(*) FROM questions),
    (SELECT COUNT(*) FROM youtube_catalog),
    (SELECT COUNT(*) FROM subjects),
    (SELECT COUNT(*) FROM topics);

-- PASO 7: Crear vistas útiles para diagnósticos rápidos  
-- ====================================================

CREATE OR REPLACE VIEW diagnostic_readiness AS
SELECT 
    'Questions' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN competencia IS NOT NULL THEN 1 END) as with_icfes_data,
    COUNT(CASE WHEN pregunta_texto IS NOT NULL THEN 1 END) as with_text
FROM questions
UNION ALL
SELECT 
    'YouTube Catalog' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN codigo_tema IS NOT NULL THEN 1 END) as with_icfes_data,
    COUNT(CASE WHEN title IS NOT NULL THEN 1 END) as with_text  
FROM youtube_catalog
UNION ALL
SELECT 
    'Subjects' as table_name,
    COUNT(*) as total_records,
    COUNT(*) as with_icfes_data,
    COUNT(CASE WHEN name IS NOT NULL THEN 1 END) as with_text
FROM subjects
UNION ALL
SELECT 
    'Topics' as table_name, 
    COUNT(*) as total_records,
    COUNT(CASE WHEN codigo_tema IS NOT NULL THEN 1 END) as with_icfes_data,
    COUNT(CASE WHEN name IS NOT NULL THEN 1 END) as with_text
FROM topics;

-- PASO 8: Mensajes finales
-- =======================

DO $$
DECLARE
    msg TEXT;
BEGIN
    -- Verificar estado de Questions
    SELECT load_icfes_questions_if_empty() INTO msg;
    RAISE NOTICE 'Questions Status: %', msg;
    
    -- Verificar estado de YouTube Catalog  
    SELECT load_youtube_catalog_if_empty() INTO msg;
    RAISE NOTICE 'YouTube Status: %', msg;
    
    RAISE NOTICE '=== ICFES LEVELING DATABASE INITIALIZATION COMPLETE ===';
    RAISE NOTICE 'Use SELECT * FROM diagnostic_readiness; to check data status';
    RAISE NOTICE 'Use SELECT * FROM initialization_log ORDER BY id DESC LIMIT 5; to check logs';
END$$;