-- ================================================
-- MIGRACIÓN COMPLETA SISTEMA ICFES
-- ================================================

BEGIN;

-- 1. CREAR TABLA MAESTRA DE TEMAS ICFES
CREATE TABLE IF NOT EXISTS study_topics_catalog (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_tema VARCHAR(20) UNIQUE NOT NULL,
    area_evaluada VARCHAR(30) NOT NULL,
    tema_principal VARCHAR(100) NOT NULL,
    subtema VARCHAR(100),
    tema_especifico VARCHAR(150),
    
    -- Clasificación ICFES
    competencia_icfes VARCHAR(150) NOT NULL,
    componente VARCHAR(50),
    afirmacion TEXT,
    evidencia TEXT,
    
    -- Estructura curricular
    grado_introduccion VARCHAR(10),
    prerequisitos TEXT[],
    temas_relacionados TEXT[],
    
    -- Configuración pedagógica
    orden_secuencial INTEGER,
    nivel_dificultad INTEGER CHECK (nivel_dificultad BETWEEN 1 AND 5),
    importancia_icfes INTEGER CHECK (importancia_icfes BETWEEN 1 AND 5),
    frecuencia_evaluacion DECIMAL(5,2),
    
    -- Tiempo de estudio
    horas_teoria INTEGER,
    horas_practica INTEGER,
    numero_ejercicios_recomendados INTEGER,
    sesiones_refuerzo INTEGER,
    
    -- Recursos
    recursos_teoria TEXT[],
    recursos_practica TEXT[],
    recursos_evaluacion TEXT[],
    
    -- Métricas
    umbral_dominio DECIMAL(5,2),
    tiempo_retencion INTEGER,
    indicadores_dominio TEXT[],
    
    -- Personalización
    estilo_aprendizaje_optimo VARCHAR(30),
    metodologia_recomendada VARCHAR(50),
    tipo_evaluacion VARCHAR(30),
    
    -- Metadatos
    estado VARCHAR(20) DEFAULT 'activo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. EXTENSIÓN DE TABLA QUESTIONS EXISTENTE
ALTER TABLE questions 
    -- Campos ICFES core
    ADD COLUMN IF NOT EXISTS competencia VARCHAR(150),
    ADD COLUMN IF NOT EXISTS componente VARCHAR(50),
    ADD COLUMN IF NOT EXISTS proceso_cognitivo VARCHAR(30),
    ADD COLUMN IF NOT EXISTS tipo_conocimiento VARCHAR(30),
    
    -- Parámetros psicométricos IRT
    ADD COLUMN IF NOT EXISTS indice_discriminacion DECIMAL(4,3),
    ADD COLUMN IF NOT EXISTS parametro_irt_a DECIMAL(4,3),
    ADD COLUMN IF NOT EXISTS parametro_irt_b DECIMAL(4,3),
    ADD COLUMN IF NOT EXISTS parametro_irt_c DECIMAL(4,3),
    
    -- Información pedagógica
    ADD COLUMN IF NOT EXISTS afirmacion TEXT,
    ADD COLUMN IF NOT EXISTS evidencia TEXT,
    ADD COLUMN IF NOT EXISTS nivel_desempeno_esperado VARCHAR(20),
    ADD COLUMN IF NOT EXISTS tiempo_estimado INTEGER,
    
    -- Sistema de scaffolding
    ADD COLUMN IF NOT EXISTS pista_1 TEXT,
    ADD COLUMN IF NOT EXISTS pista_2 TEXT,
    ADD COLUMN IF NOT EXISTS pista_3 TEXT,
    ADD COLUMN IF NOT EXISTS explicacion_respuesta TEXT,
    ADD COLUMN IF NOT EXISTS error_comun TEXT,
    
    -- Análisis de distractores
    ADD COLUMN IF NOT EXISTS distractor_a_concepto VARCHAR(100),
    ADD COLUMN IF NOT EXISTS distractor_b_concepto VARCHAR(100),
    ADD COLUMN IF NOT EXISTS distractor_c_concepto VARCHAR(100),
    ADD COLUMN IF NOT EXISTS frecuencia_error_a DECIMAL(5,2),
    ADD COLUMN IF NOT EXISTS frecuencia_error_b DECIMAL(5,2),
    ADD COLUMN IF NOT EXISTS frecuencia_error_c DECIMAL(5,2),
    
    -- Referencias al catálogo
    ADD COLUMN IF NOT EXISTS codigo_tema VARCHAR(20) REFERENCES study_topics_catalog(codigo_tema);

-- 3. CREAR TABLA DE PREREQUISITOS
CREATE TABLE IF NOT EXISTS prerequisitos_temas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tema_principal VARCHAR(100) NOT NULL,
    tema_prerequisito VARCHAR(100) NOT NULL,
    area_evaluada VARCHAR(30) NOT NULL,
    nivel_importancia INTEGER DEFAULT 1,
    grado_prerequisito VARCHAR(10),
    orden_sugerido INTEGER,
    es_obligatorio BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_prerequisito UNIQUE(tema_principal, tema_prerequisito)
);

