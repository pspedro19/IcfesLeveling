from sqlalchemy import Column, Integer, String, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from ..core.database import Base

class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    codigo_tema = Column(String(50), unique=True, nullable=True, index=True)
    difficulty_level = Column(String(50), nullable=True)
    order_index = Column(Integer, default=0)
    
    # IRT parameters for adaptive testing
    difficulty_parameter = Column(Float, default=0.0)
    discrimination_parameter = Column(Float, default=1.0)
    
    # Relationships
    subject = relationship("Subject", back_populates="topics")
    questions = relationship("Question", back_populates="topic")
    
    def __repr__(self):
        return f"<Topic(id={self.id}, name='{self.name}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "subject_id": self.subject_id,
            "name": self.name,
            "description": self.description,
            "codigo_tema": self.codigo_tema,
            "difficulty_level": self.difficulty_level,
            "order_index": self.order_index
        }