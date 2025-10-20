from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ARRAY, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

# Topic class is defined in topic.py - removed duplicate definition here

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
    
    # CAMPOS ICFES - Competencias y componentes
    competencia = Column(String(255), nullable=True)  # ICFES competency
    componente = Column(String(100), nullable=True)  # ICFES component
    proceso_cognitivo = Column(String(50), nullable=True)  # Cognitive process
    tipo_conocimiento = Column(String(50), nullable=True)  # Knowledge type

    # Parámetros IRT para adaptatividad
    indice_discriminacion = Column(Float, default=0.5)  # Discrimination index
    parametro_irt_a = Column(Float, default=1.0)  # Discriminación - IRT parameter A
    parametro_irt_b = Column(Float, default=0.0)  # Dificultad - IRT parameter B
    parametro_irt_c = Column(Float, default=0.25)  # Pseudo-adivinanza - IRT parameter C

    # Información pedagógica ICFES
    afirmacion = Column(Text, nullable=True)  # ICFES statement/affirmation
    evidencia = Column(Text, nullable=True)  # ICFES evidence
    nivel_desempeno_esperado = Column(String(30), nullable=True)  # Expected performance level
    tiempo_estimado = Column(Integer, nullable=True)  # Estimated time in seconds

    # Gamification and XP system
    puntos_xp = Column(Integer, default=10, nullable=True)  # XP points from Puntos_XP CSV field

    # Sistema de ayuda gradual (Comentados: no existen en la tabla actual)
    # pista_1 = Column(Text, nullable=True)  # Primera pista (conceptual)
    # pista_2 = Column(Text, nullable=True)  # Segunda pista (procedimental)
    # pista_3 = Column(Text, nullable=True)  # Tercera pista (específica)
    # explicacion_respuesta = Column(Text, nullable=True)  # Explicación detallada de la respuesta
    # error_comun = Column(Text, nullable=True)  # Error común identificado
    
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
    
    # Relationships - Temporarily simplified without back_populates to avoid circular references
    topic = relationship("Topic")
    subject = relationship("Subject")
    # battle_answers = # relationship("relationship("BattleAnswer",", cascade="all,delete-orphan")
    # ai_explanations = # relationship("relationship("AIExplanation",", cascade="all,delete-orphan")
    # ai_tutoring_sessions = # relationship("relationship("AITutoringSession",", cascade="all,delete-orphan")
    # quiz_answers = # relationship("relationship("QuizAnswer",", cascade="all,delete-orphan")
    # diagnostic_answers = relationship("DiagnosticTestAnswer", )
    
    # Relación con catálogo de temas ICFES - Comentado: columna no existe en la tabla
    # topic_catalog = # relationship("relationship("StudyTopicsCatalog",", foreign_keys="Question.codigo_tema")

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
        Implementa la fórmula: P(θ) = c + (1-c) / (1 + e^(-a(θ-b)))
        
        Args:
            theta: Habilidad estimada del estudiante (logit scale)
            
        Returns:
            Probabilidad de respuesta correcta (0-1)
        """
        import math
        
        # Usar parámetros reales de la base de datos
        a = self.parametro_irt_a if self.parametro_irt_a is not None else 1.0
        b = self.parametro_irt_b if self.parametro_irt_b is not None else 0.0
        c = self.parametro_irt_c if self.parametro_irt_c is not None else 0.25
        
        # Validar que los parámetros estén en rangos válidos
        a = max(0.1, min(10.0, a))  # Discriminación entre 0.1 y 10
        b = max(-5.0, min(5.0, b))  # Dificultad entre -5 y 5
        c = max(0.0, min(1.0, c))   # Pseudo-adivinanza entre 0 y 1
        
        # Modelo 3PL: P(θ) = c + (1-c)/(1+e^(-a(θ-b)))
        try:
            # Calcular el exponente con protección contra overflow
            exponent = -a * (theta - b)
            exponent = max(-50, min(50, exponent))  # Prevenir overflow
            
            exp_val = math.exp(exponent)
            probability = c + (1 - c) / (1 + exp_val)
            
            # Asegurar que la probabilidad esté en el rango válido
            return max(0.001, min(0.999, probability))
            
        except (OverflowError, ValueError, ZeroDivisionError) as e:
            # En caso de error, retornar probabilidad neutra
            return 0.5
    
    def get_irt_information(self, theta: float) -> float:
        """
        Calcula la información de Fisher usando el criterio máximo: I(θ) = a²P(θ)Q(θ)
        Donde Q(θ) = 1 - P(θ) para modelo 3PL
        
        Args:
            theta: Habilidad estimada del estudiante (logit scale)
            
        Returns:
            Información de Fisher para este ítem en theta dado
        """
        # Obtener probabilidad usando el modelo 3PL
        p = self.get_irt_probability(theta)
        q = 1 - p  # Q(θ) = 1 - P(θ)
        
        # Obtener parámetros IRT
        a = self.parametro_irt_a if self.parametro_irt_a is not None else 1.0
        c = self.parametro_irt_c if self.parametro_irt_c is not None else 0.25
        
        # Validar parámetros
        a = max(0.1, min(10.0, a))
        c = max(0.0, min(1.0, c))
        
        # Evitar división por cero
        if p <= c + 1e-10 or q <= 1e-10:
            return 1e-10
        
        try:
            # Para modelo 3PL: I(θ) = a²(P-c)²Q / [P(1-c)²]
            numerator = a**2 * (p - c)**2 * q
            denominator = p * (1 - c)**2
            
            information = numerator / denominator
            
            # Asegurar que la información sea positiva y finita
            return max(1e-10, min(100.0, information))
            
        except (OverflowError, ValueError, ZeroDivisionError):
            return 1e-10
    
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
    
    def get_progressive_hint(self, hint_level: int) -> str:
        """
        Retorna la pista correspondiente al nivel solicitado (1, 2, o 3)
        """
        if hint_level == 1:
            return self.pista_1 or "Observa cuidadosamente los datos proporcionados"
        elif hint_level == 2:
            return self.pista_2 or "Considera el procedimiento paso a paso"
        elif hint_level == 3:
            return self.pista_3 or "Aplica la fórmula o concepto específico"
        return "Nivel de pista no válido"
    
    def get_irt_information(self, theta: float) -> float:
        """
        Calcula la función de información de Fisher para esta pregunta en el nivel theta dado
        
        Args:
            theta: Habilidad estimada del estudiante (logit scale)
            
        Returns:
            Información de Fisher en theta
        """
        import math
        
        # Usar parámetros reales de la base de datos
        a = self.parametro_irt_a if self.parametro_irt_a is not None else 1.0
        b = self.parametro_irt_b if self.parametro_irt_b is not None else 0.0
        c = self.parametro_irt_c if self.parametro_irt_c is not None else 0.25
        
        # Validar que los parámetros estén en rangos válidos
        a = max(0.1, min(10.0, a))
        b = max(-5.0, min(5.0, b))
        c = max(0.0, min(1.0, c))
        
        try:
            # Calcular probabilidad de respuesta correcta
            p = self.get_irt_probability(theta)
            q = 1 - p
            
            # Calcular derivada de P con respecto a theta
            exponent = -a * (theta - b)
            exponent = max(-50, min(50, exponent))
            exp_val = math.exp(exponent)
            
            # dP/dθ = a(1-c)e^(-a(θ-b)) / (1+e^(-a(θ-b)))²
            dp_dtheta = a * (1 - c) * exp_val / ((1 + exp_val) ** 2)
            
            # Función de información: I(θ) = [P'(θ)]² / [P(θ)(1-P(θ))]
            if p > 0.001 and q > 0.001:
                information = (dp_dtheta ** 2) / (p * q)
            else:
                information = 0.0
                
            return max(0.0, information)
            
        except (OverflowError, ValueError, ZeroDivisionError):
            return 0.0 