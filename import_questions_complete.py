#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete ICFES Questions Import Script
Maps all Excel columns to database fields
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import uuid
from datetime import datetime
import json
import sys

# Set encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

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
        return None
    return str(text).strip()

def clean_number(value, default=0):
    """Clean numeric value"""
    if pd.isna(value):
        return default
    try:
        return float(value)
    except:
        return default

def map_difficulty(nivel):
    """Map difficulty level to 1-10 scale"""
    if pd.isna(nivel):
        return 5
    nivel = str(nivel).lower()
    if 'bajo' in nivel or 'fácil' in nivel or 'facil' in nivel:
        return 3
    elif 'medio' in nivel:
        return 5
    elif 'alto' in nivel or 'difícil' in nivel or 'dificil' in nivel:
        return 8
    else:
        return 5

def import_questions():
    print("="*60)
    print("ICFES COMPLETE QUESTIONS IMPORT")
    print("="*60)
    
    # Connect to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("[OK] Connected to database")
    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        return
    
    # Read Excel file
    try:
        df = pd.read_excel(EXCEL_PATH, encoding='utf-8')
        print(f"[OK] Loaded Excel: {len(df)} rows")
    except:
        try:
            df = pd.read_excel(EXCEL_PATH)
            print(f"[OK] Loaded Excel: {len(df)} rows")
        except Exception as e:
            print(f"[ERROR] Failed to read Excel: {e}")
            return
    
    # Map existing subjects
    cur.execute("SELECT id, name FROM subjects")
    existing_subjects = {row[1]: row[0] for row in cur.fetchall()}
    print(f"[OK] Found {len(existing_subjects)} existing subjects")
    
    # Prepare subject mapping
    subject_map = {
        'Matemáticas': existing_subjects.get('Matemáticas'),
        'Lectura Crítica': existing_subjects.get('Lenguaje'),
        'Ciencias Naturales': existing_subjects.get('Ciencias Naturales'),
        'Ciencias Sociales': existing_subjects.get('Ciencias Sociales'),
        'Inglés': existing_subjects.get('Inglés')
    }
    
    # Process questions
    questions_data = []
    stats = {'processed': 0, 'skipped': 0, 'by_subject': {}}
    
    print("\n[*] Processing questions...")
    
    for idx, row in df.iterrows():
        try:
            # Get area/subject
            area = clean_text(row.get('Área_Evaluada', row.get('�rea_Evaluada')))
            if not area:
                stats['skipped'] += 1
                continue
            
            # Map to subject_id
            subject_id = subject_map.get(area)
            if not subject_id:
                # Try to match Matemáticas
                if 'Matem' in area:
                    subject_id = subject_map['Matemáticas']
                elif 'Lectura' in area or 'Crítica' in area:
                    subject_id = subject_map['Lectura Crítica']
                else:
                    print(f"  [WARN] Unknown area: {area}")
                    stats['skipped'] += 1
                    continue
            
            # Get question text
            pregunta = clean_text(row.get('Pregunta'))
            if not pregunta:
                stats['skipped'] += 1
                continue
            
            # Get options
            opcion_a = clean_text(row.get('Opcion_A'))
            opcion_b = clean_text(row.get('Opcion_B'))
            opcion_c = clean_text(row.get('Opcion_C'))
            opcion_d = clean_text(row.get('Opcion_D'))
            
            # Get correct answer
            respuesta = clean_text(row.get('Respuesta_Correcta'))
            if respuesta not in ['A', 'B', 'C', 'D']:
                stats['skipped'] += 1
                continue
            
            # Map all fields
            question_id = str(uuid.uuid4())
            
            # IRT parameters
            param_a = clean_number(row.get('Parámetro_IRT_A', row.get('Par�metro_IRT_A')), 1.0)
            param_b = clean_number(row.get('Parámetro_IRT_B', row.get('Par�metro_IRT_B')), 0.0)
            param_c = clean_number(row.get('Parámetro_IRT_C', row.get('Par�metro_IRT_C')), 0.25)
            
            # Difficulty
            difficulty = map_difficulty(row.get('Nivel_Dificultad'))
            
            # Competence and component
            competencia = clean_text(row.get('Competencia'))
            componente = clean_text(row.get('Componente'))
            proceso_cognitivo = clean_text(row.get('Proceso_Cognitivo'))
            tipo_conocimiento = clean_text(row.get('Tipo_Conocimiento'))
            
            # Images
            pregunta_img = clean_text(row.get('Imagen_Pregunta_URL'))
            opcion_a_img = clean_text(row.get('Imagen_Opcion_A_URL'))
            opcion_b_img = clean_text(row.get('Imagen_Opcion_B_URL'))
            opcion_c_img = clean_text(row.get('Imagen_Opcion_C_URL'))
            opcion_d_img = clean_text(row.get('Imagen_Opcion_D_URL'))
            
            # Additional fields
            afirmacion = clean_text(row.get('Afirmación', row.get('Afirmaci�n')))
            evidencia = clean_text(row.get('Evidencia'))
            nivel_desempeno = clean_text(row.get('Nivel_Desempeño_Esperado', row.get('Nivel_Desempe�o_Esperado')))
            tiempo_estimado = int(clean_number(row.get('Tiempo_Estimado'), 60))
            
            # Hints and explanation
            pista_1 = clean_text(row.get('Pista_1'))
            pista_2 = clean_text(row.get('Pista_2'))
            pista_3 = clean_text(row.get('Pista_3'))
            explicacion = clean_text(row.get('Explicación_Respuesta', row.get('Explicaci�n_Respuesta')))
            error_comun = clean_text(row.get('Error_Común', row.get('Error_Com�n')))
            
            # Distractors
            distractor_a = clean_text(row.get('Distractor_A_Concepto'))
            distractor_b = clean_text(row.get('Distractor_B_Concepto'))
            distractor_c = clean_text(row.get('Distractor_C_Concepto'))
            
            # Error frequencies
            freq_a = clean_number(row.get('Frecuencia_Error_A'), 0)
            freq_b = clean_number(row.get('Frecuencia_Error_B'), 0)
            freq_c = clean_number(row.get('Frecuencia_Error_C'), 0)
            
            # Theme code
            codigo_tema = clean_text(row.get('Tema_Específico', row.get('Tema_Espec�fico')))
            
            # Discrimination index
            indice_disc = clean_number(row.get('Índice_Discriminación', row.get('�ndice_Discriminaci�n')), 0.5)
            
            # Create JSON for options field
            options_json = json.dumps({
                "A": opcion_a or "",
                "B": opcion_b or "",
                "C": opcion_c or "",
                "D": opcion_d or ""
            })
            
            # Create JSON for options_images field
            options_images_json = json.dumps({
                "A": opcion_a_img,
                "B": opcion_b_img,
                "C": opcion_c_img,
                "D": opcion_d_img
            }) if any([opcion_a_img, opcion_b_img, opcion_c_img, opcion_d_img]) else None
            
            # Add to batch
            questions_data.append({
                'id': question_id,
                'subject_id': subject_id,
                'question_text': pregunta,
                'pregunta_texto': pregunta,
                'pregunta_imagen': pregunta_img,
                'correct_answer': respuesta,
                'respuesta_correcta': respuesta,
                'options': options_json,
                'options_images': options_images_json,
                'difficulty': difficulty,
                'opcion_a_texto': opcion_a,
                'opcion_b_texto': opcion_b,
                'opcion_c_texto': opcion_c,
                'opcion_d_texto': opcion_d,
                'opcion_a_imagen': opcion_a_img,
                'opcion_b_imagen': opcion_b_img,
                'opcion_c_imagen': opcion_c_img,
                'opcion_d_imagen': opcion_d_img,
                'competencia': competencia,
                'componente': componente,
                'proceso_cognitivo': proceso_cognitivo,
                'tipo_conocimiento': tipo_conocimiento,
                'afirmacion': afirmacion,
                'evidencia': evidencia,
                'nivel_desempeno_esperado': nivel_desempeno,
                'tiempo_estimado': tiempo_estimado,
                'pista_1': pista_1,
                'pista_2': pista_2,
                'pista_3': pista_3,
                'explicacion_respuesta': explicacion,
                'error_comun': error_comun,
                'distractor_a_concepto': distractor_a,
                'distractor_b_concepto': distractor_b,
                'distractor_c_concepto': distractor_c,
                'frecuencia_error_a': freq_a,
                'frecuencia_error_b': freq_b,
                'frecuencia_error_c': freq_c,
                'codigo_tema': codigo_tema,
                'indice_discriminacion': indice_disc,
                'parametro_irt_a': param_a,
                'parametro_irt_b': param_b,
                'parametro_irt_c': param_c,
                'image_url': pregunta_img,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            
            stats['processed'] += 1
            
            # Track by subject
            if area not in stats['by_subject']:
                stats['by_subject'][area] = 0
            stats['by_subject'][area] += 1
            
            if stats['processed'] % 50 == 0:
                print(f"  Processed {stats['processed']} questions...")
                
        except Exception as e:
            print(f"  [ERROR] Row {idx}: {str(e)[:100]}")
            stats['skipped'] += 1
    
    # Insert questions
    if questions_data:
        print(f"\n[*] Inserting {len(questions_data)} questions...")
        
        try:
            # Clear existing questions first
            cur.execute("DELETE FROM questions")
            print("  [OK] Cleared existing questions")
            
            # Insert new questions
            for q in questions_data:
                cur.execute("""
                    INSERT INTO questions (
                        id, subject_id, question_text, correct_answer, options,
                        difficulty, pregunta_texto, pregunta_imagen, respuesta_correcta,
                        opcion_a_texto, opcion_b_texto, opcion_c_texto, opcion_d_texto,
                        opcion_a_imagen, opcion_b_imagen, opcion_c_imagen, opcion_d_imagen,
                        competencia, componente, proceso_cognitivo, tipo_conocimiento,
                        afirmacion, evidencia, nivel_desempeno_esperado, tiempo_estimado,
                        pista_1, pista_2, pista_3, explicacion_respuesta, error_comun,
                        distractor_a_concepto, distractor_b_concepto, distractor_c_concepto,
                        frecuencia_error_a, frecuencia_error_b, frecuencia_error_c,
                        codigo_tema, indice_discriminacion,
                        parametro_irt_a, parametro_irt_b, parametro_irt_c,
                        image_url, options_images, created_at, updated_at
                    ) VALUES (
                        %(id)s, %(subject_id)s, %(question_text)s, %(correct_answer)s, %(options)s,
                        %(difficulty)s, %(pregunta_texto)s, %(pregunta_imagen)s, %(respuesta_correcta)s,
                        %(opcion_a_texto)s, %(opcion_b_texto)s, %(opcion_c_texto)s, %(opcion_d_texto)s,
                        %(opcion_a_imagen)s, %(opcion_b_imagen)s, %(opcion_c_imagen)s, %(opcion_d_imagen)s,
                        %(competencia)s, %(componente)s, %(proceso_cognitivo)s, %(tipo_conocimiento)s,
                        %(afirmacion)s, %(evidencia)s, %(nivel_desempeno_esperado)s, %(tiempo_estimado)s,
                        %(pista_1)s, %(pista_2)s, %(pista_3)s, %(explicacion_respuesta)s, %(error_comun)s,
                        %(distractor_a_concepto)s, %(distractor_b_concepto)s, %(distractor_c_concepto)s,
                        %(frecuencia_error_a)s, %(frecuencia_error_b)s, %(frecuencia_error_c)s,
                        %(codigo_tema)s, %(indice_discriminacion)s,
                        %(parametro_irt_a)s, %(parametro_irt_b)s, %(parametro_irt_c)s,
                        %(image_url)s, %(options_images)s, %(created_at)s, %(updated_at)s
                    )
                """, q)
            
            conn.commit()
            print(f"  [OK] Successfully imported {len(questions_data)} questions!")
            
        except Exception as e:
            print(f"  [ERROR] Failed to insert: {e}")
            conn.rollback()
    
    # Show statistics
    print("\n" + "="*60)
    print("IMPORT STATISTICS")
    print("="*60)
    print(f"Total processed: {stats['processed']}")
    print(f"Total skipped: {stats['skipped']}")
    print("\nBy subject:")
    for subject, count in stats['by_subject'].items():
        print(f"  {subject}: {count}")
    
    # Verify in database
    cur.execute("""
        SELECT s.name, COUNT(q.id) as count
        FROM subjects s
        LEFT JOIN questions q ON s.id = q.subject_id
        GROUP BY s.name
        ORDER BY count DESC
    """)
    
    print("\nDatabase totals:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} questions")
    
    # Close connection
    cur.close()
    conn.close()
    print("\n[OK] Import complete!")

if __name__ == "__main__":
    import_questions()