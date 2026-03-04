-- Migration 050: Create refresh_tokens table for JWT rotation
-- Date: 2025-12-28
-- Purpose: Store refresh tokens to enable secure token rotation

-- ==========================================
-- REFRESH TOKENS TABLE
-- ==========================================
-- Stores active refresh tokens for each user
-- When a refresh token is used, it's marked as revoked and a new one is issued

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    jti VARCHAR(255) NOT NULL UNIQUE,  -- JWT ID from the token
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for fast JTI lookups (primary use case during token refresh)
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_jti ON refresh_tokens(jti);

-- Index for user-based queries (e.g., revoke all user tokens on logout)
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);

-- Index for cleanup of expired tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Index for finding active (non-revoked) tokens
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_revoked ON refresh_tokens(revoked) WHERE revoked = FALSE;

-- ==========================================
-- CLEANUP FUNCTION
-- ==========================================
-- Removes expired or revoked tokens older than 7 days

CREATE OR REPLACE FUNCTION cleanup_expired_refresh_tokens()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM refresh_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
       OR (revoked = TRUE AND created_at < CURRENT_TIMESTAMP - INTERVAL '1 day');
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ==========================================
-- COMMENTS
-- ==========================================
COMMENT ON TABLE refresh_tokens IS 'Stores JWT refresh tokens for secure token rotation';
COMMENT ON COLUMN refresh_tokens.jti IS 'JWT ID - unique identifier from the refresh token';
COMMENT ON COLUMN refresh_tokens.revoked IS 'TRUE when token has been used or manually revoked';
