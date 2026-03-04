-- 1. user_daily_activity: Registro por día
CREATE TABLE IF NOT EXISTS user_daily_activity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    activity_date DATE NOT NULL,

    -- Métricas del día
    xp_earned INTEGER DEFAULT 0,
    questions_answered INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    study_time_minutes INTEGER DEFAULT 0,
    battles_played INTEGER DEFAULT 0,
    battles_won INTEGER DEFAULT 0,

    -- Streak
    streak_extended BOOLEAN DEFAULT FALSE,
    daily_goal_met BOOLEAN DEFAULT FALSE,

    -- Sesiones
    first_session_at TIMESTAMPTZ,
    last_session_at TIMESTAMPTZ,
    session_count INTEGER DEFAULT 1,

    UNIQUE(user_id, activity_date),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. streak_freezes: Congelamientos de racha
CREATE TABLE IF NOT EXISTS streak_freezes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    source VARCHAR(50) NOT NULL, -- 'purchase', 'reward', 'gift', 'achievement'
    acquired_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ, -- NULL = no expira

    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMPTZ,
    used_for_date DATE, -- Qué día se cubrió

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. heart_transactions: Historial de corazones
CREATE TABLE IF NOT EXISTS heart_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    transaction_type VARCHAR(20) NOT NULL, -- 'lost', 'regenerated', 'purchased', 'ad_reward', 'refilled'
    amount INTEGER NOT NULL, -- Positivo o negativo
    hearts_after INTEGER NOT NULL, -- Balance después de transacción

    source_type VARCHAR(50), -- 'wrong_answer', 'time_regen', 'gold_purchase', 'ad_watch'
    source_id UUID, -- ID de la pregunta/sesión que causó esto

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_daily_activity_user_date ON user_daily_activity(user_id, activity_date DESC);
CREATE INDEX IF NOT EXISTS idx_streak_freezes_user ON streak_freezes(user_id, is_used);
CREATE INDEX IF NOT EXISTS idx_heart_transactions_user ON heart_transactions(user_id, created_at DESC);
