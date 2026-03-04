from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.quiz import (
    QuizCreate,
    QuizAnswerCreate,
    QuizAnswerResponse,
    QuizResponse,
    QuizGenerationRequest,
    QuizGenerationResponse,
    QuizFeedback,
    QuizProgressUpdate
)
from ..services.quiz_service import QuizService
from ..models.user import User
from ..models.quiz import Quiz, QuizAnswer
from ..models.user_profile import UserProfile # New import

router = APIRouter(prefix="/quiz", tags=["quizzes"])

@router.post("/unit/{unit_id}", response_model=QuizGenerationResponse)
async def generate_unit_quiz(
    unit_id: str,
    generation_request: QuizGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generar quiz contextualizado para una unidad específica"""
    try:
        quiz_service = QuizService(db)
        
        # Extraer plan_id y unit_number del unit_id
        # Formato esperado: "plan_id_unit_number"
        parts = unit_id.split("_")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Formato de unit_id inválido")
        
        plan_id = parts[0]
        unit_number = int(parts[1])
        
        # Get user level from UserProfile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        user_level = user_profile.level if user_profile else 1
        
        quiz_response = quiz_service.generate_unit_quiz(
            user_id=str(current_user.id),
            plan_id=plan_id,
            unit_number=unit_number,
            user_level=user_level
        )
        
        return quiz_response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando quiz: {str(e)}")

@router.post("/{quiz_id}/answer", response_model=QuizAnswerResponse)
async def submit_quiz_answer(
    quiz_id: str,
    answer_data: QuizAnswerCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enviar respuesta de quiz con retroalimentación IA"""
    try:
        quiz_service = QuizService(db)
        quiz_answer = quiz_service.submit_quiz_answer(quiz_id, answer_data)
        return quiz_answer
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando respuesta: {str(e)}")

@router.post("/{quiz_id}/complete", response_model=QuizFeedback)
async def complete_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Completar quiz y generar retroalimentación IA"""
    try:
        quiz_service = QuizService(db)
        feedback = quiz_service.complete_quiz(quiz_id)
        return feedback
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completando quiz: {str(e)}")

@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener quiz específico"""
    try:
        quiz_service = QuizService(db)
        quiz = quiz_service.get_quiz_by_id(quiz_id, str(current_user.id))
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
        return QuizResponse(
            id=str(quiz.id),
            user_id=str(quiz.user_id),
            plan_id=str(quiz.plan_id),
            unit_number=quiz.unit_number,
            quiz_name=quiz.quiz_name,
            total_questions=quiz.total_questions,
            passing_score=float(quiz.passing_score),
            time_limit_minutes=quiz.time_limit_minutes,
            status=quiz.status,
            score=float(quiz.score),
            correct_answers=quiz.correct_answers,
            time_taken_seconds=quiz.time_taken_seconds,
            ai_feedback=quiz.ai_feedback,
            created_at=quiz.created_at,
            completed_at=quiz.completed_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo quiz: {str(e)}")

@router.get("/", response_model=List[QuizResponse])
async def get_user_quizzes(
    plan_id: Optional[str] = Query(None, description="ID del plan de estudio"),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de quizzes"),
    offset: int = Query(0, ge=0, description="Número de quizzes a omitir"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener quizzes del usuario"""
    try:
        quiz_service = QuizService(db)
        quizzes = quiz_service.get_user_quizzes(str(current_user.id), plan_id)
        
        # Aplicar paginación
        quizzes = quizzes[offset:offset + limit]
        
        return [
            QuizResponse(
                id=str(quiz.id),
                user_id=str(quiz.user_id),
                plan_id=str(quiz.plan_id),
                unit_number=quiz.unit_number,
                quiz_name=quiz.quiz_name,
                total_questions=quiz.total_questions,
                passing_score=float(quiz.passing_score),
                time_limit_minutes=quiz.time_limit_minutes,
                status=quiz.status,
                score=float(quiz.score),
                correct_answers=quiz.correct_answers,
                time_taken_seconds=quiz.time_taken_seconds,
                ai_feedback=quiz.ai_feedback,
                created_at=quiz.created_at,
                completed_at=quiz.completed_at
            )
            for quiz in quizzes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo quizzes: {str(e)}")

@router.get("/{quiz_id}/progress", response_model=QuizProgressUpdate)
async def get_quiz_progress(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener progreso actual del quiz"""
    try:
        quiz = db.query(Quiz).filter(
            Quiz.id == quiz_id,
            Quiz.user_id == current_user.id
        ).first()
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
        # Obtener respuestas del quiz
        answers = db.query(QuizAnswer).filter(QuizAnswer.quiz_id == quiz_id).all()
        correct_answers = sum(1 for a in answers if a.is_correct)
        
        # Calcular tiempo restante (simulado)
        time_elapsed = (datetime.utcnow() - quiz.created_at).total_seconds()
        time_remaining = max(0, (quiz.time_limit_minutes * 60) - time_elapsed)
        
        # Calcular porcentaje de puntaje
        score_percentage = (correct_answers / quiz.total_questions * 100) if quiz.total_questions > 0 else 0
        
        return QuizProgressUpdate(
            quiz_id=str(quiz.id),
            current_question=len(answers),
            total_questions=quiz.total_questions,
            correct_answers=correct_answers,
            time_remaining_seconds=int(time_remaining),
            score_percentage=score_percentage
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo progreso: {str(e)}")

@router.delete("/{quiz_id}")
async def delete_quiz(
    quiz_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar quiz (solo si está en progreso)"""
    try:
        quiz = db.query(Quiz).filter(
            Quiz.id == quiz_id,
            Quiz.user_id == current_user.id
        ).first()
        
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz no encontrado")
        
        if quiz.status != "in_progress":
            raise HTTPException(status_code=400, detail="Solo se pueden eliminar quizzes en progreso")
        
        # Eliminar respuestas asociadas
        db.query(QuizAnswer).filter(QuizAnswer.quiz_id == quiz_id).delete()
        
        # Eliminar quiz
        db.delete(quiz)
        db.commit()
        
        return {"message": "Quiz eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error eliminando quiz: {str(e)}")

@router.get("/unit/{unit_id}/stats")
async def get_unit_quiz_stats(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de quizzes para una unidad"""
    try:
        # Extraer plan_id y unit_number del unit_id
        parts = unit_id.split("_")
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Formato de unit_id inválido")
        
        plan_id = parts[0]
        unit_number = int(parts[1])
        
        # Obtener todos los quizzes de la unidad
        quizzes = db.query(Quiz).filter(
            Quiz.user_id == current_user.id,
            Quiz.plan_id == plan_id,
            Quiz.unit_number == unit_number
        ).all()
        
        if not quizzes:
            return {
                "total_quizzes": 0,
                "completed_quizzes": 0,
                "average_score": 0,
                "best_score": 0,
                "total_questions_answered": 0,
                "correct_answers": 0
            }
        
        completed_quizzes = [q for q in quizzes if q.status == "completed"]
        scores = [q.score for q in completed_quizzes if q.score > 0]
        
        # Calcular estadísticas
        total_questions_answered = sum(q.total_questions for q in quizzes)
        correct_answers = sum(q.correct_answers for q in quizzes)
        
        stats = {
            "total_quizzes": len(quizzes),
            "completed_quizzes": len(completed_quizzes),
            "average_score": sum(scores) / len(scores) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "total_questions_answered": total_questions_answered,
            "correct_answers": correct_answers,
            "accuracy_percentage": (correct_answers / total_questions_answered * 100) if total_questions_answered > 0 else 0
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}") 