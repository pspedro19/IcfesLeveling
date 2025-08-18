-- ================================================================================================
-- ICFES LEVELING - CSV MAPPING TABLES FOR SEAMLESS DATA LOADING
-- ================================================================================================
-- CRÍTICO: Estas tablas permiten mapear los CSV de seed_data a la estructura de BD existente
-- Resuelve el gap entre estructura CSV (ICFES) y estructura de BD (gamificada)
-- ================================================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================================================
-- 1. ICFES_AREAS - MAPEO DE ÁREAS CSV A SUBJECTS DB
-- ================================================================================================

CREATE TABLE icfes_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    area_code VARCHAR(10) UNIQUE NOT NULL,           -- Código corto para CSV
    area_name VARCHAR(100) NOT NULL,                 -- Nombre completo del área
    subject_id UUID REFERENCES subjects(id),         -- FK a tabla subjects existente
    icfes_official_name VARCHAR(200),               -- Nombre oficial ICFES
    description TEXT,                                -- Descripción del área
    evaluation_weight DECIMAL(4,2) DEFAULT 25.0,    -- Peso en evaluación ICFES (%)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================================================
-- 2. ICFES_TOPICS_EXTENDED - MAPEO EXTENDIDO DE TEMAS CSV A TOPICS DB
-- ================================================================================================

CREATE TABLE icfes_topics_extended (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    codigo_tema VARCHAR(20) UNIQUE NOT NULL,         -- Código único del CSV
    tema_principal VARCHAR(200) NOT NULL,            -- Tema principal
    subtema VARCHAR(200),                            -- Subtema específico
    tema_especifico VARCHAR(200),                    -- Tema más específico
    
    -- Relaciones con BD existente
    topic_id UUID REFERENCES topics(id),             -- FK a tabla topics existente
    subject_id UUID REFERENCES subjects(id),         -- FK a tabla subjects existente
    
    -- Metadatos ICFES
    area_evaluada VARCHAR(50),                       -- Área de evaluación ICFES
    competencia_icfes VARCHAR(200),                  -- Competencia ICFES
    componente VARCHAR(200),                         -- Componente específico
    afirmacion TEXT,                                 -- Afirmación de la competencia
    evidencia TEXT,                                  -- Evidencia de aprendizaje
    
    -- Estructura curricular
    grado_introduccion INTEGER,                      -- Grado donde se introduce
    prerequisitos JSONB DEFAULT '[]',               -- Lista de códigos prerequisito
    temas_relacionados JSONB DEFAULT '[]',          -- Lista de temas relacionados
    orden_secuencial INTEGER,                       -- Orden en secuencia curricular
    
    -- Metadatos pedagógicos
    nivel_dificultad INTEGER CHECK (nivel_dificultad >= 1 AND nivel_dificultad <= 5),
    importancia_icfes INTEGER CHECK (importancia_icfes >= 1 AND importancia_icfes <= 5),
    frecuencia_evaluacion DECIMAL(4,1),            -- % de aparición en pruebas
    
    -- Planificación de estudio
    horas_teoria INTEGER DEFAULT 0,                 -- Horas teóricas recomendadas
    horas_practica INTEGER DEFAULT 0,               -- Horas prácticas recomendadas
    numero_ejercicios_recomendados INTEGER DEFAULT 0, -- Ejercicios para dominio
    sesiones_refuerzo INTEGER DEFAULT 0,            -- Sesiones de refuerzo
    
    -- Recursos de aprendizaje
    recursos_teoria JSONB DEFAULT '[]',             -- URLs, videos, documentos teóricos
    recursos_practica JSONB DEFAULT '[]',           -- Ejercicios, simulacros
    recursos_evaluacion JSONB DEFAULT '[]',         -- Evaluaciones, tests
    
    -- Métricas de dominio
    umbral_dominio DECIMAL(5,2) DEFAULT 75.0,      -- % mínimo para considerar dominado
    tiempo_retencion INTEGER DEFAULT 21,            -- Días de retención esperada
    indicadores_dominio JSONB DEFAULT '[]',         -- Lista de indicadores
    
    -- Metodología
    estilo_aprendizaje_optimo VARCHAR(50),          -- visual, auditivo, kinestésico
    metodologia_recomendada VARCHAR(100),           -- Metodología pedagógica
    tipo_evaluacion VARCHAR(50),                    -- Tipo de evaluación
    
    -- Estado y metadatos
    estado VARCHAR(20) DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'revision')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ================================================================================================ 
