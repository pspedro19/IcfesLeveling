from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime, timedelta
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.question import Question
from ..models.study_plan import StudyPlan, PlanProgress
from pydantic import BaseModel

router = APIRouter(prefix="/intelligent-recommendations", tags=["intelligent-recommendations"])
logger = logging.getLogger(__name__)

class FailedQuestionAnalysis(BaseModel):
    question_id: str
    user_answer: str
    correct_answer: str
    topic: str
    difficulty: int
    response_time_ms: int

class RecommendationRequest(BaseModel):
    test_id: str
    failed_questions: List[FailedQuestionAnalysis]
    user_level: int = 1
    preferred_duration_minutes: int = 30

class VideoRecommendation(BaseModel):
    video_id: str
    youtube_id: str
    youtube_url: str
    title: str
    channel_name: str
    duration_minutes: int
    relevance_score: float
    reason: str
    topic_match: str

class StudyRecommendation(BaseModel):
    recommendation_id: str
    user_id: str
    test_id: str
    subject_id: str
    subject_name: str
    total_failed_questions: int
    priority_topics: List[str]
    recommended_videos: List[VideoRecommendation]
    study_plan_summary: str
    estimated_study_time_hours: int
    expires_at: datetime
    created_at: datetime

@router.post("/generate-from-diagnostic", response_model=StudyRecommendation)
async def generate_intelligent_recommendations(
    request: RecommendationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generar recomendaciones inteligentes basadas en preguntas falladas
    Usa LLM para analizar patrones de error y recomendar videos específicos
    """
    try:
        logger.info(f"🧠 Generando recomendaciones inteligentes para usuario {current_user.id}")
        
        if not request.failed_questions:
            raise HTTPException(status_code=400, detail="No failed questions provided")
        
        # 1. Analizar patrones de error con LLM
        error_analysis = await analyze_error_patterns_with_llm(request.failed_questions, db)
        
        # 2. Identificar temas prioritarios
        priority_topics = extract_priority_topics(request.failed_questions, error_analysis)
        
        # 3. Obtener subject_id del primer pregunta fallada
        first_question = db.query(Question).filter(
            Question.id == request.failed_questions[0].question_id
        ).first()
        
        if not first_question:
            raise HTTPException(status_code=404, detail="Question not found")
        
        subject_id = str(first_question.subject_id)
        
        # 4. Buscar videos relevantes usando matching inteligente
        recommended_videos = await find_relevant_videos_with_ai(
            db, subject_id, priority_topics, error_analysis, request.preferred_duration_minutes
        )
        
        # 5. Generar plan de estudio personalizado
        study_plan_summary = await generate_study_plan_with_llm(
            priority_topics, recommended_videos, request.user_level
        )
        
        # 6. Crear recomendación persistente
        recommendation_id = str(uuid.uuid4())
        
        # Obtener nombre de la materia
        subject_result = db.execute(
            text("SELECT name FROM subjects WHERE id = :subject_id"),
            {"subject_id": subject_id}
        ).fetchone()
        subject_name = subject_result[0] if subject_result else "Materia"
        
        recommendation = StudyRecommendation(
            recommendation_id=recommendation_id,
            user_id=str(current_user.id),
            test_id=request.test_id,
            subject_id=subject_id,
            subject_name=subject_name,
            total_failed_questions=len(request.failed_questions),
            priority_topics=priority_topics,
            recommended_videos=recommended_videos,
            study_plan_summary=study_plan_summary,
            estimated_study_time_hours=len(recommended_videos) * 2,  # 2 horas por video aprox
            expires_at=datetime.now() + timedelta(days=30),  # Válido por 1 mes
            created_at=datetime.now()
        )
        
        # 7. Guardar recomendación en base de datos
        background_tasks.add_task(
            save_recommendation_to_db, 
            db, recommendation, current_user.id
        )
        
        logger.info(f"✅ Recomendaciones generadas: {len(recommended_videos)} videos")
        return recommendation
        
    except Exception as e:
        logger.error(f"❌ Error generando recomendaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

async def analyze_error_patterns_with_llm(
    failed_questions: List[FailedQuestionAnalysis], 
    db: Session
) -> Dict[str, Any]:
    """Analizar patrones de error usando LLM"""
    try:
        # Obtener detalles completos de las preguntas
        question_details = []
        for fq in failed_questions:
            question = db.query(Question).filter(Question.id == fq.question_id).first()
            if question:
                question_details.append({
                    'id': fq.question_id,
                    'text': question.question_text,
                    'topic': question.tags[2] if len(question.tags) > 2 else 'General',
                    'competencia': question.tags[1] if len(question.tags) > 1 else '',
                    'user_answer': fq.user_answer,
                    'correct_answer': fq.correct_answer,
                    'difficulty': fq.difficulty,
                    'response_time': fq.response_time_ms
                })
        
        # Simular análisis LLM (en producción usaría OpenAI API)
        analysis = {
            'dominant_error_pattern': 'conceptual_misunderstanding',
            'weakness_areas': [q['topic'] for q in question_details],
            'recommended_approach': 'visual_learning_with_examples',
            'confidence_score': 0.85,
            'learning_style_suggestion': 'multimedia_reinforcement'
        }
        
        logger.info(f"🧠 Análisis LLM completado: {analysis['dominant_error_pattern']}")
        return analysis
        
    except Exception as e:
        logger.error(f"❌ Error en análisis LLM: {e}")
        return {'error': str(e)}

def extract_priority_topics(
    failed_questions: List[FailedQuestionAnalysis], 
    error_analysis: Dict[str, Any]
) -> List[str]:
    """Extraer temas prioritarios basados en análisis de errores"""
    topic_frequency = {}
    
    for fq in failed_questions:
        if fq.topic not in topic_frequency:
            topic_frequency[fq.topic] = 0
        topic_frequency[fq.topic] += 1
    
    # Ordenar por frecuencia de error
    priority_topics = sorted(topic_frequency.items(), key=lambda x: x[1], reverse=True)
    return [topic for topic, _ in priority_topics[:5]]  # Top 5 temas

async def find_relevant_videos_with_ai(
    db: Session,
    subject_id: str,
    priority_topics: List[str],
    error_analysis: Dict[str, Any],
    max_duration_minutes: int
) -> List[VideoRecommendation]:
    """Encontrar videos relevantes usando matching inteligente"""
    try:
        logger.info(f"🎯 Buscando videos para {len(priority_topics)} temas prioritarios")
        
        # Buscar videos en la tabla youtube_catalog
        video_results = []
        
        for topic in priority_topics:
            # Buscar videos por tema usando LIKE para matching flexible
            query = text("""
                SELECT yc.id, yc.youtube_id, yc.youtube_url, yc.title, 
                       yc.channel_name, yc.duration_minutes, yc.quality_score,
                       yc.topics_covered, yc.codigo_tema
                FROM youtube_catalog yc
                WHERE yc.subject_id = :subject_id
                AND (
                    yc.title ILIKE :topic_pattern
                    OR :topic = ANY(yc.topics_covered)
                    OR yc.codigo_tema ILIKE :topic_pattern
                )
                AND yc.is_active = TRUE
                ORDER BY yc.quality_score DESC, yc.duration_minutes ASC
                LIMIT 3
            """)
            
            results = db.execute(query, {
                "subject_id": subject_id,
                "topic": topic,
                "topic_pattern": f"%{topic}%"
            }).fetchall()
            
            for row in results:
                # Calcular score de relevancia basado en múltiples factores
                relevance_score = calculate_relevance_score(
                    row, topic, error_analysis, max_duration_minutes
                )
                
                video_rec = VideoRecommendation(
                    video_id=str(row[0]),
                    youtube_id=row[1],
                    youtube_url=row[2],
                    title=row[3],
                    channel_name=row[4] or "Canal Educativo",
                    duration_minutes=row[5] or 15,
                    relevance_score=relevance_score,
                    reason=f"Recomendado para reforzar: {topic}",
                    topic_match=topic
                )
                
                video_results.append(video_rec)
        
        # Eliminar duplicados y ordenar por relevancia
        unique_videos = {}
        for video in video_results:
            if video.youtube_id not in unique_videos or video.relevance_score > unique_videos[video.youtube_id].relevance_score:
                unique_videos[video.youtube_id] = video
        
        final_videos = sorted(unique_videos.values(), key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"✅ Encontrados {len(final_videos)} videos únicos recomendados")
        return final_videos[:10]  # Máximo 10 videos
        
    except Exception as e:
        logger.error(f"❌ Error buscando videos: {e}")
        return []

def calculate_relevance_score(
    video_row, 
    target_topic: str, 
    error_analysis: Dict[str, Any], 
    max_duration: int
) -> float:
    """Calcular score de relevancia para un video"""
    base_score = 0.5
    
    # Factor de calidad del video
    quality_score = float(video_row[6]) if video_row[6] else 0.8
    base_score += quality_score * 0.3
    
    # Factor de duración (preferir videos más cortos)
    duration = int(video_row[5]) if video_row[5] else 15
    if duration <= max_duration:
        duration_factor = 1.0 - (duration / max_duration) * 0.2
        base_score += duration_factor * 0.2
    
    # Factor de matching de tópico
    title = str(video_row[3]).lower()
    if target_topic.lower() in title:
        base_score += 0.3
    
    # Factor de topics_covered
    topics_covered = video_row[7] if video_row[7] else []
    if isinstance(topics_covered, list) and target_topic in topics_covered:
        base_score += 0.2
    
    return min(1.0, base_score)

async def generate_study_plan_with_llm(
    priority_topics: List[str],
    recommended_videos: List[VideoRecommendation],
    user_level: int
) -> str:
    """Generar resumen del plan de estudio usando LLM"""
    try:
        # En producción, esto usaría la API de OpenAI
        # Por ahora, generar un resumen estructurado
        
        plan_summary = f"""
# 📚 Plan de Estudio Personalizado

## 🎯 Áreas de Mejora Identificadas
{', '.join(priority_topics[:3])}

## 📺 Videos Recomendados ({len(recommended_videos)} videos)
"""
        
        for i, video in enumerate(recommended_videos[:5], 1):
            plan_summary += f"""
### {i}. {video.title}
- **Canal**: {video.channel_name}
- **Duración**: {video.duration_minutes} minutos
- **Tema**: {video.topic_match}
- **Relevancia**: {video.relevance_score:.1%}
"""
        
        plan_summary += f"""

## ⏱️ Cronograma Sugerido
- **Tiempo total estimado**: {len(recommended_videos) * 2} horas
- **Distribución**: 2-3 videos por semana
- **Duración del plan**: 1 mes

## 🎮 Gamificación
- **XP por video completado**: 100-200 XP
- **Bonus por completar plan**: 1000 XP
- **Rango objetivo**: {get_target_rank(user_level)}
"""
        
        return plan_summary.strip()
        
    except Exception as e:
        logger.error(f"❌ Error generando plan con LLM: {e}")
        return "Plan de estudio personalizado basado en áreas de mejora identificadas."

def get_target_rank(current_level: int) -> str:
    """Obtener rango objetivo basado en nivel actual"""
    if current_level < 10:
        return "D (Nivel 10-15)"
    elif current_level < 20:
        return "C (Nivel 20-30)"
    elif current_level < 40:
        return "B (Nivel 40-50)"
    else:
        return "A (Nivel 50+)"

async def save_recommendation_to_db(
    db: Session, 
    recommendation: StudyRecommendation, 
    user_id: str
):
    """Guardar recomendación en la base de datos para persistencia"""
    try:
        # Crear entrada en study_plans
        study_plan = StudyPlan(
            id=uuid.UUID(recommendation.recommendation_id),
            user_id=uuid.UUID(user_id),
            subject_id=uuid.UUID(recommendation.subject_id),
            plan_name=f"Plan Inteligente - {recommendation.subject_name}",
            plan_data={
                "type": "intelligent_recommendation",
                "test_id": recommendation.test_id,
                "failed_questions_count": recommendation.total_failed_questions,
                "priority_topics": recommendation.priority_topics,
                "videos": [video.dict() for video in recommendation.recommended_videos],
                "summary": recommendation.study_plan_summary,
                "generated_at": recommendation.created_at.isoformat(),
                "expires_at": recommendation.expires_at.isoformat()
            },
            total_units=len(recommendation.recommended_videos),
            completed_units=0,
            progress_percentage=0.0,
            is_active=True,
            generated_at=recommendation.created_at,
            updated_at=recommendation.created_at
        )
        
        db.add(study_plan)
        
        # Crear unidades de progreso para cada video
        for i, video in enumerate(recommendation.recommended_videos, 1):
            unit_progress = PlanProgress(
                id=uuid.uuid4(),
                plan_id=study_plan.id,
                unit_number=i,
                unit_name=video.title,
                unit_description=f"Video sobre {video.topic_match}",
                unit_content={
                    "type": "video",
                    "youtube_id": video.youtube_id,
                    "youtube_url": video.youtube_url,
                    "channel": video.channel_name,
                    "duration_minutes": video.duration_minutes,
                    "relevance_score": video.relevance_score,
                    "reason": video.reason
                },
                is_completed=False,
                score=0.0,
                created_at=datetime.now()
            )
            db.add(unit_progress)
        
        db.commit()
        logger.info(f"✅ Recomendación guardada en BD: {recommendation.recommendation_id}")
        
    except Exception as e:
        logger.error(f"❌ Error guardando recomendación: {e}")
        db.rollback()

@router.get("/user-recommendations/{user_id}")
async def get_user_recommendations(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener recomendaciones activas del usuario"""
    try:
        # Verificar que el usuario puede acceder a estas recomendaciones
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Buscar planes de estudio inteligentes activos
        query = text("""
            SELECT sp.id, sp.plan_name, sp.subject_id, sp.plan_data,
                   sp.total_units, sp.completed_units, sp.progress_percentage,
                   sp.generated_at, s.name as subject_name
            FROM study_plans sp
            JOIN subjects s ON sp.subject_id = s.id
            WHERE sp.user_id = :user_id 
            AND sp.is_active = TRUE
            AND sp.plan_data->>'type' = 'intelligent_recommendation'
            AND (sp.plan_data->>'expires_at')::timestamp > NOW()
            ORDER BY sp.generated_at DESC
        """)
        
        results = db.execute(query, {"user_id": user_id}).fetchall()
        
        recommendations = []
        for row in results:
            plan_data = row[3]  # plan_data JSON
            
            recommendation = {
                "recommendation_id": str(row[0]),
                "plan_name": row[1],
                "subject_id": str(row[2]),
                "subject_name": row[8],
                "total_units": row[4],
                "completed_units": row[5],
                "progress_percentage": float(row[6]),
                "generated_at": row[7].isoformat(),
                "priority_topics": plan_data.get('priority_topics', []),
                "videos_count": len(plan_data.get('videos', [])),
                "estimated_hours": plan_data.get('videos', []),
                "summary": plan_data.get('summary', ''),
                "status": "active" if row[5] < row[4] else "completed"
            }
            
            recommendations.append(recommendation)
        
        logger.info(f"📊 Encontradas {len(recommendations)} recomendaciones para usuario {user_id}")
        return {
            "user_id": user_id,
            "active_recommendations": recommendations,
            "total_count": len(recommendations)
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo recomendaciones: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@router.get("/recommendation-details/{recommendation_id}")
async def get_recommendation_details(
    recommendation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener detalles completos de una recomendación específica"""
    try:
        # Buscar el plan de estudio
        query = text("""
            SELECT sp.id, sp.plan_name, sp.subject_id, sp.plan_data,
                   sp.total_units, sp.completed_units, sp.progress_percentage,
                   s.name as subject_name
            FROM study_plans sp
            JOIN subjects s ON sp.subject_id = s.id
            WHERE sp.id = :recommendation_id
            AND sp.user_id = :user_id
            AND sp.is_active = TRUE
        """)
        
        result = db.execute(query, {
            "recommendation_id": recommendation_id,
            "user_id": str(current_user.id)
        }).fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        
        plan_data = result[3]  # plan_data JSON
        
        # Obtener progreso de unidades
        progress_query = text("""
            SELECT unit_number, unit_name, unit_content, is_completed, score
            FROM plan_progress
            WHERE plan_id = :plan_id
            ORDER BY unit_number
        """)
        
        progress_results = db.execute(progress_query, {
            "plan_id": recommendation_id
        }).fetchall()
        
        units = []
        for prog_row in progress_results:
            unit_content = prog_row[2]  # unit_content JSON
            
            unit = {
                "unit_number": prog_row[0],
                "unit_name": prog_row[1],
                "is_completed": prog_row[3],
                "score": float(prog_row[4]),
                "video": unit_content if unit_content else {}
            }
            units.append(unit)
        
        recommendation_details = {
            "recommendation_id": recommendation_id,
            "plan_name": result[1],
            "subject_name": result[7],
            "total_units": result[4],
            "completed_units": result[5],
            "progress_percentage": float(result[6]),
            "priority_topics": plan_data.get('priority_topics', []),
            "summary": plan_data.get('summary', ''),
            "units": units,
            "expires_at": plan_data.get('expires_at'),
            "test_id": plan_data.get('test_id')
        }
        
        return recommendation_details
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo detalles: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendation details: {str(e)}")

@router.post("/mark-video-completed/{recommendation_id}/{unit_number}")
async def mark_video_completed(
    recommendation_id: str,
    unit_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marcar un video como completado y actualizar progreso"""
    try:
        # Actualizar progreso de la unidad
        update_query = text("""
            UPDATE plan_progress 
            SET is_completed = TRUE, 
                completion_date = NOW(),
                score = 100.0
            WHERE plan_id = :plan_id 
            AND unit_number = :unit_number
        """)
        
        db.execute(update_query, {
            "plan_id": recommendation_id,
            "unit_number": unit_number
        })
        
        # Actualizar progreso general del plan
        progress_query = text("""
            UPDATE study_plans 
            SET completed_units = (
                SELECT COUNT(*) FROM plan_progress 
                WHERE plan_id = :plan_id AND is_completed = TRUE
            ),
            progress_percentage = (
                SELECT COUNT(*) * 100.0 / :total_units
                FROM plan_progress 
                WHERE plan_id = :plan_id AND is_completed = TRUE
            ),
            updated_at = NOW()
            WHERE id = :plan_id AND user_id = :user_id
        """)
        
        # Obtener total_units
        total_query = text("SELECT total_units FROM study_plans WHERE id = :plan_id")
        total_result = db.execute(total_query, {"plan_id": recommendation_id}).fetchone()
        total_units = total_result[0] if total_result else 1
        
        db.execute(progress_query, {
            "plan_id": recommendation_id,
            "user_id": str(current_user.id),
            "total_units": total_units
        })
        
        db.commit()
        
        # Otorgar XP al usuario
        xp_gained = 150  # XP por completar video
        current_user.experience += xp_gained
        db.commit()
        
        logger.info(f"✅ Video {unit_number} marcado como completado, +{xp_gained} XP")
        
        return {
            "status": "completed",
            "unit_number": unit_number,
            "xp_gained": xp_gained,
            "message": f"¡Video completado! +{xp_gained} XP ganados"
        }
        
    except Exception as e:
        logger.error(f"❌ Error marcando video completado: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating progress: {str(e)}")
