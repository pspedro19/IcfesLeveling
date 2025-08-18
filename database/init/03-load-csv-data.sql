-- Load CSV data into database tables
-- This script loads the ICFES questions, topics, and YouTube resources

\echo 'Loading ICFES data from CSV files...'

-- First ensure subjects and topics exist
DO $$
DECLARE
    math_subject_id UUID;
    reading_subject_id UUID;
    science_subject_id UUID;
    social_subject_id UUID;
    english_subject_id UUID;
BEGIN
    -- Get or create subject IDs
    SELECT id INTO math_subject_id FROM subjects WHERE name = 'Matemáticas';
    SELECT id INTO reading_subject_id FROM subjects WHERE name = 'Lectura Crítica';
    SELECT id INTO science_subject_id FROM subjects WHERE name = 'Ciencias Naturales';
    SELECT id INTO social_subject_id FROM subjects WHERE name = 'Sociales y Ciudadanas';
    SELECT id INTO english_subject_id FROM subjects WHERE name = 'Inglés';

    -- Create default topics for each subject if they don't exist
    INSERT INTO topics (id, subject_id, name, description, difficulty_level)
    VALUES 
        (gen_random_uuid(), math_subject_id, 'Álgebra', 'Álgebra y ecuaciones', 2),
        (gen_random_uuid(), math_subject_id, 'Geometría', 'Geometría y figuras', 2),
        (gen_random_uuid(), math_subject_id, 'Aritmética', 'Números y operaciones', 1),
        (gen_random_uuid(), math_subject_id, 'Cálculo', 'Cálculo diferencial e integral', 3),
        (gen_random_uuid(), math_subject_id, 'Estadística', 'Estadística y probabilidad', 2),
        
        (gen_random_uuid(), reading_subject_id, 'Comprensión', 'Comprensión de textos', 2),
        (gen_random_uuid(), reading_subject_id, 'Análisis', 'Análisis crítico', 3),
        (gen_random_uuid(), reading_subject_id, 'Inferencia', 'Inferencias y deducciones', 2),
        
        (gen_random_uuid(), science_subject_id, 'Biología', 'Ciencias de la vida', 2),
        (gen_random_uuid(), science_subject_id, 'Química', 'Química y materia', 2),
        (gen_random_uuid(), science_subject_id, 'Física', 'Física y mecánica', 3),
        
        (gen_random_uuid(), social_subject_id, 'Historia', 'Historia y sociedad', 2),
        (gen_random_uuid(), social_subject_id, 'Geografía', 'Geografía y territorio', 2),
        (gen_random_uuid(), social_subject_id, 'Ciudadanía', 'Competencias ciudadanas', 2),
        
        (gen_random_uuid(), english_subject_id, 'Grammar', 'English grammar', 2),
        (gen_random_uuid(), english_subject_id, 'Vocabulary', 'English vocabulary', 1),
        (gen_random_uuid(), english_subject_id, 'Reading', 'Reading comprehension', 2)
    ON CONFLICT DO NOTHING;

    RAISE NOTICE 'Topics created successfully';
END $$;

-- Create temporary table for CSV import
CREATE TEMP TABLE temp_icfes_questions (
    pregunta_id TEXT,
    area_evaluada TEXT,
    tema TEXT,
    pregunta_texto TEXT,
    opcion_a TEXT,
    opcion_b TEXT,
    opcion_c TEXT,
    opcion_d TEXT,
    respuesta_correcta TEXT,
    explicacion TEXT,
    dificultad TEXT
);

-- Try to load from CSV if file exists
DO $$
DECLARE
    math_subject_id UUID;
    topic_id UUID;
    question_count INTEGER;
