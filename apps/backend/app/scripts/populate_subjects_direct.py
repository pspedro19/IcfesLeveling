"""Direct SQL script to populate subjects"""
import os
import psycopg2
import uuid
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def populate_subjects():
    """Populate subjects using direct SQL"""

    # Connection parameters (from environment variables)
    conn_params = {
        'host': os.getenv('DB_HOST', 'postgres'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'gameplay_db'),
        'user': os.getenv('DB_USER', 'gameplay'),
        'password': os.getenv('DB_PASSWORD', '')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**conn_params)
        cur = conn.cursor()
        
        # Check if subjects table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'subjects'
            );
        """)
        
        if not cur.fetchone()[0]:
            logger.info("Creating subjects table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS subjects (
                    id UUID PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    description TEXT,
                    icon_url VARCHAR(500),
                    color VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        # Clear existing subjects
        cur.execute("DELETE FROM subjects;")
        
        # Define ICFES subjects
        subjects = [
            (str(uuid.uuid4()), "Matemáticas", "Domina el arte de los números y las ecuaciones", 
             "/assets/images/subjects/matematicas.png", "#8B5CF6"),
            (str(uuid.uuid4()), "Lectura Crítica", "Conquista el poder de las palabras y la comprensión",
             "/assets/images/subjects/lectura.png", "#3B82F6"),
            (str(uuid.uuid4()), "Ciencias Naturales", "Explora los misterios del universo y la vida",
             "/assets/images/subjects/ciencias.png", "#10B981"),
            (str(uuid.uuid4()), "Sociales y Ciudadanas", "Comprende la sociedad y forja tu ciudadanía",
             "/assets/images/subjects/sociales.png", "#F59E0B"),
            (str(uuid.uuid4()), "Inglés", "Desbloquea el idioma universal",
             "/assets/images/subjects/ingles.png", "#EF4444")
        ]
        
        # Insert subjects
        for subject in subjects:
            cur.execute("""
                INSERT INTO subjects (id, name, description, icon_url, color)
                VALUES (%s, %s, %s, %s, %s);
            """, subject)
        
        # Commit the transaction
        conn.commit()
        
        # Verify subjects were created
        cur.execute("SELECT COUNT(*) FROM subjects;")
        count = cur.fetchone()[0]
        logger.info(f"Successfully populated {count} subjects")

        # List all subjects
        cur.execute("SELECT name, description FROM subjects;")
        all_subjects = cur.fetchall()
        for subject in all_subjects:
            logger.info(f"  - {subject[0]}: {subject[1]}")

        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    populate_subjects()