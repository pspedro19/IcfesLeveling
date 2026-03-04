"""
Spaced Repetition (SM-2) Routes - ICFES Leveling API

Endpoints for the spaced repetition system:
- POST /spaced-repetition/schedule - Create SR schedule for a study plan
- GET /spaced-repetition/daily-reviews - Get today's due items
- POST /spaced-repetition/review/{item_id} - Submit review result
- GET /spaced-repetition/analytics - Get retention analytics
- GET /spaced-repetition/stats - Get user's SR statistics

The SM-2 algorithm schedules reviews at optimal intervals for long-term retention.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from uuid import UUID
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.spaced_repetition_service import (
    SpacedRepetitionService,
    ReviewResult as ServiceReviewResult,
    ItemStatus
)
from ..schemas.spaced_repetition import (
    ReviewResult,
    SpacedItemResponse,
    DailyReviewsResponse,
    SubmitReviewRequest,
    SubmitReviewResponse,
    CreateScheduleRequest,
    CreateScheduleResponse,
    RetentionAnalyticsResponse,
    SpacedRepetitionStatsResponse,
)
from ..utils.response import success_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/spaced-repetition", tags=["spaced-repetition"])


# ============================================
# HELPER FUNCTIONS
# ============================================

def _map_review_result(result: ReviewResult) -> ServiceReviewResult:
    """Map schema ReviewResult to service ReviewResult enum"""
    mapping = {
        ReviewResult.AGAIN: ServiceReviewResult.AGAIN,
        ReviewResult.HARD: ServiceReviewResult.HARD,
        ReviewResult.GOOD: ServiceReviewResult.GOOD,
        ReviewResult.EASY: ServiceReviewResult.EASY,
    }
    return mapping[result]


def _convert_spaced_item_to_response(item) -> SpacedItemResponse:
    """Convert service SpacedItem to response schema"""
    # Handle both dataclass and dict
    if hasattr(item, '__dict__'):
        item_dict = item.__dict__
    else:
        item_dict = item

    return SpacedItemResponse(
        item_id=item_dict.get("item_id", ""),
        question_id=item_dict.get("content_data", {}).get("question_id") if isinstance(item_dict.get("content_data"), dict) else None,
        question_text=item_dict.get("content_data", {}).get("question_text") if isinstance(item_dict.get("content_data"), dict) else None,
        topic_name=item_dict.get("content_data", {}).get("topic_name") if isinstance(item_dict.get("content_data"), dict) else None,
        content_type=item_dict.get("content_type", "question"),
        ease_factor=item_dict.get("ease_factor", 2.5),
        interval=item_dict.get("interval", 1),
        repetitions=item_dict.get("repetitions", 0),
        due_date=item_dict.get("due_date") or datetime.now(),
        status=item_dict.get("status", ItemStatus.NEW).value if hasattr(item_dict.get("status"), 'value') else str(item_dict.get("status", "new")),
        success_rate=item_dict.get("success_rate", 0.0),
        total_reviews=item_dict.get("total_reviews", 0),
        average_response_time_ms=item_dict.get("average_response_time"),
        difficulty_rating=item_dict.get("difficulty_rating", 0.5)
    )


# ============================================
# ENDPOINTS
# ============================================

@router.post("/schedule", response_model=None)
async def create_spaced_repetition_schedule(
    request: CreateScheduleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Crear un horario de repaso espaciado para un plan de estudio.

    Genera items de repaso basados en el algoritmo SM-2 para optimizar
    la retencion a largo plazo del conocimiento.

    - **plan_id**: ID del plan de estudio
    - **topics**: Lista opcional de temas a incluir
    """
    try:
        service = SpacedRepetitionService(db)

        result = service.create_spaced_repetition_schedule(
            user_id=str(current_user.id),
            plan_id=request.plan_id,
            topics=request.topics
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "SCHEDULE_CREATION_FAILED",
                    "message": f"No se pudo crear el horario de repaso: {result['error']}"
                }
            )

        # Build response
        response_data = CreateScheduleResponse(
            success=True,
            system_id=result.get("system_id", ""),
            plan_id=result.get("plan_id", request.plan_id),
            total_items=result.get("total_items", 0),
            estimated_retention_rate=result.get("performance_metrics", {}).get("estimated_retention_rate", 0.85),
            optimal_review_frequency=result.get("performance_metrics", {}).get("optimal_review_frequency", "daily"),
            algorithm_type=result.get("algorithm_settings", {}).get("algorithm_type", "Enhanced SM-2"),
            ease_factor_range=result.get("algorithm_settings", {}).get("ease_factor_range", [1.3, 4.0]),
            learning_steps=result.get("algorithm_settings", {}).get("learning_steps", [1, 10, 1440]),
            items_summary={
                "concepts": len([i for i in result.get("spaced_items", []) if i.get("content_type") == "concept"]),
                "questions": len([i for i in result.get("spaced_items", []) if i.get("content_type") == "question"])
            },
            first_review_date=datetime.now() + timedelta(minutes=1)
        )

        return success_response(response_data.model_dump())

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error creating schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PLAN",
                "message": f"Plan de estudio no valido: {str(e)}"
            }
        )
    except Exception as e:
        logger.error(f"Error creating spaced repetition schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Error interno al crear el horario de repaso espaciado"
            }
        )


