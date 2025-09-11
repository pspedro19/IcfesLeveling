"""
PASO 10: Mapeo avanzado Preguntas-Videos
Sistema de recomendaciones basado en embeddings y criterios multi-factoriales
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from ..core.database import Base

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    from sqlalchemy import Text as Vector
    PGVECTOR_AVAILABLE = False

class QuestionVideoRecommendations(Base):
    """
    Tabla de mapeo avanzado entre preguntas ICFES y videos de YouTube
    Almacena scores de relevancia basados en múltiples criterios
    """
    __tablename__ = "question_video_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # Referencias a pregunta y video
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("youtube_catalog.id"), nullable=False, index=True)
    
    # Criterios de matching
    exact_match_score = Column(Float, nullable=False, default=0.0)  # Match exacto por subject_id/topic_id
    semantic_similarity_score = Column(Float, nullable=False, default=0.0)  # Similarity de embeddings
    difficulty_proximity_score = Column(Float, nullable=False, default=0.0)  # Proximidad de dificultad (theta)
    popularity_score = Column(Float, nullable=False, default=0.0)  # Popularidad/engagement del video
    
    # Score final combinado
    total_score = Column(Float, nullable=False, default=0.0, index=True)
    
    # Metadatos de la recomendación
    recommendation_type = Column(String(50), nullable=False, index=True)  # 'concept_review', 'error_remediation', 'skill_building'
    confidence_level = Column(String(20), nullable=False, default='medium', index=True)  # 'low', 'medium', 'high'
    
    # Análisis de errores específicos
    targets_common_error = Column(Boolean, default=False, index=True)  # Si aborda error común específico
    error_pattern_addressed = Column(String(100), nullable=True)  # Tipo de error que aborda
    distractor_focus = Column(String(1), nullable=True)  # Distractor específico (A, B, C, D)
    
    # Contexto educativo
    learning_objective = Column(Text, nullable=True)  # Objetivo de aprendizaje específico
    prerequisite_concepts = Column(ARRAY(String), nullable=True)  # Conceptos prerrequisito
    cognitive_level = Column(String(50), nullable=True, index=True)  # 'remember', 'understand', 'apply', 'analyze', 'evaluate', 'create'
    
    # Métricas de calidad
    embedding_similarity = Column(Float, nullable=True)  # Similaridad coseno de embeddings
    topic_alignment = Column(Float, nullable=True)  # Alineación de temas
    difficulty_gap = Column(Float, nullable=True)  # Diferencia de dificultad
    content_completeness = Column(Float, nullable=True)  # Completitud del contenido del video
    
    # Estado y versionado
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    recommendation_version = Column(Integer, nullable=False, default=1)
    algorithm_version = Column(String(20), nullable=False, default='v1.0')
    
    # Metadatos de procesamiento
    processing_metadata = Column(JSON, nullable=True)  # Datos adicionales del procesamiento
    last_validated_at = Column(DateTime, nullable=True)
    validation_status = Column(String(20), default='pending', index=True)  # 'pending', 'validated', 'rejected'
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    question = relationship("Question", backref="video_recommendations")
    video = relationship("YoutubeCatalog", backref="question_recommendations")
    
    def __repr__(self):
        return f"<QuestionVideoRec(q_id={str(self.question_id)[:8]}, v_id={self.video_id}, score={self.total_score:.3f})>"
    
    def to_dict(self, include_metadata: bool = False) -> Dict[str, Any]:
        """Convierte a diccionario para API responses"""
        result = {
            "id": self.id,
            "uuid": str(self.uuid),
            "question_id": str(self.question_id),
            "video_id": self.video_id,
            "total_score": round(self.total_score, 4),
            "recommendation_type": self.recommendation_type,
            "confidence_level": self.confidence_level,
            "targets_common_error": self.targets_common_error,
            "error_pattern_addressed": self.error_pattern_addressed,
            "distractor_focus": self.distractor_focus,
            "learning_objective": self.learning_objective,
            "cognitive_level": self.cognitive_level,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_metadata:
            result.update({
                "exact_match_score": round(self.exact_match_score, 4),
                "semantic_similarity_score": round(self.semantic_similarity_score, 4),
                "difficulty_proximity_score": round(self.difficulty_proximity_score, 4),
                "popularity_score": round(self.popularity_score, 4),
                "embedding_similarity": round(self.embedding_similarity, 4) if self.embedding_similarity else None,
                "topic_alignment": round(self.topic_alignment, 4) if self.topic_alignment else None,
                "difficulty_gap": round(self.difficulty_gap, 4) if self.difficulty_gap else None,
                "content_completeness": round(self.content_completeness, 4) if self.content_completeness else None,
                "algorithm_version": self.algorithm_version,
                "processing_metadata": self.processing_metadata
            })
        
        return result
    
    @classmethod
    def calculate_total_score(
        cls,
        exact_match: float = 0.0,
        semantic_similarity: float = 0.0,
        difficulty_proximity: float = 0.0,
        popularity: float = 0.0,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Calcula el score total usando los pesos configurados
        Weights por defecto basados en la especificación:
        - 50% similitud semántica
        - 20% match de dificultad  
        - 15% cobertura del error común
        - 15% popularidad/engagement
        """
        if weights is None:
            weights = {
                'semantic': 0.50,
                'difficulty': 0.20,
                'exact_match': 0.15,  # incluye cobertura de error
                'popularity': 0.15
            }
        
        total = (
            exact_match * weights.get('exact_match', 0.15) +
            semantic_similarity * weights.get('semantic', 0.50) +
            difficulty_proximity * weights.get('difficulty', 0.20) +
            popularity * weights.get('popularity', 0.15)
        )
        
        return min(1.0, max(0.0, total))  # Clamp entre 0 y 1
    
    def update_score_components(
        self,
        exact_match: Optional[float] = None,
        semantic_similarity: Optional[float] = None,
        difficulty_proximity: Optional[float] = None,
        popularity: Optional[float] = None
    ):
        """Actualiza componentes del score y recalcula el total"""
        if exact_match is not None:
            self.exact_match_score = exact_match
        if semantic_similarity is not None:
            self.semantic_similarity_score = semantic_similarity
        if difficulty_proximity is not None:
            self.difficulty_proximity_score = difficulty_proximity
        if popularity is not None:
            self.popularity_score = popularity
        
        # Recalcular score total
        self.total_score = self.calculate_total_score(
            self.exact_match_score,
            self.semantic_similarity_score,
            self.difficulty_proximity_score,
            self.popularity_score
        )
        
        # Actualizar nivel de confianza basado en score
        if self.total_score >= 0.8:
            self.confidence_level = 'high'
        elif self.total_score >= 0.6:
            self.confidence_level = 'medium'
        else:
            self.confidence_level = 'low'
    
    def should_recommend(self, threshold: float = 0.75) -> bool:
        """Determina si la recomendación cumple el umbral mínimo"""
        return self.total_score >= threshold and self.is_active
    
    @classmethod
    def get_top_recommendations(
        cls,
        db_session,
        question_id: UUID,
        limit: int = 5,
        min_threshold: float = 0.75,
        recommendation_type: Optional[str] = None
    ) -> List['QuestionVideoRecommendations']:
        """Obtiene las top recomendaciones para una pregunta"""
        query = db_session.query(cls).filter(
            cls.question_id == question_id,
            cls.is_active == True,
            cls.total_score >= min_threshold
        )
        
        if recommendation_type:
            query = query.filter(cls.recommendation_type == recommendation_type)
        
        return query.order_by(cls.total_score.desc()).limit(limit).all()


