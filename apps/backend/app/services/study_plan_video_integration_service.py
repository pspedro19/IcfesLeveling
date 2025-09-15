"""
Study Plan Video Integration Service
Integrates intelligent video recommendations into study plans and training zones
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, desc, func
from datetime import datetime, timedelta
import json

from .intelligent_video_recommendation_service import (
    IntelligentVideoRecommendationService, 
    RecommendationContext
)
from .video_question_matching_service import VideoQuestionMatchingService
from .enhanced_video_progress_service import EnhancedVideoProgressService
from ..models.study_plan import StudyPlan, PlanProgress, StudyPlanTemplate
from ..models.youtube_catalog import YoutubeCatalog
from ..models.video_tracking import VideoTracking
from ..models.user import User

logger = logging.getLogger(__name__)

class StudyPlanVideoIntegrationService:
    """
    Service for integrating video recommendations into study plans and training zones
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.recommendation_service = IntelligentVideoRecommendationService(db)
        self.matching_service = VideoQuestionMatchingService(db)
        self.progress_service = EnhancedVideoProgressService(db)
    
    async def enhance_study_plan_with_videos(
        self,
        plan_id: str,
        user_id: str
    ) -> Dict:
        """
        Enhance an existing study plan with intelligent video recommendations
        
        Args:
            plan_id: Study plan ID
            user_id: Student ID
            
        Returns:
            Enhanced study plan with video content
        """
        try:
            # Get study plan
            plan = self.db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
            if not plan:
                raise ValueError(f"Study plan {plan_id} not found")
            
            # Get plan progress/units
            units = self.db.query(PlanProgress).filter(
                PlanProgress.plan_id == plan_id
            ).order_by(PlanProgress.unit_number).all()
            
            enhanced_units = []
            for unit in units:
                enhanced_unit = await self._enhance_unit_with_videos(unit, user_id)
                enhanced_units.append(enhanced_unit)
            
            # Update plan data with video content
            plan_data = plan.plan_data or {}
            plan_data['enhanced_with_videos'] = True
            plan_data['video_enhancement_date'] = datetime.utcnow().isoformat()
            plan_data['units'] = enhanced_units
            
            plan.plan_data = plan_data
            plan.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            return {
                "success": True,
                "plan_id": plan_id,
                "enhanced_units": len(enhanced_units),
                "total_videos_added": sum(len(unit.get('videos', [])) for unit in enhanced_units)
            }
            
        except Exception as e:
            logger.error(f"Error enhancing study plan with videos: {e}")
            self.db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _enhance_unit_with_videos(
        self,
        unit: PlanProgress,
        user_id: str
    ) -> Dict:
        """
        Enhance a single study plan unit with video recommendations
        
        Args:
            unit: Plan progress unit
            user_id: Student ID
            
        Returns:
            Enhanced unit data with videos
        """
        try:
            unit_content = unit.unit_content or {}
            focus_topics = unit_content.get('focus_topics', [])
            weak_areas = unit_content.get('weak_areas', [])
            
            # Get contextual video recommendations for this unit
            videos = await self.recommendation_service.generate_contextual_recommendations(
                user_id=user_id,
                context=RecommendationContext.STUDY_PLAN,
                limit=5,
                context_data={
                    'plan_id': str(unit.plan_id),
                    'unit_number': unit.unit_number,
                    'focus_topics': focus_topics,
                    'weak_areas': weak_areas
                }
            )
            
            # Convert video recommendations to unit format
            unit_videos = []
            for video_rec in videos:
                video_data = {
                    'id': video_rec.video_id,
                    'title': video_rec.video.title,
                    'youtube_id': video_rec.video.youtube_id,
                    'youtube_url': video_rec.video.url,
                    'duration_seconds': video_rec.video.duration_seconds,
                    'channel_name': video_rec.video.channel_name,
                    'thumbnail_url': video_rec.video.thumbnail_url,
                    'description': video_rec.video.description,
                    'area_evaluada': video_rec.video.area_evaluada,
                    'tema_principal': video_rec.video.tema_principal,
                    'relevance_score': video_rec.relevance_score,
                    'learning_objective': video_rec.learning_objective,
                    'reasoning': video_rec.reasoning,
                    'estimated_impact': video_rec.estimated_impact,
                    'difficulty_match': video_rec.difficulty_match,
                    'engagement_prediction': video_rec.engagement_prediction,
                    'is_required': video_rec.relevance_score > 0.8,  # High relevance = required
                    'order': len(unit_videos) + 1
                }
                unit_videos.append(video_data)
            
            # Update unit content with videos
            enhanced_content = unit_content.copy()
            enhanced_content['videos'] = unit_videos
            enhanced_content['video_count'] = len(unit_videos)
            enhanced_content['required_videos'] = sum(1 for v in unit_videos if v['is_required'])
            
            # Update weighted progress to include videos
            weighted_progress = unit.weighted_progress or {
                "videos": {"completed": 0, "total": 0, "weight": 0.3},
                "exercises": {"completed": 0, "total": 0, "weight": 0.5},
                "readings": {"completed": 0, "total": 0, "weight": 0.2}
            }
            
            # Update video metrics
            weighted_progress["videos"]["total"] = len(unit_videos)
            
            # Check existing video progress
            completed_videos = await self._count_completed_videos_in_unit(user_id, unit_videos)
            weighted_progress["videos"]["completed"] = completed_videos
            
            # Save enhanced unit content
            unit.unit_content = enhanced_content
            unit.weighted_progress = weighted_progress
            
            return {
                "unit_number": unit.unit_number,
                "unit_name": unit.unit_name,
                "videos": unit_videos,
                "video_count": len(unit_videos),
                "required_videos": enhanced_content['required_videos'],
                "focus_topics": focus_topics,
                "weak_areas": weak_areas
            }
            
        except Exception as e:
            logger.error(f"Error enhancing unit {unit.unit_number} with videos: {e}")
            return {
                "unit_number": unit.unit_number,
                "unit_name": unit.unit_name,
                "videos": [],
                "video_count": 0,
                "error": str(e)
            }
    
    async def _count_completed_videos_in_unit(
        self,
        user_id: str,
        unit_videos: List[Dict]
    ) -> int:
        """Count how many videos in the unit have been completed by the user"""
        
        try:
            completed_count = 0
            
            for video in unit_videos:
                # Check if user has completed this video
                video_track = self.db.query(VideoTracking).filter(
                    and_(
                        VideoTracking.user_id == user_id,
                        or_(
                            VideoTracking.youtube_url == video['youtube_url'],
                            VideoTracking.youtube_url.contains(video['youtube_id'])
                        ),
                        VideoTracking.is_completed == True
                    )
                ).first()
                
                if video_track:
                    completed_count += 1
            
            return completed_count
            
        except Exception as e:
            logger.error(f"Error counting completed videos: {e}")
            return 0
    
    async def generate_video_study_session(
        self,
        user_id: str,
        session_duration: int = 45,  # minutes
        focus_areas: Optional[List[str]] = None
    ) -> Dict:
        """
        Generate a video-based study session with intelligent sequencing
        
        Args:
            user_id: Student ID
            session_duration: Available time in minutes
            focus_areas: Specific areas to focus on
            
        Returns:
            Structured video study session
        """
        try:
            # Get student profile for personalization
            profile = await self.recommendation_service.build_student_profile(user_id)
            
            # Create learning playlist
            learning_goal = f"Focused study session on {', '.join(focus_areas)}" if focus_areas else "Comprehensive study session"
            
            playlist = await self.recommendation_service.create_learning_playlist(
                user_id=user_id,
                learning_goal=learning_goal,
                session_duration=session_duration,
                difficulty_progression=True
            )
            
            # Organize session structure
            session_structure = {
                "session_id": f"session_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "duration_minutes": session_duration,
                "focus_areas": focus_areas or [],
                "generated_at": datetime.utcnow().isoformat(),
                "videos": [],
                "phases": {
                    "warmup": [],      # Easy review videos (20%)
                    "learning": [],    # New content videos (60%)
                    "practice": []     # Application videos (20%)
                }
            }
            
            # Distribute videos across phases
            total_time = 0
            warmup_time = session_duration * 0.2 * 60  # 20% in seconds
            learning_time = session_duration * 0.6 * 60  # 60% in seconds
            practice_time = session_duration * 0.2 * 60  # 20% in seconds
            
            current_phase = "warmup"
            phase_time = warmup_time
            
            for video_rec in playlist:
                video_duration = video_rec.video.duration_seconds or 600
                
                if total_time + video_duration > phase_time:
                    # Move to next phase
                    if current_phase == "warmup":
                        current_phase = "learning"
                        phase_time = learning_time
                        total_time = 0
                    elif current_phase == "learning":
                        current_phase = "practice"
                        phase_time = practice_time
                        total_time = 0
                    else:
                        break  # Session full
                
                video_data = {
                    "id": video_rec.video_id,
                    "title": video_rec.video.title,
                    "youtube_id": video_rec.video.youtube_id,
                    "youtube_url": video_rec.video.url,
                    "duration_seconds": video_duration,
                    "channel_name": video_rec.video.channel_name,
                    "thumbnail_url": video_rec.video.thumbnail_url,
                    "description": video_rec.video.description,
                    "learning_objective": video_rec.learning_objective,
                    "reasoning": video_rec.reasoning,
                    "phase": current_phase,
                    "order": len(session_structure["videos"]) + 1,
                    "estimated_impact": video_rec.estimated_impact,
                    "engagement_prediction": video_rec.engagement_prediction
                }
                
                session_structure["videos"].append(video_data)
                session_structure["phases"][current_phase].append(video_data)
                total_time += video_duration
            
            # Add session metadata
            session_structure["total_videos"] = len(session_structure["videos"])
            session_structure["estimated_duration"] = sum(v["duration_seconds"] for v in session_structure["videos"]) // 60
            session_structure["difficulty_progression"] = True
            session_structure["personalized"] = True
            
            return {
                "success": True,
                "session": session_structure
            }
            
        except Exception as e:
            logger.error(f"Error generating video study session: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def integrate_videos_into_training_zone(
        self,
        user_id: str,
        subject_id: str,
        difficulty_level: str = "adaptive"
    ) -> Dict:
        """
        Integrate video recommendations into training zone based on recent performance
        
        Args:
            user_id: Student ID
            subject_id: Subject ID
            difficulty_level: Target difficulty level
            
        Returns:
            Training zone video integration
        """
        try:
            # Analyze recent weaknesses for training zone
            weaknesses = await self.matching_service.analyze_student_weaknesses(user_id, days_lookback=7)
            
            # Get weakness-based recommendations
            weakness_videos = await self.recommendation_service.generate_contextual_recommendations(
                user_id=user_id,
                context=RecommendationContext.WEAKNESS_REMEDIATION,
                limit=10
            )
            
            # Get skill building videos
            skill_videos = await self.recommendation_service.generate_contextual_recommendations(
                user_id=user_id,
                context=RecommendationContext.SKILL_BUILDING,
                limit=5
            )
            
            # Organize videos by training focus
            training_integration = {
                "user_id": user_id,
                "subject_id": subject_id,
                "generated_at": datetime.utcnow().isoformat(),
                "weakness_remediation": {
                    "videos": self._format_videos_for_training(weakness_videos),
                    "focus": "Address identified weaknesses",
                    "priority": "high"
                },
                "skill_building": {
                    "videos": self._format_videos_for_training(skill_videos),
                    "focus": "Build on strengths",
                    "priority": "medium"
                },
                "adaptive_recommendations": {
                    "videos": [],
                    "focus": "Dynamic difficulty adjustment",
                    "priority": "adaptive"
                }
            }
            
            # Add adaptive recommendations based on performance
            if difficulty_level == "adaptive":
                adaptive_videos = await self._get_adaptive_training_videos(user_id, subject_id)
                training_integration["adaptive_recommendations"]["videos"] = adaptive_videos
            
            return {
                "success": True,
                "training_integration": training_integration,
                "total_videos": sum(len(section["videos"]) for section in training_integration.values() if isinstance(section, dict) and "videos" in section)
            }
            
        except Exception as e:
            logger.error(f"Error integrating videos into training zone: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _format_videos_for_training(self, video_recommendations: List) -> List[Dict]:
        """Format video recommendations for training zone display"""
        
        formatted_videos = []
        for video_rec in video_recommendations:
            formatted_videos.append({
                "id": video_rec.video_id,
                "title": video_rec.video.title,
                "youtube_id": video_rec.video.youtube_id,
                "youtube_url": video_rec.video.url,
                "duration_seconds": video_rec.video.duration_seconds,
                "channel_name": video_rec.video.channel_name,
                "thumbnail_url": video_rec.video.thumbnail_url,
                "area_evaluada": video_rec.video.area_evaluada,
                "tema_principal": video_rec.video.tema_principal,
                "relevance_score": video_rec.relevance_score,
                "learning_objective": video_rec.learning_objective,
                "reasoning": video_rec.reasoning,
                "difficulty_match": video_rec.difficulty_match,
                "engagement_prediction": video_rec.engagement_prediction,
                "context": video_rec.context.value
            })
        
        return formatted_videos
    
    async def _get_adaptive_training_videos(
        self,
        user_id: str,
        subject_id: str
    ) -> List[Dict]:
        """Get adaptive videos based on recent training performance"""
        
        try:
            # Get videos with dynamic difficulty based on recent performance
            adaptive_videos = await self.recommendation_service.generate_contextual_recommendations(
                user_id=user_id,
                context=RecommendationContext.SKILL_BUILDING,
                limit=5,
                context_data={
                    "subject_id": subject_id,
                    "adaptive": True
                }
            )
            
            return self._format_videos_for_training(adaptive_videos)
            
        except Exception as e:
            logger.error(f"Error getting adaptive training videos: {e}")
            return []
    
    async def track_training_zone_video_completion(
        self,
        user_id: str,
        video_id: str,
        training_context: str,
        completion_percentage: float
    ) -> Dict:
        """
        Track video completion in training zone and update adaptive recommendations
        
        Args:
            user_id: Student ID
            video_id: Video ID
            training_context: Training context (weakness_remediation, skill_building, etc.)
            completion_percentage: Percentage of video completed
            
        Returns:
            Tracking result and updated recommendations
        """
        try:
            # Track the video completion
            success = await self.progress_service.track_video_event(
                user_id=user_id,
                video_id=video_id,
                event_type="complete" if completion_percentage >= 80 else "pause",
                current_time=0,  # Would be provided by frontend
                video_duration=0,  # Would be provided by frontend
                session_id=f"training_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
                metadata={
                    "training_context": training_context,
                    "completion_percentage": completion_percentage
                }
            )
            
            # Update adaptive recommendations if needed
            updated_recommendations = None
            if completion_percentage >= 80:  # Video completed successfully
                updated_recommendations = await self._update_adaptive_recommendations(
                    user_id, video_id, training_context
                )
            
            return {
                "success": success,
                "tracking_completed": True,
                "updated_recommendations": updated_recommendations
            }
            
        except Exception as e:
            logger.error(f"Error tracking training zone video completion: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_adaptive_recommendations(
        self,
        user_id: str,
        completed_video_id: str,
        training_context: str
    ) -> Optional[List[Dict]]:
        """Update adaptive recommendations based on completed video"""
        
        try:
            # This would implement logic to adjust future recommendations
            # based on successful video completion
            
            # For now, return None indicating no immediate updates
            return None
            
        except Exception as e:
            logger.error(f"Error updating adaptive recommendations: {e}")
            return None
    
    async def get_study_plan_video_progress(
        self,
        plan_id: str,
        user_id: str
    ) -> Dict:
        """
        Get comprehensive video progress for a study plan
        
        Args:
            plan_id: Study plan ID
            user_id: Student ID
            
        Returns:
            Detailed progress information
        """
        try:
            # Get plan units
            units = self.db.query(PlanProgress).filter(
                PlanProgress.plan_id == plan_id
            ).order_by(PlanProgress.unit_number).all()
            
            total_videos = 0
            completed_videos = 0
            unit_progress = []
            
            for unit in units:
                unit_content = unit.unit_content or {}
                videos = unit_content.get('videos', [])
                
                unit_completed = 0
                for video in videos:
                    total_videos += 1
                    
                    # Check if video is completed
                    video_track = self.db.query(VideoTracking).filter(
                        and_(
                            VideoTracking.user_id == user_id,
                            or_(
                                VideoTracking.youtube_url == video['youtube_url'],
                                VideoTracking.youtube_url.contains(video['youtube_id'])
                            ),
                            VideoTracking.is_completed == True
                        )
                    ).first()
                    
                    if video_track:
                        completed_videos += 1
                        unit_completed += 1
                
                unit_progress.append({
                    "unit_number": unit.unit_number,
                    "unit_name": unit.unit_name,
                    "total_videos": len(videos),
                    "completed_videos": unit_completed,
                    "completion_rate": unit_completed / len(videos) if videos else 0
                })
            
            overall_completion = completed_videos / total_videos if total_videos > 0 else 0
            
            return {
                "plan_id": plan_id,
                "total_videos": total_videos,
                "completed_videos": completed_videos,
                "overall_completion_rate": overall_completion,
                "unit_progress": unit_progress,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting study plan video progress: {e}")
            return {
                "plan_id": plan_id,
                "error": str(e)
            }