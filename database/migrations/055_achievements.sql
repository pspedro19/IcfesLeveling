-- 1. achievements: Definición de logros
CREATE TABLE IF NOT EXISTS achievements (
    id VARCHAR(50) PRIMARY KEY, -- 'first_win', 'streak_7', etc.

    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(30) NOT NULL, -- 'battle', 'streak', 'mastery', 'social', 'special'

    icon_name VARCHAR(100), -- Nombre del icono en frontend
    rarity VARCHAR(20) DEFAULT 'common', -- 'common', 'rare', 'epic', 'legendary'

    -- Recompensas
    xp_reward INTEGER DEFAULT 0,
    gold_reward INTEGER DEFAULT 0,
    orbs_reward INTEGER DEFAULT 0,

    -- Requisitos
    requirement_type VARCHAR(50) NOT NULL, -- 'count', 'streak', 'score', 'milestone'
    requirement_value INTEGER NOT NULL,
    requirement_data JSONB, -- Condiciones adicionales

    -- Config
    is_hidden BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INTEGER DEFAULT 100,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. user_achievements: Logros desbloqueados por usuario
CREATE TABLE IF NOT EXISTS user_achievements (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id VARCHAR(50) NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,

    -- Progreso
    progress_current INTEGER DEFAULT 0,
    progress_target INTEGER NOT NULL,

    -- Estado
    unlocked_at TIMESTAMPTZ, -- NULL si no está desbloqueado
    notified BOOLEAN DEFAULT FALSE,
    reward_claimed BOOLEAN DEFAULT FALSE,

    PRIMARY KEY (user_id, achievement_id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- DATOS SEMILLA: Logros iniciales
INSERT INTO achievements (id, name, description, category, rarity, xp_reward, gold_reward, requirement_type, requirement_value, sort_order) VALUES
-- Primeros pasos
('first_login', 'Primer Paso', 'Inicia sesión por primera vez', 'special', 'common', 10, 50, 'milestone', 1, 1),
('first_battle', 'Guerrero Novato', 'Completa tu primera batalla', 'battle', 'common', 20, 100, 'count', 1, 2),
('first_win', 'Primera Victoria', 'Gana tu primera batalla', 'battle', 'common', 30, 150, 'count', 1, 3),

-- Streaks
('streak_3', 'Constancia', 'Mantén una racha de 3 días', 'streak', 'common', 50, 100, 'streak', 3, 10),
('streak_7', 'Semana Perfecta', 'Mantén una racha de 7 días', 'streak', 'rare', 100, 300, 'streak', 7, 11),
('streak_14', 'Dos Semanas', 'Mantén una racha de 14 días', 'streak', 'rare', 200, 500, 'streak', 14, 12),
('streak_30', 'Mes Imparable', 'Mantén una racha de 30 días', 'streak', 'epic', 500, 1000, 'streak', 30, 13),
('streak_100', 'Centurión', 'Mantén una racha de 100 días', 'streak', 'legendary', 1000, 5000, 'streak', 100, 14),

-- Batallas
('battles_10', 'Veterano', 'Completa 10 batallas', 'battle', 'common', 50, 200, 'count', 10, 20),
('battles_50', 'Gladiador', 'Completa 50 batallas', 'battle', 'rare', 150, 500, 'count', 50, 21),
('battles_100', 'Campeón', 'Completa 100 batallas', 'battle', 'epic', 300, 1000, 'count', 100, 22),
('wins_10', '10 Victorias', 'Gana 10 batallas', 'battle', 'common', 75, 250, 'count', 10, 25),
('wins_50', '50 Victorias', 'Gana 50 batallas', 'battle', 'rare', 200, 750, 'count', 50, 26),
('perfect_battle', 'Batalla Perfecta', 'Gana una batalla sin errores', 'battle', 'rare', 100, 300, 'milestone', 1, 30),

-- Rangos
('rank_d', 'Rango D', 'Alcanza el rango D', 'mastery', 'common', 100, 200, 'milestone', 1, 40),
('rank_c', 'Rango C', 'Alcanza el rango C', 'mastery', 'rare', 200, 500, 'milestone', 1, 41),
('rank_b', 'Rango B', 'Alcanza el rango B', 'mastery', 'epic', 400, 1000, 'milestone', 1, 42),
('rank_a', 'Rango A', 'Alcanza el rango A', 'mastery', 'epic', 600, 2000, 'milestone', 1, 43),
('rank_s', 'Élite', 'Alcanza el rango S', 'mastery', 'legendary', 1000, 5000, 'milestone', 1, 44),

-- Práctica Millonario
('millionaire_complete', 'Millonario', 'Completa una sesión de práctica de 15 preguntas', 'special', 'rare', 150, 500, 'milestone', 1, 50),
('millionaire_perfect', 'Millonario Perfecto', 'Completa una sesión sin usar comodines', 'special', 'epic', 300, 1000, 'milestone', 1, 51),
('millionaire_10', 'Practicante', 'Completa 10 sesiones de práctica', 'special', 'rare', 200, 600, 'count', 10, 52)

ON CONFLICT (id) DO NOTHING;

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_unlocked ON user_achievements(user_id, unlocked_at) WHERE unlocked_at IS NOT NULL;
