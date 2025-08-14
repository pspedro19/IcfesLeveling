-- ICFES LEVELING - Study Plans Generation
-- Planes de estudio detallados basados en el formato real del ICFES
-- Genera planes personalizados por materia con unidades temáticas específicas

-- =====================================================
-- PLANES DE ESTUDIO PARA MATEMÁTICAS
-- =====================================================

-- Plan 1: Matemáticas - Fundamentos
INSERT INTO study_plans (id, user_id, subject_id, plan_name, plan_data, total_units, completed_units, progress_percentage, is_active) VALUES
(
    'sp-001-math-fundamentals',
    '550e8400-e29b-41d4-a716-446655440000', -- user_id placeholder
    '550e8400-e29b-41d4-a716-446655440001', -- Matemáticas
    'Mazmorra de Matemáticas: Fundamentos',
    '{
        "subject": "Matemáticas",
        "title": "Mazmorra de Matemáticas: Fundamentos",
        "description": "Conquista los conceptos fundamentales de las matemáticas ICFES",
        "units": [
            {
                "unit_number": 1,
                "name": "Álgebra Básica y Ecuaciones",
                "description": "Dominio de operaciones algebraicas y resolución de ecuaciones",
                "topics": [
                    {"name": "Operaciones con números reales", "difficulty": 1, "questions": 15, "tags": ["aritmética", "básico"]},
                    {"name": "Ecuaciones lineales", "difficulty": 2, "questions": 20, "tags": ["ecuaciones", "álgebra"]},
                    {"name": "Sistemas de ecuaciones", "difficulty": 2, "questions": 18, "tags": ["sistemas", "álgebra"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["operaciones básicas", "despeje de variables"],
                    "focus_topics": ["ecuaciones lineales", "sistemas 2x2"],
                    "study_time": "3-4 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 2,
                "name": "Geometría Euclidiana",
                "description": "Propiedades de figuras geométricas y teoremas fundamentales",
                "topics": [
                    {"name": "Triángulos y teoremas", "difficulty": 2, "questions": 20, "tags": ["triángulos", "teoremas"]},
                    {"name": "Círculos y circunferencias", "difficulty": 2, "questions": 18, "tags": ["círculos", "geometría"]},
                    {"name": "Polígonos regulares", "difficulty": 3, "questions": 15, "tags": ["polígonos", "regular"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["teorema de Pitágoras", "áreas y perímetros"],
                    "focus_topics": ["triángulos rectángulos", "círculos"],
                    "study_time": "3-4 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 3,
                "name": "Funciones y Gráficas",
                "description": "Análisis de funciones lineales, cuadráticas y sus representaciones",
                "topics": [
                    {"name": "Funciones lineales", "difficulty": 2, "questions": 18, "tags": ["funciones", "lineales"]},
                    {"name": "Funciones cuadráticas", "difficulty": 3, "questions": 20, "tags": ["cuadráticas", "parábolas"]},
                    {"name": "Análisis gráfico", "difficulty": 3, "questions": 15, "tags": ["gráficas", "análisis"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["dominio y rango", "intersecciones"],
                    "focus_topics": ["funciones cuadráticas", "gráficas"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 4,
                "name": "Trigonometría Básica",
                "description": "Razones trigonométricas y aplicaciones en triángulos",
                "topics": [
                    {"name": "Razones trigonométricas", "difficulty": 3, "questions": 20, "tags": ["seno", "coseno", "tangente"]},
                    {"name": "Identidades básicas", "difficulty": 4, "questions": 15, "tags": ["identidades", "trigonometría"]},
                    {"name": "Aplicaciones prácticas", "difficulty": 3, "questions": 18, "tags": ["aplicaciones", "problemas"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["círculo unitario", "identidades"],
                    "focus_topics": ["razones trigonométricas", "aplicaciones"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            },
            {
                "unit_number": 5,
                "name": "Probabilidad y Estadística",
                "description": "Análisis de datos y cálculo de probabilidades",
                "topics": [
                    {"name": "Probabilidad básica", "difficulty": 2, "questions": 18, "tags": ["probabilidad", "eventos"]},
                    {"name": "Estadística descriptiva", "difficulty": 3, "questions": 20, "tags": ["media", "mediana", "moda"]},
                    {"name": "Distribuciones", "difficulty": 4, "questions": 15, "tags": ["distribuciones", "normal"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["permutaciones", "combinaciones"],
                    "focus_topics": ["probabilidad", "estadística"],
                    "study_time": "3-4 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            },
            {
                "unit_number": 6,
                "name": "Cálculo Diferencial",
                "description": "Límites, derivadas y aplicaciones del cálculo",
                "topics": [
                    {"name": "Límites y continuidad", "difficulty": 4, "questions": 20, "tags": ["límites", "continuidad"]},
                    {"name": "Derivadas básicas", "difficulty": 4, "questions": 22, "tags": ["derivadas", "reglas"]},
                    {"name": "Aplicaciones de derivadas", "difficulty": 5, "questions": 18, "tags": ["máximos", "mínimos"]}
                ],
                "recommendations": {
                    "priority": "low",
                    "weak_areas": ["reglas de derivación", "aplicaciones"],
                    "focus_topics": ["derivadas", "aplicaciones"],
                    "study_time": "5-6 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            }
        ],
        "total_questions": 300,
        "estimated_time": "22-28 horas",
        "difficulty_curve": "progressive",
        "icfes_weight": 0.25,
        "exam_sections": ["Pensamiento Matemático", "Razonamiento Cuantitativo"]
    }',
    6, 0, 0.00, true
);

-- =====================================================
-- PLANES DE ESTUDIO PARA LENGUAJE
-- =====================================================

-- Plan 2: Lenguaje - Comprensión y Análisis
INSERT INTO study_plans (id, user_id, subject_id, plan_name, plan_data, total_units, completed_units, progress_percentage, is_active) VALUES
(
    'sp-002-language-comprehension',
    '550e8400-e29b-41d4-a716-446655440000', -- user_id placeholder
    '550e8400-e29b-41d4-a716-446655440002', -- Lenguaje
    'Mazmorra de Lenguaje: Comprensión y Análisis',
    '{
        "subject": "Lenguaje",
        "title": "Mazmorra de Lenguaje: Comprensión y Análisis",
        "description": "Domina la comprensión lectora y el análisis textual del ICFES",
        "units": [
            {
                "unit_number": 1,
                "name": "Comprensión Lectora Básica",
                "description": "Estrategias fundamentales para la comprensión de textos",
                "topics": [
                    {"name": "Identificación de ideas principales", "difficulty": 1, "questions": 20, "tags": ["idea principal", "texto"]},
                    {"name": "Inferencia y deducción", "difficulty": 2, "questions": 18, "tags": ["inferencia", "deducción"]},
                    {"name": "Vocabulario contextual", "difficulty": 2, "questions": 15, "tags": ["vocabulario", "contexto"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["identificación de ideas", "vocabulario"],
                    "focus_topics": ["ideas principales", "inferencias"],
                    "study_time": "3-4 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 2,
                "name": "Análisis de Textos Informativos",
                "description": "Comprensión y análisis de textos expositivos y argumentativos",
                "topics": [
                    {"name": "Estructura de textos informativos", "difficulty": 2, "questions": 18, "tags": ["estructura", "informativo"]},
                    {"name": "Argumentación y tesis", "difficulty": 3, "questions": 20, "tags": ["argumentación", "tesis"]},
                    {"name": "Evidencia y soporte", "difficulty": 3, "questions": 15, "tags": ["evidencia", "soporte"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["identificación de tesis", "evidencia"],
                    "focus_topics": ["argumentación", "estructura"],
                    "study_time": "4-5 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 3,
                "name": "Literatura y Textos Literarios",
                "description": "Análisis de géneros literarios y recursos estilísticos",
                "topics": [
                    {"name": "Géneros literarios", "difficulty": 2, "questions": 18, "tags": ["géneros", "literatura"]},
                    {"name": "Recursos literarios", "difficulty": 3, "questions": 20, "tags": ["metáfora", "símil", "personificación"]},
                    {"name": "Análisis poético", "difficulty": 4, "questions": 15, "tags": ["poesía", "análisis"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["recursos literarios", "análisis poético"],
                    "focus_topics": ["géneros", "recursos"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 4,
                "name": "Gramática y Sintaxis",
                "description": "Dominio de las estructuras gramaticales y sintácticas",
                "topics": [
                    {"name": "Categorías gramaticales", "difficulty": 2, "questions": 20, "tags": ["sustantivos", "verbos", "adjetivos"]},
                    {"name": "Análisis sintáctico", "difficulty": 3, "questions": 18, "tags": ["sujeto", "predicado", "complementos"]},
                    {"name": "Oraciones compuestas", "difficulty": 4, "questions": 15, "tags": ["coordinadas", "subordinadas"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["análisis sintáctico", "oraciones compuestas"],
                    "focus_topics": ["categorías gramaticales", "sintaxis"],
                    "study_time": "3-4 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            },
            {
                "unit_number": 5,
                "name": "Comprensión Crítica",
                "description": "Análisis crítico y evaluación de textos",
                "topics": [
                    {"name": "Crítica textual", "difficulty": 4, "questions": 18, "tags": ["crítica", "evaluación"]},
                    {"name": "Perspectivas y puntos de vista", "difficulty": 4, "questions": 20, "tags": ["perspectivas", "puntos de vista"]},
                    {"name": "Evaluación de argumentos", "difficulty": 5, "questions": 15, "tags": ["argumentos", "evaluación"]}
                ],
                "recommendations": {
                    "priority": "low",
                    "weak_areas": ["crítica textual", "evaluación"],
                    "focus_topics": ["perspectivas", "argumentos"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            }
        ],
        "total_questions": 250,
        "estimated_time": "18-23 horas",
        "difficulty_curve": "progressive",
        "icfes_weight": 0.25,
        "exam_sections": ["Lectura Crítica", "Comprensión Lectora"]
    }',
    5, 0, 0.00, true
);

-- =====================================================
-- PLANES DE ESTUDIO PARA CIENCIAS NATURALES
-- =====================================================

-- Plan 3: Ciencias Naturales - Fundamentos Científicos
INSERT INTO study_plans (id, user_id, subject_id, plan_name, plan_data, total_units, completed_units, progress_percentage, is_active) VALUES
(
    'sp-003-science-fundamentals',
    '550e8400-e29b-41d4-a716-446655440000', -- user_id placeholder
    '550e8400-e29b-41d4-a716-446655440003', -- Ciencias Naturales
    'Mazmorra de Ciencias: Fundamentos Científicos',
    '{
        "subject": "Ciencias Naturales",
        "title": "Mazmorra de Ciencias: Fundamentos Científicos",
        "description": "Explora los principios fundamentales de la física, química y biología",
        "units": [
            {
                "unit_number": 1,
                "name": "Física: Mecánica Clásica",
                "description": "Movimiento, fuerzas y leyes fundamentales de la física",
                "topics": [
                    {"name": "Cinemática y movimiento", "difficulty": 2, "questions": 20, "tags": ["movimiento", "velocidad", "aceleración"]},
                    {"name": "Leyes de Newton", "difficulty": 3, "questions": 18, "tags": ["fuerzas", "newton", "dinámica"]},
                    {"name": "Energía y trabajo", "difficulty": 3, "questions": 15, "tags": ["energía", "trabajo", "potencial"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["leyes de Newton", "energía"],
                    "focus_topics": ["cinemática", "dinámica"],
                    "study_time": "4-5 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 2,
                "name": "Química: Estructura de la Materia",
                "description": "Átomos, moléculas y reacciones químicas básicas",
                "topics": [
                    {"name": "Estructura atómica", "difficulty": 2, "questions": 18, "tags": ["átomo", "electrones", "núcleo"]},
                    {"name": "Enlaces químicos", "difficulty": 3, "questions": 20, "tags": ["enlaces", "iónico", "covalente"]},
                    {"name": "Reacciones químicas", "difficulty": 3, "questions": 15, "tags": ["reacciones", "balanceo", "estequiometría"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["enlaces químicos", "balanceo"],
                    "focus_topics": ["estructura atómica", "reacciones"],
                    "study_time": "4-5 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 3,
                "name": "Biología: Células y Sistemas",
                "description": "Estructura celular y sistemas biológicos fundamentales",
                "topics": [
                    {"name": "Estructura celular", "difficulty": 2, "questions": 18, "tags": ["célula", "organelos", "membrana"]},
                    {"name": "Metabolismo celular", "difficulty": 3, "questions": 20, "tags": ["metabolismo", "respiración", "fotosíntesis"]},
                    {"name": "Sistemas del cuerpo", "difficulty": 3, "questions": 15, "tags": ["sistemas", "digestivo", "circulatorio"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["metabolismo", "sistemas"],
                    "focus_topics": ["estructura celular", "organelos"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 4,
                "name": "Física: Ondas y Electricidad",
                "description": "Propiedades de las ondas y principios eléctricos",
                "topics": [
                    {"name": "Propiedades de las ondas", "difficulty": 3, "questions": 18, "tags": ["ondas", "frecuencia", "amplitud"]},
                    {"name": "Electricidad básica", "difficulty": 3, "questions": 20, "tags": ["corriente", "voltaje", "resistencia"]},
                    {"name": "Magnetismo", "difficulty": 4, "questions": 15, "tags": ["magnetismo", "campos", "fuerzas"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["electricidad", "magnetismo"],
                    "focus_topics": ["ondas", "corriente"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            },
            {
                "unit_number": 5,
                "name": "Química: Soluciones y Equilibrio",
                "description": "Soluciones químicas y principios de equilibrio",
                "topics": [
                    {"name": "Soluciones y concentración", "difficulty": 3, "questions": 18, "tags": ["soluciones", "concentración", "molaridad"]},
                    {"name": "Equilibrio químico", "difficulty": 4, "questions": 20, "tags": ["equilibrio", "constante", "le chatelier"]},
                    {"name": "Ácidos y bases", "difficulty": 4, "questions": 15, "tags": ["ácidos", "bases", "pH"]}
                ],
                "recommendations": {
                    "priority": "low",
                    "weak_areas": ["equilibrio", "ácidos y bases"],
                    "focus_topics": ["soluciones", "concentración"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            }
        ],
        "total_questions": 280,
        "estimated_time": "20-25 horas",
        "difficulty_curve": "progressive",
        "icfes_weight": 0.20,
        "exam_sections": ["Ciencias Naturales", "Pensamiento Científico"]
    }',
    5, 0, 0.00, true
);

-- =====================================================
-- PLANES DE ESTUDIO PARA CIENCIAS SOCIALES
-- =====================================================

-- Plan 4: Ciencias Sociales - Análisis Social
INSERT INTO study_plans (id, user_id, subject_id, plan_name, plan_data, total_units, completed_units, progress_percentage, is_active) VALUES
(
    'sp-004-social-analysis',
    '550e8400-e29b-41d4-a716-446655440000', -- user_id placeholder
    '550e8400-e29b-41d4-a716-446655440004', -- Ciencias Sociales
    'Mazmorra de Ciencias Sociales: Análisis Social',
    '{
        "subject": "Ciencias Sociales",
        "title": "Mazmorra de Ciencias Sociales: Análisis Social",
        "description": "Analiza la sociedad, la historia y los fenómenos sociales",
        "units": [
            {
                "unit_number": 1,
                "name": "Historia: Procesos Históricos",
                "description": "Análisis de procesos históricos fundamentales",
                "topics": [
                    {"name": "Revoluciones y cambios sociales", "difficulty": 2, "questions": 18, "tags": ["revoluciones", "cambios", "historia"]},
                    {"name": "Colonialismo e independencia", "difficulty": 3, "questions": 20, "tags": ["colonialismo", "independencia", "América"]},
                    {"name": "Guerras mundiales", "difficulty": 3, "questions": 15, "tags": ["guerras", "conflictos", "siglo XX"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["procesos históricos", "cronología"],
                    "focus_topics": ["revoluciones", "independencia"],
                    "study_time": "3-4 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 2,
                "name": "Geografía: Espacio y Sociedad",
                "description": "Relación entre el espacio geográfico y la sociedad",
                "topics": [
                    {"name": "Geografía física y humana", "difficulty": 2, "questions": 18, "tags": ["geografía", "física", "humana"]},
                    {"name": "Globalización y desarrollo", "difficulty": 3, "questions": 20, "tags": ["globalización", "desarrollo", "economía"]},
                    {"name": "Problemas ambientales", "difficulty": 3, "questions": 15, "tags": ["ambiente", "contaminación", "sostenibilidad"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["globalización", "problemas ambientales"],
                    "focus_topics": ["geografía", "desarrollo"],
                    "study_time": "3-4 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 3,
                "name": "Filosofía: Pensamiento Crítico",
                "description": "Desarrollo del pensamiento filosófico y crítico",
                "topics": [
                    {"name": "Corrientes filosóficas", "difficulty": 3, "questions": 18, "tags": ["filosofía", "corrientes", "pensamiento"]},
                    {"name": "Ética y moral", "difficulty": 3, "questions": 20, "tags": ["ética", "moral", "valores"]},
                    {"name": "Lógica y argumentación", "difficulty": 4, "questions": 15, "tags": ["lógica", "argumentación", "razonamiento"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["corrientes filosóficas", "lógica"],
                    "focus_topics": ["ética", "argumentación"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 4,
                "name": "Política: Sistemas y Democracia",
                "description": "Análisis de sistemas políticos y democracia",
                "topics": [
                    {"name": "Sistemas políticos", "difficulty": 3, "questions": 18, "tags": ["política", "sistemas", "gobierno"]},
                    {"name": "Democracia y participación", "difficulty": 3, "questions": 20, "tags": ["democracia", "participación", "ciudadanía"]},
                    {"name": "Derechos humanos", "difficulty": 4, "questions": 15, "tags": ["derechos", "humanos", "libertades"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["sistemas políticos", "derechos humanos"],
                    "focus_topics": ["democracia", "participación"],
                    "study_time": "3-4 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            },
            {
                "unit_number": 5,
                "name": "Economía: Sistemas Económicos",
                "description": "Principios económicos y sistemas de producción",
                "topics": [
                    {"name": "Sistemas económicos", "difficulty": 3, "questions": 18, "tags": ["economía", "sistemas", "producción"]},
                    {"name": "Mercado y competencia", "difficulty": 4, "questions": 20, "tags": ["mercado", "competencia", "oferta"]},
                    {"name": "Desarrollo económico", "difficulty": 4, "questions": 15, "tags": ["desarrollo", "crecimiento", "pobreza"]}
                ],
                "recommendations": {
                    "priority": "low",
                    "weak_areas": ["mercado", "desarrollo económico"],
                    "focus_topics": ["sistemas económicos", "competencia"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            }
        ],
        "total_questions": 250,
        "estimated_time": "17-22 horas",
        "difficulty_curve": "progressive",
        "icfes_weight": 0.15,
        "exam_sections": ["Ciencias Sociales", "Comprensión Social"]
    }',
    5, 0, 0.00, true
);

-- =====================================================
-- PLANES DE ESTUDIO PARA INGLÉS
-- =====================================================

-- Plan 5: Inglés - Comprensión y Uso
INSERT INTO study_plans (id, user_id, subject_id, plan_name, plan_data, total_units, completed_units, progress_percentage, is_active) VALUES
(
    'sp-005-english-comprehension',
    '550e8400-e29b-41d4-a716-446655440000', -- user_id placeholder
    '550e8400-e29b-41d4-a716-446655440005', -- Inglés
    'Mazmorra de Inglés: Comprensión y Uso',
    '{
        "subject": "Inglés",
        "title": "Mazmorra de Inglés: Comprensión y Uso",
        "description": "Domina la comprensión y uso del idioma inglés",
        "units": [
            {
                "unit_number": 1,
                "name": "Comprensión de Lectura Básica",
                "description": "Estrategias para comprender textos en inglés",
                "topics": [
                    {"name": "Identificación de ideas principales", "difficulty": 1, "questions": 20, "tags": ["main idea", "reading", "comprehension"]},
                    {"name": "Vocabulario contextual", "difficulty": 2, "questions": 18, "tags": ["vocabulary", "context", "meaning"]},
                    {"name": "Inferencia de información", "difficulty": 2, "questions": 15, "tags": ["inference", "deduction", "reading"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["vocabulario", "inferencia"],
                    "focus_topics": ["ideas principales", "contexto"],
                    "study_time": "3-4 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 2,
                "name": "Gramática Básica",
                "description": "Estructuras gramaticales fundamentales del inglés",
                "topics": [
                    {"name": "Tiempos verbales básicos", "difficulty": 2, "questions": 18, "tags": ["tenses", "present", "past", "future"]},
                    {"name": "Estructuras de oraciones", "difficulty": 2, "questions": 20, "tags": ["sentence structure", "syntax", "grammar"]},
                    {"name": "Partes del discurso", "difficulty": 2, "questions": 15, "tags": ["parts of speech", "nouns", "verbs", "adjectives"]}
                ],
                "recommendations": {
                    "priority": "high",
                    "weak_areas": ["tiempos verbales", "estructuras"],
                    "focus_topics": ["gramática básica", "oraciones"],
                    "study_time": "3-4 horas"
                },
                "unlocked": true,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 3,
                "name": "Comprensión Avanzada",
                "description": "Análisis de textos complejos en inglés",
                "topics": [
                    {"name": "Textos académicos", "difficulty": 3, "questions": 18, "tags": ["academic", "texts", "analysis"]},
                    {"name": "Textos literarios", "difficulty": 3, "questions": 20, "tags": ["literary", "texts", "interpretation"]},
                    {"name": "Textos informativos", "difficulty": 3, "questions": 15, "tags": ["informative", "texts", "comprehension"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["textos académicos", "literarios"],
                    "focus_topics": ["análisis", "interpretación"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": true
            },
            {
                "unit_number": 4,
                "name": "Gramática Avanzada",
                "description": "Estructuras gramaticales complejas",
                "topics": [
                    {"name": "Tiempos perfectos", "difficulty": 3, "questions": 18, "tags": ["perfect tenses", "grammar", "advanced"]},
                    {"name": "Condicionales", "difficulty": 4, "questions": 20, "tags": ["conditionals", "if clauses", "grammar"]},
                    {"name": "Voz pasiva", "difficulty": 4, "questions": 15, "tags": ["passive voice", "grammar", "structure"]}
                ],
                "recommendations": {
                    "priority": "medium",
                    "weak_areas": ["condicionales", "voz pasiva"],
                    "focus_topics": ["tiempos perfectos", "estructuras"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            },
            {
                "unit_number": 5,
                "name": "Análisis Crítico en Inglés",
                "description": "Evaluación crítica de textos en inglés",
                "topics": [
                    {"name": "Evaluación de argumentos", "difficulty": 4, "questions": 18, "tags": ["argument evaluation", "critical thinking"]},
                    {"name": "Análisis de perspectivas", "difficulty": 4, "questions": 20, "tags": ["perspective analysis", "viewpoints"]},
                    {"name": "Síntesis de información", "difficulty": 5, "questions": 15, "tags": ["synthesis", "information", "analysis"]}
                ],
                "recommendations": {
                    "priority": "low",
                    "weak_areas": ["evaluación", "síntesis"],
                    "focus_topics": ["análisis crítico", "perspectivas"],
                    "study_time": "4-5 horas"
                },
                "unlocked": false,
                "progress": 0,
                "ai_recommended": false
            }
        ],
        "total_questions": 220,
        "estimated_time": "18-23 horas",
        "difficulty_curve": "progressive",
        "icfes_weight": 0.15,
        "exam_sections": ["Inglés", "Comprensión Lectora en Inglés"]
    }',
    5, 0, 0.00, true
);

-- =====================================================
-- INSERCIÓN DE PROGRESO DE PLANES (PLACEHOLDER)
-- =====================================================

-- Insertar progreso de unidades para los planes creados
INSERT INTO plan_progress (id, plan_id, unit_number, unit_name, unit_description, unit_content, is_completed, score, weighted_progress) VALUES
-- Progreso para Matemáticas
('pp-001-math-1', 'sp-001-math-fundamentals', 1, 'Álgebra Básica y Ecuaciones', 'Dominio de operaciones algebraicas y resolución de ecuaciones', 
'{"videos": ["https://youtube.com/watch?v=algebra1", "https://youtube.com/watch?v=algebra2"], "exercises": 53, "readings": 3}', 
false, 0.00, '{"videos": {"completed": 0, "total": 2, "weight": 0.3}, "exercises": {"completed": 0, "total": 53, "weight": 0.5}, "readings": {"completed": 0, "total": 3, "weight": 0.2}}'),

('pp-002-math-2', 'sp-001-math-fundamentals', 2, 'Geometría Euclidiana', 'Propiedades de figuras geométricas y teoremas fundamentales',
'{"videos": ["https://youtube.com/watch?v=geometry1", "https://youtube.com/watch?v=geometry2"], "exercises": 53, "readings": 3}',
false, 0.00, '{"videos": {"completed": 0, "total": 2, "weight": 0.3}, "exercises": {"completed": 0, "total": 53, "weight": 0.5}, "readings": {"completed": 0, "total": 3, "weight": 0.2}}'),

-- Progreso para Lenguaje
('pp-003-lang-1', 'sp-002-language-comprehension', 1, 'Comprensión Lectora Básica', 'Estrategias fundamentales para la comprensión de textos',
'{"videos": ["https://youtube.com/watch?v=reading1", "https://youtube.com/watch?v=reading2"], "exercises": 53, "readings": 3}',
false, 0.00, '{"videos": {"completed": 0, "total": 2, "weight": 0.3}, "exercises": {"completed": 0, "total": 53, "weight": 0.5}, "readings": {"completed": 0, "total": 3, "weight": 0.2}}'),

-- Progreso para Ciencias
('pp-004-sci-1', 'sp-003-science-fundamentals', 1, 'Física: Mecánica Clásica', 'Movimiento, fuerzas y leyes fundamentales de la física',
'{"videos": ["https://youtube.com/watch?v=physics1", "https://youtube.com/watch?v=physics2"], "exercises": 53, "readings": 3}',
false, 0.00, '{"videos": {"completed": 0, "total": 2, "weight": 0.3}, "exercises": {"completed": 0, "total": 53, "weight": 0.5}, "readings": {"completed": 0, "total": 3, "weight": 0.2}}'),

-- Progreso para Sociales
('pp-005-soc-1', 'sp-004-social-analysis', 1, 'Historia: Procesos Históricos', 'Análisis de procesos históricos fundamentales',
'{"videos": ["https://youtube.com/watch?v=history1", "https://youtube.com/watch?v=history2"], "exercises": 53, "readings": 3}',
false, 0.00, '{"videos": {"completed": 0, "total": 2, "weight": 0.3}, "exercises": {"completed": 0, "total": 53, "weight": 0.5}, "readings": {"completed": 0, "total": 3, "weight": 0.2}}'),

-- Progreso para Inglés
('pp-006-eng-1', 'sp-005-english-comprehension', 1, 'Comprensión de Lectura Básica', 'Estrategias para comprender textos en inglés',
'{"videos": ["https://youtube.com/watch?v=english1", "https://youtube.com/watch?v=english2"], "exercises": 53, "readings": 3}',
false, 0.00, '{"videos": {"completed": 0, "total": 2, "weight": 0.3}, "exercises": {"completed": 0, "total": 53, "weight": 0.5}, "readings": {"completed": 0, "total": 3, "weight": 0.2}}');

-- =====================================================
-- COMENTARIOS Y DOCUMENTACIÓN
-- =====================================================

COMMENT ON TABLE study_plans IS 'Planes de estudio personalizados por materia basados en el formato ICFES';
COMMENT ON COLUMN study_plans.plan_data IS 'JSON con estructura YAML que define el plan completo incluyendo unidades, temas, dificultad y recomendaciones';
COMMENT ON COLUMN study_plans.total_units IS 'Número total de unidades en el plan (típicamente 5-6 por materia)';
COMMENT ON COLUMN study_plans.completed_units IS 'Unidades completadas por el usuario';
COMMENT ON COLUMN study_plans.progress_percentage IS 'Porcentaje de progreso general del plan';

COMMENT ON TABLE plan_progress IS 'Progreso detallado de cada unidad dentro de un plan de estudio';
COMMENT ON COLUMN plan_progress.unit_content IS 'JSON con recursos de la unidad: videos, ejercicios, lecturas';
COMMENT ON COLUMN plan_progress.weighted_progress IS 'Progreso ponderado por tipo de contenido (videos 30%, ejercicios 50%, lecturas 20%)';
COMMENT ON COLUMN plan_progress.score IS 'Puntuación obtenida en la unidad (0-100)';

-- =====================================================
-- ÍNDICES PARA OPTIMIZACIÓN
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_study_plans_user_subject ON study_plans(user_id, subject_id);
CREATE INDEX IF NOT EXISTS idx_study_plans_active ON study_plans(is_active);
CREATE INDEX IF NOT EXISTS idx_plan_progress_plan_unit ON plan_progress(plan_id, unit_number);
CREATE INDEX IF NOT EXISTS idx_plan_progress_completed ON plan_progress(is_completed); 