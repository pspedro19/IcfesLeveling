from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from typing import Optional, List, Dict, Any
from ..core.database import Base

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    from sqlalchemy import Text as Vector
    PGVECTOR_AVAILABLE = False

class YoutubeCatalog(Base):
    """
    Modelo completo para el catálogo de videos YouTube con soporte para embeddings
    """
    __tablename__ = "youtube_catalog"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # Campos básicos del video
    youtube_id = Column(String(50), unique=True, nullable=False, index=True)
    url = Column(String(500), nullable=False)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    channel_name = Column(String(255), nullable=True, index=True)
    
    # Metadatos educativos del CSV
    codigo_tema = Column(String(50), nullable=False, index=True)  # CN001, MT002, etc.
    area_evaluada = Column(String(100), nullable=False, index=True)  # Ciencias Naturales, Matemáticas, etc.
    tema_principal = Column(String(255), nullable=False, index=True)
    canal_sugerido = Column(String(255), nullable=True)
    transcript = Column(Text, nullable=True)
    tema_tag = Column(String(255), nullable=True)
    
    # Metadatos adicionales del video (se obtienen de YouTube API)
    duration_seconds = Column(Integer, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    published_at = Column(DateTime, nullable=True)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    # Campos para mapeo con sistema ICFES
    subject_id = Column(Integer, nullable=True, index=True)  # ID del subject en el sistema
    topic_id = Column(Integer, nullable=True, index=True)    # ID del topic en el sistema
    competencias = Column(Text, nullable=True)  # JSON array de competencias ICFES
    componentes = Column(Text, nullable=True)   # JSON array de componentes ICFES
    nivel = Column(String(50), nullable=True)   # Básico, Intermedio, Avanzado
    
    # Scoring y calidad
    quality_score = Column(Float, default=0.0)
    relevance_score = Column(Float, default=0.0)
    educational_rating = Column(Float, default=0.0)
    
    # Estado del procesamiento
    is_processed = Column(Boolean, default=False)
    has_embeddings = Column(Boolean, default=False)
    processing_status = Column(String(50), default='pending')  # pending, processing, completed, error
    error_message = Column(Text, nullable=True)
    
    # Vector embeddings for semantic search
    title_embedding = Column(Vector(1536) if PGVECTOR_AVAILABLE else Text, nullable=True)
    description_embedding = Column(Vector(1536) if PGVECTOR_AVAILABLE else Text, nullable=True)
    combined_embedding = Column(Vector(1536) if PGVECTOR_AVAILABLE else Text, nullable=True)
    
    # IRT parameters
    irt_b = Column(Float, nullable=True)  # Difficulty parameter
    cognitive_level = Column(String(50), default='understand', index=True)
    
    # Language and versioning
    language = Column(String(10), default='es')
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_processed_at = Column(DateTime, nullable=True)
    
    # Relationships (if foreign keys exist)
    # subject = relationship("Subject", backref="youtube_videos", foreign_keys=[subject_id])
    # topic = relationship("Topic", backref="youtube_videos", foreign_keys=[topic_id])
    
    def __repr__(self):
        return f"<YoutubeCatalog(id={self.id}, codigo_tema='{self.codigo_tema}', title='{self.title[:50]}...')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "uuid": str(self.uuid),
            "youtube_id": self.youtube_id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "channel_name": self.channel_name,
            "codigo_tema": self.codigo_tema,
            "area_evaluada": self.area_evaluada,
            "tema_principal": self.tema_principal,
            "canal_sugerido": self.canal_sugerido,
            "transcript": self.transcript,
            "tema_tag": self.tema_tag,
            "duration_seconds": self.duration_seconds,
            "thumbnail_url": self.thumbnail_url,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "subject_id": self.subject_id,
            "topic_id": self.topic_id,
            "competencias": self.competencias,
            "componentes": self.componentes,
            "nivel": self.nivel,
            "quality_score": self.quality_score,
            "relevance_score": self.relevance_score,
            "educational_rating": self.educational_rating,
            "is_processed": self.is_processed,
            "has_embeddings": self.has_embeddings,
            "processing_status": self.processing_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_processed_at": self.last_processed_at.isoformat() if self.last_processed_at else None
        }
    
    def extract_youtube_id(self, url):
        """Extrae el ID de YouTube de una URL"""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*?v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_embed_url(self):
        """Genera URL para embebido del video"""
        if self.youtube_id:
            return f"https://www.youtube.com/embed/{self.youtube_id}"
        return None
    
    def get_watch_url(self):
        """Genera URL estándar de YouTube"""
        if self.youtube_id:
            return f"https://www.youtube.com/watch?v={self.youtube_id}"
        return self.url
    
    def generate_embedding_text(self) -> str:
        """Generate text for embedding generation"""
        parts = [
            self.title or "",
            self.description or "",
            self.tema_principal or "",
            self.area_evaluada or "",
            f"level_{self.nivel or 'medio'}",
            f"cognitive_{self.cognitive_level}"
        ]
        return " | ".join(filter(None, parts))
    
    def calculate_engagement_score(self) -> float:
        """Calculate basic engagement score from available metrics"""
        if not self.view_count:
            return 0.0
        
        # Simple engagement calculation based on likes vs views
        if self.view_count > 0 and self.like_count:
            like_ratio = self.like_count / self.view_count
            return min(1.0, like_ratio * 100)  # Scale to 0-1
        
        return 0.5  # Default medium engagement
    
    @classmethod
    def search_by_subject_topic(cls, db_session, subject_id: int = None, topic_id: int = None, limit: int = 10):
        """Search videos by subject and/or topic"""
        query = db_session.query(cls).filter(cls.is_processed == True)
        
        if subject_id:
            query = query.filter(cls.subject_id == subject_id)
        if topic_id:
            query = query.filter(cls.topic_id == topic_id)
        
        return query.order_by(cls.relevance_score.desc()).limit(limit).all()


