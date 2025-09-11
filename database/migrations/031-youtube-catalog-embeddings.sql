-- MIGRACIÓN 031: Sistema de catálogo YouTube y embeddings
-- FASE 2 SEMANA 1 - PASO 8-9: Carga de catálogo YouTube y generación de embeddings
-- Fecha: 2025-09-09

-- Habilitar extensión pgvector para embeddings vectoriales
CREATE EXTENSION IF NOT EXISTS vector;

-- ==========================================
-- TABLA: youtube_catalog
-- Catálogo completo de videos YouTube educativos
-- ==========================================

CREATE TABLE IF NOT EXISTS youtube_catalog (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    
    -- Campos básicos del video
    youtube_id VARCHAR(50) UNIQUE NOT NULL,
    url VARCHAR(500) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    channel_name VARCHAR(255),
    
    -- Metadatos educativos del CSV
    codigo_tema VARCHAR(50) NOT NULL,
    area_evaluada VARCHAR(100) NOT NULL,
    tema_principal VARCHAR(255) NOT NULL,
    canal_sugerido VARCHAR(255),
    transcript TEXT,
    tema_tag VARCHAR(255),
    
    -- Metadatos adicionales del video (YouTube API)
    duration_seconds INTEGER,
    thumbnail_url VARCHAR(500),
    published_at TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    
    -- Campos para mapeo con sistema ICFES
    subject_id INTEGER REFERENCES subjects(id),
    topic_id INTEGER REFERENCES topics(id),
    competencias TEXT, -- JSON array de competencias ICFES
    componentes TEXT,  -- JSON array de componentes ICFES
    nivel VARCHAR(50), -- Básico, Intermedio, Avanzado
    
    -- Scoring y calidad
    quality_score DECIMAL(3,2) DEFAULT 0.0,
    relevance_score DECIMAL(3,2) DEFAULT 0.0,
    educational_rating DECIMAL(3,2) DEFAULT 0.0,
    
    -- Estado del procesamiento
    is_processed BOOLEAN DEFAULT FALSE,
    has_embeddings BOOLEAN DEFAULT FALSE,
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, error
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_processed_at TIMESTAMP
);

