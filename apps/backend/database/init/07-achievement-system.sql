-- Achievement System Migration
-- US-013: Sistema de Logros Significativos

-- Create achievements table
CREATE TABLE IF NOT EXISTS achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- 'unit_completion', 'score_improvement', 'study_streak', 'secret'
    achievement_type VARCHAR(50) NOT NULL, -- 'single', 'progressive', 'milestone'
    icon_url VARCHAR(500),
    rarity VARCHAR(20) DEFAULT 'common', -- 'common', 'rare', 'epic', 'legendary'
    points INTEGER DEFAULT 10,
    requirements JSONB, -- Flexible requirements structure
    is_secret BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create user_achievements table
CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    progress INTEGER DEFAULT 0,
    is_unlocked BOOLEAN DEFAULT FALSE,
    unlocked_at TIMESTAMP WITH TIME ZONE,
    progress_data JSONB, -- Store detailed progress information
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

-- Create indexes
CREATE INDEX idx_achievements_category ON achievements(category);
CREATE INDEX idx_achievements_rarity ON achievements(rarity);
CREATE INDEX idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_achievement_id ON user_achievements(achievement_id);
CREATE INDEX idx_user_achievements_unlocked ON user_achievements(is_unlocked);

-- Insert sample achievements

-- Unit Completion Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Primer Paso', 'Completa tu primera unidad de estudio', 'unit_completion', 'single', '/icons/achievements/first-unit.png', 'common', 10, '{"units_completed": 1}'),
('Estudiante Dedicado', 'Completa 5 unidades de estudio', 'unit_completion', 'progressive', '/icons/achievements/5-units.png', 'rare', 25, '{"units_completed": 5}'),
('Maestro del Conocimiento', 'Completa 10 unidades de estudio', 'unit_completion', 'progressive', '/icons/achievements/10-units.png', 'epic', 50, '{"units_completed": 10}'),
('Sabio Supremo', 'Completa 20 unidades de estudio', 'unit_completion', 'progressive', '/icons/achievements/20-units.png', 'legendary', 100, '{"units_completed": 20}'),
('Especialista', 'Completa todas las unidades de una materia', 'unit_completion', 'single', '/icons/achievements/subject-master.png', 'epic', 75, '{"subject_completed": true}');

-- Score Improvement Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Mejora Constante', 'Mejora tu puntaje en 3 evaluaciones consecutivas', 'score_improvement', 'progressive', '/icons/achievements/improvement.png', 'rare', 30, '{"consecutive_improvements": 3}'),
('Superación Personal', 'Mejora tu puntaje en 10 puntos porcentuales', 'score_improvement', 'milestone', '/icons/achievements/10-points.png', 'epic', 60, '{"score_improvement": 10}'),
('Campeón de Progreso', 'Mejora tu puntaje en 25 puntos porcentuales', 'score_improvement', 'milestone', '/icons/achievements/25-points.png', 'legendary', 150, '{"score_improvement": 25}'),
('Consistencia Dorada', 'Mantén un puntaje superior al 80% por 5 evaluaciones', 'score_improvement', 'progressive', '/icons/achievements/consistency.png', 'epic', 80, '{"high_scores_consecutive": 5, "min_score": 80}');

-- Study Streak Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements) VALUES
('Constancia', 'Mantén una racha de estudio de 7 días', 'study_streak', 'progressive', '/icons/achievements/7-days.png', 'common', 20, '{"streak_days": 7}'),
('Dedicación', 'Mantén una racha de estudio de 30 días', 'study_streak', 'progressive', '/icons/achievements/30-days.png', 'rare', 50, '{"streak_days": 30}'),
('Compromiso Total', 'Mantén una racha de estudio de 100 días', 'study_streak', 'progressive', '/icons/achievements/100-days.png', 'legendary', 200, '{"streak_days": 100}'),
('Estudiante Nocturno', 'Estudia durante 5 días consecutivos después de las 10 PM', 'study_streak', 'single', '/icons/achievements/night-owl.png', 'epic', 75, '{"night_study_streak": 5}');

-- Secret Achievements
INSERT INTO achievements (title, description, category, achievement_type, icon_url, rarity, points, requirements, is_secret) VALUES
('Descubridor', 'Encuentra tu primer logro secreto', 'secret', 'single', '/icons/achievements/secret.png', 'rare', 25, '{"secret_achievements_found": 1}', TRUE),
('Coleccionista Secreto', 'Encuentra 5 logros secretos', 'secret', 'progressive', '/icons/achievements/secret-collector.png', 'epic', 100, '{"secret_achievements_found": 5}', TRUE),
('Maestro de los Secretos', 'Encuentra todos los logros secretos', 'secret', 'single', '/icons/achievements/secret-master.png', 'legendary', 500, '{"all_secrets_found": true}', TRUE),
('Perfeccionista', 'Completa una unidad con puntaje perfecto (100%)', 'secret', 'single', '/icons/achievements/perfect.png', 'epic', 100, '{"perfect_score": true}', TRUE),
('Velocista', 'Completa 10 preguntas correctas en menos de 2 minutos', 'secret', 'single', '/icons/achievements/speedster.png', 'rare', 50, '{"speed_challenge": true}', TRUE),
('Estratega', 'Gana 5 batallas consecutivas sin perder HP', 'secret', 'single', '/icons/achievements/strategist.png', 'epic', 75, '{"perfect_battles": 5}', TRUE);

-- Insert sample user achievements for testing
INSERT INTO user_achievements (user_id, achievement_id, progress, is_unlocked, unlocked_at) VALUES
-- User 1 has some achievements
('aa0e8400-e29b-41d4-a716-446655440001', (SELECT id FROM achievements WHERE title = 'Primer Paso'), 1, TRUE, NOW() - INTERVAL '5 days'),
('aa0e8400-e29b-41d4-a716-446655440001', (SELECT id FROM achievements WHERE title = 'Constancia'), 7, TRUE, NOW() - INTERVAL '3 days'),
('aa0e8400-e29b-41d4-a716-446655440001', (SELECT id FROM achievements WHERE title = 'Descubridor'), 1, TRUE, NOW() - INTERVAL '1 day'),

-- User 2 has different achievements
('aa0e8400-e29b-41d4-a716-446655440002', (SELECT id FROM achievements WHERE title = 'Estudiante Dedicado'), 5, TRUE, NOW() - INTERVAL '2 days'),
('aa0e8400-e29b-41d4-a716-446655440002', (SELECT id FROM achievements WHERE title = 'Mejora Constante'), 3, TRUE, NOW() - INTERVAL '1 day'),
('aa0e8400-e29b-41d4-a716-446655440002', (SELECT id FROM achievements WHERE title = 'Dedicación'), 30, TRUE, NOW() - INTERVAL '1 week'),

-- User 3 has progress but no unlocked achievements
('aa0e8400-e29b-41d4-a716-446655440003', (SELECT id FROM achievements WHERE title = 'Primer Paso'), 0, FALSE, NULL),
('aa0e8400-e29b-41d4-a716-446655440003', (SELECT id FROM achievements WHERE title = 'Constancia'), 3, FALSE, NULL); 