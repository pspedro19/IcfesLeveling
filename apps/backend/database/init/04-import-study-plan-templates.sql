-- ICFES LEVELING - Importación de plantillas de planes de estudio
-- Este script crea plantillas base para generar planes de estudio personalizados

-- Crear tabla para plantillas de planes de estudio si no existe
CREATE TABLE IF NOT EXISTS study_plan_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    subject_id UUID REFERENCES subjects(id) ON DELETE CASCADE,
    unit_number INTEGER NOT NULL,
    unit_name VARCHAR(200) NOT NULL,
    unit_description TEXT,
    topics TEXT[], -- Array de temas
    video_urls JSONB, -- URLs de videos de YouTube por tema
    exercise_count INTEGER DEFAULT 15, -- Número de ejercicios por unidad
    reading_materials JSONB, -- Enlaces a material de lectura
    recommendations_priority VARCHAR(10) DEFAULT 'medium',
    weak_areas TEXT[],
    focus_topics TEXT[],
    study_time VARCHAR(50),
    difficulty_level INTEGER DEFAULT 2,
    icfes_weight DECIMAL(3,2) DEFAULT 0.25,
    estimated_hours INTEGER DEFAULT 4,
    prerequisite_units INTEGER[], -- Unidades prerequisito
    learning_objectives TEXT[], -- Objetivos de aprendizaje
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejor rendimiento
CREATE INDEX IF NOT EXISTS idx_study_plan_templates_subject ON study_plan_templates(subject_id);
CREATE INDEX IF NOT EXISTS idx_study_plan_templates_unit ON study_plan_templates(subject_id, unit_number);

-- Insertar plantillas de Matemáticas con videos de YouTube
INSERT INTO study_plan_templates (
    subject_id, unit_number, unit_name, unit_description, topics, video_urls, exercise_count, 
    reading_materials, recommendations_priority, weak_areas, focus_topics, study_time, 
    difficulty_level, icfes_weight, estimated_hours, prerequisite_units, learning_objectives
) VALUES
-- Matemáticas
('550e8400-e29b-41d4-a716-446655440001', 1, 'Fundamentos Algebraicos', 'Domina las bases del álgebra necesarias para el ICFES', 
 ARRAY['Ecuaciones lineales', 'Sistemas de ecuaciones', 'Inecuaciones', 'Factorización'], 
 '{"Ecuaciones lineales": "https://www.youtube.com/watch?v=lGp_8-jAYI4", "Sistemas de ecuaciones": "https://www.youtube.com/watch?v=AuWaC5ORE3M", "Inecuaciones": "https://www.youtube.com/watch?v=HrPGPITLZFY", "Factorización": "https://www.youtube.com/watch?v=IODmjGQFp6Y"}'::jsonb,
 20,
 '{"Khan Academy Álgebra": "https://es.khanacademy.org/math/algebra", "Ejercicios adicionales": "https://www.coursera.org/learn/algebra-basica"}'::jsonb,
 'high', 
 ARRAY['ecuaciones básicas', 'despeje de variables'], ARRAY['álgebra básica', 'ecuaciones'], '3-4 horas', 1, 0.30, 4,
 ARRAY[]::integer[], ARRAY['Resolver ecuaciones lineales de primer grado', 'Aplicar métodos de resolución de sistemas', 'Interpretar soluciones algebraicas']),

('550e8400-e29b-41d4-a716-446655440001', 2, 'Geometría y Trigonometría', 'Aplica conceptos geométricos y trigonométricos', 
 ARRAY['Triángulos', 'Círculos', 'Teorema de Pitágoras', 'Funciones trigonométricas'], 
 '{"Triángulos": "https://www.youtube.com/watch?v=h1x76R-sJY8", "Círculos": "https://www.youtube.com/watch?v=XW2_F-K4gJw", "Teorema de Pitágoras": "https://www.youtube.com/watch?v=c_nOX4TSEts", "Funciones trigonométricas": "https://www.youtube.com/watch?v=PUB0TaZ7bhA"}'::jsonb,
 25,
 '{"Khan Academy Geometría": "https://es.khanacademy.org/math/geometry", "Trigonometría básica": "https://www.coursera.org/learn/trigonometry"}'::jsonb,
 'medium', 
 ARRAY['área y perímetro', 'ángulos'], ARRAY['geometría', 'trigonometría'], '4-5 horas', 2, 0.25, 5,
 ARRAY[1], ARRAY['Aplicar el teorema de Pitágoras', 'Calcular áreas y perímetros', 'Resolver problemas trigonométricos básicos']),

