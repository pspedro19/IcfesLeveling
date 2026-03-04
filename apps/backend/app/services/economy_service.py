"""
Economy Service
Handles gold, XP, and rank management for users.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List, Tuple
from uuid import UUID
import logging

from ..models.user import User
from ..models.economy import GoldTransaction, XPTransaction
from ..services.game_engine_service import GameEngineService

logger = logging.getLogger(__name__)


# Rank thresholds based on mastery percentage
RANK_THRESHOLDS = {
    'S': 90,   # 90%+ mastery
    'A': 75,   # 75-89% mastery
    'B': 60,   # 60-74% mastery
    'C': 45,   # 45-59% mastery
    'D': 30,   # 30-44% mastery
    'E': 0,    # 0-29% mastery (default)
}

# XP required per level (can be adjusted)
XP_PER_LEVEL_BASE = 100
XP_LEVEL_MULTIPLIER = 1.15  # Each level requires 15% more XP


class EconomyService:
    """
    Service for managing user economy including gold, XP, and ranks.

    Methods:
    - get_user_economy: Get complete economy status
    - add_gold: Add gold with transaction tracking
    - spend_gold: Spend gold with transaction tracking
    - add_xp: Add XP with level-up logic
    - update_rank: Update rank based on mastery percentage
    """

    @staticmethod
    def get_user_economy(db: Session, user_id: UUID) -> Optional[dict]:
        """
        Get complete economy status for a user.

        Returns:
            Dictionary with user_id, gold, total_xp, level, rank, and additional stats
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        return {
            "user_id": str(user.id),
            "gold": user.gold or 0,
            "orbs": user.orbs or 0,  # Knowledge orbs (secondary currency)
            "crystals": user.crystals or 0,  # Premium currency
            "total_xp": user.experience or 0,
            "level": user.level or 1,
            "rank": user.rank or 'E',
            "xp_to_next_level": EconomyService._calculate_xp_to_next_level(user.level, user.experience),
            "level_progress_percent": EconomyService._calculate_level_progress(user.level, user.experience),
        }

    @staticmethod
    def add_gold(
        db: Session,
        user_id: UUID,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Add gold to user's balance with transaction tracking.

        Args:
            db: Database session
            user_id: User's UUID
            amount: Amount of gold to add (must be positive)
            transaction_type: Type of transaction (e.g., 'quest_reward', 'streak_bonus')
            description: Optional description
            reference_id: Optional reference to related entity
            reference_type: Optional type of reference entity

        Returns:
            Tuple of (success, new_balance, error_message)
        """
        if amount <= 0:
            return False, 0, "Amount must be positive"

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, 0, "User not found"

        try:
            # Update user's gold balance
            old_balance = user.gold or 0
            user.gold = old_balance + amount
            new_balance = user.gold

            # Create transaction record
            transaction = GoldTransaction(
                user_id=user_id,
                amount=amount,
                balance_after=new_balance,
                transaction_type=transaction_type,
                description=description,
                reference_id=reference_id,
                reference_type=reference_type
            )
            db.add(transaction)
            db.commit()

            logger.info(f"Added {amount} gold to user {user_id}. New balance: {new_balance}")
            return True, new_balance, None

        except Exception as e:
            db.rollback()
            logger.error(f"Error adding gold: {e}")
            return False, 0, str(e)

    @staticmethod
    def spend_gold(
        db: Session,
        user_id: UUID,
        amount: int,
        transaction_type: str,
        description: Optional[str] = None,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None
    ) -> Tuple[bool, int, Optional[str]]:
        """
        Spend gold from user's balance with transaction tracking.

        Args:
            db: Database session
            user_id: User's UUID
            amount: Amount of gold to spend (must be positive)
            transaction_type: Type of transaction (e.g., 'purchase', 'unlock')
            description: Optional description
            reference_id: Optional reference to related entity
            reference_type: Optional type of reference entity

        Returns:
            Tuple of (success, remaining_balance, error_message)
        """
        if amount <= 0:
            return False, 0, "Amount must be positive"

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, 0, "User not found"

        current_balance = user.gold or 0
        if current_balance < amount:
            return False, current_balance, f"Insufficient gold. Have: {current_balance}, Need: {amount}"

        try:
            # Update user's gold balance
            user.gold = current_balance - amount
            new_balance = user.gold

            # Create transaction record (negative amount for spending)
            transaction = GoldTransaction(
                user_id=user_id,
                amount=-amount,  # Negative for spending
                balance_after=new_balance,
                transaction_type=transaction_type,
                description=description,
                reference_id=reference_id,
                reference_type=reference_type
            )
            db.add(transaction)
            db.commit()

            logger.info(f"Spent {amount} gold from user {user_id}. Remaining: {new_balance}")
            return True, new_balance, None

        except Exception as e:
            db.rollback()
            logger.error(f"Error spending gold: {e}")
            return False, 0, str(e)

    @staticmethod
    def add_xp(
        db: Session,
        user_id: UUID,
        amount: int,
        source: str,
        source_id: Optional[UUID] = None,
        multiplier: float = 1.0
    ) -> Tuple[bool, dict, Optional[str]]:
        """
        Add XP to user with level-up logic.

        Args:
            db: Database session
            user_id: User's UUID
            amount: Base XP amount to add (must be positive)
            source: Source of XP (e.g., 'question_correct', 'quest_complete')
            source_id: Optional reference to source entity
            multiplier: XP multiplier (for boosts)

        Returns:
            Tuple of (success, result_dict, error_message)
            result_dict contains: xp_gained, total_xp, level, leveled_up, levels_gained
        """
        if amount <= 0:
            return False, {}, "Amount must be positive"

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, {}, "User not found"

        try:
            # Apply multiplier
            actual_xp = int(amount * multiplier)

            # Store previous state
            level_before = user.level or 1
            xp_before = user.experience or 0

            # Add XP and check for level up
            leveled_up = user.add_experience(actual_xp)

            level_after = user.level
            levels_gained = level_after - level_before

            # Create XP transaction record
            transaction = XPTransaction(
                user_id=user_id,
                amount=actual_xp,
                total_xp_after=user.experience,
                level_before=level_before,
                level_after=level_after,
                leveled_up=levels_gained,
                source=source,
                source_id=source_id,
                multiplier=multiplier
            )
            db.add(transaction)
            db.commit()

            result = {
                "xp_gained": actual_xp,
                "total_xp": user.experience,
                "level": level_after,
                "leveled_up": leveled_up,
                "levels_gained": levels_gained,
                "xp_to_next_level": EconomyService._calculate_xp_to_next_level(level_after, user.experience),
            }

            if leveled_up:
                logger.info(f"User {user_id} leveled up! {level_before} -> {level_after} (+{actual_xp} XP)")
            else:
                logger.info(f"User {user_id} gained {actual_xp} XP. Total: {user.experience}")

            return True, result, None

        except Exception as e:
            db.rollback()
            logger.error(f"Error adding XP: {e}")
            return False, {}, str(e)

    @staticmethod
    def update_rank(
        db: Session,
        user_id: UUID,
        mastery_percent: float
    ) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        Update user's rank based on mastery percentage.

        Rank Thresholds:
        - S: 90%+ mastery
        - A: 75-89% mastery
        - B: 60-74% mastery
        - C: 45-59% mastery
        - D: 30-44% mastery
        - E: 0-29% mastery (default)

        Args:
            db: Database session
            user_id: User's UUID
            mastery_percent: Mastery percentage (0-100)

        Returns:
            Tuple of (success, new_rank, old_rank, error_message)
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, 'E', None, "User not found"

        try:
            old_rank = user.rank or 'E'

            # Determine new rank based on mastery percentage
            new_rank = 'E'  # Default
            for rank, threshold in RANK_THRESHOLDS.items():
                if mastery_percent >= threshold:
                    new_rank = rank
                    break  # Ranks are ordered from highest to lowest

            # Update user's rank
            user.rank = new_rank
            db.commit()

            if old_rank != new_rank:
                logger.info(f"User {user_id} rank changed: {old_rank} -> {new_rank} (mastery: {mastery_percent:.1f}%)")

            return True, new_rank, old_rank, None

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating rank: {e}")
            return False, 'E', None, str(e)

    @staticmethod
    def get_gold_transactions(
        db: Session,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        transaction_type: Optional[str] = None
    ) -> List[GoldTransaction]:
        """
        Get gold transaction history for a user.

        Args:
            db: Database session
            user_id: User's UUID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            transaction_type: Optional filter by transaction type

        Returns:
            List of GoldTransaction objects
        """
        query = db.query(GoldTransaction).filter(GoldTransaction.user_id == user_id)

        if transaction_type:
            query = query.filter(GoldTransaction.transaction_type == transaction_type)

        return query.order_by(desc(GoldTransaction.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def get_xp_transactions(
        db: Session,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        source: Optional[str] = None
    ) -> List[XPTransaction]:
        """
        Get XP transaction history for a user.

        Args:
            db: Database session
            user_id: User's UUID
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            source: Optional filter by source

        Returns:
            List of XPTransaction objects
        """
        query = db.query(XPTransaction).filter(XPTransaction.user_id == user_id)

        if source:
            query = query.filter(XPTransaction.source == source)

        return query.order_by(desc(XPTransaction.created_at)).offset(offset).limit(limit).all()

    @staticmethod
    def _calculate_xp_to_next_level(current_level: int, current_xp: int) -> int:
        """Calculate XP needed to reach next level."""
        xp_for_current_level = GameEngineService.calculate_xp_for_level(current_level)
        xp_for_next_level = GameEngineService.calculate_xp_for_level(current_level + 1)
        return max(0, xp_for_next_level - current_xp)

    @staticmethod
    def _calculate_level_progress(current_level: int, current_xp: int) -> float:
        """Calculate progress percentage toward next level."""
        xp_for_current_level = GameEngineService.calculate_xp_for_level(current_level)
        xp_for_next_level = GameEngineService.calculate_xp_for_level(current_level + 1)

        xp_in_current_level = current_xp - xp_for_current_level
        xp_needed_for_level = xp_for_next_level - xp_for_current_level

        if xp_needed_for_level <= 0:
            return 100.0

        return min(100.0, max(0.0, (xp_in_current_level / xp_needed_for_level) * 100))
