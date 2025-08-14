from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..models.achievement import Achievement, UserAchievement
from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.diagnostic_test import DiagnosticTest
from ..schemas.achievement import AchievementProgressUpdate, UserAchievementSummary, AchievementShowcase

class AchievementService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_achievements(self, include_secret: bool = False) -> List[Achievement]:
        """Get all available achievements"""
        query = self.db.query(Achievement).filter(Achievement.is_active == True)
        if not include_secret:
            query = query.filter(Achievement.is_secret == False)
        return query.all()
    
    def get_user_achievements(self, user_id: str, include_secret: bool = True) -> List[UserAchievement]:
        """Get user's achievements"""
        query = self.db.query(UserAchievement).filter(UserAchievement.user_id == user_id)
        if not include_secret:
            query = query.join(Achievement).filter(Achievement.is_secret == False)
        return query.all()
    
    def get_user_achievement(self, user_id: str, achievement_id: str) -> Optional[UserAchievement]:
        """Get specific user achievement"""
        return self.db.query(UserAchievement).filter(
            UserAchievement.user_id == user_id,
            UserAchievement.achievement_id == achievement_id
        ).first()
    
    def create_user_achievement(self, user_id: str, achievement_id: str) -> UserAchievement:
        """Create or get user achievement record"""
        user_achievement = self.get_user_achievement(user_id, achievement_id)
        if not user_achievement:
            user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                progress=0,
                is_unlocked=False
            )
            self.db.add(user_achievement)
            self.db.commit()
            self.db.refresh(user_achievement)
        return user_achievement
    
    def update_achievement_progress(self, user_id: str, achievement_id: str, progress_increment: int = 1, metadata: Dict[str, Any] = None) -> UserAchievement:
        """Update achievement progress and check for unlock"""
        user_achievement = self.create_user_achievement(user_id, achievement_id)
        achievement = self.db.query(Achievement).filter(Achievement.id == achievement_id).first()
        
        if not achievement or not achievement.is_active:
            return user_achievement
        
        # Update progress
        user_achievement.progress += progress_increment
        
        # Update progress data with metadata
        if metadata:
            current_data = user_achievement.get_progress_data()
            current_data.update(metadata)
            user_achievement.progress_data = current_data
        
        # Check if achievement should be unlocked
        requirements = achievement.get_requirements()
        if requirements:
            target = next(iter(requirements.values()), 1)
            if user_achievement.progress >= target and not user_achievement.is_unlocked:
                user_achievement.is_unlocked = True
                user_achievement.unlocked_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user_achievement)
        return user_achievement
    
    def check_unit_completion_achievements(self, user_id: str, unit_number: int, subject_id: str) -> List[UserAchievement]:
        """Check and update unit completion achievements"""
        unlocked_achievements = []
        
        # Get user's completed units count
        completed_units = self.db.query(PlanProgress).filter(
            PlanProgress.plan_id.in_(
                self.db.query(StudyPlan.id).filter(StudyPlan.user_id == user_id)
            ),
            PlanProgress.is_completed == True
        ).count()
        
        # Update unit completion achievements
        unit_achievements = self.db.query(Achievement).filter(
            Achievement.category == "unit_completion",
            Achievement.is_active == True
        ).all()
        
        for achievement in unit_achievements:
            requirements = achievement.get_requirements()
            if "units_completed" in requirements:
                target = requirements["units_completed"]
                user_achievement = self.update_achievement_progress(
                    user_id, 
                    str(achievement.id), 
                    completed_units,
                    {"last_completed_unit": unit_number, "subject_id": subject_id}
                )
                if user_achievement.is_unlocked and user_achievement.unlocked_at:
                    unlocked_achievements.append(user_achievement)
        
        return unlocked_achievements
    
    def check_score_improvement_achievements(self, user_id: str, new_score: float, previous_score: float = None) -> List[UserAchievement]:
        """Check and update score improvement achievements"""
        unlocked_achievements = []
        
        # Get user's recent diagnostic tests
        recent_tests = self.db.query(DiagnosticTest).filter(
            DiagnosticTest.user_id == user_id,
            DiagnosticTest.completed_at.isnot(None)
        ).order_by(DiagnosticTest.completed_at.desc()).limit(5).all()
        
        if len(recent_tests) < 2:
            return unlocked_achievements
        
        # Calculate consecutive improvements
        consecutive_improvements = 0
        total_improvement = 0
        
        for i in range(len(recent_tests) - 1):
            current_score = recent_tests[i].score_percentage or 0
            previous_score = recent_tests[i + 1].score_percentage or 0
            
            if current_score > previous_score:
                consecutive_improvements += 1
                total_improvement += (current_score - previous_score)
            else:
                consecutive_improvements = 0
        
        # Update score improvement achievements
        score_achievements = self.db.query(Achievement).filter(
            Achievement.category == "score_improvement",
            Achievement.is_active == True
        ).all()
        
        for achievement in score_achievements:
            requirements = achievement.get_requirements()
            user_achievement = self.create_user_achievement(user_id, str(achievement.id))
            
            if "consecutive_improvements" in requirements:
                target = requirements["consecutive_improvements"]
                user_achievement.progress = consecutive_improvements
                if consecutive_improvements >= target and not user_achievement.is_unlocked:
                    user_achievement.is_unlocked = True
                    user_achievement.unlocked_at = datetime.utcnow()
                    unlocked_achievements.append(user_achievement)
            
            elif "score_improvement" in requirements:
                target = requirements["score_improvement"]
                user_achievement.progress = int(total_improvement)
                if total_improvement >= target and not user_achievement.is_unlocked:
                    user_achievement.is_unlocked = True
                    user_achievement.unlocked_at = datetime.utcnow()
                    unlocked_achievements.append(user_achievement)
            
            elif "high_scores_consecutive" in requirements:
                target = requirements["high_scores_consecutive"]
                min_score = requirements.get("min_score", 80)
                high_scores_count = sum(1 for test in recent_tests if (test.score_percentage or 0) >= min_score)
                user_achievement.progress = high_scores_count
                if high_scores_count >= target and not user_achievement.is_unlocked:
                    user_achievement.is_unlocked = True
                    user_achievement.unlocked_at = datetime.utcnow()
                    unlocked_achievements.append(user_achievement)
            
            self.db.commit()
        
        return unlocked_achievements
    
    def check_study_streak_achievements(self, user_id: str, streak_days: int) -> List[UserAchievement]:
        """Check and update study streak achievements"""
        unlocked_achievements = []
        
        # Update streak achievements
        streak_achievements = self.db.query(Achievement).filter(
            Achievement.category == "study_streak",
            Achievement.is_active == True
        ).all()
        
        for achievement in streak_achievements:
            requirements = achievement.get_requirements()
            if "streak_days" in requirements:
                target = requirements["streak_days"]
                user_achievement = self.update_achievement_progress(
                    user_id, 
                    str(achievement.id), 
                    streak_days,
                    {"current_streak": streak_days}
                )
                if user_achievement.is_unlocked and user_achievement.unlocked_at:
                    unlocked_achievements.append(user_achievement)
        
        return unlocked_achievements
    
    def check_secret_achievements(self, user_id: str, action_type: str, action_data: Dict[str, Any]) -> List[UserAchievement]:
        """Check and update secret achievements based on user actions"""
        unlocked_achievements = []
        
        # Get secret achievements
        secret_achievements = self.db.query(Achievement).filter(
            Achievement.category == "secret",
            Achievement.is_active == True,
            Achievement.is_secret == True
        ).all()
        
        for achievement in secret_achievements:
            requirements = achievement.get_requirements()
            user_achievement = self.create_user_achievement(user_id, str(achievement.id))
            
            # Check different secret achievement types
            if "perfect_score" in requirements and action_type == "unit_completion":
                score = action_data.get("score", 0)
                if score == 100:
                    user_achievement.progress = 1
                    if not user_achievement.is_unlocked:
                        user_achievement.is_unlocked = True
                        user_achievement.unlocked_at = datetime.utcnow()
                        unlocked_achievements.append(user_achievement)
            
            elif "speed_challenge" in requirements and action_type == "quiz_completion":
                time_taken = action_data.get("time_taken", 0)
                correct_answers = action_data.get("correct_answers", 0)
                if time_taken <= 120 and correct_answers >= 10:  # 2 minutes, 10 correct
                    user_achievement.progress = 1
                    if not user_achievement.is_unlocked:
                        user_achievement.is_unlocked = True
                        user_achievement.unlocked_at = datetime.utcnow()
                        unlocked_achievements.append(user_achievement)
            
            elif "perfect_battles" in requirements and action_type == "battle_completion":
                damage_taken = action_data.get("damage_taken", 0)
                if damage_taken == 0:
                    user_achievement.progress += 1
                    target = requirements["perfect_battles"]
                    if user_achievement.progress >= target and not user_achievement.is_unlocked:
                        user_achievement.is_unlocked = True
                        user_achievement.unlocked_at = datetime.utcnow()
                        unlocked_achievements.append(user_achievement)
            
            self.db.commit()
        
        return unlocked_achievements
    
    def get_user_achievement_summary(self, user_id: str) -> UserAchievementSummary:
        """Get comprehensive achievement summary for user"""
        user_achievements = self.get_user_achievements(user_id)
        
        total_achievements = len(user_achievements)
        unlocked_achievements = sum(1 for ua in user_achievements if ua.is_unlocked)
        total_points = sum(ua.achievement.points for ua in user_achievements if ua.is_unlocked)
        secret_achievements_found = sum(1 for ua in user_achievements if ua.is_unlocked and ua.achievement.is_secret)
        
        # Group by category
        achievements_by_category = {}
        for ua in user_achievements:
            if ua.is_unlocked:
                category = ua.achievement.category
                achievements_by_category[category] = achievements_by_category.get(category, 0) + 1
        
        # Get recent achievements (last 5)
        recent_achievements = sorted(
            [ua for ua in user_achievements if ua.is_unlocked and ua.unlocked_at],
            key=lambda x: x.unlocked_at,
            reverse=True
        )[:5]
        
        return UserAchievementSummary(
            total_achievements=total_achievements,
            unlocked_achievements=unlocked_achievements,
            total_points=total_points,
            secret_achievements_found=secret_achievements_found,
            achievements_by_category=achievements_by_category,
            recent_achievements=recent_achievements
        )
    
    def get_achievement_showcase(self, user_id: str) -> AchievementShowcase:
        """Get achievement showcase for profile display"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        user_achievements = self.get_user_achievements(user_id)
        unlocked_achievements = [ua for ua in user_achievements if ua.is_unlocked]
        
        total_points = sum(ua.achievement.points for ua in unlocked_achievements)
        
        # Find rarest achievement
        rarest_achievement = None
        rarity_order = ["legendary", "epic", "rare", "common"]
        for rarity in rarity_order:
            for ua in unlocked_achievements:
                if ua.achievement.rarity == rarity:
                    rarest_achievement = ua
                    break
            if rarest_achievement:
                break
        
        # Get recent achievements
        recent_achievements = sorted(
            unlocked_achievements,
            key=lambda x: x.unlocked_at,
            reverse=True
        )[:3]
        
        # Count by rarity
        achievements_by_rarity = {}
        for ua in unlocked_achievements:
            rarity = ua.achievement.rarity
            achievements_by_rarity[rarity] = achievements_by_rarity.get(rarity, 0) + 1
        
        return AchievementShowcase(
            user_id=str(user.id),
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            total_points=total_points,
            unlocked_achievements=len(unlocked_achievements),
            rarest_achievement=rarest_achievement,
            recent_achievements=recent_achievements,
            achievements_by_rarity=achievements_by_rarity
        ) 