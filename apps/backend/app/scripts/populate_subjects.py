"""Script to populate subjects in the database"""
import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import SessionLocal, engine
from app.models.subject import Subject
from sqlalchemy import text

def populate_subjects():
    """Populate the database with ICFES subjects"""
    db = SessionLocal()
    
    try:
        # Clear existing subjects
        db.query(Subject).delete()
        
        # Define ICFES subjects
        subjects_data = [
            {
                "id": uuid.uuid4(),
                "name": "Matemáticas",
                "description": "Domina el arte de los números y las ecuaciones",
                "icon_url": "/assets/images/subjects/matematicas.png",
                "color": "#8B5CF6"
            },
            {
                "id": uuid.uuid4(),
                "name": "Lectura Crítica",
                "description": "Conquista el poder de las palabras y la comprensión",
                "icon_url": "/assets/images/subjects/lectura.png", 
                "color": "#3B82F6"
            },
            {
                "id": uuid.uuid4(),
                "name": "Ciencias Naturales",
                "description": "Explora los misterios del universo y la vida",
                "icon_url": "/assets/images/subjects/ciencias.png",
                "color": "#10B981"
            },
            {
                "id": uuid.uuid4(),
                "name": "Sociales y Ciudadanas",
                "description": "Comprende la sociedad y forja tu ciudadanía",
                "icon_url": "/assets/images/subjects/sociales.png",
                "color": "#F59E0B"
            },
            {
                "id": uuid.uuid4(),
                "name": "Inglés",
                "description": "Desbloquea el idioma universal",
                "icon_url": "/assets/images/subjects/ingles.png",
                "color": "#EF4444"
            }
        ]
        
        # Create subject objects
        for subject_data in subjects_data:
            subject = Subject(**subject_data)
            db.add(subject)
        
        # Commit the transaction
        db.commit()
        print(f"✅ Successfully populated {len(subjects_data)} subjects")
        
        # Verify subjects were created
        count = db.query(Subject).count()
        print(f"📊 Total subjects in database: {count}")
        
        # List all subjects
        all_subjects = db.query(Subject).all()
        for subject in all_subjects:
            print(f"  - {subject.name}: {subject.description}")
        
    except Exception as e:
        print(f"❌ Error populating subjects: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_subjects()