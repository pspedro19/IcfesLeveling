from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from ..core.database import get_db
from ..models.subject import Subject
from ..models.question import Question

router = APIRouter(prefix="/api/v1", tags=["subjects-fix"])

@router.get("/subjects-simple")
async def get_subjects_simple(db: Session = Depends(get_db)):
    """Get all subjects without assets endpoint"""
    subjects = db.query(Subject).all()
    
    result = []
    for subject in subjects:
        # Count questions for this subject
        question_count = db.query(Question).filter(
            Question.subject_id == subject.id
        ).count()
        
        result.append({
            "id": str(subject.id),
            "name": subject.name,
            "description": subject.description or f"Prepárate para {subject.name}",
            "color": subject.color or "#6B46C1",
            "icon": subject.icon or "📚",
            "question_count": question_count,
            "image": f"/images/subjects/{subject.name.lower().replace(' ', '_')}.png"
        })
    
    return result

@router.get("/subjects/{subject_id}/info")
async def get_subject_info(subject_id: str, db: Session = Depends(get_db)):
    """Get subject info without assets"""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    question_count = db.query(Question).filter(
        Question.subject_id == subject.id
    ).count()
    
    return {
        "id": str(subject.id),
        "name": subject.name,
        "description": subject.description or f"Prepárate para {subject.name}",
        "color": subject.color or "#6B46C1",
        "icon": subject.icon or "📚",
        "question_count": question_count,
        "topics": [],  # Add topics if needed
        "difficulty_levels": ["Básico", "Intermedio", "Avanzado"]
    }