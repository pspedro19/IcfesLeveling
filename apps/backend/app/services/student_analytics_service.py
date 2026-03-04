from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.user import User
from ..models.practice_session import PracticeSession, PracticeAnswer
from ..models.topic_mastery import TopicMastery
from ..models.topic import Topic
from ..models.subject import Subject
from ..models.user_daily_activity import UserDailyActivity


class StudentAnalyticsService:
    """Servicio para estadísticas reales del estudiante"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self, user_id: UUID, time_filter: str = "30d") -> Dict:
        """
        Estadísticas del dashboard.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}

        # Time filter
        days = int(time_filter.replace('d', ''))
        start_date = datetime.utcnow() - timedelta(days=days)

        # Base stats
        stats = {
            "level": user.level,
            "experience": user.experience,
            "rank": user.rank,
            "gold": user.gold,
            "streak": 0,
            "win_rate": 0,
            "accuracy": 0,
            "sessions_completed": 0,
            "subject_performance": []
        }

        # Current Streak from daily activity
        last_activity = self.db.query(UserDailyActivity).filter(
            UserDailyActivity.user_id == user_id
        ).order_by(UserDailyActivity.activity_date.desc()).first()
        if last_activity:
            stats['streak'] = user.current_streak

        # Session stats (win rate, accuracy)
        sessions = self.db.query(PracticeSession).filter(
            PracticeSession.user_id == user_id,
            PracticeSession.completed_at >= start_date
        ).all()
        
        if sessions:
            stats['sessions_completed'] = len(sessions)
            total_questions = sum(s.questions_answered for s in sessions)
            total_correct = sum(s.correct_answers for s in sessions)
            
            if total_questions > 0:
                stats['accuracy'] = round((total_correct / total_questions) * 100, 2)
            
            # Win rate (sessions with > 50% accuracy)
            won_sessions = sum(1 for s in sessions if (s.correct_answers / s.questions_answered) > 0.5)
            stats['win_rate'] = round((won_sessions / len(sessions)) * 100, 2)

        # Subject performance
        subject_perf = self.db.query(
            Subject.name,
            func.avg(TopicMastery.mastery_score)
        ).join(Topic, Subject.id == Topic.subject_id).join(TopicMastery, Topic.id == TopicMastery.topic_id).filter(
            TopicMastery.user_id == user_id
        ).group_by(Subject.name).all()

        stats['subject_performance'] = [{"subject": name, "mastery": round(score * 100, 1)} for name, score in subject_perf]

        return stats

    def get_theta_evolution(self, user_id: UUID, time_filter: str) -> List[Dict]:
        """
        Evolución del theta IRT en el tiempo. (Placeholder)
        """
        # Placeholder implementation
        return [
            {"date": (datetime.utcnow() - timedelta(days=i)).isoformat(), "theta": 0.5 + (i * 0.02)}
            for i in range(10)
        ]

    def get_error_analysis(self, user_id: UUID, filters: Dict) -> List[Dict]:
        """
        Análisis de errores cometidos. (Placeholder)
        """
        # Placeholder implementation
        return [
            {"topic": "Ecuaciones Lineales", "errors": 5, "common_mistake": "Error de despeje"},
            {"topic": "Figuras Literarias", "errors": 3, "common_mistake": "Confusión entre metáfora y símil"}
        ]

    def get_weaknesses(self, user_id: UUID, limit: int = 5) -> List[Dict]:
        """
        Identificar debilidades del estudiante.
        """
        weaknesses = self.db.query(
            Topic.name,
            Subject.name.label("subject_name"),
            TopicMastery.mastery_score
        ).join(Topic, TopicMastery.topic_id == Topic.id).join(Subject, Topic.subject_id == Subject.id).filter(
            TopicMastery.user_id == user_id,
            TopicMastery.mastery_score < 0.6
        ).order_by(TopicMastery.mastery_score.asc()).limit(limit).all()

        return [
            {"topic": topic, "subject": subject, "mastery": round(score * 100, 1)}
            for topic, subject, score in weaknesses
        ]

    def get_strengths(self, user_id: UUID, limit: int = 5) -> List[Dict]:
        """
        Identificar fortalezas del estudiante.
        """
        strengths = self.db.query(
            Topic.name,
            Subject.name.label("subject_name"),
            TopicMastery.mastery_score
        ).join(Topic, TopicMastery.topic_id == Topic.id).join(Subject, Topic.subject_id == Subject.id).filter(
            TopicMastery.user_id == user_id,
            TopicMastery.mastery_score >= 0.8
        ).order_by(TopicMastery.mastery_score.desc()).limit(limit).all()

        return [
            {"topic": topic, "subject": subject, "mastery": round(score * 100, 1)}
            for topic, subject, score in strengths
        ]
