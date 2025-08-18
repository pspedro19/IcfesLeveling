-- ICFES LEVELING - Inicialización rápida de plantillas adaptativas
-- Este script crea plantillas simplificadas si no existen en la BD

-- Verificar si ya existen plantillas
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM study_plan_templates) = 0 THEN
        -- Insertar plantillas básicas para todas las materias
        
        -- Matemáticas (4 unidades)
        INSERT INTO study_plan_templates (
            subject_id, unit_number, unit_name, unit_description, topics, video_urls, exercise_count, 
            reading_materials, recommendations_priority, weak_areas, focus_topics, study_time, 
            difficulty_level, icfes_weight, estimated_hours, prerequisite_units, learning_objectives
        ) VALUES
        ('550e8400-e29b-41d4-a716-446655440001', 1, 'Álgebra Básica', 'Fundamentos algebraicos para ICFES', 
         ARRAY['Ecuaciones lineales', 'Sistemas de ecuaciones', 'Factorización'], 
         '{"Ecuaciones lineales": "https://www.youtube.com/watch?v=lGp_8-jAYI4", "Sistemas de ecuaciones": "https://www.youtube.com/watch?v=AuWaC5ORE3M", "Factorización": "https://www.youtube.com/watch?v=IODmjGQFp6Y"}'::jsonb,
         15, '{"Khan Academy": "https://es.khanacademy.org/math/algebra"}'::jsonb, 'high', 
         ARRAY['ecuaciones básicas'], ARRAY['álgebra'], '3-4 horas', 1, 0.30, 4, ARRAY[]::integer[], 
         ARRAY['Resolver ecuaciones lineales', 'Aplicar métodos algebraicos']),
         
        ('550e8400-e29b-41d4-a716-446655440001', 2, 'Geometría', 'Conceptos geométricos esenciales', 
         ARRAY['Triángulos', 'Círculos', 'Áreas y perímetros'], 
         '{"Triángulos": "https://www.youtube.com/watch?v=h1x76R-sJY8", "Círculos": "https://www.youtube.com/watch?v=XW2_F-K4gJw"}'::jsonb,
         18, '{"Khan Academy Geometría": "https://es.khanacademy.org/math/geometry"}'::jsonb, 'medium', 
         ARRAY['cálculo de áreas'], ARRAY['geometría'], '4-5 horas', 2, 0.25, 5, ARRAY[1], 
         ARRAY['Calcular áreas y perímetros', 'Aplicar teoremas geométricos']),
         
        ('550e8400-e29b-41d4-a716-446655440001', 3, 'Funciones', 'Análisis de funciones matemáticas', 
         ARRAY['Funciones lineales', 'Funciones cuadráticas', 'Gráficas'], 
         '{"Funciones lineales": "https://www.youtube.com/watch?v=xnR-PSgQT8c", "Gráficas": "https://www.youtube.com/watch?v=i4VqXRRXi68"}'::jsonb,
         20, '{"Desmos": "https://www.desmos.com/calculator"}'::jsonb, 'medium', 
         ARRAY['interpretación gráfica'], ARRAY['funciones'], '3-4 horas', 3, 0.20, 4, ARRAY[1], 
         ARRAY['Interpretar gráficas', 'Analizar funciones']),
         
        ('550e8400-e29b-41d4-a716-446655440001', 4, 'Estadística', 'Probabilidad y estadística básica', 
         ARRAY['Medidas de tendencia', 'Probabilidad', 'Combinatoria'], 
         '{"Probabilidad": "https://www.youtube.com/watch?v=uzkc-qNVoOk", "Combinatoria": "https://www.youtube.com/watch?v=DROZVHObeko"}'::jsonb,
         22, '{"Khan Academy Estadística": "https://es.khanacademy.org/math/statistics-probability"}'::jsonb, 'high', 
         ARRAY['probabilidad básica'], ARRAY['estadística'], '4-5 horas', 2, 0.25, 5, ARRAY[1, 2], 
         ARRAY['Calcular probabilidades', 'Interpretar datos estadísticos']),

        -- Lenguaje (4 unidades)
        ('550e8400-e29b-41d4-a716-446655440002', 1, 'Comprensión Lectora', 'Habilidades de comprensión de textos', 
         ARRAY['Idea principal', 'Ideas secundarias', 'Vocabulario'], 
         '{"Idea principal": "https://www.youtube.com/watch?v=8YDP6YKRs0k", "Vocabulario": "https://www.youtube.com/watch?v=KjZjVW7GxOU"}'::jsonb,
         16, '{"Lectura crítica": "https://www.coursera.org/learn/spanish-reading"}'::jsonb, 'high', 
         ARRAY['identificación de ideas'], ARRAY['comprensión'], '3-4 horas', 1, 0.35, 4, ARRAY[]::integer[], 
         ARRAY['Identificar ideas principales', 'Ampliar vocabulario']),
         
        ('550e8400-e29b-41d4-a716-446655440002', 2, 'Análisis Textual', 'Análisis de diferentes tipos de textos', 
         ARRAY['Textos narrativos', 'Textos argumentativos', 'Estructura'], 
         '{"Textos narrativos": "https://www.youtube.com/watch?v=TJ9KYCJOCvI", "Estructura": "https://www.youtube.com/watch?v=HGF5xDdWSHo"}'::jsonb,
         20, '{"Análisis textual": "https://es.khanacademy.org/humanities/grammar"}'::jsonb, 'medium', 
         ARRAY['estructura textual'], ARRAY['análisis'], '4-5 horas', 2, 0.30, 5, ARRAY[1], 
         ARRAY['Analizar estructura textual', 'Identificar tipos de texto']),
         
        ('550e8400-e29b-41d4-a716-446655440002', 3, 'Gramática', 'Reglas gramaticales y sintaxis', 
         ARRAY['Morfología', 'Sintaxis', 'Ortografía'], 
         '{"Sintaxis": "https://www.youtube.com/watch?v=grammarexample", "Ortografía": "https://www.youtube.com/watch?v=ortografiaexample"}'::jsonb,
         18, '{"Gramática española": "https://www.rae.es"}'::jsonb, 'medium', 
         ARRAY['reglas gramaticales'], ARRAY['gramática'], '3-4 horas', 2, 0.20, 4, ARRAY[1], 
         ARRAY['Aplicar reglas gramaticales', 'Mejorar la escritura']),
         
        ('550e8400-e29b-41d4-a716-446655440002', 4, 'Literatura', 'Conocimiento literario y cultural', 
         ARRAY['Géneros literarios', 'Autores importantes', 'Contexto histórico'], 
         '{"Géneros literarios": "https://www.youtube.com/watch?v=literatureexample"}'::jsonb,
         15, '{"Literatura colombiana": "https://www.banrep.gov.co/biblioteca-virtual"}'::jsonb, 'low', 
         ARRAY['interpretación literaria'], ARRAY['literatura'], '2-3 horas', 3, 0.15, 3, ARRAY[1, 2], 
         ARRAY['Conocer géneros literarios', 'Interpretar textos literarios']),

        -- Ciencias Naturales (4 unidades)
        ('550e8400-e29b-41d4-a716-446655440003', 1, 'Física Básica', 'Conceptos fundamentales de física', 
         ARRAY['Mecánica', 'Energía', 'Fuerzas'], 
         '{"Mecánica": "https://www.youtube.com/watch?v=physicsexample", "Energía": "https://www.youtube.com/watch?v=energyexample"}'::jsonb,
         20, '{"Khan Academy Física": "https://es.khanacademy.org/science/physics"}'::jsonb, 'high', 
         ARRAY['conceptos de fuerza'], ARRAY['física'], '4-5 horas', 2, 0.30, 5, ARRAY[]::integer[], 
         ARRAY['Comprender leyes de Newton', 'Calcular energía']),
         
        ('550e8400-e29b-41d4-a716-446655440003', 2, 'Química', 'Fundamentos de química', 
         ARRAY['Átomos', 'Moléculas', 'Reacciones químicas'], 
         '{"Átomos": "https://www.youtube.com/watch?v=atomexample", "Reacciones": "https://www.youtube.com/watch?v=reactionexample"}'::jsonb,
         18, '{"Khan Academy Química": "https://es.khanacademy.org/science/chemistry"}'::jsonb, 'high', 
         ARRAY['estructura atómica'], ARRAY['química'], '4-5 horas', 2, 0.25, 5, ARRAY[]::integer[], 
         ARRAY['Entender estructura atómica', 'Balancear ecuaciones químicas']),
         
        ('550e8400-e29b-41d4-a716-446655440003', 3, 'Biología', 'Conceptos biológicos esenciales', 
         ARRAY['Célula', 'Genética', 'Ecosistemas'], 
         '{"Célula": "https://www.youtube.com/watch?v=cellexample", "Genética": "https://www.youtube.com/watch?v=geneticsexample"}'::jsonb,
         16, '{"Khan Academy Biología": "https://es.khanacademy.org/science/biology"}'::jsonb, 'medium', 
         ARRAY['función celular'], ARRAY['biología'], '3-4 horas', 2, 0.25, 4, ARRAY[]::integer[], 
         ARRAY['Comprender función celular', 'Entender herencia genética']),
         
        ('550e8400-e29b-41d4-a716-446655440003', 4, 'Ciencias Integradas', 'Integración de conocimientos científicos', 
         ARRAY['Método científico', 'Análisis de datos', 'Aplicaciones'], 
         '{"Método científico": "https://www.youtube.com/watch?v=methodexample"}'::jsonb,
         14, '{"Método científico": "https://www.coursera.org/learn/scientific-method"}'::jsonb, 'medium', 
         ARRAY['método científico'], ARRAY['ciencia'], '3-4 horas', 3, 0.20, 4, ARRAY[1, 2, 3], 
         ARRAY['Aplicar método científico', 'Analizar datos científicos']),

        -- Ciencias Sociales (4 unidades)
        ('550e8400-e29b-41d4-a716-446655440004', 1, 'Historia de Colombia', 'Historia nacional fundamental', 
         ARRAY['Independencia', 'República', 'Siglo XX'], 
         '{"Independencia": "https://www.youtube.com/watch?v=independenceexample", "República": "https://www.youtube.com/watch?v=republicexample"}'::jsonb,
         18, '{"Historia de Colombia": "https://www.banrep.gov.co/biblioteca-virtual"}'::jsonb, 'high', 
         ARRAY['procesos históricos'], ARRAY['historia'], '4-5 horas', 2, 0.30, 5, ARRAY[]::integer[], 
         ARRAY['Conocer procesos de independencia', 'Entender historia republicana']),
         
        ('550e8400-e29b-41d4-a716-446655440004', 2, 'Geografía', 'Geografía física y humana', 
         ARRAY['Relieve', 'Clima', 'Población'], 
         '{"Relieve": "https://www.youtube.com/watch?v=geografyexample", "Clima": "https://www.youtube.com/watch?v=climateexample"}'::jsonb,
         16, '{"Geografía de Colombia": "https://www.igac.gov.co"}'::jsonb, 'medium', 
         ARRAY['ubicación espacial'], ARRAY['geografía'], '3-4 horas', 2, 0.25, 4, ARRAY[]::integer[], 
         ARRAY['Identificar características geográficas', 'Analizar fenómenos espaciales']),
         
        ('550e8400-e29b-41d4-a716-446655440004', 3, 'Economía y Política', 'Conceptos económicos y políticos', 
         ARRAY['Sistema económico', 'Democracia', 'Constitución'], 
         '{"Economía": "https://www.youtube.com/watch?v=economyexample", "Democracia": "https://www.youtube.com/watch?v=democracyexample"}'::jsonb,
         15, '{"Constitución": "https://www.constitucioncolombia.com"}'::jsonb, 'medium', 
         ARRAY['conceptos económicos'], ARRAY['economía', 'política'], '3-4 horas', 2, 0.25, 4, ARRAY[1], 
         ARRAY['Entender sistema económico', 'Conocer principios democráticos']),
         
        ('550e8400-e29b-41d4-a716-446655440004', 4, 'Filosofía', 'Pensamiento crítico y filosófico', 
         ARRAY['Lógica', 'Ética', 'Filosofía política'], 
         '{"Lógica": "https://www.youtube.com/watch?v=logicexample", "Ética": "https://www.youtube.com/watch?v=ethicsexample"}'::jsonb,
         12, '{"Filosofía": "https://plato.stanford.edu"}'::jsonb, 'low', 
         ARRAY['pensamiento crítico'], ARRAY['filosofía'], '2-3 horas', 3, 0.20, 3, ARRAY[1, 2], 
         ARRAY['Desarrollar pensamiento crítico', 'Analizar problemas éticos']),

        -- Inglés (4 unidades)
        ('550e8400-e29b-41d4-a716-446655440005', 1, 'Grammar Basics', 'Fundamentos gramaticales en inglés', 
         ARRAY['Verb tenses', 'Articles', 'Pronouns'], 
         '{"Verb tenses": "https://www.youtube.com/watch?v=tensesexample", "Articles": "https://www.youtube.com/watch?v=articlesexample"}'::jsonb,
         20, '{"Khan Academy English": "https://www.khanacademy.org/humanities/grammar"}'::jsonb, 'high', 
         ARRAY['verb conjugation'], ARRAY['grammar'], '3-4 horas', 1, 0.30, 4, ARRAY[]::integer[], 
         ARRAY['Master basic verb tenses', 'Use articles correctly']),
         
        ('550e8400-e29b-41d4-a716-446655440005', 2, 'Reading Skills', 'Habilidades de lectura en inglés', 
         ARRAY['Reading comprehension', 'Vocabulary', 'Context clues'], 
         '{"Reading comprehension": "https://www.youtube.com/watch?v=readingexample", "Vocabulary": "https://www.youtube.com/watch?v=vocabexample"}'::jsonb,
         18, '{"English reading": "https://www.coursera.org/learn/english-reading"}'::jsonb, 'high', 
         ARRAY['vocabulary', 'comprehension'], ARRAY['reading'], '4-5 horas', 2, 0.35, 5, ARRAY[1], 
         ARRAY['Improve reading comprehension', 'Expand vocabulary']),
         
        ('550e8400-e29b-41d4-a716-446655440005', 3, 'Communication', 'Habilidades comunicativas', 
         ARRAY['Speaking', 'Listening', 'Conversation'], 
         '{"Speaking": "https://www.youtube.com/watch?v=speakingexample", "Listening": "https://www.youtube.com/watch?v=listeningexample"}'::jsonb,
         15, '{"English conversation": "https://www.duolingo.com"}'::jsonb, 'medium', 
         ARRAY['oral expression'], ARRAY['communication'], '3-4 horas', 2, 0.25, 4, ARRAY[1], 
         ARRAY['Improve speaking skills', 'Enhance listening comprehension']),
         
        ('550e8400-e29b-41d4-a716-446655440005', 4, 'Writing & Culture', 'Escritura y aspectos culturales', 
         ARRAY['Writing skills', 'Cultural context', 'Expressions'], 
         '{"Writing skills": "https://www.youtube.com/watch?v=writingexample", "Culture": "https://www.youtube.com/watch?v=cultureexample"}'::jsonb,
         12, '{"English writing": "https://www.coursera.org/learn/english-writing"}'::jsonb, 'low', 
         ARRAY['written expression'], ARRAY['writing'], '2-3 horas', 3, 0.10, 3, ARRAY[1, 2], 
         ARRAY['Develop writing skills', 'Understand cultural context']);

        RAISE NOTICE 'Plantillas adaptativas inicializadas: 20 unidades creadas para 5 materias';
    ELSE
        RAISE NOTICE 'Plantillas adaptativas ya existen. Saltando inicialización.';
    END IF;
END $$;