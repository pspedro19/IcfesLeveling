-- Insert subjects if they don't exist
INSERT INTO subjects (id, name, description, icon, color) VALUES
    ('11111111-1111-1111-1111-111111111111', 'Matemáticas', 'Razonamiento cuantitativo y matemático', '🔢', '#FF6B6B'),
    ('22222222-2222-2222-2222-222222222222', 'Lenguaje', 'Comprensión lectora y comunicación escrita', '📚', '#4ECDC4'),
    ('33333333-3333-3333-3333-333333333333', 'Ciencias Naturales', 'Física, Química y Biología', '🔬', '#95E77E'),
    ('44444444-4444-4444-4444-444444444444', 'Ciencias Sociales', 'Historia, Geografía y Competencias Ciudadanas', '🌍', '#FFE66D'),
    ('55555555-5555-5555-5555-555555555555', 'Inglés', 'Comprensión y uso del idioma inglés', '🌐', '#A8E6CF')
ON CONFLICT (id) DO NOTHING;

-- Insert topics for Matemáticas
INSERT INTO topics (id, subject_id, name, description, difficulty, "order") VALUES
    ('a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 'Álgebra Básica', 'Conceptos básicos de álgebra', 1, 1),
    ('a2222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111', 'Geometría Euclidiana', 'Geometría plana y espacial', 1, 2),
    ('a3333333-3333-3333-3333-333333333333', '11111111-1111-1111-1111-111111111111', 'Cálculo Diferencial', 'Derivadas y aplicaciones', 2, 3),
    ('a4444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111', 'Probabilidad', 'Teoría de probabilidades', 2, 4),
    ('a5555555-5555-5555-5555-555555555555', '11111111-1111-1111-1111-111111111111', 'Estadística', 'Análisis estadístico', 2, 5)
ON CONFLICT (id) DO NOTHING;

-- Clear existing questions
DELETE FROM questions;

-- Insert sample questions for Matemáticas (45 questions)
INSERT INTO questions (id, topic_id, subject_id, pregunta_texto, opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto, respuesta_correcta, question_text, question_type, difficulty, options, correct_answer, explanation, hint) VALUES
    ('q1111111-1111-1111-1111-111111111111', 'a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111', 
     '¿Cuál es el resultado de 2x + 3 = 11?', 'x = 3', 'x = 4', 'x = 5', 'x = 6', 'B',
     '¿Cuál es el resultado de 2x + 3 = 11?', 'multiple_choice', 1, 
     '{"A": "x = 3", "B": "x = 4", "C": "x = 5", "D": "x = 6"}', 'B', 
     'Restando 3 de ambos lados: 2x = 8, luego x = 4', 'Despeja x aislándola'),
    
    ('q2222222-2222-2222-2222-222222222222', 'a2222222-2222-2222-2222-222222222222', '11111111-1111-1111-1111-111111111111',
     '¿Cuál es el área de un triángulo con base 6cm y altura 8cm?', '24 cm²', '48 cm²', '14 cm²', '32 cm²', 'A',
     '¿Cuál es el área de un triángulo con base 6cm y altura 8cm?', 'multiple_choice', 1,
     '{"A": "24 cm²", "B": "48 cm²", "C": "14 cm²", "D": "32 cm²"}', 'A',
     'Área = (base × altura) / 2 = (6 × 8) / 2 = 24 cm²', 'Usa la fórmula del área del triángulo'),
    
    ('q3333333-3333-3333-3333-333333333333', 'a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111',
     'Si f(x) = 2x² + 3x - 1, ¿cuál es f(2)?', '9', '11', '13', '15', 'C',
     'Si f(x) = 2x² + 3x - 1, ¿cuál es f(2)?', 'multiple_choice', 2,
     '{"A": "9", "B": "11", "C": "13", "D": "15"}', 'C',
     'f(2) = 2(2)² + 3(2) - 1 = 8 + 6 - 1 = 13', 'Sustituye x = 2 en la función'),
    
    ('q4444444-4444-4444-4444-444444444444', 'a4444444-4444-4444-4444-444444444444', '11111111-1111-1111-1111-111111111111',
     '¿Cuál es la probabilidad de obtener un número par al lanzar un dado?', '1/6', '1/3', '1/2', '2/3', 'C',
     '¿Cuál es la probabilidad de obtener un número par al lanzar un dado?', 'multiple_choice', 1,
     '{"A": "1/6", "B": "1/3", "C": "1/2", "D": "2/3"}', 'C',
     'Los números pares son 2, 4, 6 (3 de 6 posibles) = 3/6 = 1/2', 'Cuenta los casos favorables'),
    
    ('q5555555-5555-5555-5555-555555555555', 'a1111111-1111-1111-1111-111111111111', '11111111-1111-1111-1111-111111111111',
     'Resuelve: 3(x - 2) = 2(x + 1)', 'x = 8', 'x = 6', 'x = 4', 'x = 2', 'A',
     'Resuelve: 3(x - 2) = 2(x + 1)', 'multiple_choice', 2,
     '{"A": "x = 8", "B": "x = 6", "C": "x = 4", "D": "x = 2"}', 'A',
     '3x - 6 = 2x + 2, entonces x = 8', 'Distribuye y agrupa términos semejantes');

-- Add more questions (40 more to complete 45)
INSERT INTO questions (id, topic_id, subject_id, pregunta_texto, opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto, respuesta_correcta, question_text, question_type, difficulty, options, correct_answer, explanation, hint) 
SELECT 
    gen_random_uuid(),
    'a1111111-1111-1111-1111-111111111111',
    '11111111-1111-1111-1111-111111111111',
    'Pregunta de matemáticas ' || generate_series,
    'Opción A',
    'Opción B',
    'Opción C',
    'Opción D',
    CASE (generate_series % 4) WHEN 0 THEN 'A' WHEN 1 THEN 'B' WHEN 2 THEN 'C' ELSE 'D' END,
    'Pregunta de matemáticas ' || generate_series,
    'multiple_choice',
    (generate_series % 3) + 1,
    '{"A": "Opción A", "B": "Opción B", "C": "Opción C", "D": "Opción D"}',
    CASE (generate_series % 4) WHEN 0 THEN 'A' WHEN 1 THEN 'B' WHEN 2 THEN 'C' ELSE 'D' END,
    'Explicación de la respuesta',
    'Pista para resolver'
FROM generate_series(6, 45);