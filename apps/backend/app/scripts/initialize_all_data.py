#!/usr/bin/env python3
"""
Complete database initialization script for ICFES Leveling
Loads all CSV and Excel files into the database
"""

import sys
import os
import logging
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import uuid
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ICFESDataLoader:
    def __init__(self):
        """Initialize database connection"""
        self.conn_params = {
            'host': os.getenv('DB_HOST', 'postgres'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'gameplay_db'),
            'user': os.getenv('DB_USER', 'gameplay'),
            'password': os.getenv('DB_PASSWORD', '')
        }
        self.conn = None
        self.cur = None
        
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
            self.cur = self.conn.cursor()
            logger.info("✅ Connected to database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
            
    def load_icfes_topics_catalog(self, filepath='/app/database/catalogs/icfes_topics.csv'):
        """Load ICFES topics catalog from CSV"""
        try:
            logger.info(f"📚 Loading ICFES topics catalog from {filepath}")
            
            # Check if file exists
            if not os.path.exists(filepath):
                logger.warning(f"⚠️ ICFES topics catalog not found at {filepath}")
                return False
            
            # Read CSV
            df = pd.read_csv(filepath)
            logger.info(f"   Found {len(df)} topics to load")
            
            # Create table if not exists
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS icfes_topics_catalog (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    codigo_tema VARCHAR(50) UNIQUE NOT NULL,
                    area_evaluada VARCHAR(100),
                    tema_principal VARCHAR(200),
                    subtema VARCHAR(200),
                    tema_especifico VARCHAR(500),
                    competencia_icfes VARCHAR(200),
                    componente VARCHAR(200),
                    afirmacion VARCHAR(500),
                    evidencia VARCHAR(500),
                    grado_introduccion VARCHAR(20),
                    prerequisitos TEXT,
                    temas_relacionados TEXT,
                    orden_secuencial INTEGER,
                    nivel_dificultad INTEGER,
                    importancia_icfes INTEGER,
                    frecuencia_evaluacion DECIMAL,
                    horas_teoria INTEGER,
                    horas_practica INTEGER,
                    numero_ejercicios_recomendados INTEGER,
                    sesiones_refuerzo INTEGER,
                    recursos_teoria TEXT,
                    recursos_practica TEXT,
                    recursos_evaluacion TEXT,
                    umbral_dominio DECIMAL,
                    tiempo_retencion INTEGER,
                    indicadores_dominio TEXT,
                    estilo_aprendizaje_optimo VARCHAR(100),
                    metodologia_recomendada VARCHAR(100),
                    tipo_evaluacion VARCHAR(100),
                    estado VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Clear existing data
            self.cur.execute("DELETE FROM icfes_topics_catalog;")
            
            # Prepare data for insertion
            records = []
            for _, row in df.iterrows():
                records.append((
                    str(uuid.uuid4()),
                    row.get('codigo_tema', ''),
                    row.get('area_evaluada', ''),
                    row.get('tema_principal', ''),
                    row.get('subtema', ''),
                    row.get('tema_especifico', ''),
                    row.get('competencia_icfes', ''),
                    row.get('componente', ''),
                    row.get('afirmacion', ''),
                    row.get('evidencia', ''),
                    row.get('grado_introduccion', ''),
                    row.get('prerequisitos', '{}'),
                    row.get('temas_relacionados', '{}'),
                    int(row.get('orden_secuencial', 0)),
                    int(row.get('nivel_dificultad', 1)),
                    int(row.get('importancia_icfes', 3)),
                    float(row.get('frecuencia_evaluacion', 0)),
                    int(row.get('horas_teoria', 0)),
                    int(row.get('horas_practica', 0)),
                    int(row.get('numero_ejercicios_recomendados', 0)),
                    int(row.get('sesiones_refuerzo', 0)),
                    row.get('recursos_teoria', '{}'),
                    row.get('recursos_practica', '{}'),
                    row.get('recursos_evaluacion', '{}'),
                    float(row.get('umbral_dominio', 70.0)),
                    int(row.get('tiempo_retencion', 14)),
                    row.get('indicadores_dominio', '{}'),
                    row.get('estilo_aprendizaje_optimo', ''),
                    row.get('metodologia_recomendada', ''),
                    row.get('tipo_evaluacion', ''),
                    row.get('estado', 'activo')
                ))
            
            # Insert data
            query = """
                INSERT INTO icfes_topics_catalog (
                    id, codigo_tema, area_evaluada, tema_principal, subtema, 
                    tema_especifico, competencia_icfes, componente, afirmacion, evidencia,
                    grado_introduccion, prerequisitos, temas_relacionados, orden_secuencial,
                    nivel_dificultad, importancia_icfes, frecuencia_evaluacion, horas_teoria,
                    horas_practica, numero_ejercicios_recomendados, sesiones_refuerzo,
                    recursos_teoria, recursos_practica, recursos_evaluacion, umbral_dominio,
                    tiempo_retencion, indicadores_dominio, estilo_aprendizaje_optimo,
                    metodologia_recomendada, tipo_evaluacion, estado
                ) VALUES %s
            """
            execute_values(self.cur, query, records)
            self.conn.commit()
            
            logger.info(f"✅ Loaded {len(records)} topics into icfes_topics_catalog")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading ICFES topics catalog: {e}")
            self.conn.rollback()
            return False
    
    def load_youtube_catalog(self, filepath='/app/database/catalogs/youtube_catalog_complete.csv'):
        """Load YouTube video catalog from CSV"""
        try:
            logger.info(f"📺 Loading YouTube catalog from {filepath}")
            
            # Check if file exists
            if not os.path.exists(filepath):
                logger.warning(f"⚠️ YouTube catalog not found at {filepath}")
                return False
            
            # Read CSV
            df = pd.read_csv(filepath)
            logger.info(f"   Found {len(df)} videos to load")
            
            # Create table if not exists
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS youtube_catalog (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    codigo_tema VARCHAR(50),
                    area_evaluada VARCHAR(100),
                    tema_principal VARCHAR(200),
                    canal_sugerido VARCHAR(200),
                    youtube_url VARCHAR(500),
                    youtube_video_id VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Clear existing data
            self.cur.execute("DELETE FROM youtube_catalog;")
            
            # Prepare data for insertion
            records = []
            for _, row in df.iterrows():
                records.append((
                    str(uuid.uuid4()),
                    row.get('codigo_tema', ''),
                    row.get('area_evaluada', ''),
                    row.get('tema_principal', ''),
                    row.get('canal_sugerido', ''),
                    row.get('youtube_url', ''),
                    row.get('youtube_video_id', '')
                ))
            
            # Insert data
            query = """
                INSERT INTO youtube_catalog (
                    id, codigo_tema, area_evaluada, tema_principal, 
                    canal_sugerido, youtube_url, youtube_video_id
                ) VALUES %s
            """
            execute_values(self.cur, query, records)
            self.conn.commit()
            
            logger.info(f"✅ Loaded {len(records)} videos into youtube_catalog")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading YouTube catalog: {e}")
            self.conn.rollback()
            return False
    
    def load_study_plan_templates(self, filepath='/app/database/catalogs/study_plan_templates.csv'):
        """Load study plan templates from CSV"""
        try:
            logger.info(f"📋 Loading study plan templates from {filepath}")
            
            # Check if file exists
            if not os.path.exists(filepath):
                logger.warning(f"⚠️ Study plan templates not found at {filepath}")
                return False
            
            # Read CSV
            df = pd.read_csv(filepath)
            logger.info(f"   Found {len(df)} study plan templates to load")
            
            # Create table if not exists
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS study_plan_templates (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    subject_id UUID,
                    subject_name VARCHAR(100),
                    unit_number INTEGER,
                    unit_name VARCHAR(200),
                    unit_description TEXT,
                    topics TEXT,
                    recommendations_priority VARCHAR(50),
                    weak_areas TEXT,
                    focus_topics TEXT,
                    study_time VARCHAR(50),
                    difficulty_level INTEGER,
                    icfes_weight DECIMAL,
                    estimated_hours INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Clear existing data
            self.cur.execute("DELETE FROM study_plan_templates;")
            
            # Prepare data for insertion
            records = []
            for _, row in df.iterrows():
                # Try to use existing subject_id or generate new one
                subject_id = row.get('subject_id', '')
                if not subject_id or pd.isna(subject_id):
                    subject_id = str(uuid.uuid4())
                    
                records.append((
                    str(uuid.uuid4()),
                    subject_id,
                    row.get('subject_name', ''),
                    int(row.get('unit_number', 1)),
                    row.get('unit_name', ''),
                    row.get('unit_description', ''),
                    row.get('topics', ''),
                    row.get('recommendations_priority', 'medium'),
                    row.get('weak_areas', ''),
                    row.get('focus_topics', ''),
                    row.get('study_time', ''),
                    int(row.get('difficulty_level', 1)),
                    float(row.get('icfes_weight', 0.2)),
                    int(row.get('estimated_hours', 4))
                ))
            
            # Insert data
            query = """
                INSERT INTO study_plan_templates (
                    id, subject_id, subject_name, unit_number, unit_name,
                    unit_description, topics, recommendations_priority,
                    weak_areas, focus_topics, study_time, difficulty_level,
                    icfes_weight, estimated_hours
                ) VALUES %s
            """
            execute_values(self.cur, query, records)
            self.conn.commit()
            
            logger.info(f"✅ Loaded {len(records)} study plan templates")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading study plan templates: {e}")
            self.conn.rollback()
            return False
    
    def load_icfes_questions(self, filepath='/app/database/allquestions/questions.xlsx'):
        """Load ICFES questions from Excel file"""
        try:
            logger.info(f"📝 Loading ICFES questions from {filepath}")
            
            # Check if file exists
            if not os.path.exists(filepath):
                logger.warning(f"⚠️ ICFES questions file not found at {filepath}")
                return False
            
            # Read Excel file
            df = pd.read_excel(filepath)
            logger.info(f"   Found {len(df)} questions to load")
            
            # Create questions table if not exists
            self.cur.execute("""
                CREATE TABLE IF NOT EXISTS questions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    question_text TEXT NOT NULL,
                    subject VARCHAR(100),
                    topic VARCHAR(200),
                    difficulty INTEGER DEFAULT 1,
                    option_a TEXT,
                    option_b TEXT,
                    option_c TEXT,
                    option_d TEXT,
                    correct_answer VARCHAR(1),
                    explanation TEXT,
                    icfes_category VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Clear existing questions
            self.cur.execute("DELETE FROM questions;")
            
            # Prepare data for insertion
            records = []
            for _, row in df.iterrows():
                records.append((
                    str(uuid.uuid4()),
                    str(row.get('question_text', row.get('pregunta', ''))),
                    str(row.get('subject', row.get('materia', 'General'))),
                    str(row.get('topic', row.get('tema', ''))),
                    int(row.get('difficulty', row.get('dificultad', 1))),
                    str(row.get('option_a', row.get('opcion_a', ''))),
                    str(row.get('option_b', row.get('opcion_b', ''))),
                    str(row.get('option_c', row.get('opcion_c', ''))),
                    str(row.get('option_d', row.get('opcion_d', ''))),
                    str(row.get('correct_answer', row.get('respuesta_correcta', 'A'))),
                    str(row.get('explanation', row.get('explicacion', ''))),
                    str(row.get('icfes_category', row.get('categoria_icfes', '')))
                ))
            
            # Insert data
            query = """
                INSERT INTO questions (
                    id, question_text, subject, topic, difficulty,
                    option_a, option_b, option_c, option_d, correct_answer,
                    explanation, icfes_category
                ) VALUES %s
            """
            execute_values(self.cur, query, records)
            self.conn.commit()
            
            logger.info(f"✅ Loaded {len(records)} questions")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading ICFES questions: {e}")
            self.conn.rollback()
            return False
    
    def verify_data(self):
        """Verify all data was loaded correctly"""
        try:
            logger.info("🔍 Verifying loaded data...")
            
            tables = [
                ('subjects', 'Subjects'),
                ('questions', 'Questions'),
                ('icfes_topics_catalog', 'ICFES Topics'),
                ('youtube_catalog', 'YouTube Videos'),
                ('study_plan_templates', 'Study Plan Templates')
            ]
            
            for table_name, display_name in tables:
                try:
                    self.cur.execute(f"SELECT COUNT(*) FROM {table_name};")
                    count = self.cur.fetchone()[0]
                    logger.info(f"   ✅ {display_name}: {count} records")
                except Exception:
                    logger.warning(f"   ⚠️ {display_name}: Table not found or empty")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verifying data: {e}")
            return False
    
    def run(self):
        """Run complete initialization"""
        logger.info("🚀 Starting ICFES data initialization...")
        
        if not self.connect():
            return False
        
        try:
            # Load all data files
            self.load_icfes_topics_catalog()
            self.load_youtube_catalog()
            self.load_study_plan_templates()
            self.load_icfes_questions()
            
            # Verify everything was loaded
            self.verify_data()
            
            logger.info("✅ ICFES data initialization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
            
        finally:
            self.close()


if __name__ == "__main__":
    loader = ICFESDataLoader()
    success = loader.run()
    sys.exit(0 if success else 1)