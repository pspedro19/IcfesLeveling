"""
Integrated Study Plan API - Complete System Integration
======================================================

API endpoints for the integrated study plan system with real YouTube videos,
fuzzy matching, and comprehensive learning recommendations.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import uuid
import json
import logging

from ..core.database import get_db
from ..models.subject import Subject
from ..models.topic import Topic
from ..models.user import User

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/integrated-study-plans", tags=["Integrated Study Plans"])

class IntegratedStudyPlanService:
    """Service class for integrated study plan functionality"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def analyze_diagnostic_results(self, user_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze diagnostic test results"""
        logger.info("Analyzing diagnostic results...")
        
        # Default subject weights for ICFES
        subject_weights = {
            "Matemáticas": 0.25,
            "Ciencias Naturales": 0.25,
            "Lenguaje": 0.20,
            "Ciencias Sociales": 0.20,
            "Inglés": 0.10
        }
        
        analysis = {
            "strengths": [],
            "weaknesses": [],
            "priority_subjects": [],
            "study_hours_needed": {},
            "difficulty_levels": {},
            "overall_score": 0.0
        }
        
        total_weighted_score = 0.0
        
        for subject, data in user_results.items():
            score = data.get("score", 0.5)
            weight = subject_weights.get(subject, 0.15)
            
            # Contribute to overall score
            total_weighted_score += score * weight
            
            # Categorize performance
            if score >= 0.75:
                analysis["strengths"].append({
                    "subject": subject,
                    "score": score,
                    "status": "strong",
                    "recommendation": "Maintain level with periodic review"
                })
            elif score < 0.60:
                analysis["weaknesses"].append({
                    "subject": subject,
                    "score": score,
                    "status": "needs_improvement",
                    "priority": 1 if score < 0.50 else 2,
                    "recommendation": "Intensive study required"
                })
            
            # Calculate study hours (inversely related to score)
            base_hours = 20
            score_multiplier = 1.5 - score
            study_hours = int(base_hours * score_multiplier * weight)
            analysis["study_hours_needed"][subject] = max(5, study_hours)
            
            # Determine difficulty level for content selection
            if score < 0.50:
                analysis["difficulty_levels"][subject] = "basic"
            elif score < 0.70:
                analysis["difficulty_levels"][subject] = "intermediate"
            else:
                analysis["difficulty_levels"][subject] = "advanced"
        
        # Sort subjects by score for prioritization
        sorted_subjects = sorted(user_results.items(), key=lambda x: x[1].get("score", 0.5))
        analysis["priority_subjects"] = [s[0] for s in sorted_subjects]
        analysis["overall_score"] = total_weighted_score
        
        return analysis
    
    def get_video_recommendations(self, subject_name: str, difficulty_level: str = "intermediate", limit: int = 8) -> List[Dict[str, Any]]:
        """Get real video recommendations for a subject"""
        logger.info(f"Getting video recommendations for {subject_name}...")
        
        try:
            # Get subject ID
            subject_query = text("SELECT id FROM subjects WHERE name = :subject_name")
            subject_result = self.db.execute(subject_query, {"subject_name": subject_name})
            subject_row = subject_result.first()
            
            if not subject_row:
                logger.warning(f"Subject '{subject_name}' not found")
                return []
            
            subject_id = subject_row[0]
            
            # Get videos with quality filtering
            video_query = text("""
                SELECT 
                    id, video_id, title, description, url, embed_url, thumbnail_url,
                    channel, duration_seconds, view_count, like_count,
                    area_evaluada, tema_principal, quality_score, educational_value
                FROM youtube_catalog 
                WHERE subject_id = :subject_id
                    AND quality_score > 0.3
                    AND educational_value > 0.4
                ORDER BY 
                    quality_score DESC, 
                    educational_value DESC, 
                    COALESCE(view_count, 0) DESC
                LIMIT :limit
            """)
            
            video_result = self.db.execute(video_query, {
                "subject_id": subject_id,
                "limit": limit
            })
            
            videos = []
            for row in video_result:
                duration_formatted = self.format_duration(row[8])
                
                video_data = {
                    "id": row[0],
                    "video_id": row[1],
                    "title": row[2],
                    "description": row[3],
                    "url": row[4],
                    "embed_url": row[5],
                    "thumbnail_url": row[6],
                    "channel": row[7],
                    "duration_seconds": row[8],
                    "duration_formatted": duration_formatted,
                    "view_count": row[9] or 0,
                    "like_count": row[10] or 0,
                    "area_evaluada": row[11],
                    "tema_principal": row[12],
                    "quality_score": float(row[13]) if row[13] else 0.0,
                    "educational_value": float(row[14]) if row[14] else 0.0,
                    "difficulty_level": difficulty_level,
                    "recommended_for": subject_name
                }
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error getting video recommendations: {e}")
            return []
    
    def format_duration(self, seconds: Optional[int]) -> str:
        """Format duration in seconds to human readable format"""
        if not seconds:
            return "N/A"
        
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        
        if minutes < 60:
            return f"{minutes}:{remaining_seconds:02d}"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}:{remaining_minutes:02d}:{remaining_seconds:02d}"
    
    def create_weekly_schedule(self, analysis: Dict[str, Any], total_weeks: int = 8) -> Dict[str, Any]:
        """Create detailed weekly study schedule"""
        logger.info(f"Creating {total_weeks}-week schedule...")
        
        weekly_schedule = {}
        priority_subjects = analysis["priority_subjects"]
        study_hours = analysis["study_hours_needed"]
        
        for week in range(1, total_weeks + 1):
            week_key = f"week_{week}"
            
            # Determine focus subjects for this week (rotate through priority subjects)
            focus_start = ((week - 1) * 2) % len(priority_subjects)
            focus_subjects = priority_subjects[focus_start:focus_start + 3]
            if len(focus_subjects) < 3 and focus_start > 0:
                focus_subjects.extend(priority_subjects[:3 - len(focus_subjects)])
            
            # Calculate study hours for the week
            week_total_hours = sum(study_hours.get(subj, 5) for subj in focus_subjects) // total_weeks * 2
            hours_per_day = max(2, week_total_hours // 5)  # 5 study days per week
            
            # Create daily schedule
            daily_plan = {}
            study_days = ["monday", "tuesday", "wednesday", "thursday", "friday"]
            
            for i, day in enumerate(study_days):
                day_subjects = focus_subjects[:2] if len(focus_subjects) >= 2 else focus_subjects
                hours_per_subject = hours_per_day // len(day_subjects) if day_subjects else 1
                
                daily_plan[day] = {
                    "subjects": day_subjects,
                    "hours_per_subject": hours_per_subject,
                    "total_hours": hours_per_day,
                    "activities": [
                        "Watch recommended videos",
                        "Take practice questions",
                        "Review difficult concepts",
                        "Complete exercises"
                    ],
                    "goals": [
                        f"Complete {hours_per_subject}h study in {subj}" for subj in day_subjects
                    ]
                }
            
            # Weekend review
            daily_plan["saturday"] = {
                "subjects": focus_subjects,
                "hours_per_subject": 1,
                "total_hours": 2,
                "activities": ["Review week's material", "Practice tests"],
                "goals": ["Consolidate weekly learning"]
            }
            
            daily_plan["sunday"] = {
                "subjects": [],
                "hours_per_subject": 0,
                "total_hours": 0,
                "activities": ["Rest", "Light review if needed"],
                "goals": ["Prepare for next week"]
            }
            
            # Week-specific milestones
            if week <= 2:
                goals = ["Build foundational understanding", "Identify knowledge gaps"]
            elif week <= 4:
                goals = ["Strengthen weak areas", "Practice problem solving"]
            elif week <= 6:
                goals = ["Master key concepts", "Improve speed and accuracy"]
            else:
                goals = ["Final review", "Practice under exam conditions"]
            
            weekly_schedule[week_key] = {
                "week_number": week,
                "focus_subjects": focus_subjects,
                "daily_plan": daily_plan,
                "total_hours": sum(day.get("total_hours", 0) for day in daily_plan.values()),
                "weekly_goals": goals,
                "milestones": [
                    f"Complete study plan for {', '.join(focus_subjects)}",
                    "Assess progress with practice questions"
                ]
            }
        
        return weekly_schedule
    
    def generate_complete_study_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complete integrated study plan"""
        logger.info("Generating complete study plan...")
        
        try:
            # Step 1: Analyze diagnostic results
            diagnostic_results = user_profile.get("diagnostic_results", {})
            analysis = self.analyze_diagnostic_results(diagnostic_results)
            
            # Step 2: Get video recommendations for each subject
            video_recommendations = {}
            for subject in analysis["priority_subjects"]:
                difficulty = analysis["difficulty_levels"].get(subject, "intermediate")
                videos = self.get_video_recommendations(subject, difficulty, limit=10)
                video_recommendations[subject] = videos
            
            # Step 3: Create weekly schedule
            weekly_schedule = self.create_weekly_schedule(analysis)
            
            # Step 4: Generate study plan structure
            plan_id = str(uuid.uuid4())
            created_at = datetime.now()
            
            study_plan = {
                "plan_id": plan_id,
                "created_at": created_at.isoformat(),
                "last_updated": created_at.isoformat(),
                "student_profile": user_profile,
                "diagnostic_analysis": analysis,
                "video_recommendations": video_recommendations,
                "weekly_schedule": weekly_schedule,
                "plan_summary": {
                    "duration_weeks": len(weekly_schedule),
                    "total_study_hours": sum(week["total_hours"] for week in weekly_schedule.values()),
                    "subjects_covered": len(analysis["priority_subjects"]),
                    "video_recommendations_count": sum(len(videos) for videos in video_recommendations.values()),
                    "priority_subjects": analysis["priority_subjects"][:3],
                    "overall_current_score": analysis["overall_score"],
                    "target_improvement": min(1.0, analysis["overall_score"] + 0.20)  # Target 20% improvement
                },
                "implementation_guide": {
                    "getting_started": [
                        "Review your diagnostic analysis",
                        "Start with your weakest subject",
                        "Watch recommended videos first",
                        "Take notes while studying"
                    ],
                    "daily_routine": [
                        "Follow the daily schedule",
                        "Watch 1-2 videos per subject",
                        "Practice questions immediately after videos",
                        "Review challenging concepts"
                    ],
                    "weekly_review": [
                        "Assess progress every Saturday",
                        "Identify areas needing more attention",
                        "Adjust next week's focus if needed"
                    ],
                    "success_tips": [
                        "Consistency is key - study daily",
                        "Quality over quantity",
                        "Don't skip the basics",
                        "Practice regularly",
                        "Track your progress"
                    ]
                },
                "progress_tracking": {
                    "weekly_checkpoints": [f"Week {i+1}: Complete assigned videos and practice" for i in range(len(weekly_schedule))],
                    "milestone_assessments": [
                        {"week": 2, "assessment": "Basic concepts mastery check"},
                        {"week": 4, "assessment": "Mid-plan progress evaluation"},
                        {"week": 6, "assessment": "Advanced concepts assessment"},
                        {"week": 8, "assessment": "Final readiness evaluation"}
                    ]
                }
            }
            
            return study_plan
            
        except Exception as e:
            logger.error(f"Error generating study plan: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to generate study plan: {str(e)}")

# API Endpoints

@router.post("/generate")
async def generate_study_plan(
    user_profile: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive study plan with real video recommendations
    
    Expected user_profile format:
    {
        "name": "Student Name",
        "grade": 11,
        "target_score": 350,
        "available_hours_per_day": 3,
        "diagnostic_results": {
            "Matemáticas": {"score": 0.65, "questions_answered": 20, "correct": 13},
            "Ciencias Naturales": {"score": 0.45, "questions_answered": 15, "correct": 7},
            ...
        }
    }
    """
    try:
        service = IntegratedStudyPlanService(db)
        study_plan = service.generate_complete_study_plan(user_profile)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Study plan generated successfully",
                "data": study_plan
            }
        )
        
    except Exception as e:
        logger.error(f"Error in generate_study_plan endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/video-recommendations/{subject_name}")
