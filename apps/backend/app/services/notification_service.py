"""
Push Notification Service for ICFES Leveling Mobile App
Firebase Cloud Messaging (FCM) Integration

Provides:
- Push notification sending via Firebase Admin SDK
- Template-based notification messages
- Device token management
- Notification history tracking
- DYNAMIC TIMING (LOGICA_DE_NEGOCIO.md): Optimal times based on user patterns

Dynamic Timing System:
- Learns from user activity patterns
- Sends notifications at optimal engagement times
- Avoids sending during known inactive periods
- Respects user timezone
"""

import logging
import os
from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
from datetime import datetime, timedelta, time
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

logger = logging.getLogger(__name__)


# =============================================================================
# DYNAMIC TIMING CONSTANTS (LOGICA_DE_NEGOCIO.md)
# =============================================================================

# Default notification windows if no user data available
DEFAULT_NOTIFICATION_WINDOWS = [
    (time(7, 30), time(8, 30)),    # Morning: 7:30-8:30 AM
    (time(12, 0), time(13, 0)),    # Lunch: 12:00-1:00 PM
    (time(18, 0), time(19, 0)),    # Evening: 6:00-7:00 PM
    (time(21, 0), time(22, 0)),    # Night: 9:00-10:00 PM
]

# Minimum activity data points needed for personalization
MIN_ACTIVITY_POINTS = 5

# Notification frequency limits (per day)
MAX_NOTIFICATIONS_PER_DAY = 3
MIN_HOURS_BETWEEN_NOTIFICATIONS = 4

# Activity analysis window
ACTIVITY_ANALYSIS_DAYS = 14

# Firebase Admin SDK initialization
# Will be initialized lazily when first notification is sent
_firebase_app = None


