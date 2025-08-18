from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..core.database import Base


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    icon_url = Column(String(500))
    color = Column(String(7), default="#3b0f6f")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    topics = relationship("Topic", back_populates="subject", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="subject", cascade="all, delete-orphan")
    diagnostic_tests = relationship("DiagnosticTest", back_populates="subject")
    study_plans = relationship("StudyPlan", back_populates="subject")
    config = relationship("SubjectConfig", back_populates="subject", uselist=False)
    aliases = relationship("SubjectAlias", back_populates="subject", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject(id={self.id}, name='{self.name}')>" 