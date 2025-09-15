"""
Enhanced Personalized Study Plan API
API endpoints that use real YouTube videos instead of placeholders
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging
import json
from datetime import datetime

from ..core.database import get_db
from ..services.enhanced_personalized_study_plan_generator import EnhancedPersonalizedStudyPlanGenerator
from ..services.diagnostic_weakness_analyzer import DiagnosticWeaknessAnalyzer
from ..services.optimized_video_recommendation_engine import OptimizedVideoRecommendationEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/enhanced-study-plans", tags=["Enhanced Study Plans"])

class EnhancedStudyPlanRequest(BaseModel):
    """Request model for enhanced study plan generation"""
    user_id: str = Field(..., description="ID del usuario")
    subject_id: str = Field(..., description="ID de la materia")
    diagnostic_test_id: str = Field(..., description="ID del test diagnóstico")
    target_weeks: int = Field(default=8, ge=4, le=16, description="Duración del plan en semanas")
    use_optimized_engine: bool = Field(default=True, description="Usar motor optimizado de videos")

class BatchEnhancedStudyPlanRequest(BaseModel):
    """Request model for batch enhanced study plan generation"""
    student_plans: List[EnhancedStudyPlanRequest] = Field(..., description="Lista de planes a generar")

class VideoQualityReport(BaseModel):
    """Model for video quality reporting"""
    total_videos: int
    real_videos: int
    fallback_videos: int
    average_quality: float
    quality_distribution: Dict[str, int]

@router.post("/generate")
async def generate_enhanced_study_plan(
    request: EnhancedStudyPlanRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate enhanced personalized study plan with real YouTube videos
    
    This endpoint creates study plans that prioritize real YouTube videos
    over placeholder content, improving learning outcomes.
    """
    try:
        logger.info(f"🚀 Generating ENHANCED study plan for user {request.user_id}")
        
        # Validate that diagnostic test exists
        diagnostic_check = db.execute(
            "SELECT id FROM diagnostic_tests WHERE id = %s AND user_id = %s",
            (request.diagnostic_test_id, request.user_id)
        ).first()
        
        if not diagnostic_check:
            raise HTTPException(
                status_code=404,
                detail=f"Diagnostic test {request.diagnostic_test_id} not found for user {request.user_id}"
            )
        
        logger.info(f"🎯 Using enhanced generator with OptimizedVideoRecommendationEngine")
        
        # Initialize the enhanced plan generator
        generator = EnhancedPersonalizedStudyPlanGenerator(db)
        
        # Generate the enhanced personalized plan
        result = await generator.generate_personalized_plan(
            user_id=request.user_id,
            subject_id=request.subject_id,
            diagnostic_test_id=request.diagnostic_test_id,
            target_weeks=request.target_weeks
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate enhanced study plan: {result.get('error', 'Unknown error')}"
            )
        
        # Log enhancement statistics
        logger.info(f"✅ Enhanced plan generated: {result['real_videos']}/{result['total_videos']} real videos")
        logger.info(f"📊 Video quality score: {result.get('video_quality_score', 0)}")
        
        # Prepare enhanced response
        enhanced_result = {
            "success": True,
            "plan_id": result['plan_id'],
            "enhancement_type": "OPTIMIZED_REAL_VIDEOS",
            "video_statistics": {
                "total_videos": result['total_videos'],
                "real_videos": result['real_videos'],
                "fallback_videos": result['fallback_videos'],
                "real_video_percentage": round((result['real_videos'] / result['total_videos']) * 100, 1) if result['total_videos'] > 0 else 0,
                "quality_score": result.get('video_quality_score', 0)
            },
            "plan_details": {
                "file_path": result['file_path'],
                "units": result['units'],
                "estimated_duration_weeks": result['estimated_duration_weeks'],
                "weakness_areas": result['weakness_areas']
            },
            "improvement_indicators": {
                "uses_real_videos": result['real_videos'] > 0,
                "high_quality_content": result.get('video_quality_score', 0) > 0.5,
                "personalization_level": "ENHANCED" if result['real_videos'] > result['fallback_videos'] else "STANDARD"
            },
            "message": result['message']
        }
        
        return enhanced_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating enhanced study plan: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.post("/generate-batch")