-- 3. YOUTUBE_VIDEOS_ENRICHED - VIDEOS CON METADATOS ENRIQUECIDOS
-- ================================================================================================

CREATE TABLE youtube_videos_enriched (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relación con temas
    codigo_tema VARCHAR(20) REFERENCES icfes_topics_extended(codigo_tema),
    topic_id UUID REFERENCES topics(id),           -- FK directa a topics
    
    -- Datos de YouTube
    youtube_video_id VARCHAR(50) NOT NULL,         -- ID único de YouTube
    youtube_url VARCHAR(500) NOT NULL,             -- URL completa
    titulo_video VARCHAR(500),                     -- Título del video
    descripcion TEXT,                              -- Descripción del video
    canal_sugerido VARCHAR(100),                   -- Canal de YouTube
    
    -- Metadatos técnicos
    duracion_segundos INTEGER,                     -- Duración en segundos
    fecha_publicacion DATE,                        -- Fecha de publicación original
    idioma VARCHAR(5) DEFAULT 'es',               -- Idioma del video
    tiene_subtitulos BOOLEAN DEFAULT FALSE,        -- Disponibilidad de subtítulos
    
    -- Métricas de YouTube
    view_count BIGINT,                             -- Número de visualizaciones
    like_count INTEGER,                            -- Número de likes
    
    -- Metadatos pedagógicos
    nivel_dificultad INTEGER CHECK (nivel_dificultad >= 1 AND nivel_dificultad <= 5),
    proceso_cognitivo VARCHAR(50),                 -- Tipo de proceso cognitivo
    calidad_pedagogica DECIMAL(3,2) CHECK (calidad_pedagogica >= 0 AND calidad_pedagogica <= 5),
    orden_sugerido INTEGER,                        -- Orden recomendado en secuencia
    prerequisitos_video JSONB DEFAULT '[]',        -- Videos prerequisito
    
    -- Métricas de efectividad
    efectividad_historica DECIMAL(5,2),           -- % de efectividad histórica
    tiempo_promedio_visto INTEGER,                 -- Tiempo promedio visto (segundos)
    tags_pedagogicos JSONB DEFAULT '[]',          -- Tags educativos
    
    -- Estado y verificación
    estado_disponibilidad VARCHAR(20) DEFAULT 'activo' CHECK (estado_disponibilidad IN ('activo', 'inactivo', 'privado', 'eliminado')),
    fecha_verificacion DATE,                       -- Última verificación de disponibilidad
    ultimo_check_automatico TIMESTAMP,            -- Último check automático
    
    -- Metadatos
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(youtube_video_id, codigo_tema)         -- Un video puede estar en múltiples temas
);

-- ================================================================================================
-- 4. STUDY_PLAN_TEMPLATES_ICFES - PLANTILLAS DE PLANES DE ESTUDIO
-- ================================================================================================

CREATE TABLE study_plan_templates_icfes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Relación con subjects
    subject_id UUID REFERENCES subjects(id),
    subject_name VARCHAR(100) NOT NULL,
    
    -- Estructura de unidad
    unit_number INTEGER NOT NULL,
    unit_name VARCHAR(200) NOT NULL,
    unit_description TEXT,
    
    -- Contenido de la unidad  
    topics_list TEXT[],                           -- Array de nombres de temas
    topic_codes VARCHAR(20)[],                    -- Array de códigos de temas
    
    -- Priorización y enfoque
    recommendations_priority VARCHAR(20) CHECK (recommendations_priority IN ('high', 'medium', 'low')),
    weak_areas TEXT[],                           -- Áreas típicamente débiles
    focus_topics TEXT[],                         -- Temas de enfoque principal
    
    -- Planificación temporal
    study_time VARCHAR(20),                      -- Tiempo de estudio recomendado
    estimated_hours INTEGER,                     -- Horas estimadas para completar
    difficulty_level INTEGER CHECK (difficulty_level >= 1 AND difficulty_level <= 5),
    
    -- Peso en ICFES
    icfes_weight DECIMAL(4,2),                  -- Peso de esta unidad en ICFES (0-1)
    
    -- Metodología
    learning_approach VARCHAR(100),              -- Enfoque de aprendizaje
    assessment_type VARCHAR(50),                 -- Tipo de evaluación
    
    -- Secuenciación
    prerequisite_units INTEGER[],               -- Unidades prerequisito
    recommended_sequence INTEGER,               -- Secuencia recomendada
    
    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(subject_id, unit_number)            -- Una unidad por número por materia
);

