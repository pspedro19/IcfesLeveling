"""
Advanced Stats Service - ICFES Leveling
Activity Heatmap, National Comparison, and Historical Stats
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AdvancedStatsService:
    """Service for advanced statistics including heatmap, national comparison, and historical data."""

    def __init__(self, db: Session):
        self.db = db

    def get_activity_heatmap(
        self,
        user_id: UUID,
        days: int = 365
    ) -> Dict[str, Any]:
        """
        Get activity heatmap data (GitHub-style contribution calendar).
        Returns daily activity counts for the past N days.
        """
        try:
            # Query to get daily activity counts
            query = text("""
                WITH daily_activity AS (
                    -- Practice answers
                    SELECT DATE(created_at) as activity_date, COUNT(*) as count, 'answer' as type
                    FROM practice_answers
                    WHERE user_id = :user_id
                    AND created_at >= NOW() - INTERVAL :days DAY
                    GROUP BY DATE(created_at)

                    UNION ALL

                    -- Diagnostic test answers
                    SELECT DATE(dta.created_at) as activity_date, COUNT(*) as count, 'diagnostic' as type
                    FROM diagnostic_test_answers dta
                    JOIN diagnostic_tests dt ON dta.diagnostic_test_id = dt.id
                    WHERE dt.user_id = :user_id
                    AND dta.created_at >= NOW() - INTERVAL :days DAY
                    GROUP BY DATE(dta.created_at)

                    UNION ALL

                    -- Video watches
                    SELECT DATE(created_at) as activity_date, COUNT(*) as count, 'video' as type
                    FROM video_progress
                    WHERE user_id = :user_id
                    AND created_at >= NOW() - INTERVAL :days DAY
                    GROUP BY DATE(created_at)
                )
                SELECT
                    activity_date,
                    SUM(count) as total_activities,
                    JSON_OBJECTAGG(type, count) as breakdown
                FROM daily_activity
                GROUP BY activity_date
                ORDER BY activity_date DESC
            """)

            result = self.db.execute(query, {
                "user_id": str(user_id),
                "days": days
            }).fetchall()

            # Build heatmap data
            heatmap = {}
            for row in result:
                date_str = row[0].strftime("%Y-%m-%d") if row[0] else None
                if date_str:
                    heatmap[date_str] = {
                        "count": int(row[1]) if row[1] else 0,
                        "level": self._get_activity_level(int(row[1]) if row[1] else 0),
                        "breakdown": row[2] if row[2] else {}
                    }

            # Fill in missing dates with zero activity
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            current = start_date

            while current <= end_date:
                date_str = current.strftime("%Y-%m-%d")
                if date_str not in heatmap:
                    heatmap[date_str] = {"count": 0, "level": 0, "breakdown": {}}
                current += timedelta(days=1)

            # Calculate stats
            total_activities = sum(d["count"] for d in heatmap.values())
            active_days = sum(1 for d in heatmap.values() if d["count"] > 0)
            max_streak = self._calculate_max_streak(heatmap)
            current_streak = self._calculate_current_streak(heatmap)

            return {
                "heatmap": heatmap,
                "stats": {
                    "total_activities": total_activities,
                    "active_days": active_days,
                    "total_days": days,
                    "activity_rate": round(active_days / days * 100, 1) if days > 0 else 0,
                    "max_streak": max_streak,
                    "current_streak": current_streak,
                    "avg_daily_activities": round(total_activities / max(active_days, 1), 1)
                }
            }

        except Exception as e:
            logger.error(f"Error getting activity heatmap: {e}")
            # Return empty heatmap on error
            return self._get_empty_heatmap(days)

    def _get_activity_level(self, count: int) -> int:
        """Convert activity count to level (0-4) for color coding."""
        if count == 0:
            return 0
        elif count <= 3:
            return 1
        elif count <= 7:
            return 2
        elif count <= 15:
            return 3
        else:
            return 4

    def _calculate_max_streak(self, heatmap: Dict) -> int:
        """Calculate maximum consecutive active days."""
        dates = sorted(heatmap.keys())
        max_streak = 0
        current_streak = 0

        for date_str in dates:
            if heatmap[date_str]["count"] > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0

        return max_streak

    def _calculate_current_streak(self, heatmap: Dict) -> int:
        """Calculate current consecutive active days (ending today or yesterday)."""
        dates = sorted(heatmap.keys(), reverse=True)
        current_streak = 0

        # Allow for today or yesterday to continue streak
        started = False
        for date_str in dates:
            if heatmap[date_str]["count"] > 0:
                current_streak += 1
                started = True
            elif started:
                break

        return current_streak

    def _get_empty_heatmap(self, days: int) -> Dict[str, Any]:
        """Return empty heatmap structure."""
        heatmap = {}
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        current = start_date

        while current <= end_date:
            date_str = current.strftime("%Y-%m-%d")
            heatmap[date_str] = {"count": 0, "level": 0, "breakdown": {}}
            current += timedelta(days=1)

        return {
            "heatmap": heatmap,
            "stats": {
                "total_activities": 0,
                "active_days": 0,
                "total_days": days,
                "activity_rate": 0,
                "max_streak": 0,
                "current_streak": 0,
                "avg_daily_activities": 0
            }
        }

    def get_national_comparison(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user's mastery compared to national averages.
        Returns percentile ranking and comparison data for radar chart.
        """
        try:
            # Get user's subject mastery
            user_mastery_query = text("""
                SELECT
                    s.id as subject_id,
                    s.name as subject_name,
                    COALESCE(AVG(utm.mastery_score), 0) as user_mastery
                FROM subjects s
                LEFT JOIN topics t ON t.subject_id = s.id
                LEFT JOIN user_topic_mastery utm ON utm.topic_id = t.id AND utm.user_id = :user_id
                GROUP BY s.id, s.name
                ORDER BY s.name
            """)

            user_result = self.db.execute(user_mastery_query, {"user_id": str(user_id)}).fetchall()

            # Get national averages (all users)
            national_avg_query = text("""
                SELECT
                    s.id as subject_id,
                    s.name as subject_name,
                    COALESCE(AVG(utm.mastery_score), 0.5) as national_avg,
                    COUNT(DISTINCT utm.user_id) as total_users
                FROM subjects s
                LEFT JOIN topics t ON t.subject_id = s.id
                LEFT JOIN user_topic_mastery utm ON utm.topic_id = t.id
                GROUP BY s.id, s.name
                ORDER BY s.name
            """)

            national_result = self.db.execute(national_avg_query).fetchall()

            # Build comparison data
            national_map = {str(row[0]): {"avg": float(row[2]), "users": int(row[3])} for row in national_result}

            subjects = []
            for row in user_result:
                subject_id = str(row[0])
                national_data = national_map.get(subject_id, {"avg": 0.5, "users": 0})

                user_score = float(row[2]) if row[2] else 0
                national_avg = national_data["avg"]

                # Calculate percentile
                percentile = self._calculate_percentile(user_id, subject_id)

                subjects.append({
                    "subject_id": subject_id,
                    "subject_name": row[1],
                    "user_mastery": round(user_score * 100, 1),
                    "national_average": round(national_avg * 100, 1),
                    "difference": round((user_score - national_avg) * 100, 1),
                    "percentile": percentile,
                    "total_users_compared": national_data["users"],
                    "status": "above" if user_score > national_avg else ("below" if user_score < national_avg else "equal")
                })

            # Overall stats
            user_overall = sum(s["user_mastery"] for s in subjects) / max(len(subjects), 1)
            national_overall = sum(s["national_average"] for s in subjects) / max(len(subjects), 1)

            return {
                "subjects": subjects,
                "overall": {
                    "user_average": round(user_overall, 1),
                    "national_average": round(national_overall, 1),
                    "difference": round(user_overall - national_overall, 1),
                    "overall_percentile": self._calculate_overall_percentile(user_id)
                }
            }

        except Exception as e:
            logger.error(f"Error getting national comparison: {e}")
            return self._get_default_national_comparison()

    def _calculate_percentile(self, user_id: UUID, subject_id: str) -> int:
        """Calculate user's percentile ranking for a subject."""
        try:
            query = text("""
                WITH user_scores AS (
                    SELECT
                        utm.user_id,
                        AVG(utm.mastery_score) as avg_score
                    FROM user_topic_mastery utm
                    JOIN topics t ON t.id = utm.topic_id
                    WHERE t.subject_id = :subject_id
                    GROUP BY utm.user_id
                ),
                user_rank AS (
                    SELECT
                        user_id,
                        PERCENT_RANK() OVER (ORDER BY avg_score) * 100 as percentile
                    FROM user_scores
                )
                SELECT COALESCE(percentile, 50) FROM user_rank WHERE user_id = :user_id
            """)

            result = self.db.execute(query, {
                "user_id": str(user_id),
                "subject_id": subject_id
            }).fetchone()

            return int(result[0]) if result else 50

        except Exception:
            return 50

    def _calculate_overall_percentile(self, user_id: UUID) -> int:
        """Calculate user's overall percentile ranking."""
        try:
            query = text("""
                WITH user_scores AS (
                    SELECT
                        user_id,
                        AVG(mastery_score) as avg_score
                    FROM user_topic_mastery
                    GROUP BY user_id
                ),
                user_rank AS (
                    SELECT
                        user_id,
                        PERCENT_RANK() OVER (ORDER BY avg_score) * 100 as percentile
                    FROM user_scores
                )
                SELECT COALESCE(percentile, 50) FROM user_rank WHERE user_id = :user_id
            """)

            result = self.db.execute(query, {"user_id": str(user_id)}).fetchone()
            return int(result[0]) if result else 50

        except Exception:
            return 50

    def _get_default_national_comparison(self) -> Dict[str, Any]:
        """Return default comparison data when database query fails."""
        default_subjects = [
            {"subject_id": "1", "subject_name": "Matematicas", "user_mastery": 50, "national_average": 52},
            {"subject_id": "2", "subject_name": "Lectura Critica", "user_mastery": 50, "national_average": 55},
            {"subject_id": "3", "subject_name": "Ciencias Naturales", "user_mastery": 50, "national_average": 48},
            {"subject_id": "4", "subject_name": "Sociales y Ciudadanas", "user_mastery": 50, "national_average": 50},
            {"subject_id": "5", "subject_name": "Ingles", "user_mastery": 50, "national_average": 45},
        ]

        for s in default_subjects:
            s["difference"] = s["user_mastery"] - s["national_average"]
            s["percentile"] = 50
            s["total_users_compared"] = 1000
            s["status"] = "above" if s["difference"] > 0 else ("below" if s["difference"] < 0 else "equal")

        return {
            "subjects": default_subjects,
            "overall": {
                "user_average": 50.0,
                "national_average": 50.0,
                "difference": 0.0,
                "overall_percentile": 50
            }
        }

    def get_historical_stats(self, user_id: UUID, days: int = 90) -> Dict[str, Any]:
        """
        Get historical statistics for the user.
        """
        try:
            # Questions answered over time
            questions_query = text("""
                SELECT
                    DATE(created_at) as date,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct
                FROM practice_answers
                WHERE user_id = :user_id
                AND created_at >= NOW() - INTERVAL :days DAY
                GROUP BY DATE(created_at)
                ORDER BY date
            """)

            questions_result = self.db.execute(questions_query, {
                "user_id": str(user_id),
                "days": days
            }).fetchall()

            # Study time (based on video watch time)
            time_query = text("""
                SELECT
                    DATE(created_at) as date,
                    SUM(watch_time_seconds) / 60 as minutes
                FROM video_progress
                WHERE user_id = :user_id
                AND created_at >= NOW() - INTERVAL :days DAY
                GROUP BY DATE(created_at)
                ORDER BY date
            """)

            time_result = self.db.execute(time_query, {
                "user_id": str(user_id),
                "days": days
            }).fetchall()

            # Build historical data
            questions_history = [
                {
                    "date": row[0].strftime("%Y-%m-%d") if row[0] else "",
                    "total": int(row[1]) if row[1] else 0,
                    "correct": int(row[2]) if row[2] else 0,
                    "accuracy": round((int(row[2]) / int(row[1]) * 100) if row[1] and int(row[1]) > 0 else 0, 1)
                }
                for row in questions_result
            ]

            study_time_history = [
                {
                    "date": row[0].strftime("%Y-%m-%d") if row[0] else "",
                    "minutes": round(float(row[1]), 1) if row[1] else 0
                }
                for row in time_result
            ]

            # Calculate totals
            total_questions = sum(q["total"] for q in questions_history)
            total_correct = sum(q["correct"] for q in questions_history)
            total_study_time = sum(t["minutes"] for t in study_time_history)

            return {
                "questions_history": questions_history,
                "study_time_history": study_time_history,
                "totals": {
                    "total_questions": total_questions,
                    "total_correct": total_correct,
                    "overall_accuracy": round((total_correct / total_questions * 100) if total_questions > 0 else 0, 1),
                    "total_study_minutes": round(total_study_time, 1),
                    "avg_daily_questions": round(total_questions / days, 1),
                    "avg_daily_study_minutes": round(total_study_time / days, 1)
                }
            }

        except Exception as e:
            logger.error(f"Error getting historical stats: {e}")
            return {
                "questions_history": [],
                "study_time_history": [],
                "totals": {
                    "total_questions": 0,
                    "total_correct": 0,
                    "overall_accuracy": 0,
                    "total_study_minutes": 0,
                    "avg_daily_questions": 0,
                    "avg_daily_study_minutes": 0
                }
            }
