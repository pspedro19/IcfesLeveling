#!/usr/bin/env python3
"""
Script para actualizar el campo requiere_imagen basado en los datos del Excel
"""

import os
import pandas as pd
import psycopg2

# Database connection parameters
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'gameplay_db',
    'user': 'gameplay',
    'password': 'gameplay123'
}

def update_requiere_imagen_field():
    """Update requiere_imagen field based on Excel data"""
    
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
        
        # Check Requiere_Imagen column
        if 'Requiere_Imagen' not in df.columns:
            print("❌ Column 'Requiere_Imagen' not found in Excel")
            return
        
        print(f"🔍 Requiere_Imagen distribution:")
        print(df['Requiere_Imagen'].value_counts())
        
        # Connect to database
        conn = psycopg2.connect(**DATABASE_CONFIG)
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
                requiere_imagen = bool(row['Requiere_Imagen'])
                
                if requiere_imagen:
                    questions_with_images += 1
                
                # Update existing question by matching question text
                update_query = """
                UPDATE questions 
                SET requiere_imagen = %s
                WHERE pregunta_texto ILIKE %s
                """
                
                # Use first 100 characters for matching
                search_text = f"%{pregunta_texto[:100]}%"
                
                cursor.execute(update_query, (requiere_imagen, search_text))
                
                if cursor.rowcount > 0:
                    updates_made += cursor.rowcount
                    if updates_made <= 10:
                        print(f"  ✅ Updated {updates_made}: {pregunta_texto[:50]}... → requiere_imagen={requiere_imagen}")
                
            except Exception as e:
                print(f"❌ Error updating row {index}: {e}")
                continue
        
        # Commit all changes
        conn.commit()
        print(f"\n🎉 Successfully updated {updates_made} questions with requiere_imagen field")
        print(f"📸 Questions that require images in Excel: {questions_with_images}")
        
        # Verify results
        cursor.execute("""
        SELECT 
            COUNT(*) as total_questions,
            COUNT(CASE WHEN requiere_imagen = TRUE THEN 1 END) as require_images,
            COUNT(CASE WHEN requiere_imagen = FALSE THEN 1 END) as no_require_images,
            COUNT(CASE WHEN pregunta_imagen IS NOT NULL AND pregunta_imagen != '' THEN 1 END) as have_image_urls
        FROM questions
        """)
        
        result = cursor.fetchone()
        print(f"\n📊 Database verification after update:")
        print(f"  Total questions: {result[0]}")
        print(f"  Require images (TRUE): {result[1]}")
        print(f"  Don't require images (FALSE): {result[2]}")
        print(f"  Have image URLs: {result[3]}")
        
        # Show questions that require images by subject
        cursor.execute("""
        SELECT 
            s.name as subject_name,
            COUNT(q.id) as total_questions,
            COUNT(CASE WHEN q.requiere_imagen = TRUE THEN 1 END) as require_images
        FROM subjects s 
        LEFT JOIN questions q ON s.id = q.subject_id 
        GROUP BY s.id, s.name 
        ORDER BY s.name
        """)
        
        print(f"\n📚 Questions requiring images by subject:")
        for result in cursor.fetchall():
            subject_name, total_q, require_imgs = result
            percentage = (require_imgs / total_q * 100) if total_q > 0 else 0
            print(f"  {subject_name}: {require_imgs}/{total_q} ({percentage:.1f}%)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error processing Excel file: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Updating requiere_imagen field from Excel data")
    print("=" * 50)
    
    update_requiere_imagen_field()
    
    print("\n✅ Process completed!")