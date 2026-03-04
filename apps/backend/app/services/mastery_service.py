"""
Service for Mastery Management - ICFES Leveling

This service handles the business logic for calculating and retrieving
user mastery data, including topic mastery, weak areas, and radar chart data.

LOGICA_DE_NEGOCIO.md Mastery Tree System:
- Prerequisites: Topics have dependencies that must be mastered first
- Decay: Mastery decreases over time if not practiced (spaced repetition)
- Unlock Validation: Check prerequisites before allowing practice
"""

import logging
import math
from uuid import UUID
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from ..models import (
    User,
    Topic,
    Subject,
    UserTopicMastery,
)
from ..models.mobile_offline import UserTopicMastery

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS FOR MASTERY SYSTEM (LOGICA_DE_NEGOCIO.md)
# =============================================================================

# Mastery thresholds
MASTERY_LOCKED = 0.0        # Not yet unlocked
MASTERY_BEGINNER = 0.3      # Just started
MASTERY_DEVELOPING = 0.5    # In progress
MASTERY_PROFICIENT = 0.7    # Good understanding
MASTERY_MASTER = 0.9        # Mastered

# Prerequisites unlock threshold (60% mastery required)
PREREQUISITE_UNLOCK_THRESHOLD = 0.6

# Decay system parameters (spaced repetition)
DECAY_START_DAYS = 3        # Start decay after 3 days of no practice
DECAY_RATE_PER_DAY = 0.02   # 2% decay per day
DECAY_MINIMUM = 0.1         # Never decay below 10% (preserve some memory)
DECAY_CAP_DAYS = 30         # Maximum decay period (60% total decay max)

# Learning rate
LEARNING_RATE_CORRECT = 0.12     # Faster learning for correct answers
LEARNING_RATE_INCORRECT = 0.06  # Slower penalty for incorrect


# =============================================================================
# TOPIC PREREQUISITES MAPPING (ICFES Subjects)
# =============================================================================
# Format: topic_id -> list of prerequisite topic_ids
# This should ideally be stored in database, but for now defined here

TOPIC_PREREQUISITES: Dict[str, List[str]] = {
    # Matemáticas - Sequential topics
    "algebra_basica": [],
    "algebra_intermedia": ["algebra_basica"],
    "algebra_avanzada": ["algebra_intermedia"],
    "geometria_basica": [],
    "geometria_analitica": ["geometria_basica", "algebra_basica"],
    "trigonometria": ["geometria_basica", "algebra_basica"],
    "calculo_diferencial": ["algebra_avanzada", "trigonometria"],
    "estadistica_basica": ["algebra_basica"],
    "estadistica_inferencial": ["estadistica_basica"],
    "probabilidad": ["estadistica_basica"],

    # Lectura Crítica - Progressive comprehension
    "comprension_literal": [],
    "comprension_inferencial": ["comprension_literal"],
    "comprension_critica": ["comprension_inferencial"],
    "analisis_argumentativo": ["comprension_critica"],
    "intertextualidad": ["analisis_argumentativo"],

    # Ciencias Naturales - Foundation to advanced
    "biologia_celular": [],
    "biologia_organismos": ["biologia_celular"],
    "ecologia": ["biologia_organismos"],
    "quimica_basica": [],
    "quimica_organica": ["quimica_basica"],
    "fisica_mecanica": [],
    "fisica_ondas": ["fisica_mecanica"],
    "fisica_electromagnetismo": ["fisica_ondas"],

    # Sociales y Ciudadanas
    "historia_colombia": [],
    "historia_mundial": ["historia_colombia"],
    "geografia_fisica": [],
    "geografia_humana": ["geografia_fisica"],
    "economia_basica": [],
    "ciencias_politicas": ["historia_colombia", "economia_basica"],
    "constitucion_ciudadania": ["ciencias_politicas"],

    # Inglés - Progressive skills
    "ingles_vocabulario": [],
    "ingles_gramatica_basica": ["ingles_vocabulario"],
    "ingles_gramatica_avanzada": ["ingles_gramatica_basica"],
    "ingles_comprension_lectora": ["ingles_gramatica_basica"],
    "ingles_expresion_escrita": ["ingles_gramatica_avanzada", "ingles_comprension_lectora"],
}

