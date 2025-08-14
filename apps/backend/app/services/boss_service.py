from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Dict, Optional
import uuid
from datetime import datetime

from ..models.battle import Battle, BattleAnswer, Certificate
from ..models.study_plan import StudyPlan, PlanProgress
from ..models.question import Question
from ..models.user import User
from ..models.subject import Subject

class BossService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_boss_narrative(self, unit_number: int, subject_name: str) -> str:
        """Genera narrativa épica para el boss de la unidad"""
        narratives = {
            "Matemáticas": {
                1: "El Guardián de los Números Primos - Una entidad ancestral que protege los secretos de la aritmética fundamental.",
                2: "El Señor de las Ecuaciones Cuadráticas - Un maestro de la simetría y las parábolas que desafía tu dominio algebraico.",
                3: "La Reina de la Geometría Euclidiana - Protectora de ángulos, triángulos y las leyes del espacio.",
                4: "El Arquitecto de las Funciones - Un ser que manipula las curvas y transformaciones del cálculo.",
                5: "El Maestro de la Estadística Inferencial - Guardián de las distribuciones y el análisis de datos.",
                6: "El Señor de la Trigonometría - Dominador de senos, cosenos y las medidas angulares.",
                7: "La Reina de la Probabilidad - Tejedora de eventos aleatorios y distribuciones.",
                8: "El Guardián del Cálculo Diferencial - Protector de límites, derivadas e infinitésimos."
            },
            "Ciencias Naturales": {
                1: "El Elemental de la Materia - Guardián de átomos, moléculas y las transformaciones químicas.",
                2: "El Señor de las Fuerzas - Dominador de gravedad, electromagnetismo y las leyes del movimiento.",
                3: "La Reina de la Evolución - Protectora de la diversidad biológica y los procesos adaptativos.",
                4: "El Arquitecto de la Energía - Maestro de la conservación y transformación energética.",
                5: "El Guardián de los Ecosistemas - Protector del equilibrio natural y las interacciones bióticas.",
                6: "El Señor de la Genética - Dominador de herencia, mutaciones y la información genética.",
                7: "La Reina de la Termodinámica - Tejedora de calor, entropía y los procesos irreversibles.",
                8: "El Maestro de la Física Cuántica - Guardián de la incertidumbre y las dualidades fundamentales."
            },
            "Lenguaje": {
                1: "El Guardián de la Comprensión Lectora - Protector de la interpretación y el análisis textual.",
                2: "El Señor de la Literatura - Dominador de géneros, estilos y la expresión artística.",
                3: "La Reina de la Gramática - Maestra de estructuras, reglas y la precisión lingüística.",
                4: "El Arquitecto de la Comunicación - Guardián de la expresión clara y efectiva.",
                5: "El Señor de la Semántica - Dominador de significados, contextos y la interpretación.",
                6: "La Reina de la Sintaxis - Protectora del orden, la coherencia y la estructura.",
                7: "El Guardián de la Pragmática - Maestro de la intención, el contexto y la comunicación.",
                8: "El Señor de la Retórica - Dominador de la persuasión, la argumentación y el discurso."
            },
            "Ciencias Sociales": {
                1: "El Guardián de la Historia - Protector de la memoria colectiva y los procesos históricos.",
                2: "El Señor de la Geografía - Dominador del espacio, el territorio y las relaciones espaciales.",
                3: "La Reina de la Economía - Maestra de la producción, distribución y el intercambio.",
                4: "El Arquitecto de la Política - Guardián de las instituciones, el poder y la organización social.",
                5: "El Señor de la Sociología - Dominador de las estructuras sociales y las interacciones humanas.",
                6: "La Reina de la Antropología - Protectora de la diversidad cultural y los sistemas de creencias.",
                7: "El Guardián de la Filosofía - Maestro del pensamiento crítico y la reflexión fundamental.",
                8: "El Señor de la Psicología - Dominador de la mente, el comportamiento y la cognición."
            }
        }
        
        return narratives.get(subject_name, {}).get(unit_number, f"El Guardián de la Unidad {unit_number}")
    
    def get_epic_rewards(self, unit_number: int, subject_name: str) -> List[Dict]:
        """Genera recompensas épicas para vencer al boss"""
        base_rewards = {
            "experience": 500 + (unit_number * 100),
            "orbs": 50 + (unit_number * 10),
            "crystals": 5 + unit_number,
            "items": []
        }
        
        # Items épicos específicos por materia
        epic_items = {
            "Matemáticas": [
                {"name": "Calculadora Épica", "rarity": "epic", "power_boost": 25},
                {"name": "Compás Legendario", "rarity": "legendary", "wisdom_boost": 30}
            ],
            "Ciencias Naturales": [
                {"name": "Microscopio Cuántico", "rarity": "epic", "wisdom_boost": 25},
                {"name": "Piedra Filosofal", "rarity": "legendary", "power_boost": 35}
            ],
            "Lenguaje": [
                {"name": "Pluma de los Antiguos", "rarity": "epic", "wisdom_boost": 25},
                {"name": "Libro de los Secretos", "rarity": "legendary", "power_boost": 30}
            ],
            "Ciencias Sociales": [
                {"name": "Mapa del Tiempo", "rarity": "epic", "wisdom_boost": 25},
                {"name": "Corona del Sabio", "rarity": "legendary", "power_boost": 30}
            ]
        }
        
        # Agregar items épicos
        if subject_name in epic_items:
            base_rewards["items"].extend(epic_items[subject_name])
        
        return base_rewards
    
    def create_boss_battle(self, user_id: str, unit_number: int, subject_id: str) -> Battle:
        """Crea una batalla de boss temático para una unidad específica"""
        
        # Obtener información del usuario y materia
        user = self.db.query(User).filter(User.id == user_id).first()
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        
        if not user or not subject:
            raise ValueError("Usuario o materia no encontrado")
        
        # Verificar que el usuario puede enfrentar este boss
        plan_progress = self.db.query(PlanProgress).filter(
            and_(
                PlanProgress.plan_id == user.study_plans[0].id if user.study_plans else None,
                PlanProgress.unit_number == unit_number
            )
        ).first()
        
        if not plan_progress or not plan_progress.is_completed:
            raise ValueError("Debes completar la unidad antes de enfrentar al boss")
        
        # Generar narrativa y recompensas
        narrative = self.get_boss_narrative(unit_number, subject.name)
        epic_rewards = self.get_epic_rewards(unit_number, subject.name)
        
        # Crear batalla de boss
        boss_battle = Battle(
            user_id=user_id,
            battle_type="boss",
            enemy_name=f"Boss de la Unidad {unit_number}",
            enemy_level=unit_number * 5,
            enemy_hp=200 + (unit_number * 50),
            user_hp_start=user.hp,
            user_hp_end=user.hp,
            is_boss_battle=True,
            unit_number=unit_number,
            boss_narrative=narrative,
            epic_rewards=epic_rewards,
            status="in_progress"
        )
        
        self.db.add(boss_battle)
        self.db.commit()
        self.db.refresh(boss_battle)
        
        return boss_battle
    
    def get_boss_questions(self, unit_number: int, subject_id: str) -> List[Question]:
        """Obtiene 20 preguntas de alta dificultad para el boss"""
        # Obtener preguntas de alta dificultad (8-10) de la materia y unidad
        questions = self.db.query(Question).filter(
            and_(
                Question.subject_id == subject_id,
                Question.difficulty >= 8,
                Question.difficulty <= 10
            )
        ).limit(20).all()
        
        if len(questions) < 20:
            # Si no hay suficientes preguntas de alta dificultad, completar con preguntas de dificultad media-alta
            additional_questions = self.db.query(Question).filter(
                and_(
                    Question.subject_id == subject_id,
                    Question.difficulty >= 6,
                    Question.difficulty <= 7
                )
            ).limit(20 - len(questions)).all()
            questions.extend(additional_questions)
        
        return questions[:20]  # Asegurar máximo 20 preguntas
    
    def complete_boss_battle(self, battle_id: str, user_id: str) -> Dict:
        """Completa la batalla de boss y otorga recompensas épicas"""
        battle = self.db.query(Battle).filter(
            and_(
                Battle.id == battle_id,
                Battle.user_id == user_id,
                Battle.is_boss_battle == True
            )
        ).first()
        
        if not battle:
            raise ValueError("Batalla de boss no encontrada")
        
        if battle.status != "completed":
            raise ValueError("La batalla de boss no ha sido completada")
        
        user = self.db.query(User).filter(User.id == user_id).first()
        
        # Otorgar recompensas épicas
        rewards = battle.epic_rewards
        
        user.experience += rewards["experience"]
        user.orbs += rewards["orbs"]
        user.crystals += rewards["crystals"]
        
        # Recalcular nivel y rango
        new_level = self._calculate_level(user.experience)
        if new_level > user.level:
            user.level = new_level
            user.rank = self._calculate_rank(new_level)
            user.hp = min(150, user.hp + 15)  # Bonus extra por vencer boss
            user.mp = min(75, user.mp + 10)
        
        # Generar certificado de dominio
        certificate = self._generate_certificate(user_id, battle.unit_number, battle.subject_id, battle_id)
        
        # Desbloquear siguiente unidad
        self._unlock_next_unit(user_id, battle.unit_number)
        
        self.db.commit()
        
        return {
            "battle_id": str(battle.id),
            "rewards": rewards,
            "certificate_id": str(certificate.id),
            "next_unit_unlocked": battle.unit_number + 1,
            "new_level": user.level,
            "new_rank": user.rank
        }
    
    def _generate_certificate(self, user_id: str, unit_number: int, subject_id: str, battle_id: str) -> Certificate:
        """Genera un certificado de dominio para la unidad completada"""
        subject = self.db.query(Subject).filter(Subject.id == subject_id).first()
        user = self.db.query(User).filter(User.id == user_id).first()
        
        certificate_data = {
            "title": f"Certificado de Dominio - Unidad {unit_number}",
            "subject": subject.name,
            "unit_number": unit_number,
            "student_name": user.username,
            "completion_date": datetime.utcnow().isoformat(),
            "achievement": f"Dominio demostrado en {subject.name} - Unidad {unit_number}",
            "signature": "Sistema ICFES Leveling",
            "certificate_id": str(uuid.uuid4())
        }
        
        certificate = Certificate(
            user_id=user_id,
            unit_number=unit_number,
            subject_id=subject_id,
            battle_id=battle_id,
            certificate_data=certificate_data
        )
        
        self.db.add(certificate)
        self.db.commit()
        self.db.refresh(certificate)
        
        return certificate
    
    def _unlock_next_unit(self, user_id: str, current_unit: int) -> bool:
        """Desbloquea la siguiente unidad si existe"""
        # Buscar el plan de estudio activo del usuario
        study_plan = self.db.query(StudyPlan).filter(
            and_(
                StudyPlan.user_id == user_id,
                StudyPlan.is_active == True
            )
        ).first()
        
        if not study_plan:
            return False
        
        # Verificar si existe la siguiente unidad
        next_unit_progress = self.db.query(PlanProgress).filter(
            and_(
                PlanProgress.plan_id == study_plan.id,
                PlanProgress.unit_number == current_unit + 1
            )
        ).first()
        
        if next_unit_progress:
            # La siguiente unidad ya existe, solo marcar como disponible
            return True
        
        return False
    
    def _calculate_level(self, experience: int) -> int:
        """Calcula el nivel basado en la experiencia"""
        return int((experience / 100) ** 0.5) + 1
    
    def _calculate_rank(self, level: int) -> str:
        """Calcula el rango basado en el nivel"""
        if level >= 90:
            return "SSS"
        elif level >= 80:
            return "SS"
        elif level >= 70:
            return "S"
        elif level >= 60:
            return "A"
        elif level >= 50:
            return "B"
        elif level >= 40:
            return "C"
        elif level >= 30:
            return "D"
        else:
            return "E" 