@router.get("/daily-reviews", response_model=None)
async def get_daily_reviews(
    date: Optional[str] = Query(
        default=None,
        description="Fecha para obtener repasos (YYYY-MM-DD). Por defecto: hoy"
    ),
    max_reviews: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Numero maximo de items a revisar"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener los items de repaso del dia.

    Retorna todos los items pendientes de revision para la fecha especificada,
    ordenados por prioridad (items vencidos primero, luego por dificultad).

    - **date**: Fecha para obtener repasos (opcional, por defecto hoy)
    - **max_reviews**: Numero maximo de items (por defecto 50)
    """
    try:
        service = SpacedRepetitionService(db)

        # Parse date if provided
        review_date = None
        if date:
            try:
                review_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_DATE_FORMAT",
                        "message": "Formato de fecha invalido. Use YYYY-MM-DD"
                    }
                )

        result = service.get_daily_reviews(
            user_id=str(current_user.id),
            date=review_date,
            max_reviews=max_reviews
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "FETCH_FAILED",
                    "message": f"Error al obtener repasos: {result['error']}"
                }
            )

        # Convert items to response format
        items = []
        for item in result.get("review_session", {}).get("items", []):
            try:
                items.append(_convert_spaced_item_to_response(item))
            except Exception as e:
                logger.warning(f"Error converting item: {e}")
                continue

        response_data = DailyReviewsResponse(
            date=datetime.strptime(result.get("date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d") if isinstance(result.get("date"), str) else datetime.now(),
            user_id=str(current_user.id),
            total_due=result.get("total_due_items", 0),
            new_items=result.get("new_items", 0),
            review_items=result.get("review_items", 0),
            learning_items=result.get("learning_items", 0),
            items=[item.model_dump() for item in items] if items else [],
            estimated_duration_minutes=result.get("estimated_duration_minutes"),
            difficulty_balance=result.get("difficulty_balance"),
            retention_prediction=result.get("retention_prediction")
        )

        return success_response(response_data.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting daily reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Error interno al obtener los repasos del dia"
            }
        )


@router.post("/review/{item_id}", response_model=None)
async def submit_review_result(
    item_id: str,
    request: SubmitReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enviar el resultado de una revision de item.

    Procesa el resultado usando el algoritmo SM-2 y actualiza
    los intervalos de revision del item.

    - **item_id**: ID del item revisado
    - **result**: Resultado de la revision (again, hard, good, easy)
    - **response_time_ms**: Tiempo de respuesta en milisegundos
    """
    try:
        service = SpacedRepetitionService(db)

        # Map the review result
        service_result = _map_review_result(request.result)

        result = service.process_review_result(
            user_id=str(current_user.id),
            item_id=item_id,
            result=service_result,
            response_time_ms=request.response_time_ms,
            additional_data=request.additional_data
        )

        if not result.get("success", False):
            error_message = result.get("error", "Error desconocido")

            if "not found" in error_message.lower():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "code": "ITEM_NOT_FOUND",
                        "message": f"El item de repaso '{item_id}' no fue encontrado"
                    }
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "REVIEW_FAILED",
                    "message": f"Error al procesar la revision: {error_message}"
                }
            )

        # Calculate XP earned based on result
        xp_map = {
            ReviewResult.AGAIN: 0,
            ReviewResult.HARD: 5,
            ReviewResult.GOOD: 10,
            ReviewResult.EASY: 15
        }
        xp_earned = xp_map.get(request.result, 10)

        # Extract updated item data
        updated_item = result.get("updated_item", {})

        response_data = SubmitReviewResponse(
            success=True,
            item_id=item_id,
            result=request.result.value,
            new_ease_factor=updated_item.get("ease_factor", 2.5),
            new_interval=updated_item.get("interval", 1),
            next_review_date=datetime.fromisoformat(result.get("next_review_date")) if isinstance(result.get("next_review_date"), str) else result.get("next_review_date", datetime.now() + timedelta(days=1)),
            new_status=updated_item.get("status", ItemStatus.REVIEW).value if hasattr(updated_item.get("status"), 'value') else str(updated_item.get("status", "review")),
            xp_earned=xp_earned,
            streak_bonus=result.get("learning_progress", {}).get("streak_bonus") if result.get("learning_progress") else None,
            retention_prediction=result.get("retention_prediction"),
            learning_progress=result.get("learning_progress")
        )

        return success_response(response_data.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing review result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Error interno al procesar el resultado de la revision"
            }
        )


