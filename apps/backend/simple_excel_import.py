#!/usr/bin/env python3
"""
Simplified ICFES Excel Import Script
Directly imports questions from Excel to database without complex model dependencies
"""

import pandas as pd
import uuid
import json
import logging
from typing import Dict, List, Optional
from sqlalchemy import create_engine, text
import os
import unicodedata

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"

def normalize_header(s: str) -> str:
    """Normalize column headers to handle Spanish characters and spaces"""
    s = str(s or "").strip()
    # Remove accents
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    # Unify separators and lowercase
    s = s.replace(" ", "_").replace("-", "_")
    s = s.replace("__", "_")
    return s.lower()

def map_difficulty(nivel_dificultad) -> int:
    """Map difficulty level to 1-10 scale"""
    if pd.isna(nivel_dificultad):
        return 5
    
    nivel = str(nivel_dificultad).lower().strip()
    
    difficulty_mapping = {
        'bajo': 1, 'baja': 1, 'facil': 2, 'fácil': 2,
        'basico': 3, 'básico': 3, 'medio': 5, 'intermedio': 5,
        'alto': 8, 'alta': 8, 'dificil': 9, 'difícil': 9,
        'muy alto': 10, 'muy alta': 10,
    }
    
    for key, value in difficulty_mapping.items():
        if key in nivel:
            return value
    
    # If numeric, convert
    try:
        num_difficulty = int(nivel)
        if 1 <= num_difficulty <= 10:
            return num_difficulty
    except ValueError:
        pass
    
    return 5

def normalize_image_path(value: str) -> str:
    """Normalize image paths to /mathimg/<filename>"""
    try:
        s = (value or '').strip()
        if not s:
            return s
        if s.startswith('/mathimg/'):
            return s
        import os
        base = os.path.basename(s)
        if s.startswith('http://') or s.startswith('https://'):
            return s
        return '/mathimg/' + base
    except Exception:
        return value or ''

