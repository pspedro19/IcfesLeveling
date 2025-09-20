#!/usr/bin/env python3
"""
Direct SQL Import for ICFES Data - Uses raw SQL to avoid SQLAlchemy constructor issues
"""

import pandas as pd
import uuid
import json
import logging
import sys
import os
import psycopg2
from psycopg2.extras import Json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters
DATABASE_CONFIG = {
    'host': 'postgres',
    'port': 5432,
    'database': 'gameplay_db',
    'user': 'gameplay',
    'password': 'gameplay123'
}

def get_db_connection():
    """Create database connection"""
    return psycopg2.connect(**DATABASE_CONFIG)

def map_subject_name(area_evaluada):
    """Map Excel subject names to database subject names"""
    mapping = {
        'MATEMATICAS': 'Matemáticas',
        'MATEMÁTICAS': 'Matemáticas',
        'LENGUAJE': 'Lenguaje',
        'LECTURA CRITICA': 'Lenguaje',
        'LECTURA CRÍTICA': 'Lenguaje',
        'CIENCIAS NATURALES': 'Ciencias Naturales',
        'CIENCIAS SOCIALES': 'Ciencias Sociales',
        'INGLES': 'Inglés',
        'INGLÉS': 'Inglés'
    }
    return mapping.get(str(area_evaluada).upper(), str(area_evaluada))

