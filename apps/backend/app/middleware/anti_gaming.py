"""
Anti-Gaming Middleware
ICFES Leveling Backend

Prevents abuse of XP and rewards system.

Protections:
- Rate limit XP per hour
- Minimum answer time validation
- Random answering detection
- Daily session limits
"""

from datetime import datetime, timedelta, date
from typing import Dict, Tuple, List, Optional
import logging
import redis
import os

logger = logging.getLogger(__name__)


class AntiGamingMiddleware:
    """
    Middleware to prevent abuse of XP and rewards system.

    Protections implemented:
    - XP hourly rate limit (500 XP/hour max)
    - Minimum answer time (3 seconds)
    - Random answering detection (75%+ errors with <5s avg = suspicious)
    - Daily session limit (30 sessions/day)
    """

    # Configuration
    XP_HOURLY_LIMIT = 500
    MIN_ANSWER_TIME_MS = 3000  # 3 seconds minimum
    MAX_DAILY_SESSIONS = 30
    SUSPICIOUS_ERROR_RATE = 0.75  # 75% errors = suspicious
    SUSPICIOUS_SPEED_MS = 5000  # Average < 5s = suspicious

    # Ban thresholds (LOGICA_DE_NEGOCIO.md specification)
    WARNING_THRESHOLD = 3  # Warnings before temp ban
    TEMP_BAN_DURATION_HOURS = 24  # 24-hour temp ban
    HARD_BAN_THRESHOLD = 10  # Permanent ban after 10 incidents

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize with optional Redis client for rate limiting."""
        if redis_client:
            self.redis = redis_client
        else:
            # Try to connect to Redis, fallback to in-memory if unavailable
            try:
                redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
                self.redis = redis.from_url(redis_url, decode_responses=True)
                self.redis.ping()
            except Exception as e:
                logger.warning(f"Redis unavailable, using in-memory fallback: {e}")
                self.redis = None
                self._memory_store: Dict[str, any] = {}

    def _get(self, key: str) -> Optional[str]:
        """Get value from Redis or memory."""
        if self.redis:
            return self.redis.get(key)
        return self._memory_store.get(key)

    def _set(self, key: str, value: any, ex: int = None) -> None:
        """Set value in Redis or memory."""
        if self.redis:
            self.redis.set(key, value, ex=ex)
        else:
            self._memory_store[key] = value
            # Note: Memory store doesn't support TTL

    def _incr(self, key: str, amount: int = 1) -> int:
        """Increment value in Redis or memory."""
        if self.redis:
            return self.redis.incr(key, amount)
        else:
            current = int(self._memory_store.get(key, 0))
            new_value = current + amount
            self._memory_store[key] = new_value
            return new_value

    async def check_xp_rate(self, user_id: str, xp_to_add: int) -> bool:
        """
        Check if user is within hourly XP limit.

        Args:
            user_id: User UUID
            xp_to_add: XP amount to add

        Returns:
            True if within limit, False if rate limited
        """
        key = f"xp_rate:{user_id}:{datetime.now().hour}"

        current_xp = int(self._get(key) or 0)

        if current_xp + xp_to_add > self.XP_HOURLY_LIMIT:
            logger.warning(
                f"XP rate limit reached for user {user_id}: "
                f"{current_xp + xp_to_add} > {self.XP_HOURLY_LIMIT}"
            )
            return False

        self._incr(key, xp_to_add)
        if self.redis:
            self.redis.expire(key, 3600)  # Expire in 1 hour

        return True

    def validate_answer_time(self, response_time_ms: int) -> Tuple[bool, str]:
        """
        Validate that answer wasn't too fast.

        Args:
            response_time_ms: Response time in milliseconds

        Returns:
            (is_valid, message)
        """
        if response_time_ms < self.MIN_ANSWER_TIME_MS:
            return False, f"Response too fast: {response_time_ms}ms < {self.MIN_ANSWER_TIME_MS}ms minimum"
        return True, "OK"

    async def check_daily_sessions(self, user_id: str) -> bool:
        """
        Check if user is within daily session limit.

        Args:
            user_id: User UUID

        Returns:
            True if within limit
        """
        key = f"daily_sessions:{user_id}:{date.today().isoformat()}"

        current_count = int(self._get(key) or 0)

        if current_count >= self.MAX_DAILY_SESSIONS:
            logger.warning(f"Daily session limit reached for user {user_id}: {current_count}")
            return False

        self._incr(key)
        if self.redis:
            self.redis.expire(key, 86400)  # 24 hours

        return True

    async def detect_random_answering(self, user_id: str, db) -> Tuple[bool, Dict]:
        """
        Detect pattern of random/spam answering.

        Warning signs:
        - High error rate (>75%)
        - Very fast responses (<5s average)
        - Predictable answer patterns (ABABAB...)

        Args:
            user_id: User UUID
            db: Database session

        Returns:
            (is_suspicious, analysis_data)
        """
        from ..models.mobile_offline import UserQuestionHistory

        # Get last 20 answers
        recent_answers = db.query(UserQuestionHistory).filter(
            UserQuestionHistory.user_id == user_id
        ).order_by(UserQuestionHistory.created_at.desc()).limit(20).all()

        if len(recent_answers) < 10:
            return False, {"reason": "insufficient_data"}

        # Calculate metrics
        error_count = sum(1 for a in recent_answers if not a.was_correct)
        error_rate = error_count / len(recent_answers)

        valid_times = [
            a.time_spent_seconds * 1000
            for a in recent_answers
            if a.time_spent_seconds and a.time_spent_seconds > 0
        ]
        avg_time = sum(valid_times) / len(valid_times) if valid_times else 0

        # Detect answer pattern
        answers = [a.selected_answer for a in recent_answers if a.selected_answer]
        pattern_score = self._detect_pattern(answers)

        analysis = {
            "error_rate": error_rate,
            "avg_response_time_ms": avg_time,
            "pattern_score": pattern_score,
            "sample_size": len(recent_answers)
        }

        # Determine if suspicious
        is_suspicious = (
            (error_rate > self.SUSPICIOUS_ERROR_RATE and avg_time < self.SUSPICIOUS_SPEED_MS) or
            pattern_score > 0.8
        )

        if is_suspicious:
            logger.warning(f"Suspicious activity detected for user {user_id}: {analysis}")

            # Track in Redis
            key = f"suspicious_activity:{user_id}"
            self._incr(key)
            if self.redis:
                self.redis.expire(key, 86400 * 7)  # Keep for 1 week

        return is_suspicious, analysis

    def _detect_pattern(self, answers: List[str]) -> float:
        """
        Detect if answers follow a predictable pattern.

        Args:
            answers: List of answer strings (A, B, C, D)

        Returns:
            Score from 0.0 to 1.0 (1.0 = obvious pattern)
        """
        if len(answers) < 4:
            return 0.0

        # Check ABAB pattern
        pattern_abab = 0
        for i in range(len(answers) - 2):
            if answers[i] == answers[i + 2]:
                pattern_abab += 1

        # Check same answer repeated
        if answers:
            most_common = max(set(answers), key=answers.count)
            same_answer_rate = answers.count(most_common) / len(answers)
        else:
            same_answer_rate = 0

        # Check ordered sequence (A, B, C, D, A, B, C, D...)
        expected_sequence = ["A", "B", "C", "D"]
        sequence_matches = 0
        for i, answer in enumerate(answers):
            if answer and answer.upper() == expected_sequence[i % 4]:
                sequence_matches += 1
        sequence_rate = sequence_matches / len(answers) if answers else 0

        return max(
            pattern_abab / (len(answers) - 2) if len(answers) > 2 else 0,
            same_answer_rate if same_answer_rate > 0.6 else 0,
            sequence_rate if sequence_rate > 0.7 else 0
        )

    async def get_user_risk_score(self, user_id: str) -> Dict:
        """
        Get risk score for a user based on historical activity.

        Args:
            user_id: User UUID

        Returns:
            Risk analysis dictionary
        """
        suspicious_count = int(self._get(f"suspicious_activity:{user_id}") or 0)

        if suspicious_count >= 10:
            risk_level = "high"
        elif suspicious_count >= 5:
            risk_level = "medium"
        elif suspicious_count >= 1:
            risk_level = "low"
        else:
            risk_level = "none"

        return {
            "user_id": user_id,
            "suspicious_incidents": suspicious_count,
            "risk_level": risk_level
        }

    async def should_reduce_xp(self, user_id: str, db) -> Tuple[bool, float]:
        """
        Determine if XP should be reduced due to suspicious activity.

        Args:
            user_id: User UUID
            db: Database session

        Returns:
            (should_reduce, multiplier)
            - If should_reduce is True, multiply XP by the returned multiplier
            - multiplier of 0.5 means 50% XP reduction
        """
        risk = await self.get_user_risk_score(user_id)

        if risk["risk_level"] == "high":
            return True, 0.25  # 75% reduction
        elif risk["risk_level"] == "medium":
            return True, 0.5  # 50% reduction
        elif risk["risk_level"] == "low":
            return True, 0.75  # 25% reduction

        return False, 1.0  # No reduction

    # ====== HARD BAN SYSTEM (LOGICA_DE_NEGOCIO.md) ======

    async def check_ban_status(self, user_id: str) -> Dict:
        """
        Check if user is currently banned.

        Returns:
            Dict with is_banned, ban_type, ban_expires, reason
        """
        # Check for permanent ban
        perm_ban_key = f"permanent_ban:{user_id}"
        if self._get(perm_ban_key):
            return {
                "is_banned": True,
                "ban_type": "permanent",
                "ban_expires": None,
                "reason": "Actividad abusiva repetida detectada. Contacta soporte."
            }

        # Check for temporary ban
        temp_ban_key = f"temp_ban:{user_id}"
        temp_ban_expires = self._get(temp_ban_key)
        if temp_ban_expires:
            try:
                expires_dt = datetime.fromisoformat(temp_ban_expires)
                if datetime.now() < expires_dt:
                    return {
                        "is_banned": True,
                        "ban_type": "temporary",
                        "ban_expires": temp_ban_expires,
                        "reason": f"Suspendido temporalmente hasta {expires_dt.strftime('%Y-%m-%d %H:%M')}"
                    }
            except Exception:
                pass

        return {
            "is_banned": False,
            "ban_type": None,
            "ban_expires": None,
            "reason": None
        }

    async def apply_ban_if_needed(self, user_id: str) -> Dict:
        """
        Check suspicious activity count and apply ban if thresholds exceeded.

        Returns:
            Dict with action_taken, ban_type, message
        """
        suspicious_count = int(self._get(f"suspicious_activity:{user_id}") or 0)

        # Permanent ban threshold
        if suspicious_count >= self.HARD_BAN_THRESHOLD:
            perm_ban_key = f"permanent_ban:{user_id}"
            self._set(perm_ban_key, "true")  # No expiration
            logger.warning(f"PERMANENT BAN applied to user {user_id}: {suspicious_count} incidents")
            return {
                "action_taken": True,
                "ban_type": "permanent",
                "message": "Cuenta suspendida permanentemente por actividad abusiva."
            }

        # Temporary ban threshold
        if suspicious_count >= self.WARNING_THRESHOLD:
            temp_ban_key = f"temp_ban:{user_id}"
            expires_at = datetime.now() + timedelta(hours=self.TEMP_BAN_DURATION_HOURS)
            self._set(temp_ban_key, expires_at.isoformat(), ex=self.TEMP_BAN_DURATION_HOURS * 3600)
            logger.warning(f"TEMP BAN applied to user {user_id}: {suspicious_count} incidents, expires {expires_at}")
            return {
                "action_taken": True,
                "ban_type": "temporary",
                "message": f"Suspendido por 24 horas por actividad sospechosa ({suspicious_count} incidentes)."
            }

        return {
            "action_taken": False,
            "ban_type": None,
            "message": None
        }

    async def record_violation(self, user_id: str, violation_type: str, details: str = None) -> Dict:
        """
        Record a violation and check if ban should be applied.

        Args:
            user_id: User UUID
            violation_type: Type of violation (speed_hack, random_answering, xp_farming)
            details: Additional details

        Returns:
            Dict with violation_count, ban_status
        """
        # Increment violation counter
        key = f"suspicious_activity:{user_id}"
        count = self._incr(key)
        if self.redis:
            self.redis.expire(key, 86400 * 30)  # Keep for 30 days

        # Log violation
        logger.warning(f"Violation recorded for {user_id}: {violation_type} ({count} total). Details: {details}")

        # Check if ban should be applied
        ban_result = await self.apply_ban_if_needed(user_id)

        return {
            "violation_count": count,
            "violation_type": violation_type,
            "ban_applied": ban_result["action_taken"],
            "ban_type": ban_result["ban_type"],
            "message": ban_result["message"]
        }

    async def is_blocked(self, user_id: str) -> Tuple[bool, str]:
        """
        Quick check if user is blocked from performing actions.

        Returns:
            (is_blocked, reason)
        """
        ban_status = await self.check_ban_status(user_id)
        return ban_status["is_banned"], ban_status["reason"]


# Singleton instance for easy import
_anti_gaming_instance: Optional[AntiGamingMiddleware] = None


def get_anti_gaming() -> AntiGamingMiddleware:
    """Get or create singleton AntiGamingMiddleware instance."""
    global _anti_gaming_instance
    if _anti_gaming_instance is None:
        _anti_gaming_instance = AntiGamingMiddleware()
    return _anti_gaming_instance
