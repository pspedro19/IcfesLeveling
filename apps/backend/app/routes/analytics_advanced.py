from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.clickhouse_service import clickhouse_service
from ..schemas.analytics import (
    EventTrackRequest,
    BatchEventTrackRequest,
    UserAnalyticsResponse,
    GlobalAnalyticsResponse,
    AnalyticsPeriod
)

router = APIRouter(prefix="/analytics", tags=["analytics"])
logger = logging.getLogger(__name__)

@router.post("/events")
async def track_events(
    request: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Track multiple analytics events (legacy endpoint for frontend compatibility)"""
    try:
        events = request.get("events", [])
        if not events:
            return {"message": "No events to track"}
        
        # Use a default user ID if no user is authenticated (for development)
        user_id = str(current_user.id) if current_user else "anonymous"
        
        # Process each event with error handling
        processed_count = 0
        for event in events:
            try:
                background_tasks.add_task(
                    clickhouse_service.insert_event,
                    event_type=event.get("event", "unknown"),
                    user_id=user_id,
                    event_data=event.get("properties", {}),
                    session_id=event.get("sessionId"),
                    platform="web"
                )
                processed_count += 1
            except Exception as e:
                logger.warning(f"Failed to process event: {e}")
                # Continue processing other events
                continue
        
        return {"message": f"{processed_count} events tracked successfully"}
    except Exception as e:
        logger.error(f"Error tracking events: {e}")
        # Return success even on error to prevent frontend issues
        return {"message": "Events processing completed"}

@router.post("/track")
async def track_event(
    request: EventTrackRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Track a single analytics event"""
    try:
        # Add to background task to not block the request
        background_tasks.add_task(
            clickhouse_service.insert_event,
            event_type=request.event_type,
            user_id=str(current_user.id),
            event_data=request.event_data,
            session_id=request.session_id,
            platform=request.platform
        )
        
        return {"message": "Event tracked successfully"}
    except Exception as e:
        logger.error(f"Error tracking event: {e}")
        raise HTTPException(status_code=500, detail="Error tracking event")

@router.post("/track/batch")
async def track_batch_events(
    request: BatchEventTrackRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Track multiple analytics events in batch"""
    try:
        # Prepare events with user_id
        events = []
        for event in request.events:
            events.append({
                'user_id': str(current_user.id),
                'event_type': event.event_type,
                'event_data': event.event_data,
                'session_id': event.session_id,
                'platform': event.platform,
                'event_time': event.event_time or datetime.now()
            })
        
        # Add to background task
        background_tasks.add_task(
            clickhouse_service.insert_batch_events,
            events
        )
        
        return {"message": f"{len(events)} events tracked successfully"}
    except Exception as e:
        logger.error(f"Error tracking batch events: {e}")
        raise HTTPException(status_code=500, detail="Error tracking batch events")

@router.post("/battle/complete")
async def track_battle_completion(
    battle_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track battle completion analytics"""
    try:
        # Add user_id to battle data
        battle_data['user_id'] = str(current_user.id)
        
        # Track in ClickHouse
        background_tasks.add_task(
            clickhouse_service.track_battle_analytics,
            battle_data
        )
        
        # Also track individual question performance if provided
        if 'question_performance' in battle_data:
            for perf in battle_data['question_performance']:
                perf['user_id'] = str(current_user.id)
                perf['battle_id'] = battle_data['battle_id']
                background_tasks.add_task(
                    clickhouse_service.track_question_performance,
                    perf
                )
        
        return {"message": "Battle analytics tracked successfully"}
    except Exception as e:
        logger.error(f"Error tracking battle completion: {e}")
        raise HTTPException(status_code=500, detail="Error tracking battle analytics")

@router.get("/user/me", response_model=UserAnalyticsResponse)
async def get_my_analytics(
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTH),
    current_user: User = Depends(get_current_user)
):
    """Get current user's analytics"""
    try:
        days_map = {
            AnalyticsPeriod.WEEK: 7,
            AnalyticsPeriod.MONTH: 30,
            AnalyticsPeriod.QUARTER: 90,
            AnalyticsPeriod.YEAR: 365
        }
        
        analytics = clickhouse_service.get_user_analytics(
            user_id=str(current_user.id),
            days=days_map[period]
        )
        
        return UserAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving analytics")

@router.get("/user/{user_id}", response_model=UserAnalyticsResponse)
async def get_user_analytics(
    user_id: str,
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTH),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a specific user (admin only)"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        days_map = {
            AnalyticsPeriod.WEEK: 7,
            AnalyticsPeriod.MONTH: 30,
            AnalyticsPeriod.QUARTER: 90,
            AnalyticsPeriod.YEAR: 365
        }
        
        analytics = clickhouse_service.get_user_analytics(
            user_id=user_id,
            days=days_map[period]
        )
        
        return UserAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving analytics")

