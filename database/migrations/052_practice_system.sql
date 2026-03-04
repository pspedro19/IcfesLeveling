-- 1. practice_sessions: Sesiones de juego
CREATE TABLE IF NOT EXISTS practice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Configuración
    session_type VARCHAR(50) DEFAULT 'failed_questions_practice',
    target_subject_id UUID REFERENCES subjects(id) ON DELETE SET NULL,
    target_topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    difficulty_level INTEGER DEFAULT 1 CHECK (difficulty_level BETWEEN 1 AND 10),

    -- Estilo Millonario
    max_questions INTEGER DEFAULT 15,
    current_question_index INTEGER DEFAULT 0,
    lifelines_available JSONB DEFAULT '{"fifty_fifty": true, "ask_ai": true, "skip": true}',

    -- Progreso
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'paused')),
    questions_answered INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    current_streak INTEGER DEFAULT 0,
    max_streak INTEGER DEFAULT 0,

    -- Recompensas acumuladas
    total_xp_earned INTEGER DEFAULT 0,
    total_gold_earned INTEGER DEFAULT 0,
    total_orbs_earned INTEGER DEFAULT 0,

    -- Boss Battle (opcional)
    boss_name VARCHAR(100),
    boss_hp INTEGER DEFAULT 100,
    boss_max_hp INTEGER DEFAULT 100,
    player_hp INTEGER DEFAULT 100,

    -- Tiempos
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    total_time_seconds INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. practice_answers: Respuestas individuales
CREATE TABLE IF NOT EXISTS practice_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,

    -- Respuesta
    question_order INTEGER NOT NULL,
    user_answer VARCHAR(1) CHECK (user_answer IN ('A', 'B', 'C', 'D')),
    is_correct BOOLEAN,
    response_time_ms INTEGER DEFAULT 0,

    -- Contexto
    difficulty_at_time INTEGER,
    was_previously_failed BOOLEAN DEFAULT FALSE,

    -- Comodines usados
    lifelines_used JSONB DEFAULT '[]',
    fifty_fifty_eliminated JSONB, -- ["A", "C"] opciones eliminadas
    ai_hint_shown BOOLEAN DEFAULT FALSE,

    -- Impacto
    xp_earned INTEGER DEFAULT 0,
    damage_dealt INTEGER DEFAULT 0, -- Para boss battle
    damage_taken INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. user_question_mastery: Dominio por pregunta
CREATE TABLE IF NOT EXISTS user_question_mastery (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,

    -- Estadísticas
    total_attempts INTEGER DEFAULT 0,
    correct_attempts INTEGER DEFAULT 0,
    consecutive_correct INTEGER DEFAULT 0,
    consecutive_wrong INTEGER DEFAULT 0,

    -- Tiempos
    avg_response_time_ms INTEGER,
    fastest_correct_ms INTEGER,

    -- Dominio (0.0 a 1.0)
    mastery_level FLOAT DEFAULT 0.0,
    needs_review BOOLEAN DEFAULT TRUE,

    -- Análisis de errores
    common_wrong_answers JSONB DEFAULT '{}', -- {"B": 3, "C": 1}

    -- Fechas
    first_attempt_at TIMESTAMPTZ,
    last_attempt_at TIMESTAMPTZ,
    mastery_achieved_at TIMESTAMPTZ, -- Cuando llegó a 85%+

    UNIQUE(user_id, question_id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. practice_rewards: Recompensas ganadas
CREATE TABLE IF NOT EXISTS practice_rewards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    reward_type VARCHAR(50) NOT NULL, -- 'xp', 'gold', 'orbs', 'item', 'achievement'
    reward_amount INTEGER,
    reward_data JSONB, -- Detalles adicionales
    earned_at_question INTEGER, -- En qué pregunta se ganó

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_practice_sessions_user ON practice_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_practice_sessions_status ON practice_sessions(status);
CREATE INDEX IF NOT EXISTS idx_practice_answers_session ON practice_answers(session_id);
CREATE INDEX IF NOT EXISTS idx_user_mastery_user ON user_question_mastery(user_id);
CREATE INDEX IF NOT EXISTS idx_user_mastery_needs_review ON user_question_mastery(user_id, needs_review) WHERE needs_review = TRUE;
