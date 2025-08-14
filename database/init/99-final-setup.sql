-- =====================================================
-- SCRIPT MAESTRO DE INICIALIZACIÓN ICFES LEVELING
-- =====================================================
-- Este script se ejecuta AL FINAL de todos los demás
-- para asegurar que el sistema esté completamente configurado
-- =====================================================

-- Marcar que la inicialización está completa
DO $$
BEGIN
    -- Crear tabla de control de inicialización si no existe
    CREATE TABLE IF NOT EXISTS system_initialization (
        id SERIAL PRIMARY KEY,
        step_name VARCHAR(100) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        details TEXT
    );
    
    -- Insertar registro de inicialización completada
    INSERT INTO system_initialization (step_name, status, details) 
    VALUES ('complete_system_setup', 'completed', 'Sistema ICFES Leveling completamente inicializado')
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE '✅ Sistema ICFES Leveling inicializado completamente';
END $$;

-- Verificar que todas las tablas críticas existan
DO $$
DECLARE
    required_tables TEXT[] := ARRAY[
        'users', 'subjects', 'topics', 'questions', 'diagnostic_tests',
        'diagnostic_test_answers', 'study_plans', 'plan_progress',
        'video_tracking', 'quizzes', 'achievements', 'guilds',
        'monthly_reassessment', 'analytics_events', 'user_progress'
    ];
    missing_tables TEXT[] := '{}';
    table_name TEXT;
BEGIN
    FOREACH table_name IN ARRAY required_tables
    LOOP
        IF NOT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = table_name
        ) THEN
            missing_tables := array_append(missing_tables, table_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_tables, 1) > 0 THEN
        RAISE EXCEPTION '❌ Tablas faltantes: %', array_to_string(missing_tables, ', ');
    ELSE
        RAISE NOTICE '✅ Todas las tablas críticas están presentes';
    END IF;
END $$;

-- Verificar que las columnas críticas de diagnostic_tests existan
DO $$
DECLARE
    required_columns TEXT[] := ARRAY[
        'reassessment_type', 'original_test_id', 'is_monthly_reassessment',
        'days_since_initial', 'comparison_with_initial', 'plan_regenerated',
        'new_goals_generated', 'notification_sent', 'questions_answered',
        'time_spent_seconds', 'score_percentage', 'score_by_topic',
        'status', 'started_at', 'completed_at'
    ];
    missing_columns TEXT[] := '{}';
    column_name TEXT;
BEGIN
    FOREACH column_name IN ARRAY required_columns
    LOOP
        IF NOT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'diagnostic_tests'
            AND column_name = column_name
        ) THEN
            missing_columns := array_append(missing_columns, column_name);
        END IF;
    END LOOP;
    
    IF array_length(missing_columns, 1) > 0 THEN
        RAISE EXCEPTION '❌ Columnas faltantes en diagnostic_tests: %', array_to_string(missing_columns, ', ');
    ELSE
        RAISE NOTICE '✅ Todas las columnas críticas de diagnostic_tests están presentes';
    END IF;
END $$;

-- Verificar que haya datos básicos
DO $$
DECLARE
    user_count INTEGER;
    subject_count INTEGER;
    question_count INTEGER;
BEGIN
    -- Verificar usuarios
    SELECT COUNT(*) INTO user_count FROM users;
    IF user_count = 0 THEN
        RAISE EXCEPTION '❌ No hay usuarios en el sistema';
    ELSE
        RAISE NOTICE '✅ Usuarios encontrados: %', user_count;
    END IF;
    
    -- Verificar materias
    SELECT COUNT(*) INTO subject_count FROM subjects;
    IF subject_count = 0 THEN
        RAISE EXCEPTION '❌ No hay materias en el sistema';
    ELSE
        RAISE NOTICE '✅ Materias encontradas: %', subject_count;
    END IF;
    
    -- Verificar preguntas
    SELECT COUNT(*) INTO question_count FROM questions;
    IF question_count = 0 THEN
        RAISE WARNING '⚠️ No hay preguntas en el sistema (se cargarán automáticamente)';
    ELSE
        RAISE NOTICE '✅ Preguntas encontradas: %', question_count;
    END IF;
END $$;

-- Crear índices de rendimiento si no existen
CREATE INDEX IF NOT EXISTS idx_diagnostic_tests_user_status 
ON diagnostic_tests(user_id, status, created_at);

CREATE INDEX IF NOT EXISTS idx_questions_subject_topic 
ON questions(subject_id, topic_id);

CREATE INDEX IF NOT EXISTS idx_user_progress_user_subject 
ON user_progress(user_id, subject_id);

-- Marcar la inicialización como exitosa
UPDATE system_initialization 
SET status = 'completed', 
    executed_at = CURRENT_TIMESTAMP,
    details = 'Sistema completamente configurado y listo para usar'
WHERE step_name = 'complete_system_setup';

-- Mensaje final
DO $$
BEGIN
    RAISE NOTICE '🎉 =====================================================';
    RAISE NOTICE '🎉 SISTEMA ICFES LEVELING COMPLETAMENTE INICIALIZADO';
    RAISE NOTICE '🎉 =====================================================';
    RAISE NOTICE '✅ Base de datos creada y configurada';
    RAISE NOTICE '✅ Tablas creadas y migradas';
    RAISE NOTICE '✅ Datos básicos cargados';
    RAISE NOTICE '✅ Índices de rendimiento creados';
    RAISE NOTICE '🎉 ¡El sistema está listo para usar!';
    RAISE NOTICE '🎉 =====================================================';
END $$;
