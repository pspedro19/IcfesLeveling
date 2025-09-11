import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import json
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from app.models.youtube_catalog import YoutubeCatalog
from app.models.content_embeddings import ContentEmbeddings
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class IntelligentVideoMapper:
    """
    Servicio para mapeo inteligente entre preguntas ICFES y videos YouTube
    Combina criterios exactos (subject_id, topic_id) con búsqueda semántica (embeddings)
    """
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        
        # Weights para scoring multi-criterio
        self.scoring_weights = {
            'exact_match': 0.4,      # Match exacto de subject/topic
            'semantic_similarity': 0.3,  # Similaridad semántica
            'content_quality': 0.2,      # Calidad del video
            'engagement': 0.1           # Métricas de engagement
        }
        
        # Pesos para diferentes tipos de embedding
        self.embedding_weights = {
            'title': 0.3,
            'description': 0.2,
            'transcript': 0.4,
            'combined': 0.1
        }
        
        # Cache para resultados recientes
        self.recommendation_cache = {}
        self.cache_ttl = 3600  # 1 hora
    
    async def find_recommended_videos(
        self,
        db: Session,
        question_text: str,
        subject_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 10,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Encuentra videos recomendados para una pregunta específica usando embeddings
        """
        logger.info(f"Finding videos for question: {question_text[:100]}...")
        
        # Generar cache key
        cache_key = self._generate_cache_key(
            question_text, subject_id, topic_id, difficulty_level, limit
        )
        
        # Verificar cache
        if cache_key in self.recommendation_cache:
            cached_result = self.recommendation_cache[cache_key]
            if datetime.utcnow().timestamp() - cached_result['timestamp'] < self.cache_ttl:
                logger.info("Returning cached recommendation")
                return cached_result['recommendations']
        
        try:
            # 1. Generar embedding para la pregunta
            question_embedding = await self.embedding_service.generate_embedding(question_text)
            if not question_embedding:
                logger.warning("Could not generate embedding for question")
                return []
            
            # 2. Obtener candidatos iniciales con filtros básicos
            candidates = self._get_candidate_videos(
                db, subject_id, topic_id, difficulty_level
            )
            
            if not candidates:
                logger.warning("No candidate videos found")
                return []
            
            # 3. Calcular scores para cada candidato
            scored_videos = []
            for video in candidates:
                try:
                    score = await self._calculate_video_score(
                        db, video, question_embedding, question_text,
                        subject_id, topic_id, difficulty_level
                    )
                    
                    if score >= min_score:
                        scored_videos.append({
                            'video': video,
                            'score': score,
                            'score_breakdown': score  # TODO: Implementar breakdown detallado
                        })
                except Exception as e:
                    logger.error(f"Error scoring video {video.id}: {e}")
                    continue
            
            # 4. Ordenar por score y limitar resultados
            scored_videos.sort(key=lambda x: x['score'], reverse=True)
            top_videos = scored_videos[:limit]
            
            # 5. Formatear resultados
            recommendations = []
            for item in top_videos:
                video = item['video']
                recommendation = {
                    'video_id': video.id,
                    'youtube_id': video.youtube_id,
                    'title': video.title or video.tema_principal,
                    'description': video.description,
                    'channel_name': video.channel_name,
                    'url': video.get_watch_url(),
                    'embed_url': video.get_embed_url(),
                    'thumbnail_url': video.thumbnail_url,
                    'duration_seconds': video.duration_seconds,
                    'area_evaluada': video.area_evaluada,
                    'tema_principal': video.tema_principal,
                    'codigo_tema': video.codigo_tema,
                    'quality_score': video.quality_score,
                    'relevance_score': item['score'],
                    'match_reasons': self._get_match_reasons(
                        video, subject_id, topic_id, difficulty_level
                    )
                }
                recommendations.append(recommendation)
            
            # 6. Cache del resultado
            self.recommendation_cache[cache_key] = {
                'recommendations': recommendations,
                'timestamp': datetime.utcnow().timestamp()
            }
            
            logger.info(f"Found {len(recommendations)} recommended videos")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in video recommendation: {e}")
            return []
    
    def _get_candidate_videos(
        self,
        db: Session,
        subject_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        difficulty_level: Optional[str] = None,
        max_candidates: int = 100
    ) -> List[YoutubeCatalog]:
        """
        Obtiene videos candidatos usando filtros básicos
        """
        query = db.query(YoutubeCatalog).filter(
            YoutubeCatalog.has_embeddings == True,
            YoutubeCatalog.processing_status == 'completed'
        )
        
        # Filtros de coincidencia exacta (prioridad alta)
        exact_match_filters = []
        if subject_id:
            exact_match_filters.append(YoutubeCatalog.subject_id == subject_id)
        if topic_id:
            exact_match_filters.append(YoutubeCatalog.topic_id == topic_id)
        if difficulty_level:
            exact_match_filters.append(YoutubeCatalog.nivel == difficulty_level)
        
        # Primero buscar coincidencias exactas
        exact_matches = []
        if exact_match_filters:
            exact_query = query.filter(and_(*exact_match_filters))
            exact_matches = exact_query.order_by(
                YoutubeCatalog.quality_score.desc()
            ).limit(max_candidates // 2).all()
        
        # Luego buscar candidatos adicionales con criterios más flexibles
        additional_candidates = []
        if len(exact_matches) < max_candidates:
            flexible_query = query
            
            # Filtros flexibles
            if subject_id:
                # Incluir videos de la misma área pero diferentes topics
                flexible_query = flexible_query.filter(
                    YoutubeCatalog.subject_id == subject_id
                )
            
            # Excluir videos ya encontrados
            if exact_matches:
                exact_ids = [v.id for v in exact_matches]
                flexible_query = flexible_query.filter(
                    ~YoutubeCatalog.id.in_(exact_ids)
                )
            
            additional_candidates = flexible_query.order_by(
                YoutubeCatalog.quality_score.desc(),
                YoutubeCatalog.relevance_score.desc()
            ).limit(max_candidates - len(exact_matches)).all()
        
        candidates = exact_matches + additional_candidates
        logger.info(f"Found {len(exact_matches)} exact matches, {len(additional_candidates)} additional candidates")
        return candidates
    
    async def _calculate_video_score(
        self,
        db: Session,
        video: YoutubeCatalog,
        question_embedding: List[float],
        question_text: str,
        subject_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        difficulty_level: Optional[str] = None
    ) -> float:
        """
        Calcula score compuesto para un video específico
        """
        scores = {
            'exact_match': 0.0,
            'semantic_similarity': 0.0,
            'content_quality': 0.0,
            'engagement': 0.0
        }
        
        # 1. Score de coincidencia exacta
        exact_score = 0.0
        if subject_id and video.subject_id == subject_id:
            exact_score += 0.4
        if topic_id and video.topic_id == topic_id:
            exact_score += 0.4
        if difficulty_level and video.nivel == difficulty_level:
            exact_score += 0.2
        scores['exact_match'] = exact_score
        
        # 2. Score de similaridad semántica
        semantic_score = await self._calculate_semantic_similarity(
            db, video, question_embedding
        )
        scores['semantic_similarity'] = semantic_score
        
        # 3. Score de calidad del contenido
        quality_score = self._calculate_content_quality_score(video)
        scores['content_quality'] = quality_score
        
        # 4. Score de engagement
        engagement_score = self._calculate_engagement_score(video)
        scores['engagement'] = engagement_score
        
        # Calcular score final ponderado
        final_score = sum(
            scores[criterion] * weight 
            for criterion, weight in self.scoring_weights.items()
        )
        
        # Aplicar boost para coincidencias exactas
        if exact_score > 0.5:
            final_score *= 1.2  # 20% boost para coincidencias muy exactas
        
        return min(final_score, 1.0)  # Cap a 1.0
    
    async def _calculate_semantic_similarity(
        self,
        db: Session,
        video: YoutubeCatalog,
        question_embedding: List[float]
    ) -> float:
        """
        Calcula similaridad semántica entre pregunta y video usando pgvector
        """
        try:
            # Si pgvector está disponible, usar búsqueda vectorial nativa
            from app.models.content_embeddings import PGVECTOR_AVAILABLE
            
            if PGVECTOR_AVAILABLE:
                return await self._vector_similarity_search(db, video, question_embedding)
            else:
                return await self._manual_similarity_calculation(db, video, question_embedding)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    async def _vector_similarity_search(
        self,
        db: Session,
        video: YoutubeCatalog,
        question_embedding: List[float]
    ) -> float:
        """
        Búsqueda vectorial usando pgvector (más eficiente)
        """
        try:
            from pgvector.sqlalchemy import Vector
            
            # Query para obtener similaridades usando operadores pgvector
            query = text("""
                SELECT 
                    embedding_type,
                    1 - (embedding_vector <=> :question_vector) as similarity
                FROM content_embeddings
                WHERE content_type = 'youtube_video'
                    AND content_id = :video_id
                    AND is_active = 'true'
                ORDER BY embedding_vector <=> :question_vector
            """)
            
            result = db.execute(query, {
                'question_vector': question_embedding,
                'video_id': video.id
            })
            
            similarities = {}
            for row in result:
                similarities[row.embedding_type] = row.similarity
            
            return self._calculate_weighted_similarity(similarities)
            
        except Exception as e:
            logger.error(f"Error in vector similarity search: {e}")
            return await self._manual_similarity_calculation(db, video, question_embedding)
    
    async def _manual_similarity_calculation(
        self,
        db: Session,
        video: YoutubeCatalog,
        question_embedding: List[float]
    ) -> float:
        """
        Cálculo manual de similaridad (fallback)
        """
        video_embeddings = db.query(ContentEmbeddings).filter(
            and_(
                ContentEmbeddings.content_type == 'youtube_video',
                ContentEmbeddings.content_id == video.id,
                ContentEmbeddings.is_active == 'true'
            )
        ).all()
        
        if not video_embeddings:
            return 0.0
        
        # Calcular similaridad para cada tipo de embedding
        similarities = {}
        for embedding in video_embeddings:
            if embedding.embedding_vector:
                similarity = self._calculate_cosine_similarity(
                    question_embedding, embedding.embedding_vector
                )
                similarities[embedding.embedding_type] = similarity
        
        return self._calculate_weighted_similarity(similarities)
    
    def _calculate_weighted_similarity(self, similarities: Dict[str, float]) -> float:
        """
        Calcula score ponderado de similaridades
        """
        if not similarities:
            return 0.0
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for embedding_type, similarity in similarities.items():
            weight = self.embedding_weights.get(embedding_type, 0.1)
            weighted_score += similarity * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _calculate_cosine_similarity(
        self, 
        vector1: List[float], 
        vector2: List[float]
    ) -> float:
        """
        Calcula similaridad coseno entre dos vectores
        """
        try:
            import numpy as np
            
            v1 = np.array(vector1)
            v2 = np.array(vector2)
            
            # Calcular producto punto
            dot_product = np.dot(v1, v2)
            
            # Calcular normas
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Similaridad coseno
            similarity = dot_product / (norm1 * norm2)
            
            # Normalizar a rango [0, 1]
            return max(0.0, (similarity + 1.0) / 2.0)
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def _calculate_content_quality_score(self, video: YoutubeCatalog) -> float:
        """
        Calcula score de calidad del contenido
        """
        score = 0.0
        
        # Score base de calidad si está disponible
        if video.quality_score:
            score += video.quality_score * 0.4
        
        # Bonus por tener transcripción
        if video.transcript and len(video.transcript) > 100:
            score += 0.3
        
        # Bonus por descripción detallada
        if video.description and len(video.description) > 50:
            score += 0.2
        
        # Bonus por canal reconocido
        educational_channels = [
            'Khan Academy', 'Crash Course', 'TED-Ed', 'Academia Internet',
            'unProfesor', 'Es Ciencia', 'educatina'
        ]
        
        if video.channel_name:
            for channel in educational_channels:
                if channel.lower() in video.channel_name.lower():
                    score += 0.1
                    break
        
        return min(score, 1.0)
    
    def _calculate_engagement_score(self, video: YoutubeCatalog) -> float:
        """
        Calcula score basado en métricas de engagement
        """
        score = 0.0
        
        # View count normalizado (log scale)
        if video.view_count and video.view_count > 0:
            log_views = math.log10(video.view_count)
            normalized_views = min(log_views / 7.0, 1.0)  # Cap at 10M views
            score += normalized_views * 0.6
        
        # Like count si está disponible
        if video.like_count and video.like_count > 0:
            log_likes = math.log10(video.like_count)
            normalized_likes = min(log_likes / 5.0, 1.0)  # Cap at 100K likes
            score += normalized_likes * 0.4
        
        return score
    
    def _get_match_reasons(
        self,
        video: YoutubeCatalog,
        subject_id: Optional[int] = None,
        topic_id: Optional[int] = None,
        difficulty_level: Optional[str] = None
    ) -> List[str]:
        """
        Genera lista de razones por las cuales el video fue seleccionado
        """
        reasons = []
        
        if subject_id and video.subject_id == subject_id:
            reasons.append(f"Misma área: {video.area_evaluada}")
        
        if topic_id and video.topic_id == topic_id:
            reasons.append(f"Mismo tema: {video.tema_principal}")
        
        if difficulty_level and video.nivel == difficulty_level:
            reasons.append(f"Mismo nivel: {difficulty_level}")
        
        if video.transcript:
            reasons.append("Incluye transcripción")
        
        if video.quality_score and video.quality_score > 0.7:
            reasons.append("Alta calidad educativa")
        
        if video.channel_name:
            educational_channels = ['Khan Academy', 'Crash Course', 'TED-Ed', 'unProfesor']
            for channel in educational_channels:
                if channel.lower() in video.channel_name.lower():
                    reasons.append(f"Canal educativo: {video.channel_name}")
                    break
        
        return reasons
    
    def _generate_cache_key(
        self,
        question_text: str,
        subject_id: Optional[int],
        topic_id: Optional[int],
        difficulty_level: Optional[str],
        limit: int
    ) -> str:
        """
        Genera clave para cache de recomendaciones
        """
        import hashlib
        
        components = [
            question_text[:200],  # Truncar texto largo
            str(subject_id) if subject_id else "none",
            str(topic_id) if topic_id else "none",
            difficulty_level or "none",
            str(limit)
        ]
        
        key_string = "|".join(components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def clear_cache(self):
        """Limpia el cache de recomendaciones"""
        self.recommendation_cache.clear()
        logger.info("Recommendation cache cleared")
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Obtiene estadísticas del cache"""
        current_time = datetime.utcnow().timestamp()
        valid_entries = sum(
            1 for entry in self.recommendation_cache.values()
            if current_time - entry['timestamp'] < self.cache_ttl
        )
        
        return {
            'total_entries': len(self.recommendation_cache),
            'valid_entries': valid_entries,
            'expired_entries': len(self.recommendation_cache) - valid_entries
        }