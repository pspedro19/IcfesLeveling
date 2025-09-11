-- Migration: Add puntos_xp column to questions table
-- Date: 2025-01-14
-- Description: Add XP points column to questions table for gamification tracking

BEGIN;

-- Add puntos_xp column to questions table
ALTER TABLE questions 
ADD COLUMN IF NOT EXISTS puntos_xp INTEGER DEFAULT 10;

-- Add comment for documentation
COMMENT ON COLUMN questions.puntos_xp IS 'XP points earned for correctly answering this question';

-- Create index for performance (optional but recommended for analytics)
CREATE INDEX IF NOT EXISTS idx_questions_puntos_xp ON questions(puntos_xp);

COMMIT;