#!/usr/bin/env python3
"""
CARGADOR AUTOMÁTICO DE DATOS ICFES LEVELING
===========================================

Este script se ejecuta automáticamente al inicializar la base de datos
y carga todos los datos necesarios de forma idempotente (no duplica datos).

Rutas de datos:
- Excel ICFES: /data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx
- CSV YouTube: /docker-entrypoint-initdb.d/youtube_catalog_extendido_enriquecido.csv
- CSV Topics: /docker-entrypoint-initdb.d/topics_catalog.csv
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import uuid
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de conexión a base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'gameplay_db',
    'user': 'gameplay',
    'password': 'gameplay123'
}

# Rutas de archivos de datos (Updated to new consolidated structure)
DATA_PATHS = {
    'excel_questions': '/seed_data/allquestions/questions.xlsx',
    'csv_youtube': '/seed_data/catalogs/youtube_catalog_complete.csv',
    'csv_topics': '/seed_data/catalogs/icfes_topics.csv'
}

def get_db_connection():
    """Crear conexión a la base de datos"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None

def check_data_status(conn):
    """Verificar el estado actual de los datos"""
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    status = {}
    
    # Verificar Questions
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN competencia IS NOT NULL AND competencia != '' THEN 1 END) as with_competencia,
            COUNT(CASE WHEN pregunta_texto IS NOT NULL AND pregunta_texto != '' THEN 1 END) as with_text
        FROM questions
    """)
    questions_data = cursor.fetchone()
    status['questions'] = {
        'total': questions_data['total'],
        'with_icfes_data': questions_data['with_competencia'],
        'with_text': questions_data['with_text'],
        'needs_loading': questions_data['with_competencia'] == 0 or questions_data['total'] < 400
    }
    
    # Verificar YouTube Catalog
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN codigo_tema IS NOT NULL AND codigo_tema != '' THEN 1 END) as with_codigo,
            COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) as with_title
        FROM youtube_catalog
    """)
    youtube_data = cursor.fetchone()
    status['youtube'] = {
        'total': youtube_data['total'],
        'with_codigo_tema': youtube_data['with_codigo'],
        'with_title': youtube_data['with_title'],
        'needs_loading': youtube_data['total'] < 50
    }
    
    # Verificar Topics
    cursor.execute("SELECT COUNT(*) as total FROM topics")
    topics_data = cursor.fetchone()
    status['topics'] = {
        'total': topics_data['total'],
        'needs_loading': topics_data['total'] < 400
    }
    
    cursor.close()
    return status

