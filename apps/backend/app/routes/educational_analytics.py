from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, case, cast, Float, distinct
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
import math

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.battle import Battle, BattleAnswer
from ..models.question import Question
from ..models.subject import Subject
from ..models.topic import Topic

router = APIRouter(prefix="/educational-analytics", tags=["educational-analytics"])
logger = logging.getLogger(__name__)

@router.get("/educational-insights")
async def get_educational_insights(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get educational insights and learning analytics"""
    try:
        # Get question difficulty distribution
        difficulty_analysis = db.query(
            func.round(Question.difficulty, 1).label('difficulty_level'),
            func.count(Question.id).label('question_count'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('success_rate')
        ).outerjoin(
            BattleAnswer, BattleAnswer.question_id == Question.id
        ).group_by(
            func.round(Question.difficulty, 1)
        ).all()
        
        # Get topic mastery levels
        topic_mastery = db.query(
            Topic.name.label('topic_name'),
            Subject.name.label('subject_name'),
            func.count(distinct(BattleAnswer.id)).label('attempts'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('mastery_rate'),
            func.avg(Question.difficulty).label('avg_difficulty')
        ).join(
            Question, Question.topic_id == Topic.id
        ).join(
            Subject, Subject.id == Question.subject_id
        ).outerjoin(
            BattleAnswer, BattleAnswer.question_id == Question.id
        ).group_by(
            Topic.name, Subject.name
        ).having(
            func.count(distinct(BattleAnswer.id)) > 0
        ).all()
        
        # Get learning curve analysis
        learning_curve = db.query(
            func.date(Battle.created_at).label('date'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('daily_accuracy'),
            func.count(distinct(Battle.user_id)).label('active_users'),
            func.avg(Battle.duration_seconds).label('avg_session_time')
        ).join(
            BattleAnswer, BattleAnswer.battle_id == Battle.id
        ).filter(
            Battle.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            func.date(Battle.created_at)
        ).order_by(
            func.date(Battle.created_at)
        ).all()
        
        return {
            "difficulty_analysis": [
                {
                    "difficulty_level": float(row.difficulty_level),
                    "question_count": row.question_count,
                    "success_rate": float(row.success_rate or 0)
                }
                for row in difficulty_analysis
            ],
            "topic_mastery": [
                {
                    "topic_name": row.topic_name,
                    "subject_name": row.subject_name,
                    "attempts": row.attempts,
                    "mastery_rate": float(row.mastery_rate or 0),
                    "avg_difficulty": float(row.avg_difficulty or 0)
                }
                for row in topic_mastery
            ],
            "learning_curve": [
                {
                    "date": row.date.isoformat(),
                    "daily_accuracy": float(row.daily_accuracy or 0),
                    "active_users": row.active_users,
                    "avg_session_time": float(row.avg_session_time or 0)
                }
                for row in learning_curve
            ]
        }
    except Exception as e:
        logger.error(f"Error getting educational insights: {e}")
        raise HTTPException(status_code=500, detail="Error getting educational insights")

@router.get("/question-difficulty-analysis")
async def get_question_difficulty_analysis(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze question difficulty patterns and effectiveness"""
    try:
        # Question difficulty effectiveness
        difficulty_effectiveness = db.query(
            Question.id,
            Question.content[:100].label('question_preview'),
            Question.difficulty,
            Subject.name.label('subject_name'),
            Topic.name.label('topic_name'),
            func.count(BattleAnswer.id).label('attempts'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('success_rate'),
            func.avg(BattleAnswer.response_time_seconds).label('avg_response_time')
        ).join(
            Subject, Subject.id == Question.subject_id
        ).join(
            Topic, Topic.id == Question.topic_id
        ).outerjoin(
            BattleAnswer, BattleAnswer.question_id == Question.id
        ).group_by(
            Question.id, Question.content, Question.difficulty, 
            Subject.name, Topic.name
        ).having(
            func.count(BattleAnswer.id) >= 5  # Minimum attempts for valid statistics
        ).order_by(
            desc(func.count(BattleAnswer.id))
        ).limit(100).all()
        
        # IRT-like analysis for adaptive difficulty
        adaptive_recommendations = []
        for q in difficulty_effectiveness:
            expected_success = 1 / (1 + math.exp(-(q.difficulty - 5)))  # IRT-like model
            actual_success = q.success_rate or 0
            
            # Recommend difficulty adjustment
            difficulty_adjustment = 0
            if actual_success > expected_success + 0.2:
                difficulty_adjustment = 1  # Too easy, increase difficulty
            elif actual_success < expected_success - 0.2:
                difficulty_adjustment = -1  # Too hard, decrease difficulty
            
            adaptive_recommendations.append({
                "question_id": str(q.id),
                "question_preview": q.question_preview,
                "current_difficulty": q.difficulty,
                "subject": q.subject_name,
                "topic": q.topic_name,
                "attempts": q.attempts,
                "success_rate": actual_success,
                "expected_success": expected_success,
                "avg_response_time": q.avg_response_time or 0,
                "difficulty_adjustment": difficulty_adjustment,
                "is_well_calibrated": abs(actual_success - expected_success) < 0.1
            })
        
        return {
            "total_questions_analyzed": len(adaptive_recommendations),
            "well_calibrated_questions": len([q for q in adaptive_recommendations if q["is_well_calibrated"]]),
            "questions_need_adjustment": len([q for q in adaptive_recommendations if q["difficulty_adjustment"] != 0]),
            "recommendations": adaptive_recommendations
        }
    except Exception as e:
        logger.error(f"Error analyzing question difficulty: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing question difficulty")

@router.get("/student-progress-analytics")
async def get_student_progress_analytics(
    student_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive student progress analytics with learning curve analysis"""
    try:
        target_user_id = student_id if student_id and current_user.is_admin else str(current_user.id)
        
        # Learning curve over time
        daily_progress = db.query(
            func.date(Battle.created_at).label('date'),
            func.count(Battle.id).label('battles_count'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('accuracy'),
            func.avg(Battle.duration_seconds).label('avg_duration'),
            func.sum(Battle.experience_gained).label('experience_gained'),
            func.avg(Question.difficulty).label('avg_difficulty_attempted')
        ).join(
            BattleAnswer, BattleAnswer.battle_id == Battle.id
        ).join(
            Question, Question.id == BattleAnswer.question_id
        ).filter(
            Battle.user_id == target_user_id,
            Battle.created_at >= datetime.utcnow() - timedelta(days=90)
        ).group_by(
            func.date(Battle.created_at)
        ).order_by(
            func.date(Battle.created_at)
        ).all()
        
        # Subject-wise progress
        subject_progress = db.query(
            Subject.name.label('subject_name'),
            func.count(BattleAnswer.id).label('questions_answered'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('accuracy'),
            func.avg(Question.difficulty).label('avg_difficulty'),
            func.min(Battle.created_at).label('first_attempt'),
            func.max(Battle.created_at).label('last_attempt'),
            func.sum(Battle.experience_gained).label('total_experience')
        ).join(
            Question, Question.subject_id == Subject.id
        ).join(
            BattleAnswer, BattleAnswer.question_id == Question.id
        ).join(
            Battle, Battle.id == BattleAnswer.battle_id
        ).filter(
            Battle.user_id == target_user_id
        ).group_by(
            Subject.name
        ).all()
        
        # Weakness identification
        weak_topics = db.query(
            Topic.name.label('topic_name'),
            Subject.name.label('subject_name'),
            func.count(BattleAnswer.id).label('attempts'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('success_rate'),
            func.avg(Question.difficulty).label('avg_difficulty')
        ).join(
            Question, Question.topic_id == Topic.id
        ).join(
            Subject, Subject.id == Question.subject_id
        ).join(
            BattleAnswer, BattleAnswer.question_id == Question.id
        ).join(
            Battle, Battle.id == BattleAnswer.battle_id
        ).filter(
            Battle.user_id == target_user_id
        ).group_by(
            Topic.name, Subject.name
        ).having(
            func.count(BattleAnswer.id) >= 3  # Minimum attempts
        ).order_by(
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0))
        ).limit(10).all()
        
        # Strengths identification
        strong_topics = db.query(
            Topic.name.label('topic_name'),
            Subject.name.label('subject_name'),
            func.count(BattleAnswer.id).label('attempts'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('success_rate'),
            func.avg(Question.difficulty).label('avg_difficulty')
        ).join(
            Question, Question.topic_id == Topic.id
        ).join(
            Subject, Subject.id == Question.subject_id
        ).join(
            BattleAnswer, BattleAnswer.question_id == Question.id
        ).join(
            Battle, Battle.id == BattleAnswer.battle_id
        ).filter(
            Battle.user_id == target_user_id
        ).group_by(
            Topic.name, Subject.name
        ).having(
            func.count(BattleAnswer.id) >= 3,  # Minimum attempts
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)) >= 0.7  # Good performance
        ).order_by(
            desc(func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)))
        ).limit(10).all()
        
        return {
            "learning_curve": [
                {
                    "date": row.date.isoformat(),
                    "battles_count": row.battles_count,
                    "accuracy": float(row.accuracy or 0),
                    "avg_duration": float(row.avg_duration or 0),
                    "experience_gained": row.experience_gained or 0,
                    "avg_difficulty_attempted": float(row.avg_difficulty_attempted or 0)
                }
                for row in daily_progress
            ],
            "subject_progress": [
                {
                    "subject_name": row.subject_name,
                    "questions_answered": row.questions_answered,
                    "accuracy": float(row.accuracy or 0),
                    "avg_difficulty": float(row.avg_difficulty or 0),
                    "first_attempt": row.first_attempt.isoformat() if row.first_attempt else None,
                    "last_attempt": row.last_attempt.isoformat() if row.last_attempt else None,
                    "total_experience": row.total_experience or 0
                }
                for row in subject_progress
            ],
            "weaknesses": [
                {
                    "topic_name": row.topic_name,
                    "subject_name": row.subject_name,
                    "attempts": row.attempts,
                    "success_rate": float(row.success_rate or 0),
                    "avg_difficulty": float(row.avg_difficulty or 0)
                }
                for row in weak_topics
            ],
            "strengths": [
                {
                    "topic_name": row.topic_name,
                    "subject_name": row.subject_name,
                    "attempts": row.attempts,
                    "success_rate": float(row.success_rate or 0),
                    "avg_difficulty": float(row.avg_difficulty or 0)
                }
                for row in strong_topics
            ]
        }
    except Exception as e:
        logger.error(f"Error getting student progress analytics: {e}")
        raise HTTPException(status_code=500, detail="Error getting student progress analytics")

@router.get("/system-performance-metrics")
async def get_system_performance_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive system usage and performance statistics"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Daily active users
        daily_active_users = db.query(
            func.date(Battle.created_at).label('date'),
            func.count(distinct(Battle.user_id)).label('active_users'),
            func.count(Battle.id).label('total_battles'),
            func.avg(Battle.duration_seconds).label('avg_session_duration'),
            func.sum(Battle.experience_gained).label('total_experience_gained')
        ).filter(
            Battle.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            func.date(Battle.created_at)
        ).order_by(
            func.date(Battle.created_at)
        ).all()
        
        # Subject popularity
        subject_popularity = db.query(
            Subject.name.label('subject_name'),
            func.count(BattleAnswer.id).label('total_questions_answered'),
            func.count(distinct(Battle.user_id)).label('unique_users'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('avg_success_rate')
        ).join(
            Question, Question.subject_id == Subject.id
        ).join(
            BattleAnswer, BattleAnswer.question_id == Question.id
        ).join(
            Battle, Battle.id == BattleAnswer.battle_id
        ).filter(
            Battle.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            Subject.name
        ).order_by(
            desc(func.count(BattleAnswer.id))
        ).all()
        
        # Peak usage hours
        hourly_usage = db.query(
            func.extract('hour', Battle.created_at).label('hour'),
            func.count(Battle.id).label('battle_count'),
            func.count(distinct(Battle.user_id)).label('unique_users')
        ).filter(
            Battle.created_at >= datetime.utcnow() - timedelta(days=7)
        ).group_by(
            func.extract('hour', Battle.created_at)
        ).order_by(
            func.extract('hour', Battle.created_at)
        ).all()
        
        return {
            "daily_metrics": [
                {
                    "date": row.date.isoformat(),
                    "active_users": row.active_users,
                    "total_battles": row.total_battles,
                    "avg_session_duration": float(row.avg_session_duration or 0),
                    "total_experience_gained": row.total_experience_gained or 0
                }
                for row in daily_active_users
            ],
            "subject_popularity": [
                {
                    "subject_name": row.subject_name,
                    "total_questions_answered": row.total_questions_answered,
                    "unique_users": row.unique_users,
                    "avg_success_rate": float(row.avg_success_rate or 0)
                }
                for row in subject_popularity
            ],
            "hourly_usage_pattern": [
                {
                    "hour": int(row.hour),
                    "battle_count": row.battle_count,
                    "unique_users": row.unique_users
                }
                for row in hourly_usage
            ],
            "summary": {
                "total_users_30d": db.query(func.count(distinct(Battle.user_id))).filter(
                    Battle.created_at >= datetime.utcnow() - timedelta(days=30)
                ).scalar() or 0,
                "total_battles_30d": db.query(func.count(Battle.id)).filter(
                    Battle.created_at >= datetime.utcnow() - timedelta(days=30)
                ).scalar() or 0,
                "total_questions_30d": db.query(func.count(BattleAnswer.id)).join(
                    Battle, Battle.id == BattleAnswer.battle_id
                ).filter(
                    Battle.created_at >= datetime.utcnow() - timedelta(days=30)
                ).scalar() or 0
            }
        }
    except Exception as e:
        logger.error(f"Error getting system performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Error getting system performance metrics")

@router.get("/personalized-recommendations")
async def get_personalized_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate personalized educational recommendations based on performance"""
    try:
        user_id = str(current_user.id)
        
        # Analyze user's performance patterns
        performance_analysis = db.query(
            Subject.name.label('subject_name'),
            Topic.name.label('topic_name'),
            func.avg(case([(BattleAnswer.is_correct == True, 1)], else_=0)).label('success_rate'),
            func.count(BattleAnswer.id).label('attempts'),
            func.avg(Question.difficulty).label('avg_difficulty'),
            func.avg(BattleAnswer.response_time_seconds).label('avg_response_time')
        ).join(
            Question, Question.topic_id == Topic.id
        ).join(
            Subject, Subject.id == Question.subject_id
        ).join(
            BattleAnswer, BattleAnswer.question_id == Question.id
        ).join(
            Battle, Battle.id == BattleAnswer.battle_id
        ).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.utcnow() - timedelta(days=30)
        ).group_by(
            Subject.name, Topic.name
        ).having(
            func.count(BattleAnswer.id) >= 3
        ).all()
        
        # Generate recommendations
        recommendations = []
        improvement_areas = []
        strengths = []
        
        for perf in performance_analysis:
            success_rate = perf.success_rate or 0
            attempts = perf.attempts
            avg_difficulty = perf.avg_difficulty or 0
            
            if success_rate < 0.6:  # Improvement needed
                improvement_areas.append({
                    "subject": perf.subject_name,
                    "topic": perf.topic_name,
                    "success_rate": success_rate,
                    "attempts": attempts,
                    "avg_difficulty": avg_difficulty,
                    "recommendation": f"Práctica adicional en {perf.topic_name}",
                    "priority": "high" if success_rate < 0.4 else "medium"
                })
            elif success_rate > 0.8 and avg_difficulty > 6:  # Strength
                strengths.append({
                    "subject": perf.subject_name,
                    "topic": perf.topic_name,
                    "success_rate": success_rate,
                    "attempts": attempts,
                    "avg_difficulty": avg_difficulty
                })
        
        # Generate specific recommendations
        if improvement_areas:
            recommendations.append({
                "type": "improvement",
                "title": "Áreas de Mejora",
                "description": "Temas que requieren práctica adicional",
                "areas": improvement_areas[:5]  # Top 5 improvement areas
            })
        
        if strengths:
            recommendations.append({
                "type": "advancement",
                "title": "Avanzar a Nivel Superior",
                "description": "Temas dominados, listo para dificultad mayor",
                "areas": strengths[:3]  # Top 3 strengths
            })
        
        # Study schedule recommendations
        recent_activity = db.query(
            func.extract('hour', Battle.created_at).label('hour'),
            func.count(Battle.id).label('session_count')
        ).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.utcnow() - timedelta(days=14)
        ).group_by(
            func.extract('hour', Battle.created_at)
        ).order_by(
            desc(func.count(Battle.id))
        ).first()
        
        optimal_hour = int(recent_activity.hour) if recent_activity else 20
        
        recommendations.append({
            "type": "schedule",
            "title": "Horario Óptimo de Estudio",
            "description": f"Basado en tu actividad, estudias mejor a las {optimal_hour}:00",
            "optimal_hour": optimal_hour
        })
        
        return {
            "user_id": user_id,
            "generated_at": datetime.utcnow().isoformat(),
            "recommendations": recommendations,
            "summary": {
                "total_improvement_areas": len(improvement_areas),
                "total_strengths": len(strengths),
                "overall_performance": sum(p.success_rate for p in performance_analysis) / len(performance_analysis) if performance_analysis else 0
            }
        }
    except Exception as e:
        logger.error(f"Error generating personalized recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error generating recommendations")