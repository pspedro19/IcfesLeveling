from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_, text
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import random
import logging
import json

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer, DiagnosticTestResult
from ..models.topic import Topic
from ..models.question import Question
from ..models.subject import Subject
from ..models.user import User
from ..models.practice_session import PracticeSession

class AdaptiveTrainingZoneService:
    """
    Service for adapting training zone questions based on diagnostic results.
    Updates question pools, difficulty levels, and focus areas based on student performance.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def update_training_zone_for_user(self, user_id: str, subject_id: str, 
                                    diagnostic_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update training zone questions and configuration based on latest diagnostic results.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            diagnostic_results: Results from latest diagnostic assessment
            
        Returns:
            Updated training zone configuration
        """
        try:
            # Analyze diagnostic results to determine focus areas
            analysis = self._analyze_diagnostic_performance(diagnostic_results)
            
            # Get current training zone configuration
            current_config = self._get_current_training_config(user_id, subject_id)
            
            # Generate adaptive question pools
            question_pools = self._generate_adaptive_question_pools(
                user_id, subject_id, analysis
            )
            
            # Update difficulty progression
            difficulty_config = self._update_difficulty_progression(
                user_id, subject_id, analysis, current_config
            )
            
            # Create focus sessions for weak areas
            focus_sessions = self._create_focus_sessions(
                user_id, subject_id, analysis
            )
            
            # Update training zone configuration
            updated_config = {
                "user_id": user_id,
                "subject_id": subject_id,
                "updated_at": datetime.utcnow(),
                "performance_analysis": analysis,
                "question_pools": question_pools,
                "difficulty_config": difficulty_config,
                "focus_sessions": focus_sessions,
                "adaptive_settings": self._calculate_adaptive_settings(analysis),
                "next_review_date": datetime.utcnow() + timedelta(days=7)
            }
            
            # Store configuration in database
            self._store_training_config(user_id, subject_id, updated_config)
            
            self.logger.info(f"Updated training zone for user {user_id}, subject {subject_id}")
            return updated_config
            
        except Exception as e:
            self.logger.error(f"Error updating training zone for user {user_id}: {str(e)}")
            raise
    
    def get_adaptive_questions(self, user_id: str, subject_id: str, 
                             session_type: str = "adaptive", count: int = 20) -> List[Dict[str, Any]]:
        """
        Get adaptively selected questions for a training session.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            session_type: Type of session ("adaptive", "focus", "review", "challenge")
            count: Number of questions to return
            
        Returns:
            List of adaptively selected questions
        """
        try:
            # Get training configuration
            config = self._get_current_training_config(user_id, subject_id)
            
            if session_type == "focus":
                questions = self._get_focus_questions(user_id, subject_id, config, count)
            elif session_type == "review":
                questions = self._get_review_questions(user_id, subject_id, config, count)
            elif session_type == "challenge":
                questions = self._get_challenge_questions(user_id, subject_id, config, count)
            else:  # adaptive
                questions = self._get_adaptive_questions_mixed(user_id, subject_id, config, count)
            
            # Format questions for frontend
            formatted_questions = []
            for question in questions:
                formatted_questions.append(self._format_question_for_training(question, config))
            
            # Log session generation
            self._log_training_session(user_id, subject_id, session_type, len(formatted_questions))
            
            return formatted_questions
            
        except Exception as e:
            self.logger.error(f"Error getting adaptive questions for user {user_id}: {str(e)}")
            raise
    
    def update_question_performance(self, user_id: str, question_id: str, 
                                  is_correct: bool, response_time_ms: int,
                                  hints_used: int = 0) -> Dict[str, Any]:
        """
        Update question performance tracking and adaptive algorithms.
        
        Args:
            user_id: User identifier
            question_id: Question identifier
            is_correct: Whether answer was correct
            response_time_ms: Response time in milliseconds
            hints_used: Number of hints used
            
        Returns:
            Updated performance metrics and next question recommendation
        """
        try:
            # Get question details
            question = self.db.query(Question).filter(Question.id == question_id).first()
            if not question:
                raise ValueError(f"Question {question_id} not found")
            
            # Update performance tracking
            performance_data = {
                "question_id": question_id,
                "user_id": user_id,
                "is_correct": is_correct,
                "response_time_ms": response_time_ms,
                "hints_used": hints_used,
                "difficulty_level": question.difficulty,
                "topic_id": question.topic_id,
                "updated_at": datetime.utcnow()
            }
            
            # Store performance data
            self._store_question_performance(performance_data)
            
            # Update adaptive parameters
            adaptive_update = self._update_adaptive_parameters(user_id, question, performance_data)
            
            # Get next question recommendation
            next_question = self._recommend_next_question(user_id, str(question.subject_id), adaptive_update)
            
            return {
                "performance_recorded": True,
                "adaptive_update": adaptive_update,
                "next_question": next_question,
                "performance_summary": self._get_session_performance_summary(user_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error updating question performance: {str(e)}")
            raise
    
    def get_training_recommendations(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """
        Get personalized training recommendations based on performance data.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            
        Returns:
            Personalized training recommendations
        """
        try:
            # Get recent performance data
            performance_analysis = self._analyze_recent_performance(user_id, subject_id)
            
            # Get training configuration
            config = self._get_current_training_config(user_id, subject_id)
            
            # Generate recommendations
            recommendations = {
                "immediate_focus": self._get_immediate_focus_recommendations(performance_analysis),
                "session_recommendations": self._get_session_recommendations(performance_analysis, config),
                "difficulty_adjustments": self._get_difficulty_recommendations(performance_analysis),
                "time_management": self._get_time_management_recommendations(performance_analysis),
                "topic_priorities": self._get_topic_priority_recommendations(performance_analysis),
                "study_schedule": self._get_study_schedule_recommendations(user_id, subject_id, performance_analysis)
            }
            
            return {
                "user_id": user_id,
                "subject_id": subject_id,
                "generated_at": datetime.utcnow(),
                "performance_analysis": performance_analysis,
                "recommendations": recommendations,
                "confidence_score": self._calculate_recommendation_confidence(performance_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating training recommendations: {str(e)}")
            raise
    
    def track_learning_progress(self, user_id: str, subject_id: str, 
                              time_period: int = 30) -> Dict[str, Any]:
        """
        Track detailed learning progress over specified time period.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            time_period: Days to look back (default 30)
            
        Returns:
            Detailed learning progress analysis
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get practice session data
            practice_sessions = self.db.query(PracticeSession).filter(
                and_(
                    PracticeSession.user_id == user_id,
                    PracticeSession.subject_id == subject_id,
                    PracticeSession.created_at >= start_date
                )
            ).order_by(PracticeSession.created_at.asc()).all()
            
            # Get diagnostic test results
            diagnostic_results = self.db.query(DiagnosticTestResult).filter(
                and_(
                    DiagnosticTestResult.user_id == user_id,
                    DiagnosticTestResult.subject_id == subject_id,
                    DiagnosticTestResult.created_at >= start_date
                )
            ).order_by(DiagnosticTestResult.created_at.asc()).all()
            
            # Analyze progress trends
            progress_analysis = self._analyze_learning_progress(practice_sessions, diagnostic_results)
            
            # Calculate learning metrics
            learning_metrics = self._calculate_learning_metrics(practice_sessions, diagnostic_results)
            
            # Generate progress insights
            insights = self._generate_progress_insights(progress_analysis, learning_metrics)
            
            return {
                "user_id": user_id,
                "subject_id": subject_id,
                "time_period_days": time_period,
                "analysis_date": datetime.utcnow(),
                "progress_analysis": progress_analysis,
                "learning_metrics": learning_metrics,
                "insights": insights,
                "total_practice_sessions": len(practice_sessions),
                "total_questions_attempted": len(diagnostic_results)
            }
            
        except Exception as e:
            self.logger.error(f"Error tracking learning progress: {str(e)}")
            raise
    
    # Private helper methods
    
    def _analyze_diagnostic_performance(self, diagnostic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze diagnostic performance to identify focus areas."""
        comparison = diagnostic_results.get("comparison", {})
        current_scores = comparison.get("current_score_by_topic", {})
        previous_scores = comparison.get("initial_score_by_topic", {})
        
        # Identify weak areas (below 60%)
        weak_topics = []
        strong_topics = []
        improving_topics = []
        declining_topics = []
        
        for topic, current_score in current_scores.items():
            if current_score < 60:
                weak_topics.append({"topic": topic, "score": current_score, "priority": "high"})
            elif current_score >= 80:
                strong_topics.append({"topic": topic, "score": current_score})
            
            # Compare with previous if available
            previous_score = previous_scores.get(topic, current_score)
            improvement = current_score - previous_score
            
            if improvement > 10:
                improving_topics.append({"topic": topic, "improvement": improvement})
            elif improvement < -10:
                declining_topics.append({"topic": topic, "decline": abs(improvement)})
        
        # Determine overall performance level
        overall_score = comparison.get("current_score", 0)
        if overall_score >= 85:
            performance_level = "advanced"
        elif overall_score >= 70:
            performance_level = "intermediate"
        elif overall_score >= 50:
            performance_level = "developing"
        else:
            performance_level = "foundational"
        
        return {
            "overall_score": overall_score,
            "performance_level": performance_level,
            "weak_topics": weak_topics,
            "strong_topics": strong_topics,
            "improving_topics": improving_topics,
            "declining_topics": declining_topics,
            "improvement_percentage": comparison.get("improvement_percentage", 0),
            "topics_needing_focus": len(weak_topics) + len(declining_topics)
        }
    
    def _get_current_training_config(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Get current training configuration for user and subject."""
        # For now, return default configuration
        # In a real implementation, this would be stored in database
        return {
            "difficulty_level": "adaptive",
            "focus_areas": [],
            "question_pool_size": 100,
            "session_length": 20,
            "adaptive_parameters": {
                "difficulty_adjustment_rate": 0.1,
                "performance_threshold": 0.7,
                "time_weight": 0.3
            }
        }
    
    def _generate_adaptive_question_pools(self, user_id: str, subject_id: str, 
                                        analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate adaptive question pools based on performance analysis."""
        pools = {
            "weak_areas": [],
            "review": [],
            "challenge": [],
            "mixed": []
        }
        
        # Get questions for weak topics
        weak_topics = [item["topic"] for item in analysis["weak_topics"]]
        if weak_topics:
            # Get topic IDs
            topic_objects = self.db.query(Topic).filter(
                Topic.name.in_(weak_topics)
            ).all()
            topic_ids = [str(t.id) for t in topic_objects]
            
            # Get questions for weak topics (easier to medium difficulty)
            weak_questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.topic_id.in_(topic_ids),
                    Question.difficulty.between(3, 6)
                )
            ).limit(50).all()
            
            pools["weak_areas"] = [str(q.id) for q in weak_questions]
        
        # Get review questions (medium difficulty across all topics)
        review_questions = self.db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                Question.difficulty.between(4, 7)
            )
        ).limit(50).all()
        pools["review"] = [str(q.id) for q in review_questions]
        
        # Get challenge questions (high difficulty)
        if analysis["performance_level"] in ["intermediate", "advanced"]:
            challenge_questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty.between(7, 10)
                )
            ).limit(30).all()
            pools["challenge"] = [str(q.id) for q in challenge_questions]
        
        # Mixed pool with balanced distribution
        mixed_questions = self.db.query(Question).filter(
            Question.subject_id == subject_id
        ).limit(100).all()
        pools["mixed"] = [str(q.id) for q in mixed_questions]
        
        return pools
    
    def _update_difficulty_progression(self, user_id: str, subject_id: str, 
                                     analysis: Dict[str, Any], 
                                     current_config: Dict[str, Any]) -> Dict[str, Any]:
        """Update difficulty progression based on performance."""
        performance_level = analysis["performance_level"]
        overall_score = analysis["overall_score"]
        
        # Calculate target difficulty range
        if performance_level == "foundational":
            target_range = (2, 5)
            progression_rate = 0.05
        elif performance_level == "developing":
            target_range = (3, 6)
            progression_rate = 0.1
        elif performance_level == "intermediate":
            target_range = (4, 8)
            progression_rate = 0.15
        else:  # advanced
            target_range = (6, 10)
            progression_rate = 0.2
        
        # Adjust based on recent improvement
        improvement = analysis["improvement_percentage"]
        if improvement > 10:
            # Accelerate progression
            target_range = (target_range[0] + 1, min(10, target_range[1] + 1))
            progression_rate *= 1.2
        elif improvement < -5:
            # Slow down progression
            target_range = (max(1, target_range[0] - 1), target_range[1])
            progression_rate *= 0.8
        
        return {
            "target_difficulty_range": target_range,
            "progression_rate": progression_rate,
            "adaptive_adjustment": True,
            "last_updated": datetime.utcnow()
        }
    
    def _create_focus_sessions(self, user_id: str, subject_id: str, 
                             analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create focused training sessions for weak areas."""
        focus_sessions = []
        
        # Create sessions for weak topics
        for weak_topic in analysis["weak_topics"]:
            topic_name = weak_topic["topic"]
            priority = weak_topic["priority"]
            
            session = {
                "session_id": f"focus_{topic_name.lower().replace(' ', '_')}",
                "topic": topic_name,
                "priority": priority,
                "target_questions": 15 if priority == "high" else 10,
                "difficulty_range": (2, 5) if weak_topic["score"] < 40 else (3, 6),
                "estimated_duration_minutes": 20,
                "description": f"Sesión enfocada en reforzar {topic_name}",
                "created_at": datetime.utcnow()
            }
            focus_sessions.append(session)
        
        # Create sessions for declining topics
        for declining_topic in analysis["declining_topics"]:
            topic_name = declining_topic["topic"]
            
            session = {
                "session_id": f"recovery_{topic_name.lower().replace(' ', '_')}",
                "topic": topic_name,
                "priority": "medium",
                "target_questions": 12,
                "difficulty_range": (3, 7),
                "estimated_duration_minutes": 18,
                "description": f"Sesión de recuperación para {topic_name}",
                "created_at": datetime.utcnow()
            }
            focus_sessions.append(session)
        
        return focus_sessions
    
    def _calculate_adaptive_settings(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate adaptive settings based on performance analysis."""
        performance_level = analysis["performance_level"]
        overall_score = analysis["overall_score"]
        
        # Adjust question selection algorithm
        if performance_level == "foundational":
            settings = {
                "question_repeat_probability": 0.3,
                "difficulty_increment": 0.5,
                "hint_availability": "high",
                "time_pressure": "low"
            }
        elif performance_level == "developing":
            settings = {
                "question_repeat_probability": 0.2,
                "difficulty_increment": 0.7,
                "hint_availability": "medium",
                "time_pressure": "medium"
            }
        elif performance_level == "intermediate":
            settings = {
                "question_repeat_probability": 0.1,
                "difficulty_increment": 1.0,
                "hint_availability": "low",
                "time_pressure": "medium"
            }
        else:  # advanced
            settings = {
                "question_repeat_probability": 0.05,
                "difficulty_increment": 1.2,
                "hint_availability": "minimal",
                "time_pressure": "high"
            }
        
        # Adjust based on improvement trend
        improvement = analysis["improvement_percentage"]
        if improvement > 15:
            settings["difficulty_increment"] *= 1.3
        elif improvement < -10:
            settings["difficulty_increment"] *= 0.7
            settings["hint_availability"] = "high"
        
        return settings
    
    def _store_training_config(self, user_id: str, subject_id: str, config: Dict[str, Any]):
        """Store training configuration in database."""
        # For now, we'll log it. In a real implementation, store in database
        self.logger.info(f"Stored training config for user {user_id}, subject {subject_id}")
    
    def _get_focus_questions(self, user_id: str, subject_id: str, 
                           config: Dict[str, Any], count: int) -> List[Question]:
        """Get questions focused on weak areas."""
        # Get questions from weak areas pool
        weak_pool_ids = config.get("question_pools", {}).get("weak_areas", [])
        
        if weak_pool_ids:
            questions = self.db.query(Question).filter(
                Question.id.in_(weak_pool_ids[:count])
            ).all()
        else:
            # Fallback to basic difficulty questions
            questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty.between(3, 6)
                )
            ).limit(count).all()
        
        return questions
    
    def _get_review_questions(self, user_id: str, subject_id: str, 
                            config: Dict[str, Any], count: int) -> List[Question]:
        """Get review questions across all topics."""
        review_pool_ids = config.get("question_pools", {}).get("review", [])
        
        if review_pool_ids:
            questions = self.db.query(Question).filter(
                Question.id.in_(review_pool_ids[:count])
            ).all()
        else:
            questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty.between(4, 7)
                )
            ).limit(count).all()
        
        return questions
    
    def _get_challenge_questions(self, user_id: str, subject_id: str, 
                               config: Dict[str, Any], count: int) -> List[Question]:
        """Get challenging questions for advanced practice."""
        challenge_pool_ids = config.get("question_pools", {}).get("challenge", [])
        
        if challenge_pool_ids:
            questions = self.db.query(Question).filter(
                Question.id.in_(challenge_pool_ids[:count])
            ).all()
        else:
            questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty.between(7, 10)
                )
            ).limit(count).all()
        
        return questions
    
    def _get_adaptive_questions_mixed(self, user_id: str, subject_id: str, 
                                    config: Dict[str, Any], count: int) -> List[Question]:
        """Get adaptively mixed questions based on performance."""
        # Get recent performance to determine mix
        recent_performance = self._get_recent_performance_summary(user_id, subject_id)
        
        # Determine question distribution
        if recent_performance.get("accuracy", 0.5) > 0.8:
            # High performance: more challenging questions
            easy_count = int(count * 0.2)
            medium_count = int(count * 0.3)
            hard_count = count - easy_count - medium_count
        elif recent_performance.get("accuracy", 0.5) > 0.6:
            # Medium performance: balanced distribution
            easy_count = int(count * 0.3)
            medium_count = int(count * 0.5)
            hard_count = count - easy_count - medium_count
        else:
            # Low performance: focus on easier questions
            easy_count = int(count * 0.5)
            medium_count = int(count * 0.4)
            hard_count = count - easy_count - medium_count
        
        questions = []
        
        # Get easy questions
        if easy_count > 0:
            easy_questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty.between(2, 4)
                )
            ).limit(easy_count).all()
            questions.extend(easy_questions)
        
        # Get medium questions
        if medium_count > 0:
            medium_questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty.between(5, 7)
                )
            ).limit(medium_count).all()
            questions.extend(medium_questions)
        
        # Get hard questions
        if hard_count > 0:
            hard_questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty.between(8, 10)
                )
            ).limit(hard_count).all()
            questions.extend(hard_questions)
        
        # Shuffle for variety
        random.shuffle(questions)
        return questions[:count]
    
    def _format_question_for_training(self, question: Question, config: Dict[str, Any]) -> Dict[str, Any]:
        """Format question for training session."""
        adaptive_settings = config.get("adaptive_settings", {})
        
        return {
            "id": str(question.id),
            "content": question.content,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d
            },
            "difficulty": question.difficulty,
            "topic": question.topic.name if question.topic else None,
            "topic_id": str(question.topic_id) if question.topic_id else None,
            "estimated_time_seconds": getattr(question, 'tiempo_estimado', 90),
            "points": question.puntos_xp or 10,
            "hint_availability": adaptive_settings.get("hint_availability", "medium"),
            "time_pressure": adaptive_settings.get("time_pressure", "medium"),
            "adaptive_metadata": {
                "target_accuracy": 0.7,
                "difficulty_adjustment": adaptive_settings.get("difficulty_increment", 1.0),
                "repeat_probability": adaptive_settings.get("question_repeat_probability", 0.1)
            }
        }
    
    def _log_training_session(self, user_id: str, subject_id: str, session_type: str, question_count: int):
        """Log training session generation."""
        self.logger.info(f"Generated {session_type} training session for user {user_id}: {question_count} questions")
    
    def _store_question_performance(self, performance_data: Dict[str, Any]):
        """Store question performance data."""
        # In a real implementation, store in database table
        self.logger.info(f"Recorded performance for question {performance_data['question_id']}")
    
    def _update_adaptive_parameters(self, user_id: str, question: Question, 
                                  performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update adaptive parameters based on question performance."""
        is_correct = performance_data["is_correct"]
        response_time = performance_data["response_time_ms"]
        difficulty = question.difficulty
        
        # Calculate performance metrics
        expected_time = getattr(question, 'tiempo_estimado', 90) * 1000  # Convert to ms
        time_efficiency = expected_time / max(response_time, 1000)  # Avoid division by zero
        
        # Determine if difficulty should be adjusted
        difficulty_adjustment = 0
        if is_correct and time_efficiency > 1.2:
            # Answered correctly and quickly - increase difficulty
            difficulty_adjustment = 0.5
        elif is_correct and time_efficiency > 0.8:
            # Answered correctly at normal pace - slight increase
            difficulty_adjustment = 0.2
        elif not is_correct:
            # Answered incorrectly - decrease difficulty
            difficulty_adjustment = -0.3
        
        # Calculate confidence score
        confidence = 0.5
        if is_correct:
            confidence = min(1.0, 0.7 + (time_efficiency * 0.3))
        else:
            confidence = max(0.1, 0.3 - (difficulty / 20))
        
        return {
            "difficulty_adjustment": difficulty_adjustment,
            "confidence_score": confidence,
            "time_efficiency": time_efficiency,
            "performance_trend": "improving" if is_correct else "needs_practice",
            "recommended_next_difficulty": max(1, min(10, difficulty + difficulty_adjustment))
        }
    
    def _recommend_next_question(self, user_id: str, subject_id: str, 
                               adaptive_update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Recommend next question based on adaptive update."""
        target_difficulty = adaptive_update["recommended_next_difficulty"]
        
        # Find question within target difficulty range
        next_question = self.db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                Question.difficulty.between(target_difficulty - 1, target_difficulty + 1)
            )
        ).first()
        
        if next_question:
            return {
                "id": str(next_question.id),
                "difficulty": next_question.difficulty,
                "topic": next_question.topic.name if next_question.topic else None,
                "reason": f"Adapted to difficulty level {target_difficulty} based on performance"
            }
        
        return None
    
    def _get_session_performance_summary(self, user_id: str) -> Dict[str, Any]:
        """Get current session performance summary."""
        # This would track current session metrics
        return {
            "questions_answered": 0,
            "correct_answers": 0,
            "average_time_seconds": 0,
            "current_streak": 0
        }
    
    def _analyze_recent_performance(self, user_id: str, subject_id: str, 
                                  days_back: int = 14) -> Dict[str, Any]:
        """Analyze recent performance data."""
        start_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get recent diagnostic results
        recent_results = self.db.query(DiagnosticTestResult).filter(
            and_(
                DiagnosticTestResult.user_id == user_id,
                DiagnosticTestResult.subject_id == subject_id,
                DiagnosticTestResult.created_at >= start_date
            )
        ).all()
        
        if not recent_results:
            return {"insufficient_data": True}
        
        # Calculate performance metrics
        total_questions = len(recent_results)
        correct_answers = sum(1 for r in recent_results if r.is_correct)
        accuracy = correct_answers / total_questions
        
        # Calculate average response time
        response_times = [r.response_time for r in recent_results if r.response_time > 0]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Analyze by topic
        topic_performance = {}
        for result in recent_results:
            if result.question and result.question.topic:
                topic_name = result.question.topic.name
                if topic_name not in topic_performance:
                    topic_performance[topic_name] = {"correct": 0, "total": 0}
                
                topic_performance[topic_name]["total"] += 1
                if result.is_correct:
                    topic_performance[topic_name]["correct"] += 1
        
        # Calculate topic accuracies
        for topic in topic_performance:
            total = topic_performance[topic]["total"]
            correct = topic_performance[topic]["correct"]
            topic_performance[topic]["accuracy"] = correct / total if total > 0 else 0
        
        return {
            "total_questions": total_questions,
            "accuracy": accuracy,
            "average_response_time_ms": avg_response_time,
            "topic_performance": topic_performance,
            "performance_trend": self._calculate_performance_trend(recent_results),
            "analysis_period_days": days_back
        }
    
    def _get_immediate_focus_recommendations(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """Get immediate focus recommendations."""
        recommendations = []
        
        if performance_analysis.get("insufficient_data"):
            return ["Completa más ejercicios para generar recomendaciones personalizadas"]
        
        accuracy = performance_analysis.get("accuracy", 0)
        
        if accuracy < 0.5:
            recommendations.append("Enfócate en conceptos básicos antes de avanzar")
            recommendations.append("Usa más tiempo para analizar cada pregunta")
        elif accuracy < 0.7:
            recommendations.append("Practica preguntas de dificultad intermedia")
            recommendations.append("Repasa los temas donde tienes más errores")
        else:
            recommendations.append("¡Excelente trabajo! Considera aumentar la dificultad")
            recommendations.append("Prueba preguntas más desafiantes")
        
        # Topic-specific recommendations
        topic_performance = performance_analysis.get("topic_performance", {})
        weak_topics = [topic for topic, data in topic_performance.items() if data["accuracy"] < 0.6]
        
        if weak_topics:
            recommendations.append(f"Refuerza estos temas: {', '.join(weak_topics[:3])}")
        
        return recommendations
    
    def _get_session_recommendations(self, performance_analysis: Dict[str, Any], 
                                   config: Dict[str, Any]) -> Dict[str, Any]:
        """Get session-specific recommendations."""
        accuracy = performance_analysis.get("accuracy", 0.5)
        
        if accuracy < 0.5:
            return {
                "recommended_session_type": "focus",
                "session_length": 15,
                "difficulty_level": "easy",
                "break_frequency": "every_5_questions"
            }
        elif accuracy < 0.7:
            return {
                "recommended_session_type": "adaptive",
                "session_length": 20,
                "difficulty_level": "mixed",
                "break_frequency": "every_10_questions"
            }
        else:
            return {
                "recommended_session_type": "challenge",
                "session_length": 25,
                "difficulty_level": "hard",
                "break_frequency": "every_15_questions"
            }
    
    def _get_difficulty_recommendations(self, performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get difficulty adjustment recommendations."""
        accuracy = performance_analysis.get("accuracy", 0.5)
        trend = performance_analysis.get("performance_trend", "stable")
        
        if trend == "improving" and accuracy > 0.8:
            return {
                "adjustment": "increase",
                "amount": 1,
                "reason": "Rendimiento excelente y en mejora"
            }
        elif trend == "declining" or accuracy < 0.5:
            return {
                "adjustment": "decrease",
                "amount": 1,
                "reason": "Necesita reforzar conceptos básicos"
            }
        else:
            return {
                "adjustment": "maintain",
                "amount": 0,
                "reason": "Nivel actual es apropiado"
            }
    
    def _get_time_management_recommendations(self, performance_analysis: Dict[str, Any]) -> List[str]:
        """Get time management recommendations."""
        avg_time = performance_analysis.get("average_response_time_ms", 60000)
        
        recommendations = []
        
        if avg_time > 120000:  # More than 2 minutes
            recommendations.append("Practica técnicas de respuesta rápida")
            recommendations.append("Lee las preguntas más eficientemente")
        elif avg_time < 30000:  # Less than 30 seconds
            recommendations.append("Tómate más tiempo para analizar las opciones")
            recommendations.append("Revisa tus respuestas antes de confirmar")
        else:
            recommendations.append("Tu ritmo de respuesta es adecuado")
        
        return recommendations
    
    def _get_topic_priority_recommendations(self, performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get topic priority recommendations."""
        topic_performance = performance_analysis.get("topic_performance", {})
        
        # Sort topics by accuracy (ascending - worst first)
        sorted_topics = sorted(
            topic_performance.items(), 
            key=lambda x: x[1]["accuracy"]
        )
        
        priorities = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": []
        }
        
        for topic, data in sorted_topics:
            accuracy = data["accuracy"]
            if accuracy < 0.5:
                priorities["high_priority"].append(topic)
            elif accuracy < 0.7:
                priorities["medium_priority"].append(topic)
            else:
                priorities["low_priority"].append(topic)
        
        return priorities
    
    def _get_study_schedule_recommendations(self, user_id: str, subject_id: str, 
                                          performance_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Get study schedule recommendations."""
        accuracy = performance_analysis.get("accuracy", 0.5)
        total_questions = performance_analysis.get("total_questions", 0)
        
        if accuracy < 0.5:
            return {
                "frequency": "daily",
                "session_duration": "15-20 minutes",
                "focus": "conceptos básicos",
                "break_schedule": "5 minutos cada 15 minutos"
            }
        elif accuracy < 0.7:
            return {
                "frequency": "5 times per week",
                "session_duration": "20-30 minutes",
                "focus": "práctica mixta",
                "break_schedule": "10 minutos cada 30 minutos"
            }
        else:
            return {
                "frequency": "3-4 times per week",
                "session_duration": "30-45 minutes",
                "focus": "preguntas desafiantes",
                "break_schedule": "15 minutos cada 45 minutos"
            }
    
    def _calculate_recommendation_confidence(self, performance_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for recommendations."""
        if performance_analysis.get("insufficient_data"):
            return 0.3
        
        total_questions = performance_analysis.get("total_questions", 0)
        
        # Base confidence on amount of data
        if total_questions >= 50:
            return 0.9
        elif total_questions >= 20:
            return 0.7
        elif total_questions >= 10:
            return 0.5
        else:
            return 0.3
    
    def _analyze_learning_progress(self, practice_sessions: List, 
                                 diagnostic_results: List) -> Dict[str, Any]:
        """Analyze learning progress from session and diagnostic data."""
        # Implementation would analyze trends in practice sessions and diagnostic results
        return {
            "progress_trend": "improving",
            "learning_velocity": 0.1,
            "consistency_score": 0.8
        }
    
    def _calculate_learning_metrics(self, practice_sessions: List, 
                                  diagnostic_results: List) -> Dict[str, Any]:
        """Calculate comprehensive learning metrics."""
        return {
            "engagement_score": 0.85,
            "retention_rate": 0.75,
            "skill_acquisition_rate": 0.6
        }
    
    def _generate_progress_insights(self, progress_analysis: Dict[str, Any], 
                                  learning_metrics: Dict[str, Any]) -> List[str]:
        """Generate actionable progress insights."""
        insights = []
        
        if learning_metrics.get("engagement_score", 0) > 0.8:
            insights.append("Tu nivel de compromiso con el estudio es excelente")
        
        if progress_analysis.get("progress_trend") == "improving":
            insights.append("Estás progresando de manera constante")
        
        return insights
    
    def _get_recent_performance_summary(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Get recent performance summary for adaptive question selection."""
        # Get last 10 diagnostic results
        recent_results = self.db.query(DiagnosticTestResult).filter(
            and_(
                DiagnosticTestResult.user_id == user_id,
                DiagnosticTestResult.subject_id == subject_id
            )
        ).order_by(DiagnosticTestResult.created_at.desc()).limit(10).all()
        
        if not recent_results:
            return {"accuracy": 0.5, "avg_difficulty": 5}
        
        correct_count = sum(1 for r in recent_results if r.is_correct)
        accuracy = correct_count / len(recent_results)
        
        return {
            "accuracy": accuracy,
            "recent_questions": len(recent_results),
            "avg_difficulty": 5  # Default if no difficulty data
        }
    
    def _calculate_performance_trend(self, results: List) -> str:
        """Calculate performance trend from results."""
        if len(results) < 5:
            return "insufficient_data"
        
        # Split into two halves and compare
        mid_point = len(results) // 2
        first_half_accuracy = sum(1 for r in results[:mid_point] if r.is_correct) / mid_point
        second_half_accuracy = sum(1 for r in results[mid_point:] if r.is_correct) / (len(results) - mid_point)
        
        if second_half_accuracy > first_half_accuracy + 0.1:
            return "improving"
        elif second_half_accuracy < first_half_accuracy - 0.1:
            return "declining"
        else:
            return "stable"