#!/usr/bin/env python3
"""
Script to fix database issues and import questions
"""

import os
import sys
import logging
import uuid
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database():
    """Fix all database issues"""
    try:
        from app.core.database import engine, get_db
        from app.models.question import Question, Topic
        from app.models.subject import Subject
        from app.import_icfes_excel import ICFESExcelImporter
        from sqlalchemy import text
        
        logger.info("Starting database fix...")
        
        # Get database session
        db = next(get_db())
        
        # 1. Ensure subjects exist
        logger.info("Checking subjects...")
        subjects = {
            "Matemáticas": {
                "description": "Razonamiento cuantitativo y matemático",
                "icon": "🔢",
                "color": "#FF6B6B"
            },
            "Lenguaje": {
                "description": "Comprensión lectora y comunicación escrita",
                "icon": "📚",
                "color": "#4ECDC4"
            },
            "Ciencias Naturales": {
                "description": "Física, Química y Biología",
                "icon": "🔬",
                "color": "#95E77E"
            },
            "Ciencias Sociales": {
                "description": "Historia, Geografía y Competencias Ciudadanas",
                "icon": "🌍",
                "color": "#FFE66D"
            },
            "Inglés": {
                "description": "Comprensión y uso del idioma inglés",
                "icon": "🌐",
                "color": "#A8E6CF"
            }
        }
        
        for subject_name, subject_data in subjects.items():
            existing = db.query(Subject).filter(Subject.name == subject_name).first()
            if not existing:
                subject = Subject(
                    id=uuid.uuid4(),
                    name=subject_name,
                    description=subject_data["description"],
                    icon=subject_data["icon"],
                    color=subject_data["color"]
                )
                db.add(subject)
                logger.info(f"Created subject: {subject_name}")
            else:
                logger.info(f"Subject already exists: {subject_name}")
        
        db.commit()
        
        # 2. Create default topics for each subject
        logger.info("Creating default topics...")
        subject_topics = {
            "Matemáticas": ["Álgebra Básica", "Geometría Euclidiana", "Cálculo Diferencial", "Probabilidad", "Estadística"],
            "Lenguaje": ["Comprensión Lectora", "Gramática", "Literatura", "Producción Textual", "Semántica"],
            "Ciencias Naturales": ["Mecánica Clásica", "Química Orgánica", "Biología Celular", "Ecología", "Termodinámica"],
            "Ciencias Sociales": ["Historia", "Geografía", "Filosofía", "Economía", "Política"],
            "Inglés": ["Grammar", "Vocabulary", "Reading Comprehension", "Listening", "Writing"]
        }
        
        for subject_name, topic_names in subject_topics.items():
            subject = db.query(Subject).filter(Subject.name == subject_name).first()
            if subject:
                for topic_name in topic_names:
                    existing_topic = db.query(Topic).filter(
                        Topic.name == topic_name,
                        Topic.subject_id == subject.id
                    ).first()
                    
                    if not existing_topic:
                        topic = Topic(
                            id=uuid.uuid4(),
                            subject_id=subject.id,
                            name=topic_name,
                            description=f"Tema de {subject_name}: {topic_name}",
                            difficulty=1,
                            order=topic_names.index(topic_name) + 1
                        )
                        db.add(topic)
                        logger.info(f"Created topic: {topic_name} for {subject_name}")
        
        db.commit()
        
        # 3. Import questions from Excel
        logger.info("Importing questions from Excel...")
        excel_path = "ICFES2.xlsx"
        
        if os.path.exists(excel_path):
            try:
                # Clear existing questions
                db.query(Question).delete()
                db.commit()
                logger.info("Cleared existing questions")
                
                # Import new questions
                importer = ICFESExcelImporter(db)
                result = importer.import_excel(excel_path, validate_only=False)
                logger.info(f"Imported {result['imported_questions']} questions")
                
                if result.get('errors'):
                    logger.warning(f"Import errors: {result['errors'][:5]}")
            except Exception as e:
                logger.error(f"Failed to import from Excel: {e}")
                # Create sample questions if Excel import fails
                create_sample_questions(db)
        else:
            logger.warning(f"Excel file not found: {excel_path}")
            # Create sample questions
            create_sample_questions(db)
        
        # 4. Verify questions exist
        question_count = db.query(Question).count()
        logger.info(f"Total questions in database: {question_count}")
        
        # 5. Show sample questions
        sample_questions = db.query(Question).limit(3).all()
        for q in sample_questions:
            logger.info(f"Sample question: {q.pregunta_texto[:50] if q.pregunta_texto else q.question_text[:50]}...")
        
        logger.info("Database fix completed successfully!")
        
    except Exception as e:
        logger.error(f"Database fix failed: {e}")
        import traceback
        traceback.print_exc()

