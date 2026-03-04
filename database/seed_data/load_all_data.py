#!/usr/bin/env python3
"""
Script to load all seed data (CSV files) into the database with seamless mapping
This script is executed automatically when the container starts
Uses the new mapping tables for ICFES data integration
"""

import os
import sys
import time
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch, Json
import uuid
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres'),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'gameplay_db'),
    'user': os.getenv('DB_USER', 'gameplay'),
    'password': os.getenv('DB_PASSWORD', 'gameplay123')
}

class DataLoader:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.subject_ids = {}
        self.topic_ids = {}
        self.icfes_areas = {}
        self.icfes_topics_mapping = {}
        self.stats = {
            'questions_loaded': 0,
            'topics_loaded': 0,
            'videos_loaded': 0,
            'templates_loaded': 0
        }
        
    def connect_db(self, max_retries=10):
        """Connect to database with retries"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting database connection... (attempt {attempt + 1})")
                self.conn = psycopg2.connect(**DB_CONFIG)
                self.cur = self.conn.cursor()
                logger.info("✅ Database connection successful")
                return True
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(5)
        return False
    
    def check_data_exists(self):
        """Check if data is already loaded"""
        try:
            self.cur.execute("SELECT COUNT(*) FROM questions")
            question_count = self.cur.fetchone()[0]
            
            self.cur.execute("SELECT COUNT(*) FROM icfes_topics_extended")
            topics_count = self.cur.fetchone()[0]
            
            if question_count >= 20 and topics_count >= 5:
                logger.info(f"✅ Data already loaded: {question_count} questions, {topics_count} ICFES topics")
                return True
            return False
        except Exception as e:
            logger.warning(f"Error checking existing data: {e}")
            return False
    
    def load_subjects_and_areas(self):
        """Get subject IDs and load ICFES areas mapping"""
        # Load subjects
        self.cur.execute("SELECT id, name FROM subjects")
        for subject_id, name in self.cur.fetchall():
            self.subject_ids[name] = subject_id
        logger.info(f"Loaded {len(self.subject_ids)} subjects")
        
        # Load ICFES areas mapping
        try:
            self.cur.execute("SELECT area_code, area_name, subject_id FROM icfes_areas")
            for area_code, area_name, subject_id in self.cur.fetchall():
                self.icfes_areas[area_name] = subject_id
                self.icfes_areas[area_code] = subject_id
            logger.info(f"Loaded {len(self.icfes_areas)} ICFES area mappings")
        except Exception as e:
            logger.warning(f"ICFES areas table not found: {e}")
    
    def load_icfes_topics_extended(self, file_path):
        """Load ICFES topics catalog with extended metadata"""
        if not os.path.exists(file_path):
            logger.warning(f"Topics catalog CSV not found: {file_path}")
            return
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"📚 Loading {len(df)} ICFES topics from topics_catalog.csv")
            
            topics_data = []
            for _, row in df.iterrows():
                # Resolve subject_id from area_evaluada
                area_evaluada = row.get('area_evaluada', '')
                subject_id = self.resolve_subject_from_area(area_evaluada)
                
                if not subject_id:
                    logger.warning(f"No subject found for area: {area_evaluada}")
                    continue
                
                # Create topic if needed
                topic_id = self.create_topic_if_not_exists(
                    row.get('tema_principal', 'Unknown Topic'),
                    subject_id,
                    int(row.get('nivel_dificultad', 2))
                )
                
                # Prepare data for icfes_topics_extended
                topics_data.append((
                    str(uuid.uuid4()),  # id
                    row.get('codigo_tema', f'TEMA_{len(topics_data)+1}'),  # codigo_tema
                    row.get('tema_principal', 'Unknown'),  # tema_principal
                    row.get('subtema', ''),  # subtema
                    row.get('tema_especifico', ''),  # tema_especifico
                    topic_id,  # topic_id
                    subject_id,  # subject_id
                    area_evaluada,  # area_evaluada
                    row.get('competencia_icfes', ''),  # competencia_icfes
                    row.get('componente', ''),  # componente
                    row.get('afirmacion', ''),  # afirmacion
                    row.get('evidencia', ''),  # evidencia
                    int(row.get('grado_introduccion', 8)),  # grado_introduccion
                    int(row.get('nivel_dificultad', 2)),  # nivel_dificultad
                    int(row.get('importancia_icfes', 3)),  # importancia_icfes
                    float(row.get('frecuencia_evaluacion', 20.0)),  # frecuencia_evaluacion
                    int(row.get('horas_teoria', 3)),  # horas_teoria
                    int(row.get('horas_practica', 5)),  # horas_practica
                    int(row.get('numero_ejercicios_recomendados', 50)),  # numero_ejercicios_recomendados
                    float(row.get('umbral_dominio', 75.0)),  # umbral_dominio
                    row.get('estilo_aprendizaje_optimo', 'visual'),  # estilo_aprendizaje_optimo
                    datetime.now()  # created_at
                ))
            
            # Insert in batch
            execute_batch(
                self.cur,
                """INSERT INTO icfes_topics_extended (
                    id, codigo_tema, tema_principal, subtema, tema_especifico,
                    topic_id, subject_id, area_evaluada, competencia_icfes, componente,
                    afirmacion, evidencia, grado_introduccion, nivel_dificultad,
                    importancia_icfes, frecuencia_evaluacion, horas_teoria, horas_practica,
                    numero_ejercicios_recomendados, umbral_dominio, estilo_aprendizaje_optimo,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (codigo_tema) DO NOTHING""",
                topics_data
            )
            
            self.conn.commit()
            self.stats['topics_loaded'] = len(topics_data)
            logger.info(f"✅ Loaded {len(topics_data)} ICFES topics to icfes_topics_extended")
            
            # Build topic mapping for questions
            self.cur.execute("SELECT codigo_tema, topic_id FROM icfes_topics_extended")
            for codigo, topic_id in self.cur.fetchall():
                self.icfes_topics_mapping[codigo] = topic_id
                
        except Exception as e:
            logger.error(f"Error loading ICFES topics: {e}")
            self.conn.rollback()
    
    def load_questions_from_excel(self, file_path):
        """Load questions from Excel file with ICFES metadata mapping"""
        if not os.path.exists(file_path):
            logger.warning(f"Questions Excel file not found: {file_path}")
            return 0
        
        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            logger.info(f"❓ Loading {len(df)} questions from questions.xlsx")
            
            questions_data = []
            metadata_data = []
            
            # Process each row with ICFES mapping
            for idx, row in df.iterrows():
                # Resolve subject and topic from ICFES data
                area_evaluada = row.get('area_evaluada', '')
                subject_id = self.resolve_subject_from_area(area_evaluada)
                
                if not subject_id:
                    logger.warning(f"No subject found for area: {area_evaluada}, skipping question {idx+1}")
                    continue
                
                # Get topic from codigo_tema_principal or create from tema_especifico
                codigo_tema = row.get('codigo_tema_principal', '')
                topic_id = self.icfes_topics_mapping.get(codigo_tema)
                
                if not topic_id:
                    # Create topic from tema_especifico
                    tema_especifico = row.get('tema_especifico', f'Tema {idx+1}')
                    topic_id = self.create_topic_if_not_exists(
                        tema_especifico, subject_id, int(row.get('nivel_dificultad', 2))
                    )
                
                question_id = str(uuid.uuid4())
                
                # Map Excel fields to database structure
                questions_data.append((
                    question_id,  # id
                    subject_id,   # subject_id
                    topic_id,     # topic_id
                    row.get('pregunta', ''),  # question_text
                    row.get('respuesta_correcta', 'B'),  # correct_answer
                    int(row.get('nivel_dificultad', 2)),  # difficulty
                    row.get('explicacion_respuesta', ''),  # explanation
                    row.get('pista_1', ''),  # hint
                    Json({
                        'A': row.get('opcion_a', ''),
                        'B': row.get('opcion_b', ''),
                        'C': row.get('opcion_c', ''),
                        'D': row.get('opcion_d', '')
                    }),  # options (JSON)
                    Json({
                        'discrimination_index': float(row.get('parametro_irt_a', 0.5)),
                        'difficulty_parameter': float(row.get('parametro_irt_b', 0.0)),
                        'guessing_parameter': float(row.get('parametro_irt_c', 0.2)),
                        'p_value': float(row.get('p_value', 0.6)),
                        'point_biserial': float(row.get('point_biserial', 0.3)),
                        'optimal_time_seconds': int(row.get('optimal_time_seconds', 120))
                    }),  # power_stats (JSON)
                    Json([
                        area_evaluada,
                        row.get('competencia', ''),
                        row.get('tema_especifico', ''),
                        row.get('tipo_razonamiento', '')
                    ]),  # tags (JSON array)
                    datetime.now()  # created_at
                ))
                
                # Prepare metadata for questions_icfes_metadata table
                metadata_data.append((
                    str(uuid.uuid4()),  # id
                    question_id,  # question_id
                    row.get('id_pregunta', ''),  # id_pregunta_original
                    area_evaluada,  # area_evaluada
                    row.get('competencia', ''),  # competencia
                    row.get('componente', ''),  # componente
                    row.get('proceso_cognitivo', ''),  # proceso_cognitivo
                    row.get('tipo_conocimiento', ''),  # tipo_conocimiento
                    row.get('afirmacion', ''),  # afirmacion
                    row.get('evidencia', ''),  # evidencia
                    row.get('tema_especifico', ''),  # tema_especifico
                    row.get('subtema', ''),  # subtema
                    int(row.get('grado_escolar', 11)),  # grado_escolar
                    int(row.get('tiempo_estimado', 120)),  # tiempo_estimado
                    row.get('pista_1', ''),  # pista_1
                    row.get('pista_2', ''),  # pista_2
                    row.get('pista_3', ''),  # pista_3
                    row.get('explicacion_respuesta', ''),  # explicacion_respuesta
                    float(row.get('parametro_irt_a', 0.5)),  # parametro_irt_a
                    float(row.get('parametro_irt_b', 0.0)),  # parametro_irt_b
                    float(row.get('parametro_irt_c', 0.2)),  # parametro_irt_c
                    float(row.get('p_value', 0.6)),  # p_value
                    float(row.get('point_biserial', 0.3)),  # point_biserial
                    codigo_tema,  # codigo_tema_principal
                    datetime.now()  # created_at
                ))
            
            # Insert questions in batch
            execute_batch(
                self.cur,
                """INSERT INTO questions (
                    id, subject_id, topic_id, question_text, correct_answer, difficulty,
                    explanation, hint, options, power_stats, tags, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING""",
                questions_data
            )
            
            # Insert metadata in batch
            execute_batch(
                self.cur,
                """INSERT INTO questions_icfes_metadata (
                    id, question_id, id_pregunta_original, area_evaluada, competencia,
                    componente, proceso_cognitivo, tipo_conocimiento, afirmacion, evidencia,
                    tema_especifico, subtema, grado_escolar, tiempo_estimado,
                    pista_1, pista_2, pista_3, explicacion_respuesta,
                    parametro_irt_a, parametro_irt_b, parametro_irt_c, p_value, point_biserial,
                    codigo_tema_principal, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (question_id) DO NOTHING""",
                metadata_data
            )
            
            self.conn.commit()
            self.stats['questions_loaded'] = len(questions_data)
            logger.info(f"✅ Loaded {len(questions_data)} questions with ICFES metadata")
            return len(questions_data)
            
        except Exception as e:
            logger.error(f"Error loading questions Excel: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.conn.rollback()
            return 0
    
    def load_questions_fallback(self):
        """Load fallback questions if Excel loading fails"""
        math_subject_id = self.subject_ids.get('Matemáticas')
        algebra_topic_id = self.topic_ids.get('Matemáticas_Álgebra')
        
        if not math_subject_id or not algebra_topic_id:
            logger.error("Cannot create fallback questions - missing subject/topic")
            return
        
        questions_data = []
        for i in range(1, 46):
            questions_data.append((
                str(uuid.uuid4()),
                math_subject_id,
                algebra_topic_id,
                f'Resuelve la ecuación: {i*2}x + {i} = {i*3}',
                f'x = {i-1}',
                f'x = {i}',
                f'x = {i+1}',
                f'x = {i+2}',
                'B',
                1 if i <= 15 else 2 if i <= 30 else 3,
                'Despeja x de la ecuación',
                datetime.now()
            ))
        
        execute_batch(
            self.cur,
            """INSERT INTO questions (
                id, subject_id, topic_id, pregunta_texto,
                opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
                correct_answer, difficulty, hint, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING""",
            questions_data
        )
        
        self.conn.commit()
        logger.info(f"✅ Created {len(questions_data)} fallback math questions")
    
    def load_youtube_videos_enriched(self, file_path):
        """Load enriched YouTube videos from CSV with effectiveness metrics"""
        if not os.path.exists(file_path):
            logger.warning(f"YouTube CSV not found: {file_path}")
            return
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"📺 Loading {len(df)} enriched YouTube videos")
            
            videos_data = []
            for _, row in df.iterrows():
                # Resolve topic from codigo_tema
                codigo_tema = row.get('codigo_tema', '')
                topic_id = self.icfes_topics_mapping.get(codigo_tema)
                
                videos_data.append((
                    str(uuid.uuid4()),  # id
                    codigo_tema,  # codigo_tema
                    topic_id,  # topic_id
                    row.get('youtube_video_id', ''),  # youtube_video_id
                    row.get('youtube_url', ''),  # youtube_url
                    row.get('titulo_video', ''),  # titulo_video
                    row.get('descripcion', ''),  # descripcion
                    row.get('canal_sugerido', ''),  # canal_sugerido
                    int(row.get('duracion_segundos', 600)),  # duracion_segundos
                    int(row.get('nivel_dificultad', 2)),  # nivel_dificultad
                    float(row.get('calidad_pedagogica', 4.0)),  # calidad_pedagogica
                    float(row.get('efectividad_historica', 80.0)),  # efectividad_historica
                    row.get('estado_disponibilidad', 'activo'),  # estado_disponibilidad
                    datetime.now()  # created_at
                ))
            
            # Insert in batch
            execute_batch(
                self.cur,
                """INSERT INTO youtube_videos_enriched (
                    id, codigo_tema, topic_id, youtube_video_id, youtube_url,
                    titulo_video, descripcion, canal_sugerido, duracion_segundos,
                    nivel_dificultad, calidad_pedagogica, efectividad_historica,
                    estado_disponibilidad, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (youtube_video_id, codigo_tema) DO NOTHING""",
                videos_data
            )
            
            self.conn.commit()
            self.stats['videos_loaded'] = len(videos_data)
            logger.info(f"✅ Loaded {len(videos_data)} enriched YouTube videos")
            
        except Exception as e:
            logger.error(f"Error loading YouTube videos: {e}")
            self.conn.rollback()
    
    def load_study_plan_templates(self, file_path):
        """Load study plan templates from CSV"""
        if not os.path.exists(file_path):
            logger.warning(f"Study plan templates CSV not found: {file_path}")
            return
        
        try:
            df = pd.read_csv(file_path)
            logger.info(f"📋 Loading {len(df)} study plan templates")
            
            templates_data = []
            for _, row in df.iterrows():
                # Parse pipe-separated fields
                topics_list = str(row.get('topics', '')).split('|') if row.get('topics') else []
                weak_areas = str(row.get('weak_areas', '')).split('|') if row.get('weak_areas') else []
                focus_topics = str(row.get('focus_topics', '')).split('|') if row.get('focus_topics') else []
                
                templates_data.append((
                    str(uuid.uuid4()),  # id
                    row.get('subject_id', ''),  # subject_id
                    row.get('subject_name', ''),  # subject_name
                    int(row.get('unit_number', 1)),  # unit_number
                    row.get('unit_name', ''),  # unit_name
                    row.get('unit_description', ''),  # unit_description
                    topics_list,  # topics_list
                    row.get('recommendations_priority', 'medium'),  # recommendations_priority
                    weak_areas,  # weak_areas
                    focus_topics,  # focus_topics
                    row.get('study_time', '3-4 horas'),  # study_time
                    int(row.get('estimated_hours', 4)),  # estimated_hours
                    int(row.get('difficulty_level', 2)),  # difficulty_level
                    float(row.get('icfes_weight', 0.25)),  # icfes_weight
                    datetime.now()  # created_at
                ))
            
            # Insert in batch
            execute_batch(
                self.cur,
                """INSERT INTO study_plan_templates_icfes (
                    id, subject_id, subject_name, unit_number, unit_name, unit_description,
                    topics_list, recommendations_priority, weak_areas, focus_topics,
                    study_time, estimated_hours, difficulty_level, icfes_weight, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (subject_id, unit_number) DO NOTHING""",
                templates_data
            )
            
            self.conn.commit()
            self.stats['templates_loaded'] = len(templates_data)
            logger.info(f"✅ Loaded {len(templates_data)} study plan templates")
            
        except Exception as e:
            logger.error(f"Error loading study plan templates: {e}")
            self.conn.rollback()
    
    def resolve_subject_from_area(self, area_evaluada):
        """Resolve subject_id from area_evaluada using mapping"""
        return self.icfes_areas.get(area_evaluada)
    
    def create_topic_if_not_exists(self, topic_name, subject_id, difficulty_level=2):
        """Create topic if it doesn't exist and return topic_id"""
        try:
            # Check if topic exists
            self.cur.execute(
                "SELECT id FROM topics WHERE name = %s AND subject_id = %s",
                (topic_name, subject_id)
            )
            result = self.cur.fetchone()
            
            if result:
                return result[0]
            
            # Create new topic
            topic_id = str(uuid.uuid4())
            self.cur.execute(
                """INSERT INTO topics (id, subject_id, name, difficulty_level)
                   VALUES (%s, %s, %s, %s)""",
                (topic_id, subject_id, topic_name, difficulty_level)
            )
            return topic_id
        except Exception as e:
            logger.warning(f"Error creating topic {topic_name}: {e}")
            return None
    
    def verify_data(self):
        """Verify data was loaded correctly with detailed stats"""
        checks = [
            ("questions", "SELECT COUNT(*) FROM questions"),
            ("topics", "SELECT COUNT(*) FROM topics"),
            ("subjects", "SELECT COUNT(*) FROM subjects"),
            ("icfes_areas", "SELECT COUNT(*) FROM icfes_areas"),
            ("icfes_topics_extended", "SELECT COUNT(*) FROM icfes_topics_extended"),
            ("youtube_videos_enriched", "SELECT COUNT(*) FROM youtube_videos_enriched"),
            ("study_plan_templates_icfes", "SELECT COUNT(*) FROM study_plan_templates_icfes"),
            ("questions_icfes_metadata", "SELECT COUNT(*) FROM questions_icfes_metadata"),
        ]
        
        logger.info("\n📊 SEAMLESS CSV MAPPING - Data Verification:")
        total_loaded = 0
        for name, query in checks:
            try:
                self.cur.execute(query)
                count = self.cur.fetchone()[0]
                logger.info(f"  ✅ {name}: {count} records")
                total_loaded += count
            except Exception as e:
                logger.warning(f"  ⚠️ {name}: {e}")
        
        logger.info(f"\n🎯 LOADING SUMMARY:")
        logger.info(f"  📝 Questions with metadata: {self.stats['questions_loaded']}")
        logger.info(f"  📚 ICFES topics extended: {self.stats['topics_loaded']}")
        logger.info(f"  📺 YouTube videos enriched: {self.stats['videos_loaded']}")
        logger.info(f"  📋 Study plan templates: {self.stats['templates_loaded']}")
        logger.info(f"  🎉 Total records loaded: {total_loaded}")
    
    def run(self):
        """Main execution"""
        logger.info("🚀 Starting data loader...")
        
        if not self.connect_db():
            logger.error("Failed to connect to database")
            return False
        
        try:
            # Check if data already exists
            if self.check_data_exists():
                logger.info("✅ ICFES data already loaded, skipping...")
                return True
            
            logger.info("🚀 Starting SEAMLESS CSV TO DATABASE MAPPING...")
            
            # Load base data with ICFES mapping
            self.load_subjects_and_areas()
            
            # Use a static base path pointing to the new consolidated data structure
            base_path = './database'
            logger.info(f"📁 Using static base path for data: {base_path}")
            
            # Load ICFES topics catalog first (creates mapping)
            topics_path = f'{base_path}/catalogs/icfes_topics.csv'
            self.load_icfes_topics_extended(topics_path)
            
            # Load questions with ICFES metadata from Excel
            questions_path = f'{base_path}/allquestions/questions.xlsx'
            questions_loaded = self.load_questions_from_excel(questions_path)
            
            # Load enriched YouTube videos from the complete catalog
            youtube_path = f'{base_path}/catalogs/youtube_catalog_complete.csv'
            self.load_youtube_videos_enriched(youtube_path)
            
            # Load study plan templates
            templates_path = f'{base_path}/catalogs/study_plan_templates.csv'
            self.load_study_plan_templates(templates_path)
            
            # Fallback only if no questions loaded
            if questions_loaded == 0:
                logger.warning("⚠️ No questions loaded from Excel, creating minimal fallback...")
                self.load_questions_fallback()
            
            # Verify data
            self.verify_data()
            
            logger.info("✅ SEAMLESS CSV MAPPING COMPLETED SUCCESSFULLY!")
            logger.info("🎯 All ICFES data loaded with proper field mapping and foreign key resolution")
            return True
            
        except Exception as e:
            logger.error(f"Fatal error in seamless CSV mapping: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if self.conn:
                self.conn.rollback()
            return False
        finally:
            if self.cur:
                self.cur.close()
            if self.conn:
                self.conn.close()


if __name__ == "__main__":
    loader = DataLoader()
    success = loader.run()
    sys.exit(0 if success else 1)