@router.get("/global", response_model=GlobalAnalyticsResponse)
async def get_global_analytics(
    period: AnalyticsPeriod = Query(AnalyticsPeriod.WEEK),
    current_user: User = Depends(get_current_user)
):
    """Get global platform analytics"""
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        days_map = {
            AnalyticsPeriod.WEEK: 7,
            AnalyticsPeriod.MONTH: 30,
            AnalyticsPeriod.QUARTER: 90,
            AnalyticsPeriod.YEAR: 365
        }
        
        analytics = clickhouse_service.get_global_analytics(
            days=days_map[period]
        )
        
        return GlobalAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error getting global analytics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving analytics")

@router.post("/user/progression")
async def update_user_progression(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user progression snapshot in analytics"""
    try:
        # Get user profile
        from ..models.user_profile import UserProfile
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == current_user.id
        ).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        progression_data = {
            'user_id': str(current_user.id),
            'level': profile.level,
            'experience': profile.experience,
            'rank': profile.rank,
            'hp': profile.hp,
            'mp': profile.mp,
            'power': profile.power,
            'wisdom': profile.wisdom,
            'speed': profile.speed,
            'orbs': profile.orbs,
            'crystals': profile.crystals,
            'streak_days': profile.streak_days
        }
        
        background_tasks.add_task(
            clickhouse_service.update_user_progression,
            progression_data
        )
        
        return {"message": "User progression updated"}
    except Exception as e:
        logger.error(f"Error updating user progression: {e}")
        raise HTTPException(status_code=500, detail="Error updating progression")

@router.get("/export/csv")
async def export_analytics_csv(
    period: AnalyticsPeriod = Query(AnalyticsPeriod.MONTH),
    current_user: User = Depends(get_current_user)
):
    """Export analytics data as CSV (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # This would generate a CSV file with analytics data
        # For now, return a placeholder
        return {
            "message": "CSV export feature coming soon",
            "period": period
        }
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        raise HTTPException(status_code=500, detail="Error exporting analytics")

@router.post("/report/daily")
async def generate_daily_report(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate daily analytics report (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        report = clickhouse_service.generate_daily_report()
        
        return {
            "message": "Daily report generated successfully",
            "report": report
        }
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise HTTPException(status_code=500, detail="Error generating report")

@router.get("/realtime/active-users")
async def get_realtime_active_users(
    current_user: User = Depends(get_current_user)
):
    """Get real-time active users count"""
    try:
        # Get users active in the last 5 minutes
        result = clickhouse_service.client.execute("""
            SELECT count(DISTINCT user_id) as active_users
            FROM game_events
            WHERE event_time >= now() - INTERVAL 5 MINUTE
        """)
        
        return {
            "active_users": result[0][0] if result else 0,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        raise HTTPException(status_code=500, detail="Error getting active users")

@router.get("/realtime/events-stream")
async def get_events_stream(
    current_user: User = Depends(get_current_user)
):
    """Get real-time events stream (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get last 50 events
        events = clickhouse_service.client.execute("""
            SELECT 
                event_time,
                user_id,
                event_type,
                event_data,
                platform
            FROM game_events
            ORDER BY event_time DESC
            LIMIT 50
        """)
        
        return {
            "events": [
                {
                    "event_time": row[0].isoformat(),
                    "user_id": row[1],
                    "event_type": row[2],
                    "event_data": row[3],
                    "platform": row[4]
                }
                for row in events
            ]
        }
    except Exception as e:
        logger.error(f"Error getting events stream: {e}")
        raise HTTPException(status_code=500, detail="Error getting events")