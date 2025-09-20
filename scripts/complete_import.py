#!/usr/bin/env python3
"""
ICFES LEVELING - Sistema de Importación Completa
Este script importa datos desde archivos Excel de forma robusta y confiable
"""

import os
import sys
import pandas as pd
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://gameplay:gameplay123@postgres:5432/gameplay_db')

def get_db_connection():
    """Crear conexión a la base de datos"""
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return engine, SessionLocal()
    except Exception as e:
        logger.error(f"Error conectando a la base de datos: {e}")
        return None, None

def find_excel_files():
    """Buscar archivos Excel con preguntas"""
    possible_paths = [
        '/app/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx',
        '/app/ICFES_questions.xlsx',
        '/app/ICFES2.xlsx',
        '/app/ICFES2 (1).xlsx',
        '/root/IcfesLeveling/database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx',
        '/root/IcfesLeveling/apps/backend/ICFES_questions.xlsx'
    ]

    for path in possible_paths:
        if os.path.exists(path):
            logger.info(f"Archivo Excel encontrado: {path}")
            return path

    logger.warning("No se encontraron archivos Excel")
    return None

def load_subjects_mapping(session):
    """Cargar mapeo de materias desde la base de datos"""
    try:
        result = session.execute(text("SELECT id, name FROM subjects"))
        subjects = {row[1]: str(row[0]) for row in result}

        # Agregar alias comunes
        if 'Matemáticas' in subjects:
            subjects['Matematicas'] = subjects['Matemáticas']
            subjects['MATEMÁTICAS'] = subjects['Matemáticas']

        if 'Lectura Crítica' in subjects:
            subjects['Lenguaje'] = subjects['Lectura Crítica']
            subjects['LENGUAJE'] = subjects['Lectura Crítica']
            subjects['Lectura Critica'] = subjects['Lectura Crítica']

        if 'Ciencias Naturales' in subjects:
            subjects['Ciencias'] = subjects['Ciencias Naturales']
            subjects['CIENCIAS NATURALES'] = subjects['Ciencias Naturales']

        if 'Ciencias Sociales' in subjects:
            subjects['Sociales'] = subjects['Ciencias Sociales']
            subjects['CIENCIAS SOCIALES'] = subjects['Ciencias Sociales']

        if 'Inglés' in subjects:
            subjects['English'] = subjects['Inglés']
            subjects['INGLÉS'] = subjects['Inglés']
            subjects['ENGLISH'] = subjects['Inglés']

        logger.info(f"Materias cargadas: {list(subjects.keys())}")
        return subjects
    except Exception as e:
        logger.error(f"Error cargando materias: {e}")
        return {}

