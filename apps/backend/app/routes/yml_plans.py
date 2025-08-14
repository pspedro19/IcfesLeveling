from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import json
import logging

from ..core.database import get_db
from ..models.user import User
from ..models.subject import Subject
from ..services.personalized_yml_generator import PersonalizedYMLGenerator
from ..services.yml_storage_service import YMLStorageService
from ..core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/yml", tags=["YML Plans"])

@router.post("/generate/{subject_id}")
async def generate_personalized_yml(
    subject_id: str,
    diagnostic_id: Optional[str] = Query(None, description="ID del test diagnóstico"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera YML personalizado para un usuario en una materia específica
    """
    try:
        # Verificar que la materia existe
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        # Crear generador de YML
        yml_generator = PersonalizedYMLGenerator(db)
        
        # Generar YML personalizado
        result = await yml_generator.generate_user_yml(
            user_id=str(current_user.id),
            diagnostic_id=diagnostic_id or f"battle_{current_user.id}",
            subject=subject.name.lower()
        )
        
        logger.info(f"✅ YML generado exitosamente para usuario {current_user.id}, materia {subject.name}")
        
        return {
            'status': 'success',
            'message': 'YML personalizado generado exitosamente',
            'data': {
                'generation_id': result['storage_info']['storage_id'],
                'subject': subject.name,
                'total_modules': result['summary']['total_modules'],
                'estimated_weeks': result['summary']['estimated_weeks'],
                'generation_time_ms': result['generation_time_ms'],
                'generated_at': result['generated_at']
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando YML: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando YML: {str(e)}")

@router.get("/{user_id}/{subject}")
async def get_user_yml(
    user_id: str,
    subject: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene YML personalizado de un usuario
    """
    try:
        # Verificar permisos (usuario solo puede ver su propio YML)
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver este YML")
        
        # Crear servicio de almacenamiento
        yml_storage = YMLStorageService(db)
        
        # Recuperar YML usando sistema de 3 capas
        yml_content = await yml_storage.retrieve_yml(user_id, subject)
        
        if not yml_content:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró YML para usuario {user_id} en materia {subject}"
            )
        
        # Parsear YML a diccionario
        import yaml
        try:
            yml_data = yaml.safe_load(yml_content)
        except yaml.YAMLError as e:
            logger.error(f"Error parseando YML: {e}")
            raise HTTPException(status_code=500, detail="Error parseando YML")
        
        logger.info(f"✅ YML recuperado exitosamente para usuario {user_id}, materia {subject}")
        
        return {
            'status': 'success',
            'data': {
                'yml_content': yml_data,
                'raw_yml': yml_content,
                'subject': subject,
                'user_id': user_id,
                'retrieved_at': yaml_data.get('generated_at', 'N/A')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error recuperando YML: {e}")
        raise HTTPException(status_code=500, detail=f"Error recuperando YML: {str(e)}")

@router.get("/{user_id}/{subject}/metadata")
async def get_yml_metadata(
    user_id: str,
    subject: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene metadata del YML sin el contenido completo
    """
    try:
        # Verificar permisos
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver esta metadata")
        
        # Crear servicio de almacenamiento
        yml_storage = YMLStorageService(db)
        
        # Obtener metadata
        metadata = yml_storage.get_user_yml_metadata(user_id, subject)
        
        if not metadata:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró YML para usuario {user_id} en materia {subject}"
            )
        
        return {
            'status': 'success',
            'data': metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo metadata: {str(e)}")

@router.get("/{user_id}/list")
async def list_user_ymls(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lista todos los YMLs de un usuario
    """
    try:
        # Verificar permisos
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para ver esta lista")
        
        # Crear servicio de almacenamiento
        yml_storage = YMLStorageService(db)
        
        # Listar YMLs
        ymls = yml_storage.list_user_ymls(user_id)
        
        return {
            'status': 'success',
            'data': {
                'user_id': user_id,
                'total_ymls': len(ymls),
                'ymls': ymls
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error listando YMLs: {e}")
        raise HTTPException(status_code=500, detail=f"Error listando YMLs: {str(e)}")

@router.post("/{user_id}/{subject}/regenerate")
async def regenerate_yml(
    user_id: str,
    subject: str,
    diagnostic_id: Optional[str] = Query(None, description="ID del test diagnóstico"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Regenera YML personalizado (útil cuando el usuario mejora o cambia)
    """
    try:
        # Verificar permisos
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para regenerar este YML")
        
        # Verificar que la materia existe
        subject_obj = db.query(Subject).filter(Subject.name.ilike(f"%{subject}%")).first()
        if not subject_obj:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        # Crear generador de YML
        yml_generator = PersonalizedYMLGenerator(db)
        
        # Regenerar YML
        result = await yml_generator.generate_user_yml(
            user_id=str(current_user.id),
            diagnostic_id=diagnostic_id or f"battle_{current_user.id}",
            subject=subject_obj.name.lower()
        )
        
        logger.info(f"✅ YML regenerado exitosamente para usuario {current_user.id}, materia {subject}")
        
        return {
            'status': 'success',
            'message': 'YML personalizado regenerado exitosamente',
            'data': {
                'generation_id': result['storage_info']['storage_id'],
                'subject': subject_obj.name,
                'total_modules': result['summary']['total_modules'],
                'estimated_weeks': result['summary']['estimated_weeks'],
                'generation_time_ms': result['generation_time_ms'],
                'regenerated_at': result['generated_at']
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error regenerando YML: {e}")
        raise HTTPException(status_code=500, detail=f"Error regenerando YML: {str(e)}")

@router.delete("/{user_id}/{subject}/cache")
async def invalidate_yml_cache(
    user_id: str,
    subject: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Invalida cache de YML (útil para forzar refresco)
    """
    try:
        # Verificar permisos
        if str(current_user.id) != user_id:
            raise HTTPException(status_code=403, detail="No tienes permisos para invalidar este cache")
        
        # Crear servicio de almacenamiento
        yml_storage = YMLStorageService(db)
        
        # Invalidar cache
        await yml_storage.invalidate_cache(user_id, subject)
        
        logger.info(f"✅ Cache invalidado para usuario {user_id}, materia {subject}")
        
        return {
            'status': 'success',
            'message': 'Cache invalidado exitosamente'
        }
        
    except Exception as e:
        logger.error(f"❌ Error invalidando cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error invalidando cache: {str(e)}")

@router.get("/storage/stats")
async def get_storage_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de almacenamiento YML (solo para administradores)
    """
    try:
        # Verificar si es administrador (implementar lógica de roles)
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Solo administradores pueden ver estadísticas")
        
        # Crear servicio de almacenamiento
        yml_storage = YMLStorageService(db)
        
        # Obtener estadísticas
        stats = yml_storage.get_storage_stats()
        
        return {
            'status': 'success',
            'data': stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@router.post("/generate-async/{subject_id}")
async def generate_yml_async(
    subject_id: str,
    diagnostic_id: Optional[str] = Query(None, description="ID del test diagnóstico"),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Genera YML de forma asíncrona (para usuarios que no quieren esperar)
    """
    try:
        # Verificar que la materia existe
        subject = db.query(Subject).filter(Subject.id == subject_id).first()
        if not subject:
            raise HTTPException(status_code=404, detail="Materia no encontrada")
        
        # Crear job ID único
        import uuid
        job_id = str(uuid.uuid4())
        
        # Agregar tarea en background
        if background_tasks:
            background_tasks.add_task(
                _generate_yml_background,
                job_id=job_id,
                user_id=str(current_user.id),
                subject_id=subject_id,
                diagnostic_id=diagnostic_id or f"battle_{current_user.id}",
                db=db
            )
        
        logger.info(f"🚀 YML en cola para generación asíncrona: {job_id}")
        
        return {
            'status': 'queued',
            'message': 'YML en cola para generación',
            'data': {
                'job_id': job_id,
                'subject': subject.name,
                'estimated_time_seconds': 10,
                'check_status_url': f'/api/yml/status/{job_id}',
                'webhook_url': f'/api/yml/webhook/{current_user.id}'
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error encolando YML: {e}")
        raise HTTPException(status_code=500, detail=f"Error encolando YML: {str(e)}")

@router.get("/status/{job_id}")
async def check_generation_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifica estado de generación de YML
    """
    try:
        # Aquí implementarías lógica para verificar estado del job
        # Por ahora, simulamos un estado
        import random
        
        # Simular diferentes estados
        statuses = ['processing', 'completed', 'failed']
        status = random.choice(statuses)
        
        if status == 'completed':
            return {
                'status': 'completed',
                'job_id': job_id,
                'message': 'YML generado exitosamente',
                'data': {
                    'download_url': f'/api/yml/{current_user.id}/matematicas',
                    'generated_at': '2024-01-01T00:00:00Z'
                }
            }
        elif status == 'processing':
            return {
                'status': 'processing',
                'job_id': job_id,
                'message': 'YML en proceso de generación',
                'progress': random.randint(20, 80)
            }
        else:
            return {
                'status': 'failed',
                'job_id': job_id,
                'message': 'Error en la generación del YML',
                'error': 'Error simulado para demostración'
            }
        
    except Exception as e:
        logger.error(f"❌ Error verificando estado: {e}")
        raise HTTPException(status_code=500, detail=f"Error verificando estado: {str(e)}")

async def _generate_yml_background(
    job_id: str,
    user_id: str,
    subject_id: str,
    diagnostic_id: str,
    db: Session
):
    """
    Función de background para generar YML
    """
    try:
        logger.info(f"🔄 Iniciando generación en background: {job_id}")
        
        # Crear generador de YML
        yml_generator = PersonalizedYMLGenerator(db)
        
        # Generar YML
        result = await yml_generator.generate_user_yml(
            user_id=user_id,
            diagnostic_id=diagnostic_id,
            subject=subject_id
        )
        
        logger.info(f"✅ YML generado en background exitosamente: {job_id}")
        
        # Aquí podrías enviar notificación al usuario
        # await notify_user_yml_ready(user_id, result)
        
    except Exception as e:
        logger.error(f"❌ Error en generación background: {e}")
        # Aquí podrías enviar notificación de error al usuario
        # await notify_user_yml_error(user_id, str(e))
