-- ================================================================================================
-- ICFES LEVELING - DATA MIGRATION TO ADVANCED LEARNING SYSTEM
-- ================================================================================================
-- CRÍTICO: Migra datos existentes a las nuevas tablas avanzadas
-- Implementación según el Plan de 4 Semanas - Semana 2: Población y Calibración
-- ================================================================================================

-- ================================================================================================
-- 1. MIGRACIÓN DE DIAGNOSTIC_TESTS A QUESTION_RESPONSES
-- ================================================================================================

DO $$
DECLARE
    migration_count INTEGER := 0;
BEGIN
    RAISE NOTICE '🔄 Starting migration of diagnostic test data to question_responses...';
    
    -- Migrar respuestas de diagnostic_test_answers a question_responses
    INSERT INTO question_responses (
        user_id,
        question_id,
        response_context,
        session_id,
        diagnostic_test_id,
        user_answer,
        correct_answer,
        is_correct,
        response_time_ms,
        question_sequence_number,
        created_at
    )
    SELECT 
        dt.user_id,
        dta.question_id,
        'diagnostic'::VARCHAR,
        dt.id, -- Usar diagnostic_test_id como session_id
        dt.id,
        dta.user_answer,
        q.correct_answer,
        dta.is_correct,
        COALESCE(dta.response_time_ms, 30000), -- Default 30 segundos si no existe
        ROW_NUMBER() OVER (PARTITION BY dt.id ORDER BY dta.created_at), -- Secuencia
        dta.created_at
    FROM diagnostic_test_answers dta
    JOIN diagnostic_tests dt ON dt.id = dta.diagnostic_test_id
    JOIN questions q ON q.id = dta.question_id
    WHERE NOT EXISTS (
        -- Evitar duplicados
        SELECT 1 FROM question_responses qr 
        WHERE qr.user_id = dt.user_id 
        AND qr.question_id = dta.question_id 
        AND qr.diagnostic_test_id = dt.id
    );
    
    GET DIAGNOSTICS migration_count = ROW_COUNT;
    RAISE NOTICE '✅ Migrated % diagnostic responses to question_responses', migration_count;
END $$;

-- ================================================================================================
-- 2. MIGRACIÓN DE BATTLE_ANSWERS A QUESTION_RESPONSES
-- ================================================================================================

DO $$
DECLARE
    migration_count INTEGER := 0;
BEGIN
    RAISE NOTICE '🔄 Starting migration of battle data to question_responses...';
    
    -- Migrar respuestas de battle_answers a question_responses
    INSERT INTO question_responses (
        user_id,
        question_id,
        response_context,
        session_id,
        battle_id,
        user_answer,
        correct_answer,
        is_correct,
        response_time_ms,
        question_sequence_number,
        created_at
    )
    SELECT 
        b.user_id,
        ba.question_id,
        'battle'::VARCHAR,
        b.id, -- Usar battle_id como session_id
        b.id,
        ba.user_answer,
        q.correct_answer,
        ba.is_correct,
        COALESCE(ba.response_time_ms, 20000), -- Default 20 segundos para battles
        ROW_NUMBER() OVER (PARTITION BY b.id ORDER BY ba.created_at),
        ba.created_at
    FROM battle_answers ba
    JOIN battles b ON b.id = ba.battle_id
    JOIN questions q ON q.id = ba.question_id
    WHERE NOT EXISTS (
        SELECT 1 FROM question_responses qr 
        WHERE qr.user_id = b.user_id 
        AND qr.question_id = ba.question_id 
        AND qr.battle_id = b.id
    );
    
    GET DIAGNOSTICS migration_count = ROW_COUNT;
    RAISE NOTICE '✅ Migrated % battle responses to question_responses', migration_count;
END $$;

-- ================================================================================================
-- 3. MIGRACIÓN DE QUIZ_ANSWERS A QUESTION_RESPONSES
-- ================================================================================================

DO $$
DECLARE
    migration_count INTEGER := 0;
