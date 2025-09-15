#!/usr/bin/env python3
"""
Script to update questions table with image URLs from Excel
"""

import os
import sys
import pandas as pd
import psycopg2
import json
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

def update_questions_with_images():
    """Update questions table with image URLs from Excel"""
    
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
        
        # Display column names to understand structure
        print("\n📋 Available columns:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        
        # Look for image-related columns
        image_columns = [col for col in df.columns if 'imagen' in col.lower() or 'image' in col.lower() or 'url' in col.lower()]
        print(f"\n🖼️ Image-related columns found: {image_columns}")
        
        # Check for questions with image URLs
        questions_with_images = 0
        for col in image_columns:
            non_null_count = df[col].notna().sum()
            if non_null_count > 0:
                print(f"  {col}: {non_null_count} non-null values")
                questions_with_images += non_null_count
        
        print(f"\n✅ Total questions with images: {questions_with_images}")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        updates_made = 0
        
        # Process each row
        for index, row in df.iterrows():
            # Look for question identifier (could be ID, text, etc.)
            question_text = None
            if 'Pregunta' in df.columns:
                question_text = row['Pregunta']
            elif 'pregunta_texto' in df.columns:
                question_text = row['pregunta_texto']
            elif 'question_text' in df.columns:
                question_text = row['question_text']
            
            if not question_text or pd.isna(question_text):
                continue
            
            # Prepare update query
            update_fields = []
            update_values = []
            
            # Check each image column
            for col in image_columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    image_url = str(row[col]).strip()
                    
                    # Map Excel column to database column
                    db_column = None
                    if 'pregunta' in col.lower() and 'imagen' in col.lower():
                        db_column = 'pregunta_imagen'
                    elif 'opcion' in col.lower() and 'a' in col.lower():
                        db_column = 'opcion_a_imagen'
                    elif 'opcion' in col.lower() and 'b' in col.lower():
                        db_column = 'opcion_b_imagen'
                    elif 'opcion' in col.lower() and 'c' in col.lower():
                        db_column = 'opcion_c_imagen'
                    elif 'opcion' in col.lower() and 'd' in col.lower():
                        db_column = 'opcion_d_imagen'
                    
                    if db_column:
                        update_fields.append(f"{db_column} = %s")
                        update_values.append(image_url)
            
            # Execute update if we have fields to update
            if update_fields and question_text:
                query = f"""
                UPDATE questions 
                SET {', '.join(update_fields)}
                WHERE pregunta_texto ILIKE %s
                """
                update_values.append(f"%{question_text[:50]}%")  # Use first 50 chars for matching
                
                try:
                    cursor.execute(query, update_values)
                    if cursor.rowcount > 0:
                        updates_made += cursor.rowcount
                        if updates_made <= 5:  # Show first 5 updates
                            print(f"  ✅ Updated question: {question_text[:50]}...")
                except Exception as e:
                    print(f"  ❌ Error updating question {index}: {e}")
        
        # Commit changes
        conn.commit()
        print(f"\n🎉 Successfully updated {updates_made} questions with image URLs")
        
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
        print(f"\n📊 Database verification:")
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

def verify_image_files():
    """Verify which image files actually exist"""
    print("\n🔍 Verifying image files...")
    
    base_path = Path("database/allquestions")
    image_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg']
    
    subjects = ['Matematicas', 'Ciencias Naturales', 'Ciencias Sociales', 'Lectura Critica', 'Ingles']
    
    for subject in subjects:
        subject_path = base_path / subject
        if subject_path.exists():
            image_count = 0
            for ext in image_extensions:
                image_count += len(list(subject_path.rglob(f'*{ext}')))
            print(f"  {subject}: {image_count} images")
        else:
            print(f"  {subject}: Directory not found")

if __name__ == "__main__":
    print("🚀 Starting ICFES Questions Image Update Process")
    print("=" * 50)
    
    verify_image_files()
    update_questions_with_images()
    
    print("\n✅ Process completed!")