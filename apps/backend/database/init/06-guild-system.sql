-- Migration para sistema de gremios por colegio - US-012
-- ICFES LEVELING - Guild System

-- Extender tabla user_profiles con campo de colegio
ALTER TABLE user_profiles
ADD COLUMN IF NOT EXISTS school_name VARCHAR(200),
ADD COLUMN IF NOT EXISTS school_city VARCHAR(100),
ADD COLUMN IF NOT EXISTS school_type VARCHAR(50); -- 'public', 'private', 'charter'

-- Tabla para gremios por colegio
CREATE TABLE IF NOT EXISTS guilds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_name VARCHAR(200) NOT NULL,
    school_city VARCHAR(100),
    guild_name VARCHAR(100) NOT NULL,
    description TEXT,
    avatar_url VARCHAR(500),
    total_members INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    average_level DECIMAL(5,2) DEFAULT 0.0,
    guild_level INTEGER DEFAULT 1,
    guild_experience INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para miembros de gremio
CREATE TABLE IF NOT EXISTS guild_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id UUID REFERENCES guilds(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- 'leader', 'officer', 'member'
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    contribution_score INTEGER DEFAULT 0,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(guild_id, user_id)
);

-- Tabla para torneos inter-colegios
CREATE TABLE IF NOT EXISTS tournaments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    tournament_type VARCHAR(50) NOT NULL, -- 'inter_school', 'regional', 'national'
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(20) DEFAULT 'upcoming', -- 'upcoming', 'active', 'completed', 'cancelled'
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,
    prize_pool JSONB DEFAULT '{}',
    rules JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para participantes de torneos
CREATE TABLE IF NOT EXISTS tournament_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tournament_id UUID REFERENCES tournaments(id) ON DELETE CASCADE,
    guild_id UUID REFERENCES guilds(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER DEFAULT 0,
    rank_position INTEGER,
    battles_won INTEGER DEFAULT 0,
    battles_lost INTEGER DEFAULT 0,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(tournament_id, user_id)
);

-- Tabla para chat de gremio
CREATE TABLE IF NOT EXISTS guild_chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    guild_id UUID REFERENCES guilds(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text', -- 'text', 'system', 'achievement'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para rankings por colegio
CREATE TABLE IF NOT EXISTS school_rankings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    school_name VARCHAR(200) NOT NULL,
    school_city VARCHAR(100),
    total_students INTEGER DEFAULT 0,
    average_score INTEGER DEFAULT 0,
    total_battles_won INTEGER DEFAULT 0,
    total_experience INTEGER DEFAULT 0,
    ranking_period VARCHAR(20) DEFAULT 'monthly', -- 'weekly', 'monthly', 'all_time'
    period_start DATE,
    period_end DATE,
    rank_position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_user_profiles_school ON user_profiles(school_name, school_city);
CREATE INDEX IF NOT EXISTS idx_guilds_school ON guilds(school_name, school_city);
CREATE INDEX IF NOT EXISTS idx_guild_members_user ON guild_members(user_id);
CREATE INDEX IF NOT EXISTS idx_guild_members_guild ON guild_members(guild_id);
CREATE INDEX IF NOT EXISTS idx_tournaments_status ON tournaments(status, start_date);
CREATE INDEX IF NOT EXISTS idx_tournament_participants_tournament ON tournament_participants(tournament_id);
CREATE INDEX IF NOT EXISTS idx_guild_chat_guild ON guild_chat_messages(guild_id, created_at);
CREATE INDEX IF NOT EXISTS idx_school_rankings_school ON school_rankings(school_name, ranking_period);

-- Insertar datos de ejemplo
INSERT INTO guilds (school_name, school_city, guild_name, description, total_members, total_score, average_level) VALUES
('Colegio San José', 'Bogotá', 'Los Sabios de San José', 'Gremio oficial del Colegio San José', 25, 15000, 45.2),
('Instituto Técnico Central', 'Medellín', 'Los Técnicos', 'Especialistas en ciencias y matemáticas', 30, 18000, 52.8),
('Liceo Moderno', 'Cali', 'Los Modernos', 'Preparación integral para ICFES', 20, 12000, 38.5),
('Colegio Santa María', 'Barranquilla', 'Los Santos', 'Excelencia académica y valores', 28, 16500, 48.3);

-- Actualizar algunos usuarios existentes con información de colegio
UPDATE user_profiles 
SET school_name = 'Colegio San José',
    school_city = 'Bogotá',
    school_type = 'private'
WHERE user_id IN (
    SELECT id FROM users WHERE username IN ('testuser1', 'testuser2')
);

-- Insertar miembros de gremio de ejemplo
INSERT INTO guild_members (guild_id, user_id, role, contribution_score) VALUES
((SELECT id FROM guilds WHERE guild_name = 'Los Sabios de San José' LIMIT 1),
 (SELECT id FROM users WHERE username = 'testuser1' LIMIT 1), 'leader', 2500),
((SELECT id FROM guilds WHERE guild_name = 'Los Técnicos' LIMIT 1),
 (SELECT id FROM users WHERE username = 'testuser2' LIMIT 1), 'officer', 1800);

-- Insertar torneo de ejemplo
INSERT INTO tournaments (name, description, tournament_type, start_date, end_date, status, max_participants, prize_pool) VALUES
('Torneo Intercolegial de Matemáticas', 'Competencia de matemáticas entre colegios de Bogotá', 'inter_school', 
 NOW() + INTERVAL '7 days', NOW() + INTERVAL '14 days', 'upcoming', 100,
 '{"first_place": {"orbs": 5000, "crystals": 100}, "second_place": {"orbs": 3000, "crystals": 50}, "third_place": {"orbs": 1500, "crystals": 25}}');

-- Insertar mensajes de chat de ejemplo
INSERT INTO guild_chat_messages (guild_id, user_id, message, message_type) VALUES
((SELECT id FROM guilds WHERE guild_name = 'Los Sabios de San José' LIMIT 1),
 (SELECT id FROM users WHERE username = 'testuser1' LIMIT 1), '¡Hola gremio! ¿Quién está listo para el torneo?', 'text'),
((SELECT id FROM guilds WHERE guild_name = 'Los Sabios de San José' LIMIT 1),
 (SELECT id FROM users WHERE username = 'testuser1' LIMIT 1), '¡Nuevo miembro alcanzó nivel 50!', 'achievement');

-- Insertar rankings de colegio de ejemplo
INSERT INTO school_rankings (school_name, school_city, total_students, average_score, total_battles_won, total_experience, ranking_period, rank_position) VALUES
('Colegio San José', 'Bogotá', 25, 15000, 125, 45000, 'monthly', 1),
('Instituto Técnico Central', 'Medellín', 30, 18000, 150, 52000, 'monthly', 2),
('Liceo Moderno', 'Cali', 20, 12000, 95, 38000, 'monthly', 3),
('Colegio Santa María', 'Barranquilla', 28, 16500, 140, 48000, 'monthly', 4); 