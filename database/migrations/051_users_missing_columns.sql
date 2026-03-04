-- Migration 051: Add all missing columns to users table
-- Date: 2025-12-28
-- Purpose: Sync users table with SQLAlchemy User model

-- ==========================================
-- BASIC USER FIELDS
-- ==========================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS streak_days INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE;

-- ==========================================
-- STREAK SYSTEM FIELDS
-- ==========================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS current_streak INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS longest_streak INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS previous_streak INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS streak_lost_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_activity_date DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS daily_goal_xp INTEGER DEFAULT 20;
ALTER TABLE users ADD COLUMN IF NOT EXISTS ad_repairs_today INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) DEFAULT 'America/Bogota';

-- ==========================================
-- HEARTS/MANA SYSTEM FIELDS
-- ==========================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS hearts INTEGER DEFAULT 5;
ALTER TABLE users ADD COLUMN IF NOT EXISTS max_hearts INTEGER DEFAULT 5;
ALTER TABLE users ADD COLUMN IF NOT EXISTS hearts_last_regeneration TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS unlimited_hearts_until TIMESTAMP WITH TIME ZONE;

-- ==========================================
-- PREMIUM/SUBSCRIPTION FIELDS
-- ==========================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS premium_plan VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;

-- ==========================================
-- UPDATE DEFAULT VALUES FOR EXISTING ROWS
-- ==========================================
UPDATE users SET display_name = username WHERE display_name IS NULL;
UPDATE users SET current_streak = COALESCE(streak_days, 0) WHERE current_streak IS NULL OR current_streak = 0;
UPDATE users SET hearts = 5 WHERE hearts IS NULL;
UPDATE users SET max_hearts = 5 WHERE max_hearts IS NULL;

-- ==========================================
-- CREATE INDEXES FOR NEW COLUMNS
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_users_current_streak ON users(current_streak);
CREATE INDEX IF NOT EXISTS idx_users_premium_plan ON users(premium_plan) WHERE premium_plan IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_users_admin ON users(is_admin) WHERE is_admin = TRUE;
