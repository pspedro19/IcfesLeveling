-- Migration: Add new fields to questions table for Excel import functionality
-- Date: 2024-01-15

-- Add new columns to questions table
ALTER TABLE questions 
ADD COLUMN IF NOT EXISTS image_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS options_images JSONB,
ADD COLUMN IF NOT EXISTS is_validated VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS validation_errors JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS usage_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS average_response_time INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Add trigger for updated_at column
CREATE OR REPLACE FUNCTION update_questions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for questions table
DROP TRIGGER IF EXISTS update_questions_updated_at ON questions;
CREATE TRIGGER update_questions_updated_at 
    BEFORE UPDATE ON questions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_questions_updated_at();

-- Add indexes for new fields
CREATE INDEX IF NOT EXISTS idx_questions_validated ON questions(is_validated);
CREATE INDEX IF NOT EXISTS idx_questions_usage_count ON questions(usage_count);
CREATE INDEX IF NOT EXISTS idx_questions_last_used ON questions(last_used_at);

-- Add constraints
ALTER TABLE questions 
ADD CONSTRAINT check_is_validated 
CHECK (is_validated IN ('pending', 'validated', 'rejected'));

-- Update existing questions to have validated status
UPDATE questions 
SET is_validated = 'validated' 
WHERE is_validated IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN questions.image_url IS 'URL of the main question image';
COMMENT ON COLUMN questions.options_images IS 'JSON object with image URLs for each option (A, B, C, D)';
COMMENT ON COLUMN questions.is_validated IS 'Validation status: pending, validated, rejected';
COMMENT ON COLUMN questions.validation_errors IS 'Array of validation error messages';
COMMENT ON COLUMN questions.usage_count IS 'Number of times this question has been used';
COMMENT ON COLUMN questions.average_response_time IS 'Average response time in milliseconds';
COMMENT ON COLUMN questions.last_used_at IS 'Timestamp of last usage';
COMMENT ON COLUMN questions.updated_at IS 'Timestamp of last update'; 