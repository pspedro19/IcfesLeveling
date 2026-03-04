"""
Unified Study Plan Service with Weekly Schedule and Spaced Repetition
LOGICA_DE_NEGOCIO.md: Claude AI Plan 100%

Features:
- Weekly schedule generation based on user preferences
- Spaced repetition algorithm for optimal learning
- Daily task distribution
- Video and practice session integration
"""

import json
import math
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any, Tuple

# Import necessary services that will be orchestrated
from .llm_service import LLMService
from .study_plan_storage import StudyPlanStorage
from .diagnostic_service import DiagnosticService
from .video_recommendation_service import VideoRecommendationService
from .mastery_service import MasteryService, DECAY_START_DAYS


# =============================================================================
# SPACED REPETITION CONSTANTS (LOGICA_DE_NEGOCIO.md)
# =============================================================================

# Interval multipliers based on response quality (SM-2 inspired)
SPACED_REPETITION_INTERVALS = {
    "failed": 1,           # Review next day
    "hard": 2,             # Review in 2 days
    "good": 4,             # Review in 4 days
    "easy": 7,             # Review in 7 days
}

# Easiness factor adjustments
EASINESS_FACTOR_MIN = 1.3
EASINESS_FACTOR_INITIAL = 2.5
EASINESS_FACTOR_ADJUSTMENT = {
    "failed": -0.3,
    "hard": -0.15,
    "good": 0.0,
    "easy": 0.1,
}

# Daily study slots
DAILY_SLOTS = ["morning", "afternoon", "evening"]
DEFAULT_SLOT_DURATION_MINUTES = 20


class SpacedRepetitionScheduler:
    """
    Implements spaced repetition algorithm for optimal topic review scheduling.
    Based on SM-2 algorithm with modifications for ICFES content.
    """

    def __init__(self, db: Session, user_id: UUID):
        self.db = db
        self.user_id = user_id

    def calculate_next_review(
        self,
        topic_id: str,
        last_quality: str,  # "failed", "hard", "good", "easy"
        current_interval: int = 1,
        current_ef: float = EASINESS_FACTOR_INITIAL
    ) -> Tuple[int, float]:
        """
        Calculate next review interval and updated easiness factor.

        Args:
            topic_id: Topic being reviewed
            last_quality: Quality of last response
            current_interval: Current interval in days
            current_ef: Current easiness factor

        Returns:
            Tuple of (new_interval, new_easiness_factor)
        """
        # Get base interval from quality
        base_interval = SPACED_REPETITION_INTERVALS.get(last_quality, 4)

        # Adjust easiness factor
        ef_adjustment = EASINESS_FACTOR_ADJUSTMENT.get(last_quality, 0.0)
        new_ef = max(EASINESS_FACTOR_MIN, current_ef + ef_adjustment)

        # Calculate new interval
        if last_quality == "failed":
            # Reset to 1 day on failure
            new_interval = 1
        elif current_interval == 1:
            # First successful review
            new_interval = base_interval
        else:
            # Subsequent reviews: interval * easiness factor
            new_interval = int(current_interval * new_ef)

        # Cap interval at 30 days
        new_interval = min(30, new_interval)

        return new_interval, new_ef

    def get_topics_due_for_review(self, limit: int = 10) -> List[Dict]:
        """
        Get topics that are due for spaced repetition review today.
        """
        from ..models.mobile_offline import UserTopicMastery

        today = datetime.utcnow().date()

        # Query topics where next_review_at <= today
        due_topics = self.db.query(UserTopicMastery).filter(
            and_(
                UserTopicMastery.user_id == self.user_id,
                UserTopicMastery.next_review_at <= today
            )
        ).order_by(UserTopicMastery.next_review_at.asc()).limit(limit).all()

        result = []
        for topic_mastery in due_topics:
            days_overdue = (today - topic_mastery.next_review_at.date()).days
            priority = "high" if days_overdue > 3 else "medium" if days_overdue > 1 else "normal"

            result.append({
                "topic_id": str(topic_mastery.topic_id),
                "mastery_score": topic_mastery.mastery_score,
                "days_overdue": days_overdue,
                "priority": priority,
                "easiness_factor": getattr(topic_mastery, 'easiness_factor', EASINESS_FACTOR_INITIAL),
            })

        return result


class WeeklyScheduleGenerator:
    """
    Generates weekly study schedules based on user preferences and available time.
    """

    def __init__(self, db: Session, user_id: UUID):
        self.db = db
        self.user_id = user_id
        self.spaced_rep = SpacedRepetitionScheduler(db, user_id)

    def generate_weekly_schedule(
        self,
        daily_study_minutes: int = 20,
        weak_subjects: List[str] = None,
        exam_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete weekly study schedule.

        Args:
            daily_study_minutes: Target daily study time (10, 20, or 30+)
            weak_subjects: List of subject IDs to prioritize
            exam_date: Optional exam date for urgency adjustment

        Returns:
            Weekly schedule with daily tasks
        """
        # Get topics needing review (spaced repetition)
        review_topics = self.spaced_rep.get_topics_due_for_review(limit=20)

        # Get new topics to learn
        new_topics = self._get_new_topics_to_learn(weak_subjects)

        # Calculate urgency multiplier if exam date provided
        urgency = 1.0
        if exam_date:
            days_until_exam = (exam_date - datetime.utcnow()).days
            if days_until_exam <= 7:
                urgency = 2.0  # Double intensity in last week
            elif days_until_exam <= 14:
                urgency = 1.5
            elif days_until_exam <= 30:
                urgency = 1.25

        # Build schedule for each day
        week_schedule = {
            "week_start": datetime.utcnow().date().isoformat(),
            "daily_target_minutes": daily_study_minutes,
            "urgency_multiplier": urgency,
            "days": []
        }

        day_names = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]

        for day_idx in range(7):
            day_date = datetime.utcnow().date() + timedelta(days=day_idx)
            is_weekend = day_idx >= 5

            # Distribute topics across the week
            daily_tasks = self._create_daily_tasks(
                day_idx=day_idx,
                review_topics=review_topics,
                new_topics=new_topics,
                daily_minutes=int(daily_study_minutes * urgency),
                is_weekend=is_weekend
            )

            week_schedule["days"].append({
                "day_name": day_names[day_idx],
                "date": day_date.isoformat(),
                "is_weekend": is_weekend,
                "tasks": daily_tasks,
                "estimated_minutes": sum(t.get("duration_minutes", 10) for t in daily_tasks),
            })

        # Add summary stats
        week_schedule["summary"] = {
            "total_review_topics": len(review_topics),
            "total_new_topics": len(new_topics),
            "total_estimated_minutes": sum(d["estimated_minutes"] for d in week_schedule["days"]),
            "focus_areas": weak_subjects or [],
        }

        return week_schedule

    def _get_new_topics_to_learn(self, weak_subjects: List[str] = None) -> List[Dict]:
        """Get new topics that user hasn't learned yet."""
        from ..models import Topic, Subject
        from ..models.mobile_offline import UserTopicMastery

        # Get all topics user hasn't started
        learned_topic_ids = self.db.query(UserTopicMastery.topic_id).filter(
            UserTopicMastery.user_id == self.user_id
        ).subquery()

        query = self.db.query(Topic, Subject).join(
            Subject, Topic.subject_id == Subject.id
        ).filter(~Topic.id.in_(learned_topic_ids))

        if weak_subjects:
            query = query.filter(Subject.id.in_(weak_subjects))

        new_topics = query.limit(14).all()  # 2 new topics per day max

        return [
            {
                "topic_id": str(topic.id),
                "topic_name": topic.name,
                "subject_id": str(subject.id),
                "subject_name": subject.name,
                "is_new": True,
            }
            for topic, subject in new_topics
        ]

    def _create_daily_tasks(
        self,
        day_idx: int,
        review_topics: List[Dict],
        new_topics: List[Dict],
        daily_minutes: int,
        is_weekend: bool
    ) -> List[Dict]:
        """Create tasks for a specific day."""
        tasks = []
        minutes_used = 0

        # Distribute review topics across the week
        review_for_day = [t for i, t in enumerate(review_topics) if i % 7 == day_idx]

        # Add review tasks (spaced repetition)
        for topic in review_for_day[:2]:  # Max 2 reviews per day
            if minutes_used >= daily_minutes:
                break

            task_minutes = 10 if topic["priority"] == "normal" else 15
            tasks.append({
                "type": "review",
                "topic_id": topic["topic_id"],
                "description": f"Repaso espaciado",
                "duration_minutes": task_minutes,
                "priority": topic["priority"],
            })
            minutes_used += task_minutes

        # Add new learning tasks
        new_for_day = [t for i, t in enumerate(new_topics) if i % 7 == day_idx]

        for topic in new_for_day[:2]:  # Max 2 new topics per day
            if minutes_used >= daily_minutes:
                break

            task_minutes = 15  # New topics take longer
            tasks.append({
                "type": "learn",
                "topic_id": topic["topic_id"],
                "topic_name": topic["topic_name"],
                "subject_name": topic["subject_name"],
                "description": f"Nuevo tema: {topic['topic_name']}",
                "duration_minutes": task_minutes,
            })
            minutes_used += task_minutes

        # Add practice session if time remains
        if minutes_used < daily_minutes:
            remaining = daily_minutes - minutes_used
            tasks.append({
                "type": "practice",
                "description": "Sesion de practica",
                "duration_minutes": remaining,
                "question_count": remaining // 2,  # ~30 seconds per question
            })

        # Weekend bonus: Add a quiz challenge
        if is_weekend and tasks:
            tasks.append({
                "type": "challenge",
                "description": "Desafio semanal",
                "duration_minutes": 15,
                "bonus_xp": 50,
            })

        return tasks


class UnifiedStudyPlanService:
    """
    The single source of truth for generating, updating, and managing student study plans.
    This service orchestrates multiple underlying services (AI, storage, diagnostics)
    to provide a cohesive experience.
    """

    def __init__(self, db: Session, user_id: UUID):
        self.db = db
        self.user_id = user_id

        # Initialize the services this orchestrator will use
        self.llm_service = LLMService()
        self.storage_service = StudyPlanStorage(db=db, user_id=user_id)
        self.diagnostic_service = DiagnosticService(db=db)
        self.video_service = VideoRecommendationService(db=db)

        # Weekly schedule and spaced repetition (LOGICA_DE_NEGOCIO.md)
        self.weekly_scheduler = WeeklyScheduleGenerator(db=db, user_id=user_id)
        self.spaced_rep = SpacedRepetitionScheduler(db=db, user_id=user_id)

    def generate_weekly_schedule(
        self,
        daily_study_minutes: int = 20,
        weak_subjects: List[str] = None,
        exam_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a personalized weekly study schedule.

        Uses spaced repetition for review topics and intelligently
        distributes new learning across the week.

        Args:
            daily_study_minutes: Target study time per day (10, 20, 30+)
            weak_subjects: Priority subjects to focus on
            exam_date: Optional exam date for urgency adjustment

        Returns:
            Complete weekly schedule with daily tasks
        """
        return self.weekly_scheduler.generate_weekly_schedule(
            daily_study_minutes=daily_study_minutes,
            weak_subjects=weak_subjects,
            exam_date=exam_date
        )

    def get_todays_tasks(self) -> Dict[str, Any]:
        """
        Get today's study tasks from the active schedule.

        Includes spaced repetition reviews and new learning tasks.
        """
        # Get topics due for review
        review_topics = self.spaced_rep.get_topics_due_for_review(limit=5)

        # Get user preferences
        preferences = self._get_user_preferences()

        # Build today's task list
        tasks = []

        # Add urgent reviews first
        for topic in review_topics:
            if topic["priority"] in ["high", "medium"]:
                tasks.append({
                    "type": "review",
                    "topic_id": topic["topic_id"],
                    "mastery_score": topic["mastery_score"],
                    "priority": topic["priority"],
                    "days_overdue": topic["days_overdue"],
                    "estimated_minutes": 10,
                    "description": "Repaso urgente - no pierdas tu progreso!",
                })

        # Add regular reviews
        for topic in review_topics:
            if topic["priority"] == "normal" and len(tasks) < 3:
                tasks.append({
                    "type": "review",
                    "topic_id": topic["topic_id"],
                    "mastery_score": topic["mastery_score"],
                    "priority": topic["priority"],
                    "estimated_minutes": 8,
                    "description": "Refuerza tu conocimiento",
                })

        return {
            "date": datetime.utcnow().date().isoformat(),
            "tasks": tasks,
            "total_estimated_minutes": sum(t.get("estimated_minutes", 10) for t in tasks),
            "review_count": len(review_topics),
        }

    def record_review_result(
        self,
        topic_id: str,
        quality: str,  # "failed", "hard", "good", "easy"
        time_spent_seconds: int = 0
    ) -> Dict[str, Any]:
        """
        Record the result of a spaced repetition review.

        Updates the topic's next review date based on performance.

        Args:
            topic_id: Topic that was reviewed
            quality: Quality of response
            time_spent_seconds: Time spent on review

        Returns:
            Updated review schedule for the topic
        """
        from ..models.mobile_offline import UserTopicMastery

        topic_mastery = self.db.query(UserTopicMastery).filter(
            and_(
                UserTopicMastery.user_id == self.user_id,
                UserTopicMastery.topic_id == topic_id
            )
        ).first()

        if not topic_mastery:
            return {"error": "Topic mastery not found"}

        # Get current values
        current_interval = getattr(topic_mastery, 'review_interval', 1) or 1
        current_ef = getattr(topic_mastery, 'easiness_factor', EASINESS_FACTOR_INITIAL) or EASINESS_FACTOR_INITIAL

        # Calculate next review
        new_interval, new_ef = self.spaced_rep.calculate_next_review(
            topic_id=topic_id,
            last_quality=quality,
            current_interval=current_interval,
            current_ef=current_ef
        )

        # Update topic mastery
        topic_mastery.next_review_at = datetime.utcnow() + timedelta(days=new_interval)
        topic_mastery.review_interval = new_interval
        topic_mastery.easiness_factor = new_ef
        topic_mastery.last_practiced_at = datetime.utcnow()

        # Update mastery score based on quality
        score_adjustment = {
            "failed": -0.1,
            "hard": -0.02,
            "good": 0.05,
            "easy": 0.1,
        }
        topic_mastery.mastery_score = max(0.0, min(1.0,
            topic_mastery.mastery_score + score_adjustment.get(quality, 0)))

        self.db.commit()

        return {
            "topic_id": topic_id,
            "quality": quality,
            "new_interval_days": new_interval,
            "new_easiness_factor": round(new_ef, 2),
            "next_review_at": topic_mastery.next_review_at.isoformat(),
            "updated_mastery": round(topic_mastery.mastery_score, 3),
        }

    def _get_user_preferences(self) -> Dict[str, Any]:
        """Get user's study preferences from onboarding data."""
        from ..models.user import User

        user = self.db.query(User).filter(User.id == self.user_id).first()
        if not user or not user.onboarding_preferences:
            return {
                "daily_study_time": "twentyMinutes",
                "weak_subjects": [],
                "goal": "mejorarIcfes",
            }

        return user.onboarding_preferences

    def generate_initial_plan(self, subject_id: UUID) -> Dict[str, Any]:
        """
        Generates the very first study plan for a user after a deep diagnostic.
        """
        # 1. Fetch diagnostic results
        weaknesses = self.diagnostic_service.get_weaknesses(self.user_id, subject_id)
        
        # 2. Get available videos for the identified weaknesses
        # This is a simplified version; in reality, we'd pass topic IDs
        recommended_videos = self.video_service.get_recommendations_for_topics(
            topic_ids=[w['topic_id'] for w in weaknesses]
        )

        # 3. Construct a prompt for the AI
        prompt = self._build_initial_plan_prompt(weaknesses, recommended_videos)
        
        # 4. Call the AI service to generate the plan
        generated_plan_str = self.llm_service.generate_text(prompt, max_tokens=2048)
        
        # 5. Parse and store the plan
        plan_data = self._parse_ai_plan(generated_plan_str)
        stored_plan = self.storage_service.save_plan(
            subject_id=subject_id, 
            plan_data=plan_data,
            generator="claude-3.5-sonnet"
        )
        
        return stored_plan

    def regenerate_monthly_plan(self, monthly_assessment_results: Dict) -> Dict[str, Any]:
        """
        Regenerates an existing study plan based on monthly reassessment data.
        """
        # This is where the more sophisticated logic will go.
        # For now, it's a placeholder.
        
        # 1. Analyze performance delta from assessment results
        # 2. Get new weaknesses and strengths
        # 3. Get progress on previous plan from video_tracking and quiz_results
        # 4. Build a new, more detailed prompt for the AI
        # 5. Call AI service
        # 6. Update the existing plan in the database
        
        print("Monthly plan regeneration logic to be implemented here.")
        return {}

    def _build_initial_plan_prompt(self, weaknesses: List[Dict], videos: List[Dict]) -> str:
        """Constructs a detailed prompt for the AI to generate a study plan."""
        
        prompt = "Create a 4-week personalized ICFES study plan for a student with the following weaknesses:\n"
        for w in weaknesses:
            prompt += f"- Topic: {w['topic_name']}, Subject: {w['subject_name']}, Current Mastery: {w['mastery_score']:.0%}\n"
        
        prompt += "\nAvailable educational videos to include in the plan:\n"
        for v in videos:
            prompt += f"- Video ID: {v['youtube_id']}, Title: {v['title']}, Topic: {v['topic_name']}\n"
            
        prompt += """
Please structure the output as a JSON object with a 'weeks' array. Each week should have 'week_number', a 'focus' description, and a 'daily_tasks' array. Each task should have a 'day', a 'description', and a 'resources' array containing video IDs or exercise descriptions.
"""
        return prompt

    def _parse_ai_plan(self, plan_str: str) -> Dict:
        """Parses the string output from the AI into a structured JSON object."""
        # In a real implementation, this would have robust error handling and validation
        try:
            return json.loads(plan_str)
        except:
            # Fallback for malformed JSON
            return {"error": "Failed to parse AI-generated plan", "raw": plan_str}
