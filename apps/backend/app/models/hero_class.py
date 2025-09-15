from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class HeroClass(Base):
    __tablename__ = "hero_classes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    description = Column(Text)
    avatar_url = Column(String(500))
    stats_boost = Column(JSON, default={})
    special_ability = Column(String(200))
    element = Column(String(20))  # 'Fuego', 'Tierra', 'Viento', 'Luz', 'Sombra'
    color_theme = Column(String(7))  # Color principal de la clase
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user_profiles = relationship("UserProfile", )
    
    def __repr__(self):
        return f"<HeroClass(id={self.id}, name='{self.name}', element='{self.element}')>"
    
    @property
    def class_type(self):
        """Get the class type from name"""
        if "Mago" in self.name:
            return "mage"
        elif "Guerrero" in self.name:
            return "warrior"
        elif "Arquero" in self.name:
            return "archer"
        elif "Sacerdote" in self.name:
            return "priest"
        elif "Asesino" in self.name:
            return "assassin"
        return "unknown"
    
    def get_stats_boost(self):
        """Get stats boost as dictionary"""
        return self.stats_boost if self.stats_boost else {} 