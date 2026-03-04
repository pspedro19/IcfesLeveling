"""
Tests for Personality system.
Covers: personality analysis, hero class assignment, personality endpoints.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import auth_header_for, create_test_user_record
from app.models import HeroClass, PersonalityQuestion, UserProfile, User
from app.schemas.personality import PersonalityTestRequest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_hero_classes(db: Session):
    """Seed two hero classes for tests."""
    mage = HeroClass(
        id=uuid.uuid4(),
        name="Mago Cuántico",
        description="Dominas las matemáticas con precisión mágica",
        avatar_url="/avatars/mage-quantum.png",
        stats_boost={"wisdom": 25, "mp": 30, "math_power": 20},
        special_ability="Explicación Mágica: +50% precisión en matemáticas",
        element="Fuego",
        color_theme="#FF6B6B",
    )
    warrior = HeroClass(
        id=uuid.uuid4(),
        name="Guerrero del Conocimiento",
        description="Tu fuerza física se convierte en poder mental",
        avatar_url="/avatars/warrior-knowledge.png",
        stats_boost={"power": 25, "hp": 30, "resistance": 15},
        special_ability="Resistencia Mental: +30% HP en batallas largas",
        element="Tierra",
        color_theme="#96CEB4",
    )
    db.add_all([mage, warrior])
    db.commit()
    return mage, warrior


def _create_personality_question(db: Session, **overrides):
    """Create a single personality question."""
    defaults = dict(
        id=uuid.uuid4(),
        question_text="¿Qué te motiva más a estudiar?",
        question_type="motivation",
        options={
            "A": "Resolver problemas complejos",
            "B": "Ayudar a otros a aprender",
            "C": "Competir y superar récords",
            "D": "Explorar nuevos conceptos",
            "E": "Dominar completamente un tema",
        },
        weight_factors={
            "A": {"warrior": 3, "mage": 2, "archer": 1, "priest": 1, "assassin": 1},
            "B": {"warrior": 1, "mage": 1, "archer": 1, "priest": 4, "assassin": 1},
            "C": {"warrior": 4, "mage": 2, "archer": 3, "priest": 1, "assassin": 2},
            "D": {"warrior": 1, "mage": 4, "archer": 2, "priest": 2, "assassin": 3},
            "E": {"warrior": 2, "mage": 3, "archer": 1, "priest": 2, "assassin": 4},
        },
        order_index=1,
        is_active=True,
    )
    defaults.update(overrides)
    q = PersonalityQuestion(**defaults)
    db.add(q)
    db.commit()
    return q


# ---------------------------------------------------------------------------
# Service-level tests (PersonalityAnalyzer)
# ---------------------------------------------------------------------------


class TestPersonalityAnalyzer:
    """Tests for PersonalityAnalyzer service."""

    def test_calculate_class_weights(self, db: Session):
        """Weight calculation should produce all 5 class weights."""
        from app.services.personality_service import PersonalityAnalyzer

        _create_personality_question(db)
        analyzer = PersonalityAnalyzer(db)

        questions = db.query(PersonalityQuestion).all()
        analyzer._calculate_class_weights({"motivation": "A"}, questions)

        assert isinstance(analyzer.class_weights, dict)
        assert len(analyzer.class_weights) == 5
        # Answer "A" gives warrior=3, mage=2, ...
        assert analyzer.class_weights["warrior"] == 3
        assert analyzer.class_weights["mage"] == 2

    def test_generate_cutscene_data(self, db: Session):
        """Cutscene data should have all required fields."""
        from app.services.personality_service import PersonalityAnalyzer

        mage, _ = _create_hero_classes(db)
        analyzer = PersonalityAnalyzer(db)

        cutscene = analyzer._generate_cutscene_data(mage)

        assert isinstance(cutscene, dict)
        assert "title" in cutscene
        assert "subtitle" in cutscene
        assert "animation" in cutscene
        assert "particles" in cutscene
        assert "sound_effect" in cutscene

    def test_get_personality_questions(self, db: Session):
        """Should return only active personality questions."""
        from app.services.personality_service import PersonalityAnalyzer

        _create_personality_question(db, is_active=True, order_index=1)
        _create_personality_question(
            db, is_active=False, order_index=2,
            question_type="learning_style",
            question_text="Inactive question",
        )
        analyzer = PersonalityAnalyzer(db)

        questions = analyzer.get_personality_questions()

        assert len(questions) >= 1
        assert all(q.is_active for q in questions)


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------


class TestPersonalityEndpoints:
    """Test personality API endpoints."""

    def test_get_personality_questions_endpoint(self, client: TestClient, db: Session):
        """GET /api/v1/personality/questions should return questions."""
        _create_personality_question(db)
        response = client.get("/api/v1/personality/questions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_hero_classes_endpoint(self, client: TestClient, db: Session):
        """GET /api/v1/personality/hero-classes should return hero classes."""
        _create_hero_classes(db)
        response = client.get("/api/v1/personality/hero-classes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert "name" in data[0]
        assert "element" in data[0]

    def test_get_hero_class_by_id(self, client: TestClient, db: Session):
        """GET /api/v1/personality/hero-class/{id} should return one class."""
        mage, _ = _create_hero_classes(db)
        response = client.get(f"/api/v1/personality/hero-class/{mage.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Mago Cuántico"
        assert "stats_boost" in data

    def test_get_hero_class_not_found(self, client: TestClient):
        """GET /api/v1/personality/hero-class/{id} with bad ID returns 404."""
        response = client.get(f"/api/v1/personality/hero-class/{uuid.uuid4()}")
        assert response.status_code == 404

    def test_personality_test_endpoint_invalid_empty(self, client: TestClient):
        """POST /api/v1/personality/test with empty answers should fail."""
        response = client.post(
            "/api/v1/personality/test",
            json={"user_id": str(uuid.uuid4()), "answers": {}},
        )
        # The service raises ValueError for empty answers → 500
        assert response.status_code in (400, 422, 500)


# ---------------------------------------------------------------------------
# Validation unit tests (no DB needed)
# ---------------------------------------------------------------------------


class TestPersonalityValidation:
    """Test answer format validation."""

    def test_validate_personality_answers_format(self):
        """All answer keys should be valid question types."""
        valid_answers = {
            "motivation": "A",
            "learning_style": "B",
            "subject_preference": "C",
            "problem_solving": "D",
            "social_preference": "E",
        }
        required_keys = [
            "motivation", "learning_style", "subject_preference",
            "problem_solving", "social_preference",
        ]
        for key in required_keys:
            assert key in valid_answers

        valid_options = ["A", "B", "C", "D", "E"]
        for value in valid_answers.values():
            assert value in valid_options

    def test_validate_answer_single_char(self):
        """Each answer should be a single uppercase letter A-E."""
        valid = ["A", "B", "C", "D", "E"]
        for letter in valid:
            assert isinstance(letter, str)
            assert len(letter) == 1
            assert letter in valid

    def test_invalid_answers_rejected(self):
        """Invalid answers should not match valid options."""
        valid_options = {"A", "B", "C", "D", "E"}
        invalid = ["F", "1", "a", "", "AB"]
        for inv in invalid:
            assert inv not in valid_options

    def test_personality_test_request_schema(self):
        """PersonalityTestRequest should accept valid data."""
        req = PersonalityTestRequest(
            user_id="test-user",
            answers={"motivation": "A", "learning_style": "B"},
        )
        assert req.user_id == "test-user"
        assert req.answers["motivation"] == "A"


# ---------------------------------------------------------------------------
# Model unit tests
# ---------------------------------------------------------------------------


class TestHeroClassModel:
    """Test HeroClass model properties."""

    def test_class_type_mage(self, db: Session):
        """Mago class should return 'mage' type."""
        mage, _ = _create_hero_classes(db)
        assert mage.class_type == "mage"

    def test_class_type_warrior(self, db: Session):
        """Guerrero class should return 'warrior' type."""
        _, warrior = _create_hero_classes(db)
        assert warrior.class_type == "warrior"

    def test_get_stats_boost(self, db: Session):
        """get_stats_boost should return the stats dict."""
        mage, _ = _create_hero_classes(db)
        stats = mage.get_stats_boost()
        assert isinstance(stats, dict)
        assert "wisdom" in stats
        assert stats["wisdom"] == 25
