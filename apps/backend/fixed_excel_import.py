#!/usr/bin/env python3
"""
Fixed ICFES Excel Import Script - Works with actual database schema
"""

import pandas as pd
import uuid
import json
import logging
import sys
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text

# Add the app directory to Python path
sys.path.append('/app')

from app.core.database import get_db, engine
from app.models.topic import Topic
from app.models.question import Question
from app.models.subject import Subject

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedICFESExcelImporter:
    def __init__(self, db: Session):
        self.db = db
        self.subjects_mapping = self._load_subjects_mapping()
        self.topics_mapping = self._load_topics_mapping()
        self.imported_questions = 0
        self.errors = []
        self.warnings = []

    def _load_subjects_mapping(self):
        """Map Excel subject names to database subject IDs"""
        subjects = self.db.query(Subject).all()
        mapping = {}

        # Direct mapping
        area_to_subject = {
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

        for subject in subjects:
            for area, subject_name in area_to_subject.items():
                if subject.name == subject_name:
                    mapping[area] = str(subject.id)

        logger.info(f"Subjects mapping loaded: {mapping}")
        return mapping

    def _load_topics_mapping(self):
        """Map topics to existing ones"""
        topics = self.db.query(Topic).all()
        mapping = {}

        for topic in topics:
            mapping[topic.name] = str(topic.id)

        logger.info(f"Topics mapping loaded with {len(mapping)} topics")
        return mapping

    def _create_or_get_topic(self, tema_especifico: str, subject_id: str):
        """Create topic if it doesn't exist or get existing one"""
        if tema_especifico in self.topics_mapping:
            return self.topics_mapping[tema_especifico]

        # Create new topic
        topic = Topic(
            id=uuid.uuid4(),
            subject_id=subject_id,
            name=tema_especifico,
            description=f"Tema específico: {tema_especifico}",
            difficulty_level=1
        )
        self.db.add(topic)
        self.db.commit()
        self.db.refresh(topic)

        # Update mapping
        self.topics_mapping[tema_especifico] = str(topic.id)
        logger.info(f"Created new topic: {tema_especifico}")

        return str(topic.id)

    def _map_difficulty(self, nivel_dificultad):
        """Map difficulty level to 1-10 scale"""
        if pd.isna(nivel_dificultad):
            return 5

        try:
            num_difficulty = int(nivel_dificultad)
            if 1 <= num_difficulty <= 10:
                return num_difficulty
        except (ValueError, TypeError):
            pass

        # Default difficulty
        return 5

    def _build_options(self, row):
        """Build options dict from Excel columns"""
        options = {}

        for option in ['A', 'B', 'C', 'D']:
            option_value = row.get(f'Opcion_{option}', '')
            if pd.notna(option_value) and str(option_value).strip():
                options[option] = str(option_value).strip()

        return options

    def _build_tags(self, row):
        """Build tags array from competencias and other fields"""
        tags = []

        # Competencia
        competencia = row.get('Competencia', '')
        if pd.notna(competencia) and str(competencia).strip():
            tags.append(str(competencia).strip())

        # Proceso cognitivo
        proceso = row.get('Proceso_Cognitivo', '')
        if pd.notna(proceso) and str(proceso).strip():
            tags.append(str(proceso).strip())

        # Tipo de conocimiento
        tipo_conocimiento = row.get('Tipo_Conocimiento', '')
        if pd.notna(tipo_conocimiento) and str(tipo_conocimiento).strip():
            tags.append(str(tipo_conocimiento).strip())

        return tags

    def _build_power_stats(self, row):
        """Build power_stats with metadata"""
        power_stats = {
            "discrimination_index": 0.5,
            "success_rate": 0.6,
            "estimated_time": int(row.get('Tiempo_Estimado', 60)),
            "xp_reward": int(row.get('Puntos_XP', 10)),
            "original_id": str(row.get('ID_Pregunta', '')),
            "bank_origin": str(row.get('Banco_Origen', '')),
            "question_type": str(row.get('Tipo_Pregunta', 'multiple_choice')),
            "cognitive_process": str(row.get('Proceso_Cognitivo', '')),
            "knowledge_type": str(row.get('Tipo_Conocimiento', '')),
            "performance_level": str(row.get('Nivel_Desempeno_Esperado', '')),
        }

        return power_stats

    def _validate_question_data(self, row):
        """Validate question data before importing"""
        errors = []

        # Validate question text
        pregunta = row.get('Pregunta', '')
        if pd.isna(pregunta) or not str(pregunta).strip():
            errors.append("Pregunta está vacía")

        # Validate correct answer
        respuesta_correcta = row.get('Respuesta_Correcta', '')
        if pd.isna(respuesta_correcta) or str(respuesta_correcta).strip().upper() not in ['A', 'B', 'C', 'D']:
            errors.append("Respuesta correcta debe ser A, B, C o D")

        # Validate options
        options = self._build_options(row)
        if len(options) < 2:
            errors.append("Debe tener al menos 2 opciones")

        if respuesta_correcta and str(respuesta_correcta).upper() not in options:
            errors.append("Respuesta correcta no coincide con las opciones disponibles")

        # Validate subject
        area_evaluada = row.get('Área_Evaluada', '')
        if pd.isna(area_evaluada) or str(area_evaluada).strip().upper() not in self.subjects_mapping:
            errors.append(f"Área evaluada '{area_evaluada}' no está mapeada")

        return errors

    def import_excel(self, file_path: str, validate_only: bool = False):
        """Import questions from Excel file"""
        try:
            logger.info(f"Reading Excel file: {file_path}")
            df = pd.read_excel(file_path)

            logger.info(f"File read: {len(df)} rows found")

            # Process each row
            for index, row in df.iterrows():
                try:
                    # Validate data
                    errors = self._validate_question_data(row)
                    if errors:
                        self.errors.append(f"Row {index + 2}: {'; '.join(errors)}")
                        continue

                    if validate_only:
                        self.imported_questions += 1
                        continue

                    # Map subject
                    area_evaluada = str(row['Área_Evaluada']).strip().upper()
                    subject_id = self.subjects_mapping.get(area_evaluada)
                    if not subject_id:
                        self.errors.append(f"Row {index + 2}: Subject '{area_evaluada}' not mapped")
                        continue

                    # Map topic - use default if not specified
                    tema_especifico = str(row.get('Tema_Especifico', 'General')).strip()
                    if not tema_especifico or tema_especifico == 'nan':
                        tema_especifico = 'General'
                    topic_id = self._create_or_get_topic(tema_especifico, subject_id)

                    # Build question data with correct field names
                    question_data = {
                        'id': uuid.uuid4(),
                        'topic_id': topic_id,
                        'subject_id': subject_id,

                        # Main question fields
                        'pregunta_texto': str(row['Pregunta']).strip(),
                        'pregunta_imagen': str(row.get('Imagen_Pregunta_URL', '')).strip() if pd.notna(row.get('Imagen_Pregunta_URL')) else None,

                        # Option text fields
                        'opcion_a_texto': str(row.get('Opcion_A', '')).strip() if pd.notna(row.get('Opcion_A')) else None,
                        'opcion_b_texto': str(row.get('Opcion_B', '')).strip() if pd.notna(row.get('Opcion_B')) else None,
                        'opcion_c_texto': str(row.get('Opcion_C', '')).strip() if pd.notna(row.get('Opcion_C')) else None,
                        'opcion_d_texto': str(row.get('Opcion_D', '')).strip() if pd.notna(row.get('Opcion_D')) else None,

                        # Option image fields
                        'opcion_a_imagen': str(row.get('Imagen_Opcion_A_URL', '')).strip() if pd.notna(row.get('Imagen_Opcion_A_URL')) else None,
                        'opcion_b_imagen': str(row.get('Imagen_Opcion_B_URL', '')).strip() if pd.notna(row.get('Imagen_Opcion_B_URL')) else None,
                        'opcion_c_imagen': str(row.get('Imagen_Opcion_C_URL', '')).strip() if pd.notna(row.get('Imagen_Opcion_C_URL')) else None,
                        'opcion_d_imagen': str(row.get('Imagen_Opcion_D_URL', '')).strip() if pd.notna(row.get('Imagen_Opcion_D_URL')) else None,

                        # Correct answer
                        'respuesta_correcta': str(row['Respuesta_Correcta']).strip().upper(),

                        # Legacy fields for compatibility
                        'question_text': str(row['Pregunta']).strip(),
                        'question_type': 'multiple_choice',
                        'difficulty': self._map_difficulty(row.get('Nivel_Dificultad')),
                        'correct_answer': str(row['Respuesta_Correcta']).strip().upper(),
                        'options': self._build_options(row),
                        'explanation': str(row.get('Explicación_Respuesta', '')).strip() if pd.notna(row.get('Explicación_Respuesta')) else None,
                        'hint': str(row.get('Contexto', '')).strip() if pd.notna(row.get('Contexto')) else None,
                        'tags': self._build_tags(row),
                        'power_stats': self._build_power_stats(row),
                        'puntos_xp': int(row.get('Puntos_XP', 10))
                    }

                    # Create question object
                    question = Question(**question_data)

                    # Validate question
                    validation_errors = question.validate_question()
                    if validation_errors:
                        self.errors.append(f"Row {index + 2}: {'; '.join(validation_errors)}")
                        continue

                    # Save to database
                    self.db.add(question)
                    self.imported_questions += 1

                    # Log progress
                    if self.imported_questions % 50 == 0:
                        logger.info(f"Processed {self.imported_questions} questions...")
                        self.db.commit()

                except Exception as e:
                    self.errors.append(f"Row {index + 2}: Error processing - {str(e)}")
                    continue

            # Final commit
            if not validate_only:
                self.db.commit()

            logger.info(f"Import completed: {self.imported_questions} questions processed")

            return {
                "imported_questions": self.imported_questions,
                "errors": self.errors,
                "warnings": self.warnings
            }

        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            raise


def main():
    """Main execution function"""
    excel_path = "/app/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"

    # Verify file exists
    if not os.path.exists(excel_path):
        logger.error(f"Excel file not found: {excel_path}")
        return {"ok": False, "error": f"File not found: {excel_path}"}

    # Connect to database
    db = next(get_db())

    try:
        # Clear existing questions if requested
        clear_existing = os.environ.get("IMPORT_CLEAR_EXISTING", "false").lower() in ("true", "1", "yes")
        if clear_existing:
            logger.info("Clearing existing questions...")
            db.query(Question).delete()
            db.commit()
            logger.info("Existing questions cleared")

        # Import questions
        importer = FixedICFESExcelImporter(db)
        result = importer.import_excel(excel_path, validate_only=False)

        # Get total questions
        total_questions = db.query(Question).count()

        summary = {
            "ok": True,
            "excel_path": excel_path,
            "result": result,
            "db_total_questions": total_questions,
        }

        logger.info(f"✅ Import successful: {result['imported_questions']} questions imported")
        logger.info(f"📊 Total questions in database: {total_questions}")
        logger.info(f"❌ Errors: {len(result['errors'])}")

        return summary

    except Exception as e:
        error_msg = f"Import error: {str(e)}"
        logger.error(error_msg)
        return {"ok": False, "error": error_msg}
    finally:
        db.close()


if __name__ == "__main__":
    import json
    result = main()
    print(json.dumps(result, indent=2))