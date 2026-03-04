"""
Celery Scheduled Tasks
======================
Background tasks that run on a schedule via Celery Beat.

Tasks:
- regenerate_hearts: Every hour - Regenerate hearts for users (1 heart per 4 hours)
- process_weekly_leagues: Monday 00:00 - Process league promotions/relegations
- send_streak_reminders: 6 PM, 9 PM, 3:30 AM - Send push notifications for streak protection
"""

from celery import Celery
from celery.schedules import crontab
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, or_, func as sql_func
from sqlalchemy.orm import Session
import logging

from ..core.config import settings
from ..core.database import SessionLocal

logger = logging.getLogger(__name__)


# ============================================
# CELERY APP CONFIGURATION
# ============================================

celery_app = Celery(
    "icfes_leveling_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Bogota",  # Colombia timezone for correct scheduling
    enable_utc=False,  # Use local timezone
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)


# ============================================
# DATABASE SESSION HELPER
# ============================================

def get_db_session() -> Session:
    """Create a database session for background tasks."""
    return SessionLocal()


# ============================================
# NOTIFICATION SERVICE
# ============================================

class NotificationService:
    """
    Service for sending push notifications via Firebase Cloud Messaging.
    This is a simplified implementation - integrate with actual FCM in production.
    """

    TEMPLATES = {
        "streak_at_risk_6pm": {
            "title": "Tu racha esta en peligro!",
            "body": "Los Cazadores no descansan. Tu racha de {streak} dias te espera."
        },
        "streak_at_risk_9pm": {
            "title": "Ultima llamada, Cazador",
            "body": "Los Cazadores debiles pierden su racha hoy. Tu tienes {streak} dias."
        },
        "streak_at_risk_330am": {
            "title": "30 minutos para el reinicio",
            "body": "El Sistema reinicia a las 4:00 AM. Salva tu racha de {streak} dias."
        },
        "hearts_refilled": {
            "title": "Mana restaurado!",
            "body": "Tienes 5 corazones listos. Vuelve a la batalla."
        },
        "league_promotion": {
            "title": "Ascenso de Liga!",
            "body": "Has subido a la liga {league}. El Sistema te reconoce."
        },
        "league_relegation": {
            "title": "Descenso de Liga",
            "body": "Has bajado a la liga {league}. Lucha para recuperar tu posicion!"
        },
    }

    @staticmethod
    def send_push_notification(
        user_id: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send push notification to a user.

        In production, this would use Firebase Admin SDK to send FCM messages.
        Currently logs the notification for development purposes.
        """
        try:
            db = get_db_session()
            try:
                # Import here to avoid circular imports
                from ..models.mobile_offline import UserDeviceToken, NotificationHistory

                # Get user's active device tokens
                tokens = db.execute(
                    select(UserDeviceToken).where(
                        and_(
                            UserDeviceToken.user_id == user_id,
                            UserDeviceToken.is_active == True
                        )
                    )
                ).scalars().all()

                if not tokens:
                    logger.debug(f"No active device tokens for user {user_id}")
                    return False

                # Log notification to history
                notification = NotificationHistory(
                    user_id=user_id,
                    notification_type="streak_reminder",
                    title=title,
                    body=body,
                    data=data or {},
                    sent_at=datetime.now(),
                    success=True
                )
                db.add(notification)
                db.commit()

                # Send via Firebase Admin SDK
                try:
                    import firebase_admin
                    from firebase_admin import messaging as fcm_messaging

                    # Initialize Firebase if not already done
                    try:
                        firebase_admin.get_app()
                    except ValueError:
                        import os, json
                        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
                        creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
                        if cred_path and os.path.exists(cred_path):
                            cred = firebase_admin.credentials.Certificate(cred_path)
                            firebase_admin.initialize_app(cred)
                        elif creds_json:
                            cred = firebase_admin.credentials.Certificate(json.loads(creds_json))
                            firebase_admin.initialize_app(cred)
                        else:
                            logger.warning("Firebase credentials not configured - notifications simulated")
                            return True

                    sent_count = 0
                    string_data = {k: str(v) for k, v in (data or {}).items()}
                    for token in tokens:
                        try:
                            message = fcm_messaging.Message(
                                notification=fcm_messaging.Notification(title=title, body=body),
                                token=token.device_token,
                                data=string_data,
                                android=fcm_messaging.AndroidConfig(
                                    priority="high",
                                    notification=fcm_messaging.AndroidNotification(
                                        icon="notification_icon",
                                        color="#6366f1",
                                        channel_id="icfes_leveling_notifications"
                                    )
                                ),
                                apns=fcm_messaging.APNSConfig(
                                    payload=fcm_messaging.APNSPayload(
                                        aps=fcm_messaging.Aps(sound="default", badge=1)
                                    )
                                )
                            )
                            fcm_messaging.send(message)
                            sent_count += 1
                        except Exception as token_err:
                            logger.warning(f"FCM send failed for token {token.device_token[:10]}...: {token_err}")

                    logger.info(f"Push notification sent to user {user_id}: {title} ({sent_count}/{len(tokens)} tokens)")
                    return True

                except ImportError:
                    logger.info(f"[SIMULATED] Push notification to user {user_id}: {title} (firebase-admin not installed)")
                    return True

            finally:
                db.close()

        except Exception as e:
            logger.error(f"Failed to send push notification to user {user_id}: {e}")
            return False

    @classmethod
    def send_streak_reminder(cls, user_id: str, streak_days: int, template_key: str) -> bool:
        """Send a streak reminder notification using a template."""
        template = cls.TEMPLATES.get(template_key)
        if not template:
            logger.error(f"Unknown notification template: {template_key}")
            return False

        title = template["title"]
        body = template["body"].format(streak=streak_days)

        return cls.send_push_notification(
            user_id=str(user_id),
            title=title,
            body=body,
            data={"action": "open_practice", "streak": streak_days}
        )


# ============================================
# SCHEDULED TASKS
# ============================================

@celery_app.task(name="app.tasks.scheduled.regenerate_hearts")
def regenerate_hearts() -> Dict[str, Any]:
    """
    Regenerate hearts for users who have less than 5 hearts.

    Logic:
    - Find users with hearts < 5
    - Calculate hours since last_heart_used_at
    - Add hearts_to_add = hours // 4 (1 heart per 4 hours)
    - Cap at max 5 hearts
    - If grace_mode_active and hearts > 0, set grace_mode_active = False

    Runs every hour via Celery beat.
    """
    db = get_db_session()
    try:
        from ..models.diagnostic_two_phase import UserEngagement

        logger.info("Starting heart regeneration task...")

        now = datetime.utcnow()
        users_updated = 0
        hearts_regenerated = 0
        grace_modes_deactivated = 0

        # Find users with hearts < 5 using ORM
        try:
            engagements = db.execute(
                select(UserEngagement).where(UserEngagement.hearts < 5)
            ).scalars().all()

        except Exception as e:
            # Table might not exist yet - return gracefully
            logger.warning(f"Could not query user_engagement table: {e}")
            return {
                "status": "skipped",
                "reason": "user_engagement table not found - run migrations first",
                "timestamp": now.isoformat()
            }

        for engagement in engagements:
            user_id = engagement.user_id
            current_hearts = engagement.hearts
            last_heart_used_at = engagement.last_heart_used_at
            grace_mode_active = engagement.grace_mode_active

            if current_hearts >= 5:
                continue

            # Calculate hours since last heart was used
            if last_heart_used_at:
                hours_since = (now - last_heart_used_at).total_seconds() / 3600
            else:
                hours_since = 0

            # Calculate hearts to add (1 heart per 4 hours)
            hearts_to_add = int(hours_since // 4)

            if hearts_to_add > 0:
                new_hearts = min(5, current_hearts + hearts_to_add)
                actual_hearts_added = new_hearts - current_hearts

                # Update user's hearts using ORM
                engagement.hearts = new_hearts
                engagement.updated_at = now

                users_updated += 1
                hearts_regenerated += actual_hearts_added

                # Deactivate grace mode if hearts > 0
                if grace_mode_active and new_hearts > 0:
                    engagement.grace_mode_active = False
                    engagement.grace_mode_started_at = None
                    grace_modes_deactivated += 1

                    logger.debug(f"Deactivated grace mode for user {user_id}")

        db.commit()

        result = {
            "status": "success",
            "users_updated": users_updated,
            "hearts_regenerated": hearts_regenerated,
            "grace_modes_deactivated": grace_modes_deactivated,
            "timestamp": now.isoformat()
        }

        logger.info(
            f"Heart regeneration complete: {users_updated} users updated, "
            f"{hearts_regenerated} hearts regenerated, "
            f"{grace_modes_deactivated} grace modes deactivated"
        )

        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Heart regeneration task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduled.process_weekly_leagues")
def process_weekly_leagues() -> Dict[str, Any]:
    """
    Process league promotions and relegations.

    Logic:
    - For each league group:
      - Get members ordered by weekly_xp DESC
      - Top 10: promoted = True, next_division += 1
      - Bottom 5: relegated = True, next_division -= 1 (min 1)
      - Reset weekly_xp = 0 for all

    Runs Monday 00:00 via Celery beat.
    """
    db = get_db_session()
    try:
        from ..models.mobile_offline import (
            LeagueGroup, LeagueWeek, LeagueDivision,
            UserLeague, UserLeagueHistory
        )

        logger.info("Starting weekly league processing...")

        now = datetime.utcnow()
        promotions = 0
        relegations = 0
        users_reset = 0
        groups_processed = 0

        # Find the active league week
        active_week = db.execute(
            select(LeagueWeek).where(LeagueWeek.is_active == True)
        ).scalar_one_or_none()

        if not active_week:
            logger.warning("No active league week found")
            return {
                "status": "skipped",
                "reason": "No active league week",
                "timestamp": now.isoformat()
            }

        # Get all groups for this week
        groups = db.execute(
            select(LeagueGroup).where(LeagueGroup.league_week_id == active_week.id)
        ).scalars().all()

        for group in groups:
            # Get all members in this group, ordered by weekly_xp DESC
            members = db.execute(
                select(UserLeague)
                .where(UserLeague.league_group_id == group.id)
                .order_by(UserLeague.weekly_xp.desc())
            ).scalars().all()

            total_members = len(members)
            if total_members == 0:
                continue

            groups_processed += 1

            # Get division info for promotion/relegation logic
            division = db.execute(
                select(LeagueDivision).where(LeagueDivision.id == group.division_id)
            ).scalar_one_or_none()

            if not division:
                logger.warning(f"Division not found for group {group.id}")
                continue

            promotion_spots = division.promotion_spots or 10
            relegation_spots = division.relegation_spots or 5

            for rank, member in enumerate(members, 1):
                # Determine status based on rank
                if rank <= promotion_spots:
                    # Top 10: Promotion
                    status = "promoted"
                    new_division_tier = min(division.tier + 1, 10)  # Cap at max tier
                    promotions += 1
                elif rank > total_members - relegation_spots:
                    # Bottom 5: Relegation
                    status = "relegated"
                    new_division_tier = max(division.tier - 1, 1)  # Min tier is 1
                    relegations += 1
                else:
                    # Middle: Stay in same division
                    status = "stayed"
                    new_division_tier = division.tier

                # Create history record
                history = UserLeagueHistory(
                    user_id=member.user_id,
                    league_week_id=active_week.id,
                    division_id=group.division_id,
                    final_xp=member.weekly_xp,
                    final_rank=rank,
                    total_participants=total_members,
                    status=status,
                    gems_earned=division.weekly_gem_reward if rank <= 3 else 0
                )
                db.add(history)

                # Reset weekly XP
                member.weekly_xp = 0
                member.current_rank = None
                users_reset += 1

                # Send notifications for promotions/relegations
                if status == "promoted":
                    # Find the new division name
                    new_division = db.execute(
                        select(LeagueDivision).where(LeagueDivision.tier == new_division_tier)
                    ).scalar_one_or_none()

                    if new_division:
                        NotificationService.send_push_notification(
                            user_id=str(member.user_id),
                            title="Ascenso de Liga!",
                            body=f"Has subido a la liga {new_division.name}. El Sistema te reconoce.",
                            data={"action": "view_league", "new_division": new_division.name}
                        )
                elif status == "relegated" and division.tier > 1:
                    # Find the new division name
                    new_division = db.execute(
                        select(LeagueDivision).where(LeagueDivision.tier == new_division_tier)
                    ).scalar_one_or_none()

                    if new_division:
                        NotificationService.send_push_notification(
                            user_id=str(member.user_id),
                            title="Cambio de Liga",
                            body=f"Has bajado a la liga {new_division.name}. Lucha para recuperar tu posicion!",
                            data={"action": "view_league", "new_division": new_division.name}
                        )

        # Mark the week as processed
        active_week.is_processed = True
        active_week.is_active = False

        # Create or activate next week
        next_week_start = active_week.week_end + timedelta(days=1)
        next_week_number = active_week.week_number + 1 if active_week.week_number < 52 else 1
        next_year = active_week.year if active_week.week_number < 52 else active_week.year + 1

        # Check if next week exists
        next_week = db.execute(
            select(LeagueWeek).where(
                and_(
                    LeagueWeek.year == next_year,
                    LeagueWeek.week_number == next_week_number
                )
            )
        ).scalar_one_or_none()

        if not next_week:
            # Create new league week
            next_week = LeagueWeek(
                year=next_year,
                week_number=next_week_number,
                week_start=next_week_start,
                week_end=next_week_start + timedelta(days=6),
                is_active=True,
                is_processed=False
            )
            db.add(next_week)
        else:
            next_week.is_active = True

        db.commit()

        result = {
            "status": "success",
            "groups_processed": groups_processed,
            "promotions": promotions,
            "relegations": relegations,
            "users_reset": users_reset,
            "week_processed": active_week.week_number,
            "next_week": next_week_number,
            "timestamp": now.isoformat()
        }

        logger.info(
            f"League processing complete: {groups_processed} groups, "
            f"{promotions} promotions, {relegations} relegations, "
            f"{users_reset} users reset"
        )

        return result

    except Exception as e:
        db.rollback()
        logger.error(f"League processing task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduled.send_streak_reminders")
def send_streak_reminders() -> Dict[str, Any]:
    """
    Send push notifications to users at risk of losing their streak.

    Logic:
    - Find users with current_streak > 0 AND today_xp == 0
    - Send push notification via NotificationService

    Runs at:
    - 6 PM (18:00) - First reminder
    - 9 PM (21:00) - Urgent reminder
    - 3:30 AM - Final warning before 4 AM reset
    """
    db = get_db_session()
    try:
        from ..models.diagnostic_two_phase import UserEngagement

        logger.info("Starting streak reminder task...")

        now = datetime.now()
        current_hour = now.hour

        # Determine which template to use based on time
        if current_hour == 18:
            template_key = "streak_at_risk_6pm"
        elif current_hour == 21:
            template_key = "streak_at_risk_9pm"
        elif current_hour == 3:
            template_key = "streak_at_risk_330am"
        else:
            template_key = "streak_at_risk_6pm"  # Default fallback

        notifications_sent = 0
        notifications_failed = 0

        # Find users with active streaks who haven't earned XP today
        # Use UserEngagement which has current_streak and today_xp fields
        try:
            engagements_at_risk = db.execute(
                select(UserEngagement).where(
                    and_(
                        UserEngagement.current_streak > 0,
                        UserEngagement.today_xp == 0
                    )
                )
            ).scalars().all()

            users_at_risk = [
                (e.user_id, e.current_streak, e.today_xp)
                for e in engagements_at_risk
            ]

        except Exception as e:
            logger.warning(f"Could not query user_engagement for streak data: {e}")
            # Fallback: try querying from users table
            from ..models.user import User
            users = db.execute(
                select(User).where(
                    and_(
                        User.streak_days > 0,
                        User.is_active == True
                    )
                )
            ).scalars().all()

            # For fallback, we'll send to all users with streaks
            # In production, you'd want proper today_xp tracking
            users_at_risk = [(u.id, u.streak_days, 0) for u in users]

        for user_data in users_at_risk:
            user_id = user_data[0]
            streak_days = user_data[1]
            today_xp = user_data[2]

            # Only send if user hasn't earned XP today
            if today_xp > 0:
                continue

            success = NotificationService.send_streak_reminder(
                user_id=str(user_id),
                streak_days=streak_days,
                template_key=template_key
            )

            if success:
                notifications_sent += 1
            else:
                notifications_failed += 1

        result = {
            "status": "success",
            "notifications_sent": notifications_sent,
            "notifications_failed": notifications_failed,
            "template_used": template_key,
            "timestamp": now.isoformat()
        }

        logger.info(
            f"Streak reminders complete: {notifications_sent} sent, "
            f"{notifications_failed} failed"
        )

        return result

    except Exception as e:
        logger.error(f"Streak reminder task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduled.generate_weekly_boss")
def generate_weekly_boss() -> Dict[str, Any]:
    """
    Generate a new weekly Boss for Boss Raid event.

    Logic:
    1. Calculate current week number and year
    2. Check if boss already exists for this week
    3. If not, create new boss with random subject
    4. Boss HP scales with number of active users

    Runs every Sunday at 10:00 AM (start of Boss Raid event).
    """
    db = get_db_session()
    try:
        from ..models.boss_raid import Boss
        from ..models.subject import Subject
        from ..models.user import User
        import random

        logger.info("Starting weekly boss generation task...")

        now = datetime.utcnow()

        # Calculate week number (ISO week)
        week_number = now.isocalendar()[1]
        year = now.year

        # Check if boss already exists for this week
        existing_boss = db.query(Boss).filter(
            Boss.week_number == week_number,
            Boss.year == year
        ).first()

        if existing_boss:
            logger.info(f"Boss already exists for week {week_number}/{year}")
            return {
                "status": "skipped",
                "reason": "Boss already exists",
                "boss_id": str(existing_boss.id),
                "boss_name": existing_boss.name,
                "timestamp": now.isoformat()
            }

        # Get random subject for boss theme
        subjects = db.query(Subject).all()
        subject = random.choice(subjects) if subjects else None

        # Calculate HP based on active users (more users = stronger boss)
        active_users = db.query(User).filter(User.is_active == True).count()
        base_hp = 10000
        hp_per_user = 100  # Each user adds 100 HP
        boss_hp = base_hp + (active_users * hp_per_user)

        # Boss names themed by subject
        boss_names = {
            "Matemáticas": ["El Algebráico Oscuro", "El Geómetra Infernal", "El Calculador Supremo"],
            "Lectura Crítica": ["El Lector de Sombras", "El Guardián de Textos", "El Maestro de Letras"],
            "Ciencias Naturales": ["El Alquimista Corrupto", "La Bestia Elemental", "El Doctor Caos"],
            "Sociales y Ciudadanas": ["El Tirano Histórico", "El Manipulador Social", "El Emperador Perdido"],
            "Inglés": ["The Grammar Fiend", "The Lost Translator", "The Dialect Demon"],
        }

        subject_name = subject.nombre if subject else "General"
        name_options = boss_names.get(subject_name, ["El Guardián del Conocimiento", "El Devorador de Mentes", "El Sabio Corrupto"])
        boss_name = random.choice(name_options)

        # Difficulty scales with week number (harder as semester progresses)
        if week_number <= 12:
            difficulty = "medium"
        elif week_number <= 24:
            difficulty = "hard"
        else:
            difficulty = "legendary"

        # Create new boss
        new_boss = Boss(
            week_number=week_number,
            year=year,
            subject_id=subject.id if subject else None,
            name=boss_name,
            description=f"El boss de la semana {week_number}. ¡Derrótalo antes del domingo a las 10PM!",
            hp=boss_hp,
            current_hp=boss_hp,
            difficulty=difficulty,
            base_xp_reward=100 * ({"medium": 1, "hard": 2, "legendary": 3}.get(difficulty, 1)),
            gold_reward=500 * ({"medium": 1, "hard": 2, "legendary": 3}.get(difficulty, 1)),
        )
        db.add(new_boss)
        db.commit()

        result = {
            "status": "success",
            "boss_id": str(new_boss.id),
            "boss_name": new_boss.name,
            "boss_hp": new_boss.hp,
            "difficulty": difficulty,
            "subject": subject_name,
            "week_number": week_number,
            "year": year,
            "timestamp": now.isoformat()
        }

        logger.info(f"Weekly boss generated: {new_boss.name} (HP: {boss_hp}, Difficulty: {difficulty})")

        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Weekly boss generation task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduled.daily_reset_4am")
def daily_reset_4am() -> Dict[str, Any]:
    """
    Daily reset at 4 AM Bogotá time.

    Logic:
    1. Evaluate streaks:
       - Users with today_xp >= daily_goal: streak += 1
       - Users with today_xp == 0 and streak > 0: streak = 0 (break streak)
    2. Reset today_xp = 0 for all users
    3. Reset today_questions_answered = 0
    4. Reset daily_goal_met = False

    Runs at 4:00 AM Colombia time via Celery beat.
    """
    db = get_db_session()
    try:
        from ..models.diagnostic_two_phase import UserEngagement
        from ..models.mobile_offline import UserDailyActivity
        from ..models.user import User

        logger.info("Starting daily reset 4AM task...")

        now = datetime.utcnow()
        today = date.today()
        streaks_broken = 0
        streaks_extended = 0
        users_reset = 0

        # Process UserEngagement table (main tracking)
        try:
            engagements = db.execute(
                select(UserEngagement)
            ).scalars().all()

            for engagement in engagements:
                today_xp = engagement.today_xp or 0
                current_streak = engagement.current_streak or 0
                daily_goal = engagement.daily_goal_xp or 20

                # Evaluate streak
                if today_xp >= daily_goal:
                    # User met daily goal - extend streak
                    engagement.current_streak = current_streak + 1
                    if engagement.current_streak > (engagement.best_streak or 0):
                        engagement.best_streak = engagement.current_streak
                    streaks_extended += 1
                elif today_xp == 0 and current_streak > 0:
                    # User did nothing - break streak
                    engagement.current_streak = 0
                    streaks_broken += 1
                # Else: user did something but didn't meet goal - streak stays same

                # Reset daily counters
                engagement.today_xp = 0
                engagement.today_questions_answered = 0
                engagement.daily_goal_met = False
                engagement.updated_at = now
                users_reset += 1

        except Exception as e:
            logger.warning(f"Could not process user_engagement table: {e}")

        # Also update User model streak_days for backwards compatibility
        try:
            users = db.query(User).filter(User.is_active == True).all()
            for user in users:
                # Check if user has UserDailyActivity for yesterday/today
                yesterday = today - timedelta(days=1)
                activity = db.query(UserDailyActivity).filter(
                    UserDailyActivity.user_id == user.id,
                    UserDailyActivity.activity_date == yesterday
                ).first()

                if activity and activity.xp_earned >= 20:
                    # Had activity yesterday - increment streak
                    user.streak_days = (user.streak_days or 0) + 1
                elif not activity or activity.xp_earned == 0:
                    # No activity - reset streak
                    if user.streak_days and user.streak_days > 0:
                        user.streak_days = 0

        except Exception as e:
            logger.warning(f"Could not update User streak_days: {e}")

        db.commit()

        result = {
            "status": "success",
            "streaks_extended": streaks_extended,
            "streaks_broken": streaks_broken,
            "users_reset": users_reset,
            "reset_date": today.isoformat(),
            "timestamp": now.isoformat()
        }

        logger.info(
            f"Daily reset complete: {streaks_extended} streaks extended, "
            f"{streaks_broken} streaks broken, {users_reset} users reset"
        )

        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Daily reset 4AM task failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduled.check_monthly_reassessments")
def check_monthly_reassessments() -> Dict[str, Any]:
    """
    Check and notify users eligible for monthly reassessment.

    Runs on the 1st of each month at 6:00 AM.
    Sends notifications to users who:
    1. Have completed initial diagnostic test 30+ days ago
    2. Haven't done a reassessment in the last 7 days
    """
    db = get_db_session()
    try:
        from ..models.user import User
        from ..models.diagnostic_test import DiagnosticTest
        from ..models.subject import Subject
        from ..services.monthly_reassessment_service import MonthlyReassessmentService

        logger.info("Starting monthly reassessment check...")

        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        seven_days_ago = now - timedelta(days=7)

        users_notified = 0
        users_eligible = 0

        # Get all active users with completed initial diagnostics
        users_with_diagnostics = db.query(User).join(
            DiagnosticTest, User.id == DiagnosticTest.user_id
        ).filter(
            User.is_active == True,
            DiagnosticTest.reassessment_type == "initial",
            DiagnosticTest.status == "completed",
            DiagnosticTest.created_at <= thirty_days_ago
        ).distinct().all()

        reassessment_service = MonthlyReassessmentService(db)

        for user in users_with_diagnostics:
            # Check each subject for eligibility
            user_diagnostics = db.query(DiagnosticTest).filter(
                DiagnosticTest.user_id == user.id,
                DiagnosticTest.reassessment_type == "initial",
                DiagnosticTest.status == "completed"
            ).all()

            for diagnostic in user_diagnostics:
                eligibility = reassessment_service.check_monthly_reassessment_eligibility(
                    str(user.id), str(diagnostic.subject_id)
                )

                if eligibility.get("eligible"):
                    users_eligible += 1

                    # Get subject name for notification
                    subject = db.query(Subject).filter(Subject.id == diagnostic.subject_id).first()
                    subject_name = subject.nombre if subject else "materia"

                    # Send notification (if notification service exists)
                    try:
                        from ..services.notification_service import NotificationService as NotificationServiceReal
                        notification_service = NotificationServiceReal(db)
                        notification_service.send_custom(
                            user_id=user.id,
                            title="Reevaluación Mensual Disponible",
                            body=f"Ha pasado un mes desde tu test de {subject_name}. Es hora de evaluar tu progreso.",
                            data={
                                "subject_id": str(diagnostic.subject_id),
                                "initial_score": eligibility.get("initial_score", 0)
                            }
                        )
                        users_notified += 1
                    except ImportError:
                        # Notification service not available
                        logger.warning("NotificationService not available")
                    except Exception as e:
                        logger.warning(f"Failed to send notification to {user.id}: {e}")

        result = {
            "status": "success",
            "users_checked": len(users_with_diagnostics),
            "users_eligible": users_eligible,
            "users_notified": users_notified,
            "timestamp": now.isoformat()
        }

        logger.info(f"Monthly reassessment check complete: {users_eligible} eligible, {users_notified} notified")

        return result

    except Exception as e:
        db.rollback()
        logger.error(f"Monthly reassessment check failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduled.generate_daily_quests")
def generate_daily_quests() -> Dict[str, Any]:
    """
    Generate 3 daily quests for each active user.

    Quest types:
    - answer_questions: Answer N questions in subject X
    - practice_session: Complete a practice session
    - streak_maintain: Maintain your streak today
    - combo_achieve: Get a 5x combo in practice
    - time_challenge: Answer 10 questions in under 5 minutes

    Runs daily at 4:05 AM (after daily reset).
    """
    db = get_db_session()
    try:
        from ..models.user import User
        import random

        logger.info("Starting daily quest generation...")

        now = datetime.utcnow()
        today = date.today()
        quests_created = 0

        quest_templates = [
            {"type": "answer_questions", "title": "Responde {n} preguntas de {subject}",
             "description": "Practica respondiendo preguntas", "xp_reward": 50, "gold_reward": 25},
            {"type": "practice_session", "title": "Completa una sesion de practica",
             "description": "Termina una sesion completa de 15 preguntas", "xp_reward": 75, "gold_reward": 50},
            {"type": "streak_maintain", "title": "Mantiene tu racha activa",
             "description": "Gana al menos 20 XP hoy", "xp_reward": 30, "gold_reward": 15},
            {"type": "combo_achieve", "title": "Logra un combo de 5x",
             "description": "Responde 5 preguntas correctas seguidas", "xp_reward": 100, "gold_reward": 75},
            {"type": "time_challenge", "title": "Desafio de velocidad",
             "description": "Responde 10 preguntas en menos de 5 minutos", "xp_reward": 80, "gold_reward": 40},
        ]

        subjects = ["Matematicas", "Lectura Critica", "Ciencias Naturales", "Sociales", "Ingles"]

        active_users = db.query(User).filter(User.is_active == True).all()

        for user in active_users:
            # Select 3 random quest templates
            selected = random.sample(quest_templates, min(3, len(quest_templates)))

            for quest_template in selected:
                title = quest_template["title"]
                if "{n}" in title:
                    title = title.replace("{n}", str(random.choice([5, 10, 15])))
                if "{subject}" in title:
                    title = title.replace("{subject}", random.choice(subjects))

                # Store quest in Redis (lightweight, expires at end of day)
                from ..core.redis_cache import get_redis
                redis = get_redis()
                if redis:
                    quest_key = f"daily_quest:{user.id}:{today.isoformat()}:{quest_template['type']}"
                    import json
                    redis.setex(quest_key, 86400, json.dumps({
                        "type": quest_template["type"],
                        "title": title,
                        "description": quest_template["description"],
                        "xp_reward": quest_template["xp_reward"],
                        "gold_reward": quest_template["gold_reward"],
                        "completed": False,
                        "created_at": now.isoformat(),
                    }))
                    quests_created += 1

        result = {
            "status": "success",
            "quests_created": quests_created,
            "users_processed": len(active_users),
            "timestamp": now.isoformat()
        }

        logger.info(f"Daily quest generation complete: {quests_created} quests for {len(active_users)} users")
        return result

    except Exception as e:
        logger.error(f"Daily quest generation failed: {e}")
        return {"status": "error", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
    finally:
        db.close()


@celery_app.task(name="app.tasks.scheduled.update_leaderboard")
def update_leaderboard() -> Dict[str, Any]:
    """
    Recalculate and cache leaderboard standings.

    Updates Redis-cached leaderboard with current weekly XP rankings.
    Runs every 30 minutes.
    """
    db = get_db_session()
    try:
        from ..models.user import User

        logger.info("Starting leaderboard update...")

        now = datetime.utcnow()

        # Get top 100 users by XP
        top_users = db.query(User).filter(
            User.is_active == True
        ).order_by(User.xp.desc()).limit(100).all()

        leaderboard_data = []
        for rank, user in enumerate(top_users, 1):
            leaderboard_data.append({
                "rank": rank,
                "user_id": str(user.id),
                "username": user.username or user.display_name or "Cazador",
                "xp": user.xp or 0,
                "level": user.level or 1,
                "rank_title": getattr(user, 'rank', 'E'),
            })

        # Cache in Redis
        from ..core.redis_cache import get_redis
        redis = get_redis()
        if redis:
            import json
            redis.setex("leaderboard:global:top100", 300, json.dumps(leaderboard_data))

        result = {
            "status": "success",
            "entries": len(leaderboard_data),
            "top_user": leaderboard_data[0]["username"] if leaderboard_data else None,
            "timestamp": now.isoformat()
        }

        logger.info(f"Leaderboard update complete: {len(leaderboard_data)} entries cached")
        return result

    except Exception as e:
        logger.error(f"Leaderboard update failed: {e}")
        return {"status": "error", "error": str(e), "timestamp": datetime.utcnow().isoformat()}
    finally:
        db.close()


# ============================================
# CELERY BEAT SCHEDULE CONFIGURATION
# ============================================

celery_app.conf.beat_schedule = {
    # Regenerate hearts every hour (at minute 0)
    "regenerate-hearts-hourly": {
        "task": "app.tasks.scheduled.regenerate_hearts",
        "schedule": crontab(minute=0),  # Every hour at :00
        "options": {"queue": "default"}
    },

    # Process leagues every Monday at 00:00 (midnight)
    "process-leagues-weekly": {
        "task": "app.tasks.scheduled.process_weekly_leagues",
        "schedule": crontab(day_of_week=1, hour=0, minute=0),  # Monday 00:00
        "options": {"queue": "default"}
    },

    # Streak reminder at 6 PM (18:00)
    "streak-reminder-6pm": {
        "task": "app.tasks.scheduled.send_streak_reminders",
        "schedule": crontab(hour=18, minute=0),  # 6:00 PM daily
        "options": {"queue": "default"}
    },

    # Streak reminder at 9 PM (21:00)
    "streak-reminder-9pm": {
        "task": "app.tasks.scheduled.send_streak_reminders",
        "schedule": crontab(hour=21, minute=0),  # 9:00 PM daily
        "options": {"queue": "default"}
    },

    # Streak reminder at 3:30 AM (final warning before 4 AM reset)
    "streak-reminder-330am": {
        "task": "app.tasks.scheduled.send_streak_reminders",
        "schedule": crontab(hour=3, minute=30),  # 3:30 AM daily
        "options": {"queue": "default"}
    },

    # Daily reset at 4:00 AM (Bogotá time) - reset streaks and daily counters
    "daily-reset-4am": {
        "task": "app.tasks.scheduled.daily_reset_4am",
        "schedule": crontab(hour=4, minute=0),  # 4:00 AM daily
        "options": {"queue": "default"}
    },

    # Generate weekly boss every Sunday at 10:00 AM (start of Boss Raid event)
    "generate-weekly-boss": {
        "task": "app.tasks.scheduled.generate_weekly_boss",
        "schedule": crontab(day_of_week=0, hour=10, minute=0),  # Sunday 10:00 AM
        "options": {"queue": "default"}
    },

    # Monthly reassessment notifications - Day 1 of each month at 6:00 AM
    "monthly-reassessment-check": {
        "task": "app.tasks.scheduled.check_monthly_reassessments",
        "schedule": crontab(day_of_month=1, hour=6, minute=0),  # Day 1, 6:00 AM
        "options": {"queue": "default"}
    },

    # Generate daily quests at 4:05 AM (after daily reset)
    "generate-daily-quests": {
        "task": "app.tasks.scheduled.generate_daily_quests",
        "schedule": crontab(hour=4, minute=5),  # 4:05 AM daily
        "options": {"queue": "default"}
    },

    # Update leaderboard every 30 minutes
    "update-leaderboard": {
        "task": "app.tasks.scheduled.update_leaderboard",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "options": {"queue": "default"}
    },
}

# Configure default queue
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_queues = {
    "default": {
        "exchange": "default",
        "routing_key": "default",
    },
}
