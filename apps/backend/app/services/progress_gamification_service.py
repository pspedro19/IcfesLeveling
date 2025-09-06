"""
Progress Tracking and Gamification Service
Comprehensive system for tracking learning progress and implementing gamification elements
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
import json
import logging
import math
from enum import Enum
from dataclasses import dataclass, asdict

from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.battle import Battle, BattleAnswer
from ..models.video_tracking import VideoTracking
from ..models.achievement import Achievement, UserAchievement
from ..models.notification import Notification
from ..core.config import settings
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class RewardType(Enum):
    XP = "xp"
    ORBS = "orbs"
    CRYSTALS = "crystals"
    BADGE = "badge"
    TITLE = "title"
    UNLOCK = "unlock"

class AchievementCategory(Enum):
    PROGRESS = "progress"
    STREAK = "streak"
    MASTERY = "mastery"
    SOCIAL = "social"
    SPECIAL = "special"

class MilestoneType(Enum):
    UNIT_COMPLETE = "unit_complete"
    TOPIC_MASTERY = "topic_mastery"
    STREAK_ACHIEVEMENT = "streak_achievement"
    SCORE_IMPROVEMENT = "score_improvement"
    TIME_MILESTONE = "time_milestone"

@dataclass
class ProgressMetric:
    """Represents a progress tracking metric"""
    metric_id: str
    name: str
    current_value: float
    target_value: float
    unit: str
    progress_percentage: float
    last_updated: datetime
    trend: str  # "increasing", "decreasing", "stable"
    
@dataclass
class Reward:
    """Represents a reward in the gamification system"""
    reward_id: str
    type: RewardType
    amount: int
    description: str
    rarity: str  # "common", "rare", "epic", "legendary"
    icon_url: str = None
    unlocked_content: Dict[str, Any] = None

@dataclass
class Milestone:
    """Represents a learning milestone"""
    milestone_id: str
    type: MilestoneType
    title: str
    description: str
    target_criteria: Dict[str, Any]
    rewards: List[Reward]
    achieved_at: Optional[datetime] = None
    progress_percentage: float = 0.0

class ProgressGamificationService:
    """
    Comprehensive service for progress tracking and gamification
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # XP calculation constants
        self.XP_QUESTION_CORRECT = 10
        self.XP_QUESTION_BONUS_DIFFICULTY = 5
        self.XP_VIDEO_COMPLETE = 5
        self.XP_UNIT_COMPLETE = 100
        self.XP_STREAK_DAILY = 25
        self.XP_ACHIEVEMENT = 50
        
        # Rank thresholds
        self.RANK_THRESHOLDS = {
            'E': 0, 'D': 500, 'C': 1500, 'B': 3500, 
            'A': 7500, 'S': 15000, 'S+': 30000
        }
        
    async def track_comprehensive_progress(
        self,
        user_id: str,
        plan_id: str = None,
        include_predictions: bool = True
    ) -> Dict[str, Any]:
        """
        Track comprehensive learning progress across all metrics
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Get all progress metrics
            progress_metrics = await self._calculate_all_progress_metrics(
                user_id, plan_id
            )
            
            # Calculate learning analytics
            learning_analytics = await self._calculate_learning_analytics(
                user_id, plan_id
            )
            
            # Track milestones
            milestones = await self._track_milestones(user_id, plan_id)
            
            # Get achievements
            achievements = await self._get_user_achievements(user_id)
            
            # Calculate streaks
            streaks = await self._calculate_streaks(user_id)
            
            # Get performance trends
            trends = await self._analyze_performance_trends(user_id, days=30)
            
            # Predict future progress
            predictions = {}
            if include_predictions:
                predictions = await self._predict_future_progress(
                    user_id, progress_metrics, trends
                )
            
            comprehensive_progress = {
                "user_id": user_id,
                "plan_id": plan_id,
                "tracking_date": datetime.now().isoformat(),
                "current_level": user.level,
                "current_rank": user.rank,
                "total_xp": user.xp,
                "progress_metrics": progress_metrics,
                "learning_analytics": learning_analytics,
                "milestones": milestones,
                "achievements": achievements,
                "streaks": streaks,
                "performance_trends": trends,
                "predictions": predictions,
                "gamification_status": await self._get_gamification_status(user),
                "recommendations": await self._generate_progress_recommendations(
                    progress_metrics, trends
                )
            }
            
            # Cache the progress data
            cache_key = f"comprehensive_progress:{user_id}:{plan_id or 'all'}"
            cache_service.set(cache_key, comprehensive_progress, expire=1800)  # 30 minutes
            
            return comprehensive_progress
            
        except Exception as e:
            logger.error(f"Error tracking comprehensive progress: {str(e)}")
            raise
    
    async def award_achievement(
        self,
        user_id: str,
        achievement_id: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Award an achievement to a user with full gamification effects
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            achievement = self.db.query(Achievement).filter(
                Achievement.id == achievement_id
            ).first()
            
            if not user or not achievement:
                raise ValueError("User or achievement not found")
            
            # Check if already awarded
            existing = self.db.query(UserAchievement).filter(
                UserAchievement.user_id == user_id,
                UserAchievement.achievement_id == achievement_id
            ).first()
            
            if existing:
                return {"success": False, "reason": "Already awarded"}
            
            # Award the achievement
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                earned_at=datetime.now(),
                context=context or {}
            )
            self.db.add(user_achievement)
            
            # Calculate rewards
            rewards = await self._calculate_achievement_rewards(
                achievement, user, context
            )
            
            # Apply rewards
            reward_results = await self._apply_rewards(user, rewards)
            
            # Create celebration effects
            celebration = await self._create_celebration_effects(
                achievement, rewards
            )
            
            # Send notification
            notification = await self._create_achievement_notification(
                user_id, achievement, rewards
            )
            
            # Check for rank progression
            rank_change = await self._check_rank_progression(user)
            
            # Update user stats
            user.achievements_earned = user.achievements_earned + 1 if user.achievements_earned else 1
            
            self.db.commit()
            
            return {
                "success": True,
                "achievement": {
                    "id": achievement.id,
                    "name": achievement.name,
                    "description": achievement.description,
                    "rarity": achievement.rarity,
                    "category": achievement.category
                },
                "rewards": [asdict(reward) for reward in rewards],
                "reward_results": reward_results,
                "celebration": celebration,
                "rank_change": rank_change,
                "notification_sent": notification is not None,
                "user_stats": {
                    "total_xp": user.xp,
                    "current_rank": user.rank,
                    "level": user.level,
                    "achievements_count": user.achievements_earned
                }
            }
            
        except Exception as e:
            logger.error(f"Error awarding achievement: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def process_learning_event(
        self,
        user_id: str,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a learning event and apply appropriate gamification
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Calculate XP and rewards for the event
            event_rewards = await self._calculate_event_rewards(
                event_type, event_data, user
            )
            
            # Apply immediate rewards
            immediate_results = await self._apply_rewards(user, event_rewards)
            
            # Check for triggered achievements
            triggered_achievements = await self._check_triggered_achievements(
                user_id, event_type, event_data
            )
            
            # Update streaks
            streak_updates = await self._update_streaks(user_id, event_type)
            
            # Check for milestones
            milestone_checks = await self._check_milestones_for_event(
                user_id, event_type, event_data
            )
            
            # Update progress metrics
            progress_updates = await self._update_progress_metrics(
                user_id, event_type, event_data
            )
            
            # Generate motivational feedback
            motivation = await self._generate_motivational_feedback(
                user, event_type, event_data, event_rewards
            )
            
            # Check for rank progression
            rank_change = await self._check_rank_progression(user)
            
            self.db.commit()
            
            return {
                "success": True,
                "event_type": event_type,
                "immediate_rewards": [asdict(reward) for reward in event_rewards],
                "reward_results": immediate_results,
                "triggered_achievements": triggered_achievements,
                "streak_updates": streak_updates,
                "milestone_checks": milestone_checks,
                "progress_updates": progress_updates,
                "motivational_feedback": motivation,
                "rank_change": rank_change,
                "user_stats": {
                    "total_xp": user.xp,
                    "current_rank": user.rank,
                    "level": user.level
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing learning event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_personalized_challenges(
        self,
        user_id: str,
        plan_id: str = None,
        max_challenges: int = 5
    ) -> Dict[str, Any]:
        """
        Generate personalized challenges based on user progress
        """
        try:
            # Analyze user's current progress
            progress_analysis = await self._analyze_user_progress_patterns(
                user_id, plan_id
            )
            
            # Identify improvement areas
            improvement_areas = await self._identify_improvement_areas(
                user_id, progress_analysis
            )
            
            # Generate challenges
            challenges = []
            
            # Performance-based challenges
            if progress_analysis["weak_areas"]:
                challenges.extend(
                    await self._create_performance_challenges(
                        progress_analysis["weak_areas"]
                    )
                )
            
            # Streak-based challenges
            current_streak = progress_analysis.get("current_streak", 0)
            if current_streak < 7:  # Less than a week streak
                challenges.append(
                    await self._create_streak_challenge(current_streak)
                )
            
            # Time-based challenges
            if progress_analysis["daily_study_time"] < 60:  # Less than 1 hour
                challenges.append(
                    await self._create_time_challenge(
                        progress_analysis["daily_study_time"]
                    )
                )
            
            # Mastery challenges
            if progress_analysis["mastery_level"] < 0.8:  # Less than 80% mastery
                challenges.extend(
                    await self._create_mastery_challenges(
                        progress_analysis, improvement_areas
                    )
                )
            
            # Social challenges (if applicable)
            challenges.extend(
                await self._create_social_challenges(user_id)
            )
            
            # Prioritize and limit challenges
            prioritized_challenges = await self._prioritize_challenges(
                challenges, progress_analysis
            )[:max_challenges]
            
            # Add challenge tracking
            for challenge in prioritized_challenges:
                await self._setup_challenge_tracking(user_id, challenge)
            
            return {
                "user_id": user_id,
                "plan_id": plan_id,
                "total_available_challenges": len(challenges),
                "personalized_challenges": prioritized_challenges,
                "progress_analysis": progress_analysis,
                "recommended_focus": improvement_areas[:3],  # Top 3 areas
                "challenge_difficulty_distribution": await self._analyze_challenge_difficulty(
                    prioritized_challenges
                ),
                "estimated_completion_time": await self._estimate_challenge_completion_time(
                    prioritized_challenges
                )
            }
            
        except Exception as e:
            logger.error(f"Error generating personalized challenges: {str(e)}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _calculate_all_progress_metrics(
        self, user_id: str, plan_id: str = None
    ) -> Dict[str, ProgressMetric]:
        """Calculate all progress tracking metrics"""
        
        metrics = {}
        
        # Study time metrics
        study_time_data = await self._get_study_time_data(user_id, days=30)
        metrics["daily_study_time"] = ProgressMetric(
            metric_id="daily_study_time",
            name="Daily Study Time",
            current_value=study_time_data["avg_daily_minutes"],
            target_value=60,  # Target 1 hour per day
            unit="minutes",
            progress_percentage=min(100, study_time_data["avg_daily_minutes"] / 60 * 100),
            last_updated=datetime.now(),
            trend=study_time_data["trend"]
        )
        
        # Accuracy metrics
        accuracy_data = await self._get_accuracy_data(user_id, days=30)
        metrics["accuracy"] = ProgressMetric(
            metric_id="accuracy",
            name="Overall Accuracy",
            current_value=accuracy_data["current_accuracy"],
            target_value=80,  # Target 80% accuracy
            unit="percentage",
            progress_percentage=accuracy_data["current_accuracy"],
            last_updated=datetime.now(),
            trend=accuracy_data["trend"]
        )
        
        # Streak metrics
        streak_data = await self._get_streak_data(user_id)
        metrics["study_streak"] = ProgressMetric(
            metric_id="study_streak",
            name="Study Streak",
            current_value=streak_data["current_streak"],
            target_value=30,  # Target 30 day streak
            unit="days",
            progress_percentage=min(100, streak_data["current_streak"] / 30 * 100),
            last_updated=datetime.now(),
            trend="increasing" if streak_data["current_streak"] > 0 else "stable"
        )
        
        # Unit completion metrics
        if plan_id:
            unit_data = await self._get_unit_completion_data(user_id, plan_id)
            metrics["unit_completion"] = ProgressMetric(
                metric_id="unit_completion",
                name="Unit Completion",
                current_value=unit_data["completed_units"],
                target_value=unit_data["total_units"],
                unit="units",
                progress_percentage=unit_data["completion_percentage"],
                last_updated=datetime.now(),
                trend=unit_data["trend"]
            )
        
        # Topic mastery metrics
        mastery_data = await self._get_topic_mastery_data(user_id)
        metrics["topic_mastery"] = ProgressMetric(
            metric_id="topic_mastery",
            name="Topic Mastery",
            current_value=mastery_data["mastered_topics"],
            target_value=mastery_data["total_topics"],
            unit="topics",
            progress_percentage=mastery_data["mastery_percentage"],
            last_updated=datetime.now(),
            trend=mastery_data["trend"]
        )
        
        # Convert to dict format
        return {key: asdict(metric) for key, metric in metrics.items()}
    
    async def _calculate_learning_analytics(
        self, user_id: str, plan_id: str = None
    ) -> Dict[str, Any]:
        """Calculate comprehensive learning analytics"""
        
        # Get recent battle/quiz data
        battles = self.db.query(Battle).filter(
            Battle.user_id == user_id,
            Battle.created_at >= datetime.now() - timedelta(days=30)
        ).order_by(Battle.created_at.desc()).all()
        
        if not battles:
            return {
                "total_sessions": 0,
                "avg_session_score": 0,
                "improvement_rate": 0,
                "learning_velocity": "insufficient_data"
            }
        
        # Calculate analytics
        total_sessions = len(battles)
        session_scores = []
        
        for battle in battles:
            answers = self.db.query(BattleAnswer).filter(
                BattleAnswer.battle_id == battle.id
            ).all()
            
            if answers:
                correct_answers = sum(1 for a in answers if a.is_correct)
                score = (correct_answers / len(answers)) * 100
                session_scores.append({
                    "score": score,
                    "date": battle.created_at,
                    "total_questions": len(answers)
                })
        
        if not session_scores:
            return {"error": "No session data available"}
        
        # Calculate trends
        avg_score = sum(s["score"] for s in session_scores) / len(session_scores)
        
        # Improvement rate (recent vs older)
        recent_scores = session_scores[:len(session_scores)//2]
        older_scores = session_scores[len(session_scores)//2:]
        
        if older_scores:
            recent_avg = sum(s["score"] for s in recent_scores) / len(recent_scores)
            older_avg = sum(s["score"] for s in older_scores) / len(older_scores)
            improvement_rate = ((recent_avg - older_avg) / older_avg) * 100 if older_avg > 0 else 0
        else:
            improvement_rate = 0
        
        # Learning velocity
        if improvement_rate > 15:
            velocity = "fast"
        elif improvement_rate > 5:
            velocity = "moderate"
        elif improvement_rate > -5:
            velocity = "stable"
        else:
            velocity = "declining"
        
        return {
            "total_sessions": total_sessions,
            "avg_session_score": round(avg_score, 2),
            "improvement_rate": round(improvement_rate, 2),
            "learning_velocity": velocity,
            "session_frequency": round(total_sessions / 30, 2),  # Sessions per day
            "consistency_score": await self._calculate_consistency_score(session_scores),
            "difficulty_progression": await self._analyze_difficulty_progression_analytics(
                user_id, session_scores
            )
        }
    
    async def _calculate_event_rewards(
        self, event_type: str, event_data: Dict[str, Any], user: User
    ) -> List[Reward]:
        """Calculate rewards for a learning event"""
        
        rewards = []
        
        if event_type == "question_answered":
            is_correct = event_data.get("is_correct", False)
            difficulty = event_data.get("difficulty", 1)
            
            if is_correct:
                xp_amount = self.XP_QUESTION_CORRECT + (difficulty * self.XP_QUESTION_BONUS_DIFFICULTY)
                rewards.append(Reward(
                    reward_id=f"xp-question-{datetime.now().timestamp()}",
                    type=RewardType.XP,
                    amount=xp_amount,
                    description=f"Correct answer (+{xp_amount} XP)",
                    rarity="common"
                ))
                
                # Bonus orbs for higher difficulty
                if difficulty >= 4:
                    rewards.append(Reward(
                        reward_id=f"orbs-difficulty-{datetime.now().timestamp()}",
                        type=RewardType.ORBS,
                        amount=difficulty,
                        description=f"High difficulty bonus (+{difficulty} orbs)",
                        rarity="rare"
                    ))
        
        elif event_type == "video_completed":
            duration = event_data.get("duration_minutes", 1)
            completion_rate = event_data.get("completion_percentage", 100)
            
            if completion_rate >= 80:
                xp_amount = self.XP_VIDEO_COMPLETE + max(0, duration - 5)  # Bonus for longer videos
                rewards.append(Reward(
                    reward_id=f"xp-video-{datetime.now().timestamp()}",
                    type=RewardType.XP,
                    amount=xp_amount,
                    description=f"Video completed (+{xp_amount} XP)",
                    rarity="common"
                ))
        
        elif event_type == "unit_completed":
            unit_number = event_data.get("unit_number", 1)
            score = event_data.get("final_score", 0)
            
            xp_amount = self.XP_UNIT_COMPLETE
            if score >= 90:
                xp_amount = int(xp_amount * 1.5)  # 50% bonus for excellent performance
                
            rewards.append(Reward(
                reward_id=f"xp-unit-{unit_number}-{datetime.now().timestamp()}",
                type=RewardType.XP,
                amount=xp_amount,
                description=f"Unit {unit_number} completed (+{xp_amount} XP)",
                rarity="uncommon"
            ))
            
            # Crystal reward for completing unit
            rewards.append(Reward(
                reward_id=f"crystals-unit-{unit_number}-{datetime.now().timestamp()}",
                type=RewardType.CRYSTALS,
                amount=1,
                description="Unit completion crystal",
                rarity="rare"
            ))
        
        elif event_type == "streak_milestone":
            days = event_data.get("streak_days", 1)
            xp_amount = self.XP_STREAK_DAILY * days
            
            rewards.append(Reward(
                reward_id=f"xp-streak-{days}-{datetime.now().timestamp()}",
                type=RewardType.XP,
                amount=xp_amount,
                description=f"{days} day streak bonus (+{xp_amount} XP)",
                rarity="rare"
            ))
            
            # Special rewards for major milestones
            if days in [7, 30, 100]:
                rewards.append(Reward(
                    reward_id=f"badge-streak-{days}-{datetime.now().timestamp()}",
                    type=RewardType.BADGE,
                    amount=1,
                    description=f"{days} Day Streak Badge",
                    rarity="epic" if days >= 30 else "rare"
                ))
        
        return rewards
    
    async def _apply_rewards(self, user: User, rewards: List[Reward]) -> Dict[str, Any]:
        """Apply rewards to user account"""
        
        results = {
            "xp_gained": 0,
            "orbs_gained": 0,
            "crystals_gained": 0,
            "badges_earned": [],
            "unlocks": []
        }
        
        for reward in rewards:
            if reward.type == RewardType.XP:
                user.xp = (user.xp or 0) + reward.amount
                results["xp_gained"] += reward.amount
                
            elif reward.type == RewardType.ORBS:
                user.orbs = (user.orbs or 0) + reward.amount
                results["orbs_gained"] += reward.amount
                
            elif reward.type == RewardType.CRYSTALS:
                user.crystals = (user.crystals or 0) + reward.amount
                results["crystals_gained"] += reward.amount
                
            elif reward.type == RewardType.BADGE:
                results["badges_earned"].append(reward.description)
                
            elif reward.type == RewardType.UNLOCK:
                results["unlocks"].append(reward.unlocked_content)
        
        # Update user level based on XP
        if results["xp_gained"] > 0:
            user.level = self._calculate_level_from_xp(user.xp)
        
        return results
    
    def _calculate_level_from_xp(self, total_xp: int) -> int:
        """Calculate user level from total XP"""
        # Level formula: level = floor(sqrt(xp / 100))
        return max(1, int(math.sqrt(max(0, total_xp) / 100)))
    
    async def _check_rank_progression(self, user: User) -> Optional[Dict[str, Any]]:
        """Check if user has progressed to a new rank"""
        
        current_rank = user.rank or 'E'
        new_rank = None
        
        for rank, threshold in sorted(self.RANK_THRESHOLDS.items(), key=lambda x: x[1]):
            if user.xp >= threshold:
                new_rank = rank
        
        if new_rank and new_rank != current_rank:
            old_rank = current_rank
            user.rank = new_rank
            
            return {
                "rank_changed": True,
                "old_rank": old_rank,
                "new_rank": new_rank,
                "xp_threshold": self.RANK_THRESHOLDS[new_rank],
                "celebration_message": f"Congratulations! You've reached {new_rank} Rank!",
                "rank_rewards": await self._get_rank_progression_rewards(new_rank)
            }
        
        return None