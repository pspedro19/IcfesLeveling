-- ICFES LEVELING - Seed Data
-- Datos sintéticos para demostrar toda la funcionalidad

-- Insert subjects (materias)
INSERT INTO subjects (id, name, description, icon_url, color) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Matemáticas', 'Cálculo, álgebra, geometría y estadística', '/assets/images/subjects/matematicasicon.png', '#FF6B6B'),
('550e8400-e29b-41d4-a716-446655440002', 'Lectura Crítica', 'Comprensión lectora, gramática y literatura', '/assets/images/subjects/lecturaicon.png', '#4ECDC4'),
('550e8400-e29b-41d4-a716-446655440003', 'Ciencias Naturales', 'Física, química y biología', '/assets/images/subjects/cienciasnaturalesicon.png', '#45B7D1'),
('550e8400-e29b-41d4-a716-446655440004', 'Ciencias Sociales', 'Historia, geografía y filosofía', '/assets/images/subjects/socialesicon.png', '#96CEB4'),
('550e8400-e29b-41d4-a716-446655440005', 'Inglés', 'Comprensión y uso del idioma inglés', '/assets/images/subjects/englishicon.png', '#FFEAA7');

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

-- Insert questions (preguntas) - DISABLED: Using real ICFES data instead
-- INSERT INTO questions (id, topic_id, subject_id, question_text, difficulty, correct_answer, options, explanation, hint, tags) VALUES
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
INSERT INTO items (id, name, description, item_type, rarity, icon_url, drop_rate, power_boost, wisdom_boost, speed_boost) VALUES
('880e8400-e29b-41d4-a716-446655440001', 'Poción de Tiempo', 'Extiende el tiempo de respuesta en 10 segundos', 'consumable', 'common', '/assets/images/ui/time-potion.png', 0.15, 0, 0, 10),
('880e8400-e29b-41d4-a716-446655440002', 'Poción de Sabiduría', 'Aumenta temporalmente la sabiduría en 5 puntos', 'consumable', 'rare', '/assets/images/ui/wisdom-potion.png', 0.08, 0, 5, 0),
('880e8400-e29b-41d4-a716-446655440003', 'Espada de Conocimiento', 'Aumenta el daño crítico en 20%', 'cosmetic', 'epic', '/assets/images/ui/knowledge-sword.png', 0.03, 20, 0, 0),
('880e8400-e29b-41d4-a716-446655440004', 'Corona del Sabio', 'Aumenta la experiencia ganada en 15%', 'cosmetic', 'legendary', '/assets/images/ui/wise-crown.png', 0.01, 0, 15, 0),
('880e8400-e29b-41d4-a716-446655440005', 'Mascota Dragón', 'Compañero que aumenta la velocidad de respuesta', 'pet', 'epic', '/assets/images/ui/dragon-pet.png', 0.05, 0, 0, 15);

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

-- 🌟 SISTEMA ÉPICO: Clases de Héroes
INSERT INTO hero_classes (id, name, description, avatar_url, stats_boost, special_ability, element, color_theme) VALUES
('cc0e8400-e29b-41d4-a716-446655440001', 'Mago Cuántico', 'Dominas las matemáticas con precisión mágica. Tu mente analítica te permite resolver problemas complejos con elegancia matemática.', '/assets/images/heroes/mage-quantum.png.jpg', '{"wisdom": 25, "mp": 30, "math_power": 20}', 'Explicación Mágica: +50% precisión en matemáticas', 'Fuego', '#FF6B6B'),
('cc0e8400-e29b-41d4-a716-446655440002', 'Guerrero del Conocimiento', 'Tu fuerza física se convierte en poder mental. Eres resistente y perseverante en el aprendizaje.', '/assets/images/heroes/warrior-knowledge.png.jpg', '{"power": 25, "hp": 30, "resistance": 15}', 'Resistencia Mental: +30% HP en batallas largas', 'Tierra', '#96CEB4'),
('cc0e8400-e29b-41d4-a716-446655440003', 'Arquero de la Sabiduría', 'Velocidad y precisión en cada respuesta. Tu agilidad mental te permite responder rápidamente.', '/assets/images/heroes/archer-wisdom.png.jpg', '{"speed": 25, "agility": 20, "accuracy": 15}', 'Tiro Crítico: +40% probabilidad de respuestas críticas', 'Viento', '#4ECDC4'),
('cc0e8400-e29b-41d4-a716-446655440004', 'Sacerdote del Aprendizaje', 'Sanas las dudas con conocimiento sagrado. Tu sabiduría te permite explicar conceptos complejos.', '/assets/images/heroes/priest-learning.png.jpg', '{"wisdom": 30, "mp": 25, "healing": 20}', 'Curación Mental: Recupera HP al explicar conceptos', 'Luz', '#FFEAA7'),
('cc0e8400-e29b-41d4-a716-446655440005', 'Asesino de la Lógica', 'Encuentras la respuesta correcta con astucia. Tu precisión te permite identificar patrones ocultos.', '/assets/images/heroes/assassin-logic.png.jpg', '{"agility": 25, "speed": 20, "critical_chance": 20}', 'Golpe Preciso: +60% daño crítico en respuestas correctas', 'Sombra', '#6C5CE7');