class VideoStats(Base):
    """Video engagement statistics"""
    __tablename__ = "video_stats"

    video_id = Column(Integer, ForeignKey("youtube_catalog.id", ondelete="CASCADE"), 
                      primary_key=True)
    
    # 7-day rolling metrics
    ctr_7d = Column(DECIMAL(5,4), default=0.0)
    completion_rate_7d = Column(DECIMAL(5,4), default=0.0)
    avg_watch_sec_7d = Column(Integer, default=0)
    unique_views_7d = Column(Integer, default=0)
    
    # 30-day rolling metrics
    ctr_30d = Column(DECIMAL(5,4), default=0.0)
    completion_rate_30d = Column(DECIMAL(5,4), default=0.0)
    avg_watch_sec_30d = Column(Integer, default=0)
    unique_views_30d = Column(Integer, default=0)
    
    # All-time metrics
    total_views = Column(Integer, default=0)
    total_completions = Column(Integer, default=0)
    avg_rating = Column(DECIMAL(3,2), default=0.0)
    total_ratings = Column(Integer, default=0)
    
    # Learning effectiveness
    avg_improvement_score = Column(DECIMAL(5,4), default=0.0)
    helpful_votes = Column(Integer, default=0)
    unhelpful_votes = Column(Integer, default=0)
    
    # Last updated
    last_updated = Column(DateTime, server_default=func.now())
    
    # Relationships
    video = relationship("YoutubeCatalog", backref="stats")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "video_id": self.video_id,
            "ctr_7d": float(self.ctr_7d) if self.ctr_7d else 0.0,
            "completion_rate_7d": float(self.completion_rate_7d) if self.completion_rate_7d else 0.0,
            "avg_watch_sec_7d": self.avg_watch_sec_7d,
            "unique_views_7d": self.unique_views_7d,
            "total_views": self.total_views,
            "total_completions": self.total_completions,
            "avg_rating": float(self.avg_rating) if self.avg_rating else 0.0,
            "helpful_votes": self.helpful_votes,
            "unhelpful_votes": self.unhelpful_votes,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


class StudentVideoInteraction(Base):
    """Student video interactions for personalized recommendations"""
    __tablename__ = "student_video_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), 
                        nullable=False, index=True)
    video_id = Column(Integer, ForeignKey("youtube_catalog.id", ondelete="CASCADE"), 
                      nullable=False, index=True)
    
    # Interaction data
    clicked_at = Column(DateTime, server_default=func.now())
    watch_start_time = Column(DateTime)
    watch_end_time = Column(DateTime)
    total_watch_seconds = Column(Integer, default=0)
    completion_percentage = Column(DECIMAL(5,2), default=0.0)
    
    # Learning context
    question_id = Column(UUID(as_uuid=True), index=True)
    session_id = Column(UUID(as_uuid=True))
    recommendation_source = Column(String(50), index=True)  # 'failed_question', 'topic_review', etc.
    
    # Feedback
    was_helpful = Column(Boolean)
    difficulty_rating = Column(Integer)  # 1-5
    quality_rating = Column(Integer)  # 1-5
    feedback_text = Column(Text)
    
    # Performance tracking
    performance_before = Column(DECIMAL(5,4))
    performance_after = Column(DECIMAL(5,4))
    improvement_delta = Column(DECIMAL(5,4))
    
    # Relationships
    student = relationship("User", backref="video_interactions")
    video = relationship("YoutubeCatalog", backref="interactions")
    
    def __repr__(self):
        return f"<StudentVideoInteraction(student={str(self.student_id)[:8]}, video={self.video_id})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "student_id": str(self.student_id),
            "video_id": self.video_id,
            "clicked_at": self.clicked_at.isoformat() if self.clicked_at else None,
            "total_watch_seconds": self.total_watch_seconds,
            "completion_percentage": float(self.completion_percentage) if self.completion_percentage else 0.0,
            "question_id": str(self.question_id) if self.question_id else None,
            "recommendation_source": self.recommendation_source,
            "was_helpful": self.was_helpful,
            "difficulty_rating": self.difficulty_rating,
            "quality_rating": self.quality_rating,
            "improvement_delta": float(self.improvement_delta) if self.improvement_delta else None
        }


# Optimized indexes for performance
Index(
    'idx_youtube_catalog_subject_topic_processed',
    YoutubeCatalog.subject_id,
    YoutubeCatalog.topic_id,
    YoutubeCatalog.is_processed,
    YoutubeCatalog.processing_status
)

Index(
    'idx_youtube_catalog_embeddings_quality',
    YoutubeCatalog.has_embeddings,
    YoutubeCatalog.quality_score.desc(),
    YoutubeCatalog.relevance_score.desc()
)

# Vector similarity indexes (only if pgvector is available)
if PGVECTOR_AVAILABLE:
    Index(
        'idx_youtube_catalog_combined_embedding_ivfflat',
        YoutubeCatalog.combined_embedding,
        postgresql_using='ivfflat',
        postgresql_with={'lists': 100},
        postgresql_ops={'combined_embedding': 'vector_cosine_ops'}
    )