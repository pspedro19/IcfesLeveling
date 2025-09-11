from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
import random
import uuid

from ..core.database import get_db
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.topic import Topic
from ..models.question import Question
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

@router.get("/diagnostic-questions/{subject_id}")
async def get_diagnostic_test_questions(
    subject_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get properly formatted questions for diagnostic test interface"""
    try:
        questions = db.query(Question).filter(
            Question.subject_id == subject_id
        ).limit(limit).all()
        
        if not questions:
            raise HTTPException(status_code=404, detail="No questions found for this subject")
        
        formatted_questions = []
        for q in questions:
            # Get the question text (prefer pregunta_texto over legacy field)
            question_text = q.pregunta_texto or q.question_text or ""
            
            # Get question image URL
            question_image_url = q.pregunta_imagen
            
            # Format options with both text and images
            options_data = {}
            option_images = {}
            
            for letter in ['a', 'b', 'c', 'd']:
                option_text = getattr(q, f'opcion_{letter}_texto')
                option_image = getattr(q, f'opcion_{letter}_imagen')
                
                if option_text or option_image:
                    options_data[letter.upper()] = option_text or f"Opción {letter.upper()}"
                    if option_image:
                        option_images[letter.upper()] = option_image
            
            # Fallback to legacy options if no new format options found
            if not options_data and q.options:
                if isinstance(q.options, dict):
                    options_data = q.options
                elif isinstance(q.options, list):
                    for i, opt in enumerate(q.options):
                        options_data[chr(65 + i)] = opt  # A, B, C, D
            
            formatted_question = {
                "id": str(q.id),
                "question_text": question_text,
                "pregunta_texto": question_text,  # For compatibility
                "image_url": question_image_url,
                "pregunta_imagen": question_image_url,  # For compatibility
                "options": options_data,
                "option_images": option_images,  # Images for options
                "correct_answer": (q.respuesta_correcta or q.correct_answer or "A").upper(),
                "difficulty": q.difficulty or 1,
                "hint": q.hint,
                "topic": {
                    "name": q.topic.name if q.topic else "General",
                    "description": getattr(q.topic, 'description', '') if q.topic else ''
                },
                "subject_id": str(q.subject_id),
                # Explanation fields
                "explicacion_respuesta": getattr(q, 'explicacion_respuesta', None),
                "error_comun": getattr(q, 'error_comun', None)
            }
            
            formatted_questions.append(formatted_question)
        
        return formatted_questions
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting diagnostic questions: {str(e)}")

@router.post("/diagnostic-questions/submit-answer")
async def submit_diagnostic_answer(
    answer_data: dict,
    db: Session = Depends(get_db)
):
    """Submit a single diagnostic test answer and save to database"""
    try:
        question_id = answer_data.get('question_id')
        user_answer = answer_data.get('user_answer', '').upper()
        response_time_ms = answer_data.get('response_time_ms', 0)
        test_id = answer_data.get('test_id', 'diagnostic_test')
        
        # Verify question exists
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Check if answer is correct
        correct_answer = (question.respuesta_correcta or question.correct_answer or "A").upper()
        is_correct = user_answer == correct_answer
        
        # Create or find user (for guest mode, create a temporary user)
        user = db.query(User).first()  # Use first available user for testing
        if not user:
            # Create a test user
            user = User(
                id=uuid.uuid4(),
                email="diagnostic_test@example.com",
                username="diagnostic_user",
                hashed_password="dummy_hash",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Save the answer to diagnostic_test_answers table if it exists
        try:
            from ..models.diagnostic_test import DiagnosticTestAnswer
            
            # Check if answer already exists for this question
            existing_answer = db.query(DiagnosticTestAnswer).filter(
                DiagnosticTestAnswer.question_id == question_id,
                DiagnosticTestAnswer.test_id == test_id
            ).first()
            
            if existing_answer:
                # Update existing answer
                existing_answer.user_answer = user_answer
                existing_answer.response_time_ms = response_time_ms
                existing_answer.is_correct = is_correct
                existing_answer.answered_at = datetime.utcnow()
            else:
                # Create new answer
                answer_record = DiagnosticTestAnswer(
                    id=uuid.uuid4(),
                    test_id=test_id,
                    question_id=question_id,
                    user_answer=user_answer,
                    response_time_ms=response_time_ms,
                    is_correct=is_correct,
                    answered_at=datetime.utcnow()
                )
                db.add(answer_record)
            
            db.commit()
            
        except ImportError:
            # If DiagnosticTestAnswer model doesn't exist, just log the answer
            print(f"Answer saved (log only): Q{question_id} = {user_answer} ({'✓' if is_correct else '✗'})")
        
        # Get explanation and error information
        explicacion_respuesta = getattr(question, 'explicacion_respuesta', None)
        error_comun = getattr(question, 'error_comun', None)
        
        return {
            "success": True,
            "is_correct": is_correct,
            "correct_answer": correct_answer,
            "user_answer": user_answer,
            "feedback": "¡Correcto!" if is_correct else f"Incorrecto. La respuesta correcta es {correct_answer}",
            "explicacion_respuesta": explicacion_respuesta,
            "error_comun": error_comun if not is_correct else None,  # Only show error for wrong answers
            "saved": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error submitting answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error submitting answer: {str(e)}")

@router.post("/tests/{test_id}/questions/{question_id}/hint")
async def request_hint_public(
    test_id: str,
    question_id: str,
    hint_level: int,
    db: Session = Depends(get_db)
):
    """
    Request a progressive hint for a specific question during diagnostic test
    
    Args:
        test_id: UUID of the diagnostic test
        question_id: UUID of the question
        hint_level: Level of hint requested (1, 2, or 3)
    
    Returns:
        Dictionary containing the hint text and tracking information
    """
    try:
        # Validate hint level
        if hint_level not in [1, 2, 3]:
            raise HTTPException(status_code=400, detail="Hint level must be 1, 2, or 3")
        
        # Get the question
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Get the diagnostic test
        test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        if not test:
            raise HTTPException(status_code=404, detail="Diagnostic test not found")
        
        # Get the progressive hint
        hint_text = question.get_progressive_hint(hint_level)
        
        # Check if there's an existing answer record for this question in this test
        existing_answer = db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id,
            DiagnosticTestAnswer.question_id == question_id
        ).first()
        
        if existing_answer:
            # Update existing answer with hint usage
            if not existing_answer.hint_levels_requested:
                existing_answer.hint_levels_requested = []
            
            if hint_level not in existing_answer.hint_levels_requested:
                existing_answer.hint_levels_requested.append(hint_level)
                existing_answer.hints_used = len(existing_answer.hint_levels_requested)
        else:
            # Create a placeholder answer record to track hints before the actual answer is submitted
            new_answer = DiagnosticTestAnswer(
                diagnostic_test_id=test_id,
                question_id=question_id,
                user_answer="",  # Will be updated when actual answer is submitted
                is_correct=False,  # Will be updated when actual answer is submitted
                response_time_ms=0,  # Will be updated when actual answer is submitted
                hints_used=1,
                hint_levels_requested=[hint_level],
                topic_id=question.topic_id
            )
            db.add(new_answer)
        
        db.commit()
        
        # Log hint usage for analytics
        print(f"Hint requested - Test: {test_id}, Question: {question_id}, Level: {hint_level}")
        
        return {
            "success": True,
            "hint": hint_text,
            "hint_level": hint_level,
            "total_hints_used": existing_answer.hints_used if existing_answer else 1,
            "available_hints": {
                "level_1": bool(question.pista_1),
                "level_2": bool(question.pista_2),
                "level_3": bool(question.pista_3)
            },
            "message": f"Pista nivel {hint_level} proporcionada"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error requesting hint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error requesting hint: {str(e)}")

@router.get("/questions/{question_id}/hints-available")
async def check_hints_available_public(
    question_id: str,
    db: Session = Depends(get_db)
):
    """
    Check which hint levels are available for a specific question
    
    Args:
        question_id: UUID of the question
    
    Returns:
        Dictionary indicating which hint levels have content
    """
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        return {
            "question_id": question_id,
            "hints_available": {
                "level_1": {
                    "available": bool(question.pista_1),
                    "preview": question.pista_1[:50] + "..." if question.pista_1 and len(question.pista_1) > 50 else question.pista_1
                },
                "level_2": {
                    "available": bool(question.pista_2),
                    "preview": question.pista_2[:50] + "..." if question.pista_2 and len(question.pista_2) > 50 else question.pista_2
                },
                "level_3": {
                    "available": bool(question.pista_3),
                    "preview": question.pista_3[:50] + "..." if question.pista_3 and len(question.pista_3) > 50 else question.pista_3
                }
            },
            "total_available": sum([1 for hint in [question.pista_1, question.pista_2, question.pista_3] if hint])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error checking hints availability: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking hints availability: {str(e)}")