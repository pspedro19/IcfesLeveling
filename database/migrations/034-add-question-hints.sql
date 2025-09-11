-- Migration: Add progressive hints system to questions table
-- File: 034-add-question-hints.sql
-- Description: Add pista_1, pista_2, pista_3, explicacion_respuesta, and error_comun columns to questions table

-- Add hint columns to questions table
ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_1 TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_2 TEXT; 
ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_3 TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS explicacion_respuesta TEXT;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS error_comun TEXT;

-- Add hint usage tracking columns to diagnostic_test_answers table
ALTER TABLE diagnostic_test_answers ADD COLUMN IF NOT EXISTS hints_used INTEGER DEFAULT 0;
ALTER TABLE diagnostic_test_answers ADD COLUMN IF NOT EXISTS hint_levels_requested JSON DEFAULT '[]';

-- Add hint usage tracking columns to diagnostic_test_results table  
ALTER TABLE diagnostic_test_results ADD COLUMN IF NOT EXISTS hints_used INTEGER DEFAULT 0;
ALTER TABLE diagnostic_test_results ADD COLUMN IF NOT EXISTS hint_levels_requested JSON DEFAULT '[]';

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_questions_hints ON questions(id) WHERE pista_1 IS NOT NULL OR pista_2 IS NOT NULL OR pista_3 IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_diagnostic_answers_hints ON diagnostic_test_answers(hints_used) WHERE hints_used > 0;
CREATE INDEX IF NOT EXISTS idx_diagnostic_results_hints ON diagnostic_test_results(hints_used) WHERE hints_used > 0;

-- Add comments for documentation
COMMENT ON COLUMN questions.pista_1 IS 'Primera pista progresiva - conceptual';
COMMENT ON COLUMN questions.pista_2 IS 'Segunda pista progresiva - procedimental';
COMMENT ON COLUMN questions.pista_3 IS 'Tercera pista progresiva - específica';
COMMENT ON COLUMN questions.explicacion_respuesta IS 'Explicación detallada de la respuesta correcta';
COMMENT ON COLUMN questions.error_comun IS 'Error común que cometen los estudiantes';

COMMENT ON COLUMN diagnostic_test_answers.hints_used IS 'Número total de pistas solicitadas para esta pregunta';
COMMENT ON COLUMN diagnostic_test_answers.hint_levels_requested IS 'Array JSON con los niveles de pista solicitados [1,2,3]';

COMMENT ON COLUMN diagnostic_test_results.hints_used IS 'Número total de pistas solicitadas para esta pregunta';
COMMENT ON COLUMN diagnostic_test_results.hint_levels_requested IS 'Array JSON con los niveles de pista solicitados [1,2,3]';