BEGIN
    RAISE NOTICE '🔄 Starting migration of quiz data to question_responses...';
    
    -- Migrar respuestas de quiz_answers a question_responses
    INSERT INTO question_responses (
        user_id,
        question_id,
        response_context,
        session_id,
        quiz_id,
        user_answer,
        correct_answer,
        is_correct,
        response_time_ms,
        question_sequence_number,
        created_at
    )
    SELECT 
        qz.user_id,
        qa.question_id,
        'quiz'::VARCHAR,
        qz.id, -- Usar quiz_id como session_id
        qz.id,
        qa.user_answer,
        q.correct_answer,
        qa.is_correct,
        COALESCE(qa.response_time_ms, 25000), -- Default 25 segundos para quizzes
        ROW_NUMBER() OVER (PARTITION BY qz.id ORDER BY qa.created_at),
        qa.created_at
    FROM quiz_answers qa
    JOIN quizzes qz ON qz.id = qa.quiz_id
    JOIN questions q ON q.id = qa.question_id
    WHERE NOT EXISTS (
        SELECT 1 FROM question_responses qr 
        WHERE qr.user_id = qz.user_id 
        AND qr.question_id = qa.question_id 
        AND qr.quiz_id = qz.id
    );
    
    GET DIAGNOSTICS migration_count = ROW_COUNT;
    RAISE NOTICE '✅ Migrated % quiz responses to question_responses', migration_count;
END $$;

-- ================================================================================================
-- 4. GENERACIÓN INICIAL DE USER_SKILLS
-- ================================================================================================

DO $$
DECLARE
    skills_created INTEGER := 0;
BEGIN
    RAISE NOTICE '🔄 Generating initial user_skills from question_responses...';
    
    -- Generar user_skills basado en question_responses existentes
    INSERT INTO user_skills (
        user_id,
        subject_id,
        topic_id,
        skill_level,
        confidence_score,
        mastery_status,
        total_attempts,
        correct_attempts,
        average_response_time_ms,
        last_interaction_date,
        created_at,
        updated_at
    )
    SELECT 
        qr.user_id,
        q.subject_id,
        q.topic_id,
        -- Calcular skill_level basado en accuracy
        LEAST(100.0, (SUM(CASE WHEN qr.is_correct THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)::DECIMAL) * 100),
        -- Calcular confidence usando Wilson Score simplificado
        CASE 
            WHEN COUNT(*) >= 5 THEN
                LEAST(1.0, (SUM(CASE WHEN qr.is_correct THEN 1 ELSE 0 END) + 2.0) / (COUNT(*) + 4.0))
            ELSE 0.4 -- Baja confianza con pocas respuestas
        END,
        -- Determinar mastery_status
        CASE 
            WHEN (SUM(CASE WHEN qr.is_correct THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)::DECIMAL) >= 0.9 THEN 'expert'
            WHEN (SUM(CASE WHEN qr.is_correct THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)::DECIMAL) >= 0.8 THEN 'mastered'
            WHEN (SUM(CASE WHEN qr.is_correct THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)::DECIMAL) >= 0.6 THEN 'practiced'
            WHEN (SUM(CASE WHEN qr.is_correct THEN 1 ELSE 0 END)::DECIMAL / COUNT(*)::DECIMAL) >= 0.3 THEN 'learning'
            ELSE 'not_started'
        END,
        COUNT(*), -- total_attempts
        SUM(CASE WHEN qr.is_correct THEN 1 ELSE 0 END), -- correct_attempts
        AVG(qr.response_time_ms)::INTEGER, -- average_response_time_ms
        MAX(qr.created_at), -- last_interaction_date
        MIN(qr.created_at), -- created_at
        CURRENT_TIMESTAMP -- updated_at
    FROM question_responses qr
    JOIN questions q ON q.id = qr.question_id
    GROUP BY qr.user_id, q.subject_id, q.topic_id
    ON CONFLICT (user_id, topic_id) DO UPDATE SET
        total_attempts = EXCLUDED.total_attempts,
        correct_attempts = EXCLUDED.correct_attempts,
        skill_level = EXCLUDED.skill_level,
        confidence_score = EXCLUDED.confidence_score,
        mastery_status = EXCLUDED.mastery_status,
        average_response_time_ms = EXCLUDED.average_response_time_ms,
        last_interaction_date = EXCLUDED.last_interaction_date,
        updated_at = CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS skills_created = ROW_COUNT;
    RAISE NOTICE '✅ Created/updated % user_skills records', skills_created;
END $$;

-- ================================================================================================
-- 5. GENERACIÓN DE LEARNING_SESSIONS
-- ================================================================================================

DO $$
DECLARE
    sessions_created INTEGER := 0;
