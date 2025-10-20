"""
Claude-Powered Study Plan Generator
Genera planes de estudio personalizados usando Claude API para análisis inteligente
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
import logging
import json
import uuid
from datetime import datetime
import os

from ..core.database import get_db
from ..models.study_plan import StudyPlan

# Import Anthropic Claude API
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("Anthropic library not installed. Install with: pip install anthropic")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/claude-study-plan", tags=["claude-recommendations"])

def get_claude_recommendations(
    failed_topics: List[Dict],
    available_videos: List[Dict],
    subject_name: str,
    score_percentage: float
) -> Dict[str, Any]:
    """
    Usa Claude API para generar recomendaciones inteligentes de videos
    basándose en los temas con errores y videos disponibles
    """
    if not ANTHROPIC_AVAILABLE:
        logger.warning("Anthropic not available, using fallback matching")
        return None

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not found in environment")
        return None

    try:
        client = Anthropic(api_key=api_key)

        # Preparar contexto para Claude
        topics_text = "\n".join([
            f"- {topic['topic_name']}: {topic['error_count']} errores (Competencia: {topic['competencia']}, Componente: {topic['componente']})"
            for topic in failed_topics[:10]
        ])

        videos_text = "\n".join([
            f"- ID:{video['id']} | {video['title']} ({video['duration_minutes']}min) - Canal: {video['channel']} | Competencia: {video.get('competencia', 'N/A')} | Componente: {video.get('componente', 'N/A')}"
            for video in available_videos[:30]
        ])

        prompt = f"""Eres un experto tutor educativo del examen ICFES de Colombia. Analiza los siguientes datos de un estudiante:

**Materia**: {subject_name}
**Puntaje obtenido**: {score_percentage}%

**Temas con más errores**:
{topics_text}

**Videos educativos disponibles en YouTube**:
{videos_text}

**Tu tarea**:
1. Analiza los temas donde el estudiante tuvo más errores
2. Para CADA tema con errores, busca videos que coincidan en:
   - Competencia ICFES (ej: "Interpretación y representación")
   - Componente ICFES (ej: "Aleatorio")
   - Contenido del título del video
3. Crea un plan de estudio de 4-6 unidades, priorizando las áreas más críticas
4. Para cada video que recomiendes, JUSTIFICA específicamente:
   - Qué tema fallado del estudiante cubre
   - Por qué es relevante (matching de competencia/componente)
   - Qué aprenderá el estudiante con ese video

**IMPORTANTE**:
- Haz matching explícito: competencia del error ↔ competencia del video
- Haz matching explícito: componente del error ↔ componente del video
- Cada video debe tener una justificación específica basada en los errores
- Prioriza videos de alta calidad (mayor duración generalmente = más completo)
- Organiza de lo más urgente a lo menos urgente