-- 🌟 SISTEMA ÉPICO: Preguntas de Personalidad
INSERT INTO personality_questions (id, question_text, question_type, options, weight_factors, order_index) VALUES
-- Pregunta 1: Motivación
('dd0e8400-e29b-41d4-a716-446655440001', '¿Qué te motiva más a estudiar?', 'motivation', 
'{"A": "Resolver problemas complejos y desafíos intelectuales", "B": "Ayudar a otros a aprender y compartir conocimiento", "C": "Competir y superar mis propios récords", "D": "Explorar nuevos conceptos y descubrir patrones", "E": "Dominar completamente un tema antes de avanzar"}',
'{"A": {"warrior": 3, "mage": 2, "archer": 1, "priest": 1, "assassin": 1}, "B": {"warrior": 1, "mage": 1, "archer": 1, "priest": 4, "assassin": 1}, "C": {"warrior": 4, "mage": 2, "archer": 3, "priest": 1, "assassin": 2}, "D": {"warrior": 1, "mage": 4, "archer": 2, "priest": 2, "assassin": 3}, "E": {"warrior": 2, "mage": 3, "archer": 1, "priest": 2, "assassin": 4}}',
1),

-- Pregunta 2: Estilo de Aprendizaje
('dd0e8400-e29b-41d4-a716-446655440002', '¿Cómo prefieres aprender nuevos conceptos?', 'learning_style',
'{"A": "A través de ejemplos prácticos y ejercicios", "B": "Explicando el concepto a otros", "C": "Competiendo y midiendo mi progreso", "D": "Analizando patrones y conexiones", "E": "Memorizando y repitiendo hasta dominarlo"}',
'{"A": {"warrior": 3, "mage": 2, "archer": 4, "priest": 2, "assassin": 2}, "B": {"warrior": 1, "mage": 2, "archer": 1, "priest": 4, "assassin": 1}, "C": {"warrior": 4, "mage": 2, "archer": 3, "priest": 1, "assassin": 2}, "D": {"warrior": 1, "mage": 4, "archer": 2, "priest": 2, "assassin": 3}, "E": {"warrior": 2, "mage": 3, "archer": 1, "priest": 2, "assassin": 4}}',
2),

-- Pregunta 3: Materia Favorita
('dd0e8400-e29b-41d4-a716-446655440003', '¿Cuál es tu materia favorita?', 'subject_preference',
'{"A": "Matemáticas - Me encantan los números y la lógica", "B": "Lenguaje - Me gusta analizar textos y comunicar ideas", "C": "Ciencias Naturales - Me fascina experimentar y descubrir", "D": "Ciencias Sociales - Me interesa entender el mundo", "E": "Inglés - Me gusta aprender idiomas y culturas"}',
'{"A": {"warrior": 2, "mage": 4, "archer": 3, "priest": 2, "assassin": 3}, "B": {"warrior": 1, "mage": 2, "archer": 2, "priest": 4, "assassin": 2}, "C": {"warrior": 3, "mage": 3, "archer": 4, "priest": 2, "assassin": 2}, "D": {"warrior": 2, "mage": 2, "archer": 1, "priest": 3, "assassin": 2}, "E": {"warrior": 1, "mage": 1, "archer": 2, "priest": 2, "assassin": 4}}',
3),

-- Pregunta 4: Enfoque de Resolución
('dd0e8400-e29b-41d4-a716-446655440004', '¿Cómo abordas un problema difícil?', 'problem_solving',
'{"A": "Lo ataco directamente con fuerza y determinación", "B": "Busco ayuda y colaboro con otros", "C": "Lo analizo paso a paso con precisión", "D": "Busco patrones y conexiones ocultas", "E": "Lo memorizo y practico hasta dominarlo"}',
'{"A": {"warrior": 4, "mage": 1, "archer": 2, "priest": 2, "assassin": 1}, "B": {"warrior": 1, "mage": 2, "archer": 1, "priest": 4, "assassin": 1}, "C": {"warrior": 2, "mage": 3, "archer": 4, "priest": 2, "assassin": 2}, "D": {"warrior": 1, "mage": 4, "archer": 2, "priest": 2, "assassin": 3}, "E": {"warrior": 2, "mage": 2, "archer": 1, "priest": 2, "assassin": 4}}',
4),

