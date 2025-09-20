"""
Intelligent Video Recommendations API Routes
Advanced video recommendation endpoints with contextual intelligence
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.intelligent_video_recommendation_service import (
    IntelligentVideoRecommendationService, 
    RecommendationContext
)
from ..services.video_question_matching_service import VideoQuestionMatchingService
from ..services.enhanced_video_progress_service import (
    EnhancedVideoProgressService,
    VideoEventType
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/intelligent-videos", tags=["Intelligent Video Recommendations"])

# Request/Response Models
class VideoEventRequest(BaseModel):
    video_id: str
    event_type: str  # play, pause, seek, complete, skip, replay
    current_time: int
    video_duration: int
    session_id: str
    metadata: Optional[Dict] = None

class PlaylistRequest(BaseModel):
    learning_goal: str
    session_duration: int = 30  # minutes
    difficulty_progression: bool = True

class RecommendationRequest(BaseModel):
    context: str  # study_plan, weakness_remediation, skill_building, review, exploration
    limit: int = 10
    context_data: Optional[Dict] = None

class VideoRecommendationResponse(BaseModel):
    video_id: int
    title: str
    description: Optional[str]
    youtube_id: str
    youtube_url: str
    duration_seconds: Optional[int]
    channel_name: Optional[str]
    thumbnail_url: Optional[str]
    area_evaluada: str
    tema_principal: str
    relevance_score: float
    context: str
    reasoning: str
    learning_objective: str
    estimated_impact: float
    difficulty_match: float
    engagement_prediction: float

class AnalyticsResponse(BaseModel):
    total_watch_time: int
    completion_rate: float
    engagement_score: float
    replay_count: int
    skip_rate: float
    average_session_length: int
    learning_effectiveness: float

@router.get("/recommendations/contextual", response_model=List[VideoRecommendationResponse])
async def get_contextual_recommendations(
    context: str = Query(..., description="Recommendation context"),
    limit: int = Query(10, ge=1, le=50),
    plan_id: Optional[str] = Query(None),
    unit_number: Optional[int] = Query(None),
    topic: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get contextual video recommendations based on specific learning context
    """
    try:
        service = IntelligentVideoRecommendationService(db)
        
        # Map context string to enum
        context_map = {
            'study_plan': RecommendationContext.STUDY_PLAN,
            'weakness_remediation': RecommendationContext.WEAKNESS_REMEDIATION,
            'skill_building': RecommendationContext.SKILL_BUILDING,
            'review': RecommendationContext.REVIEW,
            'exploration': RecommendationContext.EXPLORATION
        }
        
        context_enum = context_map.get(context)
        if not context_enum:
            raise HTTPException(status_code=400, detail="Invalid context")
        
        # Prepare context data
        context_data = {}
        if plan_id:
            context_data['plan_id'] = plan_id
        if unit_number:
            context_data['unit_number'] = unit_number
        if topic:
            context_data['topic'] = topic
        
        # Get recommendations
        recommendations = await service.generate_contextual_recommendations(
            user_id=str(current_user.id),
            context=context_enum,
            limit=limit,
            context_data=context_data if context_data else None
        )
        
        # Convert to response format
        response = []
        for rec in recommendations:
            response.append(VideoRecommendationResponse(
                video_id=rec.video_id,
                title=rec.video.title,
                description=rec.video.description,
                youtube_id=rec.video.youtube_id,
                youtube_url=rec.video.url,
                duration_seconds=rec.video.duration_seconds,
                channel_name=rec.video.channel_name,
                thumbnail_url=rec.video.thumbnail_url,
                area_evaluada=rec.video.area_evaluada,
                tema_principal=rec.video.tema_principal,
                relevance_score=rec.relevance_score,
                context=rec.context.value,
                reasoning=rec.reasoning,
                learning_objective=rec.learning_objective,
                estimated_impact=rec.estimated_impact,
                difficulty_match=rec.difficulty_match,
                engagement_prediction=rec.engagement_prediction
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting contextual recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error generating recommendations")

@router.get("/recommendations/weakness-based", response_model=List[Dict])
async def get_weakness_based_recommendations(
    limit: int = Query(20, ge=1, le=50),
    min_score: float = Query(0.6, ge=0.0, le=1.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get video recommendations based on student's identified weaknesses
    """
    try:
        service = VideoQuestionMatchingService(db)
        
        recommendations = await service.get_recommendations_for_student(
            user_id=str(current_user.id),
            limit=limit,
            min_score=min_score
        )
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "count": len(recommendations),
                "context": "weakness_remediation"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting weakness-based recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error generating weakness-based recommendations")

@router.post("/playlist/generate", response_model=List[VideoRecommendationResponse])
async def generate_learning_playlist(
    request: PlaylistRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a structured learning playlist for a specific goal
    """
    try:
        service = IntelligentVideoRecommendationService(db)
        
        playlist = await service.create_learning_playlist(
            user_id=str(current_user.id),
            learning_goal=request.learning_goal,
            session_duration=request.session_duration,
            difficulty_progression=request.difficulty_progression
        )
        
        # Convert to response format
        response = []
        for rec in playlist:
            response.append(VideoRecommendationResponse(
                video_id=rec.video_id,
                title=rec.video.title,
                description=rec.video.description,
                youtube_id=rec.video.youtube_id,
                youtube_url=rec.video.url,
                duration_seconds=rec.video.duration_seconds,
                channel_name=rec.video.channel_name,
                thumbnail_url=rec.video.thumbnail_url,
                area_evaluada=rec.video.area_evaluada,
                tema_principal=rec.video.tema_principal,
                relevance_score=rec.relevance_score,
                context=rec.context.value,
                reasoning=rec.reasoning,
                learning_objective=rec.learning_objective,
                estimated_impact=rec.estimated_impact,
                difficulty_match=rec.difficulty_match,
                engagement_prediction=rec.engagement_prediction
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating playlist: {e}")
        raise HTTPException(status_code=500, detail="Error generating learning playlist")

@router.post("/events/track")
async def track_video_event(
    request: VideoEventRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track detailed video viewing events for analytics and recommendations
    """
    try:
        service = EnhancedVideoProgressService(db)
        
        # Map event type string to enum
        event_type_map = {
            'play': VideoEventType.PLAY,
            'pause': VideoEventType.PAUSE,
            'seek': VideoEventType.SEEK,
            'complete': VideoEventType.COMPLETE,
            'skip': VideoEventType.SKIP,
            'replay': VideoEventType.REPLAY
        }
        
        event_type = event_type_map.get(request.event_type)
        if not event_type:
            raise HTTPException(status_code=400, detail="Invalid event type")
        
        success = await service.track_video_event(
            user_id=str(current_user.id),
            video_id=request.video_id,
            event_type=event_type,
            current_time=request.current_time,
            video_duration=request.video_duration,
            session_id=request.session_id,
            metadata=request.metadata
        )
        
        return {
            "success": success,
            "message": "Video event tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error tracking video event: {e}")
        raise HTTPException(status_code=500, detail="Error tracking video event")

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_video_analytics(
    video_id: Optional[str] = Query(None),
    days_back: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive video analytics for the user
    """
    try:
        service = EnhancedVideoProgressService(db)
        
        analytics = await service.get_video_analytics(
            user_id=str(current_user.id),
            video_id=video_id,
            days_back=days_back
        )
        
        return AnalyticsResponse(
            total_watch_time=analytics.total_watch_time,
            completion_rate=analytics.completion_rate,
            engagement_score=analytics.engagement_score,
            replay_count=analytics.replay_count,
            skip_rate=analytics.skip_rate,
            average_session_length=analytics.average_session_length,
            learning_effectiveness=analytics.learning_effectiveness
        )
        
    except Exception as e:
        logger.error(f"Error getting video analytics: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving video analytics")

@router.get("/analytics/sessions")
async def get_learning_sessions(
    days_back: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get learning sessions analysis
    """
    try:
        service = EnhancedVideoProgressService(db)
        
        sessions = await service.get_learning_sessions(
            user_id=str(current_user.id),
            days_back=days_back
        )
        
        session_data = []
        for session in sessions:
            session_data.append({
                "session_id": session.session_id,
                "start_time": session.start_time.isoformat(),
                "end_time": session.end_time.isoformat() if session.end_time else None,
                "videos_watched": len(session.videos_watched),
                "total_time": session.total_time,
                "completion_rate": session.completion_rate,
                "focus_score": session.focus_score
            })
        
        return {
            "success": True,
            "data": {
                "sessions": session_data,
                "total_sessions": len(sessions),
                "period_days": days_back
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting learning sessions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving learning sessions")

@router.get("/analytics/progress-report")
async def get_progress_report(
    period_days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive progress report with insights and recommendations
    """
    try:
        service = EnhancedVideoProgressService(db)
        
        report = await service.generate_progress_report(
            user_id=str(current_user.id),
            period_days=period_days
        )
        
        return {
            "success": True,
            "data": report
        }
        
    except Exception as e:
        logger.error(f"Error generating progress report: {e}")
        raise HTTPException(status_code=500, detail="Error generating progress report")

@router.get("/recommendations/viewing-patterns")
async def get_viewing_pattern_recommendations(
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recommendations based on viewing patterns and preferences
    """
    try:
        service = EnhancedVideoProgressService(db)
        
        recommendations = await service.get_video_recommendations_based_on_viewing_patterns(
            user_id=str(current_user.id),
            limit=limit
        )
        
        return {
            "success": True,
            "data": {
                "recommendations": recommendations,
                "count": len(recommendations),
                "context": "viewing_patterns"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting viewing pattern recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error generating viewing pattern recommendations")

@router.post("/study-plan/update-progress")
async def update_study_plan_progress(
    plan_id: str,
    unit_number: int,
    video_completed: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update study plan progress based on video completion
    """
    try:
        service = EnhancedVideoProgressService(db)
        
        success = await service.update_study_plan_progress(
            user_id=str(current_user.id),
            plan_id=plan_id,
            unit_number=unit_number,
            video_completion=video_completed
        )
        
        return {
            "success": success,
            "message": "Study plan progress updated"
        }
        
    except Exception as e:
        logger.error(f"Error updating study plan progress: {e}")
        raise HTTPException(status_code=500, detail="Error updating study plan progress")

@router.post("/recommendations/track-interaction")
async def track_recommendation_interaction(
    recommendation_id: int,
    interaction_type: str,  # click, watch, complete, rate
    metadata: Optional[Dict] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track user interaction with video recommendations
    """
    try:
        service = VideoQuestionMatchingService(db)
        
        success = await service.track_recommendation_interaction(
            recommendation_id=recommendation_id,
            user_id=str(current_user.id),
            interaction_type=interaction_type,
            metadata=metadata
        )
        
        return {
            "success": success,
            "message": "Interaction tracked successfully"
        }
        
    except Exception as e:
        logger.error(f"Error tracking recommendation interaction: {e}")
        raise HTTPException(status_code=500, detail="Error tracking interaction")

@router.get("/student-profile")
async def get_student_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive student learning profile for video recommendations
    """
    try:
        service = IntelligentVideoRecommendationService(db)
        
        profile = await service.build_student_profile(str(current_user.id))
        
        return {
            "success": True,
            "data": {
                "user_id": profile.user_id,
                "learning_style": profile.learning_style,
                "performance_level": profile.performance_level,
                "weak_topics": profile.weak_topics,
                "strong_topics": profile.strong_topics,
                "preferred_video_duration": profile.preferred_video_duration,
                "attention_span": profile.attention_span,
                "learning_pace": profile.learning_pace,
                "last_activity": profile.last_activity.isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting student profile: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving student profile")

@router.get("/weaknesses/analyze")
async def analyze_student_weaknesses(
    days_lookback: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Analyze student weaknesses for targeted video recommendations
    """
    try:
        service = VideoQuestionMatchingService(db)
        
        weaknesses = await service.analyze_student_weaknesses(
            user_id=str(current_user.id),
            days_lookback=days_lookback
        )
        
        weakness_data = []
        for weakness in weaknesses:
            weakness_data.append({
                "question_id": weakness.question_id,
                "topic_id": weakness.topic_id,
                "subject_id": weakness.subject_id,
                "error_pattern": weakness.error_pattern,
                "distractor_chosen": weakness.distractor_chosen,
                "difficulty_level": weakness.difficulty_level,
                "frequency": weakness.frequency,
                "last_failed": weakness.last_failed.isoformat()
            })
        
        return {
            "success": True,
            "data": {
                "weaknesses": weakness_data,
                "total_weaknesses": len(weaknesses),
                "analysis_period": days_lookback
            }
        }
        
    except Exception as e:
        logger.error(f"Error analyzing student weaknesses: {e}")
        raise HTTPException(status_code=500, detail="Error analyzing weaknesses")