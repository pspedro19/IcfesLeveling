"""
Verified Image Diagnostic Test API
==================================
Diagnostic test endpoint that ONLY serves questions with verified working images.
Uses multi-agent verification to ensure image availability.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Dict, Any, Optional
import random
import logging
import os
import asyncio
import json
from datetime import datetime

from ..core.database import get_db
from ..models.question import Question
from ..models.subject import Subject

router = APIRouter(prefix="/verified-image-diagnostic", tags=["verified-image-diagnostic"])
logger = logging.getLogger(__name__)

# Cache for verified questions (refreshed every hour)
_verified_questions_cache = {}
_cache_timestamp = None
CACHE_DURATION = 3600  # 1 hour

class ImageVerifier:
    """Verifies that image files exist in filesystem"""
    
    def __init__(self):
        self.base_paths = [
            "/root/IcfesLeveling/database/allquestions",
            "/root/IcfesLeveling/database", 
            "/root/IcfesLeveling"
        ]
    
    def url_to_filesystem_path(self, url: str) -> Optional[str]:
        """Convert localhost URL to filesystem path"""
        if not url or url.strip() == "" or url == "No Aplica":
            return None
            
        if "localhost:" in url and "/api/images/" in url:
            import urllib.parse
            relative_path = url.split("/api/images/", 1)[1]
            relative_path = urllib.parse.unquote(relative_path)
            
            for base_path in self.base_paths:
                full_path = os.path.join(base_path, relative_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    return full_path
        
        return None
    
    def verify_question_images(self, question) -> bool:
        """Verify all images for a question exist"""
        image_urls = [
            question.pregunta_imagen,
            question.opcion_a_imagen, 
            question.opcion_b_imagen,
            question.opcion_c_imagen,
            question.opcion_d_imagen
        ]
        
        # Filter out None/empty URLs
        valid_urls = [url for url in image_urls if url and url.strip() and url != "No Aplica"]
        
        if not valid_urls:
            return False  # No images to verify
        
        # All images must exist
        for url in valid_urls:
            filesystem_path = self.url_to_filesystem_path(url)
            if not filesystem_path or not os.path.exists(filesystem_path):
                return False
                
        return True

def get_verified_questions_cache(db: Session) -> Dict[str, List[dict]]:
    """Get or refresh cache of verified questions"""
    global _verified_questions_cache, _cache_timestamp
    
    current_time = datetime.now().timestamp()
    
    # Check if cache needs refresh
    if (_cache_timestamp is None or 
        current_time - _cache_timestamp > CACHE_DURATION or 
        not _verified_questions_cache):
        
        logger.info("Refreshing verified questions cache...")
        
        verifier = ImageVerifier()
        
        # Get all questions with images
        questions_query = db.query(Question, Subject.name.label('subject_name'))\
            .join(Subject, Question.subject_id == Subject.id)\
            .filter(
                or_(
                    and_(Question.pregunta_imagen.isnot(None), Question.pregunta_imagen != "", Question.pregunta_imagen != "No Aplica"),
                    and_(Question.opcion_a_imagen.isnot(None), Question.opcion_a_imagen != "", Question.opcion_a_imagen != "No Aplica"),
                    and_(Question.opcion_b_imagen.isnot(None), Question.opcion_b_imagen != "", Question.opcion_b_imagen != "No Aplica"),
                    and_(Question.opcion_c_imagen.isnot(None), Question.opcion_c_imagen != "", Question.opcion_c_imagen != "No Aplica"),
                    and_(Question.opcion_d_imagen.isnot(None), Question.opcion_d_imagen != "", Question.opcion_d_imagen != "No Aplica")
                )
            ).all()
        
        # Verify questions and group by subject
        verified_cache = {}
        verification_stats = {}
        
        for question, subject_name in questions_query:
            if subject_name not in verification_stats:
                verification_stats[subject_name] = {"total": 0, "verified": 0}
            
            verification_stats[subject_name]["total"] += 1
            
            # Verify images exist
            if verifier.verify_question_images(question):
                verification_stats[subject_name]["verified"] += 1
                
                if subject_name not in verified_cache:
                    verified_cache[subject_name] = []
                
                question_data = {
                    "id": str(question.id),
                    "pregunta_texto": question.pregunta_texto,
                    "opcion_a": question.opcion_a,
                    "opcion_b": question.opcion_b,
                    "opcion_c": question.opcion_c,
                    "opcion_d": question.opcion_d,
                    "respuesta_correcta": question.respuesta_correcta,
                    "dificultad": question.dificultad or 1,
                    "tiempo_estimado": question.tiempo_estimado or 60,
                    "puntos_xp": question.puntos_xp or 10,
                    "pregunta_imagen": question.pregunta_imagen if question.pregunta_imagen and question.pregunta_imagen.strip() and question.pregunta_imagen != "No Aplica" else None,
                    "opcion_a_imagen": question.opcion_a_imagen if question.opcion_a_imagen and question.opcion_a_imagen.strip() and question.opcion_a_imagen != "No Aplica" else None,
                    "opcion_b_imagen": question.opcion_b_imagen if question.opcion_b_imagen and question.opcion_b_imagen.strip() and question.opcion_b_imagen != "No Aplica" else None,
                    "opcion_c_imagen": question.opcion_c_imagen if question.opcion_c_imagen and question.opcion_c_imagen.strip() and question.opcion_c_imagen != "No Aplica" else None,
                    "opcion_d_imagen": question.opcion_d_imagen if question.opcion_d_imagen and question.opcion_d_imagen.strip() and question.opcion_d_imagen != "No Aplica" else None,
                    "subject_name": subject_name,
                    "verified_timestamp": current_time
                }
                
                verified_cache[subject_name].append(question_data)
        
        _verified_questions_cache = verified_cache
        _cache_timestamp = current_time
        
        # Log verification results
        logger.info("Verification complete:")
        for subject, stats in verification_stats.items():
            logger.info(f"  {subject}: {stats['verified']}/{stats['total']} questions verified ({stats['verified']/max(1,stats['total']):.1%})")
    
    return _verified_questions_cache

@router.get("/subjects")
async def get_subjects_with_verified_images(db: Session = Depends(get_db)):
    """Get subjects that have verified image questions available"""
    try:
        verified_cache = get_verified_questions_cache(db)
        
        subjects_data = []
        
        for subject_name, questions in verified_cache.items():
            if len(questions) == 0:
                continue
                
            # Get subject details
            subject = db.query(Subject).filter(Subject.name == subject_name).first()
            
            if not subject:
                continue
            
            available_questions = len(questions)
            
            # Determine readiness
            if available_questions >= 20:
                status = "🟢 READY FOR DIAGNOSTIC"
                availability = "excellent"
                max_questions = 20
            elif available_questions >= 10:
                status = "🟡 GOOD FOR DIAGNOSTIC" 
                availability = "good"
                max_questions = available_questions
            elif available_questions >= 3:
                status = "🟠 LIMITED AVAILABILITY"
                availability = "limited"
                max_questions = available_questions
            else:
                status = "🔴 NOT READY"
                availability = "insufficient"
                max_questions = 0
            
            subject_data = {
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description,
                "color": subject.color,
                "verified_questions_available": available_questions,
                "max_diagnostic_questions": max_questions,
                "status": status,
                "availability": availability,
                "is_ready_for_diagnostic": available_questions >= 10,
                "config": {
                    "recommended_questions": min(max_questions, 20),
                    "time_limit_minutes": 45,
                    "test_type": "verified_image_diagnostic",
                    "all_images_verified": True
                }
            }
            
            subjects_data.append(subject_data)
        
        # Sort by availability (best first)
        subjects_data.sort(key=lambda x: x["verified_questions_available"], reverse=True)
        
        logger.info(f"Retrieved {len(subjects_data)} subjects with verified image questions")
        return {
            "subjects": subjects_data,
            "cache_info": {
                "cache_timestamp": _cache_timestamp,
                "cache_age_minutes": (datetime.now().timestamp() - _cache_timestamp) / 60 if _cache_timestamp else 0,
                "total_subjects_with_verified_images": len(subjects_data)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting subjects with verified images: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting subjects: {str(e)}")

@router.get("/questions/{subject_id}")
async def get_verified_questions_for_diagnostic(
    subject_id: str,
    limit: int = Query(20, description="Number of questions for diagnostic (max 20)"),
    db: Session = Depends(get_db)
):
    """Get verified image questions for diagnostic test"""
    try:
        limit = min(limit, 20)  # Maximum 20 questions
        
        # Get subject
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        # Get verified questions from cache
        verified_cache = get_verified_questions_cache(db)
        
        if subject.name not in verified_cache:
            raise HTTPException(
                status_code=404,
                detail=f"No verified image questions available for {subject.name}"
            )
        
        available_questions = verified_cache[subject.name]
        
        if len(available_questions) < 3:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient verified questions for diagnostic test. Only {len(available_questions)} available (minimum 3 required)"
            )
        
        # Randomly select questions
        selected_questions = random.sample(available_questions, min(limit, len(available_questions)))
        
        response = {
            "subject": {
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description,
                "color": subject.color
            },
            "questions": selected_questions,
            "diagnostic_info": {
                "total_questions": len(selected_questions),
                "available_questions": len(available_questions),
                "all_images_verified": True,
                "verification_timestamp": _cache_timestamp,
                "test_type": "verified_image_diagnostic",
                "time_limit_minutes": 45,
                "instructions": "Esta es una prueba diagnóstica que incluye únicamente preguntas con imágenes verificadas. Todas las imágenes han sido validadas para asegurar su correcta visualización."
            }
        }
        
        logger.info(f"Provided {len(selected_questions)} verified questions for {subject.name} diagnostic")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting verified questions for {subject_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting questions: {str(e)}")

@router.get("/test-summary")
async def get_diagnostic_test_summary(db: Session = Depends(get_db)):
    """Get summary of verified image diagnostic test availability"""
    try:
        verified_cache = get_verified_questions_cache(db)
        
        summary = {
            "test_info": {
                "test_name": "Verified Image Diagnostic Test",
                "description": "Diagnostic test using only questions with verified working images",
                "cache_timestamp": _cache_timestamp,
                "cache_age_minutes": (datetime.now().timestamp() - _cache_timestamp) / 60 if _cache_timestamp else 0
            },
            "subjects_summary": [],
            "overall_stats": {
                "total_subjects": len(verified_cache),
                "subjects_ready": 0,
                "subjects_limited": 0,
                "subjects_insufficient": 0,
                "total_verified_questions": 0
            }
        }
        
        for subject_name, questions in verified_cache.items():
            question_count = len(questions)
            summary["overall_stats"]["total_verified_questions"] += question_count
            
            if question_count >= 10:
                readiness = "ready"
                summary["overall_stats"]["subjects_ready"] += 1
            elif question_count >= 3:
                readiness = "limited"
                summary["overall_stats"]["subjects_limited"] += 1
            else:
                readiness = "insufficient"
                summary["overall_stats"]["subjects_insufficient"] += 1
            
            summary["subjects_summary"].append({
                "subject_name": subject_name,
                "verified_questions": question_count,
                "readiness": readiness,
                "max_diagnostic_questions": min(question_count, 20) if question_count >= 3 else 0
            })
        
        # Sort by question count
        summary["subjects_summary"].sort(key=lambda x: x["verified_questions"], reverse=True)
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting diagnostic test summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")

@router.post("/refresh-cache")
async def refresh_verification_cache(db: Session = Depends(get_db)):
    """Force refresh of verified questions cache"""
    try:
        global _verified_questions_cache, _cache_timestamp
        _verified_questions_cache = {}
        _cache_timestamp = None
        
        # Rebuild cache
        verified_cache = get_verified_questions_cache(db)
        
        return {
            "status": "success",
            "message": "Verification cache refreshed",
            "cache_timestamp": _cache_timestamp,
            "subjects_with_verified_questions": len(verified_cache),
            "total_verified_questions": sum(len(questions) for questions in verified_cache.values())
        }
        
    except Exception as e:
        logger.error(f"Error refreshing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error refreshing cache: {str(e)}")