-- Pregunta 5: Preferencia Social
('dd0e8400-e29b-41d4-a716-446655440005', '¿Cómo prefieres estudiar?', 'social_preference',
'{"A": "Solo, concentrado en mi propio ritmo", "B": "En grupo, compartiendo ideas y ayudando", "C": "Competitivo, midiendo mi progreso contra otros", "D": "Explorativo, descubriendo nuevas conexiones", "E": "Metódico, siguiendo un plan estructurado"}',
'{"A": {"warrior": 2, "mage": 3, "archer": 4, "priest": 1, "assassin": 4}, "B": {"warrior": 1, "mage": 2, "archer": 1, "priest": 4, "assassin": 1}, "C": {"warrior": 4, "mage": 2, "archer": 3, "priest": 1, "assassin": 2}, "D": {"warrior": 1, "mage": 4, "archer": 2, "priest": 2, "assassin": 3}, "E": {"warrior": 2, "mage": 3, "archer": 1, "priest": 2, "assassin": 4}}',
5);

-- 🌟 SISTEMA ÉPICO: Asignar perfiles a usuarios existentes
INSERT INTO user_profiles (user_id, hero_class_id, personality_answers, avatar_customization) VALUES
('aa0e8400-e29b-41d4-a716-446655440001', 'cc0e8400-e29b-41d4-a716-446655440001', '{"motivation": "A", "learning_style": "A", "subject_preference": "A", "problem_solving": "C", "social_preference": "A"}', '{"hair_color": "blue", "eye_color": "purple", "accessories": ["glasses", "wand"]}'),
('aa0e8400-e29b-41d4-a716-446655440002', 'cc0e8400-e29b-41d4-a716-446655440002', '{"motivation": "C", "learning_style": "C", "subject_preference": "A", "problem_solving": "A", "social_preference": "C"}', '{"hair_color": "brown", "eye_color": "green", "accessories": ["sword", "shield"]}'),
('aa0e8400-e29b-41d4-a716-446655440003', 'cc0e8400-e29b-41d4-a716-446655440003', '{"motivation": "D", "learning_style": "A", "subject_preference": "C", "problem_solving": "C", "social_preference": "A"}', '{"hair_color": "blonde", "eye_color": "blue", "accessories": ["bow", "quiver"]}'),
('aa0e8400-e29b-41d4-a716-446655440004', 'cc0e8400-e29b-41d4-a716-446655440004', '{"motivation": "B", "learning_style": "B", "subject_preference": "B", "problem_solving": "B", "social_preference": "B"}', '{"hair_color": "white", "eye_color": "gold", "accessories": ["staff", "robe"]}'),
('aa0e8400-e29b-41d4-a716-446655440005', 'cc0e8400-e29b-41d4-a716-446655440005', '{"motivation": "E", "learning_style": "E", "subject_preference": "E", "problem_solving": "E", "social_preference": "E"}', '{"hair_color": "black", "eye_color": "red", "accessories": ["dagger", "hood"]}'); 

-- 🌟 EPIC 2: PREGUNTAS REALES DEL ICFES
-- Preguntas diagnósticas para simular exactamente el examen real

-- MATEMÁTICAS (50 preguntas)
INSERT INTO questions (id, topic_id, subject_id, question_text, difficulty, correct_answer, options, explanation, hint, tags) VALUES
-- Álgebra Básica (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440006', '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 
'Si 3x - 2 = 7, ¿cuál es el valor de x?', 1, 'C', 
'{"A": "2", "B": "2.5", "C": "3", "D": "3.5"}',
'3x - 2 = 7 → 3x = 9 → x = 3', 
'Despeja la incógnita x', 
ARRAY['ecuaciones', 'álgebra', 'lineal']),

('dd0e8400-e29b-41d4-a716-446655440007', '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 
'¿Cuál es la solución del sistema: 2x + y = 8, x - y = 1?', 2, 'A', 
'{"A": "(3,2)", "B": "(2,3)", "C": "(4,0)", "D": "(1,6)"}',
'Sumando: 3x = 9 → x = 3. Sustituyendo: 3 - y = 1 → y = 2', 
'Suma las ecuaciones para eliminar y', 
ARRAY['sistemas', 'ecuaciones', 'álgebra']),