-- ================================================================================================
-- 5. QUESTIONS_ICFES_METADATA - METADATOS EXTENDIDOS PARA PREGUNTAS
-- ================================================================================================

CREATE TABLE questions_icfes_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    
    -- ID original del CSV
    id_pregunta_original VARCHAR(50),           -- ID original del CSV
    
    -- Clasificación ICFES
    area_evaluada VARCHAR(50),                 -- Área de evaluación
    competencia VARCHAR(200),                  -- Competencia específica
    componente VARCHAR(200),                   -- Componente de la competencia
    proceso_cognitivo VARCHAR(100),           -- Proceso cognitivo evaluado
    tipo_conocimiento VARCHAR(50),            -- Tipo de conocimiento
    
    -- Contexto y clasificación
    afirmacion TEXT,                          -- Afirmación de la competencia
    evidencia TEXT,                           -- Evidencia específica
    tema_especifico VARCHAR(200),             -- Tema específico
    subtema VARCHAR(200),                     -- Subtema
    grado_escolar INTEGER,                    -- Grado escolar objetivo
    
    -- Metadatos pedagógicos
    nivel_desempeno_esperado VARCHAR(50),     -- Nivel de desempeño
    tiempo_estimado INTEGER,                  -- Tiempo estimado en segundos
    puntos_xp INTEGER DEFAULT 100,           -- Puntos de experiencia
    
    -- Recursos de apoyo
    pista_1 TEXT,                            -- Primera pista
    pista_2 TEXT,                            -- Segunda pista
    pista_3 TEXT,                            -- Tercera pista
    explicacion_respuesta TEXT,              -- Explicación de la respuesta
    error_comun TEXT,                        -- Error común de estudiantes
    
    -- Análisis cognitivo
    estrategia_discursiva VARCHAR(100),       -- Estrategia discursiva
    tipo_razonamiento VARCHAR(100),          -- Tipo de razonamiento
    complejidad_cognitiva VARCHAR(50),       -- Complejidad cognitiva
    contexto_aplicacion VARCHAR(100),        -- Contexto de aplicación
    pensamiento_matematico VARCHAR(100),     -- Tipo de pensamiento matemático
    
    -- Parámetros IRT detallados
    parametro_irt_a DECIMAL(6,4),           -- Discriminación
    parametro_irt_b DECIMAL(6,4),           -- Dificultad
    parametro_irt_c DECIMAL(6,4),           -- Adivinanza
    p_value DECIMAL(6,4),                   -- Valor p estadístico
    point_biserial DECIMAL(6,4),           -- Correlación punto-biserial
    
    -- Análisis de distractores
    distractor_a_concepto VARCHAR(200),      -- Concepto del distractor A
    distractor_b_concepto VARCHAR(200),      -- Concepto del distractor B
    distractor_c_concepto VARCHAR(200),      -- Concepto del distractor C
    distractor_frequency_a DECIMAL(4,2),    -- Frecuencia del distractor A
    distractor_frequency_b DECIMAL(4,2),    -- Frecuencia del distractor B
    distractor_frequency_c DECIMAL(4,2),    -- Frecuencia del distractor C
    distractor_frequency_d DECIMAL(4,2),    -- Frecuencia del distractor D
    
    -- Códigos de clasificación
    codigo_tema_principal VARCHAR(20),        -- Código tema principal
    codigos_tema_secundarios VARCHAR(100)[],  -- Códigos temas secundarios
    
    -- Metadatos de calibración
    historical_accuracy_rate DECIMAL(5,2),   -- Tasa de acierto histórica
    sample_size_calibration INTEGER,         -- Tamaño muestra calibración
    item_fit_statistic DECIMAL(6,4),        -- Estadístico de ajuste
    fecha_calibracion DATE,                  -- Fecha de calibración
    
    -- Timing analysis
    avg_response_time_sec INTEGER,           -- Tiempo promedio de respuesta
    std_dev_response_time_sec INTEGER,       -- Desviación estándar del tiempo
    
    -- Metadatos
    fecha_creacion DATE,                     -- Fecha de creación original
    fecha_actualizacion DATE,               -- Fecha de última actualización
    version_item INTEGER DEFAULT 1,         -- Versión del ítem
    banco_origen VARCHAR(50),               -- Banco de origen
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(question_id),                     -- Una metadata por pregunta
    UNIQUE(id_pregunta_original)            -- ID original único
);

