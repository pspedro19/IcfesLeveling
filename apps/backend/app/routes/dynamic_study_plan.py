"""
Dynamic Study Plan API
Genera y gestiona planes de estudio dinámicos con videos de YouTube
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, Optional
import logging
import json

from ..core.database import get_db
from ..services.dynamic_plan_generator import DynamicPlanGenerator
# from ..core.security import get_current_user
# from ..models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/study-plan", tags=["dynamic-study-plan"])

@router.post("/generate")
async def generate_dynamic_plan(
    diagnostic_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    Genera un plan de estudio dinámico basado en los resultados del diagnóstico
    """
    try:
        # Usar usuario actual o un ID temporal para pruebas
        user_id = diagnostic_data.get('user_id', 'guest')
        subject_id = diagnostic_data.get('subject_id')
        
        if not subject_id:
            raise HTTPException(status_code=400, detail="subject_id es requerido")
        
        logger.info(f"📚 Generando plan para usuario {user_id}, materia {subject_id}")
        
        # Generar el plan
        generator = DynamicPlanGenerator(db)
        result = generator.generate_plan_from_diagnostic(
            user_id=user_id,
            subject_id=subject_id,
            diagnostic_results=diagnostic_data
        )
        
        if result['success']:
            logger.info(f"✅ Plan generado exitosamente: {result['plan_id']}")
            return {
                'success': True,
                'plan_id': result['plan_id'],
                'redirect_url': f'/study-plan-view?plan_id={result["plan_id"]}&subject={subject_id}',
                'summary': {
                    'units': len(result['units']),
                    'videos': result['total_videos'],
                    'weeks': result['estimated_weeks']
                },
                'message': result['message']
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"❌ Error generando plan dinámico: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/view/{plan_id}")
async def get_study_plan(
    plan_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene un plan de estudio con sus unidades y videos
    """
    try:
        # Obtener el plan de yml_storage
        query = text("""
            SELECT yml_content, metadata, user_id, subject
            FROM yml_storage
            WHERE id = :plan_id
        """)
        
        result = db.execute(query, {'plan_id': plan_id}).first()
        
        if not result:
            # Crear un plan de ejemplo si no existe
            logger.warning(f"Plan {plan_id} no encontrado, creando uno de ejemplo")
            return _create_example_plan(db, plan_id)
        
        import yaml
        yml_data = yaml.safe_load(result[0])
        metadata = json.loads(result[1]) if result[1] else {}
        
        # Enriquecer con información adicional
        units = yml_data.get('plan', {}).get('units', [])
        
        return {
            'success': True,
            'plan_id': plan_id,
            'user_id': result[2],
            'subject_id': result[3],
            'units': units,
            'metadata': metadata,
            'summary': {
                'total_units': len(units),
                'total_videos': sum(len(u.get('videos', [])) for u in units),
                'total_xp': sum(sum(v.get('xp', 0) for v in u.get('videos', [])) for u in units)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo plan: {e}")
        # Devolver plan de ejemplo en caso de error
        return _create_example_plan(db, plan_id)

@router.get("/units/by-subject/{subject_id}")
async def get_units_by_subject(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """
    Obtiene las unidades disponibles para una materia con sus videos
    """
    try:
        # Obtener nombre de la materia
        subject_query = text("SELECT name FROM subjects WHERE id = :id")
        subject_result = db.execute(subject_query, {'id': subject_id}).first()
        subject_name = subject_result[0] if subject_result else 'Matemáticas'
        
        # Obtener videos de YouTube para esta materia
        videos_query = text("""
            SELECT 
                youtube_id,
                video_title,
                youtube_url,
                tema_principal,
                duration_seconds,
                puntos_xp,
                canal_sugerido,
                nivel_dificultad
            FROM youtube_links
            WHERE area_evaluada = :area
            AND estado = 'activo'
            ORDER BY orden_recomendacion, tema_principal
        """)
        
        videos = db.execute(videos_query, {'area': subject_name}).fetchall()
        
        # Organizar videos en unidades por tema
        units_dict = {}
        for video in videos:
            tema = video[3]
            if tema not in units_dict:
                units_dict[tema] = []
            
            units_dict[tema].append({
                'id': video[0],
                'title': video[1],
                'url': video[2],
                'duration': video[4],
                'xp': video[5],
                'channel': video[6],
                'difficulty': video[7]
            })
        
        # Convertir a lista de unidades
        units = []
        for i, (tema, videos_list) in enumerate(units_dict.items(), 1):
            units.append({
                'unit_number': i,
                'title': f'Unidad {i}: {tema}',
                'description': f'Aprende sobre {tema}',
                'videos': videos_list,
                'total_duration': sum(v['duration'] for v in videos_list),
                'total_xp': sum(v['xp'] for v in videos_list)
            })
        
        return {
            'success': True,
            'subject_id': subject_id,
            'subject_name': subject_name,
            'units': units,
            'total_units': len(units),
            'total_videos': sum(len(u['videos']) for u in units)
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo unidades: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _create_example_plan(db: Session, plan_id: str) -> Dict:
    """
    Crea un plan de ejemplo con videos reales de la base de datos
    """
    try:
        # Obtener algunos videos de la base de datos
        query = text("""
            SELECT 
                youtube_id,
                video_title,
                youtube_url,
                tema_principal,
                duration_seconds,
                puntos_xp
            FROM youtube_links
            WHERE estado = 'activo'
            ORDER BY relevancia_score DESC
            LIMIT 9
        """)
        
        videos = db.execute(query).fetchall()
        
        # Organizar en 3 unidades
        units = []
        for i in range(3):
            unit_videos = []
            for j in range(3):
                idx = i * 3 + j
                if idx < len(videos):
                    video = videos[idx]
                    unit_videos.append({
                        'id': video[0],
                        'title': video[1],
                        'url': video[2],
                        'duration_minutes': video[4] // 60,
                        'xp': video[5]
                    })
            
            if unit_videos:
                units.append({
                    'unit_number': i + 1,
                    'title': f'Unidad {i + 1}: {["Fundamentos", "Intermedio", "Avanzado"][i]}',
                    'description': f'Nivel {i + 1} de aprendizaje',
                    'videos': unit_videos,
                    'exercises': [
                        {'type': 'quiz', 'title': f'Quiz Unidad {i + 1}', 'questions': 5, 'xp': 50},
                        {'type': 'practice', 'title': f'Práctica Unidad {i + 1}', 'questions': 10, 'xp': 100}
                    ]
                })
        
        return {
            'success': True,
            'plan_id': plan_id,
            'units': units,
            'metadata': {
                'is_example': True,
                'message': 'Plan de ejemplo con videos reales'
            },
            'summary': {
                'total_units': len(units),
                'total_videos': sum(len(u['videos']) for u in units),
                'total_xp': sum(sum(v['xp'] for v in u['videos']) for u in units)
            }
        }
        
    except Exception as e:
        logger.error(f"Error creando plan de ejemplo: {e}")
        return {
            'success': False,
            'error': str(e),
            'units': [],
            'message': 'Error al crear plan de ejemplo'
        }