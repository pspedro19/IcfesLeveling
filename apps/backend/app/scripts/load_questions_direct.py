#!/usr/bin/env python3
"""Direct question loader - minimal approach"""

import os
import pandas as pd
import psycopg2
import uuid
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connect (using environment variables)
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'postgres'),
    port=int(os.getenv('DB_PORT', '5432')),
    database=os.getenv('DB_NAME', 'gameplay_db'),
    user=os.getenv('DB_USER', 'gameplay'),
    password=os.getenv('DB_PASSWORD', '')
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
    logger.info(f"Using topic_id: {topic_id}, subject_id: {subject_id}")

    # Load Excel
    df = pd.read_excel('/app/ICFES2 (1).xlsx')
    logger.info(f"Loading {len(df)} questions...")
    
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
                logger.info(f"Progress: {count}/{len(df)}")

        except Exception as e:
            logger.error(f"Error row {idx}: {e}")
            conn.rollback()

    conn.commit()
    logger.info(f"Loaded {count} questions")

    # Verify
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    logger.info(f"Total in DB: {total}")

except Exception as e:
    logger.error(f"Fatal: {e}")
finally:
    cur.close()
    conn.close()