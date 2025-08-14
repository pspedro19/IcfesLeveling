-- Crear usuario administrador
-- Contraseña: admin123

INSERT INTO users (
    id, 
    username, 
    email, 
    hashed_password, 
    level, 
    experience, 
    rank, 
    hp, 
    mp, 
    power, 
    wisdom, 
    speed, 
    orbs, 
    crystals, 
    premium_plan, 
    is_active
) VALUES (
    'aa0e8400-e29b-41d4-a716-446655440000',  -- ID específico para admin
    'admin',
    'admin@icfesquest.com',
    '$2b$12$0VRDu9/lgHg9EF4cO/uwKeI/qevIGbeTjxAKxaghENE5qsbCRBMmm',  -- hash de "admin123"
    99,    -- Level máximo
    999999, -- Experiencia máxima
    'SSS',  -- Rango máximo
    9999,   -- HP máximo
    9999,   -- MP máximo
    999,    -- Power máximo
    999,    -- Wisdom máximo
    999,    -- Speed máximo
    999999, -- Orbs máximos
    99999,  -- Crystals máximos
    'premium', -- Plan premium
    true    -- Activo
) ON CONFLICT (email) DO UPDATE SET
    username = EXCLUDED.username,
    hashed_password = EXCLUDED.hashed_password,
    level = EXCLUDED.level,
    experience = EXCLUDED.experience,
    rank = EXCLUDED.rank,
    premium_plan = EXCLUDED.premium_plan,
    is_active = EXCLUDED.is_active;