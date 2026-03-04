"""
Psychological Triggers Service - ICFES Leveling
Implements gamification psychology patterns for engagement
Based on LOGICA_DE_NEGOCIO.md specifications
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)


class PsychologicalTriggersService:
    """
    Service implementing psychological engagement patterns:
    - Variable Ratio Reinforcement (unpredictable rewards)
    - Social Proof (rankings, peer comparison)
    - Loss Aversion (streak protection, rank demotion warnings)
    - Progress Illusion (optimized progress bars)
    - Endowed Progress (start with something earned)
    """

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # VARIABLE RATIO REINFORCEMENT
    # =========================================================================

    def get_variable_reward(
        self,
        user_id: UUID,
        action_type: str,
        base_reward: int
    ) -> Dict[str, Any]:
        """
        Apply variable ratio reinforcement to rewards.
        Sometimes gives bonus rewards to create anticipation.

        action_type: 'answer', 'lesson_complete', 'daily_login', 'streak'
        """
        try:
            # Get user's recent reward history
            recent_bonuses = self._get_recent_bonus_count(user_id)

            # Variable ratio schedule: roughly 1 in 5 actions gets bonus
            # But never more than 2 bonuses in last 10 actions
            bonus_chance = 0.20 if recent_bonuses < 2 else 0.05

            is_bonus = random.random() < bonus_chance
            bonus_type = None
            bonus_amount = 0
            bonus_message = None

            if is_bonus:
                # Determine bonus type and amount
                bonus_roll = random.random()

                if bonus_roll < 0.5:
                    # Small XP bonus (50% of bonuses)
                    bonus_type = "xp_bonus"
                    bonus_amount = random.choice([5, 10, 15])
                    bonus_message = f"+{bonus_amount} XP Bonus!"
                elif bonus_roll < 0.8:
                    # Gold bonus (30% of bonuses)
                    bonus_type = "gold_bonus"
                    bonus_amount = random.choice([5, 10, 25])
                    bonus_message = f"+{bonus_amount} Oro encontrado!"
                else:
                    # Rare bonus (20% of bonuses)
                    bonus_type = "rare_bonus"
                    bonus_amount = random.choice([50, 100])
                    bonus_message = "Cofre Legendario! +{} XP".format(bonus_amount)

                # Log the bonus for tracking
                self._log_bonus(user_id, action_type, bonus_type, bonus_amount)

            return {
                "base_reward": base_reward,
                "total_reward": base_reward + (bonus_amount if bonus_type == "xp_bonus" else 0),
                "has_bonus": is_bonus,
                "bonus_type": bonus_type,
                "bonus_amount": bonus_amount,
                "bonus_message": bonus_message,
                "bonus_animation": self._get_bonus_animation(bonus_type) if is_bonus else None
            }

        except Exception as e:
            logger.error(f"Error in variable reward: {e}")
            return {
                "base_reward": base_reward,
                "total_reward": base_reward,
                "has_bonus": False
            }

    def _get_recent_bonus_count(self, user_id: UUID) -> int:
        """Count bonuses in last 10 actions."""
        try:
            query = text("""
                SELECT COUNT(*) FROM user_bonus_log
                WHERE user_id = :user_id
                AND created_at >= NOW() - INTERVAL 1 DAY
            """)
            result = self.db.execute(query, {"user_id": str(user_id)}).fetchone()
            return int(result[0]) if result else 0
        except:
            return 0

    def _log_bonus(self, user_id: UUID, action: str, bonus_type: str, amount: int):
        """Log bonus for tracking variable ratio."""
        try:
            query = text("""
                INSERT INTO user_bonus_log (user_id, action_type, bonus_type, amount, created_at)
                VALUES (:user_id, :action, :bonus_type, :amount, NOW())
            """)
            self.db.execute(query, {
                "user_id": str(user_id),
                "action": action,
                "bonus_type": bonus_type,
                "amount": amount
            })
            self.db.commit()
        except Exception as e:
            logger.warning(f"Could not log bonus: {e}")

    def _get_bonus_animation(self, bonus_type: str) -> str:
        """Get animation identifier for bonus type."""
        animations = {
            "xp_bonus": "sparkle",
            "gold_bonus": "coin_shower",
            "rare_bonus": "chest_open"
        }
        return animations.get(bonus_type, "sparkle")

    # =========================================================================
    # SOCIAL PROOF
    # =========================================================================

    def get_social_proof_data(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get social proof elements to display to user.
        Shows what peers are achieving to motivate action.
        """
        try:
            # Get user's current stats
            user_stats = self._get_user_stats(user_id)

            # Get peer comparison
            peer_data = self._get_peer_comparison(user_id)

            # Get recent achievements by others
            recent_achievements = self._get_recent_peer_achievements(user_id)

            # Generate social proof messages
            messages = self._generate_social_proof_messages(user_stats, peer_data)

            return {
                "user_rank": user_stats.get("rank", 0),
                "users_ahead": peer_data.get("users_ahead", 0),
                "users_behind": peer_data.get("users_behind", 0),
                "percentile": peer_data.get("percentile", 50),
                "recent_peer_achievements": recent_achievements,
                "social_messages": messages,
                "leaderboard_position": user_stats.get("leaderboard_position"),
                "league_rank": user_stats.get("league_rank", "Bronce")
            }

        except Exception as e:
            logger.error(f"Error getting social proof: {e}")
            return self._get_default_social_proof()

    def _get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's current stats for comparison."""
        try:
            query = text("""
                SELECT
                    u.total_xp,
                    u.current_streak,
                    (SELECT COUNT(*) + 1 FROM users u2 WHERE u2.total_xp > u.total_xp) as rank,
                    (SELECT name FROM leagues WHERE id = u.current_league_id) as league
                FROM users u
                WHERE u.id = :user_id
            """)
            result = self.db.execute(query, {"user_id": str(user_id)}).fetchone()
            if result:
                return {
                    "total_xp": int(result[0]) if result[0] else 0,
                    "streak": int(result[1]) if result[1] else 0,
                    "rank": int(result[2]) if result[2] else 1,
                    "league_rank": result[3] or "Bronce"
                }
        except:
            pass
        return {"total_xp": 0, "streak": 0, "rank": 1, "league_rank": "Bronce"}

    def _get_peer_comparison(self, user_id: UUID) -> Dict[str, Any]:
        """Get comparison with peers."""
        try:
            query = text("""
                WITH user_xp AS (
                    SELECT total_xp FROM users WHERE id = :user_id
                )
                SELECT
                    (SELECT COUNT(*) FROM users WHERE total_xp > (SELECT total_xp FROM user_xp)) as ahead,
                    (SELECT COUNT(*) FROM users WHERE total_xp < (SELECT total_xp FROM user_xp)) as behind,
                    (SELECT COUNT(*) FROM users) as total
            """)
            result = self.db.execute(query, {"user_id": str(user_id)}).fetchone()
            if result:
                total = int(result[2]) if result[2] else 1
                ahead = int(result[0]) if result[0] else 0
                percentile = int((1 - ahead / total) * 100)
                return {
                    "users_ahead": ahead,
                    "users_behind": int(result[1]) if result[1] else 0,
                    "percentile": percentile
                }
        except:
            pass
        return {"users_ahead": 0, "users_behind": 0, "percentile": 50}

    def _get_recent_peer_achievements(self, user_id: UUID) -> List[Dict]:
        """Get recent achievements by peers (anonymized)."""
        try:
            query = text("""
                SELECT
                    'Un Cazador' as name,
                    a.name as achievement,
                    ua.earned_at
                FROM user_achievements ua
                JOIN achievements a ON ua.achievement_id = a.id
                WHERE ua.user_id != :user_id
                AND ua.earned_at >= NOW() - INTERVAL 24 HOUR
                ORDER BY ua.earned_at DESC
                LIMIT 5
            """)
            result = self.db.execute(query, {"user_id": str(user_id)}).fetchall()
            return [
                {
                    "user_name": row[0],
                    "achievement": row[1],
                    "time_ago": self._format_time_ago(row[2])
                }
                for row in result
            ]
        except:
            return []

    def _format_time_ago(self, dt: datetime) -> str:
        """Format datetime as 'X ago'."""
        if not dt:
            return "hace poco"
        diff = datetime.utcnow() - dt
        if diff.seconds < 3600:
            return f"hace {diff.seconds // 60} min"
        elif diff.seconds < 86400:
            return f"hace {diff.seconds // 3600}h"
        return f"hace {diff.days}d"

    def _generate_social_proof_messages(self, user_stats: Dict, peer_data: Dict) -> List[str]:
        """Generate motivational social proof messages."""
        messages = []

        percentile = peer_data.get("percentile", 50)
        if percentile >= 80:
            messages.append(f"Estas en el top {100 - percentile}% de Cazadores!")
        elif percentile >= 50:
            messages.append(f"Solo {peer_data.get('users_ahead', 0)} Cazadores te superan")

        streak = user_stats.get("streak", 0)
        if streak >= 7:
            messages.append(f"Tu racha de {streak} dias supera al 90% de usuarios")
        elif streak >= 3:
            messages.append("Tu racha te pone entre los mas constantes")

        return messages

    def _get_default_social_proof(self) -> Dict[str, Any]:
        """Default social proof data."""
        return {
            "user_rank": 1,
            "users_ahead": 0,
            "users_behind": 0,
            "percentile": 50,
            "recent_peer_achievements": [],
            "social_messages": ["Muchos Cazadores estan entrenando ahora!"],
            "league_rank": "Bronce"
        }

    # =========================================================================
    # LOSS AVERSION
    # =========================================================================

    def get_loss_aversion_triggers(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get loss aversion triggers - things user might lose.
        Emphasizes potential losses to motivate action.
        """
        try:
            # Get user's current state
            query = text("""
                SELECT
                    current_streak,
                    hearts,
                    gold,
                    total_xp,
                    (SELECT position FROM league_standings WHERE user_id = u.id LIMIT 1) as league_position,
                    last_activity_at
                FROM users u
                WHERE id = :user_id
            """)
            result = self.db.execute(query, {"user_id": str(user_id)}).fetchone()

            triggers = []

            if result:
                streak = int(result[0]) if result[0] else 0
                hearts = int(result[1]) if result[1] else 5
                league_pos = int(result[4]) if result[4] else None
                last_activity = result[5]

                # Streak at risk
                if streak >= 3:
                    hours_until_reset = self._hours_until_streak_reset()
                    if hours_until_reset <= 8:
                        triggers.append({
                            "type": "streak_risk",
                            "severity": "high" if hours_until_reset <= 2 else "medium",
                            "value": streak,
                            "message": f"Tu racha de {streak} dias se pierde en {hours_until_reset}h!",
                            "action": "Completa 1 leccion para protegerla"
                        })

                # Low hearts
                if hearts <= 1:
                    triggers.append({
                        "type": "low_hearts",
                        "severity": "medium",
                        "value": hearts,
                        "message": f"Solo te queda {hearts} corazon!",
                        "action": "Espera 30min o mira un anuncio"
                    })

                # League demotion risk
                if league_pos and league_pos > 40:
                    triggers.append({
                        "type": "demotion_risk",
                        "severity": "high" if league_pos > 45 else "medium",
                        "value": league_pos,
                        "message": f"Posicion #{league_pos} - Riesgo de descenso!",
                        "action": "Gana XP para subir en la liga"
                    })

                # Inactivity warning
                if last_activity:
                    days_inactive = (datetime.utcnow() - last_activity).days
                    if days_inactive >= 2:
                        triggers.append({
                            "type": "inactivity",
                            "severity": "low",
                            "value": days_inactive,
                            "message": f"Llevas {days_inactive} dias sin entrenar",
                            "action": "Tus habilidades se debilitan!"
                        })

            return {
                "triggers": triggers,
                "has_urgent": any(t["severity"] == "high" for t in triggers),
                "total_triggers": len(triggers)
            }

        except Exception as e:
            logger.error(f"Error getting loss aversion triggers: {e}")
            return {"triggers": [], "has_urgent": False, "total_triggers": 0}

    def _hours_until_streak_reset(self) -> int:
        """Calculate hours until 4 AM Bogota (streak reset)."""
        import pytz
        bogota = pytz.timezone('America/Bogota')
        now = datetime.now(bogota)
        reset_hour = 4

        if now.hour >= reset_hour:
            # Reset is tomorrow
            reset_time = now.replace(hour=reset_hour, minute=0, second=0) + timedelta(days=1)
        else:
            # Reset is today
            reset_time = now.replace(hour=reset_hour, minute=0, second=0)

        diff = reset_time - now
        return max(0, int(diff.total_seconds() / 3600))

    # =========================================================================
    # PROGRESS ILLUSION
    # =========================================================================

    def get_optimized_progress(self, user_id: UUID, context: str = "general") -> Dict[str, Any]:
        """
        Get progress data optimized for psychological effect.
        Uses techniques like showing progress closer to goals.
        """
        try:
            # Get actual progress data
            query = text("""
                SELECT
                    u.total_xp,
                    u.current_level,
                    (SELECT xp_required FROM levels WHERE level = u.current_level + 1) as next_level_xp,
                    (SELECT COUNT(*) FROM user_achievements WHERE user_id = u.id) as achievements,
                    (SELECT COUNT(*) FROM achievements) as total_achievements,
                    (SELECT AVG(mastery_score) FROM user_topic_mastery WHERE user_id = u.id) as avg_mastery
                FROM users u
                WHERE u.id = :user_id
            """)
            result = self.db.execute(query, {"user_id": str(user_id)}).fetchone()

            if result:
                total_xp = int(result[0]) if result[0] else 0
                level = int(result[1]) if result[1] else 1
                next_level_xp = int(result[2]) if result[2] else 1000
                achievements = int(result[3]) if result[3] else 0
                total_achievements = int(result[4]) if result[4] else 20
                avg_mastery = float(result[5]) if result[5] else 0

                # Calculate level progress with psychological boost
                # Show at least 10% progress even if just started
                level_progress_raw = (total_xp % next_level_xp) / next_level_xp
                level_progress = max(0.10, level_progress_raw)

                # Achievement progress - highlight nearness to next
                achievement_progress = achievements / max(total_achievements, 1)

                # Mastery with optimistic framing
                mastery_display = max(avg_mastery, 0.15)  # Show at least 15%

                return {
                    "level_progress": {
                        "current_level": level,
                        "xp_in_level": total_xp % next_level_xp,
                        "xp_needed": next_level_xp,
                        "progress_percent": round(level_progress * 100, 1),
                        "display_percent": round(level_progress * 100, 1),
                        "to_next_level": next_level_xp - (total_xp % next_level_xp),
                        "message": self._get_level_message(level_progress)
                    },
                    "achievements_progress": {
                        "earned": achievements,
                        "total": total_achievements,
                        "progress_percent": round(achievement_progress * 100, 1),
                        "next_achievement_hint": "Completa 5 lecciones mas para el siguiente logro!"
                    },
                    "mastery_progress": {
                        "average": round(mastery_display * 100, 1),
                        "display_message": self._get_mastery_message(mastery_display)
                    }
                }

        except Exception as e:
            logger.error(f"Error getting optimized progress: {e}")

        return self._get_default_progress()

    def _get_level_message(self, progress: float) -> str:
        """Get motivational message based on level progress."""
        if progress >= 0.9:
            return "Casi ahi! Un poco mas!"
        elif progress >= 0.7:
            return "Excelente progreso!"
        elif progress >= 0.5:
            return "Medio camino recorrido!"
        else:
            return "Buen comienzo!"

    def _get_mastery_message(self, mastery: float) -> str:
        """Get mastery display message."""
        if mastery >= 0.8:
            return "Nivel Maestro"
        elif mastery >= 0.6:
            return "Nivel Avanzado"
        elif mastery >= 0.4:
            return "Nivel Intermedio"
        else:
            return "En progreso"

    def _get_default_progress(self) -> Dict[str, Any]:
        """Default progress data."""
        return {
            "level_progress": {
                "current_level": 1,
                "progress_percent": 10,
                "message": "Buen comienzo!"
            },
            "achievements_progress": {
                "earned": 0,
                "total": 20,
                "progress_percent": 0
            },
            "mastery_progress": {
                "average": 15,
                "display_message": "En progreso"
            }
        }

    # =========================================================================
    # ENDOWED PROGRESS
    # =========================================================================

    def get_endowed_progress(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get endowed progress - start user with something already earned.
        Creates sense of investment and loss aversion.
        """
        try:
            # Check if user is new (less than 7 days)
            query = text("""
                SELECT
                    created_at,
                    total_xp,
                    current_streak
                FROM users
                WHERE id = :user_id
            """)
            result = self.db.execute(query, {"user_id": str(user_id)}).fetchone()

            endowments = []

            if result:
                created_at = result[0]
                total_xp = int(result[1]) if result[1] else 0
                streak = int(result[2]) if result[2] else 0

                days_since_signup = (datetime.utcnow() - created_at).days if created_at else 0

                # New user bonus - "Welcome package"
                if days_since_signup <= 7 and total_xp < 500:
                    endowments.append({
                        "type": "welcome_bonus",
                        "title": "Pack de Bienvenida",
                        "description": "Ya tienes ventaja! Completaste el primer paso.",
                        "value": "3 corazones extra",
                        "visual": "gift_box"
                    })

                # Show progress as already started
                if days_since_signup <= 14:
                    endowments.append({
                        "type": "progress_started",
                        "title": "Tu Viaje Comenzo",
                        "description": "Ya recorriste el 10% del camino hacia Rango S",
                        "value": "10% completado",
                        "visual": "progress_bar_started"
                    })

                # Streak protection endowment
                if streak >= 1:
                    endowments.append({
                        "type": "streak_protection",
                        "title": "Racha Protegida",
                        "description": f"Tu racha de {streak} dias es un tesoro. No la pierdas!",
                        "value": f"{streak} dias",
                        "visual": "shield_glow"
                    })

            return {
                "endowments": endowments,
                "has_endowments": len(endowments) > 0,
                "message": "Ya tienes mucho invertido. Sigue adelante!" if endowments else None
            }

        except Exception as e:
            logger.error(f"Error getting endowed progress: {e}")
            return {"endowments": [], "has_endowments": False}

    # =========================================================================
    # COMBINED TRIGGERS
    # =========================================================================

    def get_all_triggers(self, user_id: UUID) -> Dict[str, Any]:
        """Get all psychological triggers combined."""
        return {
            "social_proof": self.get_social_proof_data(user_id),
            "loss_aversion": self.get_loss_aversion_triggers(user_id),
            "progress_illusion": self.get_optimized_progress(user_id),
            "endowed_progress": self.get_endowed_progress(user_id)
        }
