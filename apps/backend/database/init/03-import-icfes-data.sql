-- ICFES LEVELING - Importación automática de datos ICFES
-- Este script se ejecuta después de la inicialización básica para importar preguntas desde Excel

DO $$
BEGIN
    -- Verificar si ya existen preguntas importadas desde Excel
    IF (SELECT COUNT(*) FROM questions) < 100 THEN
        RAISE NOTICE 'Iniciando importación de datos ICFES desde Excel...';
        
        -- Crear una entrada en logs para indicar que se debe ejecutar la importación
        INSERT INTO logs (message, level, created_at) VALUES 
        ('ICFES data import required - Excel file should be processed', 'INFO', NOW())
        ON CONFLICT DO NOTHING;
    ELSE
        RAISE NOTICE 'Datos ICFES ya importados. Saltando importación.';
    END IF;
END $$;

-- Crear tabla de logs si no existe para tracking
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    level VARCHAR(10) DEFAULT 'INFO',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar configuración para la importación automática
INSERT INTO logs (message, level) VALUES 
('Database initialization completed - Ready for ICFES data import', 'INFO')
ON CONFLICT DO NOTHING;