def get_subject_id(cursor, subject_name):
    """Get subject ID from database"""
    cursor.execute("SELECT id FROM subjects WHERE name = %s", (subject_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_or_create_topic(cursor, tema_especifico, subject_id):
    """Get existing topic or create new one"""
    # Try to find existing topic
    cursor.execute("SELECT id FROM topics WHERE name = %s AND subject_id = %s", (tema_especifico, subject_id))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Create new topic
    topic_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO topics (id, subject_id, name, description, difficulty_level, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
    """, (topic_id, subject_id, tema_especifico, f"Tema específico: {tema_especifico}", 1))

    logger.info(f"Created new topic: {tema_especifico}")
    return topic_id

def import_excel_to_database():
    """Import complete Excel data to database using direct SQL"""

    # Path to Excel file
    excel_path = "/app/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"

    if not os.path.exists(excel_path):
        logger.error(f"❌ Excel file not found: {excel_path}")
        return {"ok": False, "error": f"File not found: {excel_path}"}

    logger.info(f"📂 Loading Excel file: {excel_path}")

    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        logger.info(f"📊 Loaded {len(df)} rows from Excel")

        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Clear existing questions if requested
        clear_existing = os.environ.get("IMPORT_CLEAR_EXISTING", "false").lower() in ("true", "1", "yes")
        if clear_existing:
            logger.info("🧹 Clearing existing questions...")
            cursor.execute("DELETE FROM questions")
            conn.commit()
            logger.info("✅ Existing questions cleared")

        imported_count = 0
        questions_with_images = 0
        errors = []

        # Process each row
        for index, row in df.iterrows():
            try:
                # Skip rows without question text
                if pd.isna(row['Pregunta']) or not str(row['Pregunta']).strip():
                    continue

                # Map subject
                area_evaluada = str(row['Área_Evaluada']).strip().upper()
                subject_name = map_subject_name(area_evaluada)
                subject_id = get_subject_id(cursor, subject_name)

                if not subject_id:
                    errors.append(f"Row {index + 2}: Subject not found for: {area_evaluada} -> {subject_name}")
                    continue

                # Map topic
                tema_especifico = str(row.get('Tema_Especifico', 'General')).strip()
                if not tema_especifico or tema_especifico == 'nan':
                    tema_especifico = 'General'
                topic_id = get_or_create_topic(cursor, tema_especifico, subject_id)

                # Generate UUID for question
                question_id = str(uuid.uuid4())

                # Extract main question data
                pregunta_texto = str(row['Pregunta']).strip()
                respuesta_correcta = str(row['Respuesta_Correcta']).strip().upper() if pd.notna(row['Respuesta_Correcta']) else 'A'

                # Validate correct answer
                if respuesta_correcta not in ['A', 'B', 'C', 'D']:
                    errors.append(f"Row {index + 2}: Invalid correct answer: {respuesta_correcta}")
                    continue

                # Build options JSON
                options = {}
                for option in ['A', 'B', 'C', 'D']:
                    option_value = row.get(f'Opcion_{option}', '')
                    if pd.notna(option_value) and str(option_value).strip():
                        options[option] = str(option_value).strip()

                # Validate that at least 2 options exist
                if len(options) < 2:
                    errors.append(f"Row {index + 2}: Must have at least 2 options")
                    continue

                # Validate that correct answer exists in options
                if respuesta_correcta not in options:
                    errors.append(f"Row {index + 2}: Correct answer {respuesta_correcta} not in options")
                    continue

                # Extract difficulty
                difficulty = 5  # Default
                if pd.notna(row['Nivel_Dificultad']):
                    try:
                        difficulty = int(row['Nivel_Dificultad'])
                        if not (1 <= difficulty <= 10):
                            difficulty = 5
                    except:
                        difficulty = 5

                # Extract XP points
                puntos_xp = 10
                if pd.notna(row['Puntos_XP']):
                    try:
                        puntos_xp = int(row['Puntos_XP'])
                    except:
                        puntos_xp = 10

                # Extract text for each option
                opcion_a_texto = str(row.get('Opcion_A', '')).strip() if pd.notna(row.get('Opcion_A')) else None
                opcion_b_texto = str(row.get('Opcion_B', '')).strip() if pd.notna(row.get('Opcion_B')) else None
                opcion_c_texto = str(row.get('Opcion_C', '')).strip() if pd.notna(row.get('Opcion_C')) else None
                opcion_d_texto = str(row.get('Opcion_D', '')).strip() if pd.notna(row.get('Opcion_D')) else None

                # Extract image URLs (clean paths)
                pregunta_imagen = None
                if pd.notna(row['Imagen_Pregunta_URL']) and str(row['Imagen_Pregunta_URL']).strip():
                    pregunta_imagen = str(row['Imagen_Pregunta_URL']).strip()

                opcion_a_imagen = None
                if pd.notna(row.get('Imagen_Opcion_A_URL')) and str(row.get('Imagen_Opcion_A_URL')).strip():
                    opcion_a_imagen = str(row['Imagen_Opcion_A_URL']).strip()

                opcion_b_imagen = None
                if pd.notna(row.get('Imagen_Opcion_B_URL')) and str(row.get('Imagen_Opcion_B_URL')).strip():
                    opcion_b_imagen = str(row['Imagen_Opcion_B_URL']).strip()

                opcion_c_imagen = None
                if pd.notna(row.get('Imagen_Opcion_C_URL')) and str(row.get('Imagen_Opcion_C_URL')).strip():
                    opcion_c_imagen = str(row['Imagen_Opcion_C_URL']).strip()

                opcion_d_imagen = None
                if pd.notna(row.get('Imagen_Opcion_D_URL')) and str(row.get('Imagen_Opcion_D_URL')).strip():
                    opcion_d_imagen = str(row['Imagen_Opcion_D_URL']).strip()

                # Count questions with images
                if any([pregunta_imagen, opcion_a_imagen, opcion_b_imagen, opcion_c_imagen, opcion_d_imagen]):
                    questions_with_images += 1

                # Extract additional fields
                explanation = str(row.get('Explicación_Respuesta', '')).strip() if pd.notna(row.get('Explicación_Respuesta')) else None
                hint = str(row.get('Contexto', '')).strip() if pd.notna(row.get('Contexto')) else None

                # Build tags
                tags = []
                if pd.notna(row.get('Competencia')) and str(row['Competencia']).strip():
                    tags.append(str(row['Competencia']).strip())
                if pd.notna(row.get('Proceso_Cognitivo')) and str(row['Proceso_Cognitivo']).strip():
                    tags.append(str(row['Proceso_Cognitivo']).strip())

                # Build power_stats
                power_stats = {
                    "discrimination_index": 0.5,
                    "success_rate": 0.6,
                    "estimated_time": 120,
                    "xp_reward": puntos_xp,
                    "original_id": str(row.get('ID_Pregunta', '')),
                    "cognitive_process": str(row.get('Proceso_Cognitivo', '')),
                    "knowledge_type": str(row.get('Tipo_Conocimiento', ''))
                }

                # Insert question using direct SQL
                insert_query = """
                INSERT INTO questions (
                    id, topic_id, subject_id,
                    pregunta_texto, pregunta_imagen,
                    opcion_a_texto, opcion_a_imagen,
                    opcion_b_texto, opcion_b_imagen,
                    opcion_c_texto, opcion_c_imagen,
                    opcion_d_texto, opcion_d_imagen,
                    respuesta_correcta, puntos_xp,
                    question_text, question_type, difficulty, correct_answer, options,
                    explanation, hint, tags, power_stats, created_at
                ) VALUES (
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, NOW()
                )
                """

                cursor.execute(insert_query, (
                    question_id, topic_id, subject_id,
                    pregunta_texto, pregunta_imagen,
                    opcion_a_texto, opcion_a_imagen,
                    opcion_b_texto, opcion_b_imagen,
                    opcion_c_texto, opcion_c_imagen,
                    opcion_d_texto, opcion_d_imagen,
                    respuesta_correcta.lower(), puntos_xp,
                    pregunta_texto, 'multiple_choice', difficulty, respuesta_correcta, Json(options),
                    explanation, hint, tags, Json(power_stats)
                ))

                imported_count += 1

                if imported_count <= 5 or imported_count % 50 == 0:
                    logger.info(f"  ✅ Imported {imported_count}: {pregunta_texto[:50]}...")

            except Exception as e:
                errors.append(f"Row {index + 2}: Error processing - {str(e)}")
                continue

        # Commit all changes
        conn.commit()
        logger.info(f"\n🎉 Successfully imported {imported_count} questions from Excel")
        logger.info(f"📸 Questions with images: {questions_with_images}")
        logger.info(f"❌ Errors: {len(errors)}")

        # Verify results by subject
        cursor.execute("""
        SELECT
            s.name as subject_name,
            COUNT(q.id) as total_questions,
            COUNT(CASE WHEN q.pregunta_imagen IS NOT NULL THEN 1 END) as with_pregunta_imagen,
            COUNT(CASE WHEN q.opcion_a_imagen IS NOT NULL OR q.opcion_b_imagen IS NOT NULL
                      OR q.opcion_c_imagen IS NOT NULL OR q.opcion_d_imagen IS NOT NULL THEN 1 END) as with_option_images
        FROM subjects s
        LEFT JOIN questions q ON s.id = q.subject_id
        GROUP BY s.id, s.name
        ORDER BY s.name
        """)

        results = cursor.fetchall()
        logger.info(f"\n📊 Questions imported by subject:")
        for result in results:
            subject_name, total_q, with_pregunta_img, with_option_imgs = result
            logger.info(f"  {subject_name}: {total_q} questions ({with_pregunta_img} with question images, {with_option_imgs} with option images)")

        cursor.close()
        conn.close()

        return {
            "ok": True,
            "excel_path": excel_path,
            "result": {
                "imported_questions": imported_count,
                "errors": errors[:10],  # Show only first 10 errors
                "warnings": []
            },
            "db_total_questions": imported_count,
            "questions_with_images": questions_with_images
        }

    except Exception as e:
        error_msg = f"❌ Error processing Excel file: {e}"
        logger.error(error_msg)
        import traceback
        traceback.print_exc()
        return {"ok": False, "error": error_msg}

if __name__ == "__main__":
    logger.info("🚀 Starting Direct SQL ICFES Excel Import Process")
    logger.info("📋 This will import all real questions from Excel using direct SQL")
    logger.info("=" * 60)

    result = import_excel_to_database()

    if result["ok"]:
        logger.info(f"\n✅ Import Process Completed Successfully!")
        logger.info(f"📊 Total questions imported: {result['result']['imported_questions']}")
        logger.info(f"🖼️ Questions with images: {result['questions_with_images']}")
        logger.info(f"❌ Errors: {len(result['result']['errors'])}")
    else:
        logger.error(f"\n❌ Import Process Failed: {result['error']}")

    print(json.dumps(result, indent=2))