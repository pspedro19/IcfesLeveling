"""
Training Zone API Routes - ICFES Leveling

Comprehensive API endpoints for the training zone system where students
practice with their failed ICFES questions.

Features:
- Training zone initialization and management
- Multiple training modes (Recovery, Sprint, Full Review, Spaced Repetition, Monthly Focus)
- Spaced repetition algorithm
- AI-powered explanations
- YouTube video recommendations
- Progress tracking and analytics
- Monthly rotation system

Author: Claude Code Assistant
Date: 2024
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.training_zone import TrainingMode, DifficultyLevel
from ..services.training_zone_service import TrainingZoneService

router = APIRouter(prefix="/training-zone", tags=["Training Zone"])
logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses

class TrainingSessionRequest(BaseModel):
    subject_id: str = Field(..., description="Subject ID for training")
    mode: TrainingMode = Field(..., description="Training mode")
    target_questions: Optional[int] = Field(None, description="Custom number of questions")
    time_limit_minutes: Optional[int] = Field(None, description="Custom time limit")

class TrainingAnswerRequest(BaseModel):
    question_id: str = Field(..., description="Question ID")
    user_answer: str = Field(..., description="User's answer (A, B, C, D)")
    response_time_seconds: int = Field(..., description="Response time in seconds")
    confidence_level: int = Field(3, ge=1, le=5, description="Confidence level (1-5)")
    quality_rating: Optional[int] = Field(None, ge=0, le=5, description="Quality rating for spaced repetition")

class AIExplanationRequest(BaseModel):
    explanation_type: str = Field("conceptual", description="Type of explanation")

class VideoFeedbackRequest(BaseModel):
    video_recommendation_id: str = Field(..., description="Video recommendation ID")
    was_helpful: bool = Field(..., description="Whether the video was helpful")
    rating: Optional[float] = Field(None, ge=1, le=5, description="Video rating (1-5)")

class MonthlyRotationRequest(BaseModel):
    force_update: bool = Field(False, description="Force monthly rotation update")

# Training Zone Management Endpoints

@router.post("/initialize/{subject_id}")
async def initialize_training_zone(
    subject_id: str = Path(..., description="Subject ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Initialize training zone for a subject based on failed diagnostic questions
    """
    try:
        service = TrainingZoneService(db)
        result = await service.initialize_training_zone(str(current_user.id), subject_id)
        
        if not result["success"]:
            if result.get("action_required") == "complete_diagnostic":
                raise HTTPException(status_code=400, detail={
                    "message": result["message"],
                    "action_required": "complete_diagnostic",
                    "redirect_url": f"/diagnostic/{subject_id}"
                })
            elif result.get("congratulations"):
                return {
                    "success": True,
                    "message": result["message"],
                    "congratulations": True,
                    "perfect_score": True
                }
            else:
                raise HTTPException(status_code=400, detail=result["message"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing training zone: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard/{subject_id}")
async def get_training_zone_dashboard(
    subject_id: str = Path(..., description="Subject ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive training zone dashboard data
    """
    try:
        service = TrainingZoneService(db)
        result = await service.get_training_zone_dashboard(str(current_user.id), subject_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to get dashboard"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training zone dashboard: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/rotate-monthly/{subject_id}")
async def rotate_monthly_training(
    subject_id: str = Path(..., description="Subject ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: MonthlyRotationRequest = None
) -> Dict[str, Any]:
    """
    Trigger monthly rotation of training questions based on latest diagnostic
    """
    try:
        # First get the training zone
        service = TrainingZoneService(db)
        dashboard = await service.get_training_zone_dashboard(str(current_user.id), subject_id)
        
        if not dashboard["success"]:
            raise HTTPException(status_code=400, detail="Training zone not found")
        
        training_zone_id = dashboard["training_zone_id"]
        result = await service.update_training_zone_from_latest_diagnostic(
            training_zone_id, request.force_update
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to rotate training"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rotating monthly training: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Training Session Endpoints

@router.post("/session/start")
async def start_training_session(
    request: TrainingSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Start a new training session with specified mode and settings
    """
    try:
        service = TrainingZoneService(db)
        
        custom_settings = {}
        if request.target_questions:
            custom_settings["target_questions"] = request.target_questions
        if request.time_limit_minutes:
            custom_settings["time_limit_minutes"] = request.time_limit_minutes
        
        result = await service.start_training_session(
            str(current_user.id),
            request.subject_id,
            request.mode,
            custom_settings if custom_settings else None
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to start session"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting training session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/session/{session_id}/answer")
async def submit_training_answer(
    session_id: str = Path(..., description="Training session ID"),
    request: TrainingAnswerRequest = ...,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Submit an answer for a training question
    """
    try:
        service = TrainingZoneService(db)
        result = await service.submit_training_answer(
            session_id,
            request.question_id,
            request.user_answer,
            request.response_time_seconds,
            request.confidence_level,
            request.quality_rating
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to submit answer"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting training answer: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/session/{session_id}/complete")
async def complete_training_session(
    session_id: str = Path(..., description="Training session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Complete a training session and get comprehensive report
    """
    try:
        service = TrainingZoneService(db)
        result = await service.complete_training_session(session_id)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to complete session"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing training session: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/session/{session_id}/status")
async def get_session_status(
    session_id: str = Path(..., description="Training session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get current status of a training session
    """
    try:
        from ..models.training_zone import TrainingSession, TrainingAttempt
        
        # Get session details
        session = db.query(TrainingSession).filter(
            TrainingSession.id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Training session not found")
        
        # Verify user owns this session
        if str(session.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get session attempts
        attempts = db.query(TrainingAttempt).filter(
            TrainingAttempt.training_session_id == session_id
        ).order_by(TrainingAttempt.attempt_number).all()
        
        return {
            "success": True,
            "session": {
                "id": str(session.id),
                "mode": session.mode,
                "status": session.status,
                "target_questions": session.target_questions,
                "questions_answered": session.questions_answered,
                "correct_answers": session.correct_answers,
                "accuracy": session.session_accuracy,
                "current_streak": session.current_streak,
                "max_streak": session.max_streak_in_session,
                "time_limit_minutes": session.time_limit_minutes,
                "started_at": session.started_at.isoformat(),
                "completed_at": session.completed_at.isoformat() if session.completed_at else None
            },
            "attempts": [
                {
                    "question_id": str(attempt.question_id),
                    "is_correct": attempt.is_correct,
                    "response_time_seconds": attempt.response_time_seconds,
                    "quality_rating": attempt.quality_rating,
                    "attempt_number": attempt.attempt_number
                }
                for attempt in attempts
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/session/{session_id}/results")
async def get_session_results(
    session_id: str = Path(..., description="Training session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive results and analytics for a completed training session
    """
    try:
        service = TrainingZoneService(db)
        result = await service.get_session_results(session_id, str(current_user.id))
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to get session results"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session results: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/session/{session_id}/next-question")
async def get_next_question(
    session_id: str = Path(..., description="Training session ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get the next question for a training session
    """
    try:
        service = TrainingZoneService(db)
        result = await service.get_next_question(session_id, str(current_user.id))
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to get next question"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next question: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# AI Explanation Endpoints

@router.post("/explanation/{training_attempt_id}")
async def get_ai_explanation(
    training_attempt_id: str = Path(..., description="Training attempt ID"),
    request: AIExplanationRequest = AIExplanationRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get AI-powered explanation for a training question
    """
    try:
        service = TrainingZoneService(db)
        result = await service.get_ai_explanation(training_attempt_id, request.explanation_type)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to get explanation"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting AI explanation: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/explanation/{explanation_id}/feedback")
async def submit_explanation_feedback(
    explanation_id: str = Path(..., description="AI explanation ID"),
    helpful: bool = Query(..., description="Whether explanation was helpful"),
    quality_rating: Optional[float] = Query(None, ge=1, le=5, description="Quality rating"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Submit feedback on AI explanation quality
    """
    try:
        from ..models.training_zone import TrainingAIExplanation
        
        explanation = db.query(TrainingAIExplanation).filter(
            TrainingAIExplanation.id == explanation_id
        ).first()
        
        if not explanation:
            raise HTTPException(status_code=404, detail="AI explanation not found")
        
        # Verify user owns this explanation
        if str(explanation.user_id) != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update feedback
        explanation.was_helpful = helpful
        if quality_rating:
            explanation.explanation_quality = quality_rating
        
        db.commit()
        
        return {
            "success": True,
            "message": "Feedback submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting explanation feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Video Recommendation Endpoints

@router.get("/videos/{training_question_id}")
async def get_video_recommendations(
    training_question_id: str = Path(..., description="Training question ID"),
    limit: int = Query(3, ge=1, le=10, description="Number of recommendations"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get YouTube video recommendations for a training question
    """
    try:
        service = TrainingZoneService(db)
        result = await service.get_video_recommendations(training_question_id, limit)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to get recommendations"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting video recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/videos/{recommendation_id}/feedback")
async def submit_video_feedback(
    recommendation_id: str = Path(..., description="Video recommendation ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: VideoFeedbackRequest = None
) -> Dict[str, Any]:
    """
    Submit feedback on video recommendation
    """
    try:
        from ..models.training_zone import TrainingVideoRecommendation
        
        recommendation = db.query(TrainingVideoRecommendation).filter(
            TrainingVideoRecommendation.id == recommendation_id
        ).first()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Video recommendation not found")
        
        # Update feedback
        recommendation.helped_with_question = request.was_helpful
        if request.rating:
            recommendation.user_rating = request.rating
        
        # Update interaction stats
        if request.was_helpful:
            recommendation.times_watched_full += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": "Video feedback submitted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting video feedback: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/videos/{recommendation_id}/track-view")
async def track_video_view(
    recommendation_id: str = Path(..., description="Video recommendation ID"),
    watched_duration_seconds: int = Query(..., description="Duration watched in seconds"),
    completed: bool = Query(False, description="Whether video was watched completely"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Track video viewing for analytics
    """
    try:
        from ..models.training_zone import TrainingVideoRecommendation
        
        recommendation = db.query(TrainingVideoRecommendation).filter(
            TrainingVideoRecommendation.id == recommendation_id
        ).first()
        
        if not recommendation:
            raise HTTPException(status_code=404, detail="Video recommendation not found")
        
        # Update viewing stats
        recommendation.times_clicked += 1
        if completed:
            recommendation.times_watched_full += 1
        
        db.commit()
        
        return {
            "success": True,
            "message": "Video view tracked successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking video view: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analytics and Reporting Endpoints

@router.get("/analytics/{subject_id}")
async def get_training_analytics(
    subject_id: str = Path(..., description="Subject ID"),
    period: str = Query("current_month", description="Analytics period"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed training analytics for a subject
    """
    try:
        from ..models.training_zone import TrainingZone, TrainingSession, TrainingAttempt
        from sqlalchemy import func, and_
        
        # Get training zone
        training_zone = db.query(TrainingZone).filter(
            and_(
                TrainingZone.user_id == current_user.id,
                TrainingZone.subject_id == subject_id
            )
        ).first()
        
        if not training_zone:
            raise HTTPException(status_code=404, detail="Training zone not found")
        
        # Calculate date range based on period
        if period == "current_month":
            start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == "last_month":
            import calendar
            now = datetime.now()
            if now.month == 1:
                start_date = now.replace(year=now.year-1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                start_date = now.replace(month=now.month-1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get sessions in period
        sessions = db.query(TrainingSession).filter(
            and_(
                TrainingSession.training_zone_id == training_zone.id,
                TrainingSession.started_at >= start_date
            )
        ).all()
        
        # Calculate analytics
        total_sessions = len(sessions)
        total_questions = sum(s.questions_answered for s in sessions)
        total_correct = sum(s.correct_answers for s in sessions)
        avg_accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 0
        
        # Performance by mode
        mode_stats = {}
        for session in sessions:
            mode = session.mode
            if mode not in mode_stats:
                mode_stats[mode] = {"sessions": 0, "questions": 0, "correct": 0, "accuracy": 0}
            
            mode_stats[mode]["sessions"] += 1
            mode_stats[mode]["questions"] += session.questions_answered
            mode_stats[mode]["correct"] += session.correct_answers
            
            if mode_stats[mode]["questions"] > 0:
                mode_stats[mode]["accuracy"] = (mode_stats[mode]["correct"] / mode_stats[mode]["questions"]) * 100
        
        return {
            "success": True,
            "period": period,
            "analytics": {
                "overview": {
                    "total_sessions": total_sessions,
                    "total_questions": total_questions,
                    "total_correct": total_correct,
                    "average_accuracy": avg_accuracy,
                    "current_streak": training_zone.current_training_streak,
                    "mastery_level": training_zone.mastery_level
                },
                "by_mode": mode_stats,
                "training_zone_stats": {
                    "total_lifetime_sessions": training_zone.total_training_sessions,
                    "total_lifetime_questions": training_zone.total_questions_practiced,
                    "overall_accuracy": training_zone.average_session_accuracy,
                    "improvement_rate": training_zone.improvement_rate
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training analytics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/progress/{subject_id}")
async def get_progress_tracking(
    subject_id: str = Path(..., description="Subject ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed progress tracking separate from diagnostic tests
    """
    try:
        from ..models.training_zone import TrainingZone, TrainingZoneQuestion
        from sqlalchemy import and_, func
        
        # Get training zone
        training_zone = db.query(TrainingZone).filter(
            and_(
                TrainingZone.user_id == current_user.id,
                TrainingZone.subject_id == subject_id
            )
        ).first()
        
        if not training_zone:
            raise HTTPException(status_code=404, detail="Training zone not found")
        
        # Get question progress
        questions = db.query(TrainingZoneQuestion).filter(
            TrainingZoneQuestion.training_zone_id == training_zone.id
        ).all()
        
        # Calculate progress metrics
        total_questions = len(questions)
        mastered_questions = sum(1 for q in questions if q.is_mastered)
        in_progress = total_questions - mastered_questions
        
        # Questions by priority
        priority_distribution = {}
        for q in questions:
            priority = q.priority_level
            if priority not in priority_distribution:
                priority_distribution[priority] = {"total": 0, "mastered": 0}
            priority_distribution[priority]["total"] += 1
            if q.is_mastered:
                priority_distribution[priority]["mastered"] += 1
        
        # Time improvement metrics
        questions_with_improvement = [q for q in questions if q.time_improvement_percent > 0]
        avg_time_improvement = sum(q.time_improvement_percent for q in questions_with_improvement) / len(questions_with_improvement) if questions_with_improvement else 0
        
        # Spaced repetition status
        due_today = sum(1 for q in questions if q.next_review_date.date() <= datetime.now().date() and not q.is_mastered)
        overdue = sum(1 for q in questions if q.next_review_date.date() < datetime.now().date() and not q.is_mastered)
        
        return {
            "success": True,
            "progress": {
                "overview": {
                    "total_questions": total_questions,
                    "mastered_questions": mastered_questions,
                    "in_progress": in_progress,
                    "mastery_percentage": (mastered_questions / total_questions) * 100 if total_questions > 0 else 0
                },
                "by_priority": priority_distribution,
                "time_improvement": {
                    "questions_improved": len(questions_with_improvement),
                    "average_improvement_percent": avg_time_improvement
                },
                "spaced_repetition": {
                    "due_today": due_today,
                    "overdue": overdue,
                    "mastered": mastered_questions,
                    "learning": in_progress
                },
                "monthly_progress": training_zone.monthly_stats or {},
                "streak_info": {
                    "current_streak": training_zone.current_training_streak,
                    "max_streak": training_zone.max_training_streak
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting progress tracking: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Utility Endpoints

@router.get("/modes")
async def get_training_modes() -> Dict[str, Any]:
    """
    Get available training modes with descriptions
    """
    return {
        "success": True,
        "modes": {
            "recovery": {
                "name": "Recovery Mode",
                "description": "Practice 20 prioritized questions based on recency and severity",
                "duration_minutes": 30,
                "question_limit": 20,
                "focus": "Recent failures and high-priority questions"
            },
            "sprint": {
                "name": "Sprint Mode", 
                "description": "Quick 10-minute session with top 10 critical questions",
                "duration_minutes": 10,
                "question_limit": 10,
                "focus": "Critical errors that need immediate attention"
            },
            "full_review": {
                "name": "Full Review Mode",
                "description": "Comprehensive review of all failed questions",
                "duration_minutes": 60,
                "question_limit": 50,
                "focus": "Complete coverage of all learning gaps"
            },
            "spaced_rep": {
                "name": "Spaced Repetition Mode",
                "description": "Questions scheduled based on spaced repetition algorithm",
                "duration_minutes": 25,
                "question_limit": 15,
                "focus": "Optimized long-term retention"
            },
            "monthly_focus": {
                "name": "Monthly Focus Mode",
                "description": "Focus on current month's failed questions",
                "duration_minutes": 35,
                "question_limit": 25,
                "focus": "Recent diagnostic failures"
            }
        }
    }

@router.get("/health")
async def training_zone_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for training zone system
    """
    return {
        "success": True,
        "status": "healthy",
        "features": {
            "spaced_repetition": "active",
            "ai_explanations": "active", 
            "video_recommendations": "active",
            "monthly_rotation": "active",
            "adaptive_difficulty": "active",
            "progress_tracking": "active"
        },
        "version": "1.0.0"
    }