from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
import tempfile
import os
import pandas as pd
import uuid

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.topic import Topic
from ..models.question import Question
from ..models.subject import Subject
from ..schemas.question import QuestionResponse
from ..import_icfes_excel import ICFESExcelImporter

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)

def check_admin_permissions(user: User):
    """Verificar que el usuario tenga permisos de administrador"""
    if not user or user.email not in ['admin@icfesquest.com']:
        raise HTTPException(
            status_code=403, 
            detail="Acceso denegado. Se requieren permisos de administrador."
        )

@router.post("/questions/import-excel")
async def import_questions_from_excel(
    file: UploadFile = File(...),
    validate_only: bool = Form(False),
    clear_existing: bool = Form(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Importar preguntas desde archivo Excel
    - file: Archivo Excel con preguntas ICFES
    - validate_only: Solo validar, no importar
    - clear_existing: Limpiar preguntas existentes antes de importar
    """
    # Verificar permisos
    check_admin_permissions(current_user)
    
    # Verificar tipo de archivo
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten archivos Excel (.xlsx, .xls)"
        )
    
    try:
        # Guardar archivo temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        # Importar preguntas
        importer = ICFESExcelImporter(db)
        
        # Limpiar si se solicita
        if clear_existing:
            logger.info("Limpiando preguntas existentes...")
            db.query(Question).delete()
            db.commit()
            logger.info("Preguntas existentes eliminadas")
        
        # Importar
        result = importer.import_excel(temp_file_path, validate_only=validate_only)
        
        # Limpiar archivo temporal
        os.unlink(temp_file_path)
        
        return {
            "success": True,
            "message": f"Importación completada: {result['imported_questions']} preguntas procesadas",
            "data": {
                "imported_questions": result['imported_questions'],
                "errors_count": len(result['errors']),
                "warnings_count": len(result['warnings']),
                "errors": result['errors'][:10],  # Solo primeros 10 errores
                "warnings": result['warnings'][:5]  # Solo primeras 5 advertencias
            }
        }
        
    except Exception as e:
        logger.error(f"Error en importación: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en la importación: {str(e)}"
        )

@router.get("/questions/stats")
async def get_questions_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de preguntas"""
    check_admin_permissions(current_user)
    
    try:
        # Estadísticas generales
        total_questions = db.query(Question).count()
        validated_questions = db.query(Question).filter(Question.is_validated == "validated").count()
        pending_questions = db.query(Question).filter(Question.is_validated == "pending").count()
        rejected_questions = db.query(Question).filter(Question.is_validated == "rejected").count()
        
        # Estadísticas por materia
        subjects_stats = db.query(
            Subject.name,
            db.func.count(Question.id).label('total'),
            db.func.count(db.case([(Question.is_validated == "validated", 1)])).label('validated')
        ).join(Question).group_by(Subject.name).all()
        
        # Estadísticas por dificultad
        difficulty_stats = db.query(
            Question.difficulty,
            db.func.count(Question.id).label('count')
        ).group_by(Question.difficulty).order_by(Question.difficulty).all()
        
        return {
            "general": {
                "total": total_questions,
                "validated": validated_questions,
                "pending": pending_questions,
                "rejected": rejected_questions
            },
            "by_subject": [
                {
                    "subject": stat.name,
                    "total": stat.total,
                    "validated": stat.validated,
                    "pending": stat.total - stat.validated
                }
                for stat in subjects_stats
            ],
            "by_difficulty": [
                {
                    "difficulty": stat.difficulty,
                    "count": stat.count
                }
                for stat in difficulty_stats
            ]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )

@router.post("/questions/validate-batch")
async def validate_questions_batch(
    question_ids: List[str] = Form(...),
    action: str = Form(...),  # "validate" o "reject"
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validar o rechazar un lote de preguntas"""
    check_admin_permissions(current_user)
    
    if action not in ["validate", "reject"]:
        raise HTTPException(
            status_code=400,
            detail="Acción debe ser 'validate' o 'reject'"
        )
    
    try:
        # Actualizar estado de preguntas
        updated_count = db.query(Question).filter(
            Question.id.in_(question_ids)
        ).update({
            "is_validated": "validated" if action == "validate" else "rejected"
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"{updated_count} preguntas {action}adas exitosamente",
            "updated_count": updated_count
        }
        
    except Exception as e:
        logger.error(f"Error validando preguntas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error validando preguntas: {str(e)}"
        )

@router.get("/questions/pending")
async def get_pending_questions(
    subject_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener preguntas pendientes de validación"""
    check_admin_permissions(current_user)
    
    try:
        query = db.query(Question).filter(Question.is_validated == "pending")
        
        if subject_id:
            query = query.filter(Question.subject_id == subject_id)
        
        questions = query.offset(offset).limit(limit).all()
        
        return {
            "questions": questions,
            "total": query.count(),
            "offset": offset,
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo preguntas pendientes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo preguntas pendientes: {str(e)}"
        )

@router.delete("/questions/{question_id}")
async def delete_question(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar una pregunta"""
    check_admin_permissions(current_user)
    
    try:
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=404,
                detail="Pregunta no encontrada"
            )
        
        db.delete(question)
        db.commit()
        
        return {
            "success": True,
            "message": "Pregunta eliminada exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error eliminando pregunta: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando pregunta: {str(e)}"
        ) 