async def generate_batch_enhanced_study_plans(
    request: BatchEnhancedStudyPlanRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Generate multiple enhanced study plans in batch
    
    Useful for processing multiple students or subjects efficiently
    with real video recommendations.
    """
    try:
        if not request.student_plans:
            raise HTTPException(
                status_code=400,
                detail="student_plans array is required and cannot be empty"
            )
        
        generator = EnhancedPersonalizedStudyPlanGenerator(db)
        results = []
        
        total_real_videos = 0
        total_videos = 0
        
        for i, plan_request in enumerate(request.student_plans):
            try:
                logger.info(f"🔄 Processing enhanced plan {i+1}/{len(request.student_plans)}")
                
                result = await generator.generate_personalized_plan(
                    user_id=plan_request.user_id,
                    subject_id=plan_request.subject_id,
                    diagnostic_test_id=plan_request.diagnostic_test_id,
                    target_weeks=plan_request.target_weeks
                )
                
                if result['success']:
                    total_real_videos += result.get('real_videos', 0)
                    total_videos += result.get('total_videos', 0)
                
                results.append({
                    "user_id": plan_request.user_id,
                    "subject_id": plan_request.subject_id,
                    "result": result,
                    "enhancement_level": "OPTIMIZED_REAL_VIDEOS" if result.get('success') else "FAILED"
                })
                
            except Exception as e:
                logger.error(f"❌ Error processing plan for user {plan_request.user_id}: {e}")
                results.append({
                    "user_id": plan_request.user_id,
                    "subject_id": plan_request.subject_id,
                    "result": {
                        "success": False,
                        "error": str(e)
                    },
                    "enhancement_level": "FAILED"
                })
        
        # Calculate batch statistics
        successful_plans = [r for r in results if r['result'].get('success', False)]
        real_video_percentage = round((total_real_videos / total_videos) * 100, 1) if total_videos > 0 else 0
        
        batch_summary = {
            "success": True,
            "total_requested": len(request.student_plans),
            "successful_generations": len(successful_plans),
            "failed_generations": len(request.student_plans) - len(successful_plans),
            "enhancement_statistics": {
                "total_videos_across_all_plans": total_videos,
                "total_real_videos_across_all_plans": total_real_videos,
                "real_video_percentage": real_video_percentage,
                "average_quality_improvement": "SIGNIFICANT" if real_video_percentage > 70 else "MODERATE" if real_video_percentage > 40 else "BASIC"
            },
            "individual_results": results,
            "batch_processed_at": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Batch processing completed: {len(successful_plans)}/{len(request.student_plans)} successful")
        logger.info(f"📊 Overall real video rate: {real_video_percentage}%")
        
        return batch_summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error in batch enhanced study plan generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch processing error: {str(e)}"
        )

@router.get("/student/{user_id}/subject/{subject_id}")
async def get_enhanced_student_plan(
    user_id: str,
    subject_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve enhanced study plan for a specific student and subject
    
    Returns detailed information about video quality and enhancements.
    """
    try:
        generator = EnhancedPersonalizedStudyPlanGenerator(db)
        plan = await generator.get_student_plan(user_id, subject_id)
        
        if not plan['success']:
            raise HTTPException(
                status_code=404,
                detail="No enhanced study plan found for this student and subject"
            )
        
        # Add enhancement analysis
        video_stats = plan.get('video_statistics', {})
        enhancement_analysis = {
            "is_enhanced": plan.get('enhancement_level') == 'OPTIMIZED_REAL_VIDEOS',
            "video_quality_summary": {
                "total_videos": video_stats.get('total_videos', 0),
                "real_videos": video_stats.get('real_videos', 0),
                "fallback_videos": video_stats.get('fallback_videos', 0),
                "quality_score": video_stats.get('average_quality', 0)
            },
            "content_effectiveness": "HIGH" if video_stats.get('real_videos', 0) > video_stats.get('fallback_videos', 0) else "MODERATE"
        }
        
        enhanced_response = {
            **plan,
            "enhancement_analysis": enhancement_analysis
        }
        
        return enhanced_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error retrieving enhanced student plan: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving plan: {str(e)}"
        )

