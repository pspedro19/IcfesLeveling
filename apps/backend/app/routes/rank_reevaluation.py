from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ..core.database import get_db
from ..models.user import User
from ..models.question import Question
from ..models.diagnostic_test import DiagnosticTest
from ..services.rank_validation_service import RankValidationService
from ..services.monthly_reassessment_service import MonthlyReassessmentService
from ..core.security import get_current_user
from ..schemas.diagnostic_test import DiagnosticTestSubmit
from pydantic import BaseModel

router = APIRouter(prefix="/api/rank-reevaluation", tags=["rank-reevaluation"])
logger = logging.getLogger(__name__)

class RankReevaluationRequest(BaseModel):
    subject_id: str

class RankReevaluationResponse(BaseModel):
    eligible: bool
    subject_name: str
    current_rank: str
    requirements_met: bool
    plan_completion: Dict[str, Any]
    video_completion: Dict[str, Any]
    exercise_completion: Dict[str, Any]
    reason: str

@router.get("/eligibility")
async def check_reevaluation_eligibility(
    subject_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifica si el usuario puede solicitar una reevaluación de rango
    """
    try:
        validation_service = RankValidationService(db)
        eligibility = validation_service.check_reevaluation_eligibility(
            user_id=str(current_user.id),
            subject_id=subject_id
        )
        
        return eligibility
        
    except Exception as e:
        logger.error(f"Error checking reevaluation eligibility: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error verificando elegibilidad para reevaluación"
        )

@router.get("/dashboard")
async def get_reevaluation_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el dashboard completo de reevaluación del usuario
    """
    try:
        validation_service = RankValidationService(db)
        dashboard = validation_service.get_reevaluation_dashboard(str(current_user.id))
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting reevaluation dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo dashboard de reevaluación"
        )

