from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ARRAY, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

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
    questions = relationship("Question", back_populates="topic", cascade="all,delete-orphan")
    diagnostic_answers = relationship("DiagnosticTestAnswer", back_populates="topic")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id = Column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=False)
    
    # Campos de texto de la pregunta
    pregunta_texto = Column(Text, nullable=True)  # Contenido textual de la pregunta
    pregunta_imagen = Column(String(500), nullable=True)  # URL/ruta de la imagen de la pregunta
    
    # Campos de texto de las opciones
    opcion_a_texto = Column(Text, nullable=True)  # Texto de la opción A
    opcion_a_imagen = Column(String(500), nullable=True)  # Imagen de la opción A
    opcion_b_texto = Column(Text, nullable=True)  # Texto de la opción B
    opcion_b_imagen = Column(String(500), nullable=True)  # Imagen de la opción B
    opcion_c_texto = Column(Text, nullable=True)  # Texto de la opción C
    opcion_c_imagen = Column(String(500), nullable=True)  # Imagen de la opción C
    opcion_d_texto = Column(Text, nullable=True)  # Texto de la opción D
    opcion_d_imagen = Column(String(500), nullable=True)  # Imagen de la opción D
    
    # Respuesta correcta
    respuesta_correcta = Column(String(1), nullable=False)  # Letra de la respuesta correcta (a, b, c, d)
    
    # Campos adicionales para compatibilidad
    question_text = Column(Text, nullable=True)  # Campo legacy
    question_type = Column(String(50), default="multiple_choice")
    difficulty = Column(Integer, nullable=False, default=1)
    options = Column(JSON, nullable=True)  # Campo legacy
    correct_answer = Column(String(10), nullable=True)  # Campo legacy
    explanation = Column(Text)
    hint = Column(Text)
    tags = Column(ARRAY(String))
    power_stats = Column(JSON, default={"discrimination_index": 0.5, "success_rate": 0.6})
    
    # Campos de imagen legacy
    # image_url = Column(String(500))  # Main question image - Comentado: columna no existe en la tabla
    # options_images = Column(JSON)  # Images for each option - Comentado: columna no existe en la tabla
    
    # Validation and metadata
    # is_validated = Column(String(20), default="pending")  # pending, validated, rejected - Comentado: columna no existe en la tabla
    # validation_errors = Column(JSON, default=[])  # Comentado: columna no existe en la tabla
    # usage_count = Column(Integer, default=0)  # Comentado: columna no existe en la tabla
    # average_response_time = Column(Integer, default=0)  # in milliseconds - Comentado: columna no existe en la tabla
    # last_used_at = Column(DateTime(timezone=True))  # Comentado: columna no existe en la tabla
    
    # NUEVOS CAMPOS ICFES - Comentados: columnas no existen en la tabla
    # Competencias y componentes
    # competencia = Column(String(150))  # Comentado: columna no existe en la tabla
    # componente = Column(String(50))  # Comentado: columna no existe en la tabla
    # proceso_cognitivo = Column(String(30))  # Comentado: columna no existe en la tabla
    # tipo_conocimiento = Column(String(30))  # Comentado: columna no existe en la tabla
    
    # Parámetros IRT para adaptatividad
    # indice_discriminacion = Column(Float)  # Comentado: columna no existe en la tabla
    # parametro_irt_a = Column(Float)  # Discriminación - Comentado: columna no existe en la tabla
    # parametro_irt_b = Column(Float)  # Dificultad - Comentado: columna no existe en la tabla
    # parametro_irt_c = Column(Float)  # Pseudo-adivinanza - Comentado: columna no existe en la tabla
    
    # Información pedagógica
    # afirmacion = Column(Text)  # Comentado: columna no existe en la tabla
    # evidencia = Column(Text)  # Comentado: columna no existe en la tabla
    # nivel_desempeno_esperado = Column(String(20))  # Comentado: columna no existe en la tabla
    # tiempo_estimado = Column(Integer)  # segundos - Comentado: columna no existe en la tabla
    
    # Sistema de ayuda gradual
    # pista_1 = Column(Text)  # Comentado: columna no existe en la tabla
    # pista_2 = Column(Text)  # Comentado: columna no existe en la tabla
    # pista_3 = Column(Text)  # Comentado: columna no existe en la tabla
    # explicacion_respuesta = Column(Text)  # Comentado: columna no existe en la tabla
    # error_comun = Column(Text)  # Comentado: columna no existe en la tabla
    
    # Análisis de distractores
    # distractor_a_concepto = Column(String(100))  # Comentado: columna no existe en la tabla
    # distractor_b_concepto = Column(String(100))  # Comentado: columna no existe en la tabla
    # distractor_c_concepto = Column(String(100))  # Comentado: columna no existe en la tabla
    # frecuencia_error_a = Column(Float)  # Comentado: columna no existe en la tabla
    # frecuencia_error_b = Column(Float)  # Comentado: columna no existe en la tabla
    # frecuencia_error_c = Column(Float)  # Comentado: columna no existe en la tabla
    
    # Relación con catálogo de temas
    # codigo_tema = Column(String(20), ForeignKey('study_topics_catalog.codigo_tema'))  # Comentado: columna no existe en la tabla
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())  # Comentado: columna no existe en la tabla
    
    # Relationships
    topic = relationship("Topic", back_populates="questions")
    subject = relationship("Subject", back_populates="questions")
    battle_answers = relationship("BattleAnswer", back_populates="question", cascade="all,delete-orphan")
    ai_explanations = relationship("AIExplanation", back_populates="question", cascade="all,delete-orphan")
    quiz_answers = relationship("QuizAnswer", back_populates="question", cascade="all,delete-orphan")
    diagnostic_answers = relationship("DiagnosticTestAnswer", back_populates="question")
    
    # Relación con catálogo de temas ICFES - Comentado: columna no existe en la tabla
    # topic_catalog = relationship("StudyTopicsCatalog", back_populates="questions", foreign_keys="Question.codigo_tema")

    def validate_question(self):
        """Validate question data and return errors"""
        errors = []
        
        # 1) Validar contenido de la pregunta (aceptar campos legacy)
        if not (self.pregunta_texto or self.pregunta_imagen or self.question_text):
            errors.append("La pregunta debe tener al menos texto o imagen")
        
        # 2) Validar que exista al menos una opción con contenido (texto, imagen o legacy options)
        def opcion_tiene_contenido(letra: str) -> bool:
            texto_attr = f'opcion_{letra}_texto'
            imagen_attr = f'opcion_{letra}_imagen'
            texto = getattr(self, texto_attr)
            imagen = getattr(self, imagen_attr)
            legacy_text = None
            if isinstance(self.options, dict):
                legacy_text = self.options.get(letra.upper()) or self.options.get(letra.lower())
            legacy_img = None
            # if isinstance(self.options_images, dict):  # Comentado: columna no existe en la tabla
            #     legacy_img = self.options_images.get(letra.upper()) or self.options_images.get(letra.lower())
            return bool(texto or imagen or legacy_text or legacy_img)

        opciones_con_contenido = sum(1 for l in ['a', 'b', 'c', 'd'] if opcion_tiene_contenido(l))
        if opciones_con_contenido == 0:
            errors.append("Debe haber al menos una opción con contenido (texto o imagen)")
        
        # 3) Normalizar y validar respuesta correcta
        correct_letter = (self.respuesta_correcta or '').strip().lower()
        if correct_letter not in ['a', 'b', 'c', 'd']:
            # intentar fallback a campo legacy correct_answer
            if isinstance(self.correct_answer, str) and self.correct_answer.strip():
                ca = self.correct_answer.strip().lower()
                if ca in ['a', 'b', 'c', 'd']:
                    correct_letter = ca
                else:
                    errors.append("La respuesta correcta debe ser a, b, c o d")
            else:
                errors.append("La respuesta correcta debe ser a, b, c o d")
        
        # 4) Validar que la opción correcta tenga contenido (aceptando legacy e imágenes)
        if correct_letter in ['a', 'b', 'c', 'd']:
            if not opcion_tiene_contenido(correct_letter):
                errors.append(f"La opción {correct_letter.upper()} (respuesta correcta) debe tener contenido")
        
        # 5) Validar difficulty
        if not 1 <= self.difficulty <= 10:
            errors.append("Difficulty must be between 1 and 10")
        
        return errors

    def get_options_dict(self):
        """Retorna las opciones en formato diccionario para compatibilidad"""
        options = {}
        for letra in ['a', 'b', 'c', 'd']:
            texto = getattr(self, f'opcion_{letra}_texto')
            imagen = getattr(self, f'opcion_{letra}_imagen')
            if texto or imagen:
                options[letra.upper()] = {
                    'texto': texto,
                    'imagen': imagen
                }
        return options

    def update_usage_stats(self, response_time_ms: int, is_correct: bool):
        """Update question usage statistics"""
        self.usage_count += 1
        self.last_used_at = func.now()
        
        # Update average response time
        if self.average_response_time == 0:
            self.average_response_time = response_time_ms
        else:
            self.average_response_time = (self.average_response_time + response_time_ms) // 2
        
        # Update power stats
        if not self.power_stats:
            self.power_stats = {"discrimination_index": 0.5, "success_rate": 0.6}
        
        # Update success rate
        current_success_rate = self.power_stats.get("success_rate", 0.6)
        total_answers = self.usage_count
        correct_answers = int(current_success_rate * (total_answers - 1)) + (1 if is_correct else 0)
        new_success_rate = correct_answers / total_answers
        self.power_stats["success_rate"] = round(new_success_rate, 3)

    def get_difficulty_rating(self) -> float:
        """Calculate difficulty rating based on usage statistics"""
        if self.usage_count < 10:
            return self.difficulty  # Return base difficulty if not enough data
        
        # Calculate difficulty based on success rate and response time
        success_rate = self.power_stats.get("success_rate", 0.6)
        avg_response_time = self.average_response_time / 1000  # Convert to seconds
        
        # Difficulty increases with lower success rate and higher response time
        difficulty_score = (1 - success_rate) * 5 + min(avg_response_time / 30, 5)
        return round(min(max(difficulty_score, 1), 10), 1)
    
    def get_irt_probability(self, theta: float) -> float:
        """
        Calcula la probabilidad de respuesta correcta usando modelo 3PL de IRT
        WHY: Permite adaptatividad real basada en teoría psicométrica
        """
        import math
        a = self.parametro_irt_a or 1.0
        b = self.parametro_irt_b or 0.0
        c = self.parametro_irt_c or 0.25
        
        # Modelo 3PL: P(θ) = c + (1-c)/(1+e^(-a(θ-b)))
        try:
            exp_val = math.exp(-a * (theta - b))
            return c + (1 - c) / (1 + exp_val)
        except:
            return 0.5
    
    def get_optimal_hint(self, error_type: str) -> str:
        """
        Retorna la pista más apropiada según el tipo de error
        WHY: Scaffolding personalizado según el patrón de error
        """
        if error_type == 'conceptual' and self.pista_1:
            return self.pista_1
        elif error_type == 'procedural' and self.pista_2:
            return self.pista_2
        elif error_type == 'computational' and self.pista_3:
            return self.pista_3
        return self.pista_1 or "Revisa el concepto principal" 