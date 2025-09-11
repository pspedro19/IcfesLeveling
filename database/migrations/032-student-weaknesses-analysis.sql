-- PASO 11: Análisis inteligente de debilidades
-- Vista materializada para análisis de debilidades de estudiantes
-- Incluye triggers automáticos para refresh

-- =============================================================================
-- VISTA MATERIALIZADA: vw_student_weak_topics
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS vw_student_weak_topics CASCADE;

CREATE MATERIALIZED VIEW vw_student_weak_topics AS
WITH student_performance AS (
    SELECT 
        ua.user_id as student_id,
        q.subject_id,
        q.topic_id,
        s.name as subject_name,
        t.name as topic_name,
        COUNT(*) as total_attempts,
        COUNT(*) FILTER (WHERE ua.is_correct = true) as correct_answers,
        COUNT(*) FILTER (WHERE ua.is_correct = false) as incorrect_answers,
        ROUND(
            (COUNT(*) FILTER (WHERE ua.is_correct = true)::decimal / COUNT(*)) * 100, 
            2
        ) as accuracy_percentage,
        
        -- Análisis temporal
        PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY ua.time_spent_seconds) as p90_time_seconds,
        AVG(ua.time_spent_seconds) as avg_time_seconds,
        STDDEV(ua.time_spent_seconds) as stddev_time_seconds,
        
        -- Análisis de errores por distractor
        MODE() WITHIN GROUP (ORDER BY ua.selected_option) FILTER (WHERE ua.is_correct = false) as dominant_distractor,
        COUNT(*) FILTER (WHERE ua.selected_option = 
            MODE() WITHIN GROUP (ORDER BY ua.selected_option) FILTER (WHERE ua.is_correct = false)
        ) as dominant_distractor_count,
        
        -- Últimas actividades
        MAX(ua.created_at) as last_attempt_date,
        MIN(ua.created_at) as first_attempt_date
        
    FROM user_answers ua
    INNER JOIN questions q ON ua.question_id = q.id
    LEFT JOIN subjects s ON q.subject_id = s.id
    LEFT JOIN topics t ON q.topic_id = t.id
    WHERE ua.created_at >= CURRENT_DATE - INTERVAL '90 days'  -- Solo últimos 3 meses
    GROUP BY ua.user_id, q.subject_id, q.topic_id, s.name, t.name
    HAVING COUNT(*) >= 3  -- Mínimo 3 intentos para análisis confiable
),

student_theta_analysis AS (
    SELECT 
        user_id as student_id,
        -- Estimación de habilidad theta usando IRT simplificado
        CASE 
            WHEN AVG(CASE WHEN is_correct THEN 1 ELSE 0 END) >= 0.8 THEN 0.5
            WHEN AVG(CASE WHEN is_correct THEN 1 ELSE 0 END) >= 0.6 THEN 0.0
            WHEN AVG(CASE WHEN is_correct THEN 1 ELSE 0 END) >= 0.4 THEN -0.5
            ELSE -1.0
        END as estimated_theta,
        
        COUNT(*) as total_global_attempts,
        AVG(CASE WHEN is_correct THEN 1 ELSE 0 END) as global_accuracy
        
    FROM user_answers 
    WHERE created_at >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY user_id
),

