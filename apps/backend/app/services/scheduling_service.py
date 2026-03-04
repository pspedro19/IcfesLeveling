"""
Smart Scheduling Service
Implements intelligent scheduling system with daily, weekly, and monthly planning
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta, time
import json
import logging
from enum import Enum
import pytz
from dataclasses import dataclass

from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.notification import Notification
from ..core.config import settings
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class ScheduleType(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class StudySessionType(Enum):
    NEW_CONTENT = "new_content"
    REVIEW = "review"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"
    INTENSIVE = "intensive"
    LIGHT = "light"

@dataclass
class StudySession:
    session_id: str
    user_id: str
    plan_id: str
    session_type: StudySessionType
    scheduled_start: datetime
    estimated_duration: int  # minutes
    content_topics: List[str]
    difficulty_level: int
    priority: Priority
    is_flexible: bool = True
    prerequisites_met: bool = True
    resources: Dict[str, Any] = None

class SchedulingService:
    """
    Advanced scheduling service for personalized study planning
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.timezone = pytz.timezone(settings.DEFAULT_TIMEZONE)
        
    async def create_intelligent_schedule(
        self,
        user_id: str,
        plan_id: str,
        preferences: Dict[str, Any] = None,
        target_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create an intelligent study schedule based on user preferences and constraints
        """
        try:
            # Get user and study plan
            user = self.db.query(User).filter(User.id == user_id).first()
            study_plan = self.db.query(StudyPlan).filter(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id
            ).first()
            
            if not user or not study_plan:
                raise ValueError("User or study plan not found")
            
            # Analyze user's learning patterns
            learning_patterns = await self._analyze_user_learning_patterns(user_id)
            
            # Get optimal study times
            optimal_times = await self._determine_optimal_study_times(
                user_id, preferences, learning_patterns
            )
            
            # Create schedule framework
            schedule_framework = await self._create_schedule_framework(
                user_id, plan_id, target_date, preferences
            )
            
            # Generate daily schedules
            daily_schedules = await self._generate_daily_schedules(
                schedule_framework, optimal_times, learning_patterns
            )
            
            # Add review cycles
            review_schedules = await self._create_review_cycles(
                user_id, plan_id, daily_schedules
            )
            
            # Create reminder system
            reminder_system = await self._setup_reminder_system(
                user_id, daily_schedules, preferences
            )
            
            intelligent_schedule = {
                "schedule_id": f"schedule-{user_id}-{plan_id}-{int(datetime.now().timestamp())}",
                "user_id": user_id,
                "plan_id": plan_id,
                "created_at": datetime.now().isoformat(),
                "target_date": target_date.isoformat() if target_date else None,
                "learning_patterns": learning_patterns,
                "optimal_times": optimal_times,
                "schedule_framework": schedule_framework,
                "daily_schedules": daily_schedules,
                "review_schedules": review_schedules,
                "reminder_system": reminder_system,
                "flexibility_settings": {
                    "allow_rescheduling": preferences.get("allow_rescheduling", True),
                    "buffer_time_minutes": preferences.get("buffer_time", 15),
                    "max_daily_hours": preferences.get("max_daily_hours", 3),
                    "min_session_minutes": preferences.get("min_session", 25),
                    "max_session_minutes": preferences.get("max_session", 90)
                },
                "adaptive_features": {
                    "auto_difficulty_adjustment": True,
                    "performance_based_pacing": True,
                    "intelligent_break_scheduling": True,
                    "mood_based_content_selection": True
                }
            }
            
            # Cache the schedule
            cache_key = f"intelligent_schedule:{user_id}:{plan_id}"
            cache_service.set(cache_key, intelligent_schedule, ttl=7200)
            
            return intelligent_schedule
            
        except Exception as e:
            logger.error(f"Error creating intelligent schedule: {str(e)}")
            raise
    
    async def get_daily_schedule(
        self,
        user_id: str,
        date: datetime = None
    ) -> Dict[str, Any]:
        """
        Get the daily schedule for a specific date
        """
        if not date:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        try:
            # Get cached schedule if available
            cache_key = f"daily_schedule:{user_id}:{date.strftime('%Y-%m-%d')}"
            cached_schedule = cache_service.get(cache_key)
            
            if cached_schedule:
                return cached_schedule
            
            # Generate daily schedule
            daily_schedule = await self._generate_single_day_schedule(user_id, date)
            
            # Add real-time adjustments
            daily_schedule = await self._apply_real_time_adjustments(
                user_id, daily_schedule
            )
            
            # Cache the schedule
            cache_service.set(cache_key, daily_schedule, ttl=3600)  # 1 hour
            
            return daily_schedule
            
        except Exception as e:
            logger.error(f"Error getting daily schedule: {str(e)}")
            return {"error": str(e)}
    
    async def reschedule_session(
        self,
        user_id: str,
        session_id: str,
        new_time: datetime,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Reschedule a study session with intelligent conflict resolution
        """
        try:
            # Get current schedule
            current_schedule = await self._get_current_schedule(user_id)
            
            # Find the session to reschedule
            session_to_reschedule = await self._find_session(
                current_schedule, session_id
            )
            
            if not session_to_reschedule:
                raise ValueError(f"Session {session_id} not found")
            
            # Check for conflicts
            conflicts = await self._check_scheduling_conflicts(
                user_id, new_time, session_to_reschedule["estimated_duration"]
            )
            
            # Resolve conflicts if any
            if conflicts:
                resolution = await self._resolve_scheduling_conflicts(
                    user_id, new_time, session_to_reschedule, conflicts
                )
                if not resolution["success"]:
                    return {
                        "success": False,
                        "conflicts": conflicts,
                        "suggested_times": resolution["alternatives"]
                    }
                new_time = resolution["resolved_time"]
            
            # Update the schedule
            updated_schedule = await self._update_schedule_with_reschedule(
                current_schedule, session_id, new_time, reason
            )
            
            # Update reminders
            await self._update_reminders_for_reschedule(
                user_id, session_id, new_time
            )
            
            # Log the reschedule
            await self._log_reschedule_event(
                user_id, session_id, session_to_reschedule["scheduled_start"], 
                new_time, reason
            )
            
            return {
                "success": True,
                "session_id": session_id,
                "old_time": session_to_reschedule["scheduled_start"],
                "new_time": new_time.isoformat(),
                "updated_schedule": updated_schedule
            }
            
        except Exception as e:
            logger.error(f"Error rescheduling session: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def suggest_optimal_study_times(
        self,
        user_id: str,
        duration_minutes: int,
        date_range: Tuple[datetime, datetime] = None,
        session_type: StudySessionType = StudySessionType.NEW_CONTENT
    ) -> List[Dict[str, Any]]:
        """
        Suggest optimal study times based on user patterns and availability
        """
        try:
            if not date_range:
                start_date = datetime.now()
                end_date = start_date + timedelta(days=7)
                date_range = (start_date, end_date)
            
            # Get user's historical performance data
            performance_patterns = await self._analyze_performance_by_time(user_id)
            
            # Get user's availability
            availability = await self._get_user_availability(user_id, date_range)
            
            # Calculate optimal time slots
            optimal_slots = await self._calculate_optimal_time_slots(
                performance_patterns, availability, duration_minutes, session_type
            )
            
            # Rank suggestions by effectiveness
            ranked_suggestions = await self._rank_time_suggestions(
                optimal_slots, user_id, session_type
            )
            
            return ranked_suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting optimal study times: {str(e)}")
            return []
    
    async def create_study_streaks_tracking(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Create and track study streaks for motivation
        """
        try:
            # Get recent study activity
            recent_activity = await self._get_recent_study_activity(user_id)
            
            # Calculate current streak
            current_streak = await self._calculate_current_streak(recent_activity)
            
            # Get streak history
            streak_history = await self._get_streak_history(user_id)
            
            # Calculate streak statistics
            streak_stats = await self._calculate_streak_statistics(streak_history)
            
            # Create streak challenges
            streak_challenges = await self._create_streak_challenges(
                current_streak, streak_stats
            )
            
            streaks_data = {
                "user_id": user_id,
                "current_streak": current_streak,
                "longest_streak": streak_stats["longest_streak"],
                "total_study_days": streak_stats["total_study_days"],
                "streak_history": streak_history[-30:],  # Last 30 entries
                "active_challenges": streak_challenges,
                "streak_rewards": await self._calculate_streak_rewards(current_streak),
                "next_milestone": await self._get_next_streak_milestone(current_streak),
                "motivation_message": await self._generate_streak_motivation_message(
                    current_streak, streak_stats
                )
            }
            
            return streaks_data
            
        except Exception as e:
            logger.error(f"Error creating study streaks tracking: {str(e)}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _analyze_user_learning_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's learning patterns from historical data"""
        
        # Get recent study sessions
        recent_sessions = await self._get_recent_study_sessions(user_id, days=30)
        
        if not recent_sessions:
            return {
                "preferred_times": ["19:00", "20:00", "21:00"],
                "optimal_session_length": 45,
                "peak_performance_hours": [19, 20, 21],
                "learning_velocity": "medium",
                "break_preferences": {"frequency": 25, "duration": 5}
            }
        
        # Analyze time preferences
        time_patterns = await self._analyze_time_patterns(recent_sessions)
        
        # Analyze session length preferences
        length_patterns = await self._analyze_session_length_patterns(recent_sessions)
        
        # Analyze performance by time of day
        performance_by_time = await self._analyze_performance_by_time_of_day(
            user_id, recent_sessions
        )
        
        return {
            "preferred_times": time_patterns["preferred_start_times"],
            "optimal_session_length": length_patterns["optimal_length"],
            "peak_performance_hours": performance_by_time["peak_hours"],
            "learning_velocity": length_patterns["learning_velocity"],
            "break_preferences": length_patterns["break_patterns"],
            "consistency_score": time_patterns["consistency"],
            "flexibility_score": time_patterns["flexibility"]
        }
    
    async def _determine_optimal_study_times(
        self,
        user_id: str,
        preferences: Dict[str, Any],
        learning_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine optimal study times for the user"""
        
        # Get user's preferred times from preferences
        user_preferred_times = preferences.get("preferred_times", [])
        
        # Combine with learned patterns
        peak_hours = learning_patterns["peak_performance_hours"]
        
        # Create time slots
        optimal_slots = []
        
        # Morning slots (if user is a morning person)
        if any(hour < 12 for hour in peak_hours):
            optimal_slots.extend([
                {"start_time": "07:00", "end_time": "09:00", "effectiveness": 0.9},
                {"start_time": "09:00", "end_time": "11:00", "effectiveness": 0.85}
            ])
        
        # Afternoon slots
        if any(12 <= hour < 17 for hour in peak_hours):
            optimal_slots.extend([
                {"start_time": "14:00", "end_time": "16:00", "effectiveness": 0.8},
                {"start_time": "16:00", "end_time": "18:00", "effectiveness": 0.75}
            ])
        
        # Evening slots (most common)
        if any(hour >= 17 for hour in peak_hours):
            optimal_slots.extend([
                {"start_time": "19:00", "end_time": "21:00", "effectiveness": 0.95},
                {"start_time": "21:00", "end_time": "23:00", "effectiveness": 0.85}
            ])
        
        return {
            "optimal_slots": optimal_slots,
            "peak_performance_window": {
                "start": f"{min(peak_hours):02d}:00",
                "end": f"{max(peak_hours) + 1:02d}:00"
            },
            "recommended_session_length": learning_patterns["optimal_session_length"],
            "break_frequency": learning_patterns["break_preferences"]["frequency"],
            "break_duration": learning_patterns["break_preferences"]["duration"]
        }
    
    async def _create_schedule_framework(
        self,
        user_id: str,
        plan_id: str,
        target_date: Optional[datetime],
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create the basic framework for the schedule"""
        
        # Get study plan data
        study_plan = self.db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
        plan_data = study_plan.plan_data
        if isinstance(plan_data, str):
            plan_data = json.loads(plan_data)
        
        # Calculate total time needed
        total_hours = sum(
            unit.get("estimated_hours", unit.get("personalized_hours", 4))
            for unit in plan_data.get("units", [])
        )
        
        # Determine study frequency
        daily_study_time = preferences.get("daily_study_minutes", 60) / 60  # Convert to hours
        
        # Calculate timeline
        if not target_date:
            estimated_days = max(int(total_hours / daily_study_time), 30)
            target_date = datetime.now() + timedelta(days=estimated_days)
        
        available_days = (target_date - datetime.now()).days
        required_daily_hours = total_hours / max(available_days, 1)
        
        return {
            "total_estimated_hours": total_hours,
            "target_completion_date": target_date.isoformat(),
            "available_study_days": available_days,
            "required_daily_hours": required_daily_hours,
            "recommended_daily_minutes": min(int(required_daily_hours * 60), 180),
            "total_units": len(plan_data.get("units", [])),
            "study_intensity": self._calculate_study_intensity(required_daily_hours),
            "buffer_days": max(int(available_days * 0.1), 7),  # 10% buffer or min 7 days
            "flexibility_level": self._determine_flexibility_level(
                required_daily_hours, preferences
            )
        }
    
    async def _generate_daily_schedules(
        self,
        framework: Dict[str, Any],
        optimal_times: Dict[str, Any],
        learning_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate daily schedules for the entire period"""
        
        daily_schedules = {}
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        target_date = datetime.fromisoformat(framework["target_completion_date"])
        
        current_date = start_date
        while current_date < target_date:
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Determine if it's a study day
            is_study_day = await self._is_study_day(current_date, learning_patterns)
            
            if is_study_day:
                daily_schedule = await self._create_single_day_schedule(
                    current_date, framework, optimal_times, learning_patterns
                )
                daily_schedules[date_str] = daily_schedule
            
            current_date += timedelta(days=1)
        
        return daily_schedules
    
    async def _create_single_day_schedule(
        self,
        date: datetime,
        framework: Dict[str, Any],
        optimal_times: Dict[str, Any],
        learning_patterns: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create schedule for a single day"""
        
        # Determine daily study time allocation
        recommended_minutes = framework["recommended_daily_minutes"]
        session_length = optimal_times["recommended_session_length"]
        
        # Calculate number of sessions
        num_sessions = max(1, recommended_minutes // session_length)
        
        # Create study sessions
        sessions = []
        optimal_slots = optimal_times["optimal_slots"]
        
        for i in range(min(num_sessions, len(optimal_slots))):
            slot = optimal_slots[i]
            session_start = datetime.combine(
                date.date(),
                time.fromisoformat(slot["start_time"])
            )
            
            session = {
                "session_id": f"session-{date.strftime('%Y%m%d')}-{i+1}",
                "start_time": session_start.isoformat(),
                "duration_minutes": session_length,
                "session_type": self._determine_session_type(i, num_sessions),
                "effectiveness_score": slot["effectiveness"],
                "content_focus": await self._determine_content_focus(
                    date, i, framework
                ),
                "break_schedule": await self._create_break_schedule(
                    session_length, learning_patterns
                )
            }
            sessions.append(session)
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "total_study_minutes": sum(s["duration_minutes"] for s in sessions),
            "sessions": sessions,
            "flexibility_windows": await self._create_flexibility_windows(
                date, sessions, framework
            ),
            "backup_plan": await self._create_backup_plan(sessions)
        }
    
    def _calculate_study_intensity(self, required_daily_hours: float) -> str:
        """Calculate study intensity level"""
        if required_daily_hours <= 1:
            return "light"
        elif required_daily_hours <= 2:
            return "moderate"
        elif required_daily_hours <= 3:
            return "intensive"
        else:
            return "very_intensive"
    
    def _determine_flexibility_level(
        self, required_daily_hours: float, preferences: Dict
    ) -> str:
        """Determine schedule flexibility level"""
        user_flexibility_pref = preferences.get("flexibility_preference", "medium")
        
        if required_daily_hours > 2.5:
            return "low"  # Need strict schedule
        elif user_flexibility_pref == "high":
            return "high"
        else:
            return "medium"
    
    async def _is_study_day(
        self, date: datetime, learning_patterns: Dict
    ) -> bool:
        """Determine if a given date should be a study day"""
        
        # Skip Sundays by default (can be overridden)
        if date.weekday() == 6:  # Sunday
            return False
        
        # Check consistency patterns
        consistency = learning_patterns.get("consistency_score", 0.7)
        
        # Higher consistency = more study days
        if consistency > 0.8:
            return date.weekday() < 6  # Monday to Saturday
        elif consistency > 0.6:
            return date.weekday() < 5  # Monday to Friday
        else:
            return date.weekday() in [0, 1, 2, 4]  # Mon, Tue, Wed, Fri
    
    def _determine_session_type(self, session_index: int, total_sessions: int) -> str:
        """Determine the type of study session"""
        if session_index == 0:
            return StudySessionType.NEW_CONTENT.value
        elif session_index == total_sessions - 1:
            return StudySessionType.REVIEW.value
        else:
            return StudySessionType.PRACTICE.value