#!/usr/bin/env python3
"""Direct question loader - minimal approach"""

import pandas as pd
import psycopg2
import uuid
import json

# Connect
conn = psycopg2.connect(
    host='postgres', port=5432, database='gameplay_db',
    user='gameplay', password='gameplay123'
)
cur = conn.cursor()

try:
    # Get Mathematics subject and topic
    cur.execute("""
        SELECT t.id, s.id FROM topics t 
        JOIN subjects s ON t.subject_id = s.id 
        WHERE s.name = 'Matemáticas' 
        LIMIT 1
    """)
    topic_id, subject_id = cur.fetchone()
    print(f"Using topic_id: {topic_id}, subject_id: {subject_id}")
    
    # Load Excel
    df = pd.read_excel('/app/ICFES2 (1).xlsx')
    print(f"Loading {len(df)} questions...")
    
    # Clear existing
    cur.execute("DELETE FROM questions")
    conn.commit()
    
    # Insert each question
    count = 0
    for idx, row in df.iterrows():
        try:
            # Basic fields
            q_id = str(uuid.uuid4())
            text = str(row['Pregunta'])[:2000]
            answer = str(row['Respuesta_Correcta'])[0].upper()
            diff = int(row.get('Nivel_Dificultad', 2))
            
            # Options JSON
            opts = {}
            for o in ['A','B','C','D']:
                if f'Opcion_{o}' in row and pd.notna(row[f'Opcion_{o}']):
                    opts[o] = str(row[f'Opcion_{o}'])
            
            # Insert
            cur.execute("""
                INSERT INTO questions (
                    id, topic_id, subject_id, pregunta_texto,
                    respuesta_correcta, difficulty, question_text,
                    options, correct_answer
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                q_id, topic_id, subject_id, text,
                answer, diff, text,
                json.dumps(opts), answer
            ))
            
            count += 1
            if count % 10 == 0:
                conn.commit()
                print(f"Progress: {count}/{len(df)}")
                
        except Exception as e:
            print(f"Error row {idx}: {e}")
            conn.rollback()
    
    conn.commit()
    print(f"✅ Loaded {count} questions")
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    print(f"📊 Total in DB: {total}")
    
except Exception as e:
    print(f"Fatal: {e}")
finally:
    cur.close()
    conn.close()