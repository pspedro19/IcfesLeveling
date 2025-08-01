from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import redis
import json
import hashlib

from ..core.database import get_db
from ..core.security import get_current_user
from ..core.config import settings
from ..models.user import User
from ..models.question import Question
from ..models.ai_explanation import AIExplanation

router = APIRouter(prefix="/ai", tags=["ai"])

# Conexión a Redis para cache
redis_client = redis.from_url(settings.REDIS_URL)

@router.post("/explain")
async def get_ai_explanation(
    question_id: str,
    user_answer: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener explicación de IA para una pregunta"""
    # Obtener pregunta
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    # Crear hash para cache
    cache_key = f"ai_explanation:{hashlib.sha256(f'{question_id}:{user_answer}'.encode()).hexdigest()}"
    
    # Verificar cache
    cached_explanation = redis_client.get(cache_key)
    if cached_explanation:
        return json.loads(cached_explanation)
    
    # Verificar si la respuesta es correcta
    is_correct = user_answer == question.correct_answer
    
    # Generar explicación
    if is_correct:
        explanation_text = f"¡Excelente! Tu respuesta '{user_answer}' es correcta. {question.explanation or 'Has demostrado un buen entendimiento del tema.'}"
    else:
        explanation_text = f"Tu respuesta '{user_answer}' no es correcta. La respuesta correcta es '{question.correct_answer}'. {question.explanation or 'Te recomiendo revisar este tema.'}"
    
    # Crear explicación en base de datos
    ai_explanation = AIExplanation(
        user_id=current_user.id,
        question_id=question_id,
        explanation_text=explanation_text,
        explanation_type="wrong_answer" if not is_correct else "correct_answer",
        tokens_used=len(explanation_text.split()),
        response_time_ms=100  # Mock response time
    )
    
    db.add(ai_explanation)
    db.commit()
    
    # Guardar en cache
    explanation_data = {
        "explanation": explanation_text,
        "is_correct": is_correct,
        "correct_answer": question.correct_answer,
        "hint": question.hint
    }
    
    redis_client.setex(cache_key, 60 * 60 * 24 * settings.AI_CACHE_TTL_DAYS, json.dumps(explanation_data))
    
    return explanation_data

@router.post("/study-plan")
async def get_study_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener plan de estudio personalizado"""
    # Crear hash para cache
    cache_key = f"study_plan:{current_user.id}"
    
    # Verificar cache
    cached_plan = redis_client.get(cache_key)
    if cached_plan:
        return json.loads(cached_plan)
    
    # Generar plan de estudio basado en el nivel del usuario
    user_level = current_user.level
    
    if user_level <= 10:
        plan = {
            "title": "Plan de Estudio para Principiantes",
            "description": "Enfócate en los fundamentos básicos",
            "missions": [
                {
                    "id": 1,
                    "title": "Dominar Operaciones Básicas",
                    "description": "Completa 10 preguntas de matemáticas básicas",
                    "subject": "matemáticas",
                    "difficulty": 1,
                    "reward": 50
                },
                {
                    "id": 2,
                    "title": "Comprensión de Lectura",
                    "description": "Responde 5 preguntas de lenguaje correctamente",
                    "subject": "lenguaje",
                    "difficulty": 1,
                    "reward": 40
                },
                {
                    "id": 3,
                    "title": "Conceptos Científicos",
                    "description": "Aprende 3 conceptos básicos de ciencias",
                    "subject": "ciencias",
                    "difficulty": 1,
                    "reward": 45
                }
            ]
        }
    elif user_level <= 25:
        plan = {
            "title": "Plan de Estudio Intermedio",
            "description": "Profundiza en temas más complejos",
            "missions": [
                {
                    "id": 1,
                    "title": "Álgebra Básica",
                    "description": "Resuelve 8 ecuaciones de primer grado",
                    "subject": "matemáticas",
                    "difficulty": 3,
                    "reward": 80
                },
                {
                    "id": 2,
                    "title": "Análisis Literario",
                    "description": "Analiza 3 textos literarios",
                    "subject": "lenguaje",
                    "difficulty": 3,
                    "reward": 75
                },
                {
                    "id": 3,
                    "title": "Experimentos Científicos",
                    "description": "Comprende 5 experimentos básicos",
                    "subject": "ciencias",
                    "difficulty": 3,
                    "reward": 70
                }
            ]
        }
    else:
        plan = {
            "title": "Plan de Estudio Avanzado",
            "description": "Desafía tus límites con temas complejos",
            "missions": [
                {
                    "id": 1,
                    "title": "Cálculo Diferencial",
                    "description": "Resuelve 6 problemas de derivadas",
                    "subject": "matemáticas",
                    "difficulty": 7,
                    "reward": 120
                },
                {
                    "id": 2,
                    "title": "Análisis Crítico",
                    "description": "Realiza análisis crítico de 4 textos complejos",
                    "subject": "lenguaje",
                    "difficulty": 7,
                    "reward": 110
                },
                {
                    "id": 3,
                    "title": "Investigación Científica",
                    "description": "Comprende 3 investigaciones científicas",
                    "subject": "ciencias",
                    "difficulty": 7,
                    "reward": 115
                }
            ]
        }
    
    # Guardar en cache por 24 horas
    redis_client.setex(cache_key, 60 * 60 * 24, json.dumps(plan))
    
    return plan

@router.get("/hint/{question_id}")
async def get_hint(
    question_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener pista para una pregunta"""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Pregunta no encontrada")
    
    if not question.hint:
        raise HTTPException(status_code=404, detail="No hay pista disponible para esta pregunta")
    
    return {
        "hint": question.hint,
        "question_id": question_id
    } 