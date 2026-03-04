"""
Notification and Reminder Service
Comprehensive system for intelligent notifications, reminders, and user engagement
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta, time
import json
import logging
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio

from ..models.user import User
from ..models.notification import Notification
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.battle import Battle
from ..core.config import settings
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    STUDY_REMINDER = "study_reminder"
    ACHIEVEMENT_EARNED = "achievement_earned"
    STREAK_MILESTONE = "streak_milestone"
    PLAN_UPDATE = "plan_update"
    PROGRESS_SUMMARY = "progress_summary"
    MOTIVATION = "motivation"
    DEADLINE_APPROACH = "deadline_approach"
    PERFORMANCE_INSIGHT = "performance_insight"
    SOCIAL_UPDATE = "social_update"
    CHALLENGE_INVITATION = "challenge_invitation"

class NotificationChannel(Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"

class ReminderFrequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    CUSTOM = "custom"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

@dataclass
class SmartReminder:
    """Represents an intelligent reminder"""
    reminder_id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    scheduled_time: datetime
    frequency: ReminderFrequency
    priority: Priority
    channels: List[NotificationChannel]
    context_data: Dict[str, Any]
    is_active: bool = True
    personalization_data: Dict[str, Any] = None

@dataclass
class NotificationPreference:
    """User's notification preferences"""
    user_id: str
    notification_type: NotificationType
    enabled: bool
    preferred_channels: List[NotificationChannel]
    quiet_hours_start: time
    quiet_hours_end: time
    frequency_preference: str
    personalization_level: str