@router.get("/video-quality-report")
async def get_video_quality_report(
    db: Session = Depends(get_db)
):
    """
    Get system-wide video quality report for enhanced study plans
    
    Provides insights into the effectiveness of the video enhancement system.
    """
    try:
        # Query enhanced study plans
        query = """
            SELECT plan_data
            FROM study_plans
            WHERE plan_name LIKE '%Enhanced Plan with Real Videos%'
            AND is_active = true
            ORDER BY created_at DESC
            LIMIT 100
        """
        
        results = db.execute(query).fetchall()
        
        if not results:
            return {
                "success": True,
                "message": "No enhanced study plans found",
                "total_plans": 0
            }
        
        # Analyze video statistics across all plans
        total_plans = len(results)
        total_videos = 0
        total_real_videos = 0
        total_fallback_videos = 0
        quality_scores = []
        
        for result in results:
            try:
                plan_data = json.loads(result[0])
                video_stats = plan_data.get('video_statistics', {})
                
                total_videos += video_stats.get('total_videos', 0)
                total_real_videos += video_stats.get('real_videos', 0)
                total_fallback_videos += video_stats.get('fallback_videos', 0)
                
                if video_stats.get('average_quality', 0) > 0:
                    quality_scores.append(video_stats['average_quality'])
                    
            except json.JSONDecodeError:
                continue
        
        average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        real_video_percentage = (total_real_videos / total_videos * 100) if total_videos > 0 else 0
        
        quality_report = {
            "success": True,
            "report_generated_at": datetime.now().isoformat(),
            "system_statistics": {
                "total_enhanced_plans": total_plans,
                "total_videos_across_all_plans": total_videos,
                "real_videos_count": total_real_videos,
                "fallback_videos_count": total_fallback_videos,
                "real_video_percentage": round(real_video_percentage, 2),
                "average_quality_score": round(average_quality, 3)
            },
            "quality_assessment": {
                "system_effectiveness": "EXCELLENT" if real_video_percentage > 80 else "GOOD" if real_video_percentage > 60 else "NEEDS_IMPROVEMENT",
                "content_quality": "HIGH" if average_quality > 0.6 else "MODERATE" if average_quality > 0.3 else "LOW",
                "enhancement_success": total_real_videos > total_fallback_videos
            },
            "recommendations": []
        }
        
        # Add recommendations based on performance
        if real_video_percentage < 60:
            quality_report["recommendations"].append("Consider expanding YouTube catalog for better coverage")
        if average_quality < 0.5:
            quality_report["recommendations"].append("Review video quality scoring algorithm")
        if total_fallback_videos > total_real_videos:
            quality_report["recommendations"].append("Improve topic matching algorithms")
        
        if not quality_report["recommendations"]:
            quality_report["recommendations"].append("System performing well - continue current approach")
        
        return quality_report
        
    except Exception as e:
        logger.error(f"❌ Error generating video quality report: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating report: {str(e)}"
        )

@router.post("/test-video-recommendations/{topic_code}/{topic_name}")
async def test_video_recommendations(
    topic_code: str,
    topic_name: str,
    subject_id: Optional[str] = None,
    max_videos: int = 5,
    db: Session = Depends(get_db)
):
    """
    Test endpoint to verify video recommendation quality for specific topics
    
    Useful for debugging and validating the enhanced video matching system.
    """
    try:
        # Initialize the optimized video engine
        video_engine = OptimizedVideoRecommendationEngine(db)
        
        # Get recommendations
        videos = video_engine.get_intelligent_recommendations(
            topic_code=topic_code,
            topic_name=topic_name,
            subject_id=subject_id,
            max_videos=max_videos
        )
        
        # Analyze results
        real_videos = [v for v in videos if not v.get('is_fallback', False)]
        fallback_videos = [v for v in videos if v.get('is_fallback', False)]
        
        average_quality = sum(v.get('relevance_score', 0) for v in videos) / len(videos) if videos else 0
        
        test_result = {
            "success": True,
            "test_parameters": {
                "topic_code": topic_code,
                "topic_name": topic_name,
                "subject_id": subject_id,
                "requested_videos": max_videos
            },
            "results": {
                "total_videos_found": len(videos),
                "real_videos": len(real_videos),
                "fallback_videos": len(fallback_videos),
                "average_quality_score": round(average_quality, 3),
                "recommendation_quality": "EXCELLENT" if average_quality > 0.7 else "GOOD" if average_quality > 0.4 else "NEEDS_IMPROVEMENT"
            },
            "video_details": [
                {
                    "title": video.get('title', 'N/A'),
                    "video_id": video.get('video_id', 'N/A'),
                    "relevance_score": video.get('relevance_score', 0),
                    "is_real_video": not video.get('is_fallback', False),
                    "recommendation_reason": video.get('recommendation_reason', 'N/A'),
                    "duration_minutes": video.get('duration_minutes', 0)
                }
                for video in videos
            ],
            "tested_at": datetime.now().isoformat()
        }
        
        return test_result
        
    except Exception as e:
        logger.error(f"❌ Error testing video recommendations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Test error: {str(e)}"
        )

# Add route to main router registration
if __name__ == "__main__":
    # This allows the module to be tested independently
    logger.info("Enhanced Personalized Study Plan API loaded successfully")