weakness_classification AS (
    SELECT 
        sp.*,
        sta.estimated_theta,
        sta.global_accuracy,
        
        -- Clasificación de debilidades
        CASE
            WHEN sp.accuracy_percentage < 40 THEN 'critical'
            WHEN sp.accuracy_percentage < 60 THEN 'significant' 
            WHEN sp.accuracy_percentage < 70 AND sp.p90_time_seconds > 120 THEN 'time_inefficient'
            ELSE 'minor'
        END as weakness_severity,
        
        -- Tipo de debilidad detectada
        CASE
            WHEN sp.accuracy_percentage < 50 THEN 'conceptual_gap'
            WHEN sp.p90_time_seconds > 180 THEN 'procedural_slowness'
            WHEN sp.dominant_distractor_count > sp.total_attempts * 0.6 THEN 'systematic_error'
            WHEN sp.stddev_time_seconds > sp.avg_time_seconds THEN 'inconsistent_performance'
            ELSE 'general_weakness'
        END as weakness_type,
        
        -- Score de prioridad para intervención
        ROUND(
            (
                (100 - sp.accuracy_percentage) * 0.4 +  -- 40% peso a accuracy
                LEAST(sp.p90_time_seconds / 60, 10) * 0.2 +  -- 20% peso a tiempo (cap 10 min)
                (sp.dominant_distractor_count::decimal / sp.total_attempts) * 100 * 0.2 +  -- 20% error sistemático
                CASE WHEN sta.estimated_theta < -0.5 THEN 20 ELSE 0 END * 0.2  -- 20% habilidad baja
            ), 2
        ) as intervention_priority_score,
        
        -- Indicadores específicos
        CASE WHEN sp.accuracy_percentage < 60 THEN true ELSE false END as needs_concept_review,
        CASE WHEN sp.p90_time_seconds > 120 THEN true ELSE false END as needs_speed_practice,
        CASE WHEN sp.dominant_distractor_count > sp.total_attempts * 0.5 THEN true ELSE false END as has_systematic_error,
        CASE WHEN sta.estimated_theta < -0.5 THEN true ELSE false END as low_ability_indicator
        
    FROM student_performance sp
    INNER JOIN student_theta_analysis sta ON sp.student_id = sta.student_id
)

SELECT 
    wc.*,
    
    -- Metadatos de análisis
    CURRENT_TIMESTAMP as analysis_timestamp,
    '90_days' as analysis_period,
    'materialized_view_v1' as analysis_version,
    
    -- Recomendaciones automáticas
    CASE 
        WHEN wc.weakness_severity = 'critical' THEN 'immediate_intervention'
        WHEN wc.weakness_severity = 'significant' THEN 'structured_practice'
        WHEN wc.weakness_type = 'time_inefficient' THEN 'speed_drills'
        ELSE 'regular_practice'
    END as recommended_action,
    
    -- Estimación de sesiones necesarias
    CASE 
        WHEN wc.intervention_priority_score > 80 THEN 8
        WHEN wc.intervention_priority_score > 60 THEN 5
        WHEN wc.intervention_priority_score > 40 THEN 3
        ELSE 2
    END as estimated_sessions_needed

FROM weakness_classification wc
WHERE wc.weakness_severity IN ('critical', 'significant', 'time_inefficient')
   OR wc.intervention_priority_score > 30
ORDER BY wc.intervention_priority_score DESC, wc.accuracy_percentage ASC;

