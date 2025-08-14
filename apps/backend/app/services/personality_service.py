from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import HeroClass, PersonalityQuestion, UserProfile, User
from ..schemas.personality import PersonalityTestRequest, PersonalityTestResponse
import json

class PersonalityAnalyzer:
    """Analizador de personalidad para asignar clases épicas"""
    
    def __init__(self, db: Session):
        self.db = db
        self.class_weights = {
            "warrior": 0,
            "mage": 0,
            "archer": 0,
            "priest": 0,
            "assassin": 0
        }
    
    def analyze_personality(self, request: PersonalityTestRequest) -> PersonalityTestResponse:
        """Analiza las respuestas y asigna una clase épica"""
        # Validar respuestas del usuario
        self._validate_personality_answers(request.answers)
        
        # Obtener todas las preguntas activas
        questions = self.db.query(PersonalityQuestion).filter(
            PersonalityQuestion.is_active == True
        ).order_by(PersonalityQuestion.order_index).all()
        
        # Validar que hay preguntas disponibles
        if not questions:
            raise ValueError("No hay preguntas de personalidad disponibles")
        
        # Calcular pesos para cada clase
        self._calculate_class_weights(request.answers, questions)
        
        # Asignar la clase con mayor peso
        assigned_class = self._assign_hero_class()
        
        # Obtener datos de la clase asignada
        hero_class = self.db.query(HeroClass).filter(
            HeroClass.id == assigned_class.id
        ).first()
        
        if not hero_class:
            raise ValueError("Clase épica no encontrada")
        
        # Crear o actualizar perfil de usuario
        self._create_user_profile(request.user_id, hero_class.id, request.answers)
        
        # Aplicar bonificaciones de stats
        stats_boost = self._apply_hero_bonuses(request.user_id, hero_class)
        
        # Generar datos para cutscene
        cutscene_data = self._generate_cutscene_data(hero_class)
        
        return PersonalityTestResponse(
            hero_class={
                "id": str(hero_class.id),
                "name": hero_class.name,
                "description": hero_class.description,
                "avatar_url": hero_class.avatar_url,
                "special_ability": hero_class.special_ability,
                "element": hero_class.element,
                "color_theme": hero_class.color_theme,
                "class_type": hero_class.class_type
            },
            personality_answers=request.answers,
            cutscene_data=cutscene_data,
            stats_boost=stats_boost
        )
    
    def _calculate_class_weights(self, answers: Dict[str, str], questions: List[PersonalityQuestion]):
        """Calcula los pesos para cada clase basado en las respuestas"""
        self.class_weights = {key: 0 for key in self.class_weights.keys()}
        
        for question in questions:
            if question.question_type in answers:
                answer = answers[question.question_type]
                weight_factors = question.get_weight_factors()
                
                if answer in weight_factors:
                    answer_weights = weight_factors[answer]
                    for class_type, weight in answer_weights.items():
                        if class_type in self.class_weights:
                            self.class_weights[class_type] += weight
    
    def _assign_hero_class(self) -> HeroClass:
        """Asigna la clase épica basada en los pesos calculados"""
        # Mapeo de tipos de clase a IDs de hero_classes
        class_mapping = {
            "warrior": "cc0e8400-e29b-41d4-a716-446655440002",  # Guerrero del Conocimiento
            "mage": "cc0e8400-e29b-41d4-a716-446655440001",     # Mago Cuántico
            "archer": "cc0e8400-e29b-41d4-a716-446655440003",   # Arquero de la Sabiduría
            "priest": "cc0e8400-e29b-41d4-a716-446655440004",   # Sacerdote del Aprendizaje
            "assassin": "cc0e8400-e29b-41d4-a716-446655440005"  # Asesino de la Lógica
        }
        
        # Encontrar la clase con mayor peso
        max_weight = max(self.class_weights.values())
        assigned_class_type = [k for k, v in self.class_weights.items() if v == max_weight][0]
        
        # Obtener la clase épica correspondiente
        hero_class_id = class_mapping[assigned_class_type]
        return self.db.query(HeroClass).filter(HeroClass.id == hero_class_id).first()
    
    def _create_user_profile(self, user_id: str, hero_class_id: str, answers: Dict[str, str]):
        """Crea o actualiza el perfil de usuario"""
        # Verificar si ya existe un perfil
        existing_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            # Actualizar perfil existente
            existing_profile.hero_class_id = hero_class_id
            existing_profile.personality_answers = answers
        else:
            # Crear nuevo perfil
            new_profile = UserProfile(
                user_id=user_id,
                hero_class_id=hero_class_id,
                personality_answers=answers
            )
            self.db.add(new_profile)
        
        self.db.commit()
    
    def _apply_hero_bonuses(self, user_id: str, hero_class: HeroClass) -> Dict[str, int]:
        """Aplica las bonificaciones de la clase épica al usuario"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {}
        
        stats_boost = hero_class.get_stats_boost()
        
        # Aplicar bonificaciones
        if "hp" in stats_boost:
            user.hp += stats_boost["hp"]
        if "mp" in stats_boost:
            user.mp += stats_boost["mp"]
        if "power" in stats_boost:
            user.power += stats_boost["power"]
        if "wisdom" in stats_boost:
            user.wisdom += stats_boost["wisdom"]
        if "speed" in stats_boost:
            user.speed += stats_boost["speed"]
        
        self.db.commit()
        
        return stats_boost
    
    def _generate_cutscene_data(self, hero_class: HeroClass) -> Dict[str, Any]:
        """Genera datos para la cutscene de presentación"""
        cutscenes = {
            "warrior": {
                "title": "¡Guerrero del Conocimiento!",
                "subtitle": "Tu fuerza mental es legendaria",
                "animation": "warrior_awakening",
                "particles": ["earth", "strength"],
                "sound_effect": "warrior_roar"
            },
            "mage": {
                "title": "¡Mago Cuántico!",
                "subtitle": "Las matemáticas son tu magia",
                "animation": "mage_spellcasting",
                "particles": ["fire", "magic"],
                "sound_effect": "spell_cast"
            },
            "archer": {
                "title": "¡Arquero de la Sabiduría!",
                "subtitle": "Tu precisión es mortal",
                "animation": "archer_aiming",
                "particles": ["wind", "speed"],
                "sound_effect": "bow_release"
            },
            "priest": {
                "title": "¡Sacerdote del Aprendizaje!",
                "subtitle": "Tu sabiduría sana las dudas",
                "animation": "priest_healing",
                "particles": ["light", "healing"],
                "sound_effect": "healing_spell"
            },
            "assassin": {
                "title": "¡Asesino de la Lógica!",
                "subtitle": "Tu astucia es tu arma",
                "animation": "assassin_stealth",
                "particles": ["shadow", "stealth"],
                "sound_effect": "stealth_move"
            }
        }
        
        class_type = hero_class.class_type
        return cutscenes.get(class_type, cutscenes["warrior"])
    
    def get_personality_questions(self) -> List[PersonalityQuestion]:
        """Obtiene todas las preguntas de personalidad activas"""
        return self.db.query(PersonalityQuestion).filter(
            PersonalityQuestion.is_active == True
        ).order_by(PersonalityQuestion.order_index).all()
    
    def _validate_personality_answers(self, answers: Dict[str, str]):
        """Valida el formato y contenido de las respuestas de personalidad"""
        # Validar que answers es un diccionario
        if not isinstance(answers, dict):
            raise ValueError("Las respuestas deben ser un diccionario")
        
        # Validar que no esté vacío
        if not answers:
            raise ValueError("Debe proporcionar al menos una respuesta")
        
        # Tipos de pregunta válidos
        valid_question_types = [
            "motivation", "learning_style", "subject_preference", 
            "problem_solving", "social_preference"
        ]
        
        # Opciones válidas
        valid_options = ["A", "B", "C", "D", "E"]
        
        # Validar cada respuesta
        for question_type, answer in answers.items():
            # Validar tipo de pregunta
            if question_type not in valid_question_types:
                raise ValueError(f"Tipo de pregunta inválido: {question_type}")
            
            # Validar formato de respuesta
            if not isinstance(answer, str):
                raise ValueError(f"Respuesta debe ser string: {question_type}")
            
            if answer not in valid_options:
                raise ValueError(f"Opción inválida para {question_type}: {answer}")
        
        # Validar que todas las preguntas requeridas estén respondidas
        questions = self.db.query(PersonalityQuestion).filter(
            PersonalityQuestion.is_active == True
        ).all()
        
        required_types = [q.question_type for q in questions]
        answered_types = list(answers.keys())
        
        missing_types = set(required_types) - set(answered_types)
        if missing_types:
            raise ValueError(f"Faltan respuestas para: {', '.join(missing_types)}") 