class RecommendationMetrics(Base):
    """
    Métricas de efectividad de las recomendaciones
    """
    __tablename__ = "recommendation_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("question_video_recommendations.id"), nullable=False)
    student_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Opcional para métricas agregadas
    
    # Métricas de engagement
    was_clicked = Column(Boolean, default=False)
    watch_time_seconds = Column(Integer, nullable=True)
    completion_rate = Column(Float, nullable=True)  # % del video visto
    
    # Métricas de aprendizaje
    performance_before = Column(Float, nullable=True)  # Score antes de ver el video
    performance_after = Column(Float, nullable=True)   # Score después de ver el video
    improvement_delta = Column(Float, nullable=True)   # Mejora observada
    
    # Feedback del estudiante
    student_rating = Column(Integer, nullable=True)    # 1-5 estrellas
    found_helpful = Column(Boolean, nullable=True)
    feedback_text = Column(Text, nullable=True)
    
    # Metadatos
    session_id = Column(String(100), nullable=True)
    interaction_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationship
    recommendation = relationship("QuestionVideoRecommendations", backref="metrics")


# Índices optimizados para consultas frecuentes
Index(
    'idx_qvr_question_score',
    QuestionVideoRecommendations.question_id,
    QuestionVideoRecommendations.total_score.desc(),
    QuestionVideoRecommendations.is_active
)

Index(
    'idx_qvr_video_score',
    QuestionVideoRecommendations.video_id,
    QuestionVideoRecommendations.total_score.desc(),
    QuestionVideoRecommendations.is_active
)

Index(
    'idx_qvr_type_confidence',
    QuestionVideoRecommendations.recommendation_type,
    QuestionVideoRecommendations.confidence_level,
    QuestionVideoRecommendations.total_score.desc()
)

Index(
    'idx_qvr_error_targeting',
    QuestionVideoRecommendations.targets_common_error,
    QuestionVideoRecommendations.error_pattern_addressed,
    QuestionVideoRecommendations.total_score.desc()
)

Index(
    'idx_metrics_student_performance',
    RecommendationMetrics.student_id,
    RecommendationMetrics.improvement_delta.desc(),
    RecommendationMetrics.interaction_timestamp
)