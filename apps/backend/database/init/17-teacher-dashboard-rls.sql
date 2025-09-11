-- PASO 17: Dashboard completo del docente con Row-Level Security
-- Sistema de clases, docentes y analytics avanzado

-- Tabla de docentes
CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    teacher_code VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    institution VARCHAR(200),
    department VARCHAR(100),
    specialization VARCHAR(100),
    years_experience INTEGER DEFAULT 0,
    avatar_url VARCHAR(500),
    bio TEXT,
    preferences JSONB DEFAULT '{
        "theme": "academic",
        "notifications": {
            "student_alerts": true,
            "performance_reports": true,
            "weekly_summary": true
        },
        "dashboard_layout": "default"
    }',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de clases/cursos
CREATE TABLE classes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    class_name VARCHAR(200) NOT NULL,
    class_code VARCHAR(20) UNIQUE NOT NULL,
    subject_id UUID REFERENCES subjects(id),
    grade_level VARCHAR(20), -- '9', '10', '11', 'universitario'
    semester VARCHAR(20), -- '2024-1', '2024-2'
    academic_year INTEGER DEFAULT EXTRACT(YEAR FROM CURRENT_DATE),
    description TEXT,
    max_students INTEGER DEFAULT 40,
    current_students INTEGER DEFAULT 0,
    schedule JSONB, -- Horarios de clase
    classroom VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'completed'
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de estudiantes en clases
CREATE TABLE class_enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'inactive', 'dropped', 'completed'
    final_grade DECIMAL(5,2),
    attendance_percentage DECIMAL(5,2) DEFAULT 100.0,
    last_activity TIMESTAMP,
    notes TEXT,
    UNIQUE(class_id, user_id)
);

-- Tabla de KPIs de clase (agregados diarios)
CREATE TABLE class_daily_kpis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    total_students INTEGER DEFAULT 0,
    active_students INTEGER DEFAULT 0,
    inactive_students INTEGER DEFAULT 0,
    avg_mastery DECIMAL(5,2) DEFAULT 0.0,
    avg_mastery_math DECIMAL(5,2) DEFAULT 0.0,
    avg_mastery_spanish DECIMAL(5,2) DEFAULT 0.0,
    avg_mastery_science DECIMAL(5,2) DEFAULT 0.0,
    avg_mastery_social DECIMAL(5,2) DEFAULT 0.0,
    avg_mastery_english DECIMAL(5,2) DEFAULT 0.0,
    total_battles INTEGER DEFAULT 0,
    total_questions_answered INTEGER DEFAULT 0,
    total_correct_answers INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER DEFAULT 0,
    rpg_distribution JSONB DEFAULT '{
        "E": 0, "D": 0, "C": 0, "B": 0, "A": 0, "S": 0, "S+": 0
    }',
    progress_delta_30d DECIMAL(7,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, date)
);

-- Tabla de performance de estudiante por tema
CREATE TABLE student_topic_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    topic_id UUID REFERENCES topics(id) ON DELETE CASCADE,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    mastery_level DECIMAL(5,2) DEFAULT 0.0,
    questions_attempted INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER DEFAULT 0,
    difficulty_progression DECIMAL(3,1) DEFAULT 1.0,
    last_practice TIMESTAMP,
    streak_days INTEGER DEFAULT 0,
    theta_score DECIMAL(6,3) DEFAULT 0.0, -- IRT theta parameter
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, class_id, topic_id)
);

-- Tabla de análisis de distractores
CREATE TABLE distractor_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id UUID REFERENCES questions(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    distractor_option VARCHAR(10) NOT NULL, -- 'A', 'B', 'C', 'D'
    selection_count INTEGER DEFAULT 0,
    selection_percentage DECIMAL(5,2) DEFAULT 0.0,
    avg_student_level DECIMAL(4,2) DEFAULT 0.0,
    common_error_pattern TEXT,
    pedagogical_insight TEXT,
    intervention_suggestion TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(question_id, class_id, distractor_option)
);

-- Tabla de intervenciones pedagógicas
CREATE TABLE pedagogical_interventions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    intervention_type VARCHAR(50) NOT NULL, -- 'individual', 'group', 'topic_review'
    target_students UUID[] DEFAULT '{}', -- Array de user_ids
    target_topics UUID[] DEFAULT '{}', -- Array de topic_ids
    title VARCHAR(200) NOT NULL,
    description TEXT,
    intervention_data JSONB,
    scheduled_date TIMESTAMP,
    completion_date TIMESTAMP,
    effectiveness_score DECIMAL(3,2), -- 0.0 to 1.0
    status VARCHAR(20) DEFAULT 'planned', -- 'planned', 'active', 'completed', 'cancelled'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de alertas de estudiantes en riesgo
CREATE TABLE student_risk_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    class_id UUID REFERENCES classes(id) ON DELETE CASCADE,
    teacher_id UUID REFERENCES teachers(id) ON DELETE CASCADE,
    risk_level VARCHAR(20) NOT NULL, -- 'low', 'medium', 'high', 'critical'
    risk_factors JSONB, -- Factores que contribuyen al riesgo
    alert_type VARCHAR(50) NOT NULL, -- 'academic', 'engagement', 'attendance'
    description TEXT,
    suggested_actions JSONB,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    resolution_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Habilitar Row-Level Security
ALTER TABLE classes ENABLE ROW LEVEL SECURITY;
ALTER TABLE class_enrollments ENABLE ROW LEVEL SECURITY;
ALTER TABLE class_daily_kpis ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_topic_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE distractor_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedagogical_interventions ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_risk_alerts ENABLE ROW LEVEL SECURITY;

-- Políticas RLS para docentes
CREATE POLICY teacher_own_classes ON classes
    FOR ALL USING (teacher_id IN (
        SELECT id FROM teachers WHERE user_id = current_setting('app.user_id')::UUID
    ));

CREATE POLICY teacher_class_enrollments ON class_enrollments
    FOR ALL USING (class_id IN (
        SELECT id FROM classes WHERE teacher_id IN (
            SELECT id FROM teachers WHERE user_id = current_setting('app.user_id')::UUID
        )
    ));

CREATE POLICY teacher_class_kpis ON class_daily_kpis
    FOR ALL USING (class_id IN (
        SELECT id FROM classes WHERE teacher_id IN (
            SELECT id FROM teachers WHERE user_id = current_setting('app.user_id')::UUID
        )
    ));

CREATE POLICY teacher_student_performance ON student_topic_performance
    FOR ALL USING (class_id IN (
        SELECT id FROM classes WHERE teacher_id IN (
            SELECT id FROM teachers WHERE user_id = current_setting('app.user_id')::UUID
        )
    ));

CREATE POLICY teacher_distractor_analysis ON distractor_analysis
    FOR ALL USING (class_id IN (
        SELECT id FROM classes WHERE teacher_id IN (
            SELECT id FROM teachers WHERE user_id = current_setting('app.user_id')::UUID
        )
    ));

CREATE POLICY teacher_interventions ON pedagogical_interventions
    FOR ALL USING (teacher_id IN (
        SELECT id FROM teachers WHERE user_id = current_setting('app.user_id')::UUID
    ));

CREATE POLICY teacher_risk_alerts ON student_risk_alerts
    FOR ALL USING (teacher_id IN (
        SELECT id FROM teachers WHERE user_id = current_setting('app.user_id')::UUID
    ));

-- Función para calcular KPIs de clase
CREATE OR REPLACE FUNCTION calculate_class_kpis(p_class_id UUID, p_date DATE DEFAULT CURRENT_DATE)
RETURNS VOID AS $$
DECLARE
    v_total_students INTEGER;
    v_active_students INTEGER;
    v_inactive_students INTEGER;
    v_avg_mastery DECIMAL(5,2);
    v_mastery_by_subject RECORD;
    v_rpg_dist JSONB;
    v_progress_delta DECIMAL(7,2);
BEGIN
    -- Calcular estadísticas básicas
    SELECT 
        COUNT(*),
        COUNT(CASE WHEN ce.last_activity >= p_date - INTERVAL '7 days' THEN 1 END),
        COUNT(CASE WHEN ce.last_activity < p_date - INTERVAL '7 days' OR ce.last_activity IS NULL THEN 1 END)
    INTO v_total_students, v_active_students, v_inactive_students
    FROM class_enrollments ce
    WHERE ce.class_id = p_class_id AND ce.status = 'active';
    
    -- Calcular mastery promedio general
    SELECT AVG(stp.mastery_level)
    INTO v_avg_mastery
    FROM student_topic_performance stp
    WHERE stp.class_id = p_class_id;
    
    -- Calcular distribución RPG
    SELECT jsonb_build_object(
        'E', COUNT(CASE WHEN u.rank = 'E' THEN 1 END),
        'D', COUNT(CASE WHEN u.rank = 'D' THEN 1 END),
        'C', COUNT(CASE WHEN u.rank = 'C' THEN 1 END),
        'B', COUNT(CASE WHEN u.rank = 'B' THEN 1 END),
        'A', COUNT(CASE WHEN u.rank = 'A' THEN 1 END),
        'S', COUNT(CASE WHEN u.rank = 'S' THEN 1 END),
        'S+', COUNT(CASE WHEN u.rank = 'S+' THEN 1 END)
    )
    INTO v_rpg_dist
    FROM class_enrollments ce
    JOIN users u ON ce.user_id = u.id
    WHERE ce.class_id = p_class_id AND ce.status = 'active';
    
    -- Calcular delta de progreso últimos 30 días
    SELECT 
        COALESCE(AVG(
            CASE 
                WHEN prev_kpis.avg_mastery > 0 THEN 
                    ((curr_performance.avg_mastery - prev_kpis.avg_mastery) / prev_kpis.avg_mastery) * 100
                ELSE 0
            END
        ), 0)
    INTO v_progress_delta
    FROM (
        SELECT AVG(stp.mastery_level) as avg_mastery
        FROM student_topic_performance stp
        WHERE stp.class_id = p_class_id
        AND stp.updated_at >= p_date - INTERVAL '7 days'
    ) curr_performance,
    (
        SELECT avg_mastery
        FROM class_daily_kpis
        WHERE class_id = p_class_id
        AND date = p_date - INTERVAL '30 days'
    ) prev_kpis;
    
    -- Insertar o actualizar KPIs
    INSERT INTO class_daily_kpis (
        class_id, date, total_students, active_students, inactive_students,
        avg_mastery, rpg_distribution, progress_delta_30d
    )
    VALUES (
        p_class_id, p_date, v_total_students, v_active_students, v_inactive_students,
        COALESCE(v_avg_mastery, 0), v_rpg_dist, v_progress_delta
    )
    ON CONFLICT (class_id, date)
    DO UPDATE SET
        total_students = EXCLUDED.total_students,
        active_students = EXCLUDED.active_students,
        inactive_students = EXCLUDED.inactive_students,
        avg_mastery = EXCLUDED.avg_mastery,
        rpg_distribution = EXCLUDED.rpg_distribution,
        progress_delta_30d = EXCLUDED.progress_delta_30d,
        created_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Función para detectar estudiantes en riesgo
CREATE OR REPLACE FUNCTION detect_at_risk_students(p_class_id UUID)
RETURNS VOID AS $$
DECLARE
    v_student RECORD;
    v_risk_factors JSONB;
    v_risk_level VARCHAR(20);
BEGIN
    FOR v_student IN 
        SELECT 
            ce.user_id,
            ce.class_id,
            u.username,
            AVG(stp.mastery_level) as avg_mastery,
            COUNT(CASE WHEN stp.last_practice >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as recent_activity,
            MAX(stp.last_practice) as last_activity,
            ce.attendance_percentage
        FROM class_enrollments ce
        JOIN users u ON ce.user_id = u.id
        LEFT JOIN student_topic_performance stp ON stp.user_id = ce.user_id AND stp.class_id = ce.class_id
        WHERE ce.class_id = p_class_id AND ce.status = 'active'
        GROUP BY ce.user_id, ce.class_id, u.username, ce.attendance_percentage
    LOOP
        v_risk_factors := jsonb_build_object(
            'low_mastery', v_student.avg_mastery < 60,
            'no_recent_activity', v_student.recent_activity = 0,
            'poor_attendance', v_student.attendance_percentage < 75,
            'long_absence', v_student.last_activity < CURRENT_DATE - INTERVAL '14 days'
        );
        
        -- Determinar nivel de riesgo
        IF (v_risk_factors->>'low_mastery')::BOOLEAN AND 
           (v_risk_factors->>'no_recent_activity')::BOOLEAN AND
           (v_risk_factors->>'poor_attendance')::BOOLEAN THEN
            v_risk_level := 'critical';
        ELSIF (v_risk_factors->>'low_mastery')::BOOLEAN AND 
              ((v_risk_factors->>'no_recent_activity')::BOOLEAN OR 
               (v_risk_factors->>'poor_attendance')::BOOLEAN) THEN
            v_risk_level := 'high';
        ELSIF (v_risk_factors->>'low_mastery')::BOOLEAN OR 
              (v_risk_factors->>'no_recent_activity')::BOOLEAN THEN
            v_risk_level := 'medium';
        ELSE
            v_risk_level := 'low';
        END IF;
        
        -- Insertar alerta si el riesgo es medio o superior
        IF v_risk_level != 'low' THEN
            INSERT INTO student_risk_alerts (
                user_id, class_id, teacher_id, risk_level, risk_factors, alert_type,
                description, suggested_actions
            )
            SELECT 
                v_student.user_id,
                v_student.class_id,
                c.teacher_id,
                v_risk_level,
                v_risk_factors,
                'academic',
                format('Estudiante %s presenta riesgo %s', v_student.username, v_risk_level),
                jsonb_build_array(
                    'Contactar al estudiante',
                    'Revisar material de refuerzo',
                    'Programar tutoría personalizada'
                )
            FROM classes c
            WHERE c.id = v_student.class_id
            ON CONFLICT (user_id, class_id, alert_type) WHERE NOT is_resolved
            DO UPDATE SET
                risk_level = EXCLUDED.risk_level,
                risk_factors = EXCLUDED.risk_factors,
                description = EXCLUDED.description,
                created_at = CURRENT_TIMESTAMP;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Crear índices para optimización
CREATE INDEX idx_teachers_user_id ON teachers(user_id);
CREATE INDEX idx_teachers_code ON teachers(teacher_code);
CREATE INDEX idx_classes_teacher ON classes(teacher_id);
CREATE INDEX idx_classes_subject ON classes(subject_id);
CREATE INDEX idx_classes_status ON classes(status);
CREATE INDEX idx_class_enrollments_class ON class_enrollments(class_id);
CREATE INDEX idx_class_enrollments_user ON class_enrollments(user_id);
CREATE INDEX idx_class_enrollments_status ON class_enrollments(status);
CREATE INDEX idx_class_daily_kpis_class_date ON class_daily_kpis(class_id, date);
CREATE INDEX idx_student_topic_performance_user_class ON student_topic_performance(user_id, class_id);
CREATE INDEX idx_student_topic_performance_topic ON student_topic_performance(topic_id);
CREATE INDEX idx_student_topic_performance_mastery ON student_topic_performance(mastery_level);
CREATE INDEX idx_distractor_analysis_question_class ON distractor_analysis(question_id, class_id);
CREATE INDEX idx_pedagogical_interventions_class ON pedagogical_interventions(class_id);
CREATE INDEX idx_pedagogical_interventions_teacher ON pedagogical_interventions(teacher_id);
CREATE INDEX idx_pedagogical_interventions_status ON pedagogical_interventions(status);
CREATE INDEX idx_student_risk_alerts_class ON student_risk_alerts(class_id);
CREATE INDEX idx_student_risk_alerts_teacher ON student_risk_alerts(teacher_id);
CREATE INDEX idx_student_risk_alerts_user ON student_risk_alerts(user_id);
CREATE INDEX idx_student_risk_alerts_risk_level ON student_risk_alerts(risk_level);
CREATE INDEX idx_student_risk_alerts_resolved ON student_risk_alerts(is_resolved);

-- Triggers para actualizar timestamps
CREATE TRIGGER update_teachers_updated_at 
    BEFORE UPDATE ON teachers 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_classes_updated_at 
    BEFORE UPDATE ON classes 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_student_topic_performance_updated_at 
    BEFORE UPDATE ON student_topic_performance 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();