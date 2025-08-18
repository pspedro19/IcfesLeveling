-- ================================================
-- MIGRACIÓN AUTOMÁTICA SISTEMA ICFES
-- Este archivo se ejecuta automáticamente al iniciar PostgreSQL
-- ================================================

-- Verificar si la extensión uuid-ossp está disponible
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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
DO $$ 
BEGIN
    -- Campos ICFES core
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'competencia') THEN
        ALTER TABLE questions ADD COLUMN competencia VARCHAR(150);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'componente') THEN
        ALTER TABLE questions ADD COLUMN componente VARCHAR(50);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'proceso_cognitivo') THEN
        ALTER TABLE questions ADD COLUMN proceso_cognitivo VARCHAR(30);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'tipo_conocimiento') THEN
        ALTER TABLE questions ADD COLUMN tipo_conocimiento VARCHAR(30);
    END IF;
    
    -- Parámetros psicométricos IRT
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'indice_discriminacion') THEN
        ALTER TABLE questions ADD COLUMN indice_discriminacion DECIMAL(4,3);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'parametro_irt_a') THEN
        ALTER TABLE questions ADD COLUMN parametro_irt_a DECIMAL(4,3);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'parametro_irt_b') THEN
        ALTER TABLE questions ADD COLUMN parametro_irt_b DECIMAL(4,3);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'parametro_irt_c') THEN
        ALTER TABLE questions ADD COLUMN parametro_irt_c DECIMAL(4,3);
    END IF;
    
    -- Información pedagógica
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'afirmacion') THEN
        ALTER TABLE questions ADD COLUMN afirmacion TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'evidencia') THEN
        ALTER TABLE questions ADD COLUMN evidencia TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'nivel_desempeno_esperado') THEN
        ALTER TABLE questions ADD COLUMN nivel_desempeno_esperado VARCHAR(20);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'tiempo_estimado') THEN
        ALTER TABLE questions ADD COLUMN tiempo_estimado INTEGER;
    END IF;
    
    -- Sistema de scaffolding
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'pista_1') THEN
        ALTER TABLE questions ADD COLUMN pista_1 TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'pista_2') THEN
        ALTER TABLE questions ADD COLUMN pista_2 TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'pista_3') THEN
        ALTER TABLE questions ADD COLUMN pista_3 TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'explicacion_respuesta') THEN
        ALTER TABLE questions ADD COLUMN explicacion_respuesta TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'error_comun') THEN
        ALTER TABLE questions ADD COLUMN error_comun TEXT;
    END IF;
    
    -- Análisis de distractores
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'distractor_a_concepto') THEN
        ALTER TABLE questions ADD COLUMN distractor_a_concepto VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'distractor_b_concepto') THEN
        ALTER TABLE questions ADD COLUMN distractor_b_concepto VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'distractor_c_concepto') THEN
        ALTER TABLE questions ADD COLUMN distractor_c_concepto VARCHAR(100);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'frecuencia_error_a') THEN
        ALTER TABLE questions ADD COLUMN frecuencia_error_a DECIMAL(5,2);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'frecuencia_error_b') THEN
        ALTER TABLE questions ADD COLUMN frecuencia_error_b DECIMAL(5,2);
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'frecuencia_error_c') THEN
        ALTER TABLE questions ADD COLUMN frecuencia_error_c DECIMAL(5,2);
    END IF;
    
    -- Referencias al catálogo
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'questions' AND column_name = 'codigo_tema') THEN
        ALTER TABLE questions ADD COLUMN codigo_tema VARCHAR(20);
    END IF;
    
END $$;

-- 3. CREAR TABLA DE PREREQUISITOS
CREATE TABLE IF NOT EXISTS prerequisitos_temas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tema_principal VARCHAR(100) NOT NULL,
    tema_prerequisito VARCHAR(100) NOT NULL,
    nivel_dependencia INTEGER CHECK (nivel_dependencia BETWEEN 1 AND 3),
    tiempo_estimado_prerequisito INTEGER,
    recursos_prerequisito TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_prerequisito UNIQUE(tema_principal, tema_prerequisito)
);

-- 4. CREAR SISTEMA DE RECURSOS
CREATE TABLE IF NOT EXISTS learning_resources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    titulo VARCHAR(200) NOT NULL,
    descripcion TEXT,
    tipo_recurso VARCHAR(30) NOT NULL,
    url_recurso VARCHAR(500),
    contenido_texto TEXT,
    metadata JSONB,
    codigo_tema VARCHAR(20) REFERENCES study_topics_catalog(codigo_tema),
    nivel_dificultad INTEGER CHECK (nivel_dificultad BETWEEN 1 AND 5),
    tiempo_estimado INTEGER,
    tags TEXT[],
    estado VARCHAR(20) DEFAULT 'activo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. SISTEMA DE PERFORMANCE ANALYTICS
CREATE TABLE IF NOT EXISTS topic_performance_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    codigo_tema VARCHAR(20) REFERENCES study_topics_catalog(codigo_tema),
    puntaje_obtenido DECIMAL(5,2),
    tiempo_respuesta INTEGER,
    intentos INTEGER DEFAULT 1,
    nivel_dominio VARCHAR(20),
    fecha_evaluacion TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. CREAR ÍNDICES PARA OPTIMIZACIÓN
CREATE INDEX IF NOT EXISTS idx_study_topics_catalog_codigo ON study_topics_catalog(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_study_topics_catalog_area ON study_topics_catalog(area_evaluada);
CREATE INDEX IF NOT EXISTS idx_study_topics_catalog_competencia ON study_topics_catalog(competencia_icfes);
CREATE INDEX IF NOT EXISTS idx_questions_codigo_tema ON questions(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_questions_competencia ON questions(competencia);
CREATE INDEX IF NOT EXISTS idx_prerequisitos_tema_principal ON prerequisitos_temas(tema_principal);
CREATE INDEX IF NOT EXISTS idx_learning_resources_codigo_tema ON learning_resources(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_topic_performance_user_tema ON topic_performance_analytics(user_id, codigo_tema);

-- 7. CREAR TRIGGER PARA ACTUALIZAR updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_study_topics_catalog_updated_at 
    BEFORE UPDATE ON study_topics_catalog 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 8. INSERTAR DATOS DE PRUEBA (opcional)
INSERT INTO study_topics_catalog (
    codigo_tema, 
    area_evaluada, 
    tema_principal, 
    competencia_icfes,
    nivel_dificultad,
    importancia_icfes,
    estado
) VALUES 
    ('MATH_001', 'Matemáticas', 'Álgebra Básica', 'Resolver ecuaciones lineales', 1, 5, 'activo'),
    ('MATH_002', 'Matemáticas', 'Geometría Euclidiana', 'Calcular áreas y perímetros', 2, 4, 'activo'),
    ('LANG_001', 'Lenguaje', 'Comprensión Lectora', 'Identificar idea principal', 1, 5, 'activo')
ON CONFLICT (codigo_tema) DO NOTHING;

-- 9. VERIFICAR QUE LAS TABLAS SE CREARON CORRECTAMENTE
DO $$
BEGIN
    RAISE NOTICE '✅ Migración ICFES completada exitosamente';
    RAISE NOTICE '   - study_topics_catalog: % registros', (SELECT COUNT(*) FROM study_topics_catalog);
    RAISE NOTICE '   - questions: columnas ICFES agregadas';
    RAISE NOTICE '   - prerequisitos_temas: creada';
    RAISE NOTICE '   - learning_resources: creada';
    RAISE NOTICE '   - topic_performance_analytics: creada';
END $$;
