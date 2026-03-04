from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import logging
from ..core.database import Base

logger = logging.getLogger("icfes.models.content_embeddings")

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    # Fallback si pgvector no está disponible
    from sqlalchemy import Text as Vector
    PGVECTOR_AVAILABLE = False

class ContentEmbeddings(Base):
    """
    Modelo para almacenar embeddings vectoriales del contenido educativo
    Soporta pgvector para búsquedas de similaridad eficientes
    """
    __tablename__ = "content_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    
    # Referencia al contenido
    content_type = Column(String(50), nullable=False, index=True)  # 'youtube_video', 'icfes_question', etc.
    content_id = Column(Integer, nullable=False, index=True)  # ID del contenido referenciado
    content_uuid = Column(UUID(as_uuid=True), nullable=True, index=True)  # UUID del contenido si lo tiene
    
    # Metadatos del embedding
    embedding_type = Column(String(50), nullable=False, index=True)  # 'title', 'description', 'transcript', 'combined'
    model_name = Column(String(100), nullable=False, default='text-embedding-3-large')
    model_version = Column(String(50), nullable=True)
    vector_dimensions = Column(Integer, nullable=False, default=3072)  # text-embedding-3-large usa 3072 dimensiones
    
    # Vector embedding - usar pgvector si está disponible
    if PGVECTOR_AVAILABLE:
        embedding_vector = Column(Vector(3072), nullable=False)  # pgvector
    else:
        embedding_vector = Column(ARRAY(Float), nullable=False)  # fallback a array
    
    # Texto original usado para generar el embedding
    source_text = Column(Text, nullable=False)
    source_text_hash = Column(String(64), nullable=False, index=True)  # MD5/SHA256 del texto
    
    # Metadatos del contenido para facilitar búsquedas
    subject_area = Column(String(100), nullable=True, index=True)  # Matemáticas, Ciencias, etc.
    topic = Column(String(255), nullable=True, index=True)
    difficulty_level = Column(String(50), nullable=True, index=True)  # Básico, Intermedio, Avanzado
    language = Column(String(10), nullable=False, default='es', index=True)
    
    # Scoring y calidad del embedding
    confidence_score = Column(Float, default=1.0)  # Confianza en la calidad del embedding
    processing_time_ms = Column(Integer, nullable=True)  # Tiempo que tomó generar el embedding
    token_count = Column(Integer, nullable=True)  # Número de tokens procesados
    
    # Estado y versionado
    is_active = Column(String(10), nullable=False, default='true', index=True)  # Para soft delete/versioning
    version = Column(Integer, nullable=False, default=1)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    def __repr__(self):
        return f"<ContentEmbeddings(id={self.id}, content_type='{self.content_type}', embedding_type='{self.embedding_type}')>"
    
    def to_dict(self, include_vector=False):
        result = {
            "id": self.id,
            "uuid": str(self.uuid),
            "content_type": self.content_type,
            "content_id": self.content_id,
            "content_uuid": str(self.content_uuid) if self.content_uuid else None,
            "embedding_type": self.embedding_type,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "vector_dimensions": self.vector_dimensions,
            "source_text_preview": self.source_text[:200] + "..." if len(self.source_text) > 200 else self.source_text,
            "subject_area": self.subject_area,
            "topic": self.topic,
            "difficulty_level": self.difficulty_level,
            "language": self.language,
            "confidence_score": self.confidence_score,
            "processing_time_ms": self.processing_time_ms,
            "token_count": self.token_count,
            "is_active": self.is_active,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_vector and self.embedding_vector:
            if PGVECTOR_AVAILABLE:
                result["embedding_vector"] = list(self.embedding_vector)
            else:
                result["embedding_vector"] = self.embedding_vector
        
        return result
    
    @classmethod
    def create_text_hash(cls, text):
        """Genera hash del texto para detectar cambios"""
        import hashlib
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def calculate_similarity(self, other_embedding):
        """Calcula similaridad coseno entre dos embeddings"""
        if not self.embedding_vector or not other_embedding:
            return 0.0
        
        try:
            import numpy as np
            v1 = np.array(self.embedding_vector)
            v2 = np.array(other_embedding)
            
            # Similaridad coseno
            dot_product = np.dot(v1, v2)
            norm_v1 = np.linalg.norm(v1)
            norm_v2 = np.linalg.norm(v2)
            
            if norm_v1 == 0 or norm_v2 == 0:
                return 0.0
                
            return dot_product / (norm_v1 * norm_v2)
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0

# Índices especializados para búsquedas eficientes
if PGVECTOR_AVAILABLE:
    # Índice HNSW para búsquedas vectoriales ultra-rápidas
    Index(
        'idx_content_embeddings_vector_hnsw',
        ContentEmbeddings.embedding_vector,
        postgresql_using='hnsw',
        postgresql_with={'m': 16, 'ef_construction': 64},
        postgresql_ops={'embedding_vector': 'vector_cosine_ops'}
    )
    
    # Índice IVFFlat para datasets más grandes (alternativo)
    Index(
        'idx_content_embeddings_vector_ivfflat',
        ContentEmbeddings.embedding_vector,
        postgresql_using='ivfflat',
        postgresql_with={'lists': 100},
        postgresql_ops={'embedding_vector': 'vector_cosine_ops'}
    )

# Índices compuestos para consultas filtradas
Index(
    'idx_content_embeddings_type_active',
    ContentEmbeddings.content_type,
    ContentEmbeddings.embedding_type,
    ContentEmbeddings.is_active
)

Index(
    'idx_content_embeddings_subject_topic',
    ContentEmbeddings.subject_area,
    ContentEmbeddings.topic,
    ContentEmbeddings.difficulty_level
)

Index(
    'idx_content_embeddings_content_lookup',
    ContentEmbeddings.content_type,
    ContentEmbeddings.content_id,
    ContentEmbeddings.is_active
)