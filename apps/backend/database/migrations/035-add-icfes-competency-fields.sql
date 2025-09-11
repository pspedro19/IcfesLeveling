-- ================================================
-- ADD ICFES COMPETENCY AND COMPONENT FIELDS
-- Migration: 035-add-icfes-competency-fields.sql
-- ================================================

BEGIN;

-- Add ICFES competency and component fields to questions table
ALTER TABLE questions 
ADD COLUMN IF NOT EXISTS competencia VARCHAR(150),
ADD COLUMN IF NOT EXISTS componente VARCHAR(100),
ADD COLUMN IF NOT EXISTS proceso_cognitivo VARCHAR(50),
ADD COLUMN IF NOT EXISTS tipo_conocimiento VARCHAR(50),
ADD COLUMN IF NOT EXISTS afirmacion TEXT,
ADD COLUMN IF NOT EXISTS evidencia TEXT,
ADD COLUMN IF NOT EXISTS nivel_desempeno_esperado VARCHAR(30),
ADD COLUMN IF NOT EXISTS tiempo_estimado INTEGER,
ADD COLUMN IF NOT EXISTS pista_1 TEXT,
ADD COLUMN IF NOT EXISTS pista_2 TEXT,
ADD COLUMN IF NOT EXISTS pista_3 TEXT,
ADD COLUMN IF NOT EXISTS explicacion_respuesta TEXT,
ADD COLUMN IF NOT EXISTS error_comun TEXT;

-- Create indices for efficient searching by ICFES competency fields
CREATE INDEX IF NOT EXISTS idx_questions_competencia ON questions(competencia);
CREATE INDEX IF NOT EXISTS idx_questions_componente ON questions(componente);
CREATE INDEX IF NOT EXISTS idx_questions_proceso_cognitivo ON questions(proceso_cognitivo);
CREATE INDEX IF NOT EXISTS idx_questions_tipo_conocimiento ON questions(tipo_conocimiento);

-- Create composite index for ICFES-based filtering
CREATE INDEX IF NOT EXISTS idx_questions_icfes_composite ON questions(competencia, componente, proceso_cognitivo);

COMMIT;

-- Verify the migration
SELECT COUNT(*) as total_questions, 
       COUNT(competencia) as with_competencia,
       COUNT(componente) as with_componente,
       COUNT(afirmacion) as with_afirmacion,
       COUNT(evidencia) as with_evidencia
FROM questions;