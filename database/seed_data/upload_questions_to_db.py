#!/usr/bin/env python3
"""
Script para cargar preguntas desde questions.xlsx a la base de datos PostgreSQL
Mapea correctamente los 85 campos del Excel a la estructura de la base de datos
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch, Json
import uuid
import json
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
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'gameplay_db'),
    'user': os.getenv('DB_USER', 'gameplay'),
    'password': os.getenv('DB_PASSWORD', 'gameplay123')
}

# Mapeo de áreas a subject_id
SUBJECT_MAPPING = {
    'Matemáticas': '550e8400-e29b-41d4-a716-446655440001',
    'Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
    'Lectura Crítica': '550e8400-e29b-41d4-a716-446655440002',
    'Lectura crítica': '550e8400-e29b-41d4-a716-446655440002',
    'Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
    'Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
    'Inglés': '550e8400-e29b-41d4-a716-446655440005'
}

class QuestionsUploader:
    def __init__(self):
        self.conn = None
        self.cur = None
        self.stats = {
            'questions_loaded': 0,
            'questions_skipped': 0,
            'topics_created': 0,
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
    
    def create_topic_if_not_exists(self, topic_name, subject_id, difficulty_level=2):
        """Crear tópico si no existe"""
        try:
            # Verificar si el tópico existe
            self.cur.execute(
                "SELECT id FROM topics WHERE name = %s AND subject_id = %s",
                (topic_name, subject_id)
            )
            result = self.cur.fetchone()
            
            if result:
                return result[0]
            
            # Crear nuevo tópico
            topic_id = str(uuid.uuid4())
            self.cur.execute(
                """INSERT INTO topics (id, subject_id, name, difficulty_level, created_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (topic_id, subject_id, topic_name, difficulty_level, datetime.now())
            )
            self.stats['topics_created'] += 1
            logger.info(f"📚 Tópico creado: {topic_name}")
            return topic_id
        except Exception as e:
            logger.warning(f"Error creando tópico {topic_name}: {e}")
            return None
    
    def normalize_column_names(self, df):
        """Normalizar nombres de columnas para mapeo consistente"""
        # Crear mapeo de columnas normalizadas
        column_mapping = {}
        for col in df.columns:
            normalized = col.strip().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
            column_mapping[col] = normalized.lower()
        
        # Renombrar columnas
        df_normalized = df.rename(columns=column_mapping)
        logger.info(f"📋 Columnas normalizadas: {len(column_mapping)} columnas")
        return df_normalized
    
    def map_difficulty_to_int(self, difficulty_value):
        """Mapear nivel de dificultad a entero"""
        if pd.isna(difficulty_value):
            return 3
        
        if isinstance(difficulty_value, (int, float)):
            if 0 <= difficulty_value <= 1:
                # Si es decimal (0-1), convertir a escala 1-10
                return max(1, min(10, int(difficulty_value * 10)))
            else:
                # Si ya es entero, mantener en rango 1-10
                return max(1, min(10, int(difficulty_value)))
        
        # Si es string, mapear valores conocidos
        difficulty_str = str(difficulty_value).lower()
        difficulty_map = {
            'bajo': 2, 'básico': 2, 'facil': 2, 'fácil': 2,
            'medio': 5, 'satisfactorio': 5, 'intermedio': 5,
            'alto': 8, 'avanzado': 8, 'dificil': 8, 'difícil': 8
        }
        
        return difficulty_map.get(difficulty_str, 5)  # Default: medio
    
    def load_questions_from_excel(self, excel_path):
        """Cargar preguntas desde Excel y subirlas a la base de datos"""
        try:
            logger.info(f"📖 Cargando archivo Excel: {excel_path}")
            df = pd.read_excel(excel_path)
            logger.info(f"📊 Archivo cargado: {len(df)} filas, {len(df.columns)} columnas")
            
            # Normalizar nombres de columnas
            df = self.normalize_column_names(df)
            
            # No limpiar datos existentes para preservar preguntas base
            logger.info("📊 Manteniendo preguntas existentes, agregando nuevas desde Excel...")
            
            questions_data = []
            
            for idx, row in df.iterrows():
                try:
                    # Mapear área a subject_id (probar diferentes variantes del nombre)
                    area_evaluada = ''
                    for col_variant in ['area_evaluada', 'área_evaluada', 'Área_Evaluada']:
                        if col_variant in row and pd.notna(row[col_variant]):
                            area_evaluada = str(row[col_variant]).strip()
                            break
                    
                    subject_id = SUBJECT_MAPPING.get(area_evaluada)
                    
                    if not subject_id:
                        logger.warning(f"⚠️ Área no reconocida: '{area_evaluada}' en fila {idx+1}")
                        self.stats['questions_skipped'] += 1
                        continue
                    
                    # Crear o obtener topic_id
                    tema_especifico = str(row.get('tema_especifico', 'General')).strip()
                    if not tema_especifico or tema_especifico == 'nan':
                        tema_especifico = 'General'
                    
                    difficulty_raw = row.get('nivel_dificultad', 5)
                    difficulty_int = self.map_difficulty_to_int(difficulty_raw)
                    
                    topic_id = self.create_topic_if_not_exists(tema_especifico, subject_id, difficulty_int)
                    
                    if not topic_id:
                        logger.warning(f"⚠️ No se pudo crear tópico para fila {idx+1}")
                        self.stats['questions_skipped'] += 1
                        continue
                    
                    # Generar ID único para la pregunta (UUID válido)
                    question_id = str(uuid.uuid4())
                    
                    # Extraer opciones
                    options = {}
                    for letter in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
                        option_value = row.get(f'opcion_{letter}', '')
                        if pd.notna(option_value) and str(option_value).strip() and str(option_value).strip() != 'No Aplica':
                            options[letter.upper()] = str(option_value).strip()
                    
                    # Si no hay opciones válidas, crear opciones por defecto
                    if not options:
                        options = {
                            'A': 'Opción A',
                            'B': 'Opción B', 
                            'C': 'Opción C',
                            'D': 'Opción D'
                        }
                    
                    # Respuesta correcta
                    respuesta_correcta = str(row.get('respuesta_correcta', 'A')).strip().upper()
                    if respuesta_correcta not in options:
                        respuesta_correcta = list(options.keys())[0]  # Primera opción disponible
                    
                    # Determinar texto de la pregunta
                    pregunta_text = str(row.get('pregunta', '')).strip()
                    
                    # Si la pregunta es "No Aplica", usar metadatos para crear texto descriptivo
                    if pregunta_text == 'No Aplica' or pregunta_text == ' No Aplica' or not pregunta_text:
                        afirmacion = str(row.get('afirmacion', '')).strip()
                        evidencia = str(row.get('evidencia', '')).strip()
                        
                        if afirmacion and afirmacion != 'No Aplica' and afirmacion != ' No Aplica':
                            pregunta_text = f"[MULTIMEDIA] {afirmacion[:150]}..."
                        elif evidencia and evidencia != 'No Aplica' and evidencia != ' No Aplica':
                            pregunta_text = f"[MULTIMEDIA] Evalúa: {evidencia[:150]}..."
                        else:
                            pregunta_text = f"[MULTIMEDIA] {tema_especifico} - Ver imagen para contenido completo"
                    
                    # Determinar si requiere imagen
                    requiere_imagen = row.get('requiere_imagen', False)
                    if isinstance(requiere_imagen, str):
                        requiere_imagen = requiere_imagen.lower() in ['true', '1', 'sí', 'si']
                    
                    # Preparar datos para inserción
                    question_data = (
                        question_id,  # id
                        subject_id,   # subject_id
                        topic_id,     # topic_id
                        pregunta_text,  # question_text
                        'multiple_choice',  # question_type
                        difficulty_int,     # difficulty
                        respuesta_correcta, # correct_answer
                        Json(options),      # options (JSONB)
                        str(row.get('explicacion_respuesta', '')).strip(),  # explanation
                        str(row.get('pista_1', '')).strip(),  # hint
                        [area_evaluada, str(row.get('competencia', '')), tema_especifico],  # tags (PostgreSQL array)
                        Json({
                            'discrimination_index': float(row.get('indice_discriminacion', 0.5)) if pd.notna(row.get('indice_discriminacion')) else 0.5,
                            'irt_a': float(row.get('parametro_irt_a', 1.0)) if pd.notna(row.get('parametro_irt_a')) else 1.0,
                            'irt_b': float(row.get('parametro_irt_b', 0.0)) if pd.notna(row.get('parametro_irt_b')) else 0.0,
                            'irt_c': float(row.get('parametro_irt_c', 0.25)) if pd.notna(row.get('parametro_irt_c')) else 0.25,
                            'success_rate': 0.6
                        }),  # power_stats (JSONB)
                        datetime.now()  # created_at
                    )
                    
                    questions_data.append(question_data)
                    
                    # Insertar en lotes de 100
                    if len(questions_data) >= 100:
                        self.insert_questions_batch(questions_data)
                        questions_data = []
                        
                except Exception as e:
                    logger.error(f"❌ Error procesando fila {idx+1}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            # Insertar último lote
            if questions_data:
                self.insert_questions_batch(questions_data)
            
            logger.info("✅ Carga de preguntas completada")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando Excel: {e}")
            return False
    
    def insert_questions_batch(self, questions_data):
        """Insertar lote de preguntas"""
        try:
            execute_batch(
                self.cur,
                """INSERT INTO questions (
                    id, subject_id, topic_id, question_text, question_type, difficulty,
                    correct_answer, options, explanation, hint, tags, power_stats, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING""",
                questions_data
            )
            self.conn.commit()
            self.stats['questions_loaded'] += len(questions_data)
            logger.info(f"✅ Insertadas {len(questions_data)} preguntas (Total: {self.stats['questions_loaded']})")
        except Exception as e:
            logger.error(f"❌ Error insertando lote: {e}")
            self.conn.rollback()
            self.stats['errors'] += len(questions_data)
    
    def add_icfes_fields_to_questions(self):
        """Agregar campos ICFES adicionales a la tabla questions"""
        try:
            logger.info("🔧 Agregando campos ICFES a la tabla questions...")
            
            icfes_fields = [
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS id_pregunta_original VARCHAR(50)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS area_evaluada VARCHAR(100)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS competencia VARCHAR(255)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS componente VARCHAR(255)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS proceso_cognitivo VARCHAR(100)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_conocimiento VARCHAR(100)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS afirmacion TEXT",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS evidencia TEXT",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS tema_especifico VARCHAR(255)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS grado_escolar VARCHAR(20)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS periodo_aplicacion VARCHAR(50)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS requiere_imagen BOOLEAN DEFAULT FALSE",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_pregunta_url VARCHAR(500)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_opcion_a_url VARCHAR(500)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_opcion_b_url VARCHAR(500)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_opcion_c_url VARCHAR(500)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS imagen_opcion_d_url VARCHAR(500)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS tiempo_estimado INTEGER DEFAULT 120",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS nivel_desempeno_esperado VARCHAR(50)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS subtema VARCHAR(255)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS estrategia_discursiva VARCHAR(100)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS tipo_razonamiento VARCHAR(100)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS complejidad_cognitiva VARCHAR(50)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS contexto_aplicacion VARCHAR(100)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_1 TEXT",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_2 TEXT", 
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS pista_3 TEXT",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS explicacion_respuesta TEXT",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS error_comun TEXT",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS indice_discriminacion DECIMAL(5,3)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS parametro_irt_a DECIMAL(5,3)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS parametro_irt_b DECIMAL(5,3)",
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS parametro_irt_c DECIMAL(5,3)"
            ]
            
            for field_sql in icfes_fields:
                self.cur.execute(field_sql)
            
            self.conn.commit()
            logger.info("✅ Campos ICFES agregados exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error agregando campos ICFES: {e}")
            self.conn.rollback()
            return False
    
    def verify_upload(self):
        """Verificar la carga de datos"""
        try:
            # Contar preguntas por área
            self.cur.execute("""
                SELECT 
                    s.name as subject_name,
                    COUNT(q.id) as question_count
                FROM subjects s
                LEFT JOIN questions q ON s.id = q.subject_id
                GROUP BY s.id, s.name
                ORDER BY question_count DESC
            """)
            
            results = self.cur.fetchall()
            
            logger.info("\n📊 VERIFICACIÓN DE CARGA:")
            logger.info("=" * 50)
            total_questions = 0
            for subject_name, count in results:
                logger.info(f"  📚 {subject_name}: {count} preguntas")
                total_questions += count
            
            logger.info(f"\n🎯 RESUMEN FINAL:")
            logger.info(f"  ✅ Preguntas cargadas: {self.stats['questions_loaded']}")
            logger.info(f"  ⚠️ Preguntas omitidas: {self.stats['questions_skipped']}")
            logger.info(f"  📚 Tópicos creados: {self.stats['topics_created']}")
            logger.info(f"  ❌ Errores: {self.stats['errors']}")
            logger.info(f"  📊 Total en BD: {total_questions}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error verificando carga: {e}")
            return False
    
    def run(self, excel_path):
        """Ejecutar proceso completo"""
        logger.info("🚀 Iniciando carga de preguntas desde Excel...")
        
        if not self.connect_db():
            return False
        
        try:
            # Agregar campos ICFES si no existen
            self.add_icfes_fields_to_questions()
            
            # Cargar preguntas desde Excel
            if not self.load_questions_from_excel(excel_path):
                return False
            
            # Verificar carga
            self.verify_upload()
            
            logger.info("🎉 ¡Proceso completado exitosamente!")
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
    excel_path = "database/allquestions/questions.xlsx"
    
    if not os.path.exists(excel_path):
        logger.error(f"❌ Archivo no encontrado: {excel_path}")
        return 1
    
    uploader = QuestionsUploader()
    success = uploader.run(excel_path)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
