"""
Question Pool Management System
Advanced question pool management with difficulty stratification, adaptive selection,
and intelligent question curation for diagnostic tests
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
import logging
import random
import math
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum

from ..models.question import Question, Topic
from ..models.subject import Subject
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer
from ..models.user import User

logger = logging.getLogger(__name__)

class QuestionSelectionStrategy(Enum):
    RANDOM = "random"
    DIFFICULTY_BALANCED = "difficulty_balanced"
    ADAPTIVE_IRT = "adaptive_irt"
    TOPIC_BALANCED = "topic_balanced"
    PERFORMANCE_BASED = "performance_based"

class DifficultyBand(Enum):
    VERY_EASY = (1, 2)
    EASY = (3, 4)
    MEDIUM = (5, 6)
    HARD = (7, 8)
    VERY_HARD = (9, 10)

@dataclass
class QuestionPoolConfig:
    """Configuration for question pool generation"""
    subject_id: str
    total_questions: int
    difficulty_distribution: Dict[DifficultyBand, float]  # Percentage per band
    topic_distribution: Optional[Dict[str, float]] = None  # Topic coverage
    selection_strategy: QuestionSelectionStrategy = QuestionSelectionStrategy.DIFFICULTY_BALANCED
    avoid_recent_questions: bool = True
    recent_window_days: int = 7
    min_discrimination_index: float = 0.3
    max_usage_frequency: int = 10  # Max times a question can be used
    ensure_topic_coverage: bool = True
    
@dataclass
class QuestionMetrics:
    """Metrics for question quality assessment"""
    question_id: str
    difficulty_level: int
    discrimination_index: float
    success_rate: float
    usage_count: int
    avg_response_time: float
    last_used: Optional[datetime]
    topic_representation: float
    irt_parameters: Dict[str, float]

class QuestionPoolManager:
    """
    Manages question pools with advanced selection algorithms and quality metrics
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logger
        
        # Default configurations
        self.DEFAULT_DIFFICULTY_DISTRIBUTION = {
            DifficultyBand.VERY_EASY: 0.10,  # 10%
            DifficultyBand.EASY: 0.25,       # 25%
            DifficultyBand.MEDIUM: 0.30,     # 30%
            DifficultyBand.HARD: 0.25,       # 25%
            DifficultyBand.VERY_HARD: 0.10   # 10%
        }
        
        # Quality thresholds
        self.MIN_QUESTION_QUALITY_SCORE = 0.5
        self.PREFERRED_RESPONSE_TIME_RANGE = (15000, 120000)  # 15s to 2min
        self.MAX_CONSECUTIVE_SAME_TOPIC = 3
        
        # Adaptive parameters
        self.IRT_THETA_RANGE = (-3.0, 3.0)
        self.ADAPTIVE_WINDOW_SIZE = 5  # Questions to consider for adaptation

    def create_question_pool(self, config: QuestionPoolConfig, 
                           user_id: Optional[str] = None,
                           exclude_questions: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        """
        Create an optimized question pool based on configuration and user history
        """
        exclude_questions = exclude_questions or set()
        
        # Get user performance history if provided
        user_history = None
        if user_id:
            user_history = self._get_user_performance_history(user_id, config.subject_id)
        
        # Get available questions with quality metrics
        available_questions = self._get_available_questions_with_metrics(
            config.subject_id, exclude_questions, config
        )
        
        if len(available_questions) < config.total_questions:
            raise ValueError(f"Not enough quality questions available. Needed: {config.total_questions}, Available: {len(available_questions)}")
        
        # Select questions based on strategy
        selected_questions = self._select_questions_by_strategy(
            available_questions, config, user_history
        )
        
        # Post-process for optimization
        optimized_pool = self._optimize_question_sequence(selected_questions, config)
        
        # Convert to response format
        formatted_pool = self._format_questions_for_test(optimized_pool)
        
        self.logger.info(f"Created question pool with {len(formatted_pool)} questions using {config.selection_strategy.value} strategy")
        return formatted_pool

    def get_adaptive_next_question(self, current_pool: List[Dict[str, Any]], 
                                 answered_questions: List[Dict[str, Any]],
                                 current_theta: float,
                                 config: QuestionPoolConfig) -> Optional[Dict[str, Any]]:
        """
        Get the next optimal question for adaptive testing
        """
        # Remove already answered questions
        answered_ids = {q["question_id"] for q in answered_questions}
        available_questions = [q for q in current_pool if q["id"] not in answered_ids]
        
        if not available_questions:
            return None
        
        # Calculate optimal difficulty for current theta
        optimal_difficulty = self._theta_to_difficulty_level(current_theta)
        
        # Score each question based on information value
        question_scores = []
        for question in available_questions:
            score = self._calculate_information_value(question, current_theta, answered_questions)
            question_scores.append((question, score))
        
        # Sort by information value (highest first)
        question_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Apply constraints (topic diversity, difficulty progression)
        filtered_questions = self._apply_adaptive_constraints(
            question_scores, answered_questions, config
        )
        
        if filtered_questions:
            selected_question = filtered_questions[0][0]
            self.logger.info(f"Selected adaptive question {selected_question['id']} with info value {filtered_questions[0][1]:.3f}")
            return selected_question
        
        return None

    def analyze_question_pool_quality(self, question_pool: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze the quality and characteristics of a question pool
        """
        if not question_pool:
            return {"error": "Empty question pool"}
        
        # Difficulty analysis
        difficulties = [q.get("difficulty", 5) for q in question_pool]
        difficulty_distribution = self._calculate_difficulty_distribution(difficulties)
        
        # Topic analysis
        topics = [q.get("topic", "Unknown") for q in question_pool]
        topic_distribution = self._calculate_topic_distribution(topics)
        
        # Quality metrics
        quality_metrics = self._calculate_pool_quality_metrics(question_pool)
        
        # Sequence analysis
        sequence_analysis = self._analyze_question_sequence(question_pool)
        
        return {
            "pool_size": len(question_pool),
            "difficulty_distribution": difficulty_distribution,
            "topic_distribution": topic_distribution,
            "quality_metrics": quality_metrics,
            "sequence_analysis": sequence_analysis,
            "recommendations": self._generate_pool_recommendations(question_pool)
        }

    def get_question_usage_statistics(self, subject_id: str, 
                                    days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive usage statistics for questions in a subject
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get usage data from diagnostic test answers
        usage_data = self.db.query(
            DiagnosticTestAnswer.question_id,
            func.count(DiagnosticTestAnswer.id).label('usage_count'),
            func.avg(DiagnosticTestAnswer.response_time_ms.cast(db.Float)).label('avg_response_time'),
            func.avg(DiagnosticTestAnswer.is_correct.cast(db.Float)).label('success_rate')
        ).join(
            Question, DiagnosticTestAnswer.question_id == Question.id
        ).filter(
            and_(
                Question.subject_id == subject_id,
                DiagnosticTestAnswer.created_at >= cutoff_date
            )
        ).group_by(DiagnosticTestAnswer.question_id).all()
        
        # Get all questions in subject for comparison
        all_questions = self.db.query(Question).filter(
            Question.subject_id == subject_id
        ).count()
        
        # Calculate statistics
        total_usage = sum(row.usage_count for row in usage_data)
        used_questions = len(usage_data)
        unused_questions = all_questions - used_questions
        
        # Categorize questions by usage
        usage_categories = {
            "high_usage": [],      # Used > 10 times
            "medium_usage": [],    # Used 3-10 times
            "low_usage": [],       # Used 1-2 times
            "unused": unused_questions
        }
        
        quality_issues = []
        
        for row in usage_data:
            if row.usage_count > 10:
                usage_categories["high_usage"].append(str(row.question_id))
            elif row.usage_count >= 3:
                usage_categories["medium_usage"].append(str(row.question_id))
            else:
                usage_categories["low_usage"].append(str(row.question_id))
            
            # Identify quality issues
            if row.success_rate < 0.1 or row.success_rate > 0.95:
                quality_issues.append({
                    "question_id": str(row.question_id),
                    "issue": "Extreme success rate",
                    "success_rate": float(row.success_rate)
                })
            
            if row.avg_response_time > 180000:  # > 3 minutes
                quality_issues.append({
                    "question_id": str(row.question_id),
                    "issue": "Excessive response time",
                    "avg_response_time": float(row.avg_response_time)
                })
        
        return {
            "period_days": days,
            "total_questions": all_questions,
            "total_usage": total_usage,
            "usage_distribution": {
                "used_questions": used_questions,
                "unused_questions": unused_questions,
                "usage_rate": (used_questions / all_questions) * 100 if all_questions > 0 else 0
            },
            "usage_categories": usage_categories,
            "average_metrics": {
                "avg_usage_per_question": total_usage / used_questions if used_questions > 0 else 0,
                "avg_success_rate": sum(row.success_rate for row in usage_data) / len(usage_data) if usage_data else 0,
                "avg_response_time": sum(row.avg_response_time for row in usage_data) / len(usage_data) if usage_data else 0
            },
            "quality_issues": quality_issues,
            "recommendations": self._generate_usage_recommendations(usage_data, all_questions)
        }

    def refresh_question_metrics(self, subject_id: str) -> int:
        """
        Refresh quality metrics for all questions in a subject
        """
        questions = self.db.query(Question).filter(Question.subject_id == subject_id).all()
        updated_count = 0
        
        for question in questions:
            # Calculate new metrics from usage data
            usage_stats = self._calculate_question_usage_stats(question.id)
            
            # Update question power_stats
            if question.power_stats is None:
                question.power_stats = {}
            
            question.power_stats.update({
                "discrimination_index": usage_stats.get("discrimination_index", 0.5),
                "success_rate": usage_stats.get("success_rate", 0.6),
                "avg_response_time": usage_stats.get("avg_response_time", 45000),
                "usage_count": usage_stats.get("usage_count", 0),
                "last_updated": datetime.utcnow().isoformat()
            })
            
            updated_count += 1
        
        self.db.commit()
        self.logger.info(f"Updated metrics for {updated_count} questions in subject {subject_id}")
        return updated_count

    # Private helper methods
    
    def _get_available_questions_with_metrics(self, subject_id: str, 
                                            exclude_questions: Set[str],
                                            config: QuestionPoolConfig) -> List[QuestionMetrics]:
        """
        Get available questions with calculated quality metrics
        """
        # Build base query
        query = self.db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                ~Question.id.in_(exclude_questions) if exclude_questions else True
            )
        )
        
        # Apply quality filters
        if config.min_discrimination_index > 0:
            # This would need to be implemented with proper JSON querying
            # query = query.filter(Question.power_stats['discrimination_index'] >= config.min_discrimination_index)
            pass
        
        questions = query.all()
        
        # Convert to metrics objects
        question_metrics = []
        for question in questions:
            metrics = self._calculate_question_metrics(question)
            
            # Apply quality filters
            if metrics.discrimination_index >= config.min_discrimination_index:
                if not config.max_usage_frequency or metrics.usage_count <= config.max_usage_frequency:
                    # Check recent usage if required
                    if not config.avoid_recent_questions or not self._is_recently_used(question.id, config.recent_window_days):
                        question_metrics.append(metrics)
        
        return question_metrics

    def _calculate_question_metrics(self, question: Question) -> QuestionMetrics:
        """
        Calculate comprehensive metrics for a question
        """
        power_stats = question.power_stats or {}
        
        # Get usage statistics from database
        usage_stats = self._calculate_question_usage_stats(question.id)
        
        return QuestionMetrics(
            question_id=str(question.id),
            difficulty_level=question.difficulty,
            discrimination_index=usage_stats.get("discrimination_index", power_stats.get("discrimination_index", 0.5)),
            success_rate=usage_stats.get("success_rate", power_stats.get("success_rate", 0.6)),
            usage_count=usage_stats.get("usage_count", 0),
            avg_response_time=usage_stats.get("avg_response_time", 45000),
            last_used=usage_stats.get("last_used"),
            topic_representation=self._calculate_topic_representation(question),
            irt_parameters={
                "a": power_stats.get("discrimination", 1.0),
                "b": (question.difficulty - 5.5) / 2.0,  # Map 1-10 to roughly -2.25 to 2.25
                "c": power_stats.get("guessing", 0.25)
            }
        )

    def _calculate_question_usage_stats(self, question_id: str) -> Dict[str, Any]:
        """
        Calculate usage statistics for a specific question
        """
        # Get recent usage data (last 90 days)
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        
        usage_data = self.db.query(
            DiagnosticTestAnswer.is_correct,
            DiagnosticTestAnswer.response_time_ms,
            DiagnosticTestAnswer.created_at
        ).filter(
            and_(
                DiagnosticTestAnswer.question_id == question_id,
                DiagnosticTestAnswer.created_at >= cutoff_date
            )
        ).all()
        
        if not usage_data:
            return {
                "usage_count": 0,
                "success_rate": 0.6,
                "discrimination_index": 0.5,
                "avg_response_time": 45000,
                "last_used": None
            }
        
        # Calculate basic stats
        total_uses = len(usage_data)
        correct_answers = sum(1 for row in usage_data if row.is_correct)
        success_rate = correct_answers / total_uses
        
        # Calculate average response time (exclude extreme values)
        response_times = [row.response_time_ms for row in usage_data if row.response_time_ms]
        if response_times:
            # Remove outliers (< 5s or > 10min)
            filtered_times = [t for t in response_times if 5000 <= t <= 600000]
            avg_response_time = sum(filtered_times) / len(filtered_times) if filtered_times else 45000
        else:
            avg_response_time = 45000
        
        # Calculate discrimination index (simplified)
        # In a full implementation, this would use proper IRT analysis
        if total_uses >= 10:
            discrimination_index = min(1.0, max(0.1, abs(success_rate - 0.5) * 2))
        else:
            discrimination_index = 0.5
        
        # Get last used date
        last_used = max(row.created_at for row in usage_data) if usage_data else None
        
        return {
            "usage_count": total_uses,
            "success_rate": success_rate,
            "discrimination_index": discrimination_index,
            "avg_response_time": avg_response_time,
            "last_used": last_used
        }

    def _select_questions_by_strategy(self, available_questions: List[QuestionMetrics],
                                    config: QuestionPoolConfig,
                                    user_history: Optional[Dict[str, Any]]) -> List[QuestionMetrics]:
        """
        Select questions based on the specified strategy
        """
        if config.selection_strategy == QuestionSelectionStrategy.RANDOM:
            return self._select_random_questions(available_questions, config.total_questions)
        
        elif config.selection_strategy == QuestionSelectionStrategy.DIFFICULTY_BALANCED:
            return self._select_difficulty_balanced_questions(available_questions, config)
        
        elif config.selection_strategy == QuestionSelectionStrategy.ADAPTIVE_IRT:
            return self._select_adaptive_irt_questions(available_questions, config, user_history)
        
        elif config.selection_strategy == QuestionSelectionStrategy.TOPIC_BALANCED:
            return self._select_topic_balanced_questions(available_questions, config)
        
        elif config.selection_strategy == QuestionSelectionStrategy.PERFORMANCE_BASED:
            return self._select_performance_based_questions(available_questions, config, user_history)
        
        else:
            # Default to difficulty balanced
            return self._select_difficulty_balanced_questions(available_questions, config)

    def _select_difficulty_balanced_questions(self, available_questions: List[QuestionMetrics],
                                            config: QuestionPoolConfig) -> List[QuestionMetrics]:
        """
        Select questions with balanced difficulty distribution
        """
        # Group questions by difficulty band
        difficulty_groups = defaultdict(list)
        for question in available_questions:
            band = self._get_difficulty_band(question.difficulty_level)
            difficulty_groups[band].append(question)
        
        selected_questions = []
        
        # Select from each difficulty band according to distribution
        for band, target_percentage in config.difficulty_distribution.items():
            target_count = int(config.total_questions * target_percentage)
            available_in_band = difficulty_groups.get(band, [])
            
            if available_in_band:
                # Sort by quality metrics and select best ones
                available_in_band.sort(key=lambda q: (
                    q.discrimination_index * 0.4 +
                    (1 - abs(q.success_rate - 0.6)) * 0.3 +  # Prefer ~60% success rate
                    (1 / (q.usage_count + 1)) * 0.2 +  # Prefer less used questions
                    random.random() * 0.1  # Add some randomness
                ), reverse=True)
                
                selected_count = min(target_count, len(available_in_band))
                selected_questions.extend(available_in_band[:selected_count])
        
        # If we need more questions, fill from best remaining
        if len(selected_questions) < config.total_questions:
            selected_ids = {q.question_id for q in selected_questions}
            remaining = [q for q in available_questions if q.question_id not in selected_ids]
            
            remaining.sort(key=lambda q: q.discrimination_index, reverse=True)
            needed = config.total_questions - len(selected_questions)
            selected_questions.extend(remaining[:needed])
        
        return selected_questions[:config.total_questions]

    def _select_adaptive_irt_questions(self, available_questions: List[QuestionMetrics],
                                     config: QuestionPoolConfig,
                                     user_history: Optional[Dict[str, Any]]) -> List[QuestionMetrics]:
        """
        Select questions optimized for adaptive testing using IRT principles
        """
        # Estimate initial user ability
        initial_theta = 0.0
        if user_history:
            initial_theta = user_history.get("estimated_theta", 0.0)
        
        # Calculate information value for each question at initial theta
        question_info = []
        for question in available_questions:
            info_value = self._calculate_fisher_information(question, initial_theta)
            question_info.append((question, info_value))
        
        # Sort by information value
        question_info.sort(key=lambda x: x[1], reverse=True)
        
        # Select top questions ensuring some diversity
        selected_questions = []
        used_topics = set()
        
        for question, info_value in question_info:
            if len(selected_questions) >= config.total_questions:
                break
            
            # Ensure topic diversity if required
            if config.ensure_topic_coverage:
                question_obj = self.db.query(Question).filter(Question.id == question.question_id).first()
                topic_id = question_obj.topic_id if question_obj else None
                
                if topic_id in used_topics and len(used_topics) < 5:  # Allow repeats after 5 different topics
                    continue
                
                if topic_id:
                    used_topics.add(topic_id)
            
            selected_questions.append(question)
        
        return selected_questions

    def _calculate_fisher_information(self, question: QuestionMetrics, theta: float) -> float:
        """
        Calculate Fisher information for a question at given ability level
        """
        a = question.irt_parameters["a"]  # discrimination
        b = question.irt_parameters["b"]  # difficulty
        c = question.irt_parameters["c"]  # guessing
        
        # Calculate probability of correct response (3PL model)
        exp_term = math.exp(-a * (theta - b))
        p = c + (1 - c) / (1 + exp_term)
        
        # Fisher information formula for 3PL
        q = 1 - p
        dp_dtheta = a * (1 - c) * exp_term / ((1 + exp_term) ** 2)
        
        if p > 0 and q > 0:
            information = (dp_dtheta ** 2) / (p * q)
        else:
            information = 0
        
        return information

    def _optimize_question_sequence(self, questions: List[QuestionMetrics], 
                                  config: QuestionPoolConfig) -> List[QuestionMetrics]:
        """
        Optimize the sequence of questions for better user experience
        """
        if len(questions) <= 1:
            return questions
        
        optimized = []
        remaining = questions.copy()
        
        # Start with medium difficulty question
        medium_questions = [q for q in remaining if 4 <= q.difficulty_level <= 6]
        if medium_questions:
            start_question = random.choice(medium_questions)
            optimized.append(start_question)
            remaining.remove(start_question)
        
        # Alternate difficulty levels to avoid frustration
        while remaining:
            last_difficulty = optimized[-1].difficulty_level if optimized else 5
            
            # Try to pick a question with different difficulty
            different_difficulty = [q for q in remaining if abs(q.difficulty_level - last_difficulty) >= 2]
            
            if different_difficulty:
                next_question = max(different_difficulty, key=lambda q: q.discrimination_index)
            else:
                next_question = max(remaining, key=lambda q: q.discrimination_index)
            
            optimized.append(next_question)
            remaining.remove(next_question)
        
        return optimized

    def _format_questions_for_test(self, question_metrics: List[QuestionMetrics]) -> List[Dict[str, Any]]:
        """
        Format question metrics into test-ready format
        """
        formatted_questions = []
        
        for metrics in question_metrics:
            # Get full question data from database
            question = self.db.query(Question).filter(Question.id == metrics.question_id).first()
            if not question:
                continue
            
            # Build options from individual fields
            options = []
            for letra in ['a', 'b', 'c', 'd']:
                texto = getattr(question, f'opcion_{letra}_texto')
                if texto:
                    options.append(texto)
                else:
                    options.append(f"Opción {letra.upper()}")
            
            formatted_question = {
                "id": str(question.id),
                "question_text": question.pregunta_texto or question.question_text or "Pregunta sin texto",
                "options": options,
                "subject": question.subject.name if question.subject else "General",
                "topic": question.topic.name if question.topic else "General",
                "difficulty": question.difficulty,
                "hint": question.hint,
                "image_url": question.pregunta_imagen,
                "options_images": {},
                "correct_answer": question.respuesta_correcta or question.correct_answer,
                "quality_metrics": {
                    "discrimination_index": metrics.discrimination_index,
                    "success_rate": metrics.success_rate,
                    "avg_response_time": metrics.avg_response_time,
                    "usage_count": metrics.usage_count
                },
                "irt_parameters": metrics.irt_parameters
            }
            
            formatted_questions.append(formatted_question)
        
        return formatted_questions

    def _get_difficulty_band(self, difficulty: int) -> DifficultyBand:
        """
        Map difficulty level to difficulty band
        """
        for band in DifficultyBand:
            min_diff, max_diff = band.value
            if min_diff <= difficulty <= max_diff:
                return band
        return DifficultyBand.MEDIUM

    def _theta_to_difficulty_level(self, theta: float) -> int:
        """
        Convert theta to difficulty level (1-10)
        """
        # Map theta (-3 to 3) to difficulty (1 to 10)
        normalized_theta = max(-3, min(3, theta))
        difficulty = int((normalized_theta + 3) * 9 / 6) + 1
        return max(1, min(10, difficulty))

    def _calculate_information_value(self, question: Dict[str, Any], 
                                   current_theta: float,
                                   answered_questions: List[Dict[str, Any]]) -> float:
        """
        Calculate information value of a question for current ability estimate
        """
        # Get IRT parameters
        irt_params = question.get("irt_parameters", {"a": 1.0, "b": 0.0, "c": 0.25})
        
        # Calculate Fisher information
        info = self._calculate_fisher_information_from_params(
            irt_params["a"], irt_params["b"], irt_params["c"], current_theta
        )
        
        # Adjust for question quality
        quality_metrics = question.get("quality_metrics", {})
        discrimination_bonus = quality_metrics.get("discrimination_index", 0.5)
        usage_penalty = min(0.5, quality_metrics.get("usage_count", 0) / 20)
        
        adjusted_info = info * discrimination_bonus * (1 - usage_penalty)
        
        return adjusted_info

    def _calculate_fisher_information_from_params(self, a: float, b: float, 
                                                c: float, theta: float) -> float:
        """
        Calculate Fisher information from IRT parameters
        """
        exp_term = math.exp(-a * (theta - b))
        p = c + (1 - c) / (1 + exp_term)
        q = 1 - p
        dp_dtheta = a * (1 - c) * exp_term / ((1 + exp_term) ** 2)
        
        if p > 0 and q > 0:
            return (dp_dtheta ** 2) / (p * q)
        else:
            return 0

    def _apply_adaptive_constraints(self, question_scores: List[Tuple[Dict[str, Any], float]],
                                  answered_questions: List[Dict[str, Any]],
                                  config: QuestionPoolConfig) -> List[Tuple[Dict[str, Any], float]]:
        """
        Apply constraints for adaptive question selection
        """
        if not answered_questions:
            return question_scores[:5]  # Return top 5 for first question
        
        # Get recent topic distribution
        recent_topics = [q.get("topic", "Unknown") for q in answered_questions[-self.MAX_CONSECUTIVE_SAME_TOPIC:]]
        last_topic = recent_topics[-1] if recent_topics else None
        
        # Filter out questions from over-represented topics
        filtered = []
        for question, score in question_scores:
            question_topic = question.get("topic", "Unknown")
            
            # Avoid too many consecutive questions from same topic
            if recent_topics.count(question_topic) >= self.MAX_CONSECUTIVE_SAME_TOPIC:
                continue
            
            filtered.append((question, score))
        
        return filtered[:10]  # Return top 10 candidates

    def _get_user_performance_history(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """
        Get user's performance history for the subject
        """
        # Get recent diagnostic tests
        recent_tests = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.status == "completed"
            )
        ).order_by(desc(DiagnosticTest.completed_at)).limit(5).all()
        
        if not recent_tests:
            return {"estimated_theta": 0.0, "performance_trend": "unknown"}
        
        # Calculate estimated theta from recent performance
        scores = [test.score_percentage for test in recent_tests]
        avg_score = sum(scores) / len(scores)
        estimated_theta = (avg_score - 50) / 25  # Rough conversion
        
        # Determine performance trend
        if len(scores) >= 3:
            recent_avg = sum(scores[:2]) / 2
            older_avg = sum(scores[2:]) / len(scores[2:])
            if recent_avg > older_avg + 5:
                trend = "improving"
            elif recent_avg < older_avg - 5:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"
        
        return {
            "estimated_theta": max(-3, min(3, estimated_theta)),
            "performance_trend": trend,
            "recent_scores": scores,
            "test_count": len(recent_tests)
        }

    # Additional helper methods for statistics and analysis...
    
    def _calculate_difficulty_distribution(self, difficulties: List[int]) -> Dict[str, float]:
        """Calculate difficulty distribution percentages"""
        if not difficulties:
            return {}
        
        total = len(difficulties)
        distribution = {}
        
        for band in DifficultyBand:
            min_diff, max_diff = band.value
            count = sum(1 for d in difficulties if min_diff <= d <= max_diff)
            distribution[band.name.lower()] = (count / total) * 100
        
        return distribution

    def _calculate_topic_distribution(self, topics: List[str]) -> Dict[str, float]:
        """Calculate topic distribution percentages"""
        if not topics:
            return {}
        
        total = len(topics)
        topic_counts = defaultdict(int)
        
        for topic in topics:
            topic_counts[topic] += 1
        
        return {topic: (count / total) * 100 for topic, count in topic_counts.items()}

    def _is_recently_used(self, question_id: str, days: int) -> bool:
        """Check if question was used recently"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        recent_usage = self.db.query(DiagnosticTestAnswer).filter(
            and_(
                DiagnosticTestAnswer.question_id == question_id,
                DiagnosticTestAnswer.created_at >= cutoff_date
            )
        ).first()
        
        return recent_usage is not None

    def _calculate_topic_representation(self, question: Question) -> float:
        """Calculate how well this question represents its topic"""
        if not question.topic_id:
            return 0.5
        
        # Count questions in the same topic
        topic_question_count = self.db.query(Question).filter(
            Question.topic_id == question.topic_id
        ).count()
        
        # Higher representation for topics with fewer questions
        return min(1.0, 10.0 / max(1, topic_question_count))

    # Placeholder methods for additional functionality...
    
    def _select_random_questions(self, questions: List[QuestionMetrics], count: int) -> List[QuestionMetrics]:
        """Select random questions"""
        return random.sample(questions, min(count, len(questions)))

    def _select_topic_balanced_questions(self, questions: List[QuestionMetrics], 
                                       config: QuestionPoolConfig) -> List[QuestionMetrics]:
        """Select questions with balanced topic distribution"""
        # Implementation would balance across topics
        return self._select_difficulty_balanced_questions(questions, config)

    def _select_performance_based_questions(self, questions: List[QuestionMetrics],
                                          config: QuestionPoolConfig,
                                          user_history: Optional[Dict[str, Any]]) -> List[QuestionMetrics]:
        """Select questions based on user performance history"""
        # Implementation would adapt to user's weak areas
        return self._select_difficulty_balanced_questions(questions, config)

    def _calculate_pool_quality_metrics(self, pool: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate quality metrics for the pool"""
        if not pool:
            return {}
        
        metrics = [q.get("quality_metrics", {}) for q in pool]
        
        return {
            "avg_discrimination": sum(m.get("discrimination_index", 0.5) for m in metrics) / len(metrics),
            "avg_success_rate": sum(m.get("success_rate", 0.6) for m in metrics) / len(metrics),
            "avg_usage_count": sum(m.get("usage_count", 0) for m in metrics) / len(metrics)
        }

    def _analyze_question_sequence(self, pool: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the sequence of questions"""
        if not pool:
            return {}
        
        difficulties = [q.get("difficulty", 5) for q in pool]
        topics = [q.get("topic", "Unknown") for q in pool]
        
        # Calculate difficulty variance
        avg_difficulty = sum(difficulties) / len(difficulties)
        difficulty_variance = sum((d - avg_difficulty) ** 2 for d in difficulties) / len(difficulties)
        
        # Calculate topic transitions
        topic_changes = sum(1 for i in range(1, len(topics)) if topics[i] != topics[i-1])
        
        return {
            "difficulty_variance": difficulty_variance,
            "topic_changes": topic_changes,
            "avg_difficulty": avg_difficulty,
            "sequence_score": self._calculate_sequence_score(difficulties, topics)
        }

    def _calculate_sequence_score(self, difficulties: List[int], topics: List[str]) -> float:
        """Calculate a score for question sequence quality"""
        if len(difficulties) <= 1:
            return 1.0
        
        score = 1.0
        
        # Penalize extreme difficulty jumps
        for i in range(1, len(difficulties)):
            diff_jump = abs(difficulties[i] - difficulties[i-1])
            if diff_jump > 4:
                score -= 0.1
        
        # Reward topic diversity
        unique_topics = len(set(topics))
        topic_diversity = unique_topics / len(topics) if topics else 0
        score += topic_diversity * 0.2
        
        return max(0.0, min(1.0, score))

    def _generate_pool_recommendations(self, pool: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for improving the pool"""
        recommendations = []
        
        if not pool:
            return ["No questions in pool"]
        
        # Analyze quality metrics
        avg_discrimination = sum(q.get("quality_metrics", {}).get("discrimination_index", 0.5) for q in pool) / len(pool)
        if avg_discrimination < 0.6:
            recommendations.append("Consider including questions with higher discrimination indices")
        
        # Analyze difficulty distribution
        difficulties = [q.get("difficulty", 5) for q in pool]
        if max(difficulties) - min(difficulties) < 5:
            recommendations.append("Consider including questions with wider difficulty range")
        
        # Analyze topic diversity
        topics = set(q.get("topic", "Unknown") for q in pool)
        if len(topics) < 3:
            recommendations.append("Consider including questions from more diverse topics")
        
        return recommendations if recommendations else ["Pool quality looks good"]

    def _generate_usage_recommendations(self, usage_data: List, total_questions: int) -> List[str]:
        """Generate recommendations based on usage statistics"""
        recommendations = []
        
        if not usage_data:
            return ["No usage data available"]
        
        # Check usage distribution
        high_usage_count = sum(1 for row in usage_data if row.usage_count > 10)
        if high_usage_count > len(usage_data) * 0.3:
            recommendations.append("Too many questions are overused - consider rotating question pool")
        
        unused_count = total_questions - len(usage_data)
        if unused_count > total_questions * 0.5:
            recommendations.append("Many questions are unused - review question quality or selection algorithm")
        
        # Check quality issues
        quality_issues = sum(1 for row in usage_data if row.success_rate < 0.1 or row.success_rate > 0.95)
        if quality_issues > 0:
            recommendations.append(f"{quality_issues} questions have extreme success rates - review for quality")
        
        return recommendations if recommendations else ["Usage patterns look healthy"]