-- Índices para youtube_catalog
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_youtube_id ON youtube_catalog(youtube_id);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_codigo_tema ON youtube_catalog(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_area_evaluada ON youtube_catalog(area_evaluada);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_tema_principal ON youtube_catalog(tema_principal);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_subject_id ON youtube_catalog(subject_id);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_topic_id ON youtube_catalog(topic_id);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_processing_status ON youtube_catalog(processing_status);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_has_embeddings ON youtube_catalog(has_embeddings);
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_quality_score ON youtube_catalog(quality_score DESC);

-- Índice compuesto para búsquedas frecuentes
CREATE INDEX IF NOT EXISTS idx_youtube_catalog_search ON youtube_catalog(area_evaluada, processing_status, has_embeddings);

-- ==========================================
-- TABLA: content_embeddings
-- Embeddings vectoriales para contenido educativo
-- ==========================================

CREATE TABLE IF NOT EXISTS content_embeddings (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    
    -- Referencia al contenido
    content_type VARCHAR(50) NOT NULL, -- 'youtube_video', 'icfes_question', etc.
    content_id INTEGER NOT NULL,
    content_uuid UUID,
    
    -- Metadatos del embedding
    embedding_type VARCHAR(50) NOT NULL, -- 'title', 'description', 'transcript', 'combined'
    model_name VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-large',
    model_version VARCHAR(50),
    vector_dimensions INTEGER NOT NULL DEFAULT 3072,
    
    -- Vector embedding usando pgvector
    embedding_vector vector(3072) NOT NULL,
    
    -- Texto original usado para generar el embedding
    source_text TEXT NOT NULL,
    source_text_hash VARCHAR(64) NOT NULL,
    
    -- Metadatos del contenido para facilitar búsquedas
    subject_area VARCHAR(100),
    topic VARCHAR(255),
    difficulty_level VARCHAR(50),
    language VARCHAR(10) NOT NULL DEFAULT 'es',
    
    -- Scoring y calidad del embedding
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    processing_time_ms INTEGER,
    token_count INTEGER,
    
    -- Estado y versionado
    is_active VARCHAR(10) NOT NULL DEFAULT 'true',
    version INTEGER NOT NULL DEFAULT 1,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices especializados para content_embeddings

-- Índice HNSW para búsquedas vectoriales ultra-rápidas (mejor para consultas)
CREATE INDEX IF NOT EXISTS idx_content_embeddings_vector_hnsw 
ON content_embeddings 
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Índice IVFFlat para datasets más grandes (alternativo)
-- CREATE INDEX IF NOT EXISTS idx_content_embeddings_vector_ivfflat 
-- ON content_embeddings 
-- USING ivfflat (embedding_vector vector_cosine_ops)
-- WITH (lists = 100);

-- Índices regulares
CREATE INDEX IF NOT EXISTS idx_content_embeddings_content_lookup ON content_embeddings(content_type, content_id, is_active);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_content_uuid ON content_embeddings(content_uuid);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_embedding_type ON content_embeddings(embedding_type);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_hash ON content_embeddings(source_text_hash);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_subject_area ON content_embeddings(subject_area);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_topic ON content_embeddings(topic);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_difficulty ON content_embeddings(difficulty_level);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_active ON content_embeddings(is_active);

-- Índices compuestos para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_content_embeddings_type_active ON content_embeddings(content_type, embedding_type, is_active);
CREATE INDEX IF NOT EXISTS idx_content_embeddings_subject_topic ON content_embeddings(subject_area, topic, difficulty_level);

-- Constraint único para evitar duplicados de embedding por contenido y tipo
CREATE UNIQUE INDEX IF NOT EXISTS idx_content_embeddings_unique_active 
ON content_embeddings(content_type, content_id, embedding_type, source_text_hash) 
WHERE is_active = 'true';

-- ==========================================
-- FUNCIONES AUXILIARES
-- ==========================================

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para updated_at
CREATE TRIGGER update_youtube_catalog_updated_at 
    BEFORE UPDATE ON youtube_catalog 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_content_embeddings_updated_at 
    BEFORE UPDATE ON content_embeddings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- FUNCIONES DE UTILIDAD PARA EMBEDDINGS
-- ==========================================

-- Función para buscar contenido similar usando embeddings
CREATE OR REPLACE FUNCTION find_similar_content(
    query_embedding vector(3072),
    content_type_filter text DEFAULT NULL,
    subject_area_filter text DEFAULT NULL,
    similarity_threshold float DEFAULT 0.3,
    result_limit int DEFAULT 10
)
RETURNS TABLE(
    content_id integer,
    content_type varchar(50),
    embedding_type varchar(50),
    similarity_score float,
    subject_area varchar(100),
    topic varchar(255)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ce.content_id,
        ce.content_type,
        ce.embedding_type,
        (1 - (ce.embedding_vector <=> query_embedding))::float as similarity_score,
        ce.subject_area,
        ce.topic
    FROM content_embeddings ce
    WHERE ce.is_active = 'true'
        AND (content_type_filter IS NULL OR ce.content_type = content_type_filter)
        AND (subject_area_filter IS NULL OR ce.subject_area = subject_area_filter)
        AND (1 - (ce.embedding_vector <=> query_embedding)) >= similarity_threshold
    ORDER BY ce.embedding_vector <=> query_embedding
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener estadísticas de embeddings
CREATE OR REPLACE FUNCTION get_embeddings_stats()
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_embeddings', COUNT(*),
        'active_embeddings', COUNT(*) FILTER (WHERE is_active = 'true'),
        'by_content_type', json_object_agg(content_type, count),
        'by_embedding_type', json_object_agg(embedding_type, count),
        'avg_confidence_score', ROUND(AVG(confidence_score)::numeric, 3)
    )
    INTO result
    FROM (
        SELECT 
            content_type,
            embedding_type,
            confidence_score,
            COUNT(*) OVER (PARTITION BY content_type) as count
        FROM content_embeddings 
        WHERE is_active = 'true'
    ) stats;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- VISTAS DE UTILIDAD
-- ==========================================

-- Vista para videos con embeddings completos
CREATE OR REPLACE VIEW youtube_videos_with_embeddings AS
SELECT 
    yc.*,
    COUNT(ce.id) as embedding_count,
    ARRAY_AGG(DISTINCT ce.embedding_type) as available_embedding_types,
    AVG(ce.confidence_score) as avg_embedding_confidence
FROM youtube_catalog yc
LEFT JOIN content_embeddings ce ON (
    ce.content_type = 'youtube_video' 
    AND ce.content_id = yc.id 
    AND ce.is_active = 'true'
)
WHERE yc.has_embeddings = true 
    AND yc.processing_status = 'completed'
GROUP BY yc.id;

-- Vista para estadísticas de processing
CREATE OR REPLACE VIEW youtube_processing_stats AS
SELECT 
    processing_status,
    COUNT(*) as count,
    ROUND((COUNT(*) * 100.0 / SUM(COUNT(*)) OVER())::numeric, 2) as percentage
FROM youtube_catalog
GROUP BY processing_status
ORDER BY count DESC;

-- ==========================================
-- DATOS DE EJEMPLO Y CONFIGURACIÓN INICIAL
-- ==========================================

-- Insertar configuraciones iniciales si no existen
INSERT INTO system_config (key, value, description, category, created_at)
VALUES 
    ('embeddings.model_name', 'text-embedding-3-large', 'Modelo OpenAI para generar embeddings', 'embeddings', CURRENT_TIMESTAMP),
    ('embeddings.vector_dimensions', '3072', 'Dimensiones del vector embedding', 'embeddings', CURRENT_TIMESTAMP),
    ('embeddings.similarity_threshold', '0.3', 'Umbral mínimo de similaridad', 'embeddings', CURRENT_TIMESTAMP),
    ('embeddings.batch_size', '10', 'Tamaño de lote para procesamiento', 'embeddings', CURRENT_TIMESTAMP),
    ('embeddings.cache_ttl_hours', '24', 'TTL del cache de embeddings en horas', 'embeddings', CURRENT_TIMESTAMP)
ON CONFLICT (key) DO NOTHING;

-- ==========================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- ==========================================

COMMENT ON TABLE youtube_catalog IS 'Catálogo completo de videos YouTube educativos con metadatos enriquecidos';
COMMENT ON TABLE content_embeddings IS 'Embeddings vectoriales para búsqueda semántica de contenido educativo';

COMMENT ON COLUMN youtube_catalog.youtube_id IS 'ID único del video en YouTube (extraído de la URL)';
COMMENT ON COLUMN youtube_catalog.codigo_tema IS 'Código temático del sistema ICFES (ej: CN001, MT002)';
COMMENT ON COLUMN youtube_catalog.processing_status IS 'Estado del procesamiento: pending, processing, completed, error';
COMMENT ON COLUMN youtube_catalog.has_embeddings IS 'Indica si el video tiene embeddings generados';

COMMENT ON COLUMN content_embeddings.embedding_vector IS 'Vector de embeddings usando pgvector (3072 dimensiones)';
COMMENT ON COLUMN content_embeddings.embedding_type IS 'Tipo de embedding: title, description, transcript, combined';
COMMENT ON COLUMN content_embeddings.is_active IS 'Control de versioning - solo embeddings activos se usan';

-- ==========================================
-- FINALIZACIÓN
-- ==========================================

-- Actualizar versión del esquema
INSERT INTO schema_migrations (version, description, applied_at)
VALUES ('031', 'Sistema de catálogo YouTube y embeddings vectoriales', CURRENT_TIMESTAMP)
ON CONFLICT (version) DO NOTHING;

-- Log de la migración
DO $$
BEGIN
    RAISE NOTICE 'Migración 031 completada: Sistema de catálogo YouTube y embeddings';
    RAISE NOTICE 'Tablas creadas: youtube_catalog, content_embeddings';
    RAISE NOTICE 'Extensión habilitada: pgvector';
    RAISE NOTICE 'Funciones creadas: find_similar_content, get_embeddings_stats';
    RAISE NOTICE 'Vistas creadas: youtube_videos_with_embeddings, youtube_processing_stats';
END $$;