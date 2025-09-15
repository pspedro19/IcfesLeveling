#!/usr/bin/env python3
"""
Script para agregar URLs de imágenes a las preguntas existentes
"""

import os
import pandas as pd
import psycopg2
import json

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

def update_questions_with_images():
    """Update existing questions with image URLs from Excel"""
    
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
        
        updates_made = 0
        questions_with_images = 0
        
        # Process each row
        for index, row in df.iterrows():
            try:
                # Skip rows without question text
                if pd.isna(row['Pregunta']) or not str(row['Pregunta']).strip():
                    continue
                
                pregunta_texto = str(row['Pregunta']).strip()
                
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
                    
                    # Update existing question by matching question text
                    update_query = """
                    UPDATE questions 
                    SET 
                        pregunta_imagen = %s,
                        opcion_a_imagen = %s,
                        opcion_b_imagen = %s,
                        opcion_c_imagen = %s,
                        opcion_d_imagen = %s
                    WHERE pregunta_texto ILIKE %s
                    """
                    
                    # Use first 100 characters for matching
                    search_text = f"%{pregunta_texto[:100]}%"
                    
                    cursor.execute(update_query, (
                        pregunta_imagen, opcion_a_imagen, opcion_b_imagen, 
                        opcion_c_imagen, opcion_d_imagen, search_text
                    ))
                    
                    if cursor.rowcount > 0:
                        updates_made += cursor.rowcount
                        if updates_made <= 10:
                            print(f"  ✅ Updated question {updates_made}: {pregunta_texto[:50]}...")
                
            except Exception as e:
                print(f"❌ Error updating row {index}: {e}")
                continue
        
        # Commit all changes
        conn.commit()
        print(f"\n🎉 Successfully updated {updates_made} questions with image URLs")
        print(f"📸 Questions with images in Excel: {questions_with_images}")
        
        # Verify results
        cursor.execute("""
        SELECT 
            COUNT(*) as total_questions,
            COUNT(CASE WHEN pregunta_imagen IS NOT NULL AND pregunta_imagen != '' THEN 1 END) as with_pregunta_imagen,
            COUNT(CASE WHEN opcion_a_imagen IS NOT NULL AND opcion_a_imagen != '' THEN 1 END) as with_opcion_a_imagen,
            COUNT(CASE WHEN opcion_b_imagen IS NOT NULL AND opcion_b_imagen != '' THEN 1 END) as with_opcion_b_imagen,
            COUNT(CASE WHEN opcion_c_imagen IS NOT NULL AND opcion_c_imagen != '' THEN 1 END) as with_opcion_c_imagen,
            COUNT(CASE WHEN opcion_d_imagen IS NOT NULL AND opcion_d_imagen != '' THEN 1 END) as with_opcion_d_imagen
        FROM questions
        """)
        
        result = cursor.fetchone()
        print(f"\n📊 Database verification after update:")
        print(f"  Total questions: {result[0]}")
        print(f"  With pregunta_imagen: {result[1]}")
        print(f"  With opcion_a_imagen: {result[2]}")
        print(f"  With opcion_b_imagen: {result[3]}")
        print(f"  With opcion_c_imagen: {result[4]}")
        print(f"  With opcion_d_imagen: {result[5]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error processing Excel file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Adding Image URLs to Existing Questions")
    print("=" * 50)
    
    update_questions_with_images()
    
    print("\n✅ Process completed!")