-- 4. CREAR SISTEMA DE RECURSOS
CREATE TABLE IF NOT EXISTS learning_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    codigo_tema VARCHAR(20) REFERENCES study_topics_catalog(codigo_tema),
    area_evaluada VARCHAR(30) NOT NULL,
    tipo_recurso VARCHAR(30),
    formato VARCHAR(20),
    url VARCHAR(500),
    nivel_dificultad INTEGER,
    duracion_minutos INTEGER,
    calificacion_promedio DECIMAL(3,2),
    efectividad_medida DECIMAL(5,2),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. SISTEMA DE PERFORMANCE ANALYTICS
CREATE TABLE IF NOT EXISTS topic_performance_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    codigo_tema VARCHAR(20) REFERENCES study_topics_catalog(codigo_tema),
    nivel_inicial DECIMAL(5,2),
    nivel_actual DECIMAL(5,2),
    nivel_objetivo DECIMAL(5,2),
    velocidad_aprendizaje DECIMAL(5,2),
    tiempo_total_dedicado INTEGER,
    ultima_practica DATE,
    necesita_refuerzo BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. ÍNDICES PARA OPTIMIZACIÓN
CREATE INDEX IF NOT EXISTS idx_questions_competencia ON questions(competencia);
CREATE INDEX IF NOT EXISTS idx_questions_codigo_tema ON questions(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_topics_area ON study_topics_catalog(area_evaluada);
CREATE INDEX IF NOT EXISTS idx_topics_codigo ON study_topics_catalog(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_performance_user_topic ON topic_performance_analytics(user_id, codigo_tema);
CREATE INDEX IF NOT EXISTS idx_resources_tema ON learning_resources(codigo_tema);

-- 7. FUNCIÓN PARA ACTUALIZAR TIMESTAMP
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 8. TRIGGERS PARA ACTUALIZACIÓN AUTOMÁTICA
CREATE TRIGGER update_study_topics_catalog_updated_at 
    BEFORE UPDATE ON study_topics_catalog 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- ================================================
-- VERIFICACIÓN DE LA MIGRACIÓN
-- ================================================

-- Verificar que las tablas se crearon correctamente
SELECT 
    table_name,
    column_count
FROM (
    SELECT 'study_topics_catalog' as table_name, COUNT(*) as column_count 
    FROM information_schema.columns 
    WHERE table_name = 'study_topics_catalog'
    UNION ALL
    SELECT 'learning_resources' as table_name, COUNT(*) as column_count 
    FROM information_schema.columns 
    WHERE table_name = 'learning_resources'
    UNION ALL
    SELECT 'topic_performance_analytics' as table_name, COUNT(*) as column_count 
    FROM information_schema.columns 
    WHERE table_name = 'topic_performance_analytics'
) t;

-- Verificar que se agregaron las columnas a questions
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'questions' 
AND column_name IN ('competencia', 'codigo_tema', 'parametro_irt_a')
ORDER BY column_name;
