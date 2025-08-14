from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import random
import uuid

from ..core.database import get_db
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.question import Question, Topic
from ..models.subject import Subject
from ..models.user import User
from ..schemas.diagnostic_test import (
    DiagnosticTestCreate, 
    DiagnosticTestSubmit, 
    DiagnosticTestAnalysis,
    DIAGNOSTIC_TEST_CONFIGS
)
from ..services.diagnostic_service import DiagnosticService
from ..services.diagnostic_analytics_service import DiagnosticAnalyticsService

router = APIRouter(prefix="/diagnostic-public", tags=["diagnostic-public"])

@router.get("/subjects")
async def get_subjects_public(db: Session = Depends(get_db)):
    """Get all subjects without authentication for testing"""
    subjects = db.query(Subject).all()
    return [
        {
            "id": str(subject.id),
            "name": subject.name,
            "description": subject.description,
            "config": {
                "total_questions": 45,
                "time_limit_minutes": 60,
                "topics": ["Álgebra", "Geometría", "Estadística", "Cálculo"]
            }
        }
        for subject in subjects
    ]

@router.post("/tests")
async def create_diagnostic_test_public(
    test_data: DiagnosticTestCreate,
    db: Session = Depends(get_db)
):
    """Create a diagnostic test without authentication for testing"""
    try:
        # Create a temporary test user or use a default one
        default_user = db.query(User).first()
        if not default_user:
            # Create a test user
            default_user = User(
                id=uuid.uuid4(),
                email="test@example.com",
                username="test_user",
                hashed_password="dummy_hash",
                is_active=True
            )
            db.add(default_user)
            db.commit()
            db.refresh(default_user)
        
        diagnostic_service = DiagnosticService(db)
        test = diagnostic_service.create_diagnostic_test(
            user_id=str(default_user.id),
            subject_id=test_data.subject_id,
            test_type=test_data.test_type
        )
        
        return {
            "id": str(test.id),
            "user_id": str(test.user_id),
            "subject_id": str(test.subject_id),
            "test_type": test.test_type,
            "status": test.status,
            "created_at": test.created_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test: {str(e)}")

@router.get("/tests/{test_id}/questions")
async def get_diagnostic_questions_public(
    test_id: str,
    db: Session = Depends(get_db)
):
    """Get questions for a diagnostic test without authentication for testing"""
    try:
        diagnostic_service = DiagnosticService(db)
        
        # Get the test
        test = diagnostic_service.get_diagnostic_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Get subject and config
        subject = db.query(Subject).filter(Subject.id == test.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
            
        config = diagnostic_service.get_diagnostic_test_config(subject.name)
        
        # Get questions
        questions = diagnostic_service.get_diagnostic_questions(
            subject_id=str(test.subject_id),
            limit=config["total_questions"]
        )
        
        print(f"Found {len(questions)} questions for subject {subject.name}")
        
        return [
            {
                "id": str(q.id),
                "question_text": q.question_text,
                "options": q.options,
                "subject": subject.name,
                "topic": q.topic.name if q.topic else "General",
                "difficulty": q.difficulty,
                "hint": q.hint,
                "image_url": getattr(q, 'pregunta_imagen', None),
                "options_images": {}
            }
            for q in questions
        ]
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting questions: {str(e)}")

@router.post("/tests/{test_id}/submit")
async def submit_diagnostic_test_public(
    test_id: str,
    submit_data: DiagnosticTestSubmit,
    db: Session = Depends(get_db)
):
    """Submit diagnostic test answers without authentication for testing"""
    try:
        diagnostic_service = DiagnosticService(db)
        
        # Verify test exists
        test = diagnostic_service.get_diagnostic_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Convert answers to expected format
        answers = [
            {
                "question_id": answer.question_id,
                "user_answer": answer.user_answer,
                "response_time_ms": answer.response_time_ms
            }
            for answer in submit_data.answers
        ]
        
        # Process answers
        analysis = diagnostic_service.submit_diagnostic_test(test_id, answers)
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting test: {str(e)}")

@router.get("/questions/count")
async def get_questions_count(db: Session = Depends(get_db)):
    """Get total questions count for debugging"""
    try:
        total_questions = db.query(Question).count()
        questions_by_subject = {}
        
        subjects = db.query(Subject).all()
        for subject in subjects:
            count = db.query(Question).filter(Question.subject_id == subject.id).count()
            questions_by_subject[subject.name] = count
        
        return {
            "total_questions": total_questions,
            "by_subject": questions_by_subject
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting count: {str(e)}")

@router.get("/questions/sample/{subject_id}")
async def get_sample_questions(
    subject_id: str,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Get sample questions for debugging"""
    try:
        questions = db.query(Question).filter(
            Question.subject_id == subject_id
        ).limit(limit).all()
        
        return [
            {
                "id": str(q.id),
                "question_text": q.question_text[:100] + "..." if len(q.question_text) > 100 else q.question_text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "difficulty": q.difficulty,
                "topic": q.topic.name if q.topic else "General",
                "image_url": getattr(q, 'pregunta_imagen', None),
                "has_options_images": False
            }
            for q in questions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sample: {str(e)}")