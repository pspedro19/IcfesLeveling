-- =============================================
-- MIGRACION 036: Sistema Offline-First & Adaptive Learning
-- Para: ICFES Leveling Mobile App (Flutter)
-- Fecha: 2024-12-27
-- =============================================

-- ============================================
-- 1. HISTORIAL DE RESPUESTAS (Adaptive Learning)
-- ============================================
CREATE TABLE IF NOT EXISTS user_question_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    question_id UUID NOT NULL REFERENCES questions(id) ON DELETE CASCADE,

    was_correct BOOLEAN NOT NULL,
    time_spent_seconds INTEGER,
    attempt_number INTEGER DEFAULT 1,

    -- Contexto de la respuesta
    session_type VARCHAR(30),  -- 'practice', 'battle', 'simulacro', 'daily_challenge'
    session_id UUID,

    -- Para sync offline
    client_timestamp TIMESTAMPTZ,
    synced_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_question_history_user ON user_question_history(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_question_history_question ON user_question_history(question_id);
CREATE INDEX IF NOT EXISTS idx_question_history_sync ON user_question_history(synced_at) WHERE synced_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_question_history_session ON user_question_history(session_id) WHERE session_id IS NOT NULL;

-- ============================================
-- 2. MAESTRIA POR TEMA (Algoritmo Adaptativo)
-- ============================================
CREATE TABLE IF NOT EXISTS user_topic_mastery (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,

    mastery_score FLOAT DEFAULT 0.0,  -- 0.0 (Novato) a 1.0 (Maestro)
    questions_seen INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,

    -- Spaced repetition
    last_practiced_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,

    -- Streak por tema
    consecutive_correct INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (user_id, topic_id)
);

CREATE INDEX IF NOT EXISTS idx_topic_mastery_weak ON user_topic_mastery(user_id, mastery_score)
    WHERE mastery_score < 0.6;
CREATE INDEX IF NOT EXISTS idx_topic_mastery_review ON user_topic_mastery(user_id, next_review_at)
    WHERE next_review_at IS NOT NULL;

-- ============================================
-- 3. COLA DE SYNC OFFLINE
-- ============================================
CREATE TABLE IF NOT EXISTS pending_answer_sync (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    question_id UUID NOT NULL,
    answer_id VARCHAR(50) NOT NULL,
    was_correct BOOLEAN NOT NULL,
    time_spent_seconds INTEGER,
    session_type VARCHAR(30),
    session_id UUID,

    client_id VARCHAR(100),
    client_timestamp TIMESTAMPTZ NOT NULL,

    -- Estado de sync
    sync_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'synced', 'failed'
    sync_attempts INTEGER DEFAULT 0,
    last_sync_attempt TIMESTAMPTZ,
    sync_error TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pending_sync ON pending_answer_sync(user_id, sync_status)
    WHERE sync_status = 'pending';
CREATE INDEX IF NOT EXISTS idx_pending_sync_retry ON pending_answer_sync(sync_status, sync_attempts)
    WHERE sync_status = 'pending' AND sync_attempts < 5;

-- ============================================
-- 4. SISTEMA DE CORAZONES (Hearts)
-- ============================================

-- Agregar columnas a users si no existen
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'hearts') THEN
        ALTER TABLE users ADD COLUMN hearts INTEGER DEFAULT 5;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'max_hearts') THEN
        ALTER TABLE users ADD COLUMN max_hearts INTEGER DEFAULT 5;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'hearts_last_regeneration') THEN
        ALTER TABLE users ADD COLUMN hearts_last_regeneration TIMESTAMPTZ DEFAULT NOW();
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'unlimited_hearts_until') THEN
        ALTER TABLE users ADD COLUMN unlimited_hearts_until TIMESTAMPTZ;
    END IF;
END $$;

-- Tabla de transacciones de corazones
CREATE TABLE IF NOT EXISTS heart_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    transaction_type VARCHAR(30) NOT NULL,
    -- 'lost' (respuesta incorrecta)
    -- 'regenerated' (tiempo - cada 4 horas)
    -- 'purchased' (gemas)
    -- 'rewarded' (ver anuncio)
    -- 'practice_earned' (reto de repaso)
    -- 'refilled' (premium)

    amount INTEGER NOT NULL,  -- +1 o -1
    hearts_after INTEGER NOT NULL,

    source_id UUID,
    source_type VARCHAR(30),  -- 'battle', 'question', 'ad', 'purchase'

    client_timestamp TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_heart_transactions_user ON heart_transactions(user_id, created_at DESC);

-- ============================================
-- 5. SISTEMA DE RACHAS (Streaks)
-- ============================================