('550e8400-e29b-41d4-a716-446655440001', 3, 'Funciones y Gráficas', 'Interpreta y analiza funciones matemáticas', 
 ARRAY['Funciones lineales', 'Funciones cuadráticas', 'Gráficas', 'Dominios'], 
 '{"Funciones lineales": "https://www.youtube.com/watch?v=xnR-PSgQT8c", "Funciones cuadráticas": "https://www.youtube.com/watch?v=VSnpgYHq_jg", "Gráficas": "https://www.youtube.com/watch?v=i4VqXRRXi68", "Dominios": "https://www.youtube.com/watch?v=lFtFu9wYYb8"}'::jsonb,
 22,
 '{"Khan Academy Funciones": "https://es.khanacademy.org/math/algebra2/x2ec2f6f830c9fb89:functions", "Graficación en línea": "https://www.desmos.com/calculator"}'::jsonb,
 'medium', 
 ARRAY['interpretación gráfica', 'dominios'], ARRAY['funciones', 'análisis gráfico'], '3-4 horas', 3, 0.20, 4,
 ARRAY[1], ARRAY['Interpretar gráficas de funciones', 'Determinar dominios y rangos', 'Analizar comportamiento de funciones']),

('550e8400-e29b-41d4-a716-446655440001', 4, 'Estadística y Probabilidad', 'Analiza datos y calcula probabilidades', 
 ARRAY['Medidas de tendencia', 'Probabilidad básica', 'Combinatoria', 'Distribuciones'], 
 '{"Medidas de tendencia": "https://www.youtube.com/watch?v=eJu_b37yWXQ", "Probabilidad básica": "https://www.youtube.com/watch?v=uzkc-qNVoOk", "Combinatoria": "https://www.youtube.com/watch?v=DROZVHObeko", "Distribuciones": "https://www.youtube.com/watch?v=oAZPfnWJh3A"}'::jsonb,
 30,
 '{"Khan Academy Estadística": "https://es.khanacademy.org/math/statistics-probability", "Ejercicios probabilidad": "https://www.khanacademy.org/math/probability"}'::jsonb,
 'high', 
 ARRAY['interpretación estadística', 'probabilidad'], ARRAY['estadística', 'análisis de datos'], '4-5 horas', 2, 0.25, 5,
 ARRAY[1, 2], ARRAY['Calcular medidas de tendencia central', 'Resolver problemas de probabilidad', 'Interpretar datos estadísticos']),

-- Lenguaje
('550e8400-e29b-41d4-a716-446655440002', 1, 'Comprensión Lectora Básica', 'Desarrolla habilidades de comprensión de textos', 
 ARRAY['Idea principal', 'Ideas secundarias', 'Estructura textual', 'Vocabulario'], 
 '{"Idea principal": "https://www.youtube.com/watch?v=8YDP6YKRs0k", "Ideas secundarias": "https://www.youtube.com/watch?v=HGF5xDdWSHo", "Estructura textual": "https://www.youtube.com/watch?v=TJ9KYCJOCvI", "Vocabulario": "https://www.youtube.com/watch?v=KjZjVW7GxOU"}'::jsonb,
 18,
 '{"Khan Academy Lectura": "https://es.khanacademy.org/humanities/grammar", "Ejercicios comprensión": "https://www.coursera.org/learn/spanish-reading"}'::jsonb,
 'high', 
 ARRAY['identificación de ideas', 'vocabulario'], ARRAY['comprensión', 'lectura crítica'], '3-4 horas', 1, 0.35, 4,
 ARRAY[]::integer[], ARRAY['Identificar la idea principal de textos', 'Analizar estructura textual', 'Ampliar vocabulario académico']),

('550e8400-e29b-41d4-a716-446655440002', 2, 'Análisis Textual', 'Analiza diferentes tipos de textos', 
 ARRAY['Textos narrativos', 'Textos expositivos', 'Textos argumentativos', 'Cohesión'], 'medium', 
 ARRAY['estructura textual', 'coherencia'], ARRAY['análisis', 'tipología textual'], '4-5 horas', 2, 0.30, 5),

('550e8400-e29b-41d4-a716-446655440002', 3, 'Competencia Comunicativa', 'Mejora la expresión y comunicación', 
 ARRAY['Gramática', 'Sintaxis', 'Semántica', 'Pragmática'], 'medium', 
 ARRAY['uso del lenguaje', 'contexto'], ARRAY['comunicación', 'expresión'], '3-4 horas', 2, 0.20, 4),

('550e8400-e29b-41d4-a716-446655440002', 4, 'Literatura y Cultura', 'Conoce literatura y contextos culturales', 
 ARRAY['Géneros literarios', 'Movimientos', 'Autores', 'Contexto histórico'], 'low', 
 ARRAY['interpretación literaria', 'contexto'], ARRAY['literatura', 'cultura'], '2-3 horas', 3, 0.15, 3),

