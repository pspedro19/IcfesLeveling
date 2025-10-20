#!/usr/bin/env python3
"""
Script para cargar TODAS las 480 preguntas ICFES desde archivo Excel
directamente a PostgreSQL usando docker exec.

Mapeo directo de columnas Excel a base de datos.

Uso: python load_all_icfes_questions.py
"""

import pandas as pd
import uuid
import json
import logging
import subprocess
import sys
import os
import unicodedata
from typing import Dict, List, Optional, Any
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rutas del archivo Excel
EXCEL_PATH = r"C:\Users\PEDRO_PEREZ\Documents\IcfesLeveling\database\allquestions\ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"

# Configuración de la base de datos
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'gameplay_db',
    'username': 'gameplay',
    'password': 'gameplay123'
}

# Docker container name
DOCKER_CONTAINER = "icfes_postgres"


class ICFESExcelLoader:
    def __init__(self):
        self.questions_loaded = 0
        self.errors = []
        self.warnings = []
        self.subject_mapping = {}
        self.topic_mapping = {}

    def normalize_header(self, s: str) -> str:
        """Normaliza headers del Excel para búsqueda tolerante"""
        s = str(s or "").strip()
        # Quitar acentos
        s = unicodedata.normalize('NFKD', s)
        s = ''.join(c for c in s if not unicodedata.combining(c))
        # Unificar separadores
        s = s.replace(" ", "_").replace("-", "_").replace("__", "_")
        return s.lower()

    def execute_sql_in_docker(self, sql: str) -> bool:
        """Ejecuta SQL en el contenedor PostgreSQL usando docker exec"""
        try:
            # Construir comando docker exec
            cmd = [
                'docker', 'exec', '-i', DOCKER_CONTAINER,
                'psql', '-U', DB_CONFIG['username'], '-d', DB_CONFIG['database'],
                '-c', sql
            ]
            
            # Ejecutar comando
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Error ejecutando SQL: {result.stderr}")
                return False
                
            logger.debug(f"SQL ejecutado exitosamente: {sql[:100]}...")
            return True
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ejecutando SQL: {sql[:100]}...")
            return False
        except Exception as e:
            logger.error(f"Error ejecutando SQL: {e}")
            return False

    def get_subjects_mapping(self) -> Dict[str, str]:
        """Obtiene mapeo de subjects desde la base de datos"""
        sql = "SELECT id, name FROM subjects;"
        
        try:
            cmd = [
                'docker', 'exec', '-i', DOCKER_CONTAINER,
                'psql', '-U', DB_CONFIG['username'], '-d', DB_CONFIG['database'],
                '-t', '-c', sql
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error obteniendo subjects: {result.stderr}")
                return {}
            
            mapping = {}
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    parts = line.strip().split('|')
                    if len(parts) >= 2:
                        subject_id = parts[0].strip()
                        subject_name = parts[1].strip()
                        mapping[subject_name] = subject_id
            
            logger.info(f"Subjects encontrados: {list(mapping.keys())}")
            return mapping
            
        except Exception as e:
            logger.error(f"Error obteniendo subjects: {e}")
            return {}

    def create_topic_if_not_exists(self, topic_name: str, subject_id: str) -> str:
        """Crea un topic si no existe y retorna su ID"""
        topic_id = str(uuid.uuid4())
        
        # Verificar si ya existe
        check_sql = f"SELECT id FROM topics WHERE name = '{topic_name}' AND subject_id = '{subject_id}';"
        
        try:
            cmd = [
                'docker', 'exec', '-i', DOCKER_CONTAINER,
                'psql', '-U', DB_CONFIG['username'], '-d', DB_CONFIG['database'],
                '-t', '-c', check_sql
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                # Topic existe, retornar su ID
                existing_id = result.stdout.strip()
                logger.debug(f"Topic '{topic_name}' ya existe con ID: {existing_id}")
                return existing_id
            
            # Crear nuevo topic
            create_sql = f"""
            INSERT INTO topics (id, subject_id, name, description, difficulty_level, created_at)
            VALUES ('{topic_id}', '{subject_id}', '{topic_name}', 'Topic creado para pregunta ICFES', 1, NOW());
            """
            
            if self.execute_sql_in_docker(create_sql):
                logger.info(f"Topic creado: {topic_name}")
                return topic_id
            else:
                logger.error(f"Error creando topic: {topic_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error procesando topic {topic_name}: {e}")
            return None

    def map_difficulty(self, nivel_dificultad: Any) -> int:
        """Mapea nivel de dificultad a escala 1-10"""
        if pd.isna(nivel_dificultad):
            return 5
        
        nivel = str(nivel_dificultad).lower().strip()
        
        difficulty_mapping = {
            'bajo': 2, 'baja': 2, 'facil': 2, 'fácil': 2,
            'basico': 3, 'básico': 3,
            'medio': 5, 'intermedio': 5,
            'alto': 7, 'alta': 7,
            'dificil': 9, 'difícil': 9,
            'muy alto': 10, 'muy alta': 10,
        }
        
        for key, value in difficulty_mapping.items():
            if key in nivel:
                return value
        
        # Si es numérico
        try:
            num_difficulty = int(float(nivel))
            return max(1, min(10, num_difficulty))
        except:
            return 5

    def normalize_image_path(self, value: Any) -> Optional[str]:
        """Normaliza rutas de imagen"""
        if pd.isna(value) or not str(value).strip():
            return None
            
        s = str(value).strip()
        if s.startswith('http://') or s.startswith('https://'):
            return s
        
        # Extraer nombre de archivo y agregar ruta estándar
        base_name = os.path.basename(s)
        if base_name:
            return f'/mathimg/{base_name}'
        
        return None

    def escape_sql_string(self, value: Any) -> str:
        """Escapa strings para SQL"""
        if pd.isna(value):
            return 'NULL'
        
        s = str(value)
        # Escapar comillas simples
        s = s.replace("'", "''")
        return f"'{s}'"

    def build_power_stats(self, row: pd.Series) -> str:
        """Construye objeto power_stats en JSON"""
        power_stats = {
            "discrimination_index": 0.5,
            "success_rate": 0.6,
            "estimated_time": int(row.get('Tiempo_Estimado', 60)) if pd.notna(row.get('Tiempo_Estimado')) else 60,
            "xp_reward": int(row.get('Puntos_XP', 10)) if pd.notna(row.get('Puntos_XP')) else 10,
            "original_id": str(row.get('ID_Pregunta', '')) if pd.notna(row.get('ID_Pregunta')) else '',
            "cognitive_process": str(row.get('Proceso_Cognitivo', '')) if pd.notna(row.get('Proceso_Cognitivo')) else '',
            "knowledge_type": str(row.get('Tipo_Conocimiento', '')) if pd.notna(row.get('Tipo_Conocimiento')) else '',
            "performance_level": str(row.get('Nivel_Desempeño_Esperado', '')) if pd.notna(row.get('Nivel_Desempeño_Esperado')) else '',
            "school_grade": str(row.get('Grado_Escolar', '')) if pd.notna(row.get('Grado_Escolar')) else '',
            "application_period": str(row.get('Periodo_Aplicación', '')) if pd.notna(row.get('Periodo_Aplicación')) else '',
            "discrimination_index_raw": float(row.get('Índice_Discriminación', 0.5)) if pd.notna(row.get('Índice_Discriminación')) else 0.5,
            "irt_a": float(row.get('Parámetro_IRT_A', 1.0)) if pd.notna(row.get('Parámetro_IRT_A')) else 1.0,
            "irt_b": float(row.get('Parámetro_IRT_B', 0.0)) if pd.notna(row.get('Parámetro_IRT_B')) else 0.0,
            "irt_c": float(row.get('Parámetro_IRT_C', 0.25)) if pd.notna(row.get('Parámetro_IRT_C')) else 0.25,
        }
        
        return json.dumps(power_stats).replace("'", "''")

    def build_options_dict(self, row: pd.Series) -> str:
        """Construye diccionario de opciones para compatibilidad legacy"""
        options = {}
        
        for opt in ['A', 'B', 'C', 'D']:
            text_key = f'Opcion_{opt}'
            if text_key in row and pd.notna(row[text_key]) and str(row[text_key]).strip():
                options[opt] = str(row[text_key]).strip()
        
        return json.dumps(options, ensure_ascii=False).replace("'", "''")

    def build_tags_array(self, row: pd.Series) -> str:
        """Construye array de tags para PostgreSQL"""
        tags = []
        
        # Competencia
        if pd.notna(row.get('Competencia')) and str(row['Competencia']).strip():
            tags.append(str(row['Competencia']).strip())
        
        # Componente
        if pd.notna(row.get('Componente')) and str(row['Componente']).strip():
            tags.append(str(row['Componente']).strip())
        
        # Proceso cognitivo
        if pd.notna(row.get('Proceso_Cognitivo')) and str(row['Proceso_Cognitivo']).strip():
            tags.append(str(row['Proceso_Cognitivo']).strip())
        
        # Crear array de PostgreSQL
        if tags:
            escaped_tags = [f"'{tag.replace(chr(39), chr(39)+chr(39))}'" for tag in tags]
            return f"ARRAY[{','.join(escaped_tags)}]"
        else:
            return "ARRAY[]::text[]"

    def load_excel_file(self, file_path: str) -> pd.DataFrame:
        """Carga y procesa el archivo Excel"""
        logger.info(f"Cargando archivo Excel: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        # Leer Excel
        df = pd.read_excel(file_path)
        logger.info(f"Archivo cargado: {len(df)} filas encontradas")
        
        # Mostrar columnas disponibles
        logger.info(f"Columnas encontradas: {list(df.columns)}")
        
        return df

    def validate_required_columns(self, df: pd.DataFrame) -> bool:
        """Valida que existan las columnas requeridas usando mapeo flexible"""
        # Mapeo de columnas requeridas con variantes
        required_mappings = {
            'ID_Pregunta': ['ID_Pregunta'],
            'Area_Evaluada': ['Área_Evaluada', 'Area_Evaluada', 'Ã¡rea_Evaluada'],
            'Pregunta': ['Pregunta'],
            'Respuesta_Correcta': ['Respuesta_Correcta'],
            'Opcion_A': ['Opcion_A'],
            'Opcion_B': ['Opcion_B'], 
            'Opcion_C': ['Opcion_C'],
            'Opcion_D': ['Opcion_D'],
            'Tema_Especifico': ['Tema_Específico', 'Tema_Especifico', 'Tema_EspecÃ­fico']
        }
        
        # Crear mapeo de columnas encontradas
        self.column_mapping = {}
        missing_columns = []
        
        for required, variants in required_mappings.items():
            found = False
            for variant in variants:
                if variant in df.columns:
                    self.column_mapping[required] = variant
                    found = True
                    break
            if not found:
                missing_columns.append(required)
        
        if missing_columns:
            logger.error(f"Columnas faltantes: {missing_columns}")
            logger.info(f"Columnas disponibles: {list(df.columns)}")
            return False
        
        logger.info("Todas las columnas requeridas están presentes")
        logger.info(f"Mapeo de columnas: {self.column_mapping}")
        return True

    def process_questions(self, df: pd.DataFrame) -> bool:
        """Procesa todas las preguntas del DataFrame"""
        logger.info(f"Iniciando procesamiento de {len(df)} preguntas...")
        
        # Obtener mapeo de subjects
        self.subject_mapping = self.get_subjects_mapping()
        if not self.subject_mapping:
            logger.error("No se pudieron obtener los subjects de la base de datos")
            return False
        
        # Mapeo de áreas a subjects
        area_to_subject = {
            'Matemáticas': 'Matemáticas',
            'Lenguaje': 'Lenguaje',
            'Ciencias Naturales': 'Ciencias Naturales',
            'Ciencias Sociales': 'Ciencias Sociales',
            'Inglés': 'Inglés',
            'Matematicas': 'Matemáticas',  # Sin tilde
            'Ciencias': 'Ciencias Naturales',
            'Sociales': 'Ciencias Sociales',
        }
        
        # Procesar cada fila
        for index, row in df.iterrows():
            try:
                # Validaciones básicas usando mapeo de columnas
                pregunta_col = self.column_mapping['Pregunta']
                if pd.isna(row[pregunta_col]) or not str(row[pregunta_col]).strip():
                    self.errors.append(f"Fila {index + 2}: Pregunta vacía")
                    continue
                
                respuesta_col = self.column_mapping['Respuesta_Correcta']
                if pd.isna(row[respuesta_col]) or str(row[respuesta_col]).strip().upper() not in ['A', 'B', 'C', 'D']:
                    self.errors.append(f"Fila {index + 2}: Respuesta correcta inválida")
                    continue
                
                # Mapear area a subject
                area_col = self.column_mapping['Area_Evaluada']
                area_evaluada = str(row[area_col]).strip()
                subject_name = area_to_subject.get(area_evaluada, area_evaluada)
                subject_id = self.subject_mapping.get(subject_name)
                
                if not subject_id:
                    self.errors.append(f"Fila {index + 2}: Área '{area_evaluada}' no mapeada a subject")
                    continue
                
                # Crear/obtener topic
                tema_col = self.column_mapping['Tema_Especifico']
                tema_especifico = str(row[tema_col]).strip() if pd.notna(row[tema_col]) else 'General'
                topic_id = self.create_topic_if_not_exists(tema_especifico, subject_id)
                
                if not topic_id:
                    self.errors.append(f"Fila {index + 2}: No se pudo crear/obtener topic")
                    continue
                
                # Generar UUID para la pregunta
                question_id = str(uuid.uuid4())
                
                # Preparar datos usando columnas mapeadas
                pregunta_texto = self.escape_sql_string(row[pregunta_col])
                pregunta_imagen = self.escape_sql_string(self.normalize_image_path(row.get('Imagen_Pregunta_URL')))
                
                opcion_a_texto = self.escape_sql_string(row[self.column_mapping['Opcion_A']])
                opcion_a_imagen = self.escape_sql_string(self.normalize_image_path(row.get('Imagen_Opcion_A_URL')))
                opcion_b_texto = self.escape_sql_string(row[self.column_mapping['Opcion_B']])
                opcion_b_imagen = self.escape_sql_string(self.normalize_image_path(row.get('Imagen_Opcion_B_URL')))
                opcion_c_texto = self.escape_sql_string(row[self.column_mapping['Opcion_C']])
                opcion_c_imagen = self.escape_sql_string(self.normalize_image_path(row.get('Imagen_Opcion_C_URL')))
                opcion_d_texto = self.escape_sql_string(row[self.column_mapping['Opcion_D']])
                opcion_d_imagen = self.escape_sql_string(self.normalize_image_path(row.get('Imagen_Opcion_D_URL')))
                
                respuesta_correcta = str(row[respuesta_col]).strip().lower()
                difficulty = self.map_difficulty(row.get('Nivel_Dificultad'))
                
                explanation = self.escape_sql_string(row.get('Explicación_Respuesta', ''))
                hint = self.escape_sql_string(row.get('Pista_1', ''))
                
                options_json = self.build_options_dict(row)
                power_stats_json = self.build_power_stats(row)
                tags_array = self.build_tags_array(row)
                
                # Construir SQL INSERT
                sql = f"""
                INSERT INTO questions (
                    id, topic_id, subject_id,
                    pregunta_texto, pregunta_imagen,
                    opcion_a_texto, opcion_a_imagen,
                    opcion_b_texto, opcion_b_imagen,
                    opcion_c_texto, opcion_c_imagen,
                    opcion_d_texto, opcion_d_imagen,
                    respuesta_correcta,
                    question_text, question_type, difficulty,
                    correct_answer, options, explanation, hint,
                    tags, power_stats, created_at
                ) VALUES (
                    '{question_id}', '{topic_id}', '{subject_id}',
                    {pregunta_texto}, {pregunta_imagen},
                    {opcion_a_texto}, {opcion_a_imagen},
                    {opcion_b_texto}, {opcion_b_imagen},
                    {opcion_c_texto}, {opcion_c_imagen},
                    {opcion_d_texto}, {opcion_d_imagen},
                    '{respuesta_correcta}',
                    {pregunta_texto}, 'multiple_choice', {difficulty},
                    '{respuesta_correcta.upper()}', '{options_json}', {explanation}, {hint},
                    {tags_array}, '{power_stats_json}', NOW()
                );
                """
                
                # Ejecutar SQL
                if self.execute_sql_in_docker(sql):
                    self.questions_loaded += 1
                    if self.questions_loaded % 50 == 0:
                        logger.info(f"Procesadas {self.questions_loaded} preguntas...")
                else:
                    self.errors.append(f"Fila {index + 2}: Error insertando en base de datos")
                
            except Exception as e:
                self.errors.append(f"Fila {index + 2}: Error procesando - {str(e)}")
                continue
        
        logger.info(f"Procesamiento completado: {self.questions_loaded} preguntas cargadas")
        return True

    def run(self):
        """Ejecuta el proceso completo de carga"""
        try:
            # Verificar que Docker esté corriendo
            result = subprocess.run(['docker', 'ps'], capture_output=True)
            if result.returncode != 0:
                logger.error("Docker no está corriendo o no está disponible")
                return False
            
            # Verificar que el contenedor PostgreSQL esté corriendo
            result = subprocess.run(['docker', 'ps', '--filter', f'name={DOCKER_CONTAINER}'], 
                                  capture_output=True, text=True)
            if DOCKER_CONTAINER not in result.stdout:
                logger.error(f"Contenedor PostgreSQL '{DOCKER_CONTAINER}' no está corriendo")
                return False
            
            # Cargar archivo Excel
            df = self.load_excel_file(EXCEL_PATH)
            
            # Validar columnas
            if not self.validate_required_columns(df):
                return False
            
            # Procesar preguntas
            success = self.process_questions(df)
            
            # Mostrar resultados
            print(f"\n{'='*60}")
            print(f"RESULTADOS DE LA CARGA COMPLETA DE PREGUNTAS ICFES")
            print(f"{'='*60}")
            print(f"[OK] Total de preguntas en Excel: {len(df)}")
            print(f"[OK] Preguntas cargadas exitosamente: {self.questions_loaded}")
            print(f"[ERROR] Errores encontrados: {len(self.errors)}")
            print(f"[WARN] Advertencias: {len(self.warnings)}")
            
            if self.errors:
                print(f"\n[ERROR] PRIMEROS 10 ERRORES:")
                for error in self.errors[:10]:
                    print(f"  - {error}")
                if len(self.errors) > 10:
                    print(f"  ... y {len(self.errors) - 10} errores más")
            
            if self.warnings:
                print(f"\n[WARN] ADVERTENCIAS:")
                for warning in self.warnings[:5]:
                    print(f"  - {warning}")
            
            print(f"\n{'='*60}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error en el proceso de carga: {e}")
            return False


def main():
    """Función principal"""
    print(f"INICIANDO CARGA COMPLETA DE 480 PREGUNTAS ICFES")
    print(f"Archivo Excel: {EXCEL_PATH}")
    print(f"Contenedor Docker: {DOCKER_CONTAINER}")
    print(f"Base de datos: {DB_CONFIG['database']}")
    print(f"{'='*60}\n")
    
    loader = ICFESExcelLoader()
    success = loader.run()
    
    if success:
        print(f"\nCARGA COMPLETADA EXITOSAMENTE!")
        sys.exit(0)
    else:
        print(f"\nCARGA FALLIDA - Revisar errores arriba")
        sys.exit(1)


if __name__ == "__main__":
    main()