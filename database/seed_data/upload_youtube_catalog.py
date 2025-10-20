#!/usr/bin/env python3
"""
Script para cargar el catálogo de videos de YouTube a la base de datos
Procesa tanto el archivo YAML como el CSV enriquecido
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch, Json
import uuid
import yaml
import logging
from datetime import datetime
import sys
import os
import re

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

# Mapeo de áreas a subject_id (incluye variantes de codificación)
SUBJECT_MAPPING = {
    'Matemáticas': '550e8400-e29b-41d4-a716-446655440001',
    'Matematicas': '550e8400-e29b-41d4-a716-446655440001',
    'Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
    'Lectura Crítica': '550e8400-e29b-41d4-a716-446655440002',
    'Lectura Critica': '550e8400-e29b-41d4-a716-446655440002',
    'Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
    'Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
    'Sociales y Competencias Ciudadanas': '550e8400-e29b-41d4-a716-446655440004',
    'Inglés': '550e8400-e29b-41d4-a716-446655440005',
    'InglÃ©s': '550e8400-e29b-41d4-a716-446655440005'  # Problema de codificación
}

class YouTubeCatalogUploader:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.stats = {
            'videos_loaded': 0,
            'topics_matched': 0,
            'errors': 0
        }
        
    def connect_db(self):
        """Conectar a la base de datos"""
        try:
            logger.info("Conectando a la base de datos...")
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.cur = self.conn.cursor()
            logger.info("✅ Conexión exitosa a la base de datos")
            return True
        except Exception as e:
            logger.error(f"❌ Error conectando a la base de datos: {e}")
            return False
    
    def create_youtube_catalog_table(self):
        """Crear tabla para el catálogo de YouTube si no existe"""
        try:
            logger.info("🔧 Creando tabla youtube_catalog...")
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS youtube_catalog (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                subject_id UUID REFERENCES subjects(id),
                topic_id UUID,
                codigo_tema VARCHAR(50),
                youtube_id VARCHAR(50) NOT NULL,
                youtube_url VARCHAR(500) NOT NULL,
                title VARCHAR(300) NOT NULL,
                channel_name VARCHAR(200),
                channel_id VARCHAR(100),
                duration_minutes INTEGER DEFAULT 0,
                difficulty_level VARCHAR(20) DEFAULT 'intermediate',
                quality_score DECIMAL(3,2) DEFAULT 0.80,
                views_count INTEGER DEFAULT 0,
                likes_count INTEGER DEFAULT 0,
                publish_date DATE,
                language VARCHAR(10) DEFAULT 'es',
                topics_covered TEXT[],
                icfes_competence VARCHAR(200),
                icfes_component VARCHAR(200),
                description TEXT,
                transcript TEXT,
                tags TEXT[],
                is_active BOOLEAN DEFAULT TRUE,
                effectiveness_score DECIMAL(3,2) DEFAULT 0.80,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(youtube_id, subject_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_youtube_catalog_subject ON youtube_catalog(subject_id);
            CREATE INDEX IF NOT EXISTS idx_youtube_catalog_topic ON youtube_catalog(topic_id);
            CREATE INDEX IF NOT EXISTS idx_youtube_catalog_codigo ON youtube_catalog(codigo_tema);
            CREATE INDEX IF NOT EXISTS idx_youtube_catalog_difficulty ON youtube_catalog(difficulty_level);
            CREATE INDEX IF NOT EXISTS idx_youtube_catalog_quality ON youtube_catalog(quality_score);
            """
            
            self.cur.execute(create_table_sql)
            self.conn.commit()
            logger.info("✅ Tabla youtube_catalog creada/verificada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando tabla: {e}")
            return False
    
    def extract_youtube_id(self, url):
        """Extraer YouTube ID de una URL"""
        if not url:
            return None
            
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]+)',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def load_from_csv(self, csv_path):
        """Cargar videos desde el archivo CSV enriquecido"""
        try:
            logger.info(f"📊 Cargando videos desde CSV: {csv_path}")
            # Probar diferentes codificaciones
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(csv_path, delimiter=';', encoding=encoding)
                    logger.info(f"✅ CSV cargado con codificación {encoding}: {len(df)} filas")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise Exception("No se pudo leer el archivo CSV con ninguna codificación")
            
            videos_data = []
            
            for idx, row in df.iterrows():
                try:
                    # Extraer información básica
                    codigo_tema = str(row.get('codigo_tema', f'TEMA_{idx+1}')).strip()
                    area_evaluada = str(row.get('area_evaluada', '')).strip()
                    tema_principal = str(row.get('tema_principal', 'General')).strip()
                    canal_sugerido = str(row.get('canal_sugerido', '')).strip()
                    youtube_url = str(row.get('youtube_url', '')).strip()
                    
                    # Mapear área a subject_id
                    subject_id = SUBJECT_MAPPING.get(area_evaluada)
                    if not subject_id:
                        logger.warning(f"⚠️ Área no reconocida: '{area_evaluada}' en fila {idx+1}")
                        continue
                    
                    # Extraer YouTube ID
                    youtube_id = self.extract_youtube_id(youtube_url)
                    if not youtube_id:
                        logger.warning(f"⚠️ URL de YouTube inválida: '{youtube_url}' en fila {idx+1}")
                        continue
                    
                    # Buscar topic_id basado en tema_principal
                    topic_id = self.find_topic_id(tema_principal, subject_id)
                    
                    # Preparar datos del video
                    video_data = (
                        str(uuid.uuid4()),  # id
                        subject_id,         # subject_id
                        topic_id,          # topic_id (puede ser None)
                        codigo_tema,       # codigo_tema
                        youtube_id,        # youtube_id
                        youtube_url,       # youtube_url
                        tema_principal,    # title
                        canal_sugerido.replace('@', ''),  # channel_name
                        None,              # channel_id
                        15,                # duration_minutes (default)
                        'intermediate',    # difficulty_level
                        0.80,              # quality_score
                        0,                 # views_count
                        0,                 # likes_count
                        None,              # publish_date
                        'es',              # language
                        [tema_principal, area_evaluada],  # topics_covered
                        None,              # icfes_competence
                        None,              # icfes_component
                        f"Video sobre {tema_principal} en {area_evaluada}",  # description
                        None,              # transcript
                        [codigo_tema, area_evaluada, tema_principal],  # tags
                        True,              # is_active
                        0.80,              # effectiveness_score
                        datetime.now(),    # created_at
                        datetime.now()     # updated_at
                    )
                    
                    videos_data.append(video_data)
                    
                    # Insertar en lotes de 50
                    if len(videos_data) >= 50:
                        self.insert_videos_batch(videos_data)
                        videos_data = []
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando fila {idx+1}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            # Insertar último lote
            if videos_data:
                self.insert_videos_batch(videos_data)
            
            logger.info("✅ Carga desde CSV completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando CSV: {e}")
            return False
    
    def find_topic_id(self, tema_principal, subject_id):
        """Buscar topic_id basado en el tema principal"""
        try:
            # Buscar tópico exacto
            self.cur.execute(
                "SELECT id FROM topics WHERE name ILIKE %s AND subject_id = %s LIMIT 1",
                (f"%{tema_principal}%", subject_id)
            )
            result = self.cur.fetchone()
            if result:
                return result[0]
            
            # Si no se encuentra, buscar por palabras clave
            keywords = tema_principal.split()[:2]  # Primeras 2 palabras
            for keyword in keywords:
                if len(keyword) > 3:  # Solo palabras significativas
                    self.cur.execute(
                        "SELECT id FROM topics WHERE name ILIKE %s AND subject_id = %s LIMIT 1",
                        (f"%{keyword}%", subject_id)
                    )
                    result = self.cur.fetchone()
                    if result:
                        return result[0]
            
            return None
            
        except Exception as e:
            logger.warning(f"Error buscando topic para '{tema_principal}': {e}")
            return None
    
    def insert_videos_batch(self, videos_data):
        """Insertar lote de videos"""
        try:
            execute_batch(
                self.cur,
                """INSERT INTO youtube_catalog (
                    id, subject_id, topic_id, codigo_tema, youtube_id, youtube_url,
                    title, channel_name, channel_id, duration_minutes, difficulty_level,
                    quality_score, views_count, likes_count, publish_date, language,
                    topics_covered, icfes_competence, icfes_component, description,
                    transcript, tags, is_active, effectiveness_score, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (youtube_id, subject_id) DO NOTHING""",
                videos_data
            )
            self.conn.commit()
            self.stats['videos_loaded'] += len(videos_data)
            logger.info(f"✅ Insertados {len(videos_data)} videos (Total: {self.stats['videos_loaded']})")
        except Exception as e:
            logger.error(f"❌ Error insertando lote de videos: {e}")
            self.conn.rollback()
            self.stats['errors'] += len(videos_data)
    
    def verify_upload(self):
        """Verificar la carga de videos"""
        try:
            # Contar videos por materia
            self.cur.execute("""
                SELECT 
                    s.name as subject_name,
                    COUNT(yc.id) as video_count
                FROM subjects s
                LEFT JOIN youtube_catalog yc ON s.id = yc.subject_id
                GROUP BY s.id, s.name
                ORDER BY video_count DESC
            """)
            
            results = self.cur.fetchall()
            
            logger.info("\n📊 VERIFICACIÓN DE VIDEOS:")
            logger.info("=" * 50)
            total_videos = 0
            for subject_name, count in results:
                logger.info(f"  📺 {subject_name}: {count} videos")
                total_videos += count
            
            logger.info(f"\n🎯 RESUMEN FINAL:")
            logger.info(f"  ✅ Videos cargados: {self.stats['videos_loaded']}")
            logger.info(f"  📊 Total en BD: {total_videos}")
            logger.info(f"  ❌ Errores: {self.stats['errors']}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verificando carga: {e}")
            return False
    
    def run(self):
        """Ejecutar proceso completo"""
        logger.info("🚀 Iniciando carga de catálogo de YouTube...")
        
        if not self.connect_db():
            return False
        
        try:
            # Crear tabla si no existe
            if not self.create_youtube_catalog_table():
                return False
            
            # Cargar desde CSV
            csv_path = "database/seed_data/youtube_catalog_extendido_enriquecido.csv"
            if os.path.exists(csv_path):
                self.load_from_csv(csv_path)
            else:
                logger.warning(f"⚠️ Archivo CSV no encontrado: {csv_path}")
            
            # Verificar carga
            self.verify_upload()
            
            logger.info("🎉 ¡Carga de catálogo YouTube completada!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en proceso principal: {e}")
            return False
        finally:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()

def main():
    """Función principal"""
    uploader = YouTubeCatalogUploader()
    success = uploader.run()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
