#!/usr/bin/env python3
"""
Generate FIXED SQL INSERT statements from ICFES Excel data
Uses hardcoded subject IDs and proper constraint handling
"""

import pandas as pd
import uuid
import json
import unicodedata
import logging

# Setup logging  
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def escape_sql_string(s):
    """Escape SQL string by replacing single quotes with double single quotes"""
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def generate_sql_from_excel(excel_path: str, output_path: str):
    """Generate SQL INSERT statements from Excel file"""
    
    logger.info(f"Reading Excel file: {excel_path}")
    
    # Read Excel with proper encoding
    df = pd.read_excel(excel_path)
    logger.info(f"Found {len(df)} rows in Excel file")
    
    # Normalize column names
    normalized_columns = {col: normalize_header(col) for col in df.columns}
    df.rename(columns=normalized_columns, inplace=True)
    
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
    
    # Fixed subject ID mapping (from database query results)
    subject_id_mapping = {
        'ciencias_naturales': '550e8400-e29b-41d4-a716-446655440003',  # Ciencias Naturales
        'ciencias_sociales': '550e8400-e29b-41d4-a716-446655440004',   # Ciencias Sociales
        'lectura_critica': '550e8400-e29b-41d4-a716-446655440002',     # Lenguaje (mapped)
        'matematicas': '550e8400-e29b-41d4-a716-446655440001',         # Matemáticas
        'ingles': '550e8400-e29b-41d4-a716-446655440005'               # Inglés
    }
    
    # Start building SQL
    sql_statements = []
    
    # Add header comment
    sql_statements.append("-- ICFES Questions Import SQL (Fixed Version)")
    sql_statements.append("-- Generated from Excel file with proper Spanish character encoding")
    sql_statements.append("-- Using hardcoded subject IDs from database")
    sql_statements.append("")
    
    # Clear existing questions
    sql_statements.append("-- Clear existing questions")
    sql_statements.append("DELETE FROM questions;")
    sql_statements.append("")
    
    # Process each row
    imported_count = 0
    errors = []
    created_topics = set()  # Track created topics to avoid duplicates
    
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
            
            # Map to subject ID
            area_norm = normalize_header(area_evaluada)
            subject_id = subject_id_mapping.get(area_norm)
            
            if not subject_id:
                errors.append(f"Row {index + 2}: Subject '{area_evaluada}' (normalized: '{area_norm}') not mapped")
                continue
            
            # Get topic (using tema_especifico or create generic one)
            tema_especifico = str(row.get('tema_especifico', 'General')).strip()
            if not tema_especifico or tema_especifico == 'nan':
                tema_especifico = 'General'
            
            # Extract options
            opcion_a = str(row.get('opcion_a', '')).strip()
            opcion_b = str(row.get('opcion_b', '')).strip()
            opcion_c = str(row.get('opcion_c', '')).strip()
            opcion_d = str(row.get('opcion_d', '')).strip()
            
            if not all([opcion_a, opcion_b, opcion_c, opcion_d]) or any(opt in ['nan', ''] for opt in [opcion_a, opcion_b, opcion_c, opcion_d]):
                errors.append(f"Row {index + 2}: Missing or invalid options")
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
            if explanation == 'nan':
                explanation = ''
            hint = str(row.get('pista_1', '')).strip()
            if hint == 'nan':
                hint = ''
            
            # Build power stats
            poder_stats = {
                "discrimination_index": 0.5,
                "success_rate": 0.6,
                "estimated_time": 60,  # Default to 60 seconds
                "xp_reward": 10,       # Default XP
                "original_id": str(row.get('id_pregunta', '')),
                "bank_origin": 'ICFES',
            }
            
            # Build tags
            tags = []
            competencia = str(row.get('competencia', '')).strip()
            if competencia and competencia != 'nan':
                tags.append(competencia)
            proceso = str(row.get('proceso_cognitivo', '')).strip()
            if proceso and proceso != 'nan':
                tags.append(proceso)
            
            # Generate UUIDs
            question_id = str(uuid.uuid4())
            topic_id = str(uuid.uuid4())
            
            # Create topic key to avoid duplicates
            topic_key = f"{subject_id}:{tema_especifico}"
            
            # Create topic INSERT only if not already created
            if topic_key not in created_topics:
                topic_insert = f"""
-- Create topic: {tema_especifico} for subject {area_evaluada}
INSERT INTO topics (id, subject_id, name, description, difficulty_level)
VALUES ('{topic_id}', '{subject_id}', {escape_sql_string(tema_especifico)}, {escape_sql_string(f'Tema: {tema_especifico}')}, 1);
"""
                sql_statements.append(topic_insert.strip())
                created_topics.add(topic_key)
                topic_id_to_use = topic_id
            else:
                # Find existing topic ID (we'll need to query it)
                topic_id_to_use = f"(SELECT id FROM topics WHERE name = {escape_sql_string(tema_especifico)} AND subject_id = '{subject_id}' LIMIT 1)"
            
            # Create question INSERT
            question_insert = f"""
-- Question {imported_count + 1}: {area_evaluada} - {tema_especifico}
INSERT INTO questions (
    id, topic_id, subject_id, question_text, question_type,
    difficulty, correct_answer, options, explanation, hint,
    tags, power_stats,
    pregunta_texto,
    opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
    respuesta_correcta
) VALUES (
    '{question_id}',
    {topic_id_to_use if isinstance(topic_id_to_use, str) and topic_id_to_use.startswith('(') else f"'{topic_id_to_use}'"},
    '{subject_id}',
    {escape_sql_string(pregunta)},
    'multiple_choice',
    {difficulty},
    '{respuesta_correcta}',
    {escape_sql_string(json.dumps(options))},
    {escape_sql_string(explanation) if explanation else 'NULL'},
    {escape_sql_string(hint) if hint else 'NULL'},
    {escape_sql_string(json.dumps(tags))},
    {escape_sql_string(json.dumps(poder_stats))},
    {escape_sql_string(pregunta)},
    {escape_sql_string(opcion_a)},
    {escape_sql_string(opcion_b)},
    {escape_sql_string(opcion_c)},
    {escape_sql_string(opcion_d)},
    '{respuesta_correcta.lower()}'
);
"""
            
            sql_statements.append(question_insert.strip())
            sql_statements.append("")
            
            imported_count += 1
            
            if imported_count % 50 == 0:
                logger.info(f"Processed {imported_count} questions...")
        
        except Exception as e:
            errors.append(f"Row {index + 2}: Error processing - {str(e)}")
            continue
    
    # Add final comments
    sql_statements.append(f"-- Import completed: {imported_count} questions processed")
    sql_statements.append(f"-- Topics created: {len(created_topics)}")
    sql_statements.append(f"-- Errors encountered: {len(errors)}")
    
    # Write SQL file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))
    
    logger.info(f"SQL file generated: {output_path}")
    logger.info(f"Questions processed: {imported_count}")
    logger.info(f"Topics created: {len(created_topics)}")
    logger.info(f"Errors: {len(errors)}")
    
    if errors and len(errors) <= 10:
        logger.info("Errors:")
        for error in errors:
            logger.info(f"  - {error}")
    elif errors:
        logger.info(f"First 10 errors:")
        for error in errors[:10]:
            logger.info(f"  - {error}")
        logger.info(f"  ... and {len(errors) - 10} more errors")
    
    return imported_count, errors

if __name__ == "__main__":
    excel_path = "database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
    output_path = "icfes_import_fixed.sql"
    
    generate_sql_from_excel(excel_path, output_path)