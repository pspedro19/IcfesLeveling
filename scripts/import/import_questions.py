#!/usr/bin/env python
"""
Script to import all 480 ICFES questions from Excel to PostgreSQL
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import uuid
from datetime import datetime
import json
import os

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'gameplay_db',
    'user': 'gameplay',
    'password': 'gameplay123'
}

# Excel file path
EXCEL_PATH = r"database\allquestions\ICFES_BASE_DATOS_COMPLETA_RUTAS_ACTUALIZADAS.xlsx"

def clean_text(text):
    """Clean text from Excel"""
    if pd.isna(text):
        return ""
    return str(text).strip()

def import_questions():
    print("ICFES Questions Import Script")
    print("=" * 60)
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("✅ Connected to database")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Read Excel file
    try:
        df = pd.read_excel(EXCEL_PATH)
        print(f"✅ Loaded Excel file: {len(df)} rows")
    except Exception as e:
        print(f"❌ Failed to read Excel: {e}")
        return
    
    # First, ensure subjects exist
    subjects_map = {
        'MATEMÁTICAS': 'matematicas',
        'FISICA': 'fisica',
        'QUÍMICA': 'quimica',
        'BIOLOGÍA': 'biologia',
        'ESPAÑOL': 'espanol',
        'INGLÉS': 'ingles',
        'SOCIALES': 'sociales'
    }
    
    print("\n📚 Creating/updating subjects...")
    for subject_name, subject_alias in subjects_map.items():
        subject_id = str(uuid.uuid4())
        try:
            cur.execute("""
                INSERT INTO subjects (id, nombre, alias, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (nombre) DO UPDATE
                SET alias = EXCLUDED.alias
                RETURNING id
            """, (subject_id, subject_name, subject_alias, datetime.now()))
            result = cur.fetchone()
            if result:
                subjects_map[subject_name] = result[0]
            print(f"  ✓ {subject_name}")
        except Exception as e:
            # Get existing ID
            cur.execute("SELECT id FROM subjects WHERE nombre = %s", (subject_name,))
            result = cur.fetchone()
            if result:
                subjects_map[subject_name] = result[0]
    
    conn.commit()
    
    # Prepare questions data
    questions_data = []
    skipped = 0
    processed = 0
    
    print("\n📝 Processing questions...")
    for idx, row in df.iterrows():
        try:
            # Get subject
            materia = clean_text(row.get('MATERIA', '')).upper()
            if materia not in subjects_map:
                print(f"  ⚠️ Unknown subject: {materia} (row {idx})")
                skipped += 1
                continue
            
            subject_id = subjects_map[materia]
            
            # Get question data
            pregunta = clean_text(row.get('PREGUNTA', ''))
            if not pregunta:
                skipped += 1
                continue
            
            # Get options
            opcion_a = clean_text(row.get('OPCIÓN A', ''))
            opcion_b = clean_text(row.get('OPCIÓN B', ''))
            opcion_c = clean_text(row.get('OPCIÓN C', ''))
            opcion_d = clean_text(row.get('OPCIÓN D', ''))
            
            # Get correct answer
            respuesta = clean_text(row.get('RESPUESTA CORRECTA', '')).upper()
            if respuesta not in ['A', 'B', 'C', 'D']:
                print(f"  ⚠️ Invalid answer: {respuesta} (row {idx})")
                skipped += 1
                continue
            
            # Get IRT parameters (if available)
            a_param = float(row.get('a', 1.0)) if 'a' in row else 1.0
            b_param = float(row.get('b', 0.0)) if 'b' in row else 0.0
            c_param = float(row.get('c', 0.25)) if 'c' in row else 0.25
            
            # Get image paths
            pregunta_img = clean_text(row.get('PREGUNTA IMG RUTA', ''))
            opcion_a_img = clean_text(row.get('OPCIÓN A IMG RUTA', ''))
            opcion_b_img = clean_text(row.get('OPCIÓN B IMG RUTA', ''))
            opcion_c_img = clean_text(row.get('OPCIÓN C IMG RUTA', ''))
            opcion_d_img = clean_text(row.get('OPCIÓN D IMG RUTA', ''))
            
            # Create question tuple
            question_id = str(uuid.uuid4())
            questions_data.append((
                question_id,
                subject_id,
                pregunta,
                opcion_a,
                opcion_b,
                opcion_c,
                opcion_d,
                respuesta,
                a_param,
                b_param,
                c_param,
                pregunta_img,
                opcion_a_img,
                opcion_b_img,
                opcion_c_img,
                opcion_d_img,
                datetime.now()
            ))
            
            processed += 1
            if processed % 50 == 0:
                print(f"  Processed {processed} questions...")
                
        except Exception as e:
            print(f"  ❌ Error processing row {idx}: {e}")
            skipped += 1
    
    # Clear existing questions (optional)
    print("\n🗑️ Clearing existing questions...")
    cur.execute("DELETE FROM questions")
    conn.commit()
    
    # Insert questions in batches
    print(f"\n💾 Inserting {len(questions_data)} questions...")
    try:
        execute_batch(cur, """
            INSERT INTO questions (
                id, materia_id, pregunta_texto, 
                opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
                respuesta_correcta, 
                parametro_a, parametro_b, parametro_c,
                pregunta_imagen, opcion_a_imagen, opcion_b_imagen, 
                opcion_c_imagen, opcion_d_imagen,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, questions_data, page_size=100)
        
        conn.commit()
        print(f"✅ Successfully imported {len(questions_data)} questions!")
        
    except Exception as e:
        print(f"❌ Failed to insert questions: {e}")
        conn.rollback()
    
    # Get statistics
    print("\n📊 Final Statistics:")
    cur.execute("""
        SELECT s.nombre, COUNT(q.id) as count
        FROM subjects s
        LEFT JOIN questions q ON s.id = q.materia_id
        GROUP BY s.nombre
        ORDER BY count DESC
    """)
    
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} questions")
    
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    print(f"\n  TOTAL: {total} questions")
    print(f"  Skipped: {skipped} rows")
    
    # Close connection
    cur.close()
    conn.close()
    print("\n✅ Import complete!")

if __name__ == "__main__":
    import_questions()