class MasteryService:
    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # PREREQUISITES SYSTEM (LOGICA_DE_NEGOCIO.md)
    # =========================================================================

    def check_prerequisites(self, user_id: UUID, topic_id: str) -> Tuple[bool, List[Dict]]:
        """
        Check if a user has met the prerequisites for a topic.

        Returns:
            Tuple of (is_unlocked, missing_prerequisites)
            - is_unlocked: True if all prerequisites are met
            - missing_prerequisites: List of prerequisites not yet met with their status
        """
        # Get prerequisites for this topic
        prerequisites = TOPIC_PREREQUISITES.get(topic_id, [])

        if not prerequisites:
            return True, []

        missing = []
        for prereq_id in prerequisites:
            # Check user's mastery of prerequisite
            mastery = self.db.query(UserTopicMastery).filter(
                and_(
                    UserTopicMastery.user_id == user_id,
                    UserTopicMastery.topic_id == prereq_id
                )
            ).first()

            current_score = mastery.mastery_score if mastery else 0.0

            if current_score < PREREQUISITE_UNLOCK_THRESHOLD:
                # Get topic name
                topic = self.db.query(Topic).filter(Topic.id == prereq_id).first()
                topic_name = topic.name if topic else prereq_id

                missing.append({
                    "topic_id": prereq_id,
                    "topic_name": topic_name,
                    "current_mastery": round(current_score, 2),
                    "required_mastery": PREREQUISITE_UNLOCK_THRESHOLD,
                    "progress_percent": round((current_score / PREREQUISITE_UNLOCK_THRESHOLD) * 100, 1)
                })

        return len(missing) == 0, missing

    def get_unlockable_topics(self, user_id: UUID, subject_id: Optional[UUID] = None) -> List[Dict]:
        """
        Get list of topics that are close to being unlocked.
        Useful for showing "almost there" progress indicators.
        """
        unlockable = []

        # Get all topics (optionally filtered by subject)
        query = self.db.query(Topic)
        if subject_id:
            query = query.filter(Topic.subject_id == subject_id)

        topics = query.all()

        for topic in topics:
            topic_id = str(topic.id)
            is_unlocked, missing = self.check_prerequisites(user_id, topic_id)

            if not is_unlocked and missing:
                # Calculate overall progress to unlock
                total_progress = sum(p["progress_percent"] for p in missing) / len(missing)

                if total_progress >= 50:  # Only show if at least 50% there
                    unlockable.append({
                        "topic_id": topic_id,
                        "topic_name": topic.name,
                        "subject_id": str(topic.subject_id),
                        "unlock_progress": round(total_progress, 1),
                        "missing_prerequisites": missing
                    })

        return sorted(unlockable, key=lambda x: x["unlock_progress"], reverse=True)

    def validate_can_practice(self, user_id: UUID, topic_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a user can practice a topic.

        Returns:
            Tuple of (can_practice, error_message)
        """
        is_unlocked, missing = self.check_prerequisites(user_id, topic_id)

        if not is_unlocked:
            prereq_names = [p["topic_name"] for p in missing[:3]]  # Show first 3
            message = f"Primero debes dominar: {', '.join(prereq_names)}"
            return False, message

        return True, None

    # =========================================================================
    # DECAY SYSTEM (LOGICA_DE_NEGOCIO.md - Spaced Repetition)
    # =========================================================================

    def calculate_decay(self, last_practiced: datetime, current_mastery: float) -> float:
        """
        Calculate mastery decay based on time since last practice.

        Formula: decay = rate_per_day * min(days_inactive - start_days, cap_days)
        Applied only if mastery > DECAY_MINIMUM
        """
        if last_practiced is None:
            return 0.0

        days_inactive = (datetime.utcnow() - last_practiced).days

        # No decay within grace period
        if days_inactive <= DECAY_START_DAYS:
            return 0.0

        # Calculate decay days (capped)
        decay_days = min(days_inactive - DECAY_START_DAYS, DECAY_CAP_DAYS)

        # Calculate decay amount
        decay = DECAY_RATE_PER_DAY * decay_days

        # Don't decay below minimum
        if current_mastery - decay < DECAY_MINIMUM:
            decay = max(0, current_mastery - DECAY_MINIMUM)

        return decay

    def apply_decay_to_user(self, user_id: UUID) -> Dict:
        """
        Apply decay to all of a user's topic masteries.
        Called on login or when fetching mastery data.

        Returns:
            Dictionary with decay statistics
        """
        now = datetime.utcnow()
        topics_decayed = 0
        total_decay = 0.0

        masteries = self.db.query(UserTopicMastery).filter(
            UserTopicMastery.user_id == user_id
        ).all()

        for mastery in masteries:
            if mastery.last_practiced_at and mastery.mastery_score > DECAY_MINIMUM:
                decay = self.calculate_decay(mastery.last_practiced_at, mastery.mastery_score)

                if decay > 0:
                    old_score = mastery.mastery_score
                    mastery.mastery_score = max(DECAY_MINIMUM, mastery.mastery_score - decay)
                    mastery.decay_applied_at = now

                    topics_decayed += 1
                    total_decay += (old_score - mastery.mastery_score)

                    logger.debug(
                        f"Applied decay to topic {mastery.topic_id}: "
                        f"{old_score:.2f} -> {mastery.mastery_score:.2f}"
                    )

        if topics_decayed > 0:
            self.db.flush()

        return {
            "topics_decayed": topics_decayed,
            "total_decay": round(total_decay, 3),
            "applied_at": now.isoformat()
        }

    def get_topics_needing_review(self, user_id: UUID, limit: int = 10) -> List[Dict]:
        """
        Get topics that need review based on decay risk.
        Prioritizes topics that are about to decay significantly.
        """
        now = datetime.utcnow()
        decay_threshold_date = now - timedelta(days=DECAY_START_DAYS)

        topics_at_risk = self.db.query(
            UserTopicMastery, Topic
        ).join(Topic, UserTopicMastery.topic_id == Topic.id
        ).filter(
            and_(
                UserTopicMastery.user_id == user_id,
                UserTopicMastery.mastery_score > DECAY_MINIMUM,
                UserTopicMastery.last_practiced_at < decay_threshold_date
            )
        ).order_by(UserTopicMastery.last_practiced_at.asc()
        ).limit(limit).all()

        result = []
        for mastery, topic in topics_at_risk:
            days_since = (now - mastery.last_practiced_at).days
            potential_decay = self.calculate_decay(mastery.last_practiced_at, mastery.mastery_score)

            result.append({
                "topic_id": str(topic.id),
                "topic_name": topic.name,
                "current_mastery": round(mastery.mastery_score, 2),
                "potential_decay": round(potential_decay, 2),
                "days_since_practice": days_since,
                "urgency": "high" if days_since > 14 else "medium" if days_since > 7 else "low"
            })

        return result

    # =========================================================================
    # ORIGINAL METHODS (with decay integration)
    # =========================================================================

    def get_topics_mastery(self, user_id: UUID, subject_id: Optional[UUID] = None, apply_decay: bool = True) -> dict:
        """
        Retrieves a list of topics with their mastery scores for a user.
        Includes unlock status and decay information.
        """
        # Apply decay first if requested
        decay_info = None
        if apply_decay:
            decay_info = self.apply_decay_to_user(user_id)

        query = self.db.query(
            UserTopicMastery,
            Topic,
            Subject
        ).join(Topic, UserTopicMastery.topic_id == Topic.id
        ).join(Subject, Topic.subject_id == Subject.id
        ).filter(UserTopicMastery.user_id == user_id)

        if subject_id:
            query = query.filter(Topic.subject_id == subject_id)

        results = query.order_by(Subject.name, Topic.name).all()

        topics_list = []
        for utm, topic, subject in results:
            topic_id = str(topic.id)
            days_since_last = None
            if utm.last_practiced_at:
                days_since_last = (datetime.utcnow() - utm.last_practiced_at).days

            # Calculate next review days based on: mastery * 7
            next_review_in_days = 0
            if utm.mastery_score > 0:
                next_review_in_days = int(utm.mastery_score * 7)

            # Check unlock status
            is_unlocked, missing_prereqs = self.check_prerequisites(user_id, topic_id)

            # Calculate decay risk
            decay_risk = "none"
            if days_since_last and days_since_last > DECAY_START_DAYS:
                if days_since_last > 14:
                    decay_risk = "high"
                elif days_since_last > 7:
                    decay_risk = "medium"
                else:
                    decay_risk = "low"

            # Determine mastery level
            mastery_level = "locked"
            if utm.mastery_score >= MASTERY_MASTER:
                mastery_level = "master"
            elif utm.mastery_score >= MASTERY_PROFICIENT:
                mastery_level = "proficient"
            elif utm.mastery_score >= MASTERY_DEVELOPING:
                mastery_level = "developing"
            elif utm.mastery_score >= MASTERY_BEGINNER:
                mastery_level = "beginner"
            elif utm.mastery_score > 0:
                mastery_level = "started"

            topics_list.append({
                "id": topic.id,
                "name": topic.name,
                "subject_id": subject.id,
                "subject_name": subject.name,
                "mastery_score": round(utm.mastery_score, 3),
                "mastery_level": mastery_level,
                "questions_seen": utm.questions_seen,
                "questions_correct": utm.questions_correct,
                "last_practiced_at": utm.last_practiced_at,
                "days_since_last": days_since_last,
                "status": utm.status,
                "next_review_in_days": next_review_in_days,
                "is_unlocked": is_unlocked,
                "missing_prerequisites": missing_prereqs if not is_unlocked else [],
                "decay_risk": decay_risk,
            })

        return {
            "topics": topics_list,
            "decay_applied": decay_info,
            "total_topics": len(topics_list),
            "mastered_count": sum(1 for t in topics_list if t["mastery_level"] == "master"),
            "locked_count": sum(1 for t in topics_list if not t["is_unlocked"]),
        }

    def get_weak_areas(self, user_id: UUID) -> dict:
        """
        Identifies the user's weakest areas based on mastery scores.
        """
        # A weak area is a topic with a mastery score below a threshold (e.g., 0.5)
        weak_area_threshold = 0.5
        
        query = self.db.query(
            UserTopicMastery,
            Topic,
            Subject
        ).join(Topic, UserTopicMastery.topic_id == Topic.id
        ).join(Subject, Topic.subject_id == Subject.id
        ).filter(
            UserTopicMastery.user_id == user_id,
            UserTopicMastery.mastery_score < weak_area_threshold
        ).order_by(UserTopicMastery.mastery_score.asc()) # Lowest score first

        results = query.limit(10).all() # Get top 10 weakest areas

        weak_areas_list = []
        for utm, topic, subject in results:
            priority = "high"
            if utm.mastery_score > 0.35:
                priority = "medium"
            elif utm.mastery_score > 0.2:
                priority = "low"

            weak_areas_list.append({
                "topic_id": topic.id,
                "topic_name": topic.name,
                "subject_id": subject.id,
                "subject_name": subject.name,
                "mastery_score": utm.mastery_score,
                "priority": priority,
                "suggested_practice": 5 # Suggested number of questions to practice
            })
            
        return {"weak_areas": weak_areas_list}


    def get_radar_chart_data(self, user_id: UUID) -> dict:
        """
        Aggregates mastery data per subject for the radar chart.
        """
        # Subquery to get average mastery and mastered topics per subject
        mastery_subquery = self.db.query(
            Topic.subject_id,
            func.avg(UserTopicMastery.mastery_score).label("overall_mastery"),
            func.count(UserTopicMastery.topic_id).filter(UserTopicMastery.mastery_score >= 0.7).label("topics_mastered")
        ).join(Topic, UserTopicMastery.topic_id == Topic.id
        ).filter(UserTopicMastery.user_id == user_id
        ).group_by(Topic.subject_id).subquery()

        # Subquery to get total topics per subject
        total_topics_subquery = self.db.query(
            Topic.subject_id,
            func.count(Topic.id).label("topics_total")
        ).group_by(Topic.subject_id).subquery()

        # Main query to join everything
        results = self.db.query(
            Subject,
            mastery_subquery.c.overall_mastery,
            mastery_subquery.c.topics_mastered,
            total_topics_subquery.c.topics_total
        ).outerjoin(mastery_subquery, Subject.id == mastery_subquery.c.subject_id
        ).outerjoin(total_topics_subquery, Subject.id == total_topics_subquery.c.subject_id
        ).order_by(Subject.name).all()

        subjects_list = []
        for subject, overall_mastery, topics_mastered, topics_total in results:
            subjects_list.append({
                "subject_id": subject.id,
                "subject_name": subject.name,
                "overall_mastery": overall_mastery or 0.0,
                "topics_mastered": topics_mastered or 0,
                "topics_total": topics_total or 0,
            })
            
        return {"subjects": subjects_list}

    @staticmethod
    def update_topic_mastery(db: Session, user_id: UUID, topic_id: UUID, is_correct: bool) -> dict:
        """
        Update topic mastery based on answer correctness.
        """
        LEARNING_RATE = 0.1
        try:
            topic_mastery = db.query(UserTopicMastery).filter(
                and_(UserTopicMastery.user_id == user_id, UserTopicMastery.topic_id == topic_id)
            ).first()

            if not topic_mastery:
                topic_mastery = UserTopicMastery(user_id=user_id, topic_id=topic_id, mastery_score=0.0)
                db.add(topic_mastery)

            old_score = topic_mastery.mastery_score
            topic_mastery.questions_seen = (topic_mastery.questions_seen or 0) + 1
            if is_correct:
                topic_mastery.questions_correct = (topic_mastery.questions_correct or 0) + 1
                topic_mastery.consecutive_correct = (topic_mastery.consecutive_correct or 0) + 1
                topic_mastery.mastery_score += (1.0 - topic_mastery.mastery_score) * LEARNING_RATE
            else:
                topic_mastery.consecutive_correct = 0
                topic_mastery.mastery_score -= topic_mastery.mastery_score * LEARNING_RATE * 0.5
            
            topic_mastery.mastery_score = max(0.0, min(1.0, topic_mastery.mastery_score))
            topic_mastery.last_practiced_at = datetime.utcnow()
            days_until_review = max(1, int(topic_mastery.mastery_score * 7))
            topic_mastery.next_review_at = datetime.utcnow() + timedelta(days=days_until_review)
            
            db.flush()
            return {
                "topic_id": str(topic_id), "old_score": round(old_score, 3), "new_score": round(topic_mastery.mastery_score, 3),
                "questions_seen": topic_mastery.questions_seen, "questions_correct": topic_mastery.questions_correct,
                "consecutive_correct": topic_mastery.consecutive_correct, "status": topic_mastery.status
            }
        except Exception as e:
            logger.error(f"Error updating topic mastery: {e}")
            return {"topic_id": str(topic_id), "old_score": 0.0, "new_score": 0.0, "error": str(e)}

    @staticmethod
    def get_topic_mastery(db: Session, user_id: UUID, topic_id: UUID) -> Optional[dict]:
        """
        Get current topic mastery for a user.
        """
        try:
            topic_mastery = db.query(UserTopicMastery).filter(
                and_(UserTopicMastery.user_id == user_id, UserTopicMastery.topic_id == topic_id)
            ).first()
            if not topic_mastery:
                return {"topic_id": str(topic_id), "mastery_score": 0.0, "questions_seen": 0, "questions_correct": 0, "status": "new"}
            return {
                "topic_id": str(topic_id), "mastery_score": round(topic_mastery.mastery_score, 3),
                "questions_seen": topic_mastery.questions_seen, "questions_correct": topic_mastery.questions_correct,
                "consecutive_correct": topic_mastery.consecutive_correct,
                "last_practiced_at": topic_mastery.last_practiced_at.isoformat() if topic_mastery.last_practiced_at else None,
                "next_review_at": topic_mastery.next_review_at.isoformat() if topic_mastery.next_review_at else None,
                "status": topic_mastery.status
            }
        except Exception as e:
            logger.error(f"Error getting topic mastery: {e}")
            return None
