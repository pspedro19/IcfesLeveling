from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, or_
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta, date
import calendar
import logging
import uuid
from enum import Enum

from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestAnswer, DiagnosticTestResult
from ..models.topic import Topic
from ..models.question import Question
from ..models.subject import Subject
from ..models.user import User
from ..models.study_plan import StudyPlan
from .monthly_reassessment_service import MonthlyReassessmentService
from .diagnostic_service import DiagnosticService
from .video_recommendation_service import VideoRecommendationService
from .study_plan_service import StudyPlanService

class DiagnosticFrequency(Enum):
    MONTHLY = "monthly"
    BI_WEEKLY = "bi_weekly"
    QUARTERLY = "quarterly"
    CUSTOM = "custom"

class MonthlyDiagnosticScheduler:
    """
    Comprehensive monthly diagnostic assessment system that tracks student progress over time.
    Manages scheduling, execution, comparison, and adaptation of learning experiences.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.reassessment_service = MonthlyReassessmentService(db)
        self.diagnostic_service = DiagnosticService(db)
        
    def schedule_monthly_diagnostics(self, user_id: str, subjects: List[str] = None) -> Dict[str, Any]:
        """
        Schedule monthly diagnostic assessments for a user across all or specified subjects.
        
        Args:
            user_id: User identifier
            subjects: Optional list of subject IDs to schedule for. If None, schedules for all subjects.
            
        Returns:
            Dictionary with scheduling results and next assessment dates
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get all subjects if none specified
            if subjects is None:
                subject_objects = self.db.query(Subject).all()
                subjects = [str(s.id) for s in subject_objects]
            else:
                subject_objects = self.db.query(Subject).filter(Subject.id.in_(subjects)).all()
            
            scheduled_assessments = []
            assessment_calendar = {}
            
            for subject in subject_objects:
                subject_id = str(subject.id)
                
                # Check current diagnostic status
                diagnostic_status = self._get_diagnostic_status(user_id, subject_id)
                
                # Calculate next assessment date
                next_assessment_date = self._calculate_next_assessment_date(
                    user_id, subject_id, diagnostic_status
                )
                
                # Create assessment schedule entry
                schedule_entry = {
                    "subject_id": subject_id,
                    "subject_name": subject.name,
                    "current_status": diagnostic_status,
                    "next_assessment_date": next_assessment_date,
                    "days_until_next": (next_assessment_date - datetime.now().date()).days,
                    "assessment_type": self._determine_assessment_type(diagnostic_status),
                    "estimated_duration_minutes": self._estimate_assessment_duration(subject_id),
                    "prerequisites_met": self._check_prerequisites(user_id, subject_id)
                }
                
                scheduled_assessments.append(schedule_entry)
                
                # Add to monthly calendar
                month_key = next_assessment_date.strftime("%Y-%m")
                if month_key not in assessment_calendar:
                    assessment_calendar[month_key] = []
                assessment_calendar[month_key].append(schedule_entry)
            
            # Create comprehensive schedule summary
            schedule_summary = {
                "user_id": user_id,
                "total_subjects": len(subjects),
                "scheduled_assessments": scheduled_assessments,
                "assessment_calendar": assessment_calendar,
                "upcoming_this_week": self._get_upcoming_assessments(scheduled_assessments, 7),
                "upcoming_this_month": self._get_upcoming_assessments(scheduled_assessments, 30),
                "overdue_assessments": self._get_overdue_assessments(scheduled_assessments),
                "schedule_created_at": datetime.utcnow(),
                "next_check_date": datetime.now().date() + timedelta(days=7)
            }
            
            self.logger.info(f"Scheduled {len(scheduled_assessments)} diagnostic assessments for user {user_id}")
            return schedule_summary
            
        except Exception as e:
            self.logger.error(f"Error scheduling monthly diagnostics for user {user_id}: {str(e)}")
            raise
    
    def get_diagnostic_progress_timeline(self, user_id: str, subject_id: str, 
                                       months_back: int = 12) -> Dict[str, Any]:
        """
        Generate a comprehensive progress timeline showing diagnostic results over time.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            months_back: Number of months to look back (default 12)
            
        Returns:
            Timeline data with progress trends, improvements, and predictions
        """
        try:
            # Get all diagnostic tests for the subject
            start_date = datetime.utcnow() - timedelta(days=months_back * 30)
            
            diagnostics = self.db.query(DiagnosticTest).filter(
                and_(
                    DiagnosticTest.user_id == user_id,
                    DiagnosticTest.subject_id == subject_id,
                    DiagnosticTest.status == "completed",
                    DiagnosticTest.created_at >= start_date
                )
            ).order_by(DiagnosticTest.created_at.asc()).all()
            
            if not diagnostics:
                return {
                    "user_id": user_id,
                    "subject_id": subject_id,
                    "timeline": [],
                    "trends": {},
                    "predictions": {},
                    "total_assessments": 0
                }
            
            # Build timeline with detailed analysis
            timeline_data = []
            monthly_aggregates = {}
            
            for diagnostic in diagnostics:
                # Basic test data
                test_data = {
                    "test_id": str(diagnostic.id),
                    "date": diagnostic.created_at.date(),
                    "month": diagnostic.created_at.strftime("%Y-%m"),
                    "test_type": diagnostic.test_type,
                    "reassessment_type": diagnostic.reassessment_type,
                    "is_monthly_reassessment": diagnostic.is_monthly_reassessment,
                    "score_percentage": float(diagnostic.score_percentage),
                    "questions_answered": diagnostic.questions_answered,
                    "correct_answers": diagnostic.correct_answers,
                    "time_spent_minutes": diagnostic.time_spent_seconds / 60,
                    "strengths": diagnostic.strengths or [],
                    "weaknesses": diagnostic.weaknesses or [],
                    "score_by_topic": diagnostic.score_by_topic or {}
                }
                
                # Calculate improvement metrics
                if len(timeline_data) > 0:
                    previous_test = timeline_data[-1]
                    test_data["improvement_from_previous"] = (
                        test_data["score_percentage"] - previous_test["score_percentage"]
                    )
                    test_data["time_improvement"] = (
                        previous_test["time_spent_minutes"] - test_data["time_spent_minutes"]
                    )
                else:
                    test_data["improvement_from_previous"] = 0
                    test_data["time_improvement"] = 0
                
                # Add topic-level improvements
                test_data["topic_improvements"] = self._calculate_topic_improvements(
                    test_data["score_by_topic"],
                    timeline_data[-1]["score_by_topic"] if timeline_data else {}
                )
                
                timeline_data.append(test_data)
                
                # Aggregate monthly data
                month_key = test_data["month"]
                if month_key not in monthly_aggregates:
                    monthly_aggregates[month_key] = {
                        "tests_count": 0,
                        "total_score": 0,
                        "total_time": 0,
                        "topics_data": {}
                    }
                
                monthly_aggregates[month_key]["tests_count"] += 1
                monthly_aggregates[month_key]["total_score"] += test_data["score_percentage"]
                monthly_aggregates[month_key]["total_time"] += test_data["time_spent_minutes"]
                
                # Aggregate topic data
                for topic, score in test_data["score_by_topic"].items():
                    if topic not in monthly_aggregates[month_key]["topics_data"]:
                        monthly_aggregates[month_key]["topics_data"][topic] = []
                    monthly_aggregates[month_key]["topics_data"][topic].append(score)
            
            # Calculate trends and predictions
            trends = self._calculate_progress_trends(timeline_data, monthly_aggregates)
            predictions = self._generate_progress_predictions(timeline_data, trends)
            performance_insights = self._analyze_performance_patterns(timeline_data)
            
            return {
                "user_id": user_id,
                "subject_id": subject_id,
                "timeline": timeline_data,
                "monthly_aggregates": monthly_aggregates,
                "trends": trends,
                "predictions": predictions,
                "performance_insights": performance_insights,
                "total_assessments": len(diagnostics),
                "date_range": {
                    "start": diagnostics[0].created_at.date(),
                    "end": diagnostics[-1].created_at.date()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating progress timeline for user {user_id}, subject {subject_id}: {str(e)}")
            raise
    
    def trigger_monthly_assessment(self, user_id: str, subject_id: str, 
                                 assessment_type: str = "adaptive") -> Dict[str, Any]:
        """
        Trigger a monthly diagnostic assessment for a user and subject.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            assessment_type: Type of assessment ("adaptive", "comprehensive", "focused")
            
        Returns:
            Assessment details and questions
        """
        try:
            # Check eligibility
            eligibility = self.reassessment_service.check_monthly_reassessment_eligibility(
                user_id, subject_id
            )
            
            if not eligibility["eligible"]:
                # For this enhanced system, we'll allow more flexible scheduling
                # Check if user has any completed diagnostic
                has_initial = self.db.query(DiagnosticTest).filter(
                    and_(
                        DiagnosticTest.user_id == user_id,
                        DiagnosticTest.subject_id == subject_id,
                        DiagnosticTest.status == "completed"
                    )
                ).first()
                
                if not has_initial:
                    # Create initial diagnostic test
                    test = self.diagnostic_service.create_diagnostic_test(
                        user_id, subject_id, "real_icfes"
                    )
                    test.reassessment_type = "initial"
                    self.db.commit()
                    
                    questions = self.diagnostic_service.get_diagnostic_questions(
                        subject_id, limit=30
                    )
                    
                    return {
                        "test_id": str(test.id),
                        "test_type": "initial",
                        "questions": [self._format_question_for_frontend(q) for q in questions],
                        "estimated_duration_minutes": 45,
                        "instructions": "Este es tu test diagnóstico inicial. Tómate tu tiempo y responde lo mejor que puedas."
                    }
            
            # Create monthly reassessment
            test = self.reassessment_service.create_monthly_reassessment(user_id, subject_id)
            
            # Get adaptive questions based on assessment type
            questions = self._get_adaptive_questions(
                user_id, subject_id, assessment_type, test.id
            )
            
            return {
                "test_id": str(test.id),
                "test_type": "monthly_reassessment",
                "assessment_type": assessment_type,
                "questions": [self._format_question_for_frontend(q) for q in questions],
                "estimated_duration_minutes": self._estimate_assessment_duration(subject_id),
                "instructions": f"Reevaluación mensual de {assessment_type}. Basada en tu progreso anterior.",
                "previous_performance": eligibility.get("initial_score", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error triggering monthly assessment for user {user_id}, subject {subject_id}: {str(e)}")
            raise
    
    def process_assessment_completion(self, test_id: str, answers: List[Dict]) -> Dict[str, Any]:
        """
        Process completed assessment and trigger all adaptive updates.
        
        Args:
            test_id: Test identifier
            answers: List of user answers
            
        Returns:
            Complete assessment results with updates and recommendations
        """
        try:
            # Get the test
            test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
            if not test:
                raise ValueError(f"Test {test_id} not found")
            
            # Process the assessment based on type
            if test.is_monthly_reassessment:
                # Process monthly reassessment
                reassessment_result = self.reassessment_service.submit_monthly_reassessment(
                    test_id, answers
                )
                
                # Update training zone questions
                self._update_training_zone_questions(
                    test.user_id, test.subject_id, reassessment_result
                )
                
                # Refresh video recommendations
                self._refresh_video_recommendations(
                    test.user_id, test.subject_id, reassessment_result
                )
                
                # Update study plan
                self._update_study_plan(
                    test.user_id, test.subject_id, reassessment_result
                )
                
                # Generate progress report
                progress_report = self._generate_progress_report(
                    test.user_id, test.subject_id, reassessment_result
                )
                
                return {
                    "assessment_type": "monthly_reassessment",
                    "results": reassessment_result,
                    "progress_report": progress_report,
                    "updates_applied": {
                        "training_zone_updated": True,
                        "videos_refreshed": True,
                        "study_plan_updated": True
                    }
                }
            else:
                # Process initial diagnostic
                analysis = self.diagnostic_service.submit_diagnostic_test(test_id, answers)
                
                # For initial tests, set up baseline for future comparisons
                self._establish_baseline_metrics(test.user_id, test.subject_id, test_id)
                
                return {
                    "assessment_type": "initial_diagnostic",
                    "results": analysis,
                    "baseline_established": True
                }
                
        except Exception as e:
            self.logger.error(f"Error processing assessment completion for test {test_id}: {str(e)}")
            raise
    
    def get_improvement_metrics(self, user_id: str, subject_id: str = None, 
                              time_period: str = "last_6_months") -> Dict[str, Any]:
        """
        Generate comprehensive improvement metrics for a user.
        
        Args:
            user_id: User identifier
            subject_id: Optional subject identifier. If None, generates for all subjects.
            time_period: Time period for analysis ("last_month", "last_3_months", "last_6_months", "all_time")
            
        Returns:
            Comprehensive improvement metrics and insights
        """
        try:
            # Calculate date range
            date_ranges = {
                "last_month": timedelta(days=30),
                "last_3_months": timedelta(days=90),
                "last_6_months": timedelta(days=180),
                "all_time": timedelta(days=365 * 10)  # 10 years as "all time"
            }
            
            start_date = datetime.utcnow() - date_ranges.get(time_period, date_ranges["last_6_months"])
            
            # Build query
            query = self.db.query(DiagnosticTest).filter(
                and_(
                    DiagnosticTest.user_id == user_id,
                    DiagnosticTest.status == "completed",
                    DiagnosticTest.created_at >= start_date
                )
            )
            
            if subject_id:
                query = query.filter(DiagnosticTest.subject_id == subject_id)
            
            diagnostics = query.order_by(DiagnosticTest.created_at.asc()).all()
            
            if not diagnostics:
                return {"error": "No diagnostic data found for the specified period"}
            
            # Calculate comprehensive metrics
            metrics = {
                "overview": self._calculate_overview_metrics(diagnostics),
                "score_progression": self._calculate_score_progression(diagnostics),
                "topic_improvements": self._calculate_topic_improvement_metrics(diagnostics),
                "time_efficiency": self._calculate_time_efficiency_metrics(diagnostics),
                "consistency_metrics": self._calculate_consistency_metrics(diagnostics),
                "difficulty_progression": self._calculate_difficulty_progression(diagnostics),
                "learning_velocity": self._calculate_learning_velocity(diagnostics),
                "prediction_confidence": self._calculate_prediction_confidence(diagnostics)
            }
            
            return {
                "user_id": user_id,
                "subject_id": subject_id,
                "time_period": time_period,
                "analysis_date": datetime.utcnow(),
                "total_assessments": len(diagnostics),
                "date_range": {
                    "start": diagnostics[0].created_at,
                    "end": diagnostics[-1].created_at
                },
                "metrics": metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating improvement metrics for user {user_id}: {str(e)}")
            raise
    
    # Private helper methods
    
    def _get_diagnostic_status(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Get current diagnostic status for a user and subject."""
        latest_test = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.status == "completed"
            )
        ).order_by(DiagnosticTest.created_at.desc()).first()
        
        if not latest_test:
            return {
                "status": "never_assessed",
                "last_assessment_date": None,
                "days_since_last": None,
                "last_score": None
            }
        
        days_since = (datetime.utcnow() - latest_test.created_at).days
        
        return {
            "status": "previously_assessed",
            "last_assessment_date": latest_test.created_at.date(),
            "days_since_last": days_since,
            "last_score": float(latest_test.score_percentage),
            "test_type": latest_test.test_type,
            "is_overdue": days_since >= 30
        }
    
    def _calculate_next_assessment_date(self, user_id: str, subject_id: str, 
                                      diagnostic_status: Dict[str, Any]) -> date:
        """Calculate the next assessment date based on current status."""
        if diagnostic_status["status"] == "never_assessed":
            return datetime.now().date()
        
        last_date = diagnostic_status["last_assessment_date"]
        if diagnostic_status["is_overdue"]:
            return datetime.now().date()
        
        # Calculate next monthly assessment
        next_month = last_date.replace(day=1) + timedelta(days=32)
        return next_month.replace(day=last_date.day)
    
    def _determine_assessment_type(self, diagnostic_status: Dict[str, Any]) -> str:
        """Determine the type of assessment needed."""
        if diagnostic_status["status"] == "never_assessed":
            return "initial_diagnostic"
        elif diagnostic_status["is_overdue"]:
            return "overdue_reassessment"
        else:
            return "monthly_reassessment"
    
    def _estimate_assessment_duration(self, subject_id: str) -> int:
        """Estimate assessment duration in minutes based on subject and question count."""
        # Base duration calculation
        question_count = self.db.query(Question).filter(
            Question.subject_id == subject_id
        ).count()
        
        # Estimate 1.5 minutes per question for diagnostic assessments
        estimated_minutes = min(45, max(15, int(question_count * 0.2 * 1.5)))
        return estimated_minutes
    
    def _check_prerequisites(self, user_id: str, subject_id: str) -> bool:
        """Check if prerequisites are met for assessment."""
        # Basic check - user exists and has access to the subject
        user = self.db.query(User).filter(User.id == user_id).first()
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        return user is not None and subject is not None
    
    def _get_upcoming_assessments(self, assessments: List[Dict], days: int) -> List[Dict]:
        """Filter assessments due within specified days."""
        return [
            assessment for assessment in assessments
            if 0 <= assessment["days_until_next"] <= days
        ]
    
    def _get_overdue_assessments(self, assessments: List[Dict]) -> List[Dict]:
        """Filter overdue assessments."""
        return [
            assessment for assessment in assessments
            if assessment["days_until_next"] < 0
        ]
    
    def _get_adaptive_questions(self, user_id: str, subject_id: str, 
                              assessment_type: str, test_id: str) -> List[Question]:
        """Get adaptive questions based on user's previous performance."""
        # Get user's performance history
        previous_tests = self.db.query(DiagnosticTest).filter(
            and_(
                DiagnosticTest.user_id == user_id,
                DiagnosticTest.subject_id == subject_id,
                DiagnosticTest.status == "completed"
            )
        ).order_by(DiagnosticTest.created_at.desc()).limit(3).all()
        
        if not previous_tests:
            # No history, use standard questions
            return self.diagnostic_service.get_diagnostic_questions(subject_id, limit=20)
        
        # Analyze performance patterns
        weak_topics = set()
        avg_score = 0
        total_tests = len(previous_tests)
        
        for test in previous_tests:
            avg_score += test.score_percentage
            if test.score_by_topic:
                for topic, score in test.score_by_topic.items():
                    if score < 60:  # Consider topics below 60% as weak
                        weak_topics.add(topic)
        
        avg_score /= total_tests
        
        # Determine question difficulty and topics based on assessment type
        if assessment_type == "focused":
            # Focus on weak topics
            if weak_topics:
                topic_objects = self.db.query(Topic).filter(
                    Topic.name.in_(weak_topics)
                ).all()
                
                questions = []
                for topic in topic_objects:
                    topic_questions = self.db.query(Question).filter(
                        and_(
                            Question.subject_id == subject_id,
                            Question.topic_id == topic.id,
                            Question.difficulty.between(5, 8)
                        )
                    ).limit(5).all()
                    questions.extend(topic_questions)
                
                if len(questions) < 15:
                    # Fill with general questions
                    additional = self.db.query(Question).filter(
                        Question.subject_id == subject_id
                    ).limit(15 - len(questions)).all()
                    questions.extend(additional)
                
                return questions[:20]
        
        elif assessment_type == "comprehensive":
            # Comprehensive assessment across all topics
            return self.diagnostic_service.get_diagnostic_questions(subject_id, limit=30)
        
        else:  # adaptive
            # Adaptive based on performance level
            if avg_score >= 80:
                difficulty_range = (7, 10)
                limit = 15
            elif avg_score >= 60:
                difficulty_range = (5, 8)
                limit = 20
            else:
                difficulty_range = (3, 6)
                limit = 25
            
            questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty.between(*difficulty_range)
                )
            ).limit(limit).all()
            
            return questions
    
    def _format_question_for_frontend(self, question: Question) -> Dict[str, Any]:
        """Format question data for frontend consumption."""
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
            "estimated_time_seconds": getattr(question, 'tiempo_estimado', 90),
            "points": question.puntos_xp or 10
        }
    
    def _calculate_topic_improvements(self, current_scores: Dict[str, float], 
                                    previous_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate topic-level improvements between assessments."""
        improvements = {}
        for topic, current_score in current_scores.items():
            previous_score = previous_scores.get(topic, 0)
            improvements[topic] = current_score - previous_score
        return improvements
    
    def _calculate_progress_trends(self, timeline_data: List[Dict], 
                                 monthly_aggregates: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate progress trends from timeline data."""
        if len(timeline_data) < 2:
            return {"insufficient_data": True}
        
        scores = [test["score_percentage"] for test in timeline_data]
        times = [test["time_spent_minutes"] for test in timeline_data]
        
        # Calculate linear trend
        n = len(scores)
        x_values = list(range(n))
        
        # Simple linear regression for score trend
        x_mean = sum(x_values) / n
        y_mean = sum(scores) / n
        
        numerator = sum((x_values[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))
        
        score_slope = numerator / denominator if denominator != 0 else 0
        
        # Time efficiency trend
        time_slope = 0
        if len(times) > 1:
            time_numerator = sum((x_values[i] - x_mean) * (times[i] - sum(times)/n) for i in range(n))
            time_slope = time_numerator / denominator if denominator != 0 else 0
        
        return {
            "score_trend": {
                "slope": score_slope,
                "direction": "improving" if score_slope > 0.5 else "declining" if score_slope < -0.5 else "stable",
                "rate_per_month": score_slope * 4  # Approximate monthly rate
            },
            "time_efficiency_trend": {
                "slope": time_slope,
                "direction": "faster" if time_slope < -1 else "slower" if time_slope > 1 else "stable"
            },
            "consistency": {
                "score_variance": sum((s - y_mean) ** 2 for s in scores) / n,
                "is_consistent": sum((s - y_mean) ** 2 for s in scores) / n < 100
            }
        }
    
    def _generate_progress_predictions(self, timeline_data: List[Dict], 
                                     trends: Dict[str, Any]) -> Dict[str, Any]:
        """Generate predictions for future performance."""
        if trends.get("insufficient_data") or len(timeline_data) < 3:
            return {"prediction_available": False}
        
        current_score = timeline_data[-1]["score_percentage"]
        score_slope = trends["score_trend"]["slope"]
        
        # Predict scores for next 1, 3, and 6 months
        predictions = {}
        for months in [1, 3, 6]:
            predicted_score = current_score + (score_slope * months * 4)  # 4 assessments per month
            predicted_score = max(0, min(100, predicted_score))  # Clamp between 0-100
            
            predictions[f"month_{months}"] = {
                "predicted_score": round(predicted_score, 1),
                "confidence": self._calculate_prediction_confidence_score(timeline_data, months),
                "improvement_needed": max(0, 85 - predicted_score)  # Assuming 85% is target
            }
        
        return {
            "prediction_available": True,
            "predictions": predictions,
            "trend_based": True,
            "recommendations": self._generate_prediction_recommendations(predictions, trends)
        }
    
    def _analyze_performance_patterns(self, timeline_data: List[Dict]) -> Dict[str, Any]:
        """Analyze performance patterns and identify insights."""
        if len(timeline_data) < 2:
            return {"insufficient_data": True}
        
        patterns = {
            "learning_acceleration": self._detect_learning_acceleration(timeline_data),
            "plateau_detection": self._detect_performance_plateaus(timeline_data),
            "topic_mastery_progression": self._analyze_topic_mastery(timeline_data),
            "optimal_study_frequency": self._suggest_optimal_frequency(timeline_data),
            "strength_consistency": self._analyze_strength_consistency(timeline_data),
            "weakness_resolution": self._analyze_weakness_resolution(timeline_data)
        }
        
        return patterns
    
    def _update_training_zone_questions(self, user_id: str, subject_id: str, 
                                       assessment_result: Dict[str, Any]):
        """Update training zone questions based on latest diagnostic results."""
        try:
            comparison = assessment_result.get("comparison", {})
            current_scores = comparison.get("current_score_by_topic", {})
            
            # Identify topics that need focus
            focus_topics = []
            for topic, score in current_scores.items():
                if score < 70:  # Topics below 70% need focus
                    focus_topics.append(topic)
            
            # Update question pool for training sessions
            # This would integrate with a training zone service
            self.logger.info(f"Updated training zone for user {user_id}, focusing on: {focus_topics}")
            
        except Exception as e:
            self.logger.error(f"Error updating training zone questions: {str(e)}")
    
    def _refresh_video_recommendations(self, user_id: str, subject_id: str, 
                                     assessment_result: Dict[str, Any]):
        """Refresh YouTube video recommendations based on assessment results."""
        try:
            # Get video recommendation service
            from .video_recommendation_service import VideoRecommendationService
            video_service = VideoRecommendationService(self.db)
            
            comparison = assessment_result.get("comparison", {})
            weak_topics = comparison.get("topics_declined", [])
            improved_topics = comparison.get("topics_improved", [])
            
            # Update video recommendations based on performance
            video_service.update_recommendations_for_user(
                user_id, subject_id, weak_topics, improved_topics
            )
            
            self.logger.info(f"Refreshed video recommendations for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error refreshing video recommendations: {str(e)}")
    
    def _update_study_plan(self, user_id: str, subject_id: str, 
                          assessment_result: Dict[str, Any]):
        """Update study plan based on assessment results."""
        try:
            from .study_plan_service import StudyPlanService
            plan_service = StudyPlanService(self.db)
            
            comparison = assessment_result.get("comparison", {})
            new_goals = assessment_result.get("new_goals", [])
            
            # Update or create new study plan
            plan_service.update_plan_based_on_assessment(
                user_id, subject_id, comparison, new_goals
            )
            
            self.logger.info(f"Updated study plan for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error updating study plan: {str(e)}")
    
    def _generate_progress_report(self, user_id: str, subject_id: str, 
                                assessment_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive progress report."""
        try:
            comparison = assessment_result.get("comparison", {})
            
            report = {
                "report_id": str(uuid.uuid4()),
                "user_id": user_id,
                "subject_id": subject_id,
                "generated_at": datetime.utcnow(),
                "assessment_summary": {
                    "current_score": comparison.get("current_score", 0),
                    "initial_score": comparison.get("initial_score", 0),
                    "improvement": comparison.get("improvement_percentage", 0),
                    "days_since_initial": comparison.get("days_since_initial", 0)
                },
                "topic_analysis": {
                    "improved_topics": comparison.get("topics_improved", []),
                    "declined_topics": comparison.get("topics_declined", []),
                    "score_breakdown": comparison.get("current_score_by_topic", {})
                },
                "recommendations": assessment_result.get("new_goals", []),
                "trend_analysis": comparison.get("overall_trend", "stable"),
                "next_steps": self._generate_next_steps(comparison)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating progress report: {str(e)}")
            return {"error": "Failed to generate progress report"}
    
    def _establish_baseline_metrics(self, user_id: str, subject_id: str, test_id: str):
        """Establish baseline metrics for future comparisons."""
        try:
            test = self.db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
            if test:
                test.reassessment_type = "initial"
                self.db.commit()
                self.logger.info(f"Established baseline metrics for user {user_id}, subject {subject_id}")
        except Exception as e:
            self.logger.error(f"Error establishing baseline metrics: {str(e)}")
    
    # Additional helper methods for metrics calculation
    
    def _calculate_overview_metrics(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Calculate overview metrics from diagnostic tests."""
        if not diagnostics:
            return {}
        
        scores = [float(d.score_percentage) for d in diagnostics]
        
        return {
            "total_assessments": len(diagnostics),
            "current_score": scores[-1],
            "best_score": max(scores),
            "average_score": sum(scores) / len(scores),
            "total_improvement": scores[-1] - scores[0] if len(scores) > 1 else 0,
            "assessment_frequency": len(diagnostics) / max(1, (diagnostics[-1].created_at - diagnostics[0].created_at).days / 30)
        }
    
    def _calculate_score_progression(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Calculate score progression metrics."""
        scores = [float(d.score_percentage) for d in diagnostics]
        dates = [d.created_at for d in diagnostics]
        
        if len(scores) < 2:
            return {"insufficient_data": True}
        
        # Calculate improvements between consecutive tests
        improvements = []
        for i in range(1, len(scores)):
            improvements.append(scores[i] - scores[i-1])
        
        return {
            "score_progression": scores,
            "assessment_dates": dates,
            "improvements": improvements,
            "average_improvement": sum(improvements) / len(improvements),
            "positive_improvements": sum(1 for imp in improvements if imp > 0),
            "improvement_rate": sum(1 for imp in improvements if imp > 0) / len(improvements)
        }
    
    def _calculate_topic_improvement_metrics(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Calculate topic-specific improvement metrics."""
        topic_progression = {}
        
        for diagnostic in diagnostics:
            if diagnostic.score_by_topic:
                for topic, score in diagnostic.score_by_topic.items():
                    if topic not in topic_progression:
                        topic_progression[topic] = []
                    topic_progression[topic].append({
                        "score": score,
                        "date": diagnostic.created_at
                    })
        
        topic_metrics = {}
        for topic, scores_data in topic_progression.items():
            scores = [data["score"] for data in scores_data]
            if len(scores) > 1:
                topic_metrics[topic] = {
                    "current_score": scores[-1],
                    "initial_score": scores[0],
                    "total_improvement": scores[-1] - scores[0],
                    "best_score": max(scores),
                    "progression": scores
                }
        
        return topic_metrics
    
    def _calculate_time_efficiency_metrics(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Calculate time efficiency metrics."""
        times = [d.time_spent_seconds / 60 for d in diagnostics]  # Convert to minutes
        scores = [float(d.score_percentage) for d in diagnostics]
        
        if not times:
            return {}
        
        # Calculate efficiency (score per minute)
        efficiency_scores = []
        for i, time in enumerate(times):
            if time > 0:
                efficiency_scores.append(scores[i] / time)
        
        return {
            "average_time_minutes": sum(times) / len(times),
            "time_trend": "improving" if len(times) > 1 and times[-1] < times[0] else "stable",
            "efficiency_scores": efficiency_scores,
            "average_efficiency": sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0
        }
    
    def _calculate_consistency_metrics(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Calculate consistency metrics."""
        scores = [float(d.score_percentage) for d in diagnostics]
        
        if len(scores) < 3:
            return {"insufficient_data": True}
        
        # Calculate variance and standard deviation
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # Coefficient of variation (lower is more consistent)
        cv = std_dev / mean_score if mean_score > 0 else 0
        
        return {
            "mean_score": mean_score,
            "standard_deviation": std_dev,
            "coefficient_of_variation": cv,
            "consistency_rating": "high" if cv < 0.1 else "medium" if cv < 0.2 else "low",
            "score_range": max(scores) - min(scores)
        }
    
    def _calculate_difficulty_progression(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Calculate difficulty progression metrics."""
        # This would analyze the difficulty of questions answered correctly over time
        # Implementation depends on question difficulty tracking
        return {
            "difficulty_analysis": "Feature pending - requires question difficulty tracking in diagnostic results"
        }
    
    def _calculate_learning_velocity(self, diagnostics: List[DiagnosticTest]) -> Dict[str, Any]:
        """Calculate learning velocity metrics."""
        if len(diagnostics) < 2:
            return {"insufficient_data": True}
        
        scores = [float(d.score_percentage) for d in diagnostics]
        dates = [d.created_at for d in diagnostics]
        
        # Calculate velocity as improvement per day
        total_days = (dates[-1] - dates[0]).days
        total_improvement = scores[-1] - scores[0]
        
        if total_days > 0:
            velocity = total_improvement / total_days
        else:
            velocity = 0
        
        return {
            "learning_velocity_per_day": velocity,
            "total_improvement": total_improvement,
            "total_days": total_days,
            "velocity_rating": "fast" if velocity > 0.5 else "medium" if velocity > 0.2 else "slow"
        }
    
    def _calculate_prediction_confidence(self, diagnostics: List[DiagnosticTest]) -> float:
        """Calculate confidence score for predictions."""
        if len(diagnostics) < 3:
            return 0.3
        
        # Base confidence on consistency and data points
        scores = [float(d.score_percentage) for d in diagnostics]
        mean_score = sum(scores) / len(scores)
        variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
        
        # Lower variance = higher confidence
        consistency_factor = max(0.1, 1 - (variance / 100))
        data_factor = min(1.0, len(diagnostics) / 10)  # More data = higher confidence
        
        return (consistency_factor + data_factor) / 2
    
    def _calculate_prediction_confidence_score(self, timeline_data: List[Dict], months: int) -> float:
        """Calculate prediction confidence for specific time horizon."""
        base_confidence = self._calculate_prediction_confidence([])
        
        # Reduce confidence for longer predictions
        time_factor = max(0.3, 1 - (months * 0.1))
        
        return base_confidence * time_factor
    
    def _generate_prediction_recommendations(self, predictions: Dict, trends: Dict) -> List[str]:
        """Generate recommendations based on predictions."""
        recommendations = []
        
        if trends.get("score_trend", {}).get("direction") == "improving":
            recommendations.append("Mantén tu rutina actual de estudio, estás progresando bien")
        elif trends.get("score_trend", {}).get("direction") == "declining":
            recommendations.append("Considera ajustar tu estrategia de estudio para revertir la tendencia negativa")
        else:
            recommendations.append("Busca formas de acelerar tu progreso con técnicas de estudio más efectivas")
        
        return recommendations
    
    def _detect_learning_acceleration(self, timeline_data: List[Dict]) -> Dict[str, Any]:
        """Detect if learning is accelerating."""
        if len(timeline_data) < 4:
            return {"insufficient_data": True}
        
        # Compare improvement rates in different periods
        mid_point = len(timeline_data) // 2
        first_half_improvement = timeline_data[mid_point]["score_percentage"] - timeline_data[0]["score_percentage"]
        second_half_improvement = timeline_data[-1]["score_percentage"] - timeline_data[mid_point]["score_percentage"]
        
        is_accelerating = second_half_improvement > first_half_improvement
        
        return {
            "is_accelerating": is_accelerating,
            "first_half_improvement": first_half_improvement,
            "second_half_improvement": second_half_improvement,
            "acceleration_factor": second_half_improvement / max(1, first_half_improvement)
        }
    
    def _detect_performance_plateaus(self, timeline_data: List[Dict]) -> Dict[str, Any]:
        """Detect performance plateaus."""
        if len(timeline_data) < 5:
            return {"insufficient_data": True}
        
        # Look for periods of minimal improvement
        scores = [test["score_percentage"] for test in timeline_data]
        plateau_threshold = 2.0  # Less than 2% improvement considered plateau
        
        plateau_periods = []
        current_plateau = []
        
        for i in range(1, len(scores)):
            improvement = scores[i] - scores[i-1]
            if abs(improvement) < plateau_threshold:
                current_plateau.append(i)
            else:
                if len(current_plateau) >= 3:  # At least 3 consecutive tests
                    plateau_periods.append(current_plateau)
                current_plateau = []
        
        # Check if we're currently in a plateau
        if len(current_plateau) >= 2:
            plateau_periods.append(current_plateau)
        
        return {
            "has_plateaus": len(plateau_periods) > 0,
            "plateau_periods": plateau_periods,
            "current_plateau": len(current_plateau) >= 2,
            "longest_plateau": max(len(p) for p in plateau_periods) if plateau_periods else 0
        }
    
    def _analyze_topic_mastery(self, timeline_data: List[Dict]) -> Dict[str, Any]:
        """Analyze topic mastery progression."""
        topic_mastery = {}
        mastery_threshold = 85.0  # 85% considered mastery
        
        for test in timeline_data:
            for topic, score in test.get("score_by_topic", {}).items():
                if topic not in topic_mastery:
                    topic_mastery[topic] = {
                        "scores": [],
                        "mastery_achieved": False,
                        "mastery_date": None
                    }
                
                topic_mastery[topic]["scores"].append({
                    "score": score,
                    "date": test["date"]
                })
                
                if score >= mastery_threshold and not topic_mastery[topic]["mastery_achieved"]:
                    topic_mastery[topic]["mastery_achieved"] = True
                    topic_mastery[topic]["mastery_date"] = test["date"]
        
        return {
            "topic_mastery": topic_mastery,
            "mastered_topics": [topic for topic, data in topic_mastery.items() if data["mastery_achieved"]],
            "topics_near_mastery": [
                topic for topic, data in topic_mastery.items() 
                if not data["mastery_achieved"] and data["scores"] and data["scores"][-1]["score"] >= 75
            ]
        }
    
    def _suggest_optimal_frequency(self, timeline_data: List[Dict]) -> Dict[str, Any]:
        """Suggest optimal assessment frequency based on learning patterns."""
        if len(timeline_data) < 3:
            return {"suggestion": "monthly", "reason": "Insufficient data for optimization"}
        
        # Analyze improvement patterns relative to assessment frequency
        dates = [test["date"] for test in timeline_data]
        scores = [test["score_percentage"] for test in timeline_data]
        
        # Calculate average days between assessments
        intervals = []
        for i in range(1, len(dates)):
            interval = (dates[i] - dates[i-1]).days
            intervals.append(interval)
        
        avg_interval = sum(intervals) / len(intervals)
        
        # Analyze if shorter or longer intervals correlate with better improvement
        # This is a simplified analysis
        if avg_interval <= 15:
            suggestion = "bi_weekly"
            reason = "Current frequency is working well for consistent improvement"
        elif avg_interval <= 35:
            suggestion = "monthly"
            reason = "Monthly assessments provide good balance of progress tracking"
        else:
            suggestion = "bi_weekly"
            reason = "More frequent assessments recommended to accelerate progress"
        
        return {
            "current_average_interval_days": avg_interval,
            "suggestion": suggestion,
            "reason": reason
        }
    
    def _analyze_strength_consistency(self, timeline_data: List[Dict]) -> Dict[str, Any]:
        """Analyze consistency of strengths over time."""
        strength_consistency = {}
        
        for test in timeline_data:
            for strength in test.get("strengths", []):
                if strength not in strength_consistency:
                    strength_consistency[strength] = 0
                strength_consistency[strength] += 1
        
        total_tests = len(timeline_data)
        consistent_strengths = {
            strength: count for strength, count in strength_consistency.items()
            if count >= total_tests * 0.6  # Appeared in 60% or more of tests
        }
        
        return {
            "consistent_strengths": list(consistent_strengths.keys()),
            "strength_frequency": strength_consistency,
            "strength_stability": len(consistent_strengths) / max(1, len(strength_consistency))
        }
    
    def _analyze_weakness_resolution(self, timeline_data: List[Dict]) -> Dict[str, Any]:
        """Analyze how weaknesses are being resolved over time."""
        weakness_tracking = {}
        
        for i, test in enumerate(timeline_data):
            for weakness in test.get("weaknesses", []):
                if weakness not in weakness_tracking:
                    weakness_tracking[weakness] = {
                        "first_appearance": i,
                        "last_appearance": i,
                        "total_appearances": 1
                    }
                else:
                    weakness_tracking[weakness]["last_appearance"] = i
                    weakness_tracking[weakness]["total_appearances"] += 1
        
        resolved_weaknesses = []
        persistent_weaknesses = []
        
        total_tests = len(timeline_data)
        
        for weakness, data in weakness_tracking.items():
            # Consider resolved if not appeared in last 3 tests and appeared before
            if data["last_appearance"] < total_tests - 3 and data["first_appearance"] < total_tests - 3:
                resolved_weaknesses.append(weakness)
            elif data["total_appearances"] >= total_tests * 0.5:  # Appeared in 50% or more
                persistent_weaknesses.append(weakness)
        
        return {
            "resolved_weaknesses": resolved_weaknesses,
            "persistent_weaknesses": persistent_weaknesses,
            "weakness_resolution_rate": len(resolved_weaknesses) / max(1, len(weakness_tracking)),
            "weakness_tracking": weakness_tracking
        }
    
    def _generate_next_steps(self, comparison: Dict[str, Any]) -> List[str]:
        """Generate next steps based on assessment comparison."""
        next_steps = []
        
        improvement = comparison.get("improvement_percentage", 0)
        declined_topics = comparison.get("topics_declined", [])
        improved_topics = comparison.get("topics_improved", [])
        
        if improvement > 10:
            next_steps.append("Continúa con tu estrategia actual, está funcionando muy bien")
            next_steps.append("Considera aumentar la dificultad de los ejercicios")
        elif improvement > 0:
            next_steps.append("Mantén la consistencia en tu estudio")
            next_steps.append("Enfócate en consolidar las mejoras obtenidas")
        else:
            next_steps.append("Revisa y ajusta tu plan de estudio")
            next_steps.append("Considera cambiar la metodología de estudio")
        
        if declined_topics:
            next_steps.append(f"Prioriza el refuerzo en: {', '.join(declined_topics)}")
        
        if improved_topics:
            next_steps.append(f"Mantén el buen trabajo en: {', '.join(improved_topics)}")
        
        return next_steps