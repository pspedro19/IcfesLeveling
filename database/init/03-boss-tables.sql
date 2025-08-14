-- ICFES LEVELING - Boss Tables Migration
-- PostgreSQL 16

-- Agregar campos a la tabla battles para bosses temáticos
ALTER TABLE battles 
ADD COLUMN IF NOT EXISTS is_boss_battle BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS unit_number INTEGER,
ADD COLUMN IF NOT EXISTS boss_narrative TEXT,
ADD COLUMN IF NOT EXISTS epic_rewards JSONB DEFAULT '[]',
ADD COLUMN IF NOT EXISTS certificate_generated BOOLEAN DEFAULT FALSE;

-- Crear tabla de certificados
CREATE TABLE IF NOT EXISTS certificates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    unit_number INTEGER NOT NULL,
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    battle_id UUID REFERENCES battles(id) ON DELETE CASCADE,
    certificate_data JSONB NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_battles_boss ON battles(is_boss_battle);
CREATE INDEX IF NOT EXISTS idx_battles_unit ON battles(unit_number);
CREATE INDEX IF NOT EXISTS idx_certificates_user ON certificates(user_id);
CREATE INDEX IF NOT EXISTS idx_certificates_unit ON certificates(unit_number);

-- Insertar datos de ejemplo para bosses temáticos
INSERT INTO battles (id, user_id, battle_type, enemy_name, enemy_level, enemy_hp, is_boss_battle, unit_number, boss_narrative, epic_rewards, status)
VALUES 
    (uuid_generate_v4(), (SELECT id FROM users WHERE username = 'shadow_hunter'), 'boss', 'El Guardián de los Números Primos', 5, 250, TRUE, 1, 'Una entidad ancestral que protege los secretos de la aritmética fundamental.', '{"experience": 600, "orbs": 60, "crystals": 6, "items": [{"name": "Calculadora Épica", "rarity": "epic", "power_boost": 25}]}', 'completed'),
    (uuid_generate_v4(), (SELECT id FROM users WHERE username = 'math_master'), 'boss', 'El Señor de las Ecuaciones Cuadráticas', 10, 300, TRUE, 2, 'Un maestro de la simetría y las parábolas que desafía tu dominio algebraico.', '{"experience": 700, "orbs": 70, "crystals": 7, "items": [{"name": "Compás Legendario", "rarity": "legendary", "wisdom_boost": 30}]}', 'in_progress');

-- Insertar certificados de ejemplo
INSERT INTO certificates (id, user_id, unit_number, subject_id, battle_id, certificate_data)
VALUES 
    (uuid_generate_v4(), (SELECT id FROM users WHERE username = 'shadow_hunter'), 1, (SELECT id FROM subjects WHERE name = 'Matemáticas'), (SELECT id FROM battles WHERE enemy_name = 'El Guardián de los Números Primos'), '{"title": "Certificado de Dominio - Unidad 1", "subject": "Matemáticas", "unit_number": 1, "student_name": "shadow_hunter", "completion_date": "2024-01-15T10:30:00Z", "achievement": "Dominio demostrado en Matemáticas - Unidad 1", "signature": "Sistema ICFES Leveling", "certificate_id": "cert-001"}');

-- Comentarios sobre la implementación
COMMENT ON TABLE certificates IS 'Certificados de dominio otorgados al vencer bosses temáticos';
COMMENT ON COLUMN battles.is_boss_battle IS 'Indica si es una batalla de boss temático';
COMMENT ON COLUMN battles.unit_number IS 'Número de unidad asociada al boss';
COMMENT ON COLUMN battles.boss_narrative IS 'Narrativa épica del boss';
COMMENT ON COLUMN battles.epic_rewards IS 'Recompensas épicas al vencer al boss';
COMMENT ON COLUMN battles.certificate_generated IS 'Indica si se generó certificado de dominio'; 