#!/usr/bin/env python3
"""
Generate SQL INSERT statements from ICFES Excel data
This bypasses database connection issues by generating SQL to execute via docker exec
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
    
    # Subject mapping
    subject_mapping = {
        'ciencias_naturales': 'Ciencias Naturales',
        'ciencias_sociales': 'Ciencias Sociales', 
        'lectura_critica': 'Lectura Crítica',
        'matematicas': 'Matemáticas',
        'ingles': 'Inglés'
    }
    
    # Start building SQL
    sql_statements = []
    
    # Add header comment
    sql_statements.append("-- ICFES Questions Import SQL")
    sql_statements.append("-- Generated from Excel file with proper Spanish character encoding")
    sql_statements.append("")
    
    # Clear existing questions
    sql_statements.append("-- Clear existing questions")
    sql_statements.append("DELETE FROM questions;")
    sql_statements.append("")
    
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
            
            # Map to subject ID (hardcoded based on typical subject IDs)
            subject_id = None
            area_norm = normalize_header(area_evaluada)
            
            # Subject ID mapping (these are typical UUIDs, we'll need to look them up)
            subject_id_mapping = {
                'ciencias_naturales': '(SELECT id FROM subjects WHERE name = \'Ciencias Naturales\')',
                'ciencias_sociales': '(SELECT id FROM subjects WHERE name = \'Ciencias Sociales\')',
                'lectura_critica': '(SELECT id FROM subjects WHERE name = \'Lenguaje\')',  # Map to Lenguaje
                'matematicas': '(SELECT id FROM subjects WHERE name = \'Matemáticas\')',
                'ingles': '(SELECT id FROM subjects WHERE name = \'Inglés\')'
            }
            
            if area_norm in subject_id_mapping:
                subject_id = subject_id_mapping[area_norm]
            else:
                # Try direct mapping
                subject_id = f"(SELECT id FROM subjects WHERE name = {escape_sql_string(area_evaluada)})"
            
            if not subject_id:
                errors.append(f"Row {index + 2}: Subject '{area_evaluada}' not found")
                continue
            
            # Get topic (using tema_especifico or create generic one)
            tema_especifico = str(row.get('tema_especifico', 'General')).strip()
            
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
            
            # Generate UUIDs
            question_id = str(uuid.uuid4())
            topic_id = str(uuid.uuid4())
            
            # Create topic INSERT (with conflict handling)
            topic_insert = f"""
INSERT INTO topics (id, subject_id, name, description, difficulty_level)
VALUES ('{topic_id}', {subject_id}, {escape_sql_string(tema_especifico)}, {escape_sql_string(f'Tema: {tema_especifico}')}, 1)
ON CONFLICT (name, subject_id) DO NOTHING;
"""
            
            # For the question INSERT, we need to get the topic ID that may already exist
            topic_id_query = f"(SELECT id FROM topics WHERE name = {escape_sql_string(tema_especifico)} AND subject_id = {subject_id} LIMIT 1)"
            
            # Create question INSERT
            question_insert = f"""
INSERT INTO questions (
    id, topic_id, subject_id, question_text, question_type,
    difficulty, correct_answer, options, explanation, hint,
    tags, power_stats,
    pregunta_texto, pregunta_imagen,
    opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
    respuesta_correcta
) VALUES (
    '{question_id}',
    {topic_id_query},
    {subject_id},
    {escape_sql_string(pregunta)},
    'multiple_choice',
    {difficulty},
    '{respuesta_correcta}',
    {escape_sql_string(json.dumps(options))},
    {escape_sql_string(explanation) if explanation else 'NULL'},
    {escape_sql_string(hint) if hint else 'NULL'},
    {escape_sql_string(json.dumps(tags))},
    {escape_sql_string(json.dumps(power_stats))},
    {escape_sql_string(pregunta)},
    NULL,
    {escape_sql_string(opcion_a)},
    {escape_sql_string(opcion_b)},
    {escape_sql_string(opcion_c)},
    {escape_sql_string(opcion_d)},
    '{respuesta_correcta.lower()}'
);
"""
            
            sql_statements.append(f"-- Question {imported_count + 1}: {area_evaluada}")
            sql_statements.append(topic_insert.strip())
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
    sql_statements.append(f"-- Errors encountered: {len(errors)}")
    
    # Write SQL file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))
    
    logger.info(f"SQL file generated: {output_path}")
    logger.info(f"Questions processed: {imported_count}")
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
    output_path = "icfes_import.sql"
    
    generate_sql_from_excel(excel_path, output_path)