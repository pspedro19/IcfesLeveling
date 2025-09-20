"""
Student Dashboard API endpoints
Provides comprehensive dashboard data for students including stats, analytics, and recommendations
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

# Create router
router = APIRouter(prefix="/api/student/dashboard", tags=["Student Dashboard"])

# =============================================================================
# DASHBOARD STATS ENDPOINT
# =============================================================================

@router.get("/stats")
async def get_dashboard_stats(
    timeFilter: str = Query("30d", description="Time filter (7d, 30d, 90d)"),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics for the current student
    """
    try:
        # Mock data for now - in production this would query the database
        dashboard_stats = {
            "currentLevel": 15,
            "currentRank": "C",
            "experience": 2847,
            "experienceToNext": 153,
            "totalBattles": 42,
            "winRate": 67.5,
            "currentStreak": 5,
            "mastery": {
                "mathematics": 72.5,
                "physics": 68.2,
                "chemistry": 75.1,
                "biology": 69.8,
                "spanish": 82.3
            },
            "theta": {
                "mathematics": 0.45,
                "physics": 0.32,
                "chemistry": 0.52,
                "biology": 0.38,
                "spanish": 0.67
            },
            "classRanking": 12,
            "nationalRanking": 2847
        }

        return JSONResponse(content=dashboard_stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

# =============================================================================
# THETA EVOLUTION ENDPOINT
# =============================================================================

@router.get("/theta-evolution")
async def get_theta_evolution(
    timeFilter: str = Query("30d", description="Time filter (7d, 30d, 90d)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get theta evolution data over time
    """
    try:
        # Mock data for theta evolution
        days_back = {"7d": 7, "30d": 30, "90d": 90}.get(timeFilter, 30)
        evolution_data = []

        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            evolution_data.append({
                "date": date,
                "mathematics": round(0.3 + (i * 0.005), 3),
                "physics": round(0.25 + (i * 0.004), 3),
                "chemistry": round(0.35 + (i * 0.006), 3),
                "biology": round(0.28 + (i * 0.004), 3),
                "spanish": round(0.5 + (i * 0.007), 3),
                "overall": round(0.34 + (i * 0.005), 3)
            })

        # Reverse to show chronological order
        evolution_data.reverse()

        return JSONResponse(content=evolution_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching theta evolution: {str(e)}")

# =============================================================================
# ERROR ANALYSIS ENDPOINT
# =============================================================================

@router.get("/error-analysis")
async def get_error_analysis(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    reviewed: Optional[str] = Query(None, description="Filter by reviewed status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get error analysis for wrong answers
    """
    try:
        # Mock error analysis data
        error_analysis = [
            {
                "id": "error_001",
                "questionId": "q_12345",
                "subject": "mathematics",
                "topic": "Algebra Lineal",
                "difficulty": 3,
                "irtDifficulty": 0.75,
                "questionText": "Resuelve el sistema de ecuaciones lineales...",
                "questionImage": None,
                "correctAnswer": "B",
                "selectedAnswer": "A",
                "distractors": {
                    "A": "x = 2, y = 3",
                    "B": "x = 3, y = 2",
                    "C": "x = 1, y = 4",
                    "D": "x = 4, y = 1"
                },
                "timeSpent": 185,
                "averageTime": 120,
                "percentile": 65,
                "explanation": "Para resolver este sistema, debes usar eliminación gaussiana...",
                "aiAnalysis": "El estudiante confundió el orden de las variables en la solución final.",
                "conceptsToReinforce": ["Sistemas de ecuaciones", "Eliminación gaussiana", "Sustitución"],
                "date": "2024-01-15T10:30:00Z",
                "wasReviewed": False
            },
            {
                "id": "error_002",
                "questionId": "q_67890",
                "subject": "physics",
                "topic": "Cinemática",
                "difficulty": 2,
                "irtDifficulty": 0.45,
                "questionText": "Un objeto se mueve con velocidad constante...",
                "questionImage": None,
                "correctAnswer": "C",
                "selectedAnswer": "D",
                "distractors": {
                    "A": "10 m/s",
                    "B": "15 m/s",
                    "C": "20 m/s",
                    "D": "25 m/s"
                },
                "timeSpent": 95,
                "averageTime": 110,
                "percentile": 78,
                "explanation": "La velocidad se calcula como distancia sobre tiempo...",
                "aiAnalysis": "Error en la conversión de unidades de tiempo.",
                "conceptsToReinforce": ["Velocidad", "Conversión de unidades", "Cinemática básica"],
                "date": "2024-01-14T14:22:00Z",
                "wasReviewed": True
            }
        ]

        # Apply filters if provided
        if subject:
            error_analysis = [e for e in error_analysis if e["subject"] == subject]
        if difficulty:
            error_analysis = [e for e in error_analysis if str(e["difficulty"]) == difficulty]
        if reviewed:
            reviewed_bool = reviewed.lower() in ["true", "1", "yes"]
            error_analysis = [e for e in error_analysis if e["wasReviewed"] == reviewed_bool]

        return JSONResponse(content=error_analysis)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching error analysis: {str(e)}")

# =============================================================================
# STUDY RECOMMENDATIONS ENDPOINT
# =============================================================================

@router.get("/recommendations")
async def get_study_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized study recommendations
    """
    try:
        # Mock study recommendations
        recommendations = [
            {
                "id": "rec_001",
                "type": "video",
                "title": "Álgebra Lineal: Sistemas de Ecuaciones",
                "description": "Video explicativo sobre resolución de sistemas de ecuaciones lineales",
                "subject": "mathematics",
                "difficulty": "intermediate",
                "estimatedTime": 25,
                "priority": "high",
                "xpReward": 50,
                "progress": 0,
                "completed": False
            },
            {
                "id": "rec_002",
                "type": "practice",
                "title": "Ejercicios de Cinemática",
                "description": "Práctica enfocada en problemas de velocidad y aceleración",
                "subject": "physics",
                "difficulty": "beginner",
                "estimatedTime": 15,
                "priority": "medium",
                "xpReward": 30,
                "progress": 60,
                "completed": False
            },
            {
                "id": "rec_003",
                "type": "quiz",
                "title": "Quiz de Comprensión Lectora",
                "description": "Evaluación de habilidades de lectura crítica",
                "subject": "spanish",
                "difficulty": "intermediate",
                "estimatedTime": 20,
                "priority": "low",
                "xpReward": 40,
                "progress": 100,
                "completed": True
            }
        ]

        return JSONResponse(content=recommendations)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching study recommendations: {str(e)}")

# =============================================================================
# ERROR MANAGEMENT ENDPOINTS
# =============================================================================

@router.put("/errors/{error_id}/reviewed")
async def mark_error_as_reviewed(
    error_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark an error as reviewed
    """
    try:
        # In production, this would update the database
        return JSONResponse(content={"status": "success", "message": f"Error {error_id} marked as reviewed"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking error as reviewed: {str(e)}")

# =============================================================================
# TASK MANAGEMENT ENDPOINTS
# =============================================================================

@router.put("/tasks/{task_id}/progress")
async def update_task_progress(
    task_id: str,
    progress_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update task progress
    """
    try:
        progress = progress_data.get("progress", 0)
        # In production, this would update the database
        return JSONResponse(content={
            "status": "success",
            "message": f"Task {task_id} progress updated to {progress}%"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating task progress: {str(e)}")

# =============================================================================
# STUDY PLAN ENDPOINTS
# =============================================================================

@router.post("/generate-plan")
async def generate_new_study_plan(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate new study plan
    """
    try:
        # In production, this would generate a new study plan based on current performance
        return JSONResponse(content={
            "status": "success",
            "message": "New study plan generated successfully",
            "planId": "plan_new_001"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating new study plan: {str(e)}")

# =============================================================================
# IRT METRICS ENDPOINT
# =============================================================================

@router.get("/irt-metrics")
async def get_irt_metrics(
    subjects: Optional[str] = Query(None, description="Comma-separated list of subjects"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get IRT metrics for specific subjects
    """
    try:
        # Parse subjects if provided
        subject_list = subjects.split(",") if subjects else ["mathematics", "physics", "chemistry", "biology", "spanish"]

        # Mock IRT metrics data
        irt_metrics = {
            "theta": {},
            "difficulty": {},
            "discrimination": {},
            "guessing": {}
        }

        base_values = {
            "mathematics": {"theta": 0.45, "difficulty": 0.62, "discrimination": 1.2, "guessing": 0.15},
            "physics": {"theta": 0.32, "difficulty": 0.58, "discrimination": 1.1, "guessing": 0.18},
            "chemistry": {"theta": 0.52, "difficulty": 0.65, "discrimination": 1.3, "guessing": 0.12},
            "biology": {"theta": 0.38, "difficulty": 0.55, "discrimination": 1.0, "guessing": 0.20},
            "spanish": {"theta": 0.67, "difficulty": 0.48, "discrimination": 1.4, "guessing": 0.10}
        }

        for subject in subject_list:
            if subject in base_values:
                irt_metrics["theta"][subject] = base_values[subject]["theta"]
                irt_metrics["difficulty"][subject] = base_values[subject]["difficulty"]
                irt_metrics["discrimination"][subject] = base_values[subject]["discrimination"]
                irt_metrics["guessing"][subject] = base_values[subject]["guessing"]

        return JSONResponse(content=irt_metrics)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching IRT metrics: {str(e)}")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health")
async def health_check():
    """
    Student dashboard health check
    """
    return JSONResponse(content={
        "status": "healthy",
        "service": "student_dashboard",
        "timestamp": datetime.now().isoformat()
    })