def create_sample_questions(session, subjects_mapping):
    """Crear preguntas de ejemplo como respaldo"""
    logger.info("Creando preguntas de ejemplo...")

    sample_questions = [
        # Matemáticas
        {
            'subject': 'Matemáticas',
            'topic': 'Álgebra',
            'question': '¿Cuál es el valor de x en la ecuación 2x + 5 = 13?',
            'option_a': 'x = 3',
            'option_b': 'x = 4',
            'option_c': 'x = 5',
            'option_d': 'x = 6',
            'correct_answer': 'B',
            'explanation': 'Despejando: 2x = 13 - 5 = 8, entonces x = 4'
        },
        {
            'subject': 'Matemáticas',
            'topic': 'Geometría',
            'question': '¿Cuál es el área de un triángulo con base 6 cm y altura 8 cm?',
            'option_a': '24 cm²',
            'option_b': '48 cm²',
            'option_c': '14 cm²',
            'option_d': '32 cm²',
            'correct_answer': 'A',
            'explanation': 'Área = (base × altura) / 2 = (6 × 8) / 2 = 24 cm²'
        },
        # Lectura Crítica
        {
            'subject': 'Lectura Crítica',
            'topic': 'Comprensión Lectora',
            'question': 'En el texto "La importancia de la educación", ¿cuál es la idea principal?',
            'option_a': 'La educación es costosa',
            'option_b': 'La educación transforma vidas',
            'option_c': 'La educación es obligatoria',
            'option_d': 'La educación es divertida',
            'correct_answer': 'B',
            'explanation': 'El texto enfatiza cómo la educación tiene el poder de transformar vidas y sociedades'
        },
        # Ciencias Naturales
        {
            'subject': 'Ciencias Naturales',
            'topic': 'Biología',
            'question': '¿Cuál es la función principal de los ribosomas en la célula?',
            'option_a': 'Producir energía',
            'option_b': 'Sintetizar proteínas',
            'option_c': 'Almacenar información genética',
            'option_d': 'Digerir sustancias',
            'correct_answer': 'B',
            'explanation': 'Los ribosomas son los orgánulos responsables de la síntesis de proteínas'
        },
        # Ciencias Sociales
        {
            'subject': 'Ciencias Sociales',
            'topic': 'Historia de Colombia',
            'question': '¿En qué año se firmó la independencia de Colombia?',
            'option_a': '1810',
            'option_b': '1819',
            'option_c': '1821',
            'option_d': '1830',
            'correct_answer': 'B',
            'explanation': 'La independencia de Colombia se consolidó con la Batalla de Boyacá en 1819'
        },
        # Inglés
        {
            'subject': 'Inglés',
            'topic': 'Grammar',
            'question': 'Choose the correct form: "She _____ to school every day."',
            'option_a': 'go',
            'option_b': 'goes',
            'option_c': 'going',
            'option_d': 'gone',
            'correct_answer': 'B',
            'explanation': 'For third person singular in present simple, we add -s to the verb: goes'
        }
    ]

    try:
        for i, q_data in enumerate(sample_questions):
            subject_id = subjects_mapping.get(q_data['subject'])
            if not subject_id:
                continue

            # Buscar o crear topic
            topic_result = session.execute(text("""
                SELECT id FROM topics WHERE subject_id = :subject_id AND name = :topic_name
            """), {"subject_id": subject_id, "topic_name": q_data['topic']})

            topic_row = topic_result.first()
            if topic_row:
                topic_id = str(topic_row[0])
            else:
                topic_id = str(uuid.uuid4())
                session.execute(text("""
                    INSERT INTO topics (id, subject_id, name, description, difficulty_level)
                    VALUES (:id, :subject_id, :name, :description, :difficulty_level)
                """), {
                    "id": topic_id,
                    "subject_id": subject_id,
                    "name": q_data['topic'],
                    "description": f"Tema de {q_data['subject']}",
                    "difficulty_level": 2
                })

            # Crear pregunta
            question_id = str(uuid.uuid4())
            session.execute(text("""
                INSERT INTO questions (
                    id, subject_id, topic_id, question_text, option_a, option_b,
                    option_c, option_d, correct_answer, explanation, difficulty_level,
                    question_type, points_value, time_limit, is_active
                ) VALUES (
                    :id, :subject_id, :topic_id, :question_text, :option_a, :option_b,
                    :option_c, :option_d, :correct_answer, :explanation, :difficulty_level,
                    :question_type, :points_value, :time_limit, :is_active
                )
            """), {
                "id": question_id,
                "subject_id": subject_id,
                "topic_id": topic_id,
                "question_text": q_data['question'],
                "option_a": q_data['option_a'],
                "option_b": q_data['option_b'],
                "option_c": q_data['option_c'],
                "option_d": q_data['option_d'],
                "correct_answer": q_data['correct_answer'],
                "explanation": q_data['explanation'],
                "difficulty_level": 2,
                "question_type": "multiple_choice",
                "points_value": 10,
                "time_limit": 60,
                "is_active": True
            })

        session.commit()
        logger.info(f"Creadas {len(sample_questions)} preguntas de ejemplo")
        return len(sample_questions)

    except Exception as e:
        session.rollback()
        logger.error(f"Error creando preguntas de ejemplo: {e}")
        return 0

