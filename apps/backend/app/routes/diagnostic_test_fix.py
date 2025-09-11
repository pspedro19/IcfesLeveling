from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
import random
import os

from ..core.database import get_db
from ..models.question import Question
from ..models.subject import Subject

router = APIRouter(prefix="/api/v1/diagnostic", tags=["diagnostic-fix"])

def convert_image_path_to_url(image_path: str, request: Request) -> str:
    """Convert database image path to API URL"""
    if not image_path:
        return None
    
    # Clean the path - remove leading backslashes and convert to forward slashes
    clean_path = image_path.strip().lstrip('\\').replace('\\', '/')
    
    # Remove any leading database/seed_data prefix if it exists
    if clean_path.startswith('database/seed_data'):
        clean_path = clean_path.replace('database/seed_data', '', 1).lstrip('/')
    
    # Build the complete URL
    base_url = str(request.base_url).rstrip('/')
    api_url = f"{base_url}/api/v1/images/{clean_path}"
    
    return api_url

@router.get("/test-questions/{subject_id}")
async def get_test_questions(
    subject_id: str,
    request: Request,
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
        
        # Handle question text - prioritize pregunta_texto over question_text
        question_text = q.pregunta_texto or q.question_text or "Sample question"
        
        # Handle question image
        pregunta_imagen_url = convert_image_path_to_url(q.pregunta_imagen, request)
        
        # Handle option texts - check new fields first, fallback to legacy
        option_texts = {
            "A": q.opcion_a_texto or options.get("A", "Option A"),
            "B": q.opcion_b_texto or options.get("B", "Option B"), 
            "C": q.opcion_c_texto or options.get("C", "Option C"),
            "D": q.opcion_d_texto or options.get("D", "Option D")
        }
        
        # Handle option images
        option_images = {
            "A": convert_image_path_to_url(q.opcion_a_imagen, request),
            "B": convert_image_path_to_url(q.opcion_b_imagen, request),
            "C": convert_image_path_to_url(q.opcion_c_imagen, request),
            "D": convert_image_path_to_url(q.opcion_d_imagen, request)
        }
        
        formatted_questions.append({
            "id": str(q.id),
            "question_text": question_text,
            "pregunta_texto": question_text,  # Also include new field name for compatibility
            "pregunta_imagen": pregunta_imagen_url,
            "image_url": pregunta_imagen_url,  # Legacy field name for compatibility
            "options": option_texts,
            "opcion_a_texto": option_texts["A"],
            "opcion_b_texto": option_texts["B"],
            "opcion_c_texto": option_texts["C"],
            "opcion_d_texto": option_texts["D"],
            "opcion_a_imagen": option_images["A"],
            "opcion_b_imagen": option_images["B"],
            "opcion_c_imagen": option_images["C"],
            "opcion_d_imagen": option_images["D"],
            "difficulty": q.difficulty or 1,
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