from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

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
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_processed_at = Column(DateTime, nullable=True)
    
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