-- Agregar columnas a users si no existen
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'current_streak') THEN
        ALTER TABLE users ADD COLUMN current_streak INTEGER DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'longest_streak') THEN
        ALTER TABLE users ADD COLUMN longest_streak INTEGER DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'last_activity_date') THEN
        ALTER TABLE users ADD COLUMN last_activity_date DATE;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'streak_freeze_count') THEN
        ALTER TABLE users ADD COLUMN streak_freeze_count INTEGER DEFAULT 0;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'daily_goal_xp') THEN
        ALTER TABLE users ADD COLUMN daily_goal_xp INTEGER DEFAULT 20;
    END IF;
END $$;

-- Actividad diaria detallada
CREATE TABLE IF NOT EXISTS user_daily_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,

    xp_earned INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    questions_correct INTEGER DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    sessions_completed INTEGER DEFAULT 0,
    lessons_completed INTEGER DEFAULT 0,

    daily_goal_met BOOLEAN DEFAULT FALSE,
    streak_extended BOOLEAN DEFAULT FALSE,
    streak_freeze_used BOOLEAN DEFAULT FALSE,

    first_session_at TIMESTAMPTZ,
    last_session_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, activity_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_activity_user ON user_daily_activity(user_id, activity_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_activity_date ON user_daily_activity(activity_date DESC);

-- Streak freezes disponibles
CREATE TABLE IF NOT EXISTS streak_freezes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    freeze_type VARCHAR(20) NOT NULL,  -- 'purchased', 'rewarded', 'premium'
    is_used BOOLEAN DEFAULT FALSE,
    used_date DATE,
    expires_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_streak_freezes_available ON streak_freezes(user_id)
    WHERE is_used = FALSE AND (expires_at IS NULL OR expires_at > NOW());

-- ============================================
-- 6. SISTEMA DE LIGAS SEMANALES
-- ============================================

-- Divisiones de liga
CREATE TABLE IF NOT EXISTS league_divisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(30) NOT NULL,
    tier INTEGER NOT NULL UNIQUE,  -- 1=Bronce, 2=Plata, 3=Oro, 4=Diamante, 5=Obsidiana

    icon_url TEXT,
    color_hex VARCHAR(7),

    min_xp_to_stay INTEGER DEFAULT 0,
    promotion_spots INTEGER DEFAULT 10,
    relegation_spots INTEGER DEFAULT 5,
    demotion_protection INTEGER DEFAULT 3,

    weekly_gem_reward INTEGER DEFAULT 0,
    weekly_xp_bonus INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insertar divisiones por defecto
INSERT INTO league_divisions (name, tier, color_hex, promotion_spots, relegation_spots, weekly_gem_reward)
VALUES
    ('Bronce', 1, '#CD7F32', 10, 0, 5),
    ('Plata', 2, '#C0C0C0', 10, 5, 10),
    ('Oro', 3, '#FFD700', 10, 5, 20),
    ('Diamante', 4, '#B9F2FF', 5, 5, 50),
    ('Obsidiana', 5, '#0F0F0F', 0, 10, 100)
ON CONFLICT (tier) DO NOTHING;

-- Semanas de competencia
CREATE TABLE IF NOT EXISTS league_weeks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_number INTEGER NOT NULL,
    year INTEGER NOT NULL,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    is_processed BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(year, week_number)
);

CREATE INDEX IF NOT EXISTS idx_league_weeks_active ON league_weeks(is_active) WHERE is_active = TRUE;

-- Grupos de liga (30 usuarios por grupo)
CREATE TABLE IF NOT EXISTS league_groups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    league_week_id UUID NOT NULL REFERENCES league_weeks(id) ON DELETE CASCADE,
    division_id UUID NOT NULL REFERENCES league_divisions(id) ON DELETE CASCADE,

    group_number INTEGER NOT NULL,
    max_members INTEGER DEFAULT 30,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(league_week_id, division_id, group_number)
);

CREATE INDEX IF NOT EXISTS idx_league_groups_week ON league_groups(league_week_id);

-- Usuarios en liga
CREATE TABLE IF NOT EXISTS user_league (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    league_group_id UUID NOT NULL REFERENCES league_groups(id) ON DELETE CASCADE,

    weekly_xp INTEGER DEFAULT 0,
    current_rank INTEGER,

    joined_at TIMESTAMPTZ DEFAULT NOW(),
    last_xp_update TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, league_group_id)
);

CREATE INDEX IF NOT EXISTS idx_user_league_ranking ON user_league(league_group_id, weekly_xp DESC);
CREATE INDEX IF NOT EXISTS idx_user_league_user ON user_league(user_id);

