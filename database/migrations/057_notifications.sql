-- 1. notifications: Notificaciones
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    type VARCHAR(50) NOT NULL, -- 'achievement', 'streak_risk', 'guild', 'system'
    title VARCHAR(200) NOT NULL,
    message TEXT,

    action_url VARCHAR(500), -- Deep link
    data JSONB,

    priority VARCHAR(10) DEFAULT 'normal', -- 'low', 'normal', 'high'

    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- 2. notification_preferences: Preferencias
CREATE TABLE IF NOT EXISTS notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,

    push_enabled BOOLEAN DEFAULT TRUE,
    email_enabled BOOLEAN DEFAULT FALSE,

    streak_reminders BOOLEAN DEFAULT TRUE,
    achievement_alerts BOOLEAN DEFAULT TRUE,
    guild_notifications BOOLEAN DEFAULT TRUE,

    quiet_hours_start TIME, -- ej: 22:00
    quiet_hours_end TIME,   -- ej: 08:00

    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read, created_at DESC) WHERE is_read = FALSE;
