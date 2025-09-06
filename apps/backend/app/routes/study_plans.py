from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..models.subject import Subject
from ..models.study_plan import StudyPlan, PlanProgress
from ..services.study_plan_service import StudyPlanService
from ..services.study_plan_integration_service import StudyPlanIntegrationService
from ..schemas.study_plan import (
    StudyPlanCreate,
    StudyPlanResponse,
    StudyPlanDetail,
    UnitProgressUpdate,
    StudyPlanList
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/study-plans", tags=["study-plans"])

class AdaptiveGeneratePayload(BaseModel):
    subject_id: str
    use_diagnostic: Optional[bool] = True

class SimpleUnitProgress(BaseModel):
    unit_number: int
    score: Optional[float] = None
    is_completed: Optional[bool] = None

class WeightedProgressPayload(BaseModel):
    unit_number: int
    component_type: str
    completed: int
    total: int
    is_completed: Optional[bool] = False

@router.post("/generate/{subject_id}", response_model=StudyPlanDetail)
async def generate_study_plan(
    subject_id: str,
    background_tasks: BackgroundTasks,
    use_diagnostic: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera un plan de estudio personalizado para una materia específica
    """
    try:
        # Verificar que la materia existe
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        # Crear servicio de planes de estudio
        study_plan_service = StudyPlanService(db)
        
        # Generar plan personalizado (inteligente si use_diagnostic=True)
        if use_diagnostic:
            personalized_plan = study_plan_service.generate_intelligent_plan_from_diagnostic(
                user_id=str(current_user.id),
                subject_id=subject_id
            )
        else:
            personalized_plan = study_plan_service.generate_personalized_plan(
                user_id=str(current_user.id),
                subject_id=subject_id,
                user_level=current_user.level
            )
        
        # Invalidate cache de planes del usuario
        background_tasks.add_task(
            lambda: study_plan_service._invalidate_user_cache(str(current_user.id))
        )
        
        return StudyPlanDetail(
            id=personalized_plan.get("id", "generated"),
            plan_name=personalized_plan["title"],
            subject=personalized_plan["subject"],
            title=personalized_plan["title"],
            description=personalized_plan["description"],
            units=personalized_plan["units"],
            total_units=len(personalized_plan["units"]),
            completed_units=0,
            progress_percentage=0.0,
            estimated_time=personalized_plan["estimated_time"],
            difficulty_curve=personalized_plan["difficulty_curve"],
            icfes_weight=personalized_plan["icfes_weight"],
            exam_sections=personalized_plan["exam_sections"],
            personalized_recommendations=personalized_plan.get("personalized_recommendations", {}),
            progress_details={
                "overall_progress": 0.0,
                "completed_units": 0,
                "unit_details": []
            },
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating study plan: {e}")
        raise HTTPException(status_code=500, detail="Error generando plan de estudio")

@router.post("/generate-ai-comprehensive", response_model=StudyPlanDetail)
async def generate_ai_comprehensive_study_plan(
    payload: AdaptiveGeneratePayload,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a complete AI-powered comprehensive study plan with all advanced features
    """
    try:
        subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        # Use the new AI-powered comprehensive service
        integration_service = StudyPlanIntegrationService(db)
        comprehensive_plan = await integration_service.generate_ai_powered_comprehensive_plan(
            user_id=str(current_user.id),
            subject_id=payload.subject_id,
            preferences={
                "use_diagnostic": payload.use_diagnostic,
                "allow_rescheduling": True,
                "max_daily_hours": 2
            }
        )

        # Save the generated plan to the database
        try:
            study_plan_service = StudyPlanService(db)
            
            # Create StudyPlan model instance
            study_plan = StudyPlan(
                user_id=current_user.id,
                subject_id=payload.subject_id,
                plan_name=comprehensive_plan["title"],
                plan_data=comprehensive_plan,
                total_units=len(comprehensive_plan["units"]),
                completed_units=0,
                progress_percentage=0.00,
                is_active=True
            )
            
            db.add(study_plan)
            db.commit()
            db.refresh(study_plan)
            
            # Update the plan ID with the database ID
            comprehensive_plan["id"] = str(study_plan.id)
            
            # Invalidate cache
            background_tasks.add_task(lambda: study_plan_service._invalidate_user_cache(str(current_user.id)))
            
        except Exception as e:
            logger.error(f"Error saving AI comprehensive study plan: {e}")
            # Continue without saving if there's an error

        # Convert to StudyPlanDetail format
        from ..schemas.study_plan import StudyUnit, StudyTopic, UnitRecommendations
        
        converted_units = []
        for unit in comprehensive_plan["units"]:
            # Convert topics to StudyTopic schema
            study_topics = []
            for topic in unit.get("topics", []):
                study_topics.append(StudyTopic(
                    name=topic.get("name", "Tema"),
                    difficulty=topic.get("difficulty", 1),
                    questions=topic.get("questions", 5),
                    tags=topic.get("tags", [])
                ))
            
            # Create UnitRecommendations from AI recommendations
            unit_recommendations = UnitRecommendations(
                priority=unit.get("ai_recommendations", {}).get("priority", "medium"),
                weak_areas=unit.get("ai_recommendations", {}).get("potential_challenges", []),
                focus_topics=unit.get("prioritized_topics", [])[:3],
                study_time=f"{unit.get('personalized_hours', 2)} horas"
            )
            
            # Create StudyUnit
            study_unit = StudyUnit(
                unit_number=unit.get("unit_number", 1),
                name=unit.get("name", "Unidad"),
                description=unit.get("description", "Descripción de la unidad"),
                topics=study_topics,
                recommendations=unit_recommendations,
                unlocked=unit.get("unlocked", True),
                progress=0.0,
                ai_recommended=unit.get("ai_recommended", True)
            )
            converted_units.append(study_unit)
        
        return StudyPlanDetail(
            id=comprehensive_plan.get("id", "generated"),
            plan_name=comprehensive_plan["title"],
            subject=comprehensive_plan["subject"],
            title=comprehensive_plan["title"],
            description=comprehensive_plan["description"],
            units=converted_units,
            total_units=len(comprehensive_plan["units"]),
            completed_units=0,
            progress_percentage=0.0,
            estimated_time=comprehensive_plan.get("estimated_completion_time", "8-12 semanas"),
            difficulty_curve=comprehensive_plan.get("difficulty_curve", "adaptive"),
            icfes_weight=comprehensive_plan.get("icfes_weight", 0.25),
            exam_sections=comprehensive_plan.get("exam_sections", []),
            personalized_recommendations={
                **comprehensive_plan.get("personalized_recommendations", {}),
                "ai_powered": True,
                "learning_style": comprehensive_plan.get("ai_powered_features", {})
                    .get("learning_style_detection", {}).get("primary_learning_style", "visual"),
                "personalization_confidence": comprehensive_plan.get("personalization_confidence", 0.8),
                "expected_outcomes": comprehensive_plan.get("expected_outcomes", {}),
                "ai_features_enabled": list(comprehensive_plan.get("system_capabilities", {}).keys())
            },
            progress_details={
                "overall_progress": 0.0,
                "completed_units": 0,
                "unit_details": [],
                "ai_insights": comprehensive_plan.get("ai_powered_features", {}),
                "adaptive_system_active": True
            },
            last_updated=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error generating AI comprehensive plan: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando plan AI completo: {str(e)}")

@router.post("/generate-adaptive", response_model=StudyPlanDetail)
async def generate_study_plan_adaptive(
    payload: AdaptiveGeneratePayload,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generar plan de estudio adaptativo integrando catálogo ICFES y diagnóstico
    """
    try:
        subject = db.query(Subject).filter(Subject.id == payload.subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Materia no encontrada")

        # Usar el nuevo servicio de integración
        integration_service = StudyPlanIntegrationService(db)
        personalized_plan = integration_service.generate_comprehensive_study_plan(
            user_id=str(current_user.id),
            subject_id=payload.subject_id,
            use_diagnostic=payload.use_diagnostic
        )

        # Save the generated plan to the database
        try:
            study_plan_service = StudyPlanService(db)
            
            # Create StudyPlan model instance
            from ..models.study_plan import StudyPlan
            study_plan = StudyPlan(
                user_id=current_user.id,
                subject_id=payload.subject_id,
                plan_name=personalized_plan["title"],
                plan_data=personalized_plan,
                total_units=len(personalized_plan["units"]),
                completed_units=0,
                progress_percentage=0.00,
                is_active=True
            )
            
            db.add(study_plan)
            db.commit()
            db.refresh(study_plan)
            
            # Update the plan ID with the database ID
            personalized_plan["id"] = str(study_plan.id)
            
            # Invalidate cache
            background_tasks.add_task(lambda: study_plan_service._invalidate_user_cache(str(current_user.id)))
            
        except Exception as e:
            logger.error(f"Error saving study plan: {e}")
            # Continue without saving if there's an error

        # Convert catalog units to StudyUnit schema
        from ..schemas.study_plan import StudyUnit, StudyTopic, UnitRecommendations
        
        converted_units = []
        for unit in personalized_plan["units"]:
            # Convert topics to StudyTopic schema
            study_topics = []
            for topic in unit.get("topics", []):
                study_topics.append(StudyTopic(
                    name=topic.get("main_topic", "Tema"),
                    difficulty=topic.get("difficulty", 1),
                    questions=5,  # Default 5 questions per topic
                    tags=[topic.get("code", ""), topic.get("main_topic", "")]
                ))
            
            # Create UnitRecommendations
            unit_recommendations = UnitRecommendations(
                priority=unit.get("recommendations", {}).get("priority", "medium"),
                weak_areas=unit.get("recommendations", {}).get("weak_areas", []),
                focus_topics=unit.get("recommendations", {}).get("focus_topics", []),
                study_time=unit.get("recommendations", {}).get("study_time", "2 horas")
            )
            
            # Create StudyUnit
            study_unit = StudyUnit(
                unit_number=unit.get("unit_number", 1),
                name=unit.get("name", "Unidad"),
                description=unit.get("description", "Descripción de la unidad"),
                topics=study_topics,
                recommendations=unit_recommendations,
                unlocked=unit.get("unlocked", True),
                progress=0.0,  # Initial progress
                ai_recommended=unit.get("ai_recommended", False)
            )
            converted_units.append(study_unit)
        
        return StudyPlanDetail(
            id=personalized_plan.get("id", "generated"),
            plan_name=personalized_plan["title"],
            subject=personalized_plan["subject"],
            title=personalized_plan["title"],
            description=personalized_plan["description"],
            units=converted_units,
            total_units=len(personalized_plan["units"]),
            completed_units=0,
            progress_percentage=0.0,
            estimated_time=personalized_plan["estimated_time"],
            difficulty_curve=personalized_plan["difficulty_curve"],
            icfes_weight=personalized_plan["icfes_weight"],
            exam_sections=personalized_plan["exam_sections"],
            personalized_recommendations=personalized_plan.get("personalized_recommendations", {}),
            progress_details={
                "overall_progress": 0.0,
                "completed_units": 0,
                "unit_details": []
            },
            last_updated=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Error generating adaptive plan: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando plan de estudio: {str(e)}")

@router.get("/", response_model=StudyPlanList)
async def get_user_study_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los planes de estudio del usuario
    """
    try:
        study_plan_service = StudyPlanService(db)
        plans = study_plan_service.get_user_study_plans(str(current_user.id))
        
        return StudyPlanList(
            plans=plans,
            total_plans=len(plans),
            active_plans=len([p for p in plans if p.get("progress_percentage", 0) < 100])
        )
        
    except Exception as e:
        logger.error(f"Error getting user study plans: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo planes de estudio")

@router.get("/{plan_id}", response_model=StudyPlanDetail)
async def get_study_plan_detail(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene detalles completos de un plan de estudio específico
    """
    try:
        study_plan_service = StudyPlanService(db)
        plans = study_plan_service.get_user_study_plans(str(current_user.id))
        
        # Buscar el plan específico
        plan = next((p for p in plans if p["id"] == plan_id), None)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")
        
        return StudyPlanDetail(**plan)
        
    except Exception as e:
        logger.error(f"Error getting study plan detail: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo detalles del plan")

@router.get("/plans/{plan_id}", response_model=StudyPlanDetail)
async def get_study_plan_detail_alias(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias: /study-plans/plans/{plan_id}"""
    return await get_study_plan_detail(plan_id, current_user, db)  # type: ignore

@router.post("/{plan_id}/units/{unit_number}/progress")
async def update_unit_progress(
    plan_id: str,
    unit_number: int,
    progress_update: UnitProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el progreso de una unidad específica
    """
    try:
        study_plan_service = StudyPlanService(db)
        
        # Verificar que el plan pertenece al usuario
        plans = study_plan_service.get_user_study_plans(str(current_user.id))
        plan = next((p for p in plans if p["id"] == plan_id), None)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")
        
        # Actualizar progreso
        updated_progress = study_plan_service.update_unit_progress(
            plan_id=plan_id,
            unit_number=unit_number,
            progress_data=progress_update.dict()
        )
        
        return {
            "message": "Progreso actualizado exitosamente",
            "unit_number": unit_number,
            "progress_percentage": updated_progress["progress_percentage"],
            "is_completed": updated_progress["is_completed"]
        }
        
    except Exception as e:
        logger.error(f"Error updating unit progress: {e}")
        raise HTTPException(status_code=500, detail="Error actualizando progreso")

@router.post("/plans/{plan_id}/progress")
async def update_unit_progress_alias(
    plan_id: str,
    payload: SimpleUnitProgress,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias: /study-plans/plans/{plan_id}/progress"""
    try:
        study_plan_service = StudyPlanService(db)
        plans = study_plan_service.get_user_study_plans(str(current_user.id))
        plan = next((p for p in plans if p["id"] == plan_id), None)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")

        _ = study_plan_service.update_unit_progress(
            plan_id=plan_id,
            unit_number=payload.unit_number,
            progress_data={"score": payload.score}
        )

        return {"message": "Progreso actualizado exitosamente"}
    except Exception as e:
        logger.error(f"Error updating unit progress (alias): {e}")
        raise HTTPException(status_code=500, detail="Error actualizando progreso")

@router.post("/plans/{plan_id}/weighted-progress")
async def update_weighted_progress(
    plan_id: str,
    payload: WeightedProgressPayload,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias: /study-plans/plans/{plan_id}/weighted-progress"""
    try:
        plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id, StudyPlan.user_id == current_user.id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")

        unit_progress = db.query(PlanProgress).filter(
            PlanProgress.plan_id == plan_id,
            PlanProgress.unit_number == payload.unit_number
        ).first()
        if not unit_progress:
            unit_progress = PlanProgress(
                plan_id=plan_id,
                unit_number=payload.unit_number,
                unit_name=f"Unidad {payload.unit_number}",
                unit_description="",
                unit_content={},
                is_completed=False,
                score=0.0,
                weighted_progress={
                    "videos": {"completed": 0, "total": 1, "weight": 0.3},
                    "exercises": {"completed": 0, "total": 1, "weight": 0.5},
                    "readings": {"completed": 0, "total": 1, "weight": 0.2}
                }
            )
            db.add(unit_progress)

        comp = unit_progress.weighted_progress.get(payload.component_type, {"completed": 0, "total": 0, "weight": 0})
        comp["completed"] = payload.completed
        comp["total"] = max(payload.total, 1)
        unit_progress.weighted_progress[payload.component_type] = comp
        db.commit()

        return {"message": "Progreso ponderado actualizado"}
    except Exception as e:
        logger.error(f"Error updating weighted progress: {e}")
        raise HTTPException(status_code=500, detail="Error actualizando progreso ponderado")

@router.get("/recommendations/{subject_id}")
async def get_study_recommendations(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene recomendaciones de estudio para una materia específica
    """
    try:
        study_plan_service = StudyPlanService(db)
        
        # Analizar rendimiento del usuario
        user_data = study_plan_service._analyze_user_performance(
            str(current_user.id), 
            subject_id
        )
        
        # Generar recomendaciones
        recommendations = {
            "subject_id": subject_id,
            "user_level": current_user.level,
            "performance_analysis": user_data,
            "suggested_focus": study_plan_service._get_suggested_focus(user_data),
            "study_schedule": study_plan_service._generate_study_schedule(user_data, current_user.level),
            "improvement_estimate": study_plan_service._estimate_improvement(user_data),
            "next_steps": [
                "Completar test diagnóstico si no lo has hecho",
                "Enfócate en los temas débiles identificados",
                "Mantén una racha de estudio diario",
                "Revisa las explicaciones de las preguntas incorrectas"
            ]
        }
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting study recommendations: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo recomendaciones")

@router.post("/{plan_id}/complete")
async def complete_study_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Marca un plan de estudio como completado
    """
    try:
        study_plan_service = StudyPlanService(db)
        
        # Verificar que el plan pertenece al usuario
        plans = study_plan_service.get_user_study_plans(str(current_user.id))
        plan = next((p for p in plans if p["id"] == plan_id), None)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")
        
        # Verificar que todas las unidades están completadas
        if plan["progress_details"]["completed_units"] < plan["total_units"]:
            raise HTTPException(
                status_code=400, 
                detail="No puedes completar el plan hasta terminar todas las unidades"
            )
        
        # Marcar como completado
        study_plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id).first()
        if study_plan:
            study_plan.progress_percentage = 100.00
            study_plan.completed_units = plan["total_units"]
            db.commit()
        
        return {
            "message": "¡Plan de estudio completado!",
            "plan_id": plan_id,
            "completion_date": datetime.now().isoformat(),
            "rewards": {
                "experience": 500,
                "orbs": 100,
                "crystals": 10
            }
        }
        
    except Exception as e:
        logger.error(f"Error completing study plan: {e}")
        raise HTTPException(status_code=500, detail="Error completando plan de estudio")

@router.delete("/{plan_id}")
async def delete_study_plan(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Elimina un plan de estudio (marca como inactivo)
    """
    try:
        # Verificar que el plan pertenece al usuario
        study_plan = db.query(StudyPlan).filter(
            StudyPlan.id == plan_id,
            StudyPlan.user_id == current_user.id
        ).first()
        
        if not study_plan:
            raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")
        
        # Marcar como inactivo
        study_plan.is_active = False
        db.commit()
        
        return {"message": "Plan de estudio eliminado exitosamente"}
        
    except Exception as e:
        logger.error(f"Error deleting study plan: {e}")
        raise HTTPException(status_code=500, detail="Error eliminando plan de estudio")

@router.get("/{plan_id}/adaptive", response_model=StudyPlanDetail)
async def get_adaptive_plan_alias(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias para compatibilidad con FE: GET /study-plans/{plan_id}/adaptive"""
    return await get_study_plan_detail(plan_id, current_user, db)  # type: ignore

@router.get("/plans/{plan_id}/statistics")
async def get_plan_statistics_alias(
    plan_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias: /study-plans/plans/{plan_id}/statistics"""
    try:
        plan = db.query(StudyPlan).filter(StudyPlan.id == plan_id, StudyPlan.user_id == current_user.id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="Plan de estudio no encontrado")

        unit_progresses = db.query(PlanProgress).filter(PlanProgress.plan_id == plan_id).all()
        total_units = len(unit_progresses)
        completed_units = sum(1 for up in unit_progresses if up.is_completed)
        average_score = sum(float(up.score) for up in unit_progresses) / total_units if total_units else 0
        time_spent_minutes = sum(int(up.unit_content.get("time_spent_minutes", 0)) for up in unit_progresses)

        return {
            "plan_id": plan_id,
            "total_units": total_units,
            "completed_units": completed_units,
            "progress_percentage": float(plan.progress_percentage),
            "average_score": average_score,
            "time_spent_minutes": time_spent_minutes,
            "units_by_difficulty": {},
            "completion_rate": (completed_units / total_units * 100) if total_units else 0,
            "estimated_completion_date": None,
            "improvement_trend": []
        }
    except Exception as e:
        logger.error(f"Error getting plan statistics: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas del plan")

@router.get("/real-time-progress")
async def get_real_time_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Alias: /study-plans/real-time-progress"""
    try:
        active_plans = db.query(StudyPlan).filter(StudyPlan.user_id == current_user.id, StudyPlan.is_active == True).all()
        total_completed_units = sum(p.completed_units for p in active_plans)
        current_rank = getattr(current_user, "rank", "E")
        return {"totalOrbs": getattr(current_user, "orbs", 0), "currentRank": current_rank, "completedUnits": total_completed_units}
    except Exception as e:
        logger.error(f"Error getting real-time progress: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo progreso en tiempo real")

@router.get("/subjects/available")
async def get_available_subjects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene las materias disponibles para generar planes de estudio
    """
    try:
        subjects = db.query(Subject).all()
        
        # Verificar qué materias ya tienen planes activos
        study_plan_service = StudyPlanService(db)
        existing_plans = study_plan_service.get_user_study_plans(str(current_user.id))
        existing_subject_ids = [plan["subject_id"] for plan in existing_plans]
        
        available_subjects = []
        for subject in subjects:
            has_plan = str(subject.id) in existing_subject_ids
            available_subjects.append({
                "id": str(subject.id),
                "name": subject.name,
                "description": subject.description,
                "icon_url": subject.icon_url,
                "color": subject.color,
                "has_active_plan": has_plan,
                "icfes_weight": _get_icfes_weight(subject.name)
            })
        
        return {
            "subjects": available_subjects,
            "total_subjects": len(subjects),
            "subjects_with_plans": len(existing_subject_ids)
        }
        
    except Exception as e:
        logger.error(f"Error getting available subjects: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo materias disponibles")

def _get_icfes_weight(subject_name: str) -> float:
    """
    Obtiene el peso de la materia en el examen ICFES
    """
    weights = {
        "Matemáticas": 0.25,
        "Lenguaje": 0.25,
        "Ciencias Naturales": 0.20,
        "Ciencias Sociales": 0.15,
        "Inglés": 0.15
    }
    return weights.get(subject_name, 0.0) 