def import_from_excel(excel_path, session, subjects_mapping):
    """Importar preguntas desde archivo Excel"""
    try:
        logger.info(f"Importando desde: {excel_path}")

        # Leer Excel con diferentes codificaciones
        try:
            df = pd.read_excel(excel_path, engine='openpyxl')
        except:
            df = pd.read_excel(excel_path, engine='xlrd')

        logger.info(f"Archivo cargado con {len(df)} filas")
        logger.info(f"Columnas disponibles: {list(df.columns)}")

        # Mapeo flexible de columnas
        column_mapping = {}
        for col in df.columns:
            col_lower = str(col).lower().strip()

            # Mapear columnas comunes
            if any(x in col_lower for x in ['pregunta', 'question', 'enunciado']):
                column_mapping['question_text'] = col
            elif any(x in col_lower for x in ['opcion_a', 'option_a', 'a)']):
                column_mapping['option_a'] = col
            elif any(x in col_lower for x in ['opcion_b', 'option_b', 'b)']):
                column_mapping['option_b'] = col
            elif any(x in col_lower for x in ['opcion_c', 'option_c', 'c)']):
                column_mapping['option_c'] = col
            elif any(x in col_lower for x in ['opcion_d', 'option_d', 'd)']):
                column_mapping['option_d'] = col
            elif any(x in col_lower for x in ['respuesta', 'answer', 'correcta']):
                column_mapping['correct_answer'] = col
            elif any(x in col_lower for x in ['materia', 'subject', 'area']):
                column_mapping['subject'] = col
            elif any(x in col_lower for x in ['tema', 'topic', 'subtema']):
                column_mapping['topic'] = col
            elif any(x in col_lower for x in ['explicacion', 'explanation']):
                column_mapping['explanation'] = col

        logger.info(f"Mapeo de columnas: {column_mapping}")

        imported_count = 0
        error_count = 0

        for index, row in df.iterrows():
            try:
                # Extraer datos de la fila
                question_text = str(row.get(column_mapping.get('question_text', ''), '')).strip()
                if not question_text or question_text == 'nan':
                    continue

                # Determinar materia
                subject_name = str(row.get(column_mapping.get('subject', ''), '')).strip()
                subject_id = None

                for key, value in subjects_mapping.items():
                    if key.lower() in subject_name.lower() or subject_name.lower() in key.lower():
                        subject_id = value
                        break

                if not subject_id:
                    # Usar materia por defecto si no se encuentra
                    subject_id = list(subjects_mapping.values())[0] if subjects_mapping else None

                if not subject_id:
                    continue

                # Crear/obtener topic
                topic_name = str(row.get(column_mapping.get('topic', ''), 'General')).strip()
                if not topic_name or topic_name == 'nan':
                    topic_name = 'General'

                topic_result = session.execute(text("""
                    SELECT id FROM topics WHERE subject_id = :subject_id AND name = :topic_name
                """), {"subject_id": subject_id, "topic_name": topic_name})

                topic_row = topic_result.first()
                if topic_row:
                    topic_id = str(topic_row[0])
                else:
                    topic_id = str(uuid.uuid4())
                    session.execute(text("""
                        INSERT INTO topics (id, subject_id, name, description, difficulty_level)
                        VALUES (:id, :subject_id, :name, :description, :difficulty_level)
                    """), {
                        "id": topic_id,
                        "subject_id": subject_id,
                        "name": topic_name,
                        "description": f"Tema: {topic_name}",
                        "difficulty_level": 2
                    })

                # Crear pregunta
                question_id = str(uuid.uuid4())

                option_a = str(row.get(column_mapping.get('option_a', ''), 'Opción A')).strip()
                option_b = str(row.get(column_mapping.get('option_b', ''), 'Opción B')).strip()
                option_c = str(row.get(column_mapping.get('option_c', ''), 'Opción C')).strip()
                option_d = str(row.get(column_mapping.get('option_d', ''), 'Opción D')).strip()

                correct_answer = str(row.get(column_mapping.get('correct_answer', ''), 'A')).strip().upper()
                if correct_answer not in ['A', 'B', 'C', 'D']:
                    correct_answer = 'A'

                explanation = str(row.get(column_mapping.get('explanation', ''), 'Explicación no disponible')).strip()

                session.execute(text("""
                    INSERT INTO questions (
                        id, subject_id, topic_id, question_text, option_a, option_b,
                        option_c, option_d, correct_answer, explanation, difficulty_level,
                        question_type, points_value, time_limit, is_active
                    ) VALUES (
                        :id, :subject_id, :topic_id, :question_text, :option_a, :option_b,
                        :option_c, :option_d, :correct_answer, :explanation, :difficulty_level,
                        :question_type, :points_value, :time_limit, :is_active
                    )
                """), {
                    "id": question_id,
                    "subject_id": subject_id,
                    "topic_id": topic_id,
                    "question_text": question_text,
                    "option_a": option_a,
                    "option_b": option_b,
                    "option_c": option_c,
                    "option_d": option_d,
                    "correct_answer": correct_answer,
                    "explanation": explanation,
                    "difficulty_level": 2,
                    "question_type": "multiple_choice",
                    "points_value": 10,
                    "time_limit": 60,
                    "is_active": True
                })

                imported_count += 1

                if imported_count % 100 == 0:
                    session.commit()
                    logger.info(f"Importadas {imported_count} preguntas...")

            except Exception as e:
                error_count += 1
                logger.warning(f"Error en fila {index}: {e}")
                continue

        session.commit()
        logger.info(f"Importación completada: {imported_count} preguntas importadas, {error_count} errores")
        return imported_count

    except Exception as e:
        session.rollback()
        logger.error(f"Error en importación Excel: {e}")
        return 0

def run_complete_import():
    """Ejecutar importación completa"""
    logger.info("🚀 Iniciando importación completa de datos...")

    # Conectar a la base de datos
    engine, session = get_db_connection()
    if not session:
        logger.error("No se pudo conectar a la base de datos")
        return False

    try:
        # Cargar mapeo de materias
        subjects_mapping = load_subjects_mapping(session)
        if not subjects_mapping:
            logger.error("No se pudieron cargar las materias")
            return False

        # Buscar archivo Excel
        excel_path = find_excel_files()

        total_imported = 0

        if excel_path:
            # Importar desde Excel
            total_imported = import_from_excel(excel_path, session, subjects_mapping)

        if total_imported == 0:
            # Crear preguntas de ejemplo como respaldo
            logger.info("No se importaron preguntas desde Excel, creando ejemplos...")
            total_imported = create_sample_questions(session, subjects_mapping)

        # Verificar estado final
        result = session.execute(text("SELECT COUNT(*) FROM questions"))
        final_count = result.scalar()

        logger.info(f"✅ Importación completada: {final_count} preguntas totales en la base de datos")

        session.close()
        return total_imported > 0

    except Exception as e:
        logger.error(f"Error en importación completa: {e}")
        if session:
            session.rollback()
            session.close()
        return False

if __name__ == "__main__":
    success = run_complete_import()
    sys.exit(0 if success else 1)