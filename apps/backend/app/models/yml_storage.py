from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, UUID
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
import uuid

from ..core.database import Base

class UserYMLPlan(Base):
    """
    Modelo para almacenar metadata de planes YML personalizados
    Solo almacena referencias, NO el contenido del YML
    """
    __tablename__ = "user_yml_plans"
    
    # Identificadores
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(PostgresUUID(as_uuid=True), nullable=False, index=True)
    subject = Column(String(50), nullable=False, index=True)
    
    # Información de almacenamiento
    storage_type = Column(String(20), nullable=False)  # 'local', 'spaces', 's3'
    storage_path = Column(Text, nullable=False)        # Ruta completa al archivo
    storage_url = Column(Text)                         # URL CDN si está disponible
    
    # Metadata del archivo
    file_size_bytes = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)     # MD5 hash para validación
    version = Column(Integer, default=1)
    
    # Detalles de generación
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generation_time_ms = Column(Integer)                # Tiempo de generación en ms
    algorithm_version = Column(String(20), default='1.0')
    
    # Control de cache
    cache_key = Column(String(100), nullable=False)    # Clave Redis
    cache_ttl = Column(Integer, default=3600)          # TTL en segundos
    
    # Estadísticas de uso
    last_accessed = Column(DateTime(timezone=True))
    access_count = Column(Integer, default=0)
    
    # Estado
    is_active = Column(Boolean, default=True)
    is_outdated = Column(Boolean, default=False)       # Necesita regeneración
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    class Config:
        # Configuración para Pydantic si se usa
        from_attributes = True
    
    def __repr__(self):
        return f"<UserYMLPlan(user_id={self.user_id}, subject={self.subject}, version={self.version})>"
    
    @property
    def file_size_mb(self) -> float:
        """Tamaño del archivo en MB"""
        return round(self.file_size_bytes / (1024 * 1024), 2)
    
    @property
    def is_cached(self) -> bool:
        """Verifica si el YML está en cache"""
        return self.last_accessed is not None
    
    @property
    def cache_age_hours(self) -> float:
        """Edad del cache en horas"""
        if not self.last_accessed:
            return float('inf')
        from datetime import datetime
        age = datetime.utcnow() - self.last_accessed
        return age.total_seconds() / 3600
