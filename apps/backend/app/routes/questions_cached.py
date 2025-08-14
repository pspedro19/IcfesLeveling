from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import random
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.question import Question
from ..models.subject import Subject
from ..schemas.question import QuestionResponse, QuestionCreate, QuestionUpdate
from ..services.cache_service import cache_service

router = APIRouter(prefix="/questions/cached", tags=["questions-cached"])
logger = logging.getLogger(__name__)

@router.get("/subject/{subject_id}", response_model=List[QuestionResponse])
async def get_cached_questions_by_subject(
    subject_id: str,
    difficulty: Optional[int] = Query(None, ge=1, le=10),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get questions by subject with caching"""
    # Generate cache key
    cache_key = f"questions:subject:{subject_id}:diff:{difficulty or 'all'}:limit:{limit}"
    
    # Try to get from cache
    cached_questions = cache_service.get(cache_key)
    if cached_questions:
        logger.info(f"Cache hit for questions: {cache_key}")
        return cached_questions
    
    # If not in cache, fetch from database
    logger.info(f"Cache miss for questions: {cache_key}")
    
    # Verify subject exists
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    
    # Build query
    query = db.query(Question).filter(Question.subject_id == subject_id)
    
    if difficulty is not None:
        query = query.filter(Question.difficulty == difficulty)
    
    # Get questions
    questions = query.limit(limit).all()
    
    # Shuffle questions
    random.shuffle(questions)
    
    # Convert to response model
    question_responses = [
        QuestionResponse(
            id=str(q.id),
            subject_id=str(q.subject_id),
            text=q.text,
            options=q.options,
            correct_answer=q.correct_answer,
            difficulty=q.difficulty,
            explanation=q.explanation,
            hint=q.hint,
            created_at=q.created_at,
            updated_at=q.updated_at
        )
        for q in questions
    ]
    
    # Cache the results
    cache_service.set(cache_key, question_responses, ttl=7200)  # 2 hours
    
    return question_responses

@router.get("/random/{subject_id}", response_model=QuestionResponse)
async def get_random_cached_question(
    subject_id: str,
    difficulty: Optional[int] = Query(None, ge=1, le=10),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a random question from cache or database"""
    # First try to get from cached pool
    if difficulty:
        cached_pool = cache_service.get_question_pool(subject_id, difficulty)
        if cached_pool and len(cached_pool) > 0:
            return random.choice(cached_pool)
    
    # If not in cache, fetch from database
    query = db.query(Question).filter(Question.subject_id == subject_id)
    
    if difficulty is not None:
        query = query.filter(Question.difficulty == difficulty)
    
    # Get all questions matching criteria
    questions = query.all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No questions found")
    
    # Cache the pool for future use
    if difficulty:
        question_pool = [
            {
                "id": str(q.id),
                "subject_id": str(q.subject_id),
                "text": q.text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "difficulty": q.difficulty,
                "explanation": q.explanation,
                "hint": q.hint
            }
            for q in questions
        ]
        cache_service.cache_question_pool(subject_id, difficulty, question_pool)
    
    # Return random question
    question = random.choice(questions)
    
    return QuestionResponse(
        id=str(question.id),
        subject_id=str(question.subject_id),
        text=question.text,
        options=question.options,
        correct_answer=question.correct_answer,
        difficulty=question.difficulty,
        explanation=question.explanation,
        hint=question.hint,
        created_at=question.created_at,
        updated_at=question.updated_at
    )

@router.post("/invalidate-cache")
async def invalidate_questions_cache(
    subject_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Invalidate questions cache (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if subject_id:
        # Invalidate specific subject
        pattern = f"questions:subject:{subject_id}:*"
        deleted = cache_service.delete_pattern(pattern)
        
        # Also invalidate question pools
        pool_pattern = f"questions:pool:{subject_id}:*"
        deleted += cache_service.delete_pattern(pool_pattern)
        
        return {"message": f"Invalidated {deleted} cache entries for subject {subject_id}"}
    else:
        # Invalidate all questions cache
        deleted = cache_service.delete_pattern("questions:*")
        return {"message": f"Invalidated {deleted} cache entries"}

@router.get("/cache-stats")
async def get_cache_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get cache statistics for questions (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Get all question cache keys
    subject_keys = cache_service.get_keys("questions:subject:*")
    pool_keys = cache_service.get_keys("questions:pool:*")
    
    # Calculate statistics
    stats = {
        "total_cached_queries": len(subject_keys),
        "total_cached_pools": len(pool_keys),
        "cache_keys": {
            "subject_queries": subject_keys[:10],  # Show first 10
            "question_pools": pool_keys[:10]
        },
        "estimated_memory_usage": f"{(len(subject_keys) + len(pool_keys)) * 10}KB",  # Rough estimate
        "cache_health": cache_service.ping()
    }
    
    return stats