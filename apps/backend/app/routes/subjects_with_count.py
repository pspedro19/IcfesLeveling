"""
API endpoint for getting subjects with question counts
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import logging

from ..core.database import get_db
from ..models.subject import Subject
from ..models.question import Question

router = APIRouter(prefix="/diagnostic-public", tags=["diagnostic-subjects"])
logger = logging.getLogger(__name__)

@router.get("/subjects-with-counts")
async def get_subjects_with_question_counts(db: Session = Depends(get_db)):
    """
    Get all subjects with their question counts for diagnostic availability
    
    Returns:
        List of subjects with question counts and availability status
    """
    try:
        # Query subjects with question counts
        results = db.query(
            Subject.id,
            Subject.name,
            Subject.description,
            Subject.color,
            func.count(Question.id).label('question_count')
        ).outerjoin(Question, Subject.id == Question.subject_id)\
         .group_by(Subject.id, Subject.name, Subject.description, Subject.color)\
         .order_by(Subject.name)\
         .all()
        
        subjects_with_counts = []
        
        for result in results:
            question_count = result.question_count or 0
            
            # Determine availability status
            if question_count == 0:
                availability_status = "unavailable"
                availability_message = "Sin preguntas disponibles"
            elif question_count < 20:
                availability_status = "limited"
                availability_message = f"Pocas preguntas disponibles ({question_count})"
            else:
                availability_status = "available"
                availability_message = f"{question_count} preguntas disponibles"
            
            subject_data = {
                "id": str(result.id),
                "name": result.name,
                "description": result.description,
                "color": result.color,
                "question_count": question_count,
                "availability_status": availability_status,
                "availability_message": availability_message,
                "is_available": question_count > 0
            }
            
            subjects_with_counts.append(subject_data)
        
        logger.info(f"Retrieved {len(subjects_with_counts)} subjects with question counts")
        
        return subjects_with_counts
        
    except Exception as e:
        logger.error(f"Error getting subjects with counts: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting subjects with counts: {str(e)}")