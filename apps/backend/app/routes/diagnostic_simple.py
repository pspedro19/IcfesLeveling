from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..core.database import get_db
from ..models.question import Question
from ..models.subject import Subject

router = APIRouter(prefix="/diagnostic-simple", tags=["diagnostic-simple"])

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"status": "working", "message": "Backend is responding"}

@router.get("/questions/count")
async def get_questions_count_simple(db: Session = Depends(get_db)):
    """Get total questions count for debugging"""
    try:
        total_questions = db.query(Question).count()
        return {
            "status": "success",
            "total_questions": total_questions,
            "backend_connected": True
        }
    except Exception as e:
        return {
            "status": "error", 
            "error": str(e),
            "backend_connected": True
        }

@router.get("/subjects")
async def get_subjects_simple(db: Session = Depends(get_db)):
    """Get all subjects without complex logic"""
    try:
        subjects = db.query(Subject).all()
        return {
            "status": "success",
            "subjects": [
                {
                    "id": str(subject.id),
                    "name": subject.name,
                    "description": subject.description
                }
                for subject in subjects
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

@router.get("/questions/sample")
async def get_sample_questions_simple(
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get sample questions for testing"""
    try:
        questions = db.query(Question).limit(limit).all()
        
        return {
            "status": "success",
            "count": len(questions),
            "questions": [
                {
                    "id": str(q.id),
                    "question_text": q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
                    "has_options": bool(q.options),
                    "correct_answer": q.correct_answer,
                    "difficulty": q.difficulty,
                    "image_url": getattr(q, 'pregunta_imagen', None),
                    "has_options_images": False,
                    "subject_id": str(q.subject_id) if q.subject_id else None
                }
                for q in questions
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "questions": []
        }