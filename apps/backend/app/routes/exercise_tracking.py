from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime, timedelta

from ..core.database import get_db
from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.question import Question
from ..core.security import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/exercise-tracking", tags=["exercise-tracking"])
logger = logging.getLogger(__name__)

class ExerciseAttempt(BaseModel):
    question_id: str
    user_answer: str
    is_correct: bool
    response_time_ms: int
    difficulty_level: int
    topic_name: str

class ExerciseSessionStart(BaseModel):
    unit_number: int
    topic_name: str
    expected_questions: int

class ExerciseSessionComplete(BaseModel):
    unit_number: int
    topic_name: str
    attempts: List[ExerciseAttempt]
    session_duration_seconds: int
    
class UserExerciseMetrics(BaseModel):
    user_id: str
    plan_id: str
    unit_number: int
    topic_name: str
    total_attempts: int
    correct_attempts: int
    accuracy_percentage: float
    average_response_time_ms: int
    total_time_spent_seconds: int
    difficulty_progress: Dict[str, Any]
    last_session_date: Optional[datetime]
    current_streak: int
    best_streak: int
    mastery_level: str  # "beginner", "intermediate", "advanced", "master"

@router.post("/{plan_id}/exercise-session/start")
async def start_exercise_session(
    plan_id: str,
    session_start: ExerciseSessionStart,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Inicia una sesión de ejercicios para un tema específico
    """
    try:
        # Verificar que el plan pertenezca al usuario
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id,
            StudyPlan.is_active == True
        ).first()
        
        if not study_plan:
            raise HTTPException(
                status_code=404,
                detail="Plan de estudio no encontrado"
            )
        
        # Obtener métricas actuales del usuario para este tema
        metrics = await _get_user_topic_metrics(
            current_user.id, plan_id, session_start.unit_number, 
            session_start.topic_name, db
        )
        
        # Generar recomendaciones para la sesión
        recommendations = _generate_session_recommendations(metrics)
        
        return {
            "session_id": f"{plan_id}_{session_start.unit_number}_{session_start.topic_name}_{datetime.now().timestamp()}",
            "plan_id": plan_id,
            "unit_number": session_start.unit_number,
            "topic_name": session_start.topic_name,
            "current_metrics": metrics,
            "recommendations": recommendations,
            "session_settings": {
                "adaptive_difficulty": True,
                "time_pressure": metrics.get("mastery_level") in ["advanced", "master"],
                "hint_availability": metrics.get("mastery_level") in ["beginner", "intermediate"]
            }
        }
        
    except Exception as e:
        logger.error(f"Error starting exercise session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error iniciando sesión de ejercicios"
        )

@router.post("/{plan_id}/exercise-session/complete")
async def complete_exercise_session(
    plan_id: str,
    session_complete: ExerciseSessionComplete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Completa una sesión de ejercicios y actualiza métricas
    """
    try:
        # Verificar que el plan pertenezca al usuario
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()
        
        if not study_plan:
            raise HTTPException(
                status_code=404,
                detail="Plan de estudio no encontrado"
            )
        
        # Analizar los resultados de la sesión
        session_analysis = _analyze_session_results(session_complete.attempts)
        
        # Actualizar progreso de la unidad
        unit_progress = db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id,
            PlanProgress.unit_number == session_complete.unit_number
        ).first()
        
        if not unit_progress:
            # Crear progreso de unidad si no existe
            unit_progress = PlanProgress(
                plan_id=plan_id,
                unit_number=session_complete.unit_number,
                unit_name=f"Unidad {session_complete.unit_number}",
                unit_description="",
                unit_content={},
                is_completed=False,
                score=0.0,
                weighted_progress={
                    "videos": {"completed": 0, "total": 1, "weight": 0.3},
                    "exercises": {"completed": 0, "total": 1, "weight": 0.5},
                    "readings": {"completed": 0, "total": 1, "weight": 0.2}
                }
            )
            db.add(unit_progress)
        
        # Actualizar progreso de ejercicios
        exercises_data = unit_progress.weighted_progress.get("exercises", {})
        exercises_data["completed"] = exercises_data.get("completed", 0) + len(session_complete.attempts)
        exercises_data["accuracy"] = session_analysis["accuracy_percentage"]
        exercises_data["last_session"] = datetime.now().isoformat()
        
        unit_progress.weighted_progress["exercises"] = exercises_data
        
        # Calcular nuevo score de la unidad
        new_score = _calculate_unit_score(unit_progress.weighted_progress)
        unit_progress.score = new_score
        
        # Verificar si la unidad está completada
        if session_analysis["accuracy_percentage"] >= 80 and exercises_data.get("completed", 0) >= exercises_data.get("total", 1):
            unit_progress.is_completed = True
            unit_progress.completion_date = datetime.now()
        
        db.commit()
        
        # Actualizar progreso general del plan
        await _update_overall_plan_progress(study_plan, db)
        
        # Generar recomendaciones para próximos pasos
        next_recommendations = _generate_next_steps_recommendations(
            session_analysis, 
            session_complete.unit_number,
            study_plan
        )
        
        # Actualizar métricas del usuario
        updated_metrics = await _update_user_topic_metrics(
            current_user.id, plan_id, session_complete.unit_number,
            session_complete.topic_name, session_complete.attempts, db
        )
        
        return {
            "success": True,
            "session_analysis": session_analysis,
            "unit_progress": {
                "unit_number": unit_progress.unit_number,
                "score": float(unit_progress.score),
                "is_completed": unit_progress.is_completed,
                "weighted_progress": unit_progress.weighted_progress
            },
            "updated_metrics": updated_metrics,
            "next_recommendations": next_recommendations,
            "achievements": _check_achievements(session_analysis, updated_metrics),
            "plan_progress": {
                "overall_percentage": float(study_plan.progress_percentage),
                "completed_units": study_plan.completed_units
            }
        }
        
    except Exception as e:
        logger.error(f"Error completing exercise session: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error completando sesión de ejercicios"
        )

