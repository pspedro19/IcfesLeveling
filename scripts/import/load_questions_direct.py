#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct load of ICFES questions using Docker exec
Transforms absolute paths to relative paths for frontend rendering
"""
import pandas as pd
import json
import uuid
from datetime import datetime
import subprocess
import os

# Excel file path
EXCEL_PATH = r"database\allquestions\ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"

def transform_image_path(path):
    """Transform absolute path to relative path for frontend"""
    if pd.isna(path) or not path:
        return None
    
    path = str(path).strip()
    
    # Remove absolute path prefix and convert to relative
    if 'C:\\Users\\' in path or 'C:/Users/' in path:
        # Extract just the filename and subject folder
        parts = path.replace('\\', '/').split('/')
        
        # Find where the subject folder starts
        for i, part in enumerate(parts):
            if part in ['MATEMATICAS', 'FISICA', 'QUIMICA', 'BIOLOGIA', 'ESPANOL', 'SOCIALES', 'LECTURA']:
                # Return path from subject folder onwards
                relative_path = '/'.join(parts[i:])
                return f"/assets/questions/{relative_path}"
    
    # If already relative
    if not path.startswith('/'):
        return f"/assets/questions/{path}"
    
    return path

def clean_text(text):
    """Clean text and escape quotes for SQL"""
    if pd.isna(text):
        return ''
    text = str(text).strip()
    # Escape single quotes for SQL
    text = text.replace("'", "''")
    return text

def map_subject(area):
    """Map area to subject ID"""
    mapping = {
        'Matemáticas': '550e8400-e29b-41d4-a716-446655440001',
        'Matemáticas': '550e8400-e29b-41d4-a716-446655440001',  # With accent
        'Lectura Crítica': '550e8400-e29b-41d4-a716-446655440002',
        'Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
        'Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
        'Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
        'Inglés': '550e8400-e29b-41d4-a716-446655440005'
    }
    
    # Try exact match first
    if area in mapping:
        return mapping[area]
    
    # Try partial match
    for key, value in mapping.items():
        if key.lower() in area.lower() or area.lower() in key.lower():
            return value
    
    # Default to Ciencias Naturales for unmapped
    return '550e8400-e29b-41d4-a716-446655440003'

def generate_sql():
    """Generate SQL INSERT statements"""
    print("Reading Excel file...")
    df = pd.read_excel(EXCEL_PATH)
    print(f"Found {len(df)} rows")
    
    sql_statements = []
    
    # Clear existing questions
    sql_statements.append("DELETE FROM questions;")
    
    processed = 0
    skipped = 0
    
    for idx, row in df.iterrows():
        try:
            # Get area
            area = clean_text(row.get('Área_Evaluada', row.get('Area_Evaluada', '')))
            if not area:
                skipped += 1
                continue
            
            subject_id = map_subject(area)
            
            # Get question text
            pregunta = clean_text(row.get('Pregunta'))
            if not pregunta:
                skipped += 1
                continue
            
            # Get options
            opcion_a = clean_text(row.get('Opcion_A'))
            opcion_b = clean_text(row.get('Opcion_B'))
            opcion_c = clean_text(row.get('Opcion_C'))
            opcion_d = clean_text(row.get('Opcion_D'))
            
            # Get correct answer
            respuesta = clean_text(row.get('Respuesta_Correcta'))
            if respuesta not in ['A', 'B', 'C', 'D']:
                skipped += 1
                continue
            
            # Transform image paths to relative
            pregunta_img = transform_image_path(row.get('Imagen_Pregunta_URL'))
            opcion_a_img = transform_image_path(row.get('Imagen_Opcion_A_URL'))
            opcion_b_img = transform_image_path(row.get('Imagen_Opcion_B_URL'))
            opcion_c_img = transform_image_path(row.get('Imagen_Opcion_C_URL'))
            opcion_d_img = transform_image_path(row.get('Imagen_Opcion_D_URL'))
            
            # IRT parameters
            param_a = float(row.get('Parámetro_IRT_A', row.get('Parametro_IRT_A', 1.0))) if pd.notna(row.get('Parámetro_IRT_A', row.get('Parametro_IRT_A'))) else 1.0
            param_b = float(row.get('Parámetro_IRT_B', row.get('Parametro_IRT_B', 0.0))) if pd.notna(row.get('Parámetro_IRT_B', row.get('Parametro_IRT_B'))) else 0.0
            param_c = float(row.get('Parámetro_IRT_C', row.get('Parametro_IRT_C', 0.25))) if pd.notna(row.get('Parámetro_IRT_C', row.get('Parametro_IRT_C'))) else 0.25
            
            # Difficulty
            nivel = row.get('Nivel_Dificultad', 'medio')
            if pd.isna(nivel):
                difficulty = 5
            elif 'bajo' in str(nivel).lower() or 'fácil' in str(nivel).lower():
                difficulty = 3
            elif 'alto' in str(nivel).lower() or 'difícil' in str(nivel).lower():
                difficulty = 8
            else:
                difficulty = 5
            
            # Other fields
            competencia = clean_text(row.get('Competencia', ''))
            componente = clean_text(row.get('Componente', ''))
            proceso_cognitivo = clean_text(row.get('Proceso_Cognitivo', ''))
            tipo_conocimiento = clean_text(row.get('Tipo_Conocimiento', ''))
            
            # Build options JSON
            options_json = json.dumps({
                "A": opcion_a or "",
                "B": opcion_b or "",
                "C": opcion_c or "",
                "D": opcion_d or ""
            }).replace("'", "''")
            
            # Build options_images JSON if any images
            if any([opcion_a_img, opcion_b_img, opcion_c_img, opcion_d_img]):
                options_images_json = json.dumps({
                    "A": opcion_a_img or None,
                    "B": opcion_b_img or None,
                    "C": opcion_c_img or None,
                    "D": opcion_d_img or None
                }).replace("'", "''")
            else:
                options_images_json = 'NULL'
            
            # Generate INSERT statement
            question_id = str(uuid.uuid4())
            
            sql = f"""
