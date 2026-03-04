"""
Mobile Service - Core business logic for ICFES Leveling Mobile App
Handles: Questions, Answers, Hearts, Streaks, Sync, Mastery
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, text, and_, or_
from typing import Optional, List, Tuple
from datetime import datetime, date, timedelta, timezone
from uuid import UUID
import logging

from ..models import (
    User, Question, Topic, Subject,
    UserQuestionHistory, UserTopicMastery, PendingAnswerSync,
    HeartTransaction, UserDailyActivity, StreakFreeze
)
from ..models.mobile_offline import UserLeague, LeagueGroup, LeagueWeek
from ..schemas.mobile import (
    SyncAction, ServerState, SyncFailedItem,
    MasteryUpdate, StreakUpdate, TopicMasteryInfo, WeakAreaInfo
)

logger = logging.getLogger(__name__)


class MobileService:
    """Service for mobile app business logic"""

    # Constants
    HEART_REGEN_HOURS = 4
    DEFAULT_HEARTS = 5
    DEFAULT_DAILY_GOAL_XP = 20
    XP_PER_CORRECT_ANSWER = 10
    XP_PER_WRONG_ANSWER = 2

    def __init__(self, db: Session):
        self.db = db

    # ============================================
    # QUESTIONS
    # ============================================

    def get_next_adaptive_question(
        self,
        user_id: UUID,
        subject_id: Optional[UUID] = None
    ) -> Optional[Question]:
        """Get next question using adaptive algorithm"""
        # Use the SQL function
        result = self.db.execute(
            text("SELECT get_next_adaptive_question(:user_id, :subject_id)"),
            {"user_id": str(user_id), "subject_id": str(subject_id) if subject_id else None}
        )
        question_id = result.scalar()

        if not question_id:
            # Fallback: get any random question
            query = self.db.query(Question)
            if subject_id:
                query = query.join(Topic).filter(Topic.subject_id == subject_id)
            return query.order_by(func.random()).first()

        return self.db.query(Question).filter(Question.id == question_id).first()

    def get_question_batch(
        self,
        user_id: UUID,
        limit: int = 50,
        subject_id: Optional[UUID] = None
    ) -> List[Question]:
        """Get batch of questions for offline cache"""
        # Get questions user hasn't seen recently
        subquery = self.db.query(UserQuestionHistory.question_id).filter(
            UserQuestionHistory.user_id == user_id,
            UserQuestionHistory.created_at > datetime.now(timezone.utc) - timedelta(days=7)
        ).subquery()

        query = self.db.query(Question).outerjoin(
            subquery, Question.id == subquery.c.question_id
        ).filter(subquery.c.question_id == None)

        if subject_id:
            query = query.join(Topic).filter(Topic.subject_id == subject_id)

        questions = query.order_by(func.random()).limit(limit).all()

        # If not enough, include some seen questions
        if len(questions) < limit:
            remaining = limit - len(questions)
            seen_ids = [q.id for q in questions]

            more_query = self.db.query(Question)
            if subject_id:
                more_query = more_query.join(Topic).filter(Topic.subject_id == subject_id)
            if seen_ids:
                more_query = more_query.filter(~Question.id.in_(seen_ids))

            more_questions = more_query.order_by(func.random()).limit(remaining).all()
            questions.extend(more_questions)

        return questions

    # ============================================
    # ANSWERS
    # ============================================

    def submit_answer(
        self,
        user_id: UUID,
        question_id: UUID,
        answer_id: str,
        time_spent_seconds: int,
        session_type: str,
        session_id: Optional[UUID] = None
    ) -> Tuple[bool, int, Optional[MasteryUpdate], Optional[StreakUpdate], int]:
        """
        Submit answer and return results. This is now an atomic transaction.
        Returns: (correct, xp_earned, mastery_update, streak_update, hearts_remaining)
        """
        try:
            # Lock the user row for the duration of the transaction
            user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
            if not user:
                raise ValueError("User not found")

            question = self.db.query(Question).filter(Question.id == question_id).first()
            if not question:
                raise ValueError("Question not found")

            # Check if correct
            correct_answer = getattr(question, 'respuesta_correcta', None) or question.correct_answer
            correct = answer_id.upper() == (correct_answer or '').upper()

            # Calculate XP
            xp_earned = self.XP_PER_CORRECT_ANSWER if correct else self.XP_PER_WRONG_ANSWER

            # Record in history
            history = UserQuestionHistory(
                user_id=user_id, question_id=question_id, was_correct=correct,
                time_spent_seconds=time_spent_seconds, session_type=session_type,
                session_id=session_id, synced_at=datetime.now(timezone.utc)
            )
            self.db.add(history)

            # Update mastery
            mastery_update = self._update_topic_mastery(user_id, question.topic_id, correct)

            # Update user XP
            user.experience = (user.experience or 0) + xp_earned

            # Actualizar XP de liga semanal
            user_league = self.db.query(UserLeague).join(LeagueGroup).join(LeagueWeek).filter(
                UserLeague.user_id == user_id,
                LeagueWeek.is_active == True
            ).first()
            if user_league:
                user_league.weekly_xp += xp_earned

            # Update daily activity and streak
            streak_update = self._update_daily_activity(user_id, xp_earned, correct)
            
            # Handle heart deduction for incorrect answers
            hearts_status = self.get_hearts_status(user_id)
            hearts_remaining = hearts_status["hearts"]
            if not correct and not hearts_status["is_unlimited"]:
                try:
                    hearts_remaining = self._use_heart_no_commit(user_id, "wrong_answer", question_id)
                except ValueError:
                    # No hearts left, this is fine, user enters grace mode implicitly
                    hearts_remaining = 0
            
            # ATOMIC COMMIT
            self.db.commit()

            return correct, xp_earned, mastery_update, streak_update, hearts_remaining

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during atomic answer submission for user {user_id}: {e}")
            raise

    def _update_topic_mastery(
        self,
        user_id: UUID,
        topic_id: UUID,
        was_correct: bool
    ) -> MasteryUpdate:
        """Update topic mastery score"""
        # Use the SQL function for consistency
        result = self.db.execute(
            text("SELECT update_topic_mastery(:user_id, :topic_id, :was_correct)"),
            {
                "user_id": str(user_id),
                "topic_id": str(topic_id),
                "was_correct": was_correct
            }
        )
        new_score = result.scalar() or 0.0

        # Get old score for response
        mastery = self.db.query(UserTopicMastery).filter(
            UserTopicMastery.user_id == user_id,
            UserTopicMastery.topic_id == topic_id
        ).first()

        old_score = 0.0
        if mastery:
            old_score = mastery.mastery_score - (0.3 if was_correct else 0.0)  # Approximate

        return MasteryUpdate(
            topic_id=topic_id,
            old_score=max(0, old_score),
            new_score=new_score
        )

    def _update_daily_activity(
        self,
        user_id: UUID,
        xp_earned: int,
        was_correct: bool
    ) -> StreakUpdate:
        """Update daily activity and check streak"""
        today = date.today()
        user = self.db.query(User).filter(User.id == user_id).with_for_update().first()

        # Get or create daily activity
        activity = self.db.query(UserDailyActivity).filter(
            UserDailyActivity.user_id == user_id,
            UserDailyActivity.activity_date == today
        ).first()

        first_today = activity is None

        if not activity:
            activity = UserDailyActivity(
                user_id=user_id,
                activity_date=today,
                first_session_at=datetime.now(timezone.utc)
            )
            self.db.add(activity)

        # Update activity
        activity.xp_earned = (activity.xp_earned or 0) + xp_earned
        activity.questions_answered = (activity.questions_answered or 0) + 1
        if was_correct:
            activity.correct_answers = (activity.correct_answers or 0) + 1
        activity.last_session_at = datetime.now(timezone.utc)

        # Check daily goal
        daily_goal = user.daily_goal_xp if user else self.DEFAULT_DAILY_GOAL_XP
        goal_met = activity.xp_earned >= daily_goal
        activity.daily_goal_met = goal_met

        # Update streak if goal met for first time today
        streak_extended = False
        current_streak = user.current_streak if user else 0

        if goal_met and not activity.streak_extended:
            activity.streak_extended = True
            streak_extended = True

            if user:
                # Check if streak continues or resets
                yesterday = today - timedelta(days=1)
                if user.last_activity_date == yesterday or user.last_activity_date == today:
                    user.current_streak = (user.current_streak or 0) + 1
                else:
                    user.current_streak = 1

                user.longest_streak = max(user.longest_streak or 0, user.current_streak)
                user.last_activity_date = today
                current_streak = user.current_streak

        return StreakUpdate(
            current=current_streak,
            extended=streak_extended,
            daily_goal_met=goal_met
        )

    # ============================================
    # SYNC
    # ============================================

    def sync_answers(
        self,
        user_id: UUID,
        actions: List[SyncAction]
    ) -> Tuple[int, List[SyncFailedItem], ServerState]:
        """Process offline answer sync with server-side answer validation.

        SECURITY: Never trust client-side was_correct field.
        Always validate the answer server-side by comparing against
        the question's correct answer in the database.
        """
        synced_count = 0
        failed = []

        for action in actions:
            try:
                # Check for duplicate
                existing = self.db.query(UserQuestionHistory).filter(
                    UserQuestionHistory.user_id == user_id,
                    UserQuestionHistory.question_id == action.question_id,
                    UserQuestionHistory.client_timestamp == action.client_timestamp
                ).first()

                if existing:
                    synced_count += 1
                    continue

                # SECURITY FIX: Look up the question to validate the answer server-side
                # Never trust client-provided was_correct field
                question = self.db.query(Question).filter(
                    Question.id == action.question_id
                ).first()

                if not question:
                    failed.append(SyncFailedItem(
                        id=action.id,
                        error=f"Question not found: {action.question_id}"
                    ))
                    continue

                # Get the correct answer - use respuesta_correcta (ICFES format) or correct_answer (legacy)
                correct_answer = (
                    getattr(question, 'respuesta_correcta', None) or
                    question.correct_answer or
                    ''
                )

                # SECURITY: Validate answer server-side
                # Normalize both answers to uppercase for comparison (A, B, C, D)
                submitted_answer = (action.answer_id or '').strip().upper()
                expected_answer = correct_answer.strip().upper()
                was_correct_validated = submitted_answer == expected_answer

                # Log if client sent incorrect was_correct value (potential cheating attempt)
                if action.was_correct != was_correct_validated:
                    logger.warning(
                        f"Answer validation mismatch for user={user_id}, question={action.question_id}: "
                        f"client claimed was_correct={action.was_correct}, "
                        f"server validated was_correct={was_correct_validated}, "
                        f"submitted={submitted_answer}, expected={expected_answer}"
                    )

                # Record answer with SERVER-VALIDATED correctness
                history = UserQuestionHistory(
                    user_id=user_id,
                    question_id=action.question_id,
                    was_correct=was_correct_validated,  # Use server-validated value, not client value
                    time_spent_seconds=action.time_spent_seconds,
                    session_type=action.session_type.value if action.session_type else None,
                    client_timestamp=action.client_timestamp,
                    synced_at=datetime.now(timezone.utc)
                )
                self.db.add(history)

                # Update mastery with SERVER-VALIDATED correctness
                self.db.execute(
                    text("SELECT update_topic_mastery(:user_id, :topic_id, :was_correct)"),
                    {
                        "user_id": str(user_id),
                        "topic_id": str(question.topic_id),
                        "was_correct": was_correct_validated  # Use server-validated value
                    }
                )

                synced_count += 1

            except Exception as e:
                logger.error(f"Failed to sync action {action.id}: {e}")
                failed.append(SyncFailedItem(id=action.id, error=str(e)))

        self.db.commit()

        # Get current server state
        server_state = self.get_server_state(user_id)

        return synced_count, failed, server_state

    def get_server_state(self, user_id: UUID) -> ServerState:
        """Get current server state for user"""
        user = self.db.query(User).filter(User.id == user_id).first()

        today_activity = self.db.query(UserDailyActivity).filter(
            UserDailyActivity.user_id == user_id,
            UserDailyActivity.activity_date == date.today()
        ).first()

        return ServerState(
            xp=user.experience if user else 0,
            level=user.level if user else 1,
            hearts=getattr(user, 'hearts', self.DEFAULT_HEARTS) if user else self.DEFAULT_HEARTS,
            streak=getattr(user, 'current_streak', 0) if user else 0,
            last_activity_date=getattr(user, 'last_activity_date', None) if user else None
        )

    # ============================================
    # HEARTS
    # ============================================

    def get_hearts_status(self, user_id: UUID) -> dict:
        """Get current hearts status"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        hearts = getattr(user, 'hearts', self.DEFAULT_HEARTS)
        max_hearts = getattr(user, 'max_hearts', self.DEFAULT_HEARTS)
        last_regen = getattr(user, 'hearts_last_regeneration', datetime.now(timezone.utc))
        unlimited_until = getattr(user, 'unlimited_hearts_until', None)

        # Calculate next regeneration
        next_regen_at = None
        if hearts < max_hearts:
            next_regen_at = last_regen + timedelta(hours=self.HEART_REGEN_HOURS)

        is_unlimited = bool(unlimited_until and unlimited_until > datetime.now(timezone.utc))

        return {
            "hearts": hearts or self.DEFAULT_HEARTS,
            "max_hearts": max_hearts or self.DEFAULT_HEARTS,
            "next_regen_at": next_regen_at,
            "unlimited_until": unlimited_until,
            "is_unlimited": is_unlimited
        }

    def _use_heart_no_commit(self, user_id: UUID, reason: str, source_id: Optional[UUID]) -> int:
        """Internal method to use a heart without committing."""
        user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
        if not user:
            raise ValueError("User not found")

        unlimited_until = getattr(user, 'unlimited_hearts_until', None)
        if unlimited_until and unlimited_until > datetime.now(timezone.utc):
            return getattr(user, 'hearts', self.DEFAULT_HEARTS)

        hearts = getattr(user, 'hearts', self.DEFAULT_HEARTS)
        if hearts <= 0:
            raise ValueError("No hearts available")

        new_hearts = hearts - 1
        user.hearts = new_hearts

        transaction = HeartTransaction(
            user_id=user_id, transaction_type="lost", amount=-1,
            hearts_after=new_hearts, source_id=source_id, source_type=reason
        )
        self.db.add(transaction)
        
        return new_hearts

    def use_heart(
        self,
        user_id: UUID,
        reason: str = "wrong_answer",
        source_id: Optional[UUID] = None
    ) -> int:
        """Use a heart, returns remaining hearts"""
        remaining_hearts = self._use_heart_no_commit(user_id, reason, source_id)
        self.db.commit()
        return remaining_hearts

    def regenerate_hearts(self, user_id: UUID) -> int:
        """Check and regenerate hearts based on time - Python implementation"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return self.DEFAULT_HEARTS

            current_hearts = getattr(user, 'hearts', None) or self.DEFAULT_HEARTS
            max_hearts = getattr(user, 'max_hearts', self.DEFAULT_HEARTS)

            # If already at max, no regeneration needed
            if current_hearts >= max_hearts:
                return current_hearts

            # Check last regeneration time
            last_regen = getattr(user, 'hearts_last_regeneration', None)
            if not last_regen:
                return current_hearts

            # Ensure timezone awareness
            if last_regen.tzinfo is None:
                last_regen = last_regen.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            hours_passed = (now - last_regen).total_seconds() / 3600

            # Calculate hearts to regenerate (1 heart per HEART_REGEN_HOURS)
            hearts_to_add = int(hours_passed / self.HEART_REGEN_HOURS)

            if hearts_to_add > 0:
                new_hearts = min(current_hearts + hearts_to_add, max_hearts)
                user.hearts = new_hearts
                user.hearts_last_regeneration = now
                self.db.commit()
                return new_hearts

            return current_hearts
        except Exception as e:
            logger.warning(f"Error regenerating hearts: {e}")
            return self.DEFAULT_HEARTS

    def refill_hearts(
        self,
        user_id: UUID,
        method: str,
        gems_spent: Optional[int] = None
    ) -> Tuple[int, Optional[int]]:
        """Refill hearts, returns (hearts, gems_remaining)"""
        user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
        if not user:
            raise ValueError("User not found")

        max_hearts = getattr(user, 'max_hearts', self.DEFAULT_HEARTS)

        if method == "gems" and gems_spent:
            # Check gems
            current_gems = user.crystals or 0
            if current_gems < gems_spent:
                raise ValueError("Not enough gems")
            user.crystals = current_gems - gems_spent

        # Refill hearts
        user.hearts = max_hearts
        user.hearts_last_regeneration = datetime.now(timezone.utc)

        # Log transaction
        transaction = HeartTransaction(
            user_id=user_id,
            transaction_type="refilled" if method == "gems" else "rewarded",
            amount=max_hearts - (getattr(user, 'hearts', 0) or 0),
            hearts_after=max_hearts,
            source_type=method
        )
        self.db.add(transaction)
        self.db.commit()

        return max_hearts, user.crystals

    # ============================================
    # STREAKS
    # ============================================

    # Streak multipliers based on streak days
    STREAK_MULTIPLIERS = {
        (1, 6): 1.0,
        (7, 13): 1.2,
        (14, 29): 1.5,
        (30, float('inf')): 2.0
    }

    # Streak repair window in hours
    REPAIR_WINDOW_HOURS = 24

    def get_streak_multiplier(self, streak_days: int) -> float:
        """Get XP multiplier based on streak days"""
        for (min_days, max_days), multiplier in self.STREAK_MULTIPLIERS.items():
            if min_days <= streak_days <= max_days:
                return multiplier
        return 1.0

    def get_streak_status(self, user_id: UUID) -> dict:
        """Get current streak status with timezone awareness and repair info"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")

        # Get user timezone
        user_timezone = getattr(user, 'timezone', 'America/Bogota') or 'America/Bogota'

        today = date.today()
        today_activity = self.db.query(UserDailyActivity).filter(
            UserDailyActivity.user_id == user_id,
            UserDailyActivity.activity_date == today
        ).first()

        # Count available freezes
        freezes = self.db.query(StreakFreeze).filter(
            StreakFreeze.user_id == user_id,
            StreakFreeze.is_used == False,
            or_(
                StreakFreeze.expires_at == None,
                StreakFreeze.expires_at > datetime.now(timezone.utc)
            )
        ).count()

        current_streak = getattr(user, 'current_streak', 0) or 0
        last_activity = getattr(user, 'last_activity_date', None)
        daily_goal = getattr(user, 'daily_goal_xp', self.DEFAULT_DAILY_GOAL_XP) or self.DEFAULT_DAILY_GOAL_XP

        # Check if at risk (hasn't practiced today and has streak)
        at_risk = current_streak > 0 and last_activity != today

        # Get streak multiplier
        multiplier = self.get_streak_multiplier(current_streak)

        # Check if can repair streak
        can_repair = False
        repair_window_ends_at = None
        streak_lost_at = getattr(user, 'streak_lost_at', None)

        if streak_lost_at:
            hours_since_lost = (datetime.now(timezone.utc) - streak_lost_at).total_seconds() / 3600
            if hours_since_lost <= self.REPAIR_WINDOW_HOURS:
                can_repair = True
                repair_window_ends_at = streak_lost_at + timedelta(hours=self.REPAIR_WINDOW_HOURS)

        return {
            "current": current_streak,
            "longest": getattr(user, 'longest_streak', 0) or 0,
            "today_xp": today_activity.xp_earned if today_activity else 0,
            "daily_goal": daily_goal,
            "goal_met": today_activity.daily_goal_met if today_activity else False,
            "last_activity_date": last_activity,
            "freezes_available": freezes,
            "at_risk": at_risk,
            "day_resets_at": "04:00",  # 4 AM local time
            "timezone": user_timezone,
            "multiplier": multiplier,
            "can_repair": can_repair,
            "repair_window_ends_at": repair_window_ends_at
        }

    def use_streak_freeze(self, user_id: UUID) -> Tuple[int, date]:
        """Use a streak freeze, returns (remaining_freezes, freeze_date)"""
        # Find available freeze
        freeze = self.db.query(StreakFreeze).filter(
            StreakFreeze.user_id == user_id,
            StreakFreeze.is_used == False,
            or_(
                StreakFreeze.expires_at == None,
                StreakFreeze.expires_at > datetime.now(timezone.utc)
            )
        ).first()

        if not freeze:
            raise ValueError("No streak freezes available")

        freeze.is_used = True
        freeze.used_at = datetime.now(timezone.utc)
        freeze.used_for_date = date.today()

        # Count remaining
        remaining = self.db.query(StreakFreeze).filter(
            StreakFreeze.user_id == user_id,
            StreakFreeze.is_used == False,
            or_(
                StreakFreeze.expires_at == None,
                StreakFreeze.expires_at > datetime.now(timezone.utc)
            )
        ).count()

        self.db.commit()

        return remaining, freeze.used_for_date

    # ============================================
    # MASTERY
    # ============================================

    def get_topic_mastery(
        self,
        user_id: UUID,
        subject_id: Optional[UUID] = None
    ) -> List[TopicMasteryInfo]:
        """Get mastery info for all topics"""
        query = self.db.query(
            Topic,
            Subject,
            UserTopicMastery
        ).join(
            Subject, Topic.subject_id == Subject.id
        ).outerjoin(
            UserTopicMastery,
            and_(
                UserTopicMastery.topic_id == Topic.id,
                UserTopicMastery.user_id == user_id
            )
        )

        if subject_id:
            query = query.filter(Topic.subject_id == subject_id)

        results = query.all()

        topics = []
        for topic, subject, mastery in results:
            topics.append(TopicMasteryInfo(
                id=topic.id,
                name=topic.name,
                subject_id=subject.id,
                subject_name=subject.name,
                mastery_score=mastery.mastery_score if mastery else 0.0,
                questions_seen=mastery.questions_seen if mastery else 0,
                questions_correct=mastery.questions_correct if mastery else 0,
                last_practiced_at=mastery.last_practiced_at if mastery else None,
                status=mastery.status if mastery else "new"
            ))

        return topics

    def get_weak_areas(self, user_id: UUID, limit: int = 5) -> List[WeakAreaInfo]:
        """Get weak areas that need practice"""
        results = self.db.query(
            UserTopicMastery,
            Topic,
            Subject
        ).join(
            Topic, UserTopicMastery.topic_id == Topic.id
        ).join(
            Subject, Topic.subject_id == Subject.id
        ).filter(
            UserTopicMastery.user_id == user_id,
            UserTopicMastery.mastery_score < 0.6
        ).order_by(
            UserTopicMastery.mastery_score.asc()
        ).limit(limit).all()

        weak_areas = []
        for mastery, topic, subject in results:
            priority = "high" if mastery.mastery_score < 0.3 else "medium" if mastery.mastery_score < 0.5 else "low"
            suggested = 10 if priority == "high" else 5 if priority == "medium" else 3

            weak_areas.append(WeakAreaInfo(
                topic_id=topic.id,
                topic_name=topic.name,
                subject_id=subject.id,
                subject_name=subject.name,
                mastery_score=mastery.mastery_score,
                priority=priority,
                suggested_practice=suggested
            ))

        return weak_areas
