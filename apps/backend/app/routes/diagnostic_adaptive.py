"""
Adaptive Diagnostic Routes
Enhanced diagnostic test routes with real-time adaptation and comprehensive analytics
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.diagnostic_test import (
    DiagnosticTestCreate,
    DiagnosticTestResponse,
    DiagnosticTestQuestion,
    DiagnosticResultResponse,
    DiagnosticAnswerSubmit
)
from ..services.adaptive_diagnostic_service import AdaptiveDiagnosticService
from ..models.user import User
from ..models.subject import Subject

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnostic/adaptive", tags=["adaptive-diagnostic"])

@router.post("/tests", response_model=DiagnosticTestResponse)
async def create_adaptive_diagnostic_test(
    test_data: DiagnosticTestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new adaptive diagnostic test with AI-powered question selection"""
    try:
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Validate subject exists
        subject = db.query(Subject).filter(Subject.id == test_data.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
            
        test = adaptive_service.create_adaptive_diagnostic_test(
            user_id=str(current_user.id),
            subject_id=test_data.subject_id,
            test_type="adaptive_icfes"
        )
        
        logger.info(f"Created adaptive diagnostic test {test.id} for user {current_user.id}")
        
        return {
            "id": str(test.id),
            "user_id": str(test.user_id),
            "subject_id": str(test.subject_id),
            "test_type": test.test_type,
            "questions_answered": test.questions_answered,
            "correct_answers": test.correct_answers,
            "time_spent_seconds": test.time_spent_seconds,
            "score_percentage": float(test.score_percentage),
            "strengths": test.strengths,
            "weaknesses": test.weaknesses,
            "score_by_topic": test.score_by_topic,
            "status": test.status,
            "started_at": test.started_at,
            "completed_at": test.completed_at,
            "created_at": test.created_at
        }
    except Exception as e:
        logger.error(f"Error creating adaptive diagnostic test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creando test adaptativo: {str(e)}")

@router.get("/tests/{test_id}/questions", response_model=List[DiagnosticTestQuestion])
async def get_adaptive_diagnostic_questions(
    test_id: str,
    num_questions: Optional[int] = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get adaptively selected questions based on user's current ability level"""
    try:
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Verify test ownership
        test = adaptive_service.get_diagnostic_test_by_id(test_id)
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test no encontrado o acceso denegado")
            
        if test.status != "in_progress":
            raise HTTPException(status_code=400, detail="El test no está en progreso")
            
        questions = adaptive_service.get_adaptive_diagnostic_questions(
            test_id=test_id,
            user_id=str(current_user.id),
            num_questions=min(num_questions, 50)  # Limit to 50 questions max
        )
        
        logger.info(f"Retrieved {len(questions)} adaptive questions for test {test_id}")
        
        return questions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting adaptive questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo preguntas adaptativas: {str(e)}")

@router.post("/tests/{test_id}/answer")
async def submit_single_answer(
    test_id: str,
    answer_data: DiagnosticAnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a single answer and get real-time adaptation feedback"""
    try:
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Verify test ownership
        test = adaptive_service.get_diagnostic_test_by_id(test_id)
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test no encontrado o acceso denegado")
            
        if test.status != "in_progress":
            raise HTTPException(status_code=400, detail="El test no está en progreso")
        
        # Process the answer with adaptive feedback
        result = adaptive_service.process_adaptive_answer(
            test_id=test_id,
            question_id=answer_data.question_id,
            user_answer=answer_data.user_answer.upper(),
            response_time_ms=min(answer_data.response_time_ms, 300000)  # Max 5 minutes
        )
        
        logger.info(f"Processed adaptive answer for test {test_id}, question {answer_data.question_id}")
        
        return {
            "success": True,
            "correct": result["correct"],
            "ability_change": result["theta_change"],
            "next_difficulty": result["next_recommended_difficulty"],
            "confidence_level": f"{result['confidence_interval'][0]:.2f} - {result['confidence_interval'][1]:.2f}",
            "performance_trend": result["performance_trend"],
            "feedback": {
                "message": "¡Respuesta correcta! Tu nivel aumentó." if result["correct"] and result["theta_change"] > 0
                          else "Respuesta correcta. Mantén el buen trabajo." if result["correct"]
                          else "Respuesta incorrecta. No te desanimes, sigue intentando." if result["theta_change"] > -0.2
                          else "Respuesta incorrecta. Considera revisar el concepto.",
                "encouragement": self._get_encouragement_message(result)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing adaptive answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando respuesta: {str(e)}")

@router.post("/tests/{test_id}/finalize", response_model=DiagnosticResultResponse)
async def finalize_adaptive_test(
    test_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Finalize adaptive test with comprehensive analysis and gamification rewards"""
    try:
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Verify test ownership
        test = adaptive_service.get_diagnostic_test_by_id(test_id)
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test no encontrado o acceso denegado")
            
        if test.status == "completed":
            raise HTTPException(status_code=400, detail="El test ya fue finalizado")
            
        # Finalize the test with comprehensive analysis
        result = adaptive_service.finalize_adaptive_test(test_id)
        
        # Schedule background tasks
        background_tasks.add_task(
            _create_study_plan_from_diagnostic,
            db, str(current_user.id), test_id, result
        )
        background_tasks.add_task(
            _update_user_analytics,
            db, str(current_user.id), result
        )
        
        logger.info(f"Finalized adaptive test {test_id} with score {result['icfes_score']}%")
        
        # Format response to match frontend expectations
        return {
            "score": result["correct_answers"],
            "percentage": int(result["icfes_score"]),
            "strengths": result["strengths"],
            "weaknesses": result["weaknesses"],
            "recommendations": result["recommendations"],
            "advanced_metrics": {
                "rank": result["rank"],
                "theta_estimate": result["final_theta"],
                "mastery_level": adaptive_service._get_mastery_level(result["final_theta"]),
                "consistency_score": result.get("consistency_score", 0.5),
                "gamification": result["gamification"],
                "next_steps": result["next_steps"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finalizing adaptive test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error finalizando test: {str(e)}")

@router.get("/tests/{test_id}/progress")
async def get_test_progress(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time progress and adaptation metrics for ongoing test"""
    try:
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Verify test ownership
        test = adaptive_service.get_diagnostic_test_by_id(test_id)
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test no encontrado")
            
        # Get test answers for progress calculation
        answers = adaptive_service.get_diagnostic_test_answers(test_id)
        
        # Extract adaptive parameters
        adaptive_params = test.score_by_topic.get("adaptive_params", {})
        
        # Calculate current metrics
        total_answered = len(answers)
        correct_answers = sum(1 for a in answers if a.is_correct)
        current_accuracy = (correct_answers / total_answered) * 100 if total_answered > 0 else 0
        
        return {
            "test_id": test_id,
            "status": test.status,
            "questions_answered": total_answered,
            "current_accuracy": current_accuracy,
            "estimated_ability": adaptive_params.get("current_theta", 0.0),
            "difficulty_progression": adaptive_params.get("difficulty_progression", []),
            "adaptation_history": adaptive_params.get("adaptation_history", [])[-5:],  # Last 5 adaptations
            "performance_trend": adaptive_service._analyze_performance_trend(
                adaptive_params.get("adaptation_history", [])[-5:]
            ),
            "time_elapsed": (datetime.utcnow() - test.started_at).total_seconds() if test.started_at else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting test progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo progreso: {str(e)}")

@router.get("/user/history")
async def get_user_diagnostic_history(
    limit: Optional[int] = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's diagnostic test history with trend analysis"""
    try:
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Get user's completed tests
        tests = adaptive_service.get_user_diagnostic_tests(str(current_user.id))
        completed_tests = [t for t in tests if t.status == "completed"][:limit]
        
        if not completed_tests:
            return {
                "tests": [],
                "trends": {
                    "improvement_rate": 0,
                    "consistency": 0,
                    "strongest_subject": None,
                    "areas_for_improvement": []
                }
            }
        
        # Calculate trends
        scores = [t.score_percentage for t in completed_tests if t.score_percentage]
        improvement_rate = 0
        if len(scores) >= 2:
            improvement_rate = (scores[0] - scores[-1]) / len(scores)
        
        # Format tests for response
        test_history = []
        for test in completed_tests:
            adaptive_params = test.score_by_topic.get("adaptive_params", {})
            final_metrics = test.score_by_topic.get("final_metrics", {})
            
            test_history.append({
                "id": str(test.id),
                "subject": test.subject.name if test.subject else "Unknown",
                "score_percentage": test.score_percentage,
                "rank": final_metrics.get("rank", "E"),
                "questions_answered": test.questions_answered,
                "date_completed": test.completed_at,
                "time_spent_minutes": test.time_spent_seconds / 60 if test.time_spent_seconds else 0,
                "final_theta": adaptive_params.get("current_theta", 0),
                "mastery_level": adaptive_service._get_mastery_level(adaptive_params.get("current_theta", 0))
            })
        
        return {
            "tests": test_history,
            "trends": {
                "improvement_rate": improvement_rate,
                "consistency": _calculate_score_consistency(scores),
                "total_tests": len(completed_tests),
                "average_score": sum(scores) / len(scores) if scores else 0,
                "best_score": max(scores) if scores else 0,
                "recent_performance": scores[:3] if len(scores) >= 3 else scores
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user diagnostic history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo historial: {str(e)}")

@router.get("/analytics/performance")
async def get_performance_analytics(
    subject_id: Optional[str] = None,
    days: Optional[int] = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed performance analytics for the user"""
    try:
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Get tests from specified period
        from_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(adaptive_service.DiagnosticTest).filter(
            adaptive_service.DiagnosticTest.user_id == current_user.id,
            adaptive_service.DiagnosticTest.status == "completed",
            adaptive_service.DiagnosticTest.completed_at >= from_date
        )
        
        if subject_id:
            query = query.filter(adaptive_service.DiagnosticTest.subject_id == subject_id)
            
        tests = query.all()
        
        if not tests:
            return {"message": "No hay datos suficientes para el análisis"}
        
        # Calculate comprehensive analytics
        analytics = {
            "overview": {
                "total_tests": len(tests),
                "average_score": sum(t.score_percentage for t in tests) / len(tests),
                "improvement_trend": _calculate_improvement_trend(tests),
                "consistency_rating": _calculate_consistency_rating(tests)
            },
            "ability_progression": [
                {
                    "date": test.completed_at,
                    "theta": test.score_by_topic.get("adaptive_params", {}).get("current_theta", 0),
                    "score": test.score_percentage,
                    "rank": test.score_by_topic.get("final_metrics", {}).get("rank", "E")
                }
                for test in tests
            ],
            "subject_breakdown": _analyze_subject_performance(tests),
            "recommendations": _generate_performance_recommendations(tests)
        }
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error getting performance analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo analíticas: {str(e)}")

# Helper functions

async def _create_study_plan_from_diagnostic(db: Session, user_id: str, test_id: str, result: Dict[str, Any]):
    """Background task to create study plan from diagnostic results"""
    try:
        # This would integrate with the study plan generation service
        logger.info(f"Creating study plan for user {user_id} based on test {test_id}")
        # Implementation would go here
    except Exception as e:
        logger.error(f"Error creating study plan: {str(e)}")

async def _update_user_analytics(db: Session, user_id: str, result: Dict[str, Any]):
    """Background task to update user analytics"""
    try:
        # Update user analytics and achievement progress
        logger.info(f"Updating analytics for user {user_id}")
        # Implementation would go here
    except Exception as e:
        logger.error(f"Error updating user analytics: {str(e)}")

def _get_encouragement_message(result: Dict[str, Any]) -> str:
    """Get encouraging message based on performance"""
    if result["correct"] and result["theta_change"] > 0.2:
        return "¡Excelente! Estás demostrando un dominio sólido."
    elif result["correct"]:
        return "¡Bien hecho! Sigue con ese ritmo."
    elif result["theta_change"] > -0.1:
        return "Cerca de la respuesta correcta. No te rindas."
    else:
        return "Cada error es una oportunidad de aprender. ¡Sigue adelante!"

def _calculate_score_consistency(scores: List[float]) -> float:
    """Calculate consistency score from a list of scores"""
    if len(scores) < 2:
        return 1.0
        
    mean_score = sum(scores) / len(scores)
    variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
    
    # Normalize to 0-1 scale (lower variance = higher consistency)
    consistency = 1 / (1 + variance / 100)
    return min(1.0, max(0.0, consistency))

def _calculate_improvement_trend(tests: List) -> str:
    """Calculate improvement trend from test history"""
    if len(tests) < 3:
        return "insufficient_data"
        
    scores = [t.score_percentage for t in sorted(tests, key=lambda x: x.completed_at)]
    recent_avg = sum(scores[-3:]) / 3
    older_avg = sum(scores[:-3]) / len(scores[:-3]) if len(scores) > 3 else scores[0]
    
    if recent_avg > older_avg + 5:
        return "improving"
    elif recent_avg < older_avg - 5:
        return "declining"
    else:
        return "stable"

def _calculate_consistency_rating(tests: List) -> str:
    """Calculate consistency rating from test history"""
    if len(tests) < 3:
        return "insufficient_data"
        
    scores = [t.score_percentage for t in tests]
    consistency = _calculate_score_consistency(scores)
    
    if consistency > 0.8:
        return "very_consistent"
    elif consistency > 0.6:
        return "consistent"
    elif consistency > 0.4:
        return "somewhat_consistent"
    else:
        return "inconsistent"

def _analyze_subject_performance(tests: List) -> Dict[str, Any]:
    """Analyze performance by subject"""
    subject_data = {}
    
    for test in tests:
        subject_name = test.subject.name if test.subject else "Unknown"
        if subject_name not in subject_data:
            subject_data[subject_name] = {
                "tests": 0,
                "total_score": 0,
                "best_score": 0,
                "latest_rank": "E"
            }
        
        data = subject_data[subject_name]
        data["tests"] += 1
        data["total_score"] += test.score_percentage
        data["best_score"] = max(data["best_score"], test.score_percentage)
        data["latest_rank"] = test.score_by_topic.get("final_metrics", {}).get("rank", "E")
    
    # Calculate averages
    for subject, data in subject_data.items():
        data["average_score"] = data["total_score"] / data["tests"]
    
    return subject_data

def _generate_performance_recommendations(tests: List) -> List[str]:
    """Generate recommendations based on test history"""
    recommendations = []
    
    if len(tests) < 2:
        recommendations.append("Toma más tests para obtener recomendaciones personalizadas")
        return recommendations
    
    # Analyze trends
    scores = [t.score_percentage for t in sorted(tests, key=lambda x: x.completed_at)]
    trend = _calculate_improvement_trend(tests)
    
    if trend == "improving":
        recommendations.append("¡Excelente progreso! Mantén tu rutina de estudio actual")
    elif trend == "declining":
        recommendations.append("Considera ajustar tu estrategia de estudio")
    
    # Consistency analysis
    consistency = _calculate_score_consistency(scores)
    if consistency < 0.6:
        recommendations.append("Trabaja en mantener un rendimiento más consistente")
    
    # Score-based recommendations
    avg_score = sum(scores) / len(scores)
    if avg_score < 60:
        recommendations.append("Enfócate en dominar conceptos fundamentales")
    elif avg_score > 80:
        recommendations.append("Considera desafiarte con material más avanzado")
    
    return recommendations