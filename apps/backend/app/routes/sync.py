"""
Offline Sync Routes - ICFES Leveling
Synchronize actions performed while offline
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models import User
from ..utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sync", tags=["Sync"])


# ============================================
# SCHEMAS
# ============================================

class OfflineAction(BaseModel):
    """Single offline action to sync"""
    action_type: str  # 'battle_answer', 'practice_complete', 'video_watched', etc.
    payload: dict
    client_timestamp: datetime


class SyncBatchRequest(BaseModel):
    """Batch of offline actions to sync"""
    actions: List[OfflineAction]


class SyncResultItem(BaseModel):
    """Result of processing single action"""
    action_type: str
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None


class SyncBatchResponse(BaseModel):
    """Response for batch sync"""
    synced: int
    failed: int
    results: List[SyncResultItem]


# ============================================
# ENDPOINTS
# ============================================

@router.post("/batch")
async def sync_offline_actions(
    request: SyncBatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Synchronize batch of offline actions.

    Processes actions in chronological order and returns results.
    Failed actions don't stop processing of subsequent actions.

    Supported action types:
    - battle_answer: Submit answer for dungeon battle
    - practice_complete: Complete a practice session
    - video_watched: Mark video as watched
    - xp_earned: Award XP from activity
    - streak_check: Check/update streak
    """
    results = []
    synced = 0
    failed = 0

    # Sort by timestamp to process in order
    sorted_actions = sorted(request.actions, key=lambda a: a.client_timestamp)

    for action in sorted_actions:
        try:
            result = await _process_offline_action(
                db,
                current_user.id,
                action
            )
            results.append(SyncResultItem(
                action_type=action.action_type,
                success=True,
                result=result
            ))
            synced += 1

        except Exception as e:
            logger.error(f"Failed to process offline action {action.action_type}: {e}")
            results.append(SyncResultItem(
                action_type=action.action_type,
                success=False,
                error=str(e)
            ))
            failed += 1

    return success_response({
        "synced": synced,
        "failed": failed,
        "results": [r.dict() for r in results]
    })


async def _process_offline_action(
    db: Session,
    user_id: UUID,
    action: OfflineAction
) -> dict:
    """Process a single offline action"""

    if action.action_type == "battle_answer":
        # Process battle answer
        from ..services.dungeon_service import DungeonService
        service = DungeonService(db)

        return service.submit_encounter_answers(
            encounter_id=action.payload.get("encounter_id"),
            user_id=str(user_id),
            answers=action.payload.get("answers", []),
            shadows_used=action.payload.get("shadows_used", [])
        )

    elif action.action_type == "practice_complete":
        # Update streak for practice completion
        from ..services.streak_service import StreakService
        service = StreakService(db)

        return service.check_and_update_streak(
            user_id=user_id,
            xp_earned=action.payload.get("xp_earned", 0)
        )

    elif action.action_type == "video_watched":
        # Track video watch
        from ..services.video_progress_service import VideoProgressService
        service = VideoProgressService(db)

        return service.mark_video_watched(
            user_id=user_id,
            video_id=action.payload.get("video_id"),
            watch_time_seconds=action.payload.get("watch_time_seconds", 0)
        )

    elif action.action_type == "xp_earned":
        # Award XP
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            xp = action.payload.get("amount", 0)
            user.xp = (user.xp or 0) + xp
            db.commit()
            return {"xp_added": xp, "total_xp": user.xp}
        raise ValueError("User not found")

    elif action.action_type == "streak_check":
        # Check streak
        from ..services.streak_service import StreakService
        service = StreakService(db)
        return service.get_streak_status(user_id)

    elif action.action_type == "node_complete":
        # Update node progress
        from ..services.node_progress_service import NodeProgressService
        service = NodeProgressService(db)

        return service.update_node_progress(
            user_id=user_id,
            node_id=action.payload.get("node_id"),
            kingdom_id=action.payload.get("kingdom_id"),
            accuracy=action.payload.get("accuracy", 0),
            questions_answered=action.payload.get("questions", [])
        )

    else:
        # Unknown action type - log and skip
        logger.warning(f"Unknown offline action type: {action.action_type}")
        return {"processed": True, "action_type": action.action_type, "skipped": True}


@router.get("/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current sync status for user.
    Returns last sync time and any pending items.
    """
    # This would check for any pending sync items in a queue table
    # For now, return basic status
    return success_response({
        "user_id": str(current_user.id),
        "last_sync_at": datetime.utcnow().isoformat(),
        "pending_items": 0,
        "sync_enabled": True
    })
