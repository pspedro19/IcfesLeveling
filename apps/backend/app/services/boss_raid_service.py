"""
Boss Raid Service for ICFES Leveling

Handles all business logic for the Boss Raid weekly event:
- Sunday 10 AM - 10 PM (COT - America/Bogota)
- 20 questions per session
- 3x XP multiplier
"""
from datetime import datetime, timedelta, time
from typing import Optional, Dict, List, Any, Tuple
from uuid import UUID
import random
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from ..models.boss_raid import Boss, BossRaidSession, BossRaidAnswer, BossRaidLeaderboard
from ..models.question import Question
from ..models.subject import Subject
from ..models.user import User
from ..models.mobile_offline import UserLeague, LeagueGroup, LeagueWeek

logger = logging.getLogger(__name__)


class BossRaidService:
    """
    Service for managing Boss Raid events.

    Event Schedule:
    - Day: Sunday (weekday = 6)
    - Start: 10:00 AM COT
    - End: 10:00 PM COT

    Rewards:
    - XP Multiplier: 3x
    - Base damage: 10 per correct answer
    - Combo damage bonus: +5 per combo level
    """

    # Configuration constants
    RAID_DAY = 6  # Sunday (Monday = 0, Sunday = 6)
    START_HOUR = 10  # 10 AM
    END_HOUR = 22  # 10 PM
    DEFAULT_TIMEZONE = "America/Bogota"

    # Game mechanics
    XP_MULTIPLIER = 3
    QUESTIONS_COUNT = 20
    BASE_DAMAGE = 10
    COMBO_BONUS_DAMAGE = 5
    BASE_XP_PER_QUESTION = 10

    # Entry cost and rewards by rank (LOGICA_DE_NEGOCIO.md specification)
    ENTRY_COST_GOLD = 100
    RANK_REWARDS = {
        "S": {"gold": 500, "xp_bonus": 200, "min_accuracy": 90, "badge": "Cazador Legendario"},
        "A": {"gold": 300, "xp_bonus": 100, "min_accuracy": 80, "badge": "Cazador Elite"},
        "B": {"gold": 200, "xp_bonus": 50, "min_accuracy": 70, "badge": None},
        "C": {"gold": 100, "xp_bonus": 0, "min_accuracy": 0, "badge": None},
    }

    # Boss defaults
    DEFAULT_BOSS_HP = 10000
    BOSS_NAMES = [
        "El Guardian del Conocimiento",
        "El Coloso de la Sabiduria",
        "La Bestia del Razonamiento",
        "El Titan de las Ciencias",
        "El Monstruo de la Logica",
        "El Demonio del Calculo",
        "La Serpiente del Lenguaje",
        "El Dragon de la Historia",
        "El Golem de la Fisica",
        "La Hidra de las Matematicas",
    ]

    @staticmethod
    def get_current_time(timezone: str = DEFAULT_TIMEZONE) -> datetime:
        """Get current time in specified timezone"""
        try:
            tz = ZoneInfo(timezone)
            return datetime.now(tz)
        except Exception:
            # Fallback to UTC
            return datetime.utcnow()

    @classmethod
    def is_raid_active(cls, timezone: str = DEFAULT_TIMEZONE) -> bool:
        """
        Check if Boss Raid is currently active.

        Active: Sunday 10 AM - 10 PM in specified timezone.

        Args:
            timezone: IANA timezone string (default: America/Bogota)

        Returns:
            bool: True if raid is currently active
        """
        now = cls.get_current_time(timezone)

        is_sunday = now.weekday() == cls.RAID_DAY
        is_within_hours = cls.START_HOUR <= now.hour < cls.END_HOUR

        return is_sunday and is_within_hours

    @classmethod
    def get_raid_times(cls, timezone: str = DEFAULT_TIMEZONE) -> Dict[str, datetime]:
        """
        Get start and end times for current/next raid.

        Returns:
            Dict with 'starts_at', 'ends_at', 'next_raid_at' keys
        """
        now = cls.get_current_time(timezone)
        tz = ZoneInfo(timezone)

        # Find this week's Sunday
        days_until_sunday = (cls.RAID_DAY - now.weekday()) % 7
        if days_until_sunday == 0 and now.hour >= cls.END_HOUR:
            days_until_sunday = 7  # Already past this week's raid

        this_sunday = now.date() + timedelta(days=days_until_sunday)
        next_sunday = this_sunday + timedelta(days=7)

        starts_at = datetime.combine(this_sunday, time(cls.START_HOUR, 0), tzinfo=tz)
        ends_at = datetime.combine(this_sunday, time(cls.END_HOUR, 0), tzinfo=tz)
        next_raid_at = datetime.combine(next_sunday, time(cls.START_HOUR, 0), tzinfo=tz)

        # If raid already ended this week, adjust
        if now > ends_at:
            starts_at = datetime.combine(next_sunday, time(cls.START_HOUR, 0), tzinfo=tz)
            ends_at = datetime.combine(next_sunday, time(cls.END_HOUR, 0), tzinfo=tz)
            next_raid_at = datetime.combine(next_sunday + timedelta(days=7), time(cls.START_HOUR, 0), tzinfo=tz)

        return {
            "starts_at": starts_at,
            "ends_at": ends_at,
            "next_raid_at": next_raid_at
        }

    @classmethod
    def get_or_create_current_boss(cls, db: Session) -> Boss:
        """
        Get or create the boss for the current week.

        A new boss is created for each week (ISO week number + year).

        Args:
            db: Database session

        Returns:
            Boss: Current week's boss
        """
        now = datetime.utcnow()
        week_number = now.isocalendar()[1]
        year = now.year

        # Try to find existing boss for this week
        boss = db.query(Boss).filter(
            Boss.week_number == week_number,
            Boss.year == year
        ).first()

        if boss:
            return boss

        # Create new boss for this week
        logger.info(f"Creating new Boss for week {week_number}/{year}")

        # Pick a random subject for thematic questions
        subjects = db.query(Subject).all()
        subject = random.choice(subjects) if subjects else None

        # Generate boss name
        boss_name = random.choice(cls.BOSS_NAMES)
        if subject:
            boss_name = f"{boss_name} - {subject.name}"

        boss = Boss(
            week_number=week_number,
            year=year,
            subject_id=subject.id if subject else None,
            name=boss_name,
            description=f"El temible jefe de la semana {week_number}. Derrota este enemigo con tus conocimientos!",
            hp=cls.DEFAULT_BOSS_HP,
            current_hp=cls.DEFAULT_BOSS_HP,
            difficulty="hard",
            base_xp_reward=100,
            gold_reward=500
        )

        db.add(boss)
        db.commit()
        db.refresh(boss)

        logger.info(f"Created boss: {boss.name} (Week {week_number}/{year})")
        return boss

    @classmethod
    def get_current_boss(cls, db: Session) -> Optional[Dict[str, Any]]:
        """
        Get current boss information for API response.

        Args:
            db: Database session

        Returns:
            Dict with boss information or None
        """
        boss = cls.get_or_create_current_boss(db)

        if not boss:
            return None

        # Get subject name if available
        subject_name = None
        if boss.subject_id:
            subject = db.query(Subject).filter(Subject.id == boss.subject_id).first()
            if subject:
                subject_name = subject.name

        return {
            "id": boss.id,
            "name": boss.name,
            "description": boss.description,
            "subject_id": boss.subject_id,
            "subject_name": subject_name,
            "hp": boss.hp,
            "current_hp": boss.current_hp,
            "difficulty": boss.difficulty,
            "is_defeated": boss.is_defeated,
            "defeated_at": boss.defeated_at
        }

    @classmethod
    def calculate_raid_xp(cls, base_xp: int) -> int:
        """
        Calculate XP with raid multiplier.

        Args:
            base_xp: Base XP amount

        Returns:
            int: XP with 3x multiplier applied
        """
        return base_xp * cls.XP_MULTIPLIER

    @classmethod
    def calculate_damage(cls, is_correct: bool, combo_count: int = 0) -> int:
        """
        Calculate damage dealt to boss.

        Args:
            is_correct: Whether the answer was correct
            combo_count: Current combo count

        Returns:
            int: Damage to deal to boss
        """
        if not is_correct:
            return 0

        base_damage = cls.BASE_DAMAGE
        combo_bonus = min(combo_count, 10) * cls.COMBO_BONUS_DAMAGE  # Cap combo bonus

        return base_damage + combo_bonus

    @classmethod
    def start_raid_session(
        cls,
        db: Session,
        user_id: UUID,
        timezone: str = DEFAULT_TIMEZONE
    ) -> Tuple[Optional[BossRaidSession], Optional[str], Optional[List[Question]]]:
        """
        Start a new Boss Raid session.

        Args:
            db: Database session
            user_id: ID of user starting the raid
            timezone: User's timezone

        Returns:
            Tuple of (session, error_message, questions)

        Entry Cost: 100 gold (LOGICA_DE_NEGOCIO.md specification)
        """
        # Check if raid is active
        if not cls.is_raid_active(timezone):
            return None, "RAID_NOT_ACTIVE", None

        # Get current boss
        boss = cls.get_or_create_current_boss(db)
        if boss.is_defeated:
            return None, "BOSS_ALREADY_DEFEATED", None

        # Check for existing in-progress session
        existing_session = db.query(BossRaidSession).filter(
            BossRaidSession.user_id == user_id,
            BossRaidSession.boss_id == boss.id,
            BossRaidSession.status == "in_progress"
        ).first()

        if existing_session:
            # Return existing session questions
            answered_ids = [a.question_id for a in existing_session.answers]
            questions = db.query(Question).filter(
                ~Question.id.in_(answered_ids) if answered_ids else True
            ).order_by(func.random()).limit(
                cls.QUESTIONS_COUNT - len(answered_ids)
            ).all()
            return existing_session, None, questions

        # ====== ENTRY COST VALIDATION (LOGICA_DE_NEGOCIO.md) ======
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None, "USER_NOT_FOUND", None

        current_gold = user.gold or 0
        if current_gold < cls.ENTRY_COST_GOLD:
            return None, f"INSUFFICIENT_GOLD:Necesitas {cls.ENTRY_COST_GOLD} oro para entrar al Boss Raid (tienes {current_gold})", None

        # Deduct entry cost
        user.gold = current_gold - cls.ENTRY_COST_GOLD
        logger.info(f"User {user_id} paid {cls.ENTRY_COST_GOLD} gold entry fee for Boss Raid")

        # Get questions for the raid
        # Prefer questions from boss's subject if available
        query = db.query(Question)
        if boss.subject_id:
            # 70% from boss subject, 30% from others
            subject_questions = query.filter(
                Question.subject_id == boss.subject_id
            ).order_by(func.random()).limit(14).all()

            other_questions = query.filter(
                Question.subject_id != boss.subject_id
            ).order_by(func.random()).limit(6).all()

            questions = subject_questions + other_questions
            random.shuffle(questions)
        else:
            questions = query.order_by(func.random()).limit(cls.QUESTIONS_COUNT).all()

        if len(questions) < cls.QUESTIONS_COUNT:
            # Not enough questions, use what we have
            logger.warning(f"Only {len(questions)} questions available for raid")

        # Create new session
        session = BossRaidSession(
            user_id=user_id,
            boss_id=boss.id,
            status="in_progress",
            total_questions=len(questions)
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        logger.info(f"Started raid session {session.id} for user {user_id}")

        return session, None, questions

    @classmethod
    def submit_answer(
        cls,
        db: Session,
        session_id: UUID,
        question_id: UUID,
        answer_id: str,
        time_spent_seconds: int,
        user_id: UUID
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Submit an answer in a Boss Raid session.

        Args:
            db: Database session
            session_id: Raid session ID
            question_id: Question being answered
            answer_id: User's answer
            time_spent_seconds: Time spent on question
            user_id: ID of user submitting

        Returns:
            Tuple of (result_dict, error_message)
        """
        # Get session
        session = db.query(BossRaidSession).filter(
            BossRaidSession.id == session_id,
            BossRaidSession.user_id == user_id
        ).first()

        if not session:
            return None, "SESSION_NOT_FOUND"

        if session.status != "in_progress":
            return None, "SESSION_NOT_ACTIVE"

        # Check if already answered
        existing_answer = db.query(BossRaidAnswer).filter(
            BossRaidAnswer.session_id == session_id,
            BossRaidAnswer.question_id == question_id
        ).first()

        if existing_answer:
            return None, "QUESTION_ALREADY_ANSWERED"

        # Get question and check answer
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return None, "QUESTION_NOT_FOUND"

        # Determine correct answer
        correct_answer = question.correct_answer or question.respuesta_correcta
        is_correct = answer_id.upper() == correct_answer.upper()

        # Update combo
        if is_correct:
            session.current_combo += 1
            session.combo_max = max(session.combo_max, session.current_combo)
        else:
            session.current_combo = 0

        # Calculate damage and XP
        damage = cls.calculate_damage(is_correct, session.current_combo)
        base_xp = cls.BASE_XP_PER_QUESTION if is_correct else 0
        xp_earned = cls.calculate_raid_xp(base_xp)

        # Create answer record
        answer = BossRaidAnswer(
            session_id=session_id,
            question_id=question_id,
            user_answer=answer_id,
            correct_answer=correct_answer,
            is_correct=is_correct,
            time_spent_seconds=time_spent_seconds,
            damage_dealt=damage,
            xp_earned=xp_earned,
            combo_count=session.current_combo
        )

        db.add(answer)

        # Update session stats
        session.questions_answered += 1
        session.total_damage += damage
        session.total_xp_earned += xp_earned
        session.total_time_seconds += time_spent_seconds

        if is_correct:
            session.correct_answers += 1

        # Update boss HP
        boss = session.boss
        boss.current_hp = max(0, boss.current_hp - damage)

        boss_defeated = boss.current_hp <= 0
        if boss_defeated and not boss.is_defeated:
            boss.is_defeated = True
            boss.defeated_at = datetime.utcnow()
            logger.info(f"Boss {boss.name} has been defeated!")

        # Check if session is complete
        questions_remaining = session.total_questions - session.questions_answered
        if questions_remaining <= 0:
            session.status = "completed"
            session.completed_at = datetime.utcnow()

        db.commit()

        return {
            "correct": is_correct,
            "correct_answer_id": correct_answer,
            "damage_dealt": damage,
            "boss_hp_remaining": boss.current_hp,
            "xp_earned": xp_earned,
            "combo_count": session.current_combo,
            "questions_remaining": questions_remaining,
            "session_damage_total": session.total_damage,
            "boss_defeated": boss_defeated
        }, None

    @classmethod
    def complete_raid(
        cls,
        db: Session,
        session_id: UUID,
        user_id: UUID
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Complete a Boss Raid session and calculate rewards.

        Args:
            db: Database session
            session_id: Raid session ID
            user_id: ID of user completing

        Returns:
            Tuple of (result_dict, error_message)
        """
        # Get session
        session = db.query(BossRaidSession).filter(
            BossRaidSession.id == session_id,
            BossRaidSession.user_id == user_id
        ).first()

        if not session:
            return None, "SESSION_NOT_FOUND"

        # Mark as completed if still in progress
        if session.status == "in_progress":
            session.status = "completed"
            session.completed_at = datetime.utcnow()

        # Calculate accuracy
        accuracy = (session.correct_answers / session.questions_answered * 100) if session.questions_answered > 0 else 0

        # Calculate duration
        duration = 0
        if session.completed_at and session.started_at:
            duration = int((session.completed_at - session.started_at).total_seconds())
        else:
            duration = session.total_time_seconds

        # ====== RANK-BASED REWARDS (LOGICA_DE_NEGOCIO.md) ======
        # Determine performance rank: S (90%+), A (80%+), B (70%+), C (default)
        boss = session.boss
        if accuracy >= cls.RANK_REWARDS["S"]["min_accuracy"]:
            performance_rank = "S"
        elif accuracy >= cls.RANK_REWARDS["A"]["min_accuracy"]:
            performance_rank = "A"
        elif accuracy >= cls.RANK_REWARDS["B"]["min_accuracy"]:
            performance_rank = "B"
        else:
            performance_rank = "C"

        rank_reward = cls.RANK_REWARDS[performance_rank]
        gold_earned = rank_reward["gold"]
        xp_bonus = rank_reward["xp_bonus"]
        rank_badge = rank_reward["badge"]

        # Build rewards list
        rewards = []

        # XP reward (base + bonus for rank)
        total_xp = session.total_xp_earned + xp_bonus
        if total_xp > 0:
            rewards.append({
                "type": "xp",
                "amount": total_xp,
                "name": f"Experiencia de Raid (Rank {performance_rank})"
            })

        # Gold based on rank (S=500, A=300, B=200, C=100)
        if gold_earned > 0:
            rewards.append({
                "type": "gold",
                "amount": gold_earned,
                "name": f"Oro de Raid - Rank {performance_rank}"
            })

        # Rank badge (S and A get badges)
        if rank_badge:
            rewards.append({
                "type": "badge",
                "name": rank_badge,
                "amount": None
            })

        # Additional achievement badges
        if session.combo_max >= 10:
            rewards.append({
                "type": "badge",
                "name": "Combo Master",
                "amount": None
            })

        if accuracy == 100 and session.questions_answered >= 10:
            rewards.append({
                "type": "badge",
                "name": "Perfecto",
                "amount": None
            })

        # ====== APLICAR RECOMPENSAS AL USUARIO ======
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            # Aplicar XP (base raid XP + rank bonus)
            if total_xp > 0:
                user.experience = (user.experience or 0) + total_xp

                # Actualizar XP de liga semanal
                user_league = db.query(UserLeague).join(LeagueGroup).join(LeagueWeek).filter(
                    UserLeague.user_id == user_id,
                    LeagueWeek.is_active == True
                ).first()
                if user_league:
                    user_league.weekly_xp += total_xp

            # Aplicar Gold (rank-based: S=500, A=300, B=200, C=100)
            if gold_earned > 0:
                user.gold = (user.gold or 0) + gold_earned

        logger.info(f"User {user_id} completed Boss Raid with Rank {performance_rank}: +{total_xp} XP, +{gold_earned} gold")

        # Update or create leaderboard entry
        leaderboard_entry = db.query(BossRaidLeaderboard).filter(
            BossRaidLeaderboard.boss_id == session.boss_id,
            BossRaidLeaderboard.user_id == user_id
        ).first()

        if leaderboard_entry:
            leaderboard_entry.total_damage += session.total_damage
            leaderboard_entry.total_sessions += 1
            leaderboard_entry.total_xp_earned += session.total_xp_earned
            leaderboard_entry.best_combo = max(leaderboard_entry.best_combo, session.combo_max)
        else:
            leaderboard_entry = BossRaidLeaderboard(
                boss_id=session.boss_id,
                user_id=user_id,
                total_damage=session.total_damage,
                total_sessions=1,
                total_xp_earned=session.total_xp_earned,
                best_combo=session.combo_max
            )
            db.add(leaderboard_entry)

        db.commit()

        # Get rank
        rank = cls.get_user_rank(db, session.boss_id, user_id)

        return {
            "boss_defeated": boss.is_defeated,
            "total_damage": session.total_damage,
            "total_xp": total_xp,
            "xp_bonus": xp_bonus,
            "correct_answers": session.correct_answers,
            "total_questions": session.questions_answered,
            "accuracy_percentage": round(accuracy, 2),
            "performance_rank": performance_rank,
            "gold_earned": gold_earned,
            "best_combo": session.combo_max,
            "rank_in_raid": rank,
            "rewards": rewards,
            "session_duration_seconds": duration
        }, None

    @classmethod
    def get_user_rank(cls, db: Session, boss_id: UUID, user_id: UUID) -> Optional[int]:
        """Get user's rank in the current boss raid"""
        # Get all leaderboard entries ordered by damage
        entries = db.query(BossRaidLeaderboard).filter(
            BossRaidLeaderboard.boss_id == boss_id
        ).order_by(desc(BossRaidLeaderboard.total_damage)).all()

        for i, entry in enumerate(entries, 1):
            if entry.user_id == user_id:
                return i

        return None

    @classmethod
    def get_user_total_damage(cls, db: Session, boss_id: UUID, user_id: UUID) -> int:
        """Get user's total damage dealt to a boss"""
        entry = db.query(BossRaidLeaderboard).filter(
            BossRaidLeaderboard.boss_id == boss_id,
            BossRaidLeaderboard.user_id == user_id
        ).first()

        return entry.total_damage if entry else 0

    @classmethod
    def get_leaderboard(
        cls,
        db: Session,
        boss_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get Boss Raid leaderboard.

        Args:
            db: Database session
            boss_id: Boss to get leaderboard for
            user_id: Current user ID for highlighting
            limit: Maximum entries to return

        Returns:
            Dict with leaderboard data
        """
        boss = db.query(Boss).filter(Boss.id == boss_id).first()
        if not boss:
            return {"leaderboard": [], "total_participants": 0}

        # Get entries ordered by damage
        entries = db.query(BossRaidLeaderboard).filter(
            BossRaidLeaderboard.boss_id == boss_id
        ).order_by(desc(BossRaidLeaderboard.total_damage)).limit(limit).all()

        total = db.query(BossRaidLeaderboard).filter(
            BossRaidLeaderboard.boss_id == boss_id
        ).count()

        leaderboard = []
        my_entry = None

        for i, entry in enumerate(entries, 1):
            user = db.query(User).filter(User.id == entry.user_id).first()

            entry_data = {
                "user_id": entry.user_id,
                "user_name": user.username if user else "Unknown",
                "avatar_url": getattr(user, 'avatar_url', None),
                "total_damage": entry.total_damage,
                "total_xp": entry.total_xp_earned,
                "rank": i,
                "is_me": entry.user_id == user_id
            }

            leaderboard.append(entry_data)

            if entry.user_id == user_id:
                my_entry = entry_data

        return {
            "boss_id": boss_id,
            "boss_name": boss.name,
            "leaderboard": leaderboard,
            "my_entry": my_entry,
            "total_participants": total
        }


# Export singleton instance for convenience
boss_raid_service = BossRaidService()
