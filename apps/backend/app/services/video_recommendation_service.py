"""
Servicio de Recomendaciones de Videos
Recomienda videos de YouTube basado en el rendimiento del usuario en tests diagnósticos
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..models.youtube_links import YouTubeLinks
from ..models.diagnostic_test import DiagnosticTest
import random

logger = logging.getLogger(__name__)

class VideoRecommendationService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_video_recommendations(
        self, 
        user_id: str, 
        topic_codes: List[str] = None,
        difficulty_level: int = None,
        content_type: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Obtener recomendaciones de videos basadas en criterios específicos
        
        Args:
            user_id: ID del usuario
            topic_codes: Lista de códigos de tema para filtrar
            difficulty_level: Nivel de dificultad (1-5)
            content_type: Tipo de contenido (explicativo, ejercicio_guiado, etc.)
            limit: Número máximo de videos a retornar
        
        Returns:
            Lista de videos recomendados
        """
        try:
            # Construir query base
            query = """
                SELECT * FROM youtube_links 
                WHERE estado = 'activo'
            """
            params = {}
            
            # Filtrar por códigos de tema si se especifican
            if topic_codes:
                placeholders = ','.join([f':topic_{i}' for i in range(len(topic_codes))])
                query += f" AND codigo_tema IN ({placeholders})"
                for i, topic in enumerate(topic_codes):
                    params[f'topic_{i}'] = topic
            
            # Filtrar por nivel de dificultad
            if difficulty_level:
                query += " AND nivel_dificultad = :difficulty"
                params['difficulty'] = difficulty_level
            
            # Filtrar por tipo de contenido
            if content_type:
                query += " AND tipo_contenido = :content_type"
                params['content_type'] = content_type
            
            # Ordenar por calidad y relevancia
            query += """
                ORDER BY 
                    calidad_score DESC, 
                    relevancia_score DESC,
                    orden_recomendacion ASC
                LIMIT :limit
            """
            params['limit'] = limit
            
            # Ejecutar query
            result = self.db.execute(text(query), params)
            videos = result.fetchall()
            
            # Convertir a diccionarios
            video_list = []
            for video in videos:
                video_dict = {
                    'id': str(video.id),
                    'codigo_tema': video.codigo_tema,
                    'area_evaluada': video.area_evaluada,
                    'tema_principal': video.tema_principal,
                    'canal_sugerido': video.canal_sugerido,
                    'youtube_url': video.youtube_url,
                    'youtube_id': video.youtube_id,
                    'video_title': video.video_title,
                    'channel_name': video.channel_name,
                    'duration_seconds': video.duration_seconds,
                    'tipo_contenido': video.tipo_contenido,
                    'nivel_dificultad': video.nivel_dificultad,
                    'proceso_cognitivo': video.proceso_cognitivo,
                    'calidad_score': float(video.calidad_score) if video.calidad_score else None,
                    'relevancia_score': float(video.relevancia_score) if video.relevancia_score else None,
                    'tiempo_estimado_estudio': video.tiempo_estimado_estudio,
                    'puntos_xp': video.puntos_xp
                }
                video_list.append(video_dict)
            
            logger.info(f"✅ {len(video_list)} videos recomendados para usuario {user_id}")
            return video_list
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo recomendaciones de videos: {e}")
            return []
    
    def get_personalized_video_recommendations(
        self, 
        user_id: str, 
        diagnostic_results: Dict,
        limit: int = 15
    ) -> Dict[str, List[Dict]]:
        """
        Obtener recomendaciones personalizadas basadas en resultados diagnósticos
        
        Args:
            user_id: ID del usuario
            diagnostic_results: Resultados del test diagnóstico
            limit: Número máximo de videos por categoría
        
        Returns:
            Diccionario con videos organizados por categoría
        """
        try:
            recommendations = {
                'fundamentals': [],      # Videos para temas críticos
                'weaknesses': [],       # Videos para debilidades
                'practice': [],         # Videos de práctica
                'advanced': []          # Videos avanzados
            }
            
            # Extraer información del diagnóstico
            weak_topics = diagnostic_results.get('weaknesses', [])
            strong_topics = diagnostic_results.get('strengths', [])
            overall_score = diagnostic_results.get('score_percentage', 0)
            
            # 1. Videos para fundamentos (temas críticos)
            if weak_topics:
                fundamental_videos = self.get_video_recommendations(
                    user_id=user_id,
                    topic_codes=weak_topics[:5],  # Top 5 temas débiles
                    difficulty_level=1,  # Nivel básico
                    content_type='explicativo',
                    limit=limit
                )
                recommendations['fundamentals'] = fundamental_videos
            
            # 2. Videos para debilidades (nivel intermedio)
            if weak_topics:
                weakness_videos = self.get_video_recommendations(
                    user_id=user_id,
                    topic_codes=weak_topics[:3],  # Top 3 temas débiles
                    difficulty_level=2,  # Nivel intermedio
                    content_type='ejercicio_guiado',
                    limit=limit
                )
                recommendations['weaknesses'] = weakness_videos
            
            # 3. Videos de práctica (mezcla de temas)
            practice_topics = weak_topics + strong_topics[:3]
            if practice_topics:
                practice_videos = self.get_video_recommendations(
                    user_id=user_id,
                    topic_codes=practice_topics[:5],
                    difficulty_level=3,  # Nivel intermedio
                    content_type='ejercicio_guiado',
                    limit=limit
                )
                recommendations['practice'] = practice_videos
            
            # 4. Videos avanzados (solo si el usuario tiene buen rendimiento)
            if overall_score >= 70 and strong_topics:
                advanced_videos = self.get_video_recommendations(
                    user_id=user_id,
                    topic_codes=strong_topics[:3],
                    difficulty_level=4,  # Nivel avanzado
                    content_type='resumen',
                    limit=limit
                )
                recommendations['advanced'] = advanced_videos
            
            logger.info(f"✅ Recomendaciones personalizadas generadas para usuario {user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"❌ Error generando recomendaciones personalizadas: {e}")
            return {
                'fundamentals': [],
                'weaknesses': [],
                'practice': [],
                'advanced': []
            }
    
    def get_video_by_topic(
        self, 
        topic_code: str, 
        difficulty_level: int = None,
        content_type: str = None
    ) -> Optional[Dict]:
        """
        Obtener un video específico para un tema
        
        Args:
            topic_code: Código del tema
            difficulty_level: Nivel de dificultad opcional
            content_type: Tipo de contenido opcional
        
        Returns:
            Video recomendado o None
        """
        try:
            videos = self.get_video_recommendations(
                user_id="system",
                topic_codes=[topic_code],
                difficulty_level=difficulty_level,
                content_type=content_type,
                limit=1
            )
            
            if videos:
                return videos[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo video para tema {topic_code}: {e}")
            return None
    
    def get_random_video_recommendation(
        self, 
        user_id: str,
        area_evaluada: str = None
    ) -> Optional[Dict]:
        """
        Obtener una recomendación aleatoria de video
        
        Args:
            user_id: ID del usuario
            area_evaluada: Área de evaluación opcional
        
        Returns:
            Video aleatorio o None
        """
        try:
            query = """
                SELECT * FROM youtube_links 
                WHERE estado = 'activo'
            """
            params = {}
            
            if area_evaluada:
                query += " AND area_evaluada = :area"
                params['area'] = area_evaluada
            
            query += """
                ORDER BY RANDOM()
                LIMIT 1
            """
            
            result = self.db.execute(text(query), params)
            video = result.fetchone()
            
            if video:
                return {
                    'id': str(video.id),
                    'codigo_tema': video.codigo_tema,
                    'area_evaluada': video.area_evaluada,
                    'tema_principal': video.tema_principal,
                    'youtube_url': video.youtube_url,
                    'youtube_id': video.youtube_id,
                    'video_title': video.video_title,
                    'channel_name': video.channel_name,
                    'duration_seconds': video.duration_seconds,
                    'puntos_xp': video.puntos_xp
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo video aleatorio: {e}")
            return None
    
    def get_video_playlist_for_study_plan(
        self, 
        user_id: str,
        study_plan: Dict,
        limit_per_unit: int = 5
    ) -> Dict[str, List[Dict]]:
        """
        Generar playlist de videos para un plan de estudio
        
        Args:
            user_id: ID del usuario
            study_plan: Plan de estudio
            limit_per_unit: Número máximo de videos por unidad
        
        Returns:
            Playlist organizada por unidades
        """
        try:
            playlist = {}
            
            if 'units' not in study_plan:
                return playlist
            
            for unit in study_plan['units']:
                unit_name = unit.get('name', 'Unidad')
                focus_topics = unit.get('focus_topics', [])
                
                if focus_topics:
                    unit_videos = self.get_video_recommendations(
                        user_id=user_id,
                        topic_codes=focus_topics[:3],  # Top 3 temas por unidad
                        difficulty_level=unit.get('difficulty_level', 3),
                        limit=limit_per_unit
                    )
                    
                    playlist[unit_name] = unit_videos
                else:
                    playlist[unit_name] = []
            
            logger.info(f"✅ Playlist generada para plan de estudio del usuario {user_id}")
            return playlist
            
        except Exception as e:
            logger.error(f"❌ Error generando playlist: {e}")
            return {}
