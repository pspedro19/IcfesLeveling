-- Migration 004: Dynamic Subject Configuration Tables
-- Adds support for dynamic subject configurations, aliases, and asset management

-- Subject Configurations Table
CREATE TABLE IF NOT EXISTS subject_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    
    -- Test Configuration
    total_questions INTEGER DEFAULT 45,
    time_limit_minutes INTEGER DEFAULT 60,
    passing_score INTEGER DEFAULT 75,
    
    -- Display Configuration
    icon_url VARCHAR(500),
    color_primary VARCHAR(20),
    color_secondary VARCHAR(20),
    description_short TEXT,
    description_long TEXT,
    
    -- Learning Configuration
    topics JSONB,
    difficulty_levels JSONB,
    study_sequence JSONB,
    
    -- Administrative
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Subject Aliases Table
CREATE TABLE IF NOT EXISTS subject_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    alias_name VARCHAR(100) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    language VARCHAR(10) DEFAULT 'es'
);

-- Asset Configurations Table
CREATE TABLE IF NOT EXISTS asset_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- 'subject', 'hero_class', 'achievement'
    entity_id UUID NOT NULL,
    asset_type VARCHAR(50) NOT NULL, -- 'icon', 'banner', 'audio'
    asset_url VARCHAR(500) NOT NULL,
    asset_description TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_subject_configs_subject_id ON subject_configs(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_aliases_subject_id ON subject_aliases(subject_id);
CREATE INDEX IF NOT EXISTS idx_subject_aliases_alias_name ON subject_aliases(alias_name);
CREATE INDEX IF NOT EXISTS idx_asset_configurations_entity ON asset_configurations(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_asset_configurations_type ON asset_configurations(asset_type);

-- Insert default configuration for existing subjects
INSERT INTO subject_configs (subject_id, total_questions, time_limit_minutes, passing_score, topics, difficulty_levels, study_sequence)
SELECT 
    id as subject_id,
    45 as total_questions,
    60 as time_limit_minutes,
    75 as passing_score,
    '[]'::JSONB as topics,
    '{"fácil": 1, "medio": 2, "difícil": 3}'::JSONB as difficulty_levels,
    '[]'::JSONB as study_sequence
FROM subjects 
WHERE id NOT IN (SELECT subject_id FROM subject_configs);

-- Insert common aliases for existing subjects
INSERT INTO subject_aliases (subject_id, alias_name, language)
SELECT s.id, alias.alias_name, 'es'
FROM subjects s
CROSS JOIN (
    VALUES 
        ('matemáticas', 'matematica'),
        ('matemáticas', 'matematicas'),
        ('matemáticas', 'mates'),
        ('lectura crítica', 'lectura critica'),
        ('lectura crítica', 'lenguaje'),
        ('lectura crítica', 'español'),
        ('ciencias naturales', 'ciencias'),
        ('ciencias naturales', 'naturales'),
        ('sociales y ciudadanas', 'sociales'),
        ('sociales y ciudadanas', 'ciudadanas'),
        ('inglés', 'ingles'),
        ('inglés', 'english'),
        ('filosofía', 'filosofia')
) AS alias(subject_name, alias_name)
WHERE LOWER(s.name) LIKE '%' || alias.subject_name || '%'
ON CONFLICT DO NOTHING;

COMMENT ON TABLE subject_configs IS 'Dynamic configuration for subjects including test settings and display options';
COMMENT ON TABLE subject_aliases IS 'Alternative names for subjects to enable intelligent mapping';
COMMENT ON TABLE asset_configurations IS 'Dynamic asset management for subjects, heroes, and achievements';