BEGIN
    RAISE NOTICE '🔄 Generating learning_sessions from existing data...';
    
    -- Crear learning_sessions para diagnostic tests
    INSERT INTO learning_sessions (
        user_id,
        session_type,
        subject_id,
        start_time,
        end_time,
        duration_seconds,
        questions_attempted,
        questions_correct,
        average_response_time_ms,
        accuracy_rate,
        completion_status,
        created_at
    )
    SELECT 
        dt.user_id,
        'diagnostic'::VARCHAR,
        dt.subject_id,
        dt.created_at,
        dt.created_at + INTERVAL '1 second' * dt.time_taken_seconds,
        dt.time_taken_seconds,
        dt.total_questions,
        dt.correct_answers,
        COALESCE(avg_response.avg_time, 30000)::INTEGER,
        CASE WHEN dt.total_questions > 0 THEN (dt.correct_answers::DECIMAL / dt.total_questions::DECIMAL) * 100 ELSE 0 END,
        'completed'::VARCHAR,
        dt.created_at
    FROM diagnostic_tests dt
    LEFT JOIN (
        SELECT 
            qr.diagnostic_test_id,
            AVG(qr.response_time_ms) as avg_time
        FROM question_responses qr
        WHERE qr.diagnostic_test_id IS NOT NULL
        GROUP BY qr.diagnostic_test_id
    ) avg_response ON avg_response.diagnostic_test_id = dt.id
    WHERE NOT EXISTS (
        SELECT 1 FROM learning_sessions ls 
        WHERE ls.user_id = dt.user_id 
        AND ls.session_type = 'diagnostic'
        AND ls.start_time = dt.created_at
    );
    
    GET DIAGNOSTICS sessions_created = ROW_COUNT;
    RAISE NOTICE '✅ Created % diagnostic learning_sessions', sessions_created;
    
    -- Crear learning_sessions para battles
    INSERT INTO learning_sessions (
        user_id,
        session_type,
        start_time,
        end_time,
        duration_seconds,
        questions_attempted,
        questions_correct,
        average_response_time_ms,
        accuracy_rate,
        completion_status,
        created_at
    )
    SELECT 
        b.user_id,
        'battle'::VARCHAR,
        b.created_at,
        COALESCE(b.completed_at, b.created_at + INTERVAL '1 second' * COALESCE(b.duration_seconds, 600)),
        COALESCE(b.duration_seconds, 600),
        b.questions_answered,
        b.correct_answers,
        COALESCE(avg_response.avg_time, 20000)::INTEGER,
        CASE WHEN b.questions_answered > 0 THEN (b.correct_answers::DECIMAL / b.questions_answered::DECIMAL) * 100 ELSE 0 END,
        CASE b.status
            WHEN 'completed' THEN 'completed'
            WHEN 'failed' THEN 'abandoned'
            ELSE 'interrupted'
        END,
        b.created_at
    FROM battles b
    LEFT JOIN (
        SELECT 
            qr.battle_id,
            AVG(qr.response_time_ms) as avg_time
        FROM question_responses qr
        WHERE qr.battle_id IS NOT NULL
        GROUP BY qr.battle_id
    ) avg_response ON avg_response.battle_id = b.id
    WHERE NOT EXISTS (
        SELECT 1 FROM learning_sessions ls 
        WHERE ls.user_id = b.user_id 
        AND ls.session_type = 'battle'
        AND ls.start_time = b.created_at
    );
    
    GET DIAGNOSTICS sessions_created = ROW_COUNT;
    RAISE NOTICE '✅ Created % battle learning_sessions', sessions_created;
END $$;

-- ================================================================================================
-- 6. CALCULAR PARÁMETROS IRT INICIALES PARA QUESTIONS
-- ================================================================================================

DO $$
DECLARE
    questions_updated INTEGER := 0;
