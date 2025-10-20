"""
Simple Study Plan Generator - Genera planes de estudio personalizados basados en diagnostic tests
usando el catálogo de videos de YouTube
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
import logging
import json
import uuid
from datetime import datetime

from ..core.database import get_db
from ..models.study_plan import StudyPlan

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diagnostic-public", tags=["study-plans"])

@router.post("/generate-study-plan")
async def generate_simple_study_plan(
    request_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Genera un plan de estudio personalizado basado en el diagnostic test
    
    Body:
    {
        "test_id": "diagnostic-test-...",
        "subject_id": "550e8400-...",
        "user_id": "optional-user-id" 
    }
    """
    try:
        test_id = request_data.get('test_id')
        subject_id = request_data.get('subject_id')
        user_id = request_data.get('user_id', None)  # None for anonymous users
        
        if not test_id or not subject_id:
            raise HTTPException(
                status_code=400,
                detail="test_id and subject_id are required"
            )
        
        logger.info(f"🎯 Generating study plan for test {test_id}")
        
        # 1. Get diagnostic test results
        diagnostic_query = text("""
            SELECT 
                dt.score_percentage,
                dt.weaknesses,
                dt.score_by_topic,
                s.name as subject_name
            FROM diagnostic_tests dt
            JOIN subjects s ON dt.subject_id = s.id
            WHERE dt.id = :test_id
        """)
        
        diag_result = db.execute(diagnostic_query, {"test_id": test_id}).fetchone()
        
        if not diag_result:
            raise HTTPException(status_code=404, detail="Diagnostic test not found")
        
        score_percentage = diag_result[0]
        weaknesses = diag_result[1] or []
        score_by_topic = diag_result[2] or {}
        subject_name = diag_result[3]
        
        # 2. Get incorrect questions and their topics
        incorrect_query = text("""
            SELECT DISTINCT
                t.name as topic_name,
                q.competencia,
                q.componente,
                COUNT(*) as error_count
            FROM diagnostic_test_answers dta
            JOIN questions q ON dta.question_id = q.id
            LEFT JOIN topics t ON q.topic_id = t.id
            WHERE dta.diagnostic_test_id = :test_id
            AND dta.is_correct = false
            GROUP BY t.name, q.competencia, q.componente
            ORDER BY error_count DESC
        """)
        
        incorrect_topics = db.execute(incorrect_query, {"test_id": test_id}).fetchall()
        
        # 3. Get recommended videos from catalog matching weak topics
        videos_query = text("""
            SELECT 
                yc.id,
                yc.youtube_id,
                yc.title,
                yc.youtube_url,
                yc.channel_name,
                yc.duration_minutes,
                yc.quality_score,
                yc.description,
                yc.codigo_tema,
                yc.icfes_competence,
                yc.icfes_component
            FROM youtube_catalog yc
            WHERE yc.subject_id = :subject_id
            AND yc.is_active = true
            ORDER BY yc.quality_score DESC
            LIMIT 20
        """)
        
        videos = db.execute(videos_query, {"subject_id": subject_id}).fetchall()
        
        if not videos:
            logger.warning(f"No videos found for subject {subject_id}")
        
        # 4. Build study plan structure
        units = []
        unit_number = 1
        
        # Group videos by weak topics
        for topic in incorrect_topics[:6]:  # Top 6 weak areas
            topic_name = topic[0] or "General"
            competencia = topic[1] or ""
            componente = topic[2] or ""
            
            # Find matching videos
            matching_videos = []
            for video in videos:
                # Simple matching logic - can be improved with LLM
                video_comp = video[9] or ""
                video_component = video[10] or ""
                
                if (competencia and competencia.lower() in video_comp.lower()) or \
                   (componente and componente.lower() in video_component.lower()) or \
                   (topic_name.lower() in (video[2] or "").lower()):
                    matching_videos.append({
                        "id": str(video[0]),
                        "youtube_id": video[1],
                        "title": video[2],
                        "url": video[3] or f"https://www.youtube.com/watch?v={video[1]}",
                        "channel": video[4],
                        "duration_minutes": video[5] or 10,
                        "xp": 100 + (video[5] or 10) * 2,
                        "tema_principal": topic_name,
                        "recommendation_reason": f"Recomendado para reforzar {topic_name}"
                    })
            
            # If no specific matches, add general videos for the subject
            if not matching_videos and videos:
                for video in videos[:3]:
                    matching_videos.append({
                        "id": str(video[0]),
                        "youtube_id": video[1],
                        "title": video[2],
                        "url": video[3] or f"https://www.youtube.com/watch?v={video[1]}",
                        "channel": video[4],
                        "duration_minutes": video[5] or 10,
                        "xp": 100 + (video[5] or 10) * 2,
                        "tema_principal": topic_name,
                        "recommendation_reason": f"Video educativo sobre {subject_name}"
                    })
            
            if matching_videos:
                units.append({
                    "unit_number": unit_number,
                    "title": topic_name,
                    "description": f"Videos sobre {topic_name} en {subject_name}",
                    "videos": matching_videos[:5],  # Max 5 videos per unit
                    "priority": "alta" if unit_number <= 3 else "media"
                })
                unit_number += 1
        
        # 5. Calculate totals
        total_videos = sum(len(unit['videos']) for unit in units)
        total_duration = sum(
            sum(v['duration_minutes'] for v in unit['videos'])
            for unit in units
        )
        
        # 6. Save study plan to database
        plan_data = {
            "metadata": {
                "test_id": test_id,
                "subject_id": subject_id,
                "subject_name": subject_name,
                "score_percentage": float(score_percentage) if score_percentage else 0,
                "generated_at": datetime.utcnow().isoformat(),
                "total_units": len(units),
                "total_videos": total_videos,
                "total_duration_minutes": total_duration
            },
            "units": units,
            "weaknesses": weaknesses,
            "recommendations": {
                "study_frequency": "3-4 veces por semana",
                "session_duration": "30-45 minutos",
                "estimated_completion": "4 semanas"
            }
        }
        
        # Create or update study plan (only update if we have a user_id)
        existing_plan = None
        if user_id:
            existing_plan = db.query(StudyPlan).filter(
                StudyPlan.user_id == user_id,
                StudyPlan.subject_id == subject_id,
                StudyPlan.is_active == True
            ).first()

        if existing_plan:
            existing_plan.plan_data = plan_data
            existing_plan.total_units = len(units)
            existing_plan.updated_at = datetime.utcnow()
            plan_id = str(existing_plan.id)
            logger.info(f"Updated existing plan {plan_id}")
        else:
            new_plan = StudyPlan(
                id=uuid.uuid4(),
                user_id=user_id if user_id else None,
                subject_id=subject_id,
                plan_name=f"Plan de Estudio - {subject_name}",
                plan_data=plan_data,
                total_units=len(units),
                completed_units=0,
                progress_percentage=0,
                is_active=True,
                generated_at=datetime.utcnow()
            )
            db.add(new_plan)
            plan_id = str(new_plan.id)
            logger.info(f"Created new plan {plan_id}")
        
        db.commit()
        
        logger.info(f"✅ Study plan generated successfully: {plan_id}")
        
        return {
            "success": True,
            "plan_id": plan_id,
            "plan_data": plan_data,
            "message": "Plan de estudio generado exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating study plan: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generating study plan: {str(e)}")


@router.get("/study-plan/{plan_id}")
async def get_study_plan(plan_id: str, db: Session = Depends(get_db)):
    """Get a study plan by ID"""
    try:
        plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Study plan not found")
        
        return {
            "success": True,
            "plan_id": str(plan.id),
            "plan_data": plan.plan_data,
            "progress_percentage": float(plan.progress_percentage) if plan.progress_percentage else 0,
            "completed_units": plan.completed_units,
            "total_units": plan.total_units
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving study plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