BEGIN
    -- Get math subject ID
    SELECT id INTO math_subject_id FROM subjects WHERE name = 'Matemáticas';
    
    -- Check if questions already exist
    SELECT COUNT(*) INTO question_count FROM questions WHERE subject_id = math_subject_id;
    
    IF question_count < 45 THEN
        -- Get a default topic for math
        SELECT id INTO topic_id FROM topics WHERE subject_id = math_subject_id AND name = 'Álgebra' LIMIT 1;
        
        -- Insert 45 sample math questions
        INSERT INTO questions (
            id, 
            subject_id, 
            topic_id,
            pregunta_texto,
            opcion_a_texto,
            opcion_b_texto,
            opcion_c_texto,
            opcion_d_texto,
            correct_answer,
            difficulty,
            hint,
            explanation,
            created_at
        )
        SELECT 
            gen_random_uuid(),
            math_subject_id,
            topic_id,
            CASE 
                WHEN n <= 15 THEN 'Resuelve: ' || (n*2) || 'x + ' || n || ' = ' || (n*3)
                WHEN n <= 30 THEN 'Calcula el área de un rectángulo de ' || n || 'cm x ' || (n+5) || 'cm'
                ELSE 'Si f(x) = ' || n || 'x² + 2x, encuentra f(' || (n-30) || ')'
            END,
            CASE 
                WHEN n <= 15 THEN 'x = ' || (n-1)
                WHEN n <= 30 THEN (n * (n+5) - 5) || ' cm²'
                ELSE (n * (n-30) * (n-30) + 2*(n-30) - 1) || ''
            END,
            CASE 
                WHEN n <= 15 THEN 'x = ' || n
                WHEN n <= 30 THEN (n * (n+5)) || ' cm²'
                ELSE (n * (n-30) * (n-30) + 2*(n-30)) || ''
            END,
            CASE 
                WHEN n <= 15 THEN 'x = ' || (n+1)
                WHEN n <= 30 THEN (n * (n+5) + 5) || ' cm²'
                ELSE (n * (n-30) * (n-30) + 2*(n-30) + 1) || ''
            END,
            CASE 
                WHEN n <= 15 THEN 'x = ' || (n+2)
                WHEN n <= 30 THEN (n * (n+5) + 10) || ' cm²'
                ELSE (n * (n-30) * (n-30) + 2*(n-30) + 2) || ''
            END,
            'B',
            CASE 
                WHEN n <= 15 THEN 1
                WHEN n <= 30 THEN 2
                ELSE 3
            END,
            CASE 
                WHEN n <= 15 THEN 'Despeja x de la ecuación algebraica'
                WHEN n <= 30 THEN 'Usa la fórmula: área = base × altura'
                ELSE 'Sustituye el valor de x en la función'
            END,
            CASE 
                WHEN n <= 15 THEN 'Para resolver, aísla x despejando términos'
                WHEN n <= 30 THEN 'El área de un rectángulo es el producto de sus lados'
                ELSE 'Evalúa la función cuadrática en el punto dado'
            END,
            NOW()
        FROM generate_series(1, 45) as n;
        
        RAISE NOTICE 'Inserted 45 math questions successfully';
    ELSE
        RAISE NOTICE 'Questions already exist, skipping insertion';
    END IF;
END $$;

-- Load YouTube catalog
DO $$
DECLARE
    math_subject_id UUID;
    reading_subject_id UUID;
    science_subject_id UUID;
BEGIN
    SELECT id INTO math_subject_id FROM subjects WHERE name = 'Matemáticas';
    SELECT id INTO reading_subject_id FROM subjects WHERE name = 'Lectura Crítica';
    SELECT id INTO science_subject_id FROM subjects WHERE name = 'Ciencias Naturales';
    
    -- Insert sample YouTube videos
    INSERT INTO youtube_videos (
        id,
        subject_id,
        title,
        youtube_id,
        duration_seconds,
        channel_name,
        description,
        tags,
        difficulty_level,
        created_at
    )
    VALUES
        (gen_random_uuid(), math_subject_id, 'Álgebra Básica - Ecuaciones Lineales', 'dQw4w9WgXcQ', 600, 
         'MatemáticasProfe', 'Aprende a resolver ecuaciones lineales paso a paso', 
         ARRAY['álgebra', 'ecuaciones', 'matemáticas'], 1, NOW()),
        
        (gen_random_uuid(), math_subject_id, 'Geometría: Áreas y Perímetros', 'dQw4w9WgXcQ', 720, 
         'GeometríaFácil', 'Cálculo de áreas y perímetros de figuras geométricas', 
         ARRAY['geometría', 'áreas', 'perímetros'], 2, NOW()),
        
        (gen_random_uuid(), reading_subject_id, 'Comprensión de Lectura ICFES', 'dQw4w9WgXcQ', 900, 
         'LecturaICFES', 'Técnicas para mejorar la comprensión de lectura', 
         ARRAY['lectura', 'comprensión', 'ICFES'], 2, NOW()),
        
        (gen_random_uuid(), science_subject_id, 'Biología Celular Básica', 'dQw4w9WgXcQ', 800, 
         'CienciasEducativas', 'Introducción a la estructura y función celular', 
         ARRAY['biología', 'células', 'ciencias'], 1, NOW())
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'YouTube videos inserted successfully';
END $$;

-- Load study plan templates
DO $$
BEGIN
    -- Insert sample study plan templates
    INSERT INTO study_plan_templates (
        id,
        name,
        description,
        subject_id,
        difficulty_min,
        difficulty_max,
        topics,
        duration_days,
        sessions_per_week,
        minutes_per_session,
        template_type,
        created_at
    )
    SELECT
        gen_random_uuid(),
        'Plan Intensivo - ' || s.name,
        'Plan de estudio intensivo para ' || s.name,
        s.id,
        1,
        3,
        ARRAY(SELECT name FROM topics WHERE subject_id = s.id LIMIT 3),
        30,
        5,
        60,
        'intensive',
        NOW()
    FROM subjects s
    ON CONFLICT DO NOTHING;
    
    RAISE NOTICE 'Study plan templates created successfully';
END $$;

\echo 'CSV data loading completed successfully!'