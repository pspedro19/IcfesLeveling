"""
Node Progress Service - Manage user progress through Kingdoms and Nodes
ICFES Leveling - Conquest Mode
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Dict, Any, List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime
import logging

from ..models.node_progress import UserKingdomProgress, UserNodeProgress

logger = logging.getLogger(__name__)


class NodeProgressService:
    """Service for managing node and kingdom progress"""

    # Star thresholds based on accuracy
    STAR_THRESHOLDS = {
        1: 0.60,  # 60% accuracy = 1 star
        2: 0.80,  # 80% accuracy = 2 stars
        3: 0.95,  # 95% accuracy = 3 stars
    }

    # Mastery required to unlock next node
    UNLOCK_MASTERY_THRESHOLD = 0.50  # 50% mastery to unlock next

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_kingdom_progress(
        self, user_id: UUID, kingdom_id: str
    ) -> UserKingdomProgress:
        """Get or create kingdom progress for user"""
        progress = self.db.query(UserKingdomProgress).filter(
            and_(
                UserKingdomProgress.user_id == user_id,
                UserKingdomProgress.kingdom_id == kingdom_id
            )
        ).first()

        if not progress:
            progress = UserKingdomProgress(
                user_id=user_id,
                kingdom_id=kingdom_id,
                diagnostic_completed=False,
                overall_mastery=Decimal('0.00'),
                rank='E',
                boss_defeated=False,
                total_stars=0
            )
            self.db.add(progress)
            self.db.flush()

        return progress

    def get_or_create_node_progress(
        self, user_id: UUID, node_id: str, kingdom_id: str
    ) -> UserNodeProgress:
        """Get or create node progress for user"""
        progress = self.db.query(UserNodeProgress).filter(
            and_(
                UserNodeProgress.user_id == user_id,
                UserNodeProgress.node_id == node_id
            )
        ).first()

        if not progress:
            progress = UserNodeProgress(
                user_id=user_id,
                node_id=node_id,
                kingdom_id=kingdom_id,
                mastery_percent=Decimal('0.00'),
                stars_earned=0,
                times_completed=0,
                best_accuracy=Decimal('0.00'),
                questions_seen=[],
                is_unlocked=False
            )
            self.db.add(progress)
            self.db.flush()

        return progress

    def update_node_progress(
        self,
        user_id: UUID,
        node_id: str,
        kingdom_id: str,
        accuracy: float,
        questions_answered: List[str]
    ) -> Dict[str, Any]:
        """Update node progress after completing a session"""
        node_progress = self.get_or_create_node_progress(user_id, node_id, kingdom_id)
        kingdom_progress = self.get_or_create_kingdom_progress(user_id, kingdom_id)

        # Update times completed
        node_progress.times_completed += 1

        # Update best accuracy
        if accuracy > float(node_progress.best_accuracy):
            node_progress.best_accuracy = Decimal(str(accuracy))

        # Calculate stars earned
        new_stars = self._calculate_stars(accuracy)
        stars_increased = new_stars > node_progress.stars_earned
        if stars_increased:
            old_stars = node_progress.stars_earned
            node_progress.stars_earned = new_stars
            kingdom_progress.total_stars += (new_stars - old_stars)

        # Update mastery (weighted average with more weight on recent)
        current_mastery = float(node_progress.mastery_percent)
        new_mastery = (current_mastery * 0.7) + (accuracy * 100 * 0.3)
        node_progress.mastery_percent = Decimal(str(min(100, new_mastery)))

        # Track questions seen
        existing_questions = node_progress.questions_seen or []
        for q_id in questions_answered:
            if q_id not in existing_questions:
                existing_questions.append(q_id)
        node_progress.questions_seen = existing_questions

        # Update kingdom overall mastery
        self._recalculate_kingdom_mastery(user_id, kingdom_id)

        self.db.commit()

        return {
            "node_id": node_id,
            "kingdom_id": kingdom_id,
            "accuracy": accuracy,
            "stars_earned": node_progress.stars_earned,
            "stars_increased": stars_increased,
            "mastery_percent": float(node_progress.mastery_percent),
            "times_completed": node_progress.times_completed,
            "kingdom_mastery": float(kingdom_progress.overall_mastery)
        }

    def _calculate_stars(self, accuracy: float) -> int:
        """Calculate stars based on accuracy"""
        stars = 0
        for star_count, threshold in self.STAR_THRESHOLDS.items():
            if accuracy >= threshold:
                stars = star_count
        return stars

    def _recalculate_kingdom_mastery(self, user_id: UUID, kingdom_id: str):
        """Recalculate overall kingdom mastery based on all nodes"""
        nodes = self.db.query(UserNodeProgress).filter(
            and_(
                UserNodeProgress.user_id == user_id,
                UserNodeProgress.kingdom_id == kingdom_id
            )
        ).all()

        if not nodes:
            return

        total_mastery = sum(float(n.mastery_percent) for n in nodes)
        avg_mastery = total_mastery / len(nodes)

        kingdom_progress = self.get_or_create_kingdom_progress(user_id, kingdom_id)
        kingdom_progress.overall_mastery = Decimal(str(avg_mastery))

    def unlock_node(self, user_id: UUID, node_id: str, kingdom_id: str) -> Dict[str, Any]:
        """Unlock a node for the user"""
        node_progress = self.get_or_create_node_progress(user_id, node_id, kingdom_id)

        if node_progress.is_unlocked:
            return {"already_unlocked": True, "node_id": node_id}

        node_progress.is_unlocked = True
        node_progress.unlocked_at = datetime.utcnow()
        self.db.commit()

        return {
            "unlocked": True,
            "node_id": node_id,
            "kingdom_id": kingdom_id,
            "unlocked_at": node_progress.unlocked_at
        }

    def get_kingdom_status(self, user_id: UUID, kingdom_id: str) -> Dict[str, Any]:
        """Get complete kingdom status for user"""
        kingdom = self.get_or_create_kingdom_progress(user_id, kingdom_id)
        nodes = self.db.query(UserNodeProgress).filter(
            and_(
                UserNodeProgress.user_id == user_id,
                UserNodeProgress.kingdom_id == kingdom_id
            )
        ).all()

        return {
            "kingdom_id": kingdom_id,
            "diagnostic_completed": kingdom.diagnostic_completed,
            "overall_mastery": float(kingdom.overall_mastery),
            "rank": kingdom.rank,
            "boss_defeated": kingdom.boss_defeated,
            "total_stars": kingdom.total_stars,
            "nodes": [
                {
                    "node_id": n.node_id,
                    "mastery_percent": float(n.mastery_percent),
                    "stars_earned": n.stars_earned,
                    "is_unlocked": n.is_unlocked,
                    "times_completed": n.times_completed
                }
                for n in nodes
            ]
        }

    def mark_diagnostic_complete(
        self, user_id: UUID, kingdom_id: str, initial_rank: str = 'E'
    ) -> Dict[str, Any]:
        """Mark diagnostic as complete and set initial rank"""
        kingdom = self.get_or_create_kingdom_progress(user_id, kingdom_id)
        kingdom.diagnostic_completed = True
        kingdom.rank = initial_rank
        self.db.commit()

        return {
            "kingdom_id": kingdom_id,
            "diagnostic_completed": True,
            "initial_rank": initial_rank
        }


# Factory function
def get_node_progress_service(db: Session) -> NodeProgressService:
    return NodeProgressService(db)
