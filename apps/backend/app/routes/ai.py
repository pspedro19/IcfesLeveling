from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func # New import
from typing import Optional, List, Dict, Any
import redis
import json
import hashlib
import openai
import asyncio
from datetime import datetime, timedelta
import numpy as np
import logging
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.config import settings
from ..models.user import User
from ..models.question import Question
from ..models.ai_explanation import AIExplanation
from ..models.ai_tutoring_session import AITutoringSession, AILearningProgress
from ..services.ai_explanation_engine import ai_explanation_engine
from ..middleware.rate_limit import rate_limit

router = APIRouter(prefix="/ai", tags=["ai"])
logger = logging.getLogger(__name__)

# Conexión a Redis para cache
redis_client = redis.from_url(settings.REDIS_URL)

# OpenAI client initialization
openai_client = None
if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
    openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

class ChatRequest(BaseModel):
    message: str
    question_id: Optional[str] = None
    subject_id: Optional[int] = None
    context_type: Optional[str] = "general"  # "explanation", "concept", "strategy", "hint"

class AITutoringResponse(BaseModel):
    response: str
    follow_up_questions: List[str]
    confidence_score: float
    related_resources: List[Dict[str, Any]]
    suggested_actions: List[str]

class HintRequest(BaseModel):
    question_id: str
    difficulty_level: Optional[str] = "medium"
    previous_attempts: Optional[int] = 0

class LearningPathRequest(BaseModel):
    subject_id: int
    current_level: Optional[str] = "intermediate"
    focus_areas: Optional[List[str]] = []

class ComprehensiveExplanationRequest(BaseModel):
    question_id: str
    user_answer: str
    attempt_number: Optional[int] = 1
    previous_hints_used: Optional[List[str]] = []

class TutoringFeedbackRequest(BaseModel):
    session_id: str
    satisfaction_rating: Optional[int] = None  # 1-5
    helpfulness_rating: Optional[int] = None  # 1-5
    additional_feedback: Optional[str] = None

class ProgressiveLearningRequest(BaseModel):
    question_id: str
    hint_level: int
    previous_attempts: Optional[int] = 0