@router.post("/create-exam")
async def create_rank_reevaluation_exam(
    request: RankReevaluationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crea un examen de reevaluación de rango para una materia específica
    """
    try:
        validation_service = RankValidationService(db)
        
        # Verificar elegibilidad
        eligibility = validation_service.check_reevaluation_eligibility(
            user_id=str(current_user.id),
            subject_id=request.subject_id
        )
        
        if not eligibility.get("eligible", False):
            raise HTTPException(
                status_code=400,
                detail=f"No eligible for reevaluation: {eligibility.get('reason', 'Requirements not met')}"
            )
        
        # Crear el examen
        reevaluation_test = validation_service.create_rank_reevaluation_exam(
            user_id=str(current_user.id),
            subject_id=request.subject_id
        )
        
        return {
            "exam_id": str(reevaluation_test.id),
            "subject_id": request.subject_id,
            "questions_count": 45,
            "estimated_duration": "45-60 minutos",
            "passing_score": 75.0,
            "created_at": reevaluation_test.created_at.isoformat(),
            "message": "¡Examen de reevaluación creado! Tienes que aprobar con al menos 75% para subir de rango."
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating rank reevaluation exam: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error creando examen de reevaluación"
        )

@router.get("/{exam_id}/questions")
async def get_reevaluation_questions(
    exam_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene las 45 preguntas para el examen de reevaluación
    """
    try:
        # Verificar que el examen pertenece al usuario
        exam = db.query(DiagnosticTest).filter(
            DiagnosticTest.id == exam_id,
            DiagnosticTest.user_id == current_user.id,
            DiagnosticTest.reassessment_type == "rank_reevaluation",
            DiagnosticTest.status == "in_progress"
        ).first()
        
        if not exam:
            raise HTTPException(
                status_code=404,
                detail="Examen de reevaluación no encontrado o ya completado"
            )
        
        # Obtener preguntas usando el servicio existente
        reassessment_service = MonthlyReassessmentService(db)
        questions = reassessment_service.get_reassessment_questions(
            test_id=exam_id,
            subject_id=str(exam.subject_id),
            question_count=45  # 45 preguntas para reevaluación de rango
        )
        
        # Formatear preguntas para el frontend
        formatted_questions = []
        for i, question in enumerate(questions):
            formatted_questions.append({
                "id": str(question.id),
                "question_number": i + 1,
                "question_text": question.question_text,
                "options": question.options,
                "difficulty": question.difficulty_level,
                "topic": question.topic.name if question.topic else "General",
                "subject": question.subject.name if question.subject else "Unknown"
            })
        
        return {
            "exam_id": exam_id,
            "total_questions": len(formatted_questions),
            "questions": formatted_questions,
            "exam_info": {
                "passing_score": 75.0,
                "time_limit_minutes": 60,
                "subject_name": exam.subject.name if exam.subject else "Unknown"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting reevaluation questions: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo preguntas de reevaluación"
        )

@router.post("/{exam_id}/submit")
async def submit_rank_reevaluation(
    exam_id: str,
    submit_data: DiagnosticTestSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Envía las respuestas del examen de reevaluación y procesa el resultado
    """
    try:
        # Verificar que el examen pertenece al usuario
        exam = db.query(DiagnosticTest).filter(
            DiagnosticTest.id == exam_id,
            DiagnosticTest.user_id == current_user.id,
            DiagnosticTest.reassessment_type == "rank_reevaluation",
            DiagnosticTest.status == "in_progress"
        ).first()
        
        if not exam:
            raise HTTPException(
                status_code=404,
                detail="Examen de reevaluación no encontrado"
            )
        
        # Procesar respuestas usando el servicio existente
        reassessment_service = MonthlyReassessmentService(db)
        
        # Convertir respuestas al formato esperado
        answers = [
            {
                "question_id": answer.question_id,
                "user_answer": answer.user_answer,
                "response_time_ms": answer.response_time_ms
            }
            for answer in submit_data.answers
        ]
        
        # Calcular resultado
        result = reassessment_service._calculate_reassessment_score(answers, exam.subject_id)
        
        # Actualizar el examen
        exam.questions_answered = len(answers)
        exam.correct_answers = result["correct_answers"]
        exam.score_percentage = result["score_percentage"]
        exam.time_spent_seconds = sum(answer.response_time_ms for answer in submit_data.answers) // 1000
        exam.status = "completed"
        exam.completed_at = db.query(func.now()).scalar()
        
        # Verificar si aprobó
        passed = result["score_percentage"] >= 75.0
        rank_upgraded = False
        new_rank = current_user.rank
        
        if passed:
            # Subir de rango
            rank_upgraded, new_rank = self._upgrade_user_rank(current_user, db)
            
            # Dar recompensas
            experience_bonus = 1000
            orbs_bonus = 200
            crystals_bonus = 50
            
            current_user.experience += experience_bonus
            current_user.orbs += orbs_bonus
            
        db.commit()
        
        return {
            "exam_id": exam_id,
            "score": result["score_percentage"],
            "passed": passed,
            "passing_score": 75.0,
            "questions_answered": len(answers),
            "correct_answers": result["correct_answers"],
            "rank_upgraded": rank_upgraded,
            "previous_rank": current_user.rank if not rank_upgraded else self._get_previous_rank(new_rank),
            "new_rank": new_rank,
            "rewards": {
                "experience": 1000 if passed else 100,
                "orbs": 200 if passed else 20,
                "crystals": 50 if passed else 0
            } if passed else {"experience": 100, "orbs": 20, "crystals": 0},
            "message": self._generate_result_message(passed, rank_upgraded, result["score_percentage"]),
            "next_attempt_available": (exam.created_at + timedelta(days=30)).isoformat() if not passed else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting rank reevaluation: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error procesando examen de reevaluación"
        )

@router.get("/history")
async def get_reevaluation_history(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene el historial de reevaluaciones del usuario
    """
    try:
        tests = db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == current_user.id,
            DiagnosticTest.reassessment_type == "rank_reevaluation"
        ).order_by(DiagnosticTest.created_at.desc()).limit(limit).all()
        
        history = []
        for test in tests:
            history.append({
                "id": str(test.id),
                "subject_name": test.subject.name if test.subject else "Unknown",
                "score": float(test.score_percentage) if test.score_percentage else 0,
                "passed": test.score_percentage >= 75.0 if test.score_percentage else False,
                "date": test.created_at.isoformat(),
                "questions_answered": test.questions_answered,
                "status": test.status,
                "time_spent_minutes": (test.time_spent_seconds // 60) if test.time_spent_seconds else 0
            })
        
        return {
            "history": history,
            "total_attempts": len(history),
            "best_score": max((h["score"] for h in history), default=0),
            "average_score": sum(h["score"] for h in history) / len(history) if history else 0
        }
        
    except Exception as e:
        logger.error(f"Error getting reevaluation history: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo historial de reevaluaciones"
        )

def _upgrade_user_rank(user: User, db: Session) -> tuple[bool, str]:
    """Sube el rango del usuario al siguiente nivel"""
    rank_order = ["E", "D", "C", "B", "A", "S", "SS", "SSS"]
    
    try:
        current_index = rank_order.index(user.rank)
        if current_index >= len(rank_order) - 1:
            return False, user.rank  # Ya está en el rango máximo
        
        new_rank = rank_order[current_index + 1]
        user.rank = new_rank
        
        # Bonus de stats por subir de rango
        user.hp += 20
        user.mp += 10
        user.power += 5
        user.wisdom += 5
        user.speed += 3
        
        return True, new_rank
        
    except ValueError:
        return False, user.rank

def _get_previous_rank(current_rank: str) -> str:
    """Obtiene el rango anterior"""
    rank_order = ["E", "D", "C", "B", "A", "S", "SS", "SSS"]
    
    try:
        current_index = rank_order.index(current_rank)
        if current_index <= 0:
            return "E"
        return rank_order[current_index - 1]
    except ValueError:
        return "E"

def _generate_result_message(passed: bool, rank_upgraded: bool, score: float) -> str:
    """Genera mensaje de resultado personalizado"""
    if rank_upgraded:
        return f"¡Felicitaciones! Has aprobado con {score:.1f}% y subido de rango. ¡Eres un Hunter más poderoso ahora!"
    elif passed:
        return f"¡Aprobaste con {score:.1f}%! Has demostrado tu conocimiento, pero ya estás en el rango máximo."
    else:
        return f"Obtuviste {score:.1f}%. Necesitas al menos 75% para subir de rango. ¡Sigue estudiando y vuelve a intentarlo en 30 días!"