def load_youtube_catalog_from_csv(conn):
    """Cargar catálogo de YouTube desde CSV"""
    csv_path = DATA_PATHS['csv_youtube']
    
    if not os.path.exists(csv_path):
        # Buscar en ubicaciones alternativas
        alt_paths = [
            '/docker-entrypoint-initdb.d/../seed_data/youtube_catalog_extendido_enriquecido.csv',
            '/app/seed_data/youtube_catalog_extendido_enriquecido.csv'
        ]
        
        for alt_path in alt_paths:
            if os.path.exists(alt_path):
                csv_path = alt_path
                break
        else:
            logger.error(f"No se encontró el archivo CSV de YouTube en ninguna ubicación")
            return False
    
    try:
        logger.info(f"Cargando catálogo YouTube desde: {csv_path}")
        
        # Leer CSV con el separador correcto
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
        logger.info(f"CSV leído: {len(df)} filas, columnas: {list(df.columns)}")
        
        cursor = conn.cursor()
        videos_added = 0
        
        # Mapear subjects
        subject_map = {
            'Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
            'Matemáticas': '550e8400-e29b-41d4-a716-446655440001', 
            'Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
            'Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
            'Inglés': '550e8400-e29b-41d4-a716-446655440005'
        }
        
        for _, row in df.iterrows():
            try:
                # Extraer video_id de la URL de YouTube
                youtube_url = str(row.get('youtube_url', ''))
                if 'youtube.com/watch?v=' in youtube_url:
                    video_id = youtube_url.split('v=')[1].split('&')[0]
                elif 'youtu.be/' in youtube_url:
                    video_id = youtube_url.split('youtu.be/')[1].split('?')[0]
                else:
                    continue
                
                # Verificar si ya existe
                cursor.execute("SELECT id FROM youtube_catalog WHERE video_id = %s", (video_id,))
                if cursor.fetchone():
                    continue
                    
                area_evaluada = str(row.get('area_evaluada', '')).strip()
                subject_id = subject_map.get(area_evaluada)
                
                if not subject_id:
                    logger.warning(f"Subject no encontrado para: {area_evaluada}")
                    continue
                
                # Buscar topic_id por codigo_tema si existe
                codigo_tema = str(row.get('codigo_tema', '')).strip()
                topic_id = None
                if codigo_tema:
                    cursor.execute("SELECT id FROM topics WHERE codigo_tema = %s", (codigo_tema,))
                    topic_result = cursor.fetchone()
                    if topic_result:
                        topic_id = topic_result[0]
                
                # Insertar video
                insert_query = """
                INSERT INTO youtube_catalog (
                    video_id, title, url, embed_url, subject_id, topic_id,
                    codigo_tema, area_evaluada, tema_principal, canal_sugerido,
                    transcript, tema_tag, difficulty_level, is_active, is_verified,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )"""
                
                values = (
                    video_id,
                    str(row.get('tema_principal', ''))[:200],
                    youtube_url,
                    f"https://www.youtube.com/embed/{video_id}",
                    subject_id,
                    topic_id,
                    codigo_tema,
                    area_evaluada,
                    str(row.get('tema_principal', ''))[:200],
                    str(row.get('canal_sugerido', ''))[:100],
                    str(row.get('transcript', '')),
                    str(row.get('tema tag', ''))[:200],
                    'intermedio',
                    True,
                    True,
                    datetime.now(),
                    datetime.now()
                )
                
                cursor.execute(insert_query, values)
                videos_added += 1
                
            except Exception as e:
                logger.error(f"Error procesando fila {videos_added}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        logger.info(f"✅ Catálogo YouTube cargado: {videos_added} videos añadidos")
        return True
        
    except Exception as e:
        logger.error(f"Error cargando catálogo YouTube: {e}")
        return False

def load_icfes_questions_from_excel(conn):
    """Cargar preguntas ICFES desde Excel"""
    excel_path = DATA_PATHS['excel_questions']
    
    if not os.path.exists(excel_path):
        logger.error(f"No se encontró el archivo Excel: {excel_path}")
        return False
    
    try:
        logger.info(f"Cargando preguntas ICFES desde: {excel_path}")
        
        # Leer Excel
        df = pd.read_excel(excel_path)
        logger.info(f"Excel leído: {len(df)} filas, columnas: {list(df.columns)}")
        
        cursor = conn.cursor()
        questions_updated = 0
        
        # Mapear subjects
        subject_map = {
            'CIENCIAS NATURALES': '550e8400-e29b-41d4-a716-446655440003',
            'MATEMÁTICAS': '550e8400-e29b-41d4-a716-446655440001',
            'LENGUAJE': '550e8400-e29b-41d4-a716-446655440002', 
            'CIENCIAS SOCIALES': '550e8400-e29b-41d4-a716-446655440004',
            'INGLÉS': '550e8400-e29b-41d4-a716-446655440005'
        }
        
        for _, row in df.iterrows():
            try:
                pregunta_texto = str(row.get('Pregunta', '')).strip()
                if not pregunta_texto or pregunta_texto == 'nan':
                    continue
                
                # Buscar pregunta existente por texto
                cursor.execute(
                    "SELECT id FROM questions WHERE pregunta_texto = %s LIMIT 1", 
                    (pregunta_texto,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    question_id = existing[0]
                    
                    # Actualizar con datos ICFES
                    update_query = """
                    UPDATE questions SET
                        competencia = %s,
                        componente = %s,
                        proceso_cognitivo = %s,
                        tipo_conocimiento = %s,
                        afirmacion = %s,
                        evidencia = %s,
                        nivel_desempeno_esperado = %s,
                        tiempo_estimado = %s,
                        explicacion_respuesta = %s,
                        error_comun = %s,
                        parametro_irt_b = %s,
                        parametro_irt_a = %s
                    WHERE id = %s
                    """
                    
                    values = (
                        str(row.get('Competencia', ''))[:150],
                        str(row.get('Componente', ''))[:100],
                        str(row.get('Proceso_Cognitivo', ''))[:50],
                        str(row.get('Tipo_Conocimiento', ''))[:50],
                        str(row.get('Afirmacion', '')),
                        str(row.get('Evidencia', '')),
                        str(row.get('Nivel_Desempeno', ''))[:30],
                        int(row.get('Tiempo_Estimado', 120)),
                        str(row.get('Explicacion_Respuesta', '')),
                        str(row.get('Error_Comun', '')),
                        float(row.get('Dificultad_IRT', 0.0)),
                        float(row.get('Discriminacion_IRT', 1.0)),
                        question_id
                    )
                    
                    cursor.execute(update_query, values)
                    questions_updated += 1
                
            except Exception as e:
                logger.error(f"Error procesando pregunta {questions_updated}: {e}")
                continue
        
        conn.commit()
        cursor.close()
        logger.info(f"✅ Preguntas ICFES actualizadas: {questions_updated}")
        return True
        
    except Exception as e:
        logger.error(f"Error cargando preguntas ICFES: {e}")
        return False

def main():
    """Función principal"""
    logger.info("🚀 INICIANDO CARGA AUTOMÁTICA DE DATOS ICFES LEVELING")
    
    # Conectar a base de datos
    conn = get_db_connection()
    if not conn:
        logger.error("❌ No se pudo conectar a la base de datos")
        sys.exit(1)
    
    try:
        # Verificar estado actual
        status = check_data_status(conn)
        logger.info("📊 Estado actual de datos:")
        for table, data in status.items():
            logger.info(f"  {table}: {data}")
        
        # Cargar YouTube Catalog si es necesario
        if status['youtube']['needs_loading']:
            logger.info("📺 Cargando catálogo de YouTube...")
            if load_youtube_catalog_from_csv(conn):
                logger.info("✅ Catálogo YouTube cargado exitosamente")
            else:
                logger.error("❌ Error cargando catálogo YouTube")
        else:
            logger.info("✅ Catálogo YouTube ya está cargado")
        
        # Cargar/actualizar preguntas ICFES si es necesario
        if status['questions']['needs_loading']:
            logger.info("📚 Cargando/actualizando preguntas ICFES...")
            if load_icfes_questions_from_excel(conn):
                logger.info("✅ Preguntas ICFES cargadas/actualizadas exitosamente")
            else:
                logger.error("❌ Error cargando preguntas ICFES")
        else:
            logger.info("✅ Preguntas ICFES ya están cargadas")
        
        # Verificar estado final
        final_status = check_data_status(conn)
        logger.info("📊 Estado final de datos:")
        for table, data in final_status.items():
            logger.info(f"  {table}: {data}")
        
        logger.info("🎉 CARGA AUTOMÁTICA DE DATOS COMPLETADA")
        
    except Exception as e:
        logger.error(f"❌ Error en carga automática: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    main()