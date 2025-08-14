from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.question import (
    QuestionCreate, 
    QuestionResponse, 
    QuestionUpdate,
    QuestionWithStats,
    QuestionValidationRequest,
    QuestionValidationResponse,
    QuestionNavigationGrid
)
from ..models.question import Question, Topic
from ..models.subject import Subject
from ..models.user import User

router = APIRouter(prefix="/questions", tags=["questions"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[QuestionResponse])
async def get_questions(
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    topic_id: Optional[str] = Query(None, description="Filter by topic ID"),
    difficulty: Optional[int] = Query(None, description="Filter by difficulty level"),
    limit: int = Query(50, description="Number of questions to return"),
    offset: int = Query(0, description="Number of questions to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get questions with optional filtering"""
    try:
        query = db.query(Question)
        
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        if topic_id:
            query = query.filter(Question.topic_id == topic_id)
        if difficulty:
            query = query.filter(Question.difficulty == difficulty)
        
        # Only return validated questions
        query = query.filter(Question.is_validated == "validated")
        
        questions = query.offset(offset).limit(limit).all()
        return questions
    except Exception as e:
        logger.error(f"Error fetching questions: {e}")
        raise HTTPException(status_code=500, detail="Error fetching questions")

@router.get("/multimedia", response_model=List[QuestionResponse])
async def get_multimedia_questions(
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    topic_id: Optional[str] = Query(None, description="Filter by topic ID"),
    limit: int = Query(45, description="Number of questions to return (default 45 for exam)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get multimedia questions for exam interface"""
    try:
        query = db.query(Question)
        
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        if topic_id:
            query = query.filter(Question.topic_id == topic_id)
        
        # Only return validated questions
        query = query.filter(Question.is_validated == "validated")
        
        # Order by creation date for consistent ordering
        query = query.order_by(Question.created_at)
        
        questions = query.limit(limit).all()
        return questions
    except Exception as e:
        logger.error(f"Error fetching multimedia questions: {e}")
        raise HTTPException(status_code=500, detail="Error fetching multimedia questions")

@router.get("/navigation-grid", response_model=QuestionNavigationGrid)
async def get_question_navigation_grid(
    subject_id: Optional[str] = Query(None, description="Filter by subject ID"),
    current_question: int = Query(1, description="Current question number"),
    answered_questions: Optional[List[int]] = Query(None, description="List of answered question numbers"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get navigation grid for questions"""
    try:
        query = db.query(Question)
        
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        
        # Only return validated questions
        query = query.filter(Question.is_validated == "validated")
        
        total_questions = query.count()
        
        # Default to 45 questions if none found
        if total_questions == 0:
            total_questions = 45
        
        # Create question states
        question_states = {}
        for i in range(1, total_questions + 1):
            if i == current_question:
                question_states[i] = "current"
            elif answered_questions and i in answered_questions:
                question_states[i] = "answered"
            else:
                question_states[i] = "unanswered"
        
        return QuestionNavigationGrid(
            total_questions=total_questions,
            current_question=current_question,
            answered_questions=answered_questions or [],
            question_states=question_states
        )
    except Exception as e:
        logger.error(f"Error generating navigation grid: {e}")
        raise HTTPException(status_code=500, detail="Error generating navigation grid")

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific question by ID"""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return question
    except Exception as e:
        logger.error(f"Error fetching question {question_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching question")

@router.post("/", response_model=QuestionResponse)
async def create_question(
    question_data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new question"""
    try:
        # Validate question data
        question = Question(**question_data.dict())
        validation_errors = question.validate_question()
        
        if validation_errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Question validation failed: {', '.join(validation_errors)}"
            )
        
        # Verify topic and subject exist
        topic = db.query(Topic).filter(Topic.id == question.topic_id).first()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
        
        subject = db.query(Subject).filter(Subject.id == question.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        db.add(question)
        db.commit()
        db.refresh(question)
        
        logger.info(f"Question created: {question.id}")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating question: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating question")

@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: str,
    question_data: QuestionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing question"""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Update fields
        update_data = question_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(question, field, value)
        
        # Validate updated question
        validation_errors = question.validate_question()
        if validation_errors:
            raise HTTPException(
                status_code=400, 
                detail=f"Question validation failed: {', '.join(validation_errors)}"
            )
        
        db.commit()
        db.refresh(question)
        
        logger.info(f"Question updated: {question.id}")
        return question
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question {question_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating question")

@router.delete("/{question_id}")
async def delete_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a question"""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        db.delete(question)
        db.commit()
        
        logger.info(f"Question deleted: {question_id}")
        return {"message": "Question deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting question {question_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting question")

@router.post("/validate", response_model=QuestionValidationResponse)
async def validate_question(
    validation_request: QuestionValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate question data without saving"""
    try:
        # Create temporary question object for validation
        temp_question = Question(
            pregunta_texto=validation_request.pregunta_texto,
            pregunta_imagen=validation_request.pregunta_imagen,
            opcion_a_texto=validation_request.opcion_a_texto,
            opcion_a_imagen=validation_request.opcion_a_imagen,
            opcion_b_texto=validation_request.opcion_b_texto,
            opcion_b_imagen=validation_request.opcion_b_imagen,
            opcion_c_texto=validation_request.opcion_c_texto,
            opcion_c_imagen=validation_request.opcion_c_imagen,
            opcion_d_texto=validation_request.opcion_d_texto,
            opcion_d_imagen=validation_request.opcion_d_imagen,
            respuesta_correcta=validation_request.respuesta_correcta
        )
        
        errors = temp_question.validate_question()
        warnings = []
        suggestions = []
        
        # Add suggestions for improvement
        if not validation_request.pregunta_imagen and validation_request.pregunta_texto:
            suggestions.append("Consider adding an image to make the question more engaging")
        
        if not any([validation_request.opcion_a_imagen, validation_request.opcion_b_imagen, 
                   validation_request.opcion_c_imagen, validation_request.opcion_d_imagen]):
            suggestions.append("Consider adding images to some options for better visualization")
        
        return QuestionValidationResponse(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            suggestions=suggestions
        )
    except Exception as e:
        logger.error(f"Error validating question: {e}")
        raise HTTPException(status_code=500, detail="Error validating question")

@router.get("/stats/{question_id}", response_model=QuestionWithStats)
async def get_question_stats(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed statistics for a question"""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Calculate additional stats
        success_rate = question.power_stats.get("success_rate", 0.0) if question.power_stats else 0.0
        difficulty_rating = question.get_difficulty_rating()
        
        return QuestionWithStats(
            **question.__dict__,
            success_rate=success_rate,
            difficulty_rating=difficulty_rating
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching question stats {question_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching question stats")

@router.post("/{question_id}/update-stats")
async def update_question_stats(
    question_id: str,
    response_time_ms: int,
    is_correct: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update question usage statistics"""
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        question.update_usage_stats(response_time_ms, is_correct)
        db.commit()
        
        logger.info(f"Question stats updated: {question_id}")
        return {"message": "Question stats updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating question stats {question_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating question stats") 