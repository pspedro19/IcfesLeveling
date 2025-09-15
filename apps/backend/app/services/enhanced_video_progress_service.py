"""
Enhanced Video Progress Tracking Service
Comprehensive video progress tracking with analytics and learning insights
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, desc, func, case
from datetime import datetime, timedelta
import json
import math
from dataclasses import dataclass
from enum import Enum

from ..models.video_tracking import VideoTracking
from ..models.youtube_catalog import YoutubeCatalog
from ..models.user import User
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.question_video_recommendations import RecommendationMetrics

logger = logging.getLogger(__name__)

class VideoEventType(Enum):
    """Types of video viewing events"""
    PLAY = "play"
    PAUSE = "pause"
    SEEK = "seek"
    COMPLETE = "complete"
    SKIP = "skip"
    REPLAY = "replay"

@dataclass
class VideoAnalytics:
    """Video analytics data"""
    total_watch_time: int
    completion_rate: float
    engagement_score: float
    replay_count: int
    skip_rate: float
    average_session_length: int
    learning_effectiveness: float

@dataclass
class VideoProgressEvent:
    """Individual video progress event"""
    user_id: str
    video_id: str
    event_type: VideoEventType
    timestamp: datetime
    current_time: int
    video_duration: int
    session_id: str
    metadata: Dict

@dataclass
class LearningSession:
    """Learning session with multiple videos"""
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    videos_watched: List[str]
    total_time: int
    completion_rate: float
    focus_score: float

class EnhancedVideoProgressService:
    """
    Enhanced video progress tracking with:
    - Detailed analytics and insights
    - Learning effectiveness measurement
    - Attention and engagement tracking
    - Progress correlation with performance
    - Adaptive recommendations based on viewing patterns
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def track_video_event(
        self,
        user_id: str,
        video_id: str,
        event_type: VideoEventType,
        current_time: int,
        video_duration: int,
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Track detailed video viewing events
        
        Args:
            user_id: Student ID
            video_id: Video identifier
            event_type: Type of event (play, pause, etc.)
            current_time: Current playback time in seconds
            video_duration: Total video duration in seconds
            session_id: Unique session identifier
            metadata: Additional event metadata
            
        Returns:
            Success status
        """
        try:
            # Get or create video tracking record
            video_track = self.db.query(VideoTracking).filter(
                and_(
                    VideoTracking.user_id == user_id,
                    VideoTracking.youtube_url.contains(video_id)  # Flexible matching
                )
            ).first()
            
            if not video_track:
                # Get video details
                video = self.db.query(YoutubeCatalog).filter(
                    or_(
                        YoutubeCatalog.youtube_id == video_id,
                        YoutubeCatalog.id == int(video_id) if video_id.isdigit() else -1
                    )
                ).first()
                
                if not video:
                    logger.warning(f"Video {video_id} not found in catalog")
                    return False
                
                # Create new tracking record
                video_track = VideoTracking(
                    user_id=user_id,
                    plan_id=None,  # Will be set if part of study plan
                    unit_number=1,
                    youtube_url=video.url,
                    video_title=video.title,
                    video_duration_seconds=video_duration or video.duration_seconds,
                    watched_seconds=0,
                    watch_percentage=0.0,
                    is_completed=False
                )
                self.db.add(video_track)
                self.db.flush()
            
            # Update tracking based on event type
            await self._update_tracking_for_event(
                video_track, event_type, current_time, video_duration, metadata
            )
            
            # Store detailed event for analytics
            await self._store_video_event(
                user_id, video_id, event_type, current_time, 
                video_duration, session_id, metadata
            )
            
            # Update learning session
            await self._update_learning_session(
                user_id, session_id, video_id, event_type, current_time
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking video event: {e}")
            self.db.rollback()
            return False
    
    async def _update_tracking_for_event(
        self,
        video_track: VideoTracking,
        event_type: VideoEventType,
        current_time: int,
        video_duration: int,
        metadata: Optional[Dict]
    ):
        """Update video tracking record based on event"""
        
        if event_type == VideoEventType.PLAY:
            video_track.last_watched_at = datetime.utcnow()
            
        elif event_type == VideoEventType.COMPLETE:
            video_track.watched_seconds = max(video_track.watched_seconds, current_time)
            video_track.watch_percentage = min(100.0, (current_time / video_duration) * 100)
            video_track.is_completed = True
            
        elif event_type == VideoEventType.PAUSE:
            # Update watched time if progressed
            if current_time > video_track.watched_seconds:
                video_track.watched_seconds = current_time
                video_track.watch_percentage = (current_time / video_duration) * 100
                
        elif event_type == VideoEventType.SEEK:
            # Don't count seeking as watched time unless it's forward progress
            if current_time > video_track.watched_seconds:
                video_track.watched_seconds = current_time
                video_track.watch_percentage = (current_time / video_duration) * 100
        
        # Check completion threshold
        if video_track.watch_percentage >= video_track.completion_threshold:
            video_track.is_completed = True
        
        video_track.updated_at = datetime.utcnow()
    
    async def _store_video_event(
        self,
        user_id: str,
        video_id: str,
        event_type: VideoEventType,
        current_time: int,
        video_duration: int,
        session_id: str,
        metadata: Optional[Dict]
    ):
        """Store detailed video event for analytics"""
        
        try:
            # Store in a separate events table (would be created)
            # For now, we'll use the existing metadata field to store events
            event_data = {
                'user_id': user_id,
                'video_id': video_id,
                'event_type': event_type.value,
                'current_time': current_time,
                'video_duration': video_duration,
                'session_id': session_id,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            # Could be stored in a dedicated video_events table
            logger.info(f"Video event: {event_data}")
            
        except Exception as e:
            logger.error(f"Error storing video event: {e}")
    
    async def _update_learning_session(
        self,
        user_id: str,
        session_id: str,
        video_id: str,
        event_type: VideoEventType,
        current_time: int
    ):
        """Update learning session data"""
        
        try:
            # This would typically be stored in a sessions table
            # For now, we'll track basic session info
            
            if event_type == VideoEventType.PLAY:
                # Start or continue session
                logger.info(f"Session {session_id}: Video {video_id} started at {current_time}s")
                
            elif event_type == VideoEventType.COMPLETE:
                # Mark video completion in session
                logger.info(f"Session {session_id}: Video {video_id} completed")
                
        except Exception as e:
            logger.error(f"Error updating learning session: {e}")
    
    async def get_video_analytics(
        self,
        user_id: str,
        video_id: Optional[str] = None,
        days_back: int = 30
    ) -> VideoAnalytics:
        """
        Get comprehensive video analytics for a user
        
        Args:
            user_id: Student ID
            video_id: Specific video ID (optional)
            days_back: Number of days to analyze
            
        Returns:
            Video analytics data
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Base query
            query = self.db.query(VideoTracking).filter(
                and_(
                    VideoTracking.user_id == user_id,
                    VideoTracking.created_at >= cutoff_date
                )
            )
            
            if video_id:
                query = query.filter(VideoTracking.youtube_url.contains(video_id))
            
            video_tracks = query.all()
            
            if not video_tracks:
                return VideoAnalytics(
                    total_watch_time=0,
                    completion_rate=0.0,
                    engagement_score=0.0,
                    replay_count=0,
                    skip_rate=0.0,
                    average_session_length=0,
                    learning_effectiveness=0.0
                )
            
            # Calculate analytics
            total_watch_time = sum(vt.watched_seconds for vt in video_tracks)
            completed_videos = sum(1 for vt in video_tracks if vt.is_completed)
            completion_rate = completed_videos / len(video_tracks) if video_tracks else 0
            
            # Calculate engagement score based on watch percentage
            avg_watch_percentage = sum(vt.watch_percentage for vt in video_tracks) / len(video_tracks)
            engagement_score = min(1.0, avg_watch_percentage / 80.0)  # 80% = full engagement
            
            # Estimate replay count (videos watched multiple times)
            video_urls = [vt.youtube_url for vt in video_tracks]
            unique_videos = len(set(video_urls))
            replay_count = len(video_tracks) - unique_videos
            
            # Skip rate (videos with less than 20% completion)
            skipped_videos = sum(1 for vt in video_tracks if vt.watch_percentage < 20)
            skip_rate = skipped_videos / len(video_tracks) if video_tracks else 0
            
            # Average session length
            avg_session_length = total_watch_time / len(video_tracks) if video_tracks else 0
            
            # Learning effectiveness (correlation with performance - simplified)
            learning_effectiveness = await self._calculate_learning_effectiveness(user_id, video_tracks)
            
            return VideoAnalytics(
                total_watch_time=total_watch_time,
                completion_rate=completion_rate,
                engagement_score=engagement_score,
                replay_count=replay_count,
                skip_rate=skip_rate,
                average_session_length=int(avg_session_length),
                learning_effectiveness=learning_effectiveness
            )
            
        except Exception as e:
            logger.error(f"Error getting video analytics: {e}")
            return VideoAnalytics(
                total_watch_time=0,
                completion_rate=0.0,
                engagement_score=0.0,
                replay_count=0,
                skip_rate=0.0,
                average_session_length=0,
                learning_effectiveness=0.0
            )
    
    async def _calculate_learning_effectiveness(
        self,
        user_id: str,
        video_tracks: List[VideoTracking]
    ) -> float:
        """Calculate learning effectiveness based on performance correlation"""
        
        try:
            # Get quiz performance before and after video watching
            effectiveness_scores = []
            
            for vt in video_tracks:
                if not vt.is_completed:
                    continue
                
                # Get performance in topics related to this video
                # This is simplified - in practice, we'd match video topics to questions
                
                before_score = await self._get_performance_before_video(user_id, vt.created_at)
                after_score = await self._get_performance_after_video(user_id, vt.created_at)
                
                if before_score is not None and after_score is not None:
                    improvement = after_score - before_score
                    effectiveness_scores.append(max(0, improvement))
            
            if effectiveness_scores:
                return sum(effectiveness_scores) / len(effectiveness_scores)
            else:
                return 0.5  # Default neutral effectiveness
                
        except Exception as e:
            logger.error(f"Error calculating learning effectiveness: {e}")
            return 0.5
    
    async def _get_performance_before_video(self, user_id: str, video_date: datetime) -> Optional[float]:
        """Get quiz performance before watching video"""
        
        try:
            # Get average score in 7 days before video
            cutoff_date = video_date - timedelta(days=7)
            
            query = text("""
                SELECT AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as avg_score
                FROM quiz_answers 
                WHERE user_id = :user_id 
                    AND answered_at BETWEEN :cutoff_date AND :video_date
            """)
            
            result = self.db.execute(query, {
                'user_id': user_id,
                'cutoff_date': cutoff_date,
                'video_date': video_date
            }).first()
            
            return float(result.avg_score) if result and result.avg_score is not None else None
            
        except Exception as e:
            logger.error(f"Error getting performance before video: {e}")
            return None
    
    async def _get_performance_after_video(self, user_id: str, video_date: datetime) -> Optional[float]:
        """Get quiz performance after watching video"""
        
        try:
            # Get average score in 7 days after video
            end_date = video_date + timedelta(days=7)
            
            query = text("""
                SELECT AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as avg_score
                FROM quiz_answers 
                WHERE user_id = :user_id 
                    AND answered_at BETWEEN :video_date AND :end_date
            """)
            
            result = self.db.execute(query, {
                'user_id': user_id,
                'video_date': video_date,
                'end_date': end_date
            }).first()
            
            return float(result.avg_score) if result and result.avg_score is not None else None
            
        except Exception as e:
            logger.error(f"Error getting performance after video: {e}")
            return None
    
    async def get_learning_sessions(
        self,
        user_id: str,
        days_back: int = 7
    ) -> List[LearningSession]:
        """
        Get learning sessions for analysis
        
        Args:
            user_id: Student ID
            days_back: Number of days to analyze
            
        Returns:
            List of learning sessions
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            # Group video tracking by date to approximate sessions
            query = text("""
                SELECT 
                    DATE(created_at) as session_date,
                    MIN(created_at) as start_time,
                    MAX(last_watched_at) as end_time,
                    COUNT(*) as video_count,
                    SUM(watched_seconds) as total_time,
                    AVG(watch_percentage) as avg_completion,
                    STRING_AGG(DISTINCT youtube_url, ',') as video_urls
                FROM video_tracking 
                WHERE user_id = :user_id 
                    AND created_at >= :cutoff_date
                GROUP BY DATE(created_at)
                ORDER BY session_date DESC
            """)
            
            result = self.db.execute(query, {
                'user_id': user_id,
                'cutoff_date': cutoff_date
            })
            
            sessions = []
            for row in result:
                session = LearningSession(
                    session_id=f"{user_id}_{row.session_date}",
                    user_id=user_id,
                    start_time=row.start_time,
                    end_time=row.end_time,
                    videos_watched=row.video_urls.split(',') if row.video_urls else [],
                    total_time=row.total_time or 0,
                    completion_rate=float(row.avg_completion or 0),
                    focus_score=min(1.0, (row.avg_completion or 0) / 80.0)  # Focus based on completion
                )
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting learning sessions: {e}")
            return []
    
    async def update_study_plan_progress(
        self,
        user_id: str,
        plan_id: str,
        unit_number: int,
        video_completion: bool
    ) -> bool:
        """
        Update study plan progress based on video completion
        
        Args:
            user_id: Student ID
            plan_id: Study plan ID
            unit_number: Unit number
            video_completion: Whether video was completed
            
        Returns:
            Success status
        """
        try:
            # Get unit progress
            unit_progress = self.db.query(PlanProgress).filter(
                and_(
                    PlanProgress.plan_id == plan_id,
                    PlanProgress.unit_number == unit_number
                )
            ).first()
            
            if not unit_progress:
                logger.warning(f"Unit progress not found for plan {plan_id}, unit {unit_number}")
                return False
            
            # Update weighted progress for videos
            weighted_progress = unit_progress.weighted_progress or {
                "videos": {"completed": 0, "total": 0, "weight": 0.3},
                "exercises": {"completed": 0, "total": 0, "weight": 0.5},
                "readings": {"completed": 0, "total": 0, "weight": 0.2}
            }
            
            if video_completion:
                weighted_progress["videos"]["completed"] += 1
            
            # Ensure total is at least as much as completed
            if weighted_progress["videos"]["completed"] > weighted_progress["videos"]["total"]:
                weighted_progress["videos"]["total"] = weighted_progress["videos"]["completed"]
            
            unit_progress.weighted_progress = weighted_progress
            
            # Calculate overall unit completion
            overall_completion = 0.0
            for component, data in weighted_progress.items():
                if data["total"] > 0:
                    component_completion = data["completed"] / data["total"]
                    overall_completion += component_completion * data["weight"]
            
            # Update unit completion status
            if overall_completion >= 0.8:  # 80% threshold
                unit_progress.is_completed = True
                unit_progress.completion_date = datetime.utcnow()
            
            # Update study plan progress
            await self._update_overall_plan_progress(plan_id)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating study plan progress: {e}")
            self.db.rollback()
            return False
    
    async def _update_overall_plan_progress(self, plan_id: str):
        """Update overall study plan progress"""
        
        try:
            # Get all unit progress for this plan
            unit_progresses = self.db.query(PlanProgress).filter(
                PlanProgress.plan_id == plan_id
            ).all()
            
            if not unit_progresses:
                return
            
            # Calculate overall progress
            completed_units = sum(1 for up in unit_progresses if up.is_completed)
            total_units = len(unit_progresses)
            progress_percentage = (completed_units / total_units) * 100
            
            # Update study plan
            study_plan = self.db.query(StudyPlan).filter(
                StudyPlan.id == plan_id
            ).first()
            
            if study_plan:
                study_plan.completed_units = completed_units
                study_plan.progress_percentage = progress_percentage
                study_plan.updated_at = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error updating overall plan progress: {e}")
    
    async def get_video_recommendations_based_on_viewing_patterns(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get video recommendations based on viewing patterns and preferences
        
        Args:
            user_id: Student ID
            limit: Maximum recommendations
            
        Returns:
            List of recommended videos
        """
        try:
            # Analyze viewing patterns
            analytics = await self.get_video_analytics(user_id)
            
            # Get preferred video characteristics
            preferred_duration = analytics.average_session_length
            
            # Find similar videos to those with high completion rates
            high_completion_videos = self.db.query(VideoTracking).filter(
                and_(
                    VideoTracking.user_id == user_id,
                    VideoTracking.watch_percentage >= 80
                )
            ).all()
            
            # Extract topics/channels from successful videos
            successful_channels = []
            for vt in high_completion_videos:
                video = self.db.query(YoutubeCatalog).filter(
                    YoutubeCatalog.url == vt.youtube_url
                ).first()
                if video and video.channel_name:
                    successful_channels.append(video.channel_name)
            
            # Find similar videos
            recommendations = []
            if successful_channels:
                similar_videos = self.db.query(YoutubeCatalog).filter(
                    and_(
                        YoutubeCatalog.channel_name.in_(successful_channels),
                        YoutubeCatalog.duration_seconds.between(
                            max(60, preferred_duration - 300),
                            preferred_duration + 300
                        )
                    )
                ).order_by(YoutubeCatalog.educational_rating.desc()).limit(limit).all()
                
                for video in similar_videos:
                    recommendations.append({
                        'video_id': video.id,
                        'title': video.title,
                        'url': video.url,
                        'duration': video.duration_seconds,
                        'channel': video.channel_name,
                        'reason': 'Based on your viewing preferences',
                        'confidence': 0.8
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting viewing pattern recommendations: {e}")
            return []
    
    async def generate_progress_report(
        self,
        user_id: str,
        period_days: int = 7
    ) -> Dict:
        """
        Generate comprehensive progress report
        
        Args:
            user_id: Student ID
            period_days: Reporting period in days
            
        Returns:
            Detailed progress report
        """
        try:
            analytics = await self.get_video_analytics(user_id, days_back=period_days)
            sessions = await self.get_learning_sessions(user_id, days_back=period_days)
            
            # Calculate trends
            current_analytics = await self.get_video_analytics(user_id, days_back=period_days)
            previous_analytics = await self.get_video_analytics(
                user_id, days_back=period_days * 2
            )
            
            # Calculate improvements
            completion_trend = current_analytics.completion_rate - previous_analytics.completion_rate
            engagement_trend = current_analytics.engagement_score - previous_analytics.engagement_score
            
            report = {
                'period_days': period_days,
                'analytics': {
                    'total_watch_time': analytics.total_watch_time,
                    'completion_rate': round(analytics.completion_rate * 100, 1),
                    'engagement_score': round(analytics.engagement_score * 100, 1),
                    'learning_effectiveness': round(analytics.learning_effectiveness * 100, 1),
                    'average_session_length': analytics.average_session_length
                },
                'trends': {
                    'completion_improvement': round(completion_trend * 100, 1),
                    'engagement_improvement': round(engagement_trend * 100, 1)
                },
                'sessions': {
                    'total_sessions': len(sessions),
                    'average_focus_score': round(sum(s.focus_score for s in sessions) / len(sessions) * 100, 1) if sessions else 0,
                    'most_productive_day': max(sessions, key=lambda s: s.total_time).start_time.strftime('%A') if sessions else None
                },
                'recommendations': [
                    'Increase video completion rate by choosing shorter videos' if analytics.completion_rate < 0.6 else None,
                    'Try watching videos in shorter sessions' if analytics.average_session_length > 1800 else None,
                    'Focus on videos related to your weak topics' if analytics.learning_effectiveness < 0.5 else None
                ]
            }
            
            # Remove None recommendations
            report['recommendations'] = [r for r in report['recommendations'] if r is not None]
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating progress report: {e}")
            return {
                'error': 'Unable to generate progress report',
                'period_days': period_days
            }