BEGIN
    RAISE NOTICE '🔄 Calculating initial IRT parameters for questions...';
    
    -- Actualizar power_stats en questions con parámetros IRT calculados
    UPDATE questions q SET power_stats = (
        SELECT jsonb_build_object(
            'discrimination_index', 
            CASE 
                WHEN total_responses >= 10 THEN
                    LEAST(3.0, GREATEST(0.1, 
                        -- Índice de discriminación simplificado
                        ABS(high_performers_success - low_performers_success) * 2.0
                    ))
                ELSE 0.8 -- Valor por defecto para preguntas con pocas respuestas
            END,
            'difficulty_parameter',
            CASE 
                WHEN total_responses >= 5 THEN
                    -- Parámetro de dificultad IRT (logit de la probabilidad de respuesta correcta)
                    LN(success_rate / (1.001 - success_rate)) -- Evitar división por 0
                ELSE 0.0 -- Dificultad neutral por defecto
            END,
            'success_rate', success_rate,
            'total_responses', total_responses,
            'avg_response_time', avg_response_time,
            'irt_calibrated', CASE WHEN total_responses >= 10 THEN true ELSE false END
        )
        FROM (
            SELECT 
                COUNT(*) as total_responses,
                AVG(CASE WHEN qr.is_correct THEN 1.0 ELSE 0.0 END) as success_rate,
                AVG(qr.response_time_ms) as avg_response_time,
                -- Calcular éxito para top 25% vs bottom 25% de usuarios (por skill level promedio)
                AVG(CASE 
                    WHEN user_quartile <= 0.25 AND qr.is_correct THEN 1.0
                    WHEN user_quartile <= 0.25 THEN 0.0
                    ELSE NULL 
                END) as low_performers_success,
                AVG(CASE 
                    WHEN user_quartile >= 0.75 AND qr.is_correct THEN 1.0
                    WHEN user_quartile >= 0.75 THEN 0.0
                    ELSE NULL 
                END) as high_performers_success
            FROM question_responses qr
            LEFT JOIN (
                -- Calcular cuartil de usuario basado en skill level promedio
                SELECT 
                    user_id,
                    PERCENT_RANK() OVER (ORDER BY avg_skill_level) as user_quartile
                FROM (
                    SELECT user_id, AVG(skill_level) as avg_skill_level
                    FROM user_skills
                    GROUP BY user_id
                ) user_skills_avg
            ) user_quartiles ON user_quartiles.user_id = qr.user_id
            WHERE qr.question_id = q.id
            GROUP BY qr.question_id
        ) question_stats
    )
    WHERE EXISTS (
        SELECT 1 FROM question_responses qr WHERE qr.question_id = q.id
    );
    
    GET DIAGNOSTICS questions_updated = ROW_COUNT;
    RAISE NOTICE '✅ Updated IRT parameters for % questions', questions_updated;
END $$;

-- ================================================================================================
-- 7. POBLAR SKILL_PREREQUISITES CON DATOS INTELIGENTES
-- ================================================================================================

DO $$
DECLARE
    prerequisites_created INTEGER := 0;
