#!/usr/bin/env python
"""
Database-enabled startup script that provides key endpoints with database connectivity
"""
import os
import sys
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import uvicorn

# Set up database connection - use original credentials from .env
DATABASE_URL = "postgresql://gameplay:gameplay123@localhost:5433/gameplay_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create FastAPI app
app = FastAPI(title="ICFES Leveling API - Database Enabled", version="1.0.0")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "backend", "database": "connected"}

@app.get("/")
def root():
    return {"message": "ICFES Leveling API with Database is running", "database_url": DATABASE_URL.replace("gameplay123", "***")}

# Database connection test
@app.get("/db/test")
def test_database(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1 as test")).fetchone()
        return {"status": "success", "test_query": result[0] if result else None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

# Get subjects from database
@app.get("/subjects/dynamic")
def get_dynamic_subjects(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT id, nombre, alias, created_at 
            FROM subjects 
            ORDER BY nombre
        """)).fetchall()
        
        subjects = []
        for row in result:
            subjects.append({
                "id": str(row[0]),
                "name": row[1],
                "alias": row[2] if row[2] else row[1].lower().replace(" ", "_"),
                "created_at": row[3].isoformat() if row[3] else None
            })
        
        return {"subjects": subjects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch subjects: {str(e)}")

# Get questions by subject
@app.get("/questions/by-subject/{subject_id}")
def get_questions_by_subject(subject_id: str, limit: int = 10, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT q.id, q.pregunta_texto, q.opcion_a_texto, q.opcion_b_texto, 
                   q.opcion_c_texto, q.opcion_d_texto, q.respuesta_correcta, 
                   q.materia_id, s.nombre as subject_name
            FROM questions q
            JOIN subjects s ON q.materia_id = s.id
            WHERE q.materia_id = :subject_id
            ORDER BY RANDOM()
            LIMIT :limit
        """), {"subject_id": subject_id, "limit": limit}).fetchall()
        
        questions = []
        for row in result:
            questions.append({
                "id": str(row[0]),
                "question_text": row[1],
                "option_a": row[2],
                "option_b": row[3],
                "option_c": row[4],
                "option_d": row[5],
                "correct_answer": row[6],
                "subject_id": str(row[7]),
                "subject_name": row[8]
            })
        
        return {"questions": questions, "count": len(questions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions: {str(e)}")

# Get all questions (with pagination)
@app.get("/questions")
def get_questions(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    try:
        result = db.execute(text("""
            SELECT q.id, q.pregunta_texto, q.opcion_a_texto, q.opcion_b_texto, 
                   q.opcion_c_texto, q.opcion_d_texto, q.respuesta_correcta, 
                   q.materia_id, s.nombre as subject_name
            FROM questions q
            JOIN subjects s ON q.materia_id = s.id
            ORDER BY q.created_at DESC
            OFFSET :skip LIMIT :limit
        """), {"skip": skip, "limit": limit}).fetchall()
        
        questions = []
        for row in result:
            questions.append({
                "id": str(row[0]),
                "question_text": row[1],
                "option_a": row[2],
                "option_b": row[3],
                "option_c": row[4],
                "option_d": row[5],
                "correct_answer": row[6],
                "subject_id": str(row[7]),
                "subject_name": row[8]
            })
        
        return {"questions": questions, "count": len(questions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questions: {str(e)}")

# Dashboard endpoint - basic user stats
@app.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    try:
        # Get total counts
        subjects_count = db.execute(text("SELECT COUNT(*) FROM subjects")).scalar()
        questions_count = db.execute(text("SELECT COUNT(*) FROM questions")).scalar()
        users_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        
        return {
            "total_subjects": subjects_count,
            "total_questions": questions_count,
            "total_users": users_count,
            "status": "active"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard stats: {str(e)}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ICFES LEVELING BACKEND WITH DATABASE")
    print("="*60)
    print(f"Database: {DATABASE_URL.replace('gameplay123', '***')}")
    print("API: http://localhost:8001")
    print("Docs: http://localhost:8001/docs")
    print("Test DB: http://localhost:8001/db/test")
    print("Dashboard: http://localhost:8001/dashboard/stats")
    print("Subjects: http://localhost:8001/subjects/dynamic")
    print("Questions: http://localhost:8001/questions")
    print("="*60 + "\n")
    
    # Test database connection on startup
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful!")
    except Exception as e:
        print(f"Database connection failed: {e}")
        print("Make sure PostgreSQL is running on localhost:5433")
    
    # Run the server on port 8001 to avoid conflicts
    uvicorn.run(app, host="0.0.0.0", port=8001)