('dd0e8400-e29b-41d4-a716-446655440008', '660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 
'¿Cuál es el valor de x en la ecuación: 5x + 3 = 2x + 12?', 2, 'B', 
'{"A": "2", "B": "3", "C": "4", "D": "5"}',
'5x + 3 = 2x + 12 → 3x = 9 → x = 3', 
'Agrupa términos con x en un lado', 
ARRAY['ecuaciones', 'álgebra', 'lineal']),

-- Geometría (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440009', '660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 
'¿Cuál es el área de un círculo con radio 6?', 2, 'C', 
'{"A": "18π", "B": "24π", "C": "36π", "D": "48π"}',
'Área = πr² = π(6)² = 36π', 
'Recuerda la fórmula del área del círculo', 
ARRAY['geometría', 'círculo', 'área']),

('dd0e8400-e29b-41d4-a716-446655440010', '660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 
'En un triángulo rectángulo, si los catetos miden 6 y 8, ¿cuánto mide la hipotenusa?', 1, 'D', 
'{"A": "9", "B": "10", "C": "11", "D": "10"}',
'h² = 6² + 8² = 36 + 64 = 100 → h = 10', 
'Usa el teorema de Pitágoras', 
ARRAY['pitágoras', 'triángulo', 'geometría']),

-- Cálculo (10 preguntas)
('dd0e8400-e29b-41d4-a716-446655440011', '660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 
'¿Cuál es la derivada de f(x) = 3x² + 2x + 1?', 3, 'A', 
'{"A": "6x + 2", "B": "3x + 2", "C": "6x + 1", "D": "3x² + 2"}',
'f''(x) = 6x + 2 (derivada de 3x² es 6x, de 2x es 2, de constante es 0)', 
'Recuerda las reglas de derivación', 
ARRAY['derivadas', 'cálculo', 'polinomios']),

-- Probabilidad (10 preguntas)
('dd0e8400-e29b-41d4-a716-446655440012', '660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440001', 
'¿Cuál es la probabilidad de obtener un número par al lanzar un dado?', 1, 'C', 
'{"A": "1/3", "B": "1/2", "C": "1/2", "D": "2/3"}',
'P(par) = 3/6 = 1/2 (números pares: 2,4,6)', 
'¿Cuántos números pares hay en un dado?', 
ARRAY['probabilidad', 'dado', 'eventos']);

-- LENGUAJE (40 preguntas)
INSERT INTO questions (id, topic_id, subject_id, question_text, difficulty, correct_answer, options, explanation, hint, tags) VALUES
-- Comprensión Lectora (20 preguntas)
('dd0e8400-e29b-41d4-a716-446655440013', '660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 
'¿Cuál es la función principal de un adverbio?', 2, 'B', 
'{"A": "Nombrar objetos", "B": "Modificar verbos", "C": "Conectar oraciones", "D": "Expresar acción"}',
'Los adverbios modifican verbos, adjetivos u otros adverbios', 
'Piensa en palabras como "rápidamente", "muy", "aquí"', 
ARRAY['gramática', 'adverbios', 'sintaxis']),

('dd0e8400-e29b-41d4-a716-446655440014', '660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 
'¿Qué tipo de texto es una novela?', 1, 'A', 
'{"A": "Narrativo", "B": "Expositivo", "C": "Argumentativo", "D": "Descriptivo"}',
'Una novela es un texto narrativo que cuenta una historia', 
'¿Qué hace una novela?', 
ARRAY['literatura', 'géneros', 'texto']),

-- Gramática (10 preguntas)
('dd0e8400-e29b-41d4-a716-446655440015', '660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440002', 
'¿Cuál es la función de un pronombre?', 2, 'C', 
'{"A": "Expresar acción", "B": "Calificar sustantivos", "C": "Reemplazar sustantivos", "D": "Conectar ideas"}',
'Los pronombres reemplazan o sustituyen a los sustantivos', 
'Piensa en palabras como "él", "ella", "nosotros"', 
ARRAY['gramática', 'pronombres', 'sintaxis']),

-- Literatura (10 preguntas)
('dd0e8400-e29b-41d4-a716-446655440016', '660e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440002', 
'¿Qué es una metáfora?', 2, 'A', 
'{"A": "Comparación implícita", "B": "Comparación explícita", "C": "Repetición de sonidos", "D": "Exageración"}',
'La metáfora es una comparación implícita sin usar "como" o "tal como"', 
'Es una figura literaria de comparación', 
ARRAY['literatura', 'figuras', 'metáfora']);

