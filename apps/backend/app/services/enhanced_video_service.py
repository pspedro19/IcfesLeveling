"""
Enhanced Video Service
Comprehensive service for YouTube video integration, recommendations, and learning analytics
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
import json
import logging
import re
from enum import Enum
from dataclasses import dataclass, asdict

from ..models.user import User
from ..models.video_tracking import VideoTracking
from ..models.youtube_video import YoutubeVideo
from ..models.study_plan import StudyPlan, StudyPlanTemplate
from ..models.topic import Topic
from ..core.config import settings
from ..services.cache_service import cache_service

logger = logging.getLogger(__name__)

class VideoQuality(Enum):
    SD = "sd"          # 480p
    HD = "hd"          # 720p
    FULL_HD = "fullhd" # 1080p
    AUTO = "auto"      # Adaptive

class VideoCategory(Enum):
    CONCEPT_EXPLANATION = "concept_explanation"
    PROBLEM_SOLVING = "problem_solving"
    REVIEW = "review"
    ADVANCED_TOPIC = "advanced_topic"
    MOTIVATION = "motivation"
    EXAM_PREP = "exam_prep"

class RecommendationReason(Enum):
    TOPIC_MATCH = "topic_match"
    DIFFICULTY_APPROPRIATE = "difficulty_appropriate"
    LEARNING_STYLE = "learning_style"
    PERFORMANCE_BASED = "performance_based"
    COMPLETION_PATTERN = "completion_pattern"
    PEER_PREFERENCE = "peer_preference"

@dataclass
class VideoRecommendation:
    """Represents a personalized video recommendation"""
    video_id: str
    title: str
    youtube_url: str
    thumbnail_url: str
    duration_seconds: int
    difficulty_level: int
    topic_tags: List[str]
    category: VideoCategory
    recommendation_score: float
    reasons: List[RecommendationReason]
    personalization_data: Dict[str, Any]
    estimated_engagement_time: int

@dataclass
class VideoAnalytics:
    """Video learning analytics data"""
    video_id: str
    user_id: str
    total_watch_time: int
    completion_rate: float
    engagement_score: float
    learning_effectiveness: float
    rewatch_count: int
    pause_points: List[int]  # Seconds where user paused
    skip_points: List[Tuple[int, int]]  # (start, end) seconds skipped

class EnhancedVideoService:
    """
    Advanced video service with AI-powered recommendations and analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def get_personalized_video_recommendations(
        self,
        user_id: str,
        topic: str = None,
        difficulty_level: int = None,
        max_recommendations: int = 10,
        learning_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get AI-powered personalized video recommendations for a user
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"User {user_id} not found")
            
            # Analyze user's video watching patterns
            watching_patterns = await self._analyze_user_video_patterns(user_id)
            
            # Get user's learning preferences
            learning_preferences = await self._get_user_learning_preferences(user_id)
            
            # Analyze current learning context
            context_analysis = await self._analyze_learning_context(
                user_id, topic, learning_context
            )
            
            # Get candidate videos
            candidate_videos = await self._get_candidate_videos(
                topic, difficulty_level, context_analysis
            )
            
            # Apply AI recommendation algorithm
            recommendations = await self._apply_recommendation_algorithm(
                user_id, candidate_videos, watching_patterns, 
                learning_preferences, context_analysis
            )
            
            # Rank and filter recommendations
            final_recommendations = await self._rank_and_filter_recommendations(
                recommendations, max_recommendations
            )
            
            # Add engagement predictions
            for rec in final_recommendations:
                rec.estimated_engagement_time = await self._predict_engagement_time(
                    user_id, rec, watching_patterns
                )
            
            # Create learning paths if multiple videos
            learning_paths = await self._create_video_learning_paths(
                final_recommendations, context_analysis
            )
            
            recommendation_data = {
                "user_id": user_id,
                "topic": topic,
                "difficulty_level": difficulty_level,
                "recommendation_timestamp": datetime.now().isoformat(),
                "total_candidates_analyzed": len(candidate_videos),
                "final_recommendations_count": len(final_recommendations),
                "recommendations": [asdict(rec) for rec in final_recommendations],
                "learning_paths": learning_paths,
                "user_patterns": watching_patterns,
                "context_analysis": context_analysis,
                "personalization_confidence": await self._calculate_personalization_confidence(
                    watching_patterns, learning_preferences
                ),
                "expected_learning_outcomes": await self._predict_learning_outcomes(
                    user_id, final_recommendations, context_analysis
                )
            }
            
            # Cache recommendations
            cache_key = f"video_recommendations:{user_id}:{topic or 'all'}"
            cache_service.set(cache_key, recommendation_data, expire=1800)  # 30 minutes
            
            return recommendation_data
            
        except Exception as e:
            logger.error(f"Error getting personalized video recommendations: {str(e)}")
            raise
    
    async def track_video_interaction(
        self,
        user_id: str,
        video_id: str,
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track detailed video interaction for learning analytics
        """
        try:
            # Get or create video tracking record
            video_tracking = self.db.query(VideoTracking).filter(
                VideoTracking.user_id == user_id,
                VideoTracking.video_id == video_id
            ).first()
            
            if not video_tracking:
                video_tracking = VideoTracking(
                    user_id=user_id,
                    video_id=video_id,
                    watched_at=datetime.now()
                )
                self.db.add(video_tracking)
            
            # Update tracking data
            current_time = interaction_data.get("current_time", 0)
            total_duration = interaction_data.get("total_duration", 0)
            interaction_type = interaction_data.get("interaction_type", "watch")
            
            # Update watch time and completion
            if interaction_type == "watch":
                video_tracking.watch_time_seconds = max(
                    video_tracking.watch_time_seconds or 0,
                    current_time
                )
                
                if total_duration > 0:
                    video_tracking.completion_percentage = min(100, 
                        (current_time / total_duration) * 100
                    )
            
            # Track specific interactions
            interaction_history = video_tracking.interaction_history or []
            interaction_history.append({
                "type": interaction_type,
                "timestamp": datetime.now().isoformat(),
                "current_time": current_time,
                "data": interaction_data
            })
            video_tracking.interaction_history = interaction_history
            
            # Update engagement metrics
            engagement_score = await self._calculate_engagement_score(
                video_tracking, interaction_data
            )
            video_tracking.engagement_score = engagement_score
            
            # Calculate learning effectiveness
            learning_effectiveness = await self._calculate_learning_effectiveness(
                user_id, video_tracking, interaction_data
            )
            
            self.db.commit()
            
            # Analyze learning patterns
            pattern_analysis = await self._analyze_interaction_patterns(
                user_id, video_tracking, interaction_data
            )
            
            # Check for learning milestones
            milestones = await self._check_video_learning_milestones(
                user_id, video_tracking
            )
            
            # Update AI recommendation models
            model_updates = await self._update_recommendation_models(
                user_id, video_tracking, interaction_data
            )
            
            tracking_result = {
                "success": True,
                "user_id": user_id,
                "video_id": video_id,
                "interaction_type": interaction_type,
                "updated_metrics": {
                    "watch_time_seconds": video_tracking.watch_time_seconds,
                    "completion_percentage": video_tracking.completion_percentage,
                    "engagement_score": engagement_score,
                    "learning_effectiveness": learning_effectiveness
                },
                "pattern_analysis": pattern_analysis,
                "milestones_achieved": milestones,
                "recommendation_updates": model_updates,
                "next_video_suggestions": await self._get_next_video_suggestions(
                    user_id, video_id, interaction_data
                )
            }
            
            return tracking_result
            
        except Exception as e:
            logger.error(f"Error tracking video interaction: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_video_learning_analytics(
        self,
        user_id: str,
        time_period: int = 30,
        video_id: str = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive video learning analytics
        """
        try:
            # Get video tracking data
            query = self.db.query(VideoTracking).filter(
                VideoTracking.user_id == user_id,
                VideoTracking.watched_at >= datetime.now() - timedelta(days=time_period)
            )
            
            if video_id:
                query = query.filter(VideoTracking.video_id == video_id)
            
            video_data = query.all()
            
            if not video_data:
                return {
                    "total_videos_watched": 0,
                    "total_watch_time": 0,
                    "average_completion_rate": 0,
                    "analytics": "No video data available for period"
                }
            
            # Calculate comprehensive metrics
            watch_time_metrics = await self._calculate_watch_time_metrics(video_data)
            
            # Completion analysis
            completion_analysis = await self._analyze_completion_patterns(video_data)
            
            # Engagement analysis
            engagement_analysis = await self._analyze_engagement_patterns(video_data)
            
            # Learning effectiveness analysis
            effectiveness_analysis = await self._analyze_learning_effectiveness(
                user_id, video_data
            )
            
            # Topic preference analysis
            topic_preferences = await self._analyze_topic_preferences(video_data)
            
            # Viewing behavior analysis
            behavior_analysis = await self._analyze_viewing_behavior(video_data)
            
            # Learning progress correlation
            progress_correlation = await self._correlate_videos_with_progress(
                user_id, video_data
            )
            
            # Generate insights and recommendations
            insights = await self._generate_video_learning_insights(
                watch_time_metrics, completion_analysis, engagement_analysis,
                effectiveness_analysis, topic_preferences, behavior_analysis
            )
            
            # Optimization recommendations
            optimization_recommendations = await self._generate_video_optimization_recommendations(
                user_id, insights, behavior_analysis
            )
            
            analytics = {
                "user_id": user_id,
                "analysis_period_days": time_period,
                "video_id": video_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "summary_metrics": {
                    "total_videos_watched": len(video_data),
                    "total_watch_time_minutes": watch_time_metrics["total_minutes"],
                    "average_completion_rate": completion_analysis["average_completion"],
                    "overall_engagement_score": engagement_analysis["overall_score"]
                },
                "detailed_analytics": {
                    "watch_time_metrics": watch_time_metrics,
                    "completion_analysis": completion_analysis,
                    "engagement_analysis": engagement_analysis,
                    "effectiveness_analysis": effectiveness_analysis,
                    "topic_preferences": topic_preferences,
                    "behavior_analysis": behavior_analysis,
                    "progress_correlation": progress_correlation
                },
                "insights": insights,
                "optimization_recommendations": optimization_recommendations,
                "learning_efficiency_score": await self._calculate_learning_efficiency_score(
                    watch_time_metrics, effectiveness_analysis, progress_correlation
                )
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting video learning analytics: {str(e)}")
            return {"error": str(e)}
    
    async def create_adaptive_video_playlist(
        self,
        user_id: str,
        learning_objective: str,
        target_duration_minutes: int = 60,
        difficulty_progression: str = "adaptive"
    ) -> Dict[str, Any]:
        """
        Create an adaptive video playlist based on learning objectives
        """
        try:
            # Analyze learning objective
            objective_analysis = await self._analyze_learning_objective(
                learning_objective, user_id
            )
            
            # Get user's current skill level and preferences
            user_profile = await self._build_user_video_profile(user_id)
            
            # Find relevant videos
            candidate_videos = await self._find_videos_for_objective(
                objective_analysis, user_profile
            )
            
            # Apply difficulty progression strategy
            ordered_videos = await self._apply_difficulty_progression(
                candidate_videos, difficulty_progression, user_profile
            )
            
            # Optimize playlist duration
            optimized_playlist = await self._optimize_playlist_duration(
                ordered_videos, target_duration_minutes
            )
            
            # Add interactive elements
            interactive_elements = await self._add_interactive_elements(
                optimized_playlist, user_profile
            )
            
            # Create learning checkpoints
            checkpoints = await self._create_learning_checkpoints(
                optimized_playlist, objective_analysis
            )
            
            # Predict learning outcomes
            outcome_predictions = await self._predict_playlist_outcomes(
                user_id, optimized_playlist, objective_analysis
            )
            
            playlist = {
                "playlist_id": f"adaptive-{user_id}-{int(datetime.now().timestamp())}",
                "user_id": user_id,
                "learning_objective": learning_objective,
                "created_at": datetime.now().isoformat(),
                "target_duration_minutes": target_duration_minutes,
                "actual_duration_minutes": sum(v["duration_seconds"] for v in optimized_playlist) // 60,
                "difficulty_progression": difficulty_progression,
                "objective_analysis": objective_analysis,
                "user_profile": user_profile,
                "playlist_videos": optimized_playlist,
                "interactive_elements": interactive_elements,
                "learning_checkpoints": checkpoints,
                "outcome_predictions": outcome_predictions,
                "adaptive_features": {
                    "dynamic_reordering": True,
                    "difficulty_adjustment": True,
                    "personalized_pacing": True,
                    "progress_based_recommendations": True
                },
                "effectiveness_metrics": {
                    "predicted_completion_rate": outcome_predictions.get("completion_rate", 0.8),
                    "expected_learning_gain": outcome_predictions.get("learning_gain", 0.7),
                    "engagement_score_prediction": outcome_predictions.get("engagement", 0.75)
                }
            }
            
            # Cache the playlist
            cache_key = f"adaptive_playlist:{user_id}:{objective_analysis['topic_hash']}"
            cache_service.set(cache_key, playlist, expire=3600 * 2)  # 2 hours
            
            return playlist
            
        except Exception as e:
            logger.error(f"Error creating adaptive video playlist: {str(e)}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _analyze_user_video_patterns(self, user_id: str) -> Dict[str, Any]:
        """Analyze user's video watching patterns and preferences"""
        
        video_data = self.db.query(VideoTracking).filter(
            VideoTracking.user_id == user_id,
            VideoTracking.watched_at >= datetime.now() - timedelta(days=30)
        ).all()
        
        if not video_data:
            return {
                "total_videos_watched": 0,
                "preferred_duration_range": (300, 900),  # 5-15 minutes
                "completion_rate": 0.7,
                "engagement_pattern": "mixed",
                "preferred_times": []
            }
        
        # Analyze duration preferences
        durations = [vd.watch_time_seconds for vd in video_data if vd.watch_time_seconds]
        avg_duration = sum(durations) / len(durations) if durations else 600
        
        # Analyze completion rates
        completions = [vd.completion_percentage for vd in video_data if vd.completion_percentage]
        avg_completion = sum(completions) / len(completions) if completions else 70
        
        # Analyze viewing times
        viewing_hours = [vd.watched_at.hour for vd in video_data]
        hour_frequency = {}
        for hour in viewing_hours:
            hour_frequency[hour] = hour_frequency.get(hour, 0) + 1
        
        preferred_hours = sorted(hour_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Analyze engagement patterns
        engagement_scores = [vd.engagement_score for vd in video_data if vd.engagement_score]
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0.6
        
        return {
            "total_videos_watched": len(video_data),
            "preferred_duration_range": (max(300, avg_duration - 300), avg_duration + 300),
            "average_watch_time": avg_duration,
            "completion_rate": avg_completion / 100,
            "average_engagement_score": avg_engagement,
            "preferred_viewing_hours": [hour for hour, freq in preferred_hours],
            "engagement_pattern": "high" if avg_engagement > 0.7 else "medium" if avg_engagement > 0.4 else "low",
            "rewatch_tendency": await self._calculate_rewatch_tendency(video_data),
            "skip_patterns": await self._analyze_skip_patterns(video_data)
        }
    
    async def _get_candidate_videos(
        self,
        topic: str,
        difficulty_level: int,
        context_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get candidate videos for recommendation"""
        
        # Query YouTube videos from database
        query = self.db.query(YoutubeVideo)
        
        # Filter by topic if provided
        if topic:
            query = query.filter(
                or_(
                    YoutubeVideo.tags.contains([topic]),
                    func.lower(YoutubeVideo.title).contains(topic.lower()),
                    func.lower(YoutubeVideo.description).contains(topic.lower())
                )
            )
        
        # Filter by difficulty level if provided
        if difficulty_level:
            query = query.filter(
                and_(
                    YoutubeVideo.difficulty_level >= difficulty_level - 1,
                    YoutubeVideo.difficulty_level <= difficulty_level + 1
                )
            )
        
        # Get videos ordered by quality metrics
        videos = query.order_by(desc(YoutubeVideo.quality_score)).limit(50).all()
        
        # Convert to dict format and add metadata
        candidate_videos = []
        for video in videos:
            candidate_videos.append({
                "id": str(video.id),
                "youtube_id": video.youtube_id,
                "title": video.title,
                "description": video.description,
                "duration_seconds": video.duration_seconds,
                "difficulty_level": video.difficulty_level,
                "tags": video.tags or [],
                "quality_score": video.quality_score,
                "view_count": video.view_count,
                "like_count": video.like_count,
                "channel_name": video.channel_name,
                "thumbnail_url": video.thumbnail_url,
                "youtube_url": f"https://www.youtube.com/watch?v={video.youtube_id}",
                "topic_relevance": await self._calculate_topic_relevance(video, topic),
                "context_relevance": await self._calculate_context_relevance(video, context_analysis)
            })
        
        return candidate_videos
    
    async def _apply_recommendation_algorithm(
        self,
        user_id: str,
        candidate_videos: List[Dict[str, Any]],
        watching_patterns: Dict[str, Any],
        learning_preferences: Dict[str, Any],
        context_analysis: Dict[str, Any]
    ) -> List[VideoRecommendation]:
        """Apply AI recommendation algorithm to candidate videos"""
        
        recommendations = []
        
        for video in candidate_videos:
            # Calculate recommendation score
            score_components = {
                "topic_relevance": video["topic_relevance"] * 0.3,
                "difficulty_match": await self._calculate_difficulty_match(
                    video, learning_preferences
                ) * 0.25,
                "duration_preference": await self._calculate_duration_preference(
                    video, watching_patterns
                ) * 0.2,
                "quality_score": (video["quality_score"] / 10) * 0.15,
                "engagement_prediction": await self._predict_user_engagement(
                    user_id, video, watching_patterns
                ) * 0.1
            }
            
            total_score = sum(score_components.values())
            
            # Determine recommendation reasons
            reasons = []
            if video["topic_relevance"] > 0.8:
                reasons.append(RecommendationReason.TOPIC_MATCH)
            if score_components["difficulty_match"] > 0.7:
                reasons.append(RecommendationReason.DIFFICULTY_APPROPRIATE)
            if score_components["engagement_prediction"] > 0.7:
                reasons.append(RecommendationReason.PERFORMANCE_BASED)
            
            # Create recommendation object
            recommendation = VideoRecommendation(
                video_id=video["id"],
                title=video["title"],
                youtube_url=video["youtube_url"],
                thumbnail_url=video["thumbnail_url"],
                duration_seconds=video["duration_seconds"],
                difficulty_level=video["difficulty_level"],
                topic_tags=video["tags"],
                category=await self._classify_video_category(video),
                recommendation_score=total_score,
                reasons=reasons,
                personalization_data={
                    "score_components": score_components,
                    "user_pattern_match": await self._calculate_pattern_match(
                        video, watching_patterns
                    ),
                    "learning_context_fit": video["context_relevance"]
                },
                estimated_engagement_time=0  # Will be set later
            )
            
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _calculate_engagement_score(
        self,
        video_tracking: VideoTracking,
        interaction_data: Dict[str, Any]
    ) -> float:
        """Calculate engagement score based on viewing behavior"""
        
        # Base engagement from completion rate
        completion_rate = video_tracking.completion_percentage / 100 if video_tracking.completion_percentage else 0
        base_score = completion_rate
        
        # Bonus for full completion
        if completion_rate >= 0.95:
            base_score += 0.1
        
        # Analyze interaction patterns
        interaction_history = video_tracking.interaction_history or []
        
        # Positive interactions (seeking forward/backward indicates engagement)
        positive_interactions = sum(1 for i in interaction_history 
                                  if i.get("type") in ["seek", "pause", "resume"])
        
        # Normalize interaction score
        if len(interaction_history) > 0:
            interaction_score = min(0.3, positive_interactions / len(interaction_history))
        else:
            interaction_score = 0
        
        # Consider watch time vs video duration
        if video_tracking.watch_time_seconds and interaction_data.get("total_duration"):
            time_ratio = video_tracking.watch_time_seconds / interaction_data["total_duration"]
            time_score = min(0.2, time_ratio * 0.2)
        else:
            time_score = 0.1
        
        # Combine scores
        total_engagement = base_score + interaction_score + time_score
        
        return min(1.0, max(0.0, total_engagement))
    
    async def _calculate_learning_effectiveness(
        self,
        user_id: str,
        video_tracking: VideoTracking,
        interaction_data: Dict[str, Any]
    ) -> float:
        """Calculate learning effectiveness of video for the user"""
        
        # Base effectiveness from engagement and completion
        base_effectiveness = video_tracking.engagement_score or 0.5
        
        # Check if user performed better after watching video
        # This would require correlation with quiz/battle performance
        # For now, use completion rate as proxy
        completion_bonus = min(0.3, video_tracking.completion_percentage / 100 * 0.3)
        
        # Consider rewatch behavior (indicates difficulty or high value)
        rewatch_count = sum(1 for i in video_tracking.interaction_history or []
                          if i.get("type") == "rewatch")
        
        if rewatch_count > 0:
            # Some rewatching is good, too much might indicate difficulty
            rewatch_factor = min(0.2, rewatch_count * 0.1) if rewatch_count <= 2 else -0.1
        else:
            rewatch_factor = 0
        
        # Duration appropriateness
        if interaction_data.get("total_duration"):
            duration_minutes = interaction_data["total_duration"] / 60
            if 5 <= duration_minutes <= 20:  # Optimal range
                duration_factor = 0.1
            else:
                duration_factor = 0
        else:
            duration_factor = 0
        
        total_effectiveness = base_effectiveness + completion_bonus + rewatch_factor + duration_factor
        
        return min(1.0, max(0.0, total_effectiveness))