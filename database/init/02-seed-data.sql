-- ICFES LEVELING - Seed Data
-- Datos sintéticos para demostrar toda la funcionalidad

-- Insert subjects (materias)
INSERT INTO subjects (id, name, description, icon_url, color) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Matemáticas', 'Cálculo, álgebra, geometría y estadística', '/icons/math.svg', '#FF6B6B'),
('550e8400-e29b-41d4-a716-446655440002', 'Lenguaje', 'Comprensión lectora, gramática y literatura', '/icons/language.svg', '#4ECDC4'),
('550e8400-e29b-41d4-a716-446655440003', 'Ciencias Naturales', 'Física, química y biología', '/icons/science.svg', '#45B7D1'),
('550e8400-e29b-41d4-a716-446655440004', 'Ciencias Sociales', 'Historia, geografía y filosofía', '/icons/social.svg', '#96CEB4'),
('550e8400-e29b-41d4-a716-446655440005', 'Inglés', 'Comprensión y uso del idioma inglés', '/icons/english.svg', '#FFEAA7');

-- Insert topics (temas)
INSERT INTO topics (id, subject_id, name, description, difficulty_level) VALUES
-- Matemáticas
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'Álgebra Básica', 'Ecuaciones lineales y sistemas', 1),
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'Geometría Euclidiana', 'Triángulos, círculos y polígonos', 2),
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'Cálculo Diferencial', 'Derivadas y aplicaciones', 3),
('660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 'Probabilidad', 'Eventos aleatorios y distribuciones', 4),
-- Lenguaje
('660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 'Comprensión Lectora', 'Análisis de textos', 1),
('660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 'Gramática', 'Sintaxis y morfología', 2),
('660e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440002', 'Literatura', 'Géneros literarios y análisis', 3),
-- Ciencias Naturales
('660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440003', 'Mecánica Clásica', 'Movimiento y fuerzas', 1),
('660e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440003', 'Química Orgánica', 'Compuestos del carbono', 2),
('660e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440003', 'Biología Celular', 'Estructura y función celular', 3);

-- Insert questions (preguntas)
INSERT INTO questions (id, topic_id, subject_id, question_text, difficulty, correct_answer, options, explanation, hint, tags) VALUES
-- Matemáticas - Álgebra
('770e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 
'Si 2x + 3 = 11, ¿cuál es el valor de x?', 1, 'A', 
'{"A": "4", "B": "5", "C": "6", "D": "7"}',
'Para resolver: 2x + 3 = 11 → 2x = 8 → x = 4', 
'Despeja la incógnita x', 
ARRAY['ecuaciones', 'álgebra', 'lineal']),

('770e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 
'¿Cuál es la solución del sistema: x + y = 5, 2x - y = 1?', 2, 'B', 
'{"A": "(2,3)", "B": "(2,3)", "C": "(3,2)", "D": "(1,4)"}',
'Sumando las ecuaciones: 3x = 6 → x = 2. Sustituyendo: 2 + y = 5 → y = 3', 
'Suma las dos ecuaciones para eliminar y', 
ARRAY['sistemas', 'ecuaciones', 'álgebra']),

-- Matemáticas - Geometría
('770e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 
'En un triángulo rectángulo, si los catetos miden 3 y 4, ¿cuánto mide la hipotenusa?', 1, 'C', 
'{"A": "6", "B": "6.5", "C": "5", "D": "7"}',
'Usando el teorema de Pitágoras: h² = 3² + 4² = 9 + 16 = 25 → h = 5', 
'Recuerda el teorema de Pitágoras', 
ARRAY['pitágoras', 'triángulo', 'geometría']),

-- Lenguaje - Comprensión
('770e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 
'¿Cuál es la idea principal del texto: "La tecnología ha revolucionado la forma en que nos comunicamos..."?', 1, 'A', 
'{"A": "El impacto de la tecnología en la comunicación", "B": "Los avances tecnológicos", "C": "La evolución de los medios", "D": "La sociedad moderna"}',
'La idea principal es el impacto transformador de la tecnología en la comunicación humana', 
'Busca la idea que engloba todo el texto', 
ARRAY['comprensión', 'idea principal', 'texto']),

-- Ciencias - Física
('770e8400-e29b-41d4-a716-446655440005', '660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440003', 
'¿Cuál es la unidad de medida de la fuerza en el Sistema Internacional?', 1, 'B', 
'{"A": "Joule", "B": "Newton", "C": "Watt", "D": "Pascal"}',
'La unidad de fuerza es el Newton (N), definido como kg·m/s²', 
'Recuerda la segunda ley de Newton', 
ARRAY['fuerza', 'unidades', 'física']),

-- Más preguntas para variedad
('770e8400-e29b-41d4-a716-446655440006', '660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 
'¿Cuál es la derivada de f(x) = x² + 3x + 1?', 3, 'A', 
'{"A": "2x + 3", "B": "x² + 3", "C": "2x + 1", "D": "x + 3"}',
'f''(x) = 2x + 3 (derivada de x² es 2x, de 3x es 3, de constante es 0)', 
'Recuerda las reglas de derivación', 
ARRAY['derivadas', 'cálculo', 'polinomios']),

('770e8400-e29b-41d4-a716-446655440007', '660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 
'¿Cuál es la probabilidad de obtener cara al lanzar una moneda?', 1, 'C', 
'{"A": "0.25", "B": "0.75", "C": "0.5", "D": "1"}',
'En una moneda justa, P(cara) = 1/2 = 0.5', 
'¿Cuántos resultados posibles tiene un lanzamiento?', 
ARRAY['probabilidad', 'moneda', 'eventos']),

('770e8400-e29b-41d4-a716-446655440008', '660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 
'¿Cuál es la función de un adjetivo en una oración?', 2, 'B', 
'{"A": "Expresar acción", "B": "Calificar sustantivos", "C": "Conectar ideas", "D": "Indicar tiempo"}',
'Los adjetivos califican o determinan a los sustantivos', 
'Piensa en palabras como "grande", "rojo", "hermoso"', 
ARRAY['gramática', 'adjetivos', 'sintaxis']),

('770e8400-e29b-41d4-a716-446655440009', '660e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440003', 
'¿Cuál es la fórmula molecular del metano?', 2, 'A', 
'{"A": "CH₄", "B": "C₂H₆", "C": "CH₃", "D": "C₄H₁₀"}',
'El metano es el hidrocarburo más simple: CH₄', 
'Es el primer alcano', 
ARRAY['química', 'hidrocarburos', 'metano']),

('770e8400-e29b-41d4-a716-446655440010', '660e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440003', 
'¿Cuál es la función principal de las mitocondrias?', 3, 'C', 
'{"A": "Síntesis de proteínas", "B": "Digestión celular", "C": "Producción de energía", "D": "Almacenamiento"}',
'Las mitocondrias son las "centrales energéticas" de la célula', 
'Piensa en ATP y respiración celular', 
ARRAY['biología', 'célula', 'mitocondrias']);

-- Insert items (ítems del juego)
INSERT INTO items (id, name, description, item_type, rarity, icon_url, effects, drop_rate) VALUES
('880e8400-e29b-41d4-a716-446655440001', 'Poción de Tiempo', 'Extiende el tiempo de respuesta en 10 segundos', 'consumable', 'common', '/items/time-potion.svg', '{"time_extension": 10}', 0.15),
('880e8400-e29b-41d4-a716-446655440002', 'Poción de Sabiduría', 'Aumenta temporalmente la sabiduría en 5 puntos', 'consumable', 'rare', '/items/wisdom-potion.svg', '{"wisdom_boost": 5, "duration": 300}', 0.08),
('880e8400-e29b-41d4-a716-446655440003', 'Espada de Conocimiento', 'Aumenta el daño crítico en 20%', 'cosmetic', 'epic', '/items/knowledge-sword.svg', '{"critical_damage": 0.2}', 0.03),
('880e8400-e29b-41d4-a716-446655440004', 'Corona del Sabio', 'Aumenta la experiencia ganada en 15%', 'cosmetic', 'legendary', '/items/wise-crown.svg', '{"exp_boost": 0.15}', 0.01),
('880e8400-e29b-41d4-a716-446655440005', 'Mascota Dragón', 'Compañero que aumenta la velocidad de respuesta', 'pet', 'epic', '/items/dragon-pet.svg', '{"speed_boost": 0.1}', 0.05);

-- Insert daily quests (misiones diarias)
INSERT INTO daily_quests (id, title, description, quest_type, target_value, reward_type, reward_value, reward_item_id) VALUES
('990e8400-e29b-41d4-a716-446655440001', 'Guerrero del Conocimiento', 'Completa 10 batallas hoy', 'battles', 10, 'experience', 500, NULL),
('990e8400-e29b-41d4-a716-446655440002', 'Maestro de la Precisión', 'Responde correctamente 50 preguntas', 'correct_answers', 50, 'orbs', 200, NULL),
('990e8400-e29b-41d4-a716-446655440003', 'Racha de Éxito', 'Mantén una racha de 7 días', 'streak', 7, 'crystals', 50, '880e8400-e29b-41d4-a716-446655440001'),
('990e8400-e29b-41d4-a716-446655440004', 'Conquistador de Materias', 'Completa batallas en 3 materias diferentes', 'battles', 3, 'experience', 300, NULL),
('990e8400-e29b-41d4-a716-446655440005', 'Velocista Mental', 'Responde 20 preguntas en menos de 10 segundos', 'correct_answers', 20, 'orbs', 150, '880e8400-e29b-41d4-a716-446655440002');

-- Insert sample users (usuarios de ejemplo)
INSERT INTO users (id, username, email, password_hash, display_name, level, experience, rank, hp, mp, power, wisdom, speed, orbs, crystals, streak_days) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', 'shadow_hunter', 'shadow@gameplay.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2', 'Shadow Hunter', 25, 12500, 'B', 150, 75, 25, 30, 20, 5000, 100, 5),
('aa0e8400-e29b-41d4-a716-446655440002', 'math_master', 'math@gameplay.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2', 'Math Master', 18, 8500, 'C', 120, 60, 20, 35, 15, 3000, 50, 3),
('aa0e8400-e29b-41d4-a716-446655440003', 'science_wizard', 'science@gameplay.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2', 'Science Wizard', 12, 6000, 'D', 100, 50, 15, 25, 18, 2000, 25, 1),
('aa0e8400-e29b-41d4-a716-446655440004', 'language_knight', 'language@gameplay.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2', 'Language Knight', 8, 3500, 'E', 90, 45, 12, 20, 22, 1500, 10, 0),
('aa0e8400-e29b-41d4-a716-446655440005', 'newbie_student', 'newbie@gameplay.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/HS.iK2', 'Newbie Student', 1, 0, 'E', 100, 50, 10, 10, 10, 1000, 0, 0);

-- Insert sample battles (batallas de ejemplo)
INSERT INTO battles (id, user_id, battle_type, enemy_name, enemy_level, enemy_hp, user_hp_start, user_hp_end, questions_answered, correct_answers, total_damage_dealt, total_damage_received, experience_gained, orbs_gained, status, duration_seconds) VALUES
('bb0e8400-e29b-41d4-a716-446655440001', 'aa0e8400-e29b-41d4-a716-446655440001', 'dungeon', 'Goblin Matemático', 5, 80, 150, 120, 8, 7, 140, 30, 120, 50, 'completed', 240),
('bb0e8400-e29b-41d4-a716-446655440002', 'aa0e8400-e29b-41d4-a716-446655440002', 'tower', 'Guardián de la Torre', 12, 200, 120, 80, 12, 10, 200, 40, 180, 75, 'completed', 360),
('bb0e8400-e29b-41d4-a716-446655440003', 'aa0e8400-e29b-41d4-a716-446655440003', 'dungeon', 'Esqueleto Científico', 8, 120, 100, 60, 10, 6, 120, 40, 100, 40, 'completed', 300),
('bb0e8400-e29b-41d4-a716-446655440004', 'aa0e8400-e29b-41d4-a716-446655440001', 'pvp', 'Rival Fantasma', 25, 150, 150, 90, 15, 12, 180, 60, 200, 100, 'completed', 450);

-- Insert sample battle answers (respuestas de batalla)
INSERT INTO battle_answers (id, battle_id, question_id, user_answer, is_correct, response_time_ms, damage_dealt, damage_received, critical_hit) VALUES
('cc0e8400-e29b-41d4-a716-446655440001', 'bb0e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 'A', true, 5000, 25, 0, true),
('cc0e8400-e29b-41d4-a716-446655440002', 'bb0e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 'B', true, 8000, 20, 0, false),
('cc0e8400-e29b-41d4-a716-446655440003', 'bb0e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440003', 'C', true, 3000, 30, 0, true),
('cc0e8400-e29b-41d4-a716-446655440004', 'bb0e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440004', 'B', false, 12000, 0, 15, false),
('cc0e8400-e29b-41d4-a716-446655440005', 'bb0e8400-e29b-41d4-a716-446655440002', '770e8400-e29b-41d4-a716-446655440005', 'B', true, 6000, 22, 0, false);

-- Insert user items (ítems de usuarios)
INSERT INTO user_items (user_id, item_id, quantity, equipped) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440001', 5, false),
('aa0e8400-e29b-41d4-a716-446655440001', '880e8400-e29b-41d4-a716-446655440003', 1, true),
('aa0e8400-e29b-41d4-a716-446655440002', '880e8400-e29b-41d4-a716-446655440002', 3, false),
('aa0e8400-e29b-41d4-a716-446655440003', '880e8400-e29b-41d4-a716-446655440005', 1, true);

-- Insert leaderboard entries
INSERT INTO leaderboard (user_id, score, rank_position, leaderboard_type) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', 12500, 1, 'global'),
('aa0e8400-e29b-41d4-a716-446655440002', 8500, 2, 'global'),
('aa0e8400-e29b-41d4-a716-446655440003', 6000, 3, 'global'),
('aa0e8400-e29b-41d4-a716-446655440004', 3500, 4, 'global'),
('aa0e8400-e29b-41d4-a716-446655440005', 0, 5, 'global');

-- Insert AI explanations (explicaciones de IA)
INSERT INTO ai_explanations (user_id, question_id, explanation_text, explanation_type, tokens_used, response_time_ms) VALUES
('aa0e8400-e29b-41d4-a716-446655440004', '770e8400-e29b-41d4-a716-446655440001', 
'Para resolver ecuaciones lineales, debes despejar la incógnita. En este caso: 2x + 3 = 11 → 2x = 8 → x = 4. ¡Recuerda que puedes sumar, restar, multiplicar o dividir ambos lados de la ecuación!', 
'wrong_answer', 45, 1200),

('aa0e8400-e29b-41d4-a716-446655440003', '770e8400-e29b-41d4-a716-446655440005', 
'Las unidades fundamentales del SI son: metro (m) para longitud, kilogramo (kg) para masa, segundo (s) para tiempo, y Newton (N) para fuerza. ¡La fuerza se mide en Newtons!', 
'wrong_answer', 38, 980);

-- Insert user events (eventos de usuario)
INSERT INTO user_events (user_id, event_type, event_data) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', 'user_login', '{"platform": "web", "browser": "chrome"}'),
('aa0e8400-e29b-41d4-a716-446655440001', 'battle_started', '{"battle_type": "dungeon", "enemy_level": 5}'),
('aa0e8400-e29b-41d4-a716-446655440002', 'level_up', '{"old_level": 17, "new_level": 18, "experience_gained": 500}'),
('aa0e8400-e29b-41d4-a716-446655440003', 'item_acquired', '{"item_name": "Poción de Sabiduría", "rarity": "rare"}'),
('aa0e8400-e29b-41d4-a716-446655440004', 'quest_completed', '{"quest_title": "Guerrero del Conocimiento", "reward": "500 experience"}'); 