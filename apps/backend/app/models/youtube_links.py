"""
Modelo SQLAlchemy para YouTube Links
Tabla que mapea temas ICFES con videos educativos de YouTube
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DECIMAL, DateTime, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from ..core.database import Base
import uuid

class YouTubeLinks(Base):
    __tablename__ = "youtube_links"
    
    # Primary Key
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Topic Mapping
    codigo_tema = Column(String(10), nullable=False, index=True)
    area_evaluada = Column(String(100), nullable=False, index=True)
    tema_principal = Column(Text, nullable=False)
    
    # YouTube Information
    canal_sugerido = Column(String(100))
    query_sugerida = Column(Text, nullable=False)
    youtube_url = Column(Text, nullable=False)
    
    # Video Metadata (populated by YouTube API)
    youtube_id = Column(String(20), index=True)
    video_title = Column(Text)
    channel_name = Column(String(255))
    channel_id = Column(String(50))
    duration_seconds = Column(Integer)
    view_count = Column(Integer)
    like_count = Column(Integer)
    dislike_count = Column(Integer)
    comment_count = Column(Integer)
    
    # Educational Metrics
    tipo_contenido = Column(String(50), default='explicativo')  # explicativo, ejercicio_guiado, resumen, etc.
    nivel_dificultad = Column(Integer, default=3, index=True)  # 1-5 scale
    proceso_cognitivo = Column(String(50), default='Comprender')  # Comprender, Aplicar, Analizar, Evaluar
    contexto_aplicacion = Column(String(50), default='Académico')  # Académico, Familiar, Laboral, Comunitario
    
    # Quality Metrics
    calidad_score = Column(DECIMAL(3, 2), default=0.80, index=True)
    relevancia_score = Column(DECIMAL(3, 2), default=0.85, index=True)
    ratio_likes = Column(DECIMAL(3, 2))
    
    # Learning Metadata
    prerequisitos_video = Column(ARRAY(PostgresUUID(as_uuid=True)), default=[])
    tiempo_estimado_estudio = Column(Integer, default=15)  # minutes
    puntos_xp = Column(Integer, default=50, index=True)
    orden_recomendacion = Column(Integer, default=1, index=True)
    
    # Verification
    verificado_instructor = Column(Boolean, default=False)
    fecha_verificacion = Column(DateTime(timezone=True))
    
    # Status
    estado = Column(String(20), default='activo', index=True)  # activo, inactivo, pendiente_revision
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_validated_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<YouTubeLinks(id={self.id}, codigo_tema='{self.codigo_tema}', tema='{self.tema_principal}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': str(self.id),
            'codigo_tema': self.codigo_tema,
            'area_evaluada': self.area_evaluada,
            'tema_principal': self.tema_principal,
            'canal_sugerido': self.canal_sugerido,
            'query_sugerida': self.query_sugerida,
            'youtube_url': self.youtube_url,
            'youtube_id': self.youtube_id,
            'video_title': self.video_title,
            'channel_name': self.channel_name,
            'duration_seconds': self.duration_seconds,
            'tipo_contenido': self.tipo_contenido,
            'nivel_dificultad': self.nivel_dificultad,
            'proceso_cognitivo': self.proceso_cognitivo,
            'contexto_aplicacion': self.contexto_aplicacion,
            'calidad_score': float(self.calidad_score) if self.calidad_score else None,
            'relevancia_score': float(self.relevancia_score) if self.relevancia_score else None,
            'tiempo_estimado_estudio': self.tiempo_estimado_estudio,
            'puntos_xp': self.puntos_xp,
            'orden_recomendacion': self.orden_recomendacion,
            'estado': self.estado,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
