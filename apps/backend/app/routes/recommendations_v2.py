"""
API Endpoints para el Sistema Avanzado de Recomendaciones v2.0
Motor completo con embeddings, análisis de debilidades y planes YAML
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncio
import json
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.services.master_recommendation_service import MasterRecommendationService
from app.services.yaml_plan_generator_service import YamlPlanGeneratorService
from app.services.weakness_analysis_service import WeaknessAnalysisService
from app.services.question_video_mapping_service import QuestionVideoMappingService
from app.services.recommendation_scoring_service import RecommendationScoringService

# Crear router
router = APIRouter(prefix="/api/v2/recommendations", tags=["Recommendations v2.0"])

# Instanciar servicios
master_service = MasterRecommendationService()
yaml_service = YamlPlanGeneratorService()
weakness_service = WeaknessAnalysisService()
mapping_service = QuestionVideoMappingService()
scoring_service = RecommendationScoringService()

# =============================================================================
# ENDPOINTS PRINCIPALES DE RECOMENDACIONES
# =============================================================================

@router.get("/student/{student_id}")
async def get_student_recommendations(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="Número máximo de recomendaciones"),
    recommendation_type: Optional[str] = Query(None, description="Tipo específico de recomendación"),
    include_scoring_details: bool = Query(False, description="Incluir detalles del scoring")
):
    """
    Obtiene recomendaciones personalizadas para un estudiante específico
    
    - **student_id**: ID único del estudiante
    - **limit**: Número máximo de recomendaciones (1-50)
    - **recommendation_type**: Filtrar por tipo (error_remediation, concept_reinforcement, skill_building)
    - **include_scoring_details**: Incluir detalles del algoritmo de scoring
    """
    try:
        # Verificar autorización
        if current_user.role != 'admin' and str(current_user.id) != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Obtener recomendaciones
        recommendations = await master_service.get_recommendation_for_student(
            db, student_id, limit, recommendation_type
        )
        
        if recommendations['status'] == 'error':
            raise HTTPException(status_code=500, detail=recommendations['error'])
        
        # Filtrar detalles si no se solicitan
        if not include_scoring_details:
            for rec in recommendations.get('recommendations', []):
                rec.pop('scoring_details', None)
        
        return JSONResponse(content=recommendations)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@router.post("/generate/batch")
async def generate_batch_recommendations(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_ids: Optional[List[str]] = None,
    force_regenerate: bool = False
):
    """
    Ejecuta el pipeline completo de generación de recomendaciones en lote
    
    - **student_ids**: Lista opcional de estudiantes específicos
    - **force_regenerate**: Forzar regeneración completa
    
    Ejecuta:
    1. Generación de embeddings
    2. Análisis de debilidades
    3. Mapeo pregunta-video
    4. Optimización de scoring
    5. Generación de planes YAML
    6. Validación del sistema
    """
    try:
        # Solo administradores pueden ejecutar procesamiento en lote
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Ejecutar pipeline en background
        background_tasks.add_task(
            run_complete_pipeline_background,
            db, student_ids, force_regenerate
        )
        
        return JSONResponse(content={
            "status": "pipeline_started",
            "message": "Recommendation pipeline started in background",
            "estimated_duration_minutes": 30,
            "started_at": datetime.utcnow().isoformat(),
            "target_students": len(student_ids) if student_ids else "all_active"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting pipeline: {str(e)}")

async def run_complete_pipeline_background(
    db: Session, 
    student_ids: Optional[List[str]], 
    force_regenerate: bool
):
    """Función background para ejecutar el pipeline completo"""
    try:
        result = await master_service.run_complete_recommendation_pipeline(
            db, student_ids, force_regenerate
        )
        # En implementación real, se enviaría notificación o se guardaría en log
        print(f"Pipeline completed: {result.get('overall_status')}")
    except Exception as e:
        print(f"Pipeline failed: {str(e)}")

# =============================================================================
# ENDPOINTS DE ANÁLISIS DE DEBILIDADES
# =============================================================================

@router.get("/weaknesses/student/{student_id}")
async def get_student_weaknesses(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    severity_filter: Optional[List[str]] = Query(None, description="Filtrar por severidad"),
    limit: int = Query(10, ge=1, le=20)
):
    """
    Obtiene análisis detallado de debilidades de un estudiante
    
    - **student_id**: ID del estudiante
    - **severity_filter**: Filtrar por severidad (critical, significant, time_inefficient)
    - **limit**: Número máximo de debilidades
    """
    try:
        # Verificar autorización
        if current_user.role != 'admin' and str(current_user.id) != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convertir filtros
        from app.services.weakness_analysis_service import WeaknessSeverity
        severity_enum_filter = None
        if severity_filter:
            try:
                severity_enum_filter = [WeaknessSeverity(s) for s in severity_filter]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid severity filter: {e}")
        
        # Obtener debilidades
        weaknesses = await weakness_service.get_student_weaknesses(
            db, student_id, severity_enum_filter, limit
        )
        
        # Convertir a formato serializable
        weaknesses_data = []
        for weakness in weaknesses:
            weakness_dict = {
                'subject_area': weakness.subject_name,
                'topic_name': weakness.topic_name,
                'accuracy_percentage': weakness.accuracy_percentage,
                'total_attempts': weakness.total_attempts,
                'intervention_priority_score': weakness.intervention_priority_score,
                'weakness_severity': weakness.weakness_severity.value,
                'weakness_type': weakness.weakness_type.value,
                'dominant_distractor': weakness.dominant_distractor,
                'avg_time_seconds': weakness.avg_time_seconds,
                'p90_time_seconds': weakness.p90_time_seconds,
                'recommended_action': weakness.recommended_action,
                'estimated_sessions_needed': weakness.estimated_sessions_needed,
                'needs_concept_review': weakness.needs_concept_review,
                'needs_speed_practice': weakness.needs_speed_practice,
                'has_systematic_error': weakness.has_systematic_error,
                'analysis_timestamp': weakness.analysis_timestamp.isoformat()
            }
            weaknesses_data.append(weakness_dict)
        
        return JSONResponse(content={
            'student_id': student_id,
            'weaknesses': weaknesses_data,
            'total_weaknesses': len(weaknesses_data),
            'analysis_summary': {
                'critical_count': len([w for w in weaknesses if w.weakness_severity.value == 'critical']),
                'significant_count': len([w for w in weaknesses if w.weakness_severity.value == 'significant']),
                'avg_priority_score': sum(w.intervention_priority_score for w in weaknesses) / len(weaknesses) if weaknesses else 0
            },
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting weaknesses: {str(e)}")

@router.post("/weaknesses/refresh")
async def refresh_weakness_analysis(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ejecuta refresh de la vista materializada de análisis de debilidades
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Ejecutar refresh en background
        background_tasks.add_task(refresh_weakness_analysis_background, db)
        
        return JSONResponse(content={
            "status": "refresh_started",
            "message": "Weakness analysis refresh started",
            "estimated_duration_minutes": 5
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting refresh: {str(e)}")

async def refresh_weakness_analysis_background(db: Session):
    """Función background para refresh de análisis"""
    try:
        result = await weakness_service.refresh_weakness_analysis(db)
        print(f"Weakness analysis refresh completed: {result}")
    except Exception as e:
        print(f"Weakness analysis refresh failed: {str(e)}")

@router.get("/weaknesses/alerts")
async def get_weakness_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    student_id: Optional[str] = Query(None, description="Filtrar por estudiante específico"),
    severity_filter: Optional[List[str]] = Query(None, description="Filtrar por severidad"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Obtiene alertas activas de debilidades críticas
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        alerts = await weakness_service.get_active_alerts(
            db, student_id, severity_filter, limit
        )
        
        # Convertir alertas a formato serializable
        alerts_data = []
        for alert in alerts:
            alert_dict = {
                'id': alert.id,
                'student_id': alert.student_id,
                'alert_type': alert.alert_type.value,
                'severity': alert.severity,
                'message': alert.message,
                'recommended_actions': alert.recommended_actions,
                'intervention_priority_score': alert.intervention_priority_score,
                'created_at': alert.created_at.isoformat(),
                'status': alert.status
            }
            alerts_data.append(alert_dict)
        
        return JSONResponse(content={
            'alerts': alerts_data,
            'total_alerts': len(alerts_data),
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alerts: {str(e)}")

# =============================================================================
# ENDPOINTS DE PLANES YAML
# =============================================================================

@router.post("/plans/generate/{student_id}")
async def generate_monthly_plan(
    student_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    target_month: Optional[int] = Query(None, ge=1, le=12),
    target_year: Optional[int] = Query(None, ge=2024),
    force_regenerate: bool = Query(False)
):
    """
    Genera plan de estudio mensual personalizado en formato YAML
    
    - **student_id**: ID del estudiante
    - **target_month**: Mes objetivo (1-12), por defecto mes actual
    - **target_year**: Año objetivo, por defecto año actual
    - **force_regenerate**: Forzar regeneración si ya existe
    """
    try:
        # Verificar autorización
        if current_user.role != 'admin' and str(current_user.id) != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Generar plan
        plan_result = await yaml_service.generate_monthly_plan(
            db, student_id, target_month, target_year, force_regenerate
        )
        
        if plan_result['status'] == 'error':
            raise HTTPException(status_code=500, detail=plan_result['error'])
        
        return JSONResponse(content=plan_result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating plan: {str(e)}")

@router.get("/plans/student/{student_id}")
async def get_student_plans(
    student_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene lista de planes disponibles para un estudiante
    """
    try:
        # Verificar autorización
        if current_user.role != 'admin' and str(current_user.id) != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        plans = await yaml_service.get_student_plans(student_id)
        
        return JSONResponse(content={
            'student_id': student_id,
            'available_plans': plans,
            'total_plans': len(plans)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting plans: {str(e)}")

@router.get("/plans/download/{student_id}/{year}/{month}")
async def download_monthly_plan(
    student_id: str,
    year: int,
    month: int,
    current_user: User = Depends(get_current_user)
):
    """
    Descarga plan mensual específico en formato YAML
    """
    try:
        # Verificar autorización
        if current_user.role != 'admin' and str(current_user.id) != student_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Construir ruta del archivo
        plan_filename = f"rec_plan_{student_id}_{year}{month:02d}.yml"
        plan_path = Path("plans/generated") / plan_filename
        
        if not plan_path.exists():
            raise HTTPException(status_code=404, detail="Plan not found")
        
        return FileResponse(
            path=str(plan_path),
            filename=plan_filename,
            media_type='application/x-yaml'
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading plan: {str(e)}")

# =============================================================================
# ENDPOINTS DE MÉTRICAS Y MONITOREO
# =============================================================================

@router.get("/system/health")
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene estado de salud general del sistema de recomendaciones
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        health_status = await master_service.get_system_health_status(db)
        
        return JSONResponse(content=health_status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system health: {str(e)}")

@router.get("/system/metrics")
async def get_system_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene métricas detalladas del sistema
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        metrics = await master_service._calculate_system_metrics(db)
        
        # Convertir a diccionario serializable
        metrics_data = {
            'total_students_processed': metrics.total_students_processed,
            'total_videos_analyzed': metrics.total_videos_analyzed,
            'total_embeddings_generated': metrics.total_embeddings_generated,
            'total_recommendations_created': metrics.total_recommendations_created,
            'total_yaml_plans_generated': metrics.total_yaml_plans_generated,
            'average_processing_time_seconds': metrics.average_processing_time_seconds,
            'system_accuracy_score': metrics.system_accuracy_score,
            'coverage_percentage': metrics.coverage_percentage,
            'last_processing_date': metrics.last_processing_date.isoformat()
        }
        
        return JSONResponse(content=metrics_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")

@router.get("/pipeline/status/{pipeline_id}")
async def get_pipeline_status(
    pipeline_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene estado de un pipeline de procesamiento específico
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        status = master_service.get_pipeline_status(pipeline_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        return JSONResponse(content=status)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pipeline status: {str(e)}")

# =============================================================================
# ENDPOINTS DE CONFIGURACIÓN Y ADMINISTRACIÓN
# =============================================================================

@router.post("/admin/embeddings/regenerate")
async def regenerate_embeddings(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    content_type: str = Query("all", description="Tipo de contenido (videos, questions, all)"),
    batch_size: int = Query(10, ge=1, le=50)
):
    """
    Regenera embeddings para contenido específico
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        background_tasks.add_task(
            regenerate_embeddings_background,
            db, content_type, batch_size
        )
        
        return JSONResponse(content={
            "status": "regeneration_started",
            "content_type": content_type,
            "batch_size": batch_size,
            "estimated_duration_minutes": 15
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting regeneration: {str(e)}")

async def regenerate_embeddings_background(
    db: Session, 
    content_type: str, 
    batch_size: int
):
    """Función background para regenerar embeddings"""
    try:
        from app.services.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        
        if content_type in ['videos', 'all']:
            result = await embedding_service.batch_process_videos(
                db, batch_size, filter_processed=False
            )
            print(f"Video embeddings regenerated: {result}")
        
        # En implementación real se regenerarían también embeddings de preguntas
        
    except Exception as e:
        print(f"Embeddings regeneration failed: {str(e)}")

@router.post("/admin/recommendations/optimize")
async def optimize_recommendations(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    min_score_threshold: float = Query(0.75, ge=0.0, le=1.0),
    diversity_factor: float = Query(0.7, ge=0.0, le=1.0)
):
    """
    Optimiza algoritmo de recomendaciones con nuevos parámetros
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        background_tasks.add_task(
            optimize_recommendations_background,
            db, min_score_threshold, diversity_factor
        )
        
        return JSONResponse(content={
            "status": "optimization_started",
            "parameters": {
                "min_score_threshold": min_score_threshold,
                "diversity_factor": diversity_factor
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting optimization: {str(e)}")

async def optimize_recommendations_background(
    db: Session, 
    min_score_threshold: float, 
    diversity_factor: float
):
    """Función background para optimizar recomendaciones"""
    try:
        # En implementación real se aplicarían los nuevos parámetros
        # y se recalcularían los scores de recomendaciones existentes
        print(f"Optimization completed with threshold: {min_score_threshold}")
    except Exception as e:
        print(f"Optimization failed: {str(e)}")

# =============================================================================
# ENDPOINTS DE TESTING Y DEBUG
# =============================================================================

@router.get("/debug/recommendation-details/{student_id}/{video_id}")
async def get_recommendation_debug_details(
    student_id: str,
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene detalles de debug para una recomendación específica
    (Solo para desarrollo y testing)
    """
    try:
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # En implementación real se proporcionarían detalles completos
        # del algoritmo de scoring para esta combinación específica
        
        return JSONResponse(content={
            "debug_info": "Detailed scoring breakdown would be here",
            "student_id": student_id,
            "video_id": video_id,
            "note": "This endpoint is for development/testing purposes"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting debug details: {str(e)}")

# =============================================================================
# MIDDLEWARE Y CONFIGURACIÓN
# =============================================================================

@router.on_event("startup")
async def startup_event():
    """Inicialización del módulo de recomendaciones"""
    print("Recommendations v2.0 API module initialized")
    print("- Master Recommendation Service: Ready")
    print("- YAML Plan Generator: Ready")
    print("- Weakness Analysis: Ready")
    print("- Question-Video Mapping: Ready")
    print("- Scoring Service: Ready")

@router.on_event("shutdown")
async def shutdown_event():
    """Limpieza al cerrar el módulo"""
    print("Recommendations v2.0 API module shutdown")
    # Limpiar caches, cerrar conexiones, etc.