@router.post("/explain")
@rate_limit(limit=60, window=60)
async def get_ai_explanation(
    question_id: str,
    user_answer: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener explicación de IA para una pregunta"""
    # Obtener pregunta
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    # Crear hash para cache
    cache_key = f"ai_explanation:{hashlib.sha256(f'{question_id}:{user_answer}'.encode()).hexdigest()}"
    
    # Verificar cache
    cached_explanation = redis_client.get(cache_key)
    if cached_explanation:
        return json.loads(cached_explanation)
    
    # Verificar si la respuesta es correcta
    is_correct = user_answer == question.correct_answer
    
    # Generar explicación
    if is_correct:
        explanation_text = f"¡Excelente! Tu respuesta '{user_answer}' es correcta. {question.explanation or 'Has demostrado un buen entendimiento del tema.'}"
    else:
        explanation_text = f"Tu respuesta '{user_answer}' no es correcta. La respuesta correcta es '{question.correct_answer}'. {question.explanation or 'Te recomiendo revisar este tema.'}"
    
    # Crear explicación en base de datos
    ai_explanation = AIExplanation(
        user_id=current_user.id,
        question_id=question_id,
        explanation_text=explanation_text,
        explanation_type="wrong_answer" if not is_correct else "correct_answer",
        tokens_used=len(explanation_text.split()),
        response_time_ms=100  # Mock response time
    )
    
    db.add(ai_explanation)
    db.commit()
    
    # Guardar en cache
    explanation_data = {
        "explanation": explanation_text,
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "hint": question.hint
    }
    
    redis_client.setex(cache_key, 60 * 60 * 24 * settings.AI_CACHE_TTL_DAYS, json.dumps(explanation_data))
    
    return explanation_data

@router.post("/study-plan")
@rate_limit(limit=100, window=60)
async def get_study_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener plan de estudio personalizado"""
    # Crear hash para cache
    cache_key = f"study_plan:{current_user.id}"
    
    # Verificar cache
    cached_plan = redis_client.get(cache_key)
    if cached_plan:
        return json.loads(cached_plan)
    
    # Generar plan de estudio basado en el nivel del usuario
    user_level = current_user.level
    
    if user_level <= 10:
        plan = {
            "title": "Plan de Estudio para Principiantes",
            "description": "Enfócate en los fundamentos básicos",
            "missions": [
                {
                    "id": 1,
                    "title": "Dominar Operaciones Básicas",
                    "description": "Completa 10 preguntas de matemáticas básicas",
                    "subject": "matemáticas",
                    "difficulty": 1,
                    "reward": 50
                },
                {
                    "id": 2,
                    "title": "Comprensión de Lectura",
                    "description": "Responde 5 preguntas de lenguaje correctamente",
                    "subject": "lenguaje",
                    "difficulty": 1,
                    "reward": 40
                },
                {
                    "id": 3,
                    "title": "Conceptos Científicos",
                    "description": "Aprende 3 conceptos básicos de ciencias",
                    "subject": "ciencias",
                    "difficulty": 1,
                    "reward": 45
                }
            ]
        }
    elif user_level <= 25:
        plan = {
            "title": "Plan de Estudio Intermedio",
            "description": "Profundiza en temas más complejos",
            "missions": [
                {
                    "id": 1,
                    "title": "Álgebra Básica",
                    "description": "Resuelve 8 ecuaciones de primer grado",
                    "subject": "matemáticas",
                    "difficulty": 3,
                    "reward": 80
                },
                {
                    "id": 2,
                    "title": "Análisis Literario",
                    "description": "Analiza 3 textos literarios",
                    "subject": "lenguaje",
                    "difficulty": 3,
                    "reward": 75
                },
                {
                    "id": 3,
                    "title": "Experimentos Científicos",
                    "description": "Comprende 5 experimentos básicos",
                    "subject": "ciencias",
                    "difficulty": 3,
                    "reward": 70
                }
            ]
        }
    else:
        plan = {
            "title": "Plan de Estudio Avanzado",
            "description": "Desafía tus límites con temas complejos",
            "missions": [
                {
                    "id": 1,
                    "title": "Cálculo Diferencial",
                    "description": "Resuelve 6 problemas de derivadas",
                    "subject": "matemáticas",
                    "difficulty": 7,
                    "reward": 120
                },
                {
                    "id": 2,
                    "title": "Análisis Crítico",
                    "description": "Realiza análisis crítico de 4 textos complejos",
                    "subject": "lenguaje",
                    "difficulty": 7,
                    "reward": 110
                },
                {
                    "id": 3,
                    "title": "Investigación Científica",
                    "description": "Comprende 3 investigaciones científicas",
                    "subject": "ciencias",
                    "difficulty": 7,
                    "reward": 115
                }
            ]
        }
    
    # Guardar en cache por 24 horas
    redis_client.setex(cache_key, 60 * 60 * 24, json.dumps(plan))
    
    return plan

@router.get("/hint/{question_id}")
@rate_limit(limit=100, window=60)
async def get_hint(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener pista para una pregunta"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    if not question.hint:
        raise HTTPException(status_code=404, detail="No hay pista disponible para esta pregunta")
    
    return {
        "hint": question.hint,
        "question_id": question_id
    }

@router.post("/explain/comprehensive")
@rate_limit(limit=60, window=60)
async def get_comprehensive_explanation(
    request: ComprehensiveExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive AI-powered explanation with intelligent tutoring"""
    # Get question
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    try:
        # Generate comprehensive explanation using AI engine
        explanation_data = await ai_explanation_engine.generate_comprehensive_explanation(
            question=question,
            user_answer=request.user_answer,
            user=current_user,
            db=db,
            attempt_number=request.attempt_number,
            previous_hints_used=request.previous_hints_used
        )
        
        # Create tutoring session record
        tutoring_session = AITutoringSession(
            user_id=current_user.id,
            question_id=question.id,
            estimated_student_level=explanation_data.get("student_level"),
            explanation_complexity_used=explanation_data.get("explanation_complexity"),
            user_answer=request.user_answer,
            correct_answer=explanation_data.get("correct_answer"),
            is_correct=explanation_data.get("is_correct"),
            attempt_number=request.attempt_number,
            error_type=explanation_data.get("error_type"),
            explanation_type=explanation_data.get("explanation_type"),
            main_explanation=explanation_data.get("main_explanation"),
            detailed_explanation=explanation_data.get("detailed_explanation"),
            confidence_score=explanation_data.get("confidence_score"),
            hints_provided=explanation_data.get("hints"),
            related_concepts=explanation_data.get("related_concepts"),
            recommended_resources=explanation_data.get("recommended_resources"),
            suggested_actions=explanation_data.get("suggested_actions"),
            ai_model_used="gpt-3.5-turbo" if ai_explanation_engine.client else "fallback"
        )
        
        db.add(tutoring_session)
        db.commit()
        
        # Add session ID to response
        explanation_data["session_id"] = str(tutoring_session.id)
        
        return explanation_data
        
    except Exception as e:
        logger.error(f"Error in comprehensive explanation: {e}")
        raise HTTPException(status_code=500, detail="Error generando explicación")

@router.post("/hint/progressive")
@rate_limit(limit=100, window=60)
async def get_progressive_hint(
    request: ProgressiveLearningRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get progressive contextual hints based on student level"""
    # Get question
    question = db.query(Question).filter(Question.id == request.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    try:
        hint_data = await ai_explanation_engine.get_contextual_hint(
            question=question,
            user=current_user,
            hint_level=request.hint_level,
            previous_attempts=request.previous_attempts
        )
        
        return hint_data
        
    except Exception as e:
        logger.error(f"Error generating progressive hint: {e}")
        raise HTTPException(status_code=500, detail="Error generando pista")

@router.post("/tutoring/feedback")
@rate_limit(limit=100, window=60)
async def submit_tutoring_feedback(
    request: TutoringFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for a tutoring session"""
    # Get tutoring session
    session = db.query(AITutoringSession).filter(
        AITutoringSession.id == request.session_id,
        AITutoringSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Sesión de tutoría no encontrada")
    
    # Update session with feedback
    if request.satisfaction_rating:
        session.student_satisfaction_rating = request.satisfaction_rating
    if request.helpfulness_rating:
        session.explanation_helpfulness = request.helpfulness_rating
    
    # End session
    session.session_end = datetime.now()
    session.calculate_session_duration()
    
    db.commit()
    
    return {
        "message": "Feedback registrado exitosamente",
        "session_id": request.session_id,
        "effectiveness_score": session.get_learning_effectiveness_score()
    }

@router.get("/learning/progress/{user_id}")
@rate_limit(limit=100, window=60)
async def get_learning_progress(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed learning progress analytics"""
    # Admin check - users can only view their own progress unless admin
    if str(current_user.id) != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # Get recent tutoring sessions (last 30 days)
    recent_sessions = db.query(AITutoringSession).filter(
        AITutoringSession.user_id == user_id,
        AITutoringSession.created_at > datetime.now() - timedelta(days=30)
    ).all()
    
    if not recent_sessions:
        return {
            "message": "No hay datos suficientes para generar reporte",
            "total_sessions": 0
        }
    
    # Get or create learning progress record
    progress = db.query(AILearningProgress).filter(
        AILearningProgress.user_id == user_id
    ).first()
    
    if not progress:
        progress = AILearningProgress(user_id=user_id)
        db.add(progress)
    
    # Update progress metrics
    progress.update_metrics_from_sessions(recent_sessions)
    db.commit()
    
    # Calculate additional insights
    improvement_rate = 0
    if len(recent_sessions) >= 10:
        recent_accuracy = sum(1 for s in recent_sessions[-5:] if s.is_correct) / 5
        older_accuracy = sum(1 for s in recent_sessions[:5] if s.is_correct) / 5
        improvement_rate = (recent_accuracy - older_accuracy) * 100
    
    return {
        "user_id": user_id,
        "analysis_period": "30 días",
        "total_sessions": progress.total_sessions,
        "overall_accuracy": progress.overall_accuracy_percentage,
        "improvement_rate": improvement_rate,
        "current_level": progress.current_estimated_level,
        "common_errors": progress.common_error_types,
        "average_hints_used": progress.average_hints_per_question,
        "satisfaction_trend": progress.satisfaction_trend,
        "learning_effectiveness": sum(s.get_learning_effectiveness_score() for s in recent_sessions) / len(recent_sessions)
    }

@router.get("/analytics/dashboard")
@rate_limit(limit=100, window=60)
async def get_ai_analytics_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get AI tutoring analytics dashboard for administrators"""
    # Admin check - only administrators can access
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Acceso denegado - Solo administradores")
    
    # Get overall statistics
    total_sessions = db.query(AITutoringSession).count()
    total_users_with_sessions = db.query(AITutoringSession.user_id).distinct().count()
    
    # Average effectiveness scores
    avg_effectiveness = db.query(func.avg(AITutoringSession.confidence_score)).scalar() or 0
    
    # Most common error types
    error_type_counts = db.query(
        AITutoringSession.error_type,
        func.count(AITutoringSession.error_type)
    ).filter(
        AITutoringSession.error_type.isnot(None),
        AITutoringSession.error_type != 'none'
    ).group_by(AITutoringSession.error_type).all()
    
    # AI vs Fallback usage
    ai_usage = db.query(
        AITutoringSession.explanation_type,
        func.count(AITutoringSession.explanation_type)
    ).group_by(AITutoringSession.explanation_type).all()
    
    return {
        "total_tutoring_sessions": total_sessions,
        "active_users": total_users_with_sessions,
        "average_ai_effectiveness": round(avg_effectiveness, 3),
        "common_error_patterns": dict(error_type_counts),
        "ai_vs_fallback_usage": dict(ai_usage),
        "generated_at": datetime.now().isoformat()
    } 