from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.user import User
from ..services.icfes_catalog_service import ICFESCatalogService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/icfes-catalog", tags=["icfes-catalog"])

@router.get("/areas")
async def get_icfes_areas(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Obtener todas las áreas disponibles del ICFES"""
    try:
        catalog_service = ICFESCatalogService(db)
        areas = catalog_service.get_all_areas()
        
        logger.info(f"✅ Áreas ICFES obtenidas: {len(areas)} áreas")
        return {
            "success": True,
            "areas": areas,
            "total_areas": len(areas)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo áreas ICFES: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo áreas ICFES: {str(e)}")

@router.get("/areas/{area_code}/topics")
async def get_topics_by_area(
    area_code: str,
    difficulty: Optional[int] = Query(None, description="Filtrar por dificultad (1=básico, 2=intermedio, 3=avanzado)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Obtener todos los temas de un área específica del ICFES"""
    try:
        catalog_service = ICFESCatalogService(db)
        
        if difficulty:
            topics = catalog_service.get_topics_by_difficulty(area_code, difficulty)
        else:
            topics = catalog_service.get_topics_by_area(area_code)
        
        if not topics:
            raise HTTPException(status_code=404, detail=f"No se encontraron temas para el área {area_code}")
        
        logger.info(f"✅ Temas obtenidos para área {area_code}: {len(topics)} temas")
        return {
            "success": True,
            "area_code": area_code,
            "topics": topics,
            "total_topics": len(topics),
            "filtered_by_difficulty": difficulty is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo temas para área {area_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo temas: {str(e)}")

@router.get("/topics/{topic_code}")
async def get_topic_by_code(
    topic_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Obtener un tema específico por código"""
    try:
        catalog_service = ICFESCatalogService(db)
        topic = catalog_service.get_topic_by_code(topic_code)
        
        if not topic:
            raise HTTPException(status_code=404, detail=f"Tema {topic_code} no encontrado")
        
        logger.info(f"✅ Tema obtenido: {topic_code}")
        return {
            "success": True,
            "topic": topic
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo tema {topic_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tema: {str(e)}")

@router.get("/areas/{area_code}/videos")
async def get_youtube_videos_by_area(
    area_code: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Obtener todos los videos YouTube de un área específica"""
    try:
        catalog_service = ICFESCatalogService(db)
        videos = catalog_service.get_youtube_videos_by_area(area_code)
        
        logger.info(f"✅ Videos obtenidos para área {area_code}: {len(videos)} videos")
        return {
            "success": True,
            "area_code": area_code,
            "videos": videos,
            "total_videos": len(videos)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo videos para área {area_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo videos: {str(e)}")

@router.get("/recommendations")
async def get_recommended_topics(
    max_topics: int = Query(10, ge=1, le=50, description="Número máximo de temas recomendados"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener temas recomendados basados en el nivel del usuario"""
    try:
        catalog_service = ICFESCatalogService(db)
        user_level = getattr(current_user, 'level', 1) or 1
        
        recommended = catalog_service.get_recommended_topics(user_level, max_topics)
        
        logger.info(f"✅ Temas recomendados obtenidos para usuario nivel {user_level}: {len(recommended)} temas")
        return {
            "success": True,
            "user_level": user_level,
            "recommended_topics": recommended,
            "total_recommended": len(recommended)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo temas recomendados: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo recomendaciones: {str(e)}")

@router.post("/areas/{area_code}/generate-units")
async def generate_study_units_from_catalog(
    area_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generar unidades de estudio basadas en el catálogo ICFES"""
    try:
        catalog_service = ICFESCatalogService(db)
        user_level = getattr(current_user, 'level', 1) or 1
        
        units = catalog_service.generate_study_units_from_catalog(area_code, user_level)
        
        if not units:
            raise HTTPException(status_code=404, detail=f"No se pudieron generar unidades para el área {area_code}")
        
        logger.info(f"✅ Unidades generadas para área {area_code}: {len(units)} unidades")
        return {
            "success": True,
            "area_code": area_code,
            "user_level": user_level,
            "units": units,
            "total_units": len(units)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando unidades para área {area_code}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando unidades: {str(e)}")

@router.get("/statistics")
async def get_catalog_statistics(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Obtener estadísticas completas del catálogo ICFES"""
    try:
        catalog_service = ICFESCatalogService(db)
        stats = catalog_service.get_catalog_statistics()
        
        logger.info(f"✅ Estadísticas del catálogo obtenidas: {stats['total_topics']} temas, {stats['total_videos']} videos")
        return {
            "success": True,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del catálogo: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@router.get("/search")
async def search_topics(
    query: str = Query(..., min_length=2, description="Término de búsqueda"),
    area_code: Optional[str] = Query(None, description="Filtrar por área específica"),
    difficulty: Optional[int] = Query(None, description="Filtrar por dificultad"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Buscar temas en el catálogo ICFES"""
    try:
        catalog_service = ICFESCatalogService(db)
        
        # Buscar en todas las áreas o en una específica
        search_areas = [area_code] if area_code else catalog_service.catalog_data.keys()
        
        results = []
        for area in search_areas:
            if area in catalog_service.catalog_data:
                topics = catalog_service.catalog_data[area]
                
                # Filtrar por dificultad si se especifica
                if difficulty:
                    topics = [t for t in topics if t['difficulty'] == difficulty]
                
                # Buscar en nombre del tema y área
                for topic in topics:
                    if (query.lower() in topic['main_topic'].lower() or 
                        query.lower() in topic['area'].lower()):
                        results.append({
                            **topic,
                            'area_code': area
                        })
        
        # Ordenar por relevancia (peso ICFES)
        results.sort(key=lambda x: x['icfes_weight'], reverse=True)
        
        logger.info(f"✅ Búsqueda completada: '{query}' - {len(results)} resultados")
        return {
            "success": True,
            "query": query,
            "results": results,
            "total_results": len(results),
            "filters": {
                "area_code": area_code,
                "difficulty": difficulty
            }
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")
