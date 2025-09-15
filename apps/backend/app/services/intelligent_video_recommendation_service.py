"""
Intelligent Video Recommendation Engine
Advanced recommendation system based on student learning patterns, weaknesses, and progress
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Set
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, desc, func
from datetime import datetime, timedelta
import json
import math
from dataclasses import dataclass
from enum import Enum

from .video_question_matching_service import VideoQuestionMatchingService, StudentWeakness
from ..models.youtube_catalog import YoutubeCatalog
from ..models.question_video_recommendations import QuestionVideoRecommendations
from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.video_tracking import VideoTracking
from ..models.quiz import QuizAnswer

logger = logging.getLogger(__name__)

class RecommendationContext(Enum):
    """Context for video recommendations"""
    STUDY_PLAN = "study_plan"
    WEAKNESS_REMEDIATION = "weakness_remediation"
    SKILL_BUILDING = "skill_building"
    REVIEW = "review"
    EXPLORATION = "exploration"

@dataclass
class StudentProfile:
    """Comprehensive student learning profile"""
    user_id: str
    learning_style: str
    performance_level: float
    weak_topics: List[str]
    strong_topics: List[str]
    preferred_video_duration: int
    attention_span: int
    learning_pace: str
    last_activity: datetime

@dataclass
class VideoRecommendation:
    """Enhanced video recommendation with context and reasoning"""
    video_id: int
    video: YoutubeCatalog
    relevance_score: float
    context: RecommendationContext
    reasoning: str
    learning_objective: str
    estimated_impact: float
    difficulty_match: float
    engagement_prediction: float
    prerequisite_topics: List[str]
    follow_up_videos: List[int]

class IntelligentVideoRecommendationService:
    """
    Advanced video recommendation engine that considers:
    - Student learning patterns and preferences
    - Failed question analysis and error patterns
    - Study plan progress and goals
    - Video engagement and effectiveness metrics
    - Learning psychology principles
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.matching_service = VideoQuestionMatchingService(db)
        
        # Learning psychology weights
        self.psychology_weights = {
            'spaced_repetition': 0.2,
            'difficulty_progression': 0.25,
            'interest_maintenance': 0.15,
            'concept_reinforcement': 0.2,
            'skill_transfer': 0.2
        }
    
    async def build_student_profile(self, user_id: str) -> StudentProfile:
        """
        Build comprehensive student learning profile
        
        Args:
            user_id: Student ID
            
        Returns:
            Complete student profile for personalized recommendations
        """
        try:
            # Get user basic info
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Analyze performance patterns
            performance_data = await self._analyze_performance_patterns(user_id)
            
            # Analyze topic strengths and weaknesses
            topic_analysis = await self._analyze_topic_performance(user_id)
            
            # Analyze video viewing patterns
            viewing_patterns = await self._analyze_viewing_patterns(user_id)
            
            # Determine learning style from behavior
            learning_style = await self._infer_learning_style(user_id)
            
            profile = StudentProfile(
                user_id=user_id,
                learning_style=learning_style,
                performance_level=performance_data['overall_score'],
                weak_topics=topic_analysis['weak_topics'],
                strong_topics=topic_analysis['strong_topics'],
                preferred_video_duration=viewing_patterns['preferred_duration'],
                attention_span=viewing_patterns['attention_span'],
                learning_pace=performance_data['pace'],
                last_activity=performance_data['last_activity']
            )
            
            return profile
            
        except Exception as e:
            logger.error(f"Error building student profile: {e}")
            # Return default profile
            return StudentProfile(
                user_id=user_id,
                learning_style="mixed",
                performance_level=0.5,
                weak_topics=[],
                strong_topics=[],
                preferred_video_duration=600,
                attention_span=300,
                learning_pace="normal",
                last_activity=datetime.utcnow()
            )
    
    async def _analyze_performance_patterns(self, user_id: str) -> Dict:
        """Analyze student's overall performance patterns"""
        try:
            query = text("""
                SELECT 
                    AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as avg_score,
                    COUNT(*) as total_questions,
                    MAX(answered_at) as last_activity,
                    STDDEV(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as score_variance,
                    COUNT(DISTINCT DATE(answered_at)) as active_days
                FROM quiz_answers 
                WHERE user_id = :user_id 
                    AND answered_at >= NOW() - INTERVAL '30 days'
            """)
            
            result = self.db.execute(query, {'user_id': user_id}).first()
            
            # Determine learning pace based on activity patterns
            pace = "slow"
            if result.active_days > 20:
                pace = "fast"
            elif result.active_days > 10:
                pace = "normal"
            
            return {
                'overall_score': float(result.avg_score or 0.5),
                'total_questions': result.total_questions or 0,
                'last_activity': result.last_activity or datetime.utcnow(),
                'consistency': 1.0 - (result.score_variance or 0.5),
                'pace': pace
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance patterns: {e}")
            return {
                'overall_score': 0.5,
                'total_questions': 0,
                'last_activity': datetime.utcnow(),
                'consistency': 0.5,
                'pace': 'normal'
            }
    
    async def _analyze_topic_performance(self, user_id: str) -> Dict:
        """Analyze performance by topic to identify strengths and weaknesses"""
        try:
            query = text("""
                SELECT 
                    q.topic_id,
                    t.name as topic_name,
                    AVG(CASE WHEN qa.is_correct THEN 1.0 ELSE 0.0 END) as success_rate,
                    COUNT(*) as attempts
                FROM quiz_answers qa
                JOIN questions q ON qa.question_id = q.id
                LEFT JOIN topics t ON q.topic_id = t.id
                WHERE qa.user_id = :user_id 
                    AND qa.answered_at >= NOW() - INTERVAL '30 days'
                GROUP BY q.topic_id, t.name
                HAVING COUNT(*) >= 3
                ORDER BY success_rate ASC
            """)
            
            result = self.db.execute(query, {'user_id': user_id})
            
            weak_topics = []
            strong_topics = []
            
            for row in result:
                topic_name = row.topic_name or f"Topic_{row.topic_id}"
                
                if row.success_rate < 0.6:
                    weak_topics.append(topic_name)
                elif row.success_rate > 0.8:
                    strong_topics.append(topic_name)
            
            return {
                'weak_topics': weak_topics[:10],  # Top 10 weaknesses
                'strong_topics': strong_topics[:5]  # Top 5 strengths
            }
            
        except Exception as e:
            logger.error(f"Error analyzing topic performance: {e}")
            return {'weak_topics': [], 'strong_topics': []}
    
    async def _analyze_viewing_patterns(self, user_id: str) -> Dict:
        """Analyze video viewing patterns to understand preferences"""
        try:
            query = text("""
                SELECT 
                    AVG(video_duration_seconds) as avg_duration,
                    AVG(watched_seconds) as avg_watched,
                    AVG(watch_percentage) as avg_completion,
                    COUNT(*) as total_videos,
                    STDDEV(video_duration_seconds) as duration_variance
                FROM video_tracking 
                WHERE user_id = :user_id 
                    AND created_at >= NOW() - INTERVAL '30 days'
            """)
            
            result = self.db.execute(query, {'user_id': user_id}).first()
            
            if not result or result.total_videos == 0:
                return {
                    'preferred_duration': 600,  # 10 minutes default
                    'attention_span': 300,      # 5 minutes default
                    'engagement_level': 0.5
                }
            
            # Calculate attention span based on completion rates
            attention_span = int(result.avg_watched or 300)
            preferred_duration = int(result.avg_duration or 600)
            
            # Adjust based on completion rates
            if result.avg_completion > 0.8:
                attention_span = min(preferred_duration, attention_span + 120)
            elif result.avg_completion < 0.4:
                attention_span = max(180, attention_span - 60)
            
            return {
                'preferred_duration': preferred_duration,
                'attention_span': attention_span,
                'engagement_level': float(result.avg_completion or 0.5)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing viewing patterns: {e}")
            return {
                'preferred_duration': 600,
                'attention_span': 300,
                'engagement_level': 0.5
            }
    
    async def _infer_learning_style(self, user_id: str) -> str:
        """Infer learning style based on behavior patterns"""
        try:
            # Analyze video completion rates by video type/characteristics
            query = text("""
                SELECT 
                    yc.codigo_tema,
                    yc.nivel,
                    AVG(vt.watch_percentage) as completion_rate,
                    COUNT(*) as video_count
                FROM video_tracking vt
                JOIN youtube_catalog yc ON vt.youtube_url = yc.url
                WHERE vt.user_id = :user_id
                    AND vt.created_at >= NOW() - INTERVAL '30 days'
                GROUP BY yc.codigo_tema, yc.nivel
                HAVING COUNT(*) >= 2
            """)
            
            result = self.db.execute(query, {'user_id': user_id})
            
            basic_completion = 0
            advanced_completion = 0
            total_videos = 0
            
            for row in result:
                if row.nivel and 'básico' in row.nivel.lower():
                    basic_completion += row.completion_rate * row.video_count
                elif row.nivel and 'avanzado' in row.nivel.lower():
                    advanced_completion += row.completion_rate * row.video_count
                total_videos += row.video_count
            
            if total_videos == 0:
                return "mixed"
            
            # Determine style based on completion patterns
            if basic_completion / total_videos > 0.7:
                return "step_by_step"
            elif advanced_completion / total_videos > 0.6:
                return "conceptual"
            else:
                return "mixed"
                
        except Exception as e:
            logger.error(f"Error inferring learning style: {e}")
            return "mixed"
    
    async def generate_contextual_recommendations(
        self,
        user_id: str,
        context: RecommendationContext,
        limit: int = 10,
        context_data: Optional[Dict] = None
    ) -> List[VideoRecommendation]:
        """
        Generate contextual video recommendations based on specific learning context
        
        Args:
            user_id: Student ID
            context: Recommendation context (study plan, weakness remediation, etc.)
            limit: Maximum recommendations to return
            context_data: Additional context-specific data
            
        Returns:
            List of contextual video recommendations
        """
        try:
            profile = await self.build_student_profile(user_id)
            
            if context == RecommendationContext.WEAKNESS_REMEDIATION:
                return await self._generate_weakness_remediation_videos(profile, limit, context_data)
            elif context == RecommendationContext.STUDY_PLAN:
                return await self._generate_study_plan_videos(profile, limit, context_data)
            elif context == RecommendationContext.SKILL_BUILDING:
                return await self._generate_skill_building_videos(profile, limit, context_data)
            elif context == RecommendationContext.REVIEW:
                return await self._generate_review_videos(profile, limit, context_data)
            else:  # EXPLORATION
                return await self._generate_exploration_videos(profile, limit, context_data)
                
        except Exception as e:
            logger.error(f"Error generating contextual recommendations: {e}")
            return []
    
    async def _generate_weakness_remediation_videos(
        self,
        profile: StudentProfile,
        limit: int,
        context_data: Optional[Dict]
    ) -> List[VideoRecommendation]:
        """Generate videos specifically for addressing student weaknesses"""
        
        recommendations = []
        
        try:
            # Get student's recent weaknesses
            weaknesses = await self.matching_service.analyze_student_weaknesses(profile.user_id)
            
            for weakness in weaknesses[:limit]:
                # Find best video for this weakness
                matching_videos = await self.matching_service.find_matching_videos(weakness, 3)
                
                for video, score in matching_videos:
                    # Calculate engagement prediction
                    engagement_pred = self._predict_engagement(video, profile)
                    
                    # Create recommendation
                    reasoning = f"Addresses {weakness.error_pattern} pattern in {weakness.question_id}"
                    
                    rec = VideoRecommendation(
                        video_id=video.id,
                        video=video,
                        relevance_score=score.total_score,
                        context=RecommendationContext.WEAKNESS_REMEDIATION,
                        reasoning=reasoning,
                        learning_objective=f"Fix {weakness.error_pattern}",
                        estimated_impact=score.total_score * 0.8,
                        difficulty_match=score.difficulty_proximity,
                        engagement_prediction=engagement_pred,
                        prerequisite_topics=[],
                        follow_up_videos=[]
                    )
                    
                    recommendations.append(rec)
                    
                    if len(recommendations) >= limit:
                        break
                
                if len(recommendations) >= limit:
                    break
            
            # Sort by combined score
            recommendations.sort(
                key=lambda x: x.relevance_score * 0.6 + x.engagement_prediction * 0.4,
                reverse=True
            )
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating weakness remediation videos: {e}")
            return []
    
    async def _generate_study_plan_videos(
        self,
        profile: StudentProfile,
        limit: int,
        context_data: Optional[Dict]
    ) -> List[VideoRecommendation]:
        """Generate videos aligned with current study plan progress"""
        
        recommendations = []
        
        try:
            plan_id = context_data.get('plan_id') if context_data else None
            unit_number = context_data.get('unit_number') if context_data else None
            
            if not plan_id:
                # Get active study plan
                plan = self.db.query(StudyPlan).filter(
                    and_(
                        StudyPlan.user_id == profile.user_id,
                        StudyPlan.is_active == True
                    )
                ).first()
                
                if not plan:
                    return []
                
                plan_id = plan.id
            
            # Get current unit progress
            if unit_number is None:
                progress = self.db.query(PlanProgress).filter(
                    and_(
                        PlanProgress.plan_id == plan_id,
                        PlanProgress.is_completed == False
                    )
                ).order_by(PlanProgress.unit_number).first()
                
                if progress:
                    unit_number = progress.unit_number
                else:
                    unit_number = 1
            
            # Get unit content and focus topics
            unit_progress = self.db.query(PlanProgress).filter(
                and_(
                    PlanProgress.plan_id == plan_id,
                    PlanProgress.unit_number == unit_number
                )
            ).first()
            
            if not unit_progress:
                return []
            
            # Extract topics from unit content
            unit_content = unit_progress.unit_content or {}
            focus_topics = unit_content.get('focus_topics', [])
            
            # Find videos for these topics
            for topic in focus_topics[:5]:  # Top 5 topics
                videos = self.db.query(YoutubeCatalog).filter(
                    and_(
                        YoutubeCatalog.is_processed == True,
                        or_(
                            YoutubeCatalog.tema_principal.ilike(f'%{topic}%'),
                            YoutubeCatalog.description.ilike(f'%{topic}%')
                        )
                    )
                ).order_by(YoutubeCatalog.educational_rating.desc()).limit(3).all()
                
                for video in videos:
                    engagement_pred = self._predict_engagement(video, profile)
                    difficulty_match = self._calculate_difficulty_match(video, profile)
                    
                    rec = VideoRecommendation(
                        video_id=video.id,
                        video=video,
                        relevance_score=0.8,  # High relevance for study plan content
                        context=RecommendationContext.STUDY_PLAN,
                        reasoning=f"Part of Unit {unit_number}: {unit_progress.unit_name}",
                        learning_objective=f"Master {topic}",
                        estimated_impact=0.7,
                        difficulty_match=difficulty_match,
                        engagement_prediction=engagement_pred,
                        prerequisite_topics=[],
                        follow_up_videos=[]
                    )
                    
                    recommendations.append(rec)
            
            # Sort by engagement and difficulty match
            recommendations.sort(
                key=lambda x: x.engagement_prediction * 0.5 + x.difficulty_match * 0.5,
                reverse=True
            )
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating study plan videos: {e}")
            return []
    
    async def _generate_skill_building_videos(
        self,
        profile: StudentProfile,
        limit: int,
        context_data: Optional[Dict]
    ) -> List[VideoRecommendation]:
        """Generate videos for progressive skill building"""
        
        recommendations = []
        
        try:
            # Find videos that build upon strong topics
            for strong_topic in profile.strong_topics[:3]:
                # Look for intermediate/advanced videos in this topic
                videos = self.db.query(YoutubeCatalog).filter(
                    and_(
                        YoutubeCatalog.is_processed == True,
                        YoutubeCatalog.tema_principal.ilike(f'%{strong_topic}%'),
                        or_(
                            YoutubeCatalog.nivel.ilike('%intermedio%'),
                            YoutubeCatalog.nivel.ilike('%avanzado%')
                        )
                    )
                ).order_by(YoutubeCatalog.educational_rating.desc()).limit(3).all()
                
                for video in videos:
                    engagement_pred = self._predict_engagement(video, profile)
                    
                    rec = VideoRecommendation(
                        video_id=video.id,
                        video=video,
                        relevance_score=0.7,
                        context=RecommendationContext.SKILL_BUILDING,
                        reasoning=f"Build advanced skills in {strong_topic}",
                        learning_objective=f"Advanced {strong_topic}",
                        estimated_impact=0.6,
                        difficulty_match=0.8,  # Slightly challenging
                        engagement_prediction=engagement_pred,
                        prerequisite_topics=[strong_topic],
                        follow_up_videos=[]
                    )
                    
                    recommendations.append(rec)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating skill building videos: {e}")
            return []
    
    async def _generate_review_videos(
        self,
        profile: StudentProfile,
        limit: int,
        context_data: Optional[Dict]
    ) -> List[VideoRecommendation]:
        """Generate videos for reviewing previously learned content"""
        
        recommendations = []
        
        try:
            # Find videos for concepts student has seen before
            query = text("""
                SELECT DISTINCT yc.*
                FROM video_tracking vt
                JOIN youtube_catalog yc ON vt.youtube_url = yc.url
                WHERE vt.user_id = :user_id
                    AND vt.is_completed = true
                    AND vt.last_watched_at < NOW() - INTERVAL '7 days'
                ORDER BY vt.last_watched_at ASC
                LIMIT :limit
            """)
            
            result = self.db.execute(query, {
                'user_id': profile.user_id,
                'limit': limit * 2
            })
            
            for row in result:
                video = self.db.query(YoutubeCatalog).filter(
                    YoutubeCatalog.id == row.id
                ).first()
                
                if video:
                    rec = VideoRecommendation(
                        video_id=video.id,
                        video=video,
                        relevance_score=0.6,
                        context=RecommendationContext.REVIEW,
                        reasoning="Spaced repetition review",
                        learning_objective="Reinforce knowledge",
                        estimated_impact=0.4,
                        difficulty_match=0.9,  # Should be easier now
                        engagement_prediction=0.6,
                        prerequisite_topics=[],
                        follow_up_videos=[]
                    )
                    
                    recommendations.append(rec)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating review videos: {e}")
            return []
    
    async def _generate_exploration_videos(
        self,
        profile: StudentProfile,
        limit: int,
        context_data: Optional[Dict]
    ) -> List[VideoRecommendation]:
        """Generate videos for exploring new topics and maintaining interest"""
        
        recommendations = []
        
        try:
            # Find high-quality videos in areas not yet explored
            videos = self.db.query(YoutubeCatalog).filter(
                and_(
                    YoutubeCatalog.is_processed == True,
                    YoutubeCatalog.educational_rating >= 4.0
                )
            ).order_by(func.random()).limit(limit * 2).all()
            
            for video in videos:
                engagement_pred = self._predict_engagement(video, profile)
                
                if engagement_pred > 0.5:  # Only include engaging content
                    rec = VideoRecommendation(
                        video_id=video.id,
                        video=video,
                        relevance_score=0.5,
                        context=RecommendationContext.EXPLORATION,
                        reasoning="Exploration and interest maintenance",
                        learning_objective="Discover new concepts",
                        estimated_impact=0.3,
                        difficulty_match=0.6,
                        engagement_prediction=engagement_pred,
                        prerequisite_topics=[],
                        follow_up_videos=[]
                    )
                    
                    recommendations.append(rec)
            
            # Sort by engagement prediction
            recommendations.sort(key=lambda x: x.engagement_prediction, reverse=True)
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error generating exploration videos: {e}")
            return []
    
    def _predict_engagement(self, video: YoutubeCatalog, profile: StudentProfile) -> float:
        """Predict how engaging a video will be for the student"""
        
        try:
            engagement_score = 0.0
            
            # Duration preference match
            duration_diff = abs((video.duration_seconds or 600) - profile.preferred_video_duration)
            if duration_diff <= 120:  # Within 2 minutes
                engagement_score += 0.3
            elif duration_diff <= 300:  # Within 5 minutes
                engagement_score += 0.2
            
            # Channel familiarity (if they've watched videos from this channel)
            if video.channel_name:
                familiar_channel = self.db.query(VideoTracking).filter(
                    and_(
                        VideoTracking.user_id == profile.user_id,
                        VideoTracking.video_title.ilike(f'%{video.channel_name}%')
                    )
                ).first()
                
                if familiar_channel:
                    engagement_score += 0.2
            
            # Quality indicators
            if video.educational_rating:
                engagement_score += (video.educational_rating / 5.0) * 0.3
            
            # Popularity indicators
            if video.view_count and video.view_count > 1000:
                engagement_score += min(0.2, math.log10(video.view_count) / 50)
            
            return min(1.0, engagement_score)
            
        except Exception:
            return 0.5
    
    def _calculate_difficulty_match(self, video: YoutubeCatalog, profile: StudentProfile) -> float:
        """Calculate how well video difficulty matches student's level"""
        
        try:
            video_difficulty = self._map_video_difficulty(video.nivel)
            
            # Adjust target difficulty based on context
            target_difficulty = profile.performance_level
            
            diff = abs(video_difficulty - target_difficulty)
            
            if diff <= 0.1:
                return 1.0
            elif diff <= 0.2:
                return 0.8
            elif diff <= 0.3:
                return 0.6
            else:
                return max(0.2, 1.0 - diff)
                
        except Exception:
            return 0.5
    
    def _map_video_difficulty(self, nivel: Optional[str]) -> float:
        """Map video difficulty to numeric scale"""
        if not nivel:
            return 0.5
        
        nivel_lower = nivel.lower()
        if 'básico' in nivel_lower:
            return 0.3
        elif 'intermedio' in nivel_lower:
            return 0.6
        elif 'avanzado' in nivel_lower:
            return 0.9
        else:
            return 0.5
    
    async def create_learning_playlist(
        self,
        user_id: str,
        learning_goal: str,
        session_duration: int = 30,  # minutes
        difficulty_progression: bool = True
    ) -> List[VideoRecommendation]:
        """
        Create a structured learning playlist for a specific goal
        
        Args:
            user_id: Student ID
            learning_goal: Specific learning objective
            session_duration: Available time in minutes
            difficulty_progression: Whether to include progressive difficulty
            
        Returns:
            Ordered playlist of video recommendations
        """
        
        try:
            profile = await self.build_student_profile(user_id)
            
            # Calculate available time in seconds
            available_time = session_duration * 60
            
            # Generate diverse recommendations
            playlist = []
            used_time = 0
            
            # 1. Start with weakness remediation (40% of time)
            weakness_time = available_time * 0.4
            weakness_videos = await self._generate_weakness_remediation_videos(
                profile, 5, None
            )
            
            for video in weakness_videos:
                video_duration = video.video.duration_seconds or 600
                if used_time + video_duration <= weakness_time:
                    playlist.append(video)
                    used_time += video_duration
            
            # 2. Add study plan content (40% of time)
            study_plan_time = available_time * 0.4
            study_plan_videos = await self._generate_study_plan_videos(
                profile, 5, None
            )
            
            start_time = used_time
            for video in study_plan_videos:
                video_duration = video.video.duration_seconds or 600
                if used_time + video_duration <= start_time + study_plan_time:
                    playlist.append(video)
                    used_time += video_duration
            
            # 3. Add skill building or exploration (20% of time)
            remaining_time = available_time - used_time
            if remaining_time > 300:  # At least 5 minutes
                exploration_videos = await self._generate_exploration_videos(
                    profile, 3, None
                )
                
                for video in exploration_videos:
                    video_duration = video.video.duration_seconds or 600
                    if used_time + video_duration <= available_time:
                        playlist.append(video)
                        used_time += video_duration
                        break
            
            # Sort by difficulty if progression is enabled
            if difficulty_progression:
                playlist.sort(key=lambda x: x.difficulty_match)
            
            return playlist
            
        except Exception as e:
            logger.error(f"Error creating learning playlist: {e}")
            return []