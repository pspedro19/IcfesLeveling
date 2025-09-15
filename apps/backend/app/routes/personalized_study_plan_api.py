"""
Personalized Study Plan API Endpoints
Comprehensive API for managing personalized study plans based on diagnostic weaknesses
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime

from ..core.database import get_db
from ..services.personalized_study_plan_generator import PersonalizedStudyPlanGenerator
from ..services.diagnostic_weakness_analyzer import DiagnosticWeaknessAnalyzer
from ..services.enhanced_video_matcher import EnhancedVideoMatcher
from ..services.monthly_reassessment_system import MonthlyReassessmentSystem
from ..services.study_plan_storage import StudyPlanStorageManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/personalized-study-plans", tags=["personalized-study-plans"])

@router.post("/generate")
async def generate_personalized_study_plan(
    request_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Generate a personalized study plan based on diagnostic test results
    
    Request body:
    {
        "user_id": "string",
        "subject_id": "string", 
        "diagnostic_test_id": "string",
        "target_weeks": 8,
        "preferences": {
            "daily_study_time": 60,
            "difficulty_preference": "adaptive",
            "learning_style": "visual"
        }
    }
    """
    try:
        user_id = request_data.get('user_id')
        subject_id = request_data.get('subject_id')
        diagnostic_test_id = request_data.get('diagnostic_test_id')
        target_weeks = request_data.get('target_weeks', 8)
        
        if not all([user_id, subject_id, diagnostic_test_id]):
            raise HTTPException(
                status_code=400,
                detail="user_id, subject_id, and diagnostic_test_id are required"
            )
        
        logger.info(f"🎯 Generating personalized study plan for user {user_id}")
        
        # Initialize the plan generator
        generator = PersonalizedStudyPlanGenerator(db)
        
        # Generate the personalized plan
        result = await generator.generate_personalized_plan(
            user_id=user_id,
            subject_id=subject_id,
            diagnostic_test_id=diagnostic_test_id,
            target_weeks=target_weeks
        )
        
        if result['success']:
            logger.info(f"✅ Successfully generated plan {result['plan_id']}")
            return {
                'success': True,
                'plan_id': result['plan_id'],
                'message': 'Personalized study plan generated successfully',
                'plan_summary': {
                    'total_units': result['units'],
                    'total_videos': result['total_videos'],
                    'estimated_duration_weeks': result['estimated_duration_weeks'],
                    'weakness_areas_targeted': result['weakness_areas'],
                    'file_path': result['file_path']
                },
                'next_steps': [
                    'Review your personalized learning path',
                    'Start with the highest priority units',
                    'Track your progress regularly',
                    'Take reassessment in 4 weeks'
                ]
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Plan generation failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating personalized study plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{plan_id}")
async def get_study_plan(
    plan_id: str,
    source: str = Query("auto", description="Source: auto, database, file"),
    db: Session = Depends(get_db)
):
    """Get a specific study plan by ID"""
    try:
        storage_manager = StudyPlanStorageManager(db)
        result = storage_manager.get_study_plan(plan_id, source)
        
        if result['success']:
            return {
                'success': True,
                'plan': result,
                'retrieved_from': result.get('source', 'unknown')
            }
        else:
            raise HTTPException(status_code=404, detail=result.get('error', 'Plan not found'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving study plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}")
async def list_user_study_plans(
    user_id: str,
    subject_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List all study plans for a user"""
    try:
        storage_manager = StudyPlanStorageManager(db)
        result = storage_manager.list_user_plans(user_id, subject_id)
        
        if result['success']:
            return result
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to retrieve plans'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing user plans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-diagnostic")
async def analyze_diagnostic_weaknesses(
    request_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Analyze diagnostic test results to identify specific weaknesses
    
    Request body:
    {
        "user_id": "string",
        "subject_id": "string",
        "diagnostic_test_id": "string"
    }
    """
    try:
        user_id = request_data.get('user_id')
        subject_id = request_data.get('subject_id')
        diagnostic_test_id = request_data.get('diagnostic_test_id')
        
        if not all([user_id, subject_id, diagnostic_test_id]):
            raise HTTPException(
                status_code=400,
                detail="user_id, subject_id, and diagnostic_test_id are required"
            )
        
        analyzer = DiagnosticWeaknessAnalyzer(db)
        result = await analyzer.analyze_diagnostic_results(
            user_id, subject_id, diagnostic_test_id
        )
        
        if result['success']:
            return {
                'success': True,
                'analysis': result,
                'message': 'Diagnostic analysis completed successfully'
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Analysis failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing diagnostic: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/match-videos")
async def match_videos_to_questions(
    request_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Match YouTube videos to failed questions using advanced algorithms
    
    Request body:
    {
        "failed_questions": [
            {
                "question_id": "string",
                "question_text": "string",
                "topic_name": "string",
                "difficulty_theta": 0.5,
                "is_correct": false,
                "response_time_ms": 45000
            }
        ],
        "subject_id": "string",
        "max_videos_per_question": 3,
        "total_video_limit": 20
    }
    """
    try:
        failed_questions = request_data.get('failed_questions', [])
        subject_id = request_data.get('subject_id')
        max_videos_per_question = request_data.get('max_videos_per_question', 3)
        total_video_limit = request_data.get('total_video_limit', 20)
        
        if not failed_questions or not subject_id:
            raise HTTPException(
                status_code=400,
                detail="failed_questions and subject_id are required"
            )
        
        video_matcher = EnhancedVideoMatcher(db)
        result = await video_matcher.get_matched_video_recommendations(
            failed_questions=failed_questions,
            subject_id=subject_id,
            max_videos_per_question=max_videos_per_question,
            total_video_limit=total_video_limit
        )
        
        if result['success']:
            return {
                'success': True,
                'video_recommendations': result,
                'message': 'Video matching completed successfully'
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Video matching failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching videos: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/conduct-reassessment")
async def conduct_monthly_reassessment(
    request_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Conduct monthly reassessment and potentially update study plan
    
    Request body:
    {
        "user_id": "string",
        "subject_id": "string",
        "original_plan_id": "string",
        "reassessment_test_id": "string"
    }
    """
    try:
        user_id = request_data.get('user_id')
        subject_id = request_data.get('subject_id')
        original_plan_id = request_data.get('original_plan_id')
        reassessment_test_id = request_data.get('reassessment_test_id')
        
        if not all([user_id, subject_id, original_plan_id, reassessment_test_id]):
            raise HTTPException(
                status_code=400,
                detail="All fields are required: user_id, subject_id, original_plan_id, reassessment_test_id"
            )
        
        reassessment_system = MonthlyReassessmentSystem(db)
        result = await reassessment_system.conduct_monthly_reassessment(
            user_id=user_id,
            subject_id=subject_id,
            original_plan_id=original_plan_id,
            reassessment_test_id=reassessment_test_id
        )
        
        if result['success']:
            return {
                'success': True,
                'reassessment_results': result,
                'message': 'Monthly reassessment completed successfully'
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('message', 'Reassessment failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conducting reassessment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{plan_id}/progress")
async def update_plan_progress(
    plan_id: str,
    progress_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Update study plan progress
    
    Request body:
    {
        "completed_units": 3,
        "progress_percentage": 37.5,
        "last_activity": "2024-01-15T10:30:00Z"
    }
    """
    try:
        completed_units = progress_data.get('completed_units')
        progress_percentage = progress_data.get('progress_percentage')
        
        if completed_units is None or progress_percentage is None:
            raise HTTPException(
                status_code=400,
                detail="completed_units and progress_percentage are required"
            )
        
        storage_manager = StudyPlanStorageManager(db)
        result = storage_manager.update_plan_progress(
            plan_id=plan_id,
            completed_units=completed_units,
            progress_percentage=progress_percentage
        )
        
        if result['success']:
            return {
                'success': True,
                'updated_progress': result,
                'message': 'Progress updated successfully'
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Progress update failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{plan_id}/archive")
async def archive_study_plan(
    plan_id: str,
    db: Session = Depends(get_db)
):
    """Archive a study plan (mark as inactive)"""
    try:
        storage_manager = StudyPlanStorageManager(db)
        result = storage_manager.archive_plan(plan_id)
        
        if result['success']:
            return {
                'success': True,
                'message': result['message'],
                'archived_plan_id': plan_id
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Archive failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error archiving plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{plan_id}")
async def delete_study_plan(
    plan_id: str,
    create_backup: bool = Query(True, description="Create backup before deletion"),
    db: Session = Depends(get_db)
):
    """Delete a study plan (with optional backup)"""
    try:
        storage_manager = StudyPlanStorageManager(db)
        result = storage_manager.delete_plan(plan_id, create_backup)
        
        if result['success']:
            return {
                'success': True,
                'message': result['message'],
                'deleted_plan_id': plan_id,
                'backup_created': result['backup_created']
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Deletion failed'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/storage/stats")
async def get_storage_statistics(
    db: Session = Depends(get_db)
):
    """Get storage system statistics"""
    try:
        storage_manager = StudyPlanStorageManager(db)
        result = storage_manager.get_storage_stats()
        
        if result['success']:
            return {
                'success': True,
                'storage_statistics': result,
                'timestamp': datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to get stats'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bulk-generate")
async def bulk_generate_study_plans(
    request_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Generate study plans for multiple students in bulk
    
    Request body:
    {
        "student_plans": [
            {
                "user_id": "student1",
                "subject_id": "math",
                "diagnostic_test_id": "test1"
            },
            {
                "user_id": "student2", 
                "subject_id": "science",
                "diagnostic_test_id": "test2"
            }
        ],
        "default_target_weeks": 8
    }
    """
    try:
        student_plans = request_data.get('student_plans', [])
        default_weeks = request_data.get('default_target_weeks', 8)
        
        if not student_plans:
            raise HTTPException(
                status_code=400,
                detail="student_plans array is required"
            )
        
        generator = PersonalizedStudyPlanGenerator(db)
        results = []
        
        for plan_request in student_plans:
            try:
                result = await generator.generate_personalized_plan(
                    user_id=plan_request['user_id'],
                    subject_id=plan_request['subject_id'],
                    diagnostic_test_id=plan_request['diagnostic_test_id'],
                    target_weeks=plan_request.get('target_weeks', default_weeks)
                )
                
                results.append({
                    'user_id': plan_request['user_id'],
                    'success': result['success'],
                    'plan_id': result.get('plan_id'),
                    'message': result.get('message', ''),
                    'error': result.get('error')
                })
                
            except Exception as e:
                results.append({
                    'user_id': plan_request['user_id'],
                    'success': False,
                    'error': str(e)
                })
        
        successful_plans = [r for r in results if r['success']]
        failed_plans = [r for r in results if not r['success']]
        
        return {
            'success': True,
            'total_requested': len(student_plans),
            'successful_plans': len(successful_plans),
            'failed_plans': len(failed_plans),
            'results': results,
            'summary': {
                'success_rate': len(successful_plans) / len(student_plans) * 100,
                'successful_plan_ids': [r['plan_id'] for r in successful_plans if r['plan_id']],
                'failed_users': [r['user_id'] for r in failed_plans]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk generation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{plan_id}/export")
async def export_study_plan(
    plan_id: str,
    format: str = Query("yaml", description="Export format: yaml, json, pdf"),
    db: Session = Depends(get_db)
):
    """Export study plan in different formats"""
    try:
        storage_manager = StudyPlanStorageManager(db)
        plan_data = storage_manager.get_study_plan(plan_id)
        
        if not plan_data['success']:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        if format.lower() == "yaml":
            return {
                'success': True,
                'format': 'yaml',
                'content': plan_data.get('yaml_content', ''),
                'filename': f"study_plan_{plan_id}.yaml"
            }
        elif format.lower() == "json":
            return {
                'success': True,
                'format': 'json',
                'content': plan_data.get('plan_data', {}),
                'filename': f"study_plan_{plan_id}.json"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Use 'yaml' or 'json'"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-plan")
async def validate_study_plan_structure(
    plan_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Validate study plan structure and content
    
    Request body: Study plan data to validate
    """
    try:
        validation_errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['personalized_study_plan']
        for field in required_fields:
            if field not in plan_data:
                validation_errors.append(f"Missing required field: {field}")
        
        if 'personalized_study_plan' in plan_data:
            plan = plan_data['personalized_study_plan']
            
            # Check metadata
            if 'metadata' not in plan:
                validation_errors.append("Missing metadata section")
            else:
                metadata = plan['metadata']
                required_metadata = ['student_id', 'subject_id', 'diagnostic_test_id']
                for field in required_metadata:
                    if field not in metadata:
                        validation_errors.append(f"Missing metadata field: {field}")
            
            # Check learning path
            if 'learning_path' not in plan:
                validation_errors.append("Missing learning_path section")
            else:
                learning_path = plan['learning_path']
                if 'units' not in learning_path:
                    validation_errors.append("Missing units in learning_path")
                else:
                    units = learning_path['units']
                    if not isinstance(units, list) or len(units) == 0:
                        validation_errors.append("Units must be a non-empty list")
                    
                    # Validate each unit
                    for i, unit in enumerate(units):
                        unit_errors = []
                        required_unit_fields = ['unit_number', 'title', 'recommended_videos']
                        for field in required_unit_fields:
                            if field not in unit:
                                unit_errors.append(f"Unit {i+1}: Missing {field}")
                        
                        if unit_errors:
                            validation_errors.extend(unit_errors)
                        
                        # Check video structure
                        if 'recommended_videos' in unit:
                            videos = unit['recommended_videos']
                            if not isinstance(videos, list):
                                validation_errors.append(f"Unit {i+1}: recommended_videos must be a list")
                            elif len(videos) == 0:
                                warnings.append(f"Unit {i+1}: No videos recommended")
        
        # Calculate validation score
        total_checks = 10  # Arbitrary number of validation checks
        error_count = len(validation_errors)
        warning_count = len(warnings)
        
        validation_score = max(0, (total_checks - error_count - (warning_count * 0.5)) / total_checks * 100)
        
        is_valid = len(validation_errors) == 0
        
        return {
            'success': True,
            'is_valid': is_valid,
            'validation_score': round(validation_score, 2),
            'errors': validation_errors,
            'warnings': warnings,
            'summary': {
                'total_errors': len(validation_errors),
                'total_warnings': len(warnings),
                'validation_level': 'pass' if is_valid else 'fail'
            }
        }
        
    except Exception as e:
        logger.error(f"Error validating plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/dashboard/{user_id}")
async def get_user_study_analytics(
    user_id: str,
    subject_id: Optional[str] = Query(None),
    days: int = Query(30, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get comprehensive study analytics for a user"""
    try:
        from sqlalchemy import text
        from datetime import datetime, timedelta
        
        # Get user's study plans
        storage_manager = StudyPlanStorageManager(db)
        plans_result = storage_manager.list_user_plans(user_id, subject_id)
        
        if not plans_result['success']:
            raise HTTPException(status_code=404, detail="No plans found for user")
        
        plans = plans_result['plans']
        
        # Calculate analytics
        analytics = {
            'user_id': user_id,
            'analysis_period_days': days,
            'total_plans': len(plans),
            'active_plans': len([p for p in plans if p['is_active']]),
            'completed_plans': len([p for p in plans if p['progress_percentage'] >= 100]),
            'average_progress': sum(p['progress_percentage'] for p in plans) / len(plans) if plans else 0,
            'subjects_studied': list(set(p['subject_id'] for p in plans)),
            'plan_performance': {
                'excellent': len([p for p in plans if p['progress_percentage'] >= 80]),
                'good': len([p for p in plans if 60 <= p['progress_percentage'] < 80]),
                'needs_improvement': len([p for p in plans if p['progress_percentage'] < 60])
            },
            'recent_activity': {
                'plans_created_last_30_days': len([
                    p for p in plans 
                    if p['created_at'] and 
                    datetime.fromisoformat(p['created_at'].replace('Z', '+00:00')) > datetime.now() - timedelta(days=30)
                ]),
                'plans_updated_last_7_days': len([
                    p for p in plans 
                    if p['updated_at'] and 
                    datetime.fromisoformat(p['updated_at'].replace('Z', '+00:00')) > datetime.now() - timedelta(days=7)
                ])
            }
        }
        
        return {
            'success': True,
            'analytics': analytics,
            'plans_summary': plans,
            'generated_at': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))