-- ================================================================================================
-- 6. ÍNDICES PARA PERFORMANCE
-- ================================================================================================

-- Índices para icfes_areas
CREATE INDEX idx_icfes_areas_area_code ON icfes_areas(area_code);
CREATE INDEX idx_icfes_areas_subject_id ON icfes_areas(subject_id);

-- Índices para icfes_topics_extended
CREATE INDEX idx_icfes_topics_codigo ON icfes_topics_extended(codigo_tema);
CREATE INDEX idx_icfes_topics_area ON icfes_topics_extended(area_evaluada);
CREATE INDEX idx_icfes_topics_topic_id ON icfes_topics_extended(topic_id);
CREATE INDEX idx_icfes_topics_subject_id ON icfes_topics_extended(subject_id);
CREATE INDEX idx_icfes_topics_dificultad ON icfes_topics_extended(nivel_dificultad);

-- Índices para youtube_videos_enriched
CREATE INDEX idx_youtube_videos_codigo_tema ON youtube_videos_enriched(codigo_tema);
CREATE INDEX idx_youtube_videos_topic_id ON youtube_videos_enriched(topic_id);
CREATE INDEX idx_youtube_videos_video_id ON youtube_videos_enriched(youtube_video_id);
CREATE INDEX idx_youtube_videos_disponibilidad ON youtube_videos_enriched(estado_disponibilidad);
CREATE INDEX idx_youtube_videos_calidad ON youtube_videos_enriched(calidad_pedagogica DESC);

-- Índices para study_plan_templates_icfes
CREATE INDEX idx_study_templates_subject ON study_plan_templates_icfes(subject_id);
CREATE INDEX idx_study_templates_unit ON study_plan_templates_icfes(unit_number);
CREATE INDEX idx_study_templates_priority ON study_plan_templates_icfes(recommendations_priority);

-- Índices para questions_icfes_metadata
CREATE INDEX idx_questions_metadata_question_id ON questions_icfes_metadata(question_id);
CREATE INDEX idx_questions_metadata_area ON questions_icfes_metadata(area_evaluada);
CREATE INDEX idx_questions_metadata_tema ON questions_icfes_metadata(tema_especifico);
CREATE INDEX idx_questions_metadata_original_id ON questions_icfes_metadata(id_pregunta_original);
CREATE INDEX idx_questions_metadata_codigo_tema ON questions_icfes_metadata(codigo_tema_principal);

-- ================================================================================================
-- 7. TRIGGERS PARA AUTO-UPDATE DE TIMESTAMPS
-- ================================================================================================

-- Trigger para icfes_topics_extended
CREATE TRIGGER update_icfes_topics_extended_updated_at 
    BEFORE UPDATE ON icfes_topics_extended 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para youtube_videos_enriched
CREATE TRIGGER update_youtube_videos_enriched_updated_at 
    BEFORE UPDATE ON youtube_videos_enriched 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para study_plan_templates_icfes
CREATE TRIGGER update_study_plan_templates_icfes_updated_at 
    BEFORE UPDATE ON study_plan_templates_icfes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger para questions_icfes_metadata
CREATE TRIGGER update_questions_icfes_metadata_updated_at 
    BEFORE UPDATE ON questions_icfes_metadata 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ================================================================================================
-- 8. FUNCIONES DE MAPEO Y UTILIDADES
-- ================================================================================================

-- Función para resolver area_evaluada → subject_id
CREATE OR REPLACE FUNCTION resolve_subject_from_area(area_evaluada TEXT)
RETURNS UUID AS $$
DECLARE
    subject_uuid UUID;
BEGIN
    SELECT subject_id INTO subject_uuid
    FROM icfes_areas 
    WHERE area_name = area_evaluada OR area_code = area_evaluada
    LIMIT 1;
    
    RETURN subject_uuid;
END;
$$ LANGUAGE plpgsql;