def create_sample_questions(db):
    """Create sample questions if Excel import fails"""
    logger.info("Creating sample questions...")
    
    # Get subjects
    math_subject = db.query(Subject).filter(Subject.name == "Matemáticas").first()
    lang_subject = db.query(Subject).filter(Subject.name == "Lenguaje").first()
    science_subject = db.query(Subject).filter(Subject.name == "Ciencias Naturales").first()
    
    if not math_subject:
        logger.error("No subjects found!")
        return
    
    # Get topics
    algebra_topic = db.query(Topic).filter(
        Topic.name == "Álgebra Básica",
        Topic.subject_id == math_subject.id
    ).first()
    
    if not algebra_topic:
        # Create a default topic
        algebra_topic = Topic(
            id=uuid.uuid4(),
            subject_id=math_subject.id,
            name="Álgebra Básica",
            description="Conceptos básicos de álgebra",
            difficulty=1,
            order=1
        )
        db.add(algebra_topic)
        db.commit()
    
    # Sample math questions
    math_questions = [
        {
            "pregunta_texto": "¿Cuál es el resultado de 2x + 3 = 11?",
            "opcion_a_texto": "x = 3",
            "opcion_b_texto": "x = 4", 
            "opcion_c_texto": "x = 5",
            "opcion_d_texto": "x = 6",
            "respuesta_correcta": "B",
            "difficulty": 1
        },
        {
            "pregunta_texto": "¿Cuál es el área de un triángulo con base 6cm y altura 8cm?",
            "opcion_a_texto": "24 cm²",
            "opcion_b_texto": "48 cm²",
            "opcion_c_texto": "14 cm²",
            "opcion_d_texto": "32 cm²",
            "respuesta_correcta": "A",
            "difficulty": 1
        },
        {
            "pregunta_texto": "Si f(x) = 2x² + 3x - 1, ¿cuál es f(2)?",
            "opcion_a_texto": "9",
            "opcion_b_texto": "11",
            "opcion_c_texto": "13",
            "opcion_d_texto": "15",
            "respuesta_correcta": "C",
            "difficulty": 2
        },
        {
            "pregunta_texto": "¿Cuál es la probabilidad de obtener un número par al lanzar un dado?",
            "opcion_a_texto": "1/6",
            "opcion_b_texto": "1/3",
            "opcion_c_texto": "1/2",
            "opcion_d_texto": "2/3",
            "respuesta_correcta": "C",
            "difficulty": 1
        },
        {
            "pregunta_texto": "Resuelve: 3(x - 2) = 2(x + 1)",
            "opcion_a_texto": "x = 8",
            "opcion_b_texto": "x = 6",
            "opcion_c_texto": "x = 4",
            "opcion_d_texto": "x = 2",
            "respuesta_correcta": "A",
            "difficulty": 2
        }
    ]
    
    # Create 45 questions per subject (repeat patterns for demo)
    for i in range(45):
        base_q = math_questions[i % len(math_questions)]
        question = Question(
            id=uuid.uuid4(),
            topic_id=algebra_topic.id,
            subject_id=math_subject.id,
            pregunta_texto=f"{base_q['pregunta_texto']} (Pregunta {i+1})",
            opcion_a_texto=base_q['opcion_a_texto'],
            opcion_b_texto=base_q['opcion_b_texto'],
            opcion_c_texto=base_q['opcion_c_texto'],
            opcion_d_texto=base_q['opcion_d_texto'],
            respuesta_correcta=base_q['respuesta_correcta'],
            question_text=base_q['pregunta_texto'],
            question_type="multiple_choice",
            difficulty=base_q['difficulty'],
            options=json.dumps({
                "A": base_q['opcion_a_texto'],
                "B": base_q['opcion_b_texto'],
                "C": base_q['opcion_c_texto'],
                "D": base_q['opcion_d_texto']
            }),
            correct_answer=base_q['respuesta_correcta'],
            explanation=f"La respuesta correcta es {base_q['respuesta_correcta']}",
            hint="Piensa en las propiedades matemáticas básicas"
        )
        db.add(question)
    
    db.commit()
    logger.info(f"Created {45} sample math questions")

if __name__ == "__main__":
    fix_database()