async def get_subject_video_recommendations(
    subject_name: str,
    difficulty_level: str = Query("intermediate", regex="^(basic|intermediate|advanced)$"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get video recommendations for a specific subject"""
    try:
        service = IntegratedStudyPlanService(db)
        videos = service.get_video_recommendations(subject_name, difficulty_level, limit)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Found {len(videos)} video recommendations for {subject_name}",
                "data": {
                    "subject": subject_name,
                    "difficulty_level": difficulty_level,
                    "video_count": len(videos),
                    "videos": videos
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting video recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subjects-overview")
async def get_subjects_overview(db: Session = Depends(get_db)):
    """Get overview of all subjects with video counts"""
    try:
        # Get subjects with video counts
        subjects_query = text("""
            SELECT s.id, s.name, s.description, s.color, COUNT(yc.id) as video_count
            FROM subjects s
            LEFT JOIN youtube_catalog yc ON s.id = yc.subject_id
            GROUP BY s.id, s.name, s.description, s.color
            ORDER BY video_count DESC
        """)
        
        result = db.execute(subjects_query)
        subjects = []
        
        for row in result:
            subjects.append({
                "id": str(row[0]),
                "name": row[1],
                "description": row[2],
                "color": row[3],
                "video_count": row[4],
                "has_videos": row[4] > 0
            })
        
        # Get total statistics
        total_videos_result = db.execute(text("SELECT COUNT(*) FROM youtube_catalog"))
        total_videos = total_videos_result.scalar()
        
        mapped_videos_result = db.execute(text("SELECT COUNT(*) FROM youtube_catalog WHERE subject_id IS NOT NULL"))
        mapped_videos = mapped_videos_result.scalar()
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Subjects overview retrieved successfully",
                "data": {
                    "subjects": subjects,
                    "statistics": {
                        "total_subjects": len(subjects),
                        "subjects_with_videos": len([s for s in subjects if s["has_videos"]]),
                        "total_videos": total_videos,
                        "mapped_videos": mapped_videos,
                        "mapping_coverage": (mapped_videos / total_videos * 100) if total_videos > 0 else 0
                    }
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting subjects overview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-diagnostic")
async def analyze_diagnostic_results(
    diagnostic_results: Dict[str, Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Analyze diagnostic test results and provide recommendations
    
    Expected format:
    {
        "Matemáticas": {"score": 0.65, "questions_answered": 20, "correct": 13},
        "Ciencias Naturales": {"score": 0.45, "questions_answered": 15, "correct": 7},
        ...
    }
    """
    try:
        service = IntegratedStudyPlanService(db)
        analysis = service.analyze_diagnostic_results(diagnostic_results)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Diagnostic analysis completed successfully",
                "data": {
                    "analysis": analysis,
                    "recommendations": {
                        "immediate_focus": analysis["priority_subjects"][:2],
                        "study_plan_recommended": analysis["overall_score"] < 0.70,
                        "intensive_support_needed": len(analysis["weaknesses"]) >= 3,
                        "strengths_to_maintain": [s["subject"] for s in analysis["strengths"]]
                    }
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error analyzing diagnostic results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-health")
async def check_system_health(db: Session = Depends(get_db)):
    """Check the health and status of the integrated study plan system"""
    try:
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "components": {}
        }
        
        # Check database connectivity
        try:
            db.execute(text("SELECT 1"))
            health_data["components"]["database"] = {"status": "healthy", "message": "Connected successfully"}
        except Exception as e:
            health_data["components"]["database"] = {"status": "unhealthy", "error": str(e)}
            health_data["status"] = "degraded"
        
        # Check subjects availability
        try:
            subjects_result = db.execute(text("SELECT COUNT(*) FROM subjects"))
            subject_count = subjects_result.scalar()
            health_data["components"]["subjects"] = {
                "status": "healthy" if subject_count > 0 else "warning",
                "count": subject_count,
                "message": f"{subject_count} subjects available"
            }
        except Exception as e:
            health_data["components"]["subjects"] = {"status": "unhealthy", "error": str(e)}
            health_data["status"] = "degraded"
        
        # Check video catalog availability
        try:
            videos_result = db.execute(text("SELECT COUNT(*) FROM youtube_catalog"))
            video_count = videos_result.scalar()
            
            mapped_videos_result = db.execute(text("SELECT COUNT(*) FROM youtube_catalog WHERE subject_id IS NOT NULL"))
            mapped_count = mapped_videos_result.scalar()
            
            health_data["components"]["video_catalog"] = {
                "status": "healthy" if video_count > 0 else "warning",
                "total_videos": video_count,
                "mapped_videos": mapped_count,
                "mapping_percentage": (mapped_count / video_count * 100) if video_count > 0 else 0,
                "message": f"{video_count} total videos, {mapped_count} mapped to subjects"
            }
        except Exception as e:
            health_data["components"]["video_catalog"] = {"status": "unhealthy", "error": str(e)}
            health_data["status"] = "degraded"
        
        # Overall system assessment
        component_statuses = [comp["status"] for comp in health_data["components"].values()]
        if "unhealthy" in component_statuses:
            health_data["status"] = "unhealthy"
        elif "warning" in component_statuses:
            health_data["status"] = "warning"
        
        return JSONResponse(
            status_code=200 if health_data["status"] in ["healthy", "warning"] else 503,
            content={
                "success": health_data["status"] != "unhealthy",
                "message": f"System status: {health_data['status']}",
                "data": health_data
            }
        )
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "message": "Health check failed",
                "error": str(e)
            }
        )