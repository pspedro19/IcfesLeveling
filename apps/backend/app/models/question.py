from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

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
    questions = relationship("Question", back_populates="subject")

class Topic(Base):
    __tablename__ = "topics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    difficulty_level = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subject = relationship("Subject", back_populates="topics")
    questions = relationship("Question", back_populates="topic")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default="multiple_choice")
    difficulty = Column(Integer, nullable=False)
    correct_answer = Column(String(10), nullable=False)
    options = Column(JSON, nullable=False)
    explanation = Column(Text)
    hint = Column(Text)
    tags = Column(ARRAY(String))
    power_stats = Column(JSON, default={"discrimination_index": 0.5, "success_rate": 0.6})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    topic = relationship("Topic", back_populates="questions")
    subject = relationship("Subject", back_populates="questions")
    battle_answers = relationship("BattleAnswer", back_populates="question")
    ai_explanations = relationship("AIExplanation", back_populates="question") 