def _initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized."""
    global _firebase_app

    if _firebase_app is not None:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Check if already initialized
        try:
            _firebase_app = firebase_admin.get_app()
            return True
        except ValueError:
            pass  # App not initialized yet

        # Try to get credentials from environment variable
        cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        google_creds_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")

        if cred_path and os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized from credentials file")
            return True
        elif google_creds_json:
            import json
            cred_dict = json.loads(google_creds_json)
            cred = credentials.Certificate(cred_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized from JSON credentials")
            return True
        else:
            # Try default credentials (for Cloud Run, GKE, etc.)
            try:
                cred = credentials.ApplicationDefault()
                _firebase_app = firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized with default credentials")
                return True
            except Exception:
                logger.warning(
                    "Firebase credentials not found. Push notifications will be simulated. "
                    "Set FIREBASE_CREDENTIALS_PATH or GOOGLE_APPLICATION_CREDENTIALS_JSON environment variable."
                )
                return False

    except ImportError:
        logger.warning(
            "firebase-admin package not installed. Push notifications will be simulated. "
            "Install with: pip install firebase-admin"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
        return False


class NotificationService:
    """
    Push Notification Service via Firebase Cloud Messaging.

    Templates for ICFES Leveling notifications:
    - streak_at_risk_6pm: Evening reminder for users who haven't practiced
    - streak_at_risk_9pm: Late evening reminder (more urgent)
    - streak_at_risk_330am: Last chance reminder before daily reset
    - hearts_refilled: Notification when hearts are fully regenerated
    - league_promotion: Celebration for league advancement
    - boss_raid_starting: Weekly boss raid event notification
    """

    TEMPLATES: Dict[str, Dict[str, str]] = {
        "streak_at_risk_6pm": {
            "title": "Tu racha esta en peligro!",
            "body": "Los Cazadores no descansan. Tu racha de {streak} dias te espera."
        },
        "streak_at_risk_9pm": {
            "title": "Los Cazadores debiles pierden su racha hoy",
            "body": "Ultima llamada, Cazador. Tu tienes {streak} dias de racha."
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
        "boss_raid_starting": {
            "title": "Boss Raid comenzando!",
            "body": "El Jefe {boss_name} ha aparecido. XP x3 disponible."
        },
        # Additional templates for completeness
        "daily_goal_achieved": {
            "title": "Meta diaria completada!",
            "body": "Has ganado {xp} XP hoy. Excelente trabajo, Cazador!"
        },
        "level_up": {
            "title": "Has subido de nivel!",
            "body": "Ahora eres nivel {level}. Nuevos desafios te esperan."
        },
        "new_content_available": {
            "title": "Nuevo contenido disponible",
            "body": "Hay nuevas preguntas de {subject} esperandote."
        },
        "weekly_summary": {
            "title": "Resumen semanal",
            "body": "Esta semana: {xp} XP, {questions} preguntas, {streak} dias de racha."
        },
        "achievement_unlocked": {
            "title": "Logro desbloqueado!",
            "body": "Has obtenido: {achievement_name}"
        },
    }

    def __init__(self, db: Session = None):
        """
        Initialize NotificationService.

        Args:
            db: SQLAlchemy database session (optional, needed for database operations)
        """
        self.db = db
        self._firebase_initialized = False

    # =========================================================================
    # DYNAMIC TIMING SYSTEM (LOGICA_DE_NEGOCIO.md)
    # =========================================================================

    def get_optimal_notification_time(self, user_id: UUID) -> Tuple[time, str]:
        """
        Calculate the optimal time to send a notification to this user.

        Uses user activity patterns to determine when they're most likely to engage.

        Returns:
            Tuple of (optimal_time, reasoning)
        """
        if not self.db:
            return DEFAULT_NOTIFICATION_WINDOWS[2][0], "default_no_db"

        try:
            # Get user's activity patterns
            activity_data = self._get_user_activity_patterns(user_id)

            if len(activity_data) < MIN_ACTIVITY_POINTS:
                # Not enough data, use defaults
                return DEFAULT_NOTIFICATION_WINDOWS[2][0], "default_insufficient_data"

            # Calculate most active hours
            hour_counts = defaultdict(int)
            for activity in activity_data:
                hour = activity.hour
                hour_counts[hour] += 1

            # Find the hour with highest engagement
            best_hour = max(hour_counts, key=hour_counts.get)

            # Check if we should avoid this hour (too many notifications recently)
            if self._check_notification_fatigue(user_id, best_hour):
                # Use second best hour
                del hour_counts[best_hour]
                if hour_counts:
                    best_hour = max(hour_counts, key=hour_counts.get)
                else:
                    return DEFAULT_NOTIFICATION_WINDOWS[2][0], "fallback_fatigue"

            # Add some randomization within the hour (avoid exact times)
            import random
            minute = random.randint(0, 45)

            return time(best_hour, minute), f"learned_hour_{best_hour}"

        except Exception as e:
            logger.error(f"Error calculating optimal notification time: {e}")
            return DEFAULT_NOTIFICATION_WINDOWS[2][0], "error_fallback"

    def _get_user_activity_patterns(self, user_id: UUID) -> List[datetime]:
        """
        Get user's activity timestamps from the last N days.
        """
        try:
            from ..models.mobile_offline import UserActivityLog

            cutoff = datetime.utcnow() - timedelta(days=ACTIVITY_ANALYSIS_DAYS)

            result = self.db.query(UserActivityLog.created_at).filter(
                and_(
                    UserActivityLog.user_id == user_id,
                    UserActivityLog.created_at >= cutoff
                )
            ).all()

            return [r[0] for r in result]

        except Exception:
            # Table might not exist, return empty
            return []

    def _check_notification_fatigue(self, user_id: UUID, hour: int) -> bool:
        """
        Check if user has received too many notifications at this hour recently.
        """
        try:
            from ..models.mobile_offline import NotificationHistory

            # Check last 3 days
            cutoff = datetime.utcnow() - timedelta(days=3)

            count = self.db.query(NotificationHistory).filter(
                and_(
                    NotificationHistory.user_id == user_id,
                    NotificationHistory.created_at >= cutoff,
                    func.extract('hour', NotificationHistory.created_at) == hour
                )
            ).count()

            # More than 2 notifications at this hour in 3 days = fatigue
            return count >= 2

        except Exception:
            return False

    def should_send_notification_now(self, user_id: UUID) -> Tuple[bool, str]:
        """
        Determine if we should send a notification right now.

        Checks:
        1. Daily limit not exceeded
        2. Minimum time between notifications respected
        3. Current time is within optimal window

        Returns:
            Tuple of (should_send, reason)
        """
        if not self.db:
            return True, "no_db_check"

        try:
            from ..models.mobile_offline import NotificationHistory

            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Check daily limit
            today_count = self.db.query(NotificationHistory).filter(
                and_(
                    NotificationHistory.user_id == user_id,
                    NotificationHistory.created_at >= today_start,
                    NotificationHistory.success == True
                )
            ).count()

            if today_count >= MAX_NOTIFICATIONS_PER_DAY:
                return False, "daily_limit_exceeded"

            # Check minimum time between notifications
            min_time_cutoff = now - timedelta(hours=MIN_HOURS_BETWEEN_NOTIFICATIONS)
            recent = self.db.query(NotificationHistory).filter(
                and_(
                    NotificationHistory.user_id == user_id,
                    NotificationHistory.created_at >= min_time_cutoff,
                    NotificationHistory.success == True
                )
            ).first()

            if recent:
                return False, "too_soon_since_last"

            return True, "approved"

        except Exception as e:
            logger.error(f"Error checking notification timing: {e}")
            return True, "error_allow"

    def get_notification_schedule(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get the recommended notification schedule for a user.

        Returns schedule with optimal times and next notification window.
        """
        optimal_time, reason = self.get_optimal_notification_time(user_id)
        should_send, send_reason = self.should_send_notification_now(user_id)

        # Calculate next optimal send time
        now = datetime.utcnow()
        next_optimal = now.replace(
            hour=optimal_time.hour,
            minute=optimal_time.minute,
            second=0,
            microsecond=0
        )

        if next_optimal <= now:
            next_optimal += timedelta(days=1)

        return {
            "optimal_hour": optimal_time.hour,
            "optimal_minute": optimal_time.minute,
            "optimization_reason": reason,
            "can_send_now": should_send,
            "send_restriction_reason": send_reason if not should_send else None,
            "next_optimal_time": next_optimal.isoformat(),
            "notifications_today": self._get_today_notification_count(user_id),
            "max_notifications_per_day": MAX_NOTIFICATIONS_PER_DAY,
        }

    def _get_today_notification_count(self, user_id: UUID) -> int:
        """Get count of notifications sent to user today."""
        if not self.db:
            return 0

        try:
            from ..models.mobile_offline import NotificationHistory

            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            return self.db.query(NotificationHistory).filter(
                and_(
                    NotificationHistory.user_id == user_id,
                    NotificationHistory.created_at >= today_start,
                    NotificationHistory.success == True
                )
            ).count()

        except Exception:
            return 0

    def schedule_smart_notification(
        self,
        user_id: UUID,
        template: str,
        data: Optional[Dict[str, Any]] = None,
        priority: str = "normal"
    ) -> Dict[str, Any]:
        """
        Schedule a notification with smart timing.

        High priority notifications are sent immediately if allowed.
        Normal priority notifications wait for optimal time.

        Args:
            user_id: User's UUID
            template: Template name
            data: Template data
            priority: "high" for immediate, "normal" for optimal timing

        Returns:
            Schedule info with send time
        """
        should_send, reason = self.should_send_notification_now(user_id)

        if priority == "high" and should_send:
            # Send immediately
            success = self.send(user_id, template, data)
            return {
                "sent_immediately": True,
                "success": success,
                "priority": priority,
            }

        if not should_send:
            # Get next available window
            schedule = self.get_notification_schedule(user_id)
            return {
                "sent_immediately": False,
                "scheduled_for": schedule["next_optimal_time"],
                "reason": reason,
                "priority": priority,
            }

        # Normal priority - wait for optimal time
        optimal_time, _ = self.get_optimal_notification_time(user_id)
        now = datetime.utcnow()
        current_hour = now.hour

        # If we're within 2 hours of optimal time, send now
        hour_diff = abs(optimal_time.hour - current_hour)
        if hour_diff <= 2:
            success = self.send(user_id, template, data)
            return {
                "sent_immediately": True,
                "success": success,
                "priority": priority,
                "near_optimal": True,
            }

        # Schedule for optimal time
        schedule = self.get_notification_schedule(user_id)
        return {
            "sent_immediately": False,
            "scheduled_for": schedule["next_optimal_time"],
            "priority": priority,
        }

    def _ensure_firebase(self) -> bool:
        """Ensure Firebase is initialized."""
        if not self._firebase_initialized:
            self._firebase_initialized = _initialize_firebase()
        return self._firebase_initialized

    def get_user_device(self, user_id: UUID) -> Optional[Any]:
        """
        Get user's active device token from database.

        Args:
            user_id: User's UUID

        Returns:
            UserDeviceToken model or None if not found
        """
        if not self.db:
            logger.warning("Database session not provided to NotificationService")
            return None

        try:
            from ..models.mobile_offline import UserDeviceToken

            result = self.db.execute(
                select(UserDeviceToken)
                .where(
                    UserDeviceToken.user_id == user_id,
                    UserDeviceToken.is_active == True
                )
                .order_by(UserDeviceToken.last_used_at.desc())
            )
            device = result.scalar()
            return device

        except Exception as e:
            logger.error(f"Error fetching user device token: {e}")
            return None

    def send(
        self,
        user_id: UUID,
        template: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a push notification to a user using a template.

        Args:
            user_id: User's UUID
            template: Template name from TEMPLATES dict
            data: Dictionary with template variables and additional data

        Returns:
            True if notification was sent successfully, False otherwise
        """
        # Get template
        template_data = self.TEMPLATES.get(template)
        if not template_data:
            logger.error(f"Unknown notification template: {template}")
            return False

        # Get user's device token
        user_device = self.get_user_device(user_id)
        if not user_device or not user_device.device_token:
            logger.info(f"No device token found for user {user_id}")
            return False

        # Format title and body with provided data
        format_data = data or {}
        try:
            title = template_data["title"].format(**format_data)
            body = template_data["body"].format(**format_data)
        except KeyError as e:
            logger.error(f"Missing template variable {e} for template {template}")
            return False

        # Send notification
        success = self._send_fcm_notification(
            token=user_device.device_token,
            title=title,
            body=body,
            data=data
        )

        # Log notification in history
        if success and self.db:
            self._log_notification_history(
                user_id=user_id,
                notification_type=template,
                title=title,
                body=body,
                data=data,
                platform=user_device.platform,
                success=True
            )

        return success

    def send_custom(
        self,
        user_id: UUID,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a custom push notification (not using a template).

        Args:
            user_id: User's UUID
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            True if notification was sent successfully, False otherwise
        """
        # Get user's device token
        user_device = self.get_user_device(user_id)
        if not user_device or not user_device.device_token:
            logger.info(f"No device token found for user {user_id}")
            return False

        # Send notification
        success = self._send_fcm_notification(
            token=user_device.device_token,
            title=title,
            body=body,
            data=data
        )

        # Log notification in history
        if success and self.db:
            self._log_notification_history(
                user_id=user_id,
                notification_type="custom",
                title=title,
                body=body,
                data=data,
                platform=user_device.platform,
                success=True
            )

        return success

    def send_to_multiple(
        self,
        user_ids: List[UUID],
        template: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple users.

        Args:
            user_ids: List of user UUIDs
            template: Template name from TEMPLATES dict
            data: Dictionary with template variables

        Returns:
            Dictionary with success and failure counts
        """
        success_count = 0
        failure_count = 0

        for user_id in user_ids:
            try:
                if self.send(user_id, template, data):
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")
                failure_count += 1

        return {
            "total": len(user_ids),
            "success": success_count,
            "failure": failure_count
        }

    def _send_fcm_notification(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send FCM notification via Firebase Admin SDK.

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._ensure_firebase():
            # Simulate notification in development
            logger.info(f"[SIMULATED] FCM Notification: {title} - {body}")
            return True

        try:
            from firebase_admin import messaging

            # Build the message
            notification = messaging.Notification(
                title=title,
                body=body
            )

            # Convert data values to strings (FCM requirement)
            string_data = None
            if data:
                string_data = {k: str(v) for k, v in data.items()}

            message = messaging.Message(
                notification=notification,
                token=token,
                data=string_data,
                android=messaging.AndroidConfig(
                    priority="high",
                    notification=messaging.AndroidNotification(
                        icon="notification_icon",
                        color="#6366f1",  # ICFES Leveling primary color
                        channel_id="icfes_leveling_notifications"
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1
                        )
                    )
                )
            )

            # Send the message
            response = messaging.send(message)
            logger.info(f"Successfully sent FCM notification: {response}")
            return True

        except Exception as e:
            logger.error(f"Failed to send FCM notification: {e}")
            return False

    def _log_notification_history(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        body: str,
        data: Optional[Dict[str, Any]],
        platform: str,
        success: bool,
        error_message: Optional[str] = None
    ) -> None:
        """Log notification to history table."""
        if not self.db:
            return

        try:
            from ..models.mobile_offline import NotificationHistory

            history = NotificationHistory(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                body=body,
                data=data,
                platform=platform,
                success=success,
                error_message=error_message
            )

            self.db.add(history)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log notification history: {e}")
            # Don't fail the notification if logging fails
            try:
                self.db.rollback()
            except Exception:
                pass

    def register_device_token(
        self,
        user_id: UUID,
        token: str,
        platform: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register or update a device token for push notifications.

        Args:
            user_id: User's UUID
            token: FCM device token
            platform: 'ios' or 'android'
            device_info: Optional device information (model, os_version, etc.)

        Returns:
            True if registration was successful, False otherwise
        """
        if not self.db:
            logger.error("Database session not provided to NotificationService")
            return False

        try:
            from ..models.mobile_offline import UserDeviceToken

            # Check if token already exists
            existing = self.db.execute(
                select(UserDeviceToken).where(UserDeviceToken.device_token == token)
            ).scalar()

            if existing:
                # Update existing token
                existing.user_id = user_id
                existing.platform = platform
                existing.device_info = device_info
                existing.is_active = True
                existing.last_used_at = datetime.utcnow()
            else:
                # Deactivate old tokens for this user on same platform
                self.db.execute(
                    select(UserDeviceToken)
                    .where(
                        UserDeviceToken.user_id == user_id,
                        UserDeviceToken.platform == platform,
                        UserDeviceToken.is_active == True
                    )
                )
                old_tokens = self.db.query(UserDeviceToken).filter(
                    UserDeviceToken.user_id == user_id,
                    UserDeviceToken.platform == platform,
                    UserDeviceToken.is_active == True
                ).all()

                for old_token in old_tokens:
                    old_token.is_active = False

                # Create new token
                new_token = UserDeviceToken(
                    user_id=user_id,
                    device_token=token,
                    platform=platform,
                    device_info=device_info,
                    is_active=True,
                    last_used_at=datetime.utcnow()
                )
                self.db.add(new_token)

            self.db.commit()
            logger.info(f"Device token registered for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to register device token: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
            return False

    def unregister_device_token(
        self,
        user_id: UUID,
        token: Optional[str] = None
    ) -> bool:
        """
        Unregister a device token.

        Args:
            user_id: User's UUID
            token: Specific token to unregister, or None to unregister all

        Returns:
            True if successful, False otherwise
        """
        if not self.db:
            logger.error("Database session not provided to NotificationService")
            return False

        try:
            from ..models.mobile_offline import UserDeviceToken

            if token:
                # Deactivate specific token
                device = self.db.query(UserDeviceToken).filter(
                    UserDeviceToken.user_id == user_id,
                    UserDeviceToken.device_token == token
                ).first()

                if device:
                    device.is_active = False
            else:
                # Deactivate all tokens for user
                devices = self.db.query(UserDeviceToken).filter(
                    UserDeviceToken.user_id == user_id,
                    UserDeviceToken.is_active == True
                ).all()

                for device in devices:
                    device.is_active = False

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to unregister device token: {e}")
            try:
                self.db.rollback()
            except Exception:
                pass
            return False


# Singleton instance for use throughout the application
notification_service = NotificationService()
