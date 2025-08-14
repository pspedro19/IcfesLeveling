from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
from ..core.database import get_db
from ..models.user import User
from ..models.notification import Notification, NotificationType
from ..schemas.notification import NotificationCreate, NotificationResponse, NotificationUpdate
from ..core.security import get_current_user
from ..middleware.rate_limit import user_rate_limit, endpoint_rate_limit
from ..core.redis_cache import cache

router = APIRouter(prefix="/notifications", tags=["notifications"])

# WebSocket connections for real-time notifications
connected_users = {}

@router.post("/", response_model=NotificationResponse)
@user_rate_limit(limit=100, window=3600)  # 100 notifications per hour per user
async def create_notification(
    notification: NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new notification"""
    
    # Create notification in database
    db_notification = Notification(
        user_id=notification.user_id or current_user.id,
        type=notification.type,
        title=notification.title,
        message=notification.message,
        data=notification.data,
        priority=notification.priority,
        expires_at=notification.expires_at
    )
    
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    # Send real-time notification
    background_tasks.add_task(
        send_real_time_notification,
        db_notification.user_id,
        db_notification
    )
    
    # Cache for quick access
    cache.set(
        f"notification:{db_notification.id}",
        db_notification,
        ttl=86400  # 24 hours
    )
    
    return db_notification

@router.get("/", response_model=List[NotificationResponse])
@endpoint_rate_limit("get_notifications", limit=200, window=3600)
async def get_user_notifications(
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
    type_filter: Optional[NotificationType] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user notifications with filters"""
    
    # Try cache first
    cache_key = f"user_notifications:{current_user.id}:{skip}:{limit}:{unread_only}:{type_filter}"
    cached_notifications = cache.get(cache_key)
    if cached_notifications:
        return cached_notifications
    
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    
    if type_filter:
        query = query.filter(Notification.type == type_filter)
    
    # Only get non-expired notifications
    query = query.filter(
        (Notification.expires_at.is_(None)) | 
        (Notification.expires_at > datetime.utcnow())
    )
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    # Cache results
    cache.set(cache_key, notifications, ttl=300)  # 5 minutes
    
    return notifications

@router.patch("/{notification_id}/read")
@endpoint_rate_limit("mark_read", limit=500, window=3600)
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark notification as read"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if not notification.read_at:
        notification.read_at = datetime.utcnow()
        db.commit()
        
        # Update cache
        cache.delete(f"notification:{notification_id}")
        cache.clear_pattern(f"user_notifications:{current_user.id}:*")
    
    return {"message": "Notification marked as read"}

@router.patch("/read-all")
@endpoint_rate_limit("mark_all_read", limit=10, window=60)
async def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark all user notifications as read"""
    
    updated_count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None)
    ).update({
        "read_at": datetime.utcnow()
    })
    
    db.commit()
    
    # Clear user notification cache
    cache.clear_pattern(f"user_notifications:{current_user.id}:*")
    
    return {"message": f"Marked {updated_count} notifications as read"}

@router.delete("/{notification_id}")
@endpoint_rate_limit("delete_notification", limit=100, window=3600)
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a notification"""
    
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    # Clear cache
    cache.delete(f"notification:{notification_id}")
    cache.clear_pattern(f"user_notifications:{current_user.id}:*")
    
    return {"message": "Notification deleted"}

@router.get("/unread-count")
@endpoint_rate_limit("unread_count", limit=300, window=3600)
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    
    # Try cache first
    cache_key = f"unread_count:{current_user.id}"
    cached_count = cache.get(cache_key)
    if cached_count is not None:
        return {"unread_count": cached_count}
    
    count = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.read_at.is_(None),
        (Notification.expires_at.is_(None)) | 
        (Notification.expires_at > datetime.utcnow())
    ).count()
    
    # Cache for 2 minutes
    cache.set(cache_key, count, ttl=120)
    
    return {"unread_count": count}

# Utility functions for sending notifications
async def send_real_time_notification(user_id: int, notification: Notification):
    """Send real-time notification via WebSocket"""
    if user_id in connected_users:
        try:
            websocket = connected_users[user_id]
            await websocket.send_json({
                "type": "notification",
                "data": {
                    "id": notification.id,
                    "type": notification.type.value,
                    "title": notification.title,
                    "message": notification.message,
                    "priority": notification.priority.value,
                    "created_at": notification.created_at.isoformat()
                }
            })
        except Exception as e:
            print(f"Error sending real-time notification: {e}")
            # Remove disconnected user
            del connected_users[user_id]

async def send_achievement_notification(user_id: int, achievement_name: str, db: Session):
    """Send achievement unlock notification"""
    notification = NotificationCreate(
        user_id=user_id,
        type=NotificationType.ACHIEVEMENT,
        title="🏆 ¡Logro Desbloqueado!",
        message=f"Has desbloqueado: {achievement_name}",
        data={"achievement": achievement_name},
        priority="high"
    )
    
    await create_notification(notification, BackgroundTasks(), db)

async def send_study_reminder(user_id: int, subject: str, db: Session):
    """Send study reminder notification"""
    notification = NotificationCreate(
        user_id=user_id,
        type=NotificationType.REMINDER,
        title="📚 Recordatorio de Estudio",
        message=f"Es hora de continuar estudiando {subject}",
        data={"subject": subject},
        priority="medium",
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    await create_notification(notification, BackgroundTasks(), db)

async def send_battle_result_notification(user_id: int, result: str, enemy: str, db: Session):
    """Send battle result notification"""
    emoji = "🎉" if result == "victory" else "💪"
    message = f"¡Victoria contra {enemy}!" if result == "victory" else f"Derrota contra {enemy}. ¡Sigue entrenando!"
    
    notification = NotificationCreate(
        user_id=user_id,
        type=NotificationType.BATTLE,
        title=f"{emoji} Resultado de Batalla",
        message=message,
        data={"result": result, "enemy": enemy},
        priority="medium"
    )
    
    await create_notification(notification, BackgroundTasks(), db)

async def send_rank_promotion_notification(user_id: int, new_rank: str, db: Session):
    """Send rank promotion notification"""
    notification = NotificationCreate(
        user_id=user_id,
        type=NotificationType.PROMOTION,
        title="🔥 ¡Promoción de Rango!",
        message=f"¡Felicitaciones! Has ascendido al rango {new_rank}",
        data={"new_rank": new_rank},
        priority="high"
    )
    
    await create_notification(notification, BackgroundTasks(), db)