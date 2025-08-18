-- Migración para agregar soporte de preguntas multimedia
-- Script: 14-multimedia-questions.sql

-- Agregar nuevos campos para preguntas multimedia
ALTER TABLE questions 
ADD COLUMN IF NOT EXISTS pregunta_texto TEXT,
ADD COLUMN IF NOT EXISTS pregunta_imagen VARCHAR(500),
ADD COLUMN IF NOT EXISTS opcion_a_texto TEXT,
ADD COLUMN IF NOT EXISTS opcion_a_imagen VARCHAR(500),
ADD COLUMN IF NOT EXISTS opcion_b_texto TEXT,
ADD COLUMN IF NOT EXISTS opcion_b_imagen VARCHAR(500),
ADD COLUMN IF NOT EXISTS opcion_c_texto TEXT,
ADD COLUMN IF NOT EXISTS opcion_c_imagen VARCHAR(500),
ADD COLUMN IF NOT EXISTS opcion_d_texto TEXT,
ADD COLUMN IF NOT EXISTS opcion_d_imagen VARCHAR(500),
ADD COLUMN IF NOT EXISTS respuesta_correcta VARCHAR(1);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_questions_pregunta_texto ON questions(pregunta_texto);
CREATE INDEX IF NOT EXISTS idx_questions_respuesta_correcta ON questions(respuesta_correcta);
CREATE INDEX IF NOT EXISTS idx_questions_multimedia ON questions(pregunta_texto, pregunta_imagen);

-- Agregar comentarios a las columnas
COMMENT ON COLUMN questions.pregunta_texto IS 'Contenido textual de la pregunta (puede ser NULL)';
COMMENT ON COLUMN questions.pregunta_imagen IS 'URL/ruta de la imagen de la pregunta (puede ser NULL)';
COMMENT ON COLUMN questions.opcion_a_texto IS 'Texto de la opción A (puede ser NULL)';
COMMENT ON COLUMN questions.opcion_a_imagen IS 'Imagen de la opción A (puede ser NULL)';
COMMENT ON COLUMN questions.opcion_b_texto IS 'Texto de la opción B (puede ser NULL)';
COMMENT ON COLUMN questions.opcion_b_imagen IS 'Imagen de la opción B (puede ser NULL)';
COMMENT ON COLUMN questions.opcion_c_texto IS 'Texto de la opción C (puede ser NULL)';
COMMENT ON COLUMN questions.opcion_c_imagen IS 'Imagen de la opción C (puede ser NULL)';
COMMENT ON COLUMN questions.opcion_d_texto IS 'Texto de la opción D (puede ser NULL)';
COMMENT ON COLUMN questions.opcion_d_imagen IS 'Imagen de la opción D (puede ser NULL)';
COMMENT ON COLUMN questions.respuesta_correcta IS 'Letra de la respuesta correcta (a, b, c, d)';

-- Crear función para validar preguntas multimedia
CREATE OR REPLACE FUNCTION validate_multimedia_question()
RETURNS TRIGGER AS $$
BEGIN
    -- Validar que al menos existe texto o imagen en la pregunta
    IF NEW.pregunta_texto IS NULL AND NEW.pregunta_imagen IS NULL THEN
        RAISE EXCEPTION 'La pregunta debe tener al menos texto o imagen';
    END IF;
    
    -- Validar que al menos una opción tiene contenido
    IF (NEW.opcion_a_texto IS NULL AND NEW.opcion_a_imagen IS NULL) AND
       (NEW.opcion_b_texto IS NULL AND NEW.opcion_b_imagen IS NULL) AND
       (NEW.opcion_c_texto IS NULL AND NEW.opcion_c_imagen IS NULL) AND
       (NEW.opcion_d_texto IS NULL AND NEW.opcion_d_imagen IS NULL) THEN
        RAISE EXCEPTION 'Debe haber al menos una opción con contenido (texto o imagen)';
    END IF;
    
    -- Validar respuesta correcta
    IF NEW.respuesta_correcta NOT IN ('a', 'b', 'c', 'd') THEN
        RAISE EXCEPTION 'La respuesta correcta debe ser a, b, c o d';
    END IF;
    
    -- Validar que la opción de respuesta correcta tiene contenido
    IF NEW.respuesta_correcta = 'a' AND NEW.opcion_a_texto IS NULL AND NEW.opcion_a_imagen IS NULL THEN
        RAISE EXCEPTION 'La opción A (respuesta correcta) debe tener contenido';
    ELSIF NEW.respuesta_correcta = 'b' AND NEW.opcion_b_texto IS NULL AND NEW.opcion_b_imagen IS NULL THEN
        RAISE EXCEPTION 'La opción B (respuesta correcta) debe tener contenido';
    ELSIF NEW.respuesta_correcta = 'c' AND NEW.opcion_c_texto IS NULL AND NEW.opcion_c_imagen IS NULL THEN
        RAISE EXCEPTION 'La opción C (respuesta correcta) debe tener contenido';
    ELSIF NEW.respuesta_correcta = 'd' AND NEW.opcion_d_texto IS NULL AND NEW.opcion_d_imagen IS NULL THEN
        RAISE EXCEPTION 'La opción D (respuesta correcta) debe tener contenido';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear trigger para validación automática
