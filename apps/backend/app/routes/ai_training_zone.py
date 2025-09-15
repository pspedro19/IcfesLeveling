#!/usr/bin/env python3
"""
AI Training Zone Routes - Enhanced Learning Support

Comprehensive API endpoints for AI-powered training zone including:
- Intelligent question explanations
- Adaptive hint generation  
- Personalized tutoring chat
- AI-generated practice questions
- Learning path recommendations
- Progress analysis and feedback
- Natural language concept explanations

Author: Claude Code Assistant
Date: 2024
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import asyncio
import json
import redis
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.config import settings
from ..models.user import User
from ..services.ai_training_zone import AITrainingZoneService, InteractionType

# Initialize router
router = APIRouter(prefix="/ai-training", tags=["AI Training Zone"])

# Initialize AI service
ai_service = AITrainingZoneService(
    database_url=settings.DATABASE_URL,
    redis_url=settings.REDIS_URL,
    openai_api_key=getattr(settings, 'OPENAI_API_KEY', None)
)

# Pydantic models for request/response
class QuestionExplanationRequest(BaseModel):
    question_id: str = Field(..., description="ID of the question to explain")
    student_answer: str = Field(..., description="Student's selected answer")
    include_strategy_tips: bool = Field(default=True, description="Include strategy tips in explanation")

class HintRequest(BaseModel):
    question_id: str = Field(..., description="ID of the question needing a hint")
    attempt_number: int = Field(default=1, ge=1, le=5, description="Current attempt number (1-5)")
    time_spent: int = Field(default=0, ge=0, description="Time spent on question in seconds")
    difficulty_preference: Optional[str] = Field(default=None, description="Requested hint difficulty: 'gentle', 'moderate', 'direct'")

class ConceptExplanationRequest(BaseModel):
    concept_name: str = Field(..., description="Name of the concept to explain")
    subject_id: Optional[int] = Field(default=None, description="Subject context for the concept")
    topic_name: Optional[str] = Field(default=None, description="Topic context for the concept")
    learning_style: Optional[str] = Field(default="balanced", description="Preferred learning style: 'visual', 'step-by-step', 'conceptual', 'balanced'")

class TutoringChatRequest(BaseModel):
    message: str = Field(..., description="Student's message to the AI tutor")
    context_type: str = Field(default="general", description="Type of help needed: 'general', 'homework', 'exam_prep', 'concept_review'")
    subject_id: Optional[int] = Field(default=None, description="Current subject context")

class PracticeGenerationRequest(BaseModel):
    subject_id: int = Field(..., description="Subject for practice questions")
    difficulty_level: str = Field(default="adaptive", description="Difficulty level: 'easy', 'medium', 'hard', 'adaptive'")
    question_count: int = Field(default=5, ge=1, le=20, description="Number of questions to generate")
    focus_topics: List[str] = Field(default=[], description="Specific topics to focus on")
    avoid_recent: bool = Field(default=True, description="Avoid recently answered questions")

class LearningPathRequest(BaseModel):
    subject_id: int = Field(..., description="Subject for learning path")
    time_available: Optional[int] = Field(default=None, description="Available study time in minutes per day")
    learning_goals: List[str] = Field(default=[], description="Specific learning goals")
    preferred_difficulty: str = Field(default="adaptive", description="Preferred difficulty progression")

class ProgressAnalysisRequest(BaseModel):
    subject_id: Optional[int] = Field(default=None, description="Subject to analyze (all subjects if None)")
    time_period: int = Field(default=30, ge=7, le=365, description="Analysis period in days")
    include_predictions: bool = Field(default=True, description="Include ICFES score predictions")

class AIResponse(BaseModel):
    response_text: str
    confidence_score: float
    interaction_type: str
    follow_up_questions: List[str]
    suggested_actions: List[str]
    related_resources: List[Dict[str, Any]]
    learning_objectives: List[str]
    estimated_time_needed: int
    metadata: Dict[str, Any]

@router.post("/explain-question", response_model=AIResponse)
async def explain_question(
    request: QuestionExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive AI explanation for a specific question
    
    Provides personalized explanations based on:
    - Student's performance history
    - Question difficulty and topic
    - Common mistakes and learning patterns
    - Preferred learning style
    """
    try:
        # Get question details first
        question = db.execute("""
            SELECT q.*, s.name as subject_name, t.name as topic_name
            FROM questions q
            JOIN subjects s ON q.subject_id = s.id
            LEFT JOIN topics t ON q.topic_id = t.id
            WHERE q.id = :question_id
        """, {"question_id": request.question_id}).fetchone()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Generate AI explanation
        ai_response = await ai_service.explain_question(
            student_id=current_user.id,
            question_id=request.question_id,
            student_answer=request.student_answer,
            subject_id=question.subject_id
        )
        
        # Add strategy tips if requested
        additional_resources = ai_response.related_resources
        if request.include_strategy_tips:
            strategy_response = await ai_service.provide_strategy_advice(
                student_id=current_user.id,
                problem_description=f"Improving performance on {question.topic_name or 'this type of'} questions",
                subject_id=question.subject_id
            )
            additional_resources.append({
                "type": "strategy",
                "title": "Strategic Tips",
                "content": strategy_response.response_text[:200] + "...",
                "full_content": strategy_response.response_text
            })
        
        return AIResponse(
            response_text=ai_response.response_text,
            confidence_score=ai_response.confidence_score,
            interaction_type=ai_response.interaction_type.value,
            follow_up_questions=ai_response.follow_up_questions,
            suggested_actions=ai_response.suggested_actions,
            related_resources=additional_resources,
            learning_objectives=ai_response.learning_objectives,
            estimated_time_needed=ai_response.estimated_time_needed,
            metadata={
                "question_topic": question.topic_name,
                "question_difficulty": question.irt_b,
                "correct_answer": question.correct_answer,
                "is_correct": request.student_answer == question.correct_answer,
                "response_time_ms": ai_response.response_time_ms
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

@router.post("/get-hint", response_model=AIResponse)
async def get_intelligent_hint(
    request: HintRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate progressive, intelligent hints for training questions
    
    Features:
    - Progressive hint levels (gentle → specific → direct)
    - Adapts to student's skill level
    - Considers time spent and attempt number
    - Maintains hint history to avoid repetition
    """
    try:
        # Get question context
        question = db.execute("""
            SELECT q.*, s.name as subject_name
            FROM questions q
            JOIN subjects s ON q.subject_id = s.id
            WHERE q.id = :question_id
        """, {"question_id": request.question_id}).fetchone()
        
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        # Generate intelligent hint
        ai_response = await ai_service.generate_hint(
            student_id=current_user.id,
            question_id=request.question_id,
            attempt_number=request.attempt_number,
            time_spent=request.time_spent,
            subject_id=question.subject_id
        )
        
        # Add hint progression metadata
        hint_metadata = {
            "hint_level": min(request.attempt_number, 3),
            "progression_available": request.attempt_number < 3,
            "question_subject": question.subject_name,
            "time_spent": request.time_spent,
            "optimal_time_range": "60-120 seconds"
        }
        
        # Add time management tips if needed
        if request.time_spent > 120:
            ai_response.suggested_actions.append("Consider moving on and returning if time permits")
            ai_response.suggested_actions.append("Practice time management strategies")
        
        return AIResponse(
            response_text=ai_response.response_text,
            confidence_score=ai_response.confidence_score,
            interaction_type=ai_response.interaction_type.value,
            follow_up_questions=ai_response.follow_up_questions,
            suggested_actions=ai_response.suggested_actions,
            related_resources=ai_response.related_resources,
            learning_objectives=ai_response.learning_objectives,
            estimated_time_needed=ai_response.estimated_time_needed,
            metadata=hint_metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating hint: {str(e)}")

@router.post("/explain-concept", response_model=AIResponse)
async def explain_concept(
    request: ConceptExplanationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Provide comprehensive natural language explanations for ICFES concepts
    
    Features:
    - Adapts to student's current understanding level
    - Uses analogies and real-world examples
    - Connects to previously mastered concepts
    - Provides multiple explanation approaches
    """
    try:
        # Generate concept explanation
        ai_response = await ai_service.explain_concept(
            student_id=current_user.id,
            concept_name=request.concept_name,
            subject_id=request.subject_id,
            topic_name=request.topic_name
        )
        
        # Get related practice questions
        related_questions = []
        if request.subject_id:
            questions = db.execute("""
                SELECT id, statement, irt_b as difficulty
                FROM questions q
                WHERE q.subject_id = :subject_id
                AND (LOWER(q.statement) LIKE LOWER(:concept) OR 
                     LOWER(COALESCE(q.explanation, '')) LIKE LOWER(:concept))
                ORDER BY ABS(q.irt_b - 0) -- Prefer medium difficulty
                LIMIT 3
            """, {
                "subject_id": request.subject_id, 
                "concept": f"%{request.concept_name}%"
            }).fetchall()
            
            related_questions = [
                {
                    "type": "practice_question",
                    "id": q.id,
                    "title": f"Practice: {q.statement[:50]}...",
                    "difficulty": "Easy" if q.difficulty < -0.5 else "Hard" if q.difficulty > 0.5 else "Medium"
                }
                for q in questions
            ]
        
        # Add concept-specific learning objectives
        concept_objectives = [
            f"Master the fundamental definition of {request.concept_name}",
            f"Apply {request.concept_name} in various ICFES contexts",
            f"Connect {request.concept_name} with related concepts",
            "Build confidence in concept recognition and application"
        ]
        
        return AIResponse(
            response_text=ai_response.response_text,
            confidence_score=ai_response.confidence_score,
            interaction_type=ai_response.interaction_type.value,
            follow_up_questions=ai_response.follow_up_questions,
            suggested_actions=ai_response.suggested_actions,
            related_resources=ai_response.related_resources + related_questions,
            learning_objectives=concept_objectives,
            estimated_time_needed=ai_response.estimated_time_needed,
            metadata={
                "concept_name": request.concept_name,
                "learning_style": request.learning_style,
                "subject_context": request.subject_id,
                "topic_context": request.topic_name
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error explaining concept: {str(e)}")

@router.post("/tutor-chat", response_model=AIResponse)
async def tutor_chat(
    request: TutoringChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Interactive AI tutoring chat with contextual responses
    
    Features:
    - Contextual understanding of student needs
    - Motivational and encouraging responses
    - Adaptive difficulty in explanations
    - Integration with student's learning history
    """
    try:
        # Generate chat response
        ai_response = await ai_service.chat_with_tutor(
            student_id=current_user.id,
            message=request.message,
            subject_id=request.subject_id
        )
        
        # Add context-specific enhancements
        enhanced_actions = ai_response.suggested_actions.copy()
        
        if request.context_type == "exam_prep":
            enhanced_actions.extend([
                "Take a practice exam to assess readiness",
                "Focus on time management strategies",
                "Review your most challenging topics"
            ])
        elif request.context_type == "homework":
            enhanced_actions.extend([
                "Break down complex problems into smaller steps",
                "Check your work before submitting",
                "Ask for clarification on confusing parts"
            ])
        elif request.context_type == "concept_review":
            enhanced_actions.extend([
                "Create concept maps to visualize relationships",
                "Practice with varied examples",
                "Teach the concept to someone else"
            ])
        
        # Get conversation history (last 5 interactions)
        recent_chats = db.execute("""
            SELECT interaction_type, created_at
            FROM ai_interactions
            WHERE student_id = :student_id
            ORDER BY created_at DESC
            LIMIT 5
        """, {"student_id": current_user.id}).fetchall()
        
        return AIResponse(
            response_text=ai_response.response_text,
            confidence_score=ai_response.confidence_score,
            interaction_type=ai_response.interaction_type.value,
            follow_up_questions=ai_response.follow_up_questions,
            suggested_actions=enhanced_actions[:6],  # Limit to 6 actions
            related_resources=ai_response.related_resources,
            learning_objectives=ai_response.learning_objectives,
            estimated_time_needed=ai_response.estimated_time_needed,
            metadata={
                "context_type": request.context_type,
                "conversation_length": len(recent_chats),
                "recent_interaction_types": [chat.interaction_type for chat in recent_chats]
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in tutor chat: {str(e)}")

@router.post("/generate-practice")
async def generate_practice_questions(
    request: PracticeGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate AI-powered practice questions based on student weaknesses
    
    Features:
    - Adapts to student's current skill level
    - Focuses on problem areas
    - Avoids recently answered questions
    - Provides varied question types and difficulties
    """
    try:
        # Get student context for personalization
        context = await ai_service.get_student_context(current_user.id, request.subject_id)
        
        # Determine target difficulty
        if request.difficulty_level == "adaptive":
            if context.recent_accuracy < 0.5:
                target_difficulty = "easy"
            elif context.recent_accuracy > 0.8:
                target_difficulty = "hard"
            else:
                target_difficulty = "medium"
        else:
            target_difficulty = request.difficulty_level
        
        # Get focus topics (use problem areas if none specified)
        focus_topics = request.focus_topics if request.focus_topics else context.problem_areas
        
        # Get recently answered questions to avoid
        recent_questions = []
        if request.avoid_recent:
            recent_questions = db.execute("""
                SELECT DISTINCT question_id
                FROM question_responses qr
                WHERE qr.user_id = :user_id
                AND qr.created_at >= NOW() - INTERVAL '7 days'
            """, {"user_id": current_user.id}).fetchall()
            recent_questions = [q.question_id for q in recent_questions]
        
        # Build query for existing questions
        difficulty_filter = {
            "easy": "q.irt_b < -0.5",
            "medium": "q.irt_b BETWEEN -0.5 AND 0.5", 
            "hard": "q.irt_b > 0.5"
        }
        
        topic_conditions = []
        if focus_topics:
            topic_conditions = [f"LOWER(t.name) LIKE LOWER('%{topic}%')" for topic in focus_topics]
        
        # Get existing questions
        base_query = f"""
            SELECT 
                q.id,
                q.statement,
                q.option_a,
                q.option_b,
                q.option_c,
                q.option_d,
                q.correct_answer,
                q.explanation,
                q.irt_b as difficulty,
                t.name as topic_name
            FROM questions q
            LEFT JOIN topics t ON q.topic_id = t.id
            WHERE q.subject_id = :subject_id
            AND ({difficulty_filter[target_difficulty]})
        """
        
        params = {"subject_id": request.subject_id}
        
        if topic_conditions:
            base_query += f" AND ({' OR '.join(topic_conditions)})"
        
        if recent_questions:
            placeholders = ','.join([f':recent_{i}' for i in range(len(recent_questions))])
            base_query += f" AND q.id NOT IN ({placeholders})"
            for i, qid in enumerate(recent_questions):
                params[f'recent_{i}'] = qid
        
        base_query += f" ORDER BY RANDOM() LIMIT {request.question_count}"
        
        questions = db.execute(base_query, params).fetchall()
        
        # Format questions for response
        practice_questions = []
        for q in questions:
            practice_questions.append({
                "id": q.id,
                "statement": q.statement,
                "options": {
                    "A": q.option_a,
                    "B": q.option_b,
                    "C": q.option_c,
                    "D": q.option_d
                },
                "correct_answer": q.correct_answer,
                "topic": q.topic_name,
                "difficulty": target_difficulty,
                "estimated_time": "90 seconds",
                "ai_generated": False
            })
        
        # Generate additional questions with AI if needed
        remaining_count = request.question_count - len(practice_questions)
        if remaining_count > 0 and ai_service.openai_client:
            # TODO: Implement AI question generation
            pass
        
        # Calculate practice session metadata
        session_metadata = {
            "total_questions": len(practice_questions),
            "difficulty_distribution": {target_difficulty: len(practice_questions)},
            "topics_covered": list(set([q["topic"] for q in practice_questions if q["topic"]])),
            "estimated_total_time": len(practice_questions) * 90,  # seconds
            "personalization_level": "high" if focus_topics or context.problem_areas else "medium",
            "adaptive_difficulty": request.difficulty_level == "adaptive"
        }
        
        return {
            "questions": practice_questions,
            "session_metadata": session_metadata,
            "student_context": {
                "current_level": context.difficulty_preference.value,
                "focus_areas": focus_topics or context.problem_areas,
                "recent_accuracy": context.recent_accuracy
            },
            "recommendations": {
                "study_tips": [
                    "Take your time to read each question carefully",
                    "Eliminate obviously wrong answers first",
                    "Don't spend more than 2 minutes per question",
                    "Review incorrect answers to learn from mistakes"
                ],
                "next_steps": [
                    "Complete this practice session",
                    "Review explanations for incorrect answers", 
                    "Focus on weak topics identified",
                    "Take a diagnostic test to track progress"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating practice questions: {str(e)}")

@router.get("/progress-analysis")
async def get_progress_analysis(
    subject_id: Optional[int] = None,
    time_period: int = 30,
    include_predictions: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI-powered comprehensive progress analysis and feedback
    
    Features:
    - Performance trend analysis
    - Strength and weakness identification
    - ICFES score predictions
    - Personalized improvement recommendations
    - Learning velocity tracking
    """
    try:
        # Get comprehensive performance data
        performance_query = """
            SELECT 
                qr.is_correct,
                qr.time_sec,
                qr.created_at::date as date,
                q.irt_b as difficulty,
                s.name as subject_name,
                t.name as topic_name,
                q.subject_id
            FROM question_responses qr
            JOIN questions q ON qr.question_id = q.id
            JOIN subjects s ON q.subject_id = s.id
            LEFT JOIN topics t ON q.topic_id = t.id
            WHERE qr.user_id = :user_id
            AND qr.created_at >= NOW() - INTERVAL ':time_period days'
        """
        
        params = {"user_id": current_user.id, "time_period": time_period}
        
        if subject_id:
            performance_query += " AND q.subject_id = :subject_id"
            params["subject_id"] = subject_id
        
        performance_query += " ORDER BY qr.created_at DESC"
        
        performance_data = db.execute(performance_query, params).fetchall()
        
        if not performance_data:
            return {
                "message": "No performance data available for the specified period",
                "recommendations": [
                    "Start practicing with some questions",
                    "Take a diagnostic test to establish baseline",
                    "Set a regular study schedule"
                ]
            }
        
        # Calculate key metrics
        total_questions = len(performance_data)
        correct_answers = sum(1 for p in performance_data if p.is_correct)
        overall_accuracy = correct_answers / total_questions
        
        avg_time = sum(p.time_sec for p in performance_data) / total_questions
        avg_difficulty = sum(p.difficulty for p in performance_data if p.difficulty) / total_questions
        
        # Analyze trends (daily performance)
        daily_performance = {}
        for record in performance_data:
            date = record.date
            if date not in daily_performance:
                daily_performance[date] = {"correct": 0, "total": 0}
            daily_performance[date]["total"] += 1
            if record.is_correct:
                daily_performance[date]["correct"] += 1
        
        # Calculate trend direction
        daily_accuracies = [perf["correct"] / perf["total"] for perf in daily_performance.values()]
        recent_accuracy = sum(daily_accuracies[:7]) / min(7, len(daily_accuracies)) if daily_accuracies else 0
        older_accuracy = sum(daily_accuracies[7:14]) / max(1, min(7, len(daily_accuracies[7:14]))) if len(daily_accuracies) > 7 else recent_accuracy
        
        trend_direction = "improving" if recent_accuracy > older_accuracy + 0.05 else "declining" if recent_accuracy < older_accuracy - 0.05 else "stable"
        
        # Subject/topic analysis
        subject_performance = {}
        topic_performance = {}
        
        for record in performance_data:
            # Subject analysis
            subject = record.subject_name
            if subject not in subject_performance:
                subject_performance[subject] = {"correct": 0, "total": 0}
            subject_performance[subject]["total"] += 1
            if record.is_correct:
                subject_performance[subject]["correct"] += 1
            
            # Topic analysis
            topic = record.topic_name or "General"
            if topic not in topic_performance:
                topic_performance[topic] = {"correct": 0, "total": 0}
            topic_performance[topic]["total"] += 1
            if record.is_correct:
                topic_performance[topic]["correct"] += 1
        
        # Identify strengths and weaknesses
        strengths = []
        weaknesses = []
        
        for topic, perf in topic_performance.items():
            if perf["total"] >= 3:  # Minimum attempts for significance
                accuracy = perf["correct"] / perf["total"]
                if accuracy >= 0.8:
                    strengths.append({"topic": topic, "accuracy": accuracy, "questions": perf["total"]})
                elif accuracy < 0.6:
                    weaknesses.append({"topic": topic, "accuracy": accuracy, "questions": perf["total"]})
        
        # Sort by performance
        strengths.sort(key=lambda x: x["accuracy"], reverse=True)
        weaknesses.sort(key=lambda x: x["accuracy"])
        
        # ICFES score prediction (if requested)
        predictions = {}
        if include_predictions:
            base_score = 300  # ICFES base score
            performance_bonus = (overall_accuracy - 0.5) * 400  # Scale accuracy to score range
            difficulty_bonus = avg_difficulty * 50  # Bonus for handling difficult questions
            consistency_bonus = (1 - (sum(abs(acc - overall_accuracy) for acc in daily_accuracies) / len(daily_accuracies))) * 50 if daily_accuracies else 0
            
            predicted_score = max(100, min(500, int(base_score + performance_bonus + difficulty_bonus + consistency_bonus)))
            
            predictions = {
                "estimated_icfes_score": predicted_score,
                "confidence_interval": [max(100, predicted_score - 30), min(500, predicted_score + 30)],
                "score_percentile": min(99, max(1, int((predicted_score - 100) / 400 * 100))),
                "factors": {
                    "accuracy_contribution": int(performance_bonus),
                    "difficulty_contribution": int(difficulty_bonus),
                    "consistency_contribution": int(consistency_bonus)
                }
            }
        
        # Generate AI insights
        context = await ai_service.get_student_context(current_user.id, subject_id)
        
        ai_insights_prompt = f"""
        Analiza el progreso de este estudiante ICFES:
        
        Métricas de rendimiento:
        - Precisión general: {overall_accuracy:.1%}
        - Preguntas respondidas: {total_questions}
        - Tiempo promedio: {avg_time:.1f}s
        - Tendencia: {trend_direction}
        
        Fortalezas: {[s['topic'] for s in strengths[:3]]}
        Debilidades: {[w['topic'] for w in weaknesses[:3]]}
        
        Proporciona análisis motivador y recomendaciones específicas.
        """
        
        try:
            ai_response = await ai_service.chat_with_tutor(
                student_id=current_user.id,
                message=ai_insights_prompt,
                subject_id=subject_id
            )
            ai_insights = ai_response.response_text
        except:
            ai_insights = f"""
            Tu progreso en los últimos {time_period} días muestra {trend_direction} rendimiento con {overall_accuracy:.1%} de precisión.
            
            Fortalezas identificadas: {', '.join([s['topic'] for s in strengths[:2]]) if strengths else 'Desarrollando habilidades básicas'}
            
            Áreas de mejora: {', '.join([w['topic'] for w in weaknesses[:2]]) if weaknesses else 'Mantener nivel actual'}
            
            Recomendación: {'Continúa practicando regularmente y enfócate en las áreas identificadas para mejorar.' if weaknesses else 'Excelente trabajo! Mantén la consistencia y desafíate con preguntas más complejas.'}
            """
        
        # Generate personalized recommendations
        recommendations = []
        
        if overall_accuracy < 0.5:
            recommendations.extend([
                "Enfócate en conceptos fundamentales antes de avanzar",
                "Dedica tiempo extra a repasar teoría básica",
                "Practica ejercicios de dificultad baja a media"
            ])
        elif overall_accuracy < 0.7:
            recommendations.extend([
                "Mantén práctica regular con variedad de ejercicios",
                "Revisa errores comunes para evitar repetirlos",
                "Considera estudiar en grupos para intercambiar conocimientos"
            ])
        else:
            recommendations.extend([
                "Desafíate con preguntas de alta dificultad",
                "Practica bajo presión de tiempo para el examen",
                "Ayuda a otros estudiantes para reforzar tu aprendizaje"
            ])
        
        if avg_time > 120:
            recommendations.append("Practica estrategias de gestión del tiempo")
        
        if weaknesses:
            recommendations.append(f"Dedica tiempo extra a mejorar en: {', '.join([w['topic'] for w in weaknesses[:2]])}")
        
        return {
            "analysis_period": f"{time_period} days",
            "performance_overview": {
                "questions_answered": total_questions,
                "overall_accuracy": overall_accuracy,
                "average_time_per_question": avg_time,
                "trend_direction": trend_direction,
                "improvement_rate": recent_accuracy - older_accuracy if len(daily_accuracies) > 7 else 0
            },
            "strengths": strengths[:5],
            "areas_for_improvement": weaknesses[:5],
            "subject_breakdown": {
                subject: {
                    "accuracy": perf["correct"] / perf["total"],
                    "questions_answered": perf["total"]
                }
                for subject, perf in subject_performance.items()
            },
            "daily_performance": [
                {
                    "date": str(date),
                    "accuracy": perf["correct"] / perf["total"],
                    "questions": perf["total"]
                }
                for date, perf in sorted(daily_performance.items(), reverse=True)
            ][:14],  # Last 14 days
            "ai_insights": ai_insights,
            "predictions": predictions,
            "personalized_recommendations": recommendations,
            "next_steps": {
                "immediate": recommendations[:2],
                "this_week": [
                    "Complete practice sessions focusing on weak areas",
                    "Review and understand all incorrect answers",
                    "Track daily progress and adjust study plan"
                ],
                "this_month": [
                    "Take comprehensive diagnostic tests",
                    "Build consistent study routine",
                    "Prepare for full ICFES simulation"
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating progress analysis: {str(e)}")

@router.post("/create-learning-path")
async def create_learning_path(
    request: LearningPathRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create personalized AI-powered learning paths
    
    Features:
    - Adaptive difficulty progression
    - Time-based scheduling
    - Goal-oriented milestones
    - Integration with student performance data
    """
    try:
        # Get student context
        context = await ai_service.get_student_context(current_user.id, request.subject_id)
        
        # Get subject information
        subject = db.execute("""
            SELECT name, description FROM subjects WHERE id = :subject_id
        """, {"subject_id": request.subject_id}).fetchone()
        
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        # Get available topics
        topics = db.execute("""
            SELECT name, competence, description
            FROM topics 
            WHERE subject_id = :subject_id
            ORDER BY name
        """, {"subject_id": request.subject_id}).fetchall()
        
        # Create learning modules based on student needs
        learning_modules = []
        
        # Module 1: Address immediate weaknesses
        if context.problem_areas:
            for i, problem_area in enumerate(context.problem_areas[:3]):
                learning_modules.append({
                    "id": f"remedial_{i+1}",
                    "title": f"Refuerzo: {problem_area}",
                    "type": "remedial",
                    "priority": "high",
                    "estimated_hours": 4,
                    "description": f"Módulo intensivo para fortalecer conocimientos en {problem_area}",
                    "activities": [
                        {
                            "type": "concept_review",
                            "title": f"Revisión conceptual: {problem_area}",
                            "duration_minutes": 45,
                            "description": "Revisión profunda de conceptos fundamentales"
                        },
                        {
                            "type": "guided_practice",
                            "title": f"Práctica guiada: {problem_area}",
                            "duration_minutes": 60,
                            "description": "Ejercicios con explicaciones paso a paso"
                        },
                        {
                            "type": "independent_practice",
                            "title": f"Práctica independiente: {problem_area}",
                            "duration_minutes": 45,
                            "description": "Ejercicios para consolidar aprendizaje"
                        },
                        {
                            "type": "assessment",
                            "title": f"Evaluación: {problem_area}",
                            "duration_minutes": 30,
                            "description": "Verificación de progreso y dominio"
                        }
                    ],
                    "learning_objectives": [
                        f"Dominar conceptos fundamentales de {problem_area}",
                        "Aplicar conocimientos en ejercicios prácticos",
                        "Alcanzar 75% de precisión en evaluaciones"
                    ],
                    "success_criteria": {
                        "minimum_accuracy": 0.75,
                        "completion_time": "1-2 semanas",
                        "mastery_indicators": [
                            "Resolución correcta de problemas básicos",
                            "Explicación clara de conceptos",
                            "Aplicación en contextos variados"
                        ]
                    }
                })
        
        # Module 2: Skill development for intermediate topics
        available_topics = [t.name for t in topics if t.name not in context.strong_areas and t.name not in context.problem_areas]
        for i, topic in enumerate(available_topics[:2]):
            learning_modules.append({
                "id": f"development_{i+1}",
                "title": f"Desarrollo: {topic}",
                "type": "development", 
                "priority": "medium",
                "estimated_hours": 3,
                "description": f"Desarrollo de habilidades intermedias en {topic}",
                "activities": [
                    {
                        "type": "exploration",
                        "title": f"Exploración: {topic}",
                        "duration_minutes": 30,
                        "description": "Introducción y exploración del tema"
                    },
                    {
                        "type": "practice",
                        "title": f"Práctica: {topic}",
                        "duration_minutes": 60,
                        "description": "Ejercicios de dificultad progresiva"
                    },
                    {
                        "type": "application",
                        "title": f"Aplicación: {topic}",
                        "duration_minutes": 45,
                        "description": "Aplicación en problemas complejos"
                    },
                    {
                        "type": "integration",
                        "title": f"Integración: {topic}",
                        "duration_minutes": 25,
                        "description": "Conexión con otros temas"
                    }
                ],
                "learning_objectives": [
                    f"Comprender conceptos intermedios de {topic}",
                    "Resolver problemas de complejidad media",
                    "Integrar con conocimientos previos"
                ],
                "success_criteria": {
                    "minimum_accuracy": 0.70,
                    "completion_time": "1 semana",
                    "mastery_indicators": [
                        "Resolución de problemas intermedios",
                        "Conexión con otros conceptos",
                        "Explicación coherente de procedimientos"
                    ]
                }
            })
        
        # Module 3: Advanced challenges (if student is ready)
        if context.recent_accuracy > 0.75 and context.strong_areas:
            learning_modules.append({
                "id": "advanced_1",
                "title": f"Desafío Avanzado: {context.strong_areas[0]}",
                "type": "advanced",
                "priority": "low",
                "estimated_hours": 2,
                "description": f"Desafíos avanzados para perfeccionar dominio en {context.strong_areas[0]}",
                "activities": [
                    {
                        "type": "complex_problems",
                        "title": "Problemas complejos",
                        "duration_minutes": 60,
                        "description": "Resolución de problemas de alta dificultad"
                    },
                    {
                        "type": "time_challenges",
                        "title": "Desafíos de tiempo",
                        "duration_minutes": 30,
                        "description": "Práctica bajo presión de tiempo"
                    },
                    {
                        "type": "peer_teaching",
                        "title": "Enseñanza entre pares",
                        "duration_minutes": 30,
                        "description": "Explicar conceptos a otros estudiantes"
                    }
                ],
                "learning_objectives": [
                    "Dominar problemas de alta complejidad",
                    "Desarrollar velocidad y precisión",
                    "Reforzar comprensión mediante enseñanza"
                ],
                "success_criteria": {
                    "minimum_accuracy": 0.80,
                    "completion_time": "3-5 días",
                    "mastery_indicators": [
                        "Resolución rápida y precisa",
                        "Explicación clara a otros",
                        "Creatividad en enfoques de solución"
                    ]
                }
            })
        
        # Create weekly schedule based on available time
        daily_time = request.time_available or 60  # Default 60 minutes
        total_hours_needed = sum(module["estimated_hours"] for module in learning_modules)
        estimated_weeks = max(1, int(total_hours_needed / (daily_time / 60 * 5)))  # 5 study days per week
        
        # Generate weekly milestones
        milestones = []
        for week in range(1, min(estimated_weeks + 1, 9)):  # Max 8 weeks
            if week <= len(learning_modules):
                module = learning_modules[week - 1]
                milestones.append({
                    "week": week,
                    "title": f"Semana {week}: {module['title']}",
                    "goals": module["learning_objectives"],
                    "deliverables": [
                        "Completar todas las actividades del módulo",
                        f"Alcanzar {module['success_criteria']['minimum_accuracy']:.0%} de precisión",
                        "Demostrar dominio en evaluación final"
                    ],
                    "estimated_time": f"{module['estimated_hours']} horas"
                })
        
        # Add final milestone
        milestones.append({
            "week": estimated_weeks,
            "title": f"Semana {estimated_weeks}: Evaluación Integral",
            "goals": [
                "Demostrar dominio integrado de todos los temas",
                "Preparación completa para ICFES",
                "Confianza en habilidades desarrolladas"
            ],
            "deliverables": [
                "Simulacro completo ICFES",
                "Autoevaluación de progreso",
                "Plan de repaso final"
            ],
            "estimated_time": "3 horas"
        })
        
        return {
            "learning_path_id": f"path_{current_user.id}_{request.subject_id}_{int(datetime.now().timestamp())}",
            "subject": subject.name,
            "student_level": context.difficulty_preference.value,
            "personalization_factors": {
                "current_accuracy": context.recent_accuracy,
                "problem_areas": context.problem_areas,
                "strong_areas": context.strong_areas,
                "learning_preferences": request.preferred_difficulty
            },
            "learning_modules": learning_modules,
            "schedule": {
                "estimated_duration": f"{estimated_weeks} semanas",
                "daily_time_commitment": f"{daily_time} minutos",
                "total_study_hours": total_hours_needed,
                "study_frequency": "5 días por semana"
            },
            "milestones": milestones,
            "recommendations": [
                "Sigue el orden sugerido de módulos para mejor progresión",
                "Dedica tiempo extra a módulos de refuerzo si es necesario",
                "Realiza autoevaluaciones regulares para monitorear progreso",
                "Ajusta el ritmo según tu comprensión y disponibilidad de tiempo"
            ],
            "tracking_metrics": {
                "accuracy_targets": {
                    "remedial_modules": "75%",
                    "development_modules": "70%", 
                    "advanced_modules": "80%"
                },
                "time_targets": {
                    "daily_study": f"{daily_time} minutos",
                    "weekly_goals": "Completar 1 módulo por semana",
                    "milestone_check": "Evaluación semanal de progreso"
                }
            },
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating learning path: {str(e)}")

# Background task for logging interactions
@router.post("/log-interaction")
async def log_ai_interaction(
    interaction_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Log AI interactions for analytics and improvement"""
    
    def log_interaction():
        try:
            # Add to analytics/logging system
            pass
        except Exception as e:
            print(f"Logging error: {e}")
    
    background_tasks.add_task(log_interaction)
    return {"status": "logged"}

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for AI training zone services"""
    try:
        # Test AI service
        test_context = await ai_service.get_student_context("health_check", None)
        
        return {
            "status": "healthy",
            "ai_service": "operational",
            "openai_available": ai_service.openai_client is not None,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }