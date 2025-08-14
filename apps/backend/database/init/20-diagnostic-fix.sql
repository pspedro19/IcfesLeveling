-- Crear tablas si faltan
CREATE TABLE IF NOT EXISTS diagnostic_tests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  subject_id UUID NOT NULL,
  test_type VARCHAR(50) DEFAULT 'real_icfes',
  questions_answered INT DEFAULT 0,
  correct_answers INT DEFAULT 0,
  time_spent_seconds INT DEFAULT 0,
  score_percentage FLOAT DEFAULT 0.0,
  strengths JSONB DEFAULT '[]',
  weaknesses JSONB DEFAULT '[]',
  score_by_topic JSONB DEFAULT '{}',
  status VARCHAR(20) DEFAULT 'in_progress',
  started_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS diagnostic_test_answers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  test_id UUID NOT NULL REFERENCES diagnostic_tests(id) ON DELETE CASCADE,
  question_id UUID NOT NULL,
  user_answer VARCHAR(10) NOT NULL,
  is_correct BOOLEAN NOT NULL,
  response_time_ms INT DEFAULT 0,
  topic_id UUID,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Asegurar columna test_id y FK
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='diagnostic_test_answers' AND column_name='test_id'
  ) THEN
    ALTER TABLE diagnostic_test_answers ADD COLUMN test_id UUID;
    ALTER TABLE diagnostic_test_answers
      ADD CONSTRAINT fk_dta_test FOREIGN KEY (test_id)
      REFERENCES diagnostic_tests(id) ON DELETE CASCADE;
  END IF;
END $$;

-- Índices
CREATE INDEX IF NOT EXISTS idx_dta_test_id ON diagnostic_test_answers(test_id);
CREATE INDEX IF NOT EXISTS idx_dta_question_id ON diagnostic_test_answers(question_id);
