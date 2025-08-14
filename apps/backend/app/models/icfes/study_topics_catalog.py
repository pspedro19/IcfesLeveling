"""
Modelo para el catálogo maestro de temas ICFES
WHY: Centraliza los 337 temas con toda su metadata pedagógica
"""

from sqlalchemy import Column, String, Integer, Float, Text, ARRAY, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from typing import List, Optional

from ...core.database import Base

class StudyTopicsCatalog(Base):
    __tablename__ = "study_topics_catalog"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    codigo_tema = Column(String(20), unique=True, nullable=False, index=True)
    area_evaluada = Column(String(30), nullable=False, index=True)
    tema_principal = Column(String(100), nullable=False)
    subtema = Column(String(100))
    tema_especifico = Column(String(150))
    
    # Clasificación ICFES
    competencia_icfes = Column(String(150), nullable=False)
    componente = Column(String(50))
    afirmacion = Column(Text)
    evidencia = Column(Text)
    
    # Estructura curricular
    grado_introduccion = Column(String(10))
    prerequisitos = Column(ARRAY(Text))
    temas_relacionados = Column(ARRAY(Text))
    
    # Configuración pedagógica
    orden_secuencial = Column(Integer)
    nivel_dificultad = Column(Integer)
    importancia_icfes = Column(Integer)
    frecuencia_evaluacion = Column(Float)
    
    # Tiempo de estudio
    horas_teoria = Column(Integer)
    horas_practica = Column(Integer)
    numero_ejercicios_recomendados = Column(Integer)
    sesiones_refuerzo = Column(Integer)
    
    # Recursos
    recursos_teoria = Column(ARRAY(Text))
    recursos_practica = Column(ARRAY(Text))
    recursos_evaluacion = Column(ARRAY(Text))
    
    # Métricas
    umbral_dominio = Column(Float)
    tiempo_retencion = Column(Integer)
    indicadores_dominio = Column(ARRAY(Text))
    
    # Personalización
    estilo_aprendizaje_optimo = Column(String(30))
    metodologia_recomendada = Column(String(50))
    tipo_evaluacion = Column(String(30))
    
    # Metadatos
    estado = Column(String(20), default='activo')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relaciones
    # questions = relationship("Question", back_populates="topic_catalog", foreign_keys="Question.codigo_tema")  # Comentado: columna no existe en la tabla Question
    # performances = relationship("TopicPerformanceAnalytics", back_populates="topic")
    # resources = relationship("LearningResource", back_populates="topic")
    
    def get_learning_path(self) -> List[str]:
        """Retorna la ruta de aprendizaje incluyendo prerequisitos"""
        path = []
        if self.prerequisitos:
            path.extend(self.prerequisitos)
        path.append(self.codigo_tema)
        return path
    
    def calculate_study_hours(self) -> int:
        """Calcula el total de horas necesarias para dominar el tema"""
        return (self.horas_teoria or 0) + (self.horas_practica or 0)
    
    def is_prerequisite_for(self, other_topic: str) -> bool:
        """Verifica si este tema es prerequisito para otro"""
        if self.temas_relacionados:
            return other_topic in self.temas_relacionados
        return False
    
    def get_difficulty_level(self) -> str:
        """Retorna el nivel de dificultad en texto"""
        levels = {
            1: "Básico",
            2: "Intermedio bajo",
            3: "Intermedio",
            4: "Intermedio alto",
            5: "Avanzado"
        }
        return levels.get(self.nivel_dificultad, "No especificado")
    
    def get_importance_level(self) -> str:
        """Retorna el nivel de importancia en texto"""
        levels = {
            1: "Muy baja",
            2: "Baja",
            3: "Media",
            4: "Alta",
            5: "Muy alta"
        }
        return levels.get(self.importancia_icfes, "No especificada")
    
    def get_optimal_study_time(self) -> int:
        """Calcula el tiempo óptimo de estudio en minutos"""
        base_time = self.calculate_study_hours() * 60  # Convertir a minutos
        
        # Ajustar por dificultad
        if self.nivel_dificultad >= 4:
            base_time *= 1.5  # 50% más tiempo para temas difíciles
        elif self.nivel_dificultad <= 2:
            base_time *= 0.8  # 20% menos tiempo para temas fáciles
        
        return int(base_time)
    
    def get_recommended_exercises(self) -> int:
        """Retorna el número recomendado de ejercicios"""
        base_exercises = self.numero_ejercicios_recomendados or 50
        
        # Ajustar por importancia
        if self.importancia_icfes >= 4:
            base_exercises = int(base_exercises * 1.3)  # 30% más ejercicios para temas importantes
        
        return base_exercises
    
    def to_dict(self) -> dict:
        """Convierte el modelo a diccionario para serialización"""
        return {
            'id': str(self.id),
            'codigo_tema': self.codigo_tema,
            'area_evaluada': self.area_evaluada,
            'tema_principal': self.tema_principal,
            'subtema': self.subtema,
            'tema_especifico': self.tema_especifico,
            'competencia_icfes': self.competencia_icfes,
            'componente': self.componente,
            'afirmacion': self.afirmacion,
            'evidencia': self.evidencia,
            'grado_introduccion': self.grado_introduccion,
            'prerequisitos': self.prerequisitos or [],
            'temas_relacionados': self.temas_relacionados or [],
            'orden_secuencial': self.orden_secuencial,
            'nivel_dificultad': self.nivel_dificultad,
            'importancia_icfes': self.importancia_icfes,
            'frecuencia_evaluacion': self.frecuencia_evaluacion,
            'horas_teoria': self.horas_teoria,
            'horas_practica': self.horas_practica,
            'numero_ejercicios_recomendados': self.numero_ejercicios_recomendados,
            'sesiones_refuerzo': self.sesiones_refuerzo,
            'recursos_teoria': self.recursos_teoria or [],
            'recursos_practica': self.recursos_practica or [],
            'recursos_evaluacion': self.recursos_evaluacion or [],
            'umbral_dominio': self.umbral_dominio,
            'tiempo_retencion': self.tiempo_retencion,
            'indicadores_dominio': self.indicadores_dominio or [],
            'estilo_aprendizaje_optimo': self.estilo_aprendizaje_optimo,
            'metodologia_recomendada': self.metodologia_recomendada,
            'tipo_evaluacion': self.tipo_evaluacion,
            'estado': self.estado,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"<StudyTopicsCatalog(codigo_tema='{self.codigo_tema}', area='{self.area_evaluada}', tema='{self.tema_principal}')>"
    
    def __str__(self):
        return f"{self.codigo_tema}: {self.tema_principal} ({self.area_evaluada})"