def import_excel_questions(excel_path: str, clear_existing: bool = False):
    """Import questions from Excel file"""
    
    # Create database engine
    engine = create_engine(DATABASE_URL)
    
    try:
        logger.info(f"Reading Excel file: {excel_path}")
        
        # Read Excel with proper encoding
        df = pd.read_excel(excel_path)
        logger.info(f"Found {len(df)} rows in Excel file")
        
        # Normalize column names
        original_columns = list(df.columns)
        normalized_columns = {col: normalize_header(col) for col in df.columns}
        df.rename(columns=normalized_columns, inplace=True)
        
        logger.info(f"Original columns: {original_columns[:5]}...")  # Show first 5
        logger.info(f"Normalized columns: {list(df.columns)[:5]}...")  # Show first 5
        
        # Check column distribution
        area_col = None
        for col in df.columns:
            if 'area_evaluada' in col or 'rea_evaluada' in col:
                area_col = col
                break
        
        if area_col:
            logger.info("Subject distribution in Excel:")
            distribution = df.groupby(area_col).size()
            for subject, count in distribution.items():
                percentage = (count / len(df)) * 100
                logger.info(f"  {subject}: {count} questions ({percentage:.1f}%)")
        
        with engine.connect() as conn:
            # Clear existing questions if requested
            if clear_existing:
                logger.info("Clearing existing questions...")
                conn.execute(text("DELETE FROM questions"))
                conn.commit()
                logger.info("Existing questions cleared")
            
            # Get existing subjects
            subjects_result = conn.execute(text("SELECT id, name FROM subjects"))
            subjects = {row[1]: str(row[0]) for row in subjects_result.fetchall()}
            logger.info(f"Available subjects: {list(subjects.keys())}")
            
            # Subject mapping
            subject_mapping = {
                'ciencias_naturales': 'Ciencias Naturales',
                'ciencias_sociales': 'Ciencias Sociales', 
                'lectura_critica': 'Lectura Crítica',
                'matematicas': 'Matemáticas',
                'ingles': 'Inglés'
            }
            
            # Process each row
            imported_count = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Extract basic question data
                    pregunta = str(row.get('pregunta', '')).strip()
                    if not pregunta:
                        errors.append(f"Row {index + 2}: Empty question")
                        continue
                    
                    # Get area evaluada
                    area_evaluada = ''
                    if area_col:
                        area_evaluada = str(row.get(area_col, '')).strip()
                    
                    # Map to subject
                    subject_id = None
                    area_norm = normalize_header(area_evaluada)
                    
                    if area_norm in subject_mapping:
                        subject_name = subject_mapping[area_norm]
                        subject_id = subjects.get(subject_name)
                    
                    if not subject_id:
                        # Try direct mapping
                        subject_id = subjects.get(area_evaluada)
                    
                    if not subject_id:
                        errors.append(f"Row {index + 2}: Subject '{area_evaluada}' not found in database")
                        continue
                    
                    # Get topic (using tema_especifico or create generic one)
                    tema_especifico = str(row.get('tema_especifico', 'General')).strip()
                    
                    # Check if topic exists
                    topic_result = conn.execute(
                        text("SELECT id FROM topics WHERE name = :name AND subject_id = :subject_id"),
                        {"name": tema_especifico, "subject_id": subject_id}
                    )
                    topic_row = topic_result.fetchone()
                    
                    if topic_row:
                        topic_id = str(topic_row[0])
                    else:
                        # Create new topic
                        topic_id = str(uuid.uuid4())
                        conn.execute(
                            text("""
                                INSERT INTO topics (id, subject_id, name, description, difficulty_level)
                                VALUES (:id, :subject_id, :name, :description, :difficulty_level)
                            """),
                            {
                                "id": topic_id,
                                "subject_id": subject_id,
                                "name": tema_especifico,
                                "description": f"Tema: {tema_especifico}",
                                "difficulty_level": 1
                            }
                        )
                        logger.info(f"Created new topic: {tema_especifico}")
                    
                    # Extract options
                    opcion_a = str(row.get('opcion_a', '')).strip()
                    opcion_b = str(row.get('opcion_b', '')).strip()
                    opcion_c = str(row.get('opcion_c', '')).strip()
                    opcion_d = str(row.get('opcion_d', '')).strip()
                    
                    if not all([opcion_a, opcion_b, opcion_c, opcion_d]):
                        errors.append(f"Row {index + 2}: Missing options")
                        continue
                    
                    # Get correct answer
                    respuesta_correcta = str(row.get('respuesta_correcta', '')).strip().upper()
                    if respuesta_correcta not in ['A', 'B', 'C', 'D']:
                        errors.append(f"Row {index + 2}: Invalid correct answer '{respuesta_correcta}'")
                        continue
                    
                    # Build options JSON
                    options = {
                        'A': opcion_a,
                        'B': opcion_b, 
                        'C': opcion_c,
                        'D': opcion_d
                    }
                    
                    # Extract other fields
                    difficulty = map_difficulty(row.get('nivel_dificultad'))
                    explanation = str(row.get('explicacion_respuesta', '')).strip()
                    hint = str(row.get('pista_1', '')).strip()
                    
                    # Build power stats
                    power_stats = {
                        "discrimination_index": 0.5,
                        "success_rate": 0.6,
                        "estimated_time": int(row.get('tiempo_estimado', 60)) if pd.notna(row.get('tiempo_estimado')) else 60,
                        "xp_reward": int(row.get('puntos_xp', 10)) if pd.notna(row.get('puntos_xp')) else 10,
                        "original_id": str(row.get('id_pregunta', '')),
                        "bank_origin": str(row.get('banco_origen', 'ICFES')),
                    }
                    
                    # Build tags
                    tags = []
                    if pd.notna(row.get('competencia')):
                        tags.append(str(row.get('competencia')).strip())
                    if pd.notna(row.get('proceso_cognitivo')):
                        tags.append(str(row.get('proceso_cognitivo')).strip())
                    
                    # Handle image URLs
                    imagen_pregunta = normalize_image_path(str(row.get('imagen_pregunta_url', '')))
                    
                    # Insert question
                    question_id = str(uuid.uuid4())
                    
                    conn.execute(
                        text("""
                            INSERT INTO questions (
                                id, topic_id, subject_id, question_text, question_type,
                                difficulty, correct_answer, options, explanation, hint,
                                tags, power_stats,
                                pregunta_texto, pregunta_imagen,
                                opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
                                respuesta_correcta
                            ) VALUES (
                                :id, :topic_id, :subject_id, :question_text, :question_type,
                                :difficulty, :correct_answer, :options, :explanation, :hint,
                                :tags, :power_stats,
                                :pregunta_texto, :pregunta_imagen,
                                :opcion_a_texto, :opcion_b_texto, :opcion_c_texto, :opcion_d_texto,
                                :respuesta_correcta
                            )
                        """),
                        {
                            "id": question_id,
                            "topic_id": topic_id,
                            "subject_id": subject_id,
                            "question_text": pregunta,
                            "question_type": "multiple_choice",
                            "difficulty": difficulty,
                            "correct_answer": respuesta_correcta,
                            "options": json.dumps(options),
                            "explanation": explanation or None,
                            "hint": hint or None,
                            "tags": json.dumps(tags),
                            "power_stats": json.dumps(power_stats),
                            "pregunta_texto": pregunta,
                            "pregunta_imagen": imagen_pregunta or None,
                            "opcion_a_texto": opcion_a,
                            "opcion_b_texto": opcion_b,
                            "opcion_c_texto": opcion_c,
                            "opcion_d_texto": opcion_d,
                            "respuesta_correcta": respuesta_correcta.lower()
                        }
                    )
                    
                    imported_count += 1
                    
                    if imported_count % 50 == 0:
                        logger.info(f"Imported {imported_count} questions...")
                        conn.commit()
                
                except Exception as e:
                    errors.append(f"Row {index + 2}: Error processing - {str(e)}")
                    continue
            
            # Final commit
            conn.commit()
            
            # Check final distribution
            logger.info("Checking final distribution in database...")
            result = conn.execute(text("""
                SELECT s.name, COUNT(*) as count 
                FROM questions q 
                JOIN subjects s ON q.subject_id = s.id 
                GROUP BY s.name 
                ORDER BY count DESC
            """))
            
            total = 0
            logger.info("Final question distribution in database:")
            for subject_name, count in result.fetchall():
                total += count
                percentage = (count / max(imported_count, 1)) * 100
                logger.info(f"  {subject_name}: {count} questions ({percentage:.1f}%)")
            
            logger.info(f"Import completed successfully!")
            logger.info(f"Total questions imported: {imported_count}")
            logger.info(f"Total questions in database: {total}")
            logger.info(f"Errors encountered: {len(errors)}")
            
            if errors and len(errors) <= 10:
                logger.info("Errors:")
                for error in errors:
                    logger.info(f"  - {error}")
            elif errors:
                logger.info(f"First 10 errors:")
                for error in errors[:10]:
                    logger.info(f"  - {error}")
                logger.info(f"  ... and {len(errors) - 10} more errors")
                
    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import ICFES questions from Excel')
    parser.add_argument('--file', required=True, help='Path to Excel file')
    parser.add_argument('--clear', action='store_true', help='Clear existing questions')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        logger.error(f"File not found: {args.file}")
        exit(1)
    
    import_excel_questions(args.file, args.clear)