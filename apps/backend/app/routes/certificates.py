from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime
import json

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.battle import Battle
from ..models.certificate import Certificate
from ..models.subject import Subject

router = APIRouter(prefix="/certificates", tags=["certificates"])
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[dict])
async def get_user_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all certificates for the current user"""
    try:
        certificates = db.query(Certificate).filter(
            Certificate.user_id == current_user.id
        ).order_by(Certificate.generated_at.desc()).all()
        
        return [
            {
                "id": str(cert.id),
                "unit_number": cert.unit_number,
                "subject_name": cert.subject.name if cert.subject else "Unknown",
                "certificate_data": cert.certificate_data,
                "generated_at": cert.generated_at
            }
            for cert in certificates
        ]
    except Exception as e:
        logger.error(f"Error fetching certificates: {e}")
        raise HTTPException(status_code=500, detail="Error fetching certificates")

@router.get("/{certificate_id}")
async def get_certificate(
    certificate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific certificate by ID"""
    try:
        certificate = db.query(Certificate).filter(
            Certificate.id == certificate_id,
            Certificate.user_id == current_user.id
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        return {
            "id": str(certificate.id),
            "unit_number": certificate.unit_number,
            "subject_name": certificate.subject.name if certificate.subject else "Unknown",
            "certificate_data": certificate.certificate_data,
            "generated_at": certificate.generated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching certificate {certificate_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching certificate")

@router.post("/generate")
async def generate_certificate(
    unit_number: int,
    subject_id: str,
    battle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a new certificate for completing a unit"""
    try:
        # Verify battle exists and belongs to user
        battle = db.query(Battle).filter(
            Battle.id == battle_id,
            Battle.user_id == current_user.id,
            Battle.is_boss_battle == True,
            Battle.unit_number == unit_number
        ).first()
        
        if not battle:
            raise HTTPException(status_code=404, detail="Boss battle not found")
        
        # Verify subject exists
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        # Check if certificate already exists
        existing_certificate = db.query(Certificate).filter(
            Certificate.user_id == current_user.id,
            Certificate.unit_number == unit_number,
            Certificate.subject_id == subject_id
        ).first()
        
        if existing_certificate:
            raise HTTPException(status_code=400, detail="Certificate already exists for this unit")
        
        # Generate certificate data
        certificate_data = {
            "title": f"Certificado de Dominio - Unidad {unit_number}",
            "subject": subject.name,
            "unit_number": unit_number,
            "student_name": current_user.username,
            "completion_date": datetime.now().isoformat(),
            "achievement": f"Dominio demostrado en {subject.name} - Unidad {unit_number}",
            "signature": "Sistema ICFES Leveling",
            "certificate_id": f"cert-{current_user.id}-{subject_id}-{unit_number}",
            "battle_performance": {
                "enemy_name": battle.enemy_name,
                "questions_answered": battle.questions_answered,
                "correct_answers": battle.correct_answers,
                "accuracy": round((battle.correct_answers / battle.questions_answered) * 100, 1) if battle.questions_answered > 0 else 0
            }
        }
        
        # Create certificate
        certificate = Certificate(
            user_id=current_user.id,
            unit_number=unit_number,
            subject_id=subject_id,
            battle_id=battle_id,
            certificate_data=certificate_data
        )
        
        db.add(certificate)
        db.commit()
        db.refresh(certificate)
        
        logger.info(f"Certificate generated: {certificate.id}")
        
        return {
            "id": str(certificate.id),
            "unit_number": certificate.unit_number,
            "subject_name": subject.name,
            "certificate_data": certificate.certificate_data,
            "generated_at": certificate.generated_at
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating certificate: {e}")
        raise HTTPException(status_code=500, detail="Error generating certificate")

@router.get("/download/{certificate_id}")
async def download_certificate(
    certificate_id: str,
    format: str = Query("pdf", description="Certificate format (pdf, png, json)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download certificate in specified format"""
    try:
        certificate = db.query(Certificate).filter(
            Certificate.id == certificate_id,
            Certificate.user_id == current_user.id
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        if format == "json":
            return certificate.certificate_data
        elif format == "pdf":
            # In a real implementation, generate PDF
            return {"message": "PDF generation not implemented yet"}
        elif format == "png":
            # In a real implementation, generate PNG
            return {"message": "PNG generation not implemented yet"}
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading certificate {certificate_id}: {e}")
        raise HTTPException(status_code=500, detail="Error downloading certificate")

@router.get("/stats/summary")
async def get_certificate_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get certificate statistics for the user"""
    try:
        certificates = db.query(Certificate).filter(
            Certificate.user_id == current_user.id
        ).all()
        
        # Group by subject
        subject_stats = {}
        for cert in certificates:
            subject_name = cert.subject.name if cert.subject else "Unknown"
            if subject_name not in subject_stats:
                subject_stats[subject_name] = {
                    "total_certificates": 0,
                    "units_completed": [],
                    "last_completion": None
                }
            
            subject_stats[subject_name]["total_certificates"] += 1
            subject_stats[subject_name]["units_completed"].append(cert.unit_number)
            
            if not subject_stats[subject_name]["last_completion"] or cert.generated_at > subject_stats[subject_name]["last_completion"]:
                subject_stats[subject_name]["last_completion"] = cert.generated_at
        
        return {
            "total_certificates": len(certificates),
            "subjects_with_certificates": len(subject_stats),
            "subject_stats": subject_stats,
            "recent_certificates": [
                {
                    "id": str(cert.id),
                    "subject": cert.subject.name if cert.subject else "Unknown",
                    "unit": cert.unit_number,
                    "generated_at": cert.generated_at
                }
                for cert in sorted(certificates, key=lambda x: x.generated_at, reverse=True)[:5]
            ]
        }
    except Exception as e:
        logger.error(f"Error getting certificate stats: {e}")
        raise HTTPException(status_code=500, detail="Error getting certificate stats") 