-- Ciencias Naturales
('550e8400-e29b-41d4-a716-446655440003', 1, 'Mecánica y Movimiento', 'Comprende las leyes del movimiento', 
 ARRAY['Cinemática', 'Dinámica', 'Trabajo y energía', 'Momentum'], 'high', 
 ARRAY['fuerzas', 'movimiento'], ARRAY['física', 'mecánica'], '4-5 horas', 2, 0.30, 5),

('550e8400-e29b-41d4-a716-446655440003', 2, 'Termodinámica y Ondas', 'Estudia calor, temperatura y ondas', 
 ARRAY['Calor', 'Temperatura', 'Ondas mecánicas', 'Sonido'], 'medium', 
 ARRAY['transferencia de calor', 'ondas'], ARRAY['termodinámica', 'acústica'], '3-4 horas', 2, 0.25, 4),

('550e8400-e29b-41d4-a716-446655440003', 3, 'Química Fundamental', 'Domina conceptos químicos básicos', 
 ARRAY['Átomos', 'Moléculas', 'Reacciones', 'Tabla periódica'], 'high', 
 ARRAY['estructura atómica', 'reacciones'], ARRAY['química', 'enlaces'], '4-5 horas', 2, 0.25, 5),

('550e8400-e29b-41d4-a716-446655440003', 4, 'Biología Celular', 'Conoce la vida a nivel celular', 
 ARRAY['Célula', 'Organelos', 'Metabolismo', 'Genética'], 'medium', 
 ARRAY['función celular', 'herencia'], ARRAY['biología', 'genética'], '3-4 horas', 2, 0.20, 4),

-- Ciencias Sociales
('550e8400-e29b-41d4-a716-446655440004', 1, 'Historia Universal', 'Comprende procesos históricos mundiales', 
 ARRAY['Edad Media', 'Renacimiento', 'Revoluciones', 'Guerras mundiales'], 'medium', 
 ARRAY['cronología', 'causas y efectos'], ARRAY['historia', 'procesos'], '3-4 horas', 2, 0.25, 4),

('550e8400-e29b-41d4-a716-446655440004', 2, 'Historia de Colombia', 'Conoce la historia nacional', 
 ARRAY['Conquista', 'Independencia', 'República', 'Siglo XX'], 'high', 
 ARRAY['procesos de independencia', 'violencia'], ARRAY['historia nacional', 'identidad'], '4-5 horas', 2, 0.30, 5),

('550e8400-e29b-41d4-a716-446655440004', 3, 'Geografía y Territorio', 'Analiza espacios geográficos', 
 ARRAY['Geografía física', 'Población', 'Economía', 'Medio ambiente'], 'medium', 
 ARRAY['ubicación espacial', 'recursos'], ARRAY['geografía', 'territorio'], '3-4 horas', 2, 0.25, 4),

('550e8400-e29b-41d4-a716-446655440004', 4, 'Filosofía y Pensamiento', 'Desarrolla pensamiento crítico', 
 ARRAY['Filosofía antigua', 'Moderna', 'Ética', 'Lógica'], 'low', 
 ARRAY['argumentación', 'pensamiento crítico'], ARRAY['filosofía', 'ética'], '2-3 horas', 3, 0.20, 3),

-- Inglés
('550e8400-e29b-41d4-a716-446655440005', 1, 'Grammar Fundamentals', 'Master basic English grammar', 
 ARRAY['Verb tenses', 'Articles', 'Prepositions', 'Pronouns'], 'high', 
 ARRAY['verb conjugation', 'sentence structure'], ARRAY['grammar', 'basics'], '3-4 horas', 1, 0.30, 4),

('550e8400-e29b-41d4-a716-446655440005', 2, 'Reading Comprehension', 'Improve reading skills', 
 ARRAY['Reading strategies', 'Vocabulary', 'Main ideas', 'Inference'], 'high', 
 ARRAY['vocabulary', 'comprehension'], ARRAY['reading', 'understanding'], '4-5 horas', 2, 0.35, 5),

('550e8400-e29b-41d4-a716-446655440005', 3, 'Communication Skills', 'Develop communication abilities', 
 ARRAY['Speaking', 'Listening', 'Conversation', 'Pronunciation'], 'medium', 
 ARRAY['oral expression', 'listening'], ARRAY['communication', 'speaking'], '3-4 horas', 2, 0.25, 4),

('550e8400-e29b-41d4-a716-446655440005', 4, 'Writing and Culture', 'Learn writing and cultural aspects', 
 ARRAY['Writing skills', 'Cultural context', 'Literature', 'Expressions'], 'low', 
 ARRAY['written expression', 'culture'], ARRAY['writing', 'culture'], '2-3 horas', 3, 0.10, 3)

ON CONFLICT DO NOTHING;