class NotificationReminderService:
    """
    Advanced notification and reminder service with AI-powered personalization
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def create_intelligent_reminder_system(
        self,
        user_id: str,
        plan_id: str = None,
        preferences: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a comprehensive intelligent reminder system for a user
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Analyze user patterns for optimal timing
            optimal_times = await self._analyze_optimal_notification_times(user_id)
            
            # Get user preferences
            user_preferences = await self._get_notification_preferences(user_id, preferences)
            
            # Create study reminders
            study_reminders = await self._create_study_reminders(
                user_id, plan_id, optimal_times, user_preferences
            )
            
            # Create progress check reminders
            progress_reminders = await self._create_progress_reminders(
                user_id, plan_id, user_preferences
            )
            
            # Create motivation reminders
            motivation_reminders = await self._create_motivation_reminders(
                user_id, optimal_times, user_preferences
            )
            
            # Create deadline reminders
            deadline_reminders = await self._create_deadline_reminders(
                user_id, plan_id, user_preferences
            )
            
            # Create adaptive reminders
            adaptive_reminders = await self._create_adaptive_reminders(
                user_id, optimal_times, user_preferences
            )
            
            # Set up reminder scheduling
            scheduling_system = await self._setup_reminder_scheduling(
                user_id, study_reminders + progress_reminders + motivation_reminders + 
                deadline_reminders + adaptive_reminders
            )
            
            reminder_system = {
                "user_id": user_id,
                "plan_id": plan_id,
                "created_at": datetime.now().isoformat(),
                "optimal_times": optimal_times,
                "user_preferences": asdict(user_preferences) if user_preferences else {},
                "reminder_categories": {
                    "study_reminders": len(study_reminders),
                    "progress_reminders": len(progress_reminders),
                    "motivation_reminders": len(motivation_reminders),
                    "deadline_reminders": len(deadline_reminders),
                    "adaptive_reminders": len(adaptive_reminders)
                },
                "all_reminders": [
                    asdict(reminder) for reminder in 
                    study_reminders + progress_reminders + motivation_reminders + 
                    deadline_reminders + adaptive_reminders
                ],
                "scheduling_system": scheduling_system,
                "personalization_features": {
                    "adaptive_timing": True,
                    "content_personalization": True,
                    "frequency_optimization": True,
                    "context_awareness": True
                },
                "effectiveness_tracking": await self._setup_effectiveness_tracking(user_id)
            }
            
            # Cache the reminder system
            cache_key = f"reminder_system:{user_id}:{plan_id or 'all'}"
            cache_service.set(cache_key, reminder_system, ttl=3600 * 24)  # 24 hours
            
            return reminder_system
            
        except Exception as e:
            logger.error(f"Error creating intelligent reminder system: {str(e)}")
            raise
    
    async def send_personalized_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        context: Dict[str, Any] = None,
        channels: List[NotificationChannel] = None
    ) -> Dict[str, Any]:
        """
        Send a personalized notification to a user
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Check user preferences
            preferences = await self._get_notification_preferences(user_id)
            if not await self._should_send_notification(user_id, notification_type, preferences):
                return {"sent": False, "reason": "User preferences block this notification"}
            
            # Generate personalized content
            personalized_content = await self._generate_personalized_content(
                user_id, notification_type, context
            )
            
            # Determine optimal channels
            if not channels:
                channels = await self._determine_optimal_channels(
                    user_id, notification_type, preferences
                )
            
            # Create notification record
            notification = Notification(
                user_id=user_id,
                type=notification_type.value,
                title=personalized_content["title"],
                message=personalized_content["message"],
                data=context or {},
                channels=json.dumps([channel.value for channel in channels]),
                created_at=datetime.now()
            )
            
            self.db.add(notification)
            self.db.commit()
            
            # Send through each channel
            delivery_results = {}
            for channel in channels:
                result = await self._send_through_channel(
                    channel, user, personalized_content, context
                )
                delivery_results[channel.value] = result
            
            # Track engagement
            await self._track_notification_sent(user_id, notification.id, notification_type)
            
            return {
                "sent": True,
                "notification_id": str(notification.id),
                "channels_used": [channel.value for channel in channels],
                "personalized_content": personalized_content,
                "delivery_results": delivery_results,
                "expected_engagement_rate": await self._predict_engagement_rate(
                    user_id, notification_type, personalized_content
                )
            }
            
        except Exception as e:
            logger.error(f"Error sending personalized notification: {str(e)}")
            return {"sent": False, "error": str(e)}
    
    async def process_smart_reminders(
        self,
        user_id: str = None,
        check_time: datetime = None
    ) -> Dict[str, Any]:
        """
        Process smart reminders that are due to be sent
        """
        if not check_time:
            check_time = datetime.now()
        
        try:
            # Get due reminders
            due_reminders = await self._get_due_reminders(user_id, check_time)
            
            processed_reminders = []
            failed_reminders = []
            
            for reminder in due_reminders:
                try:
                    # Check if reminder should still be sent (user might have already studied)
                    should_send = await self._should_send_reminder(reminder, check_time)
                    
                    if should_send:
                        # Generate context-aware content
                        context = await self._generate_reminder_context(reminder)
                        
                        # Send the reminder
                        send_result = await self.send_personalized_notification(
                            reminder.user_id,
                            reminder.type,
                            context,
                            reminder.channels
                        )
                        
                        if send_result["sent"]:
                            processed_reminders.append({
                                "reminder_id": reminder.reminder_id,
                                "user_id": reminder.user_id,
                                "type": reminder.type.value,
                                "sent_at": check_time.isoformat(),
                                "channels": [channel.value for channel in reminder.channels],
                                "context": context
                            })
                            
                            # Update reminder for next occurrence if recurring
                            if reminder.frequency != ReminderFrequency.ONCE:
                                await self._schedule_next_reminder_occurrence(reminder)
                        else:
                            failed_reminders.append({
                                "reminder_id": reminder.reminder_id,
                                "error": send_result.get("error", "Unknown error")
                            })
                    else:
                        # Mark as skipped
                        await self._mark_reminder_skipped(reminder, "Condition not met")
                        
                except Exception as e:
                    logger.error(f"Error processing reminder {reminder.reminder_id}: {str(e)}")
                    failed_reminders.append({
                        "reminder_id": reminder.reminder_id,
                        "error": str(e)
                    })
            
            return {
                "processed_at": check_time.isoformat(),
                "total_due_reminders": len(due_reminders),
                "successfully_processed": len(processed_reminders),
                "failed_reminders": len(failed_reminders),
                "processed_reminders": processed_reminders,
                "failed_reminders": failed_reminders
            }
            
        except Exception as e:
            logger.error(f"Error processing smart reminders: {str(e)}")
            return {"error": str(e)}
    
    async def track_notification_engagement(
        self,
        notification_id: str,
        engagement_type: str,
        engagement_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Track user engagement with notifications
        """
        try:
            notification = self.db.query(Notification).filter(
                Notification.id == notification_id
            ).first()
            
            if not notification:
                raise ValueError(f"Notification {notification_id} not found")
            
            # Update notification engagement
            engagement_history = notification.engagement_history or []
            engagement_history.append({
                "type": engagement_type,
                "timestamp": datetime.now().isoformat(),
                "data": engagement_data or {}
            })
            
            notification.engagement_history = engagement_history
            notification.is_read = engagement_type in ["opened", "clicked", "acted_upon"]
            
            # Update user's notification statistics
            await self._update_user_notification_stats(
                notification.user_id, engagement_type, notification.type
            )
            
            # Learn from engagement for future personalization
            await self._learn_from_engagement(
                notification.user_id, notification, engagement_type, engagement_data
            )
            
            self.db.commit()
            
            return {
                "success": True,
                "notification_id": notification_id,
                "engagement_type": engagement_type,
                "total_engagements": len(engagement_history),
                "learning_updates": await self._get_learning_updates(
                    notification.user_id, engagement_type
                )
            }
            
        except Exception as e:
            logger.error(f"Error tracking notification engagement: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_notification_analytics(
        self,
        user_id: str,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """
        Get comprehensive notification analytics for a user
        """
        try:
            # Get notification data
            notifications = self.db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.created_at >= datetime.now() - timedelta(days=days_back)
            ).all()
            
            if not notifications:
                return {
                    "total_notifications": 0,
                    "engagement_rate": 0,
                    "analytics": "No notifications in period"
                }
            
            # Calculate engagement metrics
            engagement_metrics = await self._calculate_engagement_metrics(notifications)
            
            # Analyze notification types performance
            type_performance = await self._analyze_type_performance(notifications)
            
            # Analyze channel effectiveness
            channel_effectiveness = await self._analyze_channel_effectiveness(notifications)
            
            # Analyze timing effectiveness
            timing_analysis = await self._analyze_timing_effectiveness(notifications)
            
            # Generate insights
            insights = await self._generate_analytics_insights(
                engagement_metrics, type_performance, channel_effectiveness, timing_analysis
            )
            
            # Create optimization recommendations
            optimization_recommendations = await self._create_optimization_recommendations(
                user_id, insights
            )
            
            analytics = {
                "user_id": user_id,
                "analysis_period_days": days_back,
                "analysis_date": datetime.now().isoformat(),
                "total_notifications": len(notifications),
                "engagement_metrics": engagement_metrics,
                "type_performance": type_performance,
                "channel_effectiveness": channel_effectiveness,
                "timing_analysis": timing_analysis,
                "insights": insights,
                "optimization_recommendations": optimization_recommendations,
                "overall_effectiveness_score": await self._calculate_overall_effectiveness(
                    engagement_metrics, type_performance, channel_effectiveness
                )
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting notification analytics: {str(e)}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _analyze_optimal_notification_times(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's activity patterns to find optimal notification times"""
        
        # Get recent activity data
        recent_battles = self.db.query(Battle).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.now() - timedelta(days=30)
        ).all()
        
        if not recent_battles:
            # Default optimal times
            return {
                "morning": "09:00",
                "afternoon": "15:00", 
                "evening": "19:00",
                "peak_activity_hours": [9, 15, 19],
                "activity_pattern": "default"
            }
        
        # Analyze activity by hour
        hourly_activity = {}
        for battle in recent_battles:
            hour = battle.created_at.hour
            hourly_activity[hour] = hourly_activity.get(hour, 0) + 1
        
        # Find peak hours
        sorted_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)
        peak_hours = [hour for hour, count in sorted_hours[:3]]
        
        return {
            "peak_activity_hours": peak_hours,
            "activity_distribution": hourly_activity,
            "optimal_morning": f"{min([h for h in peak_hours if h < 12], default=9):02d}:00",
            "optimal_afternoon": f"{min([h for h in peak_hours if 12 <= h < 17], default=15):02d}:00",
            "optimal_evening": f"{min([h for h in peak_hours if h >= 17], default=19):02d}:00",
            "activity_pattern": await self._classify_activity_pattern(hourly_activity)
        }
    
    async def _create_study_reminders(
        self,
        user_id: str,
        plan_id: str,
        optimal_times: Dict[str, Any],
        preferences: NotificationPreference
    ) -> List[SmartReminder]:
        """Create intelligent study reminders"""
        
        reminders = []
        
        # Daily study reminder
        if preferences.enabled:
            for day_offset in range(7):  # Next 7 days
                reminder_date = datetime.now().date() + timedelta(days=day_offset)
                
                # Choose optimal time based on user patterns
                optimal_hour = optimal_times["peak_activity_hours"][0] if optimal_times["peak_activity_hours"] else 19
                reminder_time = datetime.combine(reminder_date, time(optimal_hour, 0))
                
                reminder = SmartReminder(
                    reminder_id=f"study-{user_id}-{day_offset}",
                    user_id=user_id,
                    type=NotificationType.STUDY_REMINDER,
                    title="Time to Study! 📚",
                    message="Your brain is ready for some learning. Let's make progress!",
                    scheduled_time=reminder_time,
                    frequency=ReminderFrequency.DAILY,
                    priority=Priority.MEDIUM,
                    channels=[NotificationChannel.IN_APP, NotificationChannel.PUSH],
                    context_data={
                        "plan_id": plan_id,
                        "optimal_time": True,
                        "personalized": True
                    }
                )
                reminders.append(reminder)
        
        return reminders
    
    async def _create_motivation_reminders(
        self,
        user_id: str,
        optimal_times: Dict[str, Any],
        preferences: NotificationPreference
    ) -> List[SmartReminder]:
        """Create motivational reminders"""
        
        reminders = []
        
        # Analyze user's recent performance for motivation context
        recent_performance = await self._analyze_recent_performance(user_id)
        
        motivation_messages = [
            "You're making great progress! Keep it up! 🌟",
            "Every question you answer brings you closer to your goals! 🎯",
            "Your dedication is inspiring! Let's continue the journey! 🚀",
            "Small steps lead to big achievements! You've got this! 💪",
            "Learning is a superpower, and you're getting stronger every day! ⚡"
        ]
        
        # Create weekly motivation reminder
        next_week = datetime.now() + timedelta(days=7)
        motivation_time = datetime.combine(
            next_week.date(),
            time(optimal_times["peak_activity_hours"][0] if optimal_times["peak_activity_hours"] else 10, 0)
        )
        
        reminder = SmartReminder(
            reminder_id=f"motivation-{user_id}-weekly",
            user_id=user_id,
            type=NotificationType.MOTIVATION,
            title="Weekly Motivation Boost! 🎉",
            message=motivation_messages[0],  # Will be personalized when sent
            scheduled_time=motivation_time,
            frequency=ReminderFrequency.WEEKLY,
            priority=Priority.LOW,
            channels=[NotificationChannel.IN_APP],
            context_data={
                "performance_context": recent_performance,
                "motivational": True
            }
        )
        reminders.append(reminder)
        
        return reminders
    
    async def _generate_personalized_content(
        self,
        user_id: str,
        notification_type: NotificationType,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Generate personalized notification content"""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"title": "Notification", "message": "You have an update"}
        
        # Get user's name for personalization
        user_name = user.username or "Student"
        user_level = user.level or 1
        user_rank = user.rank or "E"
        
        content = {"title": "", "message": "", "action_text": "", "emoji": "📚"}
        
        if notification_type == NotificationType.STUDY_REMINDER:
            content.update({
                "title": f"Study Time, {user_name}! 📚",
                "message": f"Level {user_level} warrior, your knowledge adventure awaits! Ready to level up?",
                "action_text": "Start Studying",
                "emoji": "🎯"
            })
            
        elif notification_type == NotificationType.ACHIEVEMENT_EARNED:
            achievement_name = context.get("achievement_name", "New Achievement")
            content.update({
                "title": f"Achievement Unlocked! 🏆",
                "message": f"Congratulations {user_name}! You've earned: {achievement_name}",
                "action_text": "View Achievement",
                "emoji": "🌟"
            })
            
        elif notification_type == NotificationType.STREAK_MILESTONE:
            streak_days = context.get("streak_days", 1)
            content.update({
                "title": f"{streak_days} Day Streak! 🔥",
                "message": f"Amazing {user_name}! {streak_days} days of consistent learning. You're on fire!",
                "action_text": "Keep the Streak",
                "emoji": "🔥"
            })
            
        elif notification_type == NotificationType.MOTIVATION:
            performance = context.get("performance_context", {})
            if performance.get("improving", False):
                content.update({
                    "title": f"You're Improving, {user_name}! 📈",
                    "message": f"Your performance is trending upward! Rank {user_rank} suits you well!",
                    "action_text": "Continue Learning",
                    "emoji": "📈"
                })
            else:
                content.update({
                    "title": f"Keep Going, {user_name}! 💪",
                    "message": f"Every expert was once a beginner. You're building something amazing!",
                    "action_text": "Study Now",
                    "emoji": "💪"
                })
        
        # Add personalization based on user patterns
        content = await self._add_pattern_based_personalization(user_id, content, context)
        
        return content
    
    async def _should_send_reminder(
        self, reminder: SmartReminder, check_time: datetime
    ) -> bool:
        """Check if a reminder should be sent based on current context"""
        
        # Check if user has studied recently (last 2 hours)
        recent_activity = self.db.query(Battle).filter(
            Battle.user_id == reminder.user_id,
            Battle.created_at >= check_time - timedelta(hours=2)
        ).first()
        
        if recent_activity and reminder.type == NotificationType.STUDY_REMINDER:
            return False  # Don't remind if user recently studied
        
        # Check quiet hours
        user_prefs = await self._get_notification_preferences(reminder.user_id)
        if user_prefs and user_prefs.quiet_hours_start and user_prefs.quiet_hours_end:
            current_time = check_time.time()
            if (user_prefs.quiet_hours_start <= current_time <= user_prefs.quiet_hours_end):
                return False
        
        # Check if user is currently active (if we have real-time data)
        # For now, assume we should send
        return True
    
    async def _send_through_channel(
        self,
        channel: NotificationChannel,
        user: User,
        content: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send notification through specific channel"""
        
        try:
            if channel == NotificationChannel.IN_APP:
                # For in-app notifications, we just mark as ready to display
                return {
                    "success": True,
                    "channel": "in_app",
                    "message": "Notification queued for in-app display"
                }
            
            elif channel == NotificationChannel.PUSH:
                # Here you would integrate with push notification service
                # For now, simulate success
                return {
                    "success": True,
                    "channel": "push",
                    "message": "Push notification sent (simulated)"
                }
            
            elif channel == NotificationChannel.EMAIL:
                # Here you would integrate with email service
                return {
                    "success": True,
                    "channel": "email", 
                    "message": "Email sent (simulated)"
                }
            
            else:
                return {
                    "success": False,
                    "channel": channel.value,
                    "error": "Channel not implemented"
                }
                
        except Exception as e:
            return {
                "success": False,
                "channel": channel.value,
                "error": str(e)
            }
    
    async def _calculate_engagement_metrics(
        self, notifications: List[Notification]
    ) -> Dict[str, Any]:
        """Calculate engagement metrics for notifications"""
        
        total_notifications = len(notifications)
        if total_notifications == 0:
            return {"engagement_rate": 0, "open_rate": 0, "action_rate": 0}
        
        opened_count = 0
        clicked_count = 0
        acted_upon_count = 0
        
        for notification in notifications:
            if notification.is_read:
                opened_count += 1
            
            engagement_history = notification.engagement_history or []
            for engagement in engagement_history:
                if engagement.get("type") == "clicked":
                    clicked_count += 1
                elif engagement.get("type") == "acted_upon":
                    acted_upon_count += 1
        
        return {
            "total_notifications": total_notifications,
            "opened_count": opened_count,
            "clicked_count": clicked_count,
            "acted_upon_count": acted_upon_count,
            "open_rate": (opened_count / total_notifications) * 100,
            "click_rate": (clicked_count / total_notifications) * 100,
            "action_rate": (acted_upon_count / total_notifications) * 100,
            "overall_engagement_rate": ((opened_count + clicked_count + acted_upon_count) / (total_notifications * 3)) * 100
        }