-- Función para resolver codigo_tema → topic_id
CREATE OR REPLACE FUNCTION resolve_topic_from_codigo(codigo_tema TEXT)
RETURNS UUID AS $$
DECLARE
    topic_uuid UUID;
BEGIN
    SELECT topic_id INTO topic_uuid
    FROM icfes_topics_extended 
    WHERE codigo_tema = codigo_tema
    LIMIT 1;
    
    RETURN topic_uuid;
END;
$$ LANGUAGE plpgsql;

-- Función para crear topic si no existe
CREATE OR REPLACE FUNCTION create_topic_if_not_exists(
    topic_name TEXT,
    subject_uuid UUID,
    difficulty_level INTEGER DEFAULT 1
) RETURNS UUID AS $$
DECLARE
    topic_uuid UUID;
BEGIN
    -- Buscar topic existente
    SELECT id INTO topic_uuid
    FROM topics 
    WHERE name = topic_name AND subject_id = subject_uuid
    LIMIT 1;
    
    -- Si no existe, crear nuevo
    IF topic_uuid IS NULL THEN
        INSERT INTO topics (id, subject_id, name, difficulty_level)
        VALUES (uuid_generate_v4(), subject_uuid, topic_name, difficulty_level)
        RETURNING id INTO topic_uuid;
    END IF;
    
    RETURN topic_uuid;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================================
-- 9. VISTAS PARA CONSULTAS FRECUENTES
-- ================================================================================================

-- Vista para mapeo completo pregunta → tema → área
CREATE OR REPLACE VIEW questions_complete_mapping AS
SELECT 
    q.id as question_id,
    q.question_text,
    q.correct_answer,
    q.difficulty,
    qm.id_pregunta_original,
    qm.area_evaluada,
    qm.tema_especifico,
    qm.competencia,
    ite.codigo_tema,
    ite.tema_principal,
    ite.subtema,
    t.name as topic_name,
    s.name as subject_name,
    ia.area_code
FROM questions q
LEFT JOIN questions_icfes_metadata qm ON qm.question_id = q.id
LEFT JOIN icfes_topics_extended ite ON ite.codigo_tema = qm.codigo_tema_principal
LEFT JOIN topics t ON t.id = q.topic_id
LEFT JOIN subjects s ON s.id = q.subject_id
LEFT JOIN icfes_areas ia ON ia.subject_id = s.id;

-- Vista para videos por tema con efectividad
CREATE OR REPLACE VIEW videos_by_topic_effectiveness AS
SELECT 
    yve.codigo_tema,
    ite.tema_principal,
    ite.tema_especifico,
    yve.youtube_video_id,
    yve.titulo_video,
    yve.calidad_pedagogica,
    yve.efectividad_historica,
    yve.duracion_segundos,
    yve.estado_disponibilidad,
    t.name as topic_name,
    s.name as subject_name
FROM youtube_videos_enriched yve
JOIN icfes_topics_extended ite ON ite.codigo_tema = yve.codigo_tema
LEFT JOIN topics t ON t.id = yve.topic_id
LEFT JOIN subjects s ON s.id = t.subject_id
WHERE yve.estado_disponibilidad = 'activo'
ORDER BY yve.calidad_pedagogica DESC, yve.efectividad_historica DESC;

-- ================================================================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ================================================================================================

COMMENT ON TABLE icfes_areas IS 'Mapeo entre áreas ICFES del CSV y subjects de la BD';
COMMENT ON TABLE icfes_topics_extended IS 'Metadatos extendidos de temas desde topics_catalog.csv';
COMMENT ON TABLE youtube_videos_enriched IS 'Videos de YouTube con metadatos pedagógicos enriquecidos';
COMMENT ON TABLE study_plan_templates_icfes IS 'Plantillas de planes de estudio basadas en ICFES';
COMMENT ON TABLE questions_icfes_metadata IS 'Metadatos extendidos de preguntas desde questions.csv';

-- Mensaje de confirmación
DO $$
BEGIN
    RAISE NOTICE '✅ CSV MAPPING TABLES CREATED SUCCESSFULLY';
    RAISE NOTICE '🔗 Ready for seamless CSV to database mapping';
    RAISE NOTICE '📊 Support for questions.csv, topics_catalog.csv, youtube_catalog.csv, study_plan_templates.csv';
    RAISE NOTICE '⚡ Next step: Populate reference data and test CSV loading';
END $$;