-- Crear índices para optimizar consultas
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vw_student_weak_topics_student_priority 
ON vw_student_weak_topics (student_id, intervention_priority_score DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vw_student_weak_topics_severity_subject
ON vw_student_weak_topics (weakness_severity, subject_id, topic_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_vw_student_weak_topics_timestamp
ON vw_student_weak_topics (analysis_timestamp);

-- =============================================================================
-- FUNCIÓN PARA REFRESH AUTOMÁTICO
-- =============================================================================

CREATE OR REPLACE FUNCTION refresh_student_weaknesses_analysis()
RETURNS void AS $$
DECLARE
    start_time timestamp := clock_timestamp();
    affected_rows integer;
BEGIN
    -- Log inicio del refresh
    INSERT INTO system_logs (level, message, metadata, created_at)
    VALUES (
        'INFO',
        'Starting student weaknesses analysis refresh',
        jsonb_build_object(
            'function', 'refresh_student_weaknesses_analysis',
            'start_time', start_time
        ),
        start_time
    );
    
    -- Refresh de la vista materializada
    REFRESH MATERIALIZED VIEW CONCURRENTLY vw_student_weak_topics;
    
    -- Obtener número de filas actualizadas
    SELECT count(*) INTO affected_rows FROM vw_student_weak_topics;
    
    -- Log completion
    INSERT INTO system_logs (level, message, metadata, created_at)
    VALUES (
        'INFO',
        'Student weaknesses analysis refresh completed',
        jsonb_build_object(
            'function', 'refresh_student_weaknesses_analysis',
            'duration_ms', EXTRACT(MILLISECONDS FROM clock_timestamp() - start_time),
            'affected_rows', affected_rows,
            'completion_time', clock_timestamp()
        ),
        clock_timestamp()
    );
    
EXCEPTION WHEN OTHERS THEN
    -- Log de error
    INSERT INTO system_logs (level, message, metadata, created_at)
    VALUES (
        'ERROR',
        'Error in student weaknesses analysis refresh: ' || SQLERRM,
        jsonb_build_object(
            'function', 'refresh_student_weaknesses_analysis',
            'error_code', SQLSTATE,
            'error_message', SQLERRM,
            'error_time', clock_timestamp()
        ),
        clock_timestamp()
    );
    RAISE;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS PARA REFRESH AUTOMÁTICO
-- =============================================================================

-- Tabla para controlar el último refresh
CREATE TABLE IF NOT EXISTS materialized_view_refresh_log (
    view_name varchar(100) PRIMARY KEY,
    last_refresh_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    next_scheduled_refresh timestamp,
    refresh_frequency_minutes integer DEFAULT 60,
    auto_refresh_enabled boolean DEFAULT true,
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp DEFAULT CURRENT_TIMESTAMP
);

-- Insertar configuración para la vista de debilidades
INSERT INTO materialized_view_refresh_log (view_name, refresh_frequency_minutes)
VALUES ('vw_student_weak_topics', 60)  -- Refresh cada hora
ON CONFLICT (view_name) DO UPDATE SET
    refresh_frequency_minutes = EXCLUDED.refresh_frequency_minutes,
    updated_at = CURRENT_TIMESTAMP;

-- Función para trigger automático basado en cambios en user_answers
CREATE OR REPLACE FUNCTION trigger_weakness_analysis_refresh()
RETURNS trigger AS $$
DECLARE
    last_refresh timestamp;
    min_interval interval := '30 minutes';  -- Mínimo 30 minutos entre refreshes
BEGIN
    -- Verificar si ha pasado suficiente tiempo desde el último refresh
    SELECT last_refresh_at INTO last_refresh
    FROM materialized_view_refresh_log
    WHERE view_name = 'vw_student_weak_topics';
    
    -- Solo hacer refresh si ha pasado el tiempo mínimo
    IF last_refresh IS NULL OR (CURRENT_TIMESTAMP - last_refresh) > min_interval THEN
        -- Programar refresh asíncrono (no bloquear la transacción principal)
        PERFORM pg_notify('refresh_weaknesses', 'trigger_requested');
        
        -- Actualizar timestamp
        UPDATE materialized_view_refresh_log 
        SET last_refresh_at = CURRENT_TIMESTAMP,
            next_scheduled_refresh = CURRENT_TIMESTAMP + (refresh_frequency_minutes || ' minutes')::interval
        WHERE view_name = 'vw_student_weak_topics';
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger en user_answers para detectar cambios significativos
DROP TRIGGER IF EXISTS trig_user_answer_weakness_refresh ON user_answers;
CREATE TRIGGER trig_user_answer_weakness_refresh
    AFTER INSERT OR UPDATE OR DELETE ON user_answers
    FOR EACH STATEMENT  -- Statement-level trigger para no ejecutar por cada fila
    EXECUTE FUNCTION trigger_weakness_analysis_refresh();

-- =============================================================================
-- TABLA DE ALERTAS PARA DEBILIDADES CRÍTICAS
-- =============================================================================

CREATE TABLE IF NOT EXISTS weakness_alerts (
    id SERIAL PRIMARY KEY,
    student_id UUID NOT NULL REFERENCES users(id),
    subject_id UUID REFERENCES subjects(id),
    topic_id UUID REFERENCES topics(id),
    
    alert_type varchar(50) NOT NULL,  -- 'critical_weakness', 'systematic_error', 'performance_decline'
    severity varchar(20) NOT NULL,   -- 'low', 'medium', 'high', 'critical'
    
    alert_message text NOT NULL,
    recommended_actions jsonb,
    
    trigger_conditions jsonb NOT NULL,  -- Condiciones que dispararon la alerta
    intervention_priority_score decimal(5,2),
    
    status varchar(20) DEFAULT 'active',  -- 'active', 'acknowledged', 'resolved', 'dismissed'
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at timestamp,
    
    created_at timestamp DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp,
    
    CONSTRAINT chk_alert_severity CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT chk_alert_status CHECK (status IN ('active', 'acknowledged', 'resolved', 'dismissed'))
);

CREATE INDEX IF NOT EXISTS idx_weakness_alerts_student_active 
ON weakness_alerts (student_id, status, severity) 
WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_weakness_alerts_priority 
ON weakness_alerts (intervention_priority_score DESC, created_at DESC)
WHERE status = 'active';

-- =============================================================================
-- FUNCIÓN PARA GENERAR ALERTAS AUTOMÁTICAS
-- =============================================================================

CREATE OR REPLACE FUNCTION generate_weakness_alerts()
RETURNS integer AS $$
DECLARE
    alert_count integer := 0;
    weakness_record record;
BEGIN
    -- Generar alertas para debilidades críticas recién detectadas
    FOR weakness_record IN
        SELECT * FROM vw_student_weak_topics 
        WHERE weakness_severity = 'critical' 
           OR intervention_priority_score > 85
           OR (has_systematic_error = true AND accuracy_percentage < 50)
    LOOP
        -- Verificar si ya existe una alerta activa para este estudiante/tema
        IF NOT EXISTS (
            SELECT 1 FROM weakness_alerts 
            WHERE student_id = weakness_record.student_id
              AND topic_id = weakness_record.topic_id
              AND status = 'active'
              AND created_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
        ) THEN
            -- Crear nueva alerta
            INSERT INTO weakness_alerts (
                student_id, subject_id, topic_id,
                alert_type, severity, alert_message,
                recommended_actions, trigger_conditions,
                intervention_priority_score, expires_at
            ) VALUES (
                weakness_record.student_id,
                weakness_record.subject_id,
                weakness_record.topic_id,
                CASE 
                    WHEN weakness_record.has_systematic_error THEN 'systematic_error'
                    WHEN weakness_record.accuracy_percentage < 40 THEN 'critical_weakness'
                    ELSE 'performance_decline'
                END,
                CASE 
                    WHEN weakness_record.intervention_priority_score > 90 THEN 'critical'
                    WHEN weakness_record.intervention_priority_score > 70 THEN 'high'
                    ELSE 'medium'
                END,
                format(
                    'Critical weakness detected in %s: %s. Accuracy: %s%%, Priority Score: %s',
                    weakness_record.subject_name,
                    weakness_record.topic_name,
                    weakness_record.accuracy_percentage,
                    weakness_record.intervention_priority_score
                ),
                jsonb_build_object(
                    'immediate_actions', ARRAY[weakness_record.recommended_action],
                    'estimated_sessions', weakness_record.estimated_sessions_needed,
                    'focus_areas', ARRAY[weakness_record.weakness_type]
                ),
                jsonb_build_object(
                    'accuracy_percentage', weakness_record.accuracy_percentage,
                    'total_attempts', weakness_record.total_attempts,
                    'intervention_priority_score', weakness_record.intervention_priority_score,
                    'weakness_type', weakness_record.weakness_type,
                    'analysis_timestamp', weakness_record.analysis_timestamp
                ),
                weakness_record.intervention_priority_score,
                CURRENT_TIMESTAMP + INTERVAL '30 days'
            );
            
            alert_count := alert_count + 1;
        END IF;
    END LOOP;
    
    -- Log de alertas generadas
    INSERT INTO system_logs (level, message, metadata, created_at)
    VALUES (
        'INFO',
        'Weakness alerts generation completed',
        jsonb_build_object(
            'alerts_generated', alert_count,
            'generation_time', CURRENT_TIMESTAMP
        ),
        CURRENT_TIMESTAMP
    );
    
    RETURN alert_count;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- PROGRAMADOR DE TAREAS (usando pg_cron si está disponible)
-- =============================================================================

-- Nota: Estas funciones requieren la extensión pg_cron
-- Para instalar: CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Programar refresh automático cada hora
-- SELECT cron.schedule('refresh-weakness-analysis', '0 * * * *', 'SELECT refresh_student_weaknesses_analysis();');

-- Programar generación de alertas cada 4 horas
-- SELECT cron.schedule('generate-weakness-alerts', '0 */4 * * *', 'SELECT generate_weakness_alerts();');

-- Función alternativa para sistemas sin pg_cron (usar con scheduler externo)
CREATE OR REPLACE FUNCTION scheduled_weakness_maintenance()
RETURNS jsonb AS $$
DECLARE
    refresh_result integer;
    alerts_result integer;
    start_time timestamp := clock_timestamp();
BEGIN
    -- Refresh de análisis
    PERFORM refresh_student_weaknesses_analysis();
    
    -- Generación de alertas
    SELECT generate_weakness_alerts() INTO alerts_result;
    
    RETURN jsonb_build_object(
        'status', 'completed',
        'duration_ms', EXTRACT(MILLISECONDS FROM clock_timestamp() - start_time),
        'alerts_generated', alerts_result,
        'timestamp', CURRENT_TIMESTAMP
    );
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- VISTAS AUXILIARES PARA CONSULTAS RÁPIDAS
-- =============================================================================

-- Vista de resumen por estudiante
CREATE OR REPLACE VIEW vw_student_weakness_summary AS
SELECT 
    student_id,
    COUNT(*) as total_weak_topics,
    COUNT(*) FILTER (WHERE weakness_severity = 'critical') as critical_topics,
    COUNT(*) FILTER (WHERE weakness_severity = 'significant') as significant_topics,
    AVG(intervention_priority_score) as avg_priority_score,
    MAX(intervention_priority_score) as max_priority_score,
    COUNT(*) FILTER (WHERE needs_concept_review = true) as topics_needing_review,
    COUNT(*) FILTER (WHERE has_systematic_error = true) as topics_with_systematic_errors,
    MAX(analysis_timestamp) as last_analysis
FROM vw_student_weak_topics
GROUP BY student_id;

-- Vista de alertas activas con información del estudiante
CREATE OR REPLACE VIEW vw_active_weakness_alerts AS
SELECT 
    wa.*,
    u.username,
    u.email,
    s.name as subject_name,
    t.name as topic_name,
    EXTRACT(DAYS FROM CURRENT_TIMESTAMP - wa.created_at) as days_since_created
FROM weakness_alerts wa
LEFT JOIN users u ON wa.student_id = u.id
LEFT JOIN subjects s ON wa.subject_id = s.id  
LEFT JOIN topics t ON wa.topic_id = t.id
WHERE wa.status = 'active' 
  AND (wa.expires_at IS NULL OR wa.expires_at > CURRENT_TIMESTAMP)
ORDER BY wa.intervention_priority_score DESC, wa.created_at DESC;

COMMENT ON MATERIALIZED VIEW vw_student_weak_topics IS 
'Vista materializada que analiza debilidades de estudiantes basada en accuracy, tiempo de respuesta, errores sistemáticos y habilidad estimada. Se actualiza automáticamente cada hora.';

COMMENT ON FUNCTION refresh_student_weaknesses_analysis() IS 
'Función que actualiza la vista materializada de análisis de debilidades y registra métricas de performance.';

COMMENT ON FUNCTION generate_weakness_alerts() IS 
'Genera alertas automáticas para debilidades críticas que requieren intervención inmediata.';