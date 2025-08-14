from pydantic import BaseModel, validator, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import re

class QuestionBase(BaseModel):
    # Campos de texto de la pregunta
    pregunta_texto: Optional[str] = None
    pregunta_imagen: Optional[str] = None
    
    # Campos de texto de las opciones
    opcion_a_texto: Optional[str] = None
    opcion_a_imagen: Optional[str] = None
    opcion_b_texto: Optional[str] = None
    opcion_b_imagen: Optional[str] = None
    opcion_c_texto: Optional[str] = None
    opcion_c_imagen: Optional[str] = None
    opcion_d_texto: Optional[str] = None
    opcion_d_imagen: Optional[str] = None
    
    # Respuesta correcta
    respuesta_correcta: str
    
    # Campos adicionales
    difficulty: int = 1
    explanation: Optional[str] = None
    hint: Optional[str] = None
    tags: Optional[List[str]] = None
    
    # Campos legacy para compatibilidad
    question_text: Optional[str] = None
    image_url: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    options_images: Optional[Dict[str, str]] = None

    @validator('difficulty')
    def validate_difficulty(cls, v):
        if not 1 <= v <= 10:
            raise ValueError('Difficulty must be between 1 and 10')
        return v

    @validator('respuesta_correcta')
    def validate_respuesta_correcta(cls, v):
        if v.lower() not in ['a', 'b', 'c', 'd']:
            raise ValueError('La respuesta correcta debe ser a, b, c o d')
        return v.lower()

    @validator('pregunta_texto', 'pregunta_imagen')
    def validate_pregunta_content(cls, v, values):
        # Verificar que al menos hay texto o imagen en la pregunta
        pregunta_texto = values.get('pregunta_texto') if 'pregunta_texto' in values else None
        pregunta_imagen = values.get('pregunta_imagen') if 'pregunta_imagen' in values else None
        
        if not pregunta_texto and not pregunta_imagen:
            raise ValueError('La pregunta debe tener al menos texto o imagen')
        return v

    @validator('opcion_a_texto', 'opcion_a_imagen', 'opcion_b_texto', 'opcion_b_imagen', 
               'opcion_c_texto', 'opcion_c_imagen', 'opcion_d_texto', 'opcion_d_imagen')
    def validate_opciones_content(cls, v, values):
        # Verificar que al menos una opción tiene contenido
        opciones_con_contenido = 0
        for letra in ['a', 'b', 'c', 'd']:
            texto = values.get(f'opcion_{letra}_texto')
            imagen = values.get(f'opcion_{letra}_imagen')
            if texto or imagen:
                opciones_con_contenido += 1
        
        if opciones_con_contenido == 0:
            raise ValueError('Debe haber al menos una opción con contenido (texto o imagen)')
        return v

    @validator('respuesta_correcta')
    def validate_respuesta_correcta_has_content(cls, v, values):
        # Verificar que la opción de respuesta correcta tiene contenido
        texto_correcto = values.get(f'opcion_{v}_texto')
        imagen_correcta = values.get(f'opcion_{v}_imagen')
        if not texto_correcto and not imagen_correcta:
            raise ValueError(f'La opción {v.upper()} (respuesta correcta) debe tener contenido')
        return v

class QuestionCreate(QuestionBase):
    topic_id: UUID
    subject_id: UUID
    question_type: str = "multiple_choice"

class QuestionUpdate(BaseModel):
    pregunta_texto: Optional[str] = None
    pregunta_imagen: Optional[str] = None
    opcion_a_texto: Optional[str] = None
    opcion_a_imagen: Optional[str] = None
    opcion_b_texto: Optional[str] = None
    opcion_b_imagen: Optional[str] = None
    opcion_c_texto: Optional[str] = None
    opcion_c_imagen: Optional[str] = None
    opcion_d_texto: Optional[str] = None
    opcion_d_imagen: Optional[str] = None
    respuesta_correcta: Optional[str] = None
    difficulty: Optional[int] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    tags: Optional[List[str]] = None

class QuestionResponse(QuestionBase):
    id: UUID
    topic_id: UUID
    subject_id: UUID
    question_type: str
    power_stats: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class QuestionWithStats(QuestionResponse):
    usage_count: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    difficulty_rating: float = 0.0

class QuestionValidationRequest(BaseModel):
    pregunta_texto: Optional[str] = None
    pregunta_imagen: Optional[str] = None
    opcion_a_texto: Optional[str] = None
    opcion_a_imagen: Optional[str] = None
    opcion_b_texto: Optional[str] = None
    opcion_b_imagen: Optional[str] = None
    opcion_c_texto: Optional[str] = None
    opcion_c_imagen: Optional[str] = None
    opcion_d_texto: Optional[str] = None
    opcion_d_imagen: Optional[str] = None
    respuesta_correcta: str

class QuestionValidationResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []

class QuestionNavigationGrid(BaseModel):
    """Esquema para la cuadrícula de navegación de preguntas"""
    total_questions: int
    current_question: int
    answered_questions: List[int]
    question_states: Dict[int, str]  # 'unanswered', 'answered', 'current' 