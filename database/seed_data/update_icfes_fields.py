#!/usr/bin/env python3
"""
Script para actualizar los campos ICFES en las preguntas existentes
Toma los datos del Excel y los mapea a las preguntas ya cargadas
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import logging
from datetime import datetime
import sys
import os

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

def update_icfes_fields():
    """Actualizar campos ICFES en preguntas existentes"""
    try:
        logger.info("🔧 Conectando a la base de datos...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        logger.info("📖 Cargando datos del Excel...")
        df = pd.read_excel('database/allquestions/questions.xlsx')
        logger.info(f"📊 Excel cargado: {len(df)} filas")
        
        # Normalizar nombres de columnas
        column_mapping = {}
        for col in df.columns:
            normalized = col.strip().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
            column_mapping[col] = normalized.lower()
        
        df_normalized = df.rename(columns=column_mapping)
        
        logger.info("🔄 Actualizando campos ICFES en preguntas existentes...")
        
        # Obtener todas las preguntas existentes
        cur.execute("SELECT id, question_text FROM questions ORDER BY created_at")
        existing_questions = cur.fetchall()
        
        logger.info(f"📊 Preguntas en BD: {len(existing_questions)}")
        
        updates_made = 0
        
        # Mapear preguntas del Excel con las de la BD por contenido similar
        for idx, (q_id, q_text) in enumerate(existing_questions):
            try:
                # Buscar fila correspondiente en Excel (por índice aproximado)
                if idx < len(df_normalized):
                    excel_row = df_normalized.iloc[idx]
                    
                    # Extraer campos ICFES del Excel
                    area_evaluada = str(excel_row.get('area_evaluada', '')).strip()
                    competencia = str(excel_row.get('competencia', '')).strip()
                    componente = str(excel_row.get('componente', '')).strip()
                    tema_especifico = str(excel_row.get('tema_especifico', '')).strip()
                    proceso_cognitivo = str(excel_row.get('proceso_cognitivo', '')).strip()
                    afirmacion = str(excel_row.get('afirmacion', '')).strip()
                    evidencia = str(excel_row.get('evidencia', '')).strip()
                    
                    # Actualizar la pregunta
                    cur.execute("""
                        UPDATE questions 
                        SET 
                            area_evaluada = %s,
                            competencia = %s,
                            componente = %s,
                            tema_especifico = %s,
                            proceso_cognitivo = %s,
                            afirmacion = %s,
                            evidencia = %s
                        WHERE id = %s
                    """, (
                        area_evaluada if area_evaluada and area_evaluada != 'nan' else None,
                        competencia if competencia and competencia != 'nan' else None,
                        componente if componente and componente != 'nan' else None,
                        tema_especifico if tema_especifico and tema_especifico != 'nan' else None,
                        proceso_cognitivo if proceso_cognitivo and proceso_cognitivo != 'nan' else None,
                        afirmacion if afirmacion and afirmacion != 'nan' else None,
                        evidencia if evidencia and evidencia != 'nan' else None,
                        q_id
                    ))
                    
                    updates_made += 1
                    
                    if updates_made % 100 == 0:
                        logger.info(f"  📊 Actualizadas {updates_made} preguntas...")
                        conn.commit()  # Commit parcial
                        
            except Exception as e:
                logger.warning(f"⚠️ Error actualizando pregunta {idx+1}: {e}")
                continue
        
        # Commit final
        conn.commit()
        logger.info(f"✅ Actualización completada: {updates_made} preguntas")
        
        # Verificar resultado
        cur.execute("SELECT COUNT(*) FROM questions WHERE competencia IS NOT NULL")
        comp_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM questions WHERE area_evaluada IS NOT NULL")
        area_count = cur.fetchone()[0]
        
        logger.info(f"📊 Verificación:")
        logger.info(f"  ✅ Preguntas con competencia: {comp_count}")
        logger.info(f"  ✅ Preguntas con área evaluada: {area_count}")
        
        # Mostrar ejemplos
        cur.execute("""
            SELECT question_text, area_evaluada, competencia, componente
            FROM questions 
            WHERE competencia IS NOT NULL 
            LIMIT 3
        """)
        
        examples = cur.fetchall()
        logger.info(f"\\n📝 Ejemplos actualizados:")
        for q_text, area, comp, component in examples:
            logger.info(f"  📄 {q_text[:50]}...")
            logger.info(f"     Área: {area}")
            logger.info(f"     Competencia: {comp}")
            logger.info(f"     Componente: {component}")
            logger.info("")
        
        cur.close()
        conn.close()
        
        logger.info("🎉 ¡Actualización de campos ICFES completada!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error actualizando campos ICFES: {e}")
        return False

if __name__ == "__main__":
    success = update_icfes_fields()
    sys.exit(0 if success else 1)


