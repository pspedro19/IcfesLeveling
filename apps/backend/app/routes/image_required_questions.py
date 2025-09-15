"""
API endpoint for getting questions that require images for testing
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..core.database import get_db
from ..models.subject import Subject
from ..models.question import Question

router = APIRouter(prefix="/diagnostic-public", tags=["image-questions"])
logger = logging.getLogger(__name__)

@router.get("/questions-with-images")
async def get_questions_requiring_images(
    subject_name: Optional[str] = Query(None, description="Filter by subject name"),
    limit: int = Query(50, description="Maximum number of questions to return"),
    db: Session = Depends(get_db)
):
    """
    Get questions that require images for testing purposes
    
    Args:
        subject_name: Optional subject filter
        limit: Maximum number of questions to return
        
    Returns:
        List of questions that require images with their image URLs
    """
    try:
        query = db.query(
            Question.id,
            Question.pregunta_texto,
            Question.opcion_a,
            Question.opcion_b, 
            Question.opcion_c,
            Question.opcion_d,
            Question.pregunta_imagen,
            Question.opcion_a_imagen,
            Question.opcion_b_imagen,
            Question.opcion_c_imagen,
            Question.opcion_d_imagen,
            Subject.name.label('subject_name')
        ).join(Subject, Question.subject_id == Subject.id)\
         .filter(Question.requiere_imagen == True)
        
        if subject_name:
            query = query.filter(Subject.name.ilike(f"%{subject_name}%"))
            
        results = query.order_by(Subject.name, Question.id)\
                      .limit(limit)\
                      .all()
        
        questions_data = []
        for result in results:
            question_data = {
                "id": str(result.id),
                "subject_name": result.subject_name,
                "pregunta_texto": result.pregunta_texto[:200] + "..." if len(result.pregunta_texto or "") > 200 else result.pregunta_texto,
                "pregunta_imagen": result.pregunta_imagen,
                "opciones": {
                    "a": {
                        "texto": result.opcion_a,
                        "imagen": result.opcion_a_imagen
                    },
                    "b": {
                        "texto": result.opcion_b, 
                        "imagen": result.opcion_b_imagen
                    },
                    "c": {
                        "texto": result.opcion_c,
                        "imagen": result.opcion_c_imagen
                    },
                    "d": {
                        "texto": result.opcion_d,
                        "imagen": result.opcion_d_imagen
                    }
                },
                "has_main_image": bool(result.pregunta_imagen and result.pregunta_imagen.strip() and result.pregunta_imagen != "No Aplica"),
                "has_option_images": any([
                    result.opcion_a_imagen and result.opcion_a_imagen.strip() and result.opcion_a_imagen != "No Aplica",
                    result.opcion_b_imagen and result.opcion_b_imagen.strip() and result.opcion_b_imagen != "No Aplica", 
                    result.opcion_c_imagen and result.opcion_c_imagen.strip() and result.opcion_c_imagen != "No Aplica",
                    result.opcion_d_imagen and result.opcion_d_imagen.strip() and result.opcion_d_imagen != "No Aplica"
                ])
            }
            questions_data.append(question_data)
        
        # Summary statistics  
        summary_query = db.query(
            Subject.name.label('subject_name'),
            db.func.count(Question.id).label('count')
        ).join(Subject, Question.subject_id == Subject.id)\
         .filter(Question.requiere_imagen == True)\
         .group_by(Subject.name)\
         .order_by(db.func.count(Question.id).desc())\
         .all()
        
        summary = {subject.subject_name: subject.count for subject in summary_query}
        
        response = {
            "questions": questions_data,
            "total_found": len(questions_data),
            "summary_by_subject": summary,
            "filter_applied": subject_name if subject_name else "All subjects",
            "limit_applied": limit
        }
        
        logger.info(f"Retrieved {len(questions_data)} questions requiring images" + 
                   (f" for subject '{subject_name}'" if subject_name else " for all subjects"))
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting questions requiring images: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting questions requiring images: {str(e)}")

@router.get("/image-questions-summary")  
async def get_image_questions_summary(db: Session = Depends(get_db)):
    """
    Get summary of questions requiring images by subject
    """
    try:
        results = db.query(
            Subject.name,
            db.func.count(Question.id).label('total_questions'),
            db.func.count(db.case([(Question.requiere_imagen == True, 1)])).label('questions_with_images'),
            db.func.count(db.case([(Question.pregunta_imagen.isnot(None), 1)])).label('questions_with_main_image'),
            db.func.count(db.case([
                (db.or_(
                    Question.opcion_a_imagen.isnot(None),
                    Question.opcion_b_imagen.isnot(None), 
                    Question.opcion_c_imagen.isnot(None),
                    Question.opcion_d_imagen.isnot(None)
                ), 1)
            ])).label('questions_with_option_images')
        ).join(Subject, Question.subject_id == Subject.id)\
         .group_by(Subject.name)\
         .order_by(Subject.name)\
         .all()
        
        summary = []
        for result in results:
            percentage_with_images = (result.questions_with_images / result.total_questions * 100) if result.total_questions > 0 else 0
            summary.append({
                "subject_name": result.name,
                "total_questions": result.total_questions,
                "questions_requiring_images": result.questions_with_images,
                "questions_with_main_image": result.questions_with_main_image,
                "questions_with_option_images": result.questions_with_option_images,
                "percentage_requiring_images": round(percentage_with_images, 1)
            })
        
        return {
            "summary": summary,
            "total_subjects": len(summary),
            "total_image_questions": sum(s["questions_requiring_images"] for s in summary)
        }
        
    except Exception as e:
        logger.error(f"Error getting image questions summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")