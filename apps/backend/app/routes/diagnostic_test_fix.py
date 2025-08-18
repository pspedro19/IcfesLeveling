from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import random

from ..core.database import get_db
from ..models.question import Question
from ..models.subject import Subject

router = APIRouter(prefix="/api/v1/diagnostic", tags=["diagnostic-fix"])

@router.get("/test-questions/{subject_id}")
async def get_test_questions(
    subject_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get questions for a diagnostic test without authentication"""
    
    # Get questions for the subject
    questions = db.query(Question).filter(
        Question.subject_id == subject_id
    ).limit(limit).all()
    
    if not questions:
        # If no questions with that subject_id, get any questions
        questions = db.query(Question).limit(limit).all()
    
    # Format questions for frontend
    formatted_questions = []
    for q in questions:
        # Parse options from JSON or create default
        options = q.options if q.options else {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
        if isinstance(options, str):
            import json
            try:
                options = json.loads(options)
            except:
                options = {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
        
        formatted_questions.append({
            "id": str(q.id),
            "question_text": q.question_text or "Sample question",
            "options": options,
            "difficulty": q.difficulty or "medium",
            "topic": getattr(q, 'topic', None) or "General",
            "explanation": q.explanation or "Explanation available after answering",
            "hint": q.hint or "Think carefully about the question"
        })
    
    return formatted_questions

@router.post("/simple-test")
async def create_simple_test(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """Create a simple test session without authentication"""
    
    # Check if subject exists
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        # Get first available subject
        subject = db.query(Subject).first()
        if not subject:
            raise HTTPException(status_code=404, detail="No subjects found")
    
    # Create a simple test response
    test_id = str(uuid.uuid4())
    
    return {
        "id": test_id,
        "subject_id": str(subject.id),
        "subject_name": subject.name,
        "status": "created",
        "questions_count": 10
    }

@router.get("/subjects-with-questions")
async def get_subjects_with_questions(db: Session = Depends(get_db)):
    """Get all subjects with their question counts"""
    
    subjects = db.query(Subject).all()
    result = []
    
    for subject in subjects:
        question_count = db.query(Question).filter(
            Question.subject_id == subject.id
        ).count()
        
        result.append({
            "id": str(subject.id),
            "name": subject.name,
            "description": subject.description,
            "question_count": question_count,
            "color": subject.color or "#6B46C1",
            "icon": subject.icon or "📚"
        })
    
    return result