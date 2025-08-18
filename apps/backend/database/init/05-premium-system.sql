-- Migration para sistema premium - US-011
-- ICFES LEVELING - Premium System

-- Extender tabla users con campos premium
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS is_premium BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS premium_expires_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS premium_plan VARCHAR(50),
ADD COLUMN IF NOT EXISTS ai_requests_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS ai_requests_limit INTEGER DEFAULT 5,
ADD COLUMN IF NOT EXISTS simulacros_used INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS simulacros_limit INTEGER DEFAULT 2;

-- Tabla para mentores reales
CREATE TABLE IF NOT EXISTS real_mentors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    subject_id UUID REFERENCES subjects(id),
    bio TEXT,
    avatar_url VARCHAR(500),
    rating DECIMAL(3,2) DEFAULT 0.0,
    hourly_rate DECIMAL(10,2),
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para sesiones con mentores
CREATE TABLE IF NOT EXISTS mentor_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    mentor_id UUID REFERENCES real_mentors(id),
    session_date TIMESTAMP WITH TIME ZONE,
    duration_minutes INTEGER,
    status VARCHAR(20) DEFAULT 'scheduled', -- 'scheduled', 'completed', 'cancelled'
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla para análisis predictivo
CREATE TABLE IF NOT EXISTS predictive_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    predicted_icfes_score DECIMAL(5,2),
    confidence_level DECIMAL(3,2),
    improvement_potential DECIMAL(5,2),
    recommended_focus_areas JSONB,
    next_milestone_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para optimización
CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium, premium_expires_at);
CREATE INDEX IF NOT EXISTS idx_mentor_sessions_user ON mentor_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictive_analytics_user ON predictive_analytics(user_id);
CREATE INDEX IF NOT EXISTS idx_real_mentors_subject ON real_mentors(subject_id);
CREATE INDEX IF NOT EXISTS idx_real_mentors_available ON real_mentors(is_available);

-- Insertar mentores de ejemplo
INSERT INTO real_mentors (name, subject_id, bio, avatar_url, rating, hourly_rate) VALUES
('Dr. Maria Rodriguez', (SELECT id FROM subjects WHERE name = 'Matemáticas' LIMIT 1), 
 'Profesora con 15 años de experiencia en preparación ICFES. Especialista en álgebra y geometría.', 
 'https://example.com/mentor1.jpg', 4.8, 45.00),
('Prof. Carlos Mendoza', (SELECT id FROM subjects WHERE name = 'Lenguaje' LIMIT 1), 
 'Licenciado en Literatura con maestría en Educación. Experto en comprensión lectora y análisis textual.', 
 'https://example.com/mentor2.jpg', 4.9, 40.00),
('Dra. Ana Silva', (SELECT id FROM subjects WHERE name = 'Ciencias Naturales' LIMIT 1), 
 'Bióloga con doctorado en Educación Científica. Especialista en física y química para ICFES.', 
 'https://example.com/mentor3.jpg', 4.7, 50.00),
('Prof. Luis Torres', (SELECT id FROM subjects WHERE name = 'Ciencias Sociales' LIMIT 1), 
 'Historiador y geógrafo con experiencia en preparación de exámenes de estado.', 
 'https://example.com/mentor4.jpg', 4.6, 35.00),
('Ms. Sarah Johnson', (SELECT id FROM subjects WHERE name = 'Inglés' LIMIT 1), 
 'Nativa de Estados Unidos con certificación TESOL. Especialista en preparación de exámenes de inglés.', 
 'https://example.com/mentor5.jpg', 4.9, 55.00);

-- Actualizar algunos usuarios existentes como premium de ejemplo
UPDATE users 
SET is_premium = TRUE, 
    premium_plan = 'monthly',
    premium_expires_at = NOW() + INTERVAL '30 days',
    ai_requests_limit = 100,
    simulacros_limit = 10
WHERE username IN ('testuser1', 'testuser2');

-- Insertar análisis predictivo de ejemplo
INSERT INTO predictive_analytics (user_id, predicted_icfes_score, confidence_level, improvement_potential, recommended_focus_areas, next_milestone_date) VALUES
((SELECT id FROM users WHERE username = 'testuser1' LIMIT 1), 320.5, 0.85, 79.5, 
 '{"matematicas": true, "lenguaje": false, "ciencias": true, "sociales": true, "ingles": false}', 
 NOW() + INTERVAL '7 days'),
((SELECT id FROM users WHERE username = 'testuser2' LIMIT 1), 285.0, 0.72, 115.0, 
 '{"matematicas": true, "lenguaje": true, "ciencias": true, "sociales": false, "ingles": true}', 
 NOW() + INTERVAL '14 days'); 