INSERT INTO questions (
    id, subject_id, question_text, correct_answer, options,
    difficulty, pregunta_texto, pregunta_imagen, respuesta_correcta,
    opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
    opcion_a_imagen, opcion_b_imagen, opcion_c_imagen, opcion_d_imagen,
    competencia, componente, proceso_cognitivo, tipo_conocimiento,
    parametro_irt_a, parametro_irt_b, parametro_irt_c,
    image_url, created_at
) VALUES (
    '{question_id}', '{subject_id}', '{pregunta}', '{respuesta}', '{options_json}',
    {difficulty}, '{pregunta}', {f"'{pregunta_img}'" if pregunta_img else 'NULL'}, '{respuesta}',
    '{opcion_a}', '{opcion_b}', '{opcion_c}', '{opcion_d}',
    {f"'{opcion_a_img}'" if opcion_a_img else 'NULL'},
    {f"'{opcion_b_img}'" if opcion_b_img else 'NULL'},
    {f"'{opcion_c_img}'" if opcion_c_img else 'NULL'},
    {f"'{opcion_d_img}'" if opcion_d_img else 'NULL'},
    '{competencia}', '{componente}', '{proceso_cognitivo}', '{tipo_conocimiento}',
    {param_a}, {param_b}, {param_c},
    {f"'{pregunta_img}'" if pregunta_img else 'NULL'}, NOW()
);"""
            
            sql_statements.append(sql)
            processed += 1
            
            if processed % 50 == 0:
                print(f"Processed {processed} questions...")
                
        except Exception as e:
            print(f"Error in row {idx}: {e}")
            skipped += 1
    
    print(f"\nProcessed: {processed}")
    print(f"Skipped: {skipped}")
    
    return sql_statements

def main():
    print("="*60)
    print("ICFES QUESTIONS DIRECT LOAD")
    print("="*60)
    
    # Generate SQL
    sql_statements = generate_sql()
    
    # Save to file
    sql_file = "load_questions.sql"
    with open(sql_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_statements))
    
    print(f"\nSQL file created: {sql_file}")
    print(f"Total statements: {len(sql_statements)}")
    
    # Execute via Docker
    print("\nLoading into database...")
    try:
        # Copy SQL file to container
        subprocess.run(['docker', 'cp', sql_file, 'icfes_postgres:/tmp/load_questions.sql'], check=True)
        
        # Execute SQL
        result = subprocess.run([
            'docker', 'exec', 'icfes_postgres',
            'psql', '-U', 'gameplay', '-d', 'gameplay_db',
            '-f', '/tmp/load_questions.sql'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("[OK] Questions loaded successfully!")
            
            # Check count
            count_result = subprocess.run([
                'docker', 'exec', 'icfes_postgres',
                'psql', '-U', 'gameplay', '-d', 'gameplay_db',
                '-c', 'SELECT COUNT(*) FROM questions;'
            ], capture_output=True, text=True)
            
            print(count_result.stdout)
        else:
            print(f"[ERROR] Failed to load: {result.stderr}")
            
    except Exception as e:
        print(f"[ERROR] {e}")
    
    # Cleanup
    if os.path.exists(sql_file):
        os.remove(sql_file)

if __name__ == "__main__":
    main()