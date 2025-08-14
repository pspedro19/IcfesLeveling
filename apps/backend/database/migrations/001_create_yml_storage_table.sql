-- Migración: Crear tabla de almacenamiento YML
-- Fecha: 2024-01-01
-- Descripción: Tabla para almacenar metadata de planes YML personalizados

-- Crear tabla user_yml_plans
CREATE TABLE IF NOT EXISTS user_yml_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    subject VARCHAR(50) NOT NULL,
    
    -- Información de almacenamiento
    storage_type VARCHAR(20) NOT NULL, -- 'local', 'spaces', 's3'
    storage_path TEXT NOT NULL,        -- Ruta completa al archivo
    storage_url TEXT,                  -- URL CDN si está disponible
    
    -- Metadata del archivo
    file_size_bytes INTEGER NOT NULL,
    file_hash VARCHAR(64) NOT NULL,    -- MD5 hash para validación
    version INTEGER DEFAULT 1,
    
    -- Detalles de generación
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    generation_time_ms INTEGER,        -- Tiempo de generación en ms
    algorithm_version VARCHAR(20) DEFAULT '1.0',
    
    -- Control de cache
    cache_key VARCHAR(100) NOT NULL,   -- Clave Redis
    cache_ttl INTEGER DEFAULT 3600,   -- TTL en segundos
    
    -- Estadísticas de uso
    last_accessed TIMESTAMP WITH TIME ZONE,
    access_count INTEGER DEFAULT 0,
    
    -- Estado
    is_active BOOLEAN DEFAULT true,
    is_outdated BOOLEAN DEFAULT false, -- Necesita regeneración
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Restricciones
    UNIQUE(user_id, subject, version)
);

-- Crear índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_user_yml_plans_user_subject ON user_yml_plans(user_id, subject, is_active);
CREATE INDEX IF NOT EXISTS idx_user_yml_plans_generated_at ON user_yml_plans(generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_yml_plans_storage_type ON user_yml_plans(storage_type);
CREATE INDEX IF NOT EXISTS idx_user_yml_plans_cache_key ON user_yml_plans(cache_key);

-- Crear trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_yml_plans_updated_at 
    BEFORE UPDATE ON user_yml_plans 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Crear tabla de estadísticas de uso YML (opcional, para analytics)
CREATE TABLE IF NOT EXISTS yml_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    yml_plan_id UUID NOT NULL REFERENCES user_yml_plans(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    subject VARCHAR(50) NOT NULL,
    
    -- Métricas de uso
    time_spent_minutes INTEGER DEFAULT 0,
    modules_completed INTEGER DEFAULT 0,
    lessons_started INTEGER DEFAULT 0,
    exercises_attempted INTEGER DEFAULT 0,
    exercises_completed INTEGER DEFAULT 0,
    
    -- Fechas
    first_access TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_access TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    total_accesses INTEGER DEFAULT 1,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para yml_usage_stats
CREATE INDEX IF NOT EXISTS idx_yml_usage_stats_user_subject ON yml_usage_stats(user_id, subject);
CREATE INDEX IF NOT EXISTS idx_yml_usage_stats_yml_plan ON yml_usage_stats(yml_plan_id);

-- Trigger para yml_usage_stats
CREATE TRIGGER update_yml_usage_stats_updated_at 
    BEFORE UPDATE ON yml_usage_stats 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentar la estructura
COMMENT ON TABLE user_yml_plans IS 'Almacena metadata de planes YML personalizados generados para cada usuario';
COMMENT ON COLUMN user_yml_plans.storage_path IS 'Ruta completa al archivo YML en el sistema de almacenamiento';
COMMENT ON COLUMN user_yml_plans.file_hash IS 'Hash MD5 del contenido para validación de integridad';
COMMENT ON COLUMN user_yml_plans.cache_key IS 'Clave utilizada en Redis para cache del contenido YML';
COMMENT ON COLUMN user_yml_plans.is_outdated IS 'Indica si el YML necesita regeneración por cambios en el usuario';

COMMENT ON TABLE yml_usage_stats IS 'Estadísticas de uso de planes YML para análisis y mejora';
COMMENT ON COLUMN yml_usage_stats.time_spent_minutes IS 'Tiempo total dedicado al plan en minutos';
COMMENT ON COLUMN yml_usage_stats.modules_completed IS 'Número de módulos completados exitosamente';