-- CIENCIAS (45 preguntas)
INSERT INTO questions (id, topic_id, subject_id, question_text, difficulty, correct_answer, options, explanation, hint, tags) VALUES
-- Física (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440017', '660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440003', 
'¿Cuál es la fórmula de la energía cinética?', 2, 'B', 
'{"A": "E = mgh", "B": "E = ½mv²", "C": "E = Fd", "D": "E = Pt"}',
'La energía cinética es E = ½mv², donde m es masa y v es velocidad', 
'Es la energía del movimiento', 
ARRAY['física', 'energía', 'cinética']),

('dd0e8400-e29b-41d4-a716-446655440018', '660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440003', 
'¿Qué es la aceleración?', 1, 'C', 
'{"A": "Distancia recorrida", "B": "Velocidad constante", "C": "Cambio de velocidad", "D": "Fuerza aplicada"}',
'La aceleración es el cambio de velocidad en el tiempo', 
'¿Qué mide la aceleración?', 
ARRAY['física', 'movimiento', 'aceleración']),

-- Química (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440019', '660e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440003', 
'¿Cuál es la fórmula del agua?', 1, 'A', 
'{"A": "H₂O", "B": "CO₂", "C": "O₂", "D": "H₂"}',
'El agua es H₂O: dos átomos de hidrógeno y uno de oxígeno', 
'Es la molécula más abundante en la Tierra', 
ARRAY['química', 'moléculas', 'agua']),

-- Biología (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440020', '660e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440003', 
'¿Cuál es la función del núcleo celular?', 2, 'B', 
'{"A": "Producción de energía", "B": "Control genético", "C": "Digestión celular", "D": "Síntesis de proteínas"}',
'El núcleo contiene el ADN y controla las actividades celulares', 
'Es el "cerebro" de la célula', 
ARRAY['biología', 'célula', 'núcleo']);

-- SOCIALES (45 preguntas)
INSERT INTO questions (id, topic_id, subject_id, question_text, difficulty, correct_answer, options, explanation, hint, tags) VALUES
-- Historia (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440021', '660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440004', 
'¿En qué año comenzó la Primera Guerra Mundial?', 2, 'C', 
'{"A": "1912", "B": "1913", "C": "1914", "D": "1915"}',
'La Primera Guerra Mundial comenzó en 1914 con el asesinato del archiduque Francisco Fernando', 
'Fue un conflicto global del siglo XX', 
ARRAY['historia', 'guerra', 'siglo XX']),

-- Geografía (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440022', '660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440004', 
'¿Cuál es la capital de Brasil?', 1, 'B', 
'{"A": "Río de Janeiro", "B": "Brasilia", "C": "São Paulo", "D": "Salvador"}',
'Brasilia es la capital de Brasil desde 1960', 
'Es una ciudad planificada del siglo XX', 
ARRAY['geografía', 'capitales', 'Brasil']),

-- Filosofía (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440023', '660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440004', 
'¿Quién escribió "El Príncipe"?', 2, 'A', 
'{"A": "Maquiavelo", "B": "Platón", "C": "Aristóteles", "D": "Rousseau"}',
'Niccolò Maquiavelo escribió "El Príncipe" en el siglo XVI', 
'Es un tratado de política renacentista', 
ARRAY['filosofía', 'política', 'renacimiento']);

-- INGLÉS (35 preguntas)
INSERT INTO questions (id, topic_id, subject_id, question_text, difficulty, correct_answer, options, explanation, hint, tags) VALUES
-- Comprensión (20 preguntas)
('dd0e8400-e29b-41d4-a716-446655440024', '660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440005', 
'What is the past tense of "go"?', 1, 'B', 
'{"A": "goed", "B": "went", "C": "gone", "D": "goes"}',
'The past tense of "go" is "went" (irregular verb)', 
'Es un verbo irregular', 
ARRAY['inglés', 'verbos', 'pasado']),

('dd0e8400-e29b-41d4-a716-446655440025', '660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440005', 
'Which word is a synonym of "happy"?', 1, 'C', 
'{"A": "sad", "B": "angry", "C": "joyful", "D": "tired"}',
'"Joyful" is a synonym of "happy"', 
'Busca una palabra con significado similar', 
ARRAY['inglés', 'sinónimos', 'vocabulario']),

-- Gramática (15 preguntas)
('dd0e8400-e29b-41d4-a716-446655440026', '660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440005', 
'What is the plural of "child"?', 1, 'B', 
'{"A": "childs", "B": "children", "C": "childes", "D": "childen"}',
'The plural of "child" is "children" (irregular plural)', 
'Es un sustantivo irregular', 
ARRAY['inglés', 'plurales', 'gramática']); 