-- Load sample ICFES questions for testing
-- This ensures we have some data to work with

-- Clear existing questions
DELETE FROM questions;

-- Insert sample questions with proper image paths
INSERT INTO questions (
    id, subject_id, question_text, correct_answer, 
    options, difficulty, pregunta_texto, respuesta_correcta,
    opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
    parametro_irt_a, parametro_irt_b, parametro_irt_c,
    created_at
) VALUES 
-- Matemáticas questions
(
    gen_random_uuid(), 
    '550e8400-e29b-41d4-a716-446655440001',
    '¿Cuál es el resultado de 2x + 3 = 11?',
    'D',
    '{"A": "x = 2", "B": "x = 3", "C": "x = 5", "D": "x = 4"}',
    3,
    '¿Cuál es el resultado de 2x + 3 = 11?',
    'D',
    'x = 2', 'x = 3', 'x = 5', 'x = 4',
    1.2, 0.5, 0.25,
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440001', 
    'Si un triángulo tiene lados de 3, 4 y 5 unidades, ¿qué tipo de triángulo es?',
    'B',
    '{"A": "Equilátero", "B": "Rectángulo", "C": "Isósceles", "D": "Escaleno"}',
    5,
    'Si un triángulo tiene lados de 3, 4 y 5 unidades, ¿qué tipo de triángulo es?',
    'B',
    'Equilátero', 'Rectángulo', 'Isósceles', 'Escaleno',
    1.0, 0.0, 0.25,
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440001',
    'La derivada de f(x) = x² es:',
    'A',
    '{"A": "2x", "B": "x²", "C": "x", "D": "2"}',
    6,
    'La derivada de f(x) = x² es:',
    'A',
    '2x', 'x²', 'x', '2',
    1.5, 1.0, 0.2,
    NOW()
),
-- Ciencias Naturales questions
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440003',
    '¿Cuál es la unidad básica de la vida?',
    'C',
    '{"A": "Átomo", "B": "Molécula", "C": "Célula", "D": "Tejido"}',
    2,
    '¿Cuál es la unidad básica de la vida?',
    'C',
    'Átomo', 'Molécula', 'Célula', 'Tejido',
    0.8, -0.5, 0.25,
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440003',
    'El proceso por el cual las plantas producen su alimento se llama:',
    'B',
    '{"A": "Respiración", "B": "Fotosíntesis", "C": "Digestión", "D": "Fermentación"}',
    3,
    'El proceso por el cual las plantas producen su alimento se llama:',
    'B',
    'Respiración', 'Fotosíntesis', 'Digestión', 'Fermentación',
    1.1, 0.2, 0.25,
    NOW()
),
-- Lenguaje questions
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440002',
    '¿Cuál es el sujeto en la oración "María lee un libro"?',
    'A',
    '{"A": "María", "B": "lee", "C": "un libro", "D": "libro"}',
    2,
    '¿Cuál es el sujeto en la oración "María lee un libro"?',
    'A',
    'María', 'lee', 'un libro', 'libro',
    0.9, -0.3, 0.25,
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440002',
    'El género literario que narra hechos ficticios es:',
    'C',
    '{"A": "Lírico", "B": "Dramático", "C": "Narrativo", "D": "Didáctico"}',
    4,
    'El género literario que narra hechos ficticios es:',
    'C',
    'Lírico', 'Dramático', 'Narrativo', 'Didáctico',
    1.3, 0.7, 0.2,
    NOW()
),
-- Ciencias Sociales questions
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440004',
    '¿En qué año llegó Cristóbal Colón a América?',
    'B',
    '{"A": "1490", "B": "1492", "C": "1500", "D": "1485"}',
    3,
    '¿En qué año llegó Cristóbal Colón a América?',
    'B',
    '1490', '1492', '1500', '1485',
    1.0, 0.0, 0.25,
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440004',
    'La capital de Colombia es:',
    'D',
    '{"A": "Medellín", "B": "Cali", "C": "Barranquilla", "D": "Bogotá"}',
    1,
    'La capital de Colombia es:',
    'D',
    'Medellín', 'Cali', 'Barranquilla', 'Bogotá',
    0.7, -1.0, 0.25,
    NOW()
),
-- Inglés questions
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440005',
    'What is the past tense of "go"?',
    'C',
    '{"A": "goed", "B": "gone", "C": "went", "D": "going"}',
    2,
    'What is the past tense of "go"?',
    'C',
    'goed', 'gone', 'went', 'going',
    0.9, -0.2, 0.25,
    NOW()
);

