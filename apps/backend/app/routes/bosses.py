from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime

from ..core.database import get_db
from ..core.security import get_current_user
from ..services.boss_service import BossService
from ..models.user import User
from ..models.battle import Battle, Certificate

router = APIRouter(prefix="/bosses", tags=["bosses"])

@router.post("/{unit_number}/start")
async def start_boss_battle(
    unit_number: int,
    subject_id: str = Query(..., description="ID de la materia"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inicia una batalla de boss temático para una unidad específica"""
    try:
        boss_service = BossService(db)
        boss_battle = boss_service.create_boss_battle(str(current_user.id), unit_number, subject_id)
        
        return {
            "battle_id": str(boss_battle.id),
            "enemy_name": boss_battle.enemy_name,
            "enemy_level": boss_battle.enemy_level,
            "enemy_hp": boss_battle.enemy_hp,
            "boss_narrative": boss_battle.boss_narrative,
            "unit_number": boss_battle.unit_number,
            "status": boss_battle.status
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error iniciando batalla de boss: {str(e)}")

@router.get("/{battle_id}/questions")
async def get_boss_questions(
    battle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las 20 preguntas de alta dificultad para la batalla de boss"""
    try:
        # Verificar que la batalla existe y pertenece al usuario
        battle = db.query(Battle).filter(
            Battle.id == battle_id,
            Battle.user_id == current_user.id,
            Battle.is_boss_battle == True
        ).first()
        
        if not battle:
            raise HTTPException(status_code=404, detail="Batalla de boss no encontrada")
        
        boss_service = BossService(db)
        questions = boss_service.get_boss_questions(battle.unit_number, battle.subject_id)
        
        # Formatear preguntas para el frontend
        formatted_questions = []
        for question in questions:
            formatted_questions.append({
                "id": str(question.id),
                "question_text": question.question_text,
                "options": question.options,
                "difficulty": question.difficulty,
                "hint": question.hint,
                "explanation": question.explanation
            })
        
        return {
            "battle_id": battle_id,
            "questions": formatted_questions,
            "total_questions": len(formatted_questions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo preguntas del boss: {str(e)}")

@router.post("/{battle_id}/complete")
async def complete_boss_battle(
    battle_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Completa la batalla de boss y otorga recompensas épicas"""
    try:
        boss_service = BossService(db)
        result = boss_service.complete_boss_battle(battle_id, str(current_user.id))
        
        return {
            "message": "¡Boss derrotado! Has demostrado tu dominio.",
            "battle_id": result["battle_id"],
            "rewards": result["rewards"],
            "certificate_id": result["certificate_id"],
            "next_unit_unlocked": result["next_unit_unlocked"],
            "new_level": result["new_level"],
            "new_rank": result["new_rank"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error completando batalla de boss: {str(e)}")

@router.get("/certificates")
async def get_user_certificates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene todos los certificados de dominio del usuario"""
    try:
        certificates = db.query(Certificate).filter(
            Certificate.user_id == current_user.id
        ).all()
        
        certificate_list = []
        for cert in certificates:
            certificate_list.append({
                "id": str(cert.id),
                "unit_number": cert.unit_number,
                "subject_id": str(cert.subject_id),
                "certificate_data": cert.certificate_data,
                "generated_at": cert.generated_at.isoformat()
            })
        
        return {
            "certificates": certificate_list,
            "total_certificates": len(certificate_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo certificados: {str(e)}")

@router.get("/certificates/{certificate_id}")
async def get_certificate_by_id(
    certificate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene un certificado específico por ID"""
    try:
        certificate = db.query(Certificate).filter(
            Certificate.id == certificate_id,
            Certificate.user_id == current_user.id
        ).first()
        
        if not certificate:
            raise HTTPException(status_code=404, detail="Certificado no encontrado")
        
        return {
            "id": str(certificate.id),
            "unit_number": certificate.unit_number,
            "subject_id": str(certificate.subject_id),
            "certificate_data": certificate.certificate_data,
            "generated_at": certificate.generated_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo certificado: {str(e)}")

@router.get("/available")
async def get_available_bosses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene las unidades disponibles para enfrentar bosses"""
    try:
        # Buscar unidades completadas del usuario
        from ..models.study_plan import PlanProgress, StudyPlan
        
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.user_id == current_user.id,
            StudyPlan.is_active == True
        ).first()
        
        if not study_plan:
            return {"available_bosses": [], "message": "No tienes planes de estudio activos"}
        
        completed_units = db.query(PlanProgress).filter(
            PlanProgress.plan_id == study_plan.id,
            PlanProgress.is_completed == True
        ).all()
        
        available_bosses = []
        for unit in completed_units:
            # Verificar si ya enfrentó al boss de esta unidad
            existing_boss_battle = db.query(Battle).filter(
                Battle.user_id == current_user.id,
                Battle.unit_number == unit.unit_number,
                Battle.is_boss_battle == True
            ).first()
            
            if not existing_boss_battle:
                available_bosses.append({
                    "unit_number": unit.unit_number,
                    "unit_name": unit.unit_name,
                    "subject_id": str(study_plan.subject_id),
                    "completion_date": unit.completion_date.isoformat() if unit.completion_date else None
                })
        
        return {
            "available_bosses": available_bosses,
            "total_available": len(available_bosses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo bosses disponibles: {str(e)}")

@router.get("/progress")
async def get_boss_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene el progreso de bosses del usuario"""
    try:
        # Contar batallas de boss completadas
        completed_bosses = db.query(Battle).filter(
            Battle.user_id == current_user.id,
            Battle.is_boss_battle == True,
            Battle.status == "completed"
        ).count()
        
        # Contar certificados obtenidos
        certificates_count = db.query(Certificate).filter(
            Certificate.user_id == current_user.id
        ).count()
        
        return {
            "bosses_defeated": completed_bosses,
            "certificates_earned": certificates_count,
            "total_units": 8,  # Asumiendo 8 unidades por materia
            "progress_percentage": (completed_bosses / 8) * 100 if completed_bosses > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo progreso de bosses: {str(e)}") 