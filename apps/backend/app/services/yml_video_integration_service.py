"""
Servicio de Integración YML-Video para el Sistema ICFES
Conecta la generación de planes YML con el tracking de videos
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
import json

from ..schemas.video_learning import VideoProgressCreate
from .personalized_yml_generator import PersonalizedYMLGenerator
from .video_progress_service import VideoProgressService
from .yml_storage_service import YMLStorageService

logger = logging.getLogger(__name__)

class YMLVideoIntegrationService:
    """
    Servicio que integra la generación de planes YML con el tracking de videos
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.yml_generator = PersonalizedYMLGenerator(db)
        self.video_service = VideoProgressService(db)
        self.yml_storage = YMLStorageService(db)
    
    async def generate_yml_with_videos(
        self, 
        user_id: str, 
        diagnostic_id: str,
        subject: str
    ) -> Dict[str, Any]:
        """
        Genera un plan YML personalizado con videos integrados
        """
        try:
            logger.info(f"🎬 Generando YML con videos para usuario {user_id}, materia {subject}")
            
            # Generar YML base
            yml_content = await self.yml_generator.generate_user_yml(
                user_id, diagnostic_id, subject
            )
            
            # Parsear YML para extraer información de videos
            yml_data = self._parse_yml_content(yml_content)
            
            # Enriquecer con datos de videos del catálogo
            enriched_yml = await self._enrich_yml_with_video_data(yml_data, user_id)
            
            # Almacenar YML enriquecido
            storage_info = await self.yml_storage.store_yml(
                user_id, 
                subject, 
                enriched_yml,
                metadata={
                    'has_videos': True,
                    'total_videos': self._count_total_videos(enriched_yml),
                    'estimated_duration_minutes': self._calculate_total_duration(enriched_yml),
                    'video_integration_version': '2.0'
                }
            )
            
            logger.info(f"✅ YML con videos generado exitosamente para usuario {user_id}")
            
            return {
                'status': 'success',
                'yml_content': enriched_yml,
                'storage_info': storage_info,
                'video_summary': self._generate_video_summary(enriched_yml)
            }
            
        except Exception as e:
            logger.error(f"❌ Error generando YML con videos: {e}")
            raise
    
    def _parse_yml_content(self, yml_content: str) -> Dict[str, Any]:
        """Parsea el contenido YML para extraer información estructurada"""
        try:
            import yaml
            return yaml.safe_load(yml_content)
        except Exception as e:
            logger.error(f"Error parseando YML: {e}")
            return {}
    
    async def _enrich_yml_with_video_data(self, yml_data: Dict[str, Any], user_id: str) -> str:
        """Enriquece el YML con datos completos de videos"""
        try:
            if 'modules' not in yml_data:
                return yaml.dump(yml_data, default_flow_style=False, allow_unicode=True)
            
            # Enriquecer cada módulo con datos de videos
            for module in yml_data['modules']:
                if 'lessons' in module and module['lessons']:
                    lesson = module['lessons'][0]
                    if 'primary_resource' in lesson and 'videos' in lesson['primary_resource']:
                        # Los videos ya están enriquecidos por el generador
                        # Solo necesitamos agregar metadatos adicionales
                        lesson['primary_resource']['video_metadata'] = {
                            'total_count': len(lesson['primary_resource']['videos']),
                            'total_duration_minutes': lesson['primary_resource'].get('total_video_duration_minutes', 0),
                            'difficulty_range': self._get_difficulty_range(lesson['primary_resource']['videos']),
                            'learning_styles_covered': self._get_learning_styles(lesson['primary_resource']['videos']),
                            'last_updated': datetime.utcnow().isoformat()
                        }
                        
                        # Agregar información de progreso del usuario
                        lesson['user_progress'] = await self._get_user_video_progress(
                            user_id, 
                            [v['video_id'] for v in lesson['primary_resource']['videos']]
                        )
            
            # Agregar metadatos generales del plan
            yml_data['video_plan_metadata'] = {
                'generated_at': datetime.utcnow().isoformat(),
                'total_modules': len(yml_data['modules']),
                'total_videos': self._count_total_videos(yml_data),
                'estimated_total_duration_minutes': self._calculate_total_duration(yml_data),
                'video_catalog_version': '1.0',
                'integration_status': 'complete'
            }
            
            return yaml.dump(yml_data, default_flow_style=False, allow_unicode=True)
            
        except Exception as e:
            logger.error(f"Error enriqueciendo YML con datos de video: {e}")
            return yaml.dump(yml_data, default_flow_style=False, allow_unicode=True)
    
    async def _get_user_video_progress(
        self, 
        user_id: str, 
        video_ids: List[str]
    ) -> Dict[str, Any]:
        """Obtiene el progreso del usuario para los videos específicos"""
        try:
            if not video_ids:
                return {}
            
            # Consultar progreso existente
            query = text("""
                SELECT 
                    video_id,
                    watched_percentage,
                    is_completed,
                    replay_count,
                    last_watched_at
                FROM video_tracking 
                WHERE user_id = :user_id AND video_id = ANY(:video_ids)
            """)
            
            result = self.db.execute(query, {
                "user_id": user_id,
                "video_ids": video_ids
            })
            
            progress_data = {}
            for row in result:
                progress_data[row.video_id] = {
                    'watched_percentage': row.watched_percentage,
                    'is_completed': row.is_completed,
                    'replay_count': row.replay_count,
                    'last_watched_at': row.last_watched_at.isoformat() if row.last_watched_at else None
                }
            
            return progress_data
            
        except Exception as e:
            logger.error(f"Error obteniendo progreso de usuario: {e}")
            return {}
    
    def _get_difficulty_range(self, videos: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcula el rango de dificultad de los videos"""
        if not videos:
            return {'min': 0, 'max': 0, 'average': 0}
        
        difficulties = [v.get('difficulty', 0) for v in videos]
        return {
            'min': min(difficulties),
            'max': max(difficulties),
            'average': round(sum(difficulties) / len(difficulties), 1)
        }
    
    def _get_learning_styles(self, videos: List[Dict[str, Any]]) -> List[str]:
        """Obtiene los estilos de aprendizaje cubiertos por los videos"""
        styles = set()
        for video in videos:
            if 'learning_style' in video:
                styles.add(video['learning_style'])
        return list(styles)
    
    def _count_total_videos(self, yml_data: Dict[str, Any]) -> int:
        """Cuenta el total de videos en el plan YML"""
        total = 0
        if 'modules' in yml_data:
            for module in yml_data['modules']:
                if 'lessons' in module and module['lessons']:
                    lesson = module['lessons'][0]
                    if 'primary_resource' in lesson and 'videos' in lesson['primary_resource']:
                        total += len(lesson['primary_resource']['videos'])
        return total
    
    def _calculate_total_duration(self, yml_data: Dict[str, Any]) -> int:
        """Calcula la duración total estimada del plan"""
        total_minutes = 0
        if 'modules' in yml_data:
            for module in yml_data['modules']:
                if 'lessons' in module and module['lessons']:
                    lesson = module['lessons'][0]
                    if 'primary_resource' in lesson:
                        total_minutes += lesson['primary_resource'].get('total_video_duration_minutes', 0)
        return total_minutes
    
    def _generate_video_summary(self, yml_data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un resumen del plan de videos"""
        modules = yml_data.get('modules', [])
        
        summary = {
            'total_modules': len(modules),
            'total_videos': self._count_total_videos(yml_data),
            'estimated_duration_minutes': self._calculate_total_duration(yml_data),
            'modules_summary': []
        }
        
        for module in modules:
            if 'lessons' in module and module['lessons']:
                lesson = module['lessons'][0]
                if 'primary_resource' in lesson and 'videos' in lesson['primary_resource']:
                    videos = lesson['primary_resource']['videos']
                    module_summary = {
                        'module_id': module.get('id', ''),
                        'topic_name': module.get('topic_name', ''),
                        'video_count': len(videos),
                        'total_duration_minutes': lesson['primary_resource'].get('total_video_duration_minutes', 0),
                        'difficulty': module.get('difficulty', ''),
                        'priority': module.get('priority', '')
                    }
                    summary['modules_summary'].append(module_summary)
        
        return summary
    
    async def update_video_progress_from_yml(
        self, 
        user_id: str, 
        video_id: str, 
        progress_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Actualiza el progreso de un video basado en el plan YML
        """
        try:
            # Crear objeto de progreso
            video_progress = VideoProgressCreate(
                user_id=user_id,
                video_id=video_id,
                plan_id=progress_data.get('plan_id'),
                unit_number=progress_data.get('unit_number', 1),
                codigo_tema=progress_data.get('codigo_tema'),
                watched_seconds=progress_data.get('watched_seconds', 0),
                watched_percentage=progress_data.get('watched_percentage', 0),
                is_completed=progress_data.get('is_completed', False),
                replay_count=progress_data.get('replay_count', 0),
                speed_preference=progress_data.get('speed_preference', '1.0')
            )
            
            # Actualizar progreso
            result = await self.video_service.update_video_progress(video_progress)
            
            # Actualizar YML si es necesario
            await self._update_yml_progress(user_id, video_id, progress_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error actualizando progreso de video desde YML: {e}")
            raise
    
    async def _update_yml_progress(
        self, 
        user_id: str, 
        video_id: str, 
        progress_data: Dict[str, Any]
    ):
        """Actualiza el progreso en el YML almacenado"""
        try:
            # Obtener YML actual
            yml_data = await self.yml_storage.get_latest_yml(user_id, progress_data.get('subject', 'general'))
            if not yml_data:
                return
            
            # Parsear YML
            yml_content = yml_data.get('content', '')
            yml_parsed = self._parse_yml_content(yml_content)
            
            # Actualizar progreso del video específico
            if 'modules' in yml_parsed:
                for module in yml_parsed['modules']:
                    if 'lessons' in module and module['lessons']:
                        lesson = module['lessons'][0]
                        if 'primary_resource' in lesson and 'videos' in lesson['primary_resource']:
                            for video in lesson['primary_resource']['videos']:
                                if video.get('video_id') == video_id:
                                    # Actualizar progreso del usuario
                                    if 'user_progress' not in lesson:
                                        lesson['user_progress'] = {}
                                    
                                    lesson['user_progress'][video_id] = {
                                        'watched_percentage': progress_data.get('watched_percentage', 0),
                                        'is_completed': progress_data.get('is_completed', False),
                                        'replay_count': progress_data.get('replay_count', 0),
                                        'last_updated': datetime.utcnow().isoformat()
                                    }
                                    break
            
            # Guardar YML actualizado
            updated_yml = yaml.dump(yml_parsed, default_flow_style=False, allow_unicode=True)
            await self.yml_storage.store_yml(
                user_id,
                progress_data.get('subject', 'general'),
                updated_yml,
                metadata={
                    'updated_at': datetime.utcnow().isoformat(),
                    'video_progress_updated': video_id,
                    'update_type': 'video_progress'
                }
            )
            
        except Exception as e:
            logger.error(f"Error actualizando progreso en YML: {e}")
    
    async def get_user_yml_video_progress(
        self, 
        user_id: str, 
        subject: str
    ) -> Dict[str, Any]:
        """
        Obtiene el progreso completo de videos del plan YML del usuario
        """
        try:
            # Obtener YML más reciente
            yml_data = await self.yml_storage.get_latest_yml(user_id, subject)
            if not yml_data:
                return {'error': 'No se encontró plan YML para este usuario'}
            
            # Parsear YML
            yml_content = yml_data.get('content', '')
            yml_parsed = self._parse_yml_content(yml_content)
            
            # Extraer progreso de videos
            video_progress = {
                'plan_generated_at': yml_data.get('created_at'),
                'total_modules': len(yml_parsed.get('modules', [])),
                'modules_progress': []
            }
            
            for module in yml_parsed.get('modules', []):
                module_progress = {
                    'module_id': module.get('id'),
                    'topic_name': module.get('topic_name'),
                    'topic_code': module.get('topic_code'),
                    'difficulty': module.get('difficulty'),
                    'priority': module.get('priority'),
                    'videos': []
                }
                
                if 'lessons' in module and module['lessons']:
                    lesson = module['lessons'][0]
                    if 'primary_resource' in lesson and 'videos' in lesson['primary_resource']:
                        for video in lesson['primary_resource']['videos']:
                            video_progress_data = {
                                'video_id': video.get('video_id'),
                                'title': video.get('title'),
                                'duration_minutes': video.get('duration_minutes'),
                                'difficulty': video.get('difficulty'),
                                'learning_style': video.get('learning_style'),
                                'user_progress': lesson.get('user_progress', {}).get(video.get('video_id'), {})
                            }
                            module_progress['videos'].append(video_progress_data)
                
                video_progress['modules_progress'].append(module_progress)
            
            return video_progress
            
        except Exception as e:
            logger.error(f"Error obteniendo progreso de videos YML: {e}")
            return {'error': str(e)}
    
    async def recommend_next_videos(
        self, 
        user_id: str, 
        subject: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recomienda los siguientes videos basándose en el progreso YML
        """
        try:
            # Obtener progreso actual
            current_progress = await self.get_user_yml_video_progress(user_id, subject)
            if 'error' in current_progress:
                return []
            
            recommendations = []
            
            for module in current_progress.get('modules_progress', []):
                # Verificar si el módulo tiene videos no completados
                incomplete_videos = [
                    video for video in module['videos']
                    if not video.get('user_progress', {}).get('is_completed', False)
                ]
                
                if incomplete_videos:
                    # Agregar el primer video incompleto como recomendación
                    video = incomplete_videos[0]
                    recommendations.append({
                        'video_id': video['video_id'],
                        'title': video['title'],
                        'module_id': module['module_id'],
                        'topic_name': module['topic_name'],
                        'difficulty': video['difficulty'],
                        'duration_minutes': video['duration_minutes'],
                        'reason': f"Próximo video del módulo {module['topic_name']}",
                        'priority': module.get('priority', 'medium')
                    })
                    
                    if len(recommendations) >= limit:
                        break
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones de videos: {e}")
            return []

# =====================================================
# FUNCIONES DE UTILIDAD
# =====================================================

async def get_yml_video_integration_service(db: Session) -> YMLVideoIntegrationService:
    """Dependency para obtener el servicio de integración YML-Video"""
    return YMLVideoIntegrationService(db)


