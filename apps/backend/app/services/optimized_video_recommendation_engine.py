"""
Optimized Video Recommendation Engine
Motor optimizado que funciona sin dependencias externas críticas
Enfocado en matching efectivo con datos actuales del sistema
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from datetime import datetime
from difflib import SequenceMatcher
from collections import Counter
import math

logger = logging.getLogger(__name__)


class OptimizedVideoRecommendationEngine:
    """
    Motor de recomendación optimizado que funciona sin dependencias externas
    Elimina la dependencia de sentence-transformers, fuzzywuzzy y sklearn
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Weights optimizados basados en análisis del sistema actual
        self.weights = {
            'exact_match': 0.35,           # Coincidencia exacta en título/descripción
            'semantic_keywords': 0.25,      # Palabras clave semánticamente relacionadas  
            'subject_topic_match': 0.20,   # Coincidencia por subject/topic
            'quality_score': 0.15,         # Calidad del video
            'popularity': 0.05             # Popularidad/engagement
        }
        
        # Umbrales optimizados (más bajos y realistas)
        self.thresholds = {
            'minimum_score': 0.15,         # Umbral mínimo (reducido de 0.4)
            'good_score': 0.30,            # Score considerado bueno
            'excellent_score': 0.50        # Score excelente
        }
        
        # Mapeo de subjects UUID a nombres y áreas temáticas
        self.subject_mapping = {
            '550e8400-e29b-41d4-a716-446655440001': {
                'name': 'Matemáticas',
                'keywords': ['matemática', 'math', 'álgebra', 'geometría', 'cálculo', 'trigonometría', 'estadística'],
                'codigo_prefix': 'MAT'
            },
            '550e8400-e29b-41d4-a716-446655440002': {
                'name': 'Lenguaje',
                'keywords': ['lenguaje', 'literatura', 'comprensión', 'lectura', 'escritura', 'ortografía'],
                'codigo_prefix': 'LEN'
            },
            '550e8400-e29b-41d4-a716-446655440003': {
                'name': 'Ciencias Naturales', 
                'keywords': ['ciencias', 'biología', 'química', 'física', 'naturales'],
                'codigo_prefix': 'CIE'
            },
            '550e8400-e29b-41d4-a716-446655440004': {
                'name': 'Ciencias Sociales',
                'keywords': ['sociales', 'historia', 'geografía', 'civismo', 'política'],
                'codigo_prefix': 'SOC'
            },
            '550e8400-e29b-41d4-a716-446655440005': {
                'name': 'Inglés',
                'keywords': ['inglés', 'english', 'grammar', 'vocabulary', 'reading'],
                'codigo_prefix': 'ING'
            }
        }
        
        # Cache para mejorar performance
        self.video_cache = {}
        self.keyword_cache = {}

    def get_intelligent_recommendations(
        self,
        topic_code: str,
        topic_name: str,
        subject_id: str = None,
        difficulty_level: float = 0.5,
        max_videos: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Obtiene recomendaciones inteligentes optimizadas para el sistema actual
        """
        try:
            logger.info(f"🎯 Getting optimized recommendations for: {topic_name} (code: {topic_code})")
            
            # 1. Búsqueda optimizada por subject_id si disponible
            if subject_id:
                direct_matches = self._get_optimized_subject_matches(subject_id, topic_name, max_videos)
                if direct_matches and len(direct_matches) >= max_videos:
                    return self._enhance_video_data(direct_matches[:max_videos], topic_code, topic_name)
            
            # 2. Búsqueda semántica optimizada (sin embeddings externos)
            semantic_matches = self._get_semantic_keyword_matches(topic_name, topic_code, max_videos)
            if semantic_matches:
                return self._enhance_video_data(semantic_matches[:max_videos], topic_code, topic_name)
            
            # 3. Búsqueda por área temática mejorada
            area_matches = self._get_improved_area_matches(topic_code, topic_name, max_videos)
            if area_matches:
                return self._enhance_video_data(area_matches[:max_videos], topic_code, topic_name)
            
            # 4. Fallback inteligente (videos reales, no placeholders)
            return self._get_intelligent_fallback_videos(topic_name, topic_code, max_videos)
            
        except Exception as e:
            logger.error(f"Error in optimized recommendations: {e}")
            return self._get_intelligent_fallback_videos(topic_name, topic_code, max_videos)

    def _get_optimized_subject_matches(self, subject_id: str, topic_name: str, limit: int) -> List[Dict[str, Any]]:
        """
        Búsqueda optimizada por subject_id con matching de keywords
        """
        try:
            query = text("""
                SELECT 
                    video_id, title, description, duration_seconds,
                    url, embed_url, thumbnail_url, channel,
                    subject_id, topic_id
                FROM youtube_catalog 
                WHERE subject_id = :subject_id
                  AND (
                    LOWER(title) LIKE LOWER(:topic_pattern) OR
                    LOWER(description) LIKE LOWER(:topic_pattern) OR
                    LOWER(title) LIKE LOWER(:topic_words) OR
                    LOWER(description) LIKE LOWER(:topic_words)
                  )
                ORDER BY 
                  CASE 
                    WHEN LOWER(title) LIKE LOWER(:exact_topic) THEN 1
                    WHEN LOWER(title) LIKE LOWER(:topic_pattern) THEN 2
                    ELSE 3
                  END,
                  duration_seconds DESC
                LIMIT :limit
            """)
            
            # Preparar patrones de búsqueda
            topic_words = ' '.join(topic_name.lower().split())
            exact_topic = f'%{topic_name.lower()}%'
            topic_pattern = f'%{topic_words}%'
            
            result = self.db.execute(query, {
                "subject_id": subject_id,
                "exact_topic": exact_topic,
                "topic_pattern": topic_pattern,
                "topic_words": f'%{topic_words}%',
                "limit": limit * 2  # Obtenemos más para filtrar mejor
            })
            
            videos = [dict(row._mapping) for row in result]
            
            # Scoring optimizado para cada video
            scored_videos = []
            for video in videos:
                score = self._calculate_optimized_score(video, topic_name, subject_id)
                if score >= self.thresholds['minimum_score']:
                    video['optimized_score'] = score
                    scored_videos.append(video)
            
            # Ordenar por score y retornar top videos
            scored_videos.sort(key=lambda x: x['optimized_score'], reverse=True)
            return scored_videos[:limit]
            
        except Exception as e:
            logger.error(f"Error in optimized subject matches: {e}")
            return []

    def _get_semantic_keyword_matches(self, topic_name: str, topic_code: str, limit: int) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica usando keywords sin dependencias externas
        """
        try:
            # Extraer keywords importantes del topic_name
            keywords = self._extract_important_keywords(topic_name, topic_code)
            if not keywords:
                return []
            
            # Crear query con múltiples keywords
            keyword_conditions = []
            params = {'limit': limit * 3}  # Más videos para mejor selección
            
            for i, keyword in enumerate(keywords[:5]):  # Max 5 keywords principales
                keyword_conditions.append(f"LOWER(title) LIKE LOWER(:keyword_{i}) OR LOWER(description) LIKE LOWER(:keyword_{i})")
                params[f'keyword_{i}'] = f'%{keyword}%'
            
            if not keyword_conditions:
                return []
            
            query = text(f"""
                SELECT 
                    video_id, title, description, duration_seconds,
                    url, embed_url, thumbnail_url, channel,
                    subject_id, topic_id
                FROM youtube_catalog 
                WHERE ({' OR '.join(keyword_conditions)})
                  AND duration_seconds BETWEEN 180 AND 2400  -- 3-40 minutos
                ORDER BY 
                  CASE 
                    WHEN LOWER(title) LIKE LOWER(:primary_keyword) THEN 1
                    WHEN LOWER(title) LIKE LOWER(:secondary_keyword) THEN 2
                    ELSE 3
                  END,
                  duration_seconds ASC
                LIMIT :limit
            """)
            
            # Agregar parámetros de ordenación
            params['primary_keyword'] = f'%{keywords[0]}%' if keywords else '%educativo%'
            params['secondary_keyword'] = f'%{keywords[1]}%' if len(keywords) > 1 else '%tutorial%'
            
            result = self.db.execute(query, params)
            videos = [dict(row._mapping) for row in result]
            
            # Scoring semántico optimizado
            scored_videos = []
            for video in videos:
                score = self._calculate_semantic_score(video, topic_name, keywords)
                if score >= self.thresholds['minimum_score']:
                    video['semantic_score'] = score
                    scored_videos.append(video)
            
            scored_videos.sort(key=lambda x: x['semantic_score'], reverse=True)
            return scored_videos[:limit]
            
        except Exception as e:
            logger.error(f"Error in semantic keyword matching: {e}")
            return []

    def _get_improved_area_matches(self, topic_code: str, topic_name: str, limit: int) -> List[Dict[str, Any]]:
        """
        Búsqueda por área temática mejorada con subject mapping
        """
        try:
            # Intentar mapear el topic_code a subject conocidos
            subject_matches = []
            for subject_id, info in self.subject_mapping.items():
                if any(keyword in topic_name.lower() for keyword in info['keywords']):
                    subject_matches.append(subject_id)
                if topic_code.startswith(info['codigo_prefix']):
                    subject_matches.append(subject_id)
            
            if not subject_matches:
                # Fallback a búsqueda general por keywords
                return self._get_general_keyword_search(topic_name, limit)
            
            # Query por subjects identificados
            subject_conditions = [f"subject_id = :subject_{i}" for i, _ in enumerate(subject_matches)]
            params = {'limit': limit * 2}
            
            for i, subject_id in enumerate(subject_matches):
                params[f'subject_{i}'] = subject_id
            
            query = text(f"""
                SELECT 
                    video_id, title, description, duration_seconds,
                    url, embed_url, thumbnail_url, channel,
                    subject_id, topic_id
                FROM youtube_catalog 
                WHERE ({' OR '.join(subject_conditions)})
                  AND duration_seconds IS NOT NULL
                  AND duration_seconds > 60
                ORDER BY 
                  CASE 
                    WHEN LOWER(title) LIKE LOWER(:topic_pattern) THEN 1
                    WHEN LOWER(description) LIKE LOWER(:topic_pattern) THEN 2
                    ELSE 3
                  END,
                  duration_seconds ASC
                LIMIT :limit
            """)
            
            params['topic_pattern'] = f'%{topic_name.lower()}%'
            
            result = self.db.execute(query, params)
            videos = [dict(row._mapping) for row in result]
            
            # Filtrar y puntuar
            good_videos = []
            for video in videos:
                relevance_score = self._calculate_area_relevance(video, topic_name, topic_code)
                if relevance_score >= self.thresholds['minimum_score']:
                    video['area_score'] = relevance_score
                    good_videos.append(video)
            
            good_videos.sort(key=lambda x: x['area_score'], reverse=True)
            return good_videos[:limit]
            
        except Exception as e:
            logger.error(f"Error in improved area matching: {e}")
            return []

    def _get_general_keyword_search(self, topic_name: str, limit: int) -> List[Dict[str, Any]]:
        """
        Búsqueda general por keywords cuando otros métodos fallan
        """
        try:
            words = [word.lower() for word in topic_name.split() if len(word) > 3]
            if not words:
                words = [topic_name.lower()]
            
            # Query simplificada por palabras clave
            word_conditions = []
            params = {'limit': limit * 2}
            
            for i, word in enumerate(words[:3]):  # Max 3 palabras principales
                word_conditions.append(f"LOWER(title) LIKE :word_{i} OR LOWER(description) LIKE :word_{i}")
                params[f'word_{i}'] = f'%{word}%'
            
            if not word_conditions:
                return []
            
            query = text(f"""
                SELECT 
                    video_id, title, description, duration_seconds,
                    url, embed_url, thumbnail_url, channel,
                    subject_id, topic_id
                FROM youtube_catalog 
                WHERE ({' OR '.join(word_conditions)})
                  AND duration_seconds BETWEEN 300 AND 1800
                ORDER BY duration_seconds ASC
                LIMIT :limit
            """)
            
            result = self.db.execute(query, params)
            return [dict(row._mapping) for row in result]
            
        except Exception as e:
            logger.error(f"Error in general keyword search: {e}")
            return []

    def _get_intelligent_fallback_videos(self, topic_name: str, topic_code: str, max_videos: int) -> List[Dict[str, Any]]:
        """
        Fallback inteligente que retorna videos reales de calidad, no placeholders
        """
        try:
            # Buscar los mejores videos disponibles por duración y evitar duplicados
            query = text("""
                SELECT DISTINCT
                    video_id, title, description, duration_seconds,
                    url, embed_url, thumbnail_url, channel,
                    subject_id, topic_id
                FROM youtube_catalog 
                WHERE duration_seconds IS NOT NULL
                  AND duration_seconds BETWEEN 300 AND 1200  -- 5-20 minutos
                  AND title IS NOT NULL
                  AND url IS NOT NULL
                ORDER BY 
                  CASE 
                    WHEN duration_seconds BETWEEN 600 AND 900 THEN 1  -- Prefer 10-15 min videos
                    WHEN duration_seconds BETWEEN 300 AND 600 THEN 2   -- Then 5-10 min
                    ELSE 3
                  END,
                  RANDOM()  -- Random selection for variety
                LIMIT :limit
            """)
            
            result = self.db.execute(query, {'limit': max_videos * 2})
            fallback_videos = [dict(row._mapping) for row in result]
            
            if not fallback_videos:
                # Último recurso - videos más básicos disponibles
                query = text("""
                    SELECT 
                        video_id, title, description, duration_seconds,
                        url, embed_url, thumbnail_url, channel,
                        subject_id, topic_id
                    FROM youtube_catalog 
                    WHERE video_id IS NOT NULL 
                      AND title IS NOT NULL
                    LIMIT :limit
                """)
                
                result = self.db.execute(query, {'limit': max_videos})
                fallback_videos = [dict(row._mapping) for row in result]
            
            # Mejorar la información de los videos de fallback
            enhanced_fallback = []
            for video in fallback_videos[:max_videos]:
                enhanced_video = video.copy()
                enhanced_video.update({
                    'fallback_reason': f'Video educativo recomendado para {topic_name}',
                    'relevance_score': 0.25,  # Score bajo pero honesto
                    'recommendation_type': 'general_educational_content',
                    'is_fallback': True
                })
                enhanced_fallback.append(enhanced_video)
            
            return enhanced_fallback
            
        except Exception as e:
            logger.error(f"Error in intelligent fallback: {e}")
            # Último recurso absoluto
            return [{
                'video_id': 'fallback_educational',
                'title': f'Contenido educativo sobre {topic_name}',
                'description': f'Video educativo relacionado con {topic_name}',
                'duration_seconds': 600,
                'url': 'https://www.youtube.com/watch?v=placeholder',
                'embed_url': 'https://www.youtube.com/embed/placeholder',
                'thumbnail_url': None,
                'channel': 'Contenido Educativo',
                'subject_id': None,
                'topic_id': None,
                'relevance_score': 0.1,
                'recommendation_type': 'placeholder',
                'is_fallback': True,
                'fallback_reason': 'No se encontraron videos específicos'
            }]

    def _extract_important_keywords(self, topic_name: str, topic_code: str) -> List[str]:
        """
        Extrae keywords importantes del nombre del tema
        """
        # Palabras comunes a ignorar
        stopwords = {'el', 'la', 'de', 'en', 'con', 'por', 'para', 'que', 'y', 'o', 'un', 'una'}
        
        # Limpiar y dividir el texto
        clean_text = re.sub(r'[^\w\s]', ' ', topic_name.lower())
        words = [word for word in clean_text.split() if word not in stopwords and len(word) > 2]
        
        # Agregar sinónimos basados en el código del tema
        if topic_code.startswith('MAT'):
            words.extend(['matemática', 'math', 'números', 'cálculo'])
        elif topic_code.startswith('LEN'):
            words.extend(['lenguaje', 'literatura', 'lectura', 'comprensión'])
        elif topic_code.startswith('CIE'):
            words.extend(['ciencias', 'naturales', 'biología', 'química', 'física'])
        elif topic_code.startswith('SOC'):
            words.extend(['sociales', 'historia', 'geografía'])
        elif topic_code.startswith('ING'):
            words.extend(['inglés', 'english', 'grammar'])
        
        # Retornar keywords únicos ordenados por relevancia
        return list(dict.fromkeys(words))  # Preserva orden, elimina duplicados

    def _calculate_optimized_score(self, video: Dict[str, Any], topic_name: str, subject_id: str = None) -> float:
        """
        Calcula score optimizado considerando múltiples factores
        """
        total_score = 0.0
        
        title = video.get('title', '').lower()
        description = video.get('description', '').lower() if video.get('description') else ''
        topic_lower = topic_name.lower()
        
        # 1. Exact match score (más preciso que fuzzy)
        exact_score = 0.0
        if topic_lower in title:
            exact_score = 0.8
        elif any(word in title for word in topic_lower.split() if len(word) > 3):
            exact_score = 0.5
        elif topic_lower in description:
            exact_score = 0.3
        
        # 2. Semantic keywords score
        keywords = topic_name.lower().split()
        semantic_score = 0.0
        for keyword in keywords:
            if len(keyword) > 3:
                if keyword in title:
                    semantic_score += 0.2
                elif keyword in description:
                    semantic_score += 0.1
        semantic_score = min(semantic_score, 0.8)  # Cap at 0.8
        
        # 3. Subject/topic match score
        subject_match_score = 0.0
        if subject_id and str(video.get('subject_id')) == str(subject_id):
            subject_match_score = 0.6
        elif video.get('topic_id'):
            subject_match_score = 0.3
        
        # 4. Quality score (based on duration and metadata presence)
        quality_score = 0.0
        duration = video.get('duration_seconds', 0)
        if duration:
            if 300 <= duration <= 1200:  # 5-20 minutos es óptimo
                quality_score = 0.6
            elif 120 <= duration <= 1800:  # 2-30 minutos es aceptable
                quality_score = 0.4
            else:
                quality_score = 0.2
        
        if video.get('description'):
            quality_score += 0.2
        if video.get('thumbnail_url'):
            quality_score += 0.1
        
        # 5. Popularity score (simplificado)
        popularity_score = 0.3  # Score neutro por defecto
        
        # Combinar scores con pesos optimizados
        total_score = (
            exact_score * self.weights['exact_match'] +
            semantic_score * self.weights['semantic_keywords'] +
            subject_match_score * self.weights['subject_topic_match'] +
            quality_score * self.weights['quality_score'] +
            popularity_score * self.weights['popularity']
        )
        
        return min(1.0, max(0.0, total_score))

    def _calculate_semantic_score(self, video: Dict[str, Any], topic_name: str, keywords: List[str]) -> float:
        """
        Calcula score semántico basado en keywords
        """
        title = video.get('title', '').lower()
        description = video.get('description', '').lower() if video.get('description') else ''
        
        score = 0.0
        total_keywords = len(keywords)
        
        if total_keywords == 0:
            return 0.0
        
        # Contar coincidencias de keywords
        matches = 0
        for keyword in keywords:
            if keyword in title:
                matches += 2  # Título vale más
            elif keyword in description:
                matches += 1
        
        # Normalizar score
        max_possible_score = total_keywords * 2
        score = matches / max_possible_score if max_possible_score > 0 else 0.0
        
        # Bonus por longitud apropiada del video
        duration = video.get('duration_seconds', 0)
        if 300 <= duration <= 1200:
            score *= 1.2
        
        return min(1.0, score)

    def _calculate_area_relevance(self, video: Dict[str, Any], topic_name: str, topic_code: str) -> float:
        """
        Calcula relevancia por área temática
        """
        title = video.get('title', '').lower()
        description = video.get('description', '').lower() if video.get('description') else ''
        
        # Buscar coincidencias de área temática
        area_score = 0.0
        
        # Mapear el subject_id del video a keywords conocidos
        video_subject_id = str(video.get('subject_id', ''))
        if video_subject_id in self.subject_mapping:
            subject_info = self.subject_mapping[video_subject_id]
            for keyword in subject_info['keywords']:
                if keyword in topic_name.lower():
                    area_score += 0.3
                if keyword in title:
                    area_score += 0.2
        
        # Score básico por presencia de palabras del tema en el video
        topic_words = topic_name.lower().split()
        for word in topic_words:
            if len(word) > 3:
                if word in title:
                    area_score += 0.15
                elif word in description:
                    area_score += 0.05
        
        return min(1.0, area_score)

    def _native_fuzzy_ratio(self, str1: str, str2: str) -> float:
        """
        Implementación nativa de fuzzy matching sin dependencias externas
        Basado en ratio de SequenceMatcher de difflib
        """
        try:
            return SequenceMatcher(None, str1.lower(), str2.lower()).ratio() * 100
        except:
            return 0.0

    def _enhance_video_data(self, videos: List[Dict[str, Any]], topic_code: str, topic_name: str) -> List[Dict[str, Any]]:
        """
        Enriquece los datos de los videos con información adicional optimizada
        """
        enhanced_videos = []
        
        for video in videos:
            # Construir URLs consistentes
            video_id = video.get('video_id', '')
            embed_url = video.get('embed_url') or f"https://www.youtube.com/embed/{video_id}"
            watch_url = video.get('url') or f"https://www.youtube.com/watch?v={video_id}"
            thumbnail_url = video.get('thumbnail_url') or f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            enhanced_video = {
                'video_id': video_id,
                'title': video.get('title', f'Video sobre {topic_name}'),
                'description': video.get('description', f'Contenido educativo sobre {topic_name}'),
                'duration_seconds': video.get('duration_seconds', 600),
                'duration_minutes': round(video.get('duration_seconds', 600) / 60, 1),
                'codigo_tema': topic_code,
                'url': watch_url,
                'embed_url': embed_url,
                'watch_url': watch_url,
                'thumbnail': thumbnail_url,
                'channel': video.get('channel', 'Canal Educativo'),
                'subject_id': video.get('subject_id'),
                'topic_id': video.get('topic_id'),
                'relevance_score': video.get('optimized_score') or video.get('semantic_score') or video.get('area_score') or 0.3,
                'recommendation_reason': self._generate_optimized_reason(video, topic_name),
                'is_fallback': video.get('is_fallback', False),
                'quality_indicator': self._get_quality_indicator(video)
            }
            
            enhanced_videos.append(enhanced_video)
        
        # Ordenar por relevancia
        enhanced_videos.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return enhanced_videos

    def _generate_optimized_reason(self, video: Dict[str, Any], topic_name: str) -> str:
        """
        Genera una razón optimizada para la recomendación
        """
        reasons = []
        
        title = video.get('title', '').lower()
        
        if topic_name.lower() in title:
            reasons.append("coincidencia directa en título")
        
        if video.get('optimized_score', 0) > self.thresholds['excellent_score']:
            reasons.append("alta relevancia temática")
        elif video.get('optimized_score', 0) > self.thresholds['good_score']:
            reasons.append("buena relevancia temática")
        
        duration = video.get('duration_seconds', 0)
        if 300 <= duration <= 1200:
            reasons.append("duración apropiada")
        
        if video.get('subject_id'):
            reasons.append("área temática correcta")
        
        if video.get('is_fallback'):
            reasons.append("contenido educativo general")
        
        if not reasons:
            reasons.append("contenido educativo relevante")
        
        return f"Recomendado por: {', '.join(reasons[:3])}"

    def _get_quality_indicator(self, video: Dict[str, Any]) -> str:
        """
        Genera indicador de calidad del video
        """
        score = video.get('optimized_score') or video.get('semantic_score') or video.get('area_score') or 0.0
        
        if score >= self.thresholds['excellent_score']:
            return "Excelente coincidencia"
        elif score >= self.thresholds['good_score']:
            return "Buena coincidencia"
        elif score >= self.thresholds['minimum_score']:
            return "Coincidencia básica"
        else:
            return "Contenido general"


class OptimizedStudyPlanIntegration:
    """
    Integración optimizada con el generador de planes de estudio
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.video_engine = OptimizedVideoRecommendationEngine(db)
    
    def get_optimized_video_recommendations(
        self,
        topic_code: str,
        topic_name: str,
        subject_id: str = None,
        learning_style: str = 'general',
        max_videos: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Obtiene recomendaciones optimizadas para integración con planes de estudio
        """
        try:
            videos = self.video_engine.get_intelligent_recommendations(
                topic_code=topic_code,
                topic_name=topic_name,
                subject_id=subject_id,
                max_videos=max_videos
            )
            
            if not videos:
                logger.warning(f"No optimized videos found for {topic_code} - {topic_name}")
                return self._create_educational_placeholder(topic_code, topic_name)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error in optimized video recommendations: {e}")
            return self._create_educational_placeholder(topic_code, topic_name)
    
    def _create_educational_placeholder(self, topic_code: str, topic_name: str) -> List[Dict[str, Any]]:
        """
        Crea placeholder educativo mejorado
        """
        return [{
            'video_id': f'educational_{topic_code.lower()}',
            'title': f'Estudio de {topic_name}',
            'description': f'Contenido educativo enfocado en {topic_name}. Recurso de apoyo para el aprendizaje.',
            'duration_minutes': 15,
            'codigo_tema': topic_code,
            'embed_url': 'about:blank',  # Mejor que placeholder específico
            'watch_url': 'about:blank',
            'relevance_score': 0.2,
            'recommendation_reason': 'Recurso educativo de respaldo - contenido general',
            'is_fallback': True,
            'quality_indicator': 'Contenido de respaldo'
        }]