@router.get("/{plan_id}/exercise-metrics")
async def get_exercise_metrics(
    plan_id: str,
    unit_number: Optional[int] = None,
    topic_name: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene métricas detalladas de ejercicios del usuario
    """
    try:
        # Verificar que el plan pertenezca al usuario
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()
        
        if not study_plan:
            raise HTTPException(
                status_code=404,
                detail="Plan de estudio no encontrado"
            )
        
        # Obtener progreso de todas las unidades
        unit_progresses = db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id
        ).all()
        
        if unit_number:
            unit_progresses = [up for up in unit_progresses if up.unit_number == unit_number]
        
        metrics = {
            "plan_id": plan_id,
            "overall_metrics": {
                "total_units": len(unit_progresses),
                "completed_units": sum(1 for up in unit_progresses if up.is_completed),
                "average_score": sum(float(up.score) for up in unit_progresses) / len(unit_progresses) if unit_progresses else 0,
                "total_exercises_completed": sum(
                    up.weighted_progress.get("exercises", {}).get("completed", 0) 
                    for up in unit_progresses
                ),
                "overall_accuracy": sum(
                    up.weighted_progress.get("exercises", {}).get("accuracy", 0) 
                    for up in unit_progresses
                ) / len(unit_progresses) if unit_progresses else 0
            },
            "units": []
        }
        
        for unit_progress in unit_progresses:
            exercises_data = unit_progress.weighted_progress.get("exercises", {})
            
            unit_metrics = {
                "unit_number": unit_progress.unit_number,
                "unit_name": unit_progress.unit_name,
                "is_completed": unit_progress.is_completed,
                "score": float(unit_progress.score),
                "completion_date": unit_progress.completion_date.isoformat() if unit_progress.completion_date else None,
                "exercises": {
                    "completed": exercises_data.get("completed", 0),
                    "total": exercises_data.get("total", 0),
                    "accuracy": exercises_data.get("accuracy", 0),
                    "completion_percentage": (exercises_data.get("completed", 0) / max(exercises_data.get("total", 1), 1)) * 100,
                    "last_session": exercises_data.get("last_session")
                },
                "progress_breakdown": unit_progress.weighted_progress
            }
            
            # Si se solicita un tema específico, filtrar información
            if topic_name:
                topic_metrics = await _get_user_topic_metrics(
                    current_user.id, plan_id, unit_progress.unit_number, topic_name, db
                )
                unit_metrics["topic_specific"] = topic_metrics
            
            metrics["units"].append(unit_metrics)
        
        # Agregar tendencias y patrones de aprendizaje
        metrics["learning_patterns"] = _analyze_learning_patterns(unit_progresses)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting exercise metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo métricas de ejercicios"
        )

async def _get_user_topic_metrics(user_id: str, plan_id: str, unit_number: int, topic_name: str, db: Session) -> Dict[str, Any]:
    """Obtiene métricas específicas del usuario para un tema"""
    # En una implementación completa, esto consultaría una tabla de métricas detalladas
    # Por ahora, retorna métricas mock basadas en el progreso de la unidad
    
    unit_progress = db.query(PlanProgress).filter(
        PlanProgress.plan_id == plan_id,
        PlanProgress.unit_number == unit_number
    ).first()
    
    if not unit_progress:
        return {
            "total_attempts": 0,
            "correct_attempts": 0,
            "accuracy_percentage": 0,
            "average_response_time_ms": 0,
            "mastery_level": "beginner",
            "current_streak": 0,
            "best_streak": 0
        }
    
    exercises_data = unit_progress.weighted_progress.get("exercises", {})
    
    return {
        "total_attempts": exercises_data.get("completed", 0),
        "correct_attempts": int(exercises_data.get("completed", 0) * exercises_data.get("accuracy", 0) / 100),
        "accuracy_percentage": exercises_data.get("accuracy", 0),
        "average_response_time_ms": 8000,  # Mock data
        "mastery_level": _determine_mastery_level(exercises_data.get("accuracy", 0)),
        "current_streak": 0,  # Mock data
        "best_streak": 0  # Mock data
    }

def _generate_session_recommendations(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Genera recomendaciones para la sesión basadas en métricas del usuario"""
    accuracy = metrics.get("accuracy_percentage", 0)
    mastery = metrics.get("mastery_level", "beginner")
    
    recommendations = {
        "suggested_question_count": 10,
        "difficulty_range": [1, 3],
        "focus_areas": [],
        "study_tips": []
    }
    
    if accuracy < 60:
        recommendations["suggested_question_count"] = 5
        recommendations["difficulty_range"] = [1, 2]
        recommendations["focus_areas"].append("conceptos básicos")
        recommendations["study_tips"].append("Revisa la teoría antes de continuar")
    elif accuracy > 85:
        recommendations["suggested_question_count"] = 15
        recommendations["difficulty_range"] = [2, 4]
        recommendations["focus_areas"].append("problemas complejos")
        recommendations["study_tips"].append("Desafíate con problemas más difíciles")
    
    return recommendations

def _analyze_session_results(attempts: List[ExerciseAttempt]) -> Dict[str, Any]:
    """Analiza los resultados de una sesión de ejercicios"""
    if not attempts:
        return {
            "total_attempts": 0,
            "correct_attempts": 0,
            "accuracy_percentage": 0,
            "average_response_time": 0,
            "difficulty_distribution": {},
            "performance_trend": "stable"
        }
    
    total_attempts = len(attempts)
    correct_attempts = sum(1 for attempt in attempts if attempt.is_correct)
    accuracy = (correct_attempts / total_attempts) * 100
    avg_response_time = sum(attempt.response_time_ms for attempt in attempts) / total_attempts
    
    # Analizar distribución por dificultad
    difficulty_dist = {}
    for attempt in attempts:
        diff = attempt.difficulty_level
        if diff not in difficulty_dist:
            difficulty_dist[diff] = {"total": 0, "correct": 0}
        difficulty_dist[diff]["total"] += 1
        if attempt.is_correct:
            difficulty_dist[diff]["correct"] += 1
    
    # Analizar tendencia de rendimiento
    performance_trend = "stable"
    if len(attempts) >= 5:
        first_half = attempts[:len(attempts)//2]
        second_half = attempts[len(attempts)//2:]
        
        first_accuracy = sum(1 for a in first_half if a.is_correct) / len(first_half)
        second_accuracy = sum(1 for a in second_half if a.is_correct) / len(second_half)
        
        if second_accuracy > first_accuracy + 0.1:
            performance_trend = "improving"
        elif second_accuracy < first_accuracy - 0.1:
            performance_trend = "declining"
    
    return {
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "accuracy_percentage": round(accuracy, 2),
        "average_response_time": round(avg_response_time, 2),
        "difficulty_distribution": difficulty_dist,
        "performance_trend": performance_trend,
        "mastery_indicators": {
            "consistency": accuracy > 75,
            "speed": avg_response_time < 10000,  # Less than 10 seconds average
            "difficulty_progression": max(difficulty_dist.keys()) >= 3 if difficulty_dist else False
        }
    }

def _calculate_unit_score(weighted_progress: Dict[str, Any]) -> float:
    """Calcula el score de una unidad basado en el progreso ponderado"""
    total_score = 0.0
    
    for component, data in weighted_progress.items():
        if isinstance(data, dict) and "completed" in data and "total" in data and "weight" in data:
            completion_rate = data["completed"] / max(data["total"], 1)
            weighted_score = completion_rate * data["weight"]
            total_score += weighted_score
    
    return min(total_score * 100, 100.0)  # Convert to percentage and cap at 100

async def _update_overall_plan_progress(study_plan: StudyPlan, db: Session):
    """Actualiza el progreso general del plan basado en todas las unidades"""
    try:
        unit_progresses = db.query(PlanProgress).filter(
            PlanProgress.plan_id == study_plan.id
        ).all()
        
        if unit_progresses:
            completed_units = sum(1 for up in unit_progresses if up.is_completed)
            avg_score = sum(float(up.score) for up in unit_progresses) / len(unit_progresses)
            
            study_plan.completed_units = completed_units
            study_plan.progress_percentage = min(avg_score, 100.0)
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Error updating overall plan progress: {e}")

def _generate_next_steps_recommendations(session_analysis: Dict[str, Any], unit_number: int, study_plan: StudyPlan) -> List[str]:
    """Genera recomendaciones para los próximos pasos"""
    recommendations = []
    accuracy = session_analysis.get("accuracy_percentage", 0)
    
    if accuracy >= 85:
        recommendations.append("¡Excelente trabajo! Puedes avanzar a la siguiente unidad.")
        if unit_number < study_plan.total_units:
            recommendations.append(f"Desbloquea la Unidad {unit_number + 1}")
    elif accuracy >= 70:
        recommendations.append("Buen progreso. Refuerza algunos conceptos antes de avanzar.")
        recommendations.append("Practica más ejercicios de esta unidad")
    else:
        recommendations.append("Necesitas reforzar los conceptos básicos.")
        recommendations.append("Revisa los videos de esta unidad nuevamente")
        recommendations.append("Considera solicitar ayuda de un tutor")
    
    return recommendations

def _check_achievements(session_analysis: Dict[str, Any], metrics: Dict[str, Any]) -> List[Dict[str, str]]:
    """Verifica si se desbloquearon logros en esta sesión"""
    achievements = []
    
    accuracy = session_analysis.get("accuracy_percentage", 0)
    total_attempts = metrics.get("total_attempts", 0)
    
    if accuracy == 100:
        achievements.append({
            "type": "perfect_score",
            "title": "Puntuación Perfecta",
            "description": "¡100% de aciertos en la sesión!"
        })
    
    if accuracy >= 90 and total_attempts >= 20:
        achievements.append({
            "type": "expert_performer",
            "title": "Rendimiento Experto",
            "description": "Más del 90% de aciertos con 20+ ejercicios"
        })
    
    # Agregar más lógica de logros según necesidades
    
    return achievements

def _analyze_learning_patterns(unit_progresses: List[PlanProgress]) -> Dict[str, Any]:
    """Analiza patrones de aprendizaje del usuario"""
    if not unit_progresses:
        return {}
    
    # Análisis de consistencia
    scores = [float(up.score) for up in unit_progresses if up.score > 0]
    consistency = 1.0 - (max(scores) - min(scores)) / 100 if len(scores) > 1 else 1.0
    
    # Tendencia de mejora
    improvement_trend = "stable"
    if len(scores) >= 3:
        if scores[-1] > scores[0] + 10:
            improvement_trend = "improving"
        elif scores[-1] < scores[0] - 10:
            improvement_trend = "declining"
    
    return {
        "consistency_score": round(consistency, 2),
        "improvement_trend": improvement_trend,
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "completion_rate": sum(1 for up in unit_progresses if up.is_completed) / len(unit_progresses),
        "learning_velocity": "normal"  # Placeholder for more complex analysis
    }

def _determine_mastery_level(accuracy: float) -> str:
    """Determina el nivel de maestría basado en la precisión"""
    if accuracy >= 95:
        return "master"
    elif accuracy >= 85:
        return "advanced"
    elif accuracy >= 70:
        return "intermediate"
    else:
        return "beginner"

async def _update_user_topic_metrics(user_id: str, plan_id: str, unit_number: int, topic_name: str, attempts: List[ExerciseAttempt], db: Session) -> Dict[str, Any]:
    """Actualiza las métricas del usuario para un tema específico"""
    # En una implementación completa, esto actualizaría una tabla de métricas detalladas
    # Por ahora, retorna métricas calculadas basadas en los intentos actuales
    
    total_attempts = len(attempts)
    correct_attempts = sum(1 for attempt in attempts if attempt.is_correct)
    accuracy = (correct_attempts / total_attempts * 100) if total_attempts > 0 else 0
    avg_response_time = sum(attempt.response_time_ms for attempt in attempts) / total_attempts if attempts else 0
    
    return {
        "total_attempts": total_attempts,
        "correct_attempts": correct_attempts,
        "accuracy_percentage": round(accuracy, 2),
        "average_response_time_ms": round(avg_response_time, 2),
        "mastery_level": _determine_mastery_level(accuracy),
        "last_updated": datetime.now().isoformat()
    }