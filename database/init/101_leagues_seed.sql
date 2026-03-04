-- Seed data for Leagues (Leaderboard)
-- Run this in your PostgreSQL database to populate the leagues_leaderboard table

CREATE TABLE IF NOT EXISTS leagues_leaderboard (
    user_id VARCHAR(255) PRIMARY KEY,
    user_name VARCHAR(255),
    league VARCHAR(50),
    rank INT,
    total_xp INT,
    weekly_xp INT,
    avatar_url TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO leagues_leaderboard (user_id, user_name, league, rank, total_xp, weekly_xp, avatar_url, updated_at)
VALUES 
    (gen_random_uuid()::text, 'Juan Perez', 'Oro', 1, 15000, 2500, NULL, NOW()),
    (gen_random_uuid()::text, 'Maria Garcia', 'Oro', 2, 14500, 2400, NULL, NOW()),
    (gen_random_uuid()::text, 'Carlos Lopez', 'Oro', 3, 14000, 2300, NULL, NOW()),
    (gen_random_uuid()::text, 'Ana Rodriguez', 'Plata', 4, 12000, 1800, NULL, NOW()),
    (gen_random_uuid()::text, 'Luis Martinez', 'Plata', 5, 11500, 1750, NULL, NOW()),
    (gen_random_uuid()::text, 'Sofia Gonzalez', 'Plata', 6, 11000, 1700, NULL, NOW()),
    (gen_random_uuid()::text, 'Pedro Sanchez', 'Bronce', 7, 9000, 1200, NULL, NOW()),
    (gen_random_uuid()::text, 'Laura Ramirez', 'Bronce', 8, 8500, 1150, NULL, NOW()),
    (gen_random_uuid()::text, 'Jorge Torres', 'Bronce', 9, 8000, 1100, NULL, NOW()),
    (gen_random_uuid()::text, 'Valentina Diaz', 'Hierro', 10, 5000, 500, NULL, NOW())
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO leagues_leaderboard (user_id, user_name, league, rank, total_xp, weekly_xp, avatar_url, updated_at)
VALUES 
    ('demo-user-id', 'Cazador Demo', 'Plata', 15, 10500, 1500, NULL, NOW())
ON CONFLICT (user_id) DO UPDATE 
SET weekly_xp = 1500, league = 'Plata';
