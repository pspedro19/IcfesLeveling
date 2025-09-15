#!/usr/bin/env python3
"""
Script completo para importar todos los datos del Excel ICFES incluyendo imágenes
Este script recreará las preguntas desde el Excel como fuente única de verdad
"""

import os
import sys
import pandas as pd
import psycopg2
import json
import uuid
from pathlib import Path

# Database connection parameters
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5433,
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
        'LENGUAJE': 'Lenguaje', 
        'LECTURA CRITICA': 'Lenguaje',
        'CIENCIAS NATURALES': 'Ciencias Naturales',
        'CIENCIAS SOCIALES': 'Ciencias Sociales',
        'INGLES': 'Inglés'
    }
    return mapping.get(str(area_evaluada).upper(), str(area_evaluada))

def get_subject_id(cursor, subject_name):
    """Get subject ID from database"""
    cursor.execute("SELECT id FROM subjects WHERE name = %s", (subject_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def import_excel_to_database():
    """Import complete Excel data to database"""
    
    # Path to Excel file
    excel_path = "database/allquestions/ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found: {excel_path}")
        return
    
    print(f"📂 Loading Excel file: {excel_path}")
    
    try:
        # Read Excel file
        df = pd.read_excel(excel_path)
        print(f"📊 Loaded {len(df)} rows from Excel")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update existing questions with image URLs instead of clearing
        print("🔄 Updating existing questions with image data...")
        
        imported_count = 0
        questions_with_images = 0
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Skip rows without question text
                if pd.isna(row['Pregunta']) or not str(row['Pregunta']).strip():
                    continue
                
                # Map subject
                area_evaluada = str(row['Área_Evaluada']).strip()
                subject_name = map_subject_name(area_evaluada)
                subject_id = get_subject_id(cursor, subject_name)
                
                if not subject_id:
                    print(f"⚠️ Subject not found for: {area_evaluada} -> {subject_name}")
                    continue
                
                # Generate UUID for question
                question_id = str(uuid.uuid4())
                
                # Extract main question data
                pregunta_texto = str(row['Pregunta']).strip()
                respuesta_correcta = str(row['Respuesta_Correcta']).strip() if pd.notna(row['Respuesta_Correcta']) else 'A'
                
                # Build options JSON
                options = {
                    'A': str(row['Opcion_A']).strip() if pd.notna(row['Opcion_A']) else '',
                    'B': str(row['Opcion_B']).strip() if pd.notna(row['Opcion_B']) else '',
                    'C': str(row['Opcion_C']).strip() if pd.notna(row['Opcion_C']) else '',
                    'D': str(row['Opcion_D']).strip() if pd.notna(row['Opcion_D']) else ''
                }
                
                # Extract difficulty (default to 2 if not available)
                difficulty = 2
                if pd.notna(row['Nivel_Dificultad']):
                    try:
                        difficulty = int(row['Nivel_Dificultad'])
                    except:
                        difficulty = 2
                
                # Extract XP points
                puntos_xp = 10
                if pd.notna(row['Puntos_XP']):
                    try:
                        puntos_xp = int(row['Puntos_XP'])
                    except:
                        puntos_xp = 10
                
                # Extract image URLs (clean paths)
                pregunta_imagen = None
                if pd.notna(row['Imagen_Pregunta_URL']) and str(row['Imagen_Pregunta_URL']).strip():
                    pregunta_imagen = str(row['Imagen_Pregunta_URL']).strip()
                    if pregunta_imagen.startswith('database/allquestions/'):
                        # Convert to web-accessible path
                        pregunta_imagen = pregunta_imagen.replace('database/allquestions/', '/api/images/')
                
                opcion_a_imagen = None
                if pd.notna(row['Imagen_Opcion_A_URL']) and str(row['Imagen_Opcion_A_URL']).strip():
                    opcion_a_imagen = str(row['Imagen_Opcion_A_URL']).strip()
                    if opcion_a_imagen.startswith('database/allquestions/'):
                        opcion_a_imagen = opcion_a_imagen.replace('database/allquestions/', '/api/images/')
                
                opcion_b_imagen = None
                if pd.notna(row['Imagen_Opcion_B_URL']) and str(row['Imagen_Opcion_B_URL']).strip():
                    opcion_b_imagen = str(row['Imagen_Opcion_B_URL']).strip()
                    if opcion_b_imagen.startswith('database/allquestions/'):
                        opcion_b_imagen = opcion_b_imagen.replace('database/allquestions/', '/api/images/')
                
                opcion_c_imagen = None
                if pd.notna(row['Imagen_Opcion_C_URL']) and str(row['Imagen_Opcion_C_URL']).strip():
                    opcion_c_imagen = str(row['Imagen_Opcion_C_URL']).strip()
                    if opcion_c_imagen.startswith('database/allquestions/'):
                        opcion_c_imagen = opcion_c_imagen.replace('database/allquestions/', '/api/images/')
                
                opcion_d_imagen = None
                if pd.notna(row['Imagen_Opcion_D_URL']) and str(row['Imagen_Opcion_D_URL']).strip():
                    opcion_d_imagen = str(row['Imagen_Opcion_D_URL']).strip()
                    if opcion_d_imagen.startswith('database/allquestions/'):
                        opcion_d_imagen = opcion_d_imagen.replace('database/allquestions/', '/api/images/')
                
                # Count questions with images
                if any([pregunta_imagen, opcion_a_imagen, opcion_b_imagen, opcion_c_imagen, opcion_d_imagen]):
                    questions_with_images += 1
                
                # Extract additional fields
                competencia = str(row['Competencia']).strip() if pd.notna(row['Competencia']) else None
                componente = str(row['Componente']).strip() if pd.notna(row['Componente']) else None
                explicacion_respuesta = str(row['Explicación_Respuesta']).strip() if pd.notna(row['Explicación_Respuesta']) else None
                error_comun = str(row['Error_Común']).strip() if pd.notna(row['Error_Común']) else None
                pista_1 = str(row['Pista_1']).strip() if pd.notna(row['Pista_1']) else None
                pista_2 = str(row['Pista_2']).strip() if pd.notna(row['Pista_2']) else None
                pista_3 = str(row['Pista_3']).strip() if pd.notna(row['Pista_3']) else None
                tiempo_estimado = int(row['Tiempo_Estimado']) if pd.notna(row['Tiempo_Estimado']) else 120
                
                # Insert question
                insert_query = """
                INSERT INTO questions (
                    id, subject_id, question_text, correct_answer, options, 
                    difficulty, pregunta_texto, pregunta_imagen, 
                    opcion_a_imagen, opcion_b_imagen, opcion_c_imagen, opcion_d_imagen,
                    respuesta_correcta, puntos_xp, competencia, componente,
                    explicacion_respuesta, error_comun, pista_1, pista_2, pista_3,
                    tiempo_estimado, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, 
                    %s, %s, %s, 
                    %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, NOW()
                )
                """
                
                cursor.execute(insert_query, (
                    question_id, subject_id, pregunta_texto, respuesta_correcta, json.dumps(options),
                    difficulty, pregunta_texto, pregunta_imagen,
                    opcion_a_imagen, opcion_b_imagen, opcion_c_imagen, opcion_d_imagen,
                    respuesta_correcta, puntos_xp, competencia, componente,
                    explicacion_respuesta, error_comun, pista_1, pista_2, pista_3,
                    tiempo_estimado
                ))
                
                imported_count += 1
                
                if imported_count <= 5 or imported_count % 50 == 0:
                    print(f"  ✅ Imported {imported_count}: {pregunta_texto[:50]}...")
                
            except Exception as e:
                print(f"❌ Error importing row {index}: {e}")
                continue
        
        # Commit all changes
        conn.commit()
        print(f"\n🎉 Successfully imported {imported_count} questions from Excel")
        print(f"📸 Questions with images: {questions_with_images}")
        
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
        print(f"\n📊 Questions imported by subject:")
        for result in results:
            subject_name, total_q, with_pregunta_img, with_option_imgs = result
            print(f"  {subject_name}: {total_q} questions ({with_pregunta_img} with question images, {with_option_imgs} with option images)")
        
        cursor.close()
        conn.close()
        
        return imported_count, questions_with_images
        
    except Exception as e:
        print(f"❌ Error processing Excel file: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

if __name__ == "__main__":
    print("🚀 Starting COMPLETE ICFES Excel Import Process")
    print("📋 This will recreate all questions from Excel as source of truth")
    print("=" * 60)
    
    total_imported, total_with_images = import_excel_to_database()
    
    print(f"\n✅ Import Process Completed!")
    print(f"📊 Total questions imported: {total_imported}")
    print(f"🖼️ Questions with images: {total_with_images}")
    print(f"🔗 Image URLs converted to web-accessible paths (/api/images/...)")