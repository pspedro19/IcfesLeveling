"""
Unified Video Progress Tracking Service
Combines and enhances video tracking, analytics, and learning integration from
various legacy enhanced_video_* services.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text, desc, func, case
from datetime import datetime, timedelta
import json
import math
from dataclasses import dataclass, asdict
from enum import Enum

from ..models.user import User
from ..models.video_tracking import VideoTracking # This model needs to be the unified one
from ..models.youtube_video import YoutubeVideo # Placeholder for unified video model
from ..models.youtube_catalog import YoutubeCatalog
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.question_video_recommendations import RecommendationMetrics # If still needed
from ..core.config import settings
from ..services.cache_service import cache_service # If still needed

logger = logging.getLogger(__name__)

# Enums and Dataclasses moved from enhanced_video_progress_service.py
class VideoEventType(Enum):
    PLAY = "play"
    PAUSE = "pause"
    SEEK = "seek"
    COMPLETE = "complete"
    SKIP = "skip"
    REPLAY = "replay"

@dataclass
class VideoAnalyticsData: # Renamed from VideoAnalytics to avoid conflict
    total_watch_time: int
    completion_rate: float
    engagement_score: float
    replay_count: int
    skip_rate: float
    average_session_length: int
    learning_effectiveness: float

@dataclass
class VideoProgressEvent:
    user_id: str
    video_id: str # Refers to a unified video ID
    event_type: VideoEventType
    timestamp: datetime
    current_time: int
    video_duration: int
    session_id: str
    metadata: Dict

@dataclass
class LearningSession:
    session_id: str
    user_id: str
    start_time: datetime
    end_time: Optional[datetime]
    videos_watched: List[str]
    total_time: int
    completion_rate: float
    focus_score: float

class VideoProgressService:
    def __init__(self, db: Session):
        self.db = db
    
    # --- Logic from enhanced_video_progress_service.py ---
    
    async def track_video_event(
        self,
        user_id: str,
        video_id: str, # Assume this is youtube_id or a unified ID
        event_type: VideoEventType,
        current_time: int,
        video_duration: int,
        session_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        try:
            # Need to use the unified VideoTracking model
            video_track = self.db.query(VideoTracking).filter(
                and_(
                    VideoTracking.user_id == user_id,
                    VideoTracking.video_id == video_id # Assuming video_id maps directly
                )
            ).first()
            
            if not video_track:
                # Find video details (assuming unified youtube_catalog/YoutubeVideo)
                video_obj = self.db.query(YoutubeCatalog).filter(
                    YoutubeCatalog.youtube_id == video_id
                ).first()
                if not video_obj:
                    logger.warning(f"Video {video_id} not found in catalog for tracking event")
                    return False
                
                video_track = VideoTracking(
                    user_id=user_id,
                    video_id=video_id,
                    watched_seconds=0,
                    completion_percentage=0.0,
                    engagement_score=0.0,
                    last_watched_at=datetime.utcnow(),
                    total_duration_seconds=video_duration,
                    video_title=video_obj.video_title,
                    channel_name=video_obj.channel_name,
                    youtube_url=video_obj.youtube_url,
                    # Add other necessary fields from video_obj or defaults
                )
                self.db.add(video_track)
                self.db.flush()
            
            # Update tracking based on event type
            self._update_tracking_for_event(
                video_track, event_type, current_time, video_duration, metadata
            )
            
            # Store detailed event (potentially to an events table or as JSONB)
            self._store_video_event(
                user_id, video_id, event_type, current_time, 
                video_duration, session_id, metadata
            )
            
            # Update learning session (simplified)
            self._update_learning_session(
                user_id, session_id, video_id, event_type, current_time
            )
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error tracking video event: {e}")
            self.db.rollback()
            return False
    
    def _update_tracking_for_event(self, video_track: VideoTracking, event_type: VideoEventType,
                                   current_time: int, video_duration: int, metadata: Optional[Dict]):
        if event_type == VideoEventType.PLAY:
            video_track.last_watched_at = datetime.utcnow()
        elif event_type == VideoEventType.COMPLETE:
            video_track.watched_seconds = video_duration # Ensure full duration is marked
            video_track.completion_percentage = 100.0
            video_track.is_completed = True
        elif event_type == VideoEventType.PAUSE or event_type == VideoEventType.SEEK:
            # Update watched time if progressed beyond previous record
            video_track.watched_seconds = max(video_track.watched_seconds or 0, current_time)
            if video_duration > 0:
                video_track.completion_percentage = min(100.0, (video_track.watched_seconds / video_duration) * 100)
        
        if video_track.completion_percentage >= (video_track.completion_threshold or 80.0): # Assuming default 80%
            video_track.is_completed = True
        
        video_track.updated_at = datetime.utcnow()

    def _store_video_event(self, user_id: str, video_id: str, event_type: VideoEventType, current_time: int,
                           video_duration: int, session_id: str, metadata: Optional[Dict]):
        logger.info(f"Video event: User {user_id}, Video {video_id}, Type {event_type.value}, Time {current_time}s")

    def _update_learning_session(self, user_id: str, session_id: str, video_id: str, event_type: VideoEventType,
                                 current_time: int):
        # Placeholder for more sophisticated session tracking
        logger.info(f"Learning session {session_id} update for user {user_id}: video {video_id}, event {event_type.value}")

    async def get_video_analytics(self, user_id: str, video_id: Optional[str] = None, days_back: int = 30) -> VideoAnalyticsData:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = self.db.query(VideoTracking).filter(
            and_(VideoTracking.user_id == user_id, VideoTracking.created_at >= cutoff_date)
        )
        if video_id:
            query = query.filter(VideoTracking.video_id == video_id)
        video_tracks = query.all()
        
        if not video_tracks:
            return VideoAnalyticsData(0, 0.0, 0.0, 0, 0.0, 0, 0.0)
        
        total_watch_time = sum(vt.watched_seconds for vt in video_tracks if vt.watched_seconds is not None)
        completed_videos = sum(1 for vt in video_tracks if vt.is_completed)
        completion_rate = completed_videos / len(video_tracks) if video_tracks else 0
        
        avg_watch_percentage = sum(vt.completion_percentage for vt in video_tracks if vt.completion_percentage is not None) / len(video_tracks)
        engagement_score = min(1.0, avg_watch_percentage / 80.0)
        
        video_ids_list = [vt.video_id for vt in video_tracks]
        unique_videos = len(set(video_ids_list))
        replay_count = len(video_tracks) - unique_videos
        
        skipped_videos = sum(1 for vt in video_tracks if (vt.completion_percentage is not None and vt.completion_percentage < 20))
        skip_rate = skipped_videos / len(video_tracks) if video_tracks else 0
        
        avg_session_length = total_watch_time / len(video_tracks) if video_tracks else 0
        learning_effectiveness = await self._calculate_learning_effectiveness(user_id, video_tracks)
        
        return VideoAnalyticsData(
            total_watch_time, completion_rate, engagement_score, replay_count, skip_rate,
            int(avg_session_length), learning_effectiveness
        )

    async def _calculate_learning_effectiveness(self, user_id: str, video_tracks: List[VideoTracking]) -> float:
        # Simplified - would require matching video topics to quiz/diagnostic performance
        return 0.5 # Default neutral effectiveness

    def _get_performance_before_video(self, user_id: str, video_date: datetime) -> Optional[float]:
        return None # Placeholder for quiz_answers integration

    def _get_performance_after_video(self, user_id: str, video_date: datetime) -> Optional[float]:
        return None # Placeholder for quiz_answers integration

    # --- Logic from enhanced_video_service.py ---
    
    async def track_video_interaction(
        self,
        user_id: str,
        video_id: str, # Assume this is youtube_id
        interaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            video_tracking = self.db.query(VideoTracking).filter(
                and_(VideoTracking.user_id == user_id, VideoTracking.video_id == video_id)
            ).first()
            
            if not video_tracking:
                video_obj = self.db.query(YoutubeCatalog).filter(YoutubeCatalog.youtube_id == video_id).first()
                if not video_obj:
                    logger.warning(f"Video {video_id} not found in catalog for interaction tracking")
                    return {"success": False, "error": "Video not found"}

                video_tracking = VideoTracking(
                    user_id=user_id, video_id=video_id,
                    watched_seconds=0, completion_percentage=0.0, engagement_score=0.0,
                    last_watched_at=datetime.utcnow(), total_duration_seconds=video_obj.duration_seconds,
                    video_title=video_obj.video_title, channel_name=video_obj.channel_name,
                    youtube_url=video_obj.youtube_url
                )
                self.db.add(video_tracking)
            
            # Update tracking data from interaction_data
            current_time = interaction_data.get("current_time", 0)
            total_duration = interaction_data.get("total_duration", video_tracking.total_duration_seconds)
            
            video_tracking.watched_seconds = max(video_tracking.watched_seconds or 0, current_time)
            if total_duration > 0:
                video_tracking.completion_percentage = min(100.0, (video_tracking.watched_seconds / total_duration) * 100)
            
            video_tracking.interaction_history = video_tracking.interaction_history or []
            video_tracking.interaction_history.append({
                "type": interaction_data.get("interaction_type", "watch"),
                "timestamp": datetime.utcnow().isoformat(),
                "current_time": current_time,
                "data": interaction_data
            })
            
            video_tracking.engagement_score = self._calculate_engagement_score_from_interaction(video_tracking, interaction_data)
            
            self.db.commit()

            return {
                "success": True,
                "user_id": user_id,
                "video_id": video_id,
                "updated_metrics": {
                    "watched_seconds": video_tracking.watched_seconds,
                    "completion_percentage": video_tracking.completion_percentage,
                    "engagement_score": video_tracking.engagement_score
                }
            }
            
        except Exception as e:
            logger.error(f"Error tracking video interaction: {str(e)}")
            self.db.rollback()
            return {"success": False, "error": str(e)}

    def _calculate_engagement_score_from_interaction(self, video_tracking: VideoTracking, interaction_data: Dict[str, Any]) -> float:
        completion_rate = video_tracking.completion_percentage / 100
        base_score = completion_rate
        if completion_rate >= 0.95: base_score += 0.1
        return min(1.0, max(0.0, base_score)) # Simplified

    # --- Other methods from enhanced_video_service.py ---
    # These often duplicate functionality or use models not fully defined yet.
    # They would need careful integration into the new orchestrator or dedicated services.
    # For now, prioritizing the core tracking and analytics methods.