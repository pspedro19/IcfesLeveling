"""
Node Progress Routes - ICFES Leveling
Kingdom and Node progress tracking for Conquest Mode

Endpoints:
- GET /progress/kingdom/{kingdom_id} - Get kingdom progress with all nodes
- GET /progress/node/{node_id} - Get specific node progress
- POST /progress/node/{node_id}/complete - Update node progress after completion
- POST /progress/node/{node_id}/unlock - Unlock a node
- POST /progress/kingdom/{kingdom_id}/diagnostic - Mark diagnostic complete
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user
from ..models import User
from ..services.node_progress_service import NodeProgressService
from ..utils.response import success_response


# ============================================
# SCHEMAS
# ============================================

class NodeCompleteRequest(BaseModel):
    """Request for completing a node session"""
    kingdom_id: str
    accuracy: float  # 0.0 - 1.0
    questions_answered: List[str] = []


class DiagnosticCompleteRequest(BaseModel):
    """Request for completing kingdom diagnostic"""
    initial_rank: str = 'E'


# ============================================
# ROUTER
# ============================================

router = APIRouter(prefix="/progress", tags=["Progress"])


# ============================================
# ENDPOINTS
# ============================================

@router.get("/kingdom/{kingdom_id}")
async def get_kingdom_progress(
    kingdom_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's progress in a specific kingdom.

    Returns:
    - Kingdom-level stats (mastery, rank, boss status)
    - All node progress within the kingdom
    - Total stars earned
    """
    service = NodeProgressService(db)

    try:
        status = service.get_kingdom_status(current_user.id, kingdom_id)
        return success_response(status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}")
