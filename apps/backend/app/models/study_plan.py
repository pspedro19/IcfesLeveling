from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, JSON, DECIMAL, ARRAY
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

class StudyPlan(Base):
    __tablename__ = "study_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    plan_name = Column(String(200), nullable=False)
    plan_data = Column(JSON, nullable=False)  # Contiene el YML generado
    total_units = Column(Integer, default=8)
    completed_units = Column(Integer, default=0)
    progress_percentage = Column(DECIMAL(5,2), default=0.00)
    is_active = Column(Boolean, default=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    #     user = relationship("User", )
    subject = relationship("Subject", )
    #     progress = # relationship("relationship("PlanProgress",", cascade="all, delete-orphan")
    #     video_tracking = # relationship("relationship("VideoTracking",", cascade="all, delete-orphan")
    #     quizzes = # relationship("relationship("Quiz",", cascade="all, delete-orphan")

class PlanProgress(Base):
    __tablename__ = "plan_progress"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("study_plans.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    unit_name = Column(String(200), nullable=False)
    unit_description = Column(Text)
    unit_content = Column(JSON)  # Videos, ejercicios, recursos
    is_completed = Column(Boolean, default=False)
    completion_date = Column(DateTime(timezone=True))
    score = Column(DECIMAL(5,2), default=0.00)
    weighted_progress = Column(JSON, default={
        "videos": {"completed": 0, "total": 0, "weight": 0.3},
        "exercises": {"completed": 0, "total": 0, "weight": 0.5},
        "readings": {"completed": 0, "total": 0, "weight": 0.2}
    })
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    plan = relationship("StudyPlan", )

class StudyPlanTemplate(Base):
    __tablename__ = "study_plan_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    unit_number = Column(Integer, nullable=False)
    unit_name = Column(String(200), nullable=False)
    unit_description = Column(Text)
    topics = Column(ARRAY(Text))  # Array de temas
    video_urls = Column(JSON)  # URLs de videos de YouTube por tema
    exercise_count = Column(Integer, default=15)  # Número de ejercicios por unidad
    reading_materials = Column(JSON)  # Enlaces a material de lectura
    recommendations_priority = Column(String(10), default='medium')
    weak_areas = Column(ARRAY(Text))
    focus_topics = Column(ARRAY(Text))
    study_time = Column(String(50))
    difficulty_level = Column(Integer, default=2)
    icfes_weight = Column(DECIMAL(3,2), default=0.25)
    estimated_hours = Column(Integer, default=4)
    prerequisite_units = Column(ARRAY(Integer))  # Unidades prerequisito
    learning_objectives = Column(ARRAY(Text))  # Objetivos de aprendizaje
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subject = relationship("Subject") 