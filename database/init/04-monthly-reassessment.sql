-- Migration para US-010: Reevaluación Adaptativa Mensual
-- Agregar campos necesarios para la funcionalidad de reevaluación mensual

-- Agregar campos a la tabla diagnostic_tests
ALTER TABLE diagnostic_tests 
ADD COLUMN IF NOT EXISTS reassessment_type VARCHAR(50),
ADD COLUMN IF NOT EXISTS original_test_id UUID REFERENCES diagnostic_tests(id),
ADD COLUMN IF NOT EXISTS is_monthly_reassessment BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS days_since_initial INTEGER,
ADD COLUMN IF NOT EXISTS comparison_with_initial JSONB,
ADD COLUMN IF NOT EXISTS plan_regenerated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS new_goals_generated BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS notification_sent BOOLEAN DEFAULT FALSE;

-- Crear índices para optimizar consultas de reevaluación
CREATE INDEX IF NOT EXISTS idx_diagnostic_tests_monthly_reassessment 
ON diagnostic_tests(user_id, subject_id, is_monthly_reassessment, created_at);

CREATE INDEX IF NOT EXISTS idx_diagnostic_tests_reassessment_type 
ON diagnostic_tests(user_id, reassessment_type, created_at);

CREATE INDEX IF NOT EXISTS idx_diagnostic_tests_original_test 
ON diagnostic_tests(original_test_id);

-- Actualizar tests existentes para marcar como iniciales
UPDATE diagnostic_tests 
SET reassessment_type = 'initial' 
WHERE reassessment_type IS NULL AND status = 'completed';

-- Insertar datos de ejemplo para testing
INSERT INTO diagnostic_tests (
    id, user_id, subject_id, test_type, reassessment_type, 
    questions_answered, correct_answers, time_spent_seconds, 
    score_percentage, strengths, weaknesses, score_by_topic, 
    status, started_at, completed_at, created_at,
    is_monthly_reassessment, days_since_initial
) VALUES 
-- Test inicial de ejemplo (30 días atrás)
(
    gen_random_uuid(), 
    'aa0e8400-e29b-41d4-a716-446655440001', 
    'bb0e8400-e29b-41d4-a716-446655440001', 
    'real_icfes', 
    'initial',
    30, 18, 1800, 
    60.0, 
    '["álgebra", "geometría"]', 
    '["trigonometría", "estadística"]', 
    '{"álgebra": 70.0, "geometría": 65.0, "trigonometría": 40.0, "estadística": 45.0}',
    'completed', 
    NOW() - INTERVAL '30 days', 
    NOW() - INTERVAL '30 days' + INTERVAL '30 minutes',
    NOW() - INTERVAL '30 days',
    FALSE, 
    30
),
-- Test inicial de ejemplo (35 días atrás)
(
    gen_random_uuid(), 
    'aa0e8400-e29b-41d4-a716-446655440002', 
    'bb0e8400-e29b-41d4-a716-446655440002', 
    'real_icfes', 
    'initial',
    30, 21, 1650, 
    70.0, 
    '["comprensión lectora", "gramática"]', 
    '["literatura"]', 
    '{"comprensión lectora": 75.0, "gramática": 80.0, "literatura": 55.0}',
    'completed', 
    NOW() - INTERVAL '35 days', 
    NOW() - INTERVAL '35 days' + INTERVAL '25 minutes',
    NOW() - INTERVAL '35 days',
    FALSE, 
    35
);

-- Crear tabla para notificaciones de reevaluación (opcional)
CREATE TABLE IF NOT EXISTS reassessment_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    reassessment_id UUID NOT NULL REFERENCES diagnostic_tests(id),
    notification_type VARCHAR(50) NOT NULL, -- 'eligibility', 'completion', 'plan_update'
    message TEXT NOT NULL,
    comparison_data JSONB,
    new_goals JSONB,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para notificaciones
CREATE INDEX IF NOT EXISTS idx_reassessment_notifications_user 
ON reassessment_notifications(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_reassessment_notifications_type 
ON reassessment_notifications(notification_type, created_at);

-- Insertar notificaciones de ejemplo
INSERT INTO reassessment_notifications (
    user_id, reassessment_id, notification_type, message, comparison_data, new_goals
) VALUES 
(
    'aa0e8400-e29b-41d4-a716-446655440001',
    (SELECT id FROM diagnostic_tests WHERE user_id = 'aa0e8400-e29b-41d4-a716-446655440001' LIMIT 1),
    'eligibility',
    '¡Ya puedes realizar tu reevaluación mensual de Matemáticas! Han pasado 30 días desde tu test inicial.',
    '{"days_since_initial": 30, "initial_score": 60.0}',
    '["Mejorar trigonometría", "Reforzar estadística"]'
);

-- Comentarios sobre la implementación
COMMENT ON TABLE diagnostic_tests IS 'Tabla extendida para soportar reevaluaciones mensuales (US-010)';
COMMENT ON COLUMN diagnostic_tests.reassessment_type IS 'Tipo de reevaluación: initial, monthly, adaptive';
COMMENT ON COLUMN diagnostic_tests.original_test_id IS 'Referencia al test inicial para comparación';
COMMENT ON COLUMN diagnostic_tests.is_monthly_reassessment IS 'Indica si es una reevaluación mensual';
COMMENT ON COLUMN diagnostic_tests.days_since_initial IS 'Días transcurridos desde el test inicial';
COMMENT ON COLUMN diagnostic_tests.comparison_with_initial IS 'Datos de comparación con el test inicial';
COMMENT ON COLUMN diagnostic_tests.plan_regenerated IS 'Indica si el plan de estudio fue regenerado';
COMMENT ON COLUMN diagnostic_tests.new_goals_generated IS 'Indica si se generaron nuevos objetivos';
COMMENT ON COLUMN diagnostic_tests.notification_sent IS 'Indica si se envió notificación al usuario'; 