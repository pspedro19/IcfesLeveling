-- Migration: Add puntos_xp column to questions table
-- This column stores XP points awarded from the Puntos_XP field in the CSV data

-- Add puntos_xp column to questions table
ALTER TABLE questions 
ADD COLUMN IF NOT EXISTS puntos_xp INTEGER DEFAULT 10 NOT NULL;

-- Add comment explaining the column
COMMENT ON COLUMN questions.puntos_xp IS 'XP points awarded for this question from Puntos_XP CSV field';

-- Create index for performance on XP-based queries
CREATE INDEX IF NOT EXISTS idx_questions_puntos_xp ON questions(puntos_xp);

-- Update existing questions to have default XP values based on difficulty
-- Higher difficulty = more XP
UPDATE questions 
SET puntos_xp = CASE 
    WHEN difficulty >= 8 THEN 25
    WHEN difficulty >= 6 THEN 20
    WHEN difficulty >= 4 THEN 15
    WHEN difficulty >= 2 THEN 10
    ELSE 5
END
WHERE puntos_xp = 10; -- Only update default values

-- Log the migration
INSERT INTO migration_log (migration_name, executed_at) 
VALUES ('035-add-question-puntos-xp', NOW())
ON CONFLICT (migration_name) DO NOTHING;