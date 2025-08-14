from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.user_profile import UserProfile
from ..models.battle import BattleAnswer
from ..models.question import Question
from ..schemas.ai import (
    BattleTipsRequest,
    BattleTipsResponse,
    QuestionExplanationRequest,
    QuestionExplanationResponse,
    StudyTipsRequest,
    StudyTipsResponse,
    LearningPatternResponse,
    MotivationalMessageRequest
)
from ..services.llm_service import llm_service
from ..services.cache_service import cache_service

router = APIRouter(prefix="/ai/tips", tags=["ai-tips"])
logger = logging.getLogger(__name__)

@router.post("/battle", response_model=BattleTipsResponse)
async def get_battle_tips(
    request: BattleTipsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized battle tips based on current performance"""
    try:
        # Get user's recent performance
        recent_answers = db.query(BattleAnswer).join(
            Question, BattleAnswer.question_id == Question.id
        ).filter(
            BattleAnswer.battle_id == request.battle_id
        ).all()
        
        if not recent_answers:
            return BattleTipsResponse(tips=[], generated=False)
        
        # Calculate performance metrics
        total = len(recent_answers)
        correct = sum(1 for a in recent_answers if a.is_correct)
        accuracy = (correct / total * 100) if total > 0 else 0
        
        # Get weak topics
        topic_performance = {}
        for answer in recent_answers:
            topic = answer.question.topic or "General"
            if topic not in topic_performance:
                topic_performance[topic] = {"correct": 0, "total": 0}
            topic_performance[topic]["total"] += 1
            if answer.is_correct:
                topic_performance[topic]["correct"] += 1
        
        # Find weakest topics
        weakest_topics = []
        for topic, perf in topic_performance.items():
            topic_accuracy = (perf["correct"] / perf["total"] * 100) if perf["total"] > 0 else 0
            if topic_accuracy < 70:  # Below 70% is considered weak
                weakest_topics.append(topic)
        
        # Prepare context
        user_performance = {
            "accuracy": accuracy,
            "weakest_topics": weakest_topics,
            "total_questions": total,
            "correct_answers": correct
        }
        
        battle_context = {
            "topic": request.current_topic,
            "difficulty": request.difficulty,
            "battle_type": request.battle_type
        }
        
        # Get tips from LLM
        tips = await llm_service.get_battle_tips(user_performance, battle_context)
        
        return BattleTipsResponse(
            tips=tips,
            generated=llm_service.is_available(),
            accuracy=accuracy,
            weak_areas=weakest_topics[:3]
        )
        
    except Exception as e:
        logger.error(f"Error generating battle tips: {e}")
        raise HTTPException(status_code=500, detail="Error generating tips")

@router.post("/explanation", response_model=QuestionExplanationResponse)
async def get_question_explanation(
    request: QuestionExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed explanation for a question answer"""
    try:
        # Get question details
        question = db.query(Question).filter(
            Question.id == request.question_id
        ).first()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Prepare question data
        question_data = {
            "id": str(question.id),
            "text": question.text,
            "options": question.options,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "topic": question.topic
        }
        
        # Get explanation from LLM
        explanation = await llm_service.get_question_explanation(
            question_data,
            request.user_answer,
            request.is_correct
        )
        
        return QuestionExplanationResponse(
            explanation=explanation,
            correct_answer=question.correct_answer,
            hint=question.hint,
            generated=llm_service.is_available()
        )
        
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        raise HTTPException(status_code=500, detail="Error generating explanation")

@router.post("/study-plan", response_model=StudyTipsResponse)
async def get_personalized_study_plan(
    request: StudyTipsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate personalized study plan based on performance"""
    try:
        # Get user profile
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Get user stats
        user_stats = {
            "level": profile.level,
            "experience": profile.experience,
            "overall_accuracy": (profile.correct_answers / profile.questions_answered * 100) 
                              if profile.questions_answered > 0 else 0,
            "streak_days": profile.streak_days,
            "rank": profile.rank
        }
        
        # Get weak areas from request or calculate
        weak_areas = request.weak_areas or []
        
        # If no weak areas provided, get from recent performance
        if not weak_areas:
            # This would typically involve more complex analysis
            # For now, we'll use the provided weak areas
            pass
        
        # Generate study plan
        study_plan = await llm_service.generate_personalized_study_tips(
            user_stats,
            weak_areas
        )
        
        return StudyTipsResponse(
            objectives=study_plan.get("objetivos", []),
            strategies=study_plan.get("estrategias", []),
            daily_time=study_plan.get("tiempo_diario", "45-60 minutos"),
            resources=study_plan.get("recursos", []),
            generated=llm_service.is_available()
        )
        
    except Exception as e:
        logger.error(f"Error generating study plan: {e}")
        raise HTTPException(status_code=500, detail="Error generating study plan")

@router.get("/learning-pattern", response_model=LearningPatternResponse)
async def analyze_learning_pattern(
    days: int = 7,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Analyze user's learning patterns"""
    try:
        # Get user's answer history
        from datetime import datetime, timedelta
        since_date = datetime.utcnow() - timedelta(days=days)
        
        answer_history = db.query(
            BattleAnswer.is_correct,
            BattleAnswer.response_time,
            Question.difficulty,
            Question.topic
        ).join(
            Question, BattleAnswer.question_id == Question.id
        ).filter(
            BattleAnswer.created_at >= since_date,
            BattleAnswer.user_id == current_user.id
        ).all()
        
        # Convert to list of dicts
        history_data = [
            {
                "is_correct": answer.is_correct,
                "response_time": answer.response_time,
                "difficulty": answer.difficulty,
                "topic": answer.topic
            }
            for answer in answer_history
        ]
        
        # Analyze pattern
        pattern_analysis = await llm_service.analyze_learning_pattern(history_data)
        
        return LearningPatternResponse(
            pattern=pattern_analysis["pattern"],
            metrics=pattern_analysis["metrics"],
            insights=pattern_analysis["insights"],
            recommendations=pattern_analysis["recommendations"]
        )
        
    except Exception as e:
        logger.error(f"Error analyzing learning pattern: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing pattern")

@router.post("/motivational")
async def get_motivational_message(
    request: MotivationalMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get motivational message based on context"""
    try:
        # Get user profile for stats
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        user_stats = {
            "level": profile.level if profile else 1,
            "streak_days": profile.streak_days if profile else 0,
            "rank": profile.rank if profile else "E"
        }
        
        message = await llm_service.generate_motivational_message(
            request.context,
            user_stats
        )
        
        return {
            "message": message,
            "context": request.context
        }
        
    except Exception as e:
        logger.error(f"Error generating motivational message: {e}")
        raise HTTPException(status_code=500, detail="Error generating message")

@router.get("/status")
async def get_llm_service_status(
    current_user: User = Depends(get_current_user)
):
    """Check LLM service status"""
    return {
        "available": llm_service.is_available(),
        "service": "OpenAI" if llm_service.is_available() else "Mock",
        "features": {
            "battle_tips": True,
            "explanations": True,
            "study_plans": True,
            "pattern_analysis": True,
            "motivational_messages": True
        }
    }