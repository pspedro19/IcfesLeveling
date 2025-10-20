#!/usr/bin/env python3
"""
Script para corregir preguntas multimedia donde el texto está en imágenes
Actualiza las preguntas para que sean utilizables por el frontend
"""

import psycopg2
import os
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de base de datos
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5433'),
    'database': os.getenv('DB_NAME', 'gameplay_db'),
    'user': os.getenv('DB_USER', 'gameplay'),
    'password': os.getenv('DB_PASSWORD', 'gameplay123')
}

def fix_multimedia_questions():
    """Corregir preguntas multimedia para que sean utilizables"""
    try:
        logger.info("🔧 Conectando a la base de datos...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        logger.info("🔍 Analizando preguntas multimedia...")
        
        # Obtener preguntas que tienen "No Aplica" como texto
        cur.execute("""
            SELECT id, subject_id, question_text, imagen_pregunta_url, 
                   afirmacion, evidencia, tema_especifico
            FROM questions 
            WHERE question_text LIKE '%No Aplica%' 
            LIMIT 10
        """)
        
        multimedia_questions = cur.fetchall()
        logger.info(f"📊 Encontradas {len(multimedia_questions)} preguntas multimedia de muestra")
        
        if not multimedia_questions:
            logger.info("✅ No hay preguntas multimedia que corregir")
            return True
        
        # Actualizar preguntas multimedia con texto descriptivo
        updates_made = 0
        
        for q_id, subject_id, current_text, image_url, afirmacion, evidencia, tema in multimedia_questions:
            try:
                # Crear texto descriptivo basado en los metadatos disponibles
                new_text = f"[PREGUNTA MULTIMEDIA] {tema or 'Pregunta con imagen'}"
                
                if afirmacion and afirmacion.strip() and afirmacion != 'No Aplica':
                    new_text = f"Pregunta sobre: {afirmacion[:100]}..."
                elif evidencia and evidencia.strip() and evidencia != 'No Aplica':
                    new_text = f"Evalúa: {evidencia[:100]}..."
                
                # Actualizar la pregunta
                cur.execute("""
                    UPDATE questions 
                    SET question_text = %s,
                        pregunta_texto = %s,
                        requiere_imagen = TRUE
                    WHERE id = %s
                """, (new_text, new_text, q_id))
                
                updates_made += 1
                
            except Exception as e:
                logger.warning(f"Error actualizando pregunta {q_id}: {e}")
        
        # Actualizar todas las preguntas "No Aplica" restantes
        cur.execute("""
            UPDATE questions 
            SET question_text = CASE 
                WHEN afirmacion IS NOT NULL AND afirmacion != 'No Aplica' 
                THEN 'Pregunta multimedia: ' || LEFT(afirmacion, 100) || '...'
                WHEN evidencia IS NOT NULL AND evidencia != 'No Aplica'
                THEN 'Evalúa: ' || LEFT(evidencia, 100) || '...'
                WHEN tema_especifico IS NOT NULL 
                THEN '[MULTIMEDIA] ' || tema_especifico
                ELSE '[PREGUNTA MULTIMEDIA] Ver imagen para contenido completo'
            END,
            pregunta_texto = CASE 
                WHEN afirmacion IS NOT NULL AND afirmacion != 'No Aplica' 
                THEN 'Pregunta multimedia: ' || LEFT(afirmacion, 100) || '...'
                WHEN evidencia IS NOT NULL AND evidencia != 'No Aplica'
                THEN 'Evalúa: ' || LEFT(evidencia, 100) || '...'
                WHEN tema_especifico IS NOT NULL 
                THEN '[MULTIMEDIA] ' || tema_especifico
                ELSE '[PREGUNTA MULTIMEDIA] Ver imagen para contenido completo'
            END,
            requiere_imagen = TRUE
            WHERE question_text LIKE '%No Aplica%'
        """)
        
        rows_updated = cur.rowcount
        conn.commit()
        
        logger.info(f"✅ Actualizadas {rows_updated} preguntas multimedia")
        
        # Verificar resultado
        cur.execute("SELECT COUNT(*) FROM questions WHERE question_text NOT LIKE '%No Aplica%'")
        valid_questions = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM questions WHERE requiere_imagen = TRUE")
        multimedia_count = cur.fetchone()[0]
        
        logger.info(f"📊 Resultado:")
        logger.info(f"   ✅ Preguntas con texto válido: {valid_questions}")
        logger.info(f"   🖼️ Preguntas multimedia: {multimedia_count}")
        
        # Mostrar ejemplos actualizados
        cur.execute("""
            SELECT id, question_text, tema_especifico, imagen_pregunta_url
            FROM questions 
            WHERE requiere_imagen = TRUE
            LIMIT 3
        """)
        
        examples = cur.fetchall()
        logger.info(f"\n📝 Ejemplos de preguntas actualizadas:")
        for q_id, text, tema, image_url in examples:
            logger.info(f"   ID: {q_id}")
            logger.info(f"   Texto: {text}")
            logger.info(f"   Tema: {tema}")
            logger.info(f"   Imagen: {image_url[:50]}..." if image_url else "   Imagen: No disponible")
            logger.info("")
        
        cur.close()
        conn.close()
        
        logger.info("🎉 Corrección de preguntas multimedia completada")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error corrigiendo preguntas multimedia: {e}")
        return False

if __name__ == "__main__":
    success = fix_multimedia_questions()
    exit(0 if success else 1)
