from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import random

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.question import QuestionResponse, QuestionCreate
from ..models.user import User
from ..models.question import Question, Subject, Topic

router = APIRouter(prefix="/questions", tags=["questions"])

@router.get("/random", response_model=QuestionResponse)
async def get_random_question(
    subject_id: Optional[str] = Query(None, description="ID de la materia"),
    difficulty: Optional[int] = Query(None, ge=1, le=10, description="Nivel de dificultad"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener una pregunta aleatoria adaptativa"""
    query = db.query(Question)
    
    if subject_id:
        query = query.filter(Question.subject_id == subject_id)
    
    if difficulty:
        query = query.filter(Question.difficulty == difficulty)
    else:
        # Adaptar dificultad basada en el nivel del usuario
        user_level = current_user.level
        if user_level <= 10:
            difficulty_range = (1, 3)
        elif user_level <= 25:
            difficulty_range = (2, 5)
        elif user_level <= 50:
            difficulty_range = (3, 7)
        else:
            difficulty_range = (5, 10)
        
        query = query.filter(Question.difficulty.between(*difficulty_range))
    
    questions = query.all()
    
    if not questions:
        raise HTTPException(status_code=404, detail="No hay preguntas disponibles")
    
    # Seleccionar pregunta aleatoria
    question = random.choice(questions)
    return question

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener una pregunta específica"""
    question = db.query(Question).filter(Question.id == question_id).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    return question

@router.get("/subjects", response_model=List[dict])
async def get_subjects(db: Session = Depends(get_db)):
    """Obtener todas las materias"""
    subjects = db.query(Subject).all()
    return [
        {
            "id": str(subject.id),
            "name": subject.name,
            "description": subject.description,
            "icon_url": subject.icon_url,
            "color": subject.color
        }
        for subject in subjects
    ]

@router.get("/topics", response_model=List[dict])
async def get_topics(
    subject_id: Optional[str] = Query(None, description="ID de la materia"),
    db: Session = Depends(get_db)
):
    """Obtener temas por materia"""
    query = db.query(Topic)
    
    if subject_id:
        query = query.filter(Topic.subject_id == subject_id)
    
    topics = query.all()
    return [
        {
            "id": str(topic.id),
            "name": topic.name,
            "description": topic.description,
            "difficulty_level": topic.difficulty_level,
            "subject_id": str(topic.subject_id)
        }
        for topic in topics
    ]

@router.get("/stats/user", response_model=dict)
async def get_user_question_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de preguntas del usuario"""
    # Implementar lógica para obtener estadísticas
    # Por ahora retornamos datos mock
    return {
        "total_answered": 150,
        "correct_answers": 120,
        "accuracy": 0.8,
        "streak_current": 5,
        "streak_best": 12,
        "subjects_progress": {
            "matemáticas": 0.75,
            "ciencias": 0.68,
            "lenguaje": 0.82,
            "sociales": 0.71
        }
    } 