DROP TRIGGER IF EXISTS trigger_validate_multimedia_question ON questions;
CREATE TRIGGER trigger_validate_multimedia_question
    BEFORE INSERT OR UPDATE ON questions
    FOR EACH ROW
    EXECUTE FUNCTION validate_multimedia_question();

-- Crear función para migrar datos existentes (opcional)
CREATE OR REPLACE FUNCTION migrate_existing_questions()
RETURNS void AS $$
DECLARE
    question_record RECORD;
BEGIN
    -- Migrar preguntas existentes que usan el formato legacy
    FOR question_record IN 
        SELECT id, question_text, correct_answer, options, image_url, options_images
        FROM questions 
        WHERE pregunta_texto IS NULL 
        AND question_text IS NOT NULL
    LOOP
        UPDATE questions 
        SET 
            pregunta_texto = question_record.question_text,
            pregunta_imagen = question_record.image_url,
            respuesta_correcta = LOWER(question_record.correct_answer),
            opcion_a_texto = question_record.options->>'A',
            opcion_b_texto = question_record.options->>'B',
            opcion_c_texto = question_record.options->>'C',
            opcion_d_texto = question_record.options->>'D',
            opcion_a_imagen = question_record.options_images->>'A',
            opcion_b_imagen = question_record.options_images->>'B',
            opcion_c_imagen = question_record.options_images->>'C',
            opcion_d_imagen = question_record.options_images->>'D'
        WHERE id = question_record.id;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Ejecutar migración de datos existentes
SELECT migrate_existing_questions();

-- Crear vista para preguntas multimedia
CREATE OR REPLACE VIEW multimedia_questions AS
SELECT 
    id,
    topic_id,
    subject_id,
    pregunta_texto,
    pregunta_imagen,
    opcion_a_texto,
    opcion_a_imagen,
    opcion_b_texto,
    opcion_b_imagen,
    opcion_c_texto,
    opcion_c_imagen,
    opcion_d_texto,
    opcion_d_imagen,
    respuesta_correcta,
    difficulty,
    explanation,
    hint,
    tags,
    power_stats,
    is_validated,
    usage_count,
    average_response_time,
    created_at,
    updated_at
FROM questions
WHERE pregunta_texto IS NOT NULL OR pregunta_imagen IS NOT NULL;

-- Crear función para obtener opciones en formato JSON
CREATE OR REPLACE FUNCTION get_question_options(question_id UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'A', json_build_object('texto', opcion_a_texto, 'imagen', opcion_a_imagen),
        'B', json_build_object('texto', opcion_b_texto, 'imagen', opcion_b_imagen),
        'C', json_build_object('texto', opcion_c_texto, 'imagen', opcion_c_imagen),
        'D', json_build_object('texto', opcion_d_texto, 'imagen', opcion_d_imagen)
    ) INTO result
    FROM questions
    WHERE id = question_id;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Insertar datos de ejemplo para testing
INSERT INTO questions (
    topic_id,
    subject_id,
    pregunta_texto,
    pregunta_imagen,
    opcion_a_texto,
    opcion_a_imagen,
    opcion_b_texto,
    opcion_b_imagen,
    opcion_c_texto,
    opcion_c_imagen,
    opcion_d_texto,
    opcion_d_imagen,
    respuesta_correcta,
    difficulty,
    explanation,
    hint,
    is_validated
) VALUES 
-- Pregunta solo texto
(
    (SELECT id FROM topics LIMIT 1),
    (SELECT id FROM subjects LIMIT 1),
    '¿Cuál es la capital de Francia?',
    NULL,
    'Londres',
    NULL,
    'París',
    NULL,
    'Madrid',
    NULL,
    'Roma',
    NULL,
    'b',
    1,
    'París es la capital y ciudad más grande de Francia.',
    'Piensa en la ciudad de la luz',
    'validated'
),
-- Pregunta con imagen
(
    (SELECT id FROM topics LIMIT 1),
    (SELECT id FROM subjects LIMIT 1),
    '¿Qué figura geométrica representa esta imagen?',
    'https://via.placeholder.com/400x300/4F46E5/FFFFFF?text=Cuadrado',
    'Triángulo',
    NULL,
    'Círculo',
    NULL,
    'Cuadrado',
    NULL,
    'Rectángulo',
    NULL,
    'c',
    2,
    'La imagen muestra un cuadrado, que es un polígono de cuatro lados iguales.',
    'Cuenta los lados de la figura',
    'validated'
),
-- Pregunta con opciones multimedia
(
    (SELECT id FROM topics LIMIT 1),
    (SELECT id FROM subjects LIMIT 1),
    'Selecciona la opción correcta:',
    NULL,
    'Opción A',
    'https://via.placeholder.com/200x150/10B981/FFFFFF?text=A',
    'Opción B',
    'https://via.placeholder.com/200x150/F59E0B/FFFFFF?text=B',
    'Opción C',
    'https://via.placeholder.com/200x150/EF4444/FFFFFF?text=C',
    'Opción D',
    'https://via.placeholder.com/200x150/8B5CF6/FFFFFF?text=D',
    'a',
    3,
    'La opción A es la correcta según los criterios establecidos.',
    'Observa los colores en las imágenes',
    'validated'
)
ON CONFLICT DO NOTHING; 