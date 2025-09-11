-- Migration: Add diagnostic tracking metrics to diagnostic_test_results table
-- Date: 2025-01-14
-- Description: Add columns to track response time baseline, difficulty level, performance level, and XP earned

BEGIN;

-- Add new tracking columns to diagnostic_test_results table
ALTER TABLE diagnostic_test_results 
ADD COLUMN IF NOT EXISTS tiempo_estimado_baseline INTEGER,
ADD COLUMN IF NOT EXISTS nivel_dificultad INTEGER,
ADD COLUMN IF NOT EXISTS nivel_desempeno_esperado VARCHAR(20),
ADD COLUMN IF NOT EXISTS puntos_xp_earned INTEGER DEFAULT 0;

-- Add comments for documentation
COMMENT ON COLUMN diagnostic_test_results.tiempo_estimado_baseline IS 'Baseline response time from question data (seconds) - Tiempo_Estimado field';
COMMENT ON COLUMN diagnostic_test_results.nivel_dificultad IS 'Difficulty level attempted (1-10 scale) - Nivel_Dificultad field';
COMMENT ON COLUMN diagnostic_test_results.nivel_desempeno_esperado IS 'Performance level achieved (e.g., "Mínimo", "Satisfactorio", "Avanzado") - Nivel_Desempeño_Esperado field';
COMMENT ON COLUMN diagnostic_test_results.puntos_xp_earned IS 'XP points earned for this question - Puntos_XP field';

-- Create indexes for performance (optional but recommended for analytics)
CREATE INDEX IF NOT EXISTS idx_diagnostic_results_nivel_dificultad ON diagnostic_test_results(nivel_dificultad);
CREATE INDEX IF NOT EXISTS idx_diagnostic_results_nivel_desempeno ON diagnostic_test_results(nivel_desempeno_esperado);
CREATE INDEX IF NOT EXISTS idx_diagnostic_results_xp_earned ON diagnostic_test_results(puntos_xp_earned);

COMMIT;