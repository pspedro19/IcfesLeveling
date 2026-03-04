#!/usr/bin/env python3
"""
Simple Question Loader - Direct approach without complex transactions
"""

import os
import pandas as pd
import psycopg2
import uuid
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Database connection (from environment variables)
conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'postgres'),
    port=int(os.getenv('DB_PORT', '5432')),
    database=os.getenv('DB_NAME', 'gameplay_db'),
    user=os.getenv('DB_USER', 'gameplay'),
    password=os.getenv('DB_PASSWORD', '')
)
cur = conn.cursor()

try:
    # First, create default topics for each subject
    logger.info("Creating default topics...")
    cur.execute("SELECT id, name FROM subjects")
    subjects = cur.fetchall()
    
    for subject_id, subject_name in subjects:
        # Create a general topic for each subject
        topic_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO topics (id, name, subject_id, description)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (name, subject_id) DO NOTHING
        """, (topic_id, 'General', subject_id, f'Tema general de {subject_name}'))
    
    conn.commit()
    logger.info("✅ Default topics created")
    
    # Get the topic for Mathematics (all questions are Mathematics)
    cur.execute("""
        SELECT t.id FROM topics t 
        JOIN subjects s ON t.subject_id = s.id 
        WHERE s.name = 'Matemáticas' AND t.name = 'General'
    """)
    result = cur.fetchone()
    
    if not result:
        # Create if doesn't exist
        cur.execute("SELECT id FROM subjects WHERE name = 'Matemáticas'")
        math_subject = cur.fetchone()
        if math_subject:
            topic_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO topics (id, name, subject_id)
                VALUES (%s, 'General', %s)
            """, (topic_id, math_subject[0]))
            conn.commit()
        else:
            logger.error("Mathematics subject not found!")
            exit(1)
    else:
        topic_id = result[0]
    
    logger.info(f"Using topic_id: {topic_id}")
    
    # Load Excel file
    logger.info("Loading Excel file...")
    df = pd.read_excel('/app/ICFES2 (1).xlsx')
    logger.info(f"Found {len(df)} questions")
    
    # Clear existing questions
    cur.execute("DELETE FROM questions")
    conn.commit()
    logger.info("Cleared existing questions")
    
    # Get Mathematics subject ID
    cur.execute("SELECT id FROM subjects WHERE name = 'Matemáticas'")
    subject_id = cur.fetchone()[0]
    
    # Insert questions one by one
    success_count = 0
    for idx, row in df.iterrows():
        try:
            question_id = str(uuid.uuid4())
            
            # Prepare data
            pregunta_texto = str(row.get('Pregunta', ''))[:5000]  # Limit length
            respuesta_correcta = str(row.get('Respuesta_Correcta', 'A'))[0].upper()
            difficulty = int(row.get('Nivel_Dificultad', 2))
            
            # Options
            options = {}
            for opt in ['A', 'B', 'C', 'D']:
                col = f'Opcion_{opt}'
                if col in row and pd.notna(row[col]):
                    options[opt] = str(row[col])
            
            # Power stats
            power_stats = {
                'xp_reward': int(row.get('Puntos_XP', 20)),
                'orbs_reward': 5,
                'power_bonus': difficulty * 2
            }
            
            # Insert question
            cur.execute("""
                INSERT INTO questions (
                    id, topic_id, subject_id, 
                    pregunta_texto, respuesta_correcta, difficulty,
                    question_text, options, correct_answer, power_stats
                ) VALUES (
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s, %s, %s
                )
            """, (
                question_id, topic_id, subject_id,
                pregunta_texto, respuesta_correcta, difficulty,
                pregunta_texto,  # Duplicate for English field
                json.dumps(options),
                respuesta_correcta,
                json.dumps(power_stats)
            ))
            
            success_count += 1
            
        except Exception as e:
            logger.error(f"Error in row {idx}: {e}")
            conn.rollback()
            continue
        
        # Commit every 10 questions
        if success_count % 10 == 0:
            conn.commit()
            logger.info(f"Progress: {success_count}/{len(df)}")
    
    # Final commit
    conn.commit()
    
    # Verify
    cur.execute("SELECT COUNT(*) FROM questions")
    total = cur.fetchone()[0]
    
    logger.info(f"✅ Successfully loaded {success_count} questions")
    logger.info(f"📊 Total questions in database: {total}")
    
except Exception as e:
    logger.error(f"Fatal error: {e}")
    conn.rollback()
    
finally:
    cur.close()
    conn.close()