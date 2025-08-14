"""
Endpoints para el sistema de recomendaciones ICFES
WHY: Expone la funcionalidad del motor de recomendaciones al frontend
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import logging
from sqlalchemy import func

from ...core.database import get_db
from ...core.security import get_current_user
from ...models.user import User
from ...services.icfes.icfes_recommendation_service import ICFESRecommendationService
from ...models.icfes.study_topics_catalog import StudyTopicsCatalog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/icfes", tags=["icfes-recommendations"])

@router.post("/generate-study-path")
async def generate_study_path(
    target_date: str,
    target_score: int = Query(350, ge=200, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera un plan de estudio personalizado basado en los 337 temas ICFES
    
    WHY: Punto de entrada principal para crear rutas de estudio adaptativas
    """
    try:
        # Parsear fecha objetivo
        try:
            target_date_obj = datetime.fromisoformat(target_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Formato de fecha inválido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SS)"
            )
        
        # Verificar que la fecha sea futura
        if target_date_obj <= datetime.now():
            raise HTTPException(
                status_code=400,
                detail="La fecha objetivo debe ser futura"
            )
        
        service = ICFESRecommendationService(db)
        
        study_path = service.generate_personalized_study_path(
            user_id=str(current_user.id),
            target_date=target_date_obj,
            target_score=target_score
        )
        
        # Guardar plan en la base de datos (opcional)
        # from ...models.study_plan import StudyPlan
        # study_plan = StudyPlan(...)
        # db.add(study_plan)
        # db.commit()
        
        return {
            "success": True,
            "message": "Plan de estudio generado exitosamente",
            "data": study_path
        }
        
    except Exception as e:
        logger.error(f"Error generando plan de estudio: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error generando plan de estudio personalizado"
        )

