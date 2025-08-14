from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON, Text, ForeignKey, ARRAY, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.database import Base

class DiagnosticTestAnalytics(Base):
    __tablename__ = "diagnostic_test_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    diagnostic_test_id = Column(UUID(as_uuid=True), ForeignKey("diagnostic_tests.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    
    # Estadísticas básicas
    total_questions = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    wrong_answers = Column(Integer, nullable=False)
    unanswered_questions = Column(Integer, default=0)
    score_percentage = Column(DECIMAL(5,2), nullable=False)
    
    # Análisis por competencia y componente
    competency_scores = Column(JSON, default={})  # Score por competencia del ICFES
    component_scores = Column(JSON, default={})   # Score por componente
    cognitive_process_scores = Column(JSON, default={})  # Score por proceso cognitivo
    
    # Análisis temporal
    total_time_seconds = Column(Integer, nullable=False)
    average_time_per_question = Column(DECIMAL(8,2))
    time_per_topic = Column(JSON, default={})
    questions_with_slow_response = Column(JSON, default=[])  # IDs de preguntas con respuesta lenta
    questions_with_fast_response = Column(JSON, default=[])  # IDs de preguntas con respuesta rápida
    
    # Análisis de dificultad
    difficulty_performance = Column(JSON, default={})  # Performance por nivel de dificultad
    easy_questions_score = Column(DECIMAL(5,2), default=0)
    medium_questions_score = Column(DECIMAL(5,2), default=0)
    hard_questions_score = Column(DECIMAL(5,2), default=0)
    
    # Patrones de respuesta
    response_patterns = Column(JSON, default={})  # Patrones de respuesta
    confidence_indicators = Column(JSON, default={})  # Indicadores de confianza
    
    # Análisis comparativo
    percentile_rank = Column(DECIMAL(5,2))  # Percentil respecto a otros usuarios
    performance_vs_expected = Column(DECIMAL(5,2))  # Performance vs expectativa
    
    # Recomendaciones inteligentes
    recommended_topics = Column(ARRAY(Text))  # Temas recomendados para estudio
    critical_weaknesses = Column(ARRAY(Text))  # Debilidades críticas identificadas
    learning_style_indicators = Column(JSON, default={})  # Indicadores de estilo de aprendizaje
    
    # Metadatos
    analysis_version = Column(String(10), default='1.0')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    diagnostic_test = relationship("DiagnosticTest")
    user = relationship("User")
    subject = relationship("Subject")

class DiagnosticImprovementTracking(Base):
    __tablename__ = "diagnostic_improvement_tracking"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    
    # Métricas de mejora
    first_test_score = Column(DECIMAL(5,2))
    latest_test_score = Column(DECIMAL(5,2))
    improvement_percentage = Column(DECIMAL(5,2))
    tests_taken = Column(Integer, default=1)
    
    # Análisis de tendencias
    score_trend = Column(JSON, default=[])  # Array de scores históricos
    topic_improvement = Column(JSON, default={})  # Mejora por tema
    consistency_score = Column(DECIMAL(5,2))  # Qué tan consistente es el rendimiento
    
    # Predicciones
    predicted_icfes_score = Column(DECIMAL(5,2))  # Score ICFES predicho
    confidence_level = Column(DECIMAL(5,2))  # Nivel de confianza en la predicción
    estimated_study_time_hours = Column(Integer)  # Tiempo estimado de estudio
    
    # Hitos y objetivos
    milestones_achieved = Column(JSON, default=[])  # Hitos alcanzados
    next_milestone = Column(JSON, default={})  # Próximo hito
    goal_score = Column(DECIMAL(5,2))  # Score objetivo
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    subject = relationship("Subject")

class DiagnosticErrorPattern(Base):
    __tablename__ = "diagnostic_error_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=True)
    
    # Tipo de error
    error_type = Column(String(100), nullable=False)  # 'conceptual', 'procedural', 'computational', 'reading'
    error_description = Column(Text)
    frequency = Column(Integer, default=1)
    
    # Contexto del error
    difficulty_level = Column(Integer)
    question_types = Column(ARRAY(Text))  # Tipos de pregunta donde ocurre el error
    cognitive_process = Column(String(100))  # Proceso cognitivo involucrado
    
    # Soluciones sugeridas
    recommended_actions = Column(JSON, default=[])
    study_resources = Column(JSON, default=[])
    practice_exercises = Column(JSON, default=[])
    
    # Seguimiento
    error_resolved = Column(Boolean, default=False)
    last_occurrence = Column(DateTime(timezone=True), server_default=func.now())
    resolution_date = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    subject = relationship("Subject")
    topic = relationship("Topic")