-- Historial de resultados (snapshot al cerrar semana)
CREATE TABLE IF NOT EXISTS user_league_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    league_week_id UUID NOT NULL REFERENCES league_weeks(id) ON DELETE CASCADE,
    division_id UUID NOT NULL REFERENCES league_divisions(id) ON DELETE CASCADE,

    final_xp INTEGER NOT NULL,
    final_rank INTEGER NOT NULL,
    total_participants INTEGER,

    status VARCHAR(20) NOT NULL,  -- 'promoted', 'relegated', 'stayed'
    gems_earned INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, league_week_id)
);

CREATE INDEX IF NOT EXISTS idx_league_history_user ON user_league_history(user_id, created_at DESC);

-- ============================================
-- 7. DESAFIOS DIARIOS
-- ============================================

CREATE TABLE IF NOT EXISTS daily_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    challenge_date DATE NOT NULL,

    title VARCHAR(100) NOT NULL,
    description TEXT,

    challenge_type VARCHAR(30) NOT NULL,  -- 'answer_n', 'streak_n', 'time_n', 'perfect_n'
    target_value INTEGER NOT NULL,

    subject_id UUID REFERENCES subjects(id),
    difficulty VARCHAR(20),  -- 'easy', 'medium', 'hard'

    xp_reward INTEGER DEFAULT 50,
    gem_reward INTEGER DEFAULT 5,
    bonus_hearts INTEGER DEFAULT 0,

    is_active BOOLEAN DEFAULT TRUE,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_daily_challenges_date ON daily_challenges(challenge_date);

CREATE TABLE IF NOT EXISTS user_daily_challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id UUID NOT NULL REFERENCES daily_challenges(id) ON DELETE CASCADE,

    current_progress INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ,

    rewards_claimed BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(user_id, challenge_id)
);

CREATE INDEX IF NOT EXISTS idx_user_challenges_pending ON user_daily_challenges(user_id, is_completed)
    WHERE is_completed = FALSE;

-- ============================================
-- 8. PUSH NOTIFICATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS user_device_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    device_token TEXT NOT NULL,
    platform VARCHAR(20) NOT NULL,  -- 'ios', 'android'
    device_info JSONB,

    is_active BOOLEAN DEFAULT TRUE,
    last_used_at TIMESTAMPTZ DEFAULT NOW(),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(device_token)
);

CREATE INDEX IF NOT EXISTS idx_device_tokens_user ON user_device_tokens(user_id) WHERE is_active = TRUE;

CREATE TABLE IF NOT EXISTS notification_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    notification_type VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    data JSONB,

    sent_at TIMESTAMPTZ DEFAULT NOW(),
    opened_at TIMESTAMPTZ,

    platform VARCHAR(20),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notification_history(user_id, sent_at DESC);

-- ============================================
-- 9. FUNCION ADAPTIVE ENGINE
-- ============================================

