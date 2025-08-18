"""Public diagnostic routes that don't require authentication"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..models.subject import Subject
from ..models.diagnostic_test import DiagnosticTest
from ..schemas.diagnostic_test import DIAGNOSTIC_TEST_CONFIGS
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/diagnostic-public", tags=["diagnostic-public"])

@router.get("/tests")
async def get_public_tests(db: Session = Depends(get_db)):
    """Get diagnostic tests without authentication"""
    try:
        # Return empty list for public access
        return []
    except Exception as e:
        logger.error(f"Error getting public tests: {e}")
        return []

@router.get("/subjects")
async def get_public_subjects(db: Session = Depends(get_db)):
    """Get subjects without authentication"""
    try:
        subjects = db.query(Subject).all()
        return [
            {
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description,
                "icon_url": subject.icon_url,
                "color": subject.color,
                "config": DIAGNOSTIC_TEST_CONFIGS.get(subject.name.lower(), {
                    "total_questions": 45,
                    "time_limit_minutes": 90,
                    "topics": []
                })
            }
            for subject in subjects
        ]
    except Exception as e:
        logger.error(f"Error getting subjects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analytics/personal")
async def get_public_analytics():
    """Return empty analytics for public access"""
    return {
        "total_tests": 0,
        "average_score": 0,
        "total_time_spent": 0,
        "subjects_progress": {},
        "recent_activity": []
    }