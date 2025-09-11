-- ICFES LEVELING - Estructura completa con 81 campos e importación de datos
-- Este script actualiza la tabla questions con todos los campos ICFES y prepara para importación

-- Crear tabla de logs si no existe para tracking
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    level VARCHAR(10) DEFAULT 'INFO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agregar todos los 81 campos ICFES a la tabla questions si no existen
DO $$
BEGIN
    RAISE NOTICE 'Actualizando estructura de tabla questions con 81 campos ICFES...';
    
    -- Campos básicos del archivo Excel
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS id_pregunta_original VARCHAR(50);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS area_evaluada VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tema_especifico TEXT;
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS grado_escolar VARCHAR(20);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS periodo_aplicacion VARCHAR(50);
    
    -- Campos de imágenes
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS requiere_imagen BOOLEAN DEFAULT FALSE;
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_pregunta_url VARCHAR(500);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_opcion_a_url VARCHAR(500);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_opcion_b_url VARCHAR(500);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_opcion_c_url VARCHAR(500);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_opcion_d_url VARCHAR(500);
    
    -- Campos de gamificación
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS puntos_xp INTEGER DEFAULT 10;
    
    -- Campos de contexto
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS pregunta_con_contexto TEXT;
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS pregunta_libro TEXT;
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS orden_en_contexto INTEGER;
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS contexto_requerido BOOLEAN DEFAULT FALSE;
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_contexto_comp VARCHAR(500);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS texto_contexto_completo TEXT;
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS id_contexto_compartido VARCHAR(50);
    
    -- Campos de archivo
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS ruta_absoluta_archivo TEXT;
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS nombre_del_archivo VARCHAR(255);
    
    -- Campos de categorización
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS subtema VARCHAR(255);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS estrategia_discursiva VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_razonamiento VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS complejidad_cognitiva VARCHAR(50);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS contexto_aplicacion VARCHAR(100);
    
    -- Campos de análisis textual
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_texto VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS genero_textual VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS funcion_comunicativa VARCHAR(100);
    
    -- Campos matemáticos
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS pensamiento_matematico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_problema VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS estrategia_solucion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_representacion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS uso_herramientas VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS nivel_abstraccion VARCHAR(100);
    
    -- Campos científicos
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS disciplina_predominante VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS concepto_cientifico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS proceso_cientifico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS nivel_representacion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_experimento VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS control_variables VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_observacion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS nivel_taxonomico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS sistema_biologico VARCHAR(100);
    
    -- Campos sociales
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS periodo_historico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS ambito_analisis VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS escala_espacial VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS concepto_social VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_fuente VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS contexto_historico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS perspectiva_analisis VARCHAR(100);
    
    -- Campos de comunicación y lenguaje
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS habilidad_comunicativa VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS estructura_textual VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS proposito_comunicativo VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS audiencia_objetivo VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS registro_linguistico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_discurso VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS elemento_retorico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS figura_literaria VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_narracion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS elemento_narrativo VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_descripcion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS punto_vista VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tono_texto VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS intencion_autor VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS contexto_produccion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_intertextualidad VARCHAR(100);
    
    -- Campos de análisis y evaluación
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_grafico VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS interpretacion_datos VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_modelo VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS variables_relacionadas VARCHAR(255);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS escala_temporal VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_cambio VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_interaccion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS nivel_organizacion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_evidencia VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS grado_incertidumbre VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_relacion_causal VARCHAR(100);
    
    -- Campos de argumentación
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_argumento VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS nivel_inferencia VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_conclusion VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS validez_argumento VARCHAR(100);
    ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_falacia VARCHAR(100);
    
    RAISE NOTICE 'Estructura de tabla actualizada con 81 campos ICFES';
    
    -- Registrar en logs
    INSERT INTO logs (message, level, created_at) VALUES 
    ('Questions table structure updated with 81 ICFES fields', 'INFO', NOW());
    
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error actualizando estructura: %', SQLERRM;
    INSERT INTO logs (message, level, created_at) VALUES 
    ('Error updating table structure: ' || SQLERRM, 'ERROR', NOW());
END $$;

-- Verificar si necesitamos importar datos
DO $$
BEGIN
    IF (SELECT COUNT(*) FROM questions) < 100 THEN
        RAISE NOTICE 'Base de datos lista para importación de datos ICFES desde Excel';
        INSERT INTO logs (message, level, created_at) VALUES 
        ('Database ready for ICFES Excel import - Run import script', 'INFO', NOW());
    ELSE
        RAISE NOTICE 'Datos ya cargados. Total preguntas: %', (SELECT COUNT(*) FROM questions);
    END IF;
END $$;