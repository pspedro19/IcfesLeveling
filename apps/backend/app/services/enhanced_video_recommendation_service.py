"""
Enhanced Video Recommendation Service with Monthly Refresh
Automatically updates YouTube video recommendations based on monthly diagnostic results
and learning progress tracking.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, and_, desc, func, or_
from datetime import datetime, timedelta
from ..models.youtube_links import YouTubeLinks
from ..models.diagnostic_test import DiagnosticTest, DiagnosticTestResult
from ..models.user import User
from ..models.topic import Topic
from ..models.subject import Subject
import random
import json
import uuid

logger = logging.getLogger(__name__)

class EnhancedVideoRecommendationService:
    """
    Enhanced video recommendation service that adapts to monthly diagnostic results
    and provides personalized learning paths through video content.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def refresh_monthly_recommendations(self, user_id: str, subject_id: str, 
                                      diagnostic_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh video recommendations based on monthly diagnostic results.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            diagnostic_results: Latest diagnostic assessment results
            
        Returns:
            Updated recommendation profile with new video suggestions
        """
        try:
            # Analyze performance changes from diagnostic results
            performance_analysis = self._analyze_performance_changes(diagnostic_results)
            
            # Get current recommendation profile
            current_profile = self._get_current_recommendation_profile(user_id, subject_id)
            
            # Generate updated recommendations based on performance
            updated_recommendations = self._generate_adaptive_recommendations(
                user_id, subject_id, performance_analysis, current_profile
            )
            
            # Create personalized learning path
            learning_path = self._create_personalized_learning_path(
                user_id, subject_id, performance_analysis, updated_recommendations
            )
            
            # Calculate recommendation priorities
            priorities = self._calculate_recommendation_priorities(performance_analysis)
            
            # Store updated recommendation profile
            recommendation_profile = {
                "user_id": user_id,
                "subject_id": subject_id,
                "updated_at": datetime.utcnow(),
                "performance_analysis": performance_analysis,
                "recommendations": updated_recommendations,
                "learning_path": learning_path,
                "priorities": priorities,
                "refresh_reason": "monthly_diagnostic_update",
                "next_refresh_date": datetime.utcnow() + timedelta(days=30)
            }
            
            self._store_recommendation_profile(user_id, subject_id, recommendation_profile)
            
            # Generate immediate action items
            action_items = self._generate_immediate_action_items(performance_analysis, updated_recommendations)
            
            self.logger.info(f"Refreshed video recommendations for user {user_id}, subject {subject_id}")
            
            return {
                "profile_updated": True,
                "recommendation_profile": recommendation_profile,
                "immediate_actions": action_items,
                "recommendations_count": sum(len(videos) for videos in updated_recommendations.values()),
                "learning_path_length": len(learning_path.get("path_segments", []))
            }
            
        except Exception as e:
            self.logger.error(f"Error refreshing monthly recommendations: {str(e)}")
            raise
    
    def get_adaptive_video_recommendations(self, user_id: str, subject_id: str, 
                                         recommendation_type: str = "adaptive",
                                         count: int = 20) -> List[Dict[str, Any]]:
        """
        Get adaptive video recommendations based on current performance and learning state.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            recommendation_type: Type of recommendations ("focus", "review", "challenge", "adaptive")
            count: Number of recommendations to return
            
        Returns:
            List of recommended videos with metadata
        """
        try:
            # Get current recommendation profile
            profile = self._get_current_recommendation_profile(user_id, subject_id)
            
            if not profile:
                # Generate initial recommendations
                profile = self._generate_initial_recommendation_profile(user_id, subject_id)
            
            # Get recommendations based on type
            if recommendation_type == "focus":
                videos = self._get_focus_video_recommendations(user_id, subject_id, profile, count)
            elif recommendation_type == "review":
                videos = self._get_review_video_recommendations(user_id, subject_id, profile, count)
            elif recommendation_type == "challenge":
                videos = self._get_challenge_video_recommendations(user_id, subject_id, profile, count)
            else:  # adaptive
                videos = self._get_adaptive_mixed_recommendations(user_id, subject_id, profile, count)
            
            # Enhance videos with personalization metadata
            enhanced_videos = []
            for video in videos:
                enhanced_video = self._enhance_video_with_metadata(video, profile, recommendation_type)
                enhanced_videos.append(enhanced_video)
            
            # Track recommendation request
            self._track_recommendation_request(user_id, subject_id, recommendation_type, len(enhanced_videos))
            
            return enhanced_videos
            
        except Exception as e:
            self.logger.error(f"Error getting adaptive video recommendations: {str(e)}")
            return []
    
    def track_video_engagement(self, user_id: str, video_id: str, 
                             engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track video engagement to improve future recommendations.
        
        Args:
            user_id: User identifier
            video_id: Video identifier
            engagement_data: Data about video engagement (watch_time, completion_rate, etc.)
            
        Returns:
            Updated engagement profile and next video suggestions
        """
        try:
            # Store engagement data
            engagement_record = {
                "user_id": user_id,
                "video_id": video_id,
                "watched_duration_seconds": engagement_data.get("watched_duration", 0),
                "total_duration_seconds": engagement_data.get("total_duration", 0),
                "completion_rate": engagement_data.get("completion_rate", 0.0),
                "user_rating": engagement_data.get("rating", None),
                "helpful_rating": engagement_data.get("helpful", None),
                "watched_at": datetime.utcnow(),
                "device_type": engagement_data.get("device_type", "unknown"),
                "source": engagement_data.get("source", "recommendation")
            }
            
            self._store_video_engagement(engagement_record)
            
            # Update user's video preferences
            preference_update = self._update_video_preferences(user_id, video_id, engagement_data)
            
            # Get next video suggestions based on engagement
            next_suggestions = self._get_engagement_based_suggestions(user_id, video_id, engagement_data)
            
            # Calculate engagement score impact
            engagement_impact = self._calculate_engagement_impact(engagement_data)
            
            return {
                "engagement_recorded": True,
                "preference_update": preference_update,
                "next_suggestions": next_suggestions,
                "engagement_impact": engagement_impact
            }
            
        except Exception as e:
            self.logger.error(f"Error tracking video engagement: {str(e)}")
            return {"engagement_recorded": False, "error": str(e)}
    
    def get_learning_path_videos(self, user_id: str, subject_id: str, 
                               path_segment: str = "current") -> Dict[str, Any]:
        """
        Get videos for a specific learning path segment.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            path_segment: Segment of learning path ("current", "next", "review", "advanced")
            
        Returns:
            Videos and metadata for the learning path segment
        """
        try:
            # Get recommendation profile
            profile = self._get_current_recommendation_profile(user_id, subject_id)
            
            if not profile or "learning_path" not in profile:
                return {"error": "No learning path available"}
            
            learning_path = profile["learning_path"]
            
            # Get videos for the requested segment
            segment_data = learning_path.get("path_segments", {}).get(path_segment, {})
            
            if not segment_data:
                return {"error": f"Learning path segment '{path_segment}' not found"}
            
            # Get videos for this segment
            video_ids = segment_data.get("video_ids", [])
            videos = self._get_videos_by_ids(video_ids)
            
            # Enhance with learning path metadata
            enhanced_videos = []
            for video in videos:
                enhanced_video = video.copy()
                enhanced_video.update({
                    "learning_path_position": segment_data.get("position", 0),
                    "completion_requirement": segment_data.get("completion_requirement", 0.8),
                    "estimated_study_time": segment_data.get("estimated_time_minutes", 30),
                    "prerequisites_met": self._check_path_prerequisites(user_id, segment_data),
                    "path_segment": path_segment
                })
                enhanced_videos.append(enhanced_video)
            
            return {
                "path_segment": path_segment,
                "videos": enhanced_videos,
                "segment_metadata": segment_data,
                "progress": self._calculate_path_progress(user_id, learning_path),
                "estimated_completion_time": segment_data.get("estimated_time_minutes", 30)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting learning path videos: {str(e)}")
            return {"error": str(e)}
    
    def update_recommendations_for_user(self, user_id: str, subject_id: str, 
                                      weak_topics: List[str], improved_topics: List[str]) -> Dict[str, Any]:
        """
        Update recommendations based on topic performance changes.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            weak_topics: Topics that need improvement
            improved_topics: Topics that have improved
            
        Returns:
            Updated recommendation summary
        """
        try:
            # Get current recommendations
            current_profile = self._get_current_recommendation_profile(user_id, subject_id)
            
            # Generate topic-specific recommendations
            weak_topic_videos = self._get_videos_for_topics(weak_topics, difficulty_level="basic")
            improved_topic_videos = self._get_videos_for_topics(improved_topics, difficulty_level="advanced")
            
            # Update recommendation weights
            updated_weights = self._update_recommendation_weights(
                current_profile, weak_topics, improved_topics
            )
            
            # Create focused learning sessions
            learning_sessions = self._create_topic_focused_sessions(weak_topics, improved_topics)
            
            # Store updated profile
            updated_profile = {
                "user_id": user_id,
                "subject_id": subject_id,
                "updated_at": datetime.utcnow(),
                "weak_topics": weak_topics,
                "improved_topics": improved_topics,
                "recommendation_weights": updated_weights,
                "focused_videos": {
                    "weak_topics": weak_topic_videos,
                    "improved_topics": improved_topic_videos
                },
                "learning_sessions": learning_sessions,
                "update_reason": "topic_performance_change"
            }
            
            self._update_recommendation_profile(user_id, subject_id, updated_profile)
            
            return {
                "recommendations_updated": True,
                "weak_topic_videos": len(weak_topic_videos),
                "improved_topic_videos": len(improved_topic_videos),
                "learning_sessions_created": len(learning_sessions),
                "update_timestamp": datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error updating recommendations for user: {str(e)}")
            return {"recommendations_updated": False, "error": str(e)}
    
    def get_recommendation_analytics(self, user_id: str, subject_id: str, 
                                   time_period: int = 30) -> Dict[str, Any]:
        """
        Get analytics about video recommendation effectiveness.
        
        Args:
            user_id: User identifier
            subject_id: Subject identifier
            time_period: Number of days to analyze
            
        Returns:
            Comprehensive analytics about recommendation performance
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=time_period)
            
            # Get engagement data
            engagement_analytics = self._analyze_engagement_data(user_id, subject_id, start_date)
            
            # Get recommendation effectiveness
            effectiveness_metrics = self._calculate_recommendation_effectiveness(user_id, subject_id, start_date)
            
            # Get learning progress correlation
            progress_correlation = self._analyze_learning_progress_correlation(user_id, subject_id, start_date)
            
            # Get content preference analysis
            content_preferences = self._analyze_content_preferences(user_id, subject_id, start_date)
            
            # Generate insights and recommendations
            insights = self._generate_recommendation_insights(
                engagement_analytics, effectiveness_metrics, progress_correlation, content_preferences
            )
            
            return {
                "user_id": user_id,
                "subject_id": subject_id,
                "analysis_period_days": time_period,
                "analytics": {
                    "engagement": engagement_analytics,
                    "effectiveness": effectiveness_metrics,
                    "progress_correlation": progress_correlation,
                    "content_preferences": content_preferences
                },
                "insights": insights,
                "generated_at": datetime.utcnow()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation analytics: {str(e)}")
            return {"error": str(e)}
    
    # Private helper methods
    
    def _analyze_performance_changes(self, diagnostic_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance changes from diagnostic results."""
        comparison = diagnostic_results.get("comparison", {})
        
        return {
            "overall_improvement": comparison.get("improvement_percentage", 0),
            "current_score": comparison.get("current_score", 0),
            "previous_score": comparison.get("initial_score", 0),
            "improved_topics": comparison.get("topics_improved", []),
            "declined_topics": comparison.get("topics_declined", []),
            "score_by_topic": comparison.get("current_score_by_topic", {}),
            "performance_trend": comparison.get("overall_trend", "stable"),
            "days_since_last": comparison.get("days_since_initial", 0)
        }
    
    def _get_current_recommendation_profile(self, user_id: str, subject_id: str) -> Optional[Dict[str, Any]]:
        """Get current recommendation profile for user and subject."""
        # In a real implementation, this would be stored in database
        # For now, return a default profile
        return {
            "recommendation_weights": {"weak_topics": 0.6, "review": 0.3, "challenge": 0.1},
            "preferred_content_types": ["explicativo", "ejercicio_guiado"],
            "learning_pace": "medium",
            "last_updated": datetime.utcnow() - timedelta(days=10)
        }
    
    def _generate_adaptive_recommendations(self, user_id: str, subject_id: str, 
                                         performance_analysis: Dict[str, Any],
                                         current_profile: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """Generate adaptive recommendations based on performance analysis."""
        recommendations = {
            "immediate_focus": [],
            "skill_building": [],
            "knowledge_review": [],
            "advanced_practice": [],
            "comprehensive_review": []
        }
        
        overall_score = performance_analysis["current_score"]
        improved_topics = performance_analysis["improved_topics"]
        declined_topics = performance_analysis["declined_topics"]
        
        # Immediate focus (declined or weak topics)
        if declined_topics:
            focus_videos = self._get_videos_for_topics(
                declined_topics[:3], 
                content_type="explicativo",
                difficulty_level=1
            )
            recommendations["immediate_focus"] = focus_videos[:8]
        
        # Skill building (medium difficulty for weak areas)
        weak_topics = [topic for topic, score in performance_analysis["score_by_topic"].items() if score < 60]
        if weak_topics:
            skill_videos = self._get_videos_for_topics(
                weak_topics[:3],
                content_type="ejercicio_guiado",
                difficulty_level=2
            )
            recommendations["skill_building"] = skill_videos[:10]
        
        # Knowledge review (balanced topics)
        if overall_score >= 50:
            review_topics = list(performance_analysis["score_by_topic"].keys())[:4]
            review_videos = self._get_videos_for_topics(
                review_topics,
                content_type="resumen",
                difficulty_level=3
            )
            recommendations["knowledge_review"] = review_videos[:12]
        
        # Advanced practice (improved topics and high performance)
        if overall_score >= 70 and improved_topics:
            advanced_videos = self._get_videos_for_topics(
                improved_topics[:2],
                content_type="ejercicio_guiado",
                difficulty_level=4
            )
            recommendations["advanced_practice"] = advanced_videos[:6]
        
        # Comprehensive review (all topics, mixed difficulty)
        all_topics = list(performance_analysis["score_by_topic"].keys())
        if all_topics:
            comprehensive_videos = self._get_videos_for_topics(
                all_topics[:5],
                content_type="resumen",
                difficulty_level=None  # Mixed difficulty
            )
            recommendations["comprehensive_review"] = comprehensive_videos[:15]
        
        return recommendations
    
    def _create_personalized_learning_path(self, user_id: str, subject_id: str,
                                         performance_analysis: Dict[str, Any],
                                         recommendations: Dict[str, List[Dict]]) -> Dict[str, Any]:
        """Create a personalized learning path based on performance and recommendations."""
        overall_score = performance_analysis["current_score"]
        
        # Determine learning path structure based on performance level
        if overall_score < 50:
            path_structure = ["foundation", "basic_practice", "skill_building", "review"]
        elif overall_score < 70:
            path_structure = ["skill_building", "targeted_practice", "knowledge_review", "application"]
        else:
            path_structure = ["advanced_practice", "comprehensive_review", "mastery", "challenge"]
        
        path_segments = {}
        for i, segment_name in enumerate(path_structure):
            # Map segment to appropriate recommendation category
            if segment_name in ["foundation", "basic_practice"]:
                videos = recommendations.get("immediate_focus", [])[:5]
            elif segment_name in ["skill_building", "targeted_practice"]:
                videos = recommendations.get("skill_building", [])[:6]
            elif segment_name in ["knowledge_review", "review"]:
                videos = recommendations.get("knowledge_review", [])[:8]
            elif segment_name in ["advanced_practice", "application"]:
                videos = recommendations.get("advanced_practice", [])[:5]
            else:  # comprehensive_review, mastery, challenge
                videos = recommendations.get("comprehensive_review", [])[:10]
            
            path_segments[segment_name] = {
                "position": i,
                "video_ids": [v["id"] for v in videos],
                "estimated_time_minutes": len(videos) * 12,  # Estimate 12 min per video
                "completion_requirement": 0.8,
                "prerequisites": path_structure[:i] if i > 0 else [],
                "description": self._get_segment_description(segment_name)
            }
        
        return {
            "path_id": str(uuid.uuid4()),
            "created_at": datetime.utcnow(),
            "path_structure": path_structure,
            "path_segments": path_segments,
            "total_estimated_time": sum(seg["estimated_time_minutes"] for seg in path_segments.values()),
            "difficulty_progression": self._calculate_difficulty_progression(path_structure),
            "adaptive_checkpoints": self._define_adaptive_checkpoints(path_structure)
        }
    
    def _calculate_recommendation_priorities(self, performance_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate priorities for different types of recommendations."""
        overall_score = performance_analysis["current_score"]
        improvement = performance_analysis["overall_improvement"]
        declined_topics_count = len(performance_analysis["declined_topics"])
        
        # Base priorities
        priorities = {
            "immediate_focus": 0.4,
            "skill_building": 0.3,
            "knowledge_review": 0.2,
            "advanced_practice": 0.1,
            "comprehensive_review": 0.15
        }
        
        # Adjust based on performance
        if overall_score < 50:
            priorities["immediate_focus"] = 0.6
            priorities["skill_building"] = 0.3
            priorities["advanced_practice"] = 0.05
        elif overall_score >= 80:
            priorities["advanced_practice"] = 0.3
            priorities["comprehensive_review"] = 0.25
            priorities["immediate_focus"] = 0.2
        
        # Adjust based on improvement trend
        if improvement < -10:
            priorities["immediate_focus"] = min(0.8, priorities["immediate_focus"] + 0.2)
        elif improvement > 15:
            priorities["advanced_practice"] = min(0.4, priorities["advanced_practice"] + 0.15)
        
        # Adjust for declined topics
        if declined_topics_count > 2:
            priorities["immediate_focus"] = min(0.7, priorities["immediate_focus"] + 0.15)
        
        # Normalize to ensure sum is 1.0
        total = sum(priorities.values())
        return {k: v/total for k, v in priorities.items()}
    
    def _get_videos_for_topics(self, topics: List[str], content_type: str = None, 
                             difficulty_level: int = None) -> List[Dict[str, Any]]:
        """Get videos for specific topics with optional filters."""
        try:
            # Base query
            query = """
                SELECT * FROM youtube_links 
                WHERE estado = 'activo'
            """
            params = {}
            
            # Filter by topics
            if topics:
                # Map topic names to codes (simplified mapping)
                topic_codes = [topic.lower().replace(' ', '_')[:20] for topic in topics]
                placeholders = ','.join([f':topic_{i}' for i in range(len(topic_codes))])
                query += f" AND (codigo_tema IN ({placeholders}) OR tema_principal IN ({placeholders}))"
                for i, topic in enumerate(topic_codes):
                    params[f'topic_{i}'] = topic
            
            # Filter by content type
            if content_type:
                query += " AND tipo_contenido = :content_type"
                params['content_type'] = content_type
            
            # Filter by difficulty level
            if difficulty_level:
                query += " AND nivel_dificultad = :difficulty"
                params['difficulty'] = difficulty_level
            
            # Order and limit
            query += """
                ORDER BY 
                    calidad_score DESC, 
                    relevancia_score DESC
                LIMIT 20
            """
            
            result = self.db.execute(text(query), params)
            videos = result.fetchall()
            
            # Convert to dictionaries
            video_list = []
            for video in videos:
                video_dict = {
                    'id': str(video.id),
                    'codigo_tema': video.codigo_tema,
                    'tema_principal': video.tema_principal,
                    'youtube_url': video.youtube_url,
                    'youtube_id': video.youtube_id,
                    'video_title': video.video_title,
                    'channel_name': video.channel_name,
                    'duration_seconds': video.duration_seconds,
                    'tipo_contenido': video.tipo_contenido,
                    'nivel_dificultad': video.nivel_dificultad,
                    'calidad_score': float(video.calidad_score) if video.calidad_score else 0.0,
                    'relevancia_score': float(video.relevancia_score) if video.relevancia_score else 0.0,
                    'puntos_xp': video.puntos_xp
                }
                video_list.append(video_dict)
            
            return video_list
            
        except Exception as e:
            self.logger.error(f"Error getting videos for topics {topics}: {str(e)}")
            return []
    
    def _enhance_video_with_metadata(self, video: Dict[str, Any], profile: Dict[str, Any], 
                                   recommendation_type: str) -> Dict[str, Any]:
        """Enhance video with personalization metadata."""
        enhanced_video = video.copy()
        
        # Add personalization metadata
        enhanced_video.update({
            "recommendation_type": recommendation_type,
            "personalization_score": self._calculate_personalization_score(video, profile),
            "estimated_engagement": self._estimate_engagement_likelihood(video, profile),
            "learning_benefit": self._estimate_learning_benefit(video, profile),
            "optimal_watch_time": self._calculate_optimal_watch_time(video),
            "prerequisites_met": True,  # Simplified
            "follow_up_suggestions": self._get_follow_up_suggestions(video),
            "adaptive_metadata": {
                "difficulty_match": self._calculate_difficulty_match(video, profile),
                "content_preference_match": self._calculate_content_preference_match(video, profile),
                "timing_recommendation": self._get_timing_recommendation(video)
            }
        })
        
        return enhanced_video
    
    def _store_recommendation_profile(self, user_id: str, subject_id: str, profile: Dict[str, Any]):
        """Store recommendation profile in database."""
        # In a real implementation, store in database table
        self.logger.info(f"Stored recommendation profile for user {user_id}, subject {subject_id}")
    
    def _generate_immediate_action_items(self, performance_analysis: Dict[str, Any], 
                                       recommendations: Dict[str, List[Dict]]) -> List[Dict[str, Any]]:
        """Generate immediate action items based on analysis."""
        actions = []
        
        declined_topics = performance_analysis["declined_topics"]
        overall_score = performance_analysis["current_score"]
        
        if declined_topics:
            actions.append({
                "action": "watch_focus_videos",
                "priority": "high",
                "description": f"Ver videos sobre temas que necesitan refuerzo: {', '.join(declined_topics[:2])}",
                "estimated_time_minutes": 30,
                "video_count": len(recommendations.get("immediate_focus", []))
            })
        
        if overall_score < 60:
            actions.append({
                "action": "foundation_review",
                "priority": "high",
                "description": "Revisar conceptos fundamentales con videos explicativos",
                "estimated_time_minutes": 45,
                "video_count": len(recommendations.get("skill_building", []))
            })
        
        if overall_score >= 70:
            actions.append({
                "action": "challenge_practice",
                "priority": "medium",
                "description": "Practicar con contenido más avanzado",
                "estimated_time_minutes": 35,
                "video_count": len(recommendations.get("advanced_practice", []))
            })
        
        return actions
    
    def _generate_initial_recommendation_profile(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        """Generate initial recommendation profile for new users."""
        return {
            "user_id": user_id,
            "subject_id": subject_id,
            "created_at": datetime.utcnow(),
            "recommendation_weights": {"weak_topics": 0.5, "review": 0.3, "challenge": 0.2},
            "preferred_content_types": ["explicativo", "ejercicio_guiado"],
            "learning_pace": "medium",
            "initial_profile": True
        }
    
    def _get_focus_video_recommendations(self, user_id: str, subject_id: str, 
                                       profile: Dict[str, Any], count: int) -> List[Dict]:
        """Get videos focused on weak areas."""
        # This would use the profile to get focused recommendations
        return self._get_videos_for_topics([], content_type="explicativo", difficulty_level=1)[:count]
    
    def _get_review_video_recommendations(self, user_id: str, subject_id: str, 
                                        profile: Dict[str, Any], count: int) -> List[Dict]:
        """Get review videos for reinforcement."""
        return self._get_videos_for_topics([], content_type="resumen", difficulty_level=2)[:count]
    
    def _get_challenge_video_recommendations(self, user_id: str, subject_id: str, 
                                           profile: Dict[str, Any], count: int) -> List[Dict]:
        """Get challenging videos for advanced learners."""
        return self._get_videos_for_topics([], content_type="ejercicio_guiado", difficulty_level=4)[:count]
    
    def _get_adaptive_mixed_recommendations(self, user_id: str, subject_id: str, 
                                          profile: Dict[str, Any], count: int) -> List[Dict]:
        """Get mixed adaptive recommendations."""
        # Mix different types based on profile weights
        weights = profile.get("recommendation_weights", {})
        
        focus_count = int(count * weights.get("weak_topics", 0.4))
        review_count = int(count * weights.get("review", 0.4))
        challenge_count = count - focus_count - review_count
        
        videos = []
        videos.extend(self._get_focus_video_recommendations(user_id, subject_id, profile, focus_count))
        videos.extend(self._get_review_video_recommendations(user_id, subject_id, profile, review_count))
        videos.extend(self._get_challenge_video_recommendations(user_id, subject_id, profile, challenge_count))
        
        # Shuffle for variety
        random.shuffle(videos)
        return videos[:count]
    
    def _track_recommendation_request(self, user_id: str, subject_id: str, 
                                    recommendation_type: str, count: int):
        """Track recommendation requests for analytics."""
        self.logger.info(f"Tracked recommendation request: user={user_id}, type={recommendation_type}, count={count}")
    
    def _store_video_engagement(self, engagement_record: Dict[str, Any]):
        """Store video engagement data."""
        # In a real implementation, store in database
        self.logger.info(f"Stored video engagement for user {engagement_record['user_id']}")
    
    def _update_video_preferences(self, user_id: str, video_id: str, 
                                engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user's video preferences based on engagement."""
        completion_rate = engagement_data.get("completion_rate", 0.0)
        rating = engagement_data.get("rating", None)
        
        preference_changes = {}
        
        if completion_rate > 0.8:
            preference_changes["high_engagement_content"] = engagement_data.get("content_type", "unknown")
        
        if rating and rating >= 4:
            preference_changes["preferred_style"] = engagement_data.get("style", "unknown")
        
        return preference_changes
    
    def _get_engagement_based_suggestions(self, user_id: str, video_id: str, 
                                        engagement_data: Dict[str, Any]) -> List[Dict]:
        """Get next video suggestions based on engagement."""
        # This would analyze engagement patterns and suggest similar content
        return []
    
    def _calculate_engagement_impact(self, engagement_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the impact of video engagement on learning."""
        completion_rate = engagement_data.get("completion_rate", 0.0)
        watch_time = engagement_data.get("watched_duration", 0)
        
        return {
            "learning_impact_score": completion_rate * 0.7 + min(1.0, watch_time / 300) * 0.3,
            "engagement_quality": "high" if completion_rate > 0.8 else "medium" if completion_rate > 0.5 else "low",
            "recommended_follow_up": completion_rate > 0.7
        }
    
    def _get_videos_by_ids(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get videos by their IDs."""
        if not video_ids:
            return []
        
        try:
            placeholders = ','.join([f':id_{i}' for i in range(len(video_ids))])
            query = f"""
                SELECT * FROM youtube_links 
                WHERE id IN ({placeholders}) AND estado = 'activo'
            """
            params = {f'id_{i}': video_id for i, video_id in enumerate(video_ids)}
            
            result = self.db.execute(text(query), params)
            videos = result.fetchall()
            
            return [self._convert_video_to_dict(video) for video in videos]
            
        except Exception as e:
            self.logger.error(f"Error getting videos by IDs: {str(e)}")
            return []
    
    def _convert_video_to_dict(self, video) -> Dict[str, Any]:
        """Convert video database record to dictionary."""
        return {
            'id': str(video.id),
            'youtube_url': video.youtube_url,
            'video_title': video.video_title,
            'channel_name': video.channel_name,
            'duration_seconds': video.duration_seconds,
            'tipo_contenido': video.tipo_contenido,
            'nivel_dificultad': video.nivel_dificultad,
            'puntos_xp': video.puntos_xp
        }
    
    def _check_path_prerequisites(self, user_id: str, segment_data: Dict[str, Any]) -> bool:
        """Check if prerequisites for a path segment are met."""
        # Simplified check - in reality would check completed segments
        return True
    
    def _calculate_path_progress(self, user_id: str, learning_path: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate progress through the learning path."""
        # This would track actual progress through the path
        return {
            "segments_completed": 0,
            "total_segments": len(learning_path.get("path_segments", {})),
            "completion_percentage": 0.0,
            "current_segment": "foundation"
        }
    
    def _update_recommendation_profile(self, user_id: str, subject_id: str, updated_data: Dict[str, Any]):
        """Update recommendation profile with new data."""
        self.logger.info(f"Updated recommendation profile for user {user_id}")
    
    def _analyze_engagement_data(self, user_id: str, subject_id: str, start_date: datetime) -> Dict[str, Any]:
        """Analyze video engagement data for analytics."""
        return {
            "total_videos_watched": 0,
            "average_completion_rate": 0.0,
            "total_watch_time_minutes": 0,
            "favorite_content_types": []
        }
    
    def _calculate_recommendation_effectiveness(self, user_id: str, subject_id: str, 
                                              start_date: datetime) -> Dict[str, Any]:
        """Calculate effectiveness of recommendations."""
        return {
            "click_through_rate": 0.0,
            "completion_rate": 0.0,
            "engagement_score": 0.0,
            "learning_correlation": 0.0
        }
    
    def _analyze_learning_progress_correlation(self, user_id: str, subject_id: str, 
                                             start_date: datetime) -> Dict[str, Any]:
        """Analyze correlation between video consumption and learning progress."""
        return {
            "video_learning_correlation": 0.0,
            "performance_improvement": 0.0,
            "optimal_video_count": 0
        }
    
    def _analyze_content_preferences(self, user_id: str, subject_id: str, 
                                   start_date: datetime) -> Dict[str, Any]:
        """Analyze user's content preferences."""
        return {
            "preferred_duration": "medium",
            "preferred_style": "ejercicio_guiado",
            "preferred_difficulty": 3,
            "engagement_patterns": {}
        }
    
    def _generate_recommendation_insights(self, engagement: Dict, effectiveness: Dict, 
                                        correlation: Dict, preferences: Dict) -> List[str]:
        """Generate insights from analytics data."""
        insights = []
        
        if effectiveness.get("completion_rate", 0) > 0.8:
            insights.append("Excelente nivel de compromiso con las recomendaciones de video")
        
        if correlation.get("video_learning_correlation", 0) > 0.6:
            insights.append("Los videos están correlacionados positivamente con el progreso de aprendizaje")
        
        return insights
    
    # Helper methods for video metadata enhancement
    
    def _calculate_personalization_score(self, video: Dict, profile: Dict) -> float:
        """Calculate how well a video matches user's profile."""
        # Simplified scoring based on content type and difficulty preferences
        base_score = 0.5
        
        preferred_types = profile.get("preferred_content_types", [])
        if video.get("tipo_contenido") in preferred_types:
            base_score += 0.3
        
        return min(1.0, base_score)
    
    def _estimate_engagement_likelihood(self, video: Dict, profile: Dict) -> float:
        """Estimate likelihood of user engagement with video."""
        return random.uniform(0.4, 0.9)  # Placeholder
    
    def _estimate_learning_benefit(self, video: Dict, profile: Dict) -> float:
        """Estimate learning benefit of video for user."""
        return random.uniform(0.5, 1.0)  # Placeholder
    
    def _calculate_optimal_watch_time(self, video: Dict) -> int:
        """Calculate optimal watch time for video."""
        duration = video.get("duration_seconds", 300)
        return min(duration, max(180, int(duration * 0.8)))  # At least 3 min, max 80% of video
    
    def _get_follow_up_suggestions(self, video: Dict) -> List[str]:
        """Get follow-up suggestions after watching video."""
        return ["Practica ejercicios similares", "Ve video de mayor dificultad", "Revisa conceptos relacionados"]
    
    def _calculate_difficulty_match(self, video: Dict, profile: Dict) -> float:
        """Calculate how well video difficulty matches user level."""
        return 0.8  # Placeholder
    
    def _calculate_content_preference_match(self, video: Dict, profile: Dict) -> float:
        """Calculate content preference match."""
        return 0.75  # Placeholder
    
    def _get_timing_recommendation(self, video: Dict) -> str:
        """Get timing recommendation for when to watch video."""
        duration = video.get("duration_seconds", 300)
        if duration < 300:
            return "quick_break"
        elif duration < 600:
            return "focused_session"
        else:
            return "dedicated_study_time"
    
    def _get_segment_description(self, segment_name: str) -> str:
        """Get description for learning path segment."""
        descriptions = {
            "foundation": "Conceptos fundamentales y bases teóricas",
            "basic_practice": "Ejercicios básicos para reforzar fundamentos",
            "skill_building": "Desarrollo de habilidades específicas",
            "targeted_practice": "Práctica enfocada en áreas de mejora",
            "knowledge_review": "Repaso y consolidación de conocimientos",
            "application": "Aplicación práctica de conceptos",
            "advanced_practice": "Ejercicios avanzados y desafiantes",
            "comprehensive_review": "Repaso integral de todos los temas",
            "mastery": "Dominio completo del tema",
            "challenge": "Retos y problemas complejos"
        }
        return descriptions.get(segment_name, "Contenido educativo personalizado")
    
    def _calculate_difficulty_progression(self, path_structure: List[str]) -> List[int]:
        """Calculate difficulty progression through learning path."""
        difficulty_map = {
            "foundation": 1,
            "basic_practice": 2,
            "skill_building": 3,
            "targeted_practice": 3,
            "knowledge_review": 2,
            "application": 4,
            "advanced_practice": 4,
            "comprehensive_review": 3,
            "mastery": 5,
            "challenge": 5
        }
        return [difficulty_map.get(segment, 3) for segment in path_structure]
    
    def _define_adaptive_checkpoints(self, path_structure: List[str]) -> List[Dict[str, Any]]:
        """Define adaptive checkpoints in learning path."""
        checkpoints = []
        for i, segment in enumerate(path_structure):
            if i % 2 == 1:  # Every other segment
                checkpoints.append({
                    "position": i,
                    "segment": segment,
                    "assessment_type": "progress_check",
                    "adaptation_trigger": True
                })
        return checkpoints