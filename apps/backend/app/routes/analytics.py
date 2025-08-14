from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
import tempfile
import os

from ..core.database import get_db
from ..core.security import get_current_user
from ..services.analytics_service import AnalyticsService
from ..models.user import User
from ..schemas.analytics import PersonalAnalytics

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.post("/events")
async def track_analytics_events(events: dict):
    """Stub seguro para eventos de analytics - no bloquea el FE"""
    count = len(events.get("events", [])) if isinstance(events, dict) else 0
    return {"status": "success", "events_received": count, "timestamp": datetime.utcnow().isoformat()}

def _defaults_for(username: str, user_id: str = "default") -> dict:
    """Datos por defecto para analytics personales"""
    from datetime import datetime
    
    return {
        "user_id": user_id,  # Campo requerido
        "username": username,
        "current_level": 1,
        "current_rank": "F",
        "total_experience": 0,  # Campo requerido
        
        # Progreso por materia
        "subjects_progress": [],
        
        # Proyección ICFES - todos los campos requeridos
        "icfes_projection": {
            "current_score": 0.0,
            "projected_score": 0.0,
            "improvement_rate": 0.0,  # Campo requerido
            "target_score": 0.0,      # Campo requerido
            "weeks_to_target": 0,     # Campo requerido
            "confidence_level": 0.0   # Campo requerido
        },
        
        # Comparación nacional - todos los campos requeridos
        "national_comparison": {
            "user_percentile": 0.0,      # Campo requerido
            "national_average": 0.0,     # Campo requerido
            "user_score": 0.0,           # Campo requerido
            "difference_from_average": 0.0,  # Campo requerido
            "ranking_position": 0,       # Campo requerido
            "total_students": 0          # Campo requerido
        },
        
        # Heatmap de fortalezas/debilidades - debe ser lista
        "strength_weakness_heatmap": [],
        
        # Métricas adicionales - todos los campos requeridos
        "total_battles": 0,              # Campo requerido
        "win_rate": 0.0,                 # Campo requerido
        "average_session_duration": 0,   # Campo requerido
        "streak_days": 0,                # Campo requerido
        "total_questions_answered": 0,   # Campo requerido
        "overall_accuracy": 0.0,
        
        # Tendencias temporales
        "weekly_progress": [],
        "monthly_trends": [],
        
        "generated_at": datetime.utcnow()  # Campo requerido
    }

@router.get("/personal", response_model=PersonalAnalytics)
async def get_personal_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener dashboard de analytics personales completos"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_personal_analytics(str(current_user.id))
        return analytics or _defaults_for(current_user.username, str(current_user.id))
    except HTTPException:
        raise
    except Exception as e:
        # Devuelve datos por defecto para no romper el FE
        return _defaults_for(getattr(current_user, "username", "user"), str(current_user.id))

@router.get("/personal/export-pdf")
async def export_analytics_pdf(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exportar analytics personales como PDF"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_personal_analytics(str(current_user.id))
        
        # Generar PDF con los datos
        pdf_content = _generate_analytics_pdf(analytics)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file_path = tmp_file.name
        
        return FileResponse(
            path=tmp_file_path,
            media_type='application/pdf',
            filename=f"analytics_{current_user.username}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {str(e)}")

@router.get("/subjects/{subject_id}/progress")
async def get_subject_progress(
    subject_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener progreso detallado de una materia específica"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_personal_analytics(str(current_user.id))
        
        # Encontrar progreso de la materia específica
        subject_progress = next(
            (sp for sp in analytics.subjects_progress if sp.subject_id == subject_id),
            None
        )
        
        if not subject_progress:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        return subject_progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo progreso: {str(e)}")

@router.get("/icfes-projection")
async def get_icfes_projection(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener proyección de puntaje ICFES"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_personal_analytics(str(current_user.id))
        return analytics.icfes_projection
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo proyección: {str(e)}")

@router.get("/national-comparison")
async def get_national_comparison(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener comparación con promedio nacional"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_personal_analytics(str(current_user.id))
        return analytics.national_comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo comparación: {str(e)}")

@router.get("/strength-weakness")
async def get_strength_weakness_heatmap(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener heatmap de fortalezas y debilidades"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_personal_analytics(str(current_user.id))
        return analytics.strength_weakness_heatmap
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo heatmap: {str(e)}")

@router.get("/weekly-progress")
async def get_weekly_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener progreso semanal"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_personal_analytics(str(current_user.id))
        return analytics.weekly_progress
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo progreso semanal: {str(e)}")

@router.get("/monthly-trends")
async def get_monthly_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener tendencias mensuales"""
    try:
        analytics_service = AnalyticsService(db)
        analytics = analytics_service.get_personal_analytics(str(current_user.id))
        return analytics.monthly_trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo tendencias: {str(e)}")

def _generate_analytics_pdf(analytics: PersonalAnalytics) -> bytes:
    """Generar contenido PDF de analytics (simulado)"""
    # En producción se usaría una librería como reportlab o weasyprint
    # Por ahora retornamos un PDF simple simulado
    
    pdf_content = f"""
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 500
>>
stream
BT
/F1 12 Tf
72 720 Td
(Analytics Personales - {analytics.username}) Tj
0 -20 Td
(Nivel: {analytics.current_level} - Rank: {analytics.current_rank}) Tj
0 -20 Td
(Puntaje ICFES Actual: {analytics.icfes_projection.current_score}) Tj
0 -20 Td
(Puntaje ICFES Proyectado: {analytics.icfes_projection.projected_score}) Tj
0 -20 Td
(Precisión General: {analytics.overall_accuracy}%) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000204 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF
""".encode('utf-8')
    
    return pdf_content 