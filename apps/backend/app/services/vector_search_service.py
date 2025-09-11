import logging
from typing import List, Dict, Optional, Tuple, Any
import numpy as np
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from app.models.youtube_catalog import YoutubeCatalog
from app.models.content_embeddings import ContentEmbeddings

logger = logging.getLogger(__name__)

class VectorSearchService:
    """
    Servicio especializado para búsqueda vectorial con scoring multi-criterio
    Implementa búsquedas eficientes usando pgvector cuando está disponible
    """
    
    def __init__(self):
        # Detectar si pgvector está disponible
        try:
            from pgvector.sqlalchemy import Vector
            self.pgvector_available = True
            logger.info("pgvector extension available - using native vector operations")
        except ImportError:
            self.pgvector_available = False
            logger.warning("pgvector not available - using fallback similarity calculations")
        
        # Configuración de búsqueda
        self.similarity_threshold = 0.3
        self.max_results = 100
        
        # Weights para diferentes tipos de contenido
        self.content_type_weights = {
            'title': 0.3,
            'description': 0.2,
            'transcript': 0.4,
            'combined': 0.1
        }
        
        # Métricas de performance
        self.search_stats = {
            'total_searches': 0,
            'vector_searches': 0,
            'fallback_searches': 0,
            'avg_search_time_ms': 0
        }
    
    async def vector_similarity_search(
        self,
        db: Session,
        query_embedding: List[float],
        content_type: str = 'youtube_video',
        embedding_types: Optional[List[str]] = None,
        similarity_threshold: float = None,
        limit: int = 50,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda de similaridad vectorial optimizada
        """
        start_time = datetime.utcnow()
        threshold = similarity_threshold or self.similarity_threshold
        
        try:
            if self.pgvector_available:
                results = await self._pgvector_search(
                    db, query_embedding, content_type, embedding_types,
                    threshold, limit, filters
                )
                self.search_stats['vector_searches'] += 1
            else:
                results = await self._fallback_search(
                    db, query_embedding, content_type, embedding_types,
                    threshold, limit, filters
                )
                self.search_stats['fallback_searches'] += 1
            
            # Actualizar estadísticas
            search_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.search_stats['total_searches'] += 1
            self.search_stats['avg_search_time_ms'] = (
                (self.search_stats['avg_search_time_ms'] * (self.search_stats['total_searches'] - 1) + search_time)
                / self.search_stats['total_searches']
            )
            
            logger.info(f"Vector search completed in {search_time:.2f}ms - found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector similarity search: {e}")
            return []
    
    async def _pgvector_search(
        self,
        db: Session,
        query_embedding: List[float],
        content_type: str,
        embedding_types: Optional[List[str]],
        threshold: float,
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda usando pgvector (más eficiente)
        """
        try:
            # Construir query SQL optimizada con pgvector
            base_query = """
                SELECT 
                    ce.content_id,
                    ce.embedding_type,
                    1 - (ce.embedding_vector <=> :query_vector) as similarity_score,
                    ce.subject_area,
                    ce.topic,
                    ce.difficulty_level,
                    ce.confidence_score,
                    yc.youtube_id,
                    yc.title,
                    yc.description,
                    yc.area_evaluada,
                    yc.tema_principal,
                    yc.quality_score,
                    yc.view_count
                FROM content_embeddings ce
                JOIN youtube_catalog yc ON ce.content_id = yc.id
                WHERE ce.content_type = :content_type
                    AND ce.is_active = 'true'
                    AND yc.has_embeddings = true
                    AND yc.processing_status = 'completed'
                    AND (1 - (ce.embedding_vector <=> :query_vector)) >= :threshold
            """
            
            params = {
                'query_vector': query_embedding,
                'content_type': content_type,
                'threshold': threshold
            }
            
            # Filtros adicionales
            if embedding_types:
                placeholders = ','.join([f"':embedding_type_{i}'" for i in range(len(embedding_types))])
                base_query += f" AND ce.embedding_type IN ({placeholders})"
                for i, et in enumerate(embedding_types):
                    params[f'embedding_type_{i}'] = et
            
            if filters:
                if 'subject_area' in filters:
                    base_query += " AND ce.subject_area = :subject_area"
                    params['subject_area'] = filters['subject_area']
                
                if 'difficulty_level' in filters:
                    base_query += " AND ce.difficulty_level = :difficulty_level"
                    params['difficulty_level'] = filters['difficulty_level']
                
                if 'min_quality_score' in filters:
                    base_query += " AND yc.quality_score >= :min_quality_score"
                    params['min_quality_score'] = filters['min_quality_score']
            
            # Ordenar por similaridad y limitar
            base_query += """
                ORDER BY similarity_score DESC, yc.quality_score DESC
                LIMIT :limit
            """
            params['limit'] = limit
            
            # Ejecutar query
            result = db.execute(text(base_query), params)
            rows = result.fetchall()
            
            # Procesar resultados
            return self._process_search_results(rows)
            
        except Exception as e:
            logger.error(f"Error in pgvector search: {e}")
            # Fallback a búsqueda manual
            return await self._fallback_search(
                db, query_embedding, content_type, embedding_types,
                threshold, limit, filters
            )
    
    async def _fallback_search(
        self,
        db: Session,
        query_embedding: List[float],
        content_type: str,
        embedding_types: Optional[List[str]],
        threshold: float,
        limit: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda fallback usando cálculo manual de similaridad
        """
        try:
            # Query para obtener embeddings candidatos
            query = db.query(ContentEmbeddings, YoutubeCatalog).join(
                YoutubeCatalog, ContentEmbeddings.content_id == YoutubeCatalog.id
            ).filter(
                and_(
                    ContentEmbeddings.content_type == content_type,
                    ContentEmbeddings.is_active == 'true',
                    YoutubeCatalog.has_embeddings == True,
                    YoutubeCatalog.processing_status == 'completed'
                )
            )
            
            # Aplicar filtros
            if embedding_types:
                query = query.filter(ContentEmbeddings.embedding_type.in_(embedding_types))
            
            if filters:
                if 'subject_area' in filters:
                    query = query.filter(ContentEmbeddings.subject_area == filters['subject_area'])
                if 'difficulty_level' in filters:
                    query = query.filter(ContentEmbeddings.difficulty_level == filters['difficulty_level'])
                if 'min_quality_score' in filters:
                    query = query.filter(YoutubeCatalog.quality_score >= filters['min_quality_score'])
            
            candidates = query.limit(1000).all()  # Limitar candidatos para performance
            
            # Calcular similaridades manualmente
            scored_results = []
            for embedding, video in candidates:
                if not embedding.embedding_vector:
                    continue
                
                similarity = self._calculate_cosine_similarity(
                    query_embedding, embedding.embedding_vector
                )
                
                if similarity >= threshold:
                    scored_results.append({
                        'content_id': video.id,
                        'embedding_type': embedding.embedding_type,
                        'similarity_score': similarity,
                        'subject_area': embedding.subject_area,
                        'topic': embedding.topic,
                        'difficulty_level': embedding.difficulty_level,
                        'confidence_score': embedding.confidence_score,
                        'youtube_id': video.youtube_id,
                        'title': video.title,
                        'description': video.description,
                        'area_evaluada': video.area_evaluada,
                        'tema_principal': video.tema_principal,
                        'quality_score': video.quality_score,
                        'view_count': video.view_count
                    })
            
            # Ordenar por similaridad
            scored_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            return scored_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in fallback search: {e}")
            return []
    
    def _process_search_results(self, rows) -> List[Dict[str, Any]]:
        """
        Procesa los resultados de la búsqueda vectorial
        """
        results = []
        
        for row in rows:
            result = {
                'content_id': row.content_id,
                'embedding_type': row.embedding_type,
                'similarity_score': float(row.similarity_score),
                'subject_area': row.subject_area,
                'topic': row.topic,
                'difficulty_level': row.difficulty_level,
                'confidence_score': float(row.confidence_score) if row.confidence_score else None,
                'youtube_id': row.youtube_id,
                'title': row.title,
                'description': row.description,
                'area_evaluada': row.area_evaluada,
                'tema_principal': row.tema_principal,
                'quality_score': float(row.quality_score) if row.quality_score else None,
                'view_count': row.view_count
            }
            results.append(result)
        
        return results
    
    def _calculate_cosine_similarity(
        self, 
        vector1: List[float], 
        vector2: List[float]
    ) -> float:
        """
        Calcula similaridad coseno entre dos vectores
        """
        try:
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
    
    async def multi_criteria_search(
        self,
        db: Session,
        query_embedding: List[float],
        exact_match_criteria: Optional[Dict[str, Any]] = None,
        semantic_weight: float = 0.6,
        exact_match_weight: float = 0.4,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda multi-criterio combinando similaridad semántica y coincidencias exactas
        """
        try:
            # 1. Búsqueda vectorial semántica
            semantic_results = await self.vector_similarity_search(
                db=db,
                query_embedding=query_embedding,
                limit=limit * 2,  # Obtener más candidatos
                filters=exact_match_criteria
            )
            
            # 2. Aplicar scoring multi-criterio
            final_results = []
            
            for result in semantic_results:
                # Score semántico (ya calculado)
                semantic_score = result['similarity_score']
                
                # Score de coincidencia exacta
                exact_score = self._calculate_exact_match_score(
                    result, exact_match_criteria or {}
                )
                
                # Score combinado
                combined_score = (
                    semantic_score * semantic_weight +
                    exact_score * exact_match_weight
                )
                
                result['exact_match_score'] = exact_score
                result['combined_score'] = combined_score
                final_results.append(result)
            
            # Ordenar por score combinado
            final_results.sort(key=lambda x: x['combined_score'], reverse=True)
            
            return final_results[:limit]
            
        except Exception as e:
            logger.error(f"Error in multi-criteria search: {e}")
            return []
    
    def _calculate_exact_match_score(
        self,
        result: Dict[str, Any],
        criteria: Dict[str, Any]
    ) -> float:
        """
        Calcula score de coincidencia exacta basado en criterios
        """
        score = 0.0
        total_criteria = len(criteria) if criteria else 1
        
        if not criteria:
            return 0.0
        
        # Verificar coincidencias
        if 'subject_area' in criteria and result.get('subject_area') == criteria['subject_area']:
            score += 1.0 / total_criteria
        
        if 'difficulty_level' in criteria and result.get('difficulty_level') == criteria['difficulty_level']:
            score += 1.0 / total_criteria
        
        if 'topic' in criteria and result.get('topic') == criteria['topic']:
            score += 1.0 / total_criteria
        
        return score
    
    async def hybrid_search_with_reranking(
        self,
        db: Session,
        query_embedding: List[float],
        query_text: str,
        initial_filters: Optional[Dict[str, Any]] = None,
        rerank_top_k: int = 50,
        final_limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda híbrida con re-ranking basado en múltiples señales
        """
        try:
            # 1. Búsqueda vectorial inicial
            initial_results = await self.vector_similarity_search(
                db=db,
                query_embedding=query_embedding,
                filters=initial_filters,
                limit=rerank_top_k
            )
            
            if not initial_results:
                return []
            
            # 2. Re-ranking con múltiples señales
            reranked_results = []
            
            for result in initial_results:
                # Scores individuales
                semantic_score = result['similarity_score']
                quality_score = result.get('quality_score', 0.0) or 0.0
                confidence_score = result.get('confidence_score', 1.0) or 1.0
                
                # Score de popularidad (basado en view_count)
                popularity_score = self._calculate_popularity_score(
                    result.get('view_count', 0)
                )
                
                # Score de relevancia textual (básico)
                text_relevance_score = self._calculate_text_relevance(
                    query_text, result.get('title', ''), result.get('description', '')
                )
                
                # Score final combinado
                final_score = (
                    semantic_score * 0.4 +
                    quality_score * 0.2 +
                    confidence_score * 0.1 +
                    popularity_score * 0.1 +
                    text_relevance_score * 0.2
                )
                
                result['rerank_score'] = final_score
                result['score_breakdown'] = {
                    'semantic': semantic_score,
                    'quality': quality_score,
                    'confidence': confidence_score,
                    'popularity': popularity_score,
                    'text_relevance': text_relevance_score
                }
                
                reranked_results.append(result)
            
            # Ordenar por score final
            reranked_results.sort(key=lambda x: x['rerank_score'], reverse=True)
            
            return reranked_results[:final_limit]
            
        except Exception as e:
            logger.error(f"Error in hybrid search with reranking: {e}")
            return []
    
    def _calculate_popularity_score(self, view_count: int) -> float:
        """
        Calcula score de popularidad basado en view count (escala logarítmica)
        """
        if not view_count or view_count <= 0:
            return 0.0
        
        # Escala logarítmica normalizada
        log_views = np.log10(max(view_count, 1))
        max_log_views = 7.0  # 10M views
        
        return min(log_views / max_log_views, 1.0)
    
    def _calculate_text_relevance(
        self,
        query_text: str,
        title: str,
        description: str
    ) -> float:
        """
        Calcula relevancia textual básica (coincidencia de palabras clave)
        """
        try:
            if not query_text:
                return 0.0
            
            # Tokenizar y normalizar
            query_words = set(query_text.lower().split())
            title_words = set((title or '').lower().split())
            desc_words = set((description or '').lower().split())
            
            # Calcular intersecciones
            title_matches = len(query_words.intersection(title_words))
            desc_matches = len(query_words.intersection(desc_words))
            
            # Score ponderado
            title_score = title_matches / max(len(query_words), 1) * 0.7
            desc_score = desc_matches / max(len(query_words), 1) * 0.3
            
            return min(title_score + desc_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating text relevance: {e}")
            return 0.0
    
    def get_search_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de búsqueda
        """
        return {
            'pgvector_available': self.pgvector_available,
            'search_stats': self.search_stats.copy(),
            'config': {
                'similarity_threshold': self.similarity_threshold,
                'max_results': self.max_results,
                'content_type_weights': self.content_type_weights.copy()
            }
        }
    
    def reset_stats(self):
        """
        Resetea las estadísticas de búsqueda
        """
        self.search_stats = {
            'total_searches': 0,
            'vector_searches': 0,
            'fallback_searches': 0,
            'avg_search_time_ms': 0
        }