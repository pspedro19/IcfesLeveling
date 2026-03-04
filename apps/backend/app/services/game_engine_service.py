"""
Game Engine Service - Single Source of Truth for Game Mechanics
ICFES Leveling Backend

This service centralizes all core game logic, including calculations for
XP, levels, ranks, damage, and rewards. It resolves conflicting formulas
found in other parts of the codebase.
"""

import math
import logging
from typing import Tuple
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime # New import

from ..models.mobile_offline import UserQuestionHistory, UserTopicMastery

logger = logging.getLogger(__name__)

class GameEngineService:
    """
    Provides unified, definitive calculations for all game mechanics.
    """

    # ============================================
    # XP & LEVEL CALCULATION (UNIFIED)
    # ============================================

    # Source of Truth for XP: Based on xp_service.py (Anti-Gaming Rules)
    XP_NEW_QUESTION = 10
    XP_VALID_REVIEW = 5
    XP_INVALID_REPEAT = 0

    # Source of Truth for Streak Multipliers: Based on xp_service.py
    STREAK_MULTIPLIERS = {
        (1, 6): 1.0,
        (7, 13): 1.2,
        (14, 29): 1.5,
        (30, float('inf')): 2.0
    }

    @staticmethod
    def get_streak_multiplier(streak_days: int) -> float:
        """
        Gets the definitive XP multiplier based on streak days.
        """
        for (min_days, max_days), multiplier in GameEngineService.STREAK_MULTIPLIERS.items():
            if min_days <= streak_days <= max_days:
                return multiplier
        return 1.0

    @staticmethod
    def calculate_xp_for_answer(
        attempt_type: str,
        is_correct: bool,
        streak_days: int,
        in_grace_mode: bool = False
    ) -> int:
        """
        UNIFIED: Calculates XP earned for an answer based on the anti-gaming rules.
        """
        if not is_correct or in_grace_mode:
            return 0

        base_xp_map = {
            "new": GameEngineService.XP_NEW_QUESTION,
            "valid_review": GameEngineService.XP_VALID_REVIEW,
            "invalid_repeat": GameEngineService.XP_INVALID_REPEAT
        }
        base_xp = base_xp_map.get(attempt_type, 0)
        multiplier = GameEngineService.get_streak_multiplier(streak_days)
        final_xp = int(base_xp * multiplier)
        return final_xp

    @staticmethod
    def determine_attempt_type(db: Session, user_id: UUID, question_id: UUID, topic_id: UUID) -> str:
        """
        UNIFIED: Determines if an attempt is 'new', 'valid_review', or 'invalid_repeat'.
        """
        last_attempt = db.query(UserQuestionHistory).filter(
            UserQuestionHistory.user_id == user_id,
            UserQuestionHistory.question_id == question_id
        ).order_by(UserQuestionHistory.created_at.desc()).first()

        if not last_attempt:
            return "new"

        topic_mastery = db.query(UserTopicMastery).filter(
            UserTopicMastery.user_id == user_id,
            UserTopicMastery.topic_id == topic_id
        ).first()
        mastery_score = topic_mastery.mastery_score if topic_mastery else 0.0
        
        min_days_for_review = max(1, int(mastery_score * 7))
        days_since_last = (datetime.utcnow() - last_attempt.created_at).days

        return "valid_review" if days_since_last >= min_days_for_review else "invalid_repeat"


    @staticmethod
    def get_xp_breakdown(attempt_type: str, streak_days: int) -> dict:
        """
        Gets a detailed breakdown of XP calculation for UI display.
        """
        base_xp_map = {
            "new": GameEngineService.XP_NEW_QUESTION,
            "valid_review": GameEngineService.XP_VALID_REVIEW,
            "invalid_repeat": GameEngineService.XP_INVALID_REPEAT
        }
        base_xp = base_xp_map.get(attempt_type, 0)
        multiplier = GameEngineService.get_streak_multiplier(streak_days)
        potential_xp = int(base_xp * multiplier)

        return {
            "base_xp": base_xp,
            "streak_multiplier": multiplier,
            "streak_days": streak_days,
            "potential_xp": potential_xp,
            "attempt_type": attempt_type,
            "xp_formula": f"{base_xp} x {multiplier} = {potential_xp}"
        }

    @staticmethod
    def calculate_level_for_xp(experience: int) -> int:
        """
        UNIFIED: Calculates level based on total experience.
        Source of Truth: LOGICA_DE_NEGOCIO.md specification.
        Formula: XP_needed = level² × 100
        Inverted: level = floor(sqrt(experience / 100)) + 1

        Examples:
        - Level 1: 0-99 XP
        - Level 2: 100-399 XP (needs 100 = 1²×100)
        - Level 3: 400-899 XP (needs 400 = 2²×100)
        - Level 10: 8100+ XP (needs 8100 = 9²×100)
        """
        if experience <= 0:
            return 1
        # Formula: level² × 100 = XP needed
        # Inverted: level = sqrt(XP / 100) + 1
        return int(math.sqrt(experience / 100)) + 1

    @staticmethod
    def calculate_xp_for_level(level: int) -> int:
        """
        Calculate total XP needed to reach a specific level.
        Formula: XP_needed = (level - 1)² × 100

        Examples:
        - Level 1: 0 XP
        - Level 2: 100 XP
        - Level 3: 400 XP
        - Level 10: 8100 XP
        """
        if level <= 1:
            return 0
        return ((level - 1) ** 2) * 100

    @staticmethod
    def get_level_progress(experience: int) -> dict:
        """
        Get detailed level progress information.

        Returns:
            Dict with current_level, xp_in_level, xp_to_next, progress_percent
        """
        current_level = GameEngineService.calculate_level_for_xp(experience)
        current_level_xp = GameEngineService.calculate_xp_for_level(current_level)
        next_level_xp = GameEngineService.calculate_xp_for_level(current_level + 1)

        xp_in_level = experience - current_level_xp
        xp_needed = next_level_xp - current_level_xp
        progress = (xp_in_level / xp_needed * 100) if xp_needed > 0 else 0

        return {
            "current_level": current_level,
            "total_xp": experience,
            "xp_in_level": xp_in_level,
            "xp_to_next_level": xp_needed - xp_in_level,
            "xp_needed_for_level": xp_needed,
            "progress_percent": round(progress, 2)
        }

    # ============================================
    # RANK & COMBAT CALCULATION (MOVED FROM security.py)
    # ============================================

    @staticmethod
    def calculate_rank(level: int) -> str:
        """
        Calculates rank based on level.
        Source of Truth: Formula from core/security.py.
        """
        if level >= 90: return "SSS"
        elif level >= 80: return "SS"
        elif level >= 70: return "S"
        elif level >= 60: return "A"
        elif level >= 50: return "B"
        elif level >= 30: return "C"
        elif level >= 15: return "D"
        else: return "E"

    @staticmethod
    def calculate_damage(
        user_power: int,
        user_wisdom: int,
        is_correct: bool,
        response_time_ms: int,
        difficulty: int,
        combo_count: int = 0
    ) -> int:
        """
        Calculates damage dealt in a combat scenario.
        Source of Truth: Formula from core/security.py.
        """
        if not is_correct:
            return 0
        
        base_damage = (user_power + user_wisdom) * 2
        
        if response_time_ms < 3000: time_multiplier = 2.0
        elif response_time_ms < 10000: time_multiplier = 1.5
        elif response_time_ms < 20000: time_multiplier = 1.2
        else: time_multiplier = 1.0
        
        difficulty_multiplier = 1 + (difficulty - 1) * 0.1
        combo_multiplier = 1 + (combo_count * 0.1)
        
        total_damage = int(base_damage * time_multiplier * difficulty_multiplier * combo_multiplier)
        return max(1, total_damage)

    @staticmethod
    def calculate_orbs_gain(
        is_correct: bool,
        difficulty: int,
        critical_hit: bool
    ) -> int:
        """
        Calculates orbs (gold) gained from an action.
        Source of Truth: Formula from core/security.py.
        """
        if not is_correct:
            return 1
        
        base_orbs = difficulty * 2
        if critical_hit:
            base_orbs *= 2

        return base_orbs


