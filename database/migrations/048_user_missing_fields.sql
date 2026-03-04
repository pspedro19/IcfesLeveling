-- Migration 048: Add missing User fields per README_NEGOCIO.md spec
-- Date: 2025-12-28
-- Author: Claude Code

-- Streak Freeze System Fields
ALTER TABLE users ADD COLUMN IF NOT EXISTS streak_freeze_count INTEGER DEFAULT 0;

-- Ads System Fields (for heart recovery - max 3 per day)
ALTER TABLE users ADD COLUMN IF NOT EXISTS ads_watched_today INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS ads_watched_date DATE;

-- Onboarding & Tutorial
ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;

-- AI-Projected ICFES Score (0-500)
ALTER TABLE users ADD COLUMN IF NOT EXISTS projected_icfes_score INTEGER;

-- Add gold field for economy (spec uses 'gold', implementation has 'orbs')
-- Keep both for compatibility - gold is the primary currency per spec
ALTER TABLE users ADD COLUMN IF NOT EXISTS gold INTEGER DEFAULT 1000;

-- Add indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_users_streak_freeze ON users(streak_freeze_count) WHERE streak_freeze_count > 0;
CREATE INDEX IF NOT EXISTS idx_users_onboarding ON users(onboarding_completed) WHERE onboarding_completed = FALSE;
CREATE INDEX IF NOT EXISTS idx_users_projected_score ON users(projected_icfes_score) WHERE projected_icfes_score IS NOT NULL;

-- Comments for documentation
COMMENT ON COLUMN users.streak_freeze_count IS 'Number of streak freezes available for purchase/use';
COMMENT ON COLUMN users.ads_watched_today IS 'Number of ads watched today for heart recovery (max 3)';
COMMENT ON COLUMN users.ads_watched_date IS 'Date to track ads_watched_today reset';
COMMENT ON COLUMN users.onboarding_completed IS 'Whether user completed the tutorial/onboarding';
COMMENT ON COLUMN users.projected_icfes_score IS 'AI-projected ICFES score based on performance (0-500)';
COMMENT ON COLUMN users.gold IS 'Primary currency - gold coins for purchases';
