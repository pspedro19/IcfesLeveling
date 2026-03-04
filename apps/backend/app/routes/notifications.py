"""
Push Notifications Router for ICFES Leveling Mobile App

Endpoints:
- POST /notifications/register - Register FCM device token
- PUT /notifications/preferences - Update notification preferences
- GET /notifications/preferences - Get current notification preferences
- DELETE /notifications/unregister - Unregister device token
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from uuid import UUID
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.mobile_offline import UserDeviceToken
from ..schemas.notification import (
    RegisterDeviceRequest,
    RegisterDeviceResponse,
    NotificationPreferences,
    NotificationPreferencesResponse,
    UnregisterDeviceRequest,
)
from ..services.notification_service import NotificationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/register", response_model=RegisterDeviceResponse)
async def register_device(
    request: RegisterDeviceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a device for push notifications.

    This endpoint registers the FCM (Firebase Cloud Messaging) token
    for the current user's device, enabling push notifications.

    - **token**: FCM device token from Firebase
    - **platform**: Device platform ('ios' or 'android')
    - **device_info**: Optional device information (model, OS version, etc.)
    """
    try:
        # Convert device_info to dict if provided
        device_info_dict = None
        if request.device_info:
            device_info_dict = request.device_info.model_dump()

        # Use notification service to register the token
        notification_service = NotificationService(db)
        success = notification_service.register_device_token(
            user_id=current_user.id,
            token=request.token,
            platform=request.platform.value,
            device_info=device_info_dict
        )

        if success:
            logger.info(f"Device registered for user {current_user.id} on {request.platform.value}")
            return RegisterDeviceResponse(
                registered=True,
                message="Device registered successfully for push notifications"
            )
        else:
            logger.error(f"Failed to register device for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register device"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register device: {str(e)}"
        )


@router.delete("/unregister")
async def unregister_device(
    request: Optional[UnregisterDeviceRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unregister a device from push notifications.

    If a specific token is provided, only that token will be unregistered.
    If no token is provided, all tokens for the current user will be unregistered.
    """
    try:
        notification_service = NotificationService(db)
        token = request.token if request else None

        success = notification_service.unregister_device_token(
            user_id=current_user.id,
            token=token
        )

        if success:
            if token:
                logger.info(f"Device token unregistered for user {current_user.id}")
                return {"success": True, "message": "Device token unregistered"}
            else:
                logger.info(f"All device tokens unregistered for user {current_user.id}")
                return {"success": True, "message": "All device tokens unregistered"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to unregister device"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unregistering device: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unregister device: {str(e)}"
        )


@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's notification preferences.

    Returns the notification settings including:
    - Streak reminders (6pm, 9pm, 3:30am)
    - Hearts refilled notifications
    - League updates
    - Boss raid notifications
    - Quiet hours settings
    """
    try:
        # Try to get existing preferences from user profile or dedicated table
        # For now, we'll use a simple approach with default values
        # In production, this would be stored in a user_notification_preferences table

        # Check if user has a profile with notification settings
        # For MVP, return default preferences
        default_preferences = NotificationPreferences()

        # In a full implementation, you would query a notification_preferences table:
        # preferences = db.query(UserNotificationPreferences).filter(
        #     UserNotificationPreferences.user_id == current_user.id
        # ).first()

        return NotificationPreferencesResponse(
            user_id=current_user.id,
            preferences=default_preferences,
            updated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error getting notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification preferences: {str(e)}"
        )


@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    preferences: NotificationPreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's notification preferences.

    All fields are optional - only provided fields will be updated.

    - **streak_reminder_6pm**: Enable/disable 6 PM streak reminder
    - **streak_reminder_9pm**: Enable/disable 9 PM streak reminder
    - **streak_reminder_330am**: Enable/disable 3:30 AM last chance reminder
    - **hearts_refilled**: Enable/disable hearts refilled notification
    - **league_updates**: Enable/disable league promotion/relegation notifications
    - **boss_raid_starting**: Enable/disable boss raid event notifications
    - **quiet_hours_start**: Quiet hours start time (HH:MM format)
    - **quiet_hours_end**: Quiet hours end time (HH:MM format)
    """
    try:
        # In a full implementation, this would update a notification_preferences table
        # For MVP, we log the preferences and return them

        logger.info(f"User {current_user.id} updated notification preferences: {preferences.model_dump()}")

        # In production, you would:
        # 1. Check if user has existing preferences
        # 2. Update or create the preferences record
        # 3. Return the updated preferences

        # Example implementation:
        # existing = db.query(UserNotificationPreferences).filter(
        #     UserNotificationPreferences.user_id == current_user.id
        # ).first()
        #
        # if existing:
        #     for key, value in preferences.model_dump().items():
        #         setattr(existing, key, value)
        #     existing.updated_at = datetime.utcnow()
        # else:
        #     existing = UserNotificationPreferences(
        #         user_id=current_user.id,
        #         **preferences.model_dump()
        #     )
        #     db.add(existing)
        #
        # db.commit()
        # db.refresh(existing)

        return NotificationPreferencesResponse(
            user_id=current_user.id,
            preferences=preferences,
            updated_at=datetime.utcnow()
        )

    except Exception as e:
        logger.error(f"Error updating notification preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification preferences: {str(e)}"
        )


@router.get("/devices")
async def get_registered_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of registered devices for the current user.

    Returns information about all devices registered for push notifications.
    """
    try:
        devices = db.query(UserDeviceToken).filter(
            UserDeviceToken.user_id == current_user.id,
            UserDeviceToken.is_active == True
        ).all()

        return {
            "devices": [
                {
                    "id": str(device.id),
                    "platform": device.platform,
                    "device_info": device.device_info,
                    "registered_at": device.created_at.isoformat() if device.created_at else None,
                    "last_used": device.last_used_at.isoformat() if device.last_used_at else None
                }
                for device in devices
            ],
            "total": len(devices)
        }

    except Exception as e:
        logger.error(f"Error getting registered devices: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get registered devices: {str(e)}"
        )


@router.post("/test")
async def send_test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a test notification to the current user.

    This endpoint is useful for testing that push notifications are working correctly.
    """
    try:
        notification_service = NotificationService(db)

        success = notification_service.send_custom(
            user_id=current_user.id,
            title="Prueba de Notificacion",
            body="Esta es una notificacion de prueba de ICFES Leveling.",
            data={"type": "test", "timestamp": datetime.utcnow().isoformat()}
        )

        if success:
            return {
                "success": True,
                "message": "Test notification sent successfully"
            }
        else:
            return {
                "success": False,
                "message": "No registered device found or notification failed"
            }

    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test notification: {str(e)}"
        )
