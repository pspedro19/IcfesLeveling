from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from ..core.database import get_db
from ..schemas.diagnostic_test import DiagnosticTestCreate, DiagnosticTestSubmit
from ..services.diagnostic_public_service import DiagnosticPublicService

logger = logging.getLogger("icfes.routes.diagnostic_public")

router = APIRouter(prefix="/diagnostic-public", tags=["diagnostic-public"])

class DiagnosticStartRequest(BaseModel):
    subject_id: str
    user_id: Optional[str] = None

class DiagnosticAnswerRequest(BaseModel):
    test_id: str
    question_id: str
    user_answer: str
    response_time_ms: int = 0

class DiagnosticCompleteRequest(BaseModel):
    test_id: str

@router.get("/subjects")
async def get_subjects_public(db: Session = Depends(get_db)):
    try:
        service = DiagnosticPublicService(db)
        return service.get_subjects()
    except Exception as e:
        logger.error(f"Error in get_subjects_public endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subjects.")

@router.post("/tests")
async def create_diagnostic_test_public(test_data: DiagnosticTestCreate, db: Session = Depends(get_db)):
    try:
        service = DiagnosticPublicService(db)
        return service.create_public_test(test_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating test: {str(e)}")

@router.get("/tests/{test_id}/questions")
async def get_diagnostic_questions_public(test_id: str, db: Session = Depends(get_db)):
    try:
        service = DiagnosticPublicService(db)
        return service.get_test_questions(test_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error getting questions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting questions: {str(e)}")

@router.post("/tests/{test_id}/submit")
async def submit_diagnostic_test_public(test_id: str, submit_data: DiagnosticTestSubmit, db: Session = Depends(get_db)):
    try:
        service = DiagnosticPublicService(db)
        return service.submit_public_test(test_id, submit_data)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting test: {str(e)}")

@router.get("/results/{test_id}")
async def get_diagnostic_results_public(test_id: str, db: Session = Depends(get_db)):
    try:
        service = DiagnosticPublicService(db)
        return service.get_diagnostic_results(test_id)
    except Exception as e:
        logger.error(f"Error getting diagnostic results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting diagnostic results: {str(e)}")
