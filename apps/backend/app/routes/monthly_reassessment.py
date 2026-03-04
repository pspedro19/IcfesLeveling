from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
import json

from ..core.database import get_db
from ..core.security import get_current_user
from ..services.monthly_reassessment_service import MonthlyReassessmentService
from ..schemas.diagnostic_test import (
    MonthlyReassessmentRequest,
    ReassessmentComparison,
    ReassessmentNotification,
    DiagnosticTestSubmit,
    DiagnosticTestQuestion
)
from ..models.user import User
from ..models.subject import Subject

router = APIRouter(prefix="/monthly-reassessment", tags=["monthly-reassessment"])

@router.get("/eligibility/{subject_id}")
async def check_reassessment_eligibility(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verificar elegibilidad para reevaluación mensual"""
    try:
        reassessment_service = MonthlyReassessmentService(db)
        eligibility = reassessment_service.check_monthly_reassessment_eligibility(
            str(current_user.id), subject_id
        )
        
        return {
            "eligible": eligibility["eligible"],
            "reason": eligibility.get("reason", ""),
            "days_since_initial": eligibility.get("days_since_initial"),
            "initial_score": eligibility.get("initial_score"),
            "subject_id": subject_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando elegibilidad: {str(e)}")

@router.post("/create")
async def create_monthly_reassessment(
    request: MonthlyReassessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una nueva reevaluación mensual"""
    try:
        reassessment_service = MonthlyReassessmentService(db)
        
        # Verificar que el usuario está creando para sí mismo
        if request.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="No autorizado para crear reevaluación para otro usuario")
        
        reassessment = reassessment_service.create_monthly_reassessment(
            request.user_id, request.subject_id
        )
        
        return {
            "id": str(reassessment.id),
            "user_id": str(reassessment.user_id),
            "subject_id": str(reassessment.subject_id),
            "test_type": reassessment.test_type,
            "reassessment_type": reassessment.reassessment_type,
            "original_test_id": str(reassessment.original_test_id),
            "is_monthly_reassessment": reassessment.is_monthly_reassessment,
            "days_since_initial": reassessment.days_since_initial,
            "status": reassessment.status,
            "created_at": reassessment.created_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando reevaluación: {str(e)}")

@router.get("/{test_id}/questions")
async def get_reassessment_questions(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener preguntas para la reevaluación mensual"""
    try:
        reassessment_service = MonthlyReassessmentService(db)
        
        # Obtener el test para verificar que pertenece al usuario
        from ..models.diagnostic_test import DiagnosticTest
        test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test de reevaluación no encontrado")
        
        # Obtener configuración del test
        from ..schemas.diagnostic_test import DIAGNOSTIC_TEST_CONFIGS
        subject = db.query(Subject).filter(Subject.id == test.subject_id).first()
        config = DIAGNOSTIC_TEST_CONFIGS.get(subject.name.lower(), {
            "total_questions": 45,
            "time_limit_minutes": 90,
            "topics": []
        })
        
        # Calcular número de preguntas (20% del test original)
        original_test = db.query(DiagnosticTest).filter(
            DiagnosticTest.id == test.original_test_id
        ).first()
        
        question_count = max(6, int(original_test.questions_answered * 0.2))
        
        # Obtener preguntas de alta dificultad
        questions = reassessment_service.get_reassessment_questions(
            test_id, str(test.subject_id), question_count
        )
        
        return [
            {
                "id": str(q.id),
                "question_text": q.question_text,
                "options": q.options,
                "subject": subject.name,
                "topic": q.topic.name if q.topic else "General",
                "difficulty": q.difficulty,
                "hint": q.hint
            }
            for q in questions
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo preguntas: {str(e)}")

@router.post("/{test_id}/submit")
async def submit_reassessment(
    test_id: str,
    submit_data: DiagnosticTestSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Procesar respuestas de la reevaluación mensual"""
    try:
        reassessment_service = MonthlyReassessmentService(db)
        
        # Verificar que el test pertenece al usuario
        from ..models.diagnostic_test import DiagnosticTest
        test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test de reevaluación no encontrado")
        
        # Convertir respuestas al formato esperado
        answers = [
            {
                "question_id": answer.question_id,
                "user_answer": answer.user_answer,
                "response_time_ms": answer.response_time_ms
            }
            for answer in submit_data.answers
        ]
        
        # Procesar respuestas
        result = reassessment_service.submit_monthly_reassessment(test_id, answers)
        
        return {
            "reassessment_id": result["reassessment_id"],
            "current_score": result["current_score"],
            "initial_score": result["initial_score"],
            "improvement_percentage": result["improvement_percentage"],
            "comparison": result["comparison"],
            "new_goals": result["new_goals"],
            "message": _generate_comparison_message(result["comparison"])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando reevaluación: {str(e)}")

@router.get("/user-reassessments")
async def get_user_reassessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todas las reevaluaciones mensuales del usuario"""
    try:
        reassessment_service = MonthlyReassessmentService(db)
        reassessments = reassessment_service.get_user_reassessments(str(current_user.id))
        
        return [
            {
                "id": str(r.id),
                "subject_id": str(r.subject_id),
                "subject_name": r.subject.name,
                "test_type": r.test_type,
                "reassessment_type": r.reassessment_type,
                "score_percentage": float(r.score_percentage),
                "questions_answered": r.questions_answered,
                "correct_answers": r.correct_answers,
                "time_spent_seconds": r.time_spent_seconds,
                "days_since_initial": r.days_since_initial,
                "comparison_with_initial": r.comparison_with_initial,
                "status": r.status,
                "created_at": r.created_at,
                "completed_at": r.completed_at
            }
            for r in reassessments
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo reevaluaciones: {str(e)}")

@router.get("/summary/{subject_id}")
async def get_reassessment_summary(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener resumen de reevaluaciones para una materia"""
    try:
        reassessment_service = MonthlyReassessmentService(db)
        summary = reassessment_service.get_reassessment_summary(str(current_user.id), subject_id)
        
        return {
            "subject_id": subject_id,
            "total_reassessments": summary["total_reassessments"],
            "average_improvement": summary["average_improvement"],
            "best_improvement": summary["best_improvement"],
            "trend": summary["trend"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")

@router.get("/available-subjects")
async def get_available_subjects_for_reassessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener materias disponibles para reevaluación mensual"""
    try:
        reassessment_service = MonthlyReassessmentService(db)
        subjects = db.query(Subject).all()
        
        available_subjects = []
        for subject in subjects:
            eligibility = reassessment_service.check_monthly_reassessment_eligibility(
                str(current_user.id), str(subject.id)
            )
            
            available_subjects.append({
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description,
                "icon_url": subject.icon_url,
                "color": subject.color,
                "eligible": eligibility["eligible"],
                "reason": eligibility.get("reason", ""),
                "days_since_initial": eligibility.get("days_since_initial"),
                "initial_score": eligibility.get("initial_score")
            })
        
        return available_subjects
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo materias: {str(e)}")

def _generate_comparison_message(comparison: Dict[str, Any]) -> str:
    """Generar mensaje de comparación para el usuario"""
    improvement = comparison["improvement_percentage"]
    trend = comparison["overall_trend"]
    
    if trend == "improving":
        if improvement > 15:
            return "¡Excelente progreso! Has mejorado significativamente."
        elif improvement > 5:
            return "¡Buen trabajo! Has mostrado mejoras consistentes."
        else:
            return "Has mejorado ligeramente. Continúa con tu plan de estudio."
    elif trend == "declining":
        if improvement < -15:
            return "Necesitas revisar tu estrategia de estudio. Considera ajustar tu plan."
        else:
            return "Has tenido una ligera disminución. Revisa las áreas débiles."
    else:
        return "Tu rendimiento se mantiene estable. Considera aumentar la dificultad."

@router.get("/config/{subject_name}")
async def get_reassessment_config(
    subject_name: str,
    db: Session = Depends(get_db)
):
    """Obtener configuración de reevaluación por materia"""
    try:
        from ..schemas.diagnostic_test import DIAGNOSTIC_TEST_CONFIGS
        
        config = DIAGNOSTIC_TEST_CONFIGS.get(subject_name.lower(), {
            "total_questions": 30,
            "time_limit_minutes": 60,
            "topics": []
        })
        
        # Para reevaluación mensual, usar 20% de preguntas
        reassessment_config = {
            "subject": subject_name,
            "total_questions": max(6, int(config["total_questions"] * 0.2)),
            "time_limit_minutes": max(15, int(config["time_limit_minutes"] * 0.2)),
            "topics": config["topics"],
            "difficulty_focus": "high",  # Enfoque en preguntas de alta dificultad
            "comparison_enabled": True,
            "plan_regeneration": True,
            "notification_system": True
        }
        
        return reassessment_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}") 