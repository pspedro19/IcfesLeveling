-- ============================================
-- CONQUEST MODE: Database Tables
-- ICFES Leveling
-- Date: December 29, 2025
-- ============================================

-- 1. User Hearts System
CREATE TABLE IF NOT EXISTS user_hearts (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_hearts INTEGER NOT NULL DEFAULT 5,
    max_hearts INTEGER NOT NULL DEFAULT 5,
    last_heart_lost_at TIMESTAMP WITH TIME ZONE,
    last_regen_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_grace_mode BOOLEAN NOT NULL DEFAULT FALSE,
    ads_watched_today INTEGER NOT NULL DEFAULT 0,
    last_ad_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. User Economy System
CREATE TABLE IF NOT EXISTS user_economy (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    gold INTEGER NOT NULL DEFAULT 100,
    total_xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    rank VARCHAR(10) NOT NULL DEFAULT 'E',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS gold_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    balance_after INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS xp_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    source VARCHAR(50) NOT NULL,
    level_before INTEGER NOT NULL,
    level_after INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. User Streaks System
CREATE TABLE IF NOT EXISTS user_streaks (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_streak INTEGER NOT NULL DEFAULT 0,
    longest_streak INTEGER NOT NULL DEFAULT 0,
    last_activity_date DATE,
    streak_multiplier DECIMAL(3,2) NOT NULL DEFAULT 1.00,
    freeze_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. Kingdom Progress
CREATE TABLE IF NOT EXISTS user_kingdom_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kingdom_id VARCHAR(50) NOT NULL,
    diagnostic_completed BOOLEAN DEFAULT FALSE,
    overall_mastery DECIMAL(5,2) DEFAULT 0.00,
    rank VARCHAR(10) DEFAULT 'E',
    boss_defeated BOOLEAN DEFAULT FALSE,
    total_stars INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, kingdom_id)
);

-- 5. Node Progress
CREATE TABLE IF NOT EXISTS user_node_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    node_id VARCHAR(100) NOT NULL,
    kingdom_id VARCHAR(50) NOT NULL,
    mastery_percent DECIMAL(5,2) DEFAULT 0.00,
    stars_earned INTEGER DEFAULT 0,
    times_completed INTEGER DEFAULT 0,
    best_accuracy DECIMAL(5,2) DEFAULT 0.00,
    questions_seen JSONB DEFAULT '[]'::jsonb,
    is_unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, node_id)
);

-- 6. Shop Items
CREATE TABLE IF NOT EXISTS shop_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL,
    cost_gold INTEGER NOT NULL,
    effect JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. User Inventory
CREATE TABLE IF NOT EXISTS user_inventory (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID REFERENCES shop_items(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, item_id)
);

-- 8. Offline Sync Queue
CREATE TABLE IF NOT EXISTS offline_sync_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    client_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    server_received_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_gold_transactions_user ON gold_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_gold_transactions_date ON gold_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_user ON xp_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_node_progress_user ON user_node_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_node_progress_kingdom ON user_node_progress(kingdom_id);
CREATE INDEX IF NOT EXISTS idx_offline_queue_user ON offline_sync_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_offline_queue_processed ON offline_sync_queue(processed);
CREATE INDEX IF NOT EXISTS idx_kingdom_progress_user ON user_kingdom_progress(user_id);

-- ============================================
-- INITIAL DATA
-- ============================================
INSERT INTO shop_items (name, description, type, cost_gold, effect) VALUES
    ('Streak Freeze', 'Protege tu racha por 1 dia', 'streak_freeze', 200, '{"days": 1}'),
    ('Streak Repair', 'Restaura tu racha perdida (24h)', 'streak_repair', 300, '{"restore": true}'),
    ('Heart Refill', 'Recarga todos tus corazones', 'hearts', 150, '{"hearts": 5}'),
    ('Question Hint', 'Elimina 2 opciones incorrectas', 'hint', 50, '{"eliminate": 2}')
ON CONFLICT DO NOTHING;
