"""
PASO 12: Algoritmo de scoring multi-criterio
Sistema avanzado de puntuación para recomendaciones con pesos balanceados
50% similitud semántica + 20% dificultad + 15% error común + 15% popularidad
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any, NamedTuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from dataclasses import dataclass
import math

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, desc
from sqlalchemy.sql import select

from app.models.question import Question
from app.models.youtube_catalog import YoutubeCatalog
from app.models.content_embeddings import ContentEmbeddings
from app.models.question_video_recommendations import QuestionVideoRecommendations
from app.models.user_answer import UserAnswer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScoringCriteria(Enum):
    """Criterios de scoring disponibles"""
    SEMANTIC_SIMILARITY = "semantic_similarity"
    DIFFICULTY_PROXIMITY = "difficulty_proximity"
    ERROR_COVERAGE = "error_coverage"
    POPULARITY_ENGAGEMENT = "popularity_engagement"
    CONTENT_QUALITY = "content_quality"
    TEMPORAL_RELEVANCE = "temporal_relevance"

@dataclass
class ScoringWeights:
    """Configuración de pesos para algoritmo de scoring"""
    semantic_similarity: float = 0.50    # 50% - Similitud semántica (embeddings)
    difficulty_proximity: float = 0.20   # 20% - Proximidad de dificultad (theta)
    error_coverage: float = 0.15         # 15% - Cobertura de errores comunes
    popularity_engagement: float = 0.15  # 15% - Popularidad/engagement
    
    def __post_init__(self):
        """Validar que los pesos sumen 1.0"""
        total = (self.semantic_similarity + self.difficulty_proximity + 
                self.error_coverage + self.popularity_engagement)
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Scoring weights must sum to 1.0, got {total}")

@dataclass
class ScoringComponents:
    """Componentes individuales del score"""
    semantic_similarity: float = 0.0
    difficulty_proximity: float = 0.0
    error_coverage: float = 0.0
    popularity_engagement: float = 0.0
    content_quality: float = 0.0
    temporal_relevance: float = 0.0
    
    # Metadatos adicionales
    embedding_similarity: Optional[float] = None
    theta_difference: Optional[float] = None
    error_match_confidence: Optional[float] = None
    engagement_metrics: Optional[Dict[str, float]] = None
    quality_indicators: Optional[Dict[str, float]] = None

@dataclass
class RecommendationScore:
    """Score final de recomendación con componentes detallados"""
    total_score: float
    confidence_level: str  # 'low', 'medium', 'high'
    components: ScoringComponents
    weights_used: ScoringWeights
    recommendation_type: str
    explanation: str
    computed_at: datetime

class RecommendationScoringService:
    """
    Servicio de scoring multi-criterio para recomendaciones de videos
    """
    
    def __init__(self, custom_weights: Optional[ScoringWeights] = None):
        self.weights = custom_weights or ScoringWeights()
        
        # Configuración de umbrales
        self.thresholds = {
            'minimum_recommendation': 0.75,
            'high_confidence': 0.85,
            'excellent_match': 0.95,
            'semantic_minimum': 0.3,
            'difficulty_tolerance': 1.0,  # Rango de theta aceptable
            'popularity_baseline': 1000   # Views mínimas para score base
        }
        
        # Configuración de diversificación
        self.diversification = {
            'max_same_topic': 3,
            'max_same_creator': 2,
            'min_variety_score': 0.7
        }
        
        # Cache para optimización
        self._embedding_cache = {}
        self._popularity_cache = {}
        
    async def calculate_comprehensive_score(
        self,
        db: Session,
        question: Question,
        video: YoutubeCatalog,
        question_embeddings: Dict[str, ContentEmbeddings],
        error_analysis: Dict[str, Any],
        student_context: Optional[Dict[str, Any]] = None
    ) -> RecommendationScore:
        """
        Calcula el score comprehensivo para una recomendación pregunta-video
        """
        logger.debug(f"Calculating score for Q:{question.id} -> V:{video.id}")
        
        # Inicializar componentes
        components = ScoringComponents()
        
        try:
            # 1. SIMILARIDAD SEMÁNTICA (50%)
            components.semantic_similarity = await self._calculate_semantic_similarity(
                db, question, video, question_embeddings
            )
            
            # 2. PROXIMIDAD DE DIFICULTAD (20%)
            components.difficulty_proximity = await self._calculate_difficulty_proximity(
                question, video, student_context
            )
            
            # 3. COBERTURA DE ERROR COMÚN (15%)
            components.error_coverage = await self._calculate_error_coverage(
                db, question, video, error_analysis
            )
            
            # 4. POPULARIDAD/ENGAGEMENT (15%)
            components.popularity_engagement = await self._calculate_popularity_score(
                video
            )
            
            # 5. Componentes adicionales (no incluidos en peso principal)
            components.content_quality = await self._calculate_content_quality(video)
            components.temporal_relevance = await self._calculate_temporal_relevance(video)
            
            # Calcular score total usando pesos configurados
            total_score = (
                components.semantic_similarity * self.weights.semantic_similarity +
                components.difficulty_proximity * self.weights.difficulty_proximity +
                components.error_coverage * self.weights.error_coverage +
                components.popularity_engagement * self.weights.popularity_engagement
            )
            
            # Aplicar modificadores de calidad y temporalidad
            quality_modifier = components.content_quality * 0.1  # Máximo 10% bonus
            temporal_modifier = components.temporal_relevance * 0.05  # Máximo 5% bonus
            
            adjusted_score = min(1.0, total_score + quality_modifier + temporal_modifier)
            
            # Determinar nivel de confianza
            confidence_level = self._determine_confidence_level(adjusted_score, components)
            
            # Determinar tipo de recomendación
            recommendation_type = self._determine_recommendation_type(components, error_analysis)
            
            # Generar explicación
            explanation = self._generate_score_explanation(components, self.weights)
            
            return RecommendationScore(
                total_score=round(adjusted_score, 4),
                confidence_level=confidence_level,
                components=components,
                weights_used=self.weights,
                recommendation_type=recommendation_type,
                explanation=explanation,
                computed_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive score: {e}")
            # Retornar score por defecto en caso de error
            return RecommendationScore(
                total_score=0.0,
                confidence_level='low',
                components=ScoringComponents(),
                weights_used=self.weights,
                recommendation_type='fallback',
                explanation=f"Error in calculation: {str(e)}",
                computed_at=datetime.utcnow()
            )
    
    async def _calculate_semantic_similarity(
        self,
        db: Session,
        question: Question,
        video: YoutubeCatalog,
        question_embeddings: Dict[str, ContentEmbeddings]
    ) -> float:
        """
        Calcula similaridad semántica usando embeddings vectoriales
        """
        try:
            # Obtener embedding de la pregunta (preferir 'combined')
            question_embedding = (
                question_embeddings.get('combined') or 
                question_embeddings.get('question_text') or
                next(iter(question_embeddings.values()), None)
            )
            
            if not question_embedding:
                logger.warning(f"No question embedding found for question {question.id}")
                return 0.0
            
            # Obtener embedding del video
            video_embedding_key = f"video_{video.id}_combined"
            if video_embedding_key not in self._embedding_cache:
                video_embedding = db.query(ContentEmbeddings).filter(
                    and_(
                        ContentEmbeddings.content_type == 'youtube_video',
                        ContentEmbeddings.content_id == video.id,
                        ContentEmbeddings.embedding_type == 'combined',
                        ContentEmbeddings.is_active == 'true'
                    )
                ).first()
                self._embedding_cache[video_embedding_key] = video_embedding
            else:
                video_embedding = self._embedding_cache[video_embedding_key]
            
            if not video_embedding:
                logger.warning(f"No video embedding found for video {video.id}")
                return 0.0
            
            # Calcular similaridad coseno usando pgvector si está disponible
            try:
                # Query optimizada con pgvector
                result = db.execute(
                    text("""
                        SELECT 1 - (q.embedding_vector <=> v.embedding_vector) as similarity
                        FROM content_embeddings q, content_embeddings v
                        WHERE q.id = :q_id AND v.id = :v_id
                    """),
                    {'q_id': question_embedding.id, 'v_id': video_embedding.id}
                ).fetchone()
                
                if result and result[0] is not None:
                    similarity = float(result[0])
                    # Normalizar a [0,1] y aplicar curva de activación
                    normalized_similarity = max(0.0, min(1.0, similarity))
                    
                    # Aplicar función sigmoide para mejorar discriminación
                    enhanced_similarity = self._sigmoid_activation(normalized_similarity, midpoint=0.7)
                    
                    logger.debug(f"Semantic similarity: {normalized_similarity:.4f} -> {enhanced_similarity:.4f}")
                    return enhanced_similarity
                
            except Exception as e:
                logger.warning(f"pgvector similarity failed, using fallback: {e}")
            
            # Fallback a cálculo manual
            manual_similarity = question_embedding.calculate_similarity(video_embedding.embedding_vector)
            normalized_manual = max(0.0, min(1.0, manual_similarity))
            enhanced_manual = self._sigmoid_activation(normalized_manual, midpoint=0.7)
            
            return enhanced_manual
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    async def _calculate_difficulty_proximity(
        self,
        question: Question,
        video: YoutubeCatalog,
        student_context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calcula proximidad de dificultad usando parámetros theta de IRT
        """
        try:
            # Obtener theta de la pregunta
            question_theta = getattr(question, 'theta', None)
            if question_theta is None:
                # Estimar theta basado en dificultad numérica
                question_theta = (question.difficulty / 5.0) - 1.0  # Mapear [1,5] a [-0.8, 0.0]
            
            # Obtener theta del video
            video_theta = self._estimate_video_theta(video)
            
            # Si hay contexto del estudiante, considerar su habilidad
            if student_context and 'estimated_theta' in student_context:
                student_theta = student_context['estimated_theta']
                # Ajustar recomendación basada en habilidad del estudiante
                optimal_difficulty = self._calculate_optimal_difficulty(student_theta, question_theta)
                target_theta = optimal_difficulty
            else:
                target_theta = question_theta
            
            # Calcular proximidad usando función gaussiana
            theta_difference = abs(target_theta - video_theta)
            
            # Función gaussiana: sigma=0.5 para tolerancia razonable
            proximity_score = math.exp(-0.5 * (theta_difference / 0.5) ** 2)
            
            # Aplicar bonus si la dificultad es ligeramente mayor (zona de desarrollo próximo)
            if video_theta > target_theta and theta_difference <= 0.3:
                proximity_score *= 1.1  # 10% bonus por estar en ZDP
            
            # Registrar metadatos
            if hasattr(self, '_current_components'):
                self._current_components.theta_difference = theta_difference
            
            logger.debug(f"Difficulty proximity: theta_diff={theta_difference:.3f}, score={proximity_score:.4f}")
            return min(1.0, proximity_score)
            
        except Exception as e:
            logger.error(f"Error calculating difficulty proximity: {e}")
            return 0.5  # Score neutral
    
    def _estimate_video_theta(self, video: YoutubeCatalog) -> float:
        """Estima parámetro theta del video basado en metadatos"""
        # Mapeo mejorado de nivel a theta
        nivel_mapping = {
            'Básico': -0.5,
            'Fundamental': -0.8,
            'Elemental': -0.6,
            'Intermedio': 0.0,
            'Medio': -0.2,
            'Avanzado': 0.5,
            'Superior': 0.8,
            'Universitario': 1.0
        }
        
        base_theta = nivel_mapping.get(video.nivel, 0.0)
        
        # Ajustar basado en duración (videos muy largos pueden ser más complejos)
        if video.duration_seconds:
            duration_minutes = video.duration_seconds / 60
            if duration_minutes > 30:
                base_theta += 0.1  # Bonus por contenido extenso
            elif duration_minutes < 5:
                base_theta -= 0.1  # Penalización por contenido muy breve
        
        return base_theta
    
    def _calculate_optimal_difficulty(self, student_theta: float, question_theta: float) -> float:
        """Calcula dificultad óptima basada en zona de desarrollo próximo"""
        # ZDP: ligeramente por encima de la habilidad actual del estudiante
        zdp_offset = 0.2  # 0.2 logits por encima de la habilidad
        
        if student_theta < question_theta:
            # Estudiante tiene dificultades, recomendar contenido más fácil
            return student_theta + zdp_offset
        else:
            # Estudiante maneja bien la pregunta, mantener dificultad
            return question_theta
    
    async def _calculate_error_coverage(
        self,
        db: Session,
        question: Question,
        video: YoutubeCatalog,
        error_analysis: Dict[str, Any]
    ) -> float:
        """
        Calcula qué tan bien el video aborda errores comunes específicos
        """
        try:
            if not error_analysis.get('needs_remediation', False):
                # No hay errores significativos, score base
                return 0.5
            
            score = 0.0
            confidence = 0.0
            
            # 1. Análisis de título y descripción del video para keywords de error
            video_text = f"{video.title} {video.description or ''}".lower()
            
            # Keywords que indican abordaje de errores comunes
            error_keywords = {
                'conceptual': ['concepto', 'fundamento', 'base', 'teoría', 'principio'],
                'procedural': ['paso', 'método', 'proceso', 'procedimiento', 'algoritmo'],
                'common_mistakes': ['error', 'mistake', 'común', 'frecuente', 'equivocación'],
                'clarification': ['aclarar', 'explicar', 'demostrar', 'mostrar', 'diferencia']
            }
            
            keyword_matches = 0
            for category, keywords in error_keywords.items():
                if any(keyword in video_text for keyword in keywords):
                    keyword_matches += 1
                    score += 0.2  # 20% por categoría
            
            # 2. Análisis del distractor dominante
            dominant_distractor = error_analysis.get('dominant_distractor')
            if dominant_distractor:
                # Buscar si el video menciona errores específicos relacionados
                distractor_specific_score = self._analyze_distractor_coverage(
                    video_text, dominant_distractor, question
                )
                score += distractor_specific_score * 0.4  # 40% por cobertura específica
                confidence += 0.3
            
            # 3. Análisis de transcript si está disponible
            if video.transcript:
                transcript_score = self._analyze_transcript_for_errors(
                    video.transcript, error_analysis
                )
                score += transcript_score * 0.3  # 30% por análisis de transcript
                confidence += 0.4
            
            # 4. Histórico de efectividad para errores similares
            historical_effectiveness = await self._get_historical_error_coverage(
                db, video, error_analysis
            )
            score += historical_effectiveness * 0.1  # 10% por histórico
            confidence += 0.3
            
            # Normalizar score
            final_score = min(1.0, score)
            
            # Aplicar factor de confianza
            confidence_factor = min(1.0, confidence)
            adjusted_score = final_score * confidence_factor
            
            # Registrar metadatos
            if hasattr(self, '_current_components'):
                self._current_components.error_match_confidence = confidence_factor
            
            logger.debug(f"Error coverage: score={final_score:.4f}, confidence={confidence_factor:.4f}, final={adjusted_score:.4f}")
            return adjusted_score
            
        except Exception as e:
            logger.error(f"Error calculating error coverage: {e}")
            return 0.3  # Score conservador
    
    def _analyze_distractor_coverage(
        self, 
        video_text: str, 
        distractor: str, 
        question: Question
    ) -> float:
        """Analiza si el video aborda específicamente el distractor problemático"""
        # Esta función requeriría un análisis más sofisticado del contenido
        # Por ahora, implementación básica
        
        # Obtener texto de la opción del distractor
        distractor_text = getattr(question, f'opcion_{distractor.lower()}_texto', '')
        if not distractor_text:
            return 0.0
        
        # Buscar conceptos clave del distractor en el video
        distractor_words = distractor_text.lower().split()
        common_words = set(video_text.split()) & set(distractor_words)
        
        if len(distractor_words) > 0:
            overlap_ratio = len(common_words) / len(distractor_words)
            return min(1.0, overlap_ratio * 2)  # Amplificar overlap pequeños
        
        return 0.0
    
    def _analyze_transcript_for_errors(
        self, 
        transcript: str, 
        error_analysis: Dict[str, Any]
    ) -> float:
        """Analiza el transcript para detectar abordaje de errores comunes"""
        if not transcript:
            return 0.0
        
        transcript_lower = transcript.lower()
        score = 0.0
        
        # Buscar indicadores de corrección de errores
        error_indicators = [
            'no confundir', 'error común', 'frecuente error', 'muchos piensan',
            'incorrecto', 'equivocado', 'cuidado con', 'atención'
        ]
        
        for indicator in error_indicators:
            if indicator in transcript_lower:
                score += 0.2
        
        # Buscar explicaciones detalladas (transcripts largos tienden a ser más explicativos)
        if len(transcript) > 1000:  # Más de 1000 caracteres
            score += 0.3
        
        return min(1.0, score)
    
    async def _get_historical_error_coverage(
        self,
        db: Session,
        video: YoutubeCatalog,
        error_analysis: Dict[str, Any]
    ) -> float:
        """Obtiene efectividad histórica del video para errores similares"""
        try:
            # Query para obtener métricas históricas
            # Esta implementación requeriría una tabla de tracking más detallada
            # Por ahora, retornamos score base
            return 0.5
            
        except Exception as e:
            logger.error(f"Error getting historical error coverage: {e}")
            return 0.0
    
    async def _calculate_popularity_score(self, video: YoutubeCatalog) -> float:
        """
        Calcula score de popularidad basado en métricas de engagement
        """
        try:
            # Usar cache si está disponible
            cache_key = f"popularity_{video.id}"
            if cache_key in self._popularity_cache:
                return self._popularity_cache[cache_key]
            
            score = 0.0
            
            # 1. Views (40% del score de popularidad)
            if video.views and video.views > 0:
                # Función logarítmica para views
                view_score = min(1.0, math.log10(video.views / self.thresholds['popularity_baseline'] + 1))
                score += view_score * 0.4
            
            # 2. Engagement ratio - Likes/Views (30% del score)
            if video.likes and video.views and video.views > 0:
                like_ratio = video.likes / video.views
                # Buenos videos educativos tienen 1-5% like ratio
                engagement_score = min(1.0, (like_ratio * 100) / 3.0)  # Normalizar a 3%
                score += engagement_score * 0.3
            
            # 3. Duración apropiada (20% del score)
            if video.duration_seconds:
                duration_score = self._calculate_duration_score(video.duration_seconds)
                score += duration_score * 0.2
            
            # 4. Freshness/actualidad (10% del score)
            if video.published_at:
                freshness_score = self._calculate_freshness_score(video.published_at)
                score += freshness_score * 0.1
            
            # Aplicar factor de calidad mínima
            if video.views and video.views < 100:
                score *= 0.5  # Penalizar videos con muy pocas views
            
            final_score = min(1.0, score)
            self._popularity_cache[cache_key] = final_score
            
            logger.debug(f"Popularity score for video {video.id}: {final_score:.4f}")
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating popularity score: {e}")
            return 0.5
    
    def _calculate_duration_score(self, duration_seconds: int) -> float:
        """Calcula score basado en duración óptima para contenido educativo"""
        duration_minutes = duration_seconds / 60
        
        # Duración óptima: 5-20 minutos para videos educativos
        if 5 <= duration_minutes <= 20:
            return 1.0
        elif 3 <= duration_minutes <= 30:
            return 0.8
        elif 1 <= duration_minutes <= 45:
            return 0.6
        else:
            return 0.3  # Muy corto o muy largo
    
    def _calculate_freshness_score(self, published_at: datetime) -> float:
        """Calcula score de actualidad del contenido"""
        if not published_at:
            return 0.5
        
        days_old = (datetime.utcnow() - published_at).days
        
        # Contenido más reciente es mejor, pero no penalizar demasiado contenido viejo de calidad
        if days_old <= 365:  # Último año
            return 1.0
        elif days_old <= 1095:  # Últimos 3 años
            return 0.8
        elif days_old <= 1825:  # Últimos 5 años
            return 0.6
        else:
            return 0.4
    
    async def _calculate_content_quality(self, video: YoutubeCatalog) -> float:
        """Calcula indicadores de calidad del contenido"""
        try:
            score = 0.0
            
            # 1. Completitud de metadatos
            if video.title and len(video.title) > 10:
                score += 0.2
            if video.description and len(video.description) > 50:
                score += 0.2
            if video.transcript:
                score += 0.3
            
            # 2. Calidad del título (indicadores educativos)
            if video.title:
                educational_indicators = [
                    'cómo', 'explicación', 'tutorial', 'guía', 'aprende',
                    'ejercicio', 'problema', 'solución', 'método'
                ]
                title_lower = video.title.lower()
                for indicator in educational_indicators:
                    if indicator in title_lower:
                        score += 0.1
                        break
            
            # 3. Ratio de engagement positivo
            if video.likes and video.dislikes:
                positive_ratio = video.likes / (video.likes + video.dislikes)
                if positive_ratio > 0.9:
                    score += 0.2
                elif positive_ratio > 0.8:
                    score += 0.1
            
            return min(1.0, score)
            
        except Exception as e:
            logger.error(f"Error calculating content quality: {e}")
            return 0.5
    
    async def _calculate_temporal_relevance(self, video: YoutubeCatalog) -> float:
        """Calcula relevancia temporal del contenido"""
        try:
            # Para contenido educativo básico, la temporalidad es menos importante
            # que para contenido de tecnología o actualidad
            
            if not video.published_at:
                return 0.5
            
            days_old = (datetime.utcnow() - video.published_at).days
            
            # Función de decay suave para contenido educativo
            if days_old <= 30:
                return 1.0
            elif days_old <= 365:
                return 0.9
            elif days_old <= 1095:  # 3 años
                return 0.8
            else:
                return 0.7  # Contenido educativo fundamental mantiene relevancia
                
        except Exception as e:
            logger.error(f"Error calculating temporal relevance: {e}")
            return 0.7
    
    def _sigmoid_activation(self, x: float, midpoint: float = 0.5, steepness: float = 10) -> float:
        """Aplica función sigmoide para mejorar discriminación de scores"""
        try:
            return 1 / (1 + math.exp(-steepness * (x - midpoint)))
        except (OverflowError, ZeroDivisionError):
            return 0.0 if x < midpoint else 1.0
    
    def _determine_confidence_level(
        self, 
        total_score: float, 
        components: ScoringComponents
    ) -> str:
        """Determina nivel de confianza basado en score y componentes"""
        if total_score >= self.thresholds['excellent_match']:
            return 'high'
        elif total_score >= self.thresholds['high_confidence']:
            return 'high'
        elif total_score >= self.thresholds['minimum_recommendation']:
            # Verificar calidad de componentes individuales
            if (components.semantic_similarity >= 0.7 and 
                components.difficulty_proximity >= 0.6):
                return 'high'
            else:
                return 'medium'
        elif total_score >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _determine_recommendation_type(
        self, 
        components: ScoringComponents, 
        error_analysis: Dict[str, Any]
    ) -> str:
        """Determina el tipo de recomendación basado en componentes"""
        if error_analysis.get('needs_remediation', False) and components.error_coverage > 0.6:
            return 'error_remediation'
        elif components.semantic_similarity > 0.8:
            return 'concept_reinforcement'
        elif components.difficulty_proximity > 0.8:
            return 'skill_building'
        else:
            return 'general_review'
    
    def _generate_score_explanation(
        self, 
        components: ScoringComponents, 
        weights: ScoringWeights
    ) -> str:
        """Genera explicación legible del scoring"""
        explanations = []
        
        # Semántica
        sem_contribution = components.semantic_similarity * weights.semantic_similarity
        explanations.append(f"Similitud semántica: {components.semantic_similarity:.1%} (peso 50%) = {sem_contribution:.3f}")
        
        # Dificultad
        diff_contribution = components.difficulty_proximity * weights.difficulty_proximity
        explanations.append(f"Proximidad dificultad: {components.difficulty_proximity:.1%} (peso 20%) = {diff_contribution:.3f}")
        
        # Error coverage
        error_contribution = components.error_coverage * weights.error_coverage
        explanations.append(f"Cobertura errores: {components.error_coverage:.1%} (peso 15%) = {error_contribution:.3f}")
        
        # Popularidad
        pop_contribution = components.popularity_engagement * weights.popularity_engagement
        explanations.append(f"Popularidad: {components.popularity_engagement:.1%} (peso 15%) = {pop_contribution:.3f}")
        
        total = sem_contribution + diff_contribution + error_contribution + pop_contribution
        explanations.append(f"Score total: {total:.3f}")
        
        return " | ".join(explanations)
    
    async def apply_diversification(
        self,
        recommendations: List[Tuple[RecommendationScore, YoutubeCatalog]],
        max_recommendations: int = 5
    ) -> List[Tuple[RecommendationScore, YoutubeCatalog]]:
        """
        Aplica algoritmo de diversificación para evitar over-recommendation
        """
        if len(recommendations) <= max_recommendations:
            return recommendations
        
        # Ordenar por score total
        sorted_recs = sorted(recommendations, key=lambda x: x[0].total_score, reverse=True)
        
        diversified = []
        topic_counts = {}
        creator_counts = {}
        type_counts = {}
        
        for score, video in sorted_recs:
            # Contar limitaciones
            topic_key = f"{video.area_evaluada}_{video.tema_principal}"
            creator_key = video.channel_title or 'unknown'
            type_key = score.recommendation_type
            
            # Aplicar límites de diversificación
            if (topic_counts.get(topic_key, 0) >= self.diversification['max_same_topic'] or
                creator_counts.get(creator_key, 0) >= self.diversification['max_same_creator']):
                
                # Solo incluir si el score es excepcionalmente alto
                if score.total_score < 0.9:
                    continue
            
            # Verificar score mínimo de variedad
            if score.total_score < self.diversification['min_variety_score']:
                continue
            
            # Añadir a lista diversificada
            diversified.append((score, video))
            
            # Actualizar contadores
            topic_counts[topic_key] = topic_counts.get(topic_key, 0) + 1
            creator_counts[creator_key] = creator_counts.get(creator_key, 0) + 1
            type_counts[type_key] = type_counts.get(type_key, 0) + 1
            
            if len(diversified) >= max_recommendations:
                break
        
        logger.info(f"Applied diversification: {len(recommendations)} -> {len(diversified)} recommendations")
        return diversified
    
    def should_recommend(self, score: RecommendationScore) -> bool:
        """Determina si una recomendación debe ser incluida"""
        return (score.total_score >= self.thresholds['minimum_recommendation'] and
                score.confidence_level in ['medium', 'high'])
    
    def get_scoring_analytics(
        self, 
        scores: List[RecommendationScore]
    ) -> Dict[str, Any]:
        """Genera analytics del proceso de scoring"""
        if not scores:
            return {}
        
        total_scores = [s.total_score for s in scores]
        semantic_scores = [s.components.semantic_similarity for s in scores]
        difficulty_scores = [s.components.difficulty_proximity for s in scores]
        
        return {
            'total_recommendations': len(scores),
            'average_score': np.mean(total_scores),
            'score_std': np.std(total_scores),
            'high_confidence_count': len([s for s in scores if s.confidence_level == 'high']),
            'above_threshold_count': len([s for s in scores if s.total_score >= self.thresholds['minimum_recommendation']]),
            'component_averages': {
                'semantic_similarity': np.mean(semantic_scores),
                'difficulty_proximity': np.mean(difficulty_scores),
                'error_coverage': np.mean([s.components.error_coverage for s in scores]),
                'popularity': np.mean([s.components.popularity_engagement for s in scores])
            },
            'recommendation_types': {
                t: len([s for s in scores if s.recommendation_type == t])
                for t in set(s.recommendation_type for s in scores)
            }
        }