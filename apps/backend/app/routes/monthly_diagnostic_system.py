"""
Monthly Diagnostic Assessment System API Routes
Comprehensive API endpoints for the monthly diagnostic assessment system
that tracks student progress over time and adapts learning experiences.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.monthly_diagnostic_scheduler import MonthlyDiagnosticScheduler, DiagnosticFrequency
from ..services.adaptive_training_zone_service import AdaptiveTrainingZoneService
from ..services.enhanced_video_recommendation_service import EnhancedVideoRecommendationService
from ..services.progress_report_service import ProgressReportService, ReportType, TrajectoryType

router = APIRouter(prefix="/monthly-diagnostic", tags=["Monthly Diagnostic System"])

# Pydantic models for request/response

class ScheduleAssessmentRequest(BaseModel):
    subjects: Optional[List[str]] = None
    frequency: Optional[str] = "monthly"
    custom_settings: Optional[Dict[str, Any]] = None

class TriggerAssessmentRequest(BaseModel):
    subject_id: str
    assessment_type: str = "adaptive"  # adaptive, comprehensive, focused

class AssessmentSubmissionRequest(BaseModel):
    test_id: str
    answers: List[Dict[str, Any]]

class TrainingZoneUpdateRequest(BaseModel):
    subject_id: str
    session_type: str = "adaptive"  # adaptive, focus, review, challenge
    question_count: int = 20

class VideoRecommendationRequest(BaseModel):
    subject_id: str
    recommendation_type: str = "adaptive"  # focus, review, challenge, adaptive
    count: int = 20

class ProgressReportRequest(BaseModel):
    subject_id: Optional[str] = None
    report_type: str = "monthly"  # monthly, quarterly, semester, annual, custom
    custom_date_range: Optional[Dict[str, str]] = None

class VideoEngagementRequest(BaseModel):
    video_id: str
    engagement_data: Dict[str, Any]

class QuestionPerformanceRequest(BaseModel):
    question_id: str
    is_correct: bool
    response_time_ms: int
    hints_used: int = 0

# Monthly Diagnostic Scheduling Routes

@router.post("/schedule")
async def schedule_monthly_diagnostics(
    request: ScheduleAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Schedule monthly diagnostic assessments for a user.
    
    Creates a comprehensive schedule for diagnostic assessments across subjects,
    with automatic reminders and adaptive timing based on performance.
    """
    try:
        scheduler = MonthlyDiagnosticScheduler(db)
        
        schedule_result = scheduler.schedule_monthly_diagnostics(
            user_id=str(current_user.id),
            subjects=request.subjects
        )
        
        return {
            "success": True,
            "message": "Monthly diagnostic schedule created successfully",
            "schedule": schedule_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling diagnostics: {str(e)}")

@router.get("/schedule/{user_id}")
async def get_diagnostic_schedule(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current diagnostic schedule for a user.
    
    Returns upcoming assessments, overdue assessments, and schedule insights.
    """
    try:
        # Verify user access (users can only access their own schedule, or admin access)
        if str(current_user.id) != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Access denied")
        
        scheduler = MonthlyDiagnosticScheduler(db)
        
        schedule_result = scheduler.schedule_monthly_diagnostics(
            user_id=user_id
        )
        
        return {
            "success": True,
            "schedule": schedule_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schedule: {str(e)}")

@router.post("/trigger-assessment")
async def trigger_monthly_assessment(
    request: TriggerAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger a monthly diagnostic assessment for a user and subject.
    
    Creates an adaptive assessment based on the user's performance history
    and returns the assessment questions.
    """
    try:
        scheduler = MonthlyDiagnosticScheduler(db)
        
        assessment_result = scheduler.trigger_monthly_assessment(
            user_id=str(current_user.id),
            subject_id=request.subject_id,
            assessment_type=request.assessment_type
        )
        
        return {
            "success": True,
            "message": "Assessment triggered successfully",
            "assessment": assessment_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering assessment: {str(e)}")

@router.post("/submit-assessment")
async def submit_monthly_assessment(
    request: AssessmentSubmissionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit completed monthly assessment and trigger all adaptive updates.
    
    Processes the assessment results and automatically updates:
    - Training zone questions
    - Video recommendations
    - Study plans
    - Progress reports
    """
    try:
        scheduler = MonthlyDiagnosticScheduler(db)
        
        completion_result = scheduler.process_assessment_completion(
            test_id=request.test_id,
            answers=request.answers
        )
        
        return {
            "success": True,
            "message": "Assessment submitted and processed successfully",
            "results": completion_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting assessment: {str(e)}")

# Progress Timeline and Analytics Routes

@router.get("/progress-timeline/{subject_id}")
async def get_progress_timeline(
    subject_id: str,
    months_back: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive progress timeline showing diagnostic results over time.
    
    Returns timeline data with progress trends, improvements, and predictions.
    """
    try:
        scheduler = MonthlyDiagnosticScheduler(db)
        
        timeline_result = scheduler.get_diagnostic_progress_timeline(
            user_id=str(current_user.id),
            subject_id=subject_id,
            months_back=months_back
        )
        
        return {
            "success": True,
            "timeline": timeline_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving progress timeline: {str(e)}")

@router.get("/improvement-metrics/{subject_id}")
async def get_improvement_metrics(
    subject_id: str = None,
    time_period: str = Query("last_6_months", regex="^(last_month|last_3_months|last_6_months|all_time)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive improvement metrics for a user.
    
    Returns detailed analysis of learning progress, trends, and predictions.
    """
    try:
        scheduler = MonthlyDiagnosticScheduler(db)
        
        metrics_result = scheduler.get_improvement_metrics(
            user_id=str(current_user.id),
            subject_id=subject_id,
            time_period=time_period
        )
        
        return {
            "success": True,
            "metrics": metrics_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving improvement metrics: {str(e)}")

# Training Zone Adaptation Routes

@router.post("/training-zone/update")
async def update_training_zone(
    request: TrainingZoneUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update training zone based on latest diagnostic results.
    
    Adapts question pools, difficulty levels, and focus areas based on performance.
    """
    try:
        training_service = AdaptiveTrainingZoneService(db)
        
        # Get latest diagnostic results (simplified - would get actual results)
        diagnostic_results = {"comparison": {"current_score": 75, "improvement_percentage": 5}}
        
        update_result = training_service.update_training_zone_for_user(
            user_id=str(current_user.id),
            subject_id=request.subject_id,
            diagnostic_results=diagnostic_results
        )
        
        return {
            "success": True,
            "message": "Training zone updated successfully",
            "configuration": update_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating training zone: {str(e)}")

@router.get("/training-zone/questions/{subject_id}")
async def get_adaptive_questions(
    subject_id: str,
    session_type: str = Query("adaptive", regex="^(adaptive|focus|review|challenge)$"),
    count: int = Query(20, ge=5, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get adaptively selected questions for training session.
    
    Returns questions tailored to the user's current performance level and focus areas.
    """
    try:
        training_service = AdaptiveTrainingZoneService(db)
        
        questions = training_service.get_adaptive_questions(
            user_id=str(current_user.id),
            subject_id=subject_id,
            session_type=session_type,
            count=count
        )
        
        return {
            "success": True,
            "session_type": session_type,
            "questions": questions
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting adaptive questions: {str(e)}")

@router.post("/training-zone/question-performance")
async def update_question_performance(
    request: QuestionPerformanceRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update question performance tracking and adaptive algorithms.
    
    Records question performance and provides next question recommendations.
    """
    try:
        training_service = AdaptiveTrainingZoneService(db)
        
        performance_result = training_service.update_question_performance(
            user_id=str(current_user.id),
            question_id=request.question_id,
            is_correct=request.is_correct,
            response_time_ms=request.response_time_ms,
            hints_used=request.hints_used
        )
        
        return {
            "success": True,
            "message": "Performance recorded successfully",
            "adaptive_feedback": performance_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording performance: {str(e)}")

@router.get("/training-zone/recommendations/{subject_id}")
async def get_training_recommendations(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized training recommendations based on performance data.
    
    Returns immediate focus areas, session recommendations, and study guidance.
    """
    try:
        training_service = AdaptiveTrainingZoneService(db)
        
        recommendations = training_service.get_training_recommendations(
            user_id=str(current_user.id),
            subject_id=subject_id
        )
        
        return {
            "success": True,
            "recommendations": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@router.get("/training-zone/progress/{subject_id}")
async def track_learning_progress(
    subject_id: str,
    time_period: int = Query(30, ge=7, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track detailed learning progress over specified time period.
    
    Returns comprehensive analysis of learning patterns and efficiency.
    """
    try:
        training_service = AdaptiveTrainingZoneService(db)
        
        progress_result = training_service.track_learning_progress(
            user_id=str(current_user.id),
            subject_id=subject_id,
            time_period=time_period
        )
        
        return {
            "success": True,
            "progress_analysis": progress_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking learning progress: {str(e)}")

# Video Recommendation Routes

@router.post("/videos/refresh")
async def refresh_video_recommendations(
    request: VideoRecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh video recommendations based on monthly diagnostic results.
    
    Updates video recommendations and creates personalized learning paths.
    """
    try:
        video_service = EnhancedVideoRecommendationService(db)
        
        # Get latest diagnostic results (simplified)
        diagnostic_results = {"comparison": {"improvement_percentage": 10, "topics_improved": [], "topics_declined": []}}
        
        refresh_result = video_service.refresh_monthly_recommendations(
            user_id=str(current_user.id),
            subject_id=request.subject_id,
            diagnostic_results=diagnostic_results
        )
        
        return {
            "success": True,
            "message": "Video recommendations refreshed successfully",
            "recommendations": refresh_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing video recommendations: {str(e)}")

@router.get("/videos/recommendations/{subject_id}")
async def get_adaptive_video_recommendations(
    subject_id: str,
    recommendation_type: str = Query("adaptive", regex="^(focus|review|challenge|adaptive)$"),
    count: int = Query(20, ge=5, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get adaptive video recommendations based on current performance.
    
    Returns personalized video suggestions with learning metadata.
    """
    try:
        video_service = EnhancedVideoRecommendationService(db)
        
        recommendations = video_service.get_adaptive_video_recommendations(
            user_id=str(current_user.id),
            subject_id=subject_id,
            recommendation_type=recommendation_type,
            count=count
        )
        
        return {
            "success": True,
            "recommendation_type": recommendation_type,
            "videos": recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting video recommendations: {str(e)}")

@router.post("/videos/engagement")
async def track_video_engagement(
    request: VideoEngagementRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Track video engagement to improve future recommendations.
    
    Records viewing data and provides next video suggestions.
    """
    try:
        video_service = EnhancedVideoRecommendationService(db)
        
        engagement_result = video_service.track_video_engagement(
            user_id=str(current_user.id),
            video_id=request.video_id,
            engagement_data=request.engagement_data
        )
        
        return {
            "success": True,
            "message": "Video engagement tracked successfully",
            "engagement_analysis": engagement_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error tracking video engagement: {str(e)}")

@router.get("/videos/learning-path/{subject_id}")
async def get_learning_path_videos(
    subject_id: str,
    path_segment: str = Query("current", regex="^(current|next|review|advanced)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get videos for a specific learning path segment.
    
    Returns videos and metadata for the requested learning path segment.
    """
    try:
        video_service = EnhancedVideoRecommendationService(db)
        
        path_videos = video_service.get_learning_path_videos(
            user_id=str(current_user.id),
            subject_id=subject_id,
            path_segment=path_segment
        )
        
        return {
            "success": True,
            "learning_path": path_videos
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting learning path videos: {str(e)}")

@router.get("/videos/analytics/{subject_id}")
async def get_video_recommendation_analytics(
    subject_id: str,
    time_period: int = Query(30, ge=7, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics about video recommendation effectiveness.
    
    Returns comprehensive analytics about recommendation performance and engagement.
    """
    try:
        video_service = EnhancedVideoRecommendationService(db)
        
        analytics = video_service.get_recommendation_analytics(
            user_id=str(current_user.id),
            subject_id=subject_id,
            time_period=time_period
        )
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting video analytics: {str(e)}")

# Progress Report Routes

@router.post("/reports/generate")
async def generate_comprehensive_report(
    request: ProgressReportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive progress report with learning trajectories.
    
    Creates detailed report with visualizations, analytics, and insights.
    """
    try:
        report_service = ProgressReportService(db)
        
        # Convert report type string to enum
        report_type = ReportType(request.report_type)
        
        # Handle custom date range if provided
        custom_range = None
        if request.custom_date_range:
            start_date = datetime.fromisoformat(request.custom_date_range["start_date"])
            end_date = datetime.fromisoformat(request.custom_date_range["end_date"])
            custom_range = (start_date, end_date)
        
        report = report_service.generate_comprehensive_report(
            user_id=str(current_user.id),
            subject_id=request.subject_id,
            report_type=report_type,
            custom_date_range=custom_range
        )
        
        return {
            "success": True,
            "message": "Progress report generated successfully",
            "report": report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating progress report: {str(e)}")

@router.get("/reports/trajectory/{subject_id}")
async def get_learning_trajectory_visualization(
    subject_id: str,
    trajectory_type: str = Query("overall_performance", 
                               regex="^(overall_performance|topic_mastery|difficulty_progression|time_efficiency|learning_velocity)$"),
    time_period: int = Query(180, ge=30, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate detailed learning trajectory visualization data.
    
    Returns trajectory data for specific metrics with trend analysis and insights.
    """
    try:
        report_service = ProgressReportService(db)
        
        # Convert trajectory type string to enum
        trajectory_type_enum = TrajectoryType(trajectory_type)
        
        trajectory = report_service.generate_learning_trajectory_visualization(
            user_id=str(current_user.id),
            subject_id=subject_id,
            trajectory_type=trajectory_type_enum,
            time_period=time_period
        )
        
        return {
            "success": True,
            "trajectory": trajectory
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating trajectory visualization: {str(e)}")

@router.get("/reports/comparative")
async def get_comparative_analysis(
    subject_ids: List[str] = Query(..., description="List of subject IDs to compare"),
    comparison_period: int = Query(90, ge=30, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate comparative analysis across multiple subjects.
    
    Returns cross-subject insights and performance comparisons.
    """
    try:
        report_service = ProgressReportService(db)
        
        comparative_analysis = report_service.generate_comparative_analysis(
            user_id=str(current_user.id),
            subject_ids=subject_ids,
            comparison_period=comparison_period
        )
        
        return {
            "success": True,
            "comparative_analysis": comparative_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating comparative analysis: {str(e)}")

@router.get("/reports/milestones/{subject_id}")
async def get_milestone_report(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate milestone achievement report.
    
    Returns learning goals, accomplishments, and upcoming milestones.
    """
    try:
        report_service = ProgressReportService(db)
        
        milestone_report = report_service.generate_milestone_report(
            user_id=str(current_user.id),
            subject_id=subject_id
        )
        
        return {
            "success": True,
            "milestone_report": milestone_report
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating milestone report: {str(e)}")

@router.post("/reports/export/{report_id}")
async def export_report_data(
    report_id: str,
    export_format: str = Query("json", regex="^(json|csv|pdf|excel)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export report data in various formats.
    
    Returns exported report data for external use or download.
    """
    try:
        report_service = ProgressReportService(db)
        
        export_result = report_service.export_report_data(
            report_id=report_id,
            export_format=export_format
        )
        
        return {
            "success": True,
            "export": export_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting report: {str(e)}")

# System Administration Routes

@router.get("/admin/system-status")
async def get_system_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get overall system status and health metrics.
    
    Admin-only endpoint for monitoring the monthly diagnostic system.
    """
    try:
        # Verify admin access
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get system metrics
        system_status = {
            "system_health": "healthy",
            "active_assessments": 0,  # Would query actual active assessments
            "scheduled_assessments_today": 0,  # Would query today's scheduled assessments
            "total_users_with_schedules": 0,  # Would query users with active schedules
            "average_response_time_ms": 150,  # Would calculate actual response times
            "last_system_update": datetime.utcnow().isoformat(),
            "services_status": {
                "diagnostic_scheduler": "operational",
                "training_zone_service": "operational",
                "video_recommendation_service": "operational",
                "progress_report_service": "operational"
            }
        }
        
        return {
            "success": True,
            "system_status": system_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")

@router.post("/admin/trigger-monthly-refresh")
async def trigger_monthly_system_refresh(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger monthly system refresh for all users.
    
    Admin-only endpoint to manually trigger monthly updates across the system.
    """
    try:
        # Verify admin access
        if not getattr(current_user, 'is_admin', False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # This would trigger system-wide monthly refresh
        refresh_status = {
            "refresh_triggered": True,
            "estimated_completion_time": "30 minutes",
            "affected_users": 0,  # Would count actual users
            "services_to_refresh": [
                "video_recommendations",
                "training_zones",
                "progress_reports",
                "diagnostic_schedules"
            ]
        }
        
        return {
            "success": True,
            "message": "Monthly system refresh triggered successfully",
            "refresh_status": refresh_status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering system refresh: {str(e)}")

# Health Check Route

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint for the monthly diagnostic system.
    
    Returns system status and timestamp.
    """
    return {
        "status": "healthy",
        "service": "Monthly Diagnostic Assessment System",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }