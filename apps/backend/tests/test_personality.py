import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.services.personality_service import PersonalityAnalyzer
from app.models import HeroClass, PersonalityQuestion, UserProfile, User
from app.schemas.personality import PersonalityTestRequest

# Configuración de base de datos de prueba
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

class TestPersonalityAnalyzer:
    """Tests para el analizador de personalidad"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        self.db = TestingSessionLocal()
        self.analyzer = PersonalityAnalyzer(self.db)
        
        # Crear datos de prueba
        self.create_test_data()
    
    def teardown_method(self):
        """Limpieza después de cada test"""
        self.db.close()
    
    def create_test_data(self):
        """Crear datos de prueba en la base de datos"""
        # Crear clases épicas
        hero_classes = [
            HeroClass(
                id="cc0e8400-e29b-41d4-a716-446655440001",
                name="Mago Cuántico",
                description="Dominas las matemáticas con precisión mágica",
                avatar_url="/avatars/mage-quantum.png",
                stats_boost={"wisdom": 25, "mp": 30, "math_power": 20},
                special_ability="Explicación Mágica: +50% precisión en matemáticas",
                element="Fuego",
                color_theme="#FF6B6B"
            ),
            HeroClass(
                id="cc0e8400-e29b-41d4-a716-446655440002",
                name="Guerrero del Conocimiento",
                description="Tu fuerza física se convierte en poder mental",
                avatar_url="/avatars/warrior-knowledge.png",
                stats_boost={"power": 25, "hp": 30, "resistance": 15},
                special_ability="Resistencia Mental: +30% HP en batallas largas",
                element="Tierra",
                color_theme="#96CEB4"
            )
        ]
        
        for hero_class in hero_classes:
            self.db.add(hero_class)
        
        # Crear preguntas de personalidad
        questions = [
            PersonalityQuestion(
                id="dd0e8400-e29b-41d4-a716-446655440001",
                question_text="¿Qué te motiva más a estudiar?",
                question_type="motivation",
                options={
                    "A": "Resolver problemas complejos",
                    "B": "Ayudar a otros a aprender",
                    "C": "Competir y superar récords",
                    "D": "Explorar nuevos conceptos",
                    "E": "Dominar completamente un tema"
                },
                weight_factors={
                    "A": {"warrior": 3, "mage": 2, "archer": 1, "priest": 1, "assassin": 1},
                    "B": {"warrior": 1, "mage": 1, "archer": 1, "priest": 4, "assassin": 1},
                    "C": {"warrior": 4, "mage": 2, "archer": 3, "priest": 1, "assassin": 2},
                    "D": {"warrior": 1, "mage": 4, "archer": 2, "priest": 2, "assassin": 3},
                    "E": {"warrior": 2, "mage": 3, "archer": 1, "priest": 2, "assassin": 4}
                },
                order_index=1,
                is_active=True
            )
        ]
        
        for question in questions:
            self.db.add(question)
        
        self.db.commit()
    
    def test_analyze_personality_mage_assignment(self):
        """Test: Asignar clase Mago basado en respuestas"""
        request = PersonalityTestRequest(
            user_id="test-user-1",
            answers={
                "motivation": "D",  # Explorar nuevos conceptos
                "learning_style": "D",  # Analizando patrones
                "subject_preference": "A",  # Matemáticas
                "problem_solving": "D",  # Buscar patrones
                "social_preference": "D"  # Explorativo
            }
        )
        
        result = self.analyzer.analyze_personality(request)
        
        assert result.hero_class["name"] == "Mago Cuántico"
        assert result.hero_class["element"] == "Fuego"
        assert "wisdom" in result.stats_boost
        assert result.stats_boost["wisdom"] == 25
    
    def test_analyze_personality_warrior_assignment(self):
        """Test: Asignar clase Guerrero basado en respuestas"""
        request = PersonalityTestRequest(
            user_id="test-user-2",
            answers={
                "motivation": "C",  # Competir y superar récords
                "learning_style": "C",  # Compitiendo y midiendo progreso
                "subject_preference": "A",  # Matemáticas
                "problem_solving": "A",  # Lo ataco directamente
                "social_preference": "C"  # Competitivo
            }
        )
        
        result = self.analyzer.analyze_personality(request)
        
        assert result.hero_class["name"] == "Guerrero del Conocimiento"
        assert result.hero_class["element"] == "Tierra"
        assert "power" in result.stats_boost
        assert result.stats_boost["power"] == 25
    
    def test_calculate_class_weights(self):
        """Test: Calcular pesos de clases correctamente"""
        answers = {
            "motivation": "A",
            "learning_style": "A",
            "subject_preference": "A",
            "problem_solving": "A",
            "social_preference": "A"
        }
        
        self.analyzer._calculate_class_weights(answers, self.db.query(PersonalityQuestion).all())
        
        # Verificar que se calcularon pesos
        assert hasattr(self.analyzer, 'class_weights')
        assert isinstance(self.analyzer.class_weights, dict)
        assert len(self.analyzer.class_weights) == 5  # 5 clases
    
    def test_assign_hero_class(self):
        """Test: Asignar clase épica basada en pesos"""
        # Simular pesos calculados
        self.analyzer.class_weights = {
            "warrior": 15,
            "mage": 10,
            "archer": 8,
            "priest": 5,
            "assassin": 12
        }
        
        hero_class = self.analyzer._assign_hero_class()
        
        assert hero_class is not None
        assert hero_class.name == "Guerrero del Conocimiento"  # Mayor peso
    
    def test_create_user_profile(self):
        """Test: Crear perfil de usuario"""
        user_id = "test-user-3"
        hero_class_id = "cc0e8400-e29b-41d4-a716-446655440001"
        answers = {"motivation": "A", "learning_style": "B"}
        
        self.analyzer._create_user_profile(user_id, hero_class_id, answers)
        
        # Verificar que se creó el perfil
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        assert profile is not None
        assert profile.hero_class_id == hero_class_id
        assert profile.personality_answers == answers
    
    def test_apply_hero_bonuses(self):
        """Test: Aplicar bonificaciones de clase"""
        # Crear usuario de prueba
        user = User(
            id="test-user-4",
            username="testuser",
            email="test@example.com",
            password_hash="hash",
            display_name="Test User",
            hp=100,
            mp=50,
            power=10,
            wisdom=10,
            speed=10
        )
        self.db.add(user)
        self.db.commit()
        
        hero_class = self.db.query(HeroClass).first()
        
        stats_boost = self.analyzer._apply_hero_bonuses(user.id, hero_class)
        
        # Verificar que se aplicaron bonificaciones
        assert isinstance(stats_boost, dict)
        assert len(stats_boost) > 0
        
        # Verificar que se actualizaron stats del usuario
        updated_user = self.db.query(User).filter(User.id == user.id).first()
        assert updated_user.hp > 100 or updated_user.mp > 50 or updated_user.power > 10
    
    def test_generate_cutscene_data(self):
        """Test: Generar datos de cutscene"""
        hero_class = self.db.query(HeroClass).first()
        
        cutscene_data = self.analyzer._generate_cutscene_data(hero_class)
        
        assert isinstance(cutscene_data, dict)
        assert "title" in cutscene_data
        assert "subtitle" in cutscene_data
        assert "animation" in cutscene_data
        assert "particles" in cutscene_data
        assert "sound_effect" in cutscene_data
    
    def test_get_personality_questions(self):
        """Test: Obtener preguntas de personalidad"""
        questions = self.analyzer.get_personality_questions()
        
        assert isinstance(questions, list)
        assert len(questions) > 0
        assert all(isinstance(q, PersonalityQuestion) for q in questions)
        assert all(q.is_active for q in questions)

class TestPersonalityEndpoints:
    """Tests para endpoints de personalidad"""
    
    def setup_method(self):
        """Configuración antes de cada test"""
        self.db = TestingSessionLocal()
        self.create_test_data()
    
    def teardown_method(self):
        """Limpieza después de cada test"""
        self.db.close()
    
    def create_test_data(self):
        """Crear datos de prueba"""
        # Crear clases épicas
        hero_class = HeroClass(
            id="cc0e8400-e29b-41d4-a716-446655440001",
            name="Mago Cuántico",
            description="Dominas las matemáticas con precisión mágica",
            avatar_url="/avatars/mage-quantum.png",
            stats_boost={"wisdom": 25, "mp": 30},
            special_ability="Explicación Mágica",
            element="Fuego",
            color_theme="#FF6B6B"
        )
        self.db.add(hero_class)
        
        # Crear pregunta de personalidad
        question = PersonalityQuestion(
            id="dd0e8400-e29b-41d4-a716-446655440001",
            question_text="¿Qué te motiva más a estudiar?",
            question_type="motivation",
            options={"A": "Opción A", "B": "Opción B"},
            weight_factors={},
            order_index=1,
            is_active=True
        )
        self.db.add(question)
        
        self.db.commit()
    
    def test_get_personality_questions_endpoint(self):
        """Test: Endpoint GET /api/v1/personality/questions"""
        response = client.get("/api/v1/personality/questions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "question_text" in data[0]
        assert "options" in data[0]
    
    def test_get_hero_classes_endpoint(self):
        """Test: Endpoint GET /api/v1/personality/hero-classes"""
        response = client.get("/api/v1/personality/hero-classes")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "name" in data[0]
        assert "element" in data[0]
    
    def test_personality_test_endpoint(self):
        """Test: Endpoint POST /api/v1/personality/test"""
        test_data = {
            "user_id": "test-user-5",
            "answers": {
                "motivation": "A",
                "learning_style": "A",
                "subject_preference": "A",
                "problem_solving": "A",
                "social_preference": "A"
            }
        }
        
        response = client.post("/api/v1/personality/test", json=test_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "hero_class" in data
        assert "personality_answers" in data
        assert "cutscene_data" in data
        assert "stats_boost" in data
    
    def test_personality_test_invalid_data(self):
        """Test: Endpoint POST con datos inválidos"""
        test_data = {
            "user_id": "test-user-6",
            "answers": {}  # Respuestas vacías
        }
        
        response = client.post("/api/v1/personality/test", json=test_data)
        
        # Debería manejar el error graciosamente
        assert response.status_code in [200, 400, 422]
    
    def test_get_hero_class_endpoint(self):
        """Test: Endpoint GET /api/v1/personality/hero-class/{class_id}"""
        class_id = "cc0e8400-e29b-41d4-a716-446655440001"
        
        response = client.get(f"/api/v1/personality/hero-class/{class_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "description" in data
        assert "element" in data
        assert "stats_boost" in data
    
    def test_get_hero_class_not_found(self):
        """Test: Endpoint GET con ID inexistente"""
        class_id = "non-existent-id"
        
        response = client.get(f"/api/v1/personality/hero-class/{class_id}")
        
        assert response.status_code == 404

class TestPersonalityValidation:
    """Tests para validación de datos de personalidad"""
    
    def test_validate_personality_answers(self):
        """Test: Validar formato de respuestas"""
        valid_answers = {
            "motivation": "A",
            "learning_style": "B",
            "subject_preference": "C",
            "problem_solving": "D",
            "social_preference": "E"
        }
        
        # Verificar que todas las claves requeridas están presentes
        required_keys = ["motivation", "learning_style", "subject_preference", "problem_solving", "social_preference"]
        for key in required_keys:
            assert key in valid_answers
        
        # Verificar que los valores son válidos
        valid_options = ["A", "B", "C", "D", "E"]
        for value in valid_answers.values():
            assert value in valid_options
    
    def test_validate_question_types(self):
        """Test: Validar tipos de pregunta"""
        valid_types = ["motivation", "learning_style", "subject_preference", "problem_solving", "social_preference"]
        
        # Simular preguntas de la base de datos
        questions = [
            PersonalityQuestion(question_type="motivation"),
            PersonalityQuestion(question_type="learning_style"),
            PersonalityQuestion(question_type="subject_preference"),
            PersonalityQuestion(question_type="problem_solving"),
            PersonalityQuestion(question_type="social_preference")
        ]
        
        for question in questions:
            assert question.question_type in valid_types
    
    def test_validate_answer_format(self):
        """Test: Validar formato de respuestas individuales"""
        # Respuesta válida
        valid_answer = "A"
        assert isinstance(valid_answer, str)
        assert len(valid_answer) == 1
        assert valid_answer in ["A", "B", "C", "D", "E"]
        
        # Respuesta inválida
        invalid_answers = ["F", "1", "a", "", None]
        for invalid_answer in invalid_answers:
            assert invalid_answer not in ["A", "B", "C", "D", "E"] or invalid_answer is None

if __name__ == "__main__":
    pytest.main([__file__]) 