BEGIN
    RAISE NOTICE '🔄 Creating intelligent skill prerequisites...';
    
    -- Crear prerequisitos basados en dificultad y correlaciones observadas
    INSERT INTO skill_prerequisites (
        skill_topic_id,
        prerequisite_topic_id,
        relationship_type,
        strength_score,
        minimum_mastery_level,
        success_rate_with_prerequisite,
        success_rate_without_prerequisite,
        pedagogical_reason
    )
    SELECT DISTINCT
        advanced_topic.id as skill_topic_id,
        basic_topic.id as prerequisite_topic_id,
        CASE 
            WHEN difficulty_diff >= 3 THEN 'hard_prerequisite'
            WHEN difficulty_diff >= 2 THEN 'soft_prerequisite'
            ELSE 'recommended'
        END as relationship_type,
        LEAST(3.0, difficulty_diff * 0.8) as strength_score,
        CASE 
            WHEN difficulty_diff >= 3 THEN 80.0
            WHEN difficulty_diff >= 2 THEN 70.0
            ELSE 60.0
        END as minimum_mastery_level,
        correlation_data.with_prereq_success,
        correlation_data.without_prereq_success,
        CASE 
            WHEN difficulty_diff >= 3 THEN 'Essential foundation - high difficulty gap requires mastery'
            WHEN difficulty_diff >= 2 THEN 'Recommended foundation - moderate difficulty progression'
            ELSE 'Helpful preparation - concepts build upon each other'
        END as pedagogical_reason
    FROM topics basic_topic
    CROSS JOIN topics advanced_topic
    LEFT JOIN (
        -- Calcular correlación basada en datos de usuarios
        SELECT 
            bt.id as basic_topic_id,
            at.id as advanced_topic_id,
            AVG(CASE WHEN us_basic.skill_level >= 70 THEN us_advanced.success_rate ELSE NULL END) as with_prereq_success,
            AVG(CASE WHEN us_basic.skill_level < 70 THEN us_advanced.success_rate ELSE NULL END) as without_prereq_success
        FROM topics bt
        CROSS JOIN topics at
        LEFT JOIN (
            SELECT 
                us.user_id, 
                us.topic_id, 
                us.skill_level,
                CASE WHEN us.total_attempts > 0 THEN (us.correct_attempts::DECIMAL / us.total_attempts) ELSE 0 END as success_rate
            FROM user_skills us
        ) us_basic ON us_basic.topic_id = bt.id
        LEFT JOIN (
            SELECT 
                us.user_id, 
                us.topic_id, 
                us.skill_level,
                CASE WHEN us.total_attempts > 0 THEN (us.correct_attempts::DECIMAL / us.total_attempts) ELSE 0 END as success_rate
            FROM user_skills us
        ) us_advanced ON us_advanced.topic_id = at.id AND us_advanced.user_id = us_basic.user_id
        WHERE bt.subject_id = at.subject_id
        AND bt.difficulty_level < at.difficulty_level
        GROUP BY bt.id, at.id
        HAVING COUNT(*) >= 3 -- Al menos 3 usuarios con datos para ambos temas
    ) correlation_data ON correlation_data.basic_topic_id = basic_topic.id 
                       AND correlation_data.advanced_topic_id = advanced_topic.id
    WHERE basic_topic.subject_id = advanced_topic.subject_id
    AND basic_topic.difficulty_level < advanced_topic.difficulty_level
    AND (advanced_topic.difficulty_level - basic_topic.difficulty_level) as difficulty_diff >= 1
    AND basic_topic.id != advanced_topic.id
    ON CONFLICT (skill_topic_id, prerequisite_topic_id) DO NOTHING;
    
    GET DIAGNOSTICS prerequisites_created = ROW_COUNT;
    RAISE NOTICE '✅ Created % intelligent skill prerequisites', prerequisites_created;
END $$;

-- ================================================================================================
-- 8. ACTUALIZACIÓN DE NEXT_REVIEW_DATE PARA SPACED REPETITION
-- ================================================================================================

DO $$
DECLARE
    reviews_scheduled INTEGER := 0;
BEGIN
    RAISE NOTICE '🔄 Scheduling spaced repetition reviews...';
    
    -- Actualizar next_review_date basado en mastery_status y última actividad
    UPDATE user_skills SET 
        next_review_date = CASE 
            WHEN mastery_status = 'expert' THEN last_interaction_date + INTERVAL '30 days'
            WHEN mastery_status = 'mastered' THEN last_interaction_date + INTERVAL '14 days'
            WHEN mastery_status = 'practiced' THEN last_interaction_date + INTERVAL '7 days'
            WHEN mastery_status = 'learning' THEN last_interaction_date + INTERVAL '3 days'
            ELSE last_interaction_date + INTERVAL '1 day'
        END,
        review_interval_hours = CASE 
            WHEN mastery_status = 'expert' THEN 720 -- 30 days
            WHEN mastery_status = 'mastered' THEN 336 -- 14 days  
            WHEN mastery_status = 'practiced' THEN 168 -- 7 days
            WHEN mastery_status = 'learning' THEN 72 -- 3 days
            ELSE 24 -- 1 day
        END,
        ease_factor = LEAST(4.0, GREATEST(1.3, 
            2.5 + (confidence_score - 0.5) * 2.0 -- Ajustar ease_factor basado en confianza
        ))
    WHERE next_review_date IS NULL;
    
    GET DIAGNOSTICS reviews_scheduled = ROW_COUNT;
    RAISE NOTICE '✅ Scheduled spaced repetition for % skills', reviews_scheduled;
END $$;

-- ================================================================================================
-- 9. VALIDACIÓN DE INTEGRIDAD DE DATOS
-- ================================================================================================

DO $$
DECLARE
    validation_errors TEXT := '';
    error_count INTEGER := 0;