@router.get("/analytics", response_model=None)
async def get_retention_analytics(
    plan_id: Optional[str] = Query(
        default=None,
        description="ID del plan de estudio (opcional, para filtrar)"
    ),
    days_back: int = Query(
        default=30,
        ge=1,
        le=365,
        description="Dias hacia atras para analizar"
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener analiticas de retencion del sistema de repaso espaciado.

    Proporciona metricas detalladas sobre el rendimiento de retencion,
    curvas de olvido, y sugerencias de optimizacion.

    - **plan_id**: ID del plan de estudio (opcional)
    - **days_back**: Periodo de analisis en dias (por defecto 30)
    """
    try:
        service = SpacedRepetitionService(db)

        result = service.get_retention_analytics(
            user_id=str(current_user.id),
            plan_id=plan_id,
            days_back=days_back
        )

        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "ANALYTICS_FAILED",
                    "message": f"Error al obtener analiticas: {result['error']}"
                }
            )

        # Extract retention metrics
        retention_metrics = result.get("retention_metrics", {})

        response_data = RetentionAnalyticsResponse(
            user_id=str(current_user.id),
            plan_id=plan_id,
            analysis_period_days=days_back,
            analysis_date=datetime.now(),
            overall_retention_rate=retention_metrics.get("overall_retention_rate", 0.0),
            average_ease_factor=retention_metrics.get("average_ease_factor", 2.5),
            total_reviews=retention_metrics.get("total_reviews", 0),
            total_items=retention_metrics.get("total_items", 0),
            items_graduated=retention_metrics.get("items_graduated", 0),
            graduation_rate=retention_metrics.get("graduation_rate", 0.0),
            status_distribution=retention_metrics.get("status_distribution", {
                "new": 0,
                "learning": 0,
                "review": 0,
                "graduated": 0
            }),
            difficulty_distribution=retention_metrics.get("difficulty_distribution"),
            retention_trend=result.get("forgetting_curves", {}).get("retention_trend"),
            performance_trends=result.get("performance_trends"),
            insights=result.get("insights_and_recommendations", {}).get("insights", []) if isinstance(result.get("insights_and_recommendations"), dict) else None,
            optimization_suggestions=result.get("optimization_suggestions", []) if isinstance(result.get("optimization_suggestions"), list) else None
        )

        return success_response(response_data.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting retention analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Error interno al obtener analiticas de retencion"
            }
        )


@router.get("/stats", response_model=None)
async def get_spaced_repetition_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener estadisticas generales del sistema de repaso espaciado del usuario.

    Incluye metricas como items dominados, racha actual, tiempo total de estudio,
    y XP ganado.
    """
    try:
        service = SpacedRepetitionService(db)

        # Get all spaced items for user
        spaced_items = service._get_user_spaced_items(str(current_user.id))

        # Calculate statistics
        total_items = len(spaced_items) if spaced_items else 0
        items_mastered = len([i for i in spaced_items if hasattr(i, 'status') and i.status == ItemStatus.GRADUATED]) if spaced_items else 0
        items_learning = len([i for i in spaced_items if hasattr(i, 'status') and i.status in [ItemStatus.LEARNING, ItemStatus.REVIEW]]) if spaced_items else 0
        items_new = len([i for i in spaced_items if hasattr(i, 'status') and i.status == ItemStatus.NEW]) if spaced_items else 0

        # Calculate review stats
        total_reviews = sum(i.total_reviews for i in spaced_items if hasattr(i, 'total_reviews')) if spaced_items else 0
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)

        reviews_due_today = len([
            i for i in spaced_items
            if hasattr(i, 'due_date') and i.due_date and i.due_date <= tomorrow
        ]) if spaced_items else 0

        reviews_due_tomorrow = len([
            i for i in spaced_items
            if hasattr(i, 'due_date') and i.due_date and tomorrow < i.due_date <= tomorrow + timedelta(days=1)
        ]) if spaced_items else 0

        # Calculate accuracy
        success_rates = [i.success_rate for i in spaced_items if hasattr(i, 'success_rate') and i.success_rate > 0] if spaced_items else []
        average_accuracy = sum(success_rates) / len(success_rates) if success_rates else 0.0

        # Calculate average response time
        response_times = [i.average_response_time for i in spaced_items if hasattr(i, 'average_response_time') and i.average_response_time > 0] if spaced_items else []
        avg_response_time = sum(response_times) / len(response_times) if response_times else None

        # Get last review date
        review_dates = [i.last_reviewed for i in spaced_items if hasattr(i, 'last_reviewed') and i.last_reviewed] if spaced_items else []
        last_review = max(review_dates) if review_dates else None

        # Estimate XP earned (10 XP per successful review on average)
        total_xp = int(total_reviews * 10 * average_accuracy)

        response_data = SpacedRepetitionStatsResponse(
            user_id=str(current_user.id),
            total_items=total_items,
            items_mastered=items_mastered,
            items_learning=items_learning,
            items_new=items_new,
            total_reviews_completed=total_reviews,
            reviews_today=0,  # Would need session tracking
            reviews_due_today=reviews_due_today,
            reviews_due_tomorrow=reviews_due_tomorrow,
            current_streak_days=current_user.streak_days if hasattr(current_user, 'streak_days') else 0,
            longest_streak_days=current_user.streak_max if hasattr(current_user, 'streak_max') else 0,
            average_accuracy=round(average_accuracy, 3),
            average_response_time_ms=round(avg_response_time, 1) if avg_response_time else None,
            total_study_time_minutes=int(total_reviews * 1.5),  # Estimate 1.5 min per review
            average_session_minutes=25.0,  # Default estimate
            last_review_date=last_review,
            total_xp_earned=total_xp,
            xp_earned_today=0  # Would need daily tracking
        )

        return success_response(response_data.model_dump())

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting spaced repetition stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Error interno al obtener estadisticas de repaso espaciado"
            }
        )


@router.get("/due-count", response_model=None)
async def get_due_items_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtener un conteo rapido de items pendientes de revision.

    Endpoint ligero para mostrar badges o notificaciones.
    """
    try:
        service = SpacedRepetitionService(db)

        result = service.get_daily_reviews(
            user_id=str(current_user.id),
            max_reviews=1  # Only need count, not items
        )

        return success_response({
            "due_today": result.get("total_due_items", 0),
            "new_items": result.get("new_items", 0),
            "review_items": result.get("review_items", 0),
            "learning_items": result.get("learning_items", 0)
        })

    except Exception as e:
        logger.error(f"Error getting due count: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Error interno al obtener conteo de items pendientes"
            }
        )
