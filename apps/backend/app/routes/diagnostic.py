from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..schemas.diagnostic_test import (
    DiagnosticTestCreate,
    DiagnosticTestResponse,
    DiagnosticTestSubmit,
    DiagnosticTestAnalysis,
    DiagnosticTestQuestion,
    DiagnosticTestConfig,
    DiagnosticResultResponse,
    DIAGNOSTIC_TEST_CONFIGS
)
from ..services.diagnostic_service import DiagnosticService
from ..models.user import User
from ..models.subject import Subject

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])

@router.post("/tests", response_model=DiagnosticTestResponse)
async def create_diagnostic_test(
    test_data: DiagnosticTestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo test diagnóstico"""
    try:
        diagnostic_service = DiagnosticService(db)
        test = diagnostic_service.create_diagnostic_test(
            user_id=str(current_user.id),
            subject_id=test_data.subject_id,
            test_type=test_data.test_type
        )
        
        return {
            "id": str(test.id),
            "user_id": str(test.user_id),
            "subject_id": str(test.subject_id),
            "test_type": test.test_type,
            "questions_answered": test.questions_answered,
            "correct_answers": test.correct_answers,
            "time_spent_seconds": test.time_spent_seconds,
            "score_percentage": float(test.score_percentage),
            "strengths": test.strengths,
            "weaknesses": test.weaknesses,
            "score_by_topic": test.score_by_topic,
            "status": test.status,
            "started_at": test.started_at,
            "completed_at": test.completed_at,
            "created_at": test.created_at
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando test diagnóstico: {str(e)}")

@router.get("/tests/{test_id}/questions", response_model=List[DiagnosticTestQuestion])
async def get_diagnostic_questions(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener preguntas para un test diagnóstico específico"""
    try:
        diagnostic_service = DiagnosticService(db)
        
        # Development mode: allow access without test verification
        from ..core.config import settings
        if settings.ENVIRONMENT == "development":
            # For development, use a default subject (Matemáticas)
            subject = db.query(Subject).filter(Subject.name == "Matemáticas").first()
            if not subject:
                # If no subject found, create a mock response
                return [
                    {
                        "id": "1",
                        "question_text": "¿Cuál es el resultado de 2 + 2?",
                        "options": ["3", "4", "5", "6"],
                        "subject": "Matemáticas",
                        "topic": "Aritmética",
                        "difficulty": 1,
                        "hint": "Suma básica",
                        "image_url": None,
                        "options_images": {}
                    },
                    {
                        "id": "2",
                        "question_text": "¿Cuál es el área de un cuadrado de lado 5?",
                        "options": ["20", "25", "30", "35"],
                        "subject": "Matemáticas",
                        "topic": "Geometría",
                        "difficulty": 2,
                        "hint": "Área = lado × lado",
                        "image_url": None,
                        "options_images": {}
                    }
                ]
            
            config = diagnostic_service.get_diagnostic_test_config(subject.name)
            
            # Obtener preguntas REALES de la base de datos
            questions = diagnostic_service.get_diagnostic_questions(
                subject_id=str(subject.id),
                limit=config["total_questions"]
            )
            
            # Si no hay preguntas en la base de datos, usar mock data
            if not questions:
                return [
                    {
                        "id": "1",
                        "question_text": "¿Cuál es el resultado de 2 + 2?",
                        "options": ["3", "4", "5", "6"],
                        "subject": "Matemáticas",
                        "topic": "Aritmética",
                        "difficulty": 1,
                        "hint": "Suma básica",
                        "image_url": None,
                        "options_images": {}
                    },
                    {
                        "id": "2",
                        "question_text": "¿Cuál es el área de un cuadrado de lado 5?",
                        "options": ["20", "25", "30", "35"],
                        "subject": "Matemáticas",
                        "topic": "Geometría",
                        "difficulty": 2,
                        "hint": "Área = lado × lado",
                        "image_url": None,
                        "options_images": {}
                    }
                ]
            
            result = []
            for q in questions:
                # Merge legacy + multimedia for maximum compatibility
                image_url = getattr(q, 'pregunta_imagen', None)  # Usar el campo correcto del modelo
                options_images = {}  # Campo no existe en el modelo actual
                if not options_images:
                    maybe = {
                        'A': getattr(q, 'opcion_a_imagen', None),
                        'B': getattr(q, 'opcion_b_imagen', None),
                        'C': getattr(q, 'opcion_c_imagen', None),
                        'D': getattr(q, 'opcion_d_imagen', None),
                    }
                    options_images = {k: v for k, v in maybe.items() if v}

                # Build options list from individual fields or from options JSON
                if q.options and isinstance(q.options, dict):
                    options = list(q.options.values())
                elif q.opcion_a_texto or q.opcion_b_texto or q.opcion_c_texto or q.opcion_d_texto:
                    options = [
                        q.opcion_a_texto or "Opción A",
                        q.opcion_b_texto or "Opción B", 
                        q.opcion_c_texto or "Opción C",
                        q.opcion_d_texto or "Opción D"
                    ]
                else:
                    options = ["Opción A", "Opción B", "Opción C", "Opción D"]

                result.append({
                    "id": str(q.id),
                    "question_text": q.pregunta_texto or q.question_text or "Pregunta sin texto",
                    "options": options,
                    "subject": subject.name,
                    "topic": q.topic.name if q.topic else "General",
                    "difficulty": q.difficulty,
                    "hint": q.hint,
                    "image_url": image_url,
                    "options_images": options_images,
                })
            return result
        
        # Production mode: verify test ownership
        test = diagnostic_service.get_diagnostic_test_by_id(test_id)
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test diagnóstico no encontrado")
        
        # Obtener configuración del test
        subject = db.query(Subject).filter(Subject.id == test.subject_id).first()
        config = diagnostic_service.get_diagnostic_test_config(subject.name)
        
        # Obtener preguntas
        questions = diagnostic_service.get_diagnostic_questions(
            subject_id=str(test.subject_id),
            limit=config["total_questions"]
        )
        
        result = []
        for q in questions:
            image_url = getattr(q, 'pregunta_imagen', None)  # Usar el campo correcto del modelo
            options_images = {}  # Campo no existe en el modelo actual
            if not options_images:
                maybe = {
                    'A': getattr(q, 'opcion_a_imagen', None),
                    'B': getattr(q, 'opcion_b_imagen', None),
                    'C': getattr(q, 'opcion_c_imagen', None),
                    'D': getattr(q, 'opcion_d_imagen', None),
                }
                options_images = {k: v for k, v in maybe.items() if v}

            options = q.options
            if isinstance(options, dict):
                options = list(options.values())

            result.append({
                "id": str(q.id),
                "question_text": q.question_text or getattr(q, 'pregunta_texto', None),
                "options": options,
                "subject": subject.name,
                "topic": q.topic.name if q.topic else "General",
                "difficulty": q.difficulty,
                "hint": q.hint,
                "image_url": image_url,
                "options_images": options_images,
            })
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo preguntas: {str(e)}")

@router.post("/tests/{test_id}/submit", response_model=DiagnosticResultResponse)
async def submit_diagnostic_test(
    test_id: str,
    submit_data: DiagnosticTestSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Procesar respuestas del test diagnóstico"""
    try:
        # Log de entrada
        logger.info(f"📥 Submit test - test_id: {test_id}, user: {current_user.id}, answers: {len(submit_data.answers)}")
        
        diagnostic_service = DiagnosticService(db)
        
        # Verificar que el test pertenece al usuario
        test = diagnostic_service.get_diagnostic_test_by_id(test_id)
        if not test:
            logger.error(f"Test {test_id} no encontrado")
            raise HTTPException(status_code=404, detail="Test diagnóstico no encontrado")
            
        if str(test.user_id) != str(current_user.id):
            logger.error(f"Test {test_id} no pertenece al usuario {current_user.id}")
            raise HTTPException(status_code=500, detail="No tienes permiso para enviar este test")
        
        # Normalizar respuestas a mayúsculas
        answers = [
            {
                "question_id": answer.question_id,
                "user_answer": answer.user_answer.upper(),  # Forzar mayúsculas
                "response_time_ms": min(2147483647, max(0, answer.response_time_ms))
            }
            for answer in submit_data.answers
        ]
        
        # Log antes de procesar
        logger.info(f"✅ Procesando {len(answers)} respuestas para test {test_id}")
        
        # Procesar respuestas
        analysis = diagnostic_service.submit_diagnostic_test(test_id, answers)
        
        logger.info(f"✅ Test {test_id} completado - Score: {analysis.percentage}%")
        
        # Asegura el shape esperado por el FE:
        return {
            "score": int(analysis.score),  # int 0..500 o similar
            "percentage": int(analysis.percentage),  # 0..100
            "strengths": analysis.strengths or [],
            "weaknesses": analysis.weaknesses or [],
            "recommendations": analysis.recommendations or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error procesando test {test_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando test: {str(e)}")

@router.get("/tests", response_model=List[DiagnosticTestResponse])
async def get_user_diagnostic_tests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener todos los tests diagnósticos del usuario"""
    try:
        diagnostic_service = DiagnosticService(db)
        tests = diagnostic_service.get_user_diagnostic_tests(str(current_user.id))
        
        return [
            {
                "id": str(test.id),
                "user_id": str(test.user_id),
                "subject_id": str(test.subject_id),
                "test_type": test.test_type,
                "questions_answered": test.questions_answered,
                "correct_answers": test.correct_answers,
                "time_spent_seconds": test.time_spent_seconds,
                "score_percentage": float(test.score_percentage),
                "strengths": test.strengths,
                "weaknesses": test.weaknesses,
                "score_by_topic": test.score_by_topic,
                "status": test.status,
                "started_at": test.started_at,
                "completed_at": test.completed_at,
                "created_at": test.created_at
            }
            for test in tests
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo tests: {str(e)}")

@router.get("/tests/{test_id}", response_model=DiagnosticTestResponse)
async def get_diagnostic_test(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener un test diagnóstico específico"""
    try:
        diagnostic_service = DiagnosticService(db)
        test = diagnostic_service.get_diagnostic_test_by_id(test_id)
        
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test diagnóstico no encontrado")
        
        return {
            "id": str(test.id),
            "user_id": str(test.user_id),
            "subject_id": str(test.subject_id),
            "test_type": test.test_type,
            "questions_answered": test.questions_answered,
            "correct_answers": test.correct_answers,
            "time_spent_seconds": test.time_spent_seconds,
            "score_percentage": float(test.score_percentage),
            "strengths": test.strengths,
            "weaknesses": test.weaknesses,
            "score_by_topic": test.score_by_topic,
            "status": test.status,
            "started_at": test.started_at,
            "completed_at": test.completed_at,
            "created_at": test.created_at
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo test: {str(e)}")

@router.get("/config/{subject_name}", response_model=DiagnosticTestConfig)
async def get_diagnostic_config(
    subject_name: str,
    db: Session = Depends(get_db)
):
    """Obtener configuración del test diagnóstico por materia"""
    try:
        diagnostic_service = DiagnosticService(db)
        config = diagnostic_service.get_diagnostic_test_config(subject_name)
        
        return {
            "subject": subject_name,
            "total_questions": config["total_questions"],
            "time_limit_minutes": config["time_limit_minutes"],
            "topics": config["topics"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo configuración: {str(e)}")

@router.get("/stats/{subject_id}")
async def get_subject_stats(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de tests diagnósticos por materia"""
    try:
        diagnostic_service = DiagnosticService(db)
        stats = diagnostic_service.get_subject_stats(str(current_user.id), subject_id)
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@router.get("/subjects")
async def get_diagnostic_subjects(db: Session = Depends(get_db)):
    """Obtener materias disponibles para tests diagnósticos"""
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
        raise HTTPException(status_code=500, detail=f"Error obteniendo materias: {str(e)}") 