BEGIN
    RAISE NOTICE '🔍 Running data integrity validation...';
    
    -- Verificar que todos los user_skills tengan valores válidos
    SELECT COUNT(*) INTO error_count
    FROM user_skills 
    WHERE skill_level < 0 OR skill_level > 100 
       OR confidence_score < 0 OR confidence_score > 1
       OR total_attempts < 0 
       OR correct_attempts < 0 
       OR correct_attempts > total_attempts;
    
    IF error_count > 0 THEN
        validation_errors := validation_errors || format('❌ %s invalid user_skills records found\n', error_count);
    ELSE
        RAISE NOTICE '✅ All user_skills records have valid values';
    END IF;
    
    -- Verificar integridad de question_responses
    SELECT COUNT(*) INTO error_count
    FROM question_responses qr
    LEFT JOIN questions q ON q.id = qr.question_id
    WHERE q.id IS NULL;
    
    IF error_count > 0 THEN
        validation_errors := validation_errors || format('❌ %s orphaned question_responses found\n', error_count);
    ELSE
        RAISE NOTICE '✅ All question_responses have valid question references';
    END IF;
    
    -- Verificar skill_prerequisites cíclicos
    WITH RECURSIVE prerequisite_chain AS (
        SELECT skill_topic_id, prerequisite_topic_id, 1 as depth, 
               ARRAY[skill_topic_id] as path
        FROM skill_prerequisites
        
        UNION ALL
        
        SELECT pc.skill_topic_id, sp.prerequisite_topic_id, pc.depth + 1,
               pc.path || sp.prerequisite_topic_id
        FROM prerequisite_chain pc
        JOIN skill_prerequisites sp ON sp.skill_topic_id = pc.prerequisite_topic_id
        WHERE pc.depth < 10 -- Evitar recursión infinita
        AND NOT (sp.prerequisite_topic_id = ANY(pc.path)) -- Evitar ciclos
    )
    SELECT COUNT(*) INTO error_count
    FROM prerequisite_chain 
    WHERE skill_topic_id = prerequisite_topic_id;
    
    IF error_count > 0 THEN
        validation_errors := validation_errors || format('❌ %s circular prerequisite dependencies found\n', error_count);
    ELSE
        RAISE NOTICE '✅ No circular prerequisite dependencies detected';
    END IF;
    
    -- Mostrar resumen de validación
    IF validation_errors != '' THEN
        RAISE WARNING 'Validation errors found:\n%', validation_errors;
    ELSE
        RAISE NOTICE '✅ ALL DATA INTEGRITY VALIDATIONS PASSED';
    END IF;
END $$;

-- ================================================================================================
-- 10. ESTADÍSTICAS FINALES DE MIGRACIÓN
-- ================================================================================================

DO $$
DECLARE
    stats_summary TEXT;
BEGIN
    SELECT format(
        E'📊 MIGRATION STATISTICS SUMMARY:\n' ||
        '   • question_responses: %s records\n' ||
        '   • user_skills: %s records (%s unique users)\n' ||
        '   • learning_sessions: %s records\n' ||
        '   • skill_prerequisites: %s relationships\n' ||
        '   • Questions with IRT parameters: %s/%s (%.1f%%)\n' ||
        '   • Users with skills tracked: %s\n' ||
        '   • Average skill level: %.1f\n' ||
        '   • Average confidence score: %.3f\n',
        (SELECT COUNT(*) FROM question_responses),
        (SELECT COUNT(*) FROM user_skills),
        (SELECT COUNT(DISTINCT user_id) FROM user_skills),
        (SELECT COUNT(*) FROM learning_sessions),
        (SELECT COUNT(*) FROM skill_prerequisites),
        (SELECT COUNT(*) FROM questions WHERE (power_stats->>'irt_calibrated')::BOOLEAN = true),
        (SELECT COUNT(*) FROM questions),
        (SELECT CASE WHEN COUNT(*) > 0 THEN 
            ((SELECT COUNT(*) FROM questions WHERE (power_stats->>'irt_calibrated')::BOOLEAN = true)::DECIMAL / COUNT(*) * 100) 
         ELSE 0 END FROM questions),
        (SELECT COUNT(DISTINCT user_id) FROM user_skills),
        (SELECT COALESCE(AVG(skill_level), 0) FROM user_skills),
        (SELECT COALESCE(AVG(confidence_score), 0) FROM user_skills)
    ) INTO stats_summary;
    
    RAISE NOTICE '%', stats_summary;
    RAISE NOTICE '🎉 DATA MIGRATION COMPLETED SUCCESSFULLY';
    RAISE NOTICE '🚀 Advanced Learning System ready for production use';
END $$;