CREATE OR REPLACE FUNCTION get_next_adaptive_question(
    p_user_id UUID,
    p_subject_id UUID DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_question_id UUID;
    v_weak_topic_id UUID;
    v_review_topic_id UUID;
    v_random_factor FLOAT;
BEGIN
    v_random_factor := random();

    -- 60% del tiempo: Reforzar debilidades (mastery < 0.6)
    IF v_random_factor < 0.6 THEN
        SELECT topic_id INTO v_weak_topic_id
        FROM user_topic_mastery
        WHERE user_id = p_user_id
          AND mastery_score < 0.6
          AND (p_subject_id IS NULL OR topic_id IN (
              SELECT id FROM topics WHERE subject_id = p_subject_id
          ))
        ORDER BY mastery_score ASC, last_practiced_at ASC NULLS FIRST
        LIMIT 1;

        IF v_weak_topic_id IS NOT NULL THEN
            SELECT q.id INTO v_question_id
            FROM questions q
            LEFT JOIN user_question_history h
                ON h.question_id = q.id AND h.user_id = p_user_id
            WHERE q.topic_id = v_weak_topic_id
            ORDER BY h.created_at ASC NULLS FIRST, random()
            LIMIT 1;

            IF v_question_id IS NOT NULL THEN
                RETURN v_question_id;
            END IF;
        END IF;
    END IF;

    -- 25% del tiempo: Repaso espaciado (mastery > 0.9, no practicado hace 3+ dias)
    IF v_random_factor < 0.85 THEN
        SELECT topic_id INTO v_review_topic_id
        FROM user_topic_mastery
        WHERE user_id = p_user_id
          AND mastery_score > 0.9
          AND last_practiced_at < NOW() - INTERVAL '3 days'
        ORDER BY last_practiced_at ASC
        LIMIT 1;

        IF v_review_topic_id IS NOT NULL THEN
            SELECT q.id INTO v_question_id
            FROM questions q
            LEFT JOIN user_question_history h
                ON h.question_id = q.id AND h.user_id = p_user_id
            WHERE q.topic_id = v_review_topic_id
            ORDER BY h.created_at ASC NULLS FIRST, random()
            LIMIT 1;

            IF v_question_id IS NOT NULL THEN
                RETURN v_question_id;
            END IF;
        END IF;
    END IF;

    -- 15% del tiempo o fallback: Pregunta aleatoria no vista recientemente
    SELECT q.id INTO v_question_id
    FROM questions q
    LEFT JOIN user_question_history h
        ON h.question_id = q.id AND h.user_id = p_user_id
    WHERE (p_subject_id IS NULL OR q.topic_id IN (
        SELECT id FROM topics WHERE subject_id = p_subject_id
    ))
    ORDER BY h.created_at ASC NULLS FIRST, random()
    LIMIT 1;

    RETURN v_question_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 10. FUNCION ACTUALIZAR MASTERY
-- ============================================

CREATE OR REPLACE FUNCTION update_topic_mastery(
    p_user_id UUID,
    p_topic_id UUID,
    p_was_correct BOOLEAN
) RETURNS FLOAT AS $$
DECLARE
    v_current_score FLOAT;
    v_questions_seen INTEGER;
    v_questions_correct INTEGER;
    v_new_score FLOAT;
    v_consecutive INTEGER;
BEGIN
    -- Obtener estado actual o crear nuevo
    SELECT mastery_score, questions_seen, questions_correct, consecutive_correct
    INTO v_current_score, v_questions_seen, v_questions_correct, v_consecutive
    FROM user_topic_mastery
    WHERE user_id = p_user_id AND topic_id = p_topic_id;

    IF NOT FOUND THEN
        v_current_score := 0.0;
        v_questions_seen := 0;
        v_questions_correct := 0;
        v_consecutive := 0;
    END IF;

    -- Actualizar contadores
    v_questions_seen := v_questions_seen + 1;
    IF p_was_correct THEN
        v_questions_correct := v_questions_correct + 1;
        v_consecutive := v_consecutive + 1;
    ELSE
        v_consecutive := 0;
    END IF;

    -- Calcular nuevo score con weighted average
    -- Peso mayor a respuestas recientes
    v_new_score := (v_current_score * 0.7) +
                   (CASE WHEN p_was_correct THEN 0.3 ELSE 0.0 END);

    -- Bonus por racha de correctas
    IF v_consecutive >= 3 THEN
        v_new_score := LEAST(v_new_score + 0.05, 1.0);
    END IF;

    -- Clamp entre 0 y 1
    v_new_score := GREATEST(0.0, LEAST(1.0, v_new_score));

    -- Upsert
    INSERT INTO user_topic_mastery (
        user_id, topic_id, mastery_score, questions_seen,
        questions_correct, consecutive_correct, last_practiced_at, updated_at
    )
    VALUES (
        p_user_id, p_topic_id, v_new_score, v_questions_seen,
        v_questions_correct, v_consecutive, NOW(), NOW()
    )
    ON CONFLICT (user_id, topic_id) DO UPDATE SET
        mastery_score = v_new_score,
        questions_seen = v_questions_seen,
        questions_correct = v_questions_correct,
        consecutive_correct = v_consecutive,
        last_practiced_at = NOW(),
        updated_at = NOW();

    RETURN v_new_score;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 11. FUNCION REGENERAR CORAZONES
-- ============================================

CREATE OR REPLACE FUNCTION regenerate_hearts(p_user_id UUID)
RETURNS INTEGER AS $$
DECLARE
    v_current_hearts INTEGER;
    v_max_hearts INTEGER;
    v_last_regen TIMESTAMPTZ;
    v_hours_elapsed INTEGER;
    v_hearts_to_add INTEGER;
    v_new_hearts INTEGER;
BEGIN
    SELECT hearts, max_hearts, hearts_last_regeneration
    INTO v_current_hearts, v_max_hearts, v_last_regen
    FROM users
    WHERE id = p_user_id;

    IF v_current_hearts >= v_max_hearts THEN
        RETURN v_current_hearts;
    END IF;

    -- Calcular horas transcurridas
    v_hours_elapsed := EXTRACT(EPOCH FROM (NOW() - v_last_regen)) / 3600;

    -- 1 corazon cada 4 horas
    v_hearts_to_add := v_hours_elapsed / 4;

    IF v_hearts_to_add <= 0 THEN
        RETURN v_current_hearts;
    END IF;

    v_new_hearts := LEAST(v_current_hearts + v_hearts_to_add, v_max_hearts);

    UPDATE users
    SET hearts = v_new_hearts,
        hearts_last_regeneration = NOW()
    WHERE id = p_user_id;

    -- Log transaction
    INSERT INTO heart_transactions (user_id, transaction_type, amount, hearts_after)
    VALUES (p_user_id, 'regenerated', v_hearts_to_add, v_new_hearts);

    RETURN v_new_hearts;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FIN DE MIGRACION
-- ============================================
