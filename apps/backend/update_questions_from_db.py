"""
Script to update SAMPLE_QUESTIONS in startup_minimal.py from database
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import json

def get_questions_from_db():
    """Fetch questions from database grouped by subject"""
    conn = psycopg2.connect(
        host="localhost",
        database="icfes_db",
        user="postgres",
        password="postgres",
        cursor_factory=RealDictCursor
    )
    
    cur = conn.cursor()
    
    # Get all questions with subject info
    cur.execute("""
        SELECT 
            q.id,
            q.statement,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.correct_answer,
            q.topic,
            COALESCE(q.difficulty, 5) as difficulty,
            COALESCE(q.parametro_irt_b, 0) as irt_b,
            q.competencia,
            q.explicacion_respuesta,
            s.name as subject_name
        FROM questions q
        JOIN subjects s ON q.subject_id = s.id
        ORDER BY s.name, q.id
        LIMIT 100
    """)
    
    questions = cur.fetchall()
    conn.close()
    
    # Group by subject
    questions_by_subject = {
        "matematicas": [],
        "fisica": [],
        "quimica": [],
        "biologia": [],
        "espanol": []
    }
    
    subject_map = {
        "Matemáticas": "matematicas",
        "Física": "fisica",
        "Química": "quimica",
        "Biología": "biologia",
        "Español": "espanol",
        "Lenguaje": "espanol"
    }
    
    for q in questions:
        subject_key = subject_map.get(q['subject_name'], 'matematicas')
        
        question_dict = {
            "id": q['id'],
            "statement": q['statement'],
            "option_a": q['option_a'],
            "option_b": q['option_b'],
            "option_c": q['option_c'],
            "option_d": q['option_d'],
            "correct_answer": q['correct_answer'],
            "subject_id": subject_key,
            "topic": q['topic'] or "General",
            "difficulty": "medio" if q['difficulty'] == 5 else ("facil" if q['difficulty'] < 5 else "dificil"),
            "irt_b": float(q['irt_b']),
            "competencia": q['competencia'],
            "explicacion": q['explicacion_respuesta']
        }
        
        questions_by_subject[subject_key].append(question_dict)
    
    return questions_by_subject

def update_startup_file():
    """Update startup_minimal.py with real database questions"""
    questions = get_questions_from_db()
    
    # Print questions to copy into startup_minimal.py
    print("# Replace SAMPLE_QUESTIONS in startup_minimal.py with:")
    print("SAMPLE_QUESTIONS = {")
    
    for subject, subject_questions in questions.items():
        print(f'    "{subject}": [')
        for q in subject_questions[:10]:  # Limit to 10 per subject for MVP
            print(f'        {{')
            print(f'            "id": {q["id"]},')
            print(f'            "statement": {json.dumps(q["statement"], ensure_ascii=False)},')
            print(f'            "option_a": {json.dumps(q["option_a"], ensure_ascii=False)},')
            print(f'            "option_b": {json.dumps(q["option_b"], ensure_ascii=False)},')
            print(f'            "option_c": {json.dumps(q["option_c"], ensure_ascii=False)},')
            print(f'            "option_d": {json.dumps(q["option_d"], ensure_ascii=False)},')
            print(f'            "correct_answer": "{q["correct_answer"]}",')
            print(f'            "subject_id": "{q["subject_id"]}",')
            print(f'            "topic": {json.dumps(q["topic"], ensure_ascii=False)},')
            print(f'            "difficulty": "{q["difficulty"]}",')
            print(f'            "irt_b": {q["irt_b"]}')
            print(f'        }},')
        print(f'    ],')
    
    print("}")
    
    # Also save to a file
    with open("db_questions.json", "w", encoding="utf-8") as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Questions saved to db_questions.json")
    print(f"📊 Total questions by subject:")
    for subject, qs in questions.items():
        print(f"   - {subject}: {len(qs)} questions")

if __name__ == "__main__":
    try:
        update_startup_file()
    except Exception as e:
        print(f"❌ Error: {e}")