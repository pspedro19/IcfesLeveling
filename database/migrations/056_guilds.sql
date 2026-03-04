-- 1. guilds: Gremios
CREATE TABLE IF NOT EXISTS guilds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    emblem_url VARCHAR(500),

    leader_id UUID NOT NULL REFERENCES users(id),

    -- Stats
    level INTEGER DEFAULT 1,
    total_xp BIGINT DEFAULT 0,
    weekly_xp BIGINT DEFAULT 0,
    member_count INTEGER DEFAULT 1,
    max_members INTEGER DEFAULT 30,

    -- Configuración
    is_public BOOLEAN DEFAULT TRUE,
    join_requirements JSONB DEFAULT '{"min_level": 1}',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. guild_members: Miembros
CREATE TABLE IF NOT EXISTS guild_members (
    guild_id UUID NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    role VARCHAR(20) DEFAULT 'member', -- 'leader', 'officer', 'member'
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    contribution_xp BIGINT DEFAULT 0,
    last_active_at TIMESTAMPTZ DEFAULT NOW(),

    PRIMARY KEY (guild_id, user_id)
);

-- 3. guild_chat: Chat del gremio
CREATE TABLE IF NOT EXISTS guild_chat (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id UUID NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    message TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text', -- 'text', 'system', 'achievement'

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Constraint: Usuario solo en 1 guild
CREATE UNIQUE INDEX IF NOT EXISTS idx_guild_members_user_unique ON guild_members(user_id);

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_guilds_level ON guilds(level DESC);
CREATE INDEX IF NOT EXISTS idx_guilds_weekly_xp ON guilds(weekly_xp DESC);
CREATE INDEX IF NOT EXISTS idx_guild_chat_guild ON guild_chat(guild_id, created_at DESC);
