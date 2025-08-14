-- Virtual Economy System Migration
-- US-014: Economía Virtual Balanceada

-- Extend items table for store functionality
ALTER TABLE items ADD COLUMN IF NOT EXISTS store_price_orbs INTEGER DEFAULT 0;
ALTER TABLE items ADD COLUMN IF NOT EXISTS store_price_crystals INTEGER DEFAULT 0;
ALTER TABLE items ADD COLUMN IF NOT EXISTS is_available_in_store BOOLEAN DEFAULT FALSE;
ALTER TABLE items ADD COLUMN IF NOT EXISTS is_cosmetic BOOLEAN DEFAULT FALSE;
ALTER TABLE items ADD COLUMN IF NOT EXISTS is_power_up BOOLEAN DEFAULT FALSE;
ALTER TABLE items ADD COLUMN IF NOT EXISTS power_up_effect JSONB DEFAULT '{}';

-- Create store transactions table
CREATE TABLE IF NOT EXISTS store_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    transaction_type VARCHAR(20) NOT NULL, -- 'purchase', 'refund'
    currency_type VARCHAR(10) NOT NULL, -- 'orbs', 'crystals'
    amount_spent INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    transaction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'completed', -- 'completed', 'failed', 'refunded'
    notes TEXT
);

-- Create user power-ups table for active power-ups
CREATE TABLE IF NOT EXISTS user_power_ups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT TRUE,
    activated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    uses_remaining INTEGER DEFAULT 1,
    effect_data JSONB DEFAULT '{}'
);

-- Create currency earning history table
CREATE TABLE IF NOT EXISTS currency_earnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    currency_type VARCHAR(10) NOT NULL, -- 'orbs', 'crystals'
    amount INTEGER NOT NULL,
    source VARCHAR(50) NOT NULL, -- 'unit_completion', 'achievement', 'quest', 'battle', 'streak'
    source_id UUID, -- ID of the specific source (unit, achievement, etc.)
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Create indexes
CREATE INDEX idx_store_transactions_user_id ON store_transactions(user_id);
CREATE INDEX idx_store_transactions_item_id ON store_transactions(item_id);
CREATE INDEX idx_store_transactions_date ON store_transactions(transaction_date);
CREATE INDEX idx_user_power_ups_user_id ON user_power_ups(user_id);
CREATE INDEX idx_user_power_ups_active ON user_power_ups(is_active);
CREATE INDEX idx_currency_earnings_user_id ON currency_earnings(user_id);
CREATE INDEX idx_currency_earnings_source ON currency_earnings(source);
CREATE INDEX idx_items_store_available ON items(is_available_in_store);
CREATE INDEX idx_items_cosmetic ON items(is_cosmetic);
CREATE INDEX idx_items_power_up ON items(is_power_up);

-- Insert sample store items
INSERT INTO items (name, description, item_type, rarity, icon_url, store_price_orbs, store_price_crystals, is_available_in_store, is_cosmetic, is_power_up, power_up_effect) VALUES
-- Cosmetic Items
('Avatar Frame - Golden', 'Marco dorado para tu avatar', 'cosmetic', 'rare', '/icons/frame-golden.png', 500, 0, TRUE, TRUE, FALSE, '{}'),
('Avatar Frame - Crystal', 'Marco cristalino para tu avatar', 'cosmetic', 'epic', '/icons/frame-crystal.png', 0, 50, TRUE, TRUE, FALSE, '{}'),
('Profile Badge - Scholar', 'Insignia de estudiante destacado', 'cosmetic', 'common', '/icons/badge-scholar.png', 200, 0, TRUE, TRUE, FALSE, '{}'),
('Profile Badge - Champion', 'Insignia de campeón', 'cosmetic', 'legendary', '/icons/badge-champion.png', 0, 100, TRUE, TRUE, FALSE, '{}'),
('Custom Title - "El Sabio"', 'Título personalizado para tu perfil', 'cosmetic', 'epic', '/icons/title-sage.png', 800, 0, TRUE, TRUE, FALSE, '{}'),
('Custom Title - "El Invencible"', 'Título personalizado para tu perfil', 'cosmetic', 'legendary', '/icons/title-invincible.png', 0, 150, TRUE, TRUE, FALSE, '{}'),

-- Power-ups for Quizzes
('Double XP Potion', 'Duplica la experiencia ganada en el siguiente quiz', 'power_up', 'common', '/icons/potion-xp.png', 100, 0, TRUE, FALSE, TRUE, '{"effect": "double_xp", "duration": "next_quiz"}'),
('Time Extension', 'Añade 30 segundos extra por pregunta en el siguiente quiz', 'power_up', 'rare', '/icons/potion-time.png', 250, 0, TRUE, FALSE, TRUE, '{"effect": "time_extension", "seconds": 30, "duration": "next_quiz"}'),
('Hint Master', 'Revela una pista en cada pregunta del siguiente quiz', 'power_up', 'epic', '/icons/potion-hint.png', 0, 25, TRUE, FALSE, TRUE, '{"effect": "hint_master", "duration": "next_quiz"}'),
('Perfect Score Booster', 'Aumenta las chances de obtener puntaje perfecto', 'power_up', 'legendary', '/icons/potion-perfect.png', 0, 75, TRUE, FALSE, TRUE, '{"effect": "perfect_score_boost", "duration": "next_quiz"}'),
('Shield Generator', 'Protege contra respuestas incorrectas en el siguiente quiz', 'power_up', 'epic', '/icons/potion-shield.png', 400, 0, TRUE, FALSE, TRUE, '{"effect": "shield", "duration": "next_quiz"}'),
('Critical Strike', 'Aumenta el daño crítico en el siguiente quiz', 'power_up', 'rare', '/icons/potion-critical.png', 300, 0, TRUE, FALSE, TRUE, '{"effect": "critical_boost", "multiplier": 2, "duration": "next_quiz"}');

-- Insert sample currency earnings for testing
INSERT INTO currency_earnings (user_id, currency_type, amount, source, source_id, metadata) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'orbs', 50, 'unit_completion', '550e8400-e29b-41d4-a716-446655440001', '{"unit_number": 1, "subject": "matematicas"}'),
('550e8400-e29b-41d4-a716-446655440000', 'crystals', 10, 'achievement', '550e8400-e29b-41d4-a716-446655440002', '{"achievement": "first_unit_completed"}'),
('550e8400-e29b-41d4-a716-446655440000', 'orbs', 25, 'quest', '550e8400-e29b-41d4-a716-446655440003', '{"quest": "daily_practice"}');

-- Update existing users to have some starting currency
UPDATE users SET orbs = 1000, crystals = 50 WHERE orbs = 0 AND crystals = 0; 