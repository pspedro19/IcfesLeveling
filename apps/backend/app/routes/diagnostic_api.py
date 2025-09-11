"""
Complete Diagnostic API Endpoints
Provides comprehensive diagnostic test functionality with adaptive question selection,
real-time feedback, and theta score calculation.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import uuid

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.subject import Subject
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.question import Question
from ..services.adaptive_diagnostic_service import AdaptiveDiagnosticService
from ..schemas.diagnostic_test import (
    DiagnosticTestCreate,
    DiagnosticTestQuestion,
    DiagnosticTestAnswer as DiagnosticAnswerSubmit,
    DiagnosticResultResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diagnostic", tags=["diagnostic-api"])

# Global session store for test states
test_sessions = {}

class DiagnosticTestSession:
    """Manages individual diagnostic test session state"""
    
    def __init__(self, test_id: str, user_id: str, subject_id: str, service: AdaptiveDiagnosticService):
        self.test_id = test_id
        self.user_id = user_id
        self.subject_id = subject_id
        self.service = service
        self.current_question_index = 0
        self.questions = []
        self.answers = []
        self.current_theta = 0.0
        self.started_at = datetime.utcnow()
        
    def get_next_question(self) -> Optional[DiagnosticTestQuestion]:
        """Get the next adaptive question based on current performance"""
        if self.current_question_index >= len(self.questions) and len(self.questions) < 50:
            # Generate new questions based on current theta
            new_questions = self.service.get_adaptive_diagnostic_questions(
                test_id=self.test_id,
                user_id=self.user_id,
                num_questions=min(5, 50 - len(self.questions))
            )
            self.questions.extend(new_questions)
        
        if self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def submit_answer(self, question_id: str, user_answer: str, response_time_ms: int) -> Dict[str, Any]:
        """Submit answer and get feedback with theta update"""
        result = self.service.process_adaptive_answer(
            test_id=self.test_id,
            question_id=question_id,
            user_answer=user_answer.upper(),
            response_time_ms=response_time_ms
        )
        
        self.answers.append({
            'question_id': question_id,
            'user_answer': user_answer.upper(),
            'correct': result['correct'],
            'response_time_ms': response_time_ms,
            'theta_before': self.current_theta,
            'theta_after': result.get('new_theta', self.current_theta)
        })
        
        self.current_theta = result.get('new_theta', self.current_theta)
        self.current_question_index += 1
        
        return result

@router.get("/start/{subject_id}")
async def start_diagnostic_test(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new adaptive diagnostic test for the specified subject.
    
    Returns:
    - test_id: Unique identifier for the test session
    - subject: Subject information
    - initial_theta: Starting ability estimate
    - status: Test status
    """
    try:
        # Validate subject exists
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        # Initialize adaptive diagnostic service
        adaptive_service = AdaptiveDiagnosticService(db)
        
        # Create diagnostic test
        test_data = DiagnosticTestCreate(subject_id=subject_id, test_type="adaptive_icfes")
        test = adaptive_service.create_adaptive_diagnostic_test(
            user_id=str(current_user.id),
            subject_id=subject_id,
            test_type="adaptive_icfes"
        )
        
        # Create session
        session = DiagnosticTestSession(
            test_id=str(test.id),
            user_id=str(current_user.id),
            subject_id=subject_id,
            service=adaptive_service
        )
        test_sessions[str(test.id)] = session
        
        logger.info(f"Started diagnostic test {test.id} for user {current_user.id} in subject {subject_id}")
        
        return {
            "test_id": str(test.id),
            "subject": {
                "id": str(subject.id),
                "name": subject.name,
                "description": getattr(subject, 'description', '')
            },
            "initial_theta": session.current_theta,
            "status": "started",
            "message": f"Diagnostic test started for {subject.name}",
            "started_at": session.started_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting diagnostic test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start diagnostic test: {str(e)}")

@router.get("/next-question")
async def get_next_question(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the next adaptive question for the ongoing test.
    
    Query Parameters:
    - test_id: The test session identifier
    
    Returns:
    - question: Next question object with adaptive difficulty
    - question_number: Current question number
    - total_questions_answered: Number of questions answered so far
    - current_theta: Current ability estimate
    - difficulty_level: Question difficulty level
    """
    try:
        # Validate test session
        if test_id not in test_sessions:
            raise HTTPException(status_code=404, detail="Test session not found")
        
        session = test_sessions[test_id]
        
        # Verify user ownership
        if session.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied to this test session")
        
        # Get next question
        next_question = session.get_next_question()
        
        if not next_question:
            # Test is complete, should finalize
            return {
                "question": None,
                "test_complete": True,
                "message": "Test completed. Call /results to get final results.",
                "questions_answered": len(session.answers),
                "current_theta": session.current_theta
            }
        
        logger.info(f"Serving question {session.current_question_index + 1} for test {test_id}")
        
        return {
            "question": {
                "id": next_question.id,
                "question_text": next_question.question_text,
                "options": next_question.options,
                "subject": next_question.subject,
                "topic": next_question.topic,
                "difficulty": next_question.difficulty,
                "hint": next_question.hint
            },
            "question_number": session.current_question_index + 1,
            "total_questions_answered": len(session.answers),
            "current_theta": session.current_theta,
            "difficulty_level": _get_difficulty_level_name(next_question.difficulty),
            "test_complete": False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next question: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get next question: {str(e)}")

@router.post("/answer")
async def submit_answer(
    test_id: str,
    answer_data: DiagnosticAnswerSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit an answer and get real-time feedback with adaptive theta updates.
    
    Body:
    - question_id: ID of the question being answered
    - user_answer: User's selected answer (A, B, C, D, or E)
    - response_time_ms: Time taken to answer in milliseconds
    
    Returns:
    - correct: Whether the answer was correct
    - feedback: Detailed feedback message
    - theta_change: Change in ability estimate
    - new_theta: Updated theta score
    - performance_trend: Current performance trend
    - next_difficulty_recommendation: Suggested difficulty for next question
    """
    try:
        # Validate test session
        if test_id not in test_sessions:
            raise HTTPException(status_code=404, detail="Test session not found")
        
        session = test_sessions[test_id]
        
        # Verify user ownership
        if session.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied to this test session")
        
        # Submit answer and get adaptive feedback
        old_theta = session.current_theta
        result = session.submit_answer(
            question_id=answer_data.question_id,
            user_answer=answer_data.user_answer,
            response_time_ms=answer_data.response_time_ms
        )
        
        theta_change = session.current_theta - old_theta
        
        # Generate feedback message
        feedback_message = _generate_feedback_message(result['correct'], theta_change, result)
        
        logger.info(f"Answer submitted for test {test_id}, question {answer_data.question_id}: {'correct' if result['correct'] else 'incorrect'}")
        
        return {
            "correct": result['correct'],
            "feedback": {
                "message": feedback_message,
                "encouragement": result.get('encouragement', 'Keep up the great work!'),
                "explanation": result.get('explanation', '')
            },
            "theta_change": round(theta_change, 3),
            "new_theta": round(session.current_theta, 3),
            "performance_trend": result.get('performance_trend', 'stable'),
            "next_difficulty_recommendation": result.get('next_recommended_difficulty', 5),
            "questions_answered": len(session.answers),
            "current_accuracy": _calculate_accuracy(session.answers),
            "confidence_interval": result.get('confidence_interval', [session.current_theta - 0.5, session.current_theta + 0.5])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to submit answer: {str(e)}")

@router.get("/results", response_model=DiagnosticResultResponse)
async def get_final_results(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive final results with theta score and detailed analysis.
    
    Query Parameters:
    - test_id: The test session identifier
    
    Returns:
    - score: Number of correct answers
    - percentage: Score as percentage
    - theta_score: Final IRT theta ability estimate
    - rank: ICFES performance rank (A, B, C, D, E, S)
    - strengths: List of strong topic areas
    - weaknesses: List of areas needing improvement
    - recommendations: Personalized study recommendations
    - detailed_analysis: Comprehensive performance breakdown
    """
    try:
        # Validate test session
        if test_id not in test_sessions:
            raise HTTPException(status_code=404, detail="Test session not found")
        
        session = test_sessions[test_id]
        
        # Verify user ownership
        if session.user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="Access denied to this test session")
        
        # Finalize the test
        adaptive_service = session.service
        final_result = adaptive_service.finalize_adaptive_test(test_id)
        
        # Calculate comprehensive metrics
        correct_answers = sum(1 for answer in session.answers if answer['correct'])
        total_questions = len(session.answers)
        percentage = int((correct_answers / total_questions) * 100) if total_questions > 0 else 0
        
        # Determine ICFES rank based on theta and percentage
        icfes_rank = _calculate_icfes_rank(session.current_theta, percentage)
        
        # Generate strengths and weaknesses
        analysis = _analyze_performance_by_topic(session.answers, db)
        
        # Generate recommendations
        recommendations = _generate_personalized_recommendations(
            session.current_theta, 
            percentage, 
            analysis, 
            session.subject_id,
            db
        )
        
        # Clean up session
        if test_id in test_sessions:
            del test_sessions[test_id]
        
        logger.info(f"Completed diagnostic test {test_id} with score {percentage}% (theta: {session.current_theta:.3f})")
        
        return {
            "score": correct_answers,
            "percentage": percentage,
            "theta_score": round(session.current_theta, 3),
            "rank": icfes_rank,
            "strengths": analysis.get('strengths', []),
            "weaknesses": analysis.get('weaknesses', []),
            "recommendations": recommendations,
            "detailed_analysis": {
                "total_questions": total_questions,
                "time_spent_minutes": (datetime.utcnow() - session.started_at).total_seconds() / 60,
                "average_response_time": _calculate_average_response_time(session.answers),
                "difficulty_distribution": _analyze_difficulty_distribution(session.answers),
                "performance_progression": _analyze_performance_progression(session.answers),
                "mastery_level": _get_mastery_level(session.current_theta),
                "percentile_rank": _calculate_percentile_rank(session.current_theta),
                "topic_breakdown": analysis.get('topic_breakdown', {}),
                "next_steps": _generate_next_steps(session.current_theta, analysis)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting final results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get final results: {str(e)}")

# Helper functions

def _get_difficulty_level_name(difficulty: int) -> str:
    """Convert numeric difficulty to descriptive name"""
    if difficulty <= 3:
        return "Easy"
    elif difficulty <= 6:
        return "Medium"
    elif difficulty <= 8:
        return "Hard"
    else:
        return "Very Hard"

def _generate_feedback_message(correct: bool, theta_change: float, result: Dict) -> str:
    """Generate contextual feedback message"""
    if correct:
        if theta_change > 0.2:
            return "Excellent! Your ability level has increased significantly."
        elif theta_change > 0:
            return "Correct! You're showing good understanding."
        else:
            return "Correct answer! Keep maintaining this level."
    else:
        if theta_change > -0.1:
            return "Incorrect, but you're close. Review the concept and try again."
        elif theta_change > -0.3:
            return "Incorrect answer. Consider studying this topic more deeply."
        else:
            return "This was challenging. Don't worry, every mistake is a learning opportunity."

def _calculate_accuracy(answers: List[Dict]) -> float:
    """Calculate current accuracy percentage"""
    if not answers:
        return 0.0
    correct = sum(1 for answer in answers if answer['correct'])
    return round((correct / len(answers)) * 100, 1)

def _calculate_icfes_rank(theta: float, percentage: int) -> str:
    """Calculate ICFES rank based on theta and percentage"""
    if percentage >= 90 or theta >= 2.0:
        return "S"
    elif percentage >= 80 or theta >= 1.5:
        return "A"
    elif percentage >= 65 or theta >= 0.5:
        return "B"
    elif percentage >= 50 or theta >= -0.5:
        return "C"
    elif percentage >= 35 or theta >= -1.5:
        return "D"
    else:
        return "E"

def _analyze_performance_by_topic(answers: List[Dict], db: Session) -> Dict[str, Any]:
    """Analyze performance breakdown by topics"""
    topic_performance = {}
    
    for answer in answers:
        # Get question to determine topic
        question = db.query(Question).filter(Question.id == answer['question_id']).first()
        if question and hasattr(question, 'topic') and question.topic:
            topic = question.topic.name if hasattr(question.topic, 'name') else str(question.topic)
            if topic not in topic_performance:
                topic_performance[topic] = {'correct': 0, 'total': 0}
            
            topic_performance[topic]['total'] += 1
            if answer['correct']:
                topic_performance[topic]['correct'] += 1
    
    # Determine strengths and weaknesses
    strengths = []
    weaknesses = []
    
    for topic, performance in topic_performance.items():
        accuracy = performance['correct'] / performance['total'] if performance['total'] > 0 else 0
        if accuracy >= 0.8:
            strengths.append(topic)
        elif accuracy <= 0.4:
            weaknesses.append(topic)
    
    return {
        'strengths': strengths[:5],  # Top 5 strengths
        'weaknesses': weaknesses[:5],  # Top 5 weaknesses
        'topic_breakdown': topic_performance
    }

def _generate_personalized_recommendations(theta: float, percentage: int, analysis: Dict, subject_id: str, db: Session) -> List[str]:
    """Generate personalized study recommendations"""
    recommendations = []
    
    # Subject-specific recommendations
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    subject_name = subject.name if subject else "this subject"
    
    # Performance-based recommendations
    if percentage < 50:
        recommendations.append(f"Focus on mastering fundamental concepts in {subject_name}")
        recommendations.append("Practice with easier questions to build confidence")
    elif percentage < 70:
        recommendations.append(f"Work on intermediate topics in {subject_name}")
        recommendations.append("Review incorrect answers to identify knowledge gaps")
    else:
        recommendations.append(f"Challenge yourself with advanced {subject_name} problems")
        recommendations.append("Maintain your strong performance with regular practice")
    
    # Weakness-specific recommendations
    if analysis.get('weaknesses'):
        recommendations.append(f"Prioritize studying: {', '.join(analysis['weaknesses'][:3])}")
    
    # Theta-based recommendations
    if theta < -1.0:
        recommendations.append("Consider seeking additional support or tutoring")
    elif theta > 1.5:
        recommendations.append("You're performing at an advanced level. Consider helping others or taking on challenges")
    
    return recommendations[:5]  # Limit to 5 recommendations

def _calculate_average_response_time(answers: List[Dict]) -> float:
    """Calculate average response time in seconds"""
    if not answers:
        return 0.0
    total_time = sum(answer['response_time_ms'] for answer in answers)
    return round(total_time / (len(answers) * 1000), 1)  # Convert to seconds

def _analyze_difficulty_distribution(answers: List[Dict]) -> Dict[str, int]:
    """Analyze distribution of question difficulties attempted"""
    distribution = {"Easy": 0, "Medium": 0, "Hard": 0, "Very Hard": 0}
    # This would need to be implemented based on question difficulty data
    return distribution

def _analyze_performance_progression(answers: List[Dict]) -> str:
    """Analyze how performance changed over the course of the test"""
    if len(answers) < 5:
        return "insufficient_data"
    
    first_half = answers[:len(answers)//2]
    second_half = answers[len(answers)//2:]
    
    first_accuracy = sum(1 for a in first_half if a['correct']) / len(first_half)
    second_accuracy = sum(1 for a in second_half if a['correct']) / len(second_half)
    
    if second_accuracy > first_accuracy + 0.1:
        return "improving"
    elif second_accuracy < first_accuracy - 0.1:
        return "declining"
    else:
        return "stable"

def _get_mastery_level(theta: float) -> str:
    """Get descriptive mastery level based on theta"""
    if theta >= 2.0:
        return "Expert"
    elif theta >= 1.0:
        return "Advanced"
    elif theta >= 0:
        return "Proficient"
    elif theta >= -1.0:
        return "Developing"
    else:
        return "Beginner"

def _calculate_percentile_rank(theta: float) -> int:
    """Calculate approximate percentile rank based on theta"""
    # This is a simplified mapping - in real implementation you'd use normative data
    if theta >= 2.0:
        return 98
    elif theta >= 1.5:
        return 93
    elif theta >= 1.0:
        return 84
    elif theta >= 0.5:
        return 69
    elif theta >= 0:
        return 50
    elif theta >= -0.5:
        return 31
    elif theta >= -1.0:
        return 16
    else:
        return 7

def _generate_next_steps(theta: float, analysis: Dict) -> List[str]:
    """Generate specific next steps based on performance"""
    next_steps = []
    
    if theta < 0:
        next_steps.append("Practice fundamental concepts daily")
        next_steps.append("Work through easier practice problems")
    elif theta < 1.0:
        next_steps.append("Take practice tests regularly")
        next_steps.append("Focus on consistency in performance")
    else:
        next_steps.append("Challenge yourself with advanced materials")
        next_steps.append("Consider peer tutoring or teaching others")
    
    if analysis.get('weaknesses'):
        next_steps.append(f"Create a study plan focusing on {analysis['weaknesses'][0]}")
    
    return next_steps[:3]