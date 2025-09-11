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

@router.get("/results/{test_id}")
async def get_diagnostic_results_dashboard(
    test_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive diagnostic results for dashboard display"""
    try:
        diagnostic_service = DiagnosticService(db)
        
        # Get the diagnostic test
        test = diagnostic_service.get_diagnostic_test_by_id(test_id)
        if not test or str(test.user_id) != str(current_user.id):
            raise HTTPException(status_code=404, detail="Test diagnóstico no encontrado")
        
        if test.status != "completed":
            raise HTTPException(status_code=400, detail="Test diagnóstico no completado")
        
        # Get test answers with detailed question information
        answers = db.query(DiagnosticTestAnswer).filter(
            DiagnosticTestAnswer.diagnostic_test_id == test_id
        ).all()
        
        # Get questions with their details for analysis
        question_ids = [answer.question_id for answer in answers]
        questions = db.query(Question).filter(Question.id.in_(question_ids)).all()
        question_map = {str(q.id): q for q in questions}
        
        # Calculate final theta score using IRT
        final_theta = 0.0
        total_information = 0.0
        
        for answer in answers:
            question = question_map.get(str(answer.question_id))
            if question and hasattr(question, 'get_irt_probability'):
                # Use actual IRT parameters if available
                if question.parametro_irt_a and question.parametro_irt_b:
                    theta_est = question.parametro_irt_b if answer.is_correct else question.parametro_irt_b - 1.0
                    information = question.get_irt_information(theta_est) if hasattr(question, 'get_irt_information') else 1.0
                    
                    final_theta += theta_est * information
                    total_information += information
        
        if total_information > 0:
            final_theta = final_theta / total_information
        
        # Questions answered correctly/incorrectly with detailed breakdown
        correct_questions = []
        incorrect_questions = []
        
        for answer in answers:
            question = question_map.get(str(answer.question_id))
            if question:
                question_data = {
                    "id": str(question.id),
                    "question_text": question.pregunta_texto or question.question_text or "Pregunta sin texto",
                    "user_answer": answer.user_answer,
                    "correct_answer": question.respuesta_correcta or question.correct_answer,
                    "response_time_ms": answer.response_time_ms,
                    "topic": question.topic.name if question.topic else "General",
                    "difficulty": question.difficulty,
                    # Additional ICFES-specific data if available
                    "componente": getattr(question, 'componente', None),
                    "proceso_cognitivo": getattr(question, 'proceso_cognitivo', None),
                    "competencia": getattr(question, 'competencia', None),
                }
                
                if answer.is_correct:
                    correct_questions.append(question_data)
                else:
                    incorrect_questions.append(question_data)
        
        # Competencies analysis based on Componente and Proceso_Cognitivo
        componente_performance = {}
        proceso_cognitivo_performance = {}
        
        for answer in answers:
            question = question_map.get(str(answer.question_id))
            if question:
                # Analyze by Componente
                componente = getattr(question, 'componente', None) or 'General'
                if componente not in componente_performance:
                    componente_performance[componente] = {"correct": 0, "total": 0}
                componente_performance[componente]["total"] += 1
                if answer.is_correct:
                    componente_performance[componente]["correct"] += 1
                
                # Analyze by Proceso_Cognitivo
                proceso = getattr(question, 'proceso_cognitivo', None) or 'General'
                if proceso not in proceso_cognitivo_performance:
                    proceso_cognitivo_performance[proceso] = {"correct": 0, "total": 0}
                proceso_cognitivo_performance[proceso]["total"] += 1
                if answer.is_correct:
                    proceso_cognitivo_performance[proceso]["correct"] += 1
        
        # Determine mastered competencies (>70% performance)
        mastered_competencies = []
        improvement_areas = []
        
        for componente, stats in componente_performance.items():
            percentage = (stats["correct"] / stats["total"]) * 100
            if percentage >= 70:
                mastered_competencies.append({
                    "name": componente,
                    "type": "Componente",
                    "percentage": round(percentage, 1),
                    "questions_correct": stats["correct"],
                    "questions_total": stats["total"]
                })
            elif percentage < 50:
                improvement_areas.append({
                    "name": componente,
                    "type": "Componente", 
                    "percentage": round(percentage, 1),
                    "questions_correct": stats["correct"],
                    "questions_total": stats["total"]
                })
        
        for proceso, stats in proceso_cognitivo_performance.items():
            percentage = (stats["correct"] / stats["total"]) * 100
            if percentage >= 70:
                mastered_competencies.append({
                    "name": proceso,
                    "type": "Proceso Cognitivo",
                    "percentage": round(percentage, 1),
                    "questions_correct": stats["correct"],
                    "questions_total": stats["total"]
                })
            elif percentage < 50:
                improvement_areas.append({
                    "name": proceso,
                    "type": "Proceso Cognitivo",
                    "percentage": round(percentage, 1),
                    "questions_correct": stats["correct"],
                    "questions_total": stats["total"]
                })
        
        # Generate study topics based on improvement areas and incorrect questions
        recommended_topics = set()
        
        # Add topics from incorrect questions
        for question_data in incorrect_questions:
            if question_data["topic"] and question_data["topic"] != "General":
                recommended_topics.add(question_data["topic"])
        
        # Add topics from low-performing competencies
        for area in improvement_areas:
            if area["type"] == "Componente":
                # Map componentes to study topics
                componente_topic_map = {
                    "Entorno_vivo": "Biología y Ecosistemas",
                    "Entorno_físico": "Física y Química",
                    "Ciencia_tecnologia_sociedad": "Ciencias Aplicadas",
                    "Numeric": "Razonamiento Cuantitativo",
                    "Aleatorio": "Estadística y Probabilidad",
                    "Geométrico": "Geometría",
                    "Variacional": "Funciones y Cálculo"
                }
                topic = componente_topic_map.get(area["name"], area["name"])
                recommended_topics.add(topic)
        
        recommended_study_topics = list(recommended_topics)
        
        return {
            "test_id": str(test.id),
            "subject": test.subject.name if test.subject else "General",
            "final_theta_score": round(final_theta, 3),
            "score_percentage": round(test.score_percentage, 1),
            "questions_answered": test.questions_answered,
            "questions_correct": test.correct_answers,
            "questions_incorrect": test.questions_answered - test.correct_answers,
            "time_spent_minutes": round(test.time_spent_seconds / 60, 1),
            "completed_at": test.completed_at.isoformat() if test.completed_at else None,
            
            # Detailed question breakdown
            "correct_questions": correct_questions,
            "incorrect_questions": incorrect_questions,
            
            # Competencies analysis
            "competencies_mastered": mastered_competencies,
            "areas_for_improvement": improvement_areas,
            "componente_performance": {
                name: {
                    "percentage": round((stats["correct"] / stats["total"]) * 100, 1),
                    "questions_correct": stats["correct"],
                    "questions_total": stats["total"]
                } 
                for name, stats in componente_performance.items()
            },
            "proceso_cognitivo_performance": {
                name: {
                    "percentage": round((stats["correct"] / stats["total"]) * 100, 1),
                    "questions_correct": stats["correct"],
                    "questions_total": stats["total"]
                } 
                for name, stats in proceso_cognitivo_performance.items()
            },
            
            # Study recommendations
            "recommended_study_topics": recommended_study_topics,
            "strengths": test.strengths or [],
            "weaknesses": test.weaknesses or [],
            "score_by_topic": test.score_by_topic or {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting diagnostic results dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo resultados: {str(e)}")

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