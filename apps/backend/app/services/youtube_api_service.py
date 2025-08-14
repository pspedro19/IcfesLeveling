"""
YouTube Data API v3 Service
Servicio para interactuar con la YouTube Data API v3
Implementa gestión de cuota, caché y manejo de errores
"""

import os
import logging
import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import hashlib

logger = logging.getLogger(__name__)

class YouTubeAPIService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.base_url = 'https://www.googleapis.com/youtube/v3'
        self.redis_client = self._setup_redis()
        
        # Configuración de cuota (unidades por día)
        self.daily_quota_limit = 10000
        self.current_quota_usage = 0
        
        # Costos de API por operación
        self.api_costs = {
            'search.list': 100,
            'videos.list': 1,
            'playlistItems.list': 1,
            'channels.list': 1
        }
        
        if not self.api_key:
            logger.warning("⚠️ YouTube API Key no configurada. Algunas funciones pueden no funcionar.")
    
    def _setup_redis(self) -> Optional[redis.Redis]:
        """Configurar cliente Redis para caché"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            return redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.warning(f"⚠️ No se pudo conectar a Redis: {e}")
            return None
    
    def _get_cache_key(self, operation: str, params: Dict) -> str:
        """Generar clave de caché única"""
        param_str = json.dumps(params, sort_keys=True)
        return f"youtube_api:{operation}:{hashlib.md5(param_str.encode()).hexdigest()}"
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Obtener respuesta desde caché"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Error obteniendo caché: {e}")
        
        return None
    
    def _set_cached_response(self, cache_key: str, data: Dict, ttl: int = 3600):
        """Guardar respuesta en caché"""
        if not self.redis_client:
            return
        
        try:
            self.redis_client.setex(cache_key, ttl, json.dumps(data))
        except Exception as e:
            logger.warning(f"Error guardando caché: {e}")
    
    def _check_quota(self, operation: str) -> bool:
        """Verificar si hay cuota disponible"""
        cost = self.api_costs.get(operation, 100)
        
        # En producción, esto debería consultar una base de datos
        # Por ahora, simulamos el control de cuota
        if self.current_quota_usage + cost > self.daily_quota_limit:
            logger.warning(f"⚠️ Cuota diaria excedida. Operación: {operation}")
            return False
        
        self.current_quota_usage += cost
        return True
    
    def _make_api_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """Realizar petición a la YouTube API"""
        if not self.api_key:
            logger.error("❌ YouTube API Key no configurada")
            return None
        
        params['key'] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Verificar errores de la API
            if 'error' in data:
                error = data['error']
                logger.error(f"❌ YouTube API Error: {error.get('message', 'Unknown error')}")
                return None
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en petición a YouTube API: {e}")
            return None
    
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información detallada de un video
        Costo: 1 unidad
        """
        cache_key = self._get_cache_key('videos.list', {'id': video_id})
        
        # Verificar caché
        cached = self._get_cached_response(cache_key)
        if cached:
            logger.info(f"✅ Video info obtenida desde caché: {video_id}")
            return cached
        
        # Verificar cuota
        if not self._check_quota('videos.list'):
            return None
        
        params = {
            'part': 'snippet,statistics,contentDetails',
            'id': video_id
        }
        
        data = self._make_api_request('videos', params)
        if not data or 'items' not in data or not data['items']:
            return None
        
        video_info = data['items'][0]
        snippet = video_info.get('snippet', {})
        statistics = video_info.get('statistics', {})
        content_details = video_info.get('contentDetails', {})
        
        # Parsear duración ISO 8601
        duration = self._parse_duration(content_details.get('duration', 'PT0S'))
        
        result = {
            'video_id': video_id,
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'channel_id': snippet.get('channelId', ''),
            'channel_title': snippet.get('channelTitle', ''),
            'published_at': snippet.get('publishedAt', ''),
            'duration_seconds': duration,
            'view_count': int(statistics.get('viewCount', 0)),
            'like_count': int(statistics.get('likeCount', 0)),
            'comment_count': int(statistics.get('commentCount', 0)),
            'thumbnail_url': snippet.get('thumbnails', {}).get('maxres', {}).get('url', ''),
            'tags': snippet.get('tags', []),
            'category_id': snippet.get('categoryId', ''),
            'default_language': snippet.get('defaultLanguage', ''),
            'default_audio_language': snippet.get('defaultAudioLanguage', '')
        }
        
        # Guardar en caché por 1 hora
        self._set_cached_response(cache_key, result, 3600)
        
        logger.info(f"✅ Video info obtenida de API: {video_id}")
        return result
    
    def search_videos(self, query: str, max_results: int = 10, 
                     relevance_language: str = 'es', 
                     video_duration: str = 'medium',
                     video_definition: str = 'high') -> List[Dict[str, Any]]:
        """
        Buscar videos en YouTube
        Costo: 100 unidades
        """
        cache_key = self._get_cache_key('search.list', {
            'q': query, 'maxResults': max_results, 'relevanceLanguage': relevance_language
        })
        
        # Verificar caché
        cached = self._get_cached_response(cache_key)
        if cached:
            logger.info(f"✅ Búsqueda obtenida desde caché: {query}")
            return cached
        
        # Verificar cuota
        if not self._check_quota('search.list'):
            return []
        
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': min(max_results, 50),  # Máximo 50 por petición
            'relevanceLanguage': relevance_language,
            'videoDuration': video_duration,
            'videoDefinition': video_definition,
            'order': 'relevance'
        }
        
        data = self._make_api_request('search', params)
        if not data or 'items' not in data:
            return []
        
        videos = []
        for item in data['items']:
            snippet = item.get('snippet', {})
            video_info = {
                'video_id': item.get('id', {}).get('videoId', ''),
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                'tags': snippet.get('tags', [])
            }
            videos.append(video_info)
        
        # Guardar en caché por 1 hora
        self._set_cached_response(cache_key, videos, 3600)
        
        logger.info(f"✅ Búsqueda completada: {len(videos)} videos encontrados")
        return videos
    
    def get_playlist_videos(self, playlist_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Obtener videos de una playlist
        Costo: 1 unidad por página
        """
        cache_key = self._get_cache_key('playlistItems.list', {
            'playlistId': playlist_id, 'maxResults': max_results
        })
        
        # Verificar caché
        cached = self._get_cached_response(cache_key)
        if cached:
            logger.info(f"✅ Playlist obtenida desde caché: {playlist_id}")
            return cached
        
        # Verificar cuota
        if not self._check_quota('playlistItems.list'):
            return []
        
        params = {
            'part': 'snippet',
            'playlistId': playlist_id,
            'maxResults': min(max_results, 50)
        }
        
        data = self._make_api_request('playlistItems', params)
        if not data or 'items' not in data:
            return []
        
        videos = []
        for item in data['items']:
            snippet = item.get('snippet', {})
            video_info = {
                'video_id': snippet.get('resourceId', {}).get('videoId', ''),
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'channel_id': snippet.get('channelId', ''),
                'channel_title': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail_url': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                'position': snippet.get('position', 0)
            }
            videos.append(video_info)
        
        # Guardar en caché por 2 horas (playlists cambian menos)
        self._set_cached_response(cache_key, videos, 7200)
        
        logger.info(f"✅ Playlist obtenida: {len(videos)} videos")
        return videos
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información de un canal
        Costo: 1 unidad
        """
        cache_key = self._get_cache_key('channels.list', {'id': channel_id})
        
        # Verificar caché
        cached = self._get_cached_response(cache_key)
        if cached:
            logger.info(f"✅ Channel info obtenida desde caché: {channel_id}")
            return cached
        
        # Verificar cuota
        if not self._check_quota('channels.list'):
            return None
        
        params = {
            'part': 'snippet,statistics',
            'id': channel_id
        }
        
        data = self._make_api_request('channels', params)
        if not data or 'items' not in data or not data['items']:
            return None
        
        channel_info = data['items'][0]
        snippet = channel_info.get('snippet', {})
        statistics = channel_info.get('statistics', {})
        
        result = {
            'channel_id': channel_id,
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'custom_url': snippet.get('customUrl', ''),
            'published_at': snippet.get('publishedAt', ''),
            'thumbnail_url': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
            'banner_url': snippet.get('thumbnails', {}).get('banner', {}).get('url', ''),
            'subscriber_count': int(statistics.get('subscriberCount', 0)),
            'video_count': int(statistics.get('videoCount', 0)),
            'view_count': int(statistics.get('viewCount', 0)),
            'country': snippet.get('country', ''),
            'default_language': snippet.get('defaultLanguage', '')
        }
        
        # Guardar en caché por 24 horas (canales cambian poco)
        self._set_cached_response(cache_key, result, 86400)
        
        logger.info(f"✅ Channel info obtenida: {channel_id}")
        return result
    
    def _parse_duration(self, duration: str) -> int:
        """Parsear duración ISO 8601 a segundos"""
        import re
        
        if not duration:
            return 0
        
        # Patrón: PT1H2M3S
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def update_youtube_links_metadata(self) -> Dict[str, Any]:
        """
        Actualizar metadata de videos en la tabla youtube_links
        """
        if not self.api_key:
            return {'success': False, 'error': 'YouTube API Key no configurada'}
        
        try:
            # Obtener videos sin metadata
            result = self.db.execute(text("""
                SELECT id, youtube_url, youtube_id 
                FROM youtube_links 
                WHERE (video_title IS NULL OR duration_seconds IS NULL)
                AND youtube_url IS NOT NULL
                AND estado = 'activo'
                LIMIT 50
            """))
            
            videos_to_update = result.fetchall()
            updated_count = 0
            errors = []
            
            for video in videos_to_update:
                try:
                    video_id = video.youtube_id
                    if not video_id:
                        # Extraer ID de la URL
                        video_id = self._extract_video_id(video.youtube_url)
                        if not video_id:
                            continue
                    
                    # Obtener metadata
                    metadata = self.get_video_info(video_id)
                    if not metadata:
                        continue
                    
                    # Actualizar en base de datos
                    self.db.execute(text("""
                        UPDATE youtube_links 
                        SET 
                            video_title = :title,
                            channel_name = :channel_title,
                            channel_id = :channel_id,
                            duration_seconds = :duration,
                            view_count = :view_count,
                            like_count = :like_count,
                            comment_count = :comment_count,
                            updated_at = NOW()
                        WHERE id = :video_id
                    """), {
                        'title': metadata['title'],
                        'channel_title': metadata['channel_title'],
                        'channel_id': metadata['channel_id'],
                        'duration': metadata['duration_seconds'],
                        'view_count': metadata['view_count'],
                        'like_count': metadata['like_count'],
                        'comment_count': metadata['comment_count'],
                        'video_id': video.id
                    })
                    
                    updated_count += 1
                    logger.info(f"✅ Metadata actualizada para video: {video_id}")
                    
                except Exception as e:
                    errors.append(f"Error actualizando video {video.youtube_url}: {str(e)}")
            
            self.db.commit()
            
            return {
                'success': True,
                'updated_count': updated_count,
                'errors': errors,
                'quota_used': self.current_quota_usage
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Error actualizando metadata: {e}")
            return {'success': False, 'error': str(e)}
    
    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extraer ID del video de diferentes formatos de URL"""
        import re
        
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/v\/([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def get_quota_status(self) -> Dict[str, Any]:
        """Obtener estado actual de la cuota"""
        return {
            'daily_limit': self.daily_quota_limit,
            'current_usage': self.current_quota_usage,
            'remaining': self.daily_quota_limit - self.current_quota_usage,
            'usage_percentage': (self.current_quota_usage / self.daily_quota_limit) * 100
        }
