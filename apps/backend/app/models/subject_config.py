"""Dynamic Subject Configuration Model"""
from sqlalchemy import Column, String, Integer, Text, JSON, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..core.database import Base

class SubjectConfig(Base):
    """Dynamic configuration for subjects"""
    __tablename__ = "subject_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.id'), nullable=False)
    
    # Test Configuration
    total_questions = Column(Integer, default=45)
    time_limit_minutes = Column(Integer, default=60)
    passing_score = Column(Integer, default=75)
    
    # Display Configuration
    icon_url = Column(String(500))
    color_primary = Column(String(20))
    color_secondary = Column(String(20))
    description_short = Column(Text)
    description_long = Column(Text)
    
    # Learning Configuration
    topics = Column(JSON)  # Dynamic list of topics
    difficulty_levels = Column(JSON)  # Custom difficulty mapping
    study_sequence = Column(JSON)  # Recommended learning path
    
    # Administrative
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subject = relationship("Subject", )

class SubjectAlias(Base):
    """Alternative names for subjects for intelligent mapping"""
    __tablename__ = "subject_aliases"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey('subjects.id'), nullable=False)
    alias_name = Column(String(100), nullable=False)
    is_primary = Column(Boolean, default=False)
    language = Column(String(10), default='es')
    
    # Relationships
    subject = relationship("Subject", )

class AssetConfiguration(Base):
    """Dynamic asset management"""
    __tablename__ = "asset_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)  # 'subject', 'hero_class', 'achievement'
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    asset_type = Column(String(50), nullable=False)  # 'icon', 'banner', 'audio'
    asset_url = Column(String(500), nullable=False)
    asset_description = Column(Text)
    is_default = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())