# ============================================
# STANDALONE WRAPPER FUNCTIONS (for backwards compatibility)
# These wrappers are provided for compatibility with older parts of the codebase
# that might still call functions with these specific signatures.
# They map to the unified GameEngineService static methods.
# ============================================

def calculate_damage(is_correct: bool, time_spent_ms: int, difficulty: int, combo: int = 1) -> int:
    """Wrapper for GameEngineService.calculate_damage"""
    # Note: user_power and user_wisdom are not available in this wrapper's signature.
    # Using default values. If these are critical, the calling code should be updated.
    logger.warning("Using default user_power/user_wisdom in GameEngineService.calculate_damage wrapper.")
    return GameEngineService.calculate_damage(
        user_power=10,
        user_wisdom=10,
        is_correct=is_correct,
        response_time_ms=time_spent_ms,
        difficulty=difficulty,
        combo_count=combo
    )

def calculate_experience_gain(is_correct: bool, difficulty: int, is_first_attempt: bool = True, is_mastered: bool = False) -> int:
    """Wrapper for GameEngineService.calculate_xp_for_answer"""
    # This wrapper's signature does not perfectly align with calculate_xp_for_answer.
    # Making a best-effort mapping for attempt_type and streak_days.
    attempt_type = "new" if is_first_attempt else ("valid_review" if is_mastered else "invalid_repeat")
    logger.warning(f"Heuristic mapping 'is_first_attempt/is_mastered' to '{attempt_type}' in calculate_experience_gain wrapper.")
    return GameEngineService.calculate_xp_for_answer(
        attempt_type=attempt_type,
        is_correct=is_correct,
        streak_days=1 # Using a default streak_days for this wrapper
    )

def calculate_orbs_gain(is_correct: bool, difficulty: int, critical_hit: bool = False) -> int:
    """Wrapper for GameEngineService.calculate_orbs_gain"""
    return GameEngineService.calculate_orbs_gain(is_correct, difficulty, critical_hit)

def calculate_level(total_xp: int) -> int:
    """Wrapper for GameEngineService.calculate_level_for_xp"""
    return GameEngineService.calculate_level_for_xp(total_xp)

def calculate_rank(level: int) -> str:
    """Wrapper for GameEngineService.calculate_rank"""
    return GameEngineService.calculate_rank(level)

