"""
API endpoint for diagnostic tests with IMAGE-ONLY questions for frontend testing
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Any, Optional
import random
import logging

from ..core.database import get_db
from ..models.question import Question
from ..models.subject import Subject

router = APIRouter(prefix="/diagnostic-images-test", tags=["diagnostic-images-test"])
logger = logging.getLogger(__name__)

@router.get("/subjects-with-image-questions")
async def get_subjects_with_image_questions(db: Session = Depends(get_db)):
    """
    Get subjects that have questions with images available for testing
    """
    try:
        # Query subjects with image question counts
        # Filter questions that have any image (main question image or option images)
        results = db.query(
            Subject.id,
            Subject.name,
            Subject.description,
            Subject.color,
            func.count(Question.id).label('image_question_count')
        ).join(Question, Subject.id == Question.subject_id)\
         .filter(
             or_(
                 and_(Question.pregunta_imagen.isnot(None), Question.pregunta_imagen != "", Question.pregunta_imagen != "No Aplica"),
                 and_(Question.opcion_a_imagen.isnot(None), Question.opcion_a_imagen != "", Question.opcion_a_imagen != "No Aplica"),
                 and_(Question.opcion_b_imagen.isnot(None), Question.opcion_b_imagen != "", Question.opcion_b_imagen != "No Aplica"),
                 and_(Question.opcion_c_imagen.isnot(None), Question.opcion_c_imagen != "", Question.opcion_c_imagen != "No Aplica"),
                 and_(Question.opcion_d_imagen.isnot(None), Question.opcion_d_imagen != "", Question.opcion_d_imagen != "No Aplica")
             )
         )\
         .group_by(Subject.id, Subject.name, Subject.description, Subject.color)\
         .order_by(Subject.name)\
         .all()
        
        subjects_data = []
        for result in results:
            image_question_count = result.image_question_count or 0
            
            # Determine how many questions we can provide (max 20)
            available_questions = min(20, image_question_count)
            
            # Determine availability status
            if image_question_count == 0:
                availability_status = "unavailable"
                availability_message = "Sin preguntas con imágenes"
                is_available = False
            elif image_question_count < 5:
                availability_status = "limited"
                availability_message = f"Solo {image_question_count} preguntas con imágenes disponibles"
                is_available = True
            else:
                availability_status = "available"
                availability_message = f"{available_questions} preguntas con imágenes disponibles"
                is_available = True
            
            subject_data = {
                "id": str(result.id),
                "name": result.name,
                "description": result.description,
                "color": result.color,
                "image_question_count": image_question_count,
                "available_for_test": available_questions,
                "availability_status": availability_status,
                "availability_message": availability_message,
                "is_available": is_available,
                "config": {
                    "total_questions": available_questions,
                    "time_limit_minutes": 30,  # Shorter test for image questions
                    "test_type": "image_questions_test"
                }
            }
            subjects_data.append(subject_data)
        
        logger.info(f"Retrieved {len(subjects_data)} subjects with image questions")
        return subjects_data
        
    except Exception as e:
        logger.error(f"Error getting subjects with image questions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting subjects: {str(e)}")

@router.get("/questions/{subject_id}")
async def get_image_questions_for_subject(
    subject_id: str,
    limit: int = Query(20, description="Number of questions to return (max 20)"),
    db: Session = Depends(get_db)
):
    """
    Get questions with images for a specific subject for frontend testing
    """
    try:
        # Limit to maximum 20 questions
        limit = min(limit, 20)
        
        # Get subject first
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        # Query questions that have images for this subject
        questions_query = db.query(Question)\
            .filter(and_(
                Question.subject_id == subject_id,
                or_(
                    and_(Question.pregunta_imagen.isnot(None), Question.pregunta_imagen != "", Question.pregunta_imagen != "No Aplica"),
                    and_(Question.opcion_a_imagen.isnot(None), Question.opcion_a_imagen != "", Question.opcion_a_imagen != "No Aplica"),
                    and_(Question.opcion_b_imagen.isnot(None), Question.opcion_b_imagen != "", Question.opcion_b_imagen != "No Aplica"),
                    and_(Question.opcion_c_imagen.isnot(None), Question.opcion_c_imagen != "", Question.opcion_c_imagen != "No Aplica"),
                    and_(Question.opcion_d_imagen.isnot(None), Question.opcion_d_imagen != "", Question.opcion_d_imagen != "No Aplica")
                )
            ))\
            .order_by(func.random())\
            .limit(limit)
        
        questions = questions_query.all()
        
        if not questions:
            raise HTTPException(
                status_code=404, 
                detail=f"No questions with images found for subject {subject.name}"
            )
        
        questions_data = []
        for q in questions:
            # Format the question data for frontend
            question_data = {
                "id": str(q.id),
                "pregunta_texto": q.pregunta_texto,
                "opcion_a": q.opcion_a,
                "opcion_b": q.opcion_b,
                "opcion_c": q.opcion_c,
                "opcion_d": q.opcion_d,
                "respuesta_correcta": q.respuesta_correcta,
                "dificultad": q.dificultad or 1,
                "tiempo_estimado": q.tiempo_estimado or 60,
                "puntos_xp": q.puntos_xp or 10,
                
                # Image URLs
                "pregunta_imagen": q.pregunta_imagen if q.pregunta_imagen and q.pregunta_imagen.strip() and q.pregunta_imagen != "No Aplica" else None,
                "opcion_a_imagen": q.opcion_a_imagen if q.opcion_a_imagen and q.opcion_a_imagen.strip() and q.opcion_a_imagen != "No Aplica" else None,
                "opcion_b_imagen": q.opcion_b_imagen if q.opcion_b_imagen and q.opcion_b_imagen.strip() and q.opcion_b_imagen != "No Aplica" else None,
                "opcion_c_imagen": q.opcion_c_imagen if q.opcion_c_imagen and q.opcion_c_imagen.strip() and q.opcion_c_imagen != "No Aplica" else None,
                "opcion_d_imagen": q.opcion_d_imagen if q.opcion_d_imagen and q.opcion_d_imagen.strip() and q.opcion_d_imagen != "No Aplica" else None,
                
                # Metadata for testing
                "subject_name": subject.name,
                "requiere_imagen": q.requiere_imagen,
                "has_main_image": bool(q.pregunta_imagen and q.pregunta_imagen.strip() and q.pregunta_imagen != "No Aplica"),
                "has_option_images": any([
                    q.opcion_a_imagen and q.opcion_a_imagen.strip() and q.opcion_a_imagen != "No Aplica",
                    q.opcion_b_imagen and q.opcion_b_imagen.strip() and q.opcion_b_imagen != "No Aplica",
                    q.opcion_c_imagen and q.opcion_c_imagen.strip() and q.opcion_c_imagen != "No Aplica",
                    q.opcion_d_imagen and q.opcion_d_imagen.strip() and q.opcion_d_imagen != "No Aplica"
                ])
            }
            questions_data.append(question_data)
        
        response = {
            "subject": {
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description
            },
            "questions": questions_data,
            "total_questions": len(questions_data),
            "test_config": {
                "total_questions": len(questions_data),
                "time_limit_minutes": 30,
                "test_type": "image_questions_test",
                "all_questions_have_images": True
            }
        }
        
        logger.info(f"Retrieved {len(questions_data)} image questions for subject {subject.name}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting image questions for subject {subject_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting questions: {str(e)}")

@router.get("/test-summary")
async def get_image_test_summary(db: Session = Depends(get_db)):
    """
    Get summary of available image questions for testing across all subjects
    """
    try:
        results = db.query(
            Subject.name,
            func.count(Question.id).label('image_questions')
        ).join(Question, Subject.id == Question.subject_id)\
         .filter(Question.requiere_imagen == True)\
         .group_by(Subject.name)\
         .order_by(func.count(Question.id).desc())\
         .all()
        
        summary = []
        total_available = 0
        
        for result in results:
            available_for_test = min(20, result.image_questions)
            total_available += available_for_test
            
            summary.append({
                "subject_name": result.name,
                "total_image_questions": result.image_questions,
                "available_for_test": available_for_test,
                "status": "ready" if result.image_questions >= 5 else "limited" if result.image_questions > 0 else "unavailable"
            })
        
        return {
            "summary": summary,
            "total_subjects_with_images": len(summary),
            "total_questions_available_for_test": total_available,
            "test_info": {
                "max_questions_per_subject": 20,
                "test_duration_minutes": 30,
                "focus": "Questions with visual content only"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting image test summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")