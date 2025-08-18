-- YouTube Links Table for Educational Video Recommendations
-- This table maps ICFES topics to YouTube videos and search queries

CREATE TABLE IF NOT EXISTS youtube_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Topic Mapping
    codigo_tema VARCHAR(10) NOT NULL,
    area_evaluada VARCHAR(100) NOT NULL,
    tema_principal TEXT NOT NULL,
    
    -- YouTube Information
    canal_sugerido VARCHAR(100),
    query_sugerida TEXT NOT NULL,
    youtube_url TEXT NOT NULL,
    
    -- Video Metadata (to be populated by YouTube API)
    youtube_id VARCHAR(20),
    video_title TEXT,
    channel_name VARCHAR(255),
    channel_id VARCHAR(50),
    duration_seconds INTEGER,
    view_count BIGINT,
    like_count INTEGER,
    dislike_count INTEGER,
    comment_count INTEGER,
    
    -- Educational Metrics
    tipo_contenido VARCHAR(50) DEFAULT 'explicativo', -- explicativo, ejercicio_guiado, resumen, etc.
    nivel_dificultad INTEGER CHECK (nivel_dificultad BETWEEN 1 AND 5) DEFAULT 3,
    proceso_cognitivo VARCHAR(50) DEFAULT 'Comprender', -- Comprender, Aplicar, Analizar, Evaluar
    contexto_aplicacion VARCHAR(50) DEFAULT 'Académico', -- Académico, Familiar, Laboral, Comunitario
    
    -- Quality Metrics
    calidad_score DECIMAL(3,2) DEFAULT 0.80,
    relevancia_score DECIMAL(3,2) DEFAULT 0.85,
    ratio_likes DECIMAL(3,2),
    
    -- Learning Metadata
    prerequisitos_video UUID[], -- Referencias a otros videos
    tiempo_estimado_estudio INTEGER DEFAULT 15, -- minutos
    puntos_xp INTEGER DEFAULT 50,
    orden_recomendacion INTEGER DEFAULT 1,
    
    -- Verification
    verificado_instructor BOOLEAN DEFAULT false,
    fecha_verificacion TIMESTAMP WITH TIME ZONE,
    
    -- Status
    estado VARCHAR(20) DEFAULT 'activo', -- activo, inactivo, pendiente_revision
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_validated_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT fk_youtube_links_tema 
        FOREIGN KEY (codigo_tema) 
        REFERENCES study_topics_catalog(codigo_tema) 
        ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_youtube_links_tema ON youtube_links(codigo_tema);
CREATE INDEX IF NOT EXISTS idx_youtube_links_area ON youtube_links(area_evaluada);
CREATE INDEX IF NOT EXISTS idx_youtube_links_dificultad ON youtube_links(nivel_dificultad);
CREATE INDEX IF NOT EXISTS idx_youtube_links_quality ON youtube_links(calidad_score DESC, relevancia_score DESC);
CREATE INDEX IF NOT EXISTS idx_youtube_links_xp ON youtube_links(puntos_xp);
CREATE INDEX IF NOT EXISTS idx_youtube_links_estado ON youtube_links(estado);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_youtube_links_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_youtube_links_updated_at
    BEFORE UPDATE ON youtube_links
    FOR EACH ROW
    EXECUTE FUNCTION update_youtube_links_updated_at();

-- Insert sample data from CSV
-- This will be populated by the Python script