Responde ÚNICAMENTE con un objeto JSON válido (sin markdown, sin ```json):
{{
  "study_strategy": "Estrategia general de estudio en 2-3 oraciones",
  "estimated_weeks": 4,
  "units": [
    {{
      "unit_number": 1,
      "title": "Título de la unidad",
      "description": "Descripción breve",
      "failed_topics_covered": ["Tema1", "Tema2"],
      "priority": "alta|media|baja",
      "recommended_videos": [
        {{
          "video_id": "id del video",
          "covers_failed_topic": "Nombre exacto del tema fallado que cubre",
          "competence_match": "Competencia ICFES que refuerza",
          "component_match": "Componente ICFES que trabaja",
          "justification": "Por qué este video es recomendado para ESTE tema específico con errores"
        }}
      ],
      "learning_objectives": ["objetivo1", "objetivo2"],
      "unit_rationale": "Por qué esta unidad es importante para el estudiante"
    }}
  ],
  "additional_tips": ["tip1", "tip2", "tip3"]
}}"""

        logger.info("🤖 Llamando a Claude API para recomendaciones...")

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4096,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = message.content[0].text
        logger.info(f"✅ Claude API respondió exitosamente")

        # Parse JSON response
        try:
            recommendations = json.loads(response_text)
            return recommendations
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group())
                return recommendations
            else:
                logger.error(f"No se pudo parsear respuesta de Claude: {response_text[:200]}")
                return None

    except Exception as e:
        logger.error(f"❌ Error al llamar Claude API: {e}", exc_info=True)
        return None


@router.post("/generate")
async def generate_claude_study_plan(
    request_data: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Genera un plan de estudio usando Claude API para recomendaciones inteligentes

    Body:
    {
        "test_id": "diagnostic-test-...",
        "subject_id": "550e8400-...",
        "user_id": "optional-user-id"
    }
    """
    try:
        test_id = request_data.get('test_id')
        subject_id = request_data.get('subject_id')
        user_id = request_data.get('user_id', None)

        if not test_id or not subject_id:
            raise HTTPException(
                status_code=400,
                detail="test_id and subject_id are required"
            )

        logger.info(f"🎯 Generating Claude-powered study plan for test {test_id}")

        # 1. Get diagnostic test results
        diagnostic_query = text("""
            SELECT
                dt.score_percentage,
                dt.weaknesses,
                dt.score_by_topic,
                s.name as subject_name
            FROM diagnostic_tests dt
            JOIN subjects s ON dt.subject_id = s.id
            WHERE dt.id = :test_id
        """)

        diag_result = db.execute(diagnostic_query, {"test_id": test_id}).fetchone()

        if not diag_result:
            raise HTTPException(status_code=404, detail="Diagnostic test not found")

        score_percentage = diag_result[0] or 0
        weaknesses = diag_result[1] or []
        score_by_topic = diag_result[2] or {}
        subject_name = diag_result[3]

        # 2. Get incorrect questions WITH full details
        incorrect_questions_query = text("""
            SELECT
                q.id as question_id,
                q.pregunta_texto,
                q.competencia,
                q.componente,
                t.name as topic_name,
                q.explanation
            FROM diagnostic_test_answers dta
            JOIN questions q ON dta.question_id = q.id
            LEFT JOIN topics t ON q.topic_id = t.id
            WHERE dta.diagnostic_test_id = :test_id
            AND dta.is_correct = false
            ORDER BY q.competencia, q.componente
            LIMIT 20
        """)

        incorrect_questions_raw = db.execute(incorrect_questions_query, {"test_id": test_id}).fetchall()

        # Store full question details for display
        incorrect_questions = [
            {
                "id": str(row[0]),
                "pregunta_texto": (row[1] or "Pregunta sin texto")[:150] + ("..." if len(row[1] or "") > 150 else ""),  # Truncate for display
                "competencia": row[2] or "",
                "componente": row[3] or "",
                "topic_name": row[4] or "General",
                "difficulty_level": 5,  # Default difficulty
                "explanation": row[5] or ""
            }
            for row in incorrect_questions_raw
        ]

        # Also get aggregated topics for Claude matching
        incorrect_topics_query = text("""
            SELECT DISTINCT
                t.name as topic_name,
                q.competencia,
                q.componente,
                COUNT(*) as error_count
            FROM diagnostic_test_answers dta
            JOIN questions q ON dta.question_id = q.id
            LEFT JOIN topics t ON q.topic_id = t.id
            WHERE dta.diagnostic_test_id = :test_id
            AND dta.is_correct = false
            GROUP BY t.name, q.competencia, q.componente
            ORDER BY error_count DESC
        """)

        incorrect_topics_raw = db.execute(incorrect_topics_query, {"test_id": test_id}).fetchall()

        failed_topics = [
            {
                "topic_name": row[0] or "General",
                "competencia": row[1] or "",
                "componente": row[2] or "",
                "error_count": row[3]
            }
            for row in incorrect_topics_raw
        ]

        # 3. Get available videos from catalog (only verified working videos)
        videos_query = text("""
            SELECT
                yc.id,
                yc.youtube_id,
                yc.title,
                yc.youtube_url,
                yc.channel_name,
                yc.duration_minutes,
                yc.quality_score,
                yc.description,
                yc.icfes_competence,
                yc.icfes_component,
                yc.codigo_tema
            FROM youtube_catalog yc
            WHERE yc.subject_id = :subject_id
            AND yc.is_active = true
            AND (yc.description IS NULL OR yc.description NOT LIKE '%REPORTED%')
            AND yc.quality_score >= 0.8
            ORDER BY yc.quality_score DESC, yc.duration_minutes DESC
            LIMIT 30
        """)

        videos_raw = db.execute(videos_query, {"subject_id": subject_id}).fetchall()

        available_videos = [
            {
                "id": str(row[0]),
                "youtube_id": row[1],
                "title": row[2],
                "url": row[3] or f"https://www.youtube.com/watch?v={row[1]}",
                "channel": row[4],
                "duration_minutes": row[5] or 10,
                "quality_score": float(row[6]) if row[6] else 0.7,
                "description": row[7] or "",
                "competencia": row[8] or "",
                "componente": row[9] or "",
                "codigo_tema": row[10] or ""
            }
            for row in videos_raw
        ]

        if not available_videos:
            raise HTTPException(
                status_code=404,
                detail=f"No videos found for subject {subject_id}"
            )

        logger.info(f"📊 Found {len(failed_topics)} weak topics and {len(available_videos)} videos")

        # 4. Get Claude recommendations
        claude_recs = get_claude_recommendations(
            failed_topics=failed_topics,
            available_videos=available_videos,
            subject_name=subject_name,
            score_percentage=float(score_percentage)
        )

        # 5. Build study plan structure
        units = []

        if claude_recs and 'units' in claude_recs:
            # Use Claude recommendations with detailed justifications
            logger.info("✅ Using Claude AI recommendations with detailed matching")
            video_map = {v['id']: v for v in available_videos}

            for unit_rec in claude_recs['units']:
                unit_videos = []

                # Process new format with detailed video justifications
                for video_rec in unit_rec.get('recommended_videos', []):
                    vid_id = video_rec.get('video_id')
                    if vid_id and vid_id in video_map:
                        video = video_map[vid_id]
                        unit_videos.append({
                            "id": video['id'],
                            "youtube_id": video['youtube_id'],
                            "title": video['title'],
                            "url": video['url'],
                            "channel": video['channel'],
                            "duration_minutes": video['duration_minutes'],
                            "xp": 100 + video['duration_minutes'] * 2,
                            # Metadata detallada de justificación
                            "covers_failed_topic": video_rec.get('covers_failed_topic', ''),
                            "competence_match": video_rec.get('competence_match', ''),
                            "component_match": video_rec.get('component_match', ''),
                            "justification": video_rec.get('justification', 'Recomendado por Claude AI'),
                            "recommendation_reason": video_rec.get('justification', 'Recomendado por Claude AI')
                        })

                # Fallback: support old format if needed
                if not unit_videos:
                    for vid_id in unit_rec.get('recommended_video_ids', []):
                        if vid_id in video_map:
                            video = video_map[vid_id]
                            unit_videos.append({
                                "id": video['id'],
                                "youtube_id": video['youtube_id'],
                                "title": video['title'],
                                "url": video['url'],
                                "channel": video['channel'],
                                "duration_minutes": video['duration_minutes'],
                                "xp": 100 + video['duration_minutes'] * 2,
                                "recommendation_reason": unit_rec.get('unit_rationale', 'Recomendado por Claude AI')
                            })

                if unit_videos:
                    unit_data = {
                        "unit_number": unit_rec.get('unit_number', len(units) + 1),
                        "title": unit_rec.get('title', f"Unidad {len(units) + 1}"),
                        "description": unit_rec.get('description', ''),
                        "failed_topics_covered": unit_rec.get('failed_topics_covered', []),
                        "videos": unit_videos,
                        "priority": unit_rec.get('priority', 'media'),
                        "learning_objectives": unit_rec.get('learning_objectives', []),
                        "ai_rationale": unit_rec.get('unit_rationale', ''),
                        # Add incorrect questions that relate to this unit
                        "incorrect_questions": [
                            q for q in incorrect_questions
                            if any(
                                (q['competencia'] and q['competencia'] in video.get('competence_match', '')) or
                                (q['componente'] and q['componente'] in video.get('component_match', '')) or
                                (q['topic_name'] in unit_rec.get('failed_topics_covered', []))
                                for video in unit_videos
                            )
                        ][:3]  # Limit to 3 questions per unit for display
                    }
                    units.append(unit_data)

        else:
            # Fallback to simple matching
            logger.warning("⚠️ Claude unavailable, using simple matching")
            unit_number = 1
            for topic in failed_topics[:6]:
                topic_name = topic['topic_name']
                matching_videos = []

                for video in available_videos[:20]:
                    if (topic['competencia'] and topic['competencia'].lower() in (video['competencia'] or '').lower()) or \
                       (topic['componente'] and topic['componente'].lower() in (video['componente'] or '').lower()) or \
                       (topic_name.lower() in (video['title'] or '').lower()):
                        matching_videos.append({
                            "id": video['id'],
                            "youtube_id": video['youtube_id'],
                            "title": video['title'],
                            "url": video['url'],
                            "channel": video['channel'],
                            "duration_minutes": video['duration_minutes'],
                            "xp": 100 + video['duration_minutes'] * 2,
                            "recommendation_reason": f"Refuerza {topic_name}"
                        })

                if not matching_videos:
                    for video in available_videos[:3]:
                        matching_videos.append({
                            "id": video['id'],
                            "youtube_id": video['youtube_id'],
                            "title": video['title'],
                            "url": video['url'],
                            "channel": video['channel'],
                            "duration_minutes": video['duration_minutes'],
                            "xp": 100 + video['duration_minutes'] * 2,
                            "recommendation_reason": f"Video educativo sobre {subject_name}"
                        })

                if matching_videos:
                    units.append({
                        "unit_number": unit_number,
                        "title": topic_name,
                        "description": f"Videos sobre {topic_name}",
                        "videos": matching_videos[:5],
                        "priority": "alta" if unit_number <= 3 else "media"
                    })
                    unit_number += 1

        # 6. Calculate totals
        total_videos = sum(len(unit['videos']) for unit in units)
        total_duration = sum(
            sum(v['duration_minutes'] for v in unit['videos'])
            for unit in units
        )

        # 7. Build final plan data
        plan_data = {
            "metadata": {
                "test_id": test_id,
                "subject_id": subject_id,
                "subject_name": subject_name,
                "score_percentage": float(score_percentage),
                "generated_at": datetime.utcnow().isoformat(),
                "total_units": len(units),
                "total_videos": total_videos,
                "total_duration_minutes": total_duration,
                "ai_generated": bool(claude_recs),
                "generator": "claude-3.5-sonnet" if claude_recs else "simple-matching"
            },
            "units": units,
            "weaknesses": weaknesses,
            "failed_topics": failed_topics,
            "recommendations": {
                "study_frequency": "3-4 veces por semana",
                "session_duration": "30-45 minutos",
                "estimated_completion": f"{claude_recs.get('estimated_weeks', 4)} semanas" if claude_recs else "4 semanas",
                "study_strategy": claude_recs.get('study_strategy', '') if claude_recs else '',
                "additional_tips": claude_recs.get('additional_tips', []) if claude_recs else []
            }
        }

        # 8. Save to database
        existing_plan = None
        if user_id:
            existing_plan = db.query(StudyPlan).filter(
                StudyPlan.user_id == user_id,
                StudyPlan.subject_id == subject_id,
                StudyPlan.is_active == True
            ).first()

        if existing_plan:
            existing_plan.plan_data = plan_data
            existing_plan.total_units = len(units)
            existing_plan.updated_at = datetime.utcnow()
            plan_id = str(existing_plan.id)
            logger.info(f"📝 Updated existing plan {plan_id}")
        else:
            new_plan = StudyPlan(
                id=uuid.uuid4(),
                user_id=user_id if user_id else None,
                subject_id=subject_id,
                plan_name=f"Plan de Estudio - {subject_name} (AI)",
                plan_data=plan_data,
                total_units=len(units),
                completed_units=0,
                progress_percentage=0,
                is_active=True,
                generated_at=datetime.utcnow()
            )
            db.add(new_plan)
            plan_id = str(new_plan.id)
            logger.info(f"✨ Created new AI-powered plan {plan_id}")

        db.commit()

        return {
            "success": True,
            "plan_id": plan_id,
            "plan_data": plan_data,
            "ai_powered": bool(claude_recs),
            "message": "Plan de estudio generado con Claude AI" if claude_recs else "Plan de estudio generado (sin AI)"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating study plan: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/plan/{plan_id}")
async def get_claude_study_plan(plan_id: str, db: Session = Depends(get_db)):
    """Get a Claude-generated study plan by ID"""
    try:
        plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()

        if not plan:
            raise HTTPException(status_code=404, detail="Study plan not found")

        return {
            "success": True,
            "plan_id": str(plan.id),
            "plan_data": plan.plan_data,
            "progress_percentage": float(plan.progress_percentage) if plan.progress_percentage else 0,
            "completed_units": plan.completed_units,
            "total_units": plan.total_units,
            "ai_generated": plan.plan_data.get('metadata', {}).get('ai_generated', False)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving study plan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