@router.get("/topics-catalog")
async def get_topics_catalog(
    area: Optional[str] = Query(None, description="Filtrar por área"),
    competencia: Optional[str] = Query(None, description="Filtrar por competencia"),
    limit: int = Query(50, le=337),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Obtiene el catálogo de temas ICFES con filtros
    
    WHY: Permite explorar los 337 temas disponibles para estudio
    """
    try:
        query = db.query(StudyTopicsCatalog).filter(
            StudyTopicsCatalog.estado == 'activo'
        )
        
        if area:
            query = query.filter(StudyTopicsCatalog.area_evaluada == area)
        
        if competencia:
            query = query.filter(StudyTopicsCatalog.competencia_icfes.contains(competencia))
        
        # Ordenar por importancia y orden secuencial
        query = query.order_by(
            StudyTopicsCatalog.importancia_icfes.desc(),
            StudyTopicsCatalog.orden_secuencial
        )
        
        total = query.count()
        topics = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
            "limit": limit,
            "offset": offset,
            "topics": [
                {
                    "codigo": t.codigo_tema,
                    "area": t.area_evaluada,
                    "tema": t.tema_principal,
                    "subtema": t.subtema,
                    "competencia": t.competencia_icfes,
                    "componente": t.componente,
                    "dificultad": t.nivel_dificultad,
                    "importancia": t.importancia_icfes,
                    "horas_estudio": t.calculate_study_hours(),
                    "prerequisitos": t.prerequisitos or [],
                    "temas_relacionados": t.temas_relacionados or [],
                    "recursos_teoria": t.recursos_teoria or [],
                    "recursos_practica": t.recursos_practica or [],
                    "umbral_dominio": t.umbral_dominio,
                    "estilo_aprendizaje": t.estilo_aprendizaje_optimo,
                    "metodologia": t.metodologia_recomendada
                }
                for t in topics
            ]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo catálogo: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo catálogo de temas"
        )

@router.get("/topics/{codigo_tema}")
async def get_topic_detail(
    codigo_tema: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene detalles completos de un tema específico
    
    WHY: Información detallada para estudio individual
    """
    try:
        topic = db.query(StudyTopicsCatalog).filter(
            StudyTopicsCatalog.codigo_tema == codigo_tema,
            StudyTopicsCatalog.estado == 'activo'
        ).first()
        
        if not topic:
            raise HTTPException(
                status_code=404,
                detail=f"Tema {codigo_tema} no encontrado"
            )
        
        return {
            "success": True,
            "topic": topic.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo tema {codigo_tema}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo detalles del tema"
        )

@router.get("/areas")
async def get_areas_summary(db: Session = Depends(get_db)):
    """
    Obtiene resumen de áreas evaluadas y distribución de temas
    
    WHY: Vista general del sistema ICFES
    """
    try:
        # Contar temas por área
        areas_query = db.query(
            StudyTopicsCatalog.area_evaluada,
            func.count(StudyTopicsCatalog.id).label('total_topics'),
            func.avg(StudyTopicsCatalog.nivel_dificultad).label('avg_difficulty'),
            func.avg(StudyTopicsCatalog.importancia_icfes).label('avg_importance')
        ).filter(
            StudyTopicsCatalog.estado == 'activo'
        ).group_by(
            StudyTopicsCatalog.area_evaluada
        ).order_by(
            func.count(StudyTopicsCatalog.id).desc()
        )
        
        areas_data = areas_query.all()
        
        # Calcular estadísticas generales
        total_topics = sum(area.total_topics for area in areas_data)
        
        return {
            "success": True,
            "total_topics": total_topics,
            "areas": [
                {
                    "area": area.area_evaluada,
                    "total_topics": area.total_topics,
                    "percentage": round((area.total_topics / total_topics) * 100, 1),
                    "avg_difficulty": round(area.avg_difficulty or 0, 1),
                    "avg_importance": round(area.avg_importance or 0, 1)
                }
                for area in areas_data
            ]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo resumen de áreas: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo resumen de áreas"
        )

@router.get("/competencies")
async def get_competencies_summary(
    area: Optional[str] = Query(None, description="Filtrar por área"),
    db: Session = Depends(get_db)
):
    """
    Obtiene resumen de competencias por área
    
    WHY: Análisis de competencias para diagnóstico
    """
    try:
        query = db.query(
            StudyTopicsCatalog.area_evaluada,
            StudyTopicsCatalog.competencia_icfes,
            func.count(StudyTopicsCatalog.id).label('total_topics')
        ).filter(
            StudyTopicsCatalog.estado == 'activo'
        )
        
        if area:
            query = query.filter(StudyTopicsCatalog.area_evaluada == area)
        
        competencies = query.group_by(
            StudyTopicsCatalog.area_evaluada,
            StudyTopicsCatalog.competencia_icfes
        ).order_by(
            StudyTopicsCatalog.area_evaluada,
            func.count(StudyTopicsCatalog.id).desc()
        ).all()
        
        # Agrupar por área
        areas_competencies = {}
        for comp in competencies:
            area_name = comp.area_evaluada
            if area_name not in areas_competencies:
                areas_competencies[area_name] = []
            
            areas_competencies[area_name].append({
                "competencia": comp.competencia_icfes,
                "total_topics": comp.total_topics
            })
        
        return {
            "success": True,
            "competencies_by_area": areas_competencies
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo competencias: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo competencias"
        )

@router.get("/learning-path/{codigo_tema}")
async def get_learning_path(
    codigo_tema: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene la ruta de aprendizaje para un tema específico
    
    WHY: Muestra prerequisitos y temas relacionados
    """
    try:
        topic = db.query(StudyTopicsCatalog).filter(
            StudyTopicsCatalog.codigo_tema == codigo_tema,
            StudyTopicsCatalog.estado == 'activo'
        ).first()
        
        if not topic:
            raise HTTPException(
                status_code=404,
                detail=f"Tema {codigo_tema} no encontrado"
            )
        
        # Obtener detalles de prerequisitos
        prerequisitos_details = []
        if topic.prerequisitos:
            prereq_topics = db.query(StudyTopicsCatalog).filter(
                StudyTopicsCatalog.codigo_tema.in_(topic.prerequisitos),
                StudyTopicsCatalog.estado == 'activo'
            ).all()
            
            prerequisitos_details = [
                {
                    "codigo": p.codigo_tema,
                    "tema": p.tema_principal,
                    "area": p.area_evaluada,
                    "dificultad": p.nivel_dificultad,
                    "importancia": p.importancia_icfes
                }
                for p in prereq_topics
            ]
        
        # Obtener temas relacionados
        relacionados_details = []
        if topic.temas_relacionados:
            rel_topics = db.query(StudyTopicsCatalog).filter(
                StudyTopicsCatalog.codigo_tema.in_(topic.temas_relacionados),
                StudyTopicsCatalog.estado == 'activo'
            ).all()
            
            relacionados_details = [
                {
                    "codigo": r.codigo_tema,
                    "tema": r.tema_principal,
                    "area": r.area_evaluada,
                    "dificultad": r.nivel_dificultad,
                    "importancia": r.importancia_icfes
                }
                for r in rel_topics
            ]
        
        return {
            "success": True,
            "tema_actual": {
                "codigo": topic.codigo_tema,
                "tema": topic.tema_principal,
                "area": topic.area_evaluada,
                "dificultad": topic.nivel_dificultad,
                "importancia": topic.importancia_icfes
            },
            "prerequisitos": prerequisitos_details,
            "temas_relacionados": relacionados_details,
            "ruta_aprendizaje": topic.get_learning_path()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo ruta de aprendizaje: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error obteniendo ruta de aprendizaje"
        )

@router.get("/search")
async def search_topics(
    q: str = Query(..., min_length=2, description="Término de búsqueda"),
    area: Optional[str] = Query(None, description="Filtrar por área"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """
    Busca temas por texto en título, subtema o competencia
    
    WHY: Búsqueda semántica de temas ICFES
    """
    try:
        query = db.query(StudyTopicsCatalog).filter(
            StudyTopicsCatalog.estado == 'activo'
        ).filter(
            func.or_(
                StudyTopicsCatalog.tema_principal.ilike(f"%{q}%"),
                StudyTopicsCatalog.subtema.ilike(f"%{q}%"),
                StudyTopicsCatalog.competencia_icfes.ilike(f"%{q}%"),
                StudyTopicsCatalog.tema_especifico.ilike(f"%{q}%")
            )
        )
        
        if area:
            query = query.filter(StudyTopicsCatalog.area_evaluada == area)
        
        # Ordenar por relevancia (importancia + coincidencia)
        query = query.order_by(
            StudyTopicsCatalog.importancia_icfes.desc(),
            StudyTopicsCatalog.nivel_dificultad
        )
        
        total = query.count()
        topics = query.limit(limit).all()
        
        return {
            "success": True,
            "query": q,
            "total_results": total,
            "limit": limit,
            "topics": [
                {
                    "codigo": t.codigo_tema,
                    "area": t.area_evaluada,
                    "tema": t.tema_principal,
                    "subtema": t.subtema,
                    "competencia": t.competencia_icfes,
                    "dificultad": t.nivel_dificultad,
                    "importancia": t.importancia_icfes,
                    "relevancia_score": _calculate_relevance_score(t, q)
                }
                for t in topics
            ]
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error en búsqueda de temas"
        )
    
    def _calculate_relevance_score(topic, query: str) -> float:
        """Calcula score de relevancia para ordenamiento"""
        score = 0
        
        # Coincidencia exacta en título
        if query.lower() in topic.tema_principal.lower():
            score += 10
        
        # Coincidencia en subtema
        if topic.subtema and query.lower() in topic.subtema.lower():
            score += 8
        
        # Coincidencia en competencia
        if query.lower() in topic.competencia_icfes.lower():
            score += 6
        
        # Importancia del tema
        score += topic.importancia_icfes or 0
        
        return score