-- Add more variety with different difficulty levels
INSERT INTO questions (
    id, subject_id, question_text, correct_answer,
    options, difficulty, pregunta_texto, respuesta_correcta,
    opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
    parametro_irt_a, parametro_irt_b, parametro_irt_c,
    competencia, componente, proceso_cognitivo,
    created_at
) VALUES
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440001',
    'Si log₂(x) = 3, entonces x es igual a:',
    'C',
    '{"A": "6", "B": "9", "C": "8", "D": "5"}',
    7,
    'Si log₂(x) = 3, entonces x es igual a:',
    'C',
    '6', '9', '8', '5',
    1.8, 1.5, 0.2,
    'Razonamiento', 'Numérico-variacional', 'Análisis',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440001',
    'El área de un círculo con radio 5 cm es:',
    'B',
    '{"A": "25 cm²", "B": "25π cm²", "C": "10π cm²", "D": "50 cm²"}',
    4,
    'El área de un círculo con radio 5 cm es:',
    'B',
    '25 cm²', '25π cm²', '10π cm²', '50 cm²',
    1.2, 0.3, 0.25,
    'Formulación y ejecución', 'Espacial-métrico', 'Aplicación',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440003',
    'La ley de conservación de la energía establece que:',
    'A',
    '{"A": "La energía no se crea ni se destruye", "B": "La energía siempre aumenta", "C": "La energía se pierde como calor", "D": "La energía es constante en sistemas abiertos"}',
    5,
    'La ley de conservación de la energía establece que:',
    'A',
    'La energía no se crea ni se destruye', 'La energía siempre aumenta', 'La energía se pierde como calor', 'La energía es constante en sistemas abiertos',
    1.4, 0.8, 0.2,
    'Uso del conocimiento', 'Entorno físico', 'Comprensión',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440003',
    'El ADN está compuesto por:',
    'D',
    '{"A": "Aminoácidos", "B": "Lípidos", "C": "Carbohidratos", "D": "Nucleótidos"}',
    6,
    'El ADN está compuesto por:',
    'D',
    'Aminoácidos', 'Lípidos', 'Carbohidratos', 'Nucleótidos',
    1.5, 1.2, 0.25,
    'Explicación de fenómenos', 'Entorno vivo', 'Conocimiento',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440002',
    'Identifica la figura literaria en: "Sus ojos son dos luceros"',
    'B',
    '{"A": "Hipérbole", "B": "Metáfora", "C": "Símil", "D": "Personificación"}',
    5,
    'Identifica la figura literaria en: "Sus ojos son dos luceros"',
    'B',
    'Hipérbole', 'Metáfora', 'Símil', 'Personificación',
    1.3, 0.6, 0.25,
    'Interpretación', 'Comprensión e interpretación textual', 'Análisis',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440004',
    'El Renacimiento se caracterizó por:',
    'A',
    '{"A": "El humanismo y el arte clásico", "B": "La industrialización", "C": "El feudalismo", "D": "La conquista de América"}',
    6,
    'El Renacimiento se caracterizó por:',
    'A',
    'El humanismo y el arte clásico', 'La industrialización', 'El feudalismo', 'La conquista de América',
    1.4, 1.0, 0.2,
    'Interpretación y análisis', 'El tiempo y las culturas', 'Comprensión',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440001',
    'La probabilidad de obtener un 6 al lanzar un dado es:',
    'C',
    '{"A": "1/2", "B": "1/3", "C": "1/6", "D": "1/4"}',
    3,
    'La probabilidad de obtener un 6 al lanzar un dado es:',
    'C',
    '1/2', '1/3', '1/6', '1/4',
    1.0, 0.0, 0.25,
    'Razonamiento', 'Aleatorio', 'Aplicación',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440003',
    'La velocidad de la luz en el vacío es aproximadamente:',
    'B',
    '{"A": "300 km/s", "B": "300,000 km/s", "C": "3,000 km/s", "D": "30,000 km/s"}',
    4,
    'La velocidad de la luz en el vacío es aproximadamente:',
    'B',
    '300 km/s', '300,000 km/s', '3,000 km/s', '30,000 km/s',
    1.1, 0.4, 0.25,
    'Uso del conocimiento', 'Entorno físico', 'Conocimiento',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440002',
    'El autor de "Cien años de soledad" es:',
    'D',
    '{"A": "Pablo Neruda", "B": "Jorge Luis Borges", "C": "Mario Vargas Llosa", "D": "Gabriel García Márquez"}',
    2,
    'El autor de "Cien años de soledad" es:',
    'D',
    'Pablo Neruda', 'Jorge Luis Borges', 'Mario Vargas Llosa', 'Gabriel García Márquez',
    0.8, -0.5, 0.25,
    'Reflexión', 'Literatura', 'Conocimiento',
    NOW()
),
(
    gen_random_uuid(),
    '550e8400-e29b-41d4-a716-446655440005',
    'Choose the correct form: "She ___ to school every day"',
    'A',
    '{"A": "goes", "B": "go", "C": "going", "D": "gone"}',
    3,
    'Choose the correct form: "She ___ to school every day"',
    'A',
    'goes', 'go', 'going', 'gone',
    1.0, 0.0, 0.25,
    'Competencia lingüística', 'Gramática', 'Aplicación',
    NOW()
);

-- Verify insertion
SELECT 
    s.name as subject,
    COUNT(q.id) as question_count
FROM subjects s
LEFT JOIN questions q ON s.id = q.subject_id
GROUP BY s.name
ORDER BY question_count DESC;