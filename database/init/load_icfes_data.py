#!/usr/bin/env python3
"""
Script to load ICFES data from Excel file into PostgreSQL database
This script is executed automatically by Docker during initialization
"""

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import uuid
import os
import sys
from datetime import datetime

# Database configuration for Docker environment
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'icfes_postgres'),  # Use Docker service name
    'port': int(os.getenv('DB_PORT', '5432')),       # Internal Docker port
    'database': os.getenv('DB_NAME', 'icfes_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'postgres123')
}

# Excel file path (mounted in Docker container)
EXCEL_PATH = '/data/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx'

def get_connection():
    """Get database connection"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def map_subject_names(area_evaluada):
    """Map area names to subject UUIDs"""
    subject_map = {
        'Ciencias Naturales': '550e8400-e29b-41d4-a716-446655440003',
        'Ciencias Sociales': '550e8400-e29b-41d4-a716-446655440004',
        'Ciencias Sociales y Ciudadanas': '550e8400-e29b-41d4-a716-446655440004',
        'Matemáticas': '550e8400-e29b-41d4-a716-446655440001',
        'Lectura Crítica': '550e8400-e29b-41d4-a716-446655440002',
        'Lenguaje': '550e8400-e29b-41d4-a716-446655440002',
        'Inglés': '550e8400-e29b-41d4-a716-446655440005'
    }
    
    for key in subject_map:
        if key.lower() in str(area_evaluada).lower():
            return subject_map[key]
    
    return '550e8400-e29b-41d4-a716-446655440001'  # Default to Matemáticas

def load_excel_data():
    """Load data from Excel file"""
    print(f"Loading Excel file: {EXCEL_PATH}")
    
    if not os.path.exists(EXCEL_PATH):
        print(f"Warning: Excel file not found at {EXCEL_PATH}")
        # Try alternative path
        alt_path = '/app/database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx'
        if os.path.exists(alt_path):
            print(f"Using alternative path: {alt_path}")
            df = pd.read_excel(alt_path)
        else:
            print("Excel file not found. Skipping data import.")
            return None
    else:
        df = pd.read_excel(EXCEL_PATH)
    
    print(f"Loaded {len(df)} questions from Excel")
    
    # Clean column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    return df

def insert_questions(conn, df):
    """Insert questions into database"""
    cur = conn.cursor()
    
    print("Inserting questions into database...")
    
    # Clear existing questions (optional - comment out if you want to append)
    cur.execute("DELETE FROM questions WHERE 1=1")
    print("Cleared existing questions")
    
    inserted = 0
    errors = 0
    
    for index, row in df.iterrows():
        try:
            question_id = str(uuid.uuid4())
            subject_id = map_subject_names(row.get('área_evaluada', ''))
            
            # Build question data with all 81 fields
            question_data = {
                'id': question_id,
                'subject_id': subject_id,
                'id_pregunta_original': str(row.get('id_pregunta', index + 1)),
                'area_evaluada': str(row.get('área_evaluada', '')),
                'pregunta_texto': str(row.get('pregunta', '')),
                'question_text': str(row.get('pregunta', '')),
                'opcion_a_texto': str(row.get('opcion_a', '')),
                'opcion_b_texto': str(row.get('opcion_b', '')),
                'opcion_c_texto': str(row.get('opcion_c', '')),
                'opcion_d_texto': str(row.get('opcion_d', '')),
                'option_a': str(row.get('opcion_a', '')),
                'option_b': str(row.get('opcion_b', '')),
                'option_c': str(row.get('opcion_c', '')),
                'option_d': str(row.get('opcion_d', '')),
                'respuesta_correcta': str(row.get('respuesta_correcta', 'a')).lower()[:1],
                'correct_answer': str(row.get('respuesta_correcta', 'a')).lower()[:1],
                'competencia': str(row.get('competencia', '')),
                'componente': str(row.get('componente', '')),
                'proceso_cognitivo': str(row.get('proceso_cognitivo', '')),
                'tipo_conocimiento': str(row.get('tipo_conocimiento', '')),
                'nivel_desempeno_esperado': str(row.get('nivel_desempeño_esperado', '')),
                'tema_especifico': str(row.get('tema_específico', '')),
                'topic': str(row.get('tema_específico', 'General')),
                'grado_escolar': str(row.get('grado_escolar', '')),
                'periodo_aplicacion': str(row.get('periodo_aplicación', '')),
                'afirmacion': str(row.get('afirmación', '')),
                'evidencia': str(row.get('evidencia', '')),
                'explicacion_respuesta': str(row.get('explicación_respuesta', '')),
                'pista_1': str(row.get('pista_1', '')),
                'pista_2': str(row.get('pista_2', '')),
                'pista_3': str(row.get('pista_3', '')),
                'error_comun': str(row.get('error_común', '')),
                'difficulty': 5,  # Default difficulty
                'options': json.dumps({
                    'a': str(row.get('opcion_a', '')),
                    'b': str(row.get('opcion_b', '')),
                    'c': str(row.get('opcion_c', '')),
                    'd': str(row.get('opcion_d', ''))
                })
            }
            
            # Add numeric fields
            numeric_fields = {
                'parametro_irt_a': 'parámetro_irt_a',
                'parametro_irt_b': 'parámetro_irt_b',
                'parametro_irt_c': 'parámetro_irt_c',
                'indice_discriminacion': 'índice_discriminación',
                'tiempo_estimado': 'tiempo_estimado',
                'puntos_xp': 'puntos_xp'
            }
            
            for db_field, excel_field in numeric_fields.items():
                if pd.notna(row.get(excel_field)):
                    try:
                        if db_field in ['parametro_irt_a', 'parametro_irt_b', 'parametro_irt_c', 'indice_discriminacion']:
                            question_data[db_field] = float(row.get(excel_field))
                        else:
                            question_data[db_field] = int(row.get(excel_field))
                    except:
                        pass
            
            # Add difficulty level
            if pd.notna(row.get('nivel_dificultad')):
                try:
                    question_data['difficulty'] = int(row.get('nivel_dificultad'))
                except:
                    question_data['difficulty'] = 5
            
            # Add all additional text fields
            text_fields = [
                'pregunta_con_contexto', 'pregunta_libro', 'texto_contexto_completo',
                'ruta_absoluta_archivo', 'nombre_del_archivo', 'subtema',
                'estrategia_discursiva', 'tipo_razonamiento', 'complejidad_cognitiva',
                'contexto_aplicacion', 'tipo_texto', 'genero_textual', 'funcion_comunicativa',
                'pensamiento_matematico', 'disciplina_predominante', 'concepto_cientifico',
                'proceso_cientifico', 'nivel_representacion', 'periodo_historico',
                'ambito_analisis', 'escala_espacial', 'concepto_social', 'tipo_fuente',
                'habilidad_comunicativa', 'tipo_problema', 'estrategia_solucion',
                'tipo_representacion', 'uso_herramientas', 'nivel_abstraccion'
            ]
            
            for field in text_fields:
                if pd.notna(row.get(field)):
                    question_data[field] = str(row.get(field))
            
            # Build and execute INSERT query
            columns = list(question_data.keys())
            values = list(question_data.values())
            placeholders = ['%s'] * len(values)
            
            insert_query = f"""
                INSERT INTO questions ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT (id) DO NOTHING
            """
            
            cur.execute(insert_query, values)
            inserted += 1
            
            if inserted % 50 == 0:
                print(f"  Inserted {inserted} questions...")
                
        except Exception as e:
            errors += 1
            if errors <= 5:
                print(f"  Error in row {index}: {str(e)[:100]}")
    
    conn.commit()
    
    print(f"\nImport completed:")
    print(f"  - Questions inserted: {inserted}")
    print(f"  - Errors: {errors}")
    
    # Verify results
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    
    cur.execute("""
        SELECT s.name, COUNT(q.id) 
        FROM subjects s 
        LEFT JOIN questions q ON s.id = q.subject_id 
        GROUP BY s.id, s.name 
        ORDER BY COUNT(q.id) DESC
    """)
    
    print(f"\nDatabase summary:")
    print(f"  Total questions: {total}")
    for subject, count in cur.fetchall():
        print(f"  - {subject}: {count} questions")
    
    return inserted

def main():
    """Main function"""
    print("=" * 60)
    print("ICFES DATA IMPORT - DOCKER INITIALIZATION")
    print("=" * 60)
    
    # Wait for database to be ready
    import time
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        conn = get_connection()
        if conn:
            print("Database connection successful!")
            break
        print(f"Waiting for database... ({retry_count + 1}/{max_retries})")
        time.sleep(2)
        retry_count += 1
    
    if not conn:
        print("Could not connect to database after 60 seconds")
        sys.exit(1)
    
    try:
        # Load Excel data
        df = load_excel_data()
        if df is None:
            print("No data to import")
            return
        
        # Insert questions
        inserted = insert_questions(conn, df)
        
        print(f"\nSuccessfully imported {inserted} questions with 81 ICFES fields")
        
    except Exception as e:
        print(f"Error during import: {e}")
        conn.rollback()
    
    finally:
        conn.close()
        print("Database connection closed")

if __name__ == "__main__":
    main()