async def get_node_progress(
    node_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's progress on a specific node.

    Returns:
    - Mastery percentage
    - Stars earned (0-3)
    - Times completed
    - Best accuracy
    - Unlock status
    """
    service = NodeProgressService(db)

    # Get node progress (kingdom_id will be derived from node_id pattern)
    # node_id format: "{kingdom_id}_node_{number}"
    kingdom_id = node_id.split('_node_')[0] if '_node_' in node_id else 'unknown'

    node = service.get_or_create_node_progress(current_user.id, node_id, kingdom_id)

    return success_response({
        "node_id": node.node_id,
        "kingdom_id": node.kingdom_id,
        "mastery_percent": float(node.mastery_percent),
        "stars_earned": node.stars_earned,
        "times_completed": node.times_completed,
        "best_accuracy": float(node.best_accuracy),
        "is_unlocked": node.is_unlocked,
        "unlocked_at": node.unlocked_at.isoformat() if node.unlocked_at else None
    })


@router.post("/node/{node_id}/complete")
async def complete_node(
    node_id: str,
    request: NodeCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update node progress after completing a session.

    Calculates:
    - Stars based on accuracy (60%=1, 80%=2, 95%=3)
    - Mastery progression (weighted average)
    - Kingdom overall mastery

    Returns updated progress and any rewards.
    """
    service = NodeProgressService(db)

    try:
        result = service.update_node_progress(
            user_id=current_user.id,
            node_id=node_id,
            kingdom_id=request.kingdom_id,
            accuracy=request.accuracy,
            questions_answered=request.questions_answered
        )
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/node/{node_id}/unlock")
async def unlock_node(
    node_id: str,
    kingdom_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlock a node for the user.

    Typically called when:
    - Previous node reaches 50% mastery
    - User completes diagnostic
    - Special unlock (purchased or rewarded)
    """
    service = NodeProgressService(db)

    try:
        result = service.unlock_node(current_user.id, node_id, kingdom_id)
        return success_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/node/{node_id}/can-unlock")
async def can_unlock_node(
    node_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user can unlock a specific node.

    Requirements:
    - Previous node has >= 50% mastery
    - Or is first node in kingdom
    """
    service = NodeProgressService(db)

    # Get node progress
    kingdom_id = node_id.split('_node_')[0] if '_node_' in node_id else 'unknown'
    node = service.get_or_create_node_progress(current_user.id, node_id, kingdom_id)

    # Check if already unlocked
    if node.is_unlocked:
        return success_response({"can_unlock": True, "reason": "already_unlocked"})

    # Check if first node (always unlockable after diagnostic)
    if '_node_1' in node_id or '_node_0' in node_id:
        kingdom = service.get_or_create_kingdom_progress(current_user.id, kingdom_id)
        if kingdom.diagnostic_completed:
            return success_response({"can_unlock": True, "reason": "first_node"})
        return success_response({"can_unlock": False, "reason": "diagnostic_required"})

    # Check previous node mastery
    try:
        node_number = int(node_id.split('_node_')[-1])
        prev_node_id = f"{kingdom_id}_node_{node_number - 1}"
        prev_node = service.get_or_create_node_progress(current_user.id, prev_node_id, kingdom_id)

        if float(prev_node.mastery_percent) >= 50:
            return success_response({"can_unlock": True, "reason": "mastery_threshold_met"})
        return success_response({
            "can_unlock": False,
            "reason": "insufficient_mastery",
            "current_mastery": float(prev_node.mastery_percent),
            "required_mastery": 50
        })
    except (ValueError, IndexError):
        return success_response({"can_unlock": False, "reason": "invalid_node_id"})


@router.get("/kingdom/{kingdom_id}/can-challenge-boss")
async def can_challenge_boss(
    kingdom_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user can challenge the kingdom boss.

    Requirements:
    - All nodes in kingdom unlocked
    - Average mastery >= 60%
    - Diagnostic completed
    """
    service = NodeProgressService(db)

    status = service.get_kingdom_status(current_user.id, kingdom_id)

    # Check diagnostic
    if not status["diagnostic_completed"]:
        return success_response({
            "can_challenge": False,
            "reason": "diagnostic_required"
        })

    # Check if already defeated
    if status["boss_defeated"]:
        return success_response({
            "can_challenge": True,
            "reason": "boss_already_defeated",
            "rematch": True
        })

    # Check mastery threshold
    if status["overall_mastery"] >= 60:
        return success_response({
            "can_challenge": True,
            "reason": "mastery_threshold_met"
        })

    return success_response({
        "can_challenge": False,
        "reason": "insufficient_mastery",
        "current_mastery": status["overall_mastery"],
        "required_mastery": 60
    })


@router.post("/kingdom/{kingdom_id}/diagnostic")
async def complete_diagnostic(
    kingdom_id: str,
    request: DiagnosticCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark kingdom diagnostic as complete.

    Sets initial rank based on diagnostic results and
    unlocks first nodes in the kingdom.
    """
    service = NodeProgressService(db)

    try:
        result = service.mark_diagnostic_complete(
            user_id=current_user.id,
            kingdom_id=kingdom_id,
            initial_rank=request.initial_rank
        )

        # Auto-unlock first node
        first_node_id = f"{kingdom_id}_node_1"
        service.unlock_node(current_user.id, first_node_id, kingdom_id)

        return success_response({
            **result,
            "first_node_unlocked": first_node_id
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all")
async def get_all_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get progress across all kingdoms for the user.

    Returns summary of each kingdom's progress.
    """
    service = NodeProgressService(db)

    # Standard kingdom IDs
    kingdoms = ['math', 'reading', 'science', 'social', 'english']

    all_progress = {}
    for kingdom_id in kingdoms:
        try:
            status = service.get_kingdom_status(current_user.id, kingdom_id)
            all_progress[kingdom_id] = status
        except Exception:
            all_progress[kingdom_id] = {
                "kingdom_id": kingdom_id,
                "diagnostic_completed": False,
                "overall_mastery": 0,
                "rank": "E",
                "boss_defeated": False,
                "total_stars": 0,
                "nodes": []
            }

    return success_response({
        "kingdoms": all_progress,
        "total_stars": sum(k["total_stars"] for k in all_progress.values())
    })
