from sqlalchemy import Column, String, ForeignKey, Text, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from ..core.database import Base

class Topic(Base):
    __tablename__ = "topics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    # codigo_tema = Column(String(50), unique=True, nullable=True, index=True)  # Column doesn't exist in current table
    difficulty_level = Column(Integer, default=1)  # Changed to Integer for consistency
    # order_index = Column(Integer, default=0)  # Column doesn't exist in current table
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # IRT parameters for adaptive testing (Commented: columns don't exist in current table)
    # difficulty_parameter = Column(Float, default=0.0)  # Column doesn't exist in current table
    # discrimination_parameter = Column(Float, default=1.0)  # Column doesn't exist in current table
    
    # Relationships
    subject = relationship("Subject", )
    questions = relationship("Question", )
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "name": self.name,
            "description": self.description,
            # "codigo_tema": self.codigo_tema,  # Field doesn't exist in current table
            "difficulty_level": self.difficulty_level,
            # "order_index": self.order_index  # Field doesn't exist in current table
        }