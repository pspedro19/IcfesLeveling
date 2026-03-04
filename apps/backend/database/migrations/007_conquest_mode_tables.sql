-- ============================================
-- MIGRATION 007: CONQUEST MODE TABLES
-- ICFES Leveling - Conquest Mode
-- Date: December 29, 2025
--
-- This migration creates all tables needed for
-- the Conquest Mode feature including:
-- - Heart system
-- - Economy (gold, XP, levels, ranks)
-- - Streaks
-- - Kingdom and Node progress
-- - Shop and inventory
-- - Offline sync queue
-- ============================================

-- ============================================
-- 1. USER HEARTS SYSTEM
-- Manages heart-based attempt limits
-- ============================================
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

COMMENT ON TABLE user_hearts IS 'Tracks user hearts for the Conquest Mode attempt system';
COMMENT ON COLUMN user_hearts.current_hearts IS 'Current number of hearts available';
COMMENT ON COLUMN user_hearts.max_hearts IS 'Maximum hearts the user can have';
COMMENT ON COLUMN user_hearts.is_grace_mode IS 'True if user is in grace period (new user protection)';
COMMENT ON COLUMN user_hearts.ads_watched_today IS 'Number of ads watched today for heart recovery';

-- ============================================
-- 2. USER ECONOMY SYSTEM
-- Gold, XP, levels, and ranks
-- ============================================
CREATE TABLE IF NOT EXISTS user_economy (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    gold INTEGER NOT NULL DEFAULT 100,
    total_xp INTEGER NOT NULL DEFAULT 0,
    level INTEGER NOT NULL DEFAULT 1,
    rank VARCHAR(10) NOT NULL DEFAULT 'E',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE user_economy IS 'User economy data: gold, XP, level, and rank';
COMMENT ON COLUMN user_economy.gold IS 'Current gold balance';
COMMENT ON COLUMN user_economy.total_xp IS 'Total XP earned all-time';
COMMENT ON COLUMN user_economy.level IS 'Current player level';
COMMENT ON COLUMN user_economy.rank IS 'Current rank (E, D, C, B, A, S, SS, SSS)';

-- ============================================
-- 3. GOLD TRANSACTIONS
-- Transaction history for gold
-- ============================================
CREATE TABLE IF NOT EXISTS gold_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    description TEXT,
    balance_after INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE gold_transactions IS 'Log of all gold transactions';
COMMENT ON COLUMN gold_transactions.amount IS 'Amount of gold (positive for earned, negative for spent)';
COMMENT ON COLUMN gold_transactions.transaction_type IS 'Type: earned, spent, bonus, refund, purchase';
COMMENT ON COLUMN gold_transactions.balance_after IS 'Gold balance after this transaction';

-- ============================================
-- 4. XP TRANSACTIONS
-- XP earning history
-- ============================================
CREATE TABLE IF NOT EXISTS xp_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount INTEGER NOT NULL,
    source VARCHAR(50) NOT NULL,
    level_before INTEGER NOT NULL,
    level_after INTEGER NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE xp_transactions IS 'Log of all XP transactions';
COMMENT ON COLUMN xp_transactions.source IS 'Source: question, battle, quest, streak, daily_challenge';
COMMENT ON COLUMN xp_transactions.level_before IS 'User level before this XP was added';
COMMENT ON COLUMN xp_transactions.level_after IS 'User level after this XP was added';

-- ============================================
-- 5. USER STREAKS SYSTEM
-- Daily streak tracking
-- ============================================
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

COMMENT ON TABLE user_streaks IS 'Tracks user daily activity streaks';
COMMENT ON COLUMN user_streaks.current_streak IS 'Current consecutive day streak';
COMMENT ON COLUMN user_streaks.longest_streak IS 'Longest streak ever achieved';
COMMENT ON COLUMN user_streaks.streak_multiplier IS 'XP/gold multiplier based on streak';
COMMENT ON COLUMN user_streaks.freeze_count IS 'Number of streak freezes available';

-- ============================================
-- 6. KINGDOM PROGRESS
-- User progress per subject/kingdom
-- ============================================
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

COMMENT ON TABLE user_kingdom_progress IS 'Tracks user progress in each Kingdom (subject)';
COMMENT ON COLUMN user_kingdom_progress.kingdom_id IS 'Kingdom identifier: math, reading, science, social, english';
COMMENT ON COLUMN user_kingdom_progress.diagnostic_completed IS 'Whether diagnostic test is completed';
COMMENT ON COLUMN user_kingdom_progress.overall_mastery IS 'Overall mastery percentage (0-100)';
COMMENT ON COLUMN user_kingdom_progress.boss_defeated IS 'Whether the kingdom boss has been defeated';
COMMENT ON COLUMN user_kingdom_progress.total_stars IS 'Total stars earned across all nodes';

-- ============================================
-- 7. NODE PROGRESS
-- User progress per topic/node
-- ============================================
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

COMMENT ON TABLE user_node_progress IS 'Tracks user progress on individual nodes/topics';
COMMENT ON COLUMN user_node_progress.node_id IS 'Node identifier within the kingdom';
COMMENT ON COLUMN user_node_progress.mastery_percent IS 'Mastery percentage (0-100)';
COMMENT ON COLUMN user_node_progress.stars_earned IS 'Stars earned (0-3)';
COMMENT ON COLUMN user_node_progress.times_completed IS 'Number of times node was completed';
COMMENT ON COLUMN user_node_progress.best_accuracy IS 'Best accuracy achieved';
COMMENT ON COLUMN user_node_progress.questions_seen IS 'Array of question IDs already seen';
COMMENT ON COLUMN user_node_progress.is_unlocked IS 'Whether node is unlocked for practice';

-- ============================================
-- 8. SHOP ITEMS
-- Items available for purchase
-- ============================================
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

COMMENT ON TABLE shop_items IS 'Items available in the in-game shop';
COMMENT ON COLUMN shop_items.type IS 'Item type: streak_freeze, streak_repair, hearts, hint, cosmetic';
COMMENT ON COLUMN shop_items.cost_gold IS 'Cost in gold to purchase';
COMMENT ON COLUMN shop_items.effect IS 'JSON describing item effect';

-- ============================================
-- 9. USER INVENTORY
-- Items owned by users
-- ============================================
CREATE TABLE IF NOT EXISTS user_inventory (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID REFERENCES shop_items(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    acquired_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, item_id)
);

COMMENT ON TABLE user_inventory IS 'Items owned by each user';
COMMENT ON COLUMN user_inventory.quantity IS 'Number of this item the user owns';

-- ============================================
-- 10. OFFLINE SYNC QUEUE
-- Queue for offline actions to sync
-- ============================================
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

COMMENT ON TABLE offline_sync_queue IS 'Queue for offline actions pending sync';
COMMENT ON COLUMN offline_sync_queue.action_type IS 'Type of action: answer_question, complete_node, use_item';
COMMENT ON COLUMN offline_sync_queue.payload IS 'JSON payload with action details';
COMMENT ON COLUMN offline_sync_queue.client_timestamp IS 'When action occurred on client';
COMMENT ON COLUMN offline_sync_queue.processed IS 'Whether action has been processed';

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Gold transactions indexes
CREATE INDEX IF NOT EXISTS idx_gold_transactions_user
    ON gold_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_gold_transactions_date
    ON gold_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_gold_transactions_type
    ON gold_transactions(transaction_type);

-- XP transactions indexes
CREATE INDEX IF NOT EXISTS idx_xp_transactions_user
    ON xp_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_date
    ON xp_transactions(created_at);
CREATE INDEX IF NOT EXISTS idx_xp_transactions_source
    ON xp_transactions(source);

-- Node progress indexes
CREATE INDEX IF NOT EXISTS idx_node_progress_user
    ON user_node_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_node_progress_kingdom
    ON user_node_progress(kingdom_id);
CREATE INDEX IF NOT EXISTS idx_node_progress_unlocked
    ON user_node_progress(is_unlocked) WHERE is_unlocked = TRUE;

-- Kingdom progress indexes
CREATE INDEX IF NOT EXISTS idx_kingdom_progress_user
    ON user_kingdom_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_kingdom_progress_kingdom
    ON user_kingdom_progress(kingdom_id);

-- Offline sync queue indexes
CREATE INDEX IF NOT EXISTS idx_offline_queue_user
    ON offline_sync_queue(user_id);
CREATE INDEX IF NOT EXISTS idx_offline_queue_processed
    ON offline_sync_queue(processed);
CREATE INDEX IF NOT EXISTS idx_offline_queue_pending
    ON offline_sync_queue(user_id, processed) WHERE processed = FALSE;

-- User hearts indexes
CREATE INDEX IF NOT EXISTS idx_user_hearts_regen
    ON user_hearts(last_regen_at) WHERE current_hearts < max_hearts;

-- User streaks indexes
CREATE INDEX IF NOT EXISTS idx_user_streaks_date
    ON user_streaks(last_activity_date);

-- Shop items indexes
CREATE INDEX IF NOT EXISTS idx_shop_items_type
    ON shop_items(type) WHERE is_active = TRUE;

-- ============================================
-- INITIAL DATA: DEFAULT SHOP ITEMS
-- ============================================
INSERT INTO shop_items (name, description, type, cost_gold, effect) VALUES
    ('Streak Freeze', 'Protege tu racha por 1 dia si olvidas practicar', 'streak_freeze', 200, '{"days": 1}'),
    ('Streak Repair', 'Restaura tu racha perdida (disponible por 24h)', 'streak_repair', 300, '{"restore": true, "hours_valid": 24}'),
    ('Heart Refill', 'Recarga todos tus corazones al maximo', 'hearts', 150, '{"hearts": 5}'),
    ('Single Heart', 'Recupera un corazon inmediatamente', 'hearts', 50, '{"hearts": 1}'),
    ('Question Hint', 'Elimina 2 opciones incorrectas en una pregunta', 'hint', 50, '{"eliminate": 2}'),
    ('Double XP (1h)', 'Duplica el XP ganado durante 1 hora', 'booster', 100, '{"xp_multiplier": 2, "duration_minutes": 60}'),
    ('Gold Rush (1h)', 'Duplica el oro ganado durante 1 hora', 'booster', 100, '{"gold_multiplier": 2, "duration_minutes": 60}')
ON CONFLICT DO NOTHING;

-- ============================================
-- TRIGGER: Auto-update updated_at columns
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at
DO $$
BEGIN
    -- user_hearts trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_user_hearts_updated_at') THEN
        CREATE TRIGGER trg_user_hearts_updated_at
            BEFORE UPDATE ON user_hearts
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- user_economy trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_user_economy_updated_at') THEN
        CREATE TRIGGER trg_user_economy_updated_at
            BEFORE UPDATE ON user_economy
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- user_streaks trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_user_streaks_updated_at') THEN
        CREATE TRIGGER trg_user_streaks_updated_at
            BEFORE UPDATE ON user_streaks
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- user_kingdom_progress trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_user_kingdom_progress_updated_at') THEN
        CREATE TRIGGER trg_user_kingdom_progress_updated_at
            BEFORE UPDATE ON user_kingdom_progress
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;

    -- user_node_progress trigger
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_user_node_progress_updated_at') THEN
        CREATE TRIGGER trg_user_node_progress_updated_at
            BEFORE UPDATE ON user